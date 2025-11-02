import nested_admin
from django.contrib import admin, messages
from django.contrib.admin import DateFieldListFilter, SimpleListFilter
from django.contrib.auth import get_user_model
from django.db.models import CharField, Value
from django.db.models.functions import Cast, Concat, Right
from django.http import HttpResponseRedirect
from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
    DateTimeRangeFilterBuilder,
)

from authentication.models import Transaction
from orders.models import Order, OrderLine, OrderLineKey, SupportTicket
from products.models import Category, SubCategory


class OrderLineKeyInlineAdmin(nested_admin.NestedTabularInline):
    model = OrderLineKey
    readonly_fields = ("key_serial", "used_at", "other_info")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "key_serial",
                    "used_at",
                    "other_info",
                )
            },
        ),
    )

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False


class OrderLineInlineAdmin(nested_admin.NestedTabularInline):
    model = OrderLine
    extra = 0
    ordering = ("seq",)
    readonly_fields = (
        "seq",
        "product",
        "unit_price",
        "unit_price_usd",
        "quantity",
        "sub_total",
        "sub_total_usd",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "seq",
                    "product",
                    "unit_price",
                    "unit_price_usd",
                    "quantity",
                    "sub_total",
                    "sub_total_usd",
                )
            },
        ),
    )

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False

    inlines = [OrderLineKeyInlineAdmin]


class IsWholesaleFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "نوع الطلب"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "is_wholesale"

    def lookups(self, request, model_admin):
        return (
            ("True", "جملة"),
            ("False", "مفرد"),
        )

    def queryset(self, request, queryset):
        if self.value() == "True":
            return queryset.filter(created_by__wholesale_type__isnull=False)
        elif self.value() == "False":
            return queryset.filter(created_by__wholesale_type__isnull=True)


class CountryFilter(SimpleListFilter):
    title = "Country"
    parameter_name = "country"

    def lookups(self, request, model_admin):
        return get_user_model().CONTRY

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(created_by__country=self.value())
        return queryset


class CityFilter(SimpleListFilter):
    title = "City"
    parameter_name = "city"

    def lookups(self, request, model_admin):
        return get_user_model().CITY

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(created_by__city=self.value())
        return queryset


class CategoryFilter(SimpleListFilter):
    title = "Category"
    parameter_name = "category"

    def lookups(self, request, model_admin):
        return Category.objects.values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(order_line__product__category=self.value())
        return queryset


