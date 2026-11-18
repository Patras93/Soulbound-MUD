# -*- coding: utf-8 -*-
"""Mercenary 6.1: actual class catalogue names and NPC-only combat execution.

This bridge never calls the owner's skill caster (a mercenary can have a different
class), never learns skills for the owner and never writes contracts/EXP/SQLite.
Only engaged enemies in the same room are eligible for additional AoE hits.
The attack stays inside the existing mercenary action budget and kill pipeline.
"""
from __future__ import annotations
import random

from data.mobs import MOB_TEMPLATES
from world.machine_expansion import v0314_adjust_damage_vs_template
from systems.v115.vampire_mercenary import MERCENARIES

ATTACK_KINDS = frozenset(('damage', 'aoe_damage', 'execute', 'drain'))
# Mec's control skills are NOT ordinary damage: don't pretend to cast Jammer,
# Hypno Flash or Logic Bomb unless their native status path is implemented.
MEC_CONTROL = frozenset(('hypno_flash', 'jammer', 'logic_bomb', 'compress'))


def _catalogue(role):
    """Read the live, canonical class catalogue; pure source fallback for audits."""
    from core.archetypes.runtime_catalogue import canonical_classes_skills
    name = MERCENARIES[role]['class']
    if role == 'wampir':
        # Eliza attacks with a real drain skill plus native Nekromanta spells.
        # The actual self/party drain is bounded by dealt damage in support.
        from core.archetypes.runtime_catalogue import canonical_classes_skills
        spells = tuple(canonical_classes_skills().CLASS_SKILLS.get(name, ()))
        touch = {'id': 'v115_eliza_dotyk_nocy', 'name': 'Dotyk Nocy',
                 'kind': 'drain', 'unlock': 1}
        return (touch,) + spells
    catalogue = canonical_classes_skills().CLASS_SKILLS.get(name)
    if catalogue:
        return tuple(catalogue)
    if role == 'magitek':
        from core.magitek.catalogue import skill_catalogue
        return tuple(skill_catalogue())
    from core.archetypes.chaos import CLASS_SPECS as C107, _skills as skills107
    for cname, mode, weapon, stat, passive, value, labels in C107:
        if cname == name:
            slug = cname.casefold().replace('ł','l').replace(' ','_')
            return tuple(skills107(cname, slug, stat, mode == 'magic', labels))
    from core.archetypes.expansion import CLASS_SPECS as C110, _skills as skills110
    for cname, mode, weapon, stat, passive, value, *labels in C110:
        if cname == name:
            slug = cname.casefold().translate(str.maketrans('ąćęłńóśźż','acelnoszz')).replace(' ','_')
            return tuple(skills110(cname, slug, stat, mode == 'magic', labels))
    return ()


def available_attacks(role, level):
    result = []
    for skill in _catalogue(role):
        if skill.get('kind') not in ATTACK_KINDS or int(skill.get('unlock', 1) or 1) > level:
            continue
        if role == 'mec' and skill.get('mec_special') in MEC_CONTROL:
            continue
        result.append(skill)
    # One source of truth, no duplicate aliases masquerading as new skills.
    return tuple(dict((x['id'], x) for x in result).values())


def pick_skill(session, role, level, now, boss=False):
    """Rotate genuine learned class attacks, prioritizing different tiers.

    Mec V-MAX is a separate transient mercenary buff, not the owner's buff.
    It unlocks from the actual Mec catalogue at 130. During this window
    Cosmic Rave makes exactly five random strikes across engaged enemies.
    """
    state = getattr(session, '_mercenary_class_ai_v11334', None)
    if not isinstance(state, dict):
        state = {}
        session._mercenary_class_ai_v11334 = state
    entry = state.setdefault(role, {'turn': 0, 'vmax_until': 0., 'vmax_next': 0.})
    turn = entry['turn']
    entry['turn'] += 1
    attacks = available_attacks(role, max(1, int(level)))
    if not attacks:
        return None, False, False
    vmax_started = False
    if role == 'mec':
        has_vmax = any(x.get('mec_special') == 'vmax' and
                       int(x.get('unlock', 99999)) <= level for x in _catalogue(role))
        if has_vmax and now >= entry['vmax_next']:
            entry['vmax_until'] = now + 25.0
            entry['vmax_next'] = now + 95.0
            vmax_started = True
        vmax_active = has_vmax and now < entry['vmax_until']
        cosmic = next((x for x in attacks if x.get('mec_special') == 'cosmic_rave'), None)
        if cosmic and vmax_active and (vmax_started or turn % 2 == 0):
            return cosmic, vmax_started, True
    else:
        vmax_active = False
    # Cycle through ALL genuine unlocked offensive class skills, not a hand-
    # selected subset. All 38 classes keep their own catalogues and level gates.
    # Boss encounters offset the current turn but never remove abilities.
    index = (turn + (3 if boss else 0)) % len(attacks)
    return attacks[index], vmax_started, vmax_active


