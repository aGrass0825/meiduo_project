from django import http
from django.contrib.auth.mixins import LoginRequiredMixin

from meiduo_mall.utils.response_code import RETCODE


class LoginRequiredJSONMixin(LoginRequiredMixin):
    """验证用户是否登录并返回"""
    def handle_no_permission(self):  # 重写父类LoginRequiredMixin的handle_no_permission方法，原方法返回的是redirect重定向，不满足前端的axios请求
        """响应json数据"""
        return http.JsonResponse({"code": RETCODE.SESSIONERR, "errmsg": "用户未登录"})




# 这里是原方法
# def handle_no_permission(self):
#     if self.raise_exception:
#         raise PermissionDenied(self.get_permission_denied_message())
#     return redirect_to_login(self.request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
# class LoginRequiredMixin(AccessMixin):
#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return self.handle_no_permission()