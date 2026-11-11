# -*- coding: utf-8 -*-
"""v112: źródła danych v110/v111 są bezpiecznie odczytywane bez ich uruchamiania.

To są WYŁĄCZNIE syntetyczne bazy; test nie otwiera plików użytkownika.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from aktualizuj_soulbound import v112_base_preflight,UpdateError
from systems.v11200_activation import activation_manifest,REQUIRED


def source_fixture(root:Path,version:str):
    (root/'core').mkdir(parents=True,exist_ok=True)
    (root/'VERSION').write_text(version+'\n',encoding='utf-8')
    (root/'core/bootstrap_economy_professions.py').write_text(
        f'VERSION = "{version}"\n',encoding='utf-8')
    with sqlite3.connect(root/'soulbound.db') as c:
        for t in ('v106_equipped_instances','v106_stored_instances','v106_item_instances',
                  'equipment','inventory'):
            c.execute('CREATE TABLE '+t+' (id INTEGER PRIMARY KEY)')
        c.execute('CREATE TABLE v107_eq_production_cutover (cutover_version TEXT,backup_name TEXT)')
        c.execute('INSERT INTO v107_eq_production_cutover VALUES (?,?)',('107.00.0','pre_eq_safe.sqlite'))
        c.commit()


def run():
    checks=0
    with tempfile.TemporaryDirectory(prefix='sb112_recovery_contract_') as temp:
        work=Path(temp)
        for version in ('110.00.0','111.00.0'):
            root=work/version
            source_fixture(root,version)
            assert v112_base_preflight(root)=='validated-ledger';checks+=1
            original=(root/'soulbound.db').read_bytes()
            assert v112_base_preflight(root)=='validated-ledger';checks+=1
            assert (root/'soulbound.db').read_bytes()==original;checks+=1
            (root/'VERSION').write_text('109.00.0\n',encoding='utf-8')
            try:v112_base_preflight(root)
            except UpdateError:checks+=1
            else:raise AssertionError('Mismatched source VERSION accepted')
            (root/'VERSION').write_text(version+'\n',encoding='utf-8')
            with sqlite3.connect(root/'soulbound.db') as c:
                c.execute('DELETE FROM v107_eq_production_cutover');c.commit()
            try:v112_base_preflight(root)
            except UpdateError:checks+=1
            else:raise AssertionError('Missing EQ cutover accepted')
        # Synthetic staging manifest tests only authorization rules, not boot.
        candidate=work/'candidate.zip';candidate.write_bytes(b'synthetic-nonrelease-fixture')
        stage=work/'staged';stage.mkdir()
        mapping={Path(x):object() for x in REQUIRED}
        for relative in mapping:
            dest=stage/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text('fixture\n',encoding='utf-8')
        base={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS','returncode':0,
              'completed_stages':60,'required_stages':60,'version':'112.00.0',
              'v112_release_gates_pass':True,
              'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest()}
        for version in ('110.00.0','111.00.0'):
            state={**base,'installed_at_test':version}
            doc=activation_manifest(state,candidate,stage,mapping)
            assert doc['version']=='112.00.0' and set(REQUIRED)<=set(doc['files']);checks+=1
        for field,value in (('installed_at_test','109.00.0'),('v112_release_gates_pass',False),
                            ('sha256','a'*64),('completed_stages',59)):
            state={**base,'installed_at_test':'110.00.0',field:value}
            try:activation_manifest(state,candidate,stage,mapping)
            except ValueError:checks+=1
            else:raise AssertionError('Unsafe state accepted: '+field)
    print(f'V112 RECOVERY BASE: {checks} synthetic authorization/SQLite checks PASS')

if __name__=='__main__':run()
