from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from core.permissions import IsAdminUserOrReadOnly
from core.utils import StandardLimitOffsetPagination
from products.filters import CompanyFilter
from products.models import Company
from products.serializers import CompanySerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from core.permissions import IsAdminUser, IsAdminUserOrReadOnly



class CompanyViews(viewsets.ModelViewSet):
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = Company.objects.exclude(is_deleted=True)
    serializer_class = CompanySerializer
    model_object = Company
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = [
        "name",
        "name_ar",
    ]
    filterset_class = CompanyFilter
    ordering_fields = "__all__"
    
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
        CompanySerializer.delete_bulk(request.data)
        return Response({"stats": "Products deleted successfully."})
