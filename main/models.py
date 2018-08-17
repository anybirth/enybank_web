import os
import uuid
import random
from enum import Enum
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.

def get_image_path(instance, filename):
    name = str(uuid.uuid4()).replace('-', '')
    extension = os.path.splitext(filename)[-1]
    return name + extension


class UUIDModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Region(UUIDModel):
    order = models.SmallIntegerField(_('表示順'))
    name = models.CharField(_('地域名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    postage = models.IntegerField(_('追加送料'), default=0)
    is_supported = models.BooleanField(_('対応中'), default=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'regions'
        ordering = ['order']
        verbose_name = _('地域')
        verbose_name_plural = _('地域')

    def __str__(self):
        return '%s' % self.name


class Prefecture(UUIDModel):
    region = models.ForeignKey('Region', on_delete=models.PROTECT, verbose_name=_('地域'))
    order= models.SmallIntegerField(_('表示順'))
    name = models.CharField(_('都道府県名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    is_supported = models.BooleanField(_('対応中'), default=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'prefectures'
        ordering = ['order']
        verbose_name = _('都道府県')
        verbose_name_plural = _('都道府県')

    def __str__(self):
        return '%s' % self.name


class Airline(UUIDModel):
    name = models.CharField(_('航空会社名'), max_length=50)
    color = models.CharField(_('コーポレートカラー'), max_length=50)
    max_total_dimensions = models.FloatField(_('最大三辺合計'))
    max_weight = models.FloatField(_('最大重量'))
    order = models.SmallIntegerField(_('表示順'))
    is_supported = models.BooleanField(_('対応中'), default=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'airlines'
        ordering = ['order']
        verbose_name = _('航空会社')
        verbose_name_plural = _('航空会社')

    def __str__(self):
        return '%s' % self.name


class Size(UUIDModel):
    name = models.CharField(_('サイズ名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    min_capacity = models.SmallIntegerField(_('最小容量'))
    max_capacity = models.SmallIntegerField(_('最大容量'), blank=True, null=True)
    min_days = models.SmallIntegerField(_('最小日数'))
    max_days = models.SmallIntegerField(_('最大日数'), blank=True, null=True)
    min_weight = models.FloatField(_('最小重量'))
    max_weight = models.FloatField(_('最大重量'), blank=True, null=True)
    min_total_dimensions = models.FloatField(_('最小三辺合計'))
    max_total_dimensions = models.FloatField(_('最大三辺合計'), blank=True, null=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'sizes'
        ordering = ['min_days']
        verbose_name = _('サイズ')
        verbose_name_plural = _('サイズ')

    def __str__(self):
        return '%s' % self.name


class Type(UUIDModel):

    def _get_image_path(self, filename):
        prefix = 'img/type/'
        path = get_image_path(self, filename)
        return prefix + path

    name = models.CharField(_('タイプ名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    image = models.ImageField(upload_to=_get_image_path, verbose_name=_('画像'))
    order= models.SmallIntegerField(_('表示順'))
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'types'
        ordering = ['order']
        verbose_name = _('タイプ')
        verbose_name_plural = _('タイプ')

    def __str__(self):
        return '%s' % self.name

    def save(self, *args, **kwargs):
        try:
            type = Type.objects.get(pk=self.pk)
            if type.image:
                if type.image.url != self.image.url:
                    type.image.delete(save=False)
        except self.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.image.delete()
        super().delete(*args, **kwargs)


class ColorCategory(UUIDModel):
    name = models.CharField(_('カラー分類名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    code = models.CharField(_('カラーコード'), max_length=50)
    order= models.SmallIntegerField(_('表示順'))
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'color_categories'
        ordering = ['order']
        verbose_name = _('カラー分類')
        verbose_name_plural = _('カラー分類')

    def __str__(self):
        return '%s' % self.name


class Bland(UUIDModel):
    name = models.CharField(_('ブランド名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'blands'
        ordering = ['name']
        verbose_name = _('ブランド')
        verbose_name_plural = _('ブランド')

    def __str__(self):
        return '%s' % self.name


class Series(UUIDModel):
    bland = models.ForeignKey('Bland', on_delete=models.PROTECT, verbose_name=_('ブランド'))
    name = models.CharField(_('シリーズ名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'serieses'
        ordering = ['name']
        verbose_name = _('シリーズ')
        verbose_name_plural = _('シリーズ')

    def __str__(self):
        return '%s' % self.name


class Item(UUIDModel):
    bland = models.ForeignKey('Bland', on_delete=models.PROTECT, verbose_name=_('ブランド'))
    series = models.ForeignKey('Series', on_delete=models.PROTECT, verbose_name=_('シリーズ'))
    size = models.ForeignKey('Size', on_delete=models.PROTECT, verbose_name=_('サイズ'))
    type = models.ForeignKey('Type', on_delete=models.PROTECT, verbose_name=_('タイプ'))
    color_category = models.ForeignKey('ColorCategory', on_delete=models.PROTECT, verbose_name=_('カラー分類'))
    color = models.CharField(_('カラー'), max_length=50)
    name = models.CharField(_('商品名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    capacity = models.IntegerField(_('容量'))
    length = models.FloatField(_('縦'))
    width = models.FloatField(_('横'))
    depth = models.FloatField(_('奥行'))
    weight = models.FloatField(_('重量'))
    is_tsa = models.BooleanField(_('TSAロック対応'), default=True)
    fee_intercept = models.IntegerField(_('料金切片'))
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'items'
        ordering = ['series__name', 'capacity', 'name']
        verbose_name = _('アイテム')
        verbose_name_plural = _('アイテム')

    def __str__(self):
        return '%s' % self.name

    def save(self, *args, **kwargs):
        two_days_fee = self.fee_intercept + round((self.fee_intercept / .6) * .2, -1) * 2
        postage = 2860
        if two_days_fee <= postage and self.capacity <= 40:
            self.fee_intercept = postage - round(postage * .2, -1) * 2
        super().save(*args, **kwargs)
        ItemFeeCoef.objects.filter(item=self).delete()
        self.item_fee_coef_set.get_or_create(
            fee_coef=round((self.fee_intercept / .6) * .2, -1),
            starting_point=0,
            end_point=3
        )
        self.item_fee_coef_set.get_or_create(
            fee_coef=round((self.fee_intercept / .6) * .15, -1),
            starting_point=3,
            end_point=5
        )
        self.item_fee_coef_set.get_or_create(
            fee_coef=round((self.fee_intercept / .6) * .13, -1),
            starting_point=5
        )


class ItemFeeCoef(UUIDModel):
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_('アイテム'), related_name='item_fee_coef_set')
    fee_coef = models.IntegerField(_('料金係数'))
    starting_point = models.SmallIntegerField(_('起点日数'))
    end_point = models.SmallIntegerField(_('終点日数'), blank=True, null=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'item_fee_coefs'
        ordering = ['item__bland__name', 'item__capacity', 'item__name', 'starting_point']
        verbose_name = _('アイテム料金係数')
        verbose_name_plural = _('アイテム料金係数')

    def __str__(self):
        return '%s' % self.item.name


class ItemImage(UUIDModel):

    def _get_image_path(self, filename):
        prefix = 'img/item/'
        path = get_image_path(self, filename)
        return prefix + path

    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_('アイテム'), related_name='item_image_set')
    image = models.ImageField(upload_to=_get_image_path, verbose_name=_('画像'))
    order = models.SmallIntegerField(_('表示順'))
    description = models.TextField(_('備考'), blank=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'item_images'
        ordering = ['item__bland__name', 'item__capacity', 'item__name', 'order']
        verbose_name = _('アイテム画像')
        verbose_name_plural = _('アイテム画像')

    def __str__(self):
        return '%s' % self.item.name

    def save(self, *args, **kwargs):
        try:
            item_image = ItemImage.objects.get(pk=self.pk)
            if item_image.image:
                if item_image.image.url != self.image.url:
                    item_image.image.delete(save=False)
        except self.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.image.delete()
        super().delete(*args, **kwargs)


class AttachmentCategory(UUIDModel):
    name = models.CharField(_('付属品分類名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    order= models.SmallIntegerField(_('表示順'))
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'attachment_categories'
        ordering = ['order']
        verbose_name = _('付属品分類')
        verbose_name_plural = _('付属品分類')

    def __str__(self):
        return '%s' % self.name


class Attachment(UUIDModel):

    def _get_image_path(self, filename):
        prefix = 'img/attachment/'
        path = get_image_path(self, filename)
        return prefix + path

    attachment_category = models.ForeignKey('AttachmentCategory', on_delete=models.PROTECT, verbose_name=_('付属品分類'))
    name = models.CharField(_('付属品名'), max_length=50)
    description = models.TextField(_('備考'), blank=True)
    image = models.ImageField(upload_to=_get_image_path, verbose_name=_('画像'))
    fee = models.IntegerField(_('料金'))
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'attachments'
        ordering = ['attachment_category__order', 'name']
        verbose_name = _('付属品')
        verbose_name_plural = _('付属品')

    def __str__(self):
        return '%s' % self.name

    def save(self, *args, **kwargs):
        try:
            attachment = Attachment.objects.get(pk=self.pk)
            if attachment.image:
                if attachment.image.url != self.image.url:
                    attachment.image.delete(save=False)
        except self.DoesNotExist:
            pass
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.image.delete()
        super().delete(*args, **kwargs)


class Cart(UUIDModel):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('ユーザー'))
    description = models.TextField(_('備考'), blank=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'carts'
        ordering = ['-created_at']
        verbose_name = _('カート')
        verbose_name_plural = _('カート')

    def __str__(self):
        return '%s' % self.uuid


class Reservation(UUIDModel):

    class GenderChoice(Enum):
        male = '男性'
        female = '女性'

        @classmethod
        def choices(cls):
            return [(c.name, c.value) for c in cls]

    class AgeRangeChoice(Enum):
        teens = '～10代'
        twenties = '20代'
        thirties = '30代'
        forties = '40代'
        fifties = '50代'
        sixties = '60代～'

        @classmethod
        def choices(cls):
            return [(c.name, c.value) for c in cls]

    cart = models.ForeignKey('Cart', on_delete=models.PROTECT, verbose_name=_('カート'))
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('ユーザー'))
    item = models.ForeignKey('Item', on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('アイテム'))
    size = models.ForeignKey('Size', on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('サイズ'))
    type = models.ForeignKey('Type', on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('タイプ'))
    region = models.ForeignKey('Region', on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('地域'))
    prefecture = models.ForeignKey('Prefecture', on_delete=models.PROTECT, blank=True, null=True, verbose_name=_('都道府県'))
    attachments = models.ManyToManyField('Attachment', db_table='reservations_attachments', blank=True, verbose_name=_('付属品'))
    start_date = models.DateField(_('開始日'), blank=True, null=True)
    return_date = models.DateField(_('返却日'), blank=True, null=True)
    zip_code = models.CharField(_('郵便番号'), max_length=50, blank=True)
    city = models.CharField(_('市区町村'), max_length=50, blank=True)
    address = models.CharField(_('番地・建物名'), max_length=255, blank=True)
    address_name = models.CharField(_('氏名'), max_length=50, blank=True, null=True)
    address_name_kana = models.CharField(_('フリガナ'), max_length=50, blank=True, null=True)
    email = models.EmailField(_('email address'), blank=True, null=True)
    gender = models.CharField(_('性別'), max_length=50, choices=GenderChoice.choices(), blank=True, null=True)
    age_range = models.CharField(_('年齢層'), max_length=50, choices=AgeRangeChoice.choices(), blank=True, null=True)
    item_fee = models.IntegerField(_('小計価格'), blank=True, null=True)
    postage = models.IntegerField(_('送料'), blank=True, null=True)
    total_fee = models.IntegerField(_('合計価格'), blank=True, null=True)
    is_warranted = models.BooleanField(_('保障パック加入'), default=False)
    status = models.SmallIntegerField(_('ステータス'), default=1)
    description = models.TextField(_('備考'), blank=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'reservations'
        ordering = ['-created_at']
        verbose_name = _('予約')
        verbose_name_plural = _('予約')

    def __str__(self):
        return '%s' % self.item


class Coupon(UUIDModel):

    def generate_coupon_code():
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choices(letters, k=10))

    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, verbose_name=_('ユーザー'))
    coupon_code = models.CharField(_('クーポンコード'), max_length=50, default=generate_coupon_code, unique=True)
    discount = models.IntegerField(_('割引額'))
    status = models.SmallIntegerField(_('ステータス'), default=0)
    description = models.TextField(_('備考'), blank=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']
        verbose_name = _('クーポン')
        verbose_name_plural = _('クーポン')

    def __str__(self):
        return '%s' % self.coupon_code


class Question(UUIDModel):
    order = models.SmallIntegerField(_('表示順'))
    text = models.TextField(_('質問'))
    is_public = models.BooleanField(_('公開中'), default=False)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'questions'
        ordering = ['order']
        verbose_name = _('質問')
        verbose_name_plural = _('質問')

    def __str__(self):
        return '%s' % self.text


class Answer(UUIDModel):
    reservation = models.ForeignKey('Reservation', on_delete=models.PROTECT, verbose_name=_('予約'))
    question = models.ForeignKey('Question', on_delete=models.PROTECT, verbose_name=_('ユーザー'))
    text = models.TextField(_('回答'))
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        db_table = 'answers'
        ordering = ['-created_at']
        verbose_name = _('回答')
        verbose_name_plural = _('回答')

    def __str__(self):
        return '%s' % self.text
