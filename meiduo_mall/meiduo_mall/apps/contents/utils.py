from collections import OrderedDict

from goods.models import GoodsChannel


def get_categories():
    """
    将商品分类进行封装
    :return:
    """
    # 查询商品频道和分类
    # categories = {} 直接定义空字典是无序的，而python在3.6版本以上字典才默认为有序
    categories = OrderedDict()  # ordereddict是有序字典
    # channels = GoodsChannel.objects.all()  这样写没有排序
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')  # 返回的是模型集
    for channel in channels:
        # 取出模型集中的当前单个的id
        group_id = channel.group_id
        if group_id not in categories:  # 频道组只有11组，这里判断保证的只有11组频道
            categories[group_id] = {"channels": [], "sub_cats": []}

        cat1 = channel.category  # 当前频道的商品类别（外键）
        # categories[group_id]["channels"].append(cat1)  由于前端需求三个信息id\name\url。而url不在cat1里只能构造字典
        categories[group_id]["channels"].append({
            "id": cat1.id,
            "name": cat1.name,
            "url": channel.url
        })
        cat1_1 = cat1.subs.all()  # related_name='subs' (一查多 自关联查询)
        for cat2 in cat1_1:
            cat2.sub_cats = []
            cat2_2 = cat2.subs.all()
            for cat3 in cat2_2:
                cat2.sub_cats.append(cat3)
            categories[group_id]["sub_cats"].append(cat2)

    return categories
