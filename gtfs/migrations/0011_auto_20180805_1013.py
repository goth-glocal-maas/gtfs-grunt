# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-05 03:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gtfs', '0010_auto_20180605_2207'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stoptime',
            options={'ordering': ['sequence'], 'verbose_name_plural': 'Stop times'},
        ),
        migrations.AlterModelOptions(
            name='trip',
            options={'ordering': ('trip_id',)},
        ),
        migrations.AlterField(
            model_name='farerule',
            name='route',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gtfs.Route'),
        ),
    ]
