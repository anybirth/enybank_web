# Generated by Django 2.0.7 on 2018-08-22 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0030_reservation_attachments'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='url',
            field=models.TextField(blank=True, verbose_name='商品URL'),
        ),
    ]