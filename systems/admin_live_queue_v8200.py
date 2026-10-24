# -*- coding: utf-8 -*-
"""V82 read-only rehearsal of the *real* automatic skill queue choice.

This does not cast skills. Casting may mutate DB/other player sessions/world,
so this module refuses to invoke use_class_skill in the private arena.
"""
from __future__ import annotations
import copy
from types import SimpleNamespace
from systems.admin_live_arena_damage_v7800 import _arena, _actor_copy
from systems.uoss_queue_choice_shared_v8200 import choose_queued_skill


HELP = (
    'ADMIN LIVE POMOC 42: arena uoss kolejka nastepny - sprawdz jaki skill '
    'prawdziwy algorytm auto-kolejki wybralby teraz przeciw kopii bossa, '
    'z uwzglednieniem rodzaju kolejki, nauki, poziomow, Many, cooldownu '
    'i stanu bohatera LAB. Tylko odczyt zapisanej kolejki, bez auto-dodawania, '
    'uzycia skilla, EXP, zapisu w SQLite, modyfikacji kursora i losowosci. '
    'Wykonanie efektow skilli i AI 1:1 NADAL NIE JEST obslugiwane.'
)

# The eligibility check uses only the selected, established read methods.
# Even if a future refactor tries to write while previewing, it is blocked.
_DB_READ_METHODS = frozenset((
    'skill_queue_enabled', 'skill_queue_rows', 'active_class_rows',
    'knows_skill', 'class_progress_row', 'skill_progress',
    'equipment', 'equipped_item', 'item_qty', 'socketed_gems',
))

class _ReadOnlyQueueDB:
    def __init__(self, db):
        self._source = db
    def __getattr__(self, name):
        if name not in _DB_READ_METHODS:
            raise ValueError('Kolejka LAB: zablokowana operacja DB: '+str(name)[:45])
        method = getattr(self._source, name)
        if not callable(method):
            raise ValueError('Kolejka LAB: niepoprawna metoda odczytu DB.')
        return method


def isolated_queue_selection(session, state=None):
    """Return detached actor, boss, selection and enabled flag.

    No socket, mutable world or writable database handles are reachable from
    queue operations. The returned actor MUST NOT be used for general casts.
    """
    state = _arena(session) if state is None else state
    actor, _ = _actor_copy(session, state)
    # A shallow copy of the server with a limited DB facade and local party
    # prevents methods on the ghost from accessing mutable real-world objects.
    # No source world or other live user session is handed to eligibility.
    # Deliberately do not copy a real server object: even a shallow copy would
    # retain writable session registries, network transport and world handles.
    safe_server = SimpleNamespace(
        db=_ReadOnlyQueueDB(session.server.db),
        party_sessions=lambda *a, **k: [actor],
        world=None,
    )
    actor.server = safe_server
    actor.skill_queue_cursors = copy.deepcopy(state.get('_v8300_queue_cursors', getattr(session, 'skill_queue_cursors', {}) or {}))
    actor.skill_queue_next_type = str(state.get('_v8300_queue_next_type', getattr(session, 'skill_queue_next_type', 'physical')))
    actor.skill_cooldowns = copy.deepcopy(getattr(session, 'skill_cooldowns', {}) or {})
    actor.active_skill_buffs = copy.deepcopy(getattr(session, 'active_skill_buffs', {}) or {})
    actor.skill_guard = getattr(session, 'skill_guard', 0)
    actor.skill_evade = getattr(session, 'skill_evade', False)
    actor.closed = False
    # Expired private buffs may schedule an informational 'send'. Never allow
    # the ghost to reuse the real session's socket during inspection.
    async def _no_network_message(*args, **kwargs):
        return None
    actor.send = _no_network_message
    actor.send_combat = _no_network_message
    actor.character.room_id = str(session.character.room_id)
    boss = copy.deepcopy(state['boss'])
    boss.room_id = actor.character.room_id
    if not hasattr(boss, 'alive'):
        boss.alive = boss.hp > 0
    else:
        boss.alive = boss.hp > 0
    if not safe_server.db.skill_queue_enabled(actor.account_id):
        return actor, boss, None, False
    selected = choose_queued_skill(
        actor.skill_queue_next_type, actor.skill_queue_cursors,
        lambda channel: actor.skill_queue_entries(channel, active_only=True),
        lambda skill_id: copy.deepcopy(actor.skill_by_id(skill_id)),
        lambda skill: actor.auto_queue_skill_usable(skill, boss),
    )
    return actor, boss, selected, True


def inspect_queue(session):
    actor, boss, selected, enabled = isolated_queue_selection(session)
    if not enabled:
        return 'ARENA UOSS KOLEJKA: kolejka jest wylaczona. LAB nie zmienilo ustawien.'
    if selected is None:
        return ('ARENA UOSS KOLEJKA: brak gotowego skilla. '
                'Sprawdz klase, nauke, koszt Many, cooldown i stan kopii. '
                'Brak zmian postaci, LAB i SQLite.')
    channel, index, length, skill = selected
    skill_id = str(skill.get('id', ''))
    name = str(skill.get('name', skill_id)).replace('\n', ' ')[:90]
    return (f'ARENA UOSS KOLEJKA NASTEPNY: {name}; ID {skill_id[:90]}; '
            f'kanal {channel}; pozycja {index+1}/{length}; '
            f'Mana LAB {actor.current_mana}; HP LAB {actor.current_hp}. '
            'Wybor zgodny ze wspolnym algorytmem normalnej walki. '
            'NIE wykonano skilla, nie naliczono EXP, nie zmieniono kursora ani bazy.')
