import base64
import json
import pickle
from django import http
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from meiduo_mall.utils.response_code import RETCODE
from goods.models import SKU
from carts import constants


# Create your views here.


class CartsSimpleView(View):
    """商品界面右上角购物车"""

    def get(self, request):
        """实现界面右上角购物车展示"""
        # 业务逻辑
        user = request.user
        # 登录用户
        if user.is_authenticated and user:
            # 链接redis数据库
            redis_conn = get_redis_connection('carts')
            # 取出redis数据库中当前登录用户所有的商品
            redis_cart = redis_conn.hgetall('carts_%s' % user.id)
            # 取出当前登录用户是否勾选商品
            redis_selected = redis_conn.smembers('selected_%s' % user.id)
            # 构造从cookie中取出的商品信息格式一致
            cart_dict = {}
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected
                }
        # 未登录用户
        else:
            # 从cookie中取出valu
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将字符串转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}
        # 构造json数据
        cart_skus = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image.url
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_skus})


class CartsSelectAllView(View):
    """全选购物车"""

    def put(self, request):
        """实现用户是否全选"""
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        selected = json_dict.get('selected', True)
        # 校验参数
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('selected参数有误')
        # 业务逻辑
        user = request.user
        if user.is_authenticated and user is not None:
            # 登录用户 操作redis
            redis_conn = get_redis_connection('carts')
            cart = redis_conn.hgetall('carts_%s' % user.id)
            sku_id_list = cart.keys()

            if selected:
                # 全选时
                redis_conn.sadd('selected_%s' % user.id, *sku_id_list)
            else:
                # 不全选时
                redis_conn.srem('selected_%s' % user.id, *sku_id_list)

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        else:
            # 未登录用户 操作cookie
            cart = request.COOKIES.get('carts')
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
            if cart is not None:
                cart_str_bytes = cart.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
                # 遍历cart_dict字典
                for sku in cart_dict:
                    cart_dict[sku]['selected'] = selected

                cart_dict_bytes = pickle.dumps(cart_dict)
                cart_str_bytes = base64.b64encode(cart_dict_bytes)
                cookie_cart_str = cart_str_bytes.decode()

                response.set_cookie('carts', cookie_cart_str, max_age=constants.CARTS_COOKIE_EXPIRES)
            # 响应结果
            return response


