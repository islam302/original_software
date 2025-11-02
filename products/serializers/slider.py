from rest_framework import serializers

from core.serializer_fields import Base64ImageField
from products.models import Slider


class SliderSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = Slider
        fields = (
            "id",
            "path",
            "image",
            "created",
        )
        read_only_fields = (
            "id",
            "created",
        )
