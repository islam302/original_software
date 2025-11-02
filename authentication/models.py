from constance import config
from crum import get_current_user
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.apps import apps

from django_lifecycle import (
    AFTER_SAVE,
    AFTER_UPDATE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)
from model_utils import Choices
from model_utils.models import TimeStampedModel


class UserStampedModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="created_by",
        related_name="%(class)ss_created_by",
        related_query_name="%(class)s_created_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="updated_by",
        related_name="%(class)ss_updated_by",
        related_query_name="%(class)s_updated_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user and not user.pk:
            user = None
        if not self.pk:
            self.created_by = user
        self.updated_by = user
        super().save(*args, **kwargs)


class User(AbstractUser, TimeStampedModel, UserStampedModel):
    GENDER = Choices(
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    )
    CONTRY = Choices(
        ("iraq", "العراق"),
    )
    CITY = Choices(
        ("al_anbar", "الأنبار"),
        ("al_basra", "البصرة"),
        ("al_muthanna", "المثنى"),
        ("an_najaf", "النجف"),
        ("al_qadisiyah", "القادسية"),
        ("al_sulaymaniyah", "السليمانية"),
        ("babil", "بابل"),
        ("baghdad", "بغداد"),
        ("dhi_qar", "ذي قار"),
        ("dyala", "ديالى"),
        ("dohuk", "دهوك"),
        ("erbil", "اربيل"),
        ("karbala", "كربلاء"),
        ("kirkuk", "كركوك"),
        ("maysan", "ميسان"),
        ("ninawa", "نينوى"),
        ("salah_ad_din", "صلاح الدين"),
        ("wasit", "واسط"),
    )

    birth_date = models.DateField("Birth Date", blank=True, null=True)
    gender = models.CharField("Gender", choices=GENDER,
                              blank=True, max_length=50)
    phone = models.CharField("Phone", max_length=20, blank=True)
    phone_2 = models.CharField("Phone 2", max_length=20, blank=True)
    country = models.CharField(
        "Country", choices=CONTRY, blank=True, max_length=50)
    city = models.CharField("City", choices=CITY, blank=True, max_length=50)

    is_email_verified = property(
        lambda self: self.emailaddress_set.filter(verified=True).exists()
    )
    wholesale_type = models.ForeignKey(
        "authentication.WholesaleUserType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wholesale_types",
        related_query_name="wholesale_type",
    )
    is_wholesale = property(lambda self: self.wholesale_type is not None)

    wallet_balance = models.DecimalField(
        "Wallet Balance", max_digits=26, decimal_places=0, default=0
    )
    wallet_balance_usd = property(
        lambda self: (
            round(self.wallet_balance / config.USD_TO_IQD_EXCHANGE_RATE, 2)
            if self.wallet_balance
            else 0
        )
    )
    hidden = models.BooleanField("Hidden", default=False)
    is_deleted = models.BooleanField("Deleted", default=False)
    
    @property
    def role(self):
        if self.is_superuser or self.is_staff:
            return "Admin"
        elif self.is_wholesale:
            return "Wholesale"
        return "Customer"

    @property
    def total_orders(self):
        Orders = apps.get_model("orders", "Order")
        return Orders.objects.filter(created_by=self).count()

    @property
    def total_orders_price(self):
        Orders = apps.get_model("orders", "Order")
        all_orders = Orders.objects.filter(created_by=self)
        return sum([order.total_price for order in all_orders])
    
    @property
    def last_order_date(self):
        Orders = apps.get_model("orders", "Order")
        all_orders = Orders.objects.filter(created_by=self)
        if all_orders:
            return all_orders.last().created
        return None
    
    @property
    def id(self):
        return self.pk

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        super().save(force_insert, force_update, *args, **kwargs)

    def __str__(self):
        return (
            f"{self.email}"
            if self.get_full_name() == ""
            else f"{self.email } - {self.get_full_name()}"
        )


class WholesaleUserType(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    title = models.CharField("Title", max_length=50)
    negative_limit = models.DecimalField(
        "Negative Limit", max_digits=26, decimal_places=0
    )

    @hook(AFTER_SAVE)
    def create_product_wholesale_pricing(self):
        for product in apps.get_model("products", "Product").objects.all():
            # only create if not exists
            if not product.wholesale_pricings.filter(wholesale_user_type=self).exists():
                apps.get_model("products", "ProductWholesalePricing").objects.create(
                    product=product,
                    wholesale_user_type=self,
                    price=product.price,
                )

    def __str__(self):
        return f"Wholesale Type: {self.title}"


class Transaction(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    TRANSACTION_TYPE = Choices(
        ("deposit", "ايداع"),
        ("order", "طلب"),
    )
    transaction_type = models.CharField(
        "Transaction Type", choices=TRANSACTION_TYPE, max_length=50
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    amount = models.DecimalField("Amount", max_digits=26, decimal_places=0)
    description = models.TextField("Description", blank=True, null=True)
    related_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_transactions",
        related_query_name="related_transaction",
    )
    
    @property
    def username(self):
       return self.user.username

    @property
    def amount_usd(self):
        if not self.amount:
            return 0
        return round(self.amount / config.USD_TO_IQD_EXCHANGE_RATE, 2)

    @hook(AFTER_SAVE)
    def update_wallet_balance(self):
        # if self.user.wholesale_type:
        if self.transaction_type == self.TRANSACTION_TYPE.deposit:
            self.user.wallet_balance += self.amount
        elif self.transaction_type == self.TRANSACTION_TYPE.order and self.amount < 0:
            self.user.wallet_balance += self.amount
        self.user.save()

    def __str__(self):
        return f"Transaction: {self.user.email} - {self.amount}"
