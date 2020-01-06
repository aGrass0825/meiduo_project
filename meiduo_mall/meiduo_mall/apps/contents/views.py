from collections import OrderedDict
from django.shortcuts import render
from django.views import View

from contents.models import ContentCategory
from contents.utils import get_categories


# Create your views here.


class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页广告界面"""
        categories = get_categories()  # 调用商品分类方法
        # 广告数据
        contents = OrderedDict()
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.category.filter(status=True).order_by('sequence')  # related_name='category'

        context = {
            "categories": categories,
            "contents": contents
        }

        return render(request, 'index.html', context)
