def get_breadcrumb(category):
    """
    将面包屑导航进行封装，方便调用，提高复用性
    :param category: 商品分类
    :return: 面包屑导航字典
    """
    # 定义一个字典
    breadcrumb = {
        "cat1": "",
        "cat2": "",
        "cat3": ""
    }
    # 一级类别
    if category.parent is None:
        breadcrumb["cat1"] = category
    # 三级类别
    elif category.subs.count() == 0:
        breadcrumb["cat3"] = category
        breadcrumb["cat2"] = category.parent
        breadcrumb["cat1"] = category.parent.parent
    else:
        # 二级类别
        breadcrumb["cat2"] = category
        breadcrumb["cat1"] = category.parent

    return breadcrumb
