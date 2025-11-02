from computedfields.models import ComputedField, ComputedFieldsModel
from constance import config
from crum import get_current_user
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_SAVE,
    AFTER_UPDATE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)
from model_utils import Choices
from model_utils.fields import MonitorField
from model_utils.models import TimeStampedModel
from rest_framework import serializers
from smart_selects.db_fields import ChainedForeignKey
from django.contrib.contenttypes.fields import GenericRelation

from authentication.models import UserStampedModel, WholesaleUserType
from notifications.models import Notification

from crum import get_current_user
from core.utils import get_upload_path


class ProductWholesalePricing(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Wholesale Pricings"
        ordering = ["id"]
        unique_together = (
            "product",
            "wholesale_user_type",
        )

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="wholesale_pricings",
        related_query_name="wholesale_pricing",
    )
    wholesale_user_type = models.ForeignKey(
        "authentication.WholesaleUserType",
        on_delete=models.CASCADE,
        related_name="wholesale_pricings",
        related_query_name="wholesale_pricing",
    )
    price = models.DecimalField(max_digits=26, decimal_places=0)
    
    @property 
    def price_in_usd(self):
        if not self.price:
            return 0
        return round(self.price / config.USD_TO_IQD_EXCHANGE_RATE, 2)

    def __str__(self):
        return f"{self.product.name} - {self.wholesale_user_type.title} - {self.price}"


class Product(
    ComputedFieldsModel, LifecycleModelMixin, TimeStampedModel, UserStampedModel
):
    class Meta:
        verbose_name_plural = "Products"
        ordering = ["seq"]

    TAG = Choices(
        ("new", "New"),
        ("sale", "Sale"),
        ("featured", "Featured"),
    )

    STATUS = Choices(
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    seq = models.IntegerField(default=0)
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=26, decimal_places=0)
    old_price = models.DecimalField(
        max_digits=26, decimal_places=0, blank=True, null=True
    )
    color = models.CharField(max_length=100, blank=True)
    tag = models.CharField(
        "Tag", choices=TAG, max_length=50, blank=True, null=True)
    status = models.CharField("Status", choices=STATUS,
                              max_length=50, default=STATUS.active)
    available = models.BooleanField(default=True)
    qty = models.PositiveIntegerField(
        "Quantity",
        default=0,
    )
    qty_modified_from_zero = models.DateTimeField(blank=True, null=True)
    is_key_product = models.BooleanField(
        default=False, help_text="is this product a key product?"
    )
    keys_qty = models.PositiveIntegerField(
        "Keys Quantity",
        default=None,
        blank=True,
        null=True,
    )
    keys_qty_used = property(
        lambda self: (
            self.product_keys.filter(is_used=True).count()
            if self.is_key_product
            else None
        )
    )
    keys_qty_unused = property(
        lambda self: (
            self.product_keys.filter(is_used=False).count()
            if self.is_key_product
            else None
        )
    )
    
    keys_qty_unused_2 = property(
        lambda self: (
            self.product_keys.filter(is_used=False).count()
            if self.is_key_product
            else None
        )
    )

    SKU_code = models.CharField(max_length=100)
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="products",
        related_query_name="product",
        null=False,
        blank=False,
    )

    sub_category = ChainedForeignKey(
        "SubCategory",
        chained_field="category",
        chained_model_field="category",
        related_name="products",
        related_query_name="product",
        show_all=False,
        auto_choose=True,
        sort=True,
    )

    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="products",
        related_query_name="product",
        blank=True,
        null=True,
    )

    cashback_amount = models.DecimalField(
        max_digits=26, decimal_places=0, blank=True, null=True
    )
    description = models.TextField(
        blank=True,
    )
    description_ar = models.TextField(
        blank=True,
    )

    keys_users_count = models.ForeignKey(
        "KeyUsersCount",
        on_delete=models.CASCADE,
        related_name="+",
        related_query_name="+",
        blank=True,
        null=True,
    )

    keys_validity = models.ForeignKey(
        "KeyValidity",
        on_delete=models.CASCADE,
        related_name="+",
        related_query_name="+",
        blank=True,
        null=True,
    )

    offer_products = models.ManyToManyField(
        "Product",
        related_name="+",
        related_query_name="+",
        blank=True,
    )

    has_options = models.BooleanField(default=False)
    is_option_product = models.BooleanField(default=False)

    tutorial = models.URLField(blank=True, null=True)
    download_link = models.URLField(blank=True, null=True)

    notifications = GenericRelation(Notification)

    is_discounted = ComputedField(
        models.BooleanField(
            default=False,
            editable=False,
        ),
        depends=[("self", ["old_price"])],
        compute=lambda self: self.old_price is not None,
    )

    is_deleted = models.BooleanField(default=False)

    number_of_keys_to_send_notification = models.PositiveIntegerField(
        "Number of Keys to Send Notification",
        default=5,
    )

    search_status = models.CharField(
        max_length=255,
        default="Good"
    )

    is_special_offer = models.BooleanField(
        default=False
    )

    @hook(AFTER_UPDATE, when="keys_qty_unused")
    def set_search_status(self):
        new_status = "Good"
        if self.keys_qty_unused == 0:
            new_status = "Empty"
        elif self.keys_qty_unused <= self.number_of_keys_to_send_notification:
            new_status = "Poor"

        if self.search_status != new_status:  # Only update if it actually changed
            self.search_status = new_status  # Avoids triggering the hook again
            self.save(update_fields=["search_status"])

    @hook(AFTER_UPDATE, when="qty", was=0, is_now=lambda x: x > 0)
    def set_qty_modified_from_zero(self):
        self.qty_modified_from_zero = timezone.now()

    @hook(AFTER_CREATE)
    def set_wholesale_pricing(self):
        for wholesale_user_type in WholesaleUserType.objects.all():
            ProductWholesalePricing.objects.create(
                product=self,
                wholesale_user_type=wholesale_user_type,
                price=self.price,
            )

    @property
    def parent_product(self):
        return

    @property
    def status_display(self):
        if self.status == "active" and not self.old_price:
            return "active"
        elif self.status == "active" and self.old_price:
            return "discounted"
        elif self.status == "inactive":
            return "inactive"

    @property
    def price_in_usd(self):
        if not self.price:
            return 0
        return round(self.price / config.USD_TO_IQD_EXCHANGE_RATE, 2)

    @property
    def old_price_in_usd(self):
        if not self.old_price:
            return 0
        return round(self.old_price / config.USD_TO_IQD_EXCHANGE_RATE, 2)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def __str__(self):
        return self.name


