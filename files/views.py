from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema, no_body
from rest_framework import viewsets
from core.permissions import IsAdminUserOrReadOnly, IsAdminUser
from files.models import File
from files.serializers import FileSerializer
from core.utils import StandardLimitOffsetPagination
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import DestroyModelMixin
from django.db import transaction




class FileViewSet(viewsets.ModelViewSet):
    # Allow both JSON and multipart data
    parser_classes = (MultiPartParser,)
    permission_classes = [IsAdminUserOrReadOnly]
    queryset = File.objects.all()
    serializer_class = FileSerializer
    model_object = File
    pagination_class = StandardLimitOffsetPagination

# delete only viwset


class FileDeleteBulkViewSet(GenericViewSet, DestroyModelMixin):
    parser_classes = (MultiPartParser, JSONParser)
    permission_classes = [IsAdminUser]
    queryset = File.objects.all()
    serializer_class = FileSerializer

    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAdminUser],
    )
    @swagger_auto_schema(
        operation_description="Soft delete multiple products",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                )
            },
            required=["ids"],
        ),
        responses={200: openapi.Response("Success")},
    )
    def delete_bulk(self, request):
        """
        Delete multiple objects.
        """
        with transaction.atomic():
            ids = request.data.get("ids", [])
            self.queryset.filter(id__in=ids).delete()
        return Response(status=200)
