# -*- coding: utf-8 -*-
"""v111: trwała autoryzacja kodu po zatwierdzonym PREDEPLOY Windows.

Samo VERSION, flaga środowiska ani obecność pliku JSON nie dają zgody.
Manifest generuje wyłącznie aktualizator po dokładnym SHA i 60/60 PLUS.
Po wdrożeniu TEMP/Soulbound_PREDEPLOY można usunąć.
"""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '111.00.0'
MARKER = 'LIVE_CONTENT/release_current.json'
# The current release owns its own protection contract.  Old v110 markers,
# installer scripts and runtime lists are never needed to certify a finished v111.
# Any future change to this list is reviewed within the v111 release itself.
V111_CORE = (
    'VERSION', 'server.py', 'server/mud_server.py', 'storage/database.py',
    'world/dynamic_content.py', 'core/bootstrap_economy_professions.py',
    'player/session_mixins/command_registry.py',
    'player/session_mixins/command_special_handlers.py',
    'core/archetypes/expansion.py', 'core/archetypes/expansion_parts/profession_timing_v110.py',
    'core/archetypes/runtime_catalogue.py', 'world/v11000_realms.py',
    'systems/v11000_activation.py', 'systems/global_events/combat.py',
    'systems/v11000_profession_work.py',
)
REQUIRED = tuple(dict.fromkeys((*V111_CORE,
    'server/mud_server.py', 'core/progression_600.py',
    'systems/gifts_v109/policy.py', 'systems/v10700_activation.py',
    'systems/v11100_holiday_activation.py',
    'systems/v10700_live_equipment.py',
    'systems/holiday/calendar.py',
    'data/tzdb/Europe_Warsaw.tzif',
    'systems/holiday/schedule.py',
    'systems/holiday/events.py',
    'systems/holiday/challenges.py',
    'systems/holiday/combat.py',
    'systems/holiday/prizes.py',
    'world/holiday_expareas.py',
    'player/session_mixins/combat_rewards.py',
    'predeploy_nowej_wersji.py',
    'wdroz_po_predeploy.py', 'aktualizuj_soulbound.py',
)))

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as reader:
        for block in iter(lambda: reader.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

def _digest(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def verify(root):
    try:
        root=Path(root)
        if (root/'VERSION').read_text(encoding='utf-8-sig').strip()!=VERSION:
            return False
        marker=root/MARKER
        if marker.is_symlink():return False
        data=json.loads(marker.read_text(encoding='utf-8'))
        if (not isinstance(data,dict) or type(data.get('schema')) is not int or
            data['schema']!=1 or data.get('version')!=VERSION or
            data.get('status')!='PASS' or data.get('quality_gate')!='ULTIMATE-60-PLUS' or
            data.get('source_gate')!='WINDOWS_PREDEPLOY_APPROVED' or
            not _digest(data.get('archive_sha256'))):return False
        files=data.get('files')
        if not isinstance(files,dict) or not set(REQUIRED)<=set(files):return False
        for rel, expected in files.items():
            if (not isinstance(rel,str) or not rel or rel.startswith(('/','\\'))
                or '\\' in rel or '..' in Path(rel).parts or not _digest(expected)):
                return False
            # Opis zmian nie jest elementem bezpieczenstwa ani wymogu startu.
            if rel.casefold() == 'changelog_pl.txt':
                continue
            file=root/rel
            if file.is_symlink() or not file.is_file() or sha(file)!=expected:
                return False
        return True
    except (OSError,ValueError,TypeError,KeyError,UnicodeError):return False


def activation_manifest(state,archive_path,stage,mapping):
    if (state.get('status')!='PASS' or state.get('quality_gate')!='ULTIMATE-60-PLUS'
        or type(state.get('returncode')) is not int or state['returncode']!=0
        or state.get('completed_stages')!=60 or state.get('required_stages')!=60
        or state.get('version')!=VERSION or state.get('installed_at_test')!='110.00.0'
        or state.get('v111_release_gates_pass') is not True
        or state.get('sha256')!=sha(archive_path)):
        raise ValueError('v111: brak zatwierdzenia PREDEPLOY 60/60 i bramek v111')
    stage=Path(stage)
    hashes={}
    for relative in mapping:
        rel=str(relative).replace('\\','/')
        if rel==MARKER or rel.startswith(('/','\\')) or '..' in Path(rel).parts:
            raise ValueError('v111: niebezpieczny wpis manifestu: '+rel)
        file=stage/rel
        if not file.is_file() or file.is_symlink():raise ValueError('v111: brak pliku: '+rel)
        # Dokumentacja ma pozostać aktualizowalna bez dezaktywowania gry.
        if rel.casefold() == 'changelog_pl.txt':
            continue
        hashes[rel]=sha(file)
    if not set(REQUIRED)<=set(hashes):
        raise ValueError('v111: niekompletna instalacja')
    return {'schema':1,'version':VERSION,'status':'PASS',
        'quality_gate':'ULTIMATE-60-PLUS','source_gate':'WINDOWS_PREDEPLOY_APPROVED',
        'archive_sha256':state['sha256'],'files':dict(sorted(hashes.items()))}

@lru_cache(maxsize=1)
def production_approved():
    if verify(ROOT):
        return True
    try:
        if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip() == '112.00.0':
            from systems.v11200_activation import production_approved as v112_approved
            return v112_approved()
    except (OSError, ImportError, UnicodeError):
        return False
    return False

def _test_database(db_path):
    # Nie korzystamy z samej flagi v111 jako dowodu. Test musi mieć własną bazę,
    # host localhost i port inny niż produkcyjny.
    from systems.v11000_activation import _test_database as legacy_private_db
    if (os.environ.get('SOULBOUND_V111_STAGING')!='1' or
        os.environ.get('SOULBOUND_V110_STAGING')!='1'):
        return False
    return legacy_private_db(db_path)

def authorized_mode(db_path):
    if production_approved():return 'production'
    if _test_database(db_path):return 'test'
    raise PermissionError('v111: brak zatwierdzonego wydania lub bezpiecznej bazy testowej')

def enabled():
    try:
        if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()=='112.00.0':
            from systems.v11200_activation import enabled as current_enabled
            return bool(current_enabled())
    except (OSError, ImportError):
        return False
    return production_approved() or _test_database(os.environ.get('SOULBOUND_DB',''))
