from dal import autocomplete
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils.decorators import method_decorator
from django_filters import rest_framework as django_filters_rest_framework
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from rest_framework import exceptions as drf_exceptions
from django.db.models import Sum, Case, When
from orders.models import OrderLine


from core.permissions import IsAdminUser, IsAdminUserOrReadOnly
from core.utils import StandardLimitOffsetPagination
from products.filters import ProductCustomFilterBackend, ProductFilter
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
from products.serializers import (
    KeyUsersCountSerializer,
    KeyValiditySerializer,
    ProductImageSerializer,
    ProductKeySerializer,
    ProductOptionSerializer,
    ProductSectionSerializer,
    ProductSerializer,
    ProductWholesalePricingSerializer,
    SpecialOfferSerializer
)
from products.stats import ProductStats


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "is_discounted",
                openapi.IN_QUERY,
                description="Filter products with discount",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "has_options",
                openapi.IN_QUERY,
                description="Filter products with options",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "is_option_product",
                openapi.IN_QUERY,
                description="Filter products that are options",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "status_display",
                openapi.IN_QUERY,
                description="Filter products by status",
                type=openapi.TYPE_STRING,
            ),
        ],
    ),
)
class ProductViews(viewsets.ModelViewSet):
    queryset = Product.objects.order_by(
        Coalesce("qty_modified_from_zero", "created").desc(nulls_last=True)
    ).exclude(is_deleted=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    model_object = Product
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        ProductCustomFilterBackend,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = [
        "name",
        "qty",
        "price",
        "old_price",
        "search_status",
        "created",
        "category__name",
    ]
    filterset_class = ProductFilter

    def get_queryset(self):
        if self.request.user.is_staff:
            return Product.objects.all().exclude(is_deleted=True).order_by("created")
        return Product.objects.filter(status=Product.STATUS.active).exclude(is_deleted=True).order_by("created")

    def retrieve(self, request, *args, **kwargs):
        instance = Product.objects.get(pk=kwargs['pk'])
        if (instance.status != Product.STATUS.active or instance.is_deleted) and not request.user.is_staff:
            return Response(status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="top-sold")
    def top_sold_products(self, request):
        # Step 1: Aggregate top sold product IDs with their total sold quantity
        top_product_data = (
            OrderLine.objects
            .values("product_id")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")
        )

        # Step 2: Filter to only active products
        active_products = Product.objects.filter(status="active")
        active_product_ids = set(active_products.values_list("id", flat=True))

        # Step 3: Filter the top products to include only active ones and take top 10
        filtered_top_ids = [item["product_id"]
                            for item in top_product_data if item["product_id"] in active_product_ids][:10]

        # Step 4: Fetch those products and preserve ordering
        preserved_order = Case(
            *[When(id=pk, then=pos) for pos, pk in enumerate(filtered_top_ids)]
        )
        products = Product.objects.filter(
            id__in=filtered_top_ids).order_by(preserved_order)

        # Step 5: Serialize
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get stats for products",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering products (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering products (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: "ProductStats"},
    )
    @action(
        detail=False,
        methods=["get"],
        filter_backends=None,
        pagination_class=None,
        permission_classes=[permissions.IsAdminUser]
    )
    def stats(self, request):
        queryset = self.get_queryset()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            try:
                start_date = parse_date(start_date)
                if not start_date:
                    raise ValueError
            except ValueError:
                raise drf_exceptions.ValidationError(
                    {"start_date": "Invalid date format. Use YYYY-MM-DD."}
                )
            queryset = queryset.filter(created__date__gte=start_date)

        if end_date:
            try:
                end_date = parse_date(end_date)
                if not end_date:
                    raise ValueError
            except ValueError:
                raise drf_exceptions.ValidationError(
                    {"end_date": "Invalid date format. Use YYYY-MM-DD."}
                )
            queryset = queryset.filter(created__date__lte=end_date)

        stats = ProductStats(queryset)
        return Response(stats.get_stats())

    @swagger_auto_schema(
        operation_description="Soft delete a multiple products",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            }
        ),
        responses={200: "Success"},
    )
    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAdminUser],
    )
    def delete_bulk(self, request):
        ProductSerializer.delete_bulk(request.data)
        return Response({"stats": "Products deleted successfully."})

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()


class ProductOptionAutocompleteView(autocomplete.Select2QuerySetView):
    """Select2 autocomplete view class to return queryset for chained Select2 field
    on admin page depending on specific field value"""

    def get_queryset(self):
        if not self.request.user.is_staff:
            return Product.objects.none()
        queryset = Product.objects.all()
        query = self.q
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(name_ar__icontains=query)
            )
        return queryset


class KeyUsersCountViews(viewsets.ModelViewSet):
    queryset = KeyUsersCount.objects.all()
    serializer_class = KeyUsersCountSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = StandardLimitOffsetPagination


class KeyValidityViews(viewsets.ModelViewSet):
    queryset = KeyValidity.objects.all()
    serializer_class = KeyValiditySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = StandardLimitOffsetPagination


class ProductImageViews(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = StandardLimitOffsetPagination


class ProductSectionViews(viewsets.ModelViewSet):
    queryset = ProductSection.objects.all()
    serializer_class = ProductSectionSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = StandardLimitOffsetPagination


class ProductOptionViews(viewsets.ModelViewSet):
    queryset = ProductOption.objects.all()
    serializer_class = ProductOptionSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = StandardLimitOffsetPagination


class ProductKeyViews(viewsets.ModelViewSet):
    queryset = ProductKey.objects.all()
    serializer_class = ProductKeySerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = ["key"]


class ProductWholesalePricingViews(viewsets.ModelViewSet):
    queryset = ProductWholesalePricing.objects.all()
    serializer_class = ProductWholesalePricingSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardLimitOffsetPagination


class SpecialOfferViews(viewsets.ModelViewSet):
    queryset = SpecialOffer.objects.all()
    serializer_class = SpecialOfferSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = ["title", "title_ar"]

    def get_permissions(self):
        if self.action in ['list']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
