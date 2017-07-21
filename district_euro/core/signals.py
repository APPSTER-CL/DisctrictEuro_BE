from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.db import transaction
from core import models


@receiver(pre_delete, sender=models.StoreLocation)
@receiver(post_save, sender=models.StoreLocation)
def store_location_modify_handler(sender, **kwargs):
    instance = kwargs.get('instance', None)
    if instance:
        with transaction.atomic():
            countries = models.Country.objects.filter(cities__regions__region_stores__store_id=instance.store.pk).distinct()
            instance.store.countries.clear()
            instance.store.countries.add(*countries)
