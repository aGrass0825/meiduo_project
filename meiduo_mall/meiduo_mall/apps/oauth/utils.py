from django.conf import settings

from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import constants


def check_access_token(access_token_openid):
    """
    反解，反序列化
    :param access_token:openid密文
    :return:openid明文
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.ACCESS_TOKEN_EXPIRES)
    try:
        token = serializer.loads(access_token_openid)
    except BadData:  # openid明文可能过期
        return None
    else:
        return token.get('openid')


def generate_access_token(openid):
    """
    签名openid
    :param openid:用户的openid(明文)
    :return: access_token(密文)
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.ACCESS_TOKEN_EXPIRES)
    data = {'openid': openid}
    token = serializer.dumps(data)
    return token.decode()