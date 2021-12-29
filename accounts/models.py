import random
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from djongo.models.fields import Field


class CustomAccountManager(BaseUserManager):

    def create_superuser(self, email, username, first_name, last_name, dollar_balance, password=None, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        other_fields.setdefault('btc_balance', 999)
        other_fields.setdefault('fungible_btc', 999)
        other_fields.setdefault('fungible_balance', dollar_balance)

        if other_fields.get('is_staff') is not True:
            raise ValueError(
                'Superuser must be assigned to is_staff=True'
            )
        if other_fields.get('is_superuser') is not True:
            raise ValueError(
                'Superuser must be assigned to is_superuser=True'
            )
        return self.create_user(email, username, first_name, last_name, dollar_balance, password, **other_fields)

    def create_user(self, email, username, first_name, last_name, dollar_balance, password=None, **other_fields):

        values = [email, username, first_name, last_name, dollar_balance]

        for value in values:
            if not value:
                raise ValueError(_(f'You must provide {value}'))

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, first_name=first_name,
                          last_name=last_name, dollar_balance=dollar_balance, **other_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Trader(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), primary_key=True, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    sign_in_date = models.DateTimeField(default=now)
    btc_balance = models.FloatField(default=0.)
    fungible_btc = models.FloatField(default=0.)
    dollar_balance = models.FloatField(default=0.)
    fungible_balance = models.FloatField(default=0.)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    transactions = Field(default=[])
    subprofiles = Field(default={'sellers': [], 'buyers': []})
    n_open_orders = models.IntegerField(default=0)
    n_close_orders = models.IntegerField(default=0)

    objects = CustomAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'dollar_balance']

    def init(self):
        self.btc_balance = random.randint(1, 10)
        self.fungible_balance = self.dollar_balance
        self.fungible_btc = self.btc_balance
        self.save()

    def __str__(self):
        return self.username
