from django.conf.urls import url
from .views import users

urlpatterns = [
    url(r'authorizations/$', users.AdminAuthView.as_view())

]