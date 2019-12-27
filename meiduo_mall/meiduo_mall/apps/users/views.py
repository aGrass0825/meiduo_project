import re, json

import logging
from django import http
from django.contrib.auth import login, authenticate, logout
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin

from users.models import User
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from users.utils import generate_verify_email_url
from users.utils import check_verify_email_token
# Create your views here.

logger = logging.getLogger('django')  # 创建日志输出器


class AddressView(LoginRequiredMixin, View):
    """用户收获地址"""
    def get(self, request):
        """
        提供收获地址界面
        :param request:请求报文
        :return: render
        """
        return render(request, 'user_center_site.html')





class VerifyEmailView(View):
    """接收用户激活邮箱发送的请求"""
    def get(self, request):
        """
        实现邮箱的激活逻辑
        :param request:请求报文
        :return:
        """
        # 接收参数
        token = request.GET.get("token")
        # 校验参数
        if token is None:
            return http.HttpResponseBadRequest('缺少token')
        user = check_verify_email_token(token)
        # 修改email_active的值为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('激活邮件失败')
        # 响应结果
        return redirect(reverse("users:info"))


class EmaliView(LoginRequiredJSONMixin, View):
    """添加邮箱"""
    def put(self, request):
        """
        实现邮箱接收的逻辑
        :param request: 请求报文
        :return:
        """
        # 接收参数
        json_dict = json.loads(request.body.decode())  # 前端是json非表单传参，后端接收必须用request.body接收。
        email = json_dict.get('email')
        # 校验参数
        if not email:
            return http.HttpResponseForbidden('缺少email参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email错误')
        # 赋值email字段
        try:
            request.user.email = email  # 将用户传入的邮箱保存到用户的email字段中，传入的用户(request.user)和邮箱绑定在一起。
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "添加email失败"})
        #celery异步发送邮箱
        verify_url = generate_verify_email_url(request.user)
        # delay开关，调用celery执行调用
        send_verify_email.delay(email, verify_url)
        # 响应邮箱添加结果
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "添加email成功"})



class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""
    def get(self, request):
        """提供用户中心展示界面"""
        # if request.user.is_authenticated():
        #     return render(request, 'user_center_info.html')
        # else:
        #     return redirect(reverse('users:login'))
        context = {
            "username": request.user.username,
            "mobile": request.user.mobile,
            "email": request.user.email,
            "email_active": request.user.email_active
        }

        return render(request, 'user_center_info.html', context)




class LogoutView(View):
    """用户退出登录"""
    def get(self, request):
        """清除状态保持"""
        logout(request)
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')
        return response


class LoginView(View):
    """用户登录"""
    def get(self, request):
        """返回登录界面"""
        return render(request, 'login.html')

    def post(self, request):
        """
        实现登录逻辑
        :param request: 请求对象
        :return: 登录结果
        """
        # 接收请求 提取参数
        username = request.POST.get("username")
        password = request.POST.get("password")
        remembered = request.POST.get("remembered")

        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')

        # 认证登录用户
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 状态保持
        login(request, user)
        if remembered != 'on':
            request.session.set_expiry(0)  # 0表示会话结束状态保持结束
        else:
            request.session.set_expiry(None)  # None表示默认session保存两周
        # 取出next
        next = request.GET.get('next')  # 返回的就是个字符串 查询字符串传参
        if next:
            response = redirect(next)  # next不用字符串
        else:
            # 响应登录结果 重定向到首页
            response = redirect(reverse('contents:index'))
        # 为了首页显示用户登录信息，将用户名缓存到cookie中
        response.set_cookie('username', user.username, max_age=3600*24*15)
        return response


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    """判断手机号是否重复"""
    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    def post(self, request):
        """实现用户注册逻辑"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code_client = request.POST.get('sms_code')

        # 判断参数是否齐全
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 判断短信验证码是否输入正确
        # 创建链接到redis的对象
        redis_conn = get_redis_connection("verify_code")
        sms_code_server = redis_conn.get("sms_%s" % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})
        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})
        # 实现状态保持
        login(request, user)
        # 响应登录结果 重定向到首页
        response = redirect(reverse('contents:index'))
        # 为了首页显示用户登录信息，将用户名缓存到cookie中
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response

