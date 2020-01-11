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


class CartMixin(View):  # View的父类就是object
    """读取与写入"""

    # 重写as_view()中的dispatch方法
    def dispatch(self, request, *args, **kwargs):
        request.cart = self.read_cart(request)  # request.cart == cart_dict
        response = super().dispatch(request, *args, **kwargs)
        self.write_cart(request, response, request.cart)
        return response

    def read_cart(self, request) -> dict:
        user = request.user
        if user.is_authenticated and user:
            return self.read_redis_cart(user.id)
        else:
            return self.read_cookie_cart(request)

    def read_redis_cart(self, user_id):
        key = 'carts_%s' % user_id
        redis_conn = get_redis_connection("carts")
        cart_bytes = redis_conn.get(key)  # 从redis数据库取出的是bytes类型字符串 不需要用encode()转换
        if not cart_bytes:
            return {}
        cart_dict = pickle.loads(base64.b64decode(cart_bytes))
        return cart_dict

    def read_cookie_cart(self, request):
        cart_str = request.COOKIES.get('CART')
        if not cart_str:
            return {}
        cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
        return cart_dict

    def write_cart(self, request, response, cart_dict):
        user = request.user
        if user.is_authenticated and user:
            self.write_redis_cart(user.id, cart_dict)
        else:
            self.write_cookie_cart(response, cart_dict)

    def write_redis_cart(self, user_id, cart_dict):
        key = 'carts_%s' % user_id
        redis_conn = get_redis_connection("carts")
        cart_bytes = base64.b64encode(pickle.dumps(cart_dict))
        redis_conn.set(key, cart_bytes)

    def write_cookie_cart(self, response, cart_dict):
        cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
        response.set_cookie("CART", cart_str)


class CartsSimpleView(CartMixin, View):
    """商品界面右上角购物车"""

    def get(self, request):
        """实现界面右上角购物车展示"""
        # user = request.user
        # if user.is_authenticated and user:
        #     redis_conn = get_redis_connection('carts')
        #     redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        #     redis_selected = redis_conn.smembers('selected_%s' % user.id)
        #     cart_dict = {}
        #     for sku_id, count in redis_cart.items():
        #         cart_dict[int(sku_id)] = {
        #             'count': int(count),
        #             'selected': sku_id in redis_selected
        #         }
        # else:
        #     cart_str = request.COOKIES.get('CART')
        #     if cart_str:
        #         cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
        #     else:
        #         cart_dict = {}
        cart_dict = request.cart
        sku_ids = cart_dict.keys()
        cart_skus = []
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id)[0],
                'default_image_url': sku.default_image.url
            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': cart_skus})


class CartsSelectAllView(CartMixin, View):
    """全选购物车"""

    def put(self, request):
        """实现用户是否全选"""
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        selected = json_dict.get('selected', True)
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('selected参数有误')
        # -------------------------------------------------------------------->
        # cart_dict = self.read_cart(request)
        cart_dict = request.cart
        for l in cart_dict.values():
            l[1] = selected

        # response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        # -------------------------------------------------------------------->
        # self.write_cart(request, response, cart_dict)
        # return response
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class CartsView(CartMixin, View):
    """购物车管理"""

    def get(self, request):
        """提供查询购物车界面"""
        # -------------------------------------------------------------------->
        # carts_dict = self.read_cart(request)  # 字典样式sku_id:[count,True]
        carts_dict = request.cart
        sku_ids = carts_dict.keys()

        skus = SKU.objects.filter(id__in=sku_ids)
        carts_skus = []
        for sku in skus:
            carts_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': carts_dict.get(sku.id)[0],
                'selected': str(carts_dict.get(sku.id)[1]),  # 这里bool类型不是字符串类型所以 这里转str()必须转换， 不然前端报错
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # 单价可能是浮点数 这里转str()必须转换
                'amount': str(sku.price * carts_dict.get(sku.id)[0]),  # 单价X数量=总价 总价可能是浮点数所以这里转str()必须转换
            })
        context = {
            'carts_skus': carts_skus
        }
        return render(request, 'cart.html', context)

    def post(self, request):
        """添加购物车"""
        json_str = request.body.decode()
        json_dic = json.loads(json_str)
        sku_id = json_dic.get('sku_id')
        count = json_dic.get('count')
        selected = json_dic.get('selected', True)
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id 不存在')
        try:
            count = int(count)
        except Exception as e:
            return http.HttpResponseForbidden('count参数有误')
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected有误')
                # -------------------------------------------------------------------->
        # cart = self.read_cart(request)  # 字典样式sku_id:[count,True]
        cart = request.cart
        if sku.id in cart:  # 判断此商品是否在购物车中，有就累加， 没有就添加
            # cart[sku.id][0] += count
            # cart[sku.di][1] = selected
            cart[sku.id] = [cart[sku.id][0] + count, selected]  # 累加
        else:
            cart[sku.id] = [count, selected]  # 添加
        # response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
        #
        # self.write_cart(request, response, cart)
        # return response
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})

    def put(self, request):
        """修改购物车"""
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)
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
            # -------------------------------------------------------------------->
            # cart_dict = self.read_cart(request)
            cart_dict = request.cart
            cart_dict[sku.id] = [count, selected]  # 这里将样式定为sku_id:[count, selected]

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

            # response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
            # self.write_cart(request, response, cart_dict)
            # return response
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})

    def delete(self, request):
        """删除购物车记录"""
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        sku_id = json_dict.get('sku_id')
        if not all([sku_id]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')
            # -------------------------------------------------------------------->
        # cart_dict = self.read_cart(request)
        cart_dict = request.cart
        # 由于del删除空的字典会报错，故改用pop删除
        cart_dict.pop(sku.id, None)
        # response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})
        # # -------------------------------------------------------------------->
        # self.write_cart(request, response, cart_dict)
        # return response
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})
