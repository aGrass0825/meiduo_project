from django.db import transaction
from rest_framework import serializers

from goods.models import SKUImage, SKU, SKUSpecification, SPU, SpecificationOption


class SKUImageSerializer(serializers.ModelSerializer):
    """sku图片序列化器类"""
    sku = serializers.StringRelatedField(label='SKU商品名称')
    sku_id = serializers.IntegerField(label='SKU商品ID')

    class Meta:
        model = SKUImage
        exclude = ('create_time', 'update_time')

    def validate_sku_id(self, value):
        # 校验sku商品是否存在
        try:
            sku = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('sku商品不存在')
        return value

    def create(self, validated_data):
        # 添加图片
        sku_image = super().create(validated_data)
        # 设置默认图片
        sku = sku_image.sku
        if not sku.default_image:
            sku.default_image = sku_image.image
            sku.save()
        return sku_image


class SKUSimpleSerializer(serializers.ModelSerializer):
    """sku商品序列化器类"""
    class Meta:
        model = SKU
        fields = ('id', 'name')


class SKUSpecSerializer(serializers.ModelSerializer):
    """sku具体规格序列化器类"""
    spec_id = serializers.IntegerField(label='规格id')
    option_id = serializers.IntegerField(label='选项id')

    class Meta:
        model = SKUSpecification
        fields = ('spec_id', 'option_id')


class SKUSerializer(serializers.ModelSerializer):
    """sku商品序列化器类"""
    spu_id = serializers.IntegerField(label='SPU_ID')
    # 关联对象的嵌套序列化
    specs = SKUSpecSerializer(label='具体规格', many=True)
    category = serializers.StringRelatedField(label='分类')

    class Meta:
        model = SKU
        exclude = ('create_time', 'update_time', 'spu', 'comments', 'default_image')

        extra_kwargs = {
            'sales': {
                'read_only': True
            }
        }

    def validate(self, attrs):
        # 1.spu是否存在
        spu_id = attrs['spu_id']
        try:
            spu = SPU.objects.get(id=spu_id)
        except SPU.DoesNotExist:
            raise serializers.ValidationError('SPU不存在')
        # 2.spu的规格数据是否合法
        # 2-1.数据是否合法
        specs = attrs['specs']
        spu_specs = spu.specs.all()
        specs_count = len(specs)
        spu_specs_count = spu_specs.count()
        if specs_count != spu_specs_count:
            raise serializers.ValidationError('规格数据有误')

        # 2-2.数据是否合法
        spec_id = [spec.get('spec_id') for spec in specs]
        spu_spec_ids = [spu_spec.id for spu_spec in spu_specs]

        spec_id.sort()
        spu_spec_ids.sort()

        if spec_id != spu_spec_ids:
            raise serializers.ValidationError('规格数据有误')

        # 3.规格选项是否合法
        for spec in specs:
            spec_id = spec.get('spec_id')
            option_id = spec.get('option_id')
            # 检查spec_id对应的规格是否包含option_id对应的选项
            options = SpecificationOption.objects.filter(spec_id=spec_id)
            options_ids = [option.id for option in options]

            if option_id not in options_ids:
                raise serializers.ValidationError('规格选项数据有误')

        # attrs中添加第三级分类ID
        attrs['category_id'] = spu.category3.id

        return attrs

    def create(self, validated_data):
        """保存sku商品数据"""
        specs = validated_data.pop('specs')
        # 事务的使用
        with transaction.atomic():
            # 新增sku商品
            sku = SKU.objects.create(**validated_data)

            # 保存商品规格信息
            for spec in specs:
                SKUSpecification.objects.create(
                    sku=sku,
                    spec_id=spec.get('spec_id'),
                    option_id=spec.get('option_id')
                )

        return sku

    def update(self, instance, validated_data):
        """修改sku商品数据"""
        specs = validated_data.pop('specs')
        with transaction.atomic():
            # 1.更新sku的数据
            super().update(instance, validated_data)
            # 2.更新sku规格信息的数据
            instance.specs.all().delete()
            for spec in specs:
                spec_id = spec.get('spec_id')
                option_id = spec.get('option_id')

                SKUSpecification.objects.create(
                    sku=instance,
                    spec_id=spec_id,
                    option_id=option_id
                )
        return instance


