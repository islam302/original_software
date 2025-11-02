from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from model_utils import Choices
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class CustomRegisterSerializer(RegisterSerializer):
    GENDER = Choices(
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    )

    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=get_user_model().objects.all(),
                message="There is already an account with this email",
            )
        ]
    )
    first_name = serializers.CharField(required=False, max_length=150)
    last_name = serializers.CharField(required=False, max_length=150)
    birth_date = serializers.DateField(required=False)
    gender = serializers.ChoiceField(GENDER, allow_blank=True, required=False)
    phone = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    city = serializers.CharField(required=False)

    def custom_signup(self, request, user):
        user.first_name = self.validated_data.get("first_name", "")
        user.last_name = self.validated_data.get("last_name", "")
        user.birth_date = self.validated_data.get("birth_date", None)
        user.gender = self.validated_data.get("gender", "")
        user.phone = self.validated_data.get("phone", "")
        user.country = self.validated_data.get("country", "")
        user.city = self.validated_data.get("city", "")
        user.save(
            update_fields=[
                "first_name",
                "last_name",
                "birth_date",
                "gender",
                "phone",
                "country",
                "city",
            ]
        )
