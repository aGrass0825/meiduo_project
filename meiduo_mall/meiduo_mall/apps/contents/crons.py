# 静态化首页
from collections import OrderedDict

from contents.utils import get_categories
from contents.models import ContentCategory


def generate_static_index_html():
    """生成静态主页html"""
    # 查询首页数据
    categories = get_categories()  # 调用商品分类方法
    # 广告数据
    contents = OrderedDict()
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.category.filter(status=True).order_by('sequence')  # related_name='category'

    # 渲染到模板
    context = {
        "categories": categories,
        "contents": contents
    }

    # 获取首页模板


    # 渲染首页模板字符串
