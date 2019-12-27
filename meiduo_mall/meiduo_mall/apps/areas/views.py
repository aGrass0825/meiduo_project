import logging

from django.core.cache import cache
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render

from meiduo_mall.utils.response_code import RETCODE
from areas.models import Area
# Create your views here.
#创建日志输出器
logger = logging.getLogger("django")


class AreasView(View):
    """省市区三级联动"""
    def get(self, request):
        """

        :param request:
        :return:
        """
        # 接收参数
        area_id = request.GET.get("area_id")
        # 校验参数 实现业务逻辑
        if area_id is None:
            """提供省级数据"""
            # 读取省份缓存数据
            province_list = cache.get('province_list')
            if province_list is None:
                try:
                    # 查询省级数据
                    province_model_list = Area.objects.filter(parent__isnull=True)
                    province_list = []
                    for province_model in province_model_list:  # 遍历Area模型类对象
                        dcit = {
                            "id": province_model.id,  # 模型对象打点字段名调用
                            "name": province_model.name
                        }
                        province_list.append(dcit)
                        # 存储省份缓存数据
                        cache.set('province_list', province_list, 3600)
                except Exception as e:
                    logger.error(e)
                    return JsonResponse({"code": RETCODE.DBERR, "errmsg": "省级数据错误"})
            return JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "province_list": province_list})

        else:
            """提供市区级数据"""
            sub_list = cache.get('sub_area_')
            if sub_list is None:
                try:
                    # 查询市区级数据
                    parent_model = Area.objects.get(id=area_id)  # 查询市或区的父级
                    sub_model_list = parent_model.subs.all()  # 一对多查询 related_name="subs"
                    subs = []
                    for sub_model in sub_model_list:
                        dcit = {
                            "id": sub_model.id,
                            "name": sub_model.name
                        }
                        subs.append(dcit)
                    sub_data = {
                        "id": parent_model.id,
                        "name": parent_model.name,
                        "subs": subs
                    }
                    # 存储市区级数据
                    cache.set('sub_area_' + area_id, sub_data, 3600)
                except Exception as e:
                    logger.error(e)
                    return JsonResponse({"code": RETCODE.DBERR, "errmsg": "城市或区数据错误"})
            return JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "sub_data": sub_data})


