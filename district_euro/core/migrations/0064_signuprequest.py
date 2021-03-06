# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-08 19:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0063_auto_20161108_1910'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignUpRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
            ],
            options={
                'ordering': ('-id',),
                'verbose_name': 'Sign Up Request',
                'verbose_name_plural': 'Sign Up Requests',
            },
        ),
    ]
