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


def masterpiece_chance_v12812(profession_level, tool_level, mastery_level, material_grade):
    """An extra, optional promotion with no artificial stat or player-level cap."""
    p=max(1,int(profession_level)); t=max(1,int(tool_level)); m=max(1,int(mastery_level)); g=max(0,int(material_grade))
    if g < 1 or p < 20 or t < 10: return 0.0
    return min(.12, .001 + min(600,p)*.000065 + min(600,t)*.000045 + min(100,m)*.00016 + min(4,g)*.005)

def masterpiece_promote_v12812(quality, profession_level, tool_level, mastery_level, material_grade, roll):
    levels=('normal','good','excellent','masterwork','legendary')
    if quality not in levels or quality == 'legendary': return quality, False
    chance=masterpiece_chance_v12812(profession_level,tool_level,mastery_level,material_grade)
    if float(roll) >= chance: return quality, False
    # Master craft: a meaningful bonus tier, not a flat equipment ID renaming.
    return levels[min(4,levels.index(quality)+1)], True
