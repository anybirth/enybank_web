# Generated by Django 2.0.7 on 2018-08-19 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0025_reservation_is_agreed'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='text',
            field=models.TextField(blank=True, verbose_name='商品詳細'),
        ),
        migrations.AlterField(
            model_name='item',
            name='description',
            field=models.TextField(blank=True, verbose_name='商品概要'),
        ),
    ]
