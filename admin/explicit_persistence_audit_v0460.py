# -*- coding: utf-8 -*-
"""Soulbound v0.46.0 - explicit persistence and Database override cleanup."""
from pathlib import Path
from core.runtime_manifest import EXPLICIT_RUNTIME_EXPORTS,LEGACY_IMPLICIT_DEPENDENCY_BUDGET,RUNTIME_MODULES,V046_EXPLICIT_RUNTIME_EXPORTS
from validation.dependencies import legacy_dependency_metrics,validate_explicit_runtime_modules,validate_layer_imports

def explicit_persistence_audit_v0460():
    root=Path(__file__).resolve().parents[1]; errors=[]
    e=validate_explicit_runtime_modules(root,EXPLICIT_RUNTIME_EXPORTS,RUNTIME_MODULES); errors.extend(e["errors"])
    l=validate_layer_imports(root); errors.extend(l["errors"])
    m=legacy_dependency_metrics(root,RUNTIME_MODULES,EXPLICIT_RUNTIME_EXPORTS); total=int(m["legacy_implicit_reference_total"])
    expected={"storage/db_schema.py","storage/db_accounts.py","storage/db_world.py","storage/db_inventory.py","storage/db_progression.py","storage/db_quests.py","storage/db_guilds.py","storage/db_crafting_extensions.py","storage/database.py",'storage/schema_core.py','storage/schema_migrate_character.py','storage/schema_migrate_economy.py','storage/schema_migrate_guilds.py','storage/schema_migrate_history.py','storage/schema_migrate_social.py','storage/schema_migrate_tools.py','storage/schema_progression.py','storage/schema_social_guilds.py','storage/schema_world_quests.py'}
    missing=sorted(expected-set(EXPLICIT_RUNTIME_EXPORTS))
    if missing: errors.append("persistence modules not explicit: "+", ".join(missing))
    for old in ("storage/crafting_expansion_v03114.py","storage/milestone_v0320.py"):
        if old in RUNTIME_MODULES: errors.append("historical Database monkey patch still active: "+old)
        if (root/old).exists(): errors.append("dead historical Database monkey patch file still present: "+old)
    if len(V046_EXPLICIT_RUNTIME_EXPORTS)!=7: errors.append(f"v0.46 persistence cohort {len(V046_EXPLICIT_RUNTIME_EXPORTS)} != 7")
    if total>1132: errors.append(f"v0.46 dependency target regressed: {total} > 1132")
    return {"version":"0.46.0","error_count":len(errors),"errors":errors,"explicit_module_count":len(EXPLICIT_RUNTIME_EXPORTS),"v046_migrated_module_count":len(V046_EXPLICIT_RUNTIME_EXPORTS),"legacy_compat_module_count":m["legacy_module_count"],"legacy_implicit_reference_total":total,"legacy_implicit_reference_budget":1132,"largest_legacy_dependency_users":m["largest"]}

EXPLICIT_PERSISTENCE_AUDIT_V0460=explicit_persistence_audit_v0460()
if EXPLICIT_PERSISTENCE_AUDIT_V0460["error_count"]: raise RuntimeError("Explicit Persistence Audit v0.46.0 failed: "+"; ".join(EXPLICIT_PERSISTENCE_AUDIT_V0460["errors"][:100]))
