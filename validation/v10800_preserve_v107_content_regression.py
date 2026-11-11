# -*- coding: utf-8 -*-
"""Preserve original v107 classes, races, progression and v108 fixes.

Baselines are SHA256 of the verified full candidate v107 source ZIP,
not user data. Only an in-memory SQLite test is modified here.
"""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import hashlib
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
BASELINE = {
    'core/classes_skills.py': '515f30e864bd7023d66938637e829f94d8e8f9dbc8023ee56fce577aafba44b2',
    'core/live_level_caps_v5200.py': '3ea9ca260713c1c8302f4dd1aa608a9132eceabfc19aa1723323aae207be279a',
    'core/archetypes/chaos.py': 'e3c8337d895e213d4031381cf15690d55a2b53cbd196e924f4eaad34e68229ab',
    'world/dynamic_content.py': '665e76e425e231b11241f475edbfb9aebfa6e65e69af0667ad6845f68d0e8531',
    'world/v10700_chaos_chapter_one.py': '9fdaee1bbc922bf3a08095b470494ff5367e248d1851259f7fe36fa083f79a21',
    'world/v10700_chaos_chapters_2_6.py': '433dfbc78f2b7d6596188830dd43c54e331031dbef956f26abfefdb8be297009',
    'world/v10700_saga_760_quests.py': '900e75199c505cfcc3f61f30c01356d6286b50ddc9d30c80a80dd03f1c271870',
}

def run():
    checks = 0
    def verify(ok, reason):
        nonlocal checks
        assert ok, reason
        checks += 1

    version = (ROOT / 'VERSION').read_text('utf-8').strip()
    for name, reference in BASELINE.items():
        path = ROOT / name
        verify(path.is_file(), 'Brakuje kodu v107: ' + name)
        body = path.read_bytes()
        if name == 'world/dynamic_content.py' and version == '109.00.0':
            # v109 only APPENDS its registration hook. The entire v107/v108
            # foundation must retain its original SHA256, byte for byte.
            marker = b'\n# v109 Horyzonty:'
            verify(body.count(marker) == 1, 'Brak jednoznacznego rozszerzenia v109')
            body = body[:body.index(marker)]
        verify(hashlib.sha256(body).hexdigest() == reference,
               'Zmodyfikowano zawartosc v107: ' + name)
    from core.archetypes.chaos import CLASS_SPECS, RACE_SPECS, PROFESSION_SPECS
    verify(len(CLASS_SPECS) == 7, 'utracone klasy v107')
    verify(len(RACE_SPECS) == 8, 'utracone rasy v107')
    verify(len(PROFESSION_SPECS) == 8, 'utracone profesje v107')
    from systems.v10700_live_equipment import _check_all_accounts
    from systems.equipment_shadow_slots_v10600 import _check_account
    catalog = {'helm': {'type': 'armor'}, 'ore': {'type': 'material'}}
    with closing(sqlite3.connect(':memory:')) as conn:
        conn.executescript('''
            CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
                PRIMARY KEY(account_id,slot));
            CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE v106_item_instances(instance_id TEXT PRIMARY KEY,
                account_id INTEGER,item_id TEXT,evolution_stage INTEGER,origin TEXT);
            CREATE TABLE v106_equipped_instances(account_id INTEGER,slot TEXT,instance_id TEXT,
                PRIMARY KEY(account_id,slot));
            CREATE TABLE v106_stored_instances(instance_id TEXT PRIMARY KEY,
                account_id INTEGER,storage_kind TEXT,container TEXT);
            INSERT INTO inventory VALUES (1,'helm',1),(1,'ore',5);
            INSERT INTO equipment VALUES (1,'head','helm');
            INSERT INTO v106_item_instances VALUES ('valid',1,'helm',3,'history');
            INSERT INTO v106_equipped_instances VALUES (1,'head','valid');
        ''')
        _check_all_accounts(conn, catalog)
        verify(True, 'sprawny v107 odrzucono')
        # Another account has only an orphaned shadow slot, no inventory,
        # no physical copy and no worn legacy row. The old startup audit
        # never enumerated that account.
        conn.execute("INSERT INTO v106_equipped_instances VALUES(22,'head','missing')")
        try:
            _check_account(conn, 22, catalog)
        except RuntimeError:
            verify(True, 'single-account audit did not detect orphan')
        else:
            raise AssertionError('Orphan unnoticed by single-account audit')
        try:
            _check_all_accounts(conn, catalog)
        except RuntimeError:
            verify(True, 'startup failed to detect shadow-only account')
        else:
            raise AssertionError('Orphan unnoticed by startup audit')
        conn.execute('DELETE FROM v106_equipped_instances WHERE account_id=22')
        _check_all_accounts(conn, catalog)
        verify(True, 'healthy state did not restart after removal of synthetic orphan')
        verify(conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok',
               'synthetic SQLite integrity')
    source = (ROOT / 'server/mud_server.py').read_text('utf-8')
    verify('activate_v108_production_ledger' not in source, 'unwanted EQ2 activated')
    verify('activate_production_ledger' in source, 'existing v107 protection removed')
    for name, token in (
        ('player/session_mixins/dungeon_progression.py', 'use_giant_fortress_portal_v10800'),
        ('player/session_mixins/movement.py', 'dungeon_exit_destination'),
        ('player/session_mixins/quest_turnin.py', 'consume_quest_items_batch_v10800'),
        ('player/session_mixins/io_auth_character.py', 'character_creator'),
    ):
        verify(token in (ROOT / name).read_text('utf-8'), 'missing v108 fix: ' + name)
    return checks

if __name__ == '__main__':
    print('V108: ZACHOWANE KLASY/RASY/POZIOMY V107 I POPRAWKI V108:',
          run(), 'PASS; BEZ WDROZENIA', flush=True)
