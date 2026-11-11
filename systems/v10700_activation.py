# -*- coding: utf-8 -*-
"""Activation of authored v107 content after a verified Windows upgrade.

Staging stays isolated. A normal server only enables v107 content after the
updater has installed a marker tied to the exact 60/60 PLUS-approved archive.
The presence of VERSION=107 alone never grants authorization.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'LIVE_CONTENT/v107_release_activation.json'
REQUIRED = (
    'server.py', 'world/dynamic_content.py',
    'core/bootstrap_economy_professions.py',
    'core/archetypes/chaos.py',
    'core/live_level_caps_v5200.py',
    'world/v10700_chaos_chapter_one.py',
    'world/v10700_chaos_chapters_2_6.py',
    'world/v10700_saga_760_quests.py',
    'world/v10700_insects_expansion.py',
    'world/v10700_insects_wildlife_plus.py',
    'player/session_mixins/command_registry.py',
    'player/session_mixins/command_special_handlers.py',
    'player/session_mixins/io_auth_character.py',
    'player/session_methods_v4200/ioauthcharacter_part02.py',
    'systems/content_registry.py',
    'systems/magitek/magicite.py',
    # Gear-ledger authorization must cover every mutable runtime adapter;
    # a modified addon must not operate under the old release marker.
    'storage/database.py', 'storage/db_inventory.py',
    'server/mud_server.py', 'systems/v10700_live_equipment.py',
    'player/session_mixins/forge_guilds.py',
    'systems/equipment_shadow_slots_v10600.py',
    'systems/equipment_inventory_flow_v10600.py',
    'systems/equipment_evolution_command_v10600.py',
    'systems/equipment_evolution_stats_v10600.py',
    'systems/equipment_crafting_guard_v10600.py',
    'systems/v10700_equipment_write_barrier.py',
    'systems/v10700_eq_runtime_gate.py',
)


def _sha256(path):
    with Path(path).open('rb') as stream:
        digest=hashlib.sha256()
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            digest.update(chunk)
        return digest.hexdigest()


def _check(root):
    root=Path(root)
    if (root/'VERSION').read_text(encoding='utf-8-sig').strip() != '107.00.0':
        return False
    marker=json.loads((root/MARKER).read_text(encoding='utf-8'))
    state=json.loads((root.parent/'Soulbound_PREDEPLOY'/'last_result.json').read_text(encoding='utf-8'))
    if (not isinstance(marker,dict) or not isinstance(state,dict)
        or marker.get('schema') != 1 or marker.get('version') != '107.00.0'
        or state.get('version') != '107.00.0'
        or state.get('installed_at_test') not in ('105.00.0','106.00.0')
        or state.get('quality_gate') != 'ULTIMATE-60-PLUS'
        or state.get('status') != 'PASS' or state.get('returncode') != 0
        or state.get('completed_stages') != 60 or state.get('required_stages') != 60
        or marker.get('sha256') != state.get('sha256')):
        return False
    archive_path=Path(state['zip']).resolve(strict=True)
    if _sha256(archive_path)!=state['sha256']:
        return False
    # Exact source modules in the running installation must match the approved
    # archive. A stale, missing or tampered file fails closed at startup.
    with zipfile.ZipFile(archive_path) as archive:
        all_names={info.filename:info for info in archive.infolist() if not info.is_dir()}
        prefix='Soulbound-MUD/' if 'Soulbound-MUD/server.py' in all_names else ''
        for relative in REQUIRED:
            entry=all_names.get(prefix+relative)
            if entry is None or not (root/relative).is_file():
                return False
            if hashlib.sha256(archive.read(entry)).digest()!=hashlib.sha256(
                    (root/relative).read_bytes()).digest():
                return False
    return True


@lru_cache(maxsize=1)
def _approved():
    try:
        return _check(ROOT)
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile,
            json.JSONDecodeError, UnicodeError):
        return False


def production_approved():
    """Current release first: no historical PREDEPLOY/activation dependency.

    v112 startup must validate exactly its own installed release manifest.
    Earlier released versions keep their old checks for compatibility.
    """
    try:
        current=(ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()
        if current == '112.00.0':
            from systems.v11200_activation import production_approved as current_approved
            return current_approved()
        if current == '111.00.0':
            from systems.v11100_holiday_activation import production_approved as current_approved
            return current_approved()
        if current == '110.00.0':
            from systems.v11000_activation import production_approved as current_approved
            return current_approved()
        if current == '109.00.0':
            from systems.v10900_activation import production_approved as current_approved
            return current_approved()
        if current == '108.00.0':
            from systems.v10800_activation import production_approved as current_approved
            return current_approved()
        return _approved()
    except (ImportError, OSError):
        return False


def enabled():
    # A v112 test uses ONLY v112's own staging contract, not a collection of
    # historical v107/v109/v110/v111 flags. Production still needs approval.
    try:
        if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()=='112.00.0':
            from systems.v11200_activation import enabled as current_enabled
            return bool(current_enabled())
    except OSError:
        return False
    # Historical version fixture semantics are preserved for 60/60 regression.
    if os.environ.get('SOULBOUND_V107_STAGING')=='1':
        return True
    return production_approved()


def verify_root_for_test(root):
    """No global cache, used only for adversarial test fixtures."""
    try:return _check(Path(root))
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile,
            json.JSONDecodeError, UnicodeError):return False
