from django.db import models
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel
from core.utils import get_upload_path


class ProductSection(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Product Sections"
        ordering = ["seq", "created"]

    seq = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=100)
    title_ar = models.CharField(max_length=100)
    content = models.TextField(blank=True)
    content_ar = models.TextField(blank=True)
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="sections",
        related_query_name="section",
        null=False,
        blank=False,
    )

    def __str__(self):
        return self.product.name
