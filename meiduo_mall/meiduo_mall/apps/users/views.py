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
from users.models import Address
from users import constants
from goods.models import SKU
# Create your views here.

logger = logging.getLogger('django')  # 创建日志输出器


class UserBrowseHistory(LoginRequiredJSONMixin, View):
    """用户浏览记录"""

    def post(self, request):
        """保存用户浏览记录"""
        # 接收参数
        josn_str = request.body.decode()
        json_dict = json.loads(josn_str)
        sku_id = json_dict.get('sku_id')
        # 校验参数
        try:
            # 查询数据库存不存在
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')
        # 用redis保存用户浏览记录 用户五种数据类型选择列表类型
        redis_conn = get_redis_connection('history')  # 链接redis数据库
        user_id = request.user.id  # 获取登录用户的id
        pl = redis_conn.pipeline()
        # 1.lrem去重
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 2.lpush保存
        pl.lpush('history_%s' % user_id, sku_id)
        # 3.ltrim截取
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行
        pl.execute()
        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        """提供用户查询浏览记录界面"""
        redis_conn = get_redis_connection('history')
        user_id = request.user.id
        # 取出当前用户所有商品id
        sku_ids = redis_conn.lrange('history_%s' % user_id, 0, -1)
        # 根据取出的商品sku_ids从sql中取出商品信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': "OK", 'skus': skus})


class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def get(self, request):
        """提供修改密码界面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """
        修改密码，接收前端发送的
        :param request:
        :return:
        """
        # 接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')
        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return http.HttpResponseForbidden('缺少必传参数')
        # try:
        ret = request.user.check_password(old_password)
        # ret=false 表示原始密码错误， ret=true表示原始密码正确
        if not ret:
            # except Exception as e:
            #     logger.error(e)
            return render(request, 'user_center_pass.html', {'origin_password_errmsg': '原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_password2 != new_password:
            return http.HttpResponseForbidden('新密码不能和旧密码一致')
        # 修改密码,密码写入数据库
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_password_errmsg': '密码修改失败'})
        # 退出状态保持
        logout(request)
        # 响应结果 重定向导登录界面，让用户用新密码重新登录
        response = redirect(reverse('users:login'))
        response.delete_cookie('username')  # 删除用户cookie
        return response


class UpdateTitleAddressView(LoginRequiredJSONMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """
        设置地址标题
        :param request:
        :return:
        """
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        title = json_dict.get('title')
        # 校验参数
        if title is None:
            return http.HttpResponseForbidden('缺少title')
        # 查询数据，修改结果
        try:
            address = Address.objects.get(id=address_id)
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "设置地址标题错误"})
        # 响应结果
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK"})


class DefaultAddressView(LoginRequiredJSONMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """
        设置默认地址
        :param request:
        :return:
        """
        try:
            # 接收参数address_id 查询参数
            address = Address.objects.get(id=address_id)
            request.user.default_address = address  # 将查询的地址赋值给当前登录的用户默认地址
            request.user.save()  # 推送到数据库
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "默认地址设置失败"})
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK"})


class UpdateDestroyAddressView(LoginRequiredJSONMixin, View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """
        修改地址
        :param request:
        :return:
        """
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号错误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('固定电话错误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('email错误')
        # 修改数据库
        try:
            # 判断地址是否存在，并更新地址信息，模型类操作数据库
            Address.objects.filter(id=address_id).update(
                user=request.user,  # 当前登录的用户
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "更新地址失败"})
        # 响应结果 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }

        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "address": address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)
            # 将地址逻辑删除设置为true
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "删除失败"})
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "删除成功"})


class CreatAdderssView(LoginRequiredJSONMixin, View):
    """新增地址"""

    def post(self, request):
        """
        实现新增地址逻辑
        :param request: 请求报文
        :return: 新增地址
        """
        # 判断用户存储地址是否超过上限20个 一查多
        count = request.user.addresses.filter(is_deleted=False).count()  # filter(is_deleted=False)排除逻辑删除占用地址次数
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return http.JsonResponse({"code": RETCODE.THROTTLINGERR, "errmsg": "超过增加地址上限"})
        # 接收参数
        json_str = request.body.decode()
        json_dic = json.loads(json_str)
        # 提取字典中的参数
        receiver = json_dic.get('receiver')
        province_id = json_dic.get('province_id')
        city_id = json_dic.get('city_id')
        district_id = json_dic.get('district_id')
        place = json_dic.get('place')
        mobile = json_dic.get('mobile')
        tel = json_dic.get('tel')
        email = json_dic.get('email')
        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号错误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('固定电话错误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('email错误')
        try:
            # 存储参数
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
            # 设置默认地址
            if request.user.default_address is None or Address.objects.get(
                    id=request.user.default_address_id).is_deleted == True:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({"code": RETCODE.DBERR, "errmsg": "地址保存失败"})

        # 新增地址成功后，将新增的记录响应给前端展示(局部刷新)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email,
        }
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "address": address_dict,
                                  'default_address_id': request.user.default_address_id})


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """
        查询并展示用户地址信息
        :param request:
        :return:
        """
        # 模型类操作数据库取出符合条件模型集合
        addresses = Address.objects.filter(user=request.user, is_deleted=False)  # 前端用钩子函数显示，只显示is_deleted=False的
        # 地址模型列表转换成字典列表
        address_dict_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_dict_list.append(address_dict)
        context = {
            # "default_address_id": request.user.default_address_id or '0',  # 解决收货地址不展示
            "default_address_id": request.user.default_address_id,
            "addresses": address_dict_list
        }
        # 响应结果
        return render(request, "user_center_site.html", context)


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
        # celery异步发送邮箱
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
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
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
