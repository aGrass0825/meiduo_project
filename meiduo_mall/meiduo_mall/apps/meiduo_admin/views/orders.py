from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAdminUser

from meiduo_admin.serializers.orders import OrderListSerializer, OrderDetailSerializer, OrderStatusSerializer
from meiduo_admin.utils.pagination import StandardResultPagination
from orders.models import OrderInfo


# GET /meiduo_admin/orders/
class OrdersViewSet(UpdateModelMixin, ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]

    # 指定router动态生成路由时，提取参数的正则表达式
    lookup_value_regex = '\d+'

    # 指定视图所使用的分页类(局部)
    pagination_class = StandardResultPagination

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        orders = OrderInfo.objects.all()
        if keyword:
            orders = orders.filter(Q(order_id=keyword) | Q(skus__sku__name__contains=keyword)).distinct()

        return orders

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        else:
            return OrderStatusSerializer

    @action(methods=['put'], detail=True)
    def status(self, request, pk):
        """修改指定的订单状态"""
        return self.update(request)
        # # 1根据pk获取指定的订单
        # order = self.get_object()
        # # 2获取status并进行校验
        # serializer = self.get_serializer(order, data=request.data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        # return Response(serializer.data)