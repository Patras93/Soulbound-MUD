# -*- coding: utf-8 -*-
"""Additive, non-gameplay soundpack event transport for plain-text MUD clients.

The v4.20 audited legacy method bodies remain byte-for-byte identical.
Only successful state changes generate events; look/score/expbank never do.
"""
import re
from collections import defaultdict

_TOKEN = re.compile(r'[^\w.:-]', re.UNICODE)


def _token(value):
    """One non-control protocol token; names cannot inject another line/event."""
    return _TOKEN.sub('_', str('unknown' if value is None or value == '' else value).replace('\r', '_').replace('\n', '_'))[:120] or 'unknown'


def _event(event_name, **fields):
    return 'SOUND_EVENT ' + event_name + ''.join(' ' + str(k) + '=' + _token(v) for k, v in fields.items())


def _account_balance(db, account_id, kind, source):
    source = '' if kind in ('character', 'soul') else str(source or '').strip()
    row = db.conn.execute('SELECT balance FROM experience_bank_v2011 '
                          'WHERE account_id=? AND kind=? AND source_key=?',
                          (int(account_id), str(kind).lower(), source)).fetchone()
    return max(0, int(row[0])) if row else 0


def _enqueue(db, account_id, event_name, **fields):
    if account_id is None:
        return
    queues = getattr(db, '_sound_events_v1208', None)
    if queues is None:
        queues = db._sound_events_v1208 = defaultdict(list)
    queue = queues.setdefault(int(account_id), [])
    # Never let stalled/absent sessions accumulate unlimited events in RAM.
    if len(queue) >= 100:
        del queue[:50]
    queue.append(_event(event_name, **fields))


def _active_mobs(session):
    """Current active enemies only, addressed by instance key (AoE safe)."""
    char = getattr(session, 'character', None)
    server = getattr(session, 'server', None)
    if char is None or server is None:
        return []
    world = getattr(server, 'world', None)
    if world is None:
        return []
    result = []
    for mob in world.room_mobs(char.room_id):
        if not getattr(mob, 'alive', True):
            continue
        if not (getattr(mob, 'engaged_by', None) or getattr(mob, 'aoe_engaged_by', None)):
            continue
        key = getattr(mob, 'key', None)
        if key is None:
            continue
        maximum = max(1, int(session.mob_effective_max_hp_v11330(mob)))
        current = max(0, min(maximum, int(mob.hp)))
        result.append((mob, str(key), current, maximum))
    return result


async def _emit_hp_changes(session):
    """Broadcast real HP changes to the local party, without duplicates.

    A stranger fighting another enemy in the same room does not start our
    soundpack's battle/condition music.
    """
    char = getattr(session, 'character', None)
    if char is None:
        return
    members = session.server.party_sessions(session.account_id, same_room=char.room_id) or [session]
    participants = [person for person in members
                    if getattr(person, 'character', None)
                    and not getattr(person, 'closed', False)
                    and person.character.room_id == char.room_id]
    if session not in participants:
        participants.append(session)
    owners = {str(member.character.name) for member in participants}
    for mob, key, current, maximum in _active_mobs(session):
        engaged = {str(getattr(mob, field, '') or '')
                   for field in ('engaged_by', 'aoe_engaged_by')}
        if not (engaged & owners or any(getattr(member, 'combat_mob_key', None) == key
                                       for member in participants)):
            continue
        for listener in participants:
            cache = getattr(listener, '_sound_hp_v1208', None)
            if cache is None:
                cache = listener._sound_hp_v1208 = {}
            snapshot = current, maximum
            if cache.get(key) != snapshot:
                cache[key] = snapshot
                await listener.send(_event('MOB_HP', id=key, current=current, max=maximum),
                                    history_store=False)
            if len(cache) > 512:
                cache.clear()


async def _emit_defeat_hp(session, mob):
    """After successful kill, report zero even if killed mob was removed/unengaged."""
    server = session.server
    room_id = getattr(mob, 'room_id', None)
    key = str(getattr(mob, 'key', '') or '')
    if not key:
        return
    try:
        maximum = max(1, int(session.mob_effective_max_hp_v11330(mob)))
    except (AttributeError, TypeError, ValueError, KeyError):
        return
    owners = {str(getattr(mob, a, '') or '') for a in ('engaged_by', 'aoe_engaged_by')}
    # Some kill paths clear engagement: the owning session and its nearby party
    # still need the terminal state for their audio.
    members = server.party_sessions(session.account_id, same_room=room_id) or [session]
    recipients = list(members)
    for listener in tuple(server.sessions):
        if (listener not in recipients and getattr(listener, 'character', None)
                and listener.character.room_id == room_id
                and (getattr(listener.character, 'name', '') in owners
                     or getattr(listener, 'combat_mob_key', None) == key)):
            recipients.append(listener)
    for listener in recipients:
        if getattr(listener, 'closed', False) or not getattr(listener, 'character', None):
            continue
        if listener.character.room_id != room_id:
            continue
        cache = getattr(listener, '_sound_hp_v1208', None)
        if cache is None:
            cache = listener._sound_hp_v1208 = {}
        if cache.get(key) != (0, maximum):
            cache[key] = (0, maximum)
            await listener.send(_event('MOB_HP', id=key, current=0, max=maximum),
                                history_store=False)


