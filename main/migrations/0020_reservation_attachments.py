# Generated by Django 2.0.7 on 2018-08-17 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_attachment'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='attachments',
            field=models.ManyToManyField(blank=True, db_table='reservations_attachments', to='main.Attachment', verbose_name='付属品'),
        ),
    ]
