from django.conf.urls import url

from .views import users, statistical, channels, skus, spus, orders, permissions

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
    # 频道管理
    url(r'^goods/channel_types/$', channels.ChannelTypesView.as_view()),
    # 一级分类
    url(r'^goods/categories/$', channels.ChannelCategoriesView.as_view()),

    # 图片管理
    url(r'^skus/simple/$', skus.SKUSimpleView.as_view()),

    # SKU管理
    url(r'^goods/simple/$', spus.SPUSimpleView.as_view()),
    url(r'^goods/(?P<pk>\d+)/specs/$', spus.SPUSpecView.as_view()),

    # 权限管理
    url(r'^permission/content_types/$', permissions.PermissionViewSet.as_view({
        'get': 'content_types'
    })),

    # 用户组管理
    url(r'^permission/simple/$', permissions.GroupViewSet.as_view({
        'get': 'simple'
    }))

]


from rest_framework.routers import DefaultRouter
router = DefaultRouter()
# 频道管理
router.register('goods/channels', channels.ChannelViewSet, base_name='channels')
# 图片管理
router.register('skus/images', skus.SKUImageViewSet, base_name='images')
# sku管理
router.register('skus', skus.SKUViewSet, base_name='skus')
# 订单管理
router.register('orders', orders.OrdersViewSet, base_name='orders')
# 权限管理
router.register('permission/perms', permissions.PermissionViewSet, base_name='perms')
# 用户组管理
router.register('permission/groups', permissions.GroupViewSet, base_name='groups')
urlpatterns += router.urls