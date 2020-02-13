from django.conf.urls import url
from .views import users, statistical

urlpatterns = [
    url(r'^authorizations/$', users.AdminAuthView.as_view()),
    # 统计总用户量
    url(r'^statistical/total_count/$', statistical.UserTotaCountView.as_view()),
    # 统计日增用户量
    url(r'^statistical/day_increment/$', statistical.UserDayIncrementView.as_view()),
    # 统计日活跃用户量
    url(r'^statistical/day_active/$', statistical.UserDayActiveView.as_view()),
    # 统计用户下单量
    url(r'^statistical/day_orders/$', statistical.UserDayOrdersView.as_view()),
    # 统计月新增用户
    url(r'^statistical/month_increment/$', statistical.UserMonthIncrementView.as_view()),
    # 统计日商品访问量
    url(r'^statistical/goods_day_views/$', statistical.GoodsDayView.as_view()),

    # 用户管理
    url(r'^users/$', users.UserInfoView.as_view()),
]