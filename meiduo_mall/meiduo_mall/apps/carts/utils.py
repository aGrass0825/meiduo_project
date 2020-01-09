import base64, pickle
from django_redis import get_redis_connection


def merge_carts_cookie_to_redis(request, user, response):
    """合并购物车"""
    # 获取cookie中的数据
    carts_str = request.COOKIES.get('carts')
    # 判断cookie是否存在
    if not carts_str:
        # 如果不存在，则不需要合并
        return response
    # 将carts_str转换成正真的字典
    carts_dict = pickle.loads(base64.b64decode(carts_str.encode()))
    # 准备容器存储
    new_cart_dict = {}
    new_cart_select_sadd = []
    new_cart_select_srem = []
    # 遍历出cookie中的数据
    for sku_id, cart_dict in carts_dict.items():
        # 将count数量添加到新字典中
        new_cart_dict[sku_id] = cart_dict['count']
        if cart_dict['selected']:
            # 勾选时
            new_cart_select_sadd.append(sku_id)
        else:
            # 未勾选时
            new_cart_select_srem.append(sku_id)
    # 将新的数据结构合并到redis中
    redis_conn = get_redis_connection('carts')
    # 优化
    pl = redis_conn.pipeline()
    pl.hmset('carts_%s' % user.id, new_cart_dict)
    # 勾选时
    if new_cart_select_sadd:
        pl.sadd('selected_%s' % user.id, *new_cart_select_sadd)
    # 未勾选时
    if new_cart_select_srem:
        pl.srem('selected_%s' % user.id, *new_cart_select_srem)
    pl.execute()
    # 清除cookie中购物车数据
    response.delete_cookie('carts')
    return response
