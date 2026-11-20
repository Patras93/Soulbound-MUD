# -*- coding: utf-8 -*-
"""v116.00.4: small encounter-local monster reactions (no new aggro or DB).

Only monsters *already engaged with the same opponent* receive a death signal.
Boss scripts, adds, corpses and passive occupants are never enlisted.
"""
from __future__ import annotations

import time

from systems.tactical_ai_v2200 import role

REACTION_WINDOW = 24.0
REACTION_COOLDOWN = 45.0


def _protected(template):
    # Existing authored boss and special encounter scripts always take priority.
    from systems.monster_ai import PROTECTED_FLAGS
    return bool(template.get('boss') or any(template.get(flag) for flag in PROTECTED_FLAGS))


def notice_ally_defeat(world, defeated, *, now=None):
    """Signal combat allies after a *real* kill, without touching engagement."""
    if not defeated or getattr(defeated, 'monster_ai_summoned_v1160', False):
        return 0
    owner = getattr(defeated, 'engaged_by', None)
    if not owner or getattr(defeated, 'monster_reaction_notified_v1164', False):
        return 0
    defeated.monster_reaction_notified_v1164 = True
    now = time.monotonic() if now is None else float(now)
    count = 0
    # room_mobs is the already available room-local alive index (not a world scan).
    for ally in world.room_mobs(defeated.room_id):
        if ally.key == defeated.key or not ally.alive or ally.engaged_by != owner:
            continue
        if getattr(ally, 'monster_ai_summoned_v1160', False):
            continue
        template = world.mob_templates_for_ai_v1160(ally)
        if _protected(template) or now < float(getattr(ally, 'monster_reaction_next_v1164', 0) or 0):
            continue
        if has_reaction(ally, now=now):
            continue
        # Expired or invalid notifications cannot block later real deaths.
        ally.monster_reaction_pending_v1164 = None
        kind = 'rage' if (role(template) in ('dowodca','wojownik') or template.get('elite_affix')) else 'fear'
        ally.monster_reaction_pending_v1164 = (kind, str(owner), now + REACTION_WINDOW)
        count += 1
    return count


def has_reaction(mob, *, now=None):
    now = time.monotonic() if now is None else float(now)
    pending = getattr(mob, 'monster_reaction_pending_v1164', None)
    return bool(pending and mob.alive and mob.engaged_by == pending[1] and now < pending[2])


def choose_reaction(mob, template, live_allies, now):
    """Prefer protecting an *injured, already-engaged* boss; else react once."""
    if _protected(template) or getattr(mob, 'monster_ai_summoned_v1160', False):
        return None
    if role(template) == 'obronca':
        from data.mobs import MOB_TEMPLATES
        for boss in live_allies:
            if boss.key == mob.key or not boss.alive or boss.room_id != mob.room_id or boss.engaged_by != mob.engaged_by:
                continue
            boss_template = MOB_TEMPLATES.get(boss.template_id, {})
            if not boss_template.get('boss') or boss_template.get('uoss_superboss') or boss_template.get('boss_mechanic'):
                continue
            hp_cap = max(1, int(getattr(boss, 'adaptive_max_hp_v11330', 0) or boss_template.get('max_hp', 1)))
            if boss.hp * 100 <= hp_cap * 65 and now >= float(getattr(boss,'monster_ai_guard_until_v1160',0) or 0):
                return {'kind':'guard', 'target':boss}
    if has_reaction(mob, now=now):
        kind, _, _ = mob.monster_reaction_pending_v1164
        return {'kind':kind, 'target':mob}
    return None


def perform_reaction(mob, template, plan, now):
    kind = plan.get('kind') if plan else None
    if kind not in ('fear','rage') or not has_reaction(mob, now=now):
        return ''
    if plan.get('target') is not mob or mob.monster_reaction_pending_v1164[0] != kind:
        return ''
    mob.monster_reaction_pending_v1164 = None
    mob.monster_reaction_next_v1164 = now + REACTION_COOLDOWN
    mob.monster_ai_next_action_v1160 = now + 14.0
    name = str(template.get('name') or mob.template_id)
    if kind == 'rage':
        # Reuse the existing +18%/10-second empowered state; no stacking.
        mob.monster_ai_empowered_until_v1160 = max(float(getattr(mob,'monster_ai_empowered_until_v1160',0) or 0), now + 10.0)
        return f'{name} wpada w szał po śmierci sojusznika!'
    # Fear costs a single normal action. Mob remains in its current fight.
    return f'{name} waha się ze strachu po śmierci sojusznika!'