class SubCategoryFilter(SimpleListFilter):
    title = "Sub Category"
    parameter_name = "sub_category"

    def lookups(self, request, model_admin):
        return SubCategory.objects.values_list("id", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(order_line__product__sub_category=self.value())
        return queryset


@admin.register(Order)
class CustomOrderAdmin(nested_admin.NestedModelAdmin):
    readonly_fields = (
        "status",
        "payment_method",
        "payment_status",
        "order_number",
        "total_price",
        "use_wallet",
        "paid_amount_from_wallet",
        "is_viewed",
        "transaction_url",
        "transaction_id",
        "card_holder",
        "masked_card_number",
        "qr_code",
        "readable_code",
        "fib_payment_valid_until",
        "approved_by",
        "approved_at",
        "rejected_by",
        "rejected_at",
        "returned_by",
        "returned_at",
        "canceled_by",
        "canceled_at",
        "paid_at",
        "paid_by",
        "payment_failed_at",
        "payment_failed_by",
        "full_name",
        "email",
        "phone",
        "phone_2",
        "country",
        "city",
        "is_wholesale",
        "shipping_cost",
        "total_price_usd",
        # "total_price_with_shipping",
        # "total_price_with_shipping_usd",
        "total_price_minus_wallet",
        "total_price_minus_wallet_usd",
        "created",
        "modified",
        "created_by",
        "updated_by",
    )

    list_display = (
        "order_number",
        "status",
        "payment_method",
        "payment_status",
        "use_wallet",
        "is_viewed",
        "is_wholesale",
        "full_name",
        "email",
        "phone",
        "total_price",
        "total_price_usd",
        "total_price_minus_wallet",
        "total_price_minus_wallet_usd",
        "created",
        "approved_at",
    )
    list_filter = (
        IsWholesaleFilter,
        "status",
        "payment_method",
        "payment_status",
        "is_viewed",
        CountryFilter,
        CityFilter,
        CategoryFilter,
        SubCategoryFilter,
        ("created", DateRangeFilterBuilder(title="Filter by Order Creation Date")),
        ("approved_at", DateRangeFilterBuilder(title="Filter by Order Approval Date")),
        ("rejected_at", DateRangeFilterBuilder(title="Filter by Order Rejection Date")),
    )
    search_fields = (
        "order_number",
        "email_filter",
        "first_name_filter",
        "last_name_filter",
        "phone_filter",
        "phone_2_filter",
        "country_filter",
        "city_filter",
    )

    def is_wholesale(self, obj):
        return "جملة" if obj.is_wholesale else "مفرد"

    is_wholesale.short_description = "نوع الطلب"
    # ordering = ("name", "name_ar")
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    fieldsets = (
        (
            "Order Info",
            {
                "fields": (
                    "order_number",
                    "status",
                    "payment_method",
                    "payment_status",
                    "full_name",
                    "email",
                    "phone",
                    "phone_2",
                    "country",
                    "city",
                    "address",
                    "notes",
                    "total_price",
                    "total_price_usd",
                    "use_wallet",
                    "paid_amount_from_wallet",
                    "total_price_minus_wallet",
                    "total_price_minus_wallet_usd",
                    "shipping_cost",
                    "is_viewed",
                    "is_wholesale",
                )
            },
        ),
        (
            "Order Status and Payment",
            {
                "fields": (
                    "approved_notes",
                    "approved_by",
                    "approved_at",
                    "rejected_notes",
                    "rejected_by",
                    "rejected_at",
                    "returned_by",
                    "returned_at",
                    "canceled_by",
                    "canceled_at",
                    "paid_at",
                    "paid_by",
                    "payment_failed_at",
                    "payment_failed_by",
                )
            },
        ),
        (
            "Technical Info",
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "updated_by",
                    "transaction_url",
                    "transaction_id",
                    "card_holder",
                    "masked_card_number",
                    "qr_code",
                    "readable_code",
                    "fib_payment_valid_until",
                )
            },
        ),
    )

    def has_add_permission(self, request, obj=None):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    change_form_template = "orders/custom_change_form.html"

    def response_change(self, request, obj):
        if "_approve" in request.POST:
            obj = self.get_object(request, obj.pk)
            if obj.status == Order.STATUS.approved:
                self.message_user(
                    request, "Order is already approved", messages.WARNING
                )
                return HttpResponseRedirect(".")
            if obj.status != Order.STATUS.pending:
                self.message_user(
                    request, "Order should be pending to be approved", messages.ERROR
                )
                return HttpResponseRedirect(".")
            obj.status = Order.STATUS.approved
            obj.approved_by = request.user
            for order_line in obj.order_lines.all():
                order_line.preform_cashback()
            obj.save()
            self.message_user(
                request,
                "Order Successfully approved and email sent to the customer",
                messages.SUCCESS,
            )
            return HttpResponseRedirect(".")
        if "_reject" in request.POST:
            obj = self.get_object(request, obj.pk)
            if obj.status == Order.STATUS.rejected:
                self.message_user(
                    request, "Order is already rejected", messages.WARNING
                )
                return HttpResponseRedirect(".")
            if obj.status != Order.STATUS.pending:
                self.message_user(
                    request, "Order should be pending to be rejected", messages.ERROR
                )
                return HttpResponseRedirect(".")
            obj.status = Order.STATUS.rejected
            obj.rejected_by = request.user
            obj.save()

            self.message_user(
                request,
                "Order Successfully rejected and email sent to the customer",
                messages.SUCCESS,
            )
            return HttpResponseRedirect(".")
        if "_return" in request.POST:
            obj = self.get_object(request, obj.pk)
            if obj.status == Order.STATUS.returned:
                self.message_user(
                    request, "Order is already returned", messages.WARNING
                )
                return HttpResponseRedirect(".")
            obj.status = Order.STATUS.returned
            obj.returned_by = request.user
            obj.save()

            self.message_user(
                request,
                "Order Successfully returned and email sent to the customer",
                messages.SUCCESS,
            )
            return HttpResponseRedirect(".")
        if "_mark_as_paid" in request.POST:
            obj = self.get_object(request, obj.pk)
            if obj.payment_status == Order.PAYMENT_STATUS.paid:
                self.message_user(request, "Order is already paid", messages.WARNING)
                return HttpResponseRedirect(".")
            obj.payment_status = Order.PAYMENT_STATUS.paid
            obj.paid_by = request.user
            obj.save()

            self.message_user(
                request,
                "Order Successfully marked as paid.",
                messages.SUCCESS,
            )
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        qs = qs.annotate(
            email_filter=Cast("created_by__email", CharField()),
            first_name_filter=Cast("created_by__first_name", CharField()),
            last_name_filter=Cast("created_by__last_name", CharField()),
            phone_filter=Cast("created_by__phone", CharField()),
            phone_2_filter=Cast("created_by__phone_2", CharField()),
            country_filter=Cast("created_by__country", CharField()),
            city_filter=Cast("created_by__city", CharField()),
        )
        return qs

    inlines = [OrderLineInlineAdmin]


@admin.register(SupportTicket)
class SupportTicketCustomAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )

    list_display = (
        "full_name",
        "email",
        "phone",
        "created",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
    )

    fieldsets = (
        (
            "Ticket Info",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "description",
                )
            },
        ),
        (
            "Technical Info",
            {
                "fields": (
                    "created",
                    "modified",
                    "created_by",
                    "updated_by",
                )
            },
        ),
    )


from django_cron.models import CronJobLock, CronJobLog
from messages_extends.models import Message
from sequences.models import Sequence

admin.site.unregister(CronJobLog)
admin.site.unregister(CronJobLock)
admin.site.unregister(Sequence)
admin.site.unregister(Message)
