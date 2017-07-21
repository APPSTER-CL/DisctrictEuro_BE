# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-13 13:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_auto_20160912_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Image', verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='city',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cities', to='core.Country', verbose_name='Country'),
        ),
        migrations.AlterField(
            model_name='region',
            name='city',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regions', to='core.City', verbose_name='City'),
        ),
    ]