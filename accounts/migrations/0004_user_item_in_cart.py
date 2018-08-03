# Generated by Django 2.0.6 on 2018-08-03 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
        ('accounts', '0003_auto_20180802_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='item_in_cart',
            field=models.ManyToManyField(related_name='item_in_cart_set', to='main.Item', verbose_name='カート内のアイテム'),
        ),
    ]