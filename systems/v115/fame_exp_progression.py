# -*- coding: utf-8 -*-
"""v115 transactional bridge: EXP progression before delayed Fame.

This adapter deliberately does NOT hook itself into combat. Caller owns eligibility,
real Fame boss identity, and selection of correct full Multi Cap inputs.
No async I/O, soundpack or network calls inside the award transaction.
"""
from __future__ import annotations
import copy
from systems.v115 import fame_queue


def settle_fame_exp_progression(db, character, account_id, region, boss_id, *,
                                character_xp, soul_xp, class_xp, stat_xp,
                                class_levels=(), class_max_level=None,
                                overcap=False, now=None):
    """Durably settle all EXP axes plus queue phase on the same SQLite connection.

    The caller must provide *computed* awards after canonical Fame cap and
    scaling rules; this function never invents or substitutes XP amounts.
    It requires the game's deferred-commit SQLite proxy.  A per-character
    scheduler must serialize settlements against the same live character.
    Only send player/audio notifications AFTER this function returns and the
    surrounding transaction (if any) commits.
    """
    if db is None or character is None or type(account_id) is not int or getattr(character, 'account_id', None) != account_id:
        raise ValueError('Invalid Fame EXP owner')
    conn = db.conn
    if not callable(getattr(conn, 'deferred_commits', None)):
        raise TypeError('Atomic EXP payout requires deferred_commits SQLite connection')
    awards = (character_xp,soul_xp,class_xp,stat_xp)
    if any(type(x) is not int or x < 0 for x in awards):
        raise ValueError('EXP axis amounts must be nonnegative integers')
    # The existing progression function restores its own fields on failure.
    # The surrounding queue may fail AFTER it returned, so also snapshot the
    # complete live character state until the queue phase safely finishes.
    # Avoid deepcopy of unrelated session/server/db objects: only character.
    before = copy.deepcopy(character.__dict__)
    result = []
    from systems.combat_kill_settlement_v10400 import settle_combat_full_progression_v10400

    def award_same_connection(actual_conn, _queued_bonus):
        if actual_conn is not conn:
            raise RuntimeError('EXP payout must use the queue SQLite connection')
        # This must be enclosed by fame_queue's SAVEPOINT: never COMMIT here.
        result.append(settle_combat_full_progression_v10400(
            db,character,account_id,
            silver=0,gold=0,mithril=0,
            character_xp=character_xp,soul_xp=soul_xp,
            class_xp=class_xp,stat_xp=stat_xp,
            class_levels=tuple(class_levels),class_max_level=class_max_level,
            overcap=overcap))

    try:
        with conn.deferred_commits():
            settled = fame_queue.settle_exp(
                conn,account_id,str(region),str(boss_id),award_same_connection,now=now)
        return result[0] if settled else None
    except BaseException:
        character.__dict__.clear()
        character.__dict__.update(before)
        raise
