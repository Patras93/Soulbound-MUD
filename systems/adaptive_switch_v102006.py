# -*- coding: utf-8 -*-
"""Read-only, startup-loaded Adaptive Combat compatibility switch.

Old settings remain readable, but there are no runtime editing commands or
configuration writes. Team skills and aggro are independent of this flag.
"""
from __future__ import annotations
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config' / 'adaptive_combat_global_v102006.json'
_ENABLED = None


def enabled():
    global _ENABLED
    if _ENABLED is None:
        if CONFIG_PATH.is_file():
            doc = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            if (type(doc) is not dict or doc.get('schema') not in (1, 2)
                    or type(doc.get('enabled')) is not bool):
                raise ValueError('Niepoprawne ustawienie Adaptive Combat w LIVE_CONTENT.')
            # A legacy ON setting cannot silently bring back unwanted party scaling.
            _ENABLED = doc['enabled'] if doc['schema'] == 2 else False
        else:
            _ENABLED = False  # Fresh installations do not scale by party size.
    return _ENABLED


def reset_mob(mob, template):
    """Remove previously accrued player/party scaling, retaining combat damage.

    Do not touch authored boss/region/floor definitions, combat phases or
    intrinsic buffs. Use integer ratios to support arbitrarily high HP.
    """
    previous = int(getattr(mob, 'adaptive_max_hp_v11330', 0) or 0)
    base = max(1, int((template or {}).get('max_hp', 1) or 1))
    if previous > 0 and getattr(mob, 'alive', False):
        old_hp = min(previous, max(0, int(getattr(mob, 'hp', 0) or 0)))
        if old_hp > 0:
            mob.hp = max(1, min(base, (base * old_hp + previous - 1) // previous))
        else:
            mob.hp = 0
    mob.adaptive_max_hp_v11330 = 0
    mob.adaptive_hp_multiplier_v11330 = 1.0
    mob.adaptive_reward_multiplier_v11330 = 1.0
    mob.adaptive_party_size_v11330 = 1
    mob.adaptive_party_dps_v11330 = 0.0
    mob.adaptive_rank_v11330 = ''
    return previous > 0


