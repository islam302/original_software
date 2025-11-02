import re

from constance import config
from crum import get_current_user
from rest_framework import serializers
from rest_framework.utils import model_meta
from django.db import transaction


from core.serializer_fields import (
    Base64ImageField,
    RecursiveField,
    RelatedObjectSerializerField,
)
from core.utils import NoUpdateMixin
from products.models import (
    KeyUsersCount,
    KeyValidity,
    Product,
    ProductImage,
    ProductKey,
    ProductOption,
    ProductSection,
    ProductWholesalePricing,
    SpecialOffer
)

from authentication.serializers import UserDetailsSerializer
from authentication.models import User


class KeyUsersCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyUsersCount
        fields = ("id", "count")


class KeyValiditySerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyValidity
        fields = ("id", "validity", "validity_unit")


class NestedProductImageSerializer(serializers.ModelSerializer):
    image_file = Base64ImageField(required=True)

    class Meta:
        model = ProductImage
        fields = (
            "id",
            "image_file",
        )


class NestedProductSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSection
        fields = ("id", "seq", "title", "title_ar", "content", "content_ar")


class NestedProductOptionSerializer(serializers.ModelSerializer):
    keys_users_count = RelatedObjectSerializerField(
        queryset=KeyUsersCount.objects.all(),
        serializer_class=KeyUsersCountSerializer,
        required=True,
        many=False,
    )
    keys_validity = RelatedObjectSerializerField(
        queryset=KeyValidity.objects.all(),
        serializer_class=KeyValiditySerializer,
        required=True,
        many=False,
    )

    class Meta:
        model = ProductOption
        fields = (
            "id",
            "seq",
            "parent_product",
            "keys_users_count",
            "keys_validity",
            "product",
        )


class NestedProductKeySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductKey
        fields = (
            "id",
            "key",
            "is_used",
            "is_viewed",
            "used_at",
            "used_by",
            "used_order",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "is_used",
            "is_viewed",
            "used_order",
            "used_at",
            "used_by",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )


class NestedProductWholesalePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductWholesalePricing
        fields = (
            "id",
            "wholesale_user_type",
            "price",
            "price_in_usd",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )


