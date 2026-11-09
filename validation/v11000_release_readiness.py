# -*- coding: utf-8 -*-
"""v110: fail-closed source checks; no older versioned installer files."""
from __future__ import annotations
import ast
from pathlib import Path

REQUIRED=(
 'VERSION','server.py','server/mud_server.py','storage/database.py',
 'core/bootstrap_economy_professions.py','core/v11000_archetypes.py',
 'core/archetypes_v110/profession_timing_v110.py','core/v11000_runtime_catalogue.py',
 'validation/v11000_fast_predeploy_guard.py',
 'world/v11000_realms.py','world/v11000_realm_index.py',
 'world/teachers_v110.py','validation/v11000_teachers_regression.py',
 'systems/v11000_activation.py','systems/v11000_retired_installers.py',
 'systems/v11000_profession_work.py',
 'systems/v11000_olc_validation_views.py',
 'validation/v11000_olc_catalogue_views_regression.py',
 'systems/events_v110/clock.py','systems/events_v110/combat.py',
 'systems/events_v110/listener.py','systems/events_v110/storage.py',
 'systems/events_v110/rewards.py','systems/events_v110/status.py',
 'data/items_v110/professions.py',
 'data/shops.py','validation/v11000_profession_tools_regression.py',
 'validation/v11000_profession_race_timing_regression.py',
 'validation/v11000_world_modules_regression.py',
 'validation/v11000_events_regression.py',
 'validation/v11000_profession_atomic_regression.py',
 'validation/v11000_release_install_regression.py',
 'validation/v11000_dispatch_regression.py',
 'validation/v11000_bat_retirement_regression.py',
 'validation/v11000_olc_late_integration.py',
 'validation/v11000_release_suite.py',
 'validation/v11000_tcp_six_players.py',
 'validation/v11000_tcp_six_party_journey.py',
 'validation/v11000_tcp_child.py',
 'validation/v11000_v107_functional_audit.py',
 'validation/v11000_activation_regression.py',
 'validation/v11000_update_consent_regression.py',
 'validation/v11000_v107_catalog_compat.py',
 'validation/v11000_equipment_barrier_compat.py',
 'validation/v11000_v85_tcp_compat.py',
 'validation/v11000_staging_isolation_regression.py',
 'validation/v11000_snapshot_contract_regression.py',
 'validation/v11000_soul_tier_activation_regression.py',
 'validation/v11000_legacy_tail_isolation.py',
 'PREDEPLOY_NOWEJ_WERSJI.bat','WDROZ_PO_PREDEPLOY.bat',
 'predeploy_nowej_wersji.py','wdroz_po_predeploy.py',
)
# A release may retain historical gameplay and regression modules. Versioned
# installer bridges, however, must never be part of v110 itself.
RETIRED_INSTALLERS=(
 'wdroz_v107_z_zewnatrz.py','wdroz_v108_z_zewnatrz.py',
 'wdroz_v109_z_zewnatrz.py','predeploy_v108_z_zewnatrz.py',
 'predeploy_v109_z_zewnatrz.py','predeploy_v109_standard_router.py',
)
# Samodzielne diagnostyki historyczne, które nie mają wywołań z aktualnego
# zestawu testowego. Ich kopie są przechowane POZA katalogiem wydania.
RETIRED_STANDALONE_DIAGNOSTICS=(
 'validation/v10400_numeric_route_audit.py',
 'validation/v10500_tcp_endgame_regions.py',
 'validation/v10600_admin_live3_bootstrap_dispatch.py',
 'validation/v10600_bank_preflight.py',
 'validation/v10600_predeploy_parallel_regression.py',
 'validation/v10600_stage_v105_compatibility.py',
 'validation/v10800_eq107_source_diagnostic_regression.py',
 'validation/v10900_standard_upgrade_audit_test.py',
)
ARCHETYPES=('classes','races','professions')


def unmet_requirements(root):
    root=Path(root)
    missing=[]
    try:
        if (root/'VERSION').read_text(encoding='utf-8-sig').strip()!='110.00.0':
            missing.append('niepoprawny VERSION')
        if '110.00.0' not in (root/'core/bootstrap_economy_professions.py').read_text(encoding='utf-8'):
            missing.append('brak wersji v110 w kodzie')
    except OSError as exc:missing.append('brak identyfikatora wydania: '+str(exc))
    for rel in REQUIRED:
        if not (root/rel).is_file():missing.append('brak modułu: '+rel)
    for item in RETIRED_INSTALLERS:
        if (root/item).exists():missing.append('stary instalator w ZIP: '+item)
    for item in RETIRED_STANDALONE_DIAGNOSTICS:
        if (root/item).exists():missing.append('nieużywany skrypt diagnostyczny w ZIP: '+item)
    for category in ARCHETYPES:
        mods=[f for f in (root/'core/archetypes_v110'/category).glob('*.py') if f.name!='__init__.py']
        if len(mods)!=8:missing.append(f'v110: {category} musi mieć 8 odrębnych plików (jest {len(mods)})')
    if len([f for f in (root/'world/realms_v110').glob('*.py') if f.name not in ('__init__.py','entry.py')])!=12:
        missing.append('v110: brakuje którejś z 12 krain')
    for rel in REQUIRED:
        if rel.endswith('.py') and (root/rel).is_file():
            try:ast.parse((root/rel).read_text(encoding='utf-8-sig'),filename=rel)
            except (SyntaxError,UnicodeError) as exc:missing.append('niepoprawny AST '+rel+': '+str(exc))
    return missing

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    errors=unmet_requirements(root)
    if errors:
        for item in errors:print('V110 READINESS FAIL: '+item,flush=True)
        raise SystemExit(2)
    import sys
    sys.path.insert(0, str(root))
    from validation.v11000_bat_retirement_regression import run_regression as bat_retirement
    print(f'V110 BAT RETIREMENT: {bat_retirement()} PASS', flush=True)
    from validation.v11000_olc_catalogue_views_regression import run_regression as olc_views
    print(f'V110 OLC VIEWS: {olc_views()} PASS', flush=True)
    print('V110 READINESS PASS: 12 krain, 8 klas, 8 ras, 8 profesji, 0 starych instalatorów.',flush=True)
