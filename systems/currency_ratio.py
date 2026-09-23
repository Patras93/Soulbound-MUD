# -*- coding: utf-8 -*-
"""Soulbound v0.38.5 - Currency Ratio Rebase.

Canonical wallet remains stored in silver. Only denomination ratios and all
commands/formatters using them change globally.
"""
from core.bootstrap_economy_professions import (
    SILVER_PER_GOLD, GOLD_PER_MITHRIL, SILVER_PER_MITHRIL,
    currency_reading_text, currency_unit_multiplier,
)
from world.equipment_help import HELP_TOPICS, HELP_TOPIC_ALIASES


V0385_CURRENCY_VERSION = "0.38.5"

def currency_ratio_audit_v0385():
    errors=[]
    def check(name, cond, detail):
        if not cond:
            errors.append(f"{name}: {detail}")
    check("silver_per_gold", int(SILVER_PER_GOLD)==100, SILVER_PER_GOLD)
    check("gold_per_mithril", int(GOLD_PER_MITHRIL)==1_000_000, GOLD_PER_MITHRIL)
    check("silver_per_mithril", int(SILVER_PER_MITHRIL)==100_000_000, SILVER_PER_MITHRIL)
    check("format_100_silver", currency_reading_text(100,0,0)=="1 złota", currency_reading_text(100,0,0))
    check("format_1_mithril", currency_reading_text(100_000_000,0,0)=="1 mithril", currency_reading_text(100_000_000,0,0))
    check("format_boundary", currency_reading_text(100_000_099,0,0)=="1 mithril, 99 srebra", currency_reading_text(100_000_099,0,0))
    check("gold_unit", currency_unit_multiplier("zloto")==100, currency_unit_multiplier("zloto"))
    check("mithril_unit", currency_unit_multiplier("mithril")==100_000_000, currency_unit_multiplier("mithril"))
    return {"version":V0385_CURRENCY_VERSION,"error_count":len(errors),"errors":errors}

CURRENCY_RATIO_AUDIT_V0385 = currency_ratio_audit_v0385()
if CURRENCY_RATIO_AUDIT_V0385["error_count"]:
    raise RuntimeError("Currency Ratio Audit v0.38.5 failed: " + "; ".join(CURRENCY_RATIO_AUDIT_V0385["errors"]))

HELP_TOPICS["waluta"] = [
    "Soulbound używa jednego wspólnego salda przechowywanego wewnętrznie w srebrze.",
    "100 srebra = 1 złoto.",
    "1 000 000 złota = 1 mithril.",
    "1 mithril = 100 000 000 srebra.",
    "Bank, sklepy, gildie, nagrody, transfery i formatter korzystają z tego samego globalnego kursu.",
]
HELP_TOPIC_ALIASES.update({"kurs":"waluta","kurs waluty":"waluta","currency":"waluta","money":"waluta"})
