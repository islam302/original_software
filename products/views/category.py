from django.utils.decorators import method_decorator
from django_filters import rest_framework as django_filters_rest_framework
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, viewsets

from core.permissions import IsAdminUserOrReadOnly
from core.utils import StandardLimitOffsetPagination
from products.filters import CategoryFilter, SubCategoryFilter
from products.models import Category, CategorySlider, SubCategory, SubCategorySlider
from products.serializers import (
    CategorySerializer,
    CategorySliderSerializer,
    SubCategorySerializer,
    SubCategorySliderSerializer,
)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "created_after",
                openapi.IN_QUERY,
                description="Filter categories created after a date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created_before",
                openapi.IN_QUERY,
                description="Filter categories created before a date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created",
                openapi.IN_QUERY,
                description="DON'T USE. Use created_after and created_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
        ],
    ),
)
class CategoryViews(viewsets.ModelViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = Category.objects.exclude(is_deleted=True)
    serializer_class = CategorySerializer
    model_object = Category
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = [
        "name",
        "name_ar",
    ]
    filterset_class = CategoryFilter
    ordering_fields = "__all__"


class CategorySliderViews(viewsets.ModelViewSet):
    queryset = CategorySlider.objects.all()
    serializer_class = CategorySliderSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = StandardLimitOffsetPagination


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "created_after",
                openapi.IN_QUERY,
                description="Filter categories created after a date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created_before",
                openapi.IN_QUERY,
                description="Filter categories created before a date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created",
                openapi.IN_QUERY,
                description="DON'T USE. Use created_after and created_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
        ],
    ),
)
class SubCategoryViews(viewsets.ModelViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = SubCategory.objects.exclude(is_deleted=True)
    serializer_class = SubCategorySerializer
    model_object = SubCategory
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = [
        "name",
        "name_ar",
        "category__name",
        "category__name_ar",
    ]
    filterset_class = SubCategoryFilter
    ordering_fields = "__all__"


class SubCategorySliderViews(viewsets.ModelViewSet):
    queryset = SubCategorySlider.objects.all()
    serializer_class = SubCategorySliderSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = StandardLimitOffsetPagination