def engaged_targets(session, primary):
    """Only enemies already engaged by this owner/party, in their current room."""
    character = getattr(session, 'character', None)
    if not character or not primary or not primary.alive or primary.room_id != character.room_id:
        return ()
    members = session.server.party_sessions(session.account_id, same_room=character.room_id) or [session]
    active_names = {p.character.name for p in members if getattr(p, 'character', None)}
    active_keys = {str(p.combat_mob_key) for p in members if getattr(p, 'combat_mob_key', None)}
    result = [primary]
    # Historical synthetic regression stubs have no World object. They still
    # exercise the single-target combat path with no extra AoE targets.
    room_mobs = getattr(getattr(getattr(session, 'server', None), 'world', None), 'room_mobs', None)
    if not callable(room_mobs):
        return (primary,)
    for target in room_mobs(character.room_id):
        if target is primary or not target.alive or target.room_id != character.room_id:
            continue
        if (str(target.key) in active_keys or
            getattr(target, 'engaged_by', None) in active_names or
            getattr(target, 'aoe_engaged_by', None) in active_names):
            result.append(target)
    return tuple(result)


async def execute_attack(session, primary, raw_power, skill, role, vmax_active):
    """Apply a single existing mercenary action using source attack targeting.

    Returns (total_damage, primary_damage, slain_mobs, hit_count). Does not send
    output or grant EXP, letting the existing mob_defeated pipeline do so once.
    """
    if not primary or not getattr(session, 'character', None):
        return 0, 0, (), 0
    same_room = session.character.room_id
    possible = engaged_targets(session, primary)
    if not possible:
        return 0, 0, (), 0
    cosmic = role == 'mec' and skill.get('mec_special') == 'cosmic_rave'
    is_aoe = skill.get('kind') == 'aoe_damage' or cosmic
    targets = possible if is_aoe else (primary,)
    five = cosmic and vmax_active
    count = 5 if five else len(targets)
    # Multihit distributes a single action budget; V-MAX adds a modest bonus.
    budget = max(1, int(raw_power * (1.25 if five else (1.0 if len(targets)==1 else 1.10))))
    total = 0
    primary_damage = 0
    hit_count = 0
    defeated = []
    for idx in range(count):
        active = [x for x in targets if x.alive and x.hp > 0 and
                  x.room_id == same_room and session.character.room_id == same_room]
        if not active:
            break
        if five:
            target = random.choice(active)
        else:
            target = targets[idx]
            if target not in active:
                continue
        # Equal total action budget; remaining HP is the only per-target cap.
        amount = max(1, budget // count + (1 if idx < budget % count else 0))
        amount = await session.apply_boss_defense(target, amount)
        if session.character.room_id != same_room or target.room_id != same_room or not target.alive:
            break
        tier = getattr(session, 'v0210_adjust_player_damage', None)
        if callable(tier):
            amount = tier(amount)
        template = MOB_TEMPLATES.get(target.template_id, {})
        damage_type = 'magic' if MERCENARIES[role]['attack_type'] == 'magic' else 'physical'
        amount, _ = v0314_adjust_damage_vs_template(template, amount, damage_type, MERCENARIES[role]['role'])
        actual = min(max(0, target.hp), max(1, int(amount)))
        target.hp -= actual
        total += actual
        hit_count += 1
        if target is primary:
            primary_damage += actual
        if target.hp <= 0 and target not in defeated:
            defeated.append(target)
    return total, primary_damage, tuple(defeated), hit_count
