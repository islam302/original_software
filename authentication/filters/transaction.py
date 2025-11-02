from django.utils import timezone
from django_filters import rest_framework as rest_framework_filters

from authentication.models import Transaction


class TransactionFilter(rest_framework_filters.FilterSet):
    show_current_day = rest_framework_filters.BooleanFilter(
        field_name="created", method="filter_current_day"
    )
    show_current_month = rest_framework_filters.BooleanFilter(
        field_name="created", method="filter_current_month"
    )
    show_current_year = rest_framework_filters.BooleanFilter(
        field_name="created", method="filter_current_year"
    )

    def filter_current_day(self, queryset, name, value):
        if value:
            return queryset.filter(created__day=timezone.now().day)
        return queryset

    def filter_current_month(self, queryset, name, value):
        if value:
            return queryset.filter(created__month=timezone.now().month)
        return queryset

    def filter_current_year(self, queryset, name, value):
        if value:
            return queryset.filter(created__year=timezone.now().year)
        return queryset

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
        ]


class TransactionAdminFilter(rest_framework_filters.FilterSet):
    show_current_day = rest_framework_filters.BooleanFilter(
        field_name="created", method="filter_current_day"
    )
    show_current_month = rest_framework_filters.BooleanFilter(
        field_name="created", method="filter_current_month"
    )
    show_current_year = rest_framework_filters.BooleanFilter(
        field_name="created", method="filter_current_year"
    )
    created = rest_framework_filters.DateFromToRangeFilter()

    def filter_current_day(self, queryset, name, value):
        if value:
            return queryset.filter(created__day=timezone.now().day)
        return queryset

    def filter_current_month(self, queryset, name, value):
        if value:
            return queryset.filter(created__month=timezone.now().month)
        return queryset

    def filter_current_year(self, queryset, name, value):
        if value:
            return queryset.filter(created__year=timezone.now().year)
        return queryset

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "user__id",
            "user__username",
            "user__email",
            "user__first_name",
            "user__last_name",
            "related_order__id",
            "related_order__order_number",
        ]
