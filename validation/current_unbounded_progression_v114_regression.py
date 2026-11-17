# -*- coding: utf-8 -*-
"""Non-deployable WIP: minimal runtime checks for v114 progression policy."""

def run():
    # Match production: construct the authored native modules BEFORE applying
    # the static deploy policy, preventing unbounded catalogue construction.
    from player.character import Character
    from core.progression_policy_v114 import install_deploy_policy
    from core.live_level_caps_v5200 import cap
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
    # The 60000 boundary must remain playable. The historical fallback
    # silently hit 9e18 XP, which was practically impossible to earn.
    from systems.soul_xp_curve_v10600 import requirement as _old_soul
    from config.balance import SOUL_XP_REQUIREMENT_MULTIPLIER as _soul_mul
    from systems.soul_xp_unbounded_v114 import requirement as _new_soul
    from systems.soul_xp_early_v10600 import requirement as _soul_early
    from systems.soul_xp_bridge_v10600 import requirement as _soul_bridge
    assert soul_xp_to_next(1)==_soul_early(1,_soul_mul)
    assert soul_xp_to_next(799)==_soul_early(799,_soul_mul)
    assert soul_xp_to_next(800)==_soul_bridge(800,_soul_mul)
    assert soul_xp_to_next(29_999)==_soul_bridge(29_999,_soul_mul)
    assert soul_xp_to_next(30_000)==_old_soul(30_000,_soul_mul)
    assert soul_xp_to_next(59_999)==_old_soul(59_999,_soul_mul)
    assert soul_xp_to_next(60_000)==_new_soul(60_000,_soul_mul)
    assert 0 < soul_xp_to_next(800)-soul_xp_to_next(799) < 100_000
    assert soul_xp_to_next(60_000)-_old_soul(59_999,_soul_mul)==int(round(2000*_soul_mul))
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
    return 'PASS: all 9 unlimited, +10 EQ, 5 XP curves >=801, Soul XP 1->60000 continuous, Soul 60000->60001, int64 guarded, level 800->801, edit locked'

if __name__=='__main__':print(run())
