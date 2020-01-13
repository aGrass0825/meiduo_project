from django.db import models

# Create your models here.
from meiduo_mall.utils.models import BaseModel
from orders.models import OrderInfo


class Payment(BaseModel):
    """创建支付信息表 保存支付宝订单号与美多商城订单号"""
    order = models.ForeignKey(OrderInfo, on_delete=models.CASCADE, verbose_name='订单')  # 自动添加_id
    trade_id = models.CharField(max_length=100, unique=True, null=True, blank=True, verbose_name='支付编号')

    class Meta:
        db_table = 'tb_payment'
        verbose_name = '支付信息'
        verbose_name_plural = verbose_name
