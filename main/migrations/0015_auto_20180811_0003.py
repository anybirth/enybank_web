# Generated by Django 2.0.7 on 2018-08-11 00:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_item_weight'),
    ]

    operations = [
        migrations.AlterField(
            model_name='airline',
            name='name',
            field=models.CharField(max_length=50, verbose_name='航空会社名'),
        ),
    ]
