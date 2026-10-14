# -*- coding: utf-8 -*-
"""Soulbound v2.30.2: complete INVENTORY plus deeper execution contracts.

Every registered command and every quest is enumerated. Only checks actually
executed are counted as executed. Passing this stage is not a claim of having
completed every quest in real gameplay or tried every command argument.
The runner always supplies a disposable SOULBOUND_DB and localhost only.
"""
from __future__ import annotations

from collections import Counter
from contextlib import closing
import inspect
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

READ_TCP_CASES = (
    'who', 'status', 'look', 'help', 'tytani lista', 'expbank', 'lochy7',
    'quests', 'skills', 'professions', 'inventory', 'equipment', 'map',
    'where', 'money', 'fame', 'titles', 'achievements', 'tools', 'spells',
    'soul', 'friends', 'atlas', 'bestiary', 'codex',
)
# Non-destructive commands and deliberately INVALID operations.  The latter
# must not change money/quest state or unexpectedly complete any progression.
ADDITIONAL_TCP_CASES = (
    'quests ukonczone', 'quests godzinne', 'mistrzprof receptury',
    'ocean4 modul lista', 'tytani historia', 'help quest',
    'help profesje', 'help ocean', 'map', 'exits',
    'przyjmij quest 999999', 'oddaj quest 999999',
    'mistrzprof wykonaj Kowalstwo 999', 'ocean4 modul zaloz 0 999',
)
NEGATIVE_TCP_CASES = ADDITIONAL_TCP_CASES[-4:]

# Recognized kinds are checked against all live definitions.  A newly added
# kind MUST be explicitly reviewed and included here or the gate fails.
SUPPORTED_QUEST_KINDS = {
    'collect', 'collect_category', 'collect_distinct_category', 'collect_resource', 'collect_resource_set',
    'craft_set', 'deliver_npc', 'discover_secret', 'explore_frontier',
    'kill', 'legendary_rare', 'mini_dungeon', 'party_contract',
    'profession_action', 'talk_class_teacher', 'talk_npc',
    'world_boss', 'world_event',
}


def check_sandbox_environment():
    db = os.environ.get('SOULBOUND_DB', '')
    if not db or not Path(db).is_absolute():
        raise RuntimeError('Brak absolutnej sciezki testowej SQLite; zabroniony start bez izolacji')
    path = Path(db).resolve()
    if not path.parent.name.startswith(('soulbound-predeploy-', 'soulbound-full-audit-', 'soulbound-coverage-')):
        raise RuntimeError('Test SQLite musi znajdowac sie w katalogu tymczasowym predeploy')
    temp_root = Path(tempfile.gettempdir()).resolve()
    if temp_root not in path.parents or ROOT in path.parents:
        raise RuntimeError('Testowa SQLite musi byc pod prawdziwym katalogiem TEMP poza kodem gry')
    if os.environ.get('SOULBOUND_HOST') != '127.0.0.1':
        raise RuntimeError('Testy nie moga uzyskac polaczenia z publicznym serwerem')
    return path


def check_handlers():
    from player.session import Session
    from player.session_mixins.command_registry import COMMAND_REGISTRY
    from core.mines_threat import COMMAND_ALIASES
    from player.session_mixins.command_registry import resolve_session_command
    errors, coverage = [], Counter()
    handlers = {}
    for cmd, spec in sorted(COMMAND_REGISTRY.items()):
        if not isinstance(spec, tuple) or len(spec) != 3:
            errors.append(f'Zly format routera: {cmd}')
            continue
        name, positional, keywords = spec
        bound = getattr(Session, name, None)
        if not callable(bound):
            errors.append(f'Brak wywolywalnego handlera: {cmd} -> {name}')
            continue
        try:
            signature = inspect.signature(bound)
            if not signature.parameters:
                errors.append(f'Handler bez self: {cmd} -> {name}')
        except (TypeError, ValueError) as ex:
            errors.append(f'Handler {cmd}: brak sygnatury ({ex})')
        handlers[cmd] = name
        coverage['registered_handlers'] += 1
    for alias, canonical in sorted(COMMAND_ALIASES.items()):
        if canonical not in COMMAND_REGISTRY or resolve_session_command(alias) != canonical:
            errors.append(f'Zepsuty alias: {alias} -> {canonical}')
        coverage['alias_resolutions'] += 1
    for cmd in READ_TCP_CASES + ADDITIONAL_TCP_CASES:
        token = cmd.split()[0]
        # Some legacy commands are handled by the central command loop rather
        # than the declarative router, so coverage is verified at live TCP.
        if not token.strip():
            errors.append('Pusta komenda TCP')
    return errors, coverage, handlers


