# -*- coding: utf-8 -*-
"""OLC 16: genuine on-hit skill effects using the existing summon-status turn engine.

No new damage formula, no dynamic Python, no mutation until an authenticated OLC
revision is published. Effects are runtime-only and share summon cooldowns.
"""
import json
import math
import random
import time

KINDS = frozenset(('poison','burn','freeze','shock'))
CONTROL = frozenset(('freeze','shock'))
# Defaults come from the existing living summon status family.
DEFAULT_CHANCES = {'poison': .32, 'burn': .26, 'freeze': .22, 'shock': .20}
DURATIONS = {'poison': (12.0, 3), 'burn': (9.0, 3),
             'freeze': (6.0, 0), 'shock': (5.0, 0)}


def parse_status(raw):
    if isinstance(raw, str):
        if raw.casefold().strip() in ('auto','automatyczny','-'):
            return None
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError('Status: wymagany JSON {"kind":"poison","chance":0.32}.') from exc
    if not isinstance(raw, dict) or not {'kind','chance'} <= set(raw) or not set(raw) <= {'kind','chance','power_percent','ticks'}:
        raise ValueError('Status: kind i chance; opcjonalnie power_percent oraz ticks dla obrażeń okresowych.')
    kind = raw.get('kind')
    chance = raw.get('chance')
    if kind not in KINDS or type(chance) not in (float,int) or not math.isfinite(chance) or not 0.01 <= chance <= 1.0:
        raise ValueError('Status: poison/burn/freeze/shock; chance od 0.01 do 1.00.')
    result = {'kind': kind, 'chance': float(chance)}
    if 'power_percent' in raw or 'ticks' in raw:
        if kind not in ('poison', 'burn'):
            raise ValueError('power_percent i ticks dotyczą tylko trucizny lub podpalenia.')
    if 'power_percent' in raw:
        amount = raw['power_percent']
        if type(amount) is not int or not 1 <= amount <= 200:
            raise ValueError('power_percent: całkowita wartość 1–200 procent trafienia.')
        result['power_percent'] = amount
    if 'ticks' in raw:
        ticks = raw['ticks']
        if type(ticks) is not int or not 1 <= ticks <= 5:
            raise ValueError('ticks: od 1 do 5 impulsów obrażeń.')
        result['ticks'] = ticks
    return result


def parse_statuses(raw):
    """Up to two safe, distinct on-hit statuses using the existing turn engine.

    The existing engine holds at most two statuses and one control effect per
    control cooldown. Restrict the authored combination to those same limits.
    """
    if isinstance(raw, str):
        if raw.strip().casefold() in ('auto', 'automatyczny', '-'):
            return None
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError('Efekty: wymagana lista JSON maksymalnie 2 statusow.') from exc
    if not isinstance(raw, list) or not 1 <= len(raw) <= 2:
        raise ValueError('Efekty: lista 1 lub 2 statusow.')
    parsed = [parse_status(entry) for entry in raw]
    if any(entry is None for entry in parsed):
        raise ValueError('Efekty: auto dozwolone tylko dla calego pola.')
    kinds = [entry['kind'] for entry in parsed]
    if len(set(kinds)) != len(kinds):
        raise ValueError('Efekty: nie powtarzaj tego samego statusu.')
    if len(CONTROL.intersection(kinds)) > 1:
        raise ValueError('Efekty: tylko jedno zamrozenie lub porazenie.')
    return parsed


def skill_effect_bundle(skill):
    """Return safe runtime effect set, maintaining backwards compatibility."""
    if skill.get('olc_statuses') is not None:
        return parse_statuses(skill['olc_statuses'])
    old = skill.get('olc_status')
    return [parse_status(old)] if old is not None else []


def apply_skill_effects_v9300(mob, statuses, hit_damage, template=None, now=None, rolls=None):
    """Apply existing effects to one mob. No instant damage or DB writes."""
    statuses = parse_statuses(statuses)
    if not statuses:
        return ()
    messages = []
    for index, status in enumerate(statuses):
        roll = None if rolls is None else rolls[index]
        message = apply_skill_status_v1900(mob, status, hit_damage,
                                          template=template, now=now, roll=roll)
        if message:
            messages.append(message)
    return tuple(messages)


