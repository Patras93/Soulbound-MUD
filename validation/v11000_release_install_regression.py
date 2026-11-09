# -*- coding: utf-8 -*-
"""v110: symulacja pełnej instalacji i blokady SHA na sztucznym korzeniu.

Nie otwiera portu, nie zatrzymuje serwera, nie modyfikuje produkcji.
"""
from __future__ import annotations
import hashlib,json,sqlite3,sys,tempfile,zipfile
from contextlib import closing
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import aktualizuj_soulbound as updater
from systems.v11000_activation import CORE,verify,sha
from systems.v11000_retired_installers import RETIRED_V109_SHA256, RETIRED_VALIDATION_PY_V110


def _require_closed(conn: sqlite3.Connection) -> None:
    # Enforce Windows-safe cleanup even when regression runs on Linux, where
    # unlinking an open SQLite database may otherwise silently succeed.
    try:
        conn.execute('SELECT 1')
    except sqlite3.ProgrammingError:
        return
    raise AssertionError('v110: otwarte polaczenie SQLite w tescie aktualizatora')


def main():
    with tempfile.TemporaryDirectory(prefix='sb110_updater_offline_') as tmp:
        home=Path(tmp);live=home/'Soulbound-MUD';live.mkdir()
        (live/'core').mkdir()
        (live/'core/bootstrap_economy_professions.py').write_text("VERSION = '109.00.0'\n",encoding='utf-8')
        (live/'legacy_player_note.txt').write_text('Nie usuwać pliku użytkownika.\n',encoding='utf-8')
        certified_legacy=b'@echo off\r\nREM simulated exact v109 launcher\r\n'
        modified_legacy=b'User customized this legacy script; keep my changes\n'
        (live/'wdroz_v109_z_zewnatrz.py').write_bytes(certified_legacy)
        (live/'wdroz_v108_z_zewnatrz.py').write_bytes(modified_legacy)
        old_py, modified_py = list(RETIRED_VALIDATION_PY_V110)[:2]
        for rel, body in ((old_py, certified_legacy), (modified_py, modified_legacy)):
            p=live/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(body)
        (live/'soulbound.db').touch()
        # sqlite3.Connection.__exit__ handles COMMIT/ROLLBACK but does NOT
        # close the SQLite handle. On Windows an open handle makes the final
        # TemporaryDirectory cleanup fail with WinError 32.
        with closing(sqlite3.connect(live/'soulbound.db')) as db:
            with db:
                db.execute('CREATE TABLE v107_eq_production_cutover(x INTEGER)')
                db.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY,login TEXT)')
                db.execute('INSERT INTO accounts(login) VALUES (?)',('zachowaj',))
        _require_closed(db)
        archive=home/'Soulbound-MUD-v110.00.0-CANDIDATE.zip'
        allowed=set(CORE)|{'server.py','CHANGELOG_PL.txt','START_Soulbound.bat',
                            'STOP_Soulbound.bat','predeploy_check.py'}
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for rel in sorted(allowed):
                z.write(ROOT/rel,'Soulbound-MUD/'+rel)
        checksum=sha(archive)
        predeploy=home/'Soulbound_PREDEPLOY';predeploy.mkdir()
        result=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',version='110.00.0',
                    completed_stages=60,required_stages=60,returncode=0,
                    installed_at_test='109.00.0',v110_release_gates_pass=True,
                    zip=str(archive.resolve()),sha256=checksum)
        statefile=predeploy/'last_result.json'
        def save():statefile.write_text(json.dumps(result),encoding='utf-8')
        save()
        # Any SHA mismatch, missing v110 gate, or wrong source version stops before backup.
        updater.require_v104_official_predeploy(live,archive,'110.00.0')
        for key,bad in [('sha256','0'*64),('v110_release_gates_pass',False),
                        ('installed_at_test','108.00.0')]:
            good=result[key];result[key]=bad;save()
            try:updater.require_v104_official_predeploy(live,archive,'110.00.0')
            except updater.UpdateError as exc:
                assert str(exc), "Unsafe approval must be rejected with a reason"
            else:raise AssertionError('v110: preflight przyjął niepoprawne '+key)
            result[key]=good;save()
        orig_stop=updater.stop_local_server
        updater.stop_local_server=lambda _:False
        try:
            with patch.dict(RETIRED_V109_SHA256, {
                'wdroz_v109_z_zewnatrz.py': hashlib.sha256(certified_legacy).hexdigest(),
                old_py: hashlib.sha256(certified_legacy).hexdigest(),
                modified_py: hashlib.sha256(certified_legacy).hexdigest()
            }):
                backup=updater.run_update(live,archive,'110.00.0',restart=False)
        finally:updater.stop_local_server=orig_stop
        assert verify(live),'v110: manifest po zakończonej instalacji niespójny'
        assert (live/'legacy_player_note.txt').read_text(encoding='utf-8').startswith('Nie usuwać')
        assert (live/'core/bootstrap_economy_professions.py').read_text(encoding='utf-8').find('110.00.0')>=0
        assert (backup/'core/bootstrap_economy_professions.py').read_text(encoding='utf-8').find('109.00.0')>=0
        with closing(sqlite3.connect(live/'soulbound.db')) as db:
            assert db.execute('SELECT login FROM accounts').fetchone()==('zachowaj',)
        _require_closed(db)
        # Certified legacy installer is retired; user-modified one survives.
        assert not (live/'wdroz_v109_z_zewnatrz.py').exists()
        assert (live/'wdroz_v108_z_zewnatrz.py').read_bytes() == modified_legacy
        assert (backup/'wdroz_v109_z_zewnatrz.py').read_bytes() == certified_legacy
        assert (backup/'wdroz_v108_z_zewnatrz.py').read_bytes() == modified_legacy
        assert not (live/old_py).exists(), 'old unmodified Python diagnostic left behind'
        assert (live/modified_py).read_bytes()==modified_legacy, 'modified Python should be preserved'
        assert (backup/old_py).read_bytes()==certified_legacy, 'diagnostic must be in permanent backup'
        assert (backup/modified_py).read_bytes()==modified_legacy
        assert not (live/'LIVE_CONTENT/v109_release_activation.json').exists()
        before=(live/'core/bootstrap_economy_professions.py').read_bytes()
        release_marker=live/'LIVE_CONTENT/release_current.json'
        marker=json.loads(release_marker.read_text(encoding='utf-8'))
        assert marker['archive_sha256']==checksum
        assert len(marker['files'])==len(allowed)
        # A changed file must fail independently of any historic approval.
        (live/'core/bootstrap_economy_professions.py').write_bytes(before+b'\n# tampered\n')
        assert not verify(live)
        from validation.v11000_dispatch_regression import run_regression as check_dispatch
        assert check_dispatch() == 8, 'v110: candidate updater dispatch failed'
        print('V110 UPDATE OFFLINE PASS: staged ZIP SHA, gate, rollback backup, '
              f'{len(marker["files"])} independently hashed files, preserved SQLite; '
              'no historical installer scripts',flush=True)

if __name__=='__main__':main()
