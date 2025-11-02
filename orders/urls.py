from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include, path
from rest_framework import routers

from orders.views import OrderViews, SupportTicketViewSet, OrderLineViews

app_name = "products"


router = routers.SimpleRouter()
router.register(r"order", OrderViews, basename="order")
router.register(r"order-line", OrderLineViews, basename="order-line")
router.register(r"support", SupportTicketViewSet, basename="support")


urlpatterns = [
    path("", include(router.urls)),
]
