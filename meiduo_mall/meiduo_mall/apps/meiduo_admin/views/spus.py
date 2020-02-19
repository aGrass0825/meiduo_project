from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser

from goods.models import SPU, SPUSpecification
from meiduo_admin.serializers.spus import SPUSimpleSerializer, SPUSpecSerializer


class SPUSimpleView(ListAPIView):
    permission_classes = [IsAdminUser]

    queryset = SPU.objects.all()
    serializer_class = SPUSimpleSerializer


# GET/meiduo_admin/goods/(?P<pk>\d+)/specs/
class SPUSpecView(ListAPIView):
    """获取SPU商品的规格选项数据"""
    permission_classes = [IsAdminUser]

    # 指定视图类所使用的查询集
    def get_queryset(self):
        pk = self.kwargs['pk']
        specs = SPUSpecification.objects.filter(spu_id=pk)
        return specs

    # 指定视图类所使用的序列化器类
    serializer_class = SPUSpecSerializer



