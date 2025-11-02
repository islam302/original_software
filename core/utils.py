import io
import os
import uuid

import filetype
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from drf_extra_fields.fields import Base64ImageField
from drf_yasg import openapi
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination


class PublishedManager(models.Manager):
    def get_queryset(self: models.Manager) -> models.QuerySet:
        published = Q(publish=True)
        return super().get_queryset().filter(published)


def get_upload_path(instance, filename: str) -> str:
    # get the file extension and filename without extension
    filename, ext = os.path.splitext(filename)
    # remove forbidden characters
    filename = slugify(filename)
    # generate a unique filename
    filename = f"{filename}{uuid.uuid4().hex}{ext}"
    model = instance.__class__._meta
    path = model.verbose_name_plural.lower().replace(" ", "_")
    return os.path.join(path, filename)


class Base64ImageField(Base64ImageField):
    """
    A django-rest-framework field for handling image-uploads through raw post data.
    It uses base64 for en-/decoding the contents of the file.
    """

    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_STRING,
            "title": "Image Content",
            "description": "Content of the base64 Image encoded",
            "read_only": False,  # <-- FIX
            "format": openapi.FORMAT_BASE64,
        }

    ALLOWED_TYPES = ("jpeg", "jpg", "png", "gif", "webp")
    INVALID_FILE_MESSAGE = _("Please upload a valid image.")
    INVALID_TYPE_MESSAGE = _("The type of the image couldn't be determined.")

    def get_file_extension(self, filename, decoded_file):
        extension = filetype.guess_extension(decoded_file)
        if extension is None:
            try:
                # Try with PIL as fallback if format not detected
                # with `filetype` module
                from PIL import Image

                image = Image.open(io.BytesIO(decoded_file))
            except (ImportError, OSError):
                raise ValidationError(self.INVALID_FILE_MESSAGE)
            else:
                extension = image.format.lower()

        return "jpg" if extension == "jpeg" else extension


class StandardLimitOffsetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class NoUpdateMixin(serializers.ModelSerializer):
    def get_extra_kwargs(self):
        kwargs = super().get_extra_kwargs()
        no_update_fields = getattr(self.Meta, "no_update_fields", None)

        if self.instance and no_update_fields:
            for field in no_update_fields:
                kwargs.setdefault(field, {})
                kwargs[field]["read_only"] = True

        return kwargs
