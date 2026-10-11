# -*- coding: utf-8 -*-
"""Combat-local, bounded tactics for explicitly opted-in enemies.

Special and authored boss mechanics retain absolute priority. Never scan the
world here: live allies come from the caller's existing room-local filter.
"""
from __future__ import annotations

ROLES = frozenset(('obronca', 'dowodca', 'uzdrowiciel', 'mag', 'lowca', 'wojownik', 'nekromanta'))


def role(template):
    """Keep authored roles, derive safe roles for ordinary world encounters.

    No template mutation. Protected boss mechanics are excluded in monster_ai,
    before role selection. Explicit roles always win.
    """
    value = str(template.get('tactical_role_v2200') or '').casefold()
    if value in ROLES:
        return value
    if template.get('training_dummy') or template.get('boss') or template.get('world_boss'):
        return ''
    text = (' '.join(str(template.get(k) or '') for k in ('name', 'creature_type', 'elite_affix'))).casefold()
    # Healers and commanders first; do not give every wolf magical healing.
    groups = (
        ('uzdrowiciel', ('uzdrow', 'kaplan', 'kapłan', 'healer', 'medyk', 'druid', 'szaman')),
        ('dowodca', ('dowódc', 'dowodc', 'herszt', 'kapitan', 'komendant', 'wódz', 'wodz')),
        ('nekromanta', ('nekroman', 'licz', 'lich', 'wskrzesz')),
        ('obronca', ('strażnik', 'straznik', 'obrońc', 'obronc', 'gwardzist', 'tarczownik')),
        ('mag', ('mag ', ' czarodziej', 'czarnoksięż', 'czarnoksiez', 'zaklinacz')),
        ('lowca', ('łowca', 'lowca', 'łucznik', 'lucznik', 'strzelec')),
    )
    for kind, words in groups:
        if any(word in text for word in words):
            return kind
    return 'mag' if template.get('damage_type') == 'magic' else ''


def select_support(mob, template, live_allies, now, hp_cap):
    """Return existing AI support actions; no special cooldown bypass."""
    kind = role(template)
    if not kind:
        return None
    ready = [m for m in live_allies if m.alive and m.room_id == mob.room_id
             and m.engaged_by == mob.engaged_by and not getattr(m, 'monster_ai_summoned_v1160', False)]
    if kind == 'uzdrowiciel':
        injured = [a for a in ([mob] + ready) if a.alive and a.hp * 100 < hp_cap(a) * 65]
        if injured:
            target = min(injured, key=lambda a: (a.hp / hp_cap(a), str(a.key)))
            return {'kind': 'heal', 'target': target}
    if kind == 'obronca':
        endangered = [a for a in ready if a.key != mob.key and a.hp * 100 < hp_cap(a) * 75
                      and now >= float(getattr(a, 'monster_ai_guard_until_v1160', 0) or 0)]
        if endangered:
            return {'kind': 'guard', 'target': min(endangered, key=lambda a:a.hp / hp_cap(a))}
    if kind == 'dowodca' and len(ready) >= 2:
        if now >= float(getattr(mob, 'monster_ai_empowered_until_v1160', 0) or 0):
            return {'kind': 'buff', 'target': mob}
    return None