def apply_skill_status_v1900(mob, status, hit_damage, template=None, now=None, roll=None):
    """Attach status to the canonical runtime pool, without another instant hit.

    Enemy turns (including normal defeat credit) remain owned by
    summon_status_enemy_turn_v1808. Reapplications cannot extend stun or DOT.
    """
    status = parse_status(status)
    if status is None or mob is None or not getattr(mob, 'alive', False) or int(getattr(mob,'hp',0)) <= 0 or int(hit_damage) <= 0:
        return ''
    now = time.monotonic() if now is None else float(now)
    template = template or {}
    kind, chance = status['kind'], status['chance']
    boss = bool(template.get('boss') or template.get('world_boss') or
                template.get('uoss_superboss') or template.get('v1800_chaos_boss'))
    if boss:
        chance *= .45 if kind in CONTROL else .70
    statuses = getattr(mob, 'v1808_summon_statuses', None)
    if not isinstance(statuses, dict):
        statuses = {}
        mob.v1808_summon_statuses = statuses
    cooldowns = getattr(mob, 'v1808_summon_cooldowns', None)
    if not isinstance(cooldowns, dict):
        cooldowns = {}
        mob.v1808_summon_cooldowns = cooldowns
    for old_kind, previous in tuple(statuses.items()):
        if now >= float(previous['until']):
            del statuses[old_kind]
    if (kind in statuses or len(statuses) >= 2 or now < float(cooldowns.get(kind,0)) or
            (kind in CONTROL and now < float(cooldowns.get('control',0)))):
        return ''
    if (random.random() if roll is None else float(roll)) >= chance:
        return ''
    duration, ticks = DURATIONS[kind]
    # No global player-damage ceiling: periodic damage scales with the actual
    # strike, using integer math even at enormous Soulbound progression levels.
    # The engine only clips the final tick to the target's remaining HP.
    numerator = status.get('power_percent', 7 if kind == 'poison' else 5)
    power = max(1, (int(hit_damage) * numerator) // 100)
    if kind in ('poison', 'burn') and 'ticks' in status:
        ticks = status['ticks']
        # The existing engine ticks only on a mob action, at most every 3 s.
        # Keep the historical duration when ticks are not configured.
        duration = max(duration, 3.0 * (ticks + 2))
    statuses[kind] = {'until': now+duration, 'next_tick': now+3.0,
                      'ticks_left': ticks, 'power': power,
                      'skip_left': 1 if kind in CONTROL else 0,
                      'source':'OLC skill'}
    cooldowns[kind] = now+duration+(16.0 if boss else 9.0)
    if kind in CONTROL:
        cooldowns['control'] = now+(24.0 if boss else 14.0)
    name = {'poison':'trucizna','burn':'podpalenie','freeze':'zamrożenie','shock':'porażenie'}[kind]
    return f'Umiejętność nakłada efekt: {name}.'


async def cast_with_olc_status_v1900(self, raw, baseline, templates=None):
    """Narrow runtime adapter around the original untouched combat method.

    Count only actual HP decreases by the current cast. No event is fired for
    `look`, failed casts, no mana, already-dead mobs or stale movement.
    """
    skill, _target = self.find_skill_from_input(raw)
    config = skill_effect_bundle(skill) if isinstance(skill,dict) else []
    if not config or skill.get('kind') not in ('damage','aoe_damage'):
        return await baseline(self,raw)
    room_id = getattr(getattr(self,'character',None),'room_id',None)
    if room_id is None:
        return await baseline(self,raw)
    before = {m.key:(m,int(m.hp)) for m in self.server.world.room_mobs(room_id)
              if getattr(m,'alive',False) and int(getattr(m,'hp',0))>0}
    dealt_before = int(getattr(self,'_recap52_dealt',0) or 0)
    result = await baseline(self,raw)
    # Standard AoE does not update _recap52_dealt in the historic engine.
    # Its per-target HP changes are the source of truth instead.
    if skill['kind'] == 'damage' and int(getattr(self,'_recap52_dealt',0) or 0) <= dealt_before:
        return result
    # A targeted skill must not poison a different mob hit concurrently.
    current_target = getattr(self,'combat_mob_key',None)
    if templates is None:
        from data.mobs import MOB_TEMPLATES as templates
    for key,(mob,old_hp) in before.items():
        if skill['kind'] == 'damage' and key != current_target:
            continue
        if not getattr(mob,'alive',False) or mob.room_id != room_id:
            continue
        actual = old_hp-int(getattr(mob,'hp',0) or 0)
        if actual <= 0 or int(getattr(mob,'hp',0)) <= 0:
            continue
        for message in apply_skill_effects_v9300(mob,config,actual,
                                                   templates.get(mob.template_id)):
            await self.server.party_combat_broadcast(self,
                f'{skill["name"]}: {message}',detail='normal')
    return result
