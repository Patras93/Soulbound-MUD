# -*- coding: utf-8 -*-
"""v110: jeden stały manifest bieżącej instalacji, bez historycznych skryptów.

Produkcyjny serwer wymaga poświadczenia wystawionego po zatwierdzonym Windows
PREDEPLOY. Test lokalny może pracować tylko na osobnej bazie w TEMP.
"""
from __future__ import annotations
import hashlib,json,os,tempfile
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='110.00.0'
MARKER='LIVE_CONTENT/release_current.json'
CORE=(
    'VERSION','server.py','server/mud_server.py','storage/database.py',
    'world/dynamic_content.py','core/bootstrap_economy_professions.py',
    'player/session_mixins/command_registry.py',
    'player/session_mixins/command_special_handlers.py',
    'core/v11000_archetypes.py','core/archetypes_v110/profession_timing_v110.py','core/v11000_runtime_catalogue.py',
    'world/v11000_realms.py',
    'systems/v11000_activation.py','systems/v11000_retired_installers.py',
    'systems/events_v110/combat.py',
    'systems/v11000_profession_work.py',
)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def _valid_sha(digest):
    return isinstance(digest,str) and len(digest)==64 and all(c in '0123456789abcdef' for c in digest)

def _version(root):
    return (root/'VERSION').read_text(encoding='utf-8-sig').strip()

def verify(root):
    """No reference to v107/v108/v109 installer files or transient PREDEPLOY."""
    try:
        root=Path(root)
        if _version(root)!=VERSION or (root/MARKER).is_symlink():return False
        record=json.loads((root/MARKER).read_text(encoding='utf-8'))
        if (not isinstance(record,dict) or type(record.get('schema')) is not int
            or record['schema']!=1 or record.get('version')!=VERSION
            or record.get('status')!='PASS' or record.get('quality_gate')!='ULTIMATE-60-PLUS'
            or record.get('source_gate')!='WINDOWS_PREDEPLOY_APPROVED'
            or not _valid_sha(record.get('archive_sha256'))):return False
        hashes=record.get('files')
        if not isinstance(hashes,dict) or not set(CORE)<=set(hashes):return False
        # Do not trust a manifest which omits newly installed source modules.
        for rel,expected in hashes.items():
            if (not isinstance(rel,str) or not rel or rel.startswith(('/','\\'))
                or '\\' in rel or '..' in Path(rel).parts
                or not _valid_sha(expected)):return False
            item=root/rel
            if not item.is_file() or item.is_symlink() or sha(item)!=expected:return False
        return True
    except (OSError,ValueError,TypeError,KeyError,UnicodeError):return False

def activation_manifest(state,archive_path,staged_root,approved_files):
    """Installer-only: certify exact extracted ZIP and matching Windows PREDEPLOY.

    No historical install scripts, marker names or previous-release manifests.
    The supplied file list comes from the ZIP's already-validated mapping.
    """
    if (state.get('status')!='PASS' or state.get('quality_gate')!='ULTIMATE-60-PLUS'
        or state.get('version')!=VERSION or state.get('returncode')!=0
        or state.get('completed_stages')!=60 or state.get('required_stages')!=60
        or state.get('v110_release_gates_pass') is not True
        or state.get('sha256')!=sha(archive_path)):
        raise ValueError('v110: brak zgodnego zatwierdzenia Windows PREDEPLOY.')
    staged_root=Path(staged_root)
    hashes={}
    for rel in approved_files:
        rel=str(rel).replace('\\','/')
        if rel==MARKER or rel.startswith(('/', '\\')) or '..' in Path(rel).parts:
            raise ValueError('v110: niedopuszczalny plik manifestu: '+rel)
        file=staged_root/rel
        if not file.is_file() or file.is_symlink():
            raise ValueError('v110: brak pliku w zatwierdzonym stagingu: '+rel)
        hashes[rel]=sha(file)
    if not set(CORE).issubset(hashes):
        raise ValueError('v110: niekompletny zestaw modułów i testów.')
    return {'schema':1,'version':VERSION,'status':'PASS',
        'quality_gate':'ULTIMATE-60-PLUS','source_gate':'WINDOWS_PREDEPLOY_APPROVED',
        'archive_sha256':state['sha256'],'files':dict(sorted(hashes.items()))}

