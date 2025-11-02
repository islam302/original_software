from rest_framework import serializers

from core.serializer_fields import Base64FileField
from files.models import File
from django.db import transaction



class FileSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)

    class Meta:
        model = File
        fields = (
            "id",
            "file",
        )
        read_only_fields = (
            "id",
            "file",
        )
        
