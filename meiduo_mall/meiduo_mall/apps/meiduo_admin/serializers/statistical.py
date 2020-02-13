from rest_framework import serializers

from goods.models import GoodsVisitCount


class GoodsVisitSerializer(serializers.ModelSerializer):
    """日分类商品访问量序列化器类"""
    category = serializers.StringRelatedField(label='分类名称')

    class Meta:
        model = GoodsVisitCount
        fields = ('category', 'count')
