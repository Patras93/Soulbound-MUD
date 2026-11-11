# -*- coding: utf-8 -*-
"""v109 version-neutral backwards regressions + v109 native gates.

We do NOT change the historic v108 identity tests to accept v109. Those three
are replaced by v109 boot/activation, v109 manifest, and v109 PREDEPLOY gates.
All remaining v108 regression modules execute (no skipped applicable modules).
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
import os
import sys
from pathlib import Path

# Windows 60/60 PLUS launches this file directly with its absolute filename.
# In that mode sys.path[0] is validation/, not the game root, so imports of
# validation.* fail unless the verified staged game root is also on sys.path.
# This only affects the isolated test process; it does not change the game.
_ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, '') and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from validation.v10800_offline_suite import MODULES as V108_MODULES,_one_module

HISTORICAL_VERSION_BOUND={
    'validation.v10800_release_guard_regression',
    'validation.v10800_predeploy_tcp_isolation_regression',
    'validation.v10800_activation_install_cutover_regression',
    'validation.v10800_bat_cleanup_regression',
}
MODULES=tuple(m for m in V108_MODULES if m not in HISTORICAL_VERSION_BOUND)+(
    'validation.v10900_modular_boundaries_regression',
    'validation.v10900_horizons_regression',
    'validation.v10900_gifts_regression',
    'validation.v10900_staging_guard_regression',
    'validation.v10900_activation_regression',
    'validation.v10900_install_rollback_regression',
    'validation.v10900_predeploy_contract_regression',
    'validation.v10900_server_modules_regression',
    'validation.v10900_bat_cleanup_regression',
    'validation.v10900_sales_modules_regression',
    'validation.v10900_museum_bounty_modules_regression',
    'validation.v10900_guild_readonly_modules_regression',
    'validation.v10900_world_events_modules_regression',
    'validation.v10900_db_inventory_modules_regression',
    'validation.v10900_db_accounts_modules_regression',
    'validation.v10900_db_world_modules_regression',
    'validation.v10900_sky_modules_regression',
    'validation.v10900_exp_terrain_modules_regression',
    'validation.v10900_admin_tools_modules_regression',
    'validation.v10900_combat_survival_modules_regression',
    'validation.v10900_combat_rewards_modules_regression',
    'validation.v10900_combat_damage_modules_regression',
    'validation.v10900_admin_wipe_safety_regression',
    'validation.v10900_help_modules_regression',
    'validation.v10900_external_bridge_regression',
    'validation.v10900_standard_predeploy_router_regression',
    'validation.v10900_snapshot_preservation_regression',
)
assert len(MODULES) == len(V108_MODULES)-len(HISTORICAL_VERSION_BOUND)+27


def main():
    env=dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE']='1'
    errors=[]
    # v109: najciezsze rozruchy w pierwszej fali; bez pomijania zadnych
    # regresji i bez mieszania prywatnych katalogow testowych.
    startup_heavy={
        'validation.v10900_sales_modules_regression',
        'validation.v10900_exp_terrain_modules_regression',
        'validation.v10900_combat_rewards_modules_regression',
        'validation.v10900_horizons_regression',
        'validation.v10800_recovered_features_regression',
    }
    schedule=sorted(enumerate(MODULES,1),key=lambda im:(im[1] not in startup_heavy,im[0]))
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs=[pool.submit(_one_module,i,m,env,120) for i,m in schedule]
        for finished in as_completed(jobs):
            number,module,code,out,err=finished.result()
            if code:
                errors.append(module)
                print(f'[{number}/{len(MODULES)}] FAIL {module}: {code} {(err or out)[-900:]}',flush=True)
            else:
                lines=[s.strip() for s in out.splitlines() if s.strip()]
                print(f'[{number}/{len(MODULES)}] PASS '+(lines[-1] if lines else module)[:150],flush=True)
    if errors:
        print(f'V109: {len(errors)} FAIL z {len(MODULES)}; NIE WDRAŻAĆ',flush=True)
        return 2
    print(f'V109: {len(MODULES)}/{len(MODULES)} REGRESJI PASS; '
          'osobny Windows 60/60 PLUS i audyt bazy są nadal wymagane.',flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
