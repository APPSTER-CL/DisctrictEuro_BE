# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-10 13:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20160810_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='sample',
            name='showrooms',
            field=models.ManyToManyField(blank=True, related_name='samples', to='core.Showroom', verbose_name='Showrooms'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='warehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Warehouse', verbose_name='Warehouse'),
        ),
    ]
