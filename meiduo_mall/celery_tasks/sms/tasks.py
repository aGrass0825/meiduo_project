# 定义任务
import logging
from . import constants
from celery_tasks.sms.yuntongxun.ccp_sms import CCP
from celery_tasks.main import celery_app
logger = logging.getLogger('django')


@celery_app.task(bind=True, name='send_sms_code', retry_backoff=3)  # 保证celery识别任务
def send_sms_code(self, mobile, sms_code):
    """
    发送短信验证码的异步任务
    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return: 成功0 ,失败-1
    """
    # 发送短信验证码
    try:
        send_ret = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], constants.SEND_SMS_TEMPLATE_ID)
    except Exception as e:
        logger.error(e)
        raise self.retry(exc=e, max_retries=2)  # 发送失败重新发送retry
    else:
        return send_ret
