from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from model_utils import Choices
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel


class Notification(UserStampedModel, TimeStampedModel):

    NOTIFICATION_LEVELS = Choices(
        ("important", "Important"),
        ("normal", "Normal"),
        ("low", "Low"),
    )

    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        blank=True,
        null=True,
    )
    content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
        related_name="related_%(class)s",
        verbose_name="Content Type of the related object",
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(
        verbose_name="ID of the related object",
        null=True,
        blank=True,
    )
    content_object = GenericForeignKey(
        "content_type",
        "object_id",
    )
    linked_model_name = models.CharField(
        max_length=255,
        verbose_name="Name of the linked model",
        null=True,
        blank=True,
        editable=False,
    )
    description = models.TextField(
        verbose_name="Description of the notification",
        blank=True,
    )
    notification_level = models.CharField(
        choices=NOTIFICATION_LEVELS,
        default=NOTIFICATION_LEVELS.normal,
        max_length=20,
    )
    hidden = models.BooleanField(
        default=False,
        verbose_name="Is the notification hidden?",
    )

    def save(self, *args, **kwargs):
        linked_model_name = kwargs.get("linked_model_name", None) or getattr(
            self, "linked_model_name", None
        )
        if linked_model_name:
            app_label, model_name = linked_model_name.lower().split(".")
            # Get the ContentType based on the provided model name
            content_type = ContentType.objects.get(
                app_label=app_label, model=model_name
            )
            self.content_type = content_type
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        # Get the model name from the content type if linked_object is None
        model_name = (
            self.content_type.model
            if self.content_type
            else "Unspecified Model"
        )
        linked_object_description = (
            str(
                self.content_object) if self.content_object else f"None ({model_name})"
        )
        return f"{linked_object_description} linked to {self.__class__.__name__}"
