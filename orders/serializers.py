from collections import OrderedDict

from crum import get_current_user
from django.db import transaction
from rest_framework import serializers

from authentication.models import Transaction, User
from authentication.serializers import CustomUserDetailsSerializer
from orders.models import Order, OrderLine, OrderLineKey, SupportTicket
from products.models import ProductKey, Product
from products.serializers.product import NestedProductImageSerializer


class OrderLineKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLineKey
        fields = (
            "key_serial",
            "used_at",
            "other_info",
        )
        read_only_fields = (
            "key_serial",
            "used_at",
            "other_info",
        )


class OrderLineSerializer(serializers.ModelSerializer):
    order_line_keys = OrderLineKeySerializer(many=True, read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_name_ar = serializers.CharField(
        source="product.name_ar", read_only=True)
    product_category_name = serializers.CharField(
        source="product.category.name", read_only=True
    )
    product_category_name_ar = serializers.CharField(
        source="product.category.name_ar", read_only=True
    )
    tutorial = serializers.CharField(source="product.tutorial", read_only=True)
    download_link = serializers.CharField(
        source="product.download_link", read_only=True
    )
    is_key_product = serializers.BooleanField(
        source="product.is_key_product", read_only=True
    )
    created_by_data = CustomUserDetailsSerializer(
        source="created_by", read_only=True)
    product_images = serializers.SerializerMethodField()

    class Meta:
        model = OrderLine
        fields = (
            "id",
            "seq",
            "product",
            "is_key_product",
            "product_name",
            "product_name_ar",
            "product_category_name",
            "product_category_name_ar",
            "product_images",
            "product_image",
            "first_product_image",
            "tutorial",
            "download_link",
            "unit_price",
            "unit_price_usd",
            "quantity",
            "sub_total",
            "sub_total_usd",
            "order_line_keys",
            "payment_method",
            "created_by",
            "created_by_data",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "product_category_name",
            "product_category_name_ar",
            "product_images",
            "is_key_product",
            "unit_price",
            "unit_price_usd",
            "sub_total",
            "sub_total_usd",
            "order_line_keys",
            "payment_method",
            "created_by",
            "created_by_data",
            "updated_by",
            "created",
            "modified",
        )

    def validate(self, data):
        # Retrieve the product from initial_data
        product = data["product"]
        # if product.has_options:
        #     raise serializers.ValidationError(
        #         {
        #             "product": f"Product {product.name} has options, please send the options with the order line"
        #         }
        #     )
        if product.is_key_product and not product.offer_products.exists():
            keys_count = ProductKey.objects.filter(
                product=product,
                is_used=False,
            ).count()
            if keys_count < data["quantity"]:
                raise serializers.ValidationError(
                    {
                        "quantity": f"There is no available quantity of keys for product {product.name}"
                    }
                )
        elif product.offer_products.exists():
            for offer_product in product.offer_products.all():
                if offer_product.has_options:
                    raise serializers.ValidationError(
                        {
                            "offer_product": f"Offer Product {product.name} has options, please send the options with the order line"
                        }
                    )

                keys_count = ProductKey.objects.filter(
                    product=offer_product,
                    is_used=False,
                ).count()
                if keys_count < data["quantity"]:
                    raise serializers.ValidationError(
                        {
                            "quantity": f"There is no available quantity of keys for product {offer_product.name}"
                        }
                    )
        # Always return the value after validation
        return data

    def to_representation(self, obj):
        # get the original representation
        ret = super(OrderLineSerializer, self).to_representation(obj)

        # if the order is not paid, not approver or the user did not view the order don't show the keys
        user = get_current_user()
        if not user.is_staff:
            if (
                obj.order.payment_status != Order.PAYMENT_STATUS.paid
                or obj.order.status != Order.STATUS.approved
                or not obj.order.is_viewed
            ):
                ret["order_line_keys"] = []

        # return the modified representation
        return ret

    def get_product_images(self, obj):
        return NestedProductImageSerializer(obj.product.images.all(), many=True).data


class OrderSerializer(serializers.ModelSerializer):
    order_lines = OrderLineSerializer(many=True, read_only=False)
    approved_by = serializers.SerializerMethodField()
    rejected_by = serializers.SerializerMethodField()
    returned_by = serializers.SerializerMethodField()
    canceled_by = serializers.SerializerMethodField()
    paid_by = serializers.SerializerMethodField()
    payment_failed_by = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "payment_method",
            "payment_status",
            "order_number",
            "is_viewed",
            "is_wholesale",
            "transaction_url",
            "qr_code",
            "readable_code",
            "fib_payment_valid_until",
            "use_wallet",
            "order_lines",
            "country",
            "city",
            "address",
            "notes",
            "total_products",
            "paid_amount_from_wallet",
            "total_price",
            "total_price_usd",
            "shipping_cost",
            "total_price_with_shipping",
            "total_price_with_shipping_usd",
            "total_price_minus_wallet",
            "total_price_minus_wallet_usd",
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
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "status",
            "payment_status",
            "order_number",
            "total_price",
            "paid_amount_from_wallet",
            "is_viewed",
            "transaction_url",
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
            "total_price_with_shipping",
            "total_price_with_shipping_usd",
            "approved_notes",
            "rejected_notes",
            "created",
            "modified",
            "created_by",
            "updated_by",
        )

    def create(self, validated_data):
        with transaction.atomic():
            order_lines_data = validated_data.pop("order_lines")
            user = validated_data.pop("user", None)
            # Remove duplicates
            order_lines_data = [
                OrderedDict(t) for t in {tuple(d.items()) for d in order_lines_data}
            ]

            for order_line_data in order_lines_data:
                product = Product.objects.get(
                    id=order_line_data.get('product').id)

                # if product.has_options:
                #     raise serializers.ValidationError(
                #         {
                #             "product": f"Product {product.name} has options, please send the options with the order line"
                #         }
                #     )
                if product.is_key_product and not product.offer_products.exists():
                    keys_count = ProductKey.objects.filter(
                        product=product,
                        is_used=False,
                    ).count()
                    if keys_count < order_line_data["quantity"]:
                        raise serializers.ValidationError(
                            {
                                "quantity": f"There is no available quantity of keys for product {product.name}"
                            }
                        )
                elif product.offer_products.exists():
                    for offer_product in product.offer_products.all():
                        if offer_product.has_options:
                            raise serializers.ValidationError(
                                {
                                    "offer_product": f"Offer Product {product.name} has options, please send the options with the order line"
                                }
                            )

                        keys_count = ProductKey.objects.filter(
                            product=offer_product,
                            is_used=False,
                        ).count()
                        if keys_count < order_line_data["quantity"]:
                            raise serializers.ValidationError(
                                {
                                    "quantity": f"There is no available quantity of keys for product {offer_product.name}"
                                }
                            )
            is_wholesale = False
            if user and user.wholesale_type is not None:
                is_wholesale = True
            order = Order(**validated_data)
            order.save(skip_hooks=True)
            order.is_wholesale = is_wholesale
            order.save()
            order_lines_total_price = 0

            for order_line_data in order_lines_data:

                order_line = OrderLine.objects.create(
                    order=order, **order_line_data)
                order_line.use_keys()
                order_lines_total_price += order_line.sub_total

            order.total_price = order_lines_total_price
            order.save()

            if user:
                order.created_by = user
                order.updated_by = user
                order.save()

            if order.use_wallet:
                user = self.context["request"].user
                wholesale_type = user.wholesale_type
                if wholesale_type is not None:
                    balance = user.wallet_balance
                    negative_limit = wholesale_type.negative_limit
                    if balance - order.total_price - negative_limit < 0:
                        raise serializers.ValidationError(
                            {
                                "use_wallet": "You don't have enough balance to use from your wallet"
                            }
                        )
            order.use_wallet_balance()
            if order.payment_method == Order.PAYMENT_METHOD.zain_cash:
                order.create_zain_cash_transaction()
            elif order.payment_method == Order.PAYMENT_METHOD.credit_card:
                order.create_qi_card_transaction()
            elif order.payment_method == Order.PAYMENT_METHOD.fast_pay:
                order.create_fastpay_transaction()
            elif order.payment_method == Order.PAYMENT_METHOD.fib:
                order.create_fib_transaction()

            Order.objects.get(id=order.id).send_order_pending_email()
            return order

    def create_admin(validated_data):
        with transaction.atomic():
            order_lines_data = validated_data.pop("order_lines")
            user = User.objects.get(id=validated_data.pop("user"))
            # Remove duplicates
            order_lines_data = [
                OrderedDict(t) for t in {tuple(d.items()) for d in order_lines_data}
            ]

            for order_line_data in order_lines_data:
                product = Product.objects.get(
                    id=order_line_data.get('product'))

                # if product.has_options:
                #     raise serializers.ValidationError(
                #         {
                #             "product": f"Product {product.name} has options, please send the options with the order line"
                #         }
                #     )
                if product.is_key_product and not product.offer_products.exists():
                    keys_count = ProductKey.objects.filter(
                        product=product,
                        is_used=False,
                    ).count()
                    if keys_count < order_line_data["quantity"]:
                        raise serializers.ValidationError(
                            {
                                "quantity": f"There is no available quantity of keys for product {product.name}"
                            }
                        )
                elif product.offer_products.exists():
                    for offer_product in product.offer_products.all():
                        if offer_product.has_options:
                            raise serializers.ValidationError(
                                {
                                    "offer_product": f"Offer Product {product.name} has options, please send the options with the order line"
                                }
                            )

                        keys_count = ProductKey.objects.filter(
                            product=offer_product,
                            is_used=False,
                        ).count()
                        if keys_count < order_line_data["quantity"]:
                            raise serializers.ValidationError(
                                {
                                    "quantity": f"There is no available quantity of keys for product {offer_product.name}"
                                }
                            )

            order = Order(**validated_data)
            order.save(skip_hooks=True)
            is_wholesale = False
            if user and user.wholesale_type is not None:
                is_wholesale = True
            order.is_wholesale = is_wholesale
            order.save()
            order_lines_total_price = 0

            for order_line_data in order_lines_data:
                # return
                product = Product.objects.get(
                    id=order_line_data.pop('product'))
                order_line = OrderLine.objects.create(
                    order=order,
                    product=product,
                    ** order_line_data)
                order_line.created_by = user
                order_line.updated_by = user
                order_line.save()
                order_line.use_keys()
                order_lines_total_price += order_line.sub_total

            order.total_price = order_lines_total_price
            order.save()

            if user:
                order.created_by = user
                order.updated_by = user
                order.save()

            if order.use_wallet:

                wholesale_type = user.wholesale_type
                if wholesale_type is not None:
                    balance = user.wallet_balance
                    negative_limit = wholesale_type.negative_limit
                    if balance - order.total_price - negative_limit < 0:
                        raise serializers.ValidationError(
                            {
                                "use_wallet": "You don't have enough balance to use from your wallet"
                            }
                        )
                        
            order.use_wallet_balance()
            if order.payment_method == Order.PAYMENT_METHOD.zain_cash:
                order.create_zain_cash_transaction()
            elif order.payment_method == Order.PAYMENT_METHOD.credit_card:
                order.create_qi_card_transaction()
            elif order.payment_method == Order.PAYMENT_METHOD.fast_pay:
                order.create_fastpay_transaction()
            elif order.payment_method == Order.PAYMENT_METHOD.fib:
                order.create_fib_transaction()
                
            Order.objects.get(id=order.id).send_order_pending_email()
                
            return order

    def delete_bulk(validated_data):
        with transaction.atomic():
            orders = Order.objects.filter(id__in=validated_data["ids"])
            for order in orders:
                order.delete()

        return {"message": "Orders deleted successfully"}

    def get_approved_by(self, obj):
        if obj.approved_by:
            return CustomUserDetailsSerializer(obj.approved_by).data
        return None

    def get_rejected_by(self, obj):
        if obj.rejected_by:
            return CustomUserDetailsSerializer(obj.rejected_by).data
        return None

    def get_returned_by(self, obj):
        if obj.returned_by:
            return CustomUserDetailsSerializer(obj.returned_by).data
        return None

    def get_canceled_by(self, obj):
        if obj.canceled_by:
            return CustomUserDetailsSerializer(obj.canceled_by).data
        return None

    def get_paid_by(self, obj):
        if obj.paid_by:
            return CustomUserDetailsSerializer(obj.paid_by).data
        return None

    def get_payment_failed_by(self, obj):
        if obj.payment_failed_by:
            return CustomUserDetailsSerializer(obj.payment_failed_by).data
        return None

    def get_created_by(self, obj):
        if obj.created_by:
            return CustomUserDetailsSerializer(obj.created_by).data
        return None

    def get_updated_by(self, obj):
        if obj.updated_by:
            return CustomUserDetailsSerializer(obj.updated_by).data
        return None


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "full_name",
            "email",
            "phone",
            "description",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
        read_only_fields = (
            "id",
            "created_by",
            "updated_by",
            "created",
            "modified",
        )
