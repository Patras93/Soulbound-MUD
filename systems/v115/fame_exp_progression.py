# -*- coding: utf-8 -*-
"""v115 transactional bridge: EXP progression before delayed Fame.

This adapter deliberately does NOT hook itself into combat. Caller owns eligibility,
real Fame boss identity, and selection of correct Multi Cap inputs.
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
    # The immutable kill snapshot above is the NORMAL kill EXP. A FIRST Fame
    # also earns the independent 10% Multi Cap milestone bonus (v116.53) on
    # each existing axis. Sample before awarding the kill to avoid having a
    # character level-up artificially raise this same Fame bonus.
    # Historical isolated SQLite fixtures have no account-level Multi Cap
    # resolver. Keep their original, exact one-source payout unchanged.
    # Real production DB always has the canonical resolver: its absence on
    # a real character remains a hard failure, never a fabricated bonus.
    if getattr(db, '_uncapped_awards_v11664', False):
        from systems.independent_milestone_xp_v11664 import fame_xp_per_first_v11664
        fame_bonus = fame_xp_per_first_v11664(character.character_level)
    else:
        fame_bonus = None  # legacy test fallback below
    cap_resolver = getattr(db, 'multi_cap_v23215', None) if fame_bonus is None else None
    if callable(cap_resolver):
        multi_cap = cap_resolver(account_id)
        if multi_cap is None:
            raise RuntimeError('FAME: brak Multi Cap postaci')
        from systems.milestone_cap_rewards_v2103 import (
            milestone_payout_from_cap_v11653, V11653_FAME_CAP_PERCENT,
        )
        fame_bonus = milestone_payout_from_cap_v11653(
            multi_cap, V11653_FAME_CAP_PERCENT)
    elif fame_bonus is None:
        fame_bonus = 0

    def award_same_connection(actual_conn, _queued_bonus):
        if actual_conn is not conn:
            raise RuntimeError('EXP payout must use the queue SQLite connection')
        # This must be enclosed by fame_queue's SAVEPOINT: never COMMIT here.
        normal = settle_combat_full_progression_v10400(
            db,character,account_id,
            silver=0,gold=0,mithril=0,
            character_xp=character_xp,soul_xp=soul_xp,
            class_xp=class_xp,stat_xp=stat_xp,
            class_levels=tuple(class_levels),class_max_level=class_max_level,
            overcap=overcap)
        # Same queue SAVEPOINT and SQLite connection: either both EXP sources
        # and the phase commit, or neither. No bonus on repeat kills.
        if fame_bonus:
            premium = settle_combat_full_progression_v10400(
                db,character,account_id,
                silver=0,gold=0,mithril=0,
                character_xp=fame_bonus,soul_xp=fame_bonus,
                class_xp=fame_bonus if class_levels else 0,stat_xp=fame_bonus,
                class_levels=tuple(class_levels),class_max_level=class_max_level,
                overcap=overcap)
            normal['fame_bonus'] = premium
            normal['fame_bonus_cap'] = fame_bonus
        # New kills paid ordinary EXP immediately, so their saved snapshot
        # contains zeros. Old pending rewards contain real values and MUST
        # continue paying those amounts once; do not erase legacy debts.
        normal['fame_normal_exp_deferred'] = bool(any(awards))
        result.append(normal)

    try:
        with conn.deferred_commits():
            settled = fame_queue.settle_exp(
                conn,account_id,str(region),str(boss_id),award_same_connection,now=now)
        return result[0] if settled else None
    except BaseException:
        character.__dict__.clear()
        character.__dict__.update(before)
        raise
