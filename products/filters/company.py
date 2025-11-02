from django_filters import rest_framework as rest_framework_filters

from products.models import Company


class CompanyFilter(rest_framework_filters.FilterSet):
    class Meta:
        model = Company
        fields = ["show_in_home"]
