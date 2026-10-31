# -*- coding: utf-8 -*-
"""v104: jedna zaliczona smierc = jeden postep na zwykly quest.

Chroni rownoczesnie wpisy questow podstawowych i OLC multi-objective
SQLite SAVEPOINT. Nie zmienia klasowych sag ani innych licznikow zdarzen.
Komunikaty NVDA nalezy wysylac dopiero po powrocie z funkcji.
"""
from __future__ import annotations

from data.quests import QUESTS
from core.sqlite_numeric_guard_v10400 import require_sqlite_int64


def settle_kill_quest_progress_v10400(db, account_id, template_id, aliases=()):
    """Return (simple_updates, multi_updates) after synchronous atomic settlement.

    Multiple aliases for a defeated mob never credit the same quest twice,
    especially wildcard quests. A failure in OLC progress rolls back the
    preceding regular quest changes. Does not itself guarantee whole-kill
    atomicity with preceding EXP or later item drops.
    """
    if type(account_id) is not int or account_id <= 0:
        raise ValueError('Nieprawidlowe konto postepu questu.')
    if not isinstance(template_id, str) or not template_id:
        raise ValueError('Nieprawidlowy pokonany przeciwnik.')
    aliases = tuple(aliases)
    if any(not isinstance(alias, str) or not alias for alias in aliases):
        raise ValueError('Nieprawidlowy alias celu questu.')
    if not hasattr(db, 'increment_multi_objective_v1800'):
        raise TypeError('Brak obslugi wielocelowych questow.')
    conn = db.conn
    if not hasattr(conn, 'deferred_commits'):
        raise TypeError('Wymagana baza z odroczonym COMMIT.')
    candidates = frozenset((template_id, *aliases))
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v104_atomic_kill_quests')
        try:
            changes = []
            rows = conn.execute(
                "SELECT quest_id,progress FROM quests WHERE account_id=? AND status='active'",
                (account_id,)).fetchall()
            for row in rows:
                qid = str(row['quest_id'])
                quest = QUESTS.get(qid)
                if (not quest or quest.get('kind') != 'kill'
                        or quest.get('v800_class_saga')
                        or quest.get('target') not in candidates | {'*'}):
                    continue
                old = row['progress']
                needed = quest.get('needed')
                if (type(old) is not int or old < 0
                        or type(needed) is not int or needed <= 0):
                    raise ValueError('Nieprawidlowy licznik questu: ' + qid)
                if old >= needed:
                    continue
                new = min(needed, old + 1)
                require_sqlite_int64('quest.progress', new)
                conn.execute(
                    "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=? AND status='active'",
                    (new, account_id, qid))
                changes.append((qid, new))
            # This old helper may request commit. The enclosing defer +
            # SAVEPOINT prevents that commit from releasing earlier writes.
            multi = db.increment_multi_objective_v1800(
                account_id, 'kill', template_id, aliases=tuple(candidates))
            conn.execute('RELEASE SAVEPOINT v104_atomic_kill_quests')
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT v104_atomic_kill_quests')
            finally:
                conn.execute('RELEASE SAVEPOINT v104_atomic_kill_quests')
            raise
    return changes, multi


def settle_all_kill_quests_v10400(db, account_id, template_id, *, aliases=(),
                                   active_classes=(), mob_level=1,
                                   elite=False, boss=False,
                                   party_categories=()):
    """Commit ordinary, OLC, class-saga and party-contract kill credit together.

    The underlying legacy methods retain their quest definitions and business
    rules. Their internal commit requests are deferred until the outer SQLite
    SAVEPOINT has been released. No network I/O occurs here.
    """
    classes = tuple(dict.fromkeys(active_classes))
    categories = tuple(dict.fromkeys(party_categories))
    if (type(mob_level) is not int or mob_level < 0 or
            any(not isinstance(n, str) or not n for n in classes+categories)):
        raise ValueError('Nieprawidlowe parametry postepu walki.')
    if not hasattr(db, 'increment_class_legend_kill_v800') or not hasattr(db, 'increment_party_contract_v11339'):
        raise TypeError('Brak obslugi questow klasy albo druzyny.')
    conn = db.conn
    if not hasattr(conn, 'deferred_commits'):
        raise TypeError('Wymagana transakcyjna baza SQLite.')
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v104_all_kill_quests')
        try:
            regular, multi = settle_kill_quest_progress_v10400(
                db, account_id, template_id, aliases=aliases)
            saga = []
            for name in classes:
                saga.extend(db.increment_class_legend_kill_v800(
                    account_id, name, mob_level, elite=elite, boss=boss))
            party = []
            for category in categories:
                party.extend(db.increment_party_contract_v11339(
                    account_id, category, 1))
            conn.execute('RELEASE SAVEPOINT v104_all_kill_quests')
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT v104_all_kill_quests')
            finally:
                conn.execute('RELEASE SAVEPOINT v104_all_kill_quests')
            raise
    return regular, multi, saga, party
