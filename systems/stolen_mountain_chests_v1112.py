# -*- coding: utf-8 -*-
"""Better stolen chest supply without editing the protected mountain builder."""
from data import catalog_mutations as _catalog_mut


def enhance_stolen_mountain_chests_v1112(mobs):
    """Higher drops for real mountain trolls; quest contract is unchanged."""
    regular = ('mountain_troll','troll_brute','troll_shaman')
    rare = ('albino_troll','crystal_troll','ancient_troll','runic_troll')
    for template_id in regular + rare:
        template=mobs.get(template_id)
        if not template or 'stolen_mountain_ore' not in template.get('drops', {}):
            return False
    if mobs.get('troll_king',{}).get('drops',{}).get('stolen_mountain_ore') != 1.0:
        return False
    for template_id in regular:
        _catalog_mut.catalog_assign(.55,'MOB_TEMPLATES',mobs,(template_id,'drops','stolen_mountain_ore'))
    for template_id in rare:
        _catalog_mut.catalog_assign(.70,'MOB_TEMPLATES',mobs,(template_id,'drops','stolen_mountain_ore'))
    return True
