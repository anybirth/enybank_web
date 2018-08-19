# Generated by Django 2.0.7 on 2018-08-19 18:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_reservation_region'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='series',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='main.Series', verbose_name='シリーズ'),
        ),
    ]
