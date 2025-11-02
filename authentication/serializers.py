from dj_rest_auth.serializers import PasswordResetSerializer, UserDetailsSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction


from .forms import CustomResetPasswordForm
from .models import Transaction, WholesaleUserType

# Get the UserModel
UserModel = get_user_model()


class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta:
        extra_fields = []
        # see https://github.com/iMerica/dj-rest-auth/issues/181
        # UserModel.XYZ causing attribute error while importing other
        # classes from `serializers.py`. So, we need to check whether the auth model has
        # the attribute or not
        if hasattr(UserModel, "id"):
            extra_fields.append("id")
        if hasattr(UserModel, "USERNAME_FIELD"):
            extra_fields.append(UserModel.USERNAME_FIELD)
        if hasattr(UserModel, "EMAIL_FIELD"):
            extra_fields.append(UserModel.EMAIL_FIELD)
        if hasattr(UserModel, "first_name"):
            extra_fields.append("first_name")
        if hasattr(UserModel, "last_name"):
            extra_fields.append("last_name")
        if hasattr(UserModel, "birth_date"):
            extra_fields.append("birth_date")
        if hasattr(UserModel, "gender"):
            extra_fields.append("gender")
        if hasattr(UserModel, "phone"):
            extra_fields.append("phone")
        if hasattr(UserModel, "is_wholesale"):
            extra_fields.append("is_wholesale")
        if hasattr(UserModel, "wholesale_type"):
            extra_fields.append("wholesale_type")
        if hasattr(UserModel, "country"):
            extra_fields.append("country")
        if hasattr(UserModel, "city"):
            extra_fields.append("city")
        if hasattr(UserModel, "is_email_verified"):
            extra_fields.append("is_email_verified")
        if hasattr(UserModel, "wallet_balance"):
            extra_fields.append("wallet_balance")
        if hasattr(UserModel, "wallet_balance_usd"):
            extra_fields.append("wallet_balance_usd")
        if hasattr(UserModel, "is_active"):
            extra_fields.append("is_active")
        if hasattr(UserModel, "is_staff"):
            extra_fields.append("is_staff")
        if hasattr(UserModel, "is_superuser"):
            extra_fields.append("is_superuser")
        if hasattr(UserModel, "total_orders"):
            extra_fields.append("total_orders")
        if hasattr(UserModel, "total_orders_price"):
            extra_fields.append("total_orders_price")
        if hasattr(UserModel, "role"):
            extra_fields.append("role")
        if hasattr(UserModel, "last_order_date"):
            extra_fields.append("last_order_date")
        if hasattr(UserModel, "created"):
            extra_fields.append("created")
        if hasattr(UserModel, "hidden"):
            extra_fields.append("hidden")
        if hasattr(UserModel, "is_deleted"):
            extra_fields.append("is_deleted")
        model = UserModel
        fields = ("pk", *extra_fields)
        read_only_fields = (
            "email",
            "is_wholesale",
            "is_email_verified",
            "wallet_balance",
            "wallet_balance_usd",
            "is_staff",
            "is_superuser",
            "created",
        )
        
    def delete_bulk(request):
        """
        Delete multiple objects.
        """
        with transaction.atomic():
            users = UserModel.objects.filter(pk__in=request.data.get("ids"))
            for user in users:
                user.is_deleted = True
                user.is_active = False
                user.save()

        return {"stats": "Users deleted successfully."}

    def deactivate_bulk(request):
        """
        Deactivate multiple objects.
        """
        with transaction.atomic():
            users = UserModel.objects.filter(pk__in=request.data.get("ids"))
            for user in users:
                user.is_active = False
                user.save()

        return {"stats": "Users deactivated successfully."}


class CustomPasswordResetSerializer(PasswordResetSerializer):
    @property
    def password_reset_form_class(self):
        return CustomResetPasswordForm


class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Transaction
        fields = (
            "id",
            "transaction_type",
            "user",
            "username",
            "amount",
            "amount_usd",
            "description",
            "related_order",
            "created",
            "modified",
        )
        read_only_fields = ("id", "created", "modified", "related_order")


class TransactionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "transaction_type",
            "user",
            "username",
            "amount",
            "amount_usd",
            "description",
            "related_order",
            "created",
            "modified",
        )
        read_only_fields = ("id", "created", "modified", "related_order")


class WholesaleUserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WholesaleUserType
        fields = (
            "id",
            "title",
            "negative_limit",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
