from django.contrib import auth
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import models
from django.db.models.manager import EmptyManager
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin
from enum import Enum
from main.models import UUIDModel

# Create your models here.

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('hopes_newsletters', False)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):

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

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    first_name_kana = models.CharField(_('メイ'), max_length=30, blank=True)
    last_name_kana = models.CharField(_('セイ'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), unique=True, blank=True, null=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    prefecture = models.ForeignKey('main.Prefecture', on_delete=models.PROTECT, verbose_name=_('都道府県'), blank=True, null=True)
    zip_code1 = models.CharField(_('郵便番号1'), max_length=50, blank=True)
    zip_code2 = models.CharField(_('郵便番号2'), max_length=50, blank=True)
    city = models.CharField(_('市区町村'), max_length=50, blank=True)
    address = models.CharField(_('番地・建物名'), max_length=255, blank=True)
    gender = models.CharField(_('性別'), max_length=50, choices=GenderChoice.choices(), blank=True, null=True)
    age_range = models.CharField(_('年齢層'), max_length=50, choices=AgeRangeChoice.choices(), blank=True, null=True)
    facebook_id = models.CharField(_('Facebook ID'), max_length=255, unique=True, blank=True, null=True)
    line_id = models.CharField(_('LINE ID'), max_length=255, unique=True, blank=True, null=True)
    is_line_only = models.BooleanField(_('LINEのみのユーザー'), default=False)
    is_verified = models.BooleanField(_('認証完了'), default=False)
    hopes_newsletters = models.BooleanField(_('配信希望'), default=True)
    created_at = models.DateTimeField(_('作成日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    class Meta:
      db_table = 'users'
      ordering = ['-created_at']
      verbose_name = _('ユーザー')
      verbose_name_plural = _('ユーザー')

    def __str__(self):
      return '%s' % self.email
