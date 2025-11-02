from constance import config
from dj_rest_auth.registration.views import ResendEmailVerificationView, VerifyEmailView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.urls.conf import include
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import authentication, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response

admin.site.site_title = "Original Software"
admin.site.site_header = "Original Software"
admin.site.index_title = "Original Software Panal"

schema_view = get_schema_view(
    openapi.Info(
        title="Original Software API",
        default_version="V 1",
        # description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="hadermusc@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # this url is used to generate email content
    re_path(
        r"^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$",
        TemplateView.as_view(template_name="password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "auth/account-confirm-email/",
        VerifyEmailView.as_view(),
        name="account_confirm_email",
    ),
    path(
        "auth/resend-account-confirm-email/",
        ResendEmailVerificationView.as_view(),
        name="rest_resend_email",
    ),
    path("auth/", include("authentication.urls", namespace="authentication")),
    path("", include("products.urls", namespace="products")),
    path("", include("orders.urls", namespace="orders")),
    path("", include("files.urls", namespace="files")),
    path("", include("notifications.urls", namespace="notifications")),
    # drf-yasg
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(r"^messages/", include("messages_extends.urls")),
    path("admin/", admin.site.urls),
    re_path(r"^chaining/", include("smart_selects.urls")),
]

if True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)