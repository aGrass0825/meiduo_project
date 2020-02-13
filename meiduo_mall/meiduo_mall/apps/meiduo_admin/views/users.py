from django.db.models import Q
from rest_framework import status
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView, ListAPIView, ListCreateAPIView

from meiduo_admin.serializers.users import AdminAuthSerializer, UserInfoSerializer
from meiduo_admin.utils.pagination import StandardResultPagination
from users.models import User


class AdminAuthView(CreateAPIView):
    # 指定视图所使用的序列化器类
    serializer_class = AdminAuthSerializer

    # def post(self, request):
    #     """
    #     管理员登录
    #     :param request:
    #     :return:
    #     """
    #     # 使用序列化器
    #     serializer = AdminAuthSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #
    #     # 创建jwt token保存登录用户的身份信息
    #     serializer.save()  # 调用序列化器类create
    #
    #     # 返回响应数据
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)


# GET /meiduo_admin/users/?page=1&pagesize=10&keyword=
class UserInfoView(ListCreateAPIView):
    # 只有管理员才能访问
    permission_classes = [IsAdminUser]
    # 指定当前视图所使用的分页类(局部)
    pagination_class = StandardResultPagination

    serializer_class = UserInfoSerializer

    def get_queryset(self):
        # 1.查询获取普通用户的数据 query_params方法返回是request.GET
        keyword = self.request.query_params.get('keyword')
        # if keyword:
        #     # 1.有keyword，根据用户名查询用户含有keyword的普通用户
        #     users = User.objects.filter(username__contains=keyword, is_staff=False)
        # else:
        #     # 2.没有keyword，查询所有的普通用户
        #     users = User.objects.filter(is_staff=False)
        users = User.objects.filter(is_staff=False)
        if keyword:
            users = users.filter(Q(username__contains=keyword) | Q(mobile__contains=keyword))
        return users

    # def get(self, request):
    #     return self.list(request)

    # def get(self, request):
    #     """
    #     获取网站的普通用户的数据
    #     :param request:
    #     :return:
    #     """
    #     users = self.get_queryset()
    #     # 2.将普通用户数据序列化并返回
    #     serializer = self.get_serializer(users, many=True)
    #     return Response(serializer.data)

    # POST /meiduo_admin/users/
    # def post(self, request):
    #     """
    #     保存新增用户的数据
    #     :param request:
    #     :return:
    #     """
    #     # 1.获取参数并进行校验
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     # 2.保存新增用户的数据
    #     serializer.save()
    #     # 3.将新增用户的数据序列化并返回
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    # def post(self, request):
    #     return self.create(request)