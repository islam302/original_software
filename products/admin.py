from django.contrib import admin, messages
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from messages_extends import constants as constants_messages

from products.forms import (
    CustomProductKeyConfirmImportForm,
    CustomProductKeyImportForm,
    ProductOptionAdminForm,
)
from products.models import (
    Category,
    CategorySlider,
    Company,
    KeyUsersCount,
    KeyValidity,
    Product,
    ProductImage,
    ProductKey,
    ProductOption,
    ProductSection,
    ProductWholesalePricing,
    Slider,
    SubCategory,
    SubCategorySlider,
)


@admin.register(KeyUsersCount)
class KeyUsersCountAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = ("count",)
    search_fields = ("count",)
    fieldsets = (
        (
            None,
            {"fields": ("count",)},
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


@admin.register(KeyValidity)
class KeyValidityAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = ("validity", "validity_unit")
    search_fields = ("validity", "validity_unit")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "validity",
                    "validity_unit",
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


class ProductWholesalePricingInline(admin.TabularInline):
    model = ProductWholesalePricing
    extra = 0
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "wholesale_user_type",
                    "price",
                )
            },
        ),
    )

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProductKeyInline(admin.TabularInline):
    model = ProductKey
    extra = 0
    readonly_fields = (
        "is_used",
        "is_viewed",
        "used_at",
        "used_by",
        "used_order",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "key",
                    "is_used",
                    "is_viewed",
                    "used_at",
                    "used_by",
                    "used_order",
                )
            },
        ),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fieldsets = ((None, {"fields": ("image_file",)}),)


class ProductSectionInline(admin.TabularInline):
    model = ProductSection
    extra = 1
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "seq",
                    "title",
                    "title_ar",
                    "content",
                    "content_ar",
                )
            },
        ),
    )


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    form = ProductOptionAdminForm
    fk_name = "parent_product"
    extra = 0
    ordering = ("seq",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "seq",
                    "keys_users_count",
                    "keys_validity",
                    "product",
                )
            },
        ),
    )


