# 静态化首页
import os

from django.conf import settings
from django.template import loader

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

    # 构造上下文
    context = {
        "categories": categories,
        "contents": contents
    }

    # 获取首页模板　渲染模板
    template = loader.get_template('index.html')
    # 使用上下文渲染模板文件
    html_text = template.render(context)

    # 将模板文件写入到静态路径
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8') as es:
        es.write(html_text)