class ProductKey(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Product Keys"
        ordering = ["id"]

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="product_keys",
        related_query_name="product_key",
    )
    key = models.CharField(max_length=100)
    is_used = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    used_at = MonitorField(
        monitor="is_used",
        when=[True],
        blank=True,
        null=True,
        default=None,
    )
    used_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="used_product_keys",
        related_query_name="used_product_key",
        blank=True,
        null=True,
    )
    used_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="used_product_keys",
        related_query_name="used_product_key",
        blank=True,
        null=True,
    )

    @property
    def order_number(self):
        return self.used_order.order_number if self.used_order else None

    @property
    def product_keys_left(self):
        return ProductKey.objects.filter(product=self.product, is_used=False).count()

    @hook(AFTER_SAVE)
    def update_product_keys_qty(self):
        self.product.keys_qty = self.product.product_keys.filter().count()
        self.product.is_key_product = True
        self.product.save()

        # if there is no keys left, create important notification
        if self.product.keys_qty_unused == 0:
            Notification.objects.create(
                linked_model_name="products.Product",
                object_id=self.product.id,
                related_user=get_current_user(),
                description=f"Product {self.product.name} is out of keys",
                notification_level=Notification.NOTIFICATION_LEVELS.important,
            )
        # if there is keys left is 5 or less, create normal notification
        elif (
            self.product.keys_qty_unused
            <= self.product.number_of_keys_to_send_notification
        ):
            Notification.objects.create(
                linked_model_name="products.Product",
                object_id=self.product.id,
                related_user=get_current_user(),
                description=f"Product {self.product.name} has only {self.product.keys_qty_unused} keys left",
                notification_level=Notification.NOTIFICATION_LEVELS.normal,
            )

    @hook(BEFORE_DELETE)
    def update_product_keys_qty_on_delete(self):
        self.product.keys_qty = self.product.product_keys.filter().count()
        self.product.save()

        # if there is no keys left, create important notification
        if self.product.keys_qty_unused == 0:
            Notification.objects.create(
                linked_model_name="products.Product",
                object_id=self.product.id,
                description=f"Product {self.product.name} is out of keys",
                notification_level=Notification.NOTIFICATION_LEVELS.important,
            )
        # if there is keys left is 5 or less, create normal notification
        elif (
            self.product.keys_qty_unused
            <= self.product.number_of_keys_to_send_notification
        ):
            Notification.objects.create(
                linked_model_name="products.Product",
                object_id=self.product.id,
                description=f"Product {self.product.name} has only {self.product.keys_qty_unused} keys left",
                notification_level=Notification.NOTIFICATION_LEVELS.normal,
            )

    def save(self, *args, **kwargs):
        # add to qty if key is new
        if not self.pk:
            self.product.qty += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.key} - {'Used' if self.is_used else 'Not Used'}"


class KeyUsersCount(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Key Users Count"
        ordering = ["count"]

    count = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.count} User/s"


class KeyValidity(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Key Validity"
        ordering = ["validity"]

    VALIDITY_UNIT = Choices(
        ("day", "Day"),
        ("week", "Week"),
        ("month", "Month"),
        ("year", "Year"),
        ("lifetime", "Lifetime"),
    )

    validity = models.PositiveIntegerField(null=True, blank=True)
    validity_unit = models.CharField(
        "Validity Unit",
        choices=VALIDITY_UNIT,
        max_length=50,
    )

    def __str__(self):
        return f"{self.validity} {self.validity_unit}"


class SpecialOffer(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Key Validity"
        ordering = ["-created"]

    title = models.CharField(max_length=100,blank=True,null=True)
    title_ar = models.CharField(max_length=100,blank=True,null=True)

    image = models.ImageField(
        upload_to=get_upload_path,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title
