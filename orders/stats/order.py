from constance import config
from simple_stats import (
    ChoiceAggregateNullStat,
    QueryAggregateBucketsStat,
    QueryAggregateDateStat,
    QueryAggregateSingleStat,
    QueryAggregateStat,
    StatSet,

)

from orders.models import Order, OrderLine
from authentication.models import WholesaleUserType
from django.db.models import Count, F


class OrderStats(StatSet):
    total_orders_count = QueryAggregateSingleStat(
        label="Total Orders Count",
        field="id",
    )
    total_orders_count_per_status = ChoiceAggregateNullStat(
        label="Total Orders Count Per Status",
        field="status",
        aggr_field="id",
        choices=Order.STATUS,
    )
    total_orders_count_per_payment_status = ChoiceAggregateNullStat(
        label="Total Orders Count Per Payment Status",
        field="payment_status",
        aggr_field="id",
        choices=Order.PAYMENT_STATUS,
    )
    total_orders_count_per_payment_method = QueryAggregateStat(
        label="Total Orders Count Per Payment Method",
        field="payment_method",
        aggr_field="id",
        choices=Order.PAYMENT_METHOD,
    )
    total_orders_count_per_created_year = QueryAggregateDateStat(
        label="Total Orders Count Per Created Year",
        field="created",
        aggr_field="id",
        what="year",
    )
    total_orders_count_per_created_month = QueryAggregateDateStat(
        label="Total Orders Count Per Created Month",
        field="created",
        aggr_field="id",
        what="month",
    )
    total_orders_count_per_created_day = QueryAggregateDateStat(
        label="Total Orders Count Per Created Day",
        field="created",
        aggr_field="id",
        what="day",
    )
    total_orders_count_per_created_by = QueryAggregateStat(
        label="Total Orders Count Per Created By email",
        field="created_by__email",
    )
    total_orders_count_per_product_name = QueryAggregateStat(
        label="Total Orders Count Per Product Name",
        field="order_line__product__name",
    )

    total_orders_count_per_product_name_ar = QueryAggregateStat(
        label="Total Orders Count Per Product Name Arabic",
        field="order_line__product__name_ar",
    )
    total_orders_count_per_product_category_name = QueryAggregateStat(
        label="Total Orders Count Per Product Category Name",
        field="order_line__product__category__name",
    )
    total_orders_count_per_product_category_name_ar = QueryAggregateStat(
        label="Total Orders Count Per Product Category Name Arabic",
        field="order_line__product__category__name_ar",
    )
    total_orders_count_per_created_by_city = QueryAggregateStat(
        label="Total Orders Count Per Created By City",
        field="created_by__city",
    )
    total_orders_price = QueryAggregateSingleStat(
        label="Total Orders Price",
        field="total_price",
        method="sum",
    )
    total_orders_price_usd = QueryAggregateSingleStat(
        label="Total Orders Price USD",
        field="total_price",
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )
    total_orders_price_per_status = ChoiceAggregateNullStat(
        label="Total Orders Price Per Status",
        field="status",
        aggr_field="total_price",
        choices=Order.STATUS,
        method="sum",
    )
    total_orders_price_usd_per_status = ChoiceAggregateNullStat(
        label="Total Orders Price USD Per Status",
        field="status",
        aggr_field="total_price",
        choices=Order.STATUS,
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )
    total_orders_price_per_payment_status = ChoiceAggregateNullStat(
        label="Total Orders Price Per Payment Status",
        field="payment_status",
        aggr_field="total_price",
        choices=Order.PAYMENT_STATUS,
        method="sum",
    )
    total_orders_price_usd_per_payment_status = ChoiceAggregateNullStat(
        label="Total Orders Price USD Per Payment Status",
        field="payment_status",
        aggr_field="total_price",
        choices=Order.PAYMENT_STATUS,
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )
    total_orders_price_per_payment_method = QueryAggregateStat(
        label="Total Orders Price Per Payment Method",
        field="payment_method",
        aggr_field="total_price",
        choices=Order.PAYMENT_METHOD,
        method="sum",
    )
    total_orders_price_usd_per_payment_method = QueryAggregateStat(
        label="Total Orders Price USD Per Payment Method",
        field="payment_method",
        aggr_field="total_price",
        choices=Order.PAYMENT_METHOD,
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )
    total_orders_price_per_created_year = QueryAggregateDateStat(
        label="Total Orders Price Per Created Year",
        field="created",
        aggr_field="total_price",
        choices=Order.PAYMENT_METHOD,
        what="year",
        method="sum",
    )
    total_orders_price_usd_per_created_year = QueryAggregateDateStat(
        label="Total Orders Price Per Created Year",
        field="created",
        aggr_field="total_price",
        choices=Order.PAYMENT_METHOD,
        what="year",
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )
    total_orders_price_per_created_month = QueryAggregateDateStat(
        label="Total Orders Price USD Per Created Month",
        field="created",
        aggr_field="total_price",
        what="month",
        method="sum",
    )
    total_orders_price_usd_per_created_month = QueryAggregateDateStat(
        label="Total Orders Price Per Created Month",
        field="created",
        aggr_field="total_price",
        what="month",
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )
    total_orders_price_per_created_day = QueryAggregateDateStat(
        label="Total Orders Price Per Created Day",
        field="created",
        aggr_field="total_price",
        what="day",
        method="sum",
    )
    total_orders_price_usd_per_created_day = QueryAggregateDateStat(
        label="Total Orders Price USD Per Created Day",
        field="created",
        aggr_field="total_price",
        what="day",
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )
    total_orders_price_per_created_by = QueryAggregateStat(
        label="Total Orders Price Per Created By email",
        field="created_by__email",
        aggr_field="total_price",
        method="sum",
    )
    total_orders_price_usd_per_created_by = QueryAggregateStat(
        label="Total Orders Price USD Per Created By email",
        field="created_by__email",
        aggr_field="total_price",
        method="sum",
        formatter=lambda x: round(x / config.USD_TO_IQD_EXCHANGE_RATE, 2),
    )

    