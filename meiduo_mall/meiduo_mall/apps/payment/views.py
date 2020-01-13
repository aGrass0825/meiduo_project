from django.shortcuts import render
import os
from django.views import View
from django import http
from django.conf import settings

from alipay import AliPay

from meiduo_mall.utils.response_code import RETCODE
from orders.models import OrderInfo
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from payment.models import Payment


# Create your views here.


class PaymentStatusView(LoginRequiredJSONMixin, View):
    """保存订支付结果"""

    def get(self, request):
        # 接收参数 (支付宝采用查询字符串传参)
        query_dict = request.GET  # 查询字典
        data = query_dict.dict()  # 字典
        # 校验参数
        # 业务逻辑
        # 1.删除data中的sign 因为在校验alipay.verify时data中不能存在sign
        signature = data.pop('sign')
        # 2.创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        # 3.修改订单状态为待评价 (乐观锁)
        OrderInfo.objects.filter(order_id='order_id', status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(
            status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])
        # 4.校验这个重定向是否是alipay重定向过来的
        success = alipay.verify(data, signature)
        if success:
            # 读取order_id
            order_id = data.get('out_trade_no')
            # 读取支付宝流水号
            trade_id = data.get('trade_no')
            # 保存Payment模型类数据
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            # 响应结果
            context = {
                'trade_id': trade_id
            }
            return render(request, 'pay_success.html', context)
        else:
            return http.HttpResponseForbidden('非法操作')


class PaymentView(LoginRequiredJSONMixin, View):
    """订单支付功能"""

    def get(self, request, order_id):
        """查询要支付的订单"""
        # 接收参数
        # 校验参数
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单信息错误')

        # 业务逻辑
        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )
        # 生成支付宝链接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )
        # 响应结果
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})
