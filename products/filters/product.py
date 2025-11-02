from django.db.models import Q
from django_filters import rest_framework as django_filters_rest_framework

from products.models import Product


class ProductFilter(django_filters_rest_framework.FilterSet):
    qty = django_filters_rest_framework.NumberFilter(
        field_name="qty", lookup_expr="gte"
    )
    is_discounted = django_filters_rest_framework.BooleanFilter(
        field_name="old_price", lookup_expr="isnull", exclude=True
    )

    class Meta:
        model = Product
        fields = [
            "tag",
            "has_options",
            "is_option_product",
            "category__id",
            "sub_category__id",
            "company__id",
            "is_special_offer",
        ]


class ProductCustomFilterBackend:
    """
    Custom filter backend for filtering products based on query parameters.

    This filter backend provides functionality to filter products based on
    whether they are discounted or not, and also allows searching for products
    based on a query string.

    Attributes:
        None

    Methods:
        filter_queryset: Filters the queryset based on the request and view.

    Usage:
        This filter backend can be used by adding it to the `filter_backends`
        attribute of a view class or viewset.

        Example:
            class ProductViewSet(viewsets.ModelViewSet):
                queryset = Product.objects.all()
                serializer_class = ProductSerializer
                filter_backends = [ProductCustomFilterBackend]
    """

    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get("search", None)
        status_display = request.query_params.get("status_display", None)
        if search:
            search = search.strip()
            # take the first 3 characters of the query string
            # and search for the product name and name_ar
            # and take the last 3 characters of the query string
            # but only if the query string is at least 3 characters long
            # else search with the full query string
            # we also have to normalize the query string to lowercase
            # so that the search is case-insensitive
            if len(search) >= 3:
                queryset = queryset.filter(
                    Q(name__istartswith=search[:3])
                    | Q(name_ar__istartswith=search[:3])
                    | Q(name__iendswith=search[-3:])
                    | Q(name_ar__iendswith=search[-3:])
                    | Q(name__icontains=search)
                    | Q(name_ar__icontains=search)
                    | Q(category__name__icontains=search)
                    | Q(qty__icontains=search)
                    | Q(price__icontains=search)
                    | Q(old_price__icontains=search)
                    | Q(search_status__icontains=search)
                    | Q(created__icontains=search)

                )
            else:
                queryset = queryset.filter(
                    Q(name__icontains=search) | Q(name_ar__icontains=search)
                    | Q(category__name__icontains=search)
                    | Q(qty__icontains=search)
                    | Q(price__icontains=search)
                    | Q(old_price__icontains=search)
                    | Q(search_status__icontains=search)
                    | Q(created__icontains=search)
                )

        if status_display == "active":
            queryset = queryset.filter(
                status=Product.STATUS.active).filter(is_discounted=False)
        elif status_display == "inactive":
            queryset = queryset.filter(status=Product.STATUS.inactive)
        elif status_display == "discounted":
            queryset = queryset.filter(is_discounted=True).filter(
                status=Product.STATUS.active)

        return queryset
