# -*- coding: utf-8 -*-
"""Real copytree -> byte verification -> SQLite WAL transfer, off production.

All fixtures live in a fresh temporary directory; no game server is started.
Prevents reintroducing the mismatch between ignored logs and protected saves.
"""
from __future__ import annotations
import sqlite3
import tempfile
from contextlib import closing, ExitStack
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from aktualizuj_soulbound import backup_existing, protected, UpdateError
from systems.universal_release_update import verify_private_backup
from systems.current_fresh_install import carry_saved_data


def run():
    passed=0
    with tempfile.TemporaryDirectory(prefix='sb_current_backup_real_') as folder, ExitStack() as handles:
        temp=Path(folder)
        source=temp/'Soulbound-MUD'
        backup=temp/'Soulbound_BACKUP_test'
        stage=temp/'new-stage'
        source.mkdir();stage.mkdir()
        (source/'logs').mkdir()
        (source/'logs'/'TESTY_Soulbound.log').write_text('old logfile',encoding='utf8')
        (source/'logs'/'soulbound_control.json').write_text('old process',encoding='utf8')
        (source/'.git').mkdir()
        (source/'.git'/'config').write_text('repo metadata',encoding='utf8')
        (source/'__pycache__').mkdir()
        (source/'__pycache__'/'trash.pyc').write_bytes(b'trash')
        (source/'previous_release.zip').write_bytes(b'previous')
        (source/'soulbound_control.json').write_text('old process',encoding='utf8')
        (source/'server.py').write_text('old code',encoding='utf8')
        (stage/'server.py').write_text('new code',encoding='utf8')
        (source/'admin_level_caps.json').write_text('{"level":800}',encoding='utf8')
        (source/'soulbound_world_seed.txt').write_text('seed-not-to-lose',encoding='utf8')
        (source/'certs').mkdir()
        (source/'certs'/'private.key').write_bytes(b'local-test-key')
        # The committed rows deliberately remain in WAL until both handles close.
        db=handles.enter_context(closing(sqlite3.connect(source/'soulbound.db')))
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE characters(id INTEGER PRIMARY KEY,exp INTEGER)')
        db.execute('CREATE TABLE equipment(id INTEGER PRIMARY KEY,eq BLOB)')
        db.execute('INSERT INTO characters VALUES(1,99887)')
        db.execute('INSERT INTO equipment VALUES(1,?)',(b'\x00\xffequipment',))
        db.commit()
        assert (source/'soulbound.db-wal').exists(); passed+=1
        # A read-only, quiescent fixture with committed WAL: keep its final
        # handle open through the comparisons so SQLite does not checkpoint
        # source files between copytree and the SHA256 verification.
        backup_existing(source,backup)
        for excluded in ('logs/TESTY_Soulbound.log','logs/soulbound_control.json',
                         '.git/config','__pycache__/trash.pyc','previous_release.zip'):
            assert not (backup/excluded).exists(),excluded
            assert not protected(Path(excluded)),excluded
            passed+=1
        assert verify_private_backup(source,backup,protected)>=4;passed+=1
        stats=carry_saved_data(backup,stage,protected)
        assert stats['sqlite_files']==1 and stats['tables_checked']==2;passed+=1
        assert (stage/'soulbound_world_seed.txt').read_text(encoding='utf8')=='seed-not-to-lose';passed+=1
        assert (stage/'certs/private.key').read_bytes()==b'local-test-key';passed+=1
        assert not (stage/'soulbound_control.json').exists();passed+=1
        assert (stage/'server.py').read_text(encoding='utf8')=='new code';passed+=1
        with closing(sqlite3.connect(stage/'soulbound.db')) as new:
            assert new.execute('PRAGMA integrity_check').fetchone()==('ok',);passed+=1
            assert new.execute('SELECT exp FROM characters').fetchone()==(99887,);passed+=1
            assert new.execute('SELECT eq FROM equipment').fetchone()==(b'\x00\xffequipment',);passed+=1
        (backup/'certs/private.key').write_bytes(b'tampered-key')
        try:
            verify_private_backup(source,backup,protected)
        except UpdateError:
            passed+=1
        else:raise AssertionError('A changed protected file was not detected')
        (backup/'certs/private.key').write_bytes(b'local-test-key')
        (backup/'admin_level_caps.json').unlink()
        try:
            verify_private_backup(source,backup,protected)
        except UpdateError:
            passed+=1
        else:raise AssertionError('A missing protected file was not detected')
    print(f'REAL BACKUP LOGS AND WAL: {passed}/{passed} PASS',flush=True)

if __name__=='__main__':run()
