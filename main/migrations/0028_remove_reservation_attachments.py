# Generated by Django 2.0.7 on 2018-08-22 12:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0027_auto_20180819_2224'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservation',
            name='attachments',
        ),
    ]