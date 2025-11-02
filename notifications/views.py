from django.utils.decorators import method_decorator
from django_filters import rest_framework as django_filters_rest_framework
from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.response import Response


from rest_framework import filters, permissions, serializers, viewsets

from core.utils import StandardLimitOffsetPagination
from notifications.filters import NotificationFilter
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="related_user__id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="related user id",
            ),
            openapi.Parameter(
                name="created_after",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="created after date",
            ),
            openapi.Parameter(
                name="created_before",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="created before date",
            ),
            openapi.Parameter(
                name="created",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="DON'T USE. Use created_after and created_before instead",
            ),
            openapi.Parameter(
                name="linked_model_name",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="linked model name",
            ),
        ],
    ),
)
class NotificationViews(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = ["description"]
    ordering_fields = "__all__"
    ordering = ["-created"]
    filterset_class = NotificationFilter

    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[permissions.IsAdminUser],
        url_path="set-hidden",
    )
    @swagger_auto_schema(
        operation_description="Set hidden",
        request_body=no_body,
        responses={200: "Success"},
    )
    def set_hidden(self, request, pk=None):
        instance = self.get_object()
        instance.hidden = True
        instance.save()
        return Response({"results": "The notification has been hidden."})

    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[permissions.IsAdminUser],
        url_path="set-all-hidden",
    )
    @swagger_auto_schema(
        operation_description="Set all hidden",
        request_body=no_body,
        responses={200: "Success"},
    )
    def set_all_hidden(self, request):
        self.queryset.filter(hidden=False).update(hidden=True)
        return Response({"results": "All notifications have been hidden."})
