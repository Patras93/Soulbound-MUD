# -*- coding: utf-8 -*-
"""Production v108 authorization bound to one exact Windows 60/60+ candidate.

No staging environment variable can grant production approval. The updater
verifies the official 60/60 PLUS proof and exact ZIP BEFORE server STOP, then
persists an installer-issued manifest of SHA256 hashes inside LIVE_CONTENT.
A normal restart verifies that manifest and installed runtime modules without
requiring temporary PREDEPLOY results or keeping the downloaded ZIP.
"""
from __future__ import annotations
from functools import lru_cache
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'LIVE_CONTENT/v108_release_activation.json'
# v107 content and physical-EQ modules remain required in v108. Any modified
# runtime adapter is included in the verified candidate source surface.
from systems.v10700_activation import REQUIRED as V107_REQUIRED
REQUIRED = tuple(dict.fromkeys((*V107_REQUIRED,
    'systems/v10700_activation.py',
    'systems/v10800_activation.py', 'systems/v10800_predeploy_isolation.py',
    'systems/v10800_eq_cutover_bridge.py', 'validation/v10800_eq_rebuild_copy.py',
    'systems/v10700_live_equipment.py',
    'validation/v10800_v107_equipment_compat_gate.py',
    'validation/v10800_release_readiness.py',
    'testuj_soulbound_windows.py', 'predeploy_nowej_wersji.py',
    'aktualizuj_soulbound.py', 'wdroz_v108_z_zewnatrz.py',
    'predeploy_v108_z_zewnatrz.py',
    'core/bootstrap_economy_professions.py',
    'systems/v10800_seasonal_events.py', 'systems/v10800_pacing_metrics.py',
    'systems/experience_bank_v2011.py', 'server/mud_server.py',
    'player/session_mixins/social_expansion.py',
    'player/session_mixins/command_registry.py',
    'player/session_mixins/session_runtime_state.py',
    'player/session_mixins/combat_rewards.py',
    'player/session_methods_v4200/ioauthcharacter_part03.py',
    'VERSION')))


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as reader:
        for buf in iter(lambda: reader.read(1024*1024), b''):
            digest.update(buf)
    return digest.hexdigest()


def _valid_digest(value):
    return (isinstance(value, str) and len(value) == 64
            and all(ch in '0123456789abcdef' for ch in value))


def activation_manifest(state, archive_path, staged_root):
    """Installer-only: convert verified Windows approval into durable proof.

    This helper MUST be called only by run_update after its fail-closed
    require_v104_official_predeploy() check. It never approves a candidate.
    """
    if (state.get('status') != 'PASS' or state.get('quality_gate') != 'ULTIMATE-60-PLUS'
        or type(state.get('returncode')) is not int or state['returncode'] != 0
        or type(state.get('completed_stages')) is not int or state['completed_stages'] != 60
        or type(state.get('required_stages')) is not int or state['required_stages'] != 60
        or state.get('v108_release_gates_pass') is not True
        or state.get('v108_eq_rebuild_trial_pass') is not True
        or state.get('version') != '108.00.0'
        or state.get('installed_at_test') != '107.00.0'
        or not _valid_digest(state.get('sha256'))
        or _sha256(archive_path) != state['sha256']):
        raise ValueError('v108: niezatwierdzony wynik PREDEPLOY przed wystawieniem manifestu')
    # Release verification is not enough if files in the staging directory
    # are replaced AFTER ZIP extraction. Compare the *entire* staged tree to
    # the approved archive BEFORE the live server is stopped, then issue the
    # durable manifest. This also rejects unexpected injected stage files.
    from aktualizuj_soulbound import archive_mapping
    stage = Path(staged_root)
    with zipfile.ZipFile(archive_path) as approved:
        mapping = archive_mapping(approved)
        staged_files = {p.relative_to(stage) for p in stage.rglob('*') if p.is_file()}
        if set(mapping) != staged_files:
            raise ValueError('v108: staging zawiera inne pliki niż zatwierdzony ZIP')
        for rel, member in mapping.items():
            item = stage / rel
            if not item.is_file() or item.is_symlink():
                raise ValueError('v108: brak lub dowiązanie w stagingu: ' + str(rel))
            digest = hashlib.sha256(approved.read(member)).hexdigest()
            if _sha256(item) != digest:
                raise ValueError('v108: zmieniony plik stagingu względem ZIP: ' + str(rel))
    checksums = {}
    for rel in REQUIRED:
        item = stage / rel
        if not item.is_file() or item.is_symlink():
            raise ValueError('v108: brakuje pliku do uwierzytelnienia: ' + rel)
        checksums[rel] = _sha256(item)
    return {
        'schema': 2,
        'version': '108.00.0',
        'sha256': state['sha256'],
        'installed_at_test': '107.00.0',
        'quality_gate': 'ULTIMATE-60-PLUS',
        'completed_stages': 60,
        'required_stages': 60,
        'returncode': 0,
        'status': 'PASS',
        'v108_release_gates_pass': True,
        'v108_eq_rebuild_trial_pass': True,
        'files': checksums,
    }


def _check(root):
    """Validate installed code only. PREDEPLOY is disposable after install."""
    root = Path(root)
    if (root/'VERSION').read_text(encoding='utf-8-sig').strip() != '108.00.0':
        return False
    marker_file = root / MARKER
    if marker_file.is_symlink():
        return False
    marker = json.loads(marker_file.read_text(encoding='utf-8'))
    if (not isinstance(marker, dict)
        or type(marker.get('schema')) is not int or marker['schema'] != 2
        or marker.get('version') != '108.00.0'
        or marker.get('installed_at_test') != '107.00.0'
        or marker.get('status') != 'PASS'
        or marker.get('quality_gate') != 'ULTIMATE-60-PLUS'
        or type(marker.get('completed_stages')) is not int or marker['completed_stages'] != 60
        or type(marker.get('required_stages')) is not int or marker['required_stages'] != 60
        or type(marker.get('returncode')) is not int or marker['returncode'] != 0
        or marker.get('v108_release_gates_pass') is not True
        or marker.get('v108_eq_rebuild_trial_pass') is not True
        or not _valid_digest(marker.get('sha256'))):
        return False
    hashes = marker.get('files')
    if not isinstance(hashes, dict) or set(hashes) != set(REQUIRED):
        return False
    for rel in REQUIRED:
        expected = hashes[rel]
        installed = root / rel
        if (not _valid_digest(expected) or not installed.is_file()
            or installed.is_symlink() or _sha256(installed) != expected):
            return False
    return True


@lru_cache(maxsize=1)
def production_approved():
    try:
        return _check(ROOT)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return False


def verify_root_for_test(root):
    try:
        return _check(Path(root))
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return False
