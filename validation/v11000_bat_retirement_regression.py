# -*- coding: utf-8 -*-
"""V110: no versioned install BAT/Python bridges or historical BAT archive.

Historical safe-migration behavior is still exercised with private fixtures.
Nothing is removed from a real existing installation by this regression.
"""
from __future__ import annotations
import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
from narzedzia.porzadki_bat import ORIGINAL_SHA256
from systems.v11000_retired_installers import RETIRED_V109_SHA256,RETIRED_ROOT_BATS_V110,RETIRED_VALIDATION_PY_V110,retire

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_MARKER = b'### UNIVERSAL SOULBOUND PYTHON BOOTSTRAP, NEVER EXECUTED AS BAT ###'


def run_regression():
    count = 0
    def ck(condition, reason):
        nonlocal count
        if not condition:
            raise AssertionError('V110 LEGACY BAT: '+reason)
        count += 1

    ck(len(ORIGINAL_SHA256)==51,'51 reviewed historic SHA entries preserved')
    ck(len(RETIRED_V109_SHA256)==75,'75 exact certified old files for safe retirement')
    ck(len(RETIRED_VALIDATION_PY_V110)==8,'8 obsolete diagnostic PY')
    ck(all(name.startswith('validation/') and name.endswith('.py') for name in RETIRED_VALIDATION_PY_V110),'only selected validation PY files')
    for name in RETIRED_VALIDATION_PY_V110:
        ck(not (ROOT/name).exists(),'retired validation PY absent: '+name)
        ck(RETIRED_V109_SHA256[name]==RETIRED_VALIDATION_PY_V110[name], 'certified Python SHA256 preserved: '+name)
    ck(len(RETIRED_ROOT_BATS_V110)==10,'10 certified obsolete root BATs')
    ck(all(name.lower().endswith('.bat') and '/' not in name for name in RETIRED_ROOT_BATS_V110),
       'only root BATs in v110 retiring list')
    essential={
      'AKTUALIZUJ_Soulbound.bat','AUTOSTART_WLACZ_Soulbound.bat',
      'AUTOSTART_WYLACZ_Soulbound.bat','BACKUP_TERAZ_Soulbound.bat',
      'PREDEPLOY_NOWEJ_WERSJI.bat','START_Soulbound.bat',
      'STATUS_Soulbound.bat','STOP_Soulbound.bat',
      'Start-Soulbound-Windows.bat','TESTUJ_Soulbound.bat',
      'WDROZ_PO_PREDEPLOY.bat',
    }
    ck({p.name for p in ROOT.glob('*.bat')}==essential,
       'exact 11 supported Windows BAT entrypoints')
    ck(not list(ROOT.rglob('*.cmd')),'no stray CMD in v110 release')
    for name in RETIRED_ROOT_BATS_V110:
        ck(not (ROOT/name).exists(),'retired root BAT absent: '+name)
        ck(RETIRED_V109_SHA256[name]==RETIRED_ROOT_BATS_V110[name],
           'certified SHA256 carried into in-place upgrade: '+name)
    ck({p.rsplit('/',1)[-1] for p in RETIRED_V109_SHA256 if p.startswith('narzedzia/bat_historyczne/')}==set(ORIGINAL_SHA256),
       'all 51 archive filenames covered by safe old-file retirement')
    for relative, digest in RETIRED_V109_SHA256.items():
        ck(len(digest)==64 and all(ch in '0123456789abcdef' for ch in digest),
           'certified SHA256 format: '+relative)
    archive = ROOT/'narzedzia'/'bat_historyczne'
    ck(not list(archive.glob('*.bat')),'legacy executable archive must be empty')
    for name in ORIGINAL_SHA256:
        ck(not (archive/name).exists(),'historical BAT still shipped: '+name)
    for pattern in ('wdroz_v*_z_zewnatrz.py', 'predeploy_v*_z_zewnatrz.py',
                    'PREDEPLOY_V*_Z_ZEWNATRZ.bat', 'WDROZ_V*_Z_ZEWNATRZ.bat',
                    'V*_WDROZ_Z_ZEWNATRZ.bat', 'V*_PREDEPLOY_Z_ZEWNATRZ.bat'):
        ck(not list(ROOT.glob(pattern)),'versioned root entrypoint: '+pattern)
    for name in ('PREDEPLOY_NOWEJ_WERSJI.bat','WDROZ_PO_PREDEPLOY.bat'):
        data=(ROOT/name).read_bytes()
        ck(data.count(BRIDGE_MARKER)==3,'single universal bootstrap marker in '+name)
        source=data.rsplit(BRIDGE_MARKER,1)[1]
        # Code in the one permanent BAT is self-contained and Python-parseable.
        ast.parse(source.decode('utf-8'),filename=name)
        ck(b'from predeploy_v109' not in source and b'wdroz_v109' not in source,
           'no legacy Python imports in '+name)
    from validation.v10800_bat_cleanup_regression import run as v108
    from validation.v10900_bat_cleanup_regression import run as v109
    ck(v108()>=120,'safe v108 BAT migration fixture')
    ck(v109()>=130,'safe v109 BAT migration fixture')
    # Simulate an in-place v109->v110 upgrade. Only exact, backed-up bytes
    # may be removed; user-edited BATs and symlinks must be preserved.
    with TemporaryDirectory(prefix='v110-bat-minimal-') as tmp:
        src=Path(tmp)/'live'; saved=Path(tmp)/'backup'
        src.mkdir(); saved.mkdir()
        scripts=list(RETIRED_ROOT_BATS_V110)
        original=scripts[0]; changed=scripts[1]
        old_py, changed_py=list(RETIRED_VALIDATION_PY_V110)[:2]
        fixture=b'@echo off\r\nREM obsolete fixture\r\n'
        expected=hashlib.sha256(fixture).hexdigest()
        old_a=RETIRED_V109_SHA256[original]
        old_b=RETIRED_V109_SHA256[changed]
        old_py_hash=RETIRED_V109_SHA256[old_py]
        changed_py_hash=RETIRED_V109_SHA256[changed_py]
        RETIRED_V109_SHA256[original]=expected
        RETIRED_V109_SHA256[changed]=expected
        RETIRED_V109_SHA256[old_py]=expected
        RETIRED_V109_SHA256[changed_py]=expected
        try:
            for folder in (src,saved):
                (folder/original).write_bytes(fixture)
                (folder/changed).write_bytes(fixture if folder==saved else fixture+b'REM modified\r\n')
                for rel in (old_py,changed_py):
                    p=folder/rel; p.parent.mkdir(parents=True,exist_ok=True)
                    p.write_bytes(fixture if rel==old_py or folder==saved else fixture+b'# changed\n')
                # An unrelated private Python script is never targeted.
                private=folder/'validation/custom_user_script.py'
                private.write_bytes(b'print(123)\n')
            removed,preserved=retire(src,saved)
            ck(set(removed)=={original,old_py},'matching obsolete BAT and Python removed after full backup')
            ck(changed_py in preserved,'user-modified obsolete PY preserved')
            ck(changed in preserved,'modified user BAT preserved')
            ck(not (src/original).exists(),'old BAT gone from install root')
            ck((saved/original).read_bytes()==fixture,'original remains in permanent backup')
            ck((src/changed).exists(),'changed BAT never removed')
            ck(not (src/old_py).exists(),'old diagnostic Python removed')
            ck((saved/old_py).read_bytes()==fixture,'diagnostic Python preserved in backup')
            ck((src/changed_py).exists(),'modified Python preserved')
            ck((src/'validation/custom_user_script.py').exists(),'unrecognized Python untouched')
            removed2,preserved2=retire(src,saved)
            ck(not removed2 and changed in preserved2 and changed_py in preserved2,'rerun is idempotent')
            try: retire(src,src/'missing-backup')
            except RuntimeError: count+=1
            else: raise AssertionError('missing backup must block cleanup')
        finally:
            RETIRED_V109_SHA256[original]=old_a
            RETIRED_V109_SHA256[changed]=old_b
            RETIRED_V109_SHA256[old_py]=old_py_hash
            RETIRED_V109_SHA256[changed_py]=changed_py_hash
    return count


if __name__=='__main__':
    print('V110 BAT RETIREMENT:',run_regression(),'PASS; no production changes',flush=True)
