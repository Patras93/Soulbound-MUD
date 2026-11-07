@echo off
setlocal
cd /d "%~dp0..\..\"
echo SOULBOUND V106 - KOD ROBOCZY, WYLACZNIE TESTY LOKALNE. NIE WDRAZAC.
if not exist "world\dynamic_content.py" (
  echo BLAD: brak bazy v105 FIX7. Rozpakuj nakladke tylko do ODDZIELNEJ kopii gry.
  exit /b 2
)
set "PYTHONDONTWRITEBYTECODE=1"
set "PYTHONUTF8=1"
set "PYTHONPATH=%CD%"
set "SOULBOUND_V106_STAGING="
py -3 "validation\v10500_first_integrity.py" || exit /b 1
py -3 "validation\v10600_one_time_quest_offers.py" || exit /b 1
py -3 "validation\v10600_stage_catalog_audit.py" || exit /b 1
py -3 "validation\v10600_tcp_restart_snapshot_contract.py" || exit /b 1
py -3 "validation\test_v10600_equipment_migration_staging.py" || exit /b 1
py -3 "validation\v10600_shadow_slots_integration.py" || exit /b 1
py -3 "validation\v10600_per_copy_evolution_stats.py" || exit /b 1
py -3 "validation\v10600_haldor_copy_evolution_command.py" || exit /b 1
py -3 "validation\v10600_inventory_instance_flow.py" || exit /b 1
py -3 "validation\v10600_bank_preflight.py" || exit /b 1
py -3 "validation\v10600_bank_physical_flow.py" || exit /b 1
py -3 "validation\v10600_bank_legacy_migration.py" || exit /b 1
py -3 "validation\v10600_storage_physical_flow.py" || exit /b 1
py -3 "validation\v10600_mail_physical_flow.py" || exit /b 1
py -3 "validation\test_v10400_atomic_crafting_consumption.py" || exit /b 1
py -3 "validation\v10600_crafting_materials_atomic.py" || exit /b 1
py -3 "validation\v10600_full_recipe_atomic_flow.py" || exit /b 1
py -3 "validation\v10600_crafting_bonus_atomic.py" || exit /b 1
py -3 "validation\v10600_crafting_accounting_atomic.py" || exit /b 1
py -3 "validation\v10600_equipment_cutover_gate.py" || exit /b 1
py -3 "validation\v10600_admin_live3_staging.py" || exit /b 1
py -3 "validation\test_v10600_calendar_staging.py" || exit /b 1
py -3 "validation\test_v10600_soul_weapon_staging.py" || exit /b 1
py -3 "validation\v10600_skill_weapon_integration.py" || exit /b 1
py -3 "validation\v10600_weapon_regeneration_real.py" || exit /b 1
py -3 "validation\v10600_stage_v105_compatibility.py" || exit /b 1
py -3 "validation\v10400_etap8_invasions_calendar.py" || exit /b 1
py -3 "validation\v10600_bootstrap_contracts_integration.py" || exit /b 1
set "SOULBOUND_V106_STAGING=1"
py -3 "validation\v10600_boss_authored_stage_runtime.py" || exit /b 1
py -3 "validation\v10600_ordinary_mob_stage_runtime.py" || exit /b 1
py -3 "validation\v10600_boss_adaptive_soul_level.py" || exit /b 1
py -3 "validation\v10600_raid_full_hp_phase_runtime.py" || exit /b 1
py -3 "validation\v10600_soul_early_curve_runtime.py" || exit /b 1
py -3 "validation\v10600_soul_bridge_runtime.py" || exit /b 1
py -3 "validation\v10600_soul_xp_curve_runtime.py" || exit /b 1
py -3 "validation\v10600_soul_progression_cap_and_fast_tiers.py" || exit /b 1
py -3 "validation\v10600_soul_tier_unlock_runtime.py" || exit /b 1
py -3 "validation\v10600_admin_live3_bootstrap_dispatch.py" || exit /b 1
set "SOULBOUND_V106_STAGING="
echo V106 STAGING: AUDYTY LOKALNE PASS. NIE JEST TO WINDOWS PREDEPLOY.
exit /b 0
