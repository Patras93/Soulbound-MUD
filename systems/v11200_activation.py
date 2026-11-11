# -*- coding: utf-8 -*-
"""v112: samodzielne zatwierdzenie aktualizacji z v111 po PREDEPLOY Windows.

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
VERSION = '112.00.0'
MARKER = 'LIVE_CONTENT/release_current.json'
# The current release owns its own protection contract.  Old v110 markers,
# installer scripts and runtime lists are never needed to certify a finished v111.
# Any future change to this list is reviewed within the v112 release itself.
V112_CORE = (
    'VERSION', 'server.py', 'server/mud_server.py', 'storage/database.py',
    'world/dynamic_content.py', 'core/bootstrap_economy_professions.py',
    'player/session_mixins/command_registry.py',
    'player/session_mixins/command_special_handlers.py',
    'core/archetypes/expansion.py', 'core/archetypes/expansion_parts/profession_timing_v110.py',
    'core/archetypes/runtime_catalogue.py', 'world/v11000_realms.py',
    'systems/runtime_activation.py', 'systems/v11200_activation.py',
    'systems/current_install.py', 'systems/current_install_ledger.py',
    'systems/current_install_bootstrap.py',
    'systems/global_events/combat.py',
    'systems/profession_generations/__init__.py',
    'systems/profession_generations/chaos.py',
    'systems/profession_generations/expansion.py',
    'systems/eternal_glory/world.py',
    'systems/eternal_glory/companions.py',
    'systems/eternal_glory/depths.py',
    'systems/eternal_glory/infinite.py',
    'systems/eternal_glory/crafting.py',
    'systems/eternal_glory/class_guild.py',
    'systems/eternal_glory/story.py',
)
REQUIRED = tuple(dict.fromkeys((*V112_CORE,
    'server/mud_server.py', 'core/progression_600.py',
    'systems/gift_runtime.py', 'systems/gift_parts/policy.py',
    'systems/gift_parts/legacy.py', 'systems/gift_parts/payout.py',
    'systems/gift_parts/rewards.py', 'systems/gift_parts/delivery.py',
    'data/catalog_parts/items_01.py', 'data/catalog_parts/items_07.py',
    'data/catalog_parts/mobs_01.py', 'data/catalog_parts/mobs_02.py',
    'data/catalog_parts/npcs_01.py', 'data/catalog_parts/npcs_02.py',
    'data/catalog_parts/rooms_01.py', 'data/catalog_parts/rooms_04.py',
    'data/catalog_parts/__init__.py',
    'data/catalog_parts/items_02.py',
    'data/catalog_parts/items_03.py',
    'data/catalog_parts/items_04.py',
    'data/catalog_parts/items_05.py',
    'data/catalog_parts/items_06.py',
    'data/catalog_parts/rooms_02.py',
    'data/catalog_parts/rooms_03.py',
    'systems/gift_parts/__init__.py',
    'systems/v11200_activation.py',
    'systems/v11200_fresh_install.py',
    'world/runtime_gameplay_finalize.py',
    'systems/v10700_live_equipment.py',
    'systems/holiday/calendar.py',
    'data/tzdb/Europe_Warsaw.tzif',
    'systems/holiday/schedule.py',
    'systems/holiday/events.py',
    'systems/holiday/challenges.py',
    'systems/holiday/combat.py',
    'systems/holiday/prizes.py',
    'world/holiday_expareas.py',
    'world/realms/__init__.py',
    'world/realms/archipelag_sygnalow.py',
    'world/realms/bazylika_glosow.py',
    'world/realms/delta_przyplywow.py',
    'world/realms/entry.py',
    'world/realms/forteca_slonc.py',
    'world/realms/kanion_mechanizmow.py',
    'world/realms/ogrod_zorz.py',
    'world/realms/pustkowie_luster.py',
    'world/realms/puszcza_zarodnikow.py',
    'world/realms/serce_kontynentu.py',
    'world/realms/szczeliny_swiatla.py',
    'world/realms/wulkan_popiolu.py',
    'world/realms/ziemie_nocy.py',
    'world/horizons/__init__.py',
    'world/horizons/entry.py',
    'world/horizons/przebudzenie.py',
    'world/horizons/zapomniani.py',
    'world/horizons/wiecznosc.py',
    'world/horizon_index.py',
    'world/horizons_engine.py',

    # v112: moved holiday, Magitek and 38 archetype modules; no old module files.
    'core/archetypes/chaos.py',
    'core/archetypes/expansion.py',
    'core/archetypes/expansion_parts/__init__.py',
    'core/archetypes/expansion_parts/classes/__init__.py',
    'core/archetypes/expansion_parts/classes/egzekutor_pieczeci.py',
    'core/archetypes/expansion_parts/classes/fantomowy_szermierz.py',
    'core/archetypes/expansion_parts/classes/kartograf_przestrzeni.py',
    'core/archetypes/expansion_parts/classes/paladyn_zmierzchu.py',
    'core/archetypes/expansion_parts/classes/straznik_przypywow.py',
    'core/archetypes/expansion_parts/classes/szeptacz_bestii.py',
    'core/archetypes/expansion_parts/classes/wirtuoz_echa.py',
    'core/archetypes/expansion_parts/classes/zarowy_zniwiarz.py',
    'core/archetypes/expansion_parts/profession_timing_v110.py',
    'core/archetypes/expansion_parts/professions/__init__.py',
    'core/archetypes/expansion_parts/professions/alchemia_dzwieku.py',
    'core/archetypes/expansion_parts/professions/burzotronika.py',
    'core/archetypes/expansion_parts/professions/fitoarchitektura.py',
    'core/archetypes/expansion_parts/professions/hydrokartografia.py',
    'core/archetypes/expansion_parts/professions/kronikarstwo_materii.py',
    'core/archetypes/expansion_parts/professions/paleoekologia.py',
    'core/archetypes/expansion_parts/professions/technometeorologia.py',
    'core/archetypes/expansion_parts/professions/zwierciadlarstwo.py',
    'core/archetypes/expansion_parts/races/__init__.py',
    'core/archetypes/expansion_parts/races/gebinowcy.py',
    'core/archetypes/expansion_parts/races/lustrzanie.py',
    'core/archetypes/expansion_parts/races/miedzianie.py',
    'core/archetypes/expansion_parts/races/rezonanci.py',
    'core/archetypes/expansion_parts/races/selenici.py',
    'core/archetypes/expansion_parts/races/zaranie.py',
    'core/archetypes/expansion_parts/races/zarborny.py',
    'core/archetypes/expansion_parts/races/zarodnikowcy.py',
    'core/archetypes/runtime_catalogue.py',
    'core/magitek/catalogue.py',
    'systems/holiday/calendar.py',
    'systems/holiday/challenges.py',
    'systems/holiday/combat.py',
    'systems/holiday/events.py',
    'systems/holiday/prizes.py',
    'systems/holiday/schedule.py',
    'systems/magitek/magicite.py',
    'systems/magitek/rules.py',
    'systems/magitek/runtime.py',
    'systems/magitek/support.py',
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
        if isinstance(data, dict) and data.get('schema') == 2:
            from systems.current_install import verify_marker
            return verify_marker(root, data)
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
        or state.get('version')!=VERSION or state.get('installed_at_test') not in ('110.00.0','111.00.0')
        or state.get('v112_release_gates_pass') is not True
        or state.get('sha256')!=sha(archive_path)):
        raise ValueError('v112: brak zatwierdzenia PREDEPLOY 60/60 i bramek v112')
    stage=Path(stage)
    hashes={}
    for relative in mapping:
        rel=str(relative).replace('\\','/')
        if rel==MARKER or rel.startswith(('/','\\')) or '..' in Path(rel).parts:
            raise ValueError('v112: niebezpieczny wpis manifestu: '+rel)
        file=stage/rel
        if not file.is_file() or file.is_symlink():raise ValueError('v112: brak pliku: '+rel)
        # Dokumentacja ma pozostać aktualizowalna bez dezaktywowania gry.
        if rel.casefold() == 'changelog_pl.txt':
            continue
        hashes[rel]=sha(file)
    if not set(REQUIRED)<=set(hashes):
        raise ValueError('v112: niekompletna instalacja')
    return {'schema':1,'version':VERSION,'status':'PASS',
        'quality_gate':'ULTIMATE-60-PLUS','source_gate':'WINDOWS_PREDEPLOY_APPROVED',
        'archive_sha256':state['sha256'],'files':dict(sorted(hashes.items()))}

@lru_cache(maxsize=1)
def production_approved():return verify(ROOT)

def _test_database(db_path):
    """Isolated v112 lab authorization; no dependency on older activators.

    A staging flag is necessary but never sufficient: the database must be
    inside a recognized disposable TEMP lab, with localhost and a non-game
    port. Historical lab *names* remain accepted for regression compatibility;
    their Python modules, manifests and release markers are not consulted.
    """
    if os.environ.get('SOULBOUND_V112_STAGING') != '1':
        return False
    if os.environ.get('SOULBOUND_HOST') != '127.0.0.1':
        return False
    try:
        port = int(os.environ.get('SOULBOUND_PORT', ''))
        if not 1025 <= port <= 65535 or port == 4000:
            return False
        file = Path(db_path)
        if file.is_symlink() or file.suffix.casefold() not in ('.db', '.sqlite', '.sqlite3'):
            return False
        path = file.resolve(strict=False)
        rel = path.relative_to(Path(tempfile.gettempdir()).resolve(strict=True))
        if len(rel.parts) < 2:
            return False
        # Preserve the isolated UOSS fixture, never a real soulbound.db.
        private_uoss = (
            len(rel.parts) == 3
            and rel.parts[0].lower().startswith('soulbound_uoss_real_')
            and rel.parts[1].lower() == 'gra'
            and rel.parts[2].lower() == 'soulbound.db'
            and ROOT.resolve() == path.parent
            and (path.parent / 'VERSION').is_file()
        )
        if file.name.casefold() == 'soulbound.db' and not private_uoss:
            return False
        if private_uoss:
            return True
        name = rel.parts[0].lower()
        # The names below designate temporary test fixtures, not previous
        # release dependencies. The directory must be beneath system TEMP.
        if (len(rel.parts) == 2 and name.startswith('sb104_tcp_lab_')
            and rel.parts[1].lower() == 'tcp_test.sqlite'):
            return os.environ.get('SOULBOUND_TCP_TEST_CHILD') == '1'
        lab_prefixes = (
            'sb112_', 'sb111_', 'sb110_', 'soulbound-v110-',
            'soulbound-predeploy-stage-', 'soulbound-full-audit-',
            'soulbound-coverage-',
        )
        if any(name.startswith(prefix) for prefix in lab_prefixes):
            return True
        exact_fixtures = {
            'soulbound-tcp5-': 'five_players.sqlite',
            'sb-ultra-5-tcp-': 'stress.db',
            'sb-ultimate-tcp-waves-': 'wave.sqlite',
            'sb-ultra-sqlite-migrate-': 'candidate.db',
            'sb-ultimate-real-row-check-': 'isolated.sqlite',
            'sb-ultimate60-clone-': 'candidate.sqlite',
        }
        return len(rel.parts) == 2 and any(
            name.startswith(prefix) and rel.parts[1].lower() == basename
            for prefix, basename in exact_fixtures.items()
        )
    except (OSError, ValueError, TypeError, RuntimeError):
        return False

def authorized_mode(db_path):
    if production_approved():return 'production'
    if _test_database(db_path):return 'test'
    raise PermissionError('v112: brak zatwierdzonego wydania lub bezpiecznej bazy testowej')

def enabled():return production_approved() or _test_database(os.environ.get('SOULBOUND_DB',''))
