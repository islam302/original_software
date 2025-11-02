from django.db import models
from imagekit.models import ProcessedImageField
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel
from core.utils import get_upload_path


class Slider(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Slider"
        ordering = ["-created"]

    path = models.CharField("Path", max_length=200)
    image = ProcessedImageField(
        upload_to=get_upload_path,
        options={"quality": 70},
    )

    def __str__(self):
        return self.path


class CategorySlider(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Category Slider"
        ordering = ["-created"]

    path = models.CharField("Path", max_length=200)
    image = ProcessedImageField(
        upload_to=get_upload_path,
        options={"quality": 70},
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="category_slider_items",
        related_query_name="category_slider_item",
    )

    def __str__(self):
        return f"{self.path} - {self.category.name}"


class SubCategorySlider(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Sub Category Slider"
        ordering = ["-created"]

    path = models.CharField("Path", max_length=200)
    image = ProcessedImageField(
        upload_to=get_upload_path,
        options={"quality": 70},
    )
    sub_category = models.ForeignKey(
        "SubCategory",
        on_delete=models.CASCADE,
        related_name="sub_category_slider_items",
        related_query_name="sub_category_slider_item",
    )

    def __str__(self):
        return f"{self.path} - {self.sub_category.name}"
