# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-24 08:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0003_auto_20171215_2127'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='tags',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
