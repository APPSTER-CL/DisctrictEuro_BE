# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-28 13:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_auto_20160927_1529'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sampledispatch',
            old_name='showroom',
            new_name='showrooms',
        ),
        migrations.AlterField(
            model_name='sample',
            name='updated',
            field=models.DateTimeField(auto_now=True, verbose_name='Last Updated'),
        ),
    ]
