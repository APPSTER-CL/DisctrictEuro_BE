# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-19 14:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20160715_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='images',
            field=models.ManyToManyField(blank=True, to='core.Image', verbose_name='Images'),
        ),
        migrations.AlterField(
            model_name='category',
            name='super_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcategoires', to='core.Category', verbose_name='Parent Category'),
        ),
    ]