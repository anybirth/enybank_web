# Generated by Django 2.0.7 on 2018-08-22 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0031_item_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservation',
            name='address_name',
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='address_name_kana',
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='zip_code',
        ),
        migrations.AddField(
            model_name='reservation',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='名'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='first_name_kana',
            field=models.CharField(blank=True, max_length=30, verbose_name='メイ'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='last_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='姓'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='last_name_kana',
            field=models.CharField(blank=True, max_length=150, verbose_name='セイ'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='zip_code1',
            field=models.CharField(blank=True, max_length=50, verbose_name='郵便番号1'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='zip_code2',
            field=models.CharField(blank=True, max_length=50, verbose_name='郵便番号2'),
        ),
    ]
