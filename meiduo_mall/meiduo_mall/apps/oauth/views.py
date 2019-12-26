import logging
import re

from django.conf import settings
from django.contrib.auth import login
from django.views import View
from django.shortcuts import render, redirect
from django import http
from django_redis import get_redis_connection

from QQLoginTool.QQtool import OAuthQQ
from oauth.models import OAuthQQUser
from meiduo_mall.utils.response_code import RETCODE
from oauth.utils import generate_access_token, check_access_token
from users.models import User
# Create your views here.

# 创建日志输出器
logger = logging.getLogger('django')


class QQAuthUserView(View):
    """处理QQ登录回调界面"""
    def get(self, request):
        """Oauth2.0认证"""
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

        try:
            # 数据库查找openid是否存在
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没有绑定
            access_token_openid = generate_access_token(openid)
            return render(request, 'oauth_callback.html', {'access_token_openid': access_token_openid})
        else:
            # 如果openid绑定了美多商城
            qq_user = oauth_user.user
            # 状态保持
            login(request, qq_user)
            # 响应结果
            next = request.GET.get('state')
            response = redirect(next)
            # 登录时用户名写入cookie中
            response.set_cookie('username', qq_user.username, max_age=3600 * 24 * 15)
            return response

    def post(self, request):
        """美多商城用户绑定到openid"""
        # 接收参数  前端通过from表单发送post请求<form method="post" id="reg_form" @submit="on_submit" v-cloak>
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        access_token_openid = request.POST.get('access_token_openid')
        # 校验参数
        if not all([mobile, password, sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位密码')
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)  # 向redis数据库取手机号
        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {"sms_code_errmsg": "无效的短信验证码"})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'oauth_callback.html', {"sms_code_errmsg": "输入短信验证码有误"})

        # # 判断openid是否有效：错误提示放在sms_code_errmsg位置
        openid = check_access_token(access_token_openid)
        if openid is None:
            return render(request, 'oauth_callback.html', {"openid_errmsg": "openid已经失效"})
        # 保存注册数据
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 用户不存在，新建用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            # 用户存在，检查用户密码
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {"account_errmsg": "密码或用户名错误"})
        # 将用户绑定到openid
        try:
            oauth_qq_user = OAuthQQUser.objects.create(openid=openid, user=user)
        except Exception as e:
            logger.error(e)
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})
        # 实现状态保持
        login(request, oauth_qq_user.user)
        # 响应绑定结果
        next = request.GET.get('state')
        response = redirect(next)
        # 登录时用户名写入cookie
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response









class QQAuthURLView(View):
    """提供qq登录扫码界面"""
    def get(self, request):
        """"""
        next = request.GET.get('next')
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        login_url = oauth.get_qq_url()

        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "login_url": login_url})