def install_sound_hooks_v1208(session_class):
    """Hooks are installed once on the assembled class, not audited legacy ASTs."""
    if getattr(session_class, '_sound_hooks_installed_v1208', False):
        return
    session_class._sound_hooks_installed_v1208 = True

    # Bank rewards: only observe committed state, do not touch payout math.
    from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
    bank_class = DatabaseExperienceBankV2011Mixin
    if not getattr(bank_class, '_sound_hooks_installed_v1208', False):
        original_allocate = bank_class.allocate_experience_bank_v2011
        def allocate(self, account_id, amount, kind, source_key, cap):
            before = _account_balance(self, account_id, kind, source_key)
            paid = original_allocate(self, account_id, amount, kind, source_key, cap)
            after = _account_balance(self, account_id, kind, source_key)
            if after > before:
                _enqueue(self, account_id, 'EXP_BANK', amount=after-before, kind=kind)
            cap = max(0, int(cap or 0))
            if cap and paid > 0:
                if paid >= cap:
                    _enqueue(self, account_id, 'FULL_CAP', cap=cap, kind=kind)
                elif paid * 2 >= cap:
                    _enqueue(self, account_id, 'HALF_CAP', cap=cap, kind=kind)
            return paid
        bank_class.allocate_experience_bank_v2011 = allocate
        bank_class._sound_hooks_installed_v1208 = True

    old_send = session_class.send
    async def send(self, text='', combat_detail=None, history_category=None, history_store=True):
        # Normal informational commands cannot *create* events; only drain the
        # queue already written by a real rewarded action.
        aid = getattr(self, 'account_id', None)
        queue = getattr(self.server.db, '_sound_events_v1208', {}) if aid is not None else {}
        pending = queue.pop(int(aid), []) if aid is not None else []
        for message in pending:
            await old_send(self, message, history_store=False)
        return await old_send(self, text, combat_detail=combat_detail,
                              history_category=history_category, history_store=history_store)
    session_class.send = send

    old_combat = session_class.send_combat
    async def send_combat(self, text, detail='essential'):
        result = await old_combat(self, text, detail=detail)
        try:
            await _emit_hp_changes(self)
        except (AttributeError, KeyError, TypeError, ValueError):  # AUDIT_INTENTIONAL_PASS: telemetry failures must not break combat
            # Audio telemetry may not break ordinary fighting.
            pass  # AUDIT_INTENTIONAL_PASS: soundpack is optional telemetry
        return result
    session_class.send_combat = send_combat

    old_defeat = session_class.mob_defeated
    async def mob_defeated(self, mob):
        if not mob or not getattr(mob, 'alive', False) or getattr(mob, 'v1400_kill_in_progress', False):
            return await old_defeat(self, mob)
        result = await old_defeat(self, mob)
        if not getattr(mob, 'alive', True):
            try:
                await _emit_defeat_hp(self, mob)
            except (AttributeError, KeyError, TypeError, ValueError):  # AUDIT_INTENTIONAL_PASS: telemetry failures must not break rewards
                pass  # AUDIT_INTENTIONAL_PASS: optional sound event must not break kills
        return result
    session_class.mob_defeated = mob_defeated

    # Reply uses an older social mixin; mark only the active reply delivery.
    # Do not shadow Session.tell: the historical MRO expects the social suite.
    from player.session_mixins.social_base import SessionBaseSocialMixin
    if not getattr(SessionBaseSocialMixin, '_sound_reply_wrapped_v1208', False):
        old_reply = SessionBaseSocialMixin.reply_private_v0928
        async def reply_private_v0928(self, message):
            previous = getattr(self, '_sound_reply_mode_v1208', False)
            self._sound_reply_mode_v1208 = True
            try:
                return await old_reply(self, message)
            finally:
                self._sound_reply_mode_v1208 = previous
        SessionBaseSocialMixin.reply_private_v0928 = reply_private_v0928
        SessionBaseSocialMixin._sound_reply_wrapped_v1208 = True

    async def broadcast_presence(self, kind, name):
        for listener in tuple(self.server.sessions):
            if listener is not self and not getattr(listener, 'closed', True) and getattr(listener, 'character', None):
                await listener.send(_event(kind, name=name), history_store=False)

    old_enter = session_class.enter_world
    async def enter_world(self):
        result = await old_enter(self)
        if getattr(self, 'character', None) and not getattr(self, 'closed', False):
            await broadcast_presence(self, 'PLAYER_LOGIN', self.character.name)
        return result
    session_class.enter_world = enter_world

    old_leave = session_class.leave_current_character_for_selection
    async def leave_current_character_for_selection(self):
        old_name = getattr(getattr(self, 'character', None), 'name', None)
        result = await old_leave(self)
        if old_name and getattr(self, 'character', None) is None:
            await broadcast_presence(self, 'PLAYER_LOGOUT', old_name)
            self.__dict__.pop('_sound_hp_v1208', None)
        return result
    session_class.leave_current_character_for_selection = leave_current_character_for_selection

    old_close = session_class.close
    async def close(self):
        old_name = getattr(getattr(self, 'character', None), 'name', None)
        was_closed = bool(getattr(self, 'closed', False))
        result = await old_close(self)
        if old_name and not was_closed:
            await broadcast_presence(self, 'PLAYER_LOGOUT', old_name)
        return result
    session_class.close = close
