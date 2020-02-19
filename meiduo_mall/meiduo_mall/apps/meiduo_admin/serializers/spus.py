from rest_framework import serializers

from goods.models import SPU, SPUSpecification, SpecificationOption


class SPUSimpleSerializer(serializers.ModelSerializer):
    """spu序列化器类"""
    class Meta:
        model = SPU
        fields = ('id', 'name')


class SpecOptionSerializer(serializers.ModelSerializer):
    """规格选项序列化器类"""
    class Meta:
        model = SpecificationOption
        fields = ('id', 'value')


class SPUSpecSerializer(serializers.ModelSerializer):
    """SPU规格序列化器类"""
    options = SpecOptionSerializer(label='规格选项', many=True)

    class Meta:
        model = SPUSpecification
        fields = ('id', 'name', 'options')
