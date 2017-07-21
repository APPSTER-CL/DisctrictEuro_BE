from __future__ import unicode_literals

from django.apps import AppConfig
from core import app_settings

class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = app_settings.SITE_NAME

    def ready(self):
        ret = super(CoreConfig, self).ready()

        from core import signals

        from district_euro import settings
        from core.storage import init_connetion_pool
        init_connetion_pool(settings.S3_ACCES_KEY, settings.S3_SECRET_KEY, settings.S3_BUCKET_NAME)

        return ret