class ProductSerializer(NoUpdateMixin, serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name", read_only=True)
    category_name_ar = serializers.CharField(
        source="category.name_ar", read_only=True)
    sub_category_name = serializers.CharField(
        source="sub_category.name", read_only=True
    )
    sub_category_name_ar = serializers.CharField(
        source="sub_category.name_ar", read_only=True
    )
    company_name = serializers.CharField(source="company.name", read_only=True)
    company_name_ar = serializers.CharField(
        source="company.name_ar", read_only=True)

    keys_users_count = RelatedObjectSerializerField(
        queryset=KeyUsersCount.objects.all(),
        serializer_class=KeyUsersCountSerializer,
        required=False,
        many=False,
    )
    keys_validity = RelatedObjectSerializerField(
        queryset=KeyValidity.objects.all(),
        serializer_class=KeyValiditySerializer,
        required=False,
        many=False,
    )

    images = NestedProductImageSerializer(
        many=True, read_only=False, required=False)
    sections = NestedProductSectionSerializer(
        many=True, read_only=False, required=False
    )
    options = NestedProductOptionSerializer(
        many=True, read_only=False, write_only=True, required=False
    )
    product_keys = NestedProductKeySerializer(
        many=True, read_only=False, required=False
    )
    wholesale_pricings = NestedProductWholesalePricingSerializer(
        many=True, read_only=True, required=False
    )

    # Read only fields
    price_readonly = serializers.SerializerMethodField()
    price_in_usd_readonly = serializers.SerializerMethodField()
    options_readonly = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "name_ar",
            "description",
            "description_ar",
            "keys_users_count",
            "keys_validity",
            "product_keys",
            "options",
            "options_readonly",
            "wholesale_pricings",
            "price",
            "price_readonly",
            "price_in_usd_readonly",
            "old_price",
            "old_price_in_usd",
            "offer_products",
            "is_special_offer",
            "tutorial",
            "download_link",
            "SKU_code",
            "qty",
            "qty_modified_from_zero",
            "is_key_product",
            "is_discounted",
            "is_deleted",
            "keys_qty_unused",
            "keys_qty_unused_2",
            "number_of_keys_to_send_notification",
            "images",
            "sections",
            "available",
            "color",
            "tag",
            "status",
            "status_display",
            "category",
            "category_name",
            "category_name_ar",
            "sub_category",
            "sub_category_name",
            "sub_category_name_ar",
            "company",
            "company_name",
            "company_name_ar",
            "cashback_amount",
            "search_status",
            "has_options",
            "is_option_product",
            "is_deleted",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "wholesale_pricings",
            "is_key_product",
            "keys_qty_unused",
            "is_discounted",
            "is_deleted",
            "category_name",
            "category_name_ar",
            "sub_category_name",
            "sub_category_name_ar",
            "qty_modified_from_zero",
            "status_display",
            "created_by",
            "updated_by",
            "created",
            "modified",
            "has_options",
            "is_option_product",
        )
        write_only_fields = (
            "price",
            "options",
        )
        no_update_fields = (
            "sections",
            "images",
            "options",
            "product_keys",
        )

    def get_price_readonly(self, obj):
        user = get_current_user()
        if user.is_authenticated:
            return (
                obj.wholesale_pricings.filter(
                    wholesale_user_type=user.wholesale_type)
                .first()
                .price
                # first check if there is a user and if the user has a wholesale type
                if user and user.wholesale_type is not None
                else obj.price
            )
        return obj.price

    def get_price_in_usd_readonly(self, obj):
        user = get_current_user()
        if user.is_authenticated:
            return (
                round(
                    obj.wholesale_pricings.filter(
                        wholesale_user_type=user.wholesale_type)
                    .first()
                    .price
                    / config.USD_TO_IQD_EXCHANGE_RATE,
                    2,
                )
                if user.is_authenticated and user.wholesale_type is not None
                else obj.price_in_usd
            )
        return obj.price_in_usd

    def get_options_readonly(self, obj):
        if obj.has_options:
            return NestedProductOptionSerializer(obj.options.all(), many=True).data
        elif obj.is_option_product and obj.option_of.exists():
            return NestedProductOptionSerializer(
                obj.option_of.first().parent_product.options.all(), many=True
            ).data
        return []

    def validate(self, data):
        user = get_current_user()
        if not user.is_staff:
            if "number_of_keys_to_send_notification" in data:
                raise serializers.ValidationError(
                    {
                        "number_of_keys_to_send_notification": "You are not allowed to set this field"
                    }
                )
        return data

    def create(self, validated_data):
        sections_data = validated_data.pop("sections", [])
        images_data = validated_data.pop("images", [])
        options_data = validated_data.pop("options", [])
        product_keys = validated_data.pop("product_keys", [])
        # wholesale_pricings = validated_data.pop("wholesale_pricings", [])
        product = Product.objects.create(**validated_data)
        # for wholesale_pricing in wholesale_pricings:
        #     ProductWholesalePricing.objects.create(product=product, **wholesale_pricing)
        for section_data in sections_data:
            ProductSection.objects.create(product=product, **section_data)
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
        for option_data in options_data:
            ProductOption.objects.create(parent_product=product, **option_data)
        for key in product_keys:
            ProductKey.objects.create(product=product, **key)
        return product

    def delete_bulk(validated_data):
        with transaction.atomic():
            products = Product.objects.filter(id__in=validated_data["ids"])
            for product in products:
                product.is_deleted = True
                product.save()

        return {"message": "Products deleted successfully"}

    def update(self, instance, validated_data):
        validated_data.pop("sections", [])
        validated_data.pop("images", [])
        validated_data.pop("options", [])
        validated_data.pop("product_keys", [])
        # validated_data.pop("wholesale_pricings", [])
        return super(ProductSerializer, self).update(instance, validated_data)

    def to_representation(self, obj):
        # get the original representation
        res = super(ProductSerializer, self).to_representation(obj)

        user = get_current_user()
        if not user.is_staff:
            res.pop("product_keys")
            res.pop("wholesale_pricings")
            res.pop("number_of_keys_to_send_notification")

        # return the modified representation
        return res


class ProductImageSerializer(serializers.ModelSerializer):
    image_file = Base64ImageField(required=True)

    class Meta:
        model = ProductImage
        fields = (
            "id",
            "product",
            "image_file",
        )


class ProductSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSection
        fields = ("id", "product", "seq", "title",
                  "title_ar", "content", "content_ar")


class ProductOptionSerializer(serializers.ModelSerializer):
    keys_users_count = RelatedObjectSerializerField(
        queryset=KeyUsersCount.objects.all(),
        serializer_class=KeyUsersCountSerializer,
        required=True,
        many=False,
    )
    keys_validity = RelatedObjectSerializerField(
        queryset=KeyValidity.objects.all(),
        serializer_class=KeyValiditySerializer,
        required=True,
        many=False,
    )

    class Meta:
        model = ProductOption
        fields = (
            "id",
            "seq",
            "parent_product",
            "keys_users_count",
            "keys_validity",
            "product",
        )


class ProductKeySerializer(serializers.ModelSerializer):
    used_by = RelatedObjectSerializerField(
        queryset=User.objects.all(),
        serializer_class=UserDetailsSerializer,
        required=False,
        many=False,
    )

    class Meta:
        model = ProductKey
        fields = (
            "id",
            "product",
            "key",
            "is_used",
            "is_viewed",
            "used_at",
            "used_by",
            "used_order",
            "product_keys_left",
            "order_number",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "is_used",
            "is_viewed",
            "used_order",
            "used_at",
            "used_by",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )


class ProductWholesalePricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductWholesalePricing
        fields = (
            "id",
            "product",
            "wholesale_user_type",
            "price",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )


class SpecialOfferSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = SpecialOffer
        fields = (
            "id",
            "title",
            "title_ar",
            "image",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
