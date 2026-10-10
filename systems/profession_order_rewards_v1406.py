# -*- coding: utf-8 -*-
"""v1.40.6: economically meaningful, bounded specialist contract rewards.

Only computes new OFFER rewards.  Accepted orders keep their saved rewards and
historical completions are immutable. No persistent schema or random factors.
"""
from core.progression_resources import v0190_quest_currency_reward

MAX_ORDER_COINS_V1406 = 1_000_000_000_000


def _market_silver_v1406(item):
    """Conservative player sell value, not expensive NPC shop purchase price."""
    item = item or {}
    return max(0,
        int(item.get('sell_silver') or 0)
        + 100 * int(item.get('sell_gold') or 0)
        + 100_000_000 * int(item.get('sell_mithril') or 0),
        int(item.get('value') or 0),
    )


def balanced_order_reward_v1406(recipe, needed, item, required_level, *, item_catalog=None):
    """Return (silver, *raw* profession XP, *raw* tool XP).

    The established grant_profession_reward_xp pipeline applies all existing
    progression, guild and event multipliers to the raw values.  Contract
    rewards are intentionally larger without changing ordinary work rewards.
    """
    recipe = recipe or {}
    item = item or {}
    needed = max(1, min(1000, int(needed)))
    stage = max(1, min(800, int(recipe.get('order_reward_level',required_level) or required_level)))
    kind = str(item.get('order_kind') or recipe.get('order_kind') or '')
    tier = max(1, min(3, int(item.get('order_tier',recipe.get('order_tier',1)) or 1)))
    base_coins = max(50, int(v0190_quest_currency_reward({
        'min_profession_level':stage, 'needed':needed, 'repeatable':True
    })))
    # Substantial employer bonus, stronger for advanced specialists.  Synthetic
    # gather/action orders use the real tier to make large contracts worth it.
    wage_multiplier = (300 + stage * 3 // 8)  # x3 at level 1, ~x6 at 800
    tier_multiplier = 100 + (tier-1)*25 if kind in ('gather','action') else 100
    contract_wage = base_coins * wage_multiplier * tier_multiplier // 10_000
    # Never hand in expensive products for less than selling them yourself.
    catalog = item_catalog or {}
    output_value = _market_silver_v1406(item)
    ingredients = recipe.get('ingredients') or {}
    input_value = sum(
        max(0,int(qty or 0)) * _market_silver_v1406(catalog.get(item_id,{}))
        for item_id,qty in ingredients.items()
    )
    output_quantity = max(1, int(recipe.get('quantity',1) or 1))
    input_per_product = (input_value + output_quantity - 1) // output_quantity
    # NPC covers market cost and pays a real premium for delivery/labor.
    market_floor = needed * max(output_value,input_per_product) * 2
    # No single fixed resource can be priced for a synthetic category: the
    # player can deliver different ores/fish/wood/herbs. Pay a generous
    # per-action minimum even at level 1 without pretending every catch is a
    # mythical trophy. Repeatable orders stay once/offer/hour.
    if kind == 'gather':
        market_floor = max(market_floor, needed * (300 + stage // 2))
    elif kind == 'action':
        market_floor = max(market_floor, needed * (500 + stage))
    coins = max(150,contract_wage,market_floor)
    coins = min(MAX_ORDER_COINS_V1406,coins)
    raw_prof = max(25,int(recipe.get('profession_xp',max(20,stage*3)) or 0)*needed//2)
    raw_tool = max(15,int(recipe.get('tool_xp',max(15,stage*2)) or 0)*needed//3)
    # Bonus for completing the full order; not a change to action EXP.
    prof_factor = 200 + stage//8  # x2 to x3 across 1..800
    tool_factor = 200 + stage//10
    if kind in ('gather','action'):
        prof_factor += (tier-1)*20
        tool_factor += (tier-1)*20
    return coins, max(raw_prof,raw_prof*prof_factor//100), max(raw_tool,raw_tool*tool_factor//100)
