# -*- coding: utf-8 -*-
"""Shared source attack primitives: production realtime and detached admin arena.

Keep the critical roll and speed hit series in ONE implementation. Other
realtime layers (queue, AI, support, effects, loot, EXP) are not replayed.
"""
import random
from core.progression_resources import soul_weapon_mastery_bonuses
from core.progression_600 import soul_weapon_trait_totals_v11193
from systems.soul_ancients_v1330 import weapon_resonance_percent

BOSS_FLAGS=("world_boss", "mini_boss", "crypt_boss", "astral_boss",
            "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss")

def weapon_attack_boost(actor, mob, template, damage, *, zantetsuken=False):
    """Production attack modifiers that precede defense, including critical.

    Returns (damage, crit, crit_chance, traits, mastery); no DB writes.
    """
    mastery=soul_weapon_mastery_bonuses(actor.character.soul_weapon_mastery_level)
    damage=max(0,int(round(damage*(1.0+(mastery["damage_percent"]+
                 weapon_resonance_percent(actor.character.soul_weapon_mastery_level))/100.0))))
    traits=soul_weapon_trait_totals_v11193(actor.character.soul_tier,actor.character.class_name)
    damage=max(0,int(round(damage*(1.0+traits["damage_percent"]/100.0))))
    if mob.hp <= max(1,int(round(actor.mob_effective_max_hp_v11330(mob,template)*0.35))):
        damage=max(0,int(round(damage*(1.0+traits["execute_damage_percent"]/100.0))))
    if any(template.get(flag) for flag in BOSS_FLAGS):
        bonus=float(traits["boss_damage_percent"])+float(mastery["boss_damage_percent"])
        if bonus>0 and not zantetsuken:
            damage=max(1,int(round(damage*(1.0+bonus/100.0))))
    chance=min(0.60,actor.critical_chance()+traits["crit_chance"]+mastery["crit_chance"])
    crit=random.random()<chance
    if crit:
        multiplier=actor.critical_multiplier()*(1.0+(traits["crit_damage_percent"]+
                      mastery["crit_damage_percent"])/100.0)
        damage=max(0,int(round(damage*multiplier)))
    return damage,crit,chance,traits,mastery


def apply_weapon_hit_series(mob,damage,hit_count):
    """Source realtime loop: stop immediately on death; defense was once."""
    if type(hit_count) is not int or hit_count<1:
        raise ValueError('Nieprawidlowa liczba trafien Broni Duszy.')
    per_hit=max(0,int(damage)); actual=0; total=0
    for _ in range(hit_count):
        if mob.hp<=0:break
        mob.hp-=per_hit
        total+=per_hit
        actual+=1
    return total,actual,per_hit


def weapon_after_hit(actor, mob, damage, traits, mastery, *, disabled=False):
    """Shared production Soul Weapon Echo + lifesteal + MP restore.

    Mutates ONLY the actor and mob objects supplied by the caller. The LAB
    passes detached copies. The production caller passes its real combat pair.
    Damage is the total from the main weapon hit series before Echo; as in
    source v80, lifesteal and MP regeneration never include Echo damage.
    """
    from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
    import random

    echo=0
    if not disabled and mob.hp>0 and mastery['echo_chance']>0 and random.random()<mastery['echo_chance']:
        echo=max(1,int(round(damage*mastery['echo_damage_percent']/100.0)))
        mob.hp-=echo
        actor._recap52_dealt=int(getattr(actor,'_recap52_dealt',0) or 0)+echo

    props=actor.equipment_property_totals() if callable(getattr(actor,'equipment_property_totals',None)) else {}
    life=float(traits.get('lifesteal_percent',0.0) or 0.0)+min(8.0,float(props.get('lifesteal_percent',0.0) or 0.0))
    maxhp=actor.max_hp() if callable(getattr(actor,'max_hp',None)) else 0
    hp=int(getattr(actor,'current_hp',0) or 0)
    heal=0
    if life>0 and hp<maxhp and not superboss_healing_blocked_v11179(actor):
        heal=min(maxhp-hp,max(1,int(round(damage*life/100.0))))
        if heal>0:
            actor.current_hp+=heal
            actor._recap52_heal=int(getattr(actor,'_recap52_heal',0) or 0)+heal

    mp_pct=float(traits.get('mana_restore_percent',0.0) or 0.0)+min(6.0,float(props.get('mana_restore_percent',0.0) or 0.0))
    maxmp=actor.max_mana() if callable(getattr(actor,'max_mana',None)) else 0
    mana=int(getattr(actor,'current_mana',0) or 0)
    mp=0
    if mp_pct>0 and mana<maxmp:
        mp=min(maxmp-mana,max(1,int(round(damage*mp_pct/100.0))))
        if mp>0:actor.current_mana+=mp
    return echo,heal,mp
