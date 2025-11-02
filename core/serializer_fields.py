import io

import filetype
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from drf_extra_fields.fields import Base64FileField, Base64ImageField
from drf_yasg import openapi
from rest_framework import serializers


class RelatedObjectSerializerField(serializers.PrimaryKeyRelatedField):
    """
    A custom field that represents a related object using its primary key in POST requests
    and returns the serialized object in GET requests.

    This field is useful for handling relationships where you want to use the object representation
    in GET responses while accepting the primary key in POST requests.

    Args:
        serializer_class (Serializer): The serializer class used to serialize the related object.
        many (bool, optional): Indicates whether the serializer represents a single object or a collection.
            Defaults to False.
        **kwargs: Additional keyword arguments accepted by PrimaryKeyRelatedField.

    Example:
        Consider a CompanySerializer where `users` represents related users:

        class CompanySerializer(serializers.ModelSerializer):
            users = RelatedObjectSerializerField(
                queryset=User.objects.all(), serializer_class=MinimalUserSerializer, required=False, many=True
            )

            class Meta:
                model = Company
                fields = ["id", "name", "users"]

        Usage in GET request (response):
        {
            "id": 1,
            "name": "Example Inc.",
            "users": [
                {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com"
                },
                {
                    "id": 2,
                    "username": "jane_smith",
                    "email": "jane@example.com"
                }
            ]
        }

        Usage in POST request (request):
        {
            "name": "New Company",
            "users": [1, 2, 3]  # IDs of related users
        }
    """

    def __init__(self, serializer_class, **kwargs):
        """
        Initialize the RelatedObjectSerializerField.

        Args:
            serializer_class (Serializer): The serializer class used to serialize the related object.
            **kwargs: Additional keyword arguments accepted by PrimaryKeyRelatedField.
        """
        self.serializer_class = serializer_class
        self.serializer_class_many = kwargs.pop("many", False)
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        """
        Override to disable optimization for serializing objects using only primary keys.
        This ensures the serializer is used for GET requests.
        """
        return False

    def to_representation(self, value):
        """
        Convert the related object to its serialized representation for GET requests.

        Args:
            value: The related object instance.

        Returns:
            dict or list: Serialized representation of the related object(s).
        """
        serializer = self.serializer_class(value, many=self.serializer_class_many)
        return serializer.data

    def to_internal_value(self, data):
        """
        Convert the input primary key(s) to a related object instance for POST requests.

        Args:
            data: Primary key(s) provided in the request.

        Returns:
            Model instance or list of instances.
        """
        if self.serializer_class_many and not isinstance(data, list):
            raise serializers.ValidationError(
                "Expected a list of primary keys for a many relationship."
            )
        return super().to_internal_value(data)


class RecursiveField(serializers.Serializer):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_INTEGER,
            "title": "Recursive Field",
            "description": "A recursive field",
            "read_only": False,
        }

    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


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


class Base64FileField(Base64FileField):
    """
    A django-rest-framework field for handling file-uploads through raw post data.
    """

    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_STRING,
            "title": "File Content",
            "description": "Content of the base64 File encoded",
            "read_only": False,  # <-- FIX
            "format": openapi.FORMAT_BASE64,
        }

    ALLOWED_TYPES = (
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "csv",
        "txt",
        "rtf",
        "ppt",
        "pptx",
        "jpeg",
        "jpg",
        "png",
        "gif",
        "webp",
    )
    INVALID_FILE_MESSAGE = _("Please upload a valid file.")
    INVALID_TYPE_MESSAGE = _("The type of the file couldn't be determined.")

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
