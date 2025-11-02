from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from authentication.models import Transaction, WholesaleUserType

from .forms import TransactionAdminForm


@admin.register(WholesaleUserType)
class CustomWholesaleUserTypeAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "created_by",
        "modified",
        "updated_by",
    )
    list_display = (
        "title",
        "negative_limit",
    )
    search_fields = ("title", "description")
    list_filter = (
        "title",
        "negative_limit",
    )
    fieldsets = (
        (
            "Wholesale User Type",
            {
                "fields": (
                    "title",
                    "negative_limit",
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


@admin.register(Transaction)
class CustomTransactionAdmin(admin.ModelAdmin):
    form = TransactionAdminForm
    readonly_fields = (
        "created",
        "created_by",
        "modified",
        "updated_by",
        "amount_usd",
        "related_order",
    )
    list_display = (
        "transaction_type",
        "user",
        "amount",
        "amount_usd",
        "related_order",
    )
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "description",
    )
    list_filter = (
        "user",
        "amount",
        "transaction_type",
    )
    fieldsets = (
        (
            "Transaction",
            {
                "fields": (
                    "transaction_type",
                    "user",
                    "amount",
                    "amount_usd",
                    "description",
                    "related_order",
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

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


class IsWholesaleFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "نوع الحساب"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "is_wholesale"

    def lookups(self, request, model_admin):
        return (
            ("True", "جملة"),
            ("False", "مفرد"),
        )

    def queryset(self, request, queryset):
        if self.value() == "True":
            return queryset.filter(wholesale_type__isnull=False)
        elif self.value() == "False":
            return queryset.filter(wholesale_type__isnull=True)


@admin.register(get_user_model())
class CustomUserAdmin(UserAdmin):
    def is_wholesale(self, obj):
        return "جملة" if obj.is_wholesale else "مفرد"

    is_wholesale.short_description = "نوع الحساب"

    readonly_fields = (
        "created",
        "created_by",
        "modified",
        "updated_by",
        "is_email_verified",
        "wallet_balance",
        "wallet_balance_usd",
        "is_wholesale",
    )
    list_display = (
        "email",
        "username",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_wholesale",
        "wholesale_type",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        IsWholesaleFilter,
        "wholesale_type",
    )

    search_fields = ("email", "username")
    ordering = ("email", "username")

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "phone_2",
                    "birth_date",
                    "gender",
                    "is_email_verified",
                    "country",
                    "city",
                    "wholesale_type",
                    "is_wholesale",
                    "wallet_balance",
                    "wallet_balance_usd",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        (
            "Record Info",
            {"fields": ("created", "created_by", "modified", "updated_by")},
        ),
    )

    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    # add_fieldsets = (
    #     (None, {
    #         'classes': ('wide',),
    #         'fields': ('username', 'email', 'password1', 'password2'),
    #     }),
    # )
