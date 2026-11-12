# -*- coding: utf-8 -*-
"""Offline, synthetic checks of version-neutral release safety and WAL/rollback.

Never uses production data or opens the real server port.
"""
from __future__ import annotations
import hashlib
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch
from contextlib import closing
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from aktualizuj_soulbound import UpdateError, archive_mapping, protected
from systems.current_fresh_install import carry_saved_data, publish_clean, FreshInstallError
from systems.universal_release_update import update


def expect_block(callback):
    try:callback()
    except (UpdateError,FreshInstallError,ValueError,zipfile.BadZipFile):return
    raise AssertionError('Unsafe release operation unexpectedly accepted')


def run():
    count=0
    with tempfile.TemporaryDirectory(prefix='soulbound_universal_e2e_') as temp:
        parent=Path(temp)
        root=parent/'Soulbound-MUD';root.mkdir()
        (root/'VERSION').write_text('112.00.0\n',encoding='utf8')
        (root/'core').mkdir()
        (root/'core/bootstrap_economy_professions.py').write_text("VERSION = '112.00.0'\n",encoding='utf8')
        (root/'server.py').write_text('# old game; never run\n',encoding='utf8')
        (root/'soulbound_world_seed.txt').write_text('private-seed',encoding='utf8')
        (root/'soulbound_control.json').write_text('stale lock',encoding='utf8')
        db_path=root/'soulbound.db'
        conn=sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('CREATE TABLE characters(id INTEGER PRIMARY KEY, exp INTEGER)')
        conn.execute('CREATE TABLE eq(id INTEGER PRIMARY KEY, material BLOB)')
        conn.execute('INSERT INTO characters VALUES(3,999999)')
        conn.execute('INSERT INTO eq VALUES(7,?)',(b'\x00\xffcustom-eq',))
        conn.commit()
        assert (root/'soulbound.db-wal').exists();count+=1
        expected={f.relative_to(root):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*') if f.is_file()}
        # Fixture ZIP, NOT the release package.
        zip_path=root/'Soulbound-MUD-v113.00.0-test.zip'
        files={'server.py':'# new server\n','core/bootstrap_economy_professions.py':"VERSION = '113.00.0'\n",'VERSION':'113.00.0\n','START_Soulbound.bat':'@echo off\n','STOP_Soulbound.bat':'@echo off\n','predeploy_check.py':'# test\n'}
        with zipfile.ZipFile(zip_path,'w') as archive:
            for name,body in files.items():archive.writestr('Soulbound-MUD/'+name,body)
        with zipfile.ZipFile(zip_path) as z:mapping=archive_mapping(z)
        # Direct updater must reject inconsistent version before approval, backups, publication.
        with patch('systems.universal_release_update.validate_approval',side_effect=AssertionError('Should not reach approval')):
            expect_block(lambda:update(root,zip_path,'114.00.0',mapping,restart=False));count+=1
        with zipfile.ZipFile(zip_path,'w') as archive:
            for name,body in {**files,'VERSION':'114.00.0\n'}.items():archive.writestr('Soulbound-MUD/'+name,body)
        with zipfile.ZipFile(zip_path) as z:mapping=archive_mapping(z)
        with patch('systems.universal_release_update.validate_approval',side_effect=AssertionError('Should not reach approval')):
            expect_block(lambda:update(root,zip_path,'113.00.0',mapping,restart=False));count+=1
        with zipfile.ZipFile(zip_path,'w') as archive:
            for name,body in {**files,'VERSION':'113.00.0\n','core/bootstrap_economy_professions.py':"VERSION = '114.00.0'\n"}.items():archive.writestr('Soulbound-MUD/'+name,body)
        with zipfile.ZipFile(zip_path) as z:mapping=archive_mapping(z)
        with patch('systems.universal_release_update.validate_approval',side_effect=AssertionError('Should not reach approval')):
            expect_block(lambda:update(root,zip_path,'113.00.0',mapping,restart=False));count+=1
        with zipfile.ZipFile(zip_path,'w') as archive:
            for name,body in files.items():archive.writestr('Soulbound-MUD/'+name,body)
        with zipfile.ZipFile(zip_path) as z:mapping=archive_mapping(z)
        (root/'VERSION').write_text('110.00.0\n',encoding='utf8')
        with patch('systems.universal_release_update.validate_approval',side_effect=AssertionError('Should not reach approval')):
            expect_block(lambda:update(root,zip_path,'113.00.0',mapping,restart=False));count+=1
        (root/'VERSION').write_text('112.00.0\n',encoding='utf8')
        # Simulated end-to-end player data transfer; WAL transaction still committed in source.
        backup=parent/'backup';backup.mkdir()
        for f in root.iterdir():
            if f.is_file() and f.name!='Soulbound-MUD-v113.00.0-test.zip':
                (backup/f.name).write_bytes(f.read_bytes())
        stage=parent/'.stage';stage.mkdir();(stage/'server.py').write_text('# new server\n')
        (stage/'VERSION').write_text('113.00.0\n')
        stats=carry_saved_data(backup,stage,protected)
        assert stats['sqlite_files']==1 and stats['tables_checked']==2;count+=1
        with closing(sqlite3.connect(stage/'soulbound.db')) as new:
            assert new.execute('SELECT exp FROM characters WHERE id=3').fetchone()==(999999,);count+=1
            assert new.execute('SELECT material FROM eq WHERE id=7').fetchone()==(b'\x00\xffcustom-eq',);count+=1
            assert new.execute('PRAGMA integrity_check').fetchone()==('ok',);count+=1
        assert not (stage/'soulbound.db-wal').exists();count+=1
        assert (stage/'soulbound_world_seed.txt').read_text()=='private-seed';count+=1
        assert not (stage/'soulbound_control.json').exists();count+=1
        assert (stage/'server.py').read_text()=='# new server\n';count+=1
        expect_block(lambda:publish_clean(stage,parent/'new',lambda _:False));count+=1
        assert not (parent/'new').exists();count+=1
        published=publish_clean(stage,parent/'new',lambda p:(p/'VERSION').read_text().strip()=='113.00.0')
        assert published.is_dir();count+=1
        # No mutation of the preexisting game. WAL remains under the original root.
        for f,digest in expected.items():
            assert hashlib.sha256((root/f).read_bytes()).hexdigest()==digest,f
        count+=1
        expect_block(lambda:publish_clean(parent/'new',parent/'new',lambda _:True));count+=1
        conn.close()
    print('UNIVERSAL END TO END (synthetic): '+str(count)+'/18 PASS')

if __name__=='__main__':run()
