# -*- coding: utf-8 -*-
"""Full catalog coverage for the Windows predeploy quality gate.

Runs only AFTER the assembled world is imported by predeploy_full.py.
Checks ALL registered commands and alias resolutions, ALL quest definitions,
and the SQLite quest lifecycle for EACH quest on an in-memory test database.
This does not claim that every complex gameplay command or NPC conversation
has been run over TCP: those require stateful scenario fixtures.
"""
from __future__ import annotations

from collections import Counter
import sqlite3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if __name__ == '__main__':
    import os
    import tempfile
    _debug_test_directory = tempfile.TemporaryDirectory(prefix='soulbound-catalog-test-')
    os.environ['SOULBOUND_DB'] = _debug_test_directory.name + '/db.sqlite'
    os.environ['SOULBOUND_HOST'] = '127.0.0.1'
    import server  # Assembles dynamic world catalogs before their modules are imported.

from core.command_catalog import COMMAND_CATALOG
from core.mines_threat import COMMAND_ALIASES
from player.session import Session
from player.session_mixins.command_registry import COMMAND_REGISTRY, resolve_session_command
from systems.content_registry import QUESTS, ITEMS, NPCS
from storage.db_quests import DatabaseQuestMixin


class _QuestTestDatabase(DatabaseQuestMixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE quests (
                account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                progress INTEGER NOT NULL DEFAULT 0,
                completed_at INTEGER NOT NULL DEFAULT 0,
                completion_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (account_id, quest_id)
            );
            CREATE TABLE quest_resource_progress_v0929 (
                account_id INTEGER NOT NULL, quest_id TEXT NOT NULL,
                resource_id TEXT NOT NULL DEFAULT '', progress INTEGER NOT NULL DEFAULT 0
            );
        ''')


def run_coverage():
    errors = []
    warnings = []
    checked = 0
    catalogue = COMMAND_CATALOG.snapshot()
    aliases = dict(COMMAND_ALIASES)
    specs = dict(COMMAND_REGISTRY)
    if not specs or not aliases or not QUESTS:
        raise AssertionError('Loaded game catalog is unexpectedly empty')
    for alias, canonical in sorted(aliases.items()):
        checked += 1
        actual = resolve_session_command(alias)
        if actual != canonical:
            errors.append(f'komenda alias {alias!r}: {actual!r}, oczekiwano {canonical!r}')
        if canonical not in specs:
            errors.append(f'alias {alias!r}: brak zarejestrowanej komendy {canonical!r}')
    for canonical, spec in sorted(specs.items()):
        checked += 1
        if resolve_session_command(canonical) != canonical:
            errors.append(f'komenda {canonical}: nie rozpoznano nazwy kanonicznej')
        if not isinstance(spec, tuple) or len(spec) != 3:
            errors.append(f'komenda {canonical}: nieprawidlowa deklaracja handlera')
            continue
        handler, args, kwargs = spec
        if not isinstance(handler, str) or not callable(getattr(Session, handler, None)):
            errors.append(f'komenda {canonical}: brak wywolywalnej metody {handler!r}')
        if not isinstance(args, tuple) or not isinstance(kwargs, dict):
            errors.append(f'komenda {canonical}: bledne parametry routera')
        meta = catalogue['commands'].get(canonical)
        if not meta or meta.get('handler') != handler:
            errors.append(f'komenda {canonical}: brak/spojnosc metadanych katalogu')
    for conflict in COMMAND_CATALOG.conflicts():
        errors.append(f'konflikt aliasu: {conflict}')

    # All quest definitions, including dynamically installed expansions.
    kinds = Counter()
    rewards = 0
    referenced = Counter()
    for qid, quest in sorted(QUESTS.items()):
        checked += 1
        if not isinstance(qid, str) or not qid.strip() or not isinstance(quest, dict):
            errors.append(f'quest {qid!r}: identyfikator lub struktura niepoprawna')
            continue
        if not str(quest.get('name') or '').strip():
            errors.append(f'quest {qid}: pusta nazwa')
        if not str(quest.get('giver') or '').strip():
            errors.append(f'quest {qid}: brak zleceniodawcy')
        kind = str(quest.get('kind') or '').strip()
        kinds[kind] += 1
        if not kind:
            errors.append(f'quest {qid}: pusty rodzaj zadania')
        if 'needed' in quest:
            try:
                if int(quest['needed']) <= 0:
                    errors.append(f'quest {qid}: needed musi byc dodatnie')
            except (TypeError, ValueError, OverflowError):
                errors.append(f'quest {qid}: niepoprawne needed {quest["needed"]!r}')
        requirement = quest.get('requires_quest')
        if requirement:
            referenced[qid] = str(requirement)
            if requirement not in QUESTS:
                errors.append(f'quest {qid}: nieznany poprzednik {requirement!r}')
            if requirement == qid:
                errors.append(f'quest {qid}: wymaga samego siebie')
        if quest.get('repeatable'):
            try:
                if int(quest.get('repeat_cooldown') or 0) < 0:
                    errors.append(f'quest {qid}: ujemny cooldown')
            except (TypeError, ValueError, OverflowError):
                errors.append(f'quest {qid}: niepoprawny cooldown')
        item_rewards = quest.get('reward_items') or {}
        if not isinstance(item_rewards, dict):
            errors.append(f'quest {qid}: reward_items nie jest slownikiem')
        else:
            for item, count in item_rewards.items():
                checked += 1
                if item not in ITEMS:
                    errors.append(f'quest {qid}: nieistniejacy przedmiot nagrody {item!r}')
                try:
                    if int(count) <= 0:
                        errors.append(f'quest {qid}: niepoprawna ilosc nagrody {item!r}')
                except (TypeError, ValueError, OverflowError):
                    errors.append(f'quest {qid}: niepoprawna ilosc nagrody {item!r}')
                rewards += 1
        for field in ('reward_profession_xp', 'reward_tool_xp', 'reward_silver',
                      'reward_gold', 'reward_mithril'):
            if field in quest:
                try:
                    if int(quest[field] or 0) < 0:
                        errors.append(f'quest {qid}: ujemna nagroda {field}')
                except (TypeError, ValueError, OverflowError):
                    errors.append(f'quest {qid}: niepoprawna nagroda {field}')

    # Cycles are game-stoppers: an entire quest chain would become unreachable.
    for qid in referenced:
        node = qid
        seen = set()
        while node in referenced:
            if node in seen:
                errors.append(f'quest {qid}: cykliczne requires_quest ({node})')
                break
            seen.add(node)
            node = referenced[node]

    # An NPC may offer one or a chain of quests; every referenced quest must exist.
    npc_links = 0
    for npc_id, npc in NPCS.items():
        if not isinstance(npc, dict):
            continue
        candidates = ([npc['quest']] if npc.get('quest') else [])
        for field in ('quest_chain', 'specialist_quests'):
            candidates += list(npc.get(field) or [])
        for qid in candidates:
            npc_links += 1
            checked += 1
            if qid not in QUESTS:
                errors.append(f'NPC {npc_id}: nieznany quest {qid}')

    # Exercise persistence of EVERY quest through its real DB mixin methods.
    # Important: this DOES NOT grant actual XP/items or test NPC dialogue.
    db = _QuestTestDatabase()
    persisted = 0
    try:
        for qid, quest in sorted(QUESTS.items()):
            db.start_quest(1, qid)
            first = db.quest(1, qid)
            if first is None or first['status'] != 'active' or first['progress'] != 0:
                errors.append(f'quest {qid}: start SQLite failed')
                continue
            goal = max(1, int(quest.get('needed', 1) or 1))
            db.set_quest_progress(1, qid, goal)
            if db.quest(1, qid)['progress'] != goal:
                errors.append(f'quest {qid}: progress SQLite failed')
            db.complete_quest(1, qid)
            finished = db.quest(1, qid)
            if finished['status'] != 'completed' or finished['completion_count'] != 1:
                errors.append(f'quest {qid}: complete SQLite failed')
            db.restart_quest(1, qid)
            reopened = db.quest(1, qid)
            if reopened['status'] != 'active' or reopened['progress'] != 0 or reopened['completion_count'] != 1:
                errors.append(f'quest {qid}: restart SQLite failed')
            if db.abandon_quest(1, qid) is not True:
                errors.append(f'quest {qid}: abandon SQLite failed')
            abandoned = db.quest(1, qid)
            if abandoned['status'] != 'abandoned' or abandoned['completion_count'] != 1:
                errors.append(f'quest {qid}: abandon history lost')
            persisted += 1
            checked += 6
        integrity = db.conn.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            errors.append(f'quest SQLite integrity_check: {integrity}')
    finally:
        db.conn.close()

    # Be explicit: 7 per-player TCP info commands != all registry handlers;
    # full real-game accept/turn-in scenarios require quest-specific fixtures.
    tcp_smoke = ('who', 'look', 'help', 'tytani', 'expbank', 'lochy7', 'party', 'quests', 'inventory', 'equipment')
    for canonical in tcp_smoke:
        if canonical not in specs:
            errors.append(f'TCP smoke command {canonical} absent from registry')
    warnings.append('NOT TESTED: pelne wykonanie kazdej komendy z argumentami, stanami i uprawnieniami')
    warnings.append('NOT TESTED: realne wykonanie i odbior kazdego questa przez NPC w grze')
    return {
        'errors': errors, 'warnings': warnings, 'checks': checked,
        'aliases': len(aliases), 'commands': len(specs),
        'quests': len(QUESTS), 'sqlite_flows': persisted,
        'kinds': kinds, 'item_rewards': rewards, 'npc_links': npc_links,
        'tcp_smoke_commands': len(tcp_smoke),
    }


def main():
    data = run_coverage()
    print(f"COMMANDS: {data['aliases']}/{data['aliases']} aliases, "
          f"{data['commands']}/{data['commands']} registered methods; registry/dispatch metadata checked")
    print(f"QUESTS: {data['quests']}/{data['quests']} definitions, "
          f"{data['npc_links']} NPC links, {data['item_rewards']} item rewards checked")
    print(f"QUEST SQLITE: {data['sqlite_flows']}/{data['quests']} "
          'accept/progress/complete/restart/abandon flows in memory')
    print('QUEST TYPES: ' + ', '.join(f'{k}={v}' for k, v in sorted(data['kinds'].items())))
    for item in data['warnings']:
        print('COVERAGE WARNING: ' + item)
    if data['errors']:
        for item in data['errors'][:40]:
            print('COVERAGE ERROR: ' + item)
        raise RuntimeError(f'Command/quest coverage failed: {len(data["errors"])} errors')
    print(f'COMMAND / QUEST CATALOG v2.10.2: {data["checks"]} checks PASS; '
          'runtime scenarios only where separately documented')
    return data


if __name__ == '__main__':
    try:
        main()
    finally:
        _debug_test_directory.cleanup()
