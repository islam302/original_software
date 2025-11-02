from django.db.models import Q
from django_filters import rest_framework as django_filters_rest_framework

from orders.models import OrderLine


class OrderLineFilter(django_filters_rest_framework.FilterSet):

    class Meta:
        model = OrderLine
        fields = [
            "created_by__id",
        ]
