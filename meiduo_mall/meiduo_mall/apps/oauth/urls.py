from django.conf.urls import url
from . import views


urlpatterns = [
    # qq扫码登录界面
    url(r'^qq/login/$', views.QQAuthURLView.as_view()),
    # qq登录后回调界面
    url(r'^oauth_callback/$', views.QQAuthUserView.as_view()),
]