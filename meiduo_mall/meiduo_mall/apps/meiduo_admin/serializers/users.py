import re

from django.utils import timezone

from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from users.models import User


class AdminAuthSerializer(serializers.ModelSerializer):
    """管理员登录序列化器类"""
    token = serializers.CharField(label='jwt token', read_only=True)
    username = serializers.CharField(label='用户名')

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'token')

        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def validate(self, attrs):
        # 校验用户名密码是否正确
        username = attrs['username']
        password = attrs['password']

        try:
            user = User.objects.get(username=username, is_staff=True)  # is_staff=True 判断是否是管理员登录
        except User.DoesNotExist:
            raise serializers.ValidationError('用户名或密码错误')
        else:
            # 校验密码是否正确
            if not user.check_password(password):
                raise serializers.ValidationError('用户名或密码错误')
            # 给attrs添加user
            attrs['user'] = user
        return attrs

    def create(self, validated_data):
        # 获取user
        user = validated_data.get('user')

        # 更新管理员的登录时间
        now_time = timezone.now()
        User.last_login = now_time
        user.save()

        # 创建jwt token保存登录用户身份信息
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 给user对象增加属性token,保存jwt token
        user.token = token
        return user


class UserInfoSerializer(serializers.ModelSerializer):
    """用户序列化器类"""
    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'password')

        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    # 在序列化器类中定义特定方法validate_<field_name>，针对特定字段进行补充验证
    def validate_mobile(self, value):
        # 手机号格式校验
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        # 手机号是否注册
        count = User.objects.filter(mobile=value).count()
        if count > 0:
            raise serializers.ValidationError('手机号已注册')
        return value

    def create(self, validated_data):
        # 保存用户数据，默认create不会对密码进行加密保存故重写
        user = User.objects.create_user(**validated_data)
        return user