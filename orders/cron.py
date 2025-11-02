from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django_cron import CronJobBase, Schedule

from orders.models import Order


class CancelOrdersNotPaid(CronJobBase):
    RUN_EVERY_MINS = 5

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "orders.cancel_orders_not_paid"

    def do(self):
        count = 0
        # orders that have not been paid for 15 minutes will be canceled but the payment_method is not fib
        orders = Order.objects.filter(
            ~Q(payment_method=Order.PAYMENT_METHOD.fib),
            payment_status=Order.PAYMENT_STATUS.pending,
            created__lt=timezone.now() - timedelta(minutes=15),
        )
        for order in orders:
            order.status = Order.STATUS.canceled
            order.save()

        count += orders.count()

        # for fib orders we will check that it does not now > fib_payment_valid_until
        fib_orders = Order.objects.filter(
            payment_method=Order.PAYMENT_METHOD.fib,
            payment_status=Order.PAYMENT_STATUS.pending,
            fib_payment_valid_until__lt=timezone.now(),
        )
        for order in fib_orders:
            order.status = Order.STATUS.canceled
            order.save()

        count += fib_orders.count()

        return f"{orders.count()} orders have been canceled"
