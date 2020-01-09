from django.conf.urls import url
from . import views

urlpatterns = [
    # 对购物车进行增、删、改、查
    url(r'^carts/$', views.CartsView.as_view(), name='info'),
    # 对购物车是否全选
    url(r'^carts/selection/$', views.CartsSelectAllView.as_view()),
    # 商品右上角购物车展示
    url(r'^carts/simple/', views.CartsSimpleView.as_view()),
]
