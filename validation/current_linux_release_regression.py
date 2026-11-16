# -*- coding: utf-8 -*-
"""Linux-only release safety: offline test fixtures, no production mutation."""
from __future__ import annotations
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems import linux_release as linux
from systems import universal_activation as activation


def check(cond,message):
    if not cond:raise AssertionError(message)
    return 1


def main():
    tests=0
    tests+=check(sys.platform=='linux','Linux only')
    tests+=check(linux.VERSION == (ROOT/'VERSION').read_text().strip(),'VERSION')
    tests+=check(linux.VERSION.count('.')==2,'VERSION format')
    tests+=check(linux.SERVICE_IDENTITY.startswith('# Managed-By'),'service marker')
    with tempfile.TemporaryDirectory(prefix='sb_current_linux_gate_') as td:
        temp=Path(td);db=temp/'source.db'
        with closing(sqlite3.connect(db)) as con:
            con.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY, login TEXT)')
            con.execute('CREATE TABLE characters(id INTEGER PRIMARY KEY, account_id INTEGER, eq BLOB)')
            con.execute('INSERT INTO accounts VALUES(1,?)',('tester',))
            con.execute('INSERT INTO characters VALUES(1,1,?)',(bytes(range(256)),))
            con.commit()
        expected=linux.fingerprint_source(db)
        tests+=check(len(expected)==64,'fingerprint')
        snap=temp/'copy.sqlite'; got=linux.snap_database(db,snap)
        tests+=check(got==expected,'same DB full fingerprint')
        tests+=check(linux.fingerprint_source(snap)==got,'read-only new DB')
        with closing(sqlite3.connect(snap)) as con:
            tests+=check(con.execute('SELECT eq FROM characters').fetchone()[0]==bytes(range(256)),'EQ BLOB')
        try:linux.snap_database(db,snap)
        except linux.LinuxReleaseError: tests+=1
        else:raise AssertionError('overwrote SQLite')
        sym=temp/'alias.db';sym.symlink_to(db)
        try:linux.source_database(sym)
        except linux.LinuxReleaseError:tests+=1
        else:raise AssertionError('symlink DB accepted')
        fake=temp/'fake.log';fake.write_text('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\n')
        tests+=check(not linux._read_gate_proof(fake),'incomplete test proof')
        full=('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\n'
              'SOULBOUND RELEASE GATES PASS\nPLUS CHECKS PASS\n'
              'UNIVERSAL RELEASE SAFETY: 24/24 PASS\nTCP 6 GRACZY: PASS\n'
              'PASS - FIZYCZNE EQ NA KOPII BAZY (kod 0)\n')
        fake.write_text(full)
        tests+=check(linux._read_gate_proof(fake),'complete proof parse')
        unit=linux._service_unit(temp/'workspace')
        tests+=check('SOULBOUND_MAX_CLIENTS=6' in unit,'six players')
        tests+=check('SOULBOUND_PORT=4000' in unit,'port 4000')
        tests+=check('Restart=on-failure' in unit and 'KillMode=control-group' in unit,'service lifecycle')
        tests+=check('ExecStart=' in unit and '/current/server.py' in unit,'stable code pointer')
        tests+=check('TimeoutStopSec=90' in unit,'stop deadline')
        tests+=check('Environment=SOULBOUND_DB=' in unit,'private DB path')
        try:linux._protect_workspace(db.parent,db)
        except linux.LinuxReleaseError:tests+=1
        else:raise AssertionError('source DB inside target accepted')
        try:linux._protect_workspace(Path('/'),db)
        except linux.LinuxReleaseError:tests+=1
        else:raise AssertionError('workspace root accepted')
        mapping={}
        stage=temp/'stage';stage.mkdir()
        for rel in activation.required_for('linux'):
            file=ROOT/rel
            check(file.is_file(),'Required file not present '+rel)
            dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(file.read_bytes())
            mapping[Path(rel)]=None
        archive=temp/'test.zip';archive.write_bytes(b'linux test synthetic bytes')
        state={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
               'returncode':0,'completed_stages':60,'required_stages':60,
               'version':linux.VERSION,'release_gates_pass':True,
               'installed_at_test':'LINUX_FIRST_OR_UPGRADE',
               'platform':'linux','linux_contract_pass':True,
               'db_fingerprint':got,'sha256':linux.digest(archive)}
        manifest=activation.activation_manifest(state,archive,stage,mapping)
        tests+=check(manifest['source_gate']=='LINUX_PREDEPLOY_APPROVED','linux marker identity')
        marker=stage/activation.MARKER;marker.parent.mkdir(parents=True,exist_ok=True)
        marker.write_text(json.dumps(manifest),encoding='utf-8')
        tests+=check(activation.verify(stage),'verified Linux activation')
        (stage/'server.py').write_text('tampered',encoding='utf-8')
        tests+=check(not activation.verify(stage),'tampered source blocked')
        state['db_fingerprint']='broken'
        try:activation.activation_manifest(state,archive,stage,mapping)
        except ValueError:tests+=1
        else:raise AssertionError('missing db identity accepted')
        tests+=check(not (ROOT/'soulbound.db').is_file(),'no bundled player database')
        target=ROOT/'PREDEPLOY_NOWEJ_WERSJI.sh'
        tests+=check(target.is_file() and (ROOT/'WDROZ_PO_PREDEPLOY.sh').is_file(),'linux entrypoints')
        archive_path=os.environ.get('SOULBOUND_LINUX_ARCHIVE')
        if not archive_path:
            raise AssertionError('SOULBOUND_LINUX_ARCHIVE is mandatory for Linux package regression')
        real_zip, entries, prod=linux.archive_info(archive_path)
        tests+=check(Path('systems/linux_release.py') in prod,'Linux runtime install included')
        tests+=check(Path('PREDEPLOY_NOWEJ_WERSJI.sh') in prod,'Linux PREDEPLOY included')
        tests+=check(Path('validation/current_linux_release_regression.py') in entries,'Linux gate in ZIP')
        tests+=check(Path('validation/current_linux_release_regression.py') not in prod,'tests excluded from production')
        tests+=check(Path('soulbound.db') not in entries,'no private DB in ZIP')
        tests+=check(not any(p.suffix.lower()=='.bat' for p in entries),'no Windows BAT anywhere in Linux ZIP')
        tests+=check(not any(p.suffix.lower()=='.bat' for p in prod),'no Windows BAT in installed game')
        tests+=check(all(Path(rel) in prod for rel in activation.required_for('linux')),'Linux runtime files complete')
        tests+=check(not any((ROOT/name).exists() for name in activation.REQUIRED_WINDOWS),'no BAT in unpacked Linux edition')
        tests+=check(Path('VERSION') in prod and Path('server.py') in prod,'complete game')
    print('LINUX RELEASE SAFETY: '+str(tests)+'/'+str(tests)+' PASS',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
