from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from meiduo_admin.serializers.permissions import PermissionSerializer, ContentTypeSerializer, GroupSerializer, \
    PermSimpleSerializer
from meiduo_admin.utils.pagination import StandardResultPagination


class PermissionViewSet(ModelViewSet):
    """权限类"""
    permission_classes = [IsAdminUser]
    # 指定当前视图所使用的分页类(局部)
    pagination_class = StandardResultPagination
    # 指定router动态生成路由时，提取参数的正则表达式
    lookup_value_regex = '\d+'

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    # GET /meiduo_admin/permission/content_types/
    # 这里不能用@action()方法自动帮我们注册，
    # 因为@action()生成的url是/meiduo_admin/permission/perms/content_types/
    def content_types(self, request):
        """获取权限内容类型的数据"""
        # 1查询获取所有权限内容类型的数据
        instance = ContentType.objects.all()
        # 2将权限内容类型数据序列化并返回
        serializer = ContentTypeSerializer(instance, many=True)
        return Response(serializer.data)


class GroupViewSet(ModelViewSet):
    """用户组类"""
    permission_classes = [IsAdminUser]
    # 指定当前视图所使用的分页类(局部)
    pagination_class = StandardResultPagination
    # 指定router动态生成路由时，提取参数的正则表达式
    lookup_value_regex = '\d+'

    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    # GET /meiduo_admin/permission/simple/
    # 不能使用@action()注册，因为@action()生成的url是
    # GET /meiduo_admin/permission/groups/simple/
    def simple(self, request):
        """获取权限的简单数据"""
        # 1查询获取所有的权限数据
        qureyset = Permission.objects.all()
        # 2将权限数据序列化并返回
        serializer = PermSimpleSerializer(qureyset, many=True)
        return Response(serializer.data)