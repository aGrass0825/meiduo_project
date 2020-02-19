from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from goods.models import SKUImage, SKU
from meiduo_admin.serializers.skus import SKUImageSerializer, SKUSimpleSerializer, SKUSerializer
from meiduo_admin.utils.pagination import StandardResultPagination


class SKUImageViewSet(ModelViewSet):
    """sku图片的视图集"""
    permission_classes = [IsAdminUser]

    # 指定当前视图所使用的分页类(局部)
    pagination_class = StandardResultPagination

    # 指定router动态生成路由时，提取参数的正则表达式
    lookup_value_regex = '\d+'

    # 指定当前视图所使用的查询集
    queryset = SKUImage.objects.all()
    # 指定当前视图所使用的序列化器类
    serializer_class = SKUImageSerializer


# GET /meiduo_admin/skus/simple/
class SKUSimpleView(ListAPIView):
    permission_classes = [IsAdminUser]

    queryset = SKU.objects.all()
    serializer_class = SKUSimpleSerializer


class SKUViewSet(ModelViewSet):
    """sku管理的视图集"""
    permission_classes = [IsAdminUser]

    # 指定router动态生成路由时，提取参数的正则表达式
    lookup_value_regex = '\d+'

    # 指定当前视图所使用的分页类(局部)
    pagination_class = StandardResultPagination

    def get_queryset(self):
        # 获取keyword
        keyword = self.request.query_params.get('keyword')

        # if keyword:
        #     skus = SKU.objects.filter(Q(name__contains=keyword) | Q(caption__contains=keyword))
        # else:
        #     skus = SKU.objects.all()
        skus = SKU.objects.all()
        if keyword:
            skus = skus.filter(Q(name__contains=keyword) | Q(caption__contains=keyword))
        return skus

    serializer_class = SKUSerializer


