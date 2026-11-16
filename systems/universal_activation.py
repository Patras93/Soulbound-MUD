# -*- coding: utf-8 -*-
"""Version-neutral activation of future Soulbound releases.

The target candidate brings this module with it. No prior-release module,
manifest, archive, PREDEPLOY folder or script is needed after publication.
"""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
from pathlib import Path
from functools import lru_cache

ROOT=Path(__file__).resolve().parents[1]
MARKER='LIVE_CONTENT/release_current.json'
REQUIRED=(
    'VERSION','server.py','core/bootstrap_economy_professions.py',
    'core/release_version.py',
    'systems/runtime_activation.py','systems/universal_activation.py',
    'systems/universal_release_update.py','systems/current_fresh_install.py',
    'aktualizuj_soulbound.py','predeploy_nowej_wersji.py','wdroz_po_predeploy.py',
    'PREDEPLOY_NOWEJ_WERSJI.bat','WDROZ_PO_PREDEPLOY.bat',
    'START_Soulbound.bat','STOP_Soulbound.bat',
)

def current_version(root=ROOT):
    version=(Path(root)/'VERSION').read_text(encoding='utf-8-sig').strip()
    chunks=version.split('.')
    if len(chunks)!=3 or any(not c.isdigit() for c in chunks):
        raise ValueError('Niepoprawny VERSION')
    return version

VERSION=current_version()

def sha(file):
    digest=hashlib.sha256()
    with Path(file).open('rb') as reader:
        for block in iter(lambda:reader.read(1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()

def _digest(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def _safe_rel(rel):
    return (isinstance(rel,str) and rel and not rel.startswith(('/','\\'))
            and '\\' not in rel and ':' not in rel and '..' not in Path(rel).parts)

def verify(root):
    try:
        root=Path(root)
        version=current_version(root)
        marker=root/MARKER
        if marker.is_symlink():return False
        data=json.loads(marker.read_text(encoding='utf-8'))
        if isinstance(data,dict) and data.get('schema')==2:
            from systems.current_install import verify_marker
            return verify_marker(root,data)
        if (not isinstance(data,dict) or type(data.get('schema')) is not int
            or data['schema']!=1 or data.get('version')!=version
            or data.get('status')!='PASS' or data.get('quality_gate')!='ULTIMATE-60-PLUS'
            or data.get('source_gate')!='WINDOWS_PREDEPLOY_APPROVED'
            or not _digest(data.get('archive_sha256'))):return False
        files=data.get('files')
        if not isinstance(files,dict) or not set(REQUIRED).issubset(files):return False
        for rel,expected in files.items():
            if not _safe_rel(rel) or not _digest(expected):return False
            if rel.casefold()=='changelog_pl.txt':continue
            file=root/rel
            if file.is_symlink() or not file.is_file() or sha(file)!=expected:return False
        return True
    except (OSError,ValueError,TypeError,KeyError,UnicodeError):return False

def activation_manifest(state,archive_path,stage,mapping):
    version=current_version(stage)
    if (state.get('status')!='PASS' or state.get('quality_gate')!='ULTIMATE-60-PLUS'
        or type(state.get('returncode')) is not int or state.get('returncode')!=0
        or type(state.get('completed_stages')) is not int or state['completed_stages']!=60
        or type(state.get('required_stages')) is not int or state['required_stages']!=60
        or state.get('version')!=version or state.get('release_gates_pass') is not True
        or not isinstance(state.get('installed_at_test'),str)
        or state.get('sha256')!=sha(archive_path)):
        raise ValueError('Brak zgodnego PREDEPLOY 60/60 PLUS')
    stage=Path(stage)
    hashes={}
    for relative in mapping:
        rel=Path(relative).as_posix()
        if rel==MARKER or not _safe_rel(rel):
            raise ValueError('Niebezpieczny wpis w manifescie: '+rel)
        file=stage/rel
        if not file.is_file() or file.is_symlink():
            raise ValueError('Brak pliku aktywacji: '+rel)
        if rel.casefold()=='changelog_pl.txt':continue
        hashes[rel]=sha(file)
    if not set(REQUIRED).issubset(hashes):
        raise ValueError('Niekompletna uniwersalna instalacja')
    return {'schema':1,'version':version,'status':'PASS',
            'quality_gate':'ULTIMATE-60-PLUS','source_gate':'WINDOWS_PREDEPLOY_APPROVED',
            'archive_sha256':state['sha256'],'files':dict(sorted(hashes.items()))}

@lru_cache(maxsize=1)
def production_approved():return verify(ROOT)

def _test_database(db_path):
    """Permit only a disposable TEMP SQLite on localhost, never real saves."""
    if os.environ.get('SOULBOUND_UNIVERSAL_STAGING')!='1':return False
    if os.environ.get('SOULBOUND_HOST')!='127.0.0.1':return False
    try:
        port=int(os.environ.get('SOULBOUND_PORT',''))
        if not 1025<=port<=65535 or port==4000:return False
        file=Path(db_path)
        if file.is_symlink() or file.suffix.casefold() not in ('.db','.sqlite','.sqlite3'):
            return False
        resolved=file.resolve(strict=False)
        rel=resolved.relative_to(Path(tempfile.gettempdir()).resolve(strict=True))
        # The real-TCP UOSS regression has a second, exclusively temporary
        # clone with the conventional database name. Accept exactly that
        # clone (and never the normal game's root database).
        uoss_clone = (len(rel.parts)==3
            and rel.parts[0].casefold().startswith('soulbound_uoss_real_')
            and rel.parts[1].casefold()=='gra'
            and rel.parts[2].casefold()=='soulbound.db'
            and resolved.parent==ROOT.resolve())
        if uoss_clone:return True
        if len(rel.parts)<2 or file.name.casefold()=='soulbound.db':return False
        # A test stage and its independent child fixtures both run inside the
        # operating system TEMP directory. The stage flag, private DB, non-game
        # port and localhost are ALL mandatory; naming alone never authorizes.
        # These are names of test fixtures, not release-version dependencies.
        approved_prefixes=(
            'soulbound-predeploy-stage-', 'soulbound-predeploy-sqlite-frozen_',
            'sbcurrent_fast_', 'soulbound-full-audit-',
            'soulbound-coverage-', 'soulbound-catalogue-',
            'soulbound-tcp5-', 'sb-ultra-', 'sb-ultimate-',
            'sb-ultimate60-clone-',
            'sb-current-', 'sb_current_install_',
            # Existing archived regression fixtures. No old code is imported.
            'sb110_', 'sb111_', 'sb112_',
        )
        # The fixture must be an immediate child of TEMP; DBs may be nested
        # one folder deeper for additional isolation.
        if not rel.parts[0].casefold().startswith(approved_prefixes):return False
        if len(rel.parts)<2:return False
        return True
    except (OSError,ValueError,TypeError,RuntimeError):return False

def authorized_mode(db_path):
    if production_approved():return 'production'
    if _test_database(db_path):return 'test'
    raise PermissionError('Brak zatwierdzonego wydania lub bezpiecznej bazy testowej')

def enabled():return production_approved() or _test_database(os.environ.get('SOULBOUND_DB',''))
