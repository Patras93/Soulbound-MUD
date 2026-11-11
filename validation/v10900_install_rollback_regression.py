# -*- coding: utf-8 -*-
"""Synthetic v108->v109: official proof, installer, rollback, DB preservation.

No production data/processes, no Windows STOP. Tests the current v109 copy
only, and does NOT assert that the installed v108 scripts support v109 yet.
"""
from __future__ import annotations
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
from zipfile import ZipFile,ZIP_DEFLATED
from systems.v10900_activation import REQUIRED,MARKER,verify_root_for_test
from aktualizuj_soulbound import run_update,UpdateError

ROOT=Path(__file__).resolve().parents[1]

def run():
    checks=0
    def ck(value,name):
        nonlocal checks
        assert value,name
        checks+=1
    with tempfile.TemporaryDirectory(prefix='soulbound-v109-install-') as td:
        base=Path(td)
        live=base/'Soulbound-MUD'
        (live/'core').mkdir(parents=True)
        (live/'core/bootstrap_economy_professions.py').write_text('VERSION = "108.00.0"\n',encoding='utf-8')
        (live/'VERSION').write_text('108.00.0\n',encoding='utf-8')
        marker=live/'LIVE_CONTENT'/'v108_release_activation.json'
        marker.parent.mkdir(parents=True)
        marker.write_text('v108 fixture; production proof is verified separately',encoding='utf-8')
        db=live/'soulbound.db'
        with closing(sqlite3.connect(db)) as conn:
            conn.execute('CREATE TABLE v107_eq_production_cutover(cutover_version TEXT,backup_name TEXT)')
            conn.execute('INSERT INTO v107_eq_production_cutover VALUES(?,?)',('107.00.0','old.sqlite'))
            conn.execute('CREATE TABLE user_character_fingerprint(v TEXT)')
            conn.execute('INSERT INTO user_character_fingerprint VALUES(?)',('DO_NOT_CHANGE',))
            conn.commit()
        pristine=hashlib.sha256(db.read_bytes()).hexdigest()
        # Approved release ZIP modeled from actual candidate source files.
        required=set(REQUIRED)|{'CHANGELOG_PL.txt','START_Soulbound.bat',
                                'STOP_Soulbound.bat','predeploy_check.py'}
        archive=base/'Soulbound-MUD-v109.00.0-synthetic.zip'
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            for rel in sorted(required):z.write(ROOT/rel,'Soulbound-MUD/'+rel)
        state={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
               'required_stages':60,'completed_stages':60,'returncode':0,
               'version':'109.00.0','installed_at_test':'108.00.0',
               'v109_release_gates_pass':True,'zip':str(archive),
               'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
        approve=base/'Soulbound_PREDEPLOY'/'last_result.json'
        approve.parent.mkdir()
        with patch('systems.v10800_activation.verify_root_for_test',return_value=True),\
             patch('aktualizuj_soulbound.stop_local_server') as stop:
            for bad in ({'status':'FAIL'},{'v109_release_gates_pass':False},
                        {'installed_at_test':'107.00.0'},{'completed_stages':59},
                        {'sha256':'0'*64}):
                approve.write_text(json.dumps(state|bad),encoding='utf-8')
                try:run_update(live,archive,'109.00.0',restart=False)
                except UpdateError:ck(True,'bad PREDEPLOY blocked before STOP')
                else:raise AssertionError('bad approval accepted '+str(bad))
                stop.assert_not_called()
                ck(hashlib.sha256(db.read_bytes()).hexdigest()==pristine,'failed proof never touched SQLite')
            approve.write_text(json.dumps(state),encoding='utf-8')
            # Deliberately damaged DB: failure after code install must roll back
            # the old version and generated marker, keeping player DB intact.
            with closing(sqlite3.connect(db)) as conn:
                conn.execute('DROP TABLE v107_eq_production_cutover')
                conn.commit()
            pre_failure=hashlib.sha256(db.read_bytes()).hexdigest()
            try:run_update(live,archive,'109.00.0',restart=False)
            except UpdateError as e:
                ck('tabela EQ' in str(e),'missing ledger correctly refused')
            else:raise AssertionError('broken production DB unexpectedly accepted')
            ck((live/'VERSION').read_text().strip()=='108.00.0','rollback restored v108 code')
            ck(not (live/MARKER).exists(),'rollback removed v109 attestation')
            ck(hashlib.sha256(db.read_bytes()).hexdigest()==pre_failure,'rollback preserved SQL bytes')
            with closing(sqlite3.connect(db)) as conn:
                conn.execute('CREATE TABLE v107_eq_production_cutover(cutover_version TEXT,backup_name TEXT)')
                conn.execute('INSERT INTO v107_eq_production_cutover VALUES(?,?)',('107.00.0','old.sqlite'))
                conn.commit()
            before_install=hashlib.sha256(db.read_bytes()).hexdigest()
            backup=run_update(live,archive,'109.00.0',restart=False)
            ck(backup.is_dir(),'persistent full backup created')
            ck((live/'VERSION').read_text().strip()=='109.00.0','candidate code installed')
            ck(verify_root_for_test(live),'durable marker and code verified')
            ck(hashlib.sha256(db.read_bytes()).hexdigest()==before_install,'EQ/player SQLite untouched')
            ck((backup/'VERSION').read_text().strip()=='108.00.0','restorable previous release backup')
            import shutil
            shutil.rmtree(approve.parent)
            ck(verify_root_for_test(live),'PREDEPLOY can be deleted after activation')
    print('V109 INSTALL+ROLLBACK:',checks,'checks PASS; synthetic only')
    return checks

if __name__=='__main__':run()
