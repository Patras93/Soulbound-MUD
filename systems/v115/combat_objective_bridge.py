# -*- coding: utf-8 -*-
"""v115 server-only combat objective adapter.

A mob is eligible only if its template explicitly declares a v115 region.
Called INSIDE the existing serialized kill's deferred SQLite transaction after
loot has been processed. No soundpack or character reward dependency.
"""
from __future__ import annotations
from uuid import uuid4
from .high_level_world import REGION_BY_KEY
from .objective_progress import record_event
from .objective_rewards import settle_kill_objectives


def record_v115_victory(session, mob, template, *, event_id=None):
    """Record player/group milestones once per successful native mob death.

    Returns a count of inserted progress events. v114 mobs remain untouched.
    Individual recipients use the same room/party rule as combat rewards.
    """
    if not isinstance(template, dict):
        return 0
    region = template.get('v115_region_key')
    if region is None:
        return 0
    if region not in REGION_BY_KEY:
        raise ValueError('Nieznana kraina v115 w szablonie potwora')
    if getattr(mob, 'alive', True):
        raise ValueError('Nie wolno zaliczać żywego potwora')
    server = session.server
    recipients = server.party_sessions(session.account_id, same_room=session.character.room_id) or [session]
    # The event identifier is created server-side and shared for all recipients.
    event_id = event_id or uuid4().hex
    if not isinstance(event_id, str) or not 1 <= len(event_id) <= 100:
        raise ValueError('event_id')
    boss = bool(template.get('boss') or template.get('is_boss')
                or template.get('crypt_boss') or template.get('uoss_unique_superboss_key'))
    # Only actual, distinct player accounts present in the same room count
    # toward cooperation. Mercenaries and summoned mobs have no player session.
    eligible_accounts = {
        member.account_id for member in recipients
        if type(getattr(member, 'account_id', None)) is int
        and member.account_id > 0
        and getattr(member, 'character', None) is not None
        and getattr(member.character, 'room_id', None) == session.character.room_id
        and getattr(member.character, 'account_id', None) == member.account_id
    }
    objectives = ['defeat_enemy']
    if boss:
        objectives.append('defeat_boss')
    # Regional guardians are actual fixed boss templates, not every generic
    # high-level mob. This unlocks authored v115 'win_challenge' objectives.
    if boss and getattr(mob, 'template_id', None) == f'{region}_guardian':
        objectives.append('win_challenge')
    # A completed dungeon means its actual unique warden died in its final
    # chamber. Neither entering the room nor killing another boss suffices.
    dungeon = template.get('v115_dungeon_boss')
    if dungeon is not None:
        from .regional_dungeons import (room_id as dungeon_room_id,
            is_authored_warden_template, WIDTH, HEIGHT)
        if (dungeon != region or not boss
                or not is_authored_warden_template(getattr(mob, 'template_id', None),template,region)
                or getattr(session.character, 'room_id', None)
                    != dungeon_room_id(region, WIDTH-1, HEIGHT-1)):
            raise ValueError('v115: niepotwierdzone ukończenie lochu')
        objectives.append('finish_dungeon')
    if len(eligible_accounts) >= 2:
        objectives.append('help_party')
    conn = server.db.conn
    credited = 0
    seen = set()
    for recipient in recipients:
        account_id = getattr(recipient, 'account_id', None)
        if not isinstance(account_id, int) or isinstance(account_id, bool) or account_id <= 0:
            continue
        if account_id in seen:
            continue
        seen.add(account_id)
        if not getattr(recipient, 'character', None):
            continue
        if recipient.character.room_id != session.character.room_id:
            continue
        new_objectives = []
        for objective in objectives:
            if record_event(conn, account_id, f'v115:{event_id}:{objective}', region, objective):
                credited += 1
                new_objectives.append(objective)
        # Older minimalist fixture databases only test event crediting.
        # Real game sessions have the native character-saving API.
        if new_objectives and callable(getattr(server.db, 'save_character', None)):
            # If a later part of the full kill transaction fails, restore
            # the session wallet alongside SQLite rollback in the decorator.
            checkpoints = getattr(mob, '_v115_objective_wallet_checkpoints', None)
            if checkpoints is None:
                checkpoints = []
                mob._v115_objective_wallet_checkpoints = checkpoints
            checkpoints.append((recipient, (recipient.character.silver,
                                recipient.character.gold, recipient.character.mithril)))
            quests, achievements, silver = settle_kill_objectives(
                server.db, recipient.character, account_id, region, new_objectives)
            if quests or achievements:
                notices = getattr(mob, '_v115_objective_notices', None)
                if notices is None:
                    notices = []
                    mob._v115_objective_notices = notices
                notices.append((recipient,
                    f'Cele v115: {quests} zadań, {achievements} osiągnięć; '
                    f'+{silver} srebra.'))
    return credited
