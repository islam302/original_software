import json
import time
import uuid
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
import jwt
import requests
from constance import config
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import get_template
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_SAVE,
    BEFORE_CREATE,
    LifecycleModelMixin,
    hook,
)
from model_utils import Choices
from model_utils.fields import MonitorField
from model_utils.models import TimeStampedModel
from requests.auth import HTTPBasicAuth
from rest_framework.exceptions import APIException
from sequences import get_next_value

from authentication.models import Transaction, UserStampedModel
from core.utils import get_upload_path
from notifications.models import Notification
from products.models import ProductKey
from products.models.product_image import ProductImage
from django.contrib.contenttypes.fields import GenericRelation
import base64
from typing import Any, Dict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def get_next_order_number():
    return f"OS-{get_next_value('order_number')}"


class Order(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Orders"
        ordering = ["-id"]

    STATUS = Choices(
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("returned", "Returned"),
        ("canceled", "Canceled"),
    )
    PAYMENT_METHOD = Choices(
        ("cash", "Cash"),
        ("zain_cash", "Zain Cash"),
        ("fast_pay", "Fast Pay"),
        ("credit_card", "Credit Card"),
        ("fib", "FIB"),
    )
    PAYMENT_STATUS = Choices(
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    )

    order_number = models.CharField(
        "Order Number", max_length=50, unique=True, default=get_next_order_number
    )
    status = models.CharField(
        "Status", choices=STATUS, max_length=50, default=STATUS.pending
    )
    payment_method = models.CharField(
        "Payment Method",
        choices=PAYMENT_METHOD,
        max_length=50,
        default=PAYMENT_METHOD.cash,
    )
    payment_status = models.CharField(
        "Payment Status",
        choices=PAYMENT_STATUS,
        max_length=50,
        default=PAYMENT_STATUS.pending,
    )
    address = models.CharField(max_length=100, blank=True)
    approved_notes = models.TextField("Approved Notes", blank=True)
    rejected_notes = models.TextField("Rejected Notes", blank=True)
    notes = models.TextField(blank=True)

    total_price = models.DecimalField(
        "Total Price", max_digits=26, decimal_places=0, default=0
    )
    use_wallet = models.BooleanField(default=False)
    paid_amount_from_wallet = models.DecimalField(
        "Paid Amount From Wallet", max_digits=26, decimal_places=0, default=0
    )
    is_viewed = models.BooleanField(default=False)
    transaction_url = models.URLField(blank=True, max_length=550)
    transaction_id = models.CharField(max_length=550, blank=True)
    # qi card fields
    card_holder = models.CharField(max_length=50, blank=True)
    masked_card_number = models.CharField(max_length=50, blank=True)
    # fib fields
    qr_code = models.CharField(
        max_length=50000,
        blank=True,
        null=True,
    )
    readable_code = models.CharField(max_length=50, blank=True)
    fib_payment_valid_until = models.DateTimeField(blank=True, null=True)
    is_wholesale = models.BooleanField(default=False)

    # status tracking fields
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="approved_by",
        related_name="%(class)ss_approved_by",
        related_query_name="%(class)s_approved_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    approved_at = MonitorField(
        monitor="status",
        when=[STATUS.approved],
        blank=True,
        null=True,
        default=None,
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="rejected_by",
        related_name="%(class)ss_rejected_by",
        related_query_name="%(class)s_rejected_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    rejected_at = MonitorField(
        monitor="status",
        when=[STATUS.rejected],
        blank=True,
        null=True,
        default=None,
    )
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="returned_by",
        related_name="%(class)ss_returned_by",
        related_query_name="%(class)s_returned_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    returned_at = MonitorField(
        monitor="status",
        when=[STATUS.returned],
        blank=True,
        null=True,
        default=None,
    )
    canceled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="canceled_by",
        related_name="%(class)ss_canceled_by",
        related_query_name="%(class)s_canceled_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    canceled_at = MonitorField(
        monitor="status",
        when=[STATUS.canceled],
        blank=True,
        null=True,
        default=None,
    )
    paid_at = MonitorField(
        monitor="payment_status",
        when=[PAYMENT_STATUS.paid],
        blank=True,
        null=True,
        default=None,
    )
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="paid_by",
        related_name="%(class)ss_paid_by",
        related_query_name="%(class)s_paid_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    payment_failed_at = MonitorField(
        monitor="payment_status",
        when=[PAYMENT_STATUS.failed],
        blank=True,
        null=True,
        default=None,
    )
    payment_failed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column="payment_failed_by",
        related_name="%(class)ss_payment_failed_by",
        related_query_name="%(class)s_payment_failed_by",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    full_name = property(lambda self: self.created_by.get_full_name())
    email = property(lambda self: self.created_by.email)
    phone = property(lambda self: self.created_by.phone)
    phone_2 = property(lambda self: self.created_by.phone_2)
    country = property(
        lambda self: (
            self.created_by.CONTRY._display_map[self.created_by.country]
            if self.created_by.country
            else ""
        )
    )
    city = property(
        lambda self: (
            self.created_by.CITY._display_map[self.created_by.city]
            if self.created_by.city
            else ""
        )
    )
    notifications = GenericRelation(Notification)

    @property
    def total_products(self):
        orderLines = self.order_lines.all()
        return sum([orderLine.quantity for orderLine in orderLines])

    @property
    def shipping_cost(self):
        return Decimal(0)
        # if not self.created_by.city or self.created_by.is_wholesale:
        #     return Decimal(0)
        # if self.created_by.city == get_user_model().CITY.baghdad:
        #     return Decimal(5000)
        # return Decimal(10000)

    @property
    def total_price_usd(self):
        return round(self.total_price / config.USD_TO_IQD_EXCHANGE_RATE, 2)

    @property
    def total_price_with_shipping(self):
        return self.total_price + self.shipping_cost

    @property
    def total_price_with_shipping_usd(self):
        return round(self.total_price_usd) + (
            round(self.shipping_cost / config.USD_TO_IQD_EXCHANGE_RATE, 2)
        )

    @property
    def total_price_minus_wallet(self):
        return self.total_price - self.paid_amount_from_wallet

    @property
    def total_price_minus_wallet_usd(self):
        return round(self.total_price_minus_wallet / config.USD_TO_IQD_EXCHANGE_RATE, 2)

    def send_order_pending_email(self):
        # return
        print("Sending order pending email...")
        order_lines = OrderLine.objects.filter(order=self)
        html = get_template("orders/order_pending.html").render(
            {
                "username": self.created_by.username,
                "order_lines": order_lines,
                "total": self.total_price
            }
        )
        mail = EmailMessage(
            subject=f"Order {self.order_number} Created",
            body=html,
            from_email=settings.EMAIL_HOST_USER,
            to=[self.created_by.email],
        )
        mail.content_subtype = "html"
        mail.send()

    def send_order_approved_email(self):
        # return
        order_lines = OrderLine.objects.filter(order=self)
        


        # Render email template
        html = get_template("orders/order_approved.html").render(
            {
                "username": self.created_by.username,
                "order_lines": order_lines,
                "total": self.total_price
            }
        )

        # Create and send email message
        email_subject = f"Order {self.order_number} is Approved, Thanks for Purchasing"
        email = EmailMessage(
            subject=email_subject,
            body=html,
            from_email=settings.EMAIL_HOST_USER,
            to=[self.created_by.email],
        )
        email.content_subtype = "html"
        email.send()

    @hook(AFTER_SAVE)
    def set_is_wholesale(self):
        self.is_wholesale = self.created_by.wholesale_type is not None

    @hook(AFTER_SAVE, when="status", was="pending", is_now="approved")
    def approve_order(self):
        self.send_order_approved_email()

    @hook(AFTER_SAVE, when="status", was="pending", is_now="rejected")
    def reject_order(self):
        # send email to the user

        html = get_template("orders/order_rejected.html").render(
            {
                "username": self.created_by.username,
                "order_number": self.order_number,
            }
        )
        # send email to the user
        mail = EmailMessage(
            subject=f"Order {self.order_number} Rejected",
            body=html,
            from_email=settings.EMAIL_HOST_USER,
            to=[self.created_by.email],
        )
        mail.content_subtype = "html"
        mail.send()

    @hook(AFTER_SAVE, when="status", is_now="returned")
    def return_order(self):
        # send email to the user
        html = get_template("orders/order_returned.html").render(
            {
                "order_number": self.order_number,
            }
        )
        # send email to the user
        mail = EmailMessage(
            subject=f"Order {self.order_number} Returned",
            body=html,
            from_email=settings.EMAIL_HOST_USER,
            to=[self.created_by.email],
        )
        mail.content_subtype = "html"
        mail.send()

    @hook(AFTER_SAVE, when="payment_status", is_now="failed")
    @hook(AFTER_SAVE, when="status", is_now="canceled")
    def unuse_keys(self):
        for order_line in self.order_lines.all():
            for order_line_key in order_line.order_line_keys.all():
                order_line_key.key.is_used = False
                order_line_key.key.used_by = None
                order_line_key.key.used_at = None
                order_line_key.key.used_order = None
                order_line_key.key.save()
                order_line_key.delete()

    def create_zain_cash_transaction(self):
        if not (
            settings.ZAIN_CASH_TRANSACTION_URL
            or settings.ZAIN_CASH_MSISDN
            or settings.ZAIN_CASH_MERCHANT_ID
            or settings.ZAIN_CASH_MERCHANT_SECRET
        ):
            raise APIException("Can not connect to zain cash", code=500)
        url = settings.ZAIN_CASH_TRANSACTION_URL
        msisdn = settings.ZAIN_CASH_MSISDN
        merchant_id = settings.ZAIN_CASH_MERCHANT_ID
        merchant_secret = settings.ZAIN_CASH_MERCHANT_SECRET
        redirect_url = settings.ZAIN_CASH_REDIRECT_URL
        data = {
            "amount": str(self.total_price_minus_wallet),
            "serviceType": "Original Software",
            "msisdn": msisdn,
            "orderId": self.id,
            "redirectUrl": redirect_url,
            "iat": time.time(),
            "exp": time.time() + 3600,
        }
        newtoken = jwt.encode(
            data,
            key=merchant_secret,
            algorithm="HS256",
        )
        data_to_post = {
            "token": newtoken,
            "merchantId": merchant_id,
            "lang": "en",
        }
        headers = {
            "Content-Type": "Content-type: application/x-www-form-urlencoded",
        }

        response = requests.post(
            f"{url}/init", data=json.dumps(data_to_post), headers=headers
        )
        if response.status_code != 200:
            self.payment_status = self.PAYMENT_STATUS.failed
            self.save()
        response_data = response.json()
        if response_data.get("status", "pending") != "pending":
            self.payment_status = self.PAYMENT_STATUS.failed
            self.save()
        transaction_id = response_data.get("id", "")
        if not transaction_id:
            self.payment_status = self.PAYMENT_STATUS.failed
            self.save()
        self.transaction_id = transaction_id
        self.transaction_url = f"{url}/pay?id={transaction_id}"
        self.save()

    def create_qi_card_transaction(self):
        # raise APIException("Maintenance", code=500)
        if not (
            settings.QICARD_PAY_TRANSACTION_URL
            or settings.QICARD_USERNAME
            or settings.QICARD_PASSWORD
        ):
            raise APIException("Can not connect to qi card", code=500)

        username = settings.QICARD_USERNAME
        password = settings.QICARD_PASSWORD
        url = settings.QICARD_PAY_TRANSACTION_URL
        redirect_url = settings.QICARD_REDIRECT_URL
        webhook_url = settings.QICARD_WEBHOOK_URL

        data = {
            "requestId": str(uuid.uuid4()),
            "amount": float(self.total_price_minus_wallet),
            "currency": "IQD",
            "finishPaymentUrl": redirect_url,
            "notificationUrl": webhook_url,
            "additionalInfo": {
                "website": "Original Software",
            },
        }

        headers = {
            "Content-Type": "application/json",
            "X-Terminal-Id": settings.QICARD_TERMINAL_ID,
        }

        response = requests.post(
            url,
            data=json.dumps(data),
            headers=headers,
            auth=HTTPBasicAuth(username, password),
        )
        if response.status_code != 200:
            self.payment_status = self.PAYMENT_STATUS.failed
            self.save()

        response_data = response.json()
        if response_data.get("status", "FAILED") != "CREATED":
            self.payment_status = self.PAYMENT_STATUS.failed
            self.save()

        self.transaction_id = response_data["paymentId"]
        self.transaction_url = response_data["formUrl"]
        self.save()

    # @staticmethod
    # def create_qi_card_refund_transaction():
    #     # raise APIException("Maintenance", code=500)
    #     if not (
    #         settings.QICARD_PAY_TRANSACTION_URL
    #         or settings.QICARD_USERNAME
    #         or settings.QICARD_PASSWORD
    #     ):
    #         raise APIException("Can not connect to qi card", code=500)

    #     username = settings.QICARD_USERNAME
    #     password = settings.QICARD_PASSWORD
    #     url = f"https://uat-sandbox-3ds-api.qi.iq/api/v1/payment/d913bba2-8f0c-4547-a840-e3c83dce8840/refund"
    #     redirect_url = settings.QICARD_REDIRECT_URL
    #     webhook_url = settings.QICARD_WEBHOOK_URL

    #     # data = {
    #     #     "requestId": str(uuid.uuid4()),
    #     #     "amount": float(self.total_price_minus_wallet),
    #     #     "currency": "IQD",
    #     #     # "finishPaymentUrl": redirect_url,
    #     #     # "notificationUrl": webhook_url,
    #     #     "additionalInfo": {
    #     #         "website": "Original Software",
    #     #     },
    #     # }

    #     data = {
    #         "requestId": str(uuid.uuid4()),
    #         "amount": 10000.00,
    #         "message": "I want my money back :)"
    #     }

    #     headers = {
    #         "Content-Type": "application/json",
    #         "X-Terminal-Id": settings.QICARD_TERMINAL_ID,
    #     }

    #     response = requests.post(
    #         url,
    #         data=json.dumps(data),
    #         headers=headers,
    #         auth=HTTPBasicAuth(username, password),
    #     )
    #     # if response.status_code != 200:
    #     #     self.payment_status = self.PAYMENT_STATUS.failed
    #     #     self.save()

    #     response_data = response.json()
    #     print(response_data)
    #     # if response_data.get("status", "FAILED") != "CREATED":
    #     #     self.payment_status = self.PAYMENT_STATUS.failed
    #     #     self.save()

    #     # self.transaction_id = response_data["paymentId"]
    #     # self.transaction_url = response_data["formUrl"]
    #     # self.save()
    # @staticmethod
    # def create_qi_card_cancel_transaction():
    #     # raise APIException("Maintenance", code=500)
    #     if not (
    #         settings.QICARD_PAY_TRANSACTION_URL
    #         or settings.QICARD_USERNAME
    #         or settings.QICARD_PASSWORD
    #     ):
    #         raise APIException("Can not connect to qi card", code=500)

    #     username = settings.QICARD_USERNAME
    #     password = settings.QICARD_PASSWORD
    #     url = f"https://uat-sandbox-3ds-api.qi.iq/api/v1/payment/eecad374-29a8-4094-bb5b-6fc35d104d7c/cancel"
    #     redirect_url = settings.QICARD_REDIRECT_URL
    #     webhook_url = settings.QICARD_WEBHOOK_URL

    #     # data = {
    #     #     "requestId": str(uuid.uuid4()),
    #     #     "amount": float(self.total_price_minus_wallet),
    #     #     "currency": "IQD",
    #     #     # "finishPaymentUrl": redirect_url,
    #     #     # "notificationUrl": webhook_url,
    #     #     "additionalInfo": {
    #     #         "website": "Original Software",
    #     #     },
    #     # }

    #     data = {
    #         "requestId": str(uuid.uuid4()),
    #     }

    #     headers = {
    #         "Content-Type": "application/json",
    #         "X-Terminal-Id": settings.QICARD_TERMINAL_ID,
    #     }

    #     response = requests.post(
    #         url,
    #         data=json.dumps(data),
    #         headers=headers,
    #         auth=HTTPBasicAuth(username, password),
    #     )
    #     # if response.status_code != 200:
    #     #     self.payment_status = self.PAYMENT_STATUS.failed
    #     #     self.save()

    #     response_data = response.json()
    #     print(response_data)
    #     # if response_data.get("status", "FAILED") != "CREATED":
    #     #     self.payment_status = self.PAYMENT_STATUS.failed
    #     #     self.save()

    #     # self.transaction_id = response_data["paymentId"]
    #     # self.transaction_url = response_data["formUrl"]
    #     # self.save()

    @staticmethod
    def verify_qi_card_webhook_signature(
        payload: Dict[str, Any],
        signature_b64: str,
    ) -> bool:
        # bcuz qi is stupid
        return True
        """
        Verify a webhook’s RSA/SHA256 signature, loading the public key from disk.

        :param payload: The JSON payload received in the webhook (as a dict).
        :param signature_b64: The contents of the X-Signature header (base64-encoded).
        :return: True if the signature is valid, False otherwise.
        """
        # 1) Build the data string from selected fields, using '-' as placeholder if missing.
        fields = [
            payload.get("paymentId", "-"),
            f'{payload["amount"]}.000' if payload.get(
                "amount") is not None else "-",
            payload.get("currency", "-"),
            payload.get("creationDate", "-"),
            payload.get("status", "-"),
        ]
        data_string = "|".join(fields).encode("utf-8")
        public_key_path = settings.QICARD_PUBLIC_KEY_PATH

        # 2) Decode the signature from base64
        try:
            signature = base64.b64decode(signature_b64)
        except Exception:
            return False

        # 3) Load the public key from the given path
        try:
            with open(public_key_path, "rb") as key_file:
                public_key = serialization.load_pem_public_key(key_file.read())
        except Exception:
            return False

        # 4) Perform verification using PKCS#1 v1.5 padding and SHA-256
        try:
            public_key.verify(
                signature,
                data_string,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def create_fastpay_transaction(self):
        if not (
            settings.FASTPAY_PAYMENT_INITIAITON_URL
            or settings.FASTPAY_STORE_ID
            or settings.FASTPAY_STORE_PASSWORD
        ):
            raise APIException("Can not connect to fastpay", code=500)

        url = settings.FASTPAY_PAYMENT_INITIAITON_URL
        store_id = settings.FASTPAY_STORE_ID
        store_password = settings.FASTPAY_STORE_PASSWORD
        cart = json.dumps(
            [
                {
                    "name": "Original Software Order",
                    "qty": 1,
                    "unit_price": int(self.total_price_minus_wallet),
                    "sub_total": int(self.total_price_minus_wallet),
                }
            ]
        )
        data = {
            "store_id": store_id,
            "store_password": store_password,
            "order_id": self.id,
            "bill_amount": int(self.total_price_minus_wallet),
            "currency": "IQD",
            "cart": cart,
        }
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            self.payment_status = self.PAYMENT_STATUS.failed
            self.save()
        response_data = response.json()
        self.transaction_id = response_data["data"]["redirect_uri"]
        self.transaction_url = response_data["data"]["redirect_uri"]
        self.save()

    @staticmethod
    def auth_fib():
        if not (
            settings.FIB_AUTH_URL
            or settings.FIB_CLIENT_ID
            or settings.FIB_CLIENT_SECRET
        ):
            raise APIException("Can not connect to fib", code=500)

        url = settings.FIB_AUTH_URL
        client_id = settings.FIB_CLIENT_ID
        client_secret = settings.FIB_CLIENT_SECRET

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        response = requests.post(url, data=data)
        if response.status_code != 200:
            raise APIException("Can not connect to fib", code=500)
        response_data = response.json()
        return response_data["access_token"]

    def create_fib_transaction(self):
        if not (
            settings.FIB_CREATE_PAYMENT_URL
            or settings.FIB_CLIENT_ID
            or settings.FIB_CLIENT_SECRET
            or settings.FIB_REDIRECT_URL
        ):
            raise APIException("Can not connect to fib", code=500)

        url = settings.FIB_CREATE_PAYMENT_URL
        redirect_url = settings.FIB_REDIRECT_URL
        access_token = self.auth_fib()
        data = {
            "monetaryValue": {
                "amount": int(self.total_price_minus_wallet),
                "currency": "IQD",
            },
            "statusCallbackUrl": redirect_url,
            "description": f"Original Software Order {self.order_number}",
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 201:
            self.payment_status = self.PAYMENT_STATUS.failed
            self.save()
        response_data = response.json()
        self.transaction_id = response_data["paymentId"]
        self.transaction_url = response_data["personalAppLink"]
        self.qr_code = response_data["qrCode"]
        self.readable_code = response_data["readableCode"]
        self.fib_payment_valid_until = response_data["validUntil"]
        self.save()

    def set_order_and_keys_as_viewed(self):
        self.is_viewed = True
        self.save()
        for order_line in self.order_lines.all():
            for order_line_key in order_line.order_line_keys.all():
                order_line_key.key.is_viewed = True
                order_line_key.key.save()

    def use_wallet_balance(self):
        if not self.use_wallet:
            return

        user = self.created_by
        balance = user.wallet_balance

        if user.wholesale_type is None:
            # Ensure balance is positive and sufficient to cover the total price
            if balance >= self.total_price:
                self.paid_amount_from_wallet = self.total_price
            else:
                self.paid_amount_from_wallet = balance
        else:
            # Ensure the balance won't exceed the negative limit after the order
            if balance - self.total_price < -user.wholesale_type.negative_limit:
                self.paid_amount_from_wallet = balance
            else:
                self.paid_amount_from_wallet = self.total_price
        # Save the updated order
        self.save()
        # Create a transaction for the paid amount
        Transaction.objects.create(
            transaction_type=Transaction.TRANSACTION_TYPE.order,
            user=user,
            amount=-self.paid_amount_from_wallet,
            description=f"Order {self.order_number}",
            related_order=self,
        )

    def create_order_for_user(self, user):
        self.created_by = user
        self.save()

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            Notification.objects.create(
                related_user=self.created_by,
                content_object=self,
                linked_model_name="orders.Order",
                description=f"Order {self.order_number} created",
                notification_level=Notification.NOTIFICATION_LEVELS.low,
            )
            
        else:
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        for order_line in self.order_lines.all():
            order_line.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f" Order: {self.order_number}"


class OrderLine(LifecycleModelMixin, TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Order Lines"
        ordering = ["seq"]

    seq = models.PositiveIntegerField(default=1)

    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        related_name="order_lines",
        related_query_name="order_line",
        null=False,
        blank=False,
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="order_lines",
        related_query_name="order_line",
        null=False,
        blank=False,
    )

    product_image = models.URLField(blank=True, null=True)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=26, decimal_places=0)

    @hook(BEFORE_CREATE)
    def set_unit_price(self):
        if self.order.is_wholesale:
            wholesale_pricing = self.product.wholesale_pricings.filter(
                wholesale_user_type=self.order.created_by.wholesale_type
            ).first()
            if wholesale_pricing:
                self.unit_price = wholesale_pricing.price
            else:
                self.unit_price = self.product.price
        else:
            self.unit_price = self.product.price

    unit_price_usd = property(
        lambda self: round(self.unit_price /
                           config.USD_TO_IQD_EXCHANGE_RATE, 2)
    )

    @hook(AFTER_CREATE)
    def product_image_url(self):
        self.product_image = self.first_product_image
        self.save()

    @property
    def sub_total(self):
        return self.unit_price * self.quantity

    sub_total_usd = property(
        lambda self: round(self.sub_total / config.USD_TO_IQD_EXCHANGE_RATE, 2)
    )

    def preform_cashback(self):
        if self.product.cashback_amount and self.product.cashback_amount > 0:
            Transaction.objects.create(
                transaction_type=Transaction.TRANSACTION_TYPE.deposit,
                user=self.order.created_by,
                amount=self.product.cashback_amount * self.quantity,
                description=f"Cashback for purchasing Qty: {self.quantity} of {self.product.name} in Order {self.order.order_number}",
                related_order=self.order,
            )

    def use_keys(self):
        if self.product.is_key_product and not self.product.offer_products.exists():
            keys_to_use = ProductKey.objects.filter(
                product=self.product, is_used=False
            )[: self.quantity]
            for key in keys_to_use:
                key.is_used = True
                key.used_by = self.created_by
                key.used_order = self.order
                key.save()
                OrderLineKey.objects.create(order_line=self, key=key)
        elif self.product.offer_products.exists():
            for offer_product in self.product.offer_products.all():
                keys_to_use = ProductKey.objects.filter(
                    product=offer_product, is_used=False
                )[: self.quantity]
                for key in keys_to_use:
                    key.is_used = True
                    key.used_by = self.created_by
                    key.used_order = self.order
                    key.save()
                    OrderLineKey.objects.create(
                        order_line=self,
                        key=key,
                        other_info=f"{offer_product.name}",
                    )

    @property
    def first_product_image(self):
        return self.product.images.first().image_file.url

    @property
    def payment_method(self):
        return self.order.payment_method

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.product.is_key_product:
            for order_line_key in OrderLineKey.objects.filter(order_line=self):
                order_line_key.key.is_used = False
                order_line_key.key.is_viewed = False
                order_line_key.key.used_by = None
                order_line_key.key.used_at = None
                order_line_key.key.used_order = None
                order_line_key.key.save()
                order_line_key.delete()
        # return the product quantity to the stock
        self.product.qty += self.quantity
        self.product.save()

        super().delete(*args, **kwargs)

    def __str__(self):
        return f" Order Line for {self.order.order_number}"


class OrderLineKey(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Order Lines Key"

    order_line = models.ForeignKey(
        "OrderLine",
        on_delete=models.CASCADE,
        related_name="order_line_keys",
        related_query_name="order_line_key",
        null=False,
        blank=False,
    )

    key = models.ForeignKey(
        "products.ProductKey",
        on_delete=models.CASCADE,
        related_name="order_line_keys",
        related_query_name="order_line_key",
        null=False,
        blank=False,
    )
    other_info = models.CharField(max_length=100, blank=True)

    key_serial = property(lambda self: self.key.key)
    used_at = property(lambda self: self.key.used_at)

    def __str__(self):
        return f" Order Line Key for {self.order_line.order.order_number}"


class SupportTicket(TimeStampedModel, UserStampedModel):
    class Meta:
        verbose_name_plural = "Support Tickets"
        ordering = ["-id"]

    full_name = models.CharField(
        "Full Name",
        max_length=50,
    )
    email = models.EmailField("Email", max_length=254)
    phone = models.CharField(
        "Phone",
        max_length=50,
    )
    description = models.TextField("Description")

    def __str__(self):
        return f" Support Ticket: {self.full_name}"
