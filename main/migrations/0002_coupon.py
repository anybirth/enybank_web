# Generated by Django 2.0.6 on 2018-08-03 11:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import main.models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('coupon_code', models.CharField(default=main.models.Coupon.generate_coupon_code, max_length=50, unique=True, verbose_name='クーポンコード')),
                ('discount', models.IntegerField(verbose_name='割引額')),
                ('status', models.SmallIntegerField(default=0, verbose_name='ステータス')),
                ('description', models.TextField(blank=True, verbose_name='備考')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='作成日時')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新日時')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='ユーザー')),
            ],
            options={
                'verbose_name': 'クーポン',
                'verbose_name_plural': 'クーポン',
                'db_table': 'coupons',
                'ordering': ['-created_at'],
            },
        ),
    ]
