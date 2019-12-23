import logging
from django.conf import settings
from django.views import View
from django.shortcuts import render
from django import http

from QQLoginTool.QQtool import OAuthQQ
from meiduo_mall.utils.response_code import RETCODE
# Create your views here.


# 创建日志输出器
logger = logging.Logger('django')
class QQAuthUserView(View):
    """处理QQ登录回调界面"""
    def get(self, request):
        """"""
        code = request.GET.get('code')
        if code is None:
            return http.HttpResponseForbidden('获取code失败')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            access_token = oauth.get_access_token(code)  # 根据code获取token
            openid = oauth.get_open_id(access_token)  # 根据token获取openid
        except Exception as es:
            logger.error(es)
            return http.HttpResponseServerError('OAuth 2.0认证失败')






class QQAuthURLView(View):
    """提供qq登录扫码界面"""
    def get(self, request):
        """"""
        next = request.GET.get('next')
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        login_url = oauth.get_qq_url()

        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "login_url": login_url})





