# -*- coding: utf-8 -*-
"""Fail-closed v109 boot: explicit private trial or installed release attestation."""
from __future__ import annotations
import os
import tempfile
from pathlib import Path


def private_trial_allowed(db_path):
    if (os.environ.get('SOULBOUND_V109_STAGING') != '1'
            or os.environ.get('SOULBOUND_V107_STAGING') != '1'):
        return False
    try:
        temp=Path(tempfile.gettempdir()).resolve(strict=True)
        path=Path(db_path).expanduser().resolve(strict=False)
        if path.suffix.lower() not in ('.sqlite','.db','.sqlite3'):
            return False
        relative=path.relative_to(temp)
        # Never mistake an extracted PREDEPLOY candidate (which also lives in
        # Windows TEMP) for a disposable SQLite fixture.  In particular the
        # canonical game DB must NEVER be authorized by staging flags alone.
        # The production mode below requires an exact installed-code manifest.
        if path.name.casefold() == 'soulbound.db':
            return False
        if Path(db_path).is_symlink() or Path(db_path).parent.is_symlink():
            return False
        parts=tuple(part.casefold() for part in relative.parts[:-1])
        if any(part.startswith(('soulbound-predeploy-workers-',
                                'soulbound_predeploy_')) for part in parts):
            return False
        # Reject any SQLite file located under a staged or installed game
        # source tree, even if that source tree is inside a named TEMP folder.
        for parent in path.parents:
            if parent == temp:
                break
            if (parent/'VERSION').is_file() and (parent/'server.py').is_file():
                return False
        # Historyczny szybki PREDEPLOY v104 uruchamia własną odizolowaną
        # bazę dokładnie TEMP/sb104_tcp_lab_*/tcp_test.sqlite na loopback.
        # Wsparcie dotyczy wyłącznie tej bazy, a nie produkcyjnego katalogu.
        if (len(relative.parts)==2 and relative.parts[0].startswith('sb104_tcp_lab_')
                and relative.parts[1]=='tcp_test.sqlite'
                and os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
                and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
                and not Path(db_path).is_symlink()):
            try:
                port=int(os.environ.get('SOULBOUND_PORT',''))
            except (TypeError,ValueError):
                return False
            return 1025 <= port <= 65535 and port != 4000
        if len(relative.parts)<2:
            return False
        return any(part.lower().startswith((
            'soulbound-','soulbound_','sb-v109-','sb109_','sb109-'))
            for part in relative.parts[:-1])
    except (OSError,ValueError,TypeError):return False


def _official_predeploy_clone_allowed(db_path, installation):
    """Allow ONLY historical 60+ gate SQLite copies, never a live database.

    The old test runner uses v108's official TEMP worker and loopback flags,
    but some schema/coverage tests create a second, separately named TEMP DB.
    These fixtures must not be confused with an installed v109 runtime.
    """
    import re
    from systems.v10800_predeploy_isolation import authorized_predeploy_test
    env=os.environ
    if env.get('SOULBOUND_V108_PREDEPLOY') != '1':
        return False
    if env.get('SOULBOUND_HOST') != '127.0.0.1':
        return False
    try:
        port=int(env.get('SOULBOUND_PORT',''))
        if not 1025 <= port <= 65535 or port == 4000:
            return False
        base=Path(tempfile.gettempdir()).resolve(strict=True)
        code=Path(installation)
        database=Path(db_path)
        if code.is_symlink() or database.is_symlink() or database.parent.is_symlink():
            return False
        worker=code.resolve(strict=True).relative_to(base).parts
        fixture=database.resolve(strict=False).relative_to(base).parts
        if (len(worker) != 2 or not worker[0].lower().startswith('soulbound-predeploy-workers-')
                or not re.fullmatch(r'candidate-[0-9]+',worker[1].lower())
                or len(fixture) != 2):
            return False
        folder,name=fixture
        fixtures={
            'sb-ultra-sqlite-migrate-': 'candidate.db',
            'sb-ultimate-real-row-check-': 'isolated.sqlite',
            'sb-ultimate60-clone-': 'candidate.sqlite',
            'soulbound-catalog-test-': 'db.sqlite',
        }
        return any(folder.lower().startswith(prefix) and name.lower() == filename
                   for prefix,filename in fixtures.items())
    except (OSError,ValueError,TypeError):
        return False


def authorized_runtime(db_path, *, root=None):
    if private_trial_allowed(db_path):
        return 'trial'
    from systems.v10900_activation import ROOT,production_approved,verify_root_for_test
    installation=Path(root) if root is not None else ROOT
    # Keep all v108 regression servers available in verified disposable
    # worker folders.  This narrow predeploy route checks loopback, port,
    # named test SQLite, source directory and the real v108 test flag.
    # It grants NO access to the canonical production DB.
    from systems.v10800_predeploy_isolation import authorized_predeploy_test
    if (authorized_predeploy_test(installation,db_path)
            or _official_predeploy_clone_allowed(db_path,installation)):
        return 'trial'
    # Do not allow environment flags or an approved code tree to authorize an
    # arbitrary SQLite path. Production DB must be the canonical local file.
    raw=Path(db_path).expanduser()
    expected=installation/'soulbound.db'
    try:
        if (raw.is_symlink() or expected.is_symlink()
            or raw.resolve(strict=False)!=expected.resolve(strict=False)
            or not expected.is_file()):
            return None
        approved=production_approved() if root is None else verify_root_for_test(installation)
        return 'production' if approved else None
    except (OSError,ValueError,TypeError):return None


def ensure_authorized_start(db_path, *, root=None):
    mode=authorized_runtime(db_path,root=root)
    if mode is None:
        raise PermissionError('v109: brak autoryzowanego PREDEPLOY i trwałego dowodu instalacji. '
                              'Produkcja v108 pozostaje bez zmian.')
    return mode


# Historical name retained only for isolated regression code.
def ensure_private_trial(db_path):
    if not private_trial_allowed(db_path):
        raise PermissionError('v109: dozwolona tylko odizolowana baza testowa w TEMP')
