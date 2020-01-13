import json
import re

from django import http
from decimal import Decimal
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django_redis import get_redis_connection
from django.db import transaction

from carts.views import CartMixin
from meiduo_mall.utils.views import LoginRequiredJSONMixin, LoginRequiredMixin
from users.models import Address
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from meiduo_mall.utils.response_code import RETCODE

# Create your views here.


class OrderSuccessView(LoginRequiredMixin, View):
    """提交订单成功界面"""

    def get(self, request):
        """成功界面"""
        # 接收参数
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')
        # 校验参数
        if not all([order_id, payment_amount, pay_method]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'\d{23}', order_id):
            return http.HttpResponseForbidden('商品编号有误')
        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        # 响应结果
        return render(request, 'order_success.html', context)


class OrderCommitView(CartMixin, LoginRequiredJSONMixin, View):
    """提交订单"""

    def post(self, request):
        """保存订单信息"""
        # 接收参数
        json_str = request.body.decode()
        json_dict = json.loads(json_str)
        address_id = json_dict.get('address_id')  # 用户地址编码
        pay_method = json_dict.get('pay_method')  # 用户支付方式
        # 校验参数
        if not all([address_id, pay_method]):
            http.HttpResponseForbidden('缺少必传参数')
        # 判断地址是否正确
        user = request.user
        try:
            if user.is_authenticated and user:
                address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            http.HttpResponseForbidden('地址参数有误')
        # 判断支付方式是否正确
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            http.HttpResponseForbidden('支付方式有误')
        # 业务逻辑
        # 登录用户
        user = request.user
        # 创建订单编号 时间+用户id
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)

        # 开启一个事物
        with transaction.atomic():
            # 事物保存点
            save_id = transaction.savepoint()
            try:
                # 写入商品订单基本数据库（一）
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal(0.00),
                    freight=Decimal(10.00),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )

                # 从redis中读取被选中的购物车信息
                # redis_conn = get_redis_connection('carts')
                # redis_cart = redis_conn.hgetall('carts_%s' % user.id)
                # redis_selected = redis_conn.smembers('selected_%s' % user.id)
                cart = {}
                if not cart:
                    cart_dict = request.cart
                    for sku_id in cart_dict:
                        # cart_dict[int(sku_id)] = int(redis_cart[sku_id])
                        cart[sku_id] = cart_dict[sku_id][0]

                sku_dis = cart.keys()
                for sku_id in sku_dis:
                    while True:
                        sku = SKU.objects.get(id=sku_id)

                        # 读取原始库存
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        # 判断sku库存
                        sku_count = cart[sku.id]
                        if sku_count > sku.stock:
                            # 出错回滚
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        # 减少库存，增加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # 乐观锁更新库存和销量
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)
                        # 如果下单失败，但是库存足够时，继续下单，直到下单成功或者库存不足为止
                        if result == 0:
                            continue

                        # 修改spu销量
                        sku.spu.sales += sku_count
                        sku.spu.save()

                        # 保存订单商品信息（多）
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price
                        )

                        # 保存商品订单中总价和总数量
                        order.total_amount += sku.price * sku_count
                        order.total_count += sku_count

                        # 下单成功，退出循环
                        break

                # 邮费和保存订单信息
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '下单失败'})
            # 订单成功，提交事物
            transaction.savepoint_commit(save_id)

        # 清除购物车中的数据
        # pl = redis_conn.pipeline()
        # pl.hdel('carts_%s' % user.id, *redis_selected)
        # pl.srem('selected_%s' % user.id, *redis_selected)
        # pl.execute()

        # 清除购物车中的数据
        redis_conn = get_redis_connection("carts")
        user = request.user
        redis_conn.delete('carts_%s' % user.id)
        # 响应参数
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '下单成功', 'order_id': order.order_id})


class OrderSettlementView(CartMixin, LoginRequiredMixin, View):
    """商品订单"""

    def get(self, request):
        """提供商品订单界面"""
        # 获取用户登录信息
        user = request.user
        # 查询地址信息
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Address.DoesNotExist:
            addresses = None

        # # 从redis中查询被勾选的商品
        # redis_conn = get_redis_connection('carts')
        # redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        # redis_selected = redis_conn.smembers('selected_%s' % user.id)
        cart = {}
        if not cart:
            cart_dict = request.cart
            for sku_id in cart_dict:
                # cart_dict[int(sku_id)] = int(redis_cart[sku_id])
                cart[sku_id] = cart_dict[sku_id][0]

        # 准备初始值
        total_count = 0
        total_amount = Decimal(0.00)

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            # 由于sku没有数量和总价故动态绑定
            sku.count = cart[sku.id]  # 由于python是动态语言。可以动态绑定
            sku.amount = sku.count * sku.price
            # 计算总数量和总金额
            total_count += sku.count
            total_amount += sku.count * sku.price

        # 运费
        freight = Decimal('10.00')

        # 渲染界面
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight

        }

        return render(request, 'place_order.html', context)
