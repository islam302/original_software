from django.db.models import Q
from django_filters import rest_framework as django_filters_rest_framework
import django_filters
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification

from products.models import Product
from orders.models import Order, OrderLine


class NotificationFilter(django_filters_rest_framework.FilterSet):
    created = django_filters_rest_framework.DateTimeFromToRangeFilter()
    search = django_filters.CharFilter(method='filter_by_content_object')

    class Meta:
        model = Notification
        fields = [
            "related_user__id",
            "related_user__email",
            "related_user__username",
            "related_user__first_name",
            "related_user__last_name",
            "notification_level",
            "linked_model_name",
            "hidden",
        ]

    def filter_by_content_object(self, queryset, name, value):
        """
        Search in related object fields dynamically.
        """
        product_matches = Product.objects.filter(
            # Add more fields as needed
            Q(name__icontains=value) | Q(category__name__icontains=value)| Q(
                created__icontains=value)
        ).values_list("id", flat=True)

        # Search for Orders where order_number OR customer_name contains the search term

        order_lines = OrderLine.objects.filter(
            product__name__icontains=value
        )

        ids = []

        if order_lines.exists():
            for line in order_lines:
                ids.append(
                    line.order.id
                )

        order_matches = Order.objects.filter(
            Q(order_number__icontains=value) | Q(created_by__username__icontains=value) | Q(
                created_by__email__icontains=value) | Q(
                created__icontains=value) | Q(
                id__in=ids)  # Add more fields as needed
        ).values_list("id", flat=True)

        return queryset.filter(
            Q(object_id__in=product_matches, content_type__model="product") |
            Q(object_id__in=order_matches,
              content_type__model="order") |
            Q(
                description=value
            )
        )
