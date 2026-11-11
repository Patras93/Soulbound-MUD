# -*- coding: utf-8 -*-
"""Offline synthetic v108 EQ craft-variant restore and quarantine safety regression.

No real player files, no server, no writes outside in-memory SQLite.
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from uuid import uuid4
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from hashlib import sha256

from validation.v10800_eq_rebuild_copy_regression import CAT, model
from validation.v10800_eq_rebuild_copy import (
    RebuildBlocked, _safe_unlisted_crafted_copies, rebuild_clone,
    _snapshot_other_tables, run as run_on_files,
    _legacy_crafted_item_in_other_routes,
)
from systems.v10800_eq_dynamic_catalog import restore_known_crafted_equipment
from systems.crafting_quality import ensure_crafting_quality_variant_v0332
from world.dynamic_content import ITEMS

ITEM = 'craftq_normal_none_jewel_iron_ring'


def _example():
    current, old = model()
    uid1, uid2 = str(uuid4()), str(uuid4())
    current.executemany('INSERT INTO v106_item_instances VALUES (?,?,?,?,?)', [
        (uid1, 1, ITEM, 0, 'v106_inventory'),
        (uid2, 1, ITEM, 0, 'v106_inventory'),
    ])
    current.commit()
    catalog = {**CAT, ITEM: ITEMS[ITEM]}
    return current, old, catalog, (uid1, uid2)


def _blocked_from_routes(mutate):
    current, old, catalog, ids = _example()
    with closing(current), closing(old):
        mutate(current)
        current.commit()
        before = tuple(current.iterdump())
        assert _legacy_crafted_item_in_other_routes(current, ITEM)
        try:
            rebuild_clone(current, old, catalog, confirm_detached_copy=True)
        except RebuildBlocked as exc:
            assert str(exc) == 'STRUKTURA_FIZYCZNA_NIEZGODNA'
        else:
            raise AssertionError('Untracked legacy item route improperly quarantined')
        assert tuple(current.iterdump()) == before
        assert not current.execute("SELECT 1 FROM v106_stored_instances WHERE storage_kind='v108_rebuild_quarantine'").fetchone()


def _replay_user_aggregate_counts():
    """Simulate 20 wrongly bound slots + 36 missing copies + two inert rings."""
    current, baseline = model()
    # Build a fresh synthetic v107-like ledger with 20 distinct gear templates.
    for conn in (current, baseline):
        conn.execute('DELETE FROM inventory')
        conn.execute('DELETE FROM equipment')
    current.execute('DELETE FROM v106_item_instances')
    current.execute('DELETE FROM v106_equipped_instances')
    catalog = {**CAT, ITEM: ITEMS[ITEM],
               **{f'gear_{n:02d}': {'type':'armor', 'slot':f'slot_{n:02d}'}
                  for n in range(20)},
               'new_loot': {'type':'weapon'}}
    identities = []
    for n in range(20):
        iid = f'gear_{n:02d}'
        slot = f'slot_{n:02d}'
        uid = str(uuid4())
        identities.append(uid)
        for conn in (current, baseline):
            conn.execute('INSERT INTO inventory VALUES(1,?,1)',(iid,))
        baseline.execute('INSERT INTO equipment VALUES(1,?,?)',(slot,iid))
        current.execute('INSERT INTO equipment VALUES(1,?,?)',
                        (slot,f'gear_{(n+1)%20:02d}'))
        current.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
                        (uid,1,iid,0,'v106_inventory'))
        current.execute('INSERT INTO v106_equipped_instances VALUES(?,?,?)',
                        (1,slot,uid))
    current.execute('INSERT INTO inventory VALUES(1,?,?)',('new_loot',36))
    rings = [str(uuid4()),str(uuid4())]
    for uid in rings:
        current.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
                        (uid,1,ITEM,0,'v106_inventory'))
    current.commit(); baseline.commit()
    with closing(current),closing(baseline):
        immutable_before = _snapshot_other_tables(current)
        original = {r[0]:tuple(r) for r in current.execute('SELECT * FROM v106_item_instances')}
        report = rebuild_clone(current,baseline,catalog,confirm_detached_copy=True)
        assert (report['SLOTY_PRZEBUDOWANE'],report['KOPIE_DODANE_W_KOPII_TESTOWEJ'],
                report['ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE']) == (20,36,2),report
        assert _snapshot_other_tables(current) == immutable_before
        after = {r[0]:tuple(r) for r in current.execute('SELECT * FROM v106_item_instances')}
        assert all(after[k] == v for k,v in original.items())
        assert len(after)-len(original) == 36
        assert current.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        report2 = rebuild_clone(current,baseline,catalog,confirm_detached_copy=True)
        assert (report2['SLOTY_PRZEBUDOWANE'], report2['KOPIE_DODANE_W_KOPII_TESTOWEJ'],
                report2['ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE']) == (0,0,0)
    return 7


def _replay_file_based_backup():
    """Real file snapshot, real game catalog, no player data or live server."""
    gear_ids = [k for k,v in ITEMS.items()
                if isinstance(v, dict) and v.get('type') in ('weapon','armor')
                and k != ITEM][:21]
    assert len(gear_ids) == 21
    current, old = model()
    with closing(current), closing(old), TemporaryDirectory(prefix='sb108_craft_on_disk_') as home:
        for db in (current, old):
            db.execute('DELETE FROM inventory')
            db.execute('DELETE FROM equipment')
        current.execute('DELETE FROM v106_equipped_instances')
        current.execute('DELETE FROM v106_item_instances')
        originals = []
        for n, iid in enumerate(gear_ids[:20]):
            slot = f'fixture_slot_{n:02d}'
            uid = str(uuid4())
            originals.append(uid)
            for db in (current, old):
                db.execute('INSERT INTO inventory VALUES(1,?,1)', (iid,))
            old.execute('INSERT INTO equipment VALUES(1,?,?)',(slot,iid))
            current.execute('INSERT INTO equipment VALUES(1,?,?)',
                            (slot, gear_ids[(n+1)%20]))
            current.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
                            (uid,1,iid,0,'v106_inventory'))
            current.execute('INSERT INTO v106_equipped_instances VALUES(?,?,?)',
                            (1,slot,uid))
        current.execute('INSERT INTO inventory VALUES(1,?,36)',(gear_ids[20],))
        two = [str(uuid4()),str(uuid4())]
        for uid in two:
            current.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
                            (uid,1,ITEM,0,'v106_inventory'))
        current.commit(); old.commit()
        home = Path(home)
        game = home / 'game'; game.mkdir()
        (game/'backups').mkdir()
        output = home / 'test_only'
        with closing(sqlite3.connect(game/'soulbound.db')) as dest:
            current.backup(dest)
        with closing(sqlite3.connect(game/'backups'/'old.sqlite')) as dest:
            old.backup(dest)
        db_before=sha256((game/'soulbound.db').read_bytes()).hexdigest()
        backup_before=sha256((game/'backups'/'old.sqlite').read_bytes()).hexdigest()
        gear=set(gear_ids[:21])|{ITEM}
        with patch('validation.v10800_eq_rebuild_copy.equipment_catalog',return_value=(ITEMS,gear)):
            result=run_on_files(game,output)
        assert (result['SLOTY_PRZEBUDOWANE'],result['KOPIE_DODANE_W_KOPII_TESTOWEJ'],
                result['ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE']) == (20,36,2),result
        assert sha256((game/'soulbound.db').read_bytes()).hexdigest()==db_before
        assert sha256((game/'backups'/'old.sqlite').read_bytes()).hexdigest()==backup_before
        with closing(sqlite3.connect(output/'REBUILT_TEST_ONLY.sqlite')) as rebuilt:
            assert rebuilt.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert rebuilt.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==58
            assert rebuilt.execute('SELECT COUNT(*) FROM v106_stored_instances WHERE storage_kind=?',
                                   ('v108_rebuild_quarantine',)).fetchone()[0]==2
            assert rebuilt.execute('SELECT COUNT(*) FROM v106_equipped_instances').fetchone()[0]==20
        return 8


def run():
    count = 0
    assert ensure_crafting_quality_variant_v0332(ITEM) is ITEMS[ITEM]
    assert ITEMS[ITEM].get('type') == 'armor'
    assert ITEMS[ITEM].get('slot') == 'ring'
    assert ITEMS[ITEM].get('crafted_base_id_v03054') == 'jewel_iron_ring'
    count += 1
    with closing(sqlite3.connect(':memory:')) as probe:
        for table in ('inventory', 'equipment', 'v106_item_instances'):
            probe.execute(f'CREATE TABLE {table} (item_id TEXT)')
        probe.execute('INSERT INTO v106_item_instances VALUES (?)', (ITEM,))
        # The catalog uses exactly the shared game ITEMS registry.
        assert restore_known_crafted_equipment(probe, ITEMS) == 0  # already restored
        count += 1
    cur, old, catalog, ids = _example()
    with closing(cur), closing(old):
        assert _safe_unlisted_crafted_copies(cur, old, catalog) == set(ids)
        original_rows = sorted(cur.execute('SELECT * FROM v106_item_instances'))
        result = rebuild_clone(cur, old, catalog, confirm_detached_copy=True)
        assert result['ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE'] == 2
        assert result['SLOTY_PRZEBUDOWANE'] == 1
        assert result['KOPIE_DODANE_W_KOPII_TESTOWEJ'] == 2
        after = dict((row[0], row) for row in cur.execute('SELECT * FROM v106_item_instances'))
        assert all(after[row[0]] == row for row in original_rows)
        assert len(cur.execute('SELECT instance_id FROM v106_stored_instances WHERE storage_kind=?',
                               ('v108_rebuild_quarantine',)).fetchall()) == 2
        assert cur.execute('SELECT COUNT(*) FROM inventory WHERE item_id=?', (ITEM,)).fetchone()[0] == 0
        assert rebuild_clone(cur, old, catalog, confirm_detached_copy=True)['ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE'] == 0
        count += 6
    _blocked_from_routes(lambda c: c.executescript('''
        CREATE TABLE bank_items(item_id TEXT, quantity INTEGER);
        INSERT INTO bank_items VALUES('craftq_normal_none_jewel_iron_ring',1);
    ''')); count += 1
    _blocked_from_routes(lambda c: c.executescript('''
        CREATE TABLE profession_storage(item_id TEXT, quantity INTEGER);
        INSERT INTO profession_storage VALUES('craftq_normal_none_jewel_iron_ring',2);
    ''')); count += 1
    _blocked_from_routes(lambda c: c.executescript('''
        CREATE TABLE player_mail_v03051(attachment_item_id TEXT,attachment_kind TEXT,attachment_claimed INTEGER);
        INSERT INTO player_mail_v03051 VALUES('craftq_normal_none_jewel_iron_ring','item',0);
    ''')); count += 1
    _blocked_from_routes(lambda c: c.executescript('''
        CREATE TABLE player_housing_v03051(storage_json TEXT);
        INSERT INTO player_housing_v03051 VALUES('{"craftq_normal_none_jewel_iron_ring":2}');
    ''')); count += 1
    _blocked_from_routes(lambda c: c.executescript('''
        CREATE TABLE housing_rooms_v03052(chest_json TEXT);
        INSERT INTO housing_rooms_v03052 VALUES('{"craftq_normal_none_jewel_iron_ring":1}');
    ''')); count += 1
    _blocked_from_routes(lambda c: c.executescript('''
        CREATE TABLE player_housing_v03051(storage_json TEXT);
        INSERT INTO player_housing_v03051 VALUES('broken-json');
    ''')); count += 1
    cur, old, catalog, ids = _example()
    with closing(cur), closing(old):
        cur.executescript('''
            CREATE TABLE player_mail_v03051(attachment_item_id TEXT,attachment_kind TEXT,attachment_claimed INTEGER);
            INSERT INTO player_mail_v03051 VALUES('craftq_normal_none_jewel_iron_ring','item',1);
        ''')
        assert not _legacy_crafted_item_in_other_routes(cur, ITEM)
        assert _safe_unlisted_crafted_copies(cur, old, catalog) == set(ids)
        count += 2
    # The exception is limited to exactly two historic IRON rings. Neither
    # three otherwise harmless rings nor another fabricated craft template
    # may be auto-parked based solely on an ID prefix.
    cur, old, catalog, ids = _example()
    with closing(cur),closing(old):
        cur.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
                    (str(uuid4()),1,ITEM,0,'v106_inventory'))
        cur.commit()
        before=tuple(cur.iterdump())
        assert not _safe_unlisted_crafted_copies(cur,old,catalog)
        blocked = False
        try:
            rebuild_clone(cur,old,catalog,confirm_detached_copy=True)
        except RebuildBlocked:
            blocked = True
        assert blocked, 'Three unlisted craft copies auto-parked'
        assert tuple(cur.iterdump())==before
        count += 3
    cur, old, catalog, ids = _example()
    with closing(cur),closing(old):
        alternate = 'craftq_normal_none_jewel_silver_ring'
        catalog[alternate] = {'type':'armor','slot':'ring',
                              'crafted_base_id_v03054':'jewel_silver_ring'}
        cur.execute('UPDATE v106_item_instances SET item_id=? WHERE item_id=?',
                    (alternate,ITEM))
        cur.commit()
        assert not _safe_unlisted_crafted_copies(cur,old,catalog)
        blocked = False
        try:
            rebuild_clone(cur,old,catalog,confirm_detached_copy=True)
        except RebuildBlocked:
            blocked = True
        assert blocked, 'Unrelated craftq prefix accepted'
        count += 2
    count += _replay_user_aggregate_counts()
    count += _replay_file_based_backup()
    print(f'V108 DYNAMIC CRAFT EQ REBUILD: {count}/{count} PASS, SOURCE DB NOT USED')
    return count

if __name__ == '__main__':
    run()
