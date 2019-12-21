import logging
import random

from django import http
from django.views import View
from django_redis import get_redis_connection

from celery_tasks.sms import constants
from meiduo_mall.utils.response_code import RETCODE
from verifications.libs.captcha.captcha import captcha
from celery_tasks.sms.tasks import send_sms_code
# Create your views here.
# 创建日志输出器
logger = logging.getLogger('django')


class SMSCodeView(View):
    """短信验证码"""
    def get(self, request, mobile):
        """

        :param request:请求对象
        :param mobile: 手机号
        :return: JSON
        """
        # 接收参数
        image_code_client = request.GET.get('image_code')  # 客户填写的图片验证码
        uuid = request.GET.get('uuid')

        # 校验参数
        if not all([image_code_client, uuid]):
            # return http.JsonResponse({"code": RETCODE.NECESSARYPARAMERR, "errmsg": "缺少必传参数"})
            return http.HttpResponseForbidden('缺少必传参数')

        # 创建链接到redis的对象
        redis_conn = get_redis_connection("verify_code")
        # 提取短信验证码标记
        send_flag = redis_conn.get("sms_flag_%s" % mobile)
        if send_flag:
            return http.JsonResponse({"code": RETCODE.THROTTLINGERR, "errmsg": "发送短信过于频繁"})
        # 提出图形验证码
        image_code_server = redis_conn.get("img_%s" % uuid)
        if image_code_server is None:
            # 图形验证码不存在或者过期
            return http.JsonResponse({"code": RETCODE.IMAGECODEERR, "errmsg": "图形验证码失效"})
        # 从redis数据库中拿到验证码后就立马删除库中的验证码，避免恶意测试
        # try:
        redis_conn.delete("img_%s" % uuid)
        # except Exception as f:
        #     logger.error(f)

        # 对比图形验证码
        image_code_server = image_code_server.decode()  # 解码
        if image_code_client.lower() != image_code_server.lower():  # 全部转换成小写
            return http.JsonResponse({"code": RETCODE.IMAGECODEERR, "errmsg": "输入的图形验证码有误"})

        # 生成短信验证码：发给第三方运通讯
        sms_code = "%06d" % random.randint(0, 999999)

        # 日志
        logger.info(sms_code)
        # 创建redis管道
        pl = redis_conn.pipeline()
        # 将redis添加到请求队列中
        # 保存短信验证码
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存短信验证码的标记
        pl.setex("sms_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        # 执行请求
        pl.execute()
        # 发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], constants.SEND_SMS_TEMPLATE_ID)
        send_sms_code.delay(mobile, sms_code)  # 使用celery发送短信的开关

        # 响应结果
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "发送短信成功"})


class ImageCodeView(View):
    """图形验证码"""
    def get(self, request, uuid):
        """
        图形验证
        :param request: 用户请求
        :param uuid: 通用唯一标识码
        :return: image/jpg
        """
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return http.HttpResponse(image, content_type='image/jpg')
