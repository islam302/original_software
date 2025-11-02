from constance import config
from dal import autocomplete
from dj_rest_auth.views import UserDetailsView
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django_filters import rest_framework as django_filters_rest_framework
from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import exceptions as drf_exceptions
from rest_framework import filters, mixins, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.filters import TransactionAdminFilter, TransactionFilter, UserFilter
from authentication.filters.user import UserCustomFilterBackend

from authentication.models import Transaction, WholesaleUserType
from authentication.serializers import (
    CustomUserDetailsSerializer,
    TransactionAdminSerializer,
    TransactionSerializer,
    WholesaleUserTypeSerializer,
)
from authentication.stats import TransactionStats, UserStats
from core.utils import StandardLimitOffsetPagination
from django.db.models import Sum, F, Case, When, Count, DecimalField, CharField, Value
from django.db.models.functions import TruncDate
from rest_framework.response import Response
from collections import defaultdict
from dj_rest_auth.views import LoginView
from django.contrib.auth import authenticate
from rest_framework import status

UserDetailsView.__doc__ = """
    Reads and updates UserModel fields
    Accepts GET, PUT, PATCH methods.

    Default accepted fields: username, first_name, last_name, birth_date, gender, total_balance, buy_margin, sell_margin
    Default display fields: pk, username, email, first_name, last_name, birth_date, gender, total_balance, buy_margin, sell_margin
    Read-only fields: pk, email

    Returns UserModel fields.
    """
    
