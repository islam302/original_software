from django.db import models
from imagekit.models import ProcessedImageField
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel
from core.utils import get_upload_path


class Company(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ["id"]

    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    logo = ProcessedImageField(
        upload_to=get_upload_path,
        options={"quality": 70},
        blank=True,
        null=True,
    )
    show_in_home = models.BooleanField(default=True)
    
    is_deleted = models.BooleanField(default=False)
    

    def __str__(self):
        return self.name
    
    def delete(self, using = ..., keep_parents = ...):
        self.is_deleted = True
        self.save()
        
