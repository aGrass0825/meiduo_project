# 自定义用户认证后端，实现多帐号登录
import re
from django.contrib.auth.backends import ModelBackend

from users.models import User


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
