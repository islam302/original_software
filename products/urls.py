from django.urls import include, path, re_path
from rest_framework import routers

from products.views import (
    CategorySliderViews,
    CategoryViews,
    CompanyViews,
    KeyUsersCountViews,
    KeyValidityViews,
    ProductImageViews,
    ProductKeyViews,
    ProductOptionAutocompleteView,
    ProductOptionViews,
    ProductSectionViews,
    ProductViews,
    ProductWholesalePricingViews,
    SliderViews,
    SubCategorySliderViews,
    SubCategoryViews,
    SpecialOfferViews
)

app_name = "products"
 
 

router = routers.SimpleRouter()
router.register(r"category", CategoryViews, basename="category")
router.register(r"category_slider", CategorySliderViews, basename="category_slider")
router.register(r"sub_category", SubCategoryViews, basename="sub_category")
router.register(
    r"sub_category_slider", SubCategorySliderViews, basename="sub_category_slider"
)
router.register(r"product", ProductViews, basename="product")
router.register(r"key_users_count", KeyUsersCountViews, basename="key_users_count")
router.register(r"key_validity", KeyValidityViews, basename="key_validity")
router.register(r"slider", SliderViews, basename="slider")
router.register(r"company", CompanyViews, basename="company")
router.register(r"product_image", ProductImageViews, basename="product_image")
router.register(r"product_section", ProductSectionViews, basename="product_section")
router.register(r"product_option", ProductOptionViews, basename="product_option")
router.register(r"product_key", ProductKeyViews, basename="product_key")
router.register(
    r"product_wholesale_pricing",
    ProductWholesalePricingViews,
    basename="product_wholesale_pricing",
)
router.register(
    r"special_offer",
    SpecialOfferViews,
    basename="special_offer",
)

urlpatterns = [
    path("", include(router.urls)),
    re_path(
        r"^product_option_autocomplete/$",
        ProductOptionAutocompleteView.as_view(),
        name="product_option_autocomplete",
    ),
]
