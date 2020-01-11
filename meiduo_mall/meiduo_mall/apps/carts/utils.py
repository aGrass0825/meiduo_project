import base64, pickle
from django_redis import get_redis_connection
from .views import CartMixin


def merge_carts_cookie_to_redis(request, user, response):
    """合并购物车"""
    # 获取cookie中的购物车数据（调用CartMixin扩展类）
    tools = CartMixin()
    # 获取redis购物车
    redis_cart = tools.read_redis_cart(user.id)
    # 获取cookie购物车
    cookie_cart = tools.read_cookie_cart(request)
    # 合并购物车
    redis_cart.update(cookie_cart)
    # 写入redis购物车
    tools.write_redis_cart(user.id, redis_cart)
    # 删除cookie购物车
    response.delete_cookie("CART")
    return response


# 装饰器，装饰合并购物车  在注册、qq登录、qq第一次登录绑定、用户登录
def afer_login(func):
    def wrapper(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        user = request.user
        if user and user.is_authenticated:
            merge_carts_cookie_to_redis(request, user, response)

        return response

    return wrapper
