# 定义任务
from . import constants
from celery_tasks.sms.yuntongxun.ccp_sms import CCP
from celery_tasks.main import celery_app


@celery_app.task(name='send_sms_code')  # 保证celery识别任务
def send_sms_code(mobile, sms_code):
    """
    发送短信验证码的异步任务
    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return: 成功0 ,失败-1
    """
    # 发送短信验证码
    send_ret = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], constants.SEND_SMS_TEMPLATE_ID)
    return send_ret
