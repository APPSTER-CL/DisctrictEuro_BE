# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-07 15:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_auto_20161007_1115'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnapprovedProduct',
            fields=[
            ],
            options={
                'verbose_name': 'Product Unapproved',
                'proxy': True,
                'verbose_name_plural': 'Products Unapproved',
            },
            bases=('core.product',),
        ),
    ]