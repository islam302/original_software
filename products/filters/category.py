from django_filters import rest_framework as rest_framework_filters

from products.models import Category, SubCategory


class CategoryFilter(rest_framework_filters.FilterSet):
    created = rest_framework_filters.DateFromToRangeFilter()


class SubCategoryFilter(rest_framework_filters.FilterSet):
    created = rest_framework_filters.DateFromToRangeFilter()

    class Meta:
        model = SubCategory
        fields = ["category__id"]
