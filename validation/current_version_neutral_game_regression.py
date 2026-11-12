# -*- coding: utf-8 -*-
"""Guard core gameplay and fresh install against release-specific activation."""
from __future__ import annotations
from pathlib import Path
import sqlite3
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems import current_install
from systems.current_install_ledger import initialize_empty_ledger
from systems.universal_activation import current_version

ROOT=Path(__file__).resolve().parents[1]
TARGETS=(
 'systems/runtime_activation.py',
 'player/session_mixins/command_special_handlers.py',
 'systems/magitek/magicite.py',
 'systems/holiday/combat.py',
 'systems/current_install.py',
 'systems/current_install_bootstrap.py',
 'systems/current_install_ledger.py',
)

def run():
    checks=0
    for name in TARGETS:
        content=(ROOT/name).read_text(encoding='utf-8')
        assert 'from systems.v11200_activation import' not in content, name
        assert 'SOULBOUND_V112_STAGING' not in content, name
        checks+=2
    from aktualizuj_soulbound import production_release_mapping
    assert 'systems/v11200_activation.py' not in {p.as_posix() for p in production_release_mapping({Path('systems/v11200_activation.py'):None,Path('systems/runtime_activation.py'):None})}
    checks+=1
    from core.release_version import load_version
    from aktualizuj_soulbound import file_version,read_archive_version,archive_mapping
    import zipfile
    assert load_version(ROOT)==current_version(ROOT)
    assert file_version(ROOT/'core/bootstrap_economy_professions.py')==load_version(ROOT)
    checks+=2
    with tempfile.TemporaryDirectory(prefix='sb_version_zip_') as temporary:
        archive=Path(temporary)/'candidate.zip'
        with zipfile.ZipFile(archive,'w') as z:
            for rel in ('VERSION','core/bootstrap_economy_professions.py','core/release_version.py'):
                z.write(ROOT/rel, 'Soulbound-MUD/'+rel)
            for rel in ('server.py','START_Soulbound.bat','STOP_Soulbound.bat','predeploy_check.py'):
                z.writestr('Soulbound-MUD/'+rel,'fixture')
        with zipfile.ZipFile(archive) as z:
            mapping=archive_mapping(z)
            assert read_archive_version(z,mapping)==load_version(ROOT)
        checks+=1
    assert current_install.VERSION==current_version(ROOT)
    assert current_install.VALIDATORS[0]=='validation.current_universal_release_suite'
    checks+=2
    for future in ('113.00.0','114.09.2','220.00.0'):
        with tempfile.TemporaryDirectory(prefix='sb_current_versions_') as temp:
            root=Path(temp)
            (root/'VERSION').write_text(future,encoding='utf-8')
            assert current_version(root)==future
            checks+=1
    with tempfile.TemporaryDirectory(prefix='sb_current_install_unit_') as temp:
        db=sqlite3.connect(Path(temp)/'scratch.sqlite')
        try:
            for table in ('accounts','characters','inventory','equipment','bank_items','profession_storage'):
                db.execute('CREATE TABLE '+table+' (id INTEGER)')
            db.commit()
            result=initialize_empty_ledger(db)
            assert result['version']==current_version(ROOT)
            assert db.execute('SELECT version FROM current_install_origin').fetchone()[0]==current_version(ROOT)
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            checks+=3
        finally:db.close()
    print(f'VERSION-NEUTRAL GAME: {checks}/{checks} PASS')

if __name__=='__main__':run()
