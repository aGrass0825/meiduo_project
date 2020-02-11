from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from meiduo_admin.serializers.users import AdminAuthSerializer


class AdminAuthView(APIView):
    def post(self, request):
        """
        管理员登录
        :param request:
        :return:
        """
        # 使用序列化器
        serializer = AdminAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 创建jwt token保存登录用户的身份信息
        serializer.save()  # 调用序列化器类create

        # 返回响应数据
        return Response(serializer.data, status=status.HTTP_201_CREATED)