# -*- coding: utf-8 -*-
"""Soulbound v108: offline conservative EQ ledger rebuild, on a detached copy ONLY.

The v107 authoritative equipment+inventory are not rewritten. Existing physical
identity rows and per-copy evolution are never edited or deleted. Historical
pre-cutover backup gates new stage-zero physical copies. Ambiguous evolved
bindings fail closed. No production activation, no installers, no in-place DB.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import closing
from hashlib import sha256
from pathlib import Path
import os
import sqlite3
import sys
import tempfile
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.v10800_eq107_readonly_reconcile import (
    AuditBlocked, equipment_catalog, locate_original_backup, take_snapshot, tables,
)
from validation.v10800_v107_drift_details_ro import classify_snapshot
from systems.equipment_shadow_slots_v10600 import _check_account
from systems.v10800_eq_physical_routes import physical_route_conflicts
from systems.v10800_eq_restore_rehearsal import _fields


class RebuildBlocked(AuditBlocked):
    def __init__(self, code, counters=None):
        super().__init__(code)
        # Aggregate-only. Never attach owner, item or instance identifiers.
        self.counters = dict(counters or {})


def _fail(code, counters=None):
    raise RebuildBlocked(code, counters)


def _snapshot_other_tables(conn):
    """Portable order-insensitive fingerprint of EVERY non-rebuilt table.

    No rows or IDs escape; include sqlite_sequence, BLOBs and arbitrary user
    tables. Row multiplicities are retained using a commutative 256-bit sum.
    """
    excluded = {'v106_item_instances', 'v106_equipped_instances', 'v106_stored_instances'}
    h = sha256(b'SB-v108-nonrebuild-tables\0')
    for record in sorted(conn.execute('SELECT type,name,tbl_name,sql FROM sqlite_master'), key=repr):
        h.update(_fields(*record))
    total = 0
    for table in sorted(tables(conn) - excluded):
        name = '"' + table.replace('"', '""') + '"'
        count = 0
        summed = 0
        for row in conn.execute('SELECT * FROM ' + name):
            digest = int.from_bytes(sha256(_fields(*row)).digest(), 'big')
            summed = (summed + digest) % (1 << 256)
            count += 1
        total += count
        h.update(_fields(table, count))
        h.update(summed.to_bytes(32,'big'))
    return h.hexdigest(), total


def _collect_equipment(conn, gear):
    eq = {}
    for aid, slot, iid in conn.execute('SELECT account_id,slot,item_id FROM equipment'):
        if type(aid) is not int or aid <= 0 or not isinstance(slot, str) or not slot:
            _fail('NIEPRAWIDLOWY_SLOT_LUB_WLASCICIEL')
        if str(iid) not in gear:
            # Ignore non-EQ only if it really is a known non-gear template;
            # the game's regular equipment table is expected to contain gear.
            _fail('NIEZNANY_PRZEDMIOT_W_SLOCIE')
        key = (aid, slot)
        if key in eq:
            _fail('ZDUPLIKOWANE_SLOTY')
        eq[key] = str(iid)
    return eq


def _collect_bags(conn, gear):
    bag = {}
    for aid, iid, qty in conn.execute('SELECT account_id,item_id,quantity FROM inventory'):
        if str(iid) not in gear:
            continue
        key = (aid, str(iid))
        if key in bag or type(aid) is not int or aid <= 0 or type(qty) is not int or qty < 0:
            _fail('NIEPRAWIDLOWY_STAN_PLECAKA')
        bag[key] = qty
    return bag


def _isolated_nongear_copies(conn, catalog):
    """Classify out-of-EQ physical rows; never expose owners or item IDs.

    An inert known non-gear copy can be retained, not converted/deleted.
    Unknown IDs, equipped/stored/evolved copies, and legacy upgrade history
    are always blockers. No bypass of deployment or live runtime guards.
    """
    from uuid import UUID
    from validation.v10800_eq107_readonly_reconcile import clean_legacy_history
    gear = {str(k) for k, v in catalog.items()
            if isinstance(v, dict) and v.get('type') in ('armor', 'weapon')}
    worn_uids = {uid for (uid,) in conn.execute(
        'SELECT instance_id FROM v106_equipped_instances')}
    stored_uids = {uid for (uid,) in conn.execute(
        'SELECT instance_id FROM v106_stored_instances')}
    active = {(a, str(i)) for a, i in conn.execute(
        'SELECT account_id,item_id FROM equipment')}
    result = Counter()
    eligible = set()
    version_by_origin = {
        'legacy_unique': 5, 'manual_legacy_review': 5,
        'v106_inventory': 4, 'v108_recovered_stage0': 4,
    }
    for uid, aid, iid, stage, origin in conn.execute(
        'SELECT instance_id,account_id,item_id,evolution_stage,origin '
        'FROM v106_item_instances'):
        iid = str(iid)
        if iid in gear:
            continue
        result['TEMPLATY_FIZYCZNE_POZA_EQ'] += 1
        meta = catalog.get(iid)
        if not isinstance(meta, dict):
            result['SZABLON_NIEOBECNY_W_KATALOGU'] += 1
            continue
        result['ZNANY_TYP_NIESPRZETOWY'] += 1
        unsafe = False
        if uid in worn_uids or (aid, iid) in active:
            result['NIESPRZETOWY_POWIAZANY_Z_ZALOZONYM_EQ'] += 1
            unsafe = True
        if uid in stored_uids:
            result['NIESPRZETOWY_W_MAGAZYNIE'] += 1
            unsafe = True
        if stage != 0:
            result['NIESPRZETOWY_Z_EWOLUCJA'] += 1
            unsafe = True
        if not clean_legacy_history(conn, (aid, iid)):
            result['NIESPRZETOWY_Z_HISTORIA_ULEPSZEN'] += 1
            unsafe = True
        try:
            v = UUID(uid)
            valid = (str(v) == uid and v.version == version_by_origin.get(origin))
        except (TypeError, ValueError, AttributeError):
            valid = False
        if not valid:
            result['NIESPRZETOWY_BLEDNA_TOZSAMOSC'] += 1
            unsafe = True
        if not unsafe:
            eligible.add(uid)
            result['NIESPRZETOWY_ODIZOLOWANY_ZACHOWANY'] += 1
    return eligible, dict(result)



def _legacy_crafted_item_in_other_routes(conn, iid):
    """Fail-closed check for craft items still held outside inventory/EQ.

    A physical UUID with no bag or worn binding is not automatically an
    abandoned item: old bank, profession storage, pending mail or housing
    may still retain a template-level claim. This reads only the detached
    snapshot and emits no owner, item identifier or message contents.
    """
    import json
    present = tables(conn)

    def columns(table):
        return {str(row[1]) for row in conn.execute(
            'PRAGMA table_info("' + table + '")')}

    for table in ('bank_items', 'profession_storage'):
        if table not in present:
            continue
        if not {'item_id', 'quantity'} <= columns(table):
            return True  # Schema mismatch: don't infer that an item is free.
        if conn.execute('SELECT 1 FROM "' + table + '" WHERE item_id=? LIMIT 1',
                        (iid,)).fetchone():
            return True  # Even a malformed/zero quantity is ambiguous.

    if 'player_mail_v03051' in present:
        needed = {'attachment_item_id', 'attachment_kind', 'attachment_claimed'}
        if not needed <= columns('player_mail_v03051'):
            return True
        if conn.execute('SELECT 1 FROM player_mail_v03051 '
                "WHERE attachment_item_id=? AND attachment_kind='item' "
                'AND COALESCE(attachment_claimed,0) != 1 LIMIT 1',
                (iid,)).fetchone():
            return True

    for table, field in (('player_housing_v03051', 'storage_json'),
                         ('housing_rooms_v03052', 'chest_json')):
        if table not in present:
            continue
        if field not in columns(table):
            return True
        for (raw,) in conn.execute('SELECT "' + field + '" FROM "' + table + '"'):
            try:
                box = json.loads(raw or '{}')
                if not isinstance(box, dict):
                    return True
            except (TypeError, ValueError):
                return True
            # Any existing entry is ambiguous, including invalid/zero qty.
            if iid in box:
                return True
    return False


def _safe_unlisted_crafted_copies(conn, previous, catalog):
    """Park only the two specifically diagnosed legacy ring ghosts on a COPY.

    On the COPY ONLY, these original IDs may be parked in a separate held
    route so they do not become invented inventory items. All other physical
    extras remain hard blockers. The original rows are NEVER edited/deleted.
    """
    from uuid import UUID
    from validation.v10800_eq107_readonly_reconcile import clean_legacy_history
    worn = {u for (u,) in conn.execute('SELECT instance_id FROM v106_equipped_instances')}
    stored = {u for (u,) in conn.execute('SELECT instance_id FROM v106_stored_instances')}
    owned = {(a, str(i)): q for a, i, q in conn.execute(
        'SELECT account_id,item_id,quantity FROM inventory')}
    now_worn_templates = {(a, str(i)) for a, i in conn.execute(
        'SELECT account_id,item_id FROM equipment')}
    old_worn_templates = {(a, str(i)) for a, i in previous.execute(
        'SELECT account_id,item_id FROM equipment')}
    previously = {(a, str(i)): q for a, i, q in previous.execute(
        'SELECT account_id,item_id,quantity FROM inventory')}
    result = set()
    other_routes = {}
    # The user's real v107 diagnostic proved precisely two copies of this
    # template, not a general rule for abandoned crafting loot. Broadly
    # parking all unused craftq_* equipment would hide unrelated data loss.
    isolated_ring = 'craftq_normal_none_jewel_iron_ring'
    if conn.execute('SELECT COUNT(*) FROM v106_item_instances WHERE item_id=?',
                    (isolated_ring,)).fetchone()[0] != 2:
        return result
    origin_versions = {'legacy_unique':5,'manual_legacy_review':5,
                       'v106_inventory':4,'v108_recovered_stage0':4}
    for uid, aid, iid, stage, origin in conn.execute(
            'SELECT instance_id,account_id,item_id,evolution_stage,origin FROM v106_item_instances'):
        iid = str(iid)
        item = catalog.get(iid)
        if not (iid == isolated_ring and isinstance(item,dict)
                and item.get('type') == 'armor' and item.get('slot') == 'ring'
                and item.get('crafted_base_id_v03054') == 'jewel_iron_ring'):
            continue
        key = (aid, iid)
        if iid not in other_routes:
            other_routes[iid] = _legacy_crafted_item_in_other_routes(conn, iid)
        if (other_routes[iid] or uid in worn or uid in stored or stage != 0
                or type(aid) is not int or aid <= 0
                or owned.get(key,0) != 0 or previously.get(key,0) != 0
                or key in now_worn_templates or key in old_worn_templates
                or not clean_legacy_history(conn,key)):
            continue
        try:
            valid = isinstance(uid, str) and str(UUID(uid)) == uid and UUID(uid).version == origin_versions.get(origin)
        except (TypeError, ValueError, AttributeError):
            valid = False
        if valid:
            result.add(uid)
    return result

def rebuild_clone(conn, previous, catalog, *, confirm_detached_copy=False):
    """Rebuild on a disposable transaction, refuse every ambiguous evolution.

    Returns aggregate counts; the caller owns a COPY, never a live connection.
    """
    if confirm_detached_copy is not True:
        _fail('WYMAGANA_POTWIERDZONA_ODLACZONA_KOPIA')
    required = {'inventory', 'equipment', 'v106_item_instances',
                'v106_equipped_instances', 'v106_stored_instances',
                'player_records_v03051', 'v107_eq_production_cutover'}
    if required - tables(conn) or not {'inventory','equipment'} <= tables(previous):
        _fail('NIEKOMPLETNY_SCHEMAT')
    gear = {str(k) for k,v in catalog.items() if isinstance(v,dict)
            and v.get('type') in ('armor','weapon')}
    if not gear:
        _fail('PUSTY_KATALOG_EQ')
    if previous.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        _fail('USZKODZONY_BACKUP_SPRZED_V107')
    if 'v107_eq_production_cutover' in tables(previous):
        _fail('BACKUP_NIE_JEST_SPRZED_V107')
    if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        _fail('NIESPOJNA_KOPIA_SQLITE')
    before_stats = classify_snapshot(conn, catalog)
    parked = _safe_unlisted_crafted_copies(conn, previous, catalog)
    # Only exactly eligible unlisted crafts can account for surplus; no wider
    # relaxation of the preflight gate. Future templates still fail closed.
    if parked:
        before_stats['surplus_copies'] -= len(parked)
    # Show the EXACT failing aggregate (never player or item identifiers).
    # A generic physical-structure refusal previously sent users through
    # repeated rebuild downloads without revealing what was actually wrong.
    # Do not relax the guard: ambiguous rows could contain copy upgrades.
    structure_checks = (
        'invalid_physical_rows', 'unrecognized_physical_templates',
        'duplicate_physical_ids', 'duplicate_stored_ids',
        'orphan_stored_ids', 'stored_owner_conflicts',
        'orphan_worn_ids', 'worn_owner_conflicts',
        'invalid_bag_rows', 'surplus_copies',
    )
    structural_issues = {field: int(before_stats[field])
                         for field in structure_checks if int(before_stats[field])}
    preserved_nongear, nongear_counts = _isolated_nongear_copies(conn, catalog)
    unknown_total = structural_issues.pop('unrecognized_physical_templates', 0)
    if unknown_total != len(preserved_nongear):
        structural_issues['unrecognized_not_proven_inert'] = unknown_total - len(preserved_nongear)
    if structural_issues:
        if unknown_total:
            structural_issues['unrecognized_physical_templates'] = unknown_total
        _fail('STRUKTURA_FIZYCZNA_NIEZGODNA', {**structural_issues, **nongear_counts})
    bag = _collect_bags(conn, gear)
    oldbag = _collect_bags(previous, gear)
    eq = _collect_equipment(conn, gear)
    instances = {}
    inst_counts = Counter()
    for uid, aid, iid, stage, origin in conn.execute(
            'SELECT instance_id,account_id,item_id,evolution_stage,origin FROM v106_item_instances'):
        if (not isinstance(uid,str) or not uid or uid in instances or
            type(aid) is not int or aid <= 0 or (str(iid) not in gear and uid not in preserved_nongear) or
            type(stage) is not int or not 0<=stage<=10 or not isinstance(origin,str) or not origin):
            _fail('BLEDNA_FIZYCZNA_KOPIA')
        instances[uid] = (aid,str(iid),stage,origin)
    stored = set()
    for uid,aid in conn.execute('SELECT instance_id,account_id FROM v106_stored_instances'):
        if uid in stored or uid not in instances or instances[uid][0]!=aid:
            _fail('BLEDNY_MAGAZYN')
        stored.add(uid)
    for uid,(aid,item,stage,origin) in instances.items():
        if uid in preserved_nongear or uid in parked:
            continue
        if uid not in stored:
            inst_counts[(aid,item)] += 1
    deficits = {}
    # One aggregate preflight rather than another sequence of one-error-at-a-
    # time user runs. These groups can overlap, and no account/UID/item leaks.
    preflight = Counter()
    from validation.v10800_eq107_readonly_reconcile import clean_legacy_history
    for key in set(bag)|set(inst_counts):
        difference=bag.get(key,0)-inst_counts.get(key,0)
        if difference < 0:
            preflight['GRUPY_NADMIAROWE'] += 1
            preflight['KOPIE_NADMIAROWE'] += -difference
        if difference > 0:
            # ALL inferred stage-zero copies need sufficient historical growth.
            if bag.get(key,0)-oldbag.get(key,0) < difference:
                preflight['GRUPY_BEZ_POKRYCIA_PRZYROSTEM'] += 1
                preflight['KOPIE_BEZ_POKRYCIA_PRZYROSTEM'] += difference
            # Template-wide upgrades cannot be safely moved to a guessed UID.
            if not clean_legacy_history(conn,key):
                preflight['GRUPY_Z_NIEJEDNOZNACZNA_HISTORIA'] += 1
            deficits[key] = difference
    if preflight:
        _fail('BLOKADY_PRZYROSTU_LUB_HISTORII_EQ', preflight)
    bindings = {}
    worn_ids = set()
    affected = []
    evolved_slot_conflicts = 0
    for aid,slot,uid in conn.execute(
            'SELECT account_id,slot,instance_id FROM v106_equipped_instances'):
        key=(aid,str(slot))
        if key in bindings or uid in worn_ids or key not in eq or uid not in instances:
            _fail('BLEDNE_WIAZANIA_SLOTOW')
        owner,item,stage,origin = instances[uid]
        if owner!=aid or uid in stored:
            _fail('NIEZGODNY_WLASCICIEL_KOPII')
        if item!=eq[key]:
            # No hidden reassignment of per-copy stage or altered template.
            if stage != 0:
                evolved_slot_conflicts += 1
            affected.append(key)
        bindings[key] = uid
        worn_ids.add(uid)
    if eq.keys()!=bindings.keys():
        _fail('BRAKUJACE_LUB_NADMIAROWE_SLOTY')
    if evolved_slot_conflicts:
        _fail('EWOLUCJA_NIEJEDNOZNACZNA_W_SLOTACH',
              {'SLOTY_Z_EWOLUCJA': evolved_slot_conflicts})
    used = set(uid for key,uid in bindings.items() if key not in affected)
    # Preserve all existing bindings that agree. New identities are appended,
    # never replacing/mutating existing physical item data/stages.
    canonical = {}
    for (aid,slot),iid in eq.items():
        if (aid,slot) not in affected:
            canonical[(aid,slot)] = bindings[(aid,slot)]
    changed = len(affected)
    created = 0
    outer = conn.in_transaction
    conn.execute('SAVEPOINT sb108_eq_rebuild_CLONE_ONLY')
    try:
        # Preserve orphan physical identity, but park it in a non-gameplay
        # storage kind on the detached COPY. No items enter inventory.
        for uid in sorted(parked):
            aid = instances[uid][0]
            conn.execute('INSERT INTO v106_stored_instances '
                         '(instance_id,account_id,storage_kind,container) '
                         'VALUES(?,?,?,?)',
                         (uid,aid,'v108_rebuild_quarantine','unlisted_crafted_copy'))
            stored.add(uid)
        # Append EXACT deficit per (account, template); all new copies stage0.
        for (aid,iid),count in sorted(deficits.items()):
            for _ in range(count):
                uid=str(uuid4())
                conn.execute('INSERT INTO v106_item_instances '
                    '(instance_id,account_id,item_id,evolution_stage,origin) VALUES(?,?,?,0,?)',
                    (uid,aid,iid,'v108_recovered_stage0'))
                instances[uid]=(aid,iid,0,'v108_recovered_stage0')
                created+=1
        # A stale slot may hold the exact copy required by ANOTHER stale
        # slot. Detach all mismatched shadows together on the COPY before
        # rebinding; otherwise UNIQUE(instance_id) can reject a safe swap.
        # The physical copy rows and their stages are never modified.
        for aid, slot in affected:
            conn.execute('DELETE FROM v106_equipped_instances '
                         'WHERE account_id=? AND slot=?', (aid, slot))
        free = defaultdict(list)
        for uid,(aid,item,stage,origin) in instances.items():
            if uid not in stored and uid not in used and uid not in preserved_nongear:
                free[(aid,item)].append((uid,stage))
        for key in sorted(affected):
            aid,slot=key
            item=eq[key]
            choices=free.get((aid,item),[])
            # Do not choose the wrong evolved copy merely because its template
            # matches; it may carry a player's unique earned upgrade.
            if not choices or any(stage!=0 for uid,stage in choices):
                _fail('BRAK_BEZPIECZNEJ_NIEULEPSZONEJ_KOPII')
            chosen=min(uid for uid,stage in choices)
            free[(aid,item)]=[(uid,stage) for uid,stage in choices if uid!=chosen]
            canonical[key]=chosen
            used.add(chosen)
            conn.execute('INSERT INTO v106_equipped_instances '
                         '(account_id,slot,instance_id) VALUES(?,?,?)',
                         (aid,slot,chosen))
        # No direct modifications to equipment, inventory, modifiers,
        # physical stages/owners, storage or game progression.
        all_aids={a for a,_ in bag}|{a for a,_ in eq}|{a for a,_ in inst_counts}
        for aid in sorted(all_aids):
            _check_account(conn,aid,catalog)
        if physical_route_conflicts(conn,catalog, allowed_isolated_nongear_ids=preserved_nongear):
            _fail('KONFLIKT_TRAS_FIZYCZNYCH_PO_REBUILDZIE')
        after = classify_snapshot(conn,catalog)
        for field in ('deficit_copies','surplus_copies','worn_slot_mismatches',
                      'invalid_physical_rows','orphan_worn_ids','orphan_stored_ids'):
            if after[field]:
                _fail('NIEZGODNOSC_PO_REBUILDZIE')
        after_preserved, _ = _isolated_nongear_copies(conn, catalog)
        if after_preserved != preserved_nongear or after['unrecognized_physical_templates'] != len(preserved_nongear):
            _fail('NIESPRZETOWE_REKORDY_ZMIENIONE_PO_REBUILDZIE')
        if conn.execute('PRAGMA foreign_key_check').fetchone() is not None:
            _fail('BLAD_KLUCZY_OBCYCH_PO_REBUILDZIE')
        if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            _fail('BLAD_INTEGRALNOSCI_PO_REBUILDZIE')
        conn.execute('RELEASE SAVEPOINT sb108_eq_rebuild_CLONE_ONLY')
        if not outer:conn.commit()
        return {'SLOTY_PRZEBUDOWANE':changed,'KOPIE_DODANE_W_KOPII_TESTOWEJ':created,
                'SLOTY_NIEZMIENIONE':len(eq)-changed,
                'ORYGINALNE_KOPIE_ZACHOWANE':len(instances)-created,
                'ORYGINALNE_ETAPY_ZACHOWANE':1,
                'NIESPRZETOWE_KOPIE_ZACHOWANE':len(preserved_nongear),
                'ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE':len(parked),
                'INNE_TABELE_NIETYKALNE':1,
                'SQLITE_INTEGRITY_PASS':1,'TEST_REBUILD_PASS':1}
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT sb108_eq_rebuild_CLONE_ONLY')
        conn.execute('RELEASE SAVEPOINT sb108_eq_rebuild_CLONE_ONLY')
        if not outer:conn.rollback()
        raise


def _equal_instance_rows(before, after):
    a = {r[0]: tuple(r) for r in before.execute('SELECT * FROM v106_item_instances')}
    b = {r[0]: tuple(r) for r in after.execute('SELECT * FROM v106_item_instances')}
    return all(b.get(uid)==row for uid,row in a.items()) and len(b)>=len(a)


def run(game_root, output_dir=None):
    """Copies source and historic backup read-only; keeps rebuilt DB only on PASS."""
    game_root=Path(game_root).expanduser().resolve(strict=True)
    dbfile=game_root/'soulbound.db'
    if not dbfile.is_file() or dbfile.is_symlink():
        _fail('BRAK_BEZPIECZNEJ_BAZY_PRODUKCYJNEJ')
    catalog,gear=equipment_catalog()
    if output_dir is None:
        output=ROOT/'WYNIKI_EQ_REBUILD_TEST'
    else:
        output=Path(output_dir).expanduser().resolve()
    if game_root==output or game_root in output.parents or output==game_root.parent:
        _fail('WYNIKI_NIE_MOGA_BYC_W_KATALOGU_PRODUKCJI')
    output.mkdir(parents=True,exist_ok=True)
    target=output/'REBUILT_TEST_ONLY.sqlite'
    if target.exists() or target.is_symlink():
        _fail('PLIK_TESTOWY_JUZ_ISTNIEJE_NIE_NADPISUJEMY')
    with tempfile.TemporaryDirectory(prefix='sb108_eq_rebuild_',dir=output) as directory:
        folder=Path(directory)
        current,baseline,candidate=(folder/x for x in ('baza_teraz.sqlite','backup_v107.sqlite','rebuild.sqlite'))
        take_snapshot(dbfile,current)
        with closing(sqlite3.connect(current.as_uri()+'?mode=ro',uri=True)) as now:
            oldpath=locate_original_backup(dbfile,now)
        take_snapshot(oldpath,baseline)
        # Copy snapshot to isolated candidate. Source is *never* opened rw.
        with closing(sqlite3.connect(current.as_uri()+'?mode=ro',uri=True)) as origin:
            from systems.v10800_eq_dynamic_catalog import restore_known_crafted_equipment
            restored_count = restore_known_crafted_equipment(origin,catalog)
            with closing(sqlite3.connect(candidate)) as destination:
                origin.backup(destination)
        with closing(sqlite3.connect(current.as_uri()+'?mode=ro',uri=True)) as origin, \
             closing(sqlite3.connect(baseline.as_uri()+'?mode=ro',uri=True)) as old, \
             closing(sqlite3.connect(candidate)) as rebuilt:
            before,_=_snapshot_other_tables(origin)
            original_stored = {r[0]: tuple(r) for r in origin.execute('SELECT * FROM v106_stored_instances')}
            result=rebuild_clone(rebuilt,old,catalog,confirm_detached_copy=True)
            new_stored = {r[0]: tuple(r) for r in rebuilt.execute('SELECT * FROM v106_stored_instances')}
            if not all(new_stored.get(k)==v for k,v in original_stored.items()):
                _fail('ZMIENIONO_STARE_MAGAZYNY')
            added_stored = set(new_stored)-set(original_stored)
            if (len(added_stored) != result['ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE'] or
                any(new_stored[uid][-2:] != ('v108_rebuild_quarantine','unlisted_crafted_copy')
                    for uid in added_stored)):
                _fail('NIEPRAWIDLOWA_KWARANTANNA_KOPII')
            after,_=_snapshot_other_tables(rebuilt)
            if before!=after:
                _fail('ZMIENIONE_STATYSTYKI_LUB_INNE_TABELE')
            if not _equal_instance_rows(origin,rebuilt):
                _fail('UTRACONO_STARA_KOPIE_LUB_JEJ_EWOLUCJE')
            origin_slots=origin.execute('SELECT * FROM equipment').fetchall()
            trial_slots=rebuilt.execute('SELECT * FROM equipment').fetchall()
            if sorted(origin_slots)!=sorted(trial_slots):
                _fail('ZMIENIONE_PRZEDMIOTY_ZALOZONE')
            result['INNE_TABELE_NIETYKALNE']=1
            result['ORYGINALNE_ETAPY_ZACHOWANE']=1
        # Ensure all SQLite pages are in ONE standalone .sqlite (no WAL sidecar).
        with closing(sqlite3.connect(candidate)) as final_db:
            final_db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            final_db.execute('PRAGMA journal_mode=DELETE')
            if final_db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                _fail('USZKODZONA_KOPIA_PRZED_ZAPISEM')
        # Final move only after all checks. Test database retains private
        # account data on the user's PC, never to be uploaded to chat.
        os.replace(candidate,target)
        return result


def main(argv=None):
    ap=argparse.ArgumentParser(description='Odbudowa fizycznego EQ na KOPII testowej, bez wdrozenia')
    ap.add_argument('--root',default=r'C:\Soulbound-MUD')
    ap.add_argument('--output',default=None)
    args=ap.parse_args(argv)
    try:
        result=run(args.root,args.output)
        for key,value in result.items():
            print(f'{key}: {value}',flush=True)
        print('WYNIK: REBUILD_KOPII_TESTOWEJ_PASS_NIE_WDRAZAC',flush=True)
        print('PRYWATNA_KOPIA: katalog WYNIKI_EQ_REBUILD_TEST; NIE WYSYLAJ BAZY.',flush=True)
        return 0
    except (AuditBlocked,sqlite3.Error,ValueError,RuntimeError,OSError) as exc:
        if isinstance(exc, RebuildBlocked):
            for key, value in sorted(exc.counters.items()):
                # Fixed, script-defined key names and bounded numeric counts.
                print(f'ANOMALIA_{key.upper()}: {int(value)}', flush=True)
        code=(str(exc) if isinstance(exc,AuditBlocked) else 'BLEDNY_STAN_LUB_SQLITE')
        print('WYNIK: BLOKADA_REBUILD_KOPII_TESTOWEJ_'+code,flush=True)
        print('Produkcja i historyczny backup bez zmian. NIE WDRAZAC.',flush=True)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
