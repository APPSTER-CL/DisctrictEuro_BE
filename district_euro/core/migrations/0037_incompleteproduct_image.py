# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-12 13:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_auto_20160912_1004'),
    ]

    operations = [
        migrations.AddField(
            model_name='incompleteproduct',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Image', verbose_name='Main image'),
        ),
    ]
