# -*- coding: utf-8 -*-
"""Gold-first PRICE labels without modifying the underlying wallet."""
from pathlib import Path
from core.bootstrap_economy_professions import (
    currency_price_text, currency_reading_text,
    legacy_currency_to_coins, SILVER_PER_GOLD, GOLD_PER_MITHRIL,
)
from systems.mercenary_taverns import MERCENARIES, price_silver


def validate_gold_prices_v1227():
    checks = 0
    samples = {
        0: '0 złota', 1: '0,01 złota', 25: '0,25 złota',
        99: '0,99 złota', 100: '1 złota', 150: '1,50 złota',
        10000: '100 złota', 12550: '125,50 złota',
        100_000_000: '1 000 000 złota',
    }
    for amount, expected in samples.items():
        value = currency_price_text(amount)
        assert value == expected, (amount, value, expected)
        checks += 1
        gold, fraction = divmod(amount, SILVER_PER_GOLD)
        assert int(value.split(' złota')[0].replace(' ', '').replace(',','')) == gold * (100 if fraction else 1) + (fraction if fraction else 0)
        checks += 1
    assert SILVER_PER_GOLD == 100 and GOLD_PER_MITHRIL == 1_000_000
    checks += 1
    assert currency_price_text(23, 2, 1) == '1 000 002,23 złota'
    checks += 1
    assert currency_reading_text(150,0,0) == '1 złota, 50 srebra'
    checks += 1
    assert legacy_currency_to_coins(150,0,0) == 150
    checks += 1

    class Owner:
        def shop_discount_percent(self):
            return 25
    for role, spec in MERCENARIES.items():
        price = price_silver(Owner(), role)
        assert price == spec['cost'] * 75, (role,price)
        assert currency_price_text(price) == f"{spec['cost']*75//100}" + (f",{spec['cost']*75%100:02d}" if spec['cost']*75%100 else '') + ' złota'
        checks += 2

    root = Path(__file__).resolve().parent.parent
    sources = {
        'player/session_mixins/shops_teachers.py': ('currency_price_text(money)', 'currency_price_text(total_price)'),
        'player/session_mixins/mercenary_taverns.py': ('currency_price_text(price)', 'currency_price_text(price_silver(self.character,role))'),
        'player/session_mixins/social_base.py': ('currency_price_text(cost_silver)',),
        'player/session_mixins/ocean.py': ('currency_price_text(self.V1000_SHIP_BASE_COST)',),
        'player/session_mixins/class_guild_progress.py': ('currency_price_text(total_silver_cost)',),
        'player/session_mixins/atlas_codex.py': ('"Cena kupna: " + currency_price_text(price_coins)',),
    }
    for file, needles in sources.items():
        source = (root / file).read_text(encoding='utf8')
        for needle in needles:
            assert needle in source, (file, needle)
            checks += 1
    return checks