class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        # Extract credentials
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is deleted
        if getattr(user, "is_deleted", False):
            return Response(
                {"detail": "This account has been deleted."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if email is verified
        if not getattr(user, "is_email_verified", False):
            return Response(
                {"detail": "Email is not verified."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # If all checks pass, continue with the normal login
        return super().post(request, *args, **kwargs)


class UsersViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = get_user_model().objects.exclude(is_deleted=True)
    serializer_class = CustomUserDetailsSerializer
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        UserCustomFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    ordering_fields = "__all__"
    search_fields = [
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
        "city",
        "country",
    ]
    filterset_class = UserFilter
    
    @swagger_auto_schema(
        operation_description="Get stats for users",
        manual_parameters=[
            openapi.Parameter(
                "type",
                openapi.IN_QUERY,
                description="Filter users by type",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: "UserStats"},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    

    @swagger_auto_schema(
        operation_description="Get stats for users",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering users (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering users (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: "UserStats"},
    )
    @action(
        detail=False,
        methods=["get"],
        filter_backends=None,
        pagination_class=None,
    )
    def stats(self, request):
        queryset = get_user_model().objects.all()
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

        stats = UserStats(queryset)
        return Response(stats.get_stats())

    @swagger_auto_schema(
        operation_description="Get stats for users",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering users (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering users (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: "UserStats"},
    )
    @action(
        detail=False,
        methods=["get"],
        filter_backends=None,
        pagination_class=None,
    )
    def users_created_per_day_per_type(self, request):
        queryset = get_user_model().objects.all()

        # Get start_date and end_date from query parameters
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        # Filter by start_date
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

        # Filter by end_date
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

        # Annotate users with their type
        results = (
            queryset.annotate(
                day=TruncDate("created"),
                user_type=Case(
                    When(wholesale_type_id__isnull=False,
                         then=Value("wholesale_user")),
                    When(is_staff=True, then=Value("admin")),
                    default=Value("normal_user"),
                    output_field=CharField(),
                ),
            )
            .values("day", "user_type")
            .annotate(user_count=Count("id"))
            .order_by("-day", "user_type")
        )

        # Reformat results into the desired structure
        structured_results = defaultdict(
            lambda: {"day": None, "normal_user": 0, "wholesale_user": 0, "admin": 0})

        for result in results:
            day = result["day"]
            user_type = result["user_type"]
            user_count = result["user_count"]

            structured_results[day]["day"] = day
            structured_results[day][user_type] = user_count

        # Convert structured results to a list
        formatted_response = list(structured_results.values())

        return Response(formatted_response)

    @action(
        detail=True,
        methods=["get"],
        url_path="set-superuser",
    )
    def set_superuser(self, request, pk=None):
        user = self.get_object()
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return Response({"result": "user is now superuser"})

    @action(
        detail=True,
        methods=["get"],
        url_path="unset-superuser",
    )
    def unset_superuser(self, request, pk=None):
        user = self.get_object()
        user.is_superuser = False
        user.is_staff = False
        user.save()
        return Response({"result": "user is now not superuser"})

    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[permissions.IsAdminUser],
        url_path="delete-bulk",
    )
    @swagger_auto_schema(
        operation_description="Soft delete a multiple users",
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
    def delete_bulk(self, request):
        """
        Delete multiple objects.
        """
        CustomUserDetailsSerializer.delete_bulk(request)
        return Response({"stats": "Users deleted successfully."})

    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[permissions.IsAdminUser],
        url_path="deactivate-bulk",
    )
    @swagger_auto_schema(
        operation_description="Soft delete a multiple users",
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
    def deactivate_bulk(self, request):
        """
        Delete multiple objects.
        """
        CustomUserDetailsSerializer.deactivate_bulk(request)
        return Response({"stats": "Users deleted successfully."})

    @action(
        detail=True,
        methods=["patch"],
        url_path="set-hidden",
        permission_classes=[permissions.IsAdminUser],

    )
    @swagger_auto_schema(
        request_body=no_body,
        operation_description="Set user as hidden",
        responses={200: "User is now hidden"},
    )
    def set_hidden(self, request, pk=None):
        user = self.get_object()
        user.hidden = True
        user.save()
        return Response({"result": "user is now hidden"})

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
        get_user_model().objects.filter(hidden=False).update(hidden=True)
        return Response({"results": "All users have been hidden."})


class DeleteUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = self.request.user
        user.is_active = False
        user.save()
        return Response({"result": "user delete"})


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "show_current_day",
                openapi.IN_QUERY,
                description="Filter transactions of the current day",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "show_current_month",
                openapi.IN_QUERY,
                description="Filter transactions of the current month",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "show_current_year",
                openapi.IN_QUERY,
                description="Filter transactions of the current year",
                type=openapi.TYPE_BOOLEAN,
            ),
        ],
    ),
)
class TransactionViews(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = ["user__username", "user__email"]
    filterset_class = TransactionFilter
    ordering_fields = "__all__"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Transaction.objects.filter(user=self.request.user)
        return Transaction.objects.none()


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "show_current_day",
                openapi.IN_QUERY,
                description="Filter transactions of the current day",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "show_current_month",
                openapi.IN_QUERY,
                description="Filter transactions of the current month",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "show_current_year",
                openapi.IN_QUERY,
                description="Filter transactions of the current year",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "created_after",
                openapi.IN_QUERY,
                description="Filter transactions created after the given date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created_before",
                openapi.IN_QUERY,
                description="Filter transactions created before the given date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created",
                openapi.IN_QUERY,
                description="DON'T USE. Use created_after and created_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "user__id",
                openapi.IN_QUERY,
                description="Filter transactions by user id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "related_order__id",
                openapi.IN_QUERY,
                description="Filter transactions by related order id",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    ),
)
class TransactionAdminViews(viewsets.ModelViewSet):
    serializer_class = TransactionAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardLimitOffsetPagination
    queryset = Transaction.objects.all()
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    search_fields = [
        "user__username",
        "user__email",
        "transaction_type",
        "description",
        "related_order__id",
        "related_order__order_number",
    ]
    filterset_class = TransactionAdminFilter
    ordering_fields = "__all__"

    @swagger_auto_schema(
        operation_description="Get stats for transactions",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering transactions (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering transactions (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: "TransactionStats"},
    )
    @action(
        detail=False,
        methods=["get"],
        filter_backends=None,
        pagination_class=None,
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

        stats = TransactionStats(queryset)
        return Response(stats.get_stats())


class TransactionUserAutocompleteView(autocomplete.Select2QuerySetView):
    """Select2 autocomplete view class to return queryset for chained Select2 field
    on admin page depending on specific field value"""

    def get_queryset(self):
        if not self.request.user.is_staff:
            return get_user_model().objects.none()

        queryset = get_user_model().objects.all()
        query = self.q
        if query:
            queryset = queryset.filter(email__icontains=query)
        return queryset


class ConfigViewSet(
    viewsets.ViewSet,
):
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=["get"], url_path="")
    def get(self, request):
        return Response(
            {
                "USD_TO_IQD_EXCHANGE_RATE": config.USD_TO_IQD_EXCHANGE_RATE,
            }
        )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "value": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="The value to set the key to",
                ),
            },
        ),
        manual_parameters=[
            openapi.Parameter(
                "key",
                openapi.IN_PATH,
                description="The key to set the value of",
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    @action(detail=False, methods=["patch"], url_path="(?P<key>[^/.]+)")
    def patch(self, request, *args, **kwargs):
        # there user should provide the key in path and value in body
        key = kwargs.get("key")
        value = request.data.get("value")
        if not hasattr(config, key):
            raise serializers.ValidationError(
                {
                    "key": "Invalid key",
                }
            )
        setattr(config, key, value)
        return Response(
            {
                key: getattr(config, key),
            }
        )


class WholesaleUserTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = WholesaleUserType.objects.all()
    serializer_class = WholesaleUserTypeSerializer
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = [
        "title",
    ]
    ordering_fields = "__all__"
