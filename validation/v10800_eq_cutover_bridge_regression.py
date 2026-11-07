# -*- coding: utf-8 -*-
"""Isolated synthetic end-to-end rehearsal for v108 source, cutover and rollback.
No user SQLite, external traffic, Windows services or installation paths.
"""
import os,sys,sqlite3,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing
from unittest.mock import patch
from hashlib import sha256
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v10800_eq_rebuild_copy_regression import model
from systems.v10800_eq_cutover_bridge import prepare_from_snapshot,commit_verified_copy,restore_sqlite_from_backup
from validation.v10800_eq107_readonly_reconcile import take_snapshot
from world.dynamic_content import ITEMS
from uuid import uuid4
ITEM='craftq_normal_none_jewel_iron_ring'


def run():
    with TemporaryDirectory(prefix='sb108_cutover_fixtures_') as d:
     h=Path(d); live=h/'live'; live.mkdir(); (live/'backups').mkdir();work=h/'work';work.mkdir()
     c,o=model()
     with closing(c),closing(o):
      all_gear=[k for k,v in ITEMS.items() if isinstance(v,dict) and v.get('type') in ('weapon','armor') and k!=ITEM][:21]
      for db in (c,o):
       db.execute('DELETE FROM inventory');db.execute('DELETE FROM equipment')
      c.execute('DELETE FROM v106_equipped_instances');c.execute('DELETE FROM v106_item_instances')
      for n,iid in enumerate(all_gear[:20]):
       slot=f'test_slot_{n}'
       for db in (c,o):db.execute('INSERT INTO inventory VALUES(1,?,1)',(iid,))
       o.execute('INSERT INTO equipment VALUES(1,?,?)',(slot,iid))
       c.execute('INSERT INTO equipment VALUES(1,?,?)',(slot,all_gear[(n+1)%20]))
       uid=str(uuid4());c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',(uid,1,iid,0,'v106_inventory'))
       c.execute('INSERT INTO v106_equipped_instances VALUES(?,?,?)',(1,slot,uid))
      c.execute('INSERT INTO inventory VALUES(1,?,36)',(all_gear[20],))
      for _ in range(2):c.execute('INSERT INTO v106_item_instances VALUES(?,?,?,?,?)',(str(uuid4()),1,ITEM,0,'v106_inventory'))
      c.executescript('CREATE TABLE accounts(id INTEGER PRIMARY KEY); INSERT INTO accounts VALUES(1);'
                     'CREATE TABLE characters(id INTEGER PRIMARY KEY); INSERT INTO characters VALUES(1);')
      c.commit();o.commit()
      with closing(sqlite3.connect(live/'soulbound.db')) as z:c.backup(z)
      with closing(sqlite3.connect(live/'backups'/'old.sqlite')) as z:o.backup(z)
     src=h/'before.sqlite';take_snapshot(live/'soulbound.db',src)
     orig=sha256((live/'soulbound.db').read_bytes()).hexdigest()
     # Exercise the exact v108 PREDEPLOY runner (not only its helper).
     # Its child process must receive only the repaired detached source.
     mock_stage=h/'v108_stage';mock_stage.mkdir()
     (mock_stage/'VERSION').write_text('108.00.0\n',encoding='utf-8')
     (mock_stage/'testuj_soulbound_windows.py').write_text('''import sqlite3,os
from pathlib import Path
p=Path(os.environ['SOULBOUND_ULTRA_SOURCE_DB'])
assert p.suffix=='.sqlite' and p.exists()
with sqlite3.connect(p) as c:
 assert c.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==58
 assert c.execute('SELECT COUNT(*) FROM v106_stored_instances WHERE storage_kind="v108_rebuild_quarantine"').fetchone()[0]==2
 assert c.execute('SELECT COUNT(*) FROM v106_equipped_instances').fetchone()[0]==20
print('synthetic repaired PREDEPLOY child PASS')
''',encoding='utf-8')
     from predeploy_nowej_wersji import run_tests
     log=h/'v108_rehearsal.log'
     assert run_tests(mock_stage,log,source_db=live/'soulbound.db',timeout_seconds=90)==0
     assert 'V108 PREDEPLOY REBUILD SNAPSHOT PASS:' in log.read_text(encoding='utf-8')
     assert sha256((live/'soulbound.db').read_bytes()).hexdigest()==orig
     rebuilt,stats=prepare_from_snapshot(src,live,work)
     assert (stats['SLOTY_PRZEBUDOWANE'],stats['KOPIE_DODANE_W_KOPII_TESTOWEJ'],stats['ODIZOLOWANE_CRAFT_KOPIE_ZACHOWANE'])==(20,36,2),stats
     assert sha256((live/'soulbound.db').read_bytes()).hexdigest()==orig
     # Frozen-snapshot rehearsal never modifies the source installed DB
     env={**os.environ,'SOULBOUND_ULTRA_SOURCE_DB':str(rebuilt),'PYTHONDONTWRITEBYTECODE':'1'}
     verify=subprocess.run([sys.executable,'-m','validation.v10800_v107_equipment_compat_gate'],
         cwd=ROOT,env=env,text=True,capture_output=True,timeout=60)
     assert verify.returncode==0,(verify.stdout,verify.stderr)
     # New subprocess must independently approve the detached repaired source
     cutover=live/'soulbound.db';commit_verified_copy(rebuilt,cutover)
     with closing(sqlite3.connect(cutover)) as db:
      assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
      assert db.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==58
      assert db.execute('SELECT COUNT(*) FROM v106_stored_instances WHERE storage_kind="v108_rebuild_quarantine"').fetchone()[0]==2
     # Same SQLite route used by stopped-server cutover
     restore_sqlite_from_backup(src,cutover)
     with closing(sqlite3.connect(cutover)) as db:
      assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
      assert db.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]==22
     # Rollback must reproduce pre-cutover player records

    return 13

if __name__=='__main__':
    print('V108 WINDOWS EQ REBUILD CUTOFF: ',run(),'/13 PASS; SYNTETYCZNE DANE')
