# -*- coding: utf-8 -*-
"""Bezstratne wypłaty Soul, statystyk i klasy do istniejącego SQLite.

Nie jest migracją INTEGER -> BigNumber TEXT. Każda wypłata obejmuje EXP Bank,
postęp postaci/klasy i trwały zapis w tym samym SAVEPOINT. Nie wysyła wiadomości
ani nie tworzy nowych połączeń. Nagrody większe niż INTEGER SQLite pozostają
w EXP Bank przy capie zero albo są bezpiecznie odrzucane przez preflight.
"""
from __future__ import annotations

from systems.experience_bank_v2011 import banked_experience_v2011
from collections.abc import Mapping


def _check(db, character, account_id):
    if db is None or character is None or type(account_id) is not int or account_id != character.account_id:
        raise ValueError('Nieprawidłowe konto nagrody.')
    if not hasattr(db.conn, 'deferred_commits'):
        raise TypeError('Wymagana obsługa odroczonego COMMIT SQLite.')


def _atomic(db, marker, operation, rollback):
    """Operacja nie może popełnić osobnego COMMIT między bankiem a postacią."""
    conn = db.conn
    with conn.deferred_commits():
        conn.execute('SAVEPOINT ' + marker)
        try:
            result = operation()
            conn.execute('RELEASE SAVEPOINT ' + marker)
            return result
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT ' + marker)
                conn.execute('RELEASE SAVEPOINT ' + marker)
            finally:
                rollback()
            raise


def award_soul_xp_atomic_v10400(db, character, account_id, amount, *,
                                overcap=False, single_level_cap=False):
    """Bank Soul + mnożniki rasy/gildii + awans + zapis postaci jako jedna operacja."""
    _check(db, character, account_id)
    old = (character.soul_level, character.soul_xp, character.soul_tier)
    def run():
        paid = banked_experience_v2011(
            db, account_id, amount, 'soul', int(old[0]), overcap=overcap)
        notes = character.add_soul_xp(paid, single_level_cap=single_level_cap)
        if paid:
            db.save_character(character, commit=False)
        return paid, notes
    def undo():
        character.soul_level, character.soul_xp, character.soul_tier = old
    return _atomic(db, 'v104_live_soul_atomic', run, undo)


def award_stats_xp_atomic_v10400(db, character, account_id, amount, *,
                                 targets=None, overcap=False, single_level_cap=False):
    """Wszystkie wskazane statystyki w jednej transakcji, a nie 6 częściowych."""
    _check(db, character, account_id)
    valid = character.STAT_PROGRESS_FIELDS
    names = tuple(valid) if targets is None else tuple(targets)
    if not names or len(names) > len(valid) or len(set(names)) != len(names) or any(n not in valid for n in names):
        raise ValueError('Nieprawidłowe lub powtórzone statystyki.')
    # v104: Questy moga przyznawac inny EXP kazdej statystyce. Zweryfikuj
    # CALY rozklad nagrod przed pierwszym zapisem, bez rzutowania float -> int.
    if isinstance(amount, Mapping):
        if set(amount) != set(names) or any(type(amount[name]) is not int or amount[name] < 0 for name in names):
            raise ValueError('Nieprawidlowy rozklad EXP statystyk.')
        requested = {name: amount[name] for name in names}
    else:
        if type(amount) is not int or amount < 0:
            raise ValueError('Nieprawidlowa ilosc EXP statystyk.')
        requested = {name: amount for name in names}
    fields = tuple(dict.fromkeys(('stat_progress',) + tuple(f for name in valid for f in valid[name][1:])))
    old = {field: getattr(character, field) for field in fields}
    def run():
        results = []
        for name in names:
            # Przy zerze nie dotykamy stanu postaci ani banku.
            if requested[name] == 0:
                results.append((name, 0, []))
                continue
            paid = banked_experience_v2011(
                db, account_id, requested[name], 'stat', character.character_level,
                source_key=name, overcap=overcap)
            notes = character.add_stat_progress(
                paid, targets=(name,), single_level_cap=single_level_cap)
            results.append((name, paid, notes))
        if any(paid for _, paid, _ in results):
            db.save_character(character, commit=False)
        return results
    def undo():
        for field, value in old.items():
            setattr(character, field, value)
    return _atomic(db, 'v104_live_stats_atomic', run, undo)


def award_class_xp_atomic_v10400(db, account_id, class_name, amount, level, *,
                                 overcap=False, single_level_cap=False):
    """Jedna wypłata biegłości: bank EXP + class_progress w jednym SAVEPOINT."""
    if db is None or type(account_id) is not int or account_id <= 0 or not isinstance(class_name, str) or not class_name:
        raise ValueError('Nieprawidłowa klasa lub konto.')
    if not hasattr(db.conn, 'deferred_commits'):
        raise TypeError('Wymagana obsługa odroczonego COMMIT SQLite.')
    def run():
        paid = banked_experience_v2011(db, account_id, amount, 'class', int(level),
                                       source_key=class_name, overcap=overcap)
        result = db.add_class_mastery_xp(account_id, class_name, paid,
                                         single_level_cap=single_level_cap)
        return paid, result
    return _atomic(db, 'v104_live_class_atomic', run, lambda: None)


def award_class_xp_batch_atomic_v10400(db, account_id, class_levels, amount, *,
                                       overcap=False, single_level_cap=False):
    """Wszystkie klasy z JEDNEJ nagrody w jednym SAVEPOINT.

    Nie aktywuje klas, nie zmienia liczby slotow. Każda z nich zachowuje
    wlasny bank. Jezeli ktorakolwiek wyplata zawiedzie, wszystkie sie cofaja.
    """
    if db is None or type(account_id) is not int or account_id <= 0:
        raise ValueError('Nieprawidlowe konto.')
    if type(amount) is not int or amount < 0:
        raise ValueError('Nieprawidlowy EXP klasy.')
    pairs = tuple(class_levels)
    if not pairs or any(not isinstance(p, (tuple,list)) or len(p) != 2 or
                        not isinstance(p[0], str) or not p[0] or
                        type(p[1]) is not int or p[1] < 1 for p in pairs):
        raise ValueError('Nieprawidlowa lista klas.')
    if len(set(name for name, _ in pairs)) != len(pairs):
        raise ValueError('Powtorzona klasa w jednej nagrodzie.')
    if not hasattr(db.conn, 'deferred_commits'):
        raise TypeError('Wymagany SQLite z odroczonym COMMIT.')
    def run():
        return [award_class_xp_atomic_v10400(
            db, account_id, name, amount, level,
            overcap=overcap, single_level_cap=single_level_cap
        ) for name, level in pairs]
    return _atomic(db, 'v104_live_class_batch_atomic', run, lambda: None)
