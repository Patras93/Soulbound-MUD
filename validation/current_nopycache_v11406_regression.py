# -*- coding: utf-8 -*-
"""v114.00.6: never write project bytecode; retire ONLY disposable caches."""
from __future__ import annotations
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def _before_project_import(file):
    lines=(ROOT/file).read_text(encoding='utf-8')
    tree=ast.parse(lines)
    first=next(i for i,node in enumerate(tree.body)
               if isinstance(node,ast.ImportFrom) and node.module=='systems.runtime_activation')
    earlier=tree.body[:first]
    assert any(isinstance(n,ast.Import) and any(x.name=='sys' for x in n.names)
               for n in earlier),file
    assert any(isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant)
               and n.value.value is True and any(isinstance(t,ast.Attribute)
               and isinstance(t.value,ast.Name) and t.value.id=='sys'
               and t.attr=='dont_write_bytecode' for t in n.targets)
               for n in earlier),file


def run():
    checks=0
    _before_project_import('server.py'); checks+=1
    s=(ROOT/'uruchom_w_tle.py')
    if list(ROOT.glob('*.bat')) and s.is_file():
        text=s.read_text(encoding='utf-8'); head=text.split('from datetime import datetime',1)[0]
        assert 'sys.dont_write_bytecode = True' in head
        checks+=1
        # v114.00.7: pythonw autostart launches a SECOND Python interpreter.
        # The v114.00.6 guard only lived in the parent and could not prevent
        # watchdog/local imports from creating __pycache__ again.
        assert "'PYTHONDONTWRITEBYTECODE': '1'" in text, 'pythonw child must inherit flag'
        checks+=1
        for guarded, local_import in (
            ('supervisor_windows.py', 'windows_launcher_state'),
            ('host_windows.py', 'soulbound_backup_windows'),
            ('start_windows_bootstrap.py', None),
        ):
            source=(ROOT/guarded).read_text(encoding='utf-8')
            before=source.split('from '+local_import+' import',1)[0] if local_import else source.split('import runpy',1)[0]
            assert 'sys.dont_write_bytecode = True' in before,guarded
            checks+=1
        host=(ROOT/'host_windows.py').read_text(encoding='utf-8')
        assert '"PYTHONDONTWRITEBYTECODE": "1"' in host.split('process = subprocess.Popen',1)[0]
        checks+=1
        for bat in ROOT.glob('*.bat'):
            assert 'PYTHONDONTWRITEBYTECODE=1' in bat.read_text(encoding='utf-8'),bat.name
            checks+=1
        from systems.universal_release_update import retire_generated_bytecode_caches
        with tempfile.TemporaryDirectory(prefix='sb11406_nopycache_') as work:
            root=Path(work)/'Soulbound-MUD';root.mkdir()
            (root/'systems'/'deep'/'__pycache__').mkdir(parents=True)
            (root/'player'/'__pycache__').mkdir(parents=True)
            (root/'logs'/'__pycache__').mkdir(parents=True)
            (root/'systems'/'deep'/'__pycache__'/'alpha.cpython-314.pyc').write_bytes(b'junk')
            (root/'player'/'__pycache__'/'notes.txt').write_text('zostaw',encoding='utf-8')
            (root/'logs'/'__pycache__'/'log.cpython-314.pyc').write_bytes(b'private')
            count=retire_generated_bytecode_caches(root)
            assert count==(1,1),count;checks+=1
            assert not (root/'systems'/'deep'/'__pycache__').exists();checks+=1
            assert (root/'player'/'__pycache__'/'notes.txt').read_text()=='zostaw';checks+=1
            assert (root/'logs'/'__pycache__'/'log.cpython-314.pyc').read_bytes()==b'private';checks+=1
            assert retire_generated_bytecode_caches(root)==(0,0);checks+=1
    else:
        shell=(ROOT/'START_Soulbound.sh').read_text(encoding='utf-8')
        assert 'python3 -B' in shell;checks+=1
        unit=(ROOT/'systems/linux_release.py').read_text(encoding='utf-8')
        assert "'ExecStart='+exe+' -u '" in unit  # service compatibility unchanged
        checks+=1
    # Candidate development notes must not be installed, even if present
    # in an untrusted archive. Remove only exact known old bytes from disk.
    from aktualizuj_soulbound import production_release_mapping
    note_names=('v114_REMOVED_EDITOR_FILES_AUDIT.txt','v114_WORK_IN_PROGRESS.txt')
    assert not any((ROOT/name).exists() for name in note_names)
    checks+=1
    sample={Path(name):None for name in (*note_names,'server.py','VERSION')}
    selected=production_release_mapping(sample)
    assert set(selected)=={Path('server.py'),Path('VERSION')}
    checks+=1
    from release_readme_cleanup import cleanup_legacy_readmes,V114_CANDIDATE_ONLY_NOTES
    legacy_note=('KANDYDAT v114.00.0. NIE WDRAZAC bez realnego PREDEPLOY 60/60 PLUS.\n'
                 'Pelny aktualny status w CZYTAJ_NAJPIERW_V114_PL.txt.\n')
    import hashlib
    assert hashlib.sha256(legacy_note.encode('utf-8')).hexdigest()==V114_CANDIDATE_ONLY_NOTES['v114_WORK_IN_PROGRESS.txt']
    checks+=1
    with tempfile.TemporaryDirectory(prefix='sb11407_notes_') as tmp:
        home=Path(tmp); root=home/'Soulbound-MUD';root.mkdir()
        # Explicit bytes are essential: Path.write_text on Windows may
        # translate LF to CRLF, changing the protected SHA256. The prior
        # test then incorrectly expected an edited file to be deleted.
        old=root/note_names[1]
        old.write_bytes(legacy_note.encode('utf-8'))
        assert hashlib.sha256(old.read_bytes()).hexdigest() == V114_CANDIDATE_ONLY_NOTES[note_names[1]]
        edited=root/note_names[0];edited.write_text('ZMIENIONY PLIK — NIE USUWAJ',encoding='utf-8')
        retired,saved=cleanup_legacy_readmes(root,home/'archive')
        assert retired==[note_names[1]] and not old.exists(),retired
        assert (saved/note_names[1]).read_text(encoding='utf-8')==legacy_note
        assert edited.is_file() and edited.read_text(encoding='utf-8')=='ZMIENIONY PLIK — NIE USUWAJ'
        checks+=4
        # A CRLF-normalized file really has different bytes. Retain it
        # rather than silently deleting locally modified documentation.
        crlf_note=legacy_note.replace('\n','\r\n').encode('utf-8')
        old.write_bytes(crlf_note)
        retired_crlf, saved_crlf=cleanup_legacy_readmes(root,home/'another_archive')
        assert retired_crlf==[] and saved_crlf is None
        assert old.read_bytes()==crlf_note
        checks+=2
    # Real module import without -B, env flag, or PYCACHEPREFIX, under an isolated path.
    # A sibling python module imported after the early guard cannot create __pycache__.
    with tempfile.TemporaryDirectory(prefix='sb11406_import_') as work:
        root=Path(work)
        (root/'payload.py').write_text('VALUE = 42\n',encoding='utf-8')
        (root/'entry.py').write_text('import sys\nsys.dont_write_bytecode=True\nimport payload\nassert payload.VALUE==42\n',encoding='utf-8')
        env=dict(os.environ)
        env.pop('PYTHONDONTWRITEBYTECODE',None)
        env.pop('PYTHONPYCACHEPREFIX',None)
        p=subprocess.run([sys.executable,str(root/'entry.py')],cwd=root,env=env,
                         capture_output=True,text=True,timeout=15)
        assert p.returncode==0,(p.returncode,p.stderr);checks+=1
        assert not (root/'__pycache__').exists();checks+=1
    print(f'NO PYCACHE v114.00.8: {checks} controls PASS')
    return 0


if __name__=='__main__':raise SystemExit(run())
