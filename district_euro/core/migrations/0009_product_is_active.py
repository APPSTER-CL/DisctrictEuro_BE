# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-25 15:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_order_shipping_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Is active'),
        ),
    ]
