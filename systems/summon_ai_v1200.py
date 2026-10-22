# -*- coding: utf-8 -*-
"""v12.00.0: local, deterministic, class-specific summoned companion AI.

No external model, subscriptions, global mob scans or additional XP curves.
All orders remain under their owners; autonomous AI makes bounded decisions
about existing enemy, same-room allies, heals, guarding and tactical skills.
"""
from __future__ import annotations

# Identity is the existing owning class, not the creature's name. Existing
# 95 class summon keys and all legacy Mage/Druid/Necromancer keys are retained.
# profile: signature ability, operational specialty, offensive momentum
CLASS_AI = {
 'Wojownik':('Szyk żelaznego legionu','guard',.06),
 'Berserker':('Ryk krwawej furii','execute',.12),
 'Łotrzyk':('Atak w słaby punkt','mark',.10),
 'Łowca':('Oznaczenie zwierzyny','mark',.08),
 'Mnich':('Osłona harmonii Ki','guard',.05),
 'Strażnik':('Bastion ochronny','guard',.04),
 'Kapłan':('Łaska uzdrowienia','heal',.04),
 'Czarownik':('Klątwa otchłani','curse',.09),
 'Psionik':('Przeciążenie umysłu','slow',.08),
 'Mec':('Skanowanie celu','mark',.08),
 'Inżynier':('Kalibracja ostrzału','mark',.08),
 'Paladyn':('Święta zasłona','guard',.06),
 'Samuraj':('Riposta bushidō','execute',.10),
 'Korsarz':('Ostrzał oskrzydlający','mark',.09),
 'Gladiator':('Natarcie areny','execute',.09),
 'Chronomanta':('Spowolnienie eonów','slow',.07),
 'Iluzjonista':('Złudzenie rozproszenia','slow',.07),
 'Bard':('Pieśń odnowy','heal',.05),
 'Szaman':('Błogosławieństwo przodków','heal',.05),
 'Druid':('Oddech pradawnego gaju','heal',.05),
 'Mag':('Synergia żywiołów','mark',.09),
 'Nekromanta':('Klątwa umarłych','curse',.08),
}
assert len(CLASS_AI) == 22


def paralysis_token(mob):
    """Only an active Logic Bomb paralysis qualifies for Mec Jammer.

    A new successful Logic Bomb receives a fresh token, and Jammer never
    fires twice on that same paralysis even if the stop effect runs out.
    """
    rounds = max(0, int(getattr(mob, 'v11196_logic_bomb_rounds', 0) or 0))
    effects = getattr(mob, 'v11196_logic_bomb_effects', set()) or set()
    if rounds <= 0 or 'paralyze' not in effects:
        return None
    return max(0, int(getattr(mob, 'v1200_logic_paralyze_token', 0) or 0))


def jammer_eligible(mob, template):
    if not mob or not getattr(mob, 'alive', False):
        return False
    from systems.boss_companions_v1281 import boss_jammer_immune_v1281
    if boss_jammer_immune_v1281(template):
        return False
    token = paralysis_token(mob)
    if token is None or max(0,int(getattr(mob,'v11196_jammer_stop_rounds',0) or 0)):
        return False
    return getattr(mob, 'v1200_jammer_attempted_token', None) != token


def plan_for_class(class_name, *, owner_hp, owner_max, ally_needs_heal=False,
                   guarded=False, enemy_hp=1, enemy_max=1, boss=False,
                   marked=False, controlled=False, step=0):
    """Pure decision: no resources spent, no cooldown when effect isn't useful.

    Caller decides which actual ally has lowest HP. Status effects only apply
    to ordinary non-immune mobs, and only while missing. Other classes choose
    an offensive strike instead of wasting the turn on redundant support.
    """
    name,role,bonus = CLASS_AI[class_name]
    from systems.live_olc23_state import SUMMON_TACTICS
    tactics = SUMMON_TACTICS.get(class_name, {})
    guard_threshold = tactics.get('guard_threshold_percent',80)/100.0
    execute_threshold = tactics.get('execute_threshold_percent',35)/100.0
    tactic_interval = tactics.get('tactic_interval',3)
    ratio=max(0.0,min(1.0,float(owner_hp)/max(1.0,float(owner_max))))
    eratio=max(0.0,min(1.0,float(enemy_hp)/max(1.0,float(enemy_max))))
    ready=(int(step)%tactic_interval==0)
    if role == 'heal' and ally_needs_heal:
        return {'ability':name,'action':'heal','bonus':bonus}
    if role == 'guard' and ratio < guard_threshold and not guarded:
        return {'ability':name,'action':'guard','bonus':bonus}
    if role == 'mark' and not marked and ready:
        return {'ability':name,'action':'mark','bonus':bonus}
    if role in ('curse','slow') and not boss and not controlled and ready:
        return {'ability':name,'action':role,'bonus':bonus}
    if role == 'execute' and eratio <= execute_threshold:
        return {'ability':name,'action':'execute','bonus':bonus}
    return {'ability':name,'action':'strike','bonus':bonus*.30}


def profession_amulet_bonus(db, account_id):
    """A single optional masterwork provides a small additive tactical bonus.

    Items are not spent by combat; no requirement to craft them to summon.
    No stacking over 22 professions, DB query bounded by 22 IDs.
    """
    from systems.profession_projects_v1200 import PROJECTS, project_item_id
    ids=tuple(project_item_id(profession) for profession in PROJECTS)
    # Masterworks are craft materials: normal add_item() puts them in the
    # craftbox, not necessarily in the inventory table. Reuse the canonical
    # storage accessor: it checks both places in two bounded SQLite reads.
    # Lightweight legacy combat-test databases only implement item_qty and
    # storage_qty and intentionally do not have an inventory SQL table.
    total=getattr(db,'total_items_across_storage_and_inventory',None)
    if callable(total):
        return .04 if total(account_id,ids,container='craftbox')>0 else 0.0
    item_qty=getattr(db,'item_qty',None)
    storage_qty=getattr(db,'storage_qty',None)
    if not callable(item_qty) and not callable(storage_qty):
        return 0.0
    for item_id in ids:
        if callable(item_qty) and item_qty(account_id,item_id)>0:
            return .04
        if callable(storage_qty) and storage_qty(account_id,'craftbox',item_id)>0:
            return .04
    return 0.0
