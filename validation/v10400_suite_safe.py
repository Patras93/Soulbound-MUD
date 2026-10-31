# -*- coding: utf-8 -*-
"""Safe v104 Linux/offline regression, never opens TCP or production databases."""
from __future__ import annotations
import importlib
import time

TESTS=(
    'validation.v10400_predeploy_contracts_regression',
    'validation.v10400_topology_performance_equivalence',
    'validation.v10400_topology_role_cache_test',
    'validation.v10400_economy_budget_cache_test',
    'validation.test_v10400_tcp_wait_single_socket',
    # Final consolidated non-network regression. These test real SQLite
    # transactions, cap-boundary preservation, and immutable copy recovery.
    'validation.test_v10400_exact_reward_math',
    'validation.test_v10400_big_number_copy_runtime',
    'validation.test_v10400_live_character_production',
    'validation.test_v10400_live_keyed_xp_production',
    'validation.test_v10400_class_xp_big_number_copy',
    'validation.test_v10400_keyed_shadow_receipts',
    'validation.test_v10400_single_axis_receipt',
    'validation.v10400_release_safety_check',
    'validation.test_v10400_combat_wallet_stat_atomic',
    'validation.test_v10400_party_loot_atomic',
    'validation.test_v10400_all_rolls_one_kill',
    'validation.test_v10400_deferred_commit_rollback',
    'validation.test_v10400_imperial_atomic_ownership',
    'validation.test_v10400_atomic_kill_quests',
    'validation.v10400_quest_credit_route_integrity',
    'validation.v10400_party_loot_route_integrity',
    'validation.test_v10400_combat_bundle_atomic',
    'validation.test_v10400_full_kill_atomic',
    'validation.test_v10400_release_isolation_guard',
    'validation.v10400_combat_reward_route_integrity',
    'validation.test_v10400_no_loss_at_caps',
    'validation.test_v10400_atomic_live_character_xp',
    'validation.test_v10400_live_multiaxis_atomic',
    'validation.test_v10400_quest_class_atomic_endtoend',
    'validation.v10400_safe_method_fingerprints',
    'validation.v10400_migration_recovery_offline',
    'validation.test_v10400_legacy_wallet_migration_safe',
    'validation.test_v10400_stage14_live_expbank',
    'validation.v1020012_exp_unlimited',
    'validation.v23215_multi_cap',
    'validation.v23217_curve_soul_level',
    'validation.v23216_level_overview',
    'validation.v23218_full_cap_per_axis',
    'validation.test_v10400_stage10_numeric_safety',
    'validation.test_v10400_stage10_ledger',
    'validation.test_v10400_stage11_atomic',
    'validation.test_v10400_stage12_events',
    'validation.test_v10400_stage13_bundle',
    'validation.test_v10400_stage13_live_guards',
    'validation.test_v10400_sqlite_write_barriers',
    'validation.v10400_final_integrity',
    'validation.v10400_etap4_rajdy',
    'validation.v10400_etap4_party_sqlite',
    'validation.v10400_contracts_sqlite',
    'validation.v10400_etap8_invasions_calendar',
    'validation.v10400_etap9_invasion_rewards',
    'validation.v10400_etap3_soul_tiers',
    'validation.v10400_etap2_integracja',
    'validation.v10400_krainy_etap2',
    'validation.v10300_era_raids',
    'validation.v10300_era_raid_party_sqlite',
)

def run():
    total=0
    for name in TESTS:
        begin=time.monotonic()
        obj=importlib.import_module(name)
        n=(getattr(obj, "run", None) or obj.run_regression)()
        print(f'PASS {name}: {n} checks ({time.monotonic()-begin:.2f}s)',flush=True)
        total+=n[0] if isinstance(n,tuple) else n
    print(f'V104 SAFE SUITE: {total} PASS',flush=True)
    return total

if __name__=='__main__':run()
