# -*- coding: utf-8 -*-
"""v12.00.2: meaningful, non-regressive XP for actual jewelry crafts.

Only reached AFTER a real recipe succeeds and AFTER the general v12.00.1
profession/tool reward regulator.  Difficulty comes from the real recipe;
never use the character's current level as a proxy for material difficulty.
"""
from __future__ import annotations

QUALITY_BONUS = {
    'raw': 1.0, 'normal': 1.0, 'common': 1.0,
    'pure': 1.12, 'czysta': 1.12,
    'fine': 1.24, 'excellent': 1.24, 'doskonala': 1.24,
    'perfect': 1.40, 'perfekcyjna': 1.40,
}


def improved_jewelry_recipe_xp(profession_xp, tool_xp, recipe=None):
    """Supplement the existing paid craft action, never reduce its award.

    A cut stone takes valuable Mining input; a necklace uses more ingots
    than a ring.  Improved gem quality gets extra XP.  The general XP
    regulator has already handled relative required XP and recipe tier.
    """
    p = max(0, int(profession_xp or 0))
    t = max(0, int(tool_xp or 0))
    if not isinstance(recipe, dict):
        return p, t
    cut = bool(recipe.get('gem_cut_recipe'))
    ingredients = recipe.get('ingredients') or {}
    material_count = sum(max(0, int(qty)) for qty in ingredients.values())
    material_count = min(4, material_count)
    gem_quality = str(recipe.get('gem_quality') or 'raw').lower()
    quality_mult = QUALITY_BONUS.get(gem_quality, 1.0)
    # The bonus rewards actual work and resources.  It does not touch
    # progression requirements, RNG odds, currency, level caps or drops.
    profession_mult = (3.0 if cut else 2.5) * quality_mult
    tool_mult = (2.5 if cut else 2.0) * quality_mult
    if not cut and material_count >= 3:
        profession_mult += 0.30
        tool_mult += 0.20
    return (max(p, int(round(p * profession_mult))) if p else 0,
            max(t, int(round(t * tool_mult))) if t else 0)
