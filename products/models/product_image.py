from django.db import models
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel
from core.utils import get_upload_path


class ProductImage(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Product Images"
        ordering = ["id"]

    image_file = models.ImageField(
        upload_to=get_upload_path,
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="images",
        related_query_name="image",
        null=False,
        blank=False,
    )

    def __str__(self):
        return self.product.name
