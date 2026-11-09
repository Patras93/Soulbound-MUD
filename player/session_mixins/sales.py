# -*- coding: utf-8 -*-
"""Zgodny interfejs sprzedaży; implementacje przeniesiono do modułów v109.

MRO zachowuje wszystkie metody i publiczną nazwę SessionSalesMixin.
"""
from .sales_parts_v109.dependencies import *
from .sales_parts_v109 import (
    SalesPricingV109Mixin,
    SalesMarketV109Mixin,
    SalesProfessionExpV109Mixin,
    SalesBulkV109Mixin,
    SalesEquipmentV109Mixin,
    SalesResourcesV109Mixin
)

class SessionSalesMixin(
    SalesPricingV109Mixin,
    SalesMarketV109Mixin,
    SalesProfessionExpV109Mixin,
    SalesBulkV109Mixin,
    SalesEquipmentV109Mixin,
    SalesResourcesV109Mixin
):
    """Zgodny z v108 interfejs sprzedaży i skupów."""
    pass
