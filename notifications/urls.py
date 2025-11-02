from django.urls import include, path
from rest_framework import routers

from notifications.views import NotificationViews

app_name = "notifications"


router = routers.SimpleRouter()
router.register("notifications", NotificationViews, basename="notifications")

urlpatterns = [
    path("", include(router.urls)),
]
