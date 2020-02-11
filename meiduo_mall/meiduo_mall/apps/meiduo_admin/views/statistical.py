from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from users.models import User


# GET /meiduo_admin/statistical/total_count/
class UserTotaCountView(APIView):
    # 只有管理员才能进行访问
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        统计网站的总用户数
        :param request:
        :return:
        """
        # 1.查询数据统计网站的总用户数
        count = User.objects.count()

        # 2.返回响应的数据
        now_date = timezone.now()  # 返回的是年－月－日　时－分－秒

        response_data = {
            "count": count,
            "date": now_date.date()  # now_date.date()返回的是年－月－日
        }
        return Response(response_data)


# GET /meiduo_admin/statistical/day_increment/
class UserDayIncrementView(APIView):
    # 只有管理员才能访问
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        统计日增用户量
        :param request:
        :return:
        """
        # 1.查询数据库统计网站的日增用户数
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(date_joined__gte=now_date).count()

        # 2.返回响应结果
        response_data = {
            'count': count,
            'date': now_date.date()
        }
        return Response(response_data)


# GET /meiduo_admin/statistical/day_active/
class UserDayActiveView(APIView):
    # 只有管理员才能访问
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        统计日活跃用户数
        :param request:
        :return:
        """
        # 1.查询数据库日活跃用户数
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(last_login__gte=now_date).count()

        # 2.返回响应结果
        response_data = {
            'count': count,
            'date': now_date.date()
        }
        return Response(response_data)

# GET /meiduo_admin/statistical/day_orders/
class UserDayOrdersView(APIView):
    # 只有管理员才能访问
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        统计下单人数
        :param request:
        :return:
        """
        # 1.查询数据库日下单用户数量
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(orders__create_time__gte=now_date).distinct().count()

        # 2.返回响应结果
        response_data = {
            'count': count,
            'date': now_date.date()
        }
        return Response(response_data)
