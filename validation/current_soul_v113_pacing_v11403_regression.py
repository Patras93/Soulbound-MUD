# -*- coding: utf-8 -*-
"""v114.00.3 mandatory regression: Soul Tier must not race through levels."""
from __future__ import annotations
import os


def run():
    # Build the historical tier catalogue first; test the REAL release XP
    # policy even when the caller enabled staging for the catalogue.
    from player.character import Character
    os.environ['SOULBOUND_V106_STAGING']='0'
    from core.progression_policy_v114 import install_deploy_policy
    install_deploy_policy()
    from core.progression_resources import soul_xp_to_next, soul_weapon_mastery_xp_to_next
    from systems.soul_xp_unbounded_v114 import historical_continuation_v11403
    # Concrete production-v113 reference at level 240, not a new v114 formula.
    assert soul_xp_to_next(240)==1_066_673_281_000, soul_xp_to_next(240)
    assert soul_xp_to_next(240)>15_646_770_816
    assert soul_xp_to_next(800)<soul_xp_to_next(801)
    assert soul_xp_to_next(801)==historical_continuation_v11403(801,soul_xp_to_next(800))
    assert soul_xp_to_next(60_001)>soul_xp_to_next(60_000)
    c=object.__new__(Character)
    c.soul_level=240; c.soul_tier=24; c.soul_xp=0; c.race='Człowiek'
    c._guild_bonus_percent=0
    c.racial_soul_xp_multiplier=lambda: 1.0
    previous_weapon=soul_weapon_mastery_xp_to_next(240)
    msgs=c.add_soul_xp(15_646_770_816)
    assert c.soul_level==240 and c.soul_tier==24 and c.soul_xp==15_646_770_816,(c.soul_level,c.soul_tier,c.soul_xp,msgs)
    assert soul_weapon_mastery_xp_to_next(240)==previous_weapon
    return 'PASS: v113 level-240 Soul threshold restored; 15.6bn XP cannot skip tiers; 801+ continuous; weapon mastery unchanged'

if __name__=='__main__':print(run())