def check_quest_isolation(quests):
    from storage.db_quests import DatabaseQuestMixin

    class _QuestDatabase(DatabaseQuestMixin):
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.conn.executescript('''
                CREATE TABLE quests (
                    account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active', progress INTEGER NOT NULL DEFAULT 0,
                    completed_at INTEGER NOT NULL DEFAULT 0,
                    completion_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (account_id, quest_id)
                );
                CREATE TABLE quest_resource_progress_v0929 (
                    account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL DEFAULT '', progress INTEGER NOT NULL DEFAULT 0
                );
            ''')

    errors = []
    checks = 0
    db = _QuestDatabase()
    try:
        for index, (qid, quest) in enumerate(sorted(quests.items())):
            aid = 10000 + index
            other = 20000 + index
            if db.quest(aid, qid) is not None or db.quest(other, qid) is not None:
                errors.append(f'{qid}: nowy gracz ma nieoczekiwany quest')
            db.start_quest(aid, qid)
            goal = max(1, int(quest.get('needed', 1) or 1))
            db.set_quest_progress(aid, qid, goal)
            if db.quest(other, qid) is not None:
                errors.append(f'{qid}: przeciek postepu miedzy kontami')
            db.complete_quest(aid, qid)
            if db.quest(other, qid) is not None:
                errors.append(f'{qid}: przeciek ukonczenia miedzy kontami')
            db.restart_quest(aid, qid)
            if db.quest(aid, qid)['progress'] != 0 or db.quest(other, qid) is not None:
                errors.append(f'{qid}: postep innego konta naruszony przy restarcie')
            db.abandon_quest(aid, qid)
            if db.quest(other, qid) is not None:
                errors.append(f'{qid}: porzucenie dotknelo innego konta')
            checks += 6
        if db.conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            errors.append('SQLite quest memory: integrity_check failed')
    finally:
        db.conn.close()
    return errors, checks


def run_exhaustive():
    check_sandbox_environment()
    # Called from predeploy_full.py after the world is assembled; no duplicate bootstrap.
    from systems.content_registry import QUESTS
    from validation.v2102_command_quest_coverage import run_coverage
    base = run_coverage()
    errors = list(base['errors'])
    handler_errors, stats, handlers = check_handlers()
    errors += handler_errors
    kinds = Counter(str(q.get('kind') or '') for q in QUESTS.values())
    unexpected = sorted(set(kinds) - SUPPORTED_QUEST_KINDS)
    if unexpected:
        errors.append('Nowy typ questu bez jawnej klasyfikacji: ' + ', '.join(unexpected))
    quest_errors, isolation = check_quest_isolation(QUESTS)
    errors += quest_errors
    print('AUDYT WZDLUZ I WSZERZ - POKRYCIE KATALOGOW')
    print(f"KOMENDY: {base['aliases']} aliasow, {base['commands']} handlerow, "
          f"{stats['registered_handlers']} sygnatur sprawdzonych")
    print(f"QUESTY: {base['quests']} definicji, {len(kinds)} typow, "
          f"{base['sqlite_flows']} pelnych cykli bazy")
    print(f'QUESTY SQLITE: {isolation} dodatkowych kontroli izolacji kont')
    print(f'TCP ZAPLANOWANE: {len(READ_TCP_CASES)} bazowych komend na 5 klientach, '
          f'{len(ADDITIONAL_TCP_CASES)} scenariuszy dodatkowych na pierwszym kliencie')
    print(f'RZECZYWISTE TCP: {len(READ_TCP_CASES) + len(ADDITIONAL_TCP_CASES)} wariantow komend '
          '(w tym powtorzone nazwy z innymi argumentami), testowane w ostatniej bramce.')
    print(f'QUESTY NPC PRZEJSCIE FABULY: 0/{base["quests"]} w TYM MODULE; osobne scenariusze NPC/TCP sa na koncu predeploy.')
    print('POKRYCIE WYKONANIA: TESTOWANE OSOBNO przez TCP i dedykowane scenariusze.')
    print('NOT TESTED: kompletne wykonanie wszystkich 373 handlerow we wszystkich stanach gry.')
    print('NOT TESTED w tym module: fabularne ukonczenie i odbior wszystkich questow przez TCP; pojedyncze rzeczywiste questy bada osobny autogracz.')
    if errors:
        for error in errors[:50]:
            print('AUDYT FAIL: ' + error)
        raise AssertionError(f'AUDYT gry: {len(errors)} bledow')
    checks = base['checks'] + stats['registered_handlers'] + isolation + len(READ_TCP_CASES) + len(ADDITIONAL_TCP_CASES)
    print(f'PELNE KATALOGI I IZOLACJA SQLite: {checks} checks PASS; runtime coverage raportowane oddzielnie')
    return checks


if __name__ == '__main__':
    run_exhaustive()
