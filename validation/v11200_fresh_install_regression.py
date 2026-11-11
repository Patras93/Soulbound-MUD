# -*- coding: utf-8 -*-
"""v112: clean install without launching broken v110/v111; synthetic files only."""
from __future__ import annotations
import ast
from contextlib import closing
import hashlib
import sqlite3
import tempfile
from pathlib import Path
from shutil import copytree

from systems.v11200_fresh_install import (
    FreshInstallError,target_for,carry_saved_data,publish_clean)
from aktualizuj_soulbound import protected

ROOT=Path(__file__).resolve().parents[1]


def run():
    checks=0
    with tempfile.TemporaryDirectory(prefix='sb112_fresh_safe_') as td:
        base=Path(td)
        old=base/'Soulbound-MUD';old.mkdir()
        (old/'VERSION').write_text('110.00.0\n',encoding='utf8')
        (old/'server.py').write_text('raise RuntimeError("BROKEN OLD SERVER")',encoding='utf8')
        (old/'soulbound_world_seed.txt').write_text('seed-from-user',encoding='utf8')
        (old/'soulbound_control.json').write_text('stale process',encoding='utf8')
        db=old/'soulbound.db'
        with closing(sqlite3.connect(db)) as sql, sql:
            sql.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY,name TEXT, exp INTEGER)')
            sql.execute('CREATE TABLE v107_eq_production_cutover(cutover_version TEXT,backup_name TEXT)')
            sql.execute('INSERT INTO characters VALUES(1,\'Ala\',43210)')
            sql.execute('INSERT INTO v107_eq_production_cutover VALUES(\'107.00.0\',\'EQ_BACKUP.sqlite\')')
            sql.commit()
        source_hash={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.is_file()}
        backup=base/'Soulbound_BACKUP';copytree(old,backup)
        stage=base/'.Soulbound_stage_123';stage.mkdir()
        (stage/'VERSION').write_text('112.00.0\n',encoding='utf8')
        (stage/'server.py').write_text('# current v112 game',encoding='utf8')
        stats=carry_saved_data(backup,stage,protected)
        assert stats['sqlite_files']==1 and stats['tables_checked']==2,stats
        checks+=1
        assert (stage/'soulbound_world_seed.txt').read_text()=='seed-from-user'
        assert not (stage/'soulbound_control.json').exists()
        checks+=2
        assert (stage/'server.py').read_text()=='# current v112 game'
        assert not any(x.name.endswith('.soulbound-new') for x in stage.rglob('*'))
        checks+=2
        with closing(sqlite3.connect(stage/'soulbound.db')) as sql, sql:
            assert sql.execute('PRAGMA integrity_check').fetchone()==('ok',)
            assert sql.execute('SELECT * FROM characters').fetchone()==(1,'Ala',43210)
            assert sql.execute('SELECT * FROM v107_eq_production_cutover').fetchone()==('107.00.0','EQ_BACKUP.sqlite')
            checks+=3
        target=target_for(old)
        assert target==base/'Soulbound-MUD_V112_NOWA' and not target.exists()
        checks+=1
        verifier=lambda p:(p/'VERSION').read_text('utf8').strip()=='112.00.0'
        assert publish_clean(stage,target,verifier)==target
        assert target.exists() and not stage.exists()
        checks+=2
        assert source_hash=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.is_file()}
        assert (old/'server.py').read_text().startswith('raise RuntimeError')
        checks+=2
        another=base/'.Soulbound_stage_456';another.mkdir();(another/'VERSION').write_text('112.00.0')
        try:publish_clean(another,target,verifier)
        except FreshInstallError:checks+=1
        else:raise AssertionError('new install overwrote existing target')
        assert another.is_dir() and (target/'soulbound.db').exists()
        checks+=1
        try:target_for(old,'111.00.0')
        except FreshInstallError:checks+=1
        else:raise AssertionError('wrong release version accepted')
        failed=base/'.Soulbound_stage_bad';failed.mkdir();(failed/'VERSION').write_text('111.00.0')
        try:publish_clean(failed,base/'INVALID_TARGET',verifier)
        except FreshInstallError:checks+=1
        else:raise AssertionError('unsigned staging published')
        assert not (base/'INVALID_TARGET').exists()
        checks+=1
        # Failure after rename must restore unpublished stage, not leave a broken install.
        post=base/'.Soulbound_stage_post';post.mkdir();(post/'VERSION').write_text('112.00.0')
        attempts=iter((True,False))
        try:publish_clean(post,base/'POST_FAIL',lambda p:next(attempts))
        except FreshInstallError:checks+=1
        else:raise AssertionError('manifest mismatch after publish accepted')
        assert post.exists() and not (base/'POST_FAIL').exists()
        checks+=1
        empty=base/'EMPTY_BACKUP';empty.mkdir()
        try:carry_saved_data(empty,failed,protected)
        except FreshInstallError:checks+=1
        else:raise AssertionError('empty save backup accepted')
        bad=base/'CORRUPTED_BACKUP';bad.mkdir();(bad/'soulbound.db').write_bytes(b'corrupted sqlite')
        try:carry_saved_data(bad,failed,protected)
        except FreshInstallError:checks+=1
        else:raise AssertionError('corrupted save backup accepted')
        # The permanent deploy flow passes --fresh, without a second prompt.
        deploy=(ROOT/'wdroz_po_predeploy.py').read_text('utf8')
        assert "'--yes','--fresh'" in deploy
        checks+=1
        bat=(ROOT/'WDROZ_PO_PREDEPLOY.bat').read_text('utf8')
        assert "'VERSION','systems/v11200_activation.py'" in bat
        checks+=1
        updater=(ROOT/'aktualizuj_soulbound.py').read_text('utf8')
        tree=ast.parse(updater)
        assert 'carry_saved_data(backup,stage,protected)' in updater
        assert 'publish_clean(stage,target,verify)' in updater
        assert 'stop_local_server(root)' in updater  # unreachable in fresh v112 branch
        assert "raise UpdateError('v112: instalacja w miejscu jest wylaczona" in updater
        checks+=1
    print('V112 CZYSTA INSTALACJA: '+str(checks)+' PASS, sqlite, backup, old code intact, no overwrite')
    return checks

if __name__=='__main__':run()
