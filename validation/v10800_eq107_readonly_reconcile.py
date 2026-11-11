# -*- coding: utf-8 -*-
"""Soulbound v108: read-only examination of 11 old v107 physical-EQ deficits.

No write to user SQLite or backups, no automatic recovery, no release approval.
SQLite read-only source/backups are snapshotted with backup API; trial writes take
place solely in TemporaryDirectory and are discarded when finished. This file
must not be imported by server startup or a deployment installer.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from hashlib import sha256
from pathlib import Path
import sqlite3
import sys
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class AuditBlocked(Exception):
    """Known, bounded refusal, without leaking account or item identifiers."""


class SlotAuditBlocked(AuditBlocked):
    """Blocked after an anonymous, read-only slot classification."""
    def __init__(self, counts):
        super().__init__('NIEZGODNE_SLOTY_EQ')
        self.counts = counts


def tables(conn):
    return {str(r[0]) for r in conn.execute('SELECT name FROM sqlite_master WHERE type="table"')}


def take_snapshot(path, dest):
    if not path.is_file() or path.is_symlink():
        raise AuditBlocked('BRAK_BAZY_LUB_DOWIAZANIE')
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)) as source:
        source.execute('PRAGMA query_only=ON')
        with closing(sqlite3.connect(dest)) as target:
            source.backup(target, pages=128, sleep=0.02)
            if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise AuditBlocked('BLEDNA_INTEGRALNOSC_SQLITE')


def locate_original_backup(game_path, conn):
    if 'v107_eq_production_cutover' not in tables(conn):
        raise AuditBlocked('BRAK_MIGRACJI_V107')
    records = conn.execute('SELECT cutover_version,backup_name FROM v107_eq_production_cutover').fetchall()
    if len(records) != 1 or records[0][0] != '107.00.0':
        raise AuditBlocked('NIEZGODNY_ZNACZNIK_V107')
    name = records[0][1]
    if not isinstance(name, str) or name in ('', '.', '..') or Path(name).name != name or '/' in name or '\\' in name:
        raise AuditBlocked('NIEBEZPIECZNA_NAZWA_BACKUPU')
    folder = (game_path.parent / 'backups').resolve(strict=True)
    located = folder / name
    if not located.is_file() or located.is_symlink() or located.resolve(strict=True).parent != folder:
        raise AuditBlocked('BRAK_BEZPIECZNEGO_BACKUPU_V107')
    return located


def equipment_catalog():
    # This package's exact game catalog, including generated equipment IDs.
    from world.dynamic_content import ITEMS
    gear = {str(item_id) for item_id, meta in ITEMS.items()
            if isinstance(meta, dict) and meta.get('type') in ('weapon', 'armor')}
    if not gear:
        raise AuditBlocked('PUSTY_KATALOG_EQ')
    return ITEMS, gear


def inventory(conn, gear):
    result = {}
    for aid, item, qty in conn.execute('SELECT account_id,item_id,quantity FROM inventory'):
        item = str(item)
        if item not in gear:
            continue
        key = (aid, item)
        if key in result or type(aid) is not int or aid < 1 or type(qty) is not int or qty < 0:
            raise AuditBlocked('BLEDNY_STAN_PLECAKA')
        result[key] = qty
    return result


def collect(conn, gear):
    needed = {'inventory', 'equipment', 'v106_item_instances',
              'v106_equipped_instances', 'v106_stored_instances', 'player_records_v03051'}
    if needed - tables(conn):
        raise AuditBlocked('NIEPELNY_SCHEMAT_EQ')
    bag = inventory(conn, gear)
    instances = defaultdict(list)
    identities = {}
    for uid, aid, iid, stage, origin in conn.execute(
            'SELECT instance_id,account_id,item_id,evolution_stage,origin FROM v106_item_instances'):
        if (not isinstance(uid, str) or not uid or uid in identities or
            type(aid) is not int or aid < 1 or type(stage) is not int or stage < 0 or
            not isinstance(origin, str) or not origin):
            raise AuditBlocked('NIEPRAWIDLOWE_FIZYCZNE_KOPIE')
        key = (aid, str(iid))
        identities[uid] = (key, stage, origin)
        instances[key].append((uid, stage, origin))
    stored = set()
    for uid, aid in conn.execute('SELECT instance_id,account_id FROM v106_stored_instances'):
        if uid in stored or uid not in identities or identities[uid][0][0] != aid:
            raise AuditBlocked('NIEZGODNE_MAGAZYNY')
        stored.add(uid)
    worn = {}
    for aid, slot, iid in conn.execute('SELECT account_id,slot,item_id FROM equipment'):
        if str(iid) not in gear:
            continue
        key = (aid, str(slot))
        if key in worn:
            raise AuditBlocked('POWTORZONY_SLOT')
        worn[key] = str(iid)
    bindings = {}
    bound_ids = set()
    for aid, slot, uid in conn.execute('SELECT account_id,slot,instance_id FROM v106_equipped_instances'):
        key = (aid, str(slot))
        if (key in bindings or uid in bound_ids or uid not in identities or
            identities[uid][0] != (aid, worn.get(key)) or uid in stored):
            raise AuditBlocked('NIEZGODNE_SLOTY_EQ')
        bindings[key] = uid
        bound_ids.add(uid)
    if worn.keys() != bindings.keys():
        raise AuditBlocked('NIEZGODNE_SLOTY_EQ')
    physical = Counter()
    for uid, (key, _stage, _origin) in identities.items():
        if uid not in stored and key[1] in gear:
            physical[key] += 1
    return bag, instances, identities, stored, worn, physical


def clean_legacy_history(conn, key):
    aid, iid = key
    result = conn.execute('SELECT value FROM player_records_v03051 '
                          'WHERE account_id=? AND record_key=?',
                          (aid, 'eq_evolution_v10500:' + iid)).fetchone()
    if result and str(result[0]).strip() not in ('0', '+0', '-0'):
        return False
    known = tables(conn)
    for name in ('v106_manual_evolution_allocations', 'v106_evolution_migration_issues',
                 'equipment_reforges', 'equipment_upgrades_v03042',
                 'equipment_runes_v0925', 'equipment_socket_bonus_v03114',
                 'tech_set_upgrades_v0320'):
        if name in known and conn.execute(
                'SELECT 1 FROM "' + name + '" WHERE account_id=? AND item_id=? LIMIT 1', key).fetchone():
            return False
    return True


def unchanged_tables_fingerprint(conn):
    """Protect ALL data tables except the one receiving synthetic instance rows."""
    digest = sha256()
    for table in sorted(tables(conn) - {'v106_item_instances'}):
        digest.update(table.encode('utf-8'))
        sql = 'SELECT * FROM "' + table.replace('"', '""') + '"'
        for row in conn.execute(sql):
            raw = repr(tuple(row)).encode('utf-8', 'backslashreplace')
            digest.update(len(raw).to_bytes(8, 'big'))
            digest.update(raw)
    return digest.hexdigest()


def trial_reconcile(now, old, preview, catalog, gear):
    from systems.v10700_live_equipment import _check_all_accounts
    from validation.v10800_v107_drift_details_ro import classify_snapshot
    out = Counter()
    with closing(sqlite3.connect(now)) as current, closing(sqlite3.connect(old)) as baseline:
        if 'v107_eq_production_cutover' in tables(baseline):
            raise AuditBlocked('BACKUP_NIE_SPRZED_V107')
        initial = inventory(baseline, gear)
        bag, ledger, ids, stored, worn, physical = collect(current, gear)
        out['KOPIE_FIZYCZNE'] = len(ids)
        out['SLOTY_ZGODNE'] = len(worn)
        deficits = []
        for key in bag.keys() | physical.keys():
            missing = bag.get(key, 0) - physical.get(key, 0)
            if missing > 0:
                deficits.append((key, missing))
                out['GRUPY_NIEDOBORU'] += 1
                out['BRAKUJACE_KOPIE'] += missing
            elif missing < 0:
                out['GRUPY_NADMIARU'] += 1
                out['NADMIAROWE_KOPIE'] += -missing
        candidates = []
        for key, missing in deficits:
            rows = ledger.get(key, ())
            no_worn = not any(aid == key[0] and item == key[1]
                              for (aid, _slot), item in worn.items())
            no_stored = not any(uid in stored for uid, _stage, _origin in rows)
            stage_zero = all(type(stage) is int and stage == 0 for _uid, stage, _origin in rows)
            increase_since_cutover = bag[key] > initial.get(key, 0)
            if no_worn and no_stored and stage_zero and increase_since_cutover and clean_legacy_history(current, key):
                candidates.append((key, missing))
                out['BEZ_SLADOW_ULEPSZEN_GRUPY'] += 1
                out['BEZ_SLADOW_ULEPSZEN_SZTUKI'] += missing
            else:
                out['NIEPEWNE_GRUPY'] += 1
                out['NIEPEWNE_SZTUKI'] += missing
        # A fail-closed rule based on the ACTUAL previously observed case.
        # Never guess on changed inventory, equipped/stored/evolved pieces.
        if (out['GRUPY_NIEDOBORU'] != 11 or out['BRAKUJACE_KOPIE'] != 11 or
            out['GRUPY_NADMIARU'] or out['NADMIAROWE_KOPIE'] or
            out['BEZ_SLADOW_ULEPSZEN_GRUPY'] != 11 or
            out['BEZ_SLADOW_ULEPSZEN_SZTUKI'] != 11 or out['NIEPEWNE_GRUPY']):
            return out, False
        before = classify_snapshot(current, catalog)
        if (before['deficit_copies'] != 11 or before['surplus_copies'] or
            before['worn_slot_mismatches'] or before['invalid_physical_rows'] or
            before['orphan_worn_ids'] or before['orphan_stored_ids'] or
            before['unrecognized_physical_templates']):
            return out, False
        expected_existing = set(ids)

    # Trial only on the third detached temp SQLite file; no run-time connection.
    with closing(sqlite3.connect(preview)) as trial:
        digest_before = unchanged_tables_fingerprint(trial)
        original_ids = {r[0] for r in trial.execute('SELECT instance_id FROM v106_item_instances')}
        if original_ids != expected_existing:
            raise AuditBlocked('ROZNICA_MIEDZY_KOPIAMI_TESTOWYMI')
        trial.execute('PRAGMA foreign_keys=ON')
        trial.execute('SAVEPOINT sb107_eq_preview_only')
        try:
            for key, n in candidates:
                for _ in range(n):
                    trial.execute('INSERT INTO v106_item_instances '
                                  '(instance_id,account_id,item_id,evolution_stage,origin) '
                                  'VALUES (?,?,?,0,?)',
                                  (str(uuid4()), key[0], key[1], 'v108_temp_preview_only'))
            _check_all_accounts(trial, catalog)
            after = classify_snapshot(trial, catalog)
            if (after['deficit_copies'] or after['surplus_copies'] or
                after['worn_slot_mismatches'] or after['orphan_worn_ids'] or
                after['orphan_stored_ids'] or after['invalid_physical_rows']):
                raise AuditBlocked('NIEZGODNA_KONTROLA_PO_PROBIE')
            if trial.execute('PRAGMA foreign_key_check').fetchone() is not None:
                raise AuditBlocked('NIEZGODNE_KLUCZE_OBCE')
            if trial.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise AuditBlocked('NIEZGODNA_INTEGRALNOSC_PO_PROBIE')
            if unchanged_tables_fingerprint(trial) != digest_before:
                raise AuditBlocked('ZMIENIONE_INNE_TABELE_W_PROBIE')
            if not original_ids.issubset({r[0] for r in trial.execute('SELECT instance_id FROM v106_item_instances')}):
                raise AuditBlocked('UTRACONO_STARE_IDENTYFIKATORY')
            if (trial.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]
                != len(original_ids) + 11):
                raise AuditBlocked('ZLA_LICZBA_FIZYCZNYCH_KOPII')
            out['KOPIE_DODANE_TYLKO_DO_PROBY'] = 11
            out['TEST_KOPII_PASS'] = 1
        finally:
            # Always discard the entire trial including rows and UUIDs.
            trial.execute('ROLLBACK TO SAVEPOINT sb107_eq_preview_only')
            trial.execute('RELEASE SAVEPOINT sb107_eq_preview_only')
    return out, True


def run(game_path, catalog, gear):
    game = Path(game_path).expanduser().resolve(strict=True)
    dbfile = game / 'soulbound.db'
    if not dbfile.is_file():
        raise AuditBlocked('BRAK_PLIKU_SOULBOUND_DB')
    with tempfile.TemporaryDirectory(prefix='sb108_eq107_tylko_kopia_') as directory:
        path = Path(directory)
        now, old, preview = (path / name for name in ('teraz.sqlite', 'sprzed_v107.sqlite', 'proba.sqlite'))
        take_snapshot(dbfile, now)
        with closing(sqlite3.connect(now)) as conn:
            original = locate_original_backup(dbfile, conn)
        take_snapshot(original, old)
        take_snapshot(now, preview)
        try:
            counts, result = trial_reconcile(now, old, preview, catalog, gear)
        except AuditBlocked as error:
            if str(error) != 'NIEZGODNE_SLOTY_EQ':
                raise
            # Only the detached snapshot, never the running SQLite database.
            from validation.v10800_eq107_slot_details_ro import summarize
            with closing(sqlite3.connect(now)) as detached, closing(sqlite3.connect(old)) as baseline:
                counts = summarize(detached, gear)
                try:
                    from validation.v10800_eq107_source_diagnostic_ro import compare_snapshots
                    counts.update(compare_snapshots(detached, baseline, gear))
                    counts['POROWNANIE_Z_BACKUPEM_DOSTEPNE'] = 1
                except (ValueError, sqlite3.DatabaseError):
                    counts['POROWNANIE_Z_BACKUPEM_DOSTEPNE'] = 0
                raise SlotAuditBlocked(counts) from None
    return counts, result


def main(argv=None):
    parser = argparse.ArgumentParser(description='Soulbound: test 11 brakujacych kopii tylko w TEMP.')
    parser.add_argument('--root', default=r'C:\Soulbound-MUD', help='Folder z aktualna v107')
    args = parser.parse_args(argv)
    print('Soulbound v108 / analiza 11 rozbieznosci starego EQ v107', flush=True)
    print('TYLKO ODCZYT PRODUKCJI. Bez modyfikacji bazy i bez plikow wynikowych.', flush=True)
    try:
        catalog, gear = equipment_catalog()
        counts, success = run(args.root, catalog, gear)
        for key in sorted(counts):
            print(f'{key}: {counts[key]}', flush=True)
        if success:
            print('WYNIK: PROBA_NA_ODLACZONEJ_KOPII_PASS', flush=True)
            print('To NIE jest zgoda na wdrozenie ani automatyczna naprawa bazy.', flush=True)
            return 0
        print('WYNIK: WYMAGA_WERYFIKACJI_STAN_SIE_ZMIENIL_LUB_NIEPEWNY', flush=True)
        return 2
    except Exception as exc:
        if isinstance(exc, AuditBlocked):
            code = str(exc)
        else:
            code = 'NIEPRZEWIDZIANY_BLAD_' + type(exc).__name__.upper()
        if isinstance(exc, SlotAuditBlocked):
            print('ANONIMOWA DIAGNOZA SLOTOW (liczniki; kategorie moga sie pokrywac):', flush=True)
            for key, value in exc.counts.items():
                print(f'{key}: {value}', flush=True)
        print('WYNIK: BLOKADA_' + code, flush=True)
        print('Brak zgody na wdrozenie. Produkcja pozostaje nietknieta.', flush=True)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