@lru_cache(maxsize=1)
def production_approved():return verify(ROOT)

def _test_database(db_path):
    # Flag alone cannot authorize the production soulbound.db.
    if (os.environ.get('SOULBOUND_V110_STAGING')!='1'
        or os.environ.get('SOULBOUND_V107_STAGING')!='1'
        or os.environ.get('SOULBOUND_V109_STAGING')!='1'):
        return False
    try:
        path=Path(db_path).resolve(strict=False)
        tmp=Path(tempfile.gettempdir()).resolve(strict=True)
        rel=path.relative_to(tmp)
        if (len(rel.parts)<2 or path.suffix.casefold() not in ('.db','.sqlite','.sqlite3')
            or Path(db_path).is_symlink()):return False
        # v85 uses a second clean, synthetic UOSS source cloned into
        # TEMP/Soulbound_UOSS_REAL_<unique>/gra/soulbound.db. This is the
        # ONLY permitted soulbound.db test path, and only when the Python
        # module itself is running inside that exact private copied tree.
        private_uoss = (
            len(rel.parts)==3 and
            rel.parts[0].lower().startswith('soulbound_uoss_real_') and
            rel.parts[1].lower()=='gra' and rel.parts[2].lower()=='soulbound.db'
            and ROOT.resolve()==path.parent
            and (path.parent/'VERSION').is_file()
        )
        if path.name.casefold()=='soulbound.db' and not private_uoss:return False
        # Only explicitly recognized PREDEPLOY/test workspaces may run an
        # unapproved candidate. A flag alone NEVER authorizes a player DB.
        # Only loopback ephemeral ports are permitted for any sandbox server.
        if os.environ.get('SOULBOUND_HOST') != '127.0.0.1':return False
        try: port=int(os.environ.get('SOULBOUND_PORT',''))
        except (TypeError,ValueError):return False
        if not 1025 <= port <= 65535 or port == 4000:return False
        # Legacy FAST PREDEPLOY creates a uniquely named sb104 TCP lab.
        # Accept only that exact disposable DB on loopback and an ephemeral
        # non-production port, with the child marker. No generic sb104 files.
        if (len(rel.parts)==2 and rel.parts[0].lower().startswith('sb104_tcp_lab_')
            and rel.parts[1].lower()=='tcp_test.sqlite'
            and os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'):
            try:port=int(os.environ.get('SOULBOUND_PORT',''))
            except (TypeError,ValueError):return False
            return 1025<=port<=65535 and port!=4000
        if private_uoss:
            return True
        name=rel.parts[0].lower()
        ordinary_prefixes=(
            'sb110_', 'soulbound-v110-',
            'soulbound-predeploy-stage-', 'soulbound-full-audit-',
            'soulbound-coverage-',
        )
        # Exact historical test-suite disposable folders, never a generic
        # TEMP database. These names occur only inside dedicated tests.
        expected_test_files={
            'soulbound-tcp5-': 'five_players.sqlite',
            'sb-ultra-5-tcp-': 'stress.db',
            'sb-ultimate-tcp-waves-': 'wave.sqlite',
            'sb-ultra-sqlite-migrate-': 'candidate.db',
            'sb-ultimate-real-row-check-': 'isolated.sqlite',
            'sb-ultimate60-clone-': 'candidate.sqlite',
        }
        if any(name.startswith(prefix) for prefix in ordinary_prefixes):
            # At least one nested filename, never a bare TEMP root.
            return len(rel.parts) >= 2
        return len(rel.parts)==2 and any(
            name.startswith(prefix) and rel.parts[1].lower()==basename
            for prefix,basename in expected_test_files.items()
        )
    except (OSError,ValueError,TypeError):return False

def authorized_mode(db_path):
    if production_approved():return 'production'
    if _test_database(db_path):return 'test'
    raise PermissionError('v110: brak zatwierdzonej instalacji lub odizolowanej bazy testowej')

def enabled():
    return production_approved() or _test_database(os.environ.get('SOULBOUND_DB',''))
