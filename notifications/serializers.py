from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework import serializers

from authentication.serializers import CustomUserDetailsSerializer
from notifications.models import Notification
from orders.serializers import OrderSerializer, SupportTicketSerializer
from products.serializers import ProductSerializer


class NotificationSerializer(serializers.ModelSerializer):
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "related_user",
            "object_id",
            "linked_model_name",
            "description",
            "notification_level",
            "content_object",
            "hidden",
            "created",
            "modified",
        ]

    def get_content_object(self, obj):
        if obj.linked_model_name == "orders.Order":
            try:
                Order = apps.get_model("orders.Order")
                return OrderSerializer(Order.objects.get(id=obj.object_id)).data
            except Order.DoesNotExist:
                return None
        if obj.linked_model_name == "orders.SupportTicket":
            try:
                SupportTicket = apps.get_model("orders.SupportTicket")
                return SupportTicketSerializer(
                    SupportTicket.objects.get(id=obj.object_id)
                ).data
            except SupportTicket.DoesNotExist:
                return None
        if obj.linked_model_name == "products.Product":
            try:
                Product = apps.get_model("products.Product")
                return ProductSerializer(
                    Product.objects.get(id=obj.object_id)
                ).data
            except Product.DoesNotExist:
                return None
        if obj.linked_model_name == "authentication.User":
            try:
                User = get_user_model()
                return CustomUserDetailsSerializer(
                    User.objects.get(id=obj.object_id)
                ).data
            except User.DoesNotExist:
                return
        return None
