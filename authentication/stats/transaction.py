from constance import config
from simple_stats import (
    ChoiceAggregateStat,
    QueryAggregateDateStat,
    QueryAggregateSingleStat,
    QueryAggregateStat,
    StatSet,
)

from authentication.models import Transaction


class TransactionStats(StatSet):
    total_transactions_count = QueryAggregateSingleStat(
        label="Total Transactions Count",
        field="id",
    )
    total_transactions_count_per_created_year = QueryAggregateDateStat(
        label="Total Transactions Count Per Created Year",
        field="created",
        aggr_field="id",
        what="year",
    )
    total_transactions_count_per_created_month = QueryAggregateDateStat(
        label="Total Transactions Count Per Created Month",
        field="created",
        aggr_field="id",
        what="month",
    )
    total_transactions_count_per_created_day = QueryAggregateDateStat(
        label="Total Transactions Count Per Created Day",
        field="created",
        aggr_field="id",
        what="day",
    )
    total_transactions_count_per_user = QueryAggregateStat(
        label="Total Transactions Count Per User",
        field="user",
        aggr_field="id",
    )
    total_transactions_count_per_transaction_type = ChoiceAggregateStat(
        label="Total Transactions Count Per Transaction Type",
        field="transaction_type",
        aggr_field="id",
        choices=Transaction.TRANSACTION_TYPE,
    )
    total_transactions_amount_per_user = QueryAggregateStat(
        label="Total Transactions Amount Per User",
        field="user",
        aggr_field="amount",
    )
    total_transactions_amount_per_created_year = QueryAggregateDateStat(
        label="Total Transactions Amount Per Created Year",
        field="created",
        aggr_field="amount",
        what="year",
    )
    total_transactions_amount_per_created_month = QueryAggregateDateStat(
        label="Total Transactions Amount Per Created Month",
        field="created",
        aggr_field="amount",
        what="month",
    )
    total_transactions_amount_per_created_day = QueryAggregateDateStat(
        label="Total Transactions Amount Per Created Day",
        field="created",
        aggr_field="amount",
        what="day",
    )
    total_transactions_amount_per_transaction_type = ChoiceAggregateStat(
        label="Total Transactions Amount Per Transaction Type",
        field="transaction_type",
        aggr_field="amount",
        choices=Transaction.TRANSACTION_TYPE,
    )
