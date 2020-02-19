from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from goods.models import GoodsChannel, GoodsChannelGroup, GoodsCategory
from meiduo_admin.serializers.channels import ChannelSerializer, ChannelTypeSerializer, ChannelCategorySerializer
from meiduo_admin.utils.pagination import StandardResultPagination


# GET /meiduo_admin/goods/channels/?page=<页码>&page_size=<页容量>


class ChannelViewSet(ModelViewSet):
    """频道管理视图集"""
    permission_classes = [IsAdminUser]
    # 指定当前视图所使用的分页类(局部)
    pagination_class = StandardResultPagination
    # 指定视图所使用的查询集
    queryset = GoodsChannel.objects.all()

    # 指定序列化器类
    serializer_class = ChannelSerializer


# GET /meiduo_admin/goods/channel_types/
class ChannelTypesView(ListAPIView):
    """
    获取所有频道组数据
    """
    permission_classes = [IsAdminUser]
    # 指定视图所使用的查询集
    queryset = GoodsChannelGroup.objects.all()
    # 指定视图所使用的序列化器类
    serializer_class = ChannelTypeSerializer

    # def get(self,request):
    #   return self.list(request)
    # def get(self, request):
    #     # 1.查询获取所有的频道数据
    #     group = self.get_queryset()
    #
    #     # 2.将频道组的数据序列化并返回
    #     serializer = self.get_serializer(group, many=True)
    #     return Response(serializer.data)


# GET /meiduo_admin/goods/categories/
class ChannelCategoriesView(ListAPIView):
    """获取一级分类数据"""
    permission_classes = [IsAdminUser]

    queryset = GoodsCategory.objects.filter(parent=None)
    serializer_class = ChannelCategorySerializer



