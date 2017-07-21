# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-05 15:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20160805_1204'),
    ]

    operations = [
        migrations.AddField(
            model_name='productunit',
            name='attributes',
            field=models.ManyToManyField(blank=True, to='core.AttributeValue', verbose_name='Product Attributes'),
        ),
    ]
