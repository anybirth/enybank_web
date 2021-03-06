# Generated by Django 2.0.7 on 2018-08-10 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_airline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='airline',
            name='max_total_dimensions',
            field=models.FloatField(verbose_name='最大三辺合計'),
        ),
        migrations.AlterField(
            model_name='airline',
            name='max_weight',
            field=models.FloatField(verbose_name='最大重量'),
        ),
        migrations.AlterField(
            model_name='size',
            name='max_total_dimensions',
            field=models.FloatField(blank=True, null=True, verbose_name='最大三辺合計'),
        ),
        migrations.AlterField(
            model_name='size',
            name='max_weight',
            field=models.FloatField(blank=True, null=True, verbose_name='最大重量'),
        ),
        migrations.AlterField(
            model_name='size',
            name='min_total_dimensions',
            field=models.FloatField(verbose_name='最小三辺合計'),
        ),
        migrations.AlterField(
            model_name='size',
            name='min_weight',
            field=models.FloatField(verbose_name='最小重量'),
        ),
    ]
