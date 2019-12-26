# 自定义用户认证后端，实现多帐号登录
import re
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from itsdangerous import BadData

from users import constants
from users.models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


def check_verify_email_token(token):
    """
    接收email发送的get请求，反序列化
    :param token: 用户签名后的结果
    :return: user, None
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    try:
        data = serializer.loads(token)
    except BadData:
        return None
    else:
        id = data.get("user_id")
        email = data.get("user_email")
    try:
        user = User.objects.get(id=id, email=email)  # 与数据库进行匹配，并且返回用户注册的用户名
    except User.DoesNotExist:
        return None
    else:
        return user





def generate_verify_email_url(user):
    """
    生成邮箱验证链接,进行签名
    :param user: 当前用户登录
    :return: verify_url
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    data = {"user_id": user.id, "user_email": user.email}
    token = serializer.dumps(data).decode()
    verify_url = settings.EMAIL_VERIFY_URL + "?token=" + token
    return verify_url



def get_user_by_account(account):
    """
    对多帐号登录进行封装
    :param account: 用户或手机号
    :return: user
    """
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileBackend(ModelBackend):
    """自定义用户认证后端"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写用户认证的方法
        :param request:请求方法
        :param username: 用户名
        :param password: 明文密码
        :param kwargs: 额外参数
        :return: user
        """
        # 调用封装的多帐号登录的函数
        user = get_user_by_account(username)

        if user and user.check_password(password):
            return user
        else:
            return None
