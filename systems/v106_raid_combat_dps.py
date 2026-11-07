# -*- coding: utf-8 -*-
"""v106 staging: true Soul Weapon expectation for 26–35 raid HP scaling.

Only read-only combat projection. It does NOT roll a critical, consume mana,
activate Impulse, mutate gear, award XP, or touch a live player's database.
The historical v105 estimator remains the only one outside v106 raids.
"""
from __future__ import annotations

from functools import lru_cache
import math
import os


def is_v106_raid_boss(mob, template, room=None):
    if os.getenv('SOULBOUND_V106_STAGING') != '1':
        return False
    ident = str(getattr(mob, 'template_id', '') or '').split('__', 1)[0]
    room_id = str(getattr(mob, 'room_id', '') or '')
    if not (ident.startswith('v10600_raid_') and '_boss_' in ident
            and room_id == ident.replace('_boss_', '_stage_')):
        return False
    if not isinstance(template, dict) or not isinstance(room, dict):
        return False
    try:
        return (not template.get('training_dummy')
                and not room.get('training_dummy')
                and int(room.get('generator_level') or 0) >= 30001
                and int(template.get('v106_authored_boss_stage') or 0) >= 30001)
    except (TypeError, ValueError, OverflowError):
        return False


@lru_cache(maxsize=512)
def _weapon_traits(tier, class_name):
    from core.progression_600 import soul_weapon_trait_totals_v11193
    return soul_weapon_trait_totals_v11193(tier, class_name)


def raid_autoattack_dps_v106(actor, template):
    """Expected *ordinary* weapon DPS, including 1000 Soul Tier traits.

    The old estimator counted regular criticals but omitted weapon traits.
    At tier 3400 this missed +720% damage and +1800% critical damage;
    a 12-hit real weapon round could therefore exceed the whole raid HP.
    """
    c = actor.character
    if c is None:
        raise ValueError('Brak postaci w prognozie rajdu.')
    base_expected = float(actor.consider_player_expected_hit())
    base_chance = float(actor.critical_chance())
    base_crit = float(actor.critical_multiplier())
    # The legacy preview ALREADY includes regular critical probability.
    base_factor = max(1.0, 1.0 + base_chance * (base_crit - 1.0))
    precrit = max(1.0, base_expected) / base_factor

    from core.progression_resources import soul_weapon_mastery_bonuses
    from systems.soul_ancients_v1330 import weapon_resonance_percent
    from systems.soul_weapon_elements_v10500 import weapon_multiplier
    from systems.soul_weapon_astral_v10600 import secondary_damage_multiplier
    from systems.uoss_basic_weapon_shared_v8000 import BOSS_FLAGS
    mastery = soul_weapon_mastery_bonuses(c.soul_weapon_mastery_level)
    traits = _weapon_traits(int(c.soul_tier), c.class_name)
    factor = (1.0 + (mastery['damage_percent'] +
              weapon_resonance_percent(c.soul_weapon_mastery_level)) / 100.0)
    factor *= (1.0 + traits['damage_percent'] / 100.0)
    if any(template.get(flag) for flag in BOSS_FLAGS):
        factor *= (1.0 + (traits['boss_damage_percent'] +
                   mastery['boss_damage_percent']) / 100.0)
    factor *= weapon_multiplier(actor, template)
    factor *= secondary_damage_multiplier(actor, template)
    # Only passive effects: an armed Impulse is a ONE-TIME buff, not sustained DPS.
    chance = min(0.60, base_chance + traits['crit_chance'] + mastery['crit_chance'])
    crit = base_crit * (1.0 + (traits['crit_damage_percent'] +
                              mastery['crit_damage_percent']) / 100.0)
    expected_crit = 1.0 + chance * (crit - 1.0)
    # Match live post-hit path; do not predict transient execute/guard/status.
    factor *= max(1.0, float(actor.class_damage_multiplier_v1700()))
    world_tier = actor.v0210_world_tier_multipliers()
    factor /= max(1.0, float(world_tier['effective_hp']))
    hit_count = max(1, int(actor.basic_attack_hit_count_v11196()))
    interval = max(0.35, float(actor.player_action_interval_v11154()))
    # Weryfikacja TCP: podczas prawdziwej serii 6 postaci w pierwszych 20 s
    # serwer oddawal ok. 10–12 mld/s zamiast prognozowanych ~28 mld/s.
    # Teoretyczny hit/s nie uwzglednial kosztow tury, mieszanego składu,
    # unikow i rzeczywistego czasu miedzy kolejkami. Wspolczynnik
    # dlugotrwalej aktywnosci dotyczy WYŁĄCZNIE wyliczania HP rajdów v106;
    # nie modyfikuje zadnego realnego ciosu ani nagrody.
    real_turn_uptime = 0.45
    result = precrit * factor * expected_crit * hit_count / interval * real_turn_uptime
    if not math.isfinite(result) or result <= 0:
        raise ValueError('Nieskończony DPS Broni Duszy; nie wolno zaniżać HP.')
    return result


def raid_party_dps_v106(members, template):
    return sum(raid_autoattack_dps_v106(m, template) for m in members)


def _raid_party_signature_v106(members):
    """Cheap invalidation for changed party/character build; no DB reads.

    Short TTL also covers temporary buffs, consumables, class effects and
    equipment fields not represented in the compact signature.
    """
    result=[]
    for member in members:
        c=member.character
        result.append((id(member),id(c),getattr(member,'account_id',None),
            getattr(member,'current_hp',0)>0,getattr(member,'current_mana',0)>=4,
            getattr(c,'room_id',None),getattr(c,'class_name',None),
            getattr(c,'character_level',None),getattr(c,'soul_level',None),
            getattr(c,'soul_tier',None),getattr(c,'soul_weapon_mastery_level',None),
            getattr(c,'soul_weapon',None),
            *(getattr(c,stat,None) for stat in (
                'strength','dexterity','constitution','intelligence','willpower','charisma'))))
    return tuple(result)


def raid_party_dps_cached_v106(mob, members, template, *, now=None):
    """Reuse one stage-only raid projection across same boss/party frame.

    Recalculations must never be shared between bosses or separate fights.
    Whenever membership/major stats change invalidate immediately; any
    remaining transient bonus is captured on a short .75-second expiry.
    On expiry a fresh projection is calculated before applying boss scale.
    """
    import time
    if os.getenv('SOULBOUND_V106_STAGING') != '1':
        raise RuntimeError('Cache DPS rajdu wyłącznie w v106 staging.')
    override_now = now is not None
    if now is None:
        now=time.monotonic()
    signature=_raid_party_signature_v106(members)
    snapshot=getattr(mob,'_v106_party_dps_cache',None)
    if (snapshot is not None and snapshot[1] == signature
            and 0 <= now-snapshot[0] < .75):
        return snapshot[2]
    dps=raid_party_dps_v106(members,template)
    mob._v106_party_dps_cache=(now if override_now else time.monotonic(),
                                signature,dps)
    return dps
