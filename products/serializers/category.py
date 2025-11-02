from rest_framework import serializers
from rest_framework.utils import model_meta

from core.serializer_fields import Base64ImageField
from core.utils import NoUpdateMixin
from products.models import Category, CategorySlider, SubCategory, SubCategorySlider


class SubCategorySliderSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = SubCategorySlider
        fields = (
            "id",
            "sub_category",
            "path",
            "image",
            "created",
        )
        read_only_fields = (
            "id",
            "created",
        )


class NestedSubCategorySliderSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = SubCategorySlider
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


class SubCategorySerializer(NoUpdateMixin, serializers.ModelSerializer):
    sub_category_slider_items = NestedSubCategorySliderSerializer(
        many=True, read_only=False, required=False
    )
    image_file = Base64ImageField(required=False)

    class Meta:
        model = SubCategory
        fields = (
            "id",
            "seq",
            "name",
            "name_ar",
            "category",
            "category_name",
            "image_file",
            "sub_category_slider_items",
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
        no_update_fields = ("sub_category_slider_items",)

    def create(self, validated_data):
        sub_category_slider_items_data = validated_data.pop("sub_category_slider_items")
        sub_category = SubCategory.objects.create(**validated_data)
        for sub_category_slider_item_data in sub_category_slider_items_data:
            SubCategorySlider.objects.create(
                sub_category=sub_category, **sub_category_slider_item_data
            )
        return sub_category

    def update(self, instance, validated_data):
        validated_data.pop("sub_category_slider_items", [])
        return super(SubCategorySerializer, self).update(instance, validated_data)


class NestedSubCategorySerializer(serializers.ModelSerializer):
    sub_category_slider_items = NestedSubCategorySliderSerializer(
        many=True, read_only=False, required=False
    )
    image_file = Base64ImageField(required=False)

    class Meta:
        model = SubCategory
        fields = (
            "id",
            "seq",
            "name", 
            "name_ar",
            "image_file",
            "sub_category_slider_items",
            "is_deleted",
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

    def create(self, validated_data):
        sub_category_slider_items_data = validated_data.pop("sub_category_slider_items")
        sub_category = SubCategory.objects.create(**validated_data)
        for sub_category_slider_item_data in sub_category_slider_items_data:
            SubCategorySlider.objects.create(
                sub_category=sub_category, **sub_category_slider_item_data
            )
        return sub_category

    def update(self, instance, validated_data):
        validated_data.pop("sub_category_slider_items", [])
        return super(NestedSubCategorySerializer, self).update(instance, validated_data)


class CategorySliderSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = CategorySlider
        fields = (
            "id",
            "category",
            "path",
            "image",
            "created",
        )
        read_only_fields = (
            "id",
            "created",
        )


class NestedCategorySliderSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = CategorySlider
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


class CategorySerializer(NoUpdateMixin, serializers.ModelSerializer):
    category_slider_items = NestedCategorySliderSerializer(
        many=True, read_only=False, required=False
    )
    sub_categories = NestedSubCategorySerializer(
        many=True, read_only=False, required=False
    )
    image_file = Base64ImageField(required=False)

    class Meta:
        model = Category
        fields = (
            "id",
            "seq",
            "name",
            "name_ar",
            "image_file",
            "category_slider_items",
            "sub_categories",
            "is_deleted",
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
        no_update_fields = (
            "category_slider_items",
            "sub_categories",
        )
        

    def create(self, validated_data):
        sub_categories_data = validated_data.pop("sub_categories", [])
        category_slider_items = validated_data.pop("category_slider_items", [])
        category = Category.objects.create(**validated_data)
        for category_slider_item_data in category_slider_items:
            CategorySlider.objects.create(
                category=category, **category_slider_item_data
            )
        for sub_category_data in sub_categories_data:
            sub_category_slider_items_data = sub_category_data.pop(
                "sub_category_slider_items"
            )
            sub_category = SubCategory.objects.create(
                category=category, **sub_category_data
            )
            for sub_category_slider_item_data in sub_category_slider_items_data:
                SubCategorySlider.objects.create(
                    sub_category=sub_category, **sub_category_slider_item_data
                )
        return category

    def update(self, instance, validated_data):
        validated_data.pop("category_slider_items", [])
        validated_data.pop("sub_categories", [])
        return super(CategorySerializer, self).update(instance, validated_data)
    
    def to_representation(self, instance):
        """Customize serialization to exclude deleted sub-categories."""
        data = super().to_representation(instance)
        data["sub_categories"] = [
            sub for sub in data["sub_categories"] if not sub.get("is_deleted", False)
        ]
        return data
