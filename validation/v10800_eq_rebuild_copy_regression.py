# -*- coding: utf-8 -*-
"""No player DB: isolated SQLite regression for conservative v108 EQ rebuild."""
from __future__ import annotations
from contextlib import closing
from uuid import uuid4, uuid5, NAMESPACE_URL
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from hashlib import sha256

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10800_eq_rebuild_copy import rebuild_clone, RebuildBlocked, _snapshot_other_tables, run as run_on_files
from systems.equipment_shadow_slots_v10600 import _check_account
from systems.v10800_eq_physical_routes import physical_route_conflicts

CAT={'old': {'type':'armor','defense':450},
     'new': {'type':'armor','defense':550},
     'other':{'type':'weapon','attack':123},
     'material':{'type':'material'}}


def model():
    current=sqlite3.connect(':memory:')
    previous=sqlite3.connect(':memory:')
    for conn in (current,previous):
        conn.executescript('''
            CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,
              PRIMARY KEY(account_id,item_id));
            CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,
              PRIMARY KEY(account_id,slot));
            CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value TEXT,
              PRIMARY KEY(account_id,record_key));
            CREATE TABLE equipment_reforges(account_id INTEGER,item_id TEXT,bonus INTEGER);
            CREATE TABLE user_stats(account_id INTEGER PRIMARY KEY, exp INTEGER, zrecznosc INTEGER);
            INSERT INTO user_stats VALUES(1,999999,77);
            INSERT INTO inventory VALUES(1,'old',1);
            INSERT INTO inventory VALUES(1,'other',1);
            INSERT INTO equipment VALUES(1,'head','old');
        ''')
    current.executescript('''
        CREATE TABLE v106_item_instances(instance_id TEXT PRIMARY KEY,account_id INTEGER,
          item_id TEXT,evolution_stage INTEGER,origin TEXT);
        CREATE TABLE v106_equipped_instances(account_id INTEGER,slot TEXT,
          instance_id TEXT UNIQUE,PRIMARY KEY(account_id,slot));
        CREATE TABLE v106_stored_instances(instance_id TEXT PRIMARY KEY,
          account_id INTEGER,storage_kind TEXT,container TEXT);
        CREATE TABLE v107_eq_production_cutover(cutover_version TEXT,backup_name TEXT,cutover_utc TEXT);
        INSERT INTO v107_eq_production_cutover VALUES ('107.00.0','old.sqlite','date');
    ''')
    uid_old=str(uuid5(NAMESPACE_URL,'soulbound:v106:legacy:1:old'))
    uid_other=str(uuid5(NAMESPACE_URL,'soulbound:v106:legacy:1:other'))
    current.executemany('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',[
        (uid_old,1,'old',0,'legacy_unique'),
        (uid_other,1,'other',5,'legacy_unique')])
    current.execute('INSERT INTO v106_equipped_instances VALUES(?,?,?)',(1,'head',uid_old))
    # Gains since v107: one new worn item + one additional duplicate.
    current.execute('UPDATE equipment SET item_id="new" WHERE account_id=1 AND slot="head"')
    current.execute('INSERT INTO inventory VALUES(1,"new",2)')
    current.commit(); previous.commit()
    return current,previous


def ensure(cond,msg):
    if not cond: raise AssertionError(msg)


def expected_block(mutate):
    c,p=model()
    with closing(c),closing(p):
        mutate(c,p)
        c.commit()
        before=list(c.iterdump())
        try:rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        except RebuildBlocked:
            assert list(c.iterdump())==before, "Nieudany test zmienil dane"
            return 1
        raise AssertionError('Brak blokady niejednoznacznego EQ')


