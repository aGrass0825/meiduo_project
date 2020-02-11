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

]