from simple_stats import (
    ChoiceAggregateNullStat,
    QueryAggregateBucketsStat,
    QueryAggregateDateStat,
    QueryAggregateSingleStat,
    QueryAggregateStat,
    StatSet,
)

from products.models import Product


class ProductStats(StatSet):
    id = QueryAggregateSingleStat(label="Total Products")
    tag = ChoiceAggregateNullStat(label="Per Tag", choices=Product.TAG)
    category__name = QueryAggregateStat(label="Per Category Name")
    category__name_ar = QueryAggregateStat(label="Per Category Name Arabic")
    available = QueryAggregateStat(label="Available")
    is_key_product = QueryAggregateStat(label="Key Products")
