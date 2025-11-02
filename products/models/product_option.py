from django.db import models
from django_lifecycle import AFTER_DELETE, AFTER_SAVE, LifecycleModelMixin, hook
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel
from core.utils import get_upload_path


class ProductOption(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Product Options"
        ordering = ["seq", "created"]

    seq = models.PositiveIntegerField(default=0)
    parent_product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="options",
        related_query_name="option",
    )
    keys_users_count = models.ForeignKey(
        "KeyUsersCount",
        on_delete=models.CASCADE,
        related_name="+",
        related_query_name="+",
    )
    keys_validity = models.ForeignKey(
        "KeyValidity",
        on_delete=models.CASCADE,
        related_name="+",
        related_query_name="+",
    )
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="option_of",
        related_query_name="option_of",
    )

    def __str__(self):
        return f"{self.parent_product.name} - {self.keys_users_count.count} User/s - {self.keys_validity.validity} {self.keys_validity.validity_unit}"

    @hook(AFTER_SAVE)
    def update_product_keys_qty(self):
        self.product.keys_users_count = self.keys_users_count
        self.product.keys_validity = self.keys_validity
        self.product.save()

    @hook(AFTER_SAVE)
    def set_options_booleans(self):
        self.product.is_option_product = True
        self.product.save()
        self.parent_product.has_options = True
        self.parent_product.save()

    @hook(AFTER_DELETE)
    def unset_options_booleans(self):
        self.product.is_option_product = False
        self.product.save()
        if not self.parent_product.options.exists():
            self.parent_product.has_options = False
            self.parent_product.save()
