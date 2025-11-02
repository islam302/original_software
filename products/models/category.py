from django.db import models
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel
from core.utils import get_upload_path


class Category(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["seq"]

    seq = models.IntegerField(default=0)
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    image_file = models.ImageField(
        upload_to=get_upload_path,
        null=True,
        blank=True,
    )
    is_deleted = models.BooleanField(default=False)
    
    def delete(self, using = ..., keep_parents = ...):
        self.is_deleted = True
        
        sub_categories = self.sub_categories.all()
        for sub_category in sub_categories:
            sub_category.delete()
            
            
        
        self.save()
        

    def __str__(self):
        return self.name


class SubCategory(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Sub Categories"
        ordering = ["seq"]

    seq = models.IntegerField(default=0)
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    image_file = models.ImageField(
        upload_to=get_upload_path,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="sub_categories",
        related_query_name="subcategory",
        null=False,
        blank=False,
    )
    
    is_deleted = models.BooleanField(default=False)
    
    def delete(self, using = ..., keep_parents = ...):
        self.is_deleted = True
        products = self.products.all()
        for product in products:
            product.delete()
            
        self.save()
    
    
    @property
    def category_name(self):
        return self.category.name

    def __str__(self):
        return self.name
