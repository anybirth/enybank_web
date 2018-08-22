from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from main.admin import ReservationInline
from . import models

# Register your models here.

class EmailUserCreationForm(UserCreationForm):

    class Meta():
        model = models.User
        fields = ('email',)


class EmailUserChangeForm(UserChangeForm):

    class Meta:
        model = models.User
        fields = '__all__'


class GroupAdmin(BaseGroupAdmin):
    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('permissions',)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs['queryset'] = qs.select_related('content_type')
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)


class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'line_id', 'facebook_id', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'first_name_kana', 'last_name_kana', 'zip_code1', 'zip_code2', 'prefecture', 'city', 'address', 'age_range', 'gender', 'is_line_only', 'is_verified', 'hopes_newsletters')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = EmailUserChangeForm
    add_form = EmailUserCreationForm
    list_display = ('email', 'line_id', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'prefecture', 'age_range', 'gender', 'created_at', 'updated_at')
    search_fields = ('email', 'line_id', 'facebook_id', 'first_name', 'last_name', 'first_name_kana', 'last_name_kana', 'zip_code1', 'zip_code2', 'prefecture', 'city', 'address')
    ordering = ('-created_at', )
    filter_horizontal = ('groups', 'user_permissions',)
    inlines = [ReservationInline]

admin.site.register(models.User, UserAdmin)
