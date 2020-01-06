import logging
from datetime import datetime
from django.utils import timezone
from django.views import View
from django import http
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage

from goods.models import GoodsCategory, SKU, GoodsVisitCount
from contents.utils import get_categories
from goods.utils import get_breadcrumb
from goods import constants
from meiduo_mall.utils.response_code import RETCODE

# Create your views here.
logger = logging.getLevelName('django')


class DetailVisitView(View):
    """详情分页访问量"""

    def post(self, request, category_id):
        """

        :param request:
        :param category_id: 商品id
        :return:
        """
        # 接收参数 # 校验参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('参数不存在')
            # 业务逻辑
            # 获取时间
        t = timezone.localtime()
        today_str = '%d-%02d-%02d' % (t.year, t.month, t.day)
        # strptime是将字符串转换成时间
        # strftime是将时间转换成字符串
        today_date = datetime.strptime(today_str, '%Y-%m-%d')
        # 响应结果
        try:
            # 查询数据库商品访问量是否存在
            # counts_data = category.goodesvisitcount_set.get(date=today_date)
            counts_data = GoodsVisitCount.objects.get(date=today_date, category=category)
        except GoodsVisitCount.DoesNotExist:
            # 不存在访问记录则添加记录
            counts_data = GoodsVisitCount()
        # 操作sql
        try:
            counts_data.category = category
            counts_data.count += 1
            counts_data.date = today_date
            counts_data.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('保存失败')
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DetailView(View):
    """商品详情页"""

    def get(self, request, sku_id):
        """提供商品详情界面"""
        # 解收参数 # 校验参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')
        # 实现业务逻辑
        # 1.实现商品分类
        categories = get_categories()
        # 2.实现面包屑导航
        breadcrumb = get_breadcrumb(sku.category)

        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options
        # 3.构造上下文
        context = {
            "categories": categories,
            "breadcrumb": breadcrumb,
            "sku": sku,
            "specs": goods_specs
        }
        # 响应结果
        return render(request, 'detail.html', context)


class HotGoodsView(View):
    """热销排行榜"""

    def get(self, request, category_id):
        """
        热销商品排行榜
        :param request:
        :param category_id: 商品id 三级分类
        :return:
        """
        # 接收参数
        # 校验参数
        # 业务逻辑
        skus = SKU.objects.filter(category_id=category_id, is_launched=True).order_by('-sales')[:2]
        hot_skus = []
        for sku in skus:
            context = {
                "id": sku.id,
                "name": sku.name,
                "price": sku.price,
                "default_image_url": sku.default_image.url
            }
            hot_skus.append(context)
        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class ListView(View):
    """商品列表页"""

    def get(self, request, category_id, page_num):
        """
        查询商品列表并渲染
        :param request:
        :return:
        """
        try:
            # 三级分类(前端已经给出了category_id三级分类)
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('参数category_id不存在')
        # 调用商品分类封装好的方法
        categories = get_categories()
        # 查询面包屑导航 (不能满足url的要求)
        # breadcrumb = {
        #     "cat1": category.parent.parent,  # 一级分类
        #     "cat2": category.parent,         # 二级分类
        #     "cat3": category                 # 三级分类
        # }
        # 调用查询面包屑导航方法
        breadcrumb = get_breadcrumb(category)
        sort = request.GET.get('sort', 'default')  # 表示如果'sort'不存在就取'default'
        if sort == 'price':
            sort_field = 'price'
        elif sort == 'hot':
            sort_field = '-sales'  # 销量对应着热度 倒序排序
        else:
            sort = 'default'  # 防止用户乱输入排序方式发送请求 将default赋值给sort
            sort_field = 'create_time'  # 创建时间为默认 时间越新排前
        cat1 = breadcrumb['cat1']
        channel = cat1.goodschannel_set.get()
        # channel = category.parent.parent.goodschannel_set.get() # 一对多访问 用一级分类
        cat1.url = channel.url
        # 分页查询和排序
        # 一对多访问  一对应的模型类对象.多对应的模型类名小写_set
        skus = category.sku_set.filter(is_launched=True).order_by(sort_field)

        # 创建分页器，每页n条记录
        paginator = Paginator(skus, constants.GOODS_LIST_LIMIT)
        try:
            # 获取当前用户要看的那一页
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseNotFound('不存在')
        total_page = paginator.num_pages  # 对象调用num_pages(总页数)方法

        context = {
            "categories": categories,
            "breadcrumb": breadcrumb,
            "sort": sort,
            "page_skus": page_skus,
            "total_page": total_page,
            "page_num": page_num,
            "category_id": category_id
        }

        return render(request, "list.html", context)  # 用jinjao2模板引擎后端渲染好发给前端展示
