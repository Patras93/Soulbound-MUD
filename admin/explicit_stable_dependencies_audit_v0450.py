# -*- coding: utf-8 -*-
"""Soulbound v0.45.0 - conservative explicit dependency migration audit."""
from pathlib import Path
from core.runtime_manifest import EXPLICIT_RUNTIME_EXPORTS,LEGACY_IMPLICIT_DEPENDENCY_BUDGET,RUNTIME_MODULES,V045_EXPLICIT_RUNTIME_EXPORTS
from validation.dependencies import legacy_dependency_metrics,validate_explicit_runtime_modules,validate_layer_imports

def explicit_stable_dependencies_audit_v0450():
 root=Path(__file__).resolve().parents[1]; errors=[]
 e=validate_explicit_runtime_modules(root,EXPLICIT_RUNTIME_EXPORTS,RUNTIME_MODULES); errors.extend(e["errors"])
 l=validate_layer_imports(root); errors.extend(l["errors"])
 m=legacy_dependency_metrics(root,RUNTIME_MODULES,EXPLICIT_RUNTIME_EXPORTS); total=int(m["legacy_implicit_reference_total"])
 if len(V045_EXPLICIT_RUNTIME_EXPORTS)!=20:errors.append(f"v0.45 cohort {len(V045_EXPLICIT_RUNTIME_EXPORTS)} != 20")
 if len(EXPLICIT_RUNTIME_EXPORTS)<62:errors.append(f"explicit module count too small: {len(EXPLICIT_RUNTIME_EXPORTS)}")
 if total>1182:errors.append(f"legacy implicit references regressed: {total} > 1182")
 if total>LEGACY_IMPLICIT_DEPENDENCY_BUDGET:errors.append(f"budget exceeded: {total} > {LEGACY_IMPLICIT_DEPENDENCY_BUDGET}")
 return {"version":"0.45.0","error_count":len(errors),"errors":errors,"explicit_module_count":len(EXPLICIT_RUNTIME_EXPORTS),"v045_migrated_module_count":len(V045_EXPLICIT_RUNTIME_EXPORTS),"legacy_compat_module_count":m["legacy_module_count"],"legacy_implicit_reference_total":total,"legacy_implicit_reference_budget":LEGACY_IMPLICIT_DEPENDENCY_BUDGET,"largest_legacy_dependency_users":m["largest"]}
EXPLICIT_STABLE_DEPENDENCIES_AUDIT_V0450=explicit_stable_dependencies_audit_v0450()
if EXPLICIT_STABLE_DEPENDENCIES_AUDIT_V0450["error_count"]:raise RuntimeError("Explicit Stable Dependencies Audit v0.45.0 failed: "+"; ".join(EXPLICIT_STABLE_DEPENDENCIES_AUDIT_V0450["errors"][:100]))
