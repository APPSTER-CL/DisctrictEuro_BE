# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-14 17:23
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0042_auto_20160914_1110'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='amount_reviews',
            field=models.IntegerField(default=0, verbose_name='Amount of reviews of this product'),
        ),
        migrations.AddField(
            model_name='product',
            name='mean_qualification',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)], verbose_name='Mean Review Qualification'),
        ),
    ]
