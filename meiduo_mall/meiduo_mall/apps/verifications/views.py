from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from verifications.libs.captcha.captcha import captcha
from django_redis import get_redis_connection


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
        redis_conn.setex('img_%s' % uuid, 300, text)

        return http.HttpResponse(image, content_type='image/jpg')
