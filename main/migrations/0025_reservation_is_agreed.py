# Generated by Django 2.0.7 on 2018-08-19 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0024_auto_20180819_1826'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='is_agreed',
            field=models.BooleanField(default=False, verbose_name='規約同意'),
        ),
    ]
