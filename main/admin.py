from django.contrib import admin
from django import forms
from . import models

# Register your models here.

class PrefectureInline(admin.TabularInline):
    model = models.Prefecture
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['name', 'is_supported']

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.prefecture_set.count()
        return max_num

class SeriesInline(admin.TabularInline):
    model = models.Series
    extra = 1
    can_delete = False
    show_change_link = True
    fields = ['name']

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.series_set.count()
        return max_num

class ItemInline(admin.TabularInline):
    model = models.Item
    can_delete = False
    show_change_link = True
    fields = ['name', 'bland', 'capacity', 'size', 'type', 'color_category']

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.item_set.count()
        return max_num

class ItemFeeCoefInline(admin.TabularInline):
    model = models.ItemFeeCoef
    can_delete = True
    show_change_link = False

    def get_extra(self, request, obj=None, **kwargs):
        extra = 3
        if obj:
            return extra - obj.item_fee_coef_set.count()
        return extra

class ItemImageInline(admin.TabularInline):
    model = models.ItemImage
    can_delete = True
    show_change_link = True
    exclude = ['description']

    def get_extra(self, request, obj=None, **kwargs):
        extra = 5
        if obj:
            return extra - obj.item_image_set.count()
        return extra

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 10
        return max_num

class AttachmentInline(admin.TabularInline):
    model = models.Attachment
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['name', 'fee', 'image']

class ReservationAttachmentInline(admin.TabularInline):
    model = models.Reservation.attachments.through
    extra = 0
    can_delete = True
    show_change_link = True

class ReservationInline(admin.TabularInline):
    model = models.Reservation
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['item', 'prefecture', 'start_date', 'return_date', 'total_fee', 'status']

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.reservation_set.count()
        return max_num

class AnswerInline(admin.TabularInline):
    model = models.Answer
    extra = 0
    can_delete = False
    show_change_link = False
    fields = ['reservation', 'question', 'text']

    def get_max_num(self, request, obj=None, **kwargs):
        max_num = 0
        if obj:
            max_num = obj.answer_set.count()
        return max_num

class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'description', 'postage', 'is_supported')
    list_filter = ['postage']
    search_fields = ['name', 'description', 'postage']
    inlines = [PrefectureInline]

class PrefectureAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'region', 'description', 'is_supported')
    list_filter = ['region']
    search_fields = ['name', 'description']

class AirlineAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_total_dimensions_carry_on', 'max_total_dimensions_domestic', 'max_total_dimensions_international', 'is_supported')
    list_filter = ['is_supported']
    search_fields = ['name', 'max_total_dimensions', 'max_weight', 'is_supported']

class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_days', 'max_days', 'min_weight', 'max_weight', 'min_total_dimensions', 'max_total_dimensions')
    search_fields = ['name', 'description', 'min_days', 'max_days', 'min_weight', 'max_weight', 'min_total_dimensions', 'max_total_dimensions']
    inlines = [ItemInline]

class TypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ['name', 'description']
    inlines = [ItemInline]

class ColorCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ['name', 'description']
    inlines = [ItemInline]

class BlandAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ['name', 'description']
    inlines = [SeriesInline, ItemInline]

class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ['name', 'description']
    inlines = [ItemInline]

class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'bland', 'series', 'capacity', 'size', 'type', 'color_category')
    list_filter = ['size', 'type', 'color_category', 'bland', 'series']
    search_fields = ['name', 'description', 'bland__name', 'series__name', 'size__name', 'type__name', 'color_category__name', 'color']
    inlines = [ItemFeeCoefInline, ItemImageInline, ReservationInline]

class AttachmentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ['name', 'description', 'order']
    inlines = [AttachmentInline]

class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'fee', 'attachment_category')
    list_filter = ['attachment_category']
    search_fields = ['name', 'description', 'fee', 'attachment_category__name']

class CartAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'user', 'created_at', 'updated_at')
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__address_name']
    inlines = [ReservationInline]

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('item', 'total_fee', 'start_date', 'return_date', 'status')
    list_filter = ['start_date', 'return_date', 'item__bland', 'status']
    search_fields = ['name', 'zip_code' 'address', 'size', 'type', 'user__first_name', 'user__last_name', 'user__address_name', 'item__name', 'item__bland__name', 'item__series_name', 'item__color__name']
    exclude = ['attachments']
    inlines = [ReservationAttachmentInline, AnswerInline]

class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'user', 'coupon_code', 'discount', 'status')
    list_filter = ['status']
    search_fields = ['coupon_code', 'user__first_name', 'user__last_name', 'user__address_name', 'discount', 'description']

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('order', 'text', 'is_public')
    list_filter = ['is_public']
    search_fields = ['order', 'text']
    inlines = [AnswerInline]

admin.site.register(models.Region, RegionAdmin)
admin.site.register(models.Prefecture, PrefectureAdmin)
admin.site.register(models.Airline, AirlineAdmin)
admin.site.register(models.Size, SizeAdmin)
admin.site.register(models.Type, TypeAdmin)
admin.site.register(models.ColorCategory, ColorCategoryAdmin)
admin.site.register(models.Bland, BlandAdmin)
admin.site.register(models.Series, SeriesAdmin)
admin.site.register(models.Item, ItemAdmin)
admin.site.register(models.AttachmentCategory, AttachmentCategoryAdmin)
admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.Cart, CartAdmin)
admin.site.register(models.Reservation, ReservationAdmin)
admin.site.register(models.Coupon, CouponAdmin)
admin.site.register(models.Question, QuestionAdmin)
