import json
from collections import defaultdict
from rest_framework import status
import jwt
import requests
from django.conf import settings
from django.db.models import Case, Count, DecimalField, F, Sum, When
from django.db.models.functions import TruncDate, TruncMonth
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django_filters import rest_framework as django_filters_rest_framework
from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema
from requests.auth import HTTPBasicAuth
from rest_framework import exceptions as drf_exceptions
from rest_framework import filters, permissions, serializers, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from core.utils import StandardLimitOffsetPagination
from orders.filters import OrderFilter, OrderLineFilter
from orders.models import Order, SupportTicket
from orders.serializers import (
    OrderLineSerializer,
    OrderSerializer,
    SupportTicketSerializer,
)
from orders.stats import OrderStats
from products.models import ProductImage

from .models import Order, OrderLine


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "approved_at_after",
                openapi.IN_QUERY,
                description="Filter orders approved after a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "approved_at_before",
                openapi.IN_QUERY,
                description="Filter orders approved before a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "rejected_at_after",
                openapi.IN_QUERY,
                description="Filter orders rejected after a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "rejected_at_before",
                openapi.IN_QUERY,
                description="Filter orders rejected before a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "returned_at_after",
                openapi.IN_QUERY,
                description="Filter orders returned after a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "returned_at_before",
                openapi.IN_QUERY,
                description="Filter orders returned before a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "canceled_at_after",
                openapi.IN_QUERY,
                description="Filter orders canceled after a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "canceled_at_before",
                openapi.IN_QUERY,
                description="Filter orders canceled before a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "paid_at_after",
                openapi.IN_QUERY,
                description="Filter orders paid after a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "paid_at_before",
                openapi.IN_QUERY,
                description="Filter orders paid before a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "payment_failed_at_after",
                openapi.IN_QUERY,
                description="Filter orders payment failed after a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "payment_failed_at_before",
                openapi.IN_QUERY,
                description="Filter orders payment failed before a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created_after",
                openapi.IN_QUERY,
                description="Filter orders created after a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created_before",
                openapi.IN_QUERY,
                description="Filter orders created before a specific date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "approved_at",
                openapi.IN_QUERY,
                description="DON'T USE. Use approved_at_after and approved_at_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "rejected_at",
                openapi.IN_QUERY,
                description="DON'T USE. Use rejected_at_after and rejected_at_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "returned_at",
                openapi.IN_QUERY,
                description="DON'T USE. Use returned_at_after and returned_at_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "canceled_at",
                openapi.IN_QUERY,
                description="DON'T USE. Use canceled_at_after and canceled_at_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "paid_at",
                openapi.IN_QUERY,
                description="DON'T USE. Use paid_at_after and paid_at_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "payment_failed_at",
                openapi.IN_QUERY,
                description="DON'T USE. Use payment_failed_at_after and payment_failed_at_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "created_at",
                openapi.IN_QUERY,
                description="DON'T USE. Use created_at_after and created_at_before instead",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
            ),
            openapi.Parameter(
                "is_viewed",
                openapi.IN_QUERY,
                description="Filter orders that are viewed",
                type=openapi.TYPE_BOOLEAN,
            ),
            openapi.Parameter(
                "approved_by__id",
                openapi.IN_QUERY,
                description="Filter orders approved by user id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "rejected_by__id",
                openapi.IN_QUERY,
                description="Filter orders rejected by user id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "returned_by__id",
                openapi.IN_QUERY,
                description="Filter orders returned by user id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "canceled_by__id",
                openapi.IN_QUERY,
                description="Filter orders canceled by user id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "paid_by__id",
                openapi.IN_QUERY,
                description="Filter orders paid by user id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "payment_failed_by__id",
                openapi.IN_QUERY,
                description="Filter orders payment failed by user id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "created_by__id",
                openapi.IN_QUERY,
                description="Filter orders created by user id",
                type=openapi.TYPE_INTEGER,
            ),
        ],
    ),
)
class OrderViews(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    model_object = Order
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    filterset_class = OrderFilter
    ordering_fields = "__all__"
    search_fields = [
        "order_number",
        "order_line__product__name",
        "created_by__email",
        "payment_method",
    ]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all().order_by("created")
        return Order.objects.filter(created_by=self.request.user.id).order_by("created")

    @action(detail=True, methods=["get"])
    def first_view(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != Order.STATUS.approved:
            raise serializers.ValidationError(
                {"status": "Order is not approved yet."})
        if instance.payment_status != Order.PAYMENT_STATUS.paid:
            raise serializers.ValidationError(
                {"payment_status": "Order is not paid yet."}
            )
        instance.is_viewed = True
        for order_line in instance.order_lines.all():
            for product_key in order_line.order_line_keys.all():
                product_key.key.is_viewed = True
                product_key.save()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(
        auto_schema=None,
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="zain-cash-redirect",
        permission_classes=[permissions.AllowAny],
    )
    def zain_cash_redirect(self, request):
        transaction_token = request.GET.get("token", None)
        client_transaction_success_url = settings.CLIENT_TRANSACTION_SUCCESS_URL
        client_transaction_failed_url = settings.CLIENT_TRANSACTION_FAILED_URL
        if not transaction_token:
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        merchant_secret = settings.ZAIN_CASH_MERCHANT_SECRET
        try:
            result = jwt.decode(
                transaction_token, key=merchant_secret, algorithms=["HS256"]
            )
        except:
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        if result["status"] != "success":
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        order = get_object_or_404(Order, id=result["orderid"])
        order.payment_status = Order.PAYMENT_STATUS.paid
        order.save()
        return HttpResponseRedirect(redirect_to=client_transaction_success_url)

    @swagger_auto_schema(
        auto_schema=None,
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="qi-card-redirect",
        permission_classes=[permissions.AllowAny],
    )
    def qi_card_redirect(self, request):
        transaction_id = request.GET.get("paymentId", None)
        client_transaction_failed_url = settings.CLIENT_TRANSACTION_FAILED_URL
        if not transaction_id:
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        order = get_object_or_404(Order, transaction_id=transaction_id)
        username = settings.QICARD_USERNAME
        password = settings.QICARD_PASSWORD
        transaction_id = order.transaction_id
        url = settings.QICARD_TRANSACTION_STATUS_URL.format(
            transaction_id=transaction_id
        )
        headers = {
            "Content-Type": "application/json",
            "X-Terminal-Id": settings.QICARD_TERMINAL_ID,
        }

        response = requests.get(
            url, headers=headers, auth=HTTPBasicAuth(username, password)
        )
        if response.status_code != 200:
            order.payment_status = Order.PAYMENT_STATUS.failed
            order.save()
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        response_data = response.json()
        if response_data.get("status", "FAILED") != "SUCCESS":
            order.payment_status = Order.PAYMENT_STATUS.failed
            order.save()
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)

        order.payment_status = Order.PAYMENT_STATUS.paid
        order.masked_card_number = response_data["details"]["maskedPan"]
        order.save()

        client_transaction_success_url = settings.CLIENT_TRANSACTION_SUCCESS_URL
        return HttpResponseRedirect(redirect_to=client_transaction_success_url)


    @action(
        detail=False,
        methods=["post"],
        url_path="qi-card-webhook",
        permission_classes=[permissions.AllowAny],
    )
    def qi_card_webhook(self, request, *args, **kwargs):
        # 1) Grab the X-Signature header
        signature = request.headers.get("X-Signature")
        # if not signature:
        #     return Response(
        #         {"error": "Missing X-Signature header"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        # 2) Parse JSON payload
        try:
            payload = request.data
        except Exception:
            return Response(
                {"error": "Invalid JSON payload"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Verify the signature
        valid = Order.verify_qi_card_webhook_signature(
            payload=payload,
            signature_b64=signature,
        )
        if not valid:
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4) Signature is valid — process your business logic
        transaction_id = payload.get("paymentId", None)
        if not transaction_id:
            return Response(
                {"error": "Missing paymentId in payload"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order = get_object_or_404(Order, transaction_id=transaction_id)
        if payload.get("status", "FAILED") != "SUCCESS":
            order.payment_status = Order.PAYMENT_STATUS.failed
            order.save()
            return Response({"status": "failed"}, status=status.HTTP_200_OK)

        order.payment_status = Order.PAYMENT_STATUS.paid
        order.save()

        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        auto_schema=None,
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="fast-pay-redirect",
        permission_classes=[permissions.AllowAny],
    )
    def fast_pay_redirect(self, request):
        order_id = request.GET.get("order_id", None)
        client_transaction_success_url = settings.CLIENT_TRANSACTION_SUCCESS_URL
        client_transaction_failed_url = settings.CLIENT_TRANSACTION_FAILED_URL
        if not order_id:
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        order = get_object_or_404(Order, id=order_id)
        url = settings.FASTPAY_PAYMENT_VALIDATION_URL
        store_id = settings.FASTPAY_STORE_ID
        store_password = settings.FASTPAY_STORE_PASSWORD
        data = {
            "store_id": store_id,
            "store_password": store_password,
            "order_id": order.id,
        }
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            order.payment_status = Order.PAYMENT_STATUS.failed
            order.save()
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        response_data = response.json()
        if response_data.get("code", 200) == 404:
            order.payment_status = Order.PAYMENT_STATUS.failed
            order.save()
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        if response_data.get("data").get("status", "error") != "Success":
            order.payment_status = Order.PAYMENT_STATUS.failed
            order.save()
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)

        order.payment_status = Order.PAYMENT_STATUS.paid
        order.transaction_id = response_data["data"]["transaction_id"]
        order.save()
        return HttpResponseRedirect(redirect_to=client_transaction_success_url)

    @action(
        detail=False,
        methods=["post"],
        url_path="fib-redirect",
        permission_classes=[permissions.AllowAny],
    )
    def fib_redirect(self, request):
        transaction_id = request.data.get("id", None)
        client_transaction_success_url = settings.CLIENT_TRANSACTION_SUCCESS_URL
        client_transaction_failed_url = settings.CLIENT_TRANSACTION_FAILED_URL
        if not transaction_id:
            return HttpResponseRedirect(redirect_to=client_transaction_failed_url)
        order = Order.objects.filter(transaction_id=transaction_id).first()
        url = settings.FIB_PAYMENT_STATUS_URL.format(
            transaction_id=transaction_id)
        access_token = order.auth_fib()
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response_data = response.json()
        if response_data.get("status", "error") == "PAID":
            order.payment_status = Order.PAYMENT_STATUS.paid
            order.save()
            return HttpResponseRedirect(redirect_to=client_transaction_success_url)

        order.payment_status = Order.PAYMENT_STATUS.failed
        order.save()
        return HttpResponseRedirect(redirect_to=client_transaction_failed_url)

    @swagger_auto_schema(
        operation_description="Get stats for orders within a date range",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "whole_sale",
                openapi.IN_QUERY,
                description="Filter orders approved after a specific date",
                type=openapi.TYPE_STRING,
                enum=["true", "false", "all"],
            ),
            openapi.Parameter(
                "payment_method",
                openapi.IN_QUERY,
                description="Filter orders approved after a specific date",
                type=openapi.TYPE_STRING,
                enum=["cash", "zain_cash", "fast_pay", "credit_card", "fib"],
            ),
        ],
        responses={200: "OrderStats"},
    )
    @action(
        detail=False,
        methods=["get"],
        filter_backends=None,
        pagination_class=None,
        permission_classes=[IsAdminUser],
    )
    def stats(self, request):
        queryset = self.get_queryset()

        is_wholesale = "all"
        if request.GET.get("whole_sale", False) == "true":
            is_wholesale = True
        elif request.GET.get("whole_sale", False) == "false":
            is_wholesale = False

        if is_wholesale == "all":
            queryset = self.get_queryset()
        else:
            queryset = self.get_queryset().filter(is_wholesale=is_wholesale)

        payment_method = request.query_params.get("payment_method")
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

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

        stats = OrderStats(queryset)
        return Response(stats.get_stats())

    @swagger_auto_schema(
        operation_description="Approve an order",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "approved_notes": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Notes for approving the order",
                )
            },
        ),
    )
    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsAdminUser],
    )
    def approve_order(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status == Order.STATUS.approved:
            raise serializers.ValidationError(
                {"status": "Order is already approved."})
        if order.status != Order.STATUS.pending:
            raise serializers.ValidationError(
                {"status": "Order is not in pending status."}
            )
        order.status = Order.STATUS.approved
        order.approved_by = request.user
        order.approved_notes = request.data.get("approved_notes", "")
        for order_line in order.order_lines.all():
            order_line.preform_cashback()
        order.save()
        return Response(
            {
                "status": "Order Successfully approved and email sent to the customer",
                "order": OrderSerializer(order).data,
            }
        )

    @swagger_auto_schema(
        operation_description="Reject an order",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "rejected_notes": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Notes for rejecting the order",
                )
            },
        ),
    )
    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsAdminUser],
    )
    def reject_order(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status == Order.STATUS.rejected:
            raise serializers.ValidationError(
                {"status": "Order is already rejected."})
        if order.status != Order.STATUS.pending:
            raise serializers.ValidationError(
                {"status": "Order is not in pending status."}
            )
        order.status = Order.STATUS.rejected
        order.rejected_by = request.user
        order.rejected_notes = request.data.get("rejected_notes", "")
        order.save()
        return Response(
            {
                "status": "Order Successfully rejected and email sent to the customer",
                "order": OrderSerializer(order).data,
            }
        )

    @swagger_auto_schema(
        operation_description="Return an order",
        request_body=no_body,
    )
    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsAdminUser],
    )
    def return_order(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status == Order.STATUS.returned:
            raise serializers.ValidationError(
                {"status": "Order is already returned."})
        order.status = Order.STATUS.returned
        order.returned_by = request.user
        order.save()
        return Response(
            {
                "status": "Order Successfully returned and email sent to the customer",
                "order": OrderSerializer(order).data,
            }
        )

    @swagger_auto_schema(
        operation_description="Mark an order as canceled",
        request_body=no_body,
    )
    @action(
        detail=True,
        methods=["patch"],
        permission_classes=[IsAdminUser],
    )
    def mark_as_paid(self, request, *args, **kwargs):
        order = self.get_object()
        if order.payment_status == Order.PAYMENT_STATUS.paid:
            raise serializers.ValidationError(
                {"payment_status": "Order is already paid."}
            )
        order.payment_status = Order.PAYMENT_STATUS.paid
        order.paid_by = request.user
        order.save()
        return Response(
            {
                "status": "Order Successfully marked as paid",
                "order": OrderSerializer(order).data,
            }
        )

    @swagger_auto_schema(
        operation_description="create order for user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "payment_method": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Payment method",
                ),
                "use_wallet": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="Payment method",
                ),
                "user": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="User id",
                ),
                "order_lines": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "product": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Product id",
                            ),
                            "quantity": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Quantity of the product",
                            ),
                        },
                    ),
                ),
                "address": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Payment method",
                ),
                "notes": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Payment method",
                ),
            },
        ),
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAdminUser],
    )
    def crete_order_for_user(self, request):
        order = OrderSerializer.create_admin(request.data)

        return Response(
            {
                "status": "Order Successfully created",
                "order": OrderSerializer(order).data,
            }
        )

    @swagger_auto_schema(
        operation_description="Delete multiple orders",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description="List of order ids to delete",
                )
            },
        ),
    )
    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAdminUser],
    )
    def delete_bulk(self, request):
        OrderSerializer.delete_bulk(request.data)
        return Response(
            {
                "status": "Orders Successfully deleted",
            }
        )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "product_name",
                openapi.IN_QUERY,
                description="Filter order lines by product name",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "is_wholesale",
                openapi.IN_QUERY,
                description="Filter order lines by product name",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    @action(
        pagination_class=StandardLimitOffsetPagination,
        permission_classes=[IsAdminUser],
        
        detail=False,
        methods=["get"],
        url_path="total_sold_per_product_per_day",
    )
    def total_sold_per_product_per_day(self, request):
        queryset = OrderLine.objects.all().order_by("-created")

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        product_name = request.query_params.get("product_name")
        is_wholesale = request.query_params.get("is_wholesale")
        

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

        if product_name:
            queryset = queryset.filter(product__name__icontains=product_name)
            
        if is_wholesale:
            queryset = queryset.filter(order__is_wholesale=True if is_wholesale.lower() == "wholesale" else False)

        results = (
            queryset.annotate(day=TruncDate("created"))
            .values("product__name", "day")
            .annotate(total_sold=Sum("quantity"))
            .annotate(total_revenue=Sum(F("quantity") * F("product__price")))
            .order_by("day", "product__name")
        )

        all_product_revenue = 0

        for result in results:
            all_product_revenue += result["total_revenue"]

        Fromated_results = {
            "total_revenue": all_product_revenue, "products": results}

        return Response(Fromated_results)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "product_name",
                openapi.IN_QUERY,
                description="Filter order lines by product name",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    @action(
        pagination_class=StandardLimitOffsetPagination,
        detail=False,
        methods=["get"],
        url_path="total_sold_per_product_per_month",
        permission_classes=[IsAdminUser],
        
    )
    def total_sold_per_product_per_month(self, request):
        queryset = OrderLine.objects.all().order_by("-created")

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        product_name = request.query_params.get("product_name")

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

        if product_name:
            queryset = queryset.filter(product__name__icontains=product_name)

        results = (
            queryset.annotate(month=TruncMonth("created"))
            .values("product__name", "month")
            .annotate(total_sold=Sum("quantity"))
            .annotate(total_revenue=Sum(F("quantity") * F("product__price")))
            .order_by("-month", "product__name")
        )

        all_product_revenue = 0

        for result in results:
            all_product_revenue += result["total_revenue"]

        Fromated_results = {
            "total_revenue": all_product_revenue, "products": results}

        return Response(Fromated_results)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="total_payment_per_type_per_day",
        pagination_class=StandardLimitOffsetPagination,
        permission_classes=[IsAdminUser],
        
    )
    def total_per_payment_method_per_day(self, request):
        queryset = Order.objects.all()

        # Filter by start_date
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

        # Aggregate total sales and counts per payment method per day
        results = (
            queryset.annotate(
                day=TruncDate("created"),
                wallet_payment=Case(
                    When(
                        use_wallet=True,
                        then=F("paid_amount_from_wallet"),
                    ),
                    default=0,
                    output_field=DecimalField(),
                ),
            )
            .values("payment_method", "day")
            .annotate(
                total_amount=Sum("total_price"),
                total_wallet_payment=Sum("wallet_payment"),
                count=Count("id"),
            )
            .order_by("day", "payment_method")
        )

        # Reformat results into the desired structure
        structured_results = defaultdict(dict)
        overall_totals = defaultdict(lambda: {"total_amount": 0, "count": 0})

        for result in results:
            day = result["day"]
            payment_method = result["payment_method"]
            total_amount = result["total_amount"]
            transaction_count = result["count"]

            # Add wallet totals as a separate payment method
            if result["total_wallet_payment"] > 0:
                if "Wallet" not in structured_results[day]:
                    structured_results[day]["Wallet"] = 0
                    structured_results[day]["Wallet_count"] = 0

                structured_results[day]["Wallet"] += result["total_wallet_payment"]
                structured_results[day]["Wallet_count"] += 1

                # Update overall totals for wallet
                overall_totals["Wallet"]["total_amount"] += result[
                    "total_wallet_payment"
                ]
                overall_totals["Wallet"]["count"] += 1

            # Add or update the payment method's total and count
            if payment_method not in structured_results[day]:
                structured_results[day][payment_method] = 0
                structured_results[day][f"{payment_method}_count"] = 0

            structured_results[day][payment_method] += total_amount
            structured_results[day][f"{payment_method}_count"] += transaction_count

            # Update overall totals
            overall_totals[payment_method]["total_amount"] += total_amount
            overall_totals[payment_method]["count"] += transaction_count

        # Convert structured results to the desired list format
        formatted_response = [
            {"day": day, **payments} for day, payments in structured_results.items()
        ]

        # Add overall totals at the end
        overall_totals_response = {"day": "Total"}
        for payment_method, data in overall_totals.items():
            overall_totals_response[payment_method] = data["total_amount"]
            overall_totals_response[f"{payment_method}_count"] = data["count"]

        formatted_response.append(overall_totals_response)

        return Response(formatted_response)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    @action(
        pagination_class=StandardLimitOffsetPagination,
        permission_classes=[IsAdminUser],
        detail=False,
        methods=["get"],
        url_path="top_sold_products",
    )
    def top_sold_product(self, request):
        queryset = OrderLine.objects.all().order_by("-created")

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

        results = (
            queryset.values("product__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")
        )

        structured_results = [
            {
                "product": result["product__name"],
                "total_sold": result["total_sold"],
                "total_revenue": OrderLine.objects.filter(
                    product__name=result["product__name"]
                )
                .first()
                .sub_total
                * result["total_sold"],
                "image": ProductImage.objects.filter(
                    product__name=result["product__name"]
                )
                .first()
                .image_file.url,
            }
            for result in results
        ]

        return Response(structured_results)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="top_users_per_type",
        permission_classes=[IsAdminUser],
        
        pagination_class=StandardLimitOffsetPagination,
    )
    def top_users_per_type(self, request):
        queryset = Order.objects.all()

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

        results = (
            queryset.exclude(created_by__wholesale_type=None)
            .values("created_by__username")
            .annotate(total_orders=Count("id"))
            .order_by("-total_orders")
        )

        structured_wholesale = [
            {
                "user": result["created_by__username"],
                "total_orders": result["total_orders"],
            }
            for result in results
        ]

        results = (
            queryset.filter(created_by__wholesale_type=None)
            .values("created_by__username")
            .annotate(total_orders=Count("id"))
            .order_by("-total_orders")
        )

        structured_normal = [
            {
                "user": result["created_by__username"],
                "total_orders": result["total_orders"],
            }
            for result in results
        ]

        structured_results = {
            "wholesale": structured_wholesale,
            "normal": structured_normal,
        }

        return Response(structured_results)

    @swagger_auto_schema(
        operation_description="Get stats for orders within a date range",
        manual_parameters=[
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: "OrderStats"},
    )
    @action(
        detail=False,
        methods=["get"],
        filter_backends=None,
        pagination_class=StandardLimitOffsetPagination,
        permission_classes=[IsAdminUser],
    )
    def wholesale_order_per_month(self, request):
        queryset = Order.objects.filter(
            created_by__wholesale_type__isnull=False)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date:
            try:
                start_date = parse_date(start_date)
                if not start_date:
                    raise ValueError
            except ValueError:
                raise drf_exceptions(
                    {"created_after": "Invalid date format. Use YYYY-MM-DD."}
                )
            queryset = queryset.filter(created__date__gte=start_date)

        if end_date:
            try:
                end_date = parse_date(end_date)
                if not end_date:
                    raise ValueError
            except ValueError:
                raise drf_exceptions(
                    {"created_before": "Invalid date format. Use YYYY-MM-DD."}
                )
            queryset = queryset.filter(created__date__lte=end_date)

        queryset = queryset.filter(created_by__wholesale_type__isnull=False)

        results = (
            queryset.annotate(month=TruncMonth("created"))
            .values("month")
            .annotate(total_orders=Count("id"))
            .annotate(total_amount=Sum("total_price"))
            .order_by("-month")
        )

        return Response(results)

    @swagger_auto_schema(
        operation_description="Get stats for orders within a date range",
        manual_parameters=[
            openapi.Parameter(
                "created_after",
                openapi.IN_QUERY,
                description="Start date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "created_before",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "username",
                openapi.IN_QUERY,
                description="End date for filtering orders (YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: "OrderStats"},
    )
    @action(
        detail=False,
        methods=["get"],
        filter_backends=None,
        pagination_class=StandardLimitOffsetPagination,
        permission_classes=[IsAdminUser],
    )
    def revenu(self, request):
        queryset = OrderLine.objects.all()
        start_date = request.query_params.get("created_after")
        end_date = request.query_params.get("created_before")
        username = request.query_params.get("username")

        if start_date:
            try:
                start_date = parse_date(start_date)
                if not start_date:
                    raise ValueError
            except ValueError:
                raise drf_exceptions(
                    {"created_after": "Invalid date format. Use YYYY-MM-DD."}
                )
            queryset = queryset.filter(created__gte=start_date)

        if end_date:
            try:
                end_date = parse_date(end_date)
                if not end_date:
                    raise ValueError
            except ValueError:
                raise drf_exceptions(
                    {"created_before": "Invalid date format. Use YYYY-MM-DD."}
                )
            queryset = queryset.filter(created__lte=end_date)

        if username:
            queryset = queryset.filter(
                created_by__username__icontains=username)

        paginator = StandardLimitOffsetPagination()

        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = OrderLineSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # In case pagination is not applied (e.g., no results or invalid params)
        serializer = OrderLineSerializer(queryset, many=True)
        return Response(serializer.data)


class OrderLineViews(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = OrderLineSerializer
    model_object = OrderLine
    pagination_class = StandardLimitOffsetPagination
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters_rest_framework.DjangoFilterBackend,
    ]
    queryset = OrderLine.objects.all()
    filterset_class = OrderLineFilter
    ordering_fields = "__all__"


class SupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    model_object = SupportTicket
    pagination_class = StandardLimitOffsetPagination
