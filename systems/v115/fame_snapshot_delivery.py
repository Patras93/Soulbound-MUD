# -*- coding: utf-8 -*-
"""v115: immutable Multi Cap snapshot -> authenticated, delayed settlement.

Pure orchestration: this module does not install combat hooks or a scheduler.
Caller must serialize concurrent payouts for a character and send messages only
once the database transaction has committed. No soundpack dependency.
"""
from __future__ import annotations
from systems.v115 import fame_queue, fame_reward_snapshot, fame_exp_progression, fame_legacy_bridge, fame_repeat_rewards


def stage_first_clear(conn, account_id, region, boss_id, boss_name, snapshot, *, now=None):
    """Write-once staging, preserving Fame already earned in the old ledger."""
    if type(account_id) is not int or account_id < 1:
        raise ValueError('Invalid Fame recipient')
    if not isinstance(snapshot, fame_reward_snapshot.RewardSnapshot):
        raise TypeError('Canonical combat EXP snapshot required')
    snapshot.validate()
    legacy_exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fame_bosses_v1702'").fetchone()
    if legacy_exists and conn.execute(
        'SELECT 1 FROM fame_bosses_v1702 WHERE account_id=? AND region=? AND boss_id=?',
        (account_id, str(region), str(boss_id))
    ).fetchone():
        return False
    return fame_reward_snapshot.stage_with_snapshot(
        conn, account_id, region, boss_id, boss_name, snapshot, now=now)


def deliver_stored_for_online_player(db, character, account_id, *, now=None, limit=20):
    """Deliver exactly the XP calculated at the kill, then Fame >=2s later.

    Run under a per-character lock on a serialized authenticated session.
    Outputs are *post-commit* notifications, never call soundpack or network.
    """
    if db is None or character is None or type(account_id) is not int or account_id < 1:
        raise ValueError('Invalid authenticated session')
    if getattr(character, 'account_id', None) != account_id:
        raise ValueError('Character owner mismatch')
    if not callable(getattr(db.conn, 'deferred_commits', None)):
        raise TypeError('Deferred SQLite commit required')
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Invalid payout batch limit')
    events = []
    for region, boss_id, boss_name, status, _, points in fame_queue.due_events(
            db.conn, account_id, now=now, limit=limit):
        if status in ('WAITING', 'EXP_READY'):
            stored = fame_reward_snapshot.load_snapshot(db.conn, account_id, region, boss_id)
            if stored is None:
                raise RuntimeError('Missing immutable Fame EXP snapshot: payment blocked')
            # v115: Fame is account-wide, but EXP belongs to the character that
            # actually fought. Never pay a sibling character on the same account.
            if stored.character_name is not None and stored.character_name != getattr(character, 'name', None):
                continue
            paid = fame_exp_progression.settle_fame_exp_progression(
                db, character, account_id, region, boss_id,
                character_xp=stored.character_xp, soul_xp=stored.soul_xp,
                class_xp=stored.class_xp, stat_xp=stored.stat_xp,
                class_levels=stored.class_levels, class_max_level=stored.class_max_level,
                overcap=stored.overcap, now=now)
            if paid is not None:
                events.append(('exp', region, boss_id, boss_name, paid))
                # At most ONE reward event per scheduler tick. The 3-second
                # cadence separates soundpack cues without requiring audio.
                return events
        elif status == 'FAME_READY':
            stored = fame_reward_snapshot.load_snapshot(db.conn, account_id, region, boss_id)
            if stored and stored.character_name is not None and stored.character_name != getattr(character, 'name', None):
                continue
            if int(points) != 1:
                raise ValueError('Legacy first-clear Fame is exactly one point')
            with db.conn.deferred_commits():
                credited = fame_legacy_bridge.settle_legacy_fame(
                    db.conn, account_id, region, boss_id, now=now)
            if credited:
                events.append(('fame', region, boss_id, boss_name, 1))
                return events
    # Repeat kills earn delayed EXP only; Fame is credited once per objective.
    # The scheduler runs this entire function under the same kill-settlement lock.
    for token, boss_name in fame_repeat_rewards.due_repeats(
            db.conn,account_id,getattr(character,'name',None),now=now,limit=limit):
        paid = fame_repeat_rewards.settle_repeat_exp(
            db,character,account_id,token,now=now)
        if paid is not None:
            events.append(('exp', 'Ponowne zwycięstwo',token,boss_name,paid))
            return events
    return events
