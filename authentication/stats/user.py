from constance import config
from django.contrib.auth import get_user_model
from simple_stats import (
    ChoiceAggregateNullStat,
    QueryAggregateBucketsStat,
    QueryAggregateDateStat,
    QueryAggregateSingleStat,
    QueryAggregateStat,
    StatSet,
)


class UserStats(StatSet):
    total_users_count = QueryAggregateSingleStat(
        label="Total Users Count",
        field="id",
    )
    total_users_count_per_created_year = QueryAggregateDateStat(
        label="Total Users Count Per Created Year",
        field="created",
        aggr_field="id",
        what="year",
    )
    total_users_count_per_created_month = QueryAggregateDateStat(
        label="Total Users Count Per Created Month",
        field="created",
        aggr_field="id",
        what="month",
    )
    total_users_count_per_created_day = QueryAggregateDateStat(
        label="Total Users Count Per Created Day",
        field="created",
        aggr_field="id",
        what="day",
    )
    total_users_count_per_city = QueryAggregateStat(
        label="Total Users Count Per City",
        field="city",
        aggr_field="id",
    )
    total_users_count_per_gender = ChoiceAggregateNullStat(
        label="Total Users Count Per Gender",
        field="gender",
        aggr_field="id",
        choices=get_user_model().GENDER,
    )
    total_users_count_per_wholesale_type = QueryAggregateStat(
        label="Total Users Count Per Wholesale Type Title",
        field="wholesale_type__title",
        aggr_field="id",
    )
