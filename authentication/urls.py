from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from django.conf import settings
from django.urls import include, path, re_path
from rest_framework import routers

from authentication.views import (
    ConfigViewSet,
    DeleteUser,
    TransactionAdminViews,
    TransactionUserAutocompleteView,
    TransactionViews,
    UsersViewSet,
    WholesaleUserTypeViewSet,
    CustomLoginView
)

app_name = "authentication"

router = routers.SimpleRouter()
router.register(r"transactions", TransactionViews, basename="transactions")
router.register(
    r"admin/transactions", TransactionAdminViews, basename="admin-transactions"
)
router.register(r"admin/users", UsersViewSet, basename="admin-users")
router.register(r"config", ConfigViewSet, basename="config")
router.register(
    r"wholesale_user_type", WholesaleUserTypeViewSet, basename="wholesale-user-type"
)


urlpatterns = [
    # URLs that do not require a session or valid token
    path("password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    # path("login/", CustomLoginView.as_view(), name="rest_login"),
    path("user/login/", CustomLoginView.as_view(), name="rest_login"),
    path("login/", LoginView.as_view(), name="rest_login"),
    # URLs that require a user to be logged in with a valid session / token.
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    path("user/", UserDetailsView.as_view(), name="rest_user_details"),
    path(
        "password/change/",
        PasswordChangeView.as_view(),
        name="rest_password_change",
    ),
    path("register", RegisterView.as_view(), name="rest_register"),
    path("delete_user/", DeleteUser.as_view()),
    re_path(
        r"^transaction-user-autocomplete/$",
        TransactionUserAutocompleteView.as_view(),
        name="transaction-user-autocomplete",
    ),
    path("", include(router.urls)),
]


if getattr(settings, "REST_USE_JWT", False):
    from dj_rest_auth.jwt_auth import get_refresh_view
    from rest_framework_simplejwt.views import TokenVerifyView

    urlpatterns += [
        path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
        path("token/refresh/", get_refresh_view().as_view(), name="token_refresh"),
    ]
