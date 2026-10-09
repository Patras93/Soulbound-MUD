# -*- coding: utf-8 -*-
"""Bounded, predictable commodity demand shared by inventory/sale estimations."""
import hashlib
import time

CATEGORIES = ('fish', 'ore', 'wood', 'herb')

def market_demand_v1250(category, now=None):
    if category not in CATEGORIES: return 1.0
    now = time.time() if now is None else float(now)
    slot = int(now // (6 * 3600))  # Same price for six hours, no per-command reroll.
    digest = hashlib.sha256(f'soulbound:market1250:{category}:{slot}'.encode()).digest()
    return round(.92 + digest[0] / 255.0 * .30, 3)

def material_grade_v1250(item_ids, items):
    """Material identity, tier and rare-quality impact craft outcomes."""
    grade = 0
    for item_id in item_ids:
        data = items.get(item_id, {})
        if not data: continue
        rarity = str(data.get('rarity', '')).casefold()
        rare = float(data.get('rare_value_multiplier', 1) or 1)
        level = max(1, int(data.get('required_level', data.get('level', 1)) or 1))
        name = str(data.get('name', item_id)).casefold()
        entry = 1 if level >= 40 else 0
        if level >= 150 or any(x in name for x in ('mithril', 'adamant', 'legendarn', 'mityczn', 'eter', 'runicz')):
            entry = 2
        if rare >= 2 or rarity in ('epic', 'legendary', 'mythic'): entry += 2
        grade = max(grade, entry)
    return min(4, grade)

def material_quality_upgrade_v1250(quality, grade, random_roll):
    """Rare ingredients can promote one tier, never downgrade normal materials."""
    CRAFT_QUALITY_ORDER_V03054 = ("normal", "good", "excellent", "masterwork", "legendary")
    if quality not in CRAFT_QUALITY_ORDER_V03054 or grade < 1:
        return quality
    if float(random_roll) >= min(.60, .08 * grade + .03): return quality
    idx = CRAFT_QUALITY_ORDER_V03054.index(quality)
    return CRAFT_QUALITY_ORDER_V03054[min(len(CRAFT_QUALITY_ORDER_V03054)-1, idx + 1)]