class CartsView(View):
    """购物车管理"""

    def get(self, request):
        """提供查询购物车界面"""
        user = request.user
        if user.is_authenticated:
            # 登录用户
            # 链接redis数据库
            redis_conn = get_redis_connection('carts')
            # 取商品sku
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 取是否勾选状态
            redis_selected = redis_conn.smembers('selected_%s' % user.id)

            # 将redis数据构造成和cookie数据一样，方便统一查询
            carts_dict = {}
            for sku_id, count in redis_carts.items():
                carts_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected  # 判断sku_id是否在selected里面，在则返回True, 不再返回False
                }
        else:
            # 未登录用户
            # 从cookie 中取出carts的字符串
            carts_str = request.COOKIES.get('carts')
            if carts_str:
                # 将取出的cookie字符串转换成bytes类型字符串
                carts_str_bytes = carts_str.encode()
                # 将bytes类型字符串转换成bytes类型字典
                carts_dict_bytes = base64.b64decode(carts_str_bytes)
                # 将bytes类型字典转换成真正的字典类型
                carts_dict = pickle.loads(carts_dict_bytes)
            else:
                carts_dict = {}

        # 构造购物车渲染数据
        sku_dis = carts_dict.keys()
        skus = SKU.objects.filter(id__in=sku_dis)
        carts_skus = []
        for sku in skus:
            carts_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id).get('count'),
                'selected': str(carts_dict.get(sku.id).get('selected')),  # 这里bool类型不是字符串类型所以 这里转str()必须转换， 不然前端报错
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 单价可能是浮点数 这里转str()必须转换
                'amount': str(sku.price * carts_dict.get(sku.id).get('count')),  # 单价X数量=总价 总价可能是浮点数所以这里转str()必须转换
            })
        context = {
            'carts_skus': carts_skus
        }
        return render(request, 'cart.html', context)

    def post(self, request):
        """添加购物车"""
        # 接收参数
        json_str = request.body.decode()
        json_dic = json.loads(json_str)
        sku_id = json_dic.get('sku_id')
        count = json_dic.get('count')
        selected = json_dic.get('selected', True)
        # 校验参数 是否缺少必传参数
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断商品在数据库中是否存在
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id 不存在')
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('count参数有误')
        # 判断selected 是否为bool值
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected有误')

        # 登录用户
        user = request.user
        # 业务逻辑
        if user.is_authenticated and user:
            # 登录用户 redis
            redis_conn = get_redis_connection('carts')
            # 优化
            pl = redis_conn.pipeline()
            # 新增购物车数据
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            # 判断用户是否勾选商品
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            pl.execute()
            # 响应结果
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功！'})
        else:
            # 未登录用户 cookie 取出cookie
            carts_str = request.COOKIES.get('carts')
            if carts_str:
                # 将取出的cookie字符串转换成bytes类型字符串
                carts_str_bytes = carts_str.encode()
                # 将bytes类型字符串转换成bytes类型字典
                carts_dict_bytes = base64.b64decode(carts_str_bytes)
                # 将bytes类型字典转换成真正的字典类型
                carts_dict = pickle.loads(carts_dict_bytes)
            else:
                carts_dict = {}
            # 判断商品在购物车中是否已经存在，不存在则添加，有则累计加
            if sku_id in carts_dict:
                count += carts_dict[sku_id]['count']  # 有则累计加
            # 不存在则添加
            carts_dict[sku_id] = {
                "count": count,
                "selected": selected
            }
            # 将真正字典转换成bytes类型字典 pickle
            carts_dict_bytes = pickle.dumps(carts_dict)
            # 将bytes类型字典转换成bytes类型字符串 base64
            carts_str_bytes = base64.b64encode(carts_dict_bytes)
            # 将bytes类型字符串转换成字符串 decode
            cookie_carts_str = carts_str_bytes.decode()
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
            response.set_cookie('carts', cookie_carts_str, max_age=constants.CARTS_COOKIE_EXPIRES)
            # 响应结果
            return response

    def put(self, request):
        """修改购物车"""
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
        # 校验参数
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')
        if int(count) < 0:
            return http.HttpResponseForbidden('count参数有误')
        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('count参数有误')
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected有误')
        user = request.user
        # 用户登录
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            # 用前端发来的数据来覆盖之前保存的数据
            pl = redis_conn.pipeline()
            pl.hset('carts_%s' % user.id, sku_id, count)
            # 判断是否勾选
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)
            # 执行管道
            pl.execute()
            # 构造上下文
            cart_sku = {
                'id': sku.id,
                'name': sku.name,
                'count': count,
                'selected': selected,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count
            }
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
        # 用户未登录
        else:
            carts_str = request.COOKIES.get('carts')
            if carts_str:
                # 将取出的cookie字符串转换成bytes类型字符串
                carts_str_bytes = carts_str.encode()
                # 将bytes类型字符串转换成bytes类型字典
                carts_dict_bytes = base64.b64decode(carts_str_bytes)
                # 将bytes类型字典转换成真正的字典类型
                carts_dict = pickle.loads(carts_dict_bytes)
            else:
                carts_dict = {}

            # 由于后端接收到的是最终的结果，直接覆盖
            carts_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将字典转换成bytes字典
            carts_dict_bytes = pickle.dumps(carts_dict)
            # 将bytes字典转换成bytes字符串
            carts_str_bytes = base64.b64encode(carts_dict_bytes)
            # 将bytes字符串转换成json字符串
            cookie_carts_str = carts_str_bytes.decode()
            # 构造上下文
            cart_sku = {
                'id': sku.id,
                'name': sku.name,
                'count': count,
                'selected': selected,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count
            }

            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
            response.set_cookie('carts', cookie_carts_str, max_age=constants.CARTS_COOKIE_EXPIRES)
            return response

    def delete(self, request):
        """删除购物车记录"""
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')
        # 校验参数
        if not all([sku_id]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')
        # 业务逻辑
        user = request.user
        if user.is_authenticated and user is not None:
            # 登录用户操作redis
            redis_conn = get_redis_connection('carts')

            pl = redis_conn.pipeline()
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})
        else:
            # 未登录用户操作cookie
            carts_str = request.COOKIES.get('carts')
            if carts_str:
                # 将json字符串转换成bytes字符串
                carts_str_bytes = carts_str.encode()
                # 将bytes字符串转换成bytes字典
                carts_dict_bytes = base64.b64decode(carts_str_bytes)
                # 将bytes字典转换成正真字典
                carts_dict = pickle.loads(carts_dict_bytes)
            else:
                carts_dict = {}

            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})
            if sku_id in carts_dict:
                # 删除字典
                del carts_dict[sku_id]
                # 将字典转换成bytes字典
                carts_dict_bytes = pickle.dumps(carts_dict)
                # 将bytes字典转换成bytes字符串
                carts_str_bytes = base64.b64encode(carts_dict_bytes)
                # 将bytes字符串转换成json字符串
                cookie_carts_str = carts_str_bytes.decode()
                response.set_cookie('carts', cookie_carts_str, max_age=constants.CARTS_COOKIE_EXPIRES)
            # 响应结果
            return response
