from django.db.models import Q
from django_filters import rest_framework as django_filters_rest_framework

from orders.models import Order


class OrderFilter(django_filters_rest_framework.FilterSet):
    approved_at = django_filters_rest_framework.DateFromToRangeFilter()
    rejected_at = django_filters_rest_framework.DateFromToRangeFilter()
    returned_at = django_filters_rest_framework.DateFromToRangeFilter()
    canceled_at = django_filters_rest_framework.DateFromToRangeFilter()
    paid_at = django_filters_rest_framework.DateFromToRangeFilter()
    payment_failed_at = django_filters_rest_framework.DateFromToRangeFilter()
    created = django_filters_rest_framework.DateFromToRangeFilter()

    class Meta:
        model = Order
        fields = [
            "order_number",
            "status",
            "status",
            "payment_method",
            "payment_status",
            "is_viewed",
            "approved_by__id",
            "rejected_by__id",
            "returned_by__id",
            "canceled_by__id",
            "paid_by__id",
            "payment_failed_by__id",
            "created_by__id",
            "created_by__username",
            "created_by__email",
            "created_by__phone",
            "created_by__phone_2",
            "created_by__country",
            "created_by__city",
            "created_by__first_name",
            "created_by__last_name",
        ]

