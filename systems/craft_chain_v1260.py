# -*- coding: utf-8 -*-
"""Chain of actual professions, with no new equipment system or fake stats."""
QUALITY = ('normal','good','excellent','masterwork','legendary')

def craft_chain_bonus_v1260(quality, grade, levels, roll):
    """Good ore + mining/smithing/enchanting/archaeology can promote real quality.

    All four professions are useful, but none is mandatory; no downgrades or
    player level gates. This rolls after the original ingredient-quality roll.
    """
    if quality not in QUALITY or grade < 2 or quality == 'legendary':
        return quality
    levels = [max(0,int(v)) for v in levels]
    trained = sum(v>=10 for v in levels)
    if trained < 2:
        return quality
    chance = min(.30, .015*trained + .00013*sum(levels) + .015*grade)
    if float(roll) >= chance:
        return quality
    return QUALITY[min(4, QUALITY.index(quality)+1)]
