# -*- coding: utf-8 -*-
"""v115: atomic, bounded silver rewards for proven objective milestones.

Only rewards objectives reported by the authoritative server. All inserts,
claim reservations and shared-wallet writes happen inside the caller's kill
transaction. No audio, no own scheduler, no duplicate progression engine.
"""
from __future__ import annotations
from collections import defaultdict
from core.bootstrap_economy_professions import (
    CURRENCY_SQLITE_SAFE_TOTAL, legacy_currency_to_coins,
)
from .content_catalog import quest_catalog, achievement_catalog
from .objective_progress import mark_claimed, total

_BY_OBJECTIVE = defaultdict(list)
for _quest in quest_catalog():
    _BY_OBJECTIVE[(_quest.region, _quest.objective)].append(('quest', _quest))
for _achievement in achievement_catalog():
    _BY_OBJECTIVE[(_achievement.region, _achievement.objective)].append(
        ('achievement', _achievement))
_BY_OBJECTIVE = {key: tuple(value) for key, value in _BY_OBJECTIVE.items()}

# At most this many rewards per person, per kill. Prevent floods at very high
# levels, while leaving remaining earned milestones claimable by future events.
MAX_PAYOUTS_PER_KILL = 24


def _silver_reward(kind, item, cycle):
    # Capped deterministic, non-exponential economy; no artificial tool drops.
    factor = 240 if kind == 'quest' else 120
    return min(200_000, factor * max(1, int(item.tier)) * (1 + min(4, cycle // 5)))


def settle_kill_objectives(db, character, account_id, region, objectives):
    """Return (quest_count, achievement_count, silver) after atomic payout.

    Must be called *after successful event credit* inside native kill
    settlement. Does not send network messages before commit.
    """
    if isinstance(account_id, bool) or not isinstance(account_id, int) or account_id <= 0:
        raise ValueError('Nieprawidłowy odbiorca nagrody')
    if int(getattr(character, 'account_id', -1)) != account_id:
        raise ValueError('Postać nie należy do odbiorcy nagrody')
    if not callable(getattr(db, 'save_character', None)):
        raise TypeError('Brak autorytatywnego zapisu postaci')
    targets = tuple(dict.fromkeys(objectives))
    if not all((region, objective) in _BY_OBJECTIVE for objective in targets):
        raise ValueError('Nieznany cel nagrody v115')
    coin_balance = legacy_currency_to_coins(character.silver, character.gold, character.mithril)
    original_wallet = (character.silver, character.gold, character.mithril)
    claims = []
    silver = 0
    conn = db.conn
    conn.execute('SAVEPOINT v115_objective_settlement')
    try:
        for objective in targets:
            progress = total(conn, account_id, region, objective)
            for kind, item in _BY_OBJECTIVE[(region, objective)]:
                if len(claims) >= MAX_PAYOUTS_PER_KILL:
                    break
                base = item.target if kind == 'quest' else item.threshold
                if progress < base:
                    continue
                if kind == 'quest' or not item.repeatable:
                    maximum_cycle = 0
                else:
                    maximum_cycle = min(1_000_000, progress // base - 1)
                # Read only this objective's awarded cycles. Never scan the
                # complete 7000-item catalog on each mob death.
                rows = conn.execute(
                    'SELECT cycle FROM v115_objective_claims '
                    'WHERE account_id=? AND claim_key=? AND cycle<=? ORDER BY cycle',
                    (account_id, item.key, maximum_cycle),
                ).fetchall()
                paid = {int(row[0]) for row in rows}
                first_unclaimed = 0
                while first_unclaimed in paid:
                    first_unclaimed += 1
                for cycle in range(first_unclaimed, maximum_cycle + 1):
                    if len(claims) >= MAX_PAYOUTS_PER_KILL:
                        break
                    if cycle in paid:
                        continue
                    reward = _silver_reward(kind, item, cycle)
                    # A full wallet must never silently forfeit a claim.
                    if coin_balance + silver > CURRENCY_SQLITE_SAFE_TOTAL - reward:
                        break
                    if mark_claimed(conn, account_id, item.key, cycle):
                        silver += reward
                        claims.append((kind, item.key, cycle))
        if silver:
            character.silver = int(character.silver) + silver
            db.save_character(character, commit=False)
        conn.execute('RELEASE SAVEPOINT v115_objective_settlement')
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v115_objective_settlement')
        conn.execute('RELEASE SAVEPOINT v115_objective_settlement')
        character.silver, character.gold, character.mithril = original_wallet
        raise
    return (sum(kind == 'quest' for kind, _, _ in claims),
            sum(kind == 'achievement' for kind, _, _ in claims), silver)
