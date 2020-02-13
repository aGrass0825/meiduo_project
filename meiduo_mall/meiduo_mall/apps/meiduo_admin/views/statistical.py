from django.utils import timezone

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from goods.models import GoodsVisitCount
from meiduo_admin.serializers.statistical import GoodsVisitSerializer
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
        # 一模型类关联属性名(ordes)__一模型类属性名(create_time)__条件运算符(gte)=值
        count = User.objects.filter(orders__create_time__gte=now_date).distinct().count()  # distinct()能去掉重复的用户

        # 2.返回响应结果
        response_data = {
            'count': count,
            'date': now_date.date()
        }
        return Response(response_data)


# GET /meiduo_admin/statistical/month_increment/
class UserMonthIncrementView(APIView):
    # 只有管理员才能访问
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        统计月新增用户
        :param request:
        :return:
        """
        # 1.查询数据库统计网站最近30天每日新增的用户数量
        # 结束时间
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # 起始时间 当前天时间-29天得到的是一个月的时间
        begin_date = now_date - timezone.timedelta(days=29)
        # 起始日期
        current_date = begin_date

        # 新增用户数量
        month_list = []
        while current_date <= now_date:
            # 次日时间
            next_date = current_date + timezone.timedelta(days=1)
            # 统计每天的新增用户数
            count = User.objects.filter(date_joined__gte=current_date,
                                        date_joined__lt=next_date).count()

            # 追加统计
            month_list.append({
                'count': count,
                'date': current_date.date()
            })
            current_date += timezone.timedelta(days=1)

        # 2.返回响应结果
        return Response(month_list)


# GET /meiduo_admin/statistical/goods_day_views/
class GoodsDayView(ListAPIView):
    # 只有管理员才能访问
    permission_classes = [IsAdminUser]

    # 指定所使用的序列化器类
    serializer_class = GoodsVisitSerializer
    # 获取日商品访问量数据
    def get_queryset(self):
        now_date = timezone.now().date()
        queryset = GoodsVisitCount.objects.filter(date=now_date)
        return queryset


    # def get(self, request):
    #     """
    #     获取日商品访问量数据
    #     :param request:
    #     :return:
    #     """
    #     # 1.查询数据库日商品访问量
    #     now_date = timezone.now().date()
    #     goods_visits = GoodsVisitCount.objects.filter(date=now_date)
    #
    #     # 2.返回响应数据
    #     serializer = GoodsVisitSerializer(goods_visits, many=True)
    #     return Response(serializer.data)