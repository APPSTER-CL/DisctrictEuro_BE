# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-21 14:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0046_order_date_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='country',
            name='in_app',
            field=models.BooleanField(default=True, verbose_name='If this country is shown in the app'),
        ),
    ]