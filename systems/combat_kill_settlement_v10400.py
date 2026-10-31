# -*- coding: utf-8 -*-
"""v104: atomowe rozliczenie monet i statystyk jednego odbiorcy walki.

Wspolny SQLite SAVEPOINT obejmuje wspolny portfel (wszystkie sloty postaci),
EXP Bank szesciu statystyk, EXP postaci i zapis poziomow/statystyk. Brak I/O sieciowego
podczas transakcji; wiadomosci NVDA nalezy wyslac dopiero po sukcesie.
Ta zmiana nie deklaruje jeszcze atomowosci calego zabicia (Soul/klasy/questy).
"""
from __future__ import annotations

from core.sqlite_numeric_guard_v10400 import require_sqlite_int64
from systems.atomic_progression_rewards_v10400 import award_stats_xp_atomic_v10400
from systems.atomic_character_experience_v10400 import award_character_xp_atomic_v10400


def settle_combat_currency_stats_v10400(db, character, account_id, *,
                                         silver=0, gold=0, mithril=0,
                                         stat_xp=0, overcap=False,
                                         character_xp=None):
    if db is None or character is None or type(account_id) is not int or character.account_id != account_id:
        raise ValueError('Nieprawidlowy odbiorca nagrody walki.')
    if not hasattr(db.conn, 'deferred_commits'):
        raise TypeError('Wymagane odroczone COMMIT SQLite.')
    values = (silver, gold, mithril, stat_xp)
    if character_xp is not None:
        values += (character_xp,)
    if any(type(n) is not int or n < 0 for n in values):
        raise ValueError('Nagroda musi byc nieujemna liczba calkowita.')
    old_money = (character.silver, character.gold, character.mithril)
    # Rollback pamieci po udanym rozwoju statystyk, gdy pozniejszy
    # zapis EXP postaci zawiedzie w tej samej transakcji.
    stat_fields = getattr(character, 'STAT_PROGRESS_FIELDS', {})
    saved_fields = tuple(dict.fromkeys(
        ('stat_progress',) + tuple(field for desc in stat_fields.values()
                                     for field in desc[1:]))) if character_xp is not None else ()
    old_stats = {field: getattr(character, field) for field in saved_fields}
    # Fail BEFORE any wallet/EXP bank changes, never clamp overflowing money.
    for label, old, delta in zip(('silver', 'gold', 'mithril'), old_money, values):
        require_sqlite_int64('combat.' + label, old + delta)
    conn = db.conn
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v104_combat_currency_stats')
        try:
            character.silver += silver
            character.gold += gold
            character.mithril += mithril
            # Nested atomic helper guards all stat fields and their bank debits.
            results = (award_stats_xp_atomic_v10400(
                db, character, account_id, stat_xp, overcap=overcap)
                       if stat_xp else [])
            character_result = None
            if character_xp is not None:
                # Same outer SAVEPOINT: money + 6 stats + character EXP and
                # character level. The nested helper restores level on failure.
                character_result = award_character_xp_atomic_v10400(
                    db, character, account_id, character_xp, overcap=overcap)
            if any((silver, gold, mithril)):
                # Wallet mirrors are part of the same transaction.
                db.save_character(character, commit=False)
            conn.execute('RELEASE SAVEPOINT v104_combat_currency_stats')
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT v104_combat_currency_stats')
                conn.execute('RELEASE SAVEPOINT v104_combat_currency_stats')
            finally:
                character.silver, character.gold, character.mithril = old_money
                for field, old_value in old_stats.items():
                    setattr(character, field, old_value)
            raise
    # Existing callers keep their original API. Only the new opt-in live
    # combat path gets committed character payout and its level messages.
    if character_xp is not None:
        return results, character_result
    return results


def settle_combat_full_progression_v10400(
        db, character, account_id, *, silver=0, gold=0, mithril=0,
        stat_xp=0, character_xp=0, soul_xp=0, class_xp=0,
        class_levels=(), overcap=False, class_max_level=None):
    """One per-recipient SQLite transaction for five axes of kill rewards.

    Nested bank, wallet, character and class helpers use SAVEPOINTs but cannot
    commit independently. No await, network sends or combat/event hooks occur
    inside this function. An error at ANY stage restores the entire wallet,
    EXP bank, class rows, character levels and in-memory progression.
    
    Quest/event/bestiary side effects outside this function are NOT included.
    """
    from systems.atomic_progression_rewards_v10400 import (
        award_soul_xp_atomic_v10400, award_class_xp_batch_atomic_v10400)
    if db is None or character is None or type(account_id) is not int or character.account_id != account_id:
        raise ValueError('Nieprawidlowy odbiorca nagrody.')
    if any(type(value) is not int or value < 0 for value in
           (silver, gold, mithril, stat_xp, character_xp, soul_xp, class_xp)):
        raise ValueError('Nagrody musza byc nieujemnymi liczbami calkowitymi.')
    classes = tuple(class_levels)
    if class_xp and not classes:
        raise ValueError('Brak aktywnej klasy do przyznania EXP.')
    if class_max_level is not None and (type(class_max_level) is not int or class_max_level < 1):
        raise ValueError('Nieprawidlowy limit klasy.')
    conn = db.conn
    if not hasattr(conn, 'deferred_commits'):
        raise TypeError('Wymagane odroczone transakcje SQLite.')
    # Snapshot is taken before any helper mutates this live object.
    fields = tuple(dict.fromkeys(
        ('silver','gold','mithril','character_level','character_xp',
         'soul_level','soul_xp','soul_tier','stat_progress') +
        tuple(field for desc in character.STAT_PROGRESS_FIELDS.values()
              for field in desc[1:])))
    before = {key: getattr(character,key) for key in fields}
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v104_full_kill_reward')
        try:
            stats, (character_paid, character_notes) = settle_combat_currency_stats_v10400(
                db, character, account_id, silver=silver, gold=gold,
                mithril=mithril, stat_xp=stat_xp, character_xp=character_xp,
                overcap=overcap)
            soul_paid, soul_notes = (award_soul_xp_atomic_v10400(
                db, character, account_id, soul_xp, overcap=overcap)
                if soul_xp else (0, []))
            class_results = (award_class_xp_batch_atomic_v10400(
                db, account_id, classes, class_xp, overcap=overcap)
                if class_xp else [])
            ascensions = {}
            if class_max_level is not None:
                for (name, _level), (_paid, result) in zip(classes, class_results):
                    overflow = max(0, int(result.get('overflow_xp', 0) or 0))
                    if overflow and int(result['level']) >= class_max_level:
                        ascensions[name] = db.add_ascension_xp_v021(
                            account_id, 'class:' + name, overflow)
            conn.execute('RELEASE SAVEPOINT v104_full_kill_reward')
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT v104_full_kill_reward')
                conn.execute('RELEASE SAVEPOINT v104_full_kill_reward')
            finally:
                for field, value in before.items():
                    setattr(character, field, value)
            raise
    return {
        'stats': stats, 'character': (character_paid, character_notes),
        'soul': (soul_paid, soul_notes),
        'classes': class_results, 'ascensions': ascensions,
        'soul_level_before': before['soul_level'],
        'character_level_before': before['character_level'],
    }