def run():
    n=0
    # Direct invocation without explicit test-copy acknowledgment always blocks.
    c,p=model()
    with closing(c), closing(p):
        try: rebuild_clone(c,p,CAT)
        except RebuildBlocked: n+=1
        else: raise AssertionError('Lack of clone guard did not block')
    c,p=model()
    with closing(c),closing(p):
        before_stats=_snapshot_other_tables(c)
        original=c.execute('SELECT * FROM v106_item_instances ORDER BY instance_id').fetchall()
        result=rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        ensure(result['SLOTY_PRZEBUDOWANE']==1,'rebuild mismatch'); n+=1
        ensure(result['KOPIE_DODANE_W_KOPII_TESTOWEJ']==2,'2 historical additions');n+=1
        ensure(result['ORYGINALNE_KOPIE_ZACHOWANE']==2,'original copies count');n+=1
        ensure(all(row in c.execute('SELECT * FROM v106_item_instances').fetchall() for row in original),'physical copies lost');n+=1
        ensure(_snapshot_other_tables(c)==before_stats,'stats or equipment changed');n+=1
        ensure(c.execute('SELECT evolution_stage FROM v106_item_instances WHERE item_id="other"').fetchone()[0]==5,'evolution stage changed');n+=1
        _check_account(c,1,CAT); n+=1
        ensure(physical_route_conflicts(c,CAT)==0,'physical conflict');n+=1
        ensure(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity');n+=1
        ensure(c.execute('SELECT value FROM player_records_v03051').fetchall()==[],'records modified');n+=1
        re=rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        ensure(re['SLOTY_PRZEBUDOWANE']==0 and re['KOPIE_DODANE_W_KOPII_TESTOWEJ']==0,
               'rebuild not idempotent');n+=1
    # A true two-slot swap is recoverable on a COPY without inventing IDs.
    c,p=model()
    with closing(c),closing(p):
        c.execute('UPDATE v106_item_instances SET evolution_stage=0 WHERE item_id="other"')
        uid_old=c.execute('SELECT instance_id FROM v106_item_instances WHERE item_id="old"').fetchone()[0]
        uid_other=c.execute('SELECT instance_id FROM v106_item_instances WHERE item_id="other"').fetchone()[0]
        c.execute('DELETE FROM inventory WHERE item_id="new"')
        c.execute('UPDATE equipment SET item_id="other" WHERE slot="head"')
        c.execute('INSERT INTO equipment VALUES(1,"body","old")')
        c.execute('INSERT INTO v106_equipped_instances VALUES(1,"body",?)',(uid_other,))
        c.commit()
        result=rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        ensure(result['SLOTY_PRZEBUDOWANE']==2 and result['KOPIE_DODANE_W_KOPII_TESTOWEJ']==0,
               'two-slot copy swap should not create items');n+=1
        bindings=dict(c.execute('SELECT slot,instance_id FROM v106_equipped_instances'))
        ensure(bindings=={'head':uid_other,'body':uid_old},'wrong physical copy swap');n+=1
        _check_account(c,1,CAT);n+=1
        ensure(physical_route_conflicts(c,CAT)==0,'physical conflict after swap');n+=1
    # Malformed physical rows must report a fixed aggregate reason, not an ID.
    c,p=model()
    with closing(c), closing(p):
        c.execute('UPDATE v106_item_instances SET item_id="material" WHERE item_id="other"')
        c.commit()
        before=list(c.iterdump())
        try:rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        except RebuildBlocked as exc:
            ensure(str(exc)=='STRUKTURA_FIZYCZNA_NIEZGODNA',
                   'generic/unexpected physical failure: '+str(exc));n+=1
            ensure(exc.counters.get('unrecognized_physical_templates')==1,
                   'unknown template count missing');n+=1
        else:raise AssertionError('unknown physical template not blocked')
        ensure(list(c.iterdump())==before,'structural refusal modified source');n+=1
    # A KNOWN, physically inert non-EQ record must survive byte-for-byte.
    # The DEFAULT production validator is still strict (no live-gate bypass).
    c,p=model()
    with closing(c), closing(p):
        inert_id=str(uuid4())
        c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
                  (inert_id,1,'material',0,'v106_inventory'))
        c.commit()
        before=c.execute('SELECT * FROM v106_item_instances WHERE instance_id=?',(inert_id,)).fetchone()
        ensure(physical_route_conflicts(c,CAT)>0,'default physical validator must stay strict');n+=1
        report=rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        ensure(report['NIESPRZETOWE_KOPIE_ZACHOWANE']==1,'inert record not acknowledged');n+=1
        after=c.execute('SELECT * FROM v106_item_instances WHERE instance_id=?',(inert_id,)).fetchone()
        ensure(after==before,'known nongear physical changed or deleted');n+=1
        ensure(physical_route_conflicts(c,CAT)>0,'live validator bypass was introduced');n+=1
        ensure(c.execute('PRAGMA integrity_check').fetchone()[0]=='ok','non-gear sample damaged');n+=1
    # An UNRECOGNIZED item template must never be silently accepted.
    n+=expected_block(lambda c,p:c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
        (str(uuid4()),1,'discontinued_missing_template',0,'v106_inventory')))
    # No automatic preservation if the non-gear physical row is evolved, stored,
    # worn, has history of upgrades, or carries a malformed identity.
    n+=expected_block(lambda c,p:c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
        (str(uuid4()),1,'material',4,'v106_inventory')))
    def stored_nongear(c,p):
        uid=str(uuid4())
        c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',(uid,1,'material',0,'v106_inventory'))
        c.execute('INSERT INTO v106_stored_instances VALUES(?,?,?,?)',(uid,1,'bank',''))
    n+=expected_block(stored_nongear)
    def worn_nongear(c,p):
        uid=str(uuid4())
        c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',(uid,1,'material',0,'v106_inventory'))
        c.execute('INSERT INTO v106_equipped_instances VALUES(?,?,?)',(1,'special',uid))
    n+=expected_block(worn_nongear)
    def active_nongear(c,p):
        c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',(str(uuid4()),1,'material',0,'v106_inventory'))
        c.execute('INSERT INTO equipment VALUES(?,?,?)',(1,'special','material'))
    n+=expected_block(active_nongear)
    def upgraded_nongear(c,p):
        c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',(str(uuid4()),1,'material',0,'v106_inventory'))
        c.execute('INSERT INTO equipment_reforges VALUES(?,?,?)',(1,'material',16))
    n+=expected_block(upgraded_nongear)
    n+=expected_block(lambda c,p:c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',
        ('not-a-real-uuid',1,'material',0,'v106_inventory')))
    # A worn mismatch with a per-copy stage is ambiguous: absolutely no automatic transfer.
    n+=expected_block(lambda c,p:c.execute('UPDATE v106_item_instances SET evolution_stage=2 WHERE item_id="old"'))
    # Upgrade on missing target template: preserve and refuse stage0 synthesis.
    n+=expected_block(lambda c,p:c.execute('INSERT INTO equipment_reforges VALUES(1,"new",16)'))
    # Partial deficit not covered by historical growth.
    n+=expected_block(lambda c,p:p.execute('INSERT INTO inventory VALUES(1,"new",2)'))
    # Owner drift.
    n+=expected_block(lambda c,p:c.execute('UPDATE v106_item_instances SET account_id=9 WHERE item_id="old"'))
    # Count surplus from lost inventory.
    n+=expected_block(lambda c,p:c.execute('UPDATE inventory SET quantity=0 WHERE item_id="old"'))
    # Storage conflict: equipped physical copy also stored.
    n+=expected_block(lambda c,p:c.execute("INSERT INTO v106_stored_instances VALUES((SELECT instance_id FROM v106_item_instances WHERE item_id='old'),1,'bank','')"))
    # No auto-upgrade of legacy template evolution.
    n+=expected_block(lambda c,p:c.execute("INSERT INTO player_records_v03051 VALUES(1,'eq_evolution_v10500:new','4')"))
    # Loss of physically bound UID.
    n+=expected_block(lambda c,p:c.execute('DELETE FROM v106_item_instances WHERE item_id="old"'))
    # Duplicate binding with same copy is blocked by SQLite UNIQUE itself.
    n+=expected_block(lambda c,p:c.execute('DELETE FROM v106_equipped_instances'))
    # When several independent data guards fail, report ALL anonymous
    # categories in one run instead of one blocker per new test download.
    c,p=model()
    with closing(c),closing(p):
        p.execute('INSERT INTO inventory VALUES(1,"new",2)')
        c.execute('INSERT INTO equipment_reforges VALUES(1,"new",16)')
        c.commit();p.commit()
        before=tuple(c.iterdump())
        try:rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        except RebuildBlocked as exc:
            ensure(str(exc)=='BLOKADY_PRZYROSTU_LUB_HISTORII_EQ','incorrect combined preflight code');n+=1
            ensure(exc.counters.get('GRUPY_BEZ_POKRYCIA_PRZYROSTEM')==1,'growth blocker not counted');n+=1
            ensure(exc.counters.get('GRUPY_Z_NIEJEDNOZNACZNA_HISTORIA')==1,'history blocker not counted');n+=1
        else:raise AssertionError('combined guards not triggered')
        ensure(tuple(c.iterdump())==before,'preflight changed data');n+=1
    c,p=model()
    with closing(c),closing(p):
        c.execute('UPDATE v106_item_instances SET evolution_stage=2 WHERE item_id="old"')
        old_uid=c.execute('SELECT instance_id FROM v106_item_instances WHERE item_id="other"').fetchone()[0]
        c.execute('INSERT INTO equipment VALUES(1,"body","old")')
        c.execute('INSERT INTO v106_equipped_instances VALUES(1,"body",?)',(old_uid,))
        c.commit()
        before=tuple(c.iterdump())
        try:rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        except RebuildBlocked as exc:
            ensure(str(exc)=='EWOLUCJA_NIEJEDNOZNACZNA_W_SLOTACH','slot evolve gate');n+=1
            ensure(exc.counters.get('SLOTY_Z_EWOLUCJA')==2,'all ambiguous slots not counted');n+=1
        else:raise AssertionError('evolved mismatches not blocked')
        ensure(tuple(c.iterdump())==before,'evolved preflight changed data');n+=1
    # SQL failure halfway through INSERT must roll back all trial writes.
    c,p=model()
    with closing(c),closing(p):
        c.executescript('''
            CREATE TRIGGER block_second_recovery BEFORE INSERT ON v106_item_instances
            WHEN NEW.item_id='new' AND
                 (SELECT COUNT(*) FROM v106_item_instances WHERE item_id='new') >= 1
            BEGIN SELECT RAISE(ABORT,'intentional test failure'); END;
        ''')
        before=list(c.iterdump())
        try:rebuild_clone(c,p,CAT,confirm_detached_copy=True)
        except sqlite3.DatabaseError: n+=1
        else:raise AssertionError('no SQL failure in trial')
        ensure(list(c.iterdump())==before,'partial SQL insert was not rolled back'); n+=1
    # Complete Windows-like path, using only mock private files in TEMP.
    with TemporaryDirectory(prefix='sb108_eq_rebuild_end2end_') as folder:
        home=Path(folder)
        game=home/'game';game.mkdir()
        (game/'backups').mkdir()
        output=home/'offline_copy'
        c,p=model()
        with closing(c),closing(p):
            with closing(sqlite3.connect(game/'soulbound.db')) as dst:c.backup(dst)
            with closing(sqlite3.connect(game/'backups'/'old.sqlite')) as dst:p.backup(dst)
        original_hash=sha256((game/'soulbound.db').read_bytes()).hexdigest()
        backup_hash=sha256((game/'backups'/'old.sqlite').read_bytes()).hexdigest()
        with patch('validation.v10800_eq_rebuild_copy.equipment_catalog',return_value=(CAT,{'old','new','other'})):
            out=run_on_files(game,output)
            ensure(out['SLOTY_PRZEBUDOWANE']==1,'file clone did not rebuild');n+=1
            ensure((output/'REBUILT_TEST_ONLY.sqlite').is_file(),'no output DB');n+=1
            with closing(sqlite3.connect(output/'REBUILT_TEST_ONLY.sqlite')) as trial:
                _check_account(trial,1,CAT);n+=1
                ensure(trial.execute('PRAGMA integrity_check').fetchone()[0]=='ok','damaged rebuilt file');n+=1
            ensure(sha256((game/'soulbound.db').read_bytes()).hexdigest()==original_hash,'source changed');n+=1
            ensure(sha256((game/'backups'/'old.sqlite').read_bytes()).hexdigest()==backup_hash,'old backup changed');n+=1
            try:run_on_files(game,output)
            except RebuildBlocked:n+=1
            else:raise AssertionError('output should never be overwritten')
    print('EQ v108 REBUILD KOPII - TESTY PASS',n)
    return n

if __name__=='__main__':run()
