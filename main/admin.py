from django.contrib import admin
from django import forms
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
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

class ReservedAttachmentInline(admin.TabularInline):
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
    actions = ['copy_models_1', 'copy_models_2', 'copy_models_3', 'copy_models_4', 'copy_models_5', 'copy_models_6', 'copy_models_7', 'copy_models_8', 'copy_models_9', 'copy_models_10']

    def _copy_models(self, request, queryset, n):
        for obj in queryset:
            for i in range(0, n):
                obj.pk = None
                obj.uuid = None
                obj.save()
        self.message_user(request, "選択されたアイテムを{}個ずつ複製しました".format(n), level=messages.SUCCESS)
        if queryset.count() == 1:
            if queryset.first().series:
                return redirect(reverse('admin:main_item_changelist') + '?series__uuid__exact={}'.format(queryset.first().series.uuid))
            elif queryset.first().bland and not queryset.first().series:
                return redirect(reverse('admin:main_item_changelist') + '?bland__uuid__exact={}'.format(queryset.first().bland.uuid))

    def copy_models_1(self, request, queryset):
        return self._copy_models(request, queryset, 1)

    def copy_models_2(self, request, queryset):
        return self._copy_models(request, queryset, 2)

    def copy_models_3(self, request, queryset):
        return self._copy_models(request, queryset, 3)

    def copy_models_4(self, request, queryset):
        return self._copy_models(request, queryset, 4)

    def copy_models_5(self, request, queryset):
        return self._copy_models(request, queryset, 5)

    def copy_models_6(self, request, queryset):
        return self._copy_models(request, queryset, 6)

    def copy_models_7(self, request, queryset):
        return self._copy_models(request, queryset, 7)

    def copy_models_8(self, request, queryset):
        return self._copy_models(request, queryset, 8)

    def copy_models_9(self, request, queryset):
        return self._copy_models(request, queryset, 9)

    def copy_models_10(self, request, queryset):
        return self._copy_models(request, queryset, 10)

    copy_models_1.short_description = "選択された アイテム の複製 (1個)"
    copy_models_2.short_description = "選択された アイテム の複製 (2個)"
    copy_models_3.short_description = "選択された アイテム の複製 (3個)"
    copy_models_4.short_description = "選択された アイテム の複製 (4個)"
    copy_models_5.short_description = "選択された アイテム の複製 (5個)"
    copy_models_6.short_description = "選択された アイテム の複製 (6個)"
    copy_models_7.short_description = "選択された アイテム の複製 (7個)"
    copy_models_8.short_description = "選択された アイテム の複製 (8個)"
    copy_models_9.short_description = "選択された アイテム の複製 (9個)"
    copy_models_10.short_description = "選択された アイテム の複製 (10個)"

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
    search_fields = ['user__first_name', 'user__last_name', 'user__first_name_kana', 'user__last_name_kana', 'user__address']
    inlines = [ReservationInline]

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('item', 'total_fee', 'start_date', 'return_date', 'status')
    list_filter = ['start_date', 'return_date', 'item__bland', 'status']
    search_fields = ['first_name', 'last_name', 'first_name_kana', 'last_name_kana' 'zip_code1', 'zip_code2', 'address', 'size', 'type', 'user__first_name', 'user__last_name', 'user__first_name_kana', 'user__last_name_kana', 'user__address', 'item__name', 'item__bland__name', 'item__series__name', 'item__color__name']
    exclude = ['attachments']
    inlines = [ReservedAttachmentInline, AnswerInline]

class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'user', 'coupon_code', 'discount', 'status')
    list_filter = ['status']
    search_fields = ['coupon_code', 'user__first_name', 'user__last_name', 'user__first_name_kana', 'user__last_name_kana', 'user__address', 'discount', 'description']

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
