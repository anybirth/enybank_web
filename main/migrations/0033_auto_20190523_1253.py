# Generated by Django 2.2.1 on 2019-05-23 12:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0032_auto_20180822_1815'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='cart',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='main.Cart', verbose_name='カート'),
        ),
    ]