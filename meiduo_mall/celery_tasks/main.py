# celery启动入口
import os
from celery import Celery


# 为celery使用django配置文件进行设置
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ["DJANGO_SETTINGS_MODULE"] = "meiduo_mall.settings.dev"

# 创建celery实例  生产者
celery_app = Celery("meiduo")

# 加载配置  中间人
celery_app.config_from_object("celery_tasks.config")

# 自动注册celery任务  消费者
celery_app.autodiscover_tasks(["celery_tasks.sms", "celery_tasks.email"])