@admin.register(Product)
class CustomProductAdmin(admin.ModelAdmin):
    readonly_fields = (
        "price_in_usd",
        "old_price_in_usd",
        "qty_modified_from_zero",
        "is_key_product",
        "keys_qty",
        "keys_qty_used",
        "keys_qty_unused",
        "has_options",
        "is_option_product",
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = (
        "seq",
        "name",
        "name_ar",
        "price",
        "category",
        "sub_category",
        "company",
        "qty",
        "is_key_product",
        "has_options",
        "is_option_product",
        "keys_qty",
        "keys_qty_used",
        "keys_qty_unused",
        "available",
        "created",
        # "qty_modified_from_zero",
    )
    list_display_links = ("name", "name_ar")
    list_filter = (
        "tag",
        "status",
        "has_options",
        "is_option_product",
        "company",
        "category",
        "sub_category",
        "qty",
        "is_deleted",
    )
    search_fields = (
        "name",
        "name_ar",
        "SKU_code",
    )
    ordering = ("name", "name_ar")
    fieldsets = (
        (
            "Product Info",
            {
                "fields": (
                    "name",
                    "name_ar",
                    "description",
                    "description_ar",
                    "cashback_amount",
                    "SKU_code",
                    "qty",
                    "qty_modified_from_zero",
                    "price",
                    "price_in_usd",
                    "old_price",
                    "old_price_in_usd",
                    "color",
                    "tag",
                    "status",
                    "keys_users_count",
                    "keys_validity",
                    "has_options",
                    "is_option_product",
                    "available",
                    "tutorial",
                    "download_link",
                    "is_key_product",
                    "keys_qty",
                    "keys_qty_used",
                    "keys_qty_unused",
                    "is_deleted",
                )
            },
        ),
        (
            "Product Category & Company",
            {
                "fields": (
                    "category",
                    "sub_category",
                    "company",
                )
            },
        ),
        (
            "Offer Products",
            {"fields": ("offer_products",)},
        ),
        # (
        #     "Technical Info",
        #     {
        #         "fields": (
        #             "created",
        #             "modified",
        #             "created_by",
        #             "updated_by",
        #         )
        #     },
        # ),
    )

    inlines = [
        ProductImageInline,
        ProductSectionInline,
        ProductOptionInline,
        ProductKeyInline,
        ProductWholesalePricingInline,
    ]

    def get_inlines(self, request, obj):
        if obj and obj.offer_products.exists():
            return [
                ProductImageInline,
                ProductSectionInline,
                ProductOptionInline,
                ProductWholesalePricingInline,
            ]
        if not obj:
            return [
                ProductImageInline,
                ProductSectionInline,
                ProductOptionInline,
                ProductKeyInline,
            ]
        # Otherwise, return the default inlines
        return self.inlines

    def save_model(self, request, obj, form, change):
        # messages.add_message(request, constants_messages.WARNING_PERSISTENT, 'You are going to see this message until you mark it as read.')
        super().save_model(request, obj, form, change)


class ProductKeyExportResource(resources.ModelResource):
    class Meta:
        model = ProductKey
        fields = ("product__name", "key")


class ProductKeyResource(resources.ModelResource):
    class Meta:
        model = ProductKey
        import_id_fields = ("key",)
        fields = ("key",)

    def __init__(self, **kwargs):
        super().__init__()
        self.product = kwargs.get("product")

    def before_save_instance(self, instance, using_transactions, dry_run):
        instance.product = self.product


@admin.register(ProductKey)
class CustomProductKeyAdmin(ImportExportModelAdmin):
    resource_classes = [ProductKeyResource]
    import_form_class = CustomProductKeyImportForm
    confirm_form_class = CustomProductKeyConfirmImportForm

    def get_export_resource_class(self):
        """
        Returns ResourceClass to use for export.
        """
        return ProductKeyExportResource

    def get_confirm_form_initial(self, request, import_form):
        initial = super().get_confirm_form_initial(request, import_form)
        # Pass on the `product` value from the import form to
        # the confirm form (if provided)
        if import_form:
            initial["product"] = import_form.cleaned_data["product"]
        return initial

    def get_import_data_kwargs(self, request, *args, **kwargs):
        """
        Return form data as kwargs for import_data.
        """
        form = kwargs.get("form")
        if form:
            return form.cleaned_data
        return {}

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        kwargs = super().get_resource_kwargs(request, *args, **kwargs)
        form = kwargs.get("form")
        if form and form.is_valid():
            kwargs["product"] = form.cleaned_data["product"]
        return kwargs

    readonly_fields = (
        "is_used",
        "used_at",
        "used_by",
        "used_order",
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = (
        "product",
        "key",
        "is_used",
        "used_at",
        "used_by",
        "used_order",
    )
    list_filter = (
        "is_used",
        "product__name",
        "product__price",
        "product__tag",
        "product__status",
        "product__has_options",
        "product__is_option_product",
        "product__company",
        "product__category",
        "product__sub_category",
        "product__qty",
    )
    search_fields = (
        "key",
        "product__name",
        "product__name_ar",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "product",
                    "key",
                    "is_used",
                    "used_at",
                    "used_by",
                    "used_order",
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


class SubCategoryInlineAdmin(admin.TabularInline):
    model = SubCategory
    extra = 1
    fieldsets = ((None, {"fields": ("seq", "name", "name_ar", "image_file")}),)


class CategorySliderInline(admin.TabularInline):
    model = CategorySlider
    extra = 1
    fieldsets = ((None, {"fields": ("path", "image")}),)


@admin.register(Category)
class CustomCategoryAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = (
        "seq",
        "name",
        "name_ar",
    )
    list_display_links = ("name", "name_ar")
    search_fields = ("name", "name_ar")
    ordering = ("seq", "name", "name_ar")

    fieldsets = (
        ("Category Info", {
         "fields": ("seq", "name", "name_ar", "image_file","is_deleted",)}),
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
    inlines = [CategorySliderInline, SubCategoryInlineAdmin]


class SubCategorySliderInline(admin.TabularInline):
    model = SubCategorySlider
    extra = 1
    fieldsets = ((None, {"fields": ("path", "image")}),)


@admin.register(SubCategory)
class CustomSubCategoryAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = (
        "seq",
        "name",
        "name_ar",
        "category",
    )
    list_filter = ("category",)
    search_fields = ("name", "name_ar")
    ordering = ("seq", "name", "name_ar")

    fieldsets = (
        (
            "Sub Category Info",
            {"fields": ("seq", "name", "name_ar", "category", "image_file","is_deleted",)},
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

    inlines = [SubCategorySliderInline]


@admin.register(Company)
class CustomCompanyAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = (
        "name",
        "name_ar",
        "show_in_home",
    )
    # list_filter = ()
    search_fields = ("name", "name_ar")
    ordering = ("name", "name_ar")

    fieldsets = (
        ("Company Info", {
         "fields": ("name", "name_ar", "logo", "show_in_home","is_deleted")}),
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


@admin.register(Slider)
class CustomSliderAdmin(admin.ModelAdmin):
    readonly_fields = (
        "created",
        "modified",
        "created_by",
        "updated_by",
    )
    list_display = ("path",)

    fieldsets = (
        (
            "Slider Item Info",
            {
                "fields": (
                    "path",
                    "image",
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
