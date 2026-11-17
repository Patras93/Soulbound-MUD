# -*- coding: utf-8 -*-
"""Non-deployable WIP: minimal runtime checks for v114 progression policy."""

def run():
    # Match production: construct the authored native modules BEFORE applying
    # the static deploy policy, preventing unbounded catalogue construction.
    from player.character import Character
    from core.progression_policy_v114 import install_deploy_policy
    from core.live_level_caps_v5200 import cap
    # Tier 6000 catalogue was loaded with STAGING=1 by the PREDEPLOY runner,
    # but gameplay XP must be checked in the normal production policy.
    import os
    os.environ['SOULBOUND_V106_STAGING']='0'
    values=install_deploy_policy()
    axes=('postac','bieglosc','dusza','bron_duszy','skille','profesje','narzedzia','gildia','eq')
    assert all(values[k] is None for k in axes)
    assert cap('ulepszenia_eq') == 10
    from core.progression_resources import (
        character_xp_to_next,class_mastery_xp_to_next,soul_xp_to_next,
        skill_xp_to_next,soul_weapon_mastery_xp_to_next,
    )
    for callback in (character_xp_to_next,class_mastery_xp_to_next,
                     soul_xp_to_next,skill_xp_to_next,soul_weapon_mastery_xp_to_next):
        assert callback(800)>0, callback.__name__
        assert callback(801)>0, callback.__name__
    character=object.__new__(Character)
    character.character_level=800
    character.character_xp=0
    required=character_xp_to_next(800)
    lines=character.add_character_xp(required)
    assert character.character_level==801,(character.character_level,lines)
    assert character.character_xp==0
    from core.bootstrap_economy_professions import profession_max_level,tool_max_level
    assert profession_max_level('Górnictwo')>801
    assert tool_max_level('mining')>801
    # v114.00.3: 1..800 must match normal production v113 rather than
    # accidentally activating the v106 STAGING-only fast curve.
    from config.balance import SOUL_XP_REQUIREMENT_MULTIPLIER as _soul_mul
    from core.progression_resources import _late_game_axis_requirement
    from systems.soul_xp_bands_v10402 import requirement as _historic_band
    from systems.soul_xp_unbounded_v114 import historical_continuation_v11403
    for level in range(1,801):
        historic=_historic_band(level,_late_game_axis_requirement('soul',level,_soul_mul))
        assert soul_xp_to_next(level)==historic, (level,soul_xp_to_next(level),historic)
    assert soul_xp_to_next(240)==1_066_673_281_000
    assert soul_xp_to_next(240)>15_646_770_816
    assert soul_xp_to_next(801)==historical_continuation_v11403(801,soul_xp_to_next(800))
    assert soul_xp_to_next(801)>soul_xp_to_next(800)
    assert soul_xp_to_next(60_001)>soul_xp_to_next(60_000)>soul_xp_to_next(801)
    assert 0<soul_xp_to_next(1_000_000)<9_000_000_000_000_000_000
    soul=object.__new__(Character)
    soul.soul_level=60_000
    soul.soul_tier=6000
    soul.soul_xp=0
    soul.race='Człowiek'
    soul.racial_soul_xp_multiplier=lambda: 1.0
    soul._guild_bonus_percent=0
    needed=soul.soul_xp_to_next()
    messages=soul.add_soul_xp(needed)
    assert soul.soul_level==60_001 and soul.soul_xp==0,(messages,soul.soul_level,soul.soul_xp)
    # Prove overflow is blocked BEFORE in-memory modification, never after.
    soul.soul_xp=9_223_372_036_854_775_804
    try:soul.add_soul_xp(100)
    except OverflowError: pass  # AUDIT_INTENTIONAL_PASS: expected SQLite overflow denial
    else:raise AssertionError('Soul XP integer overflow not blocked')
    assert soul.soul_xp==9_223_372_036_854_775_804
    from core import live_level_caps_v5200 as stable
    assert not any(hasattr(stable, name) for name in ('change','change_all','reset','reset_all','load'))
    return 'PASS: 9 unlimited axes, EQ +10; Soul XP 1..800 equals v113, level 240 restored, 801+ continuous, 60000->60001, int64 guarded, character 800->801'

if __name__=='__main__':print(run())
