# -*- coding: utf-8 -*-
"""v4.00.6: compare legacy audit wrappers against extracted pure audit rules."""
from __future__ import annotations
from validation.v1100_release_counts import expected_quest_total_v1100
import ast
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('generator_numeric_only_audit_v03018', 'generator_whitelist_audit_v03019', 'equipment_expansion_audit_v03020', 'currency_economy_audit_v03021', 'buff_duration_audit_v03030', 'party_combat_feed_audit_v03031', 'party_roles_audit_v03032', 'tool_tier_name_audit_v03033', 'haldor_steel_plate_corpse_audit_v03034', 'broken_blades_spoken_progress_audit_v03038', 'eq_shortcuts_auto_audit_v03040', 'universal_salvage_audit_v03041', 'equipment_upgrade_audit_v03042', 'soul_tier7_cemetery_spawn_audit_v0365')
DEPENDENCIES = {'generator_numeric_only_audit_v03018': ['CATALOG_VALIDATION_AUDIT', 'SOUL_MILESTONE_TIERS', 'CLASS_MASTERY_MAX_LEVEL', 'CLASS_SKILLS', 'ITEMS'], 'generator_whitelist_audit_v03019': ['CATALOG_VALIDATION_AUDIT', 'BALANCE_MATH_VERSION'], 'equipment_expansion_audit_v03020': ['CLASS_EQUIPMENT_SLOT_DEFS', 'EQUIPMENT_SLOT_NAMES', 'COMMAND_ALIASES', 'CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER', 'ITEMS'], 'currency_economy_audit_v03021': ['SILVER_PER_GOLD', 'SILVER_PER_MITHRIL', 'currency_reading_text', 'QUESTS', 'v0190_quest_currency_reward', 'ITEMS'], 'buff_duration_audit_v03030': ['CLASS_SKILLS', 'GLOBAL_SKILL_BUFF_DURATION_SECONDS'], 'party_combat_feed_audit_v03031': ['MudServer'], 'party_roles_audit_v03032': ['MudServer', 'Session', 'PARTY_AUTO_HEAL_THRESHOLD'], 'tool_tier_name_audit_v03033': ['TOOL_TIER_NAMES', 'TOOL_MAX_TIER', 'QUESTS', 'QUEST_REPEAT_COOLDOWN_SECONDS'], 'haldor_steel_plate_corpse_audit_v03034': ['QUESTS', 'MOB_TEMPLATES', 'ITEMS', 'CRAFT_MATERIAL_STORAGE_IDS'], 'broken_blades_spoken_progress_audit_v03038': ['Session', 'QUESTS'], 'eq_shortcuts_auto_audit_v03040': ['COMMAND_ALIASES', 'Session', 'CLASS_EQUIPMENT_SLOT_DEFS'], 'universal_salvage_audit_v03041': ['ITEMS', 'V0925_SALVAGE_MATERIALS', 'v03041_salvage_material_key', 'SessionForgeGuildsMixin', 'Session', 'normalize_lookup_text'], 'equipment_upgrade_audit_v03042': ['ITEMS', 'V03042_EQ_UPGRADE_MAX', 'v03042_upgrade_required_smithing', 'v03042_upgrade_material_cost', 'CHARACTER_MAX_LEVEL', 'v03041_salvage_material_key', 'V0925_SALVAGE_MATERIALS', 'COMMAND_ALIASES', 'Session'], 'soul_tier7_cemetery_spawn_audit_v0365': ['SOUL_TRIAL_QUEST_IDS', 'QUESTS', 'MOB_SPAWNS', 'ROOMS']}


def run_regression():
    from core.bootstrap_economy_professions import VERSION
    from admin import audit_rules_v406
    import server
    import admin.audits as legacy
    count = 0
    assert len(NAMES) == 14
    count += 1
    assert len(server.CLASS_SKILLS) == 22 and len(server.QUESTS) == (expected_quest_total_v1100() if VERSION in ('11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') else 6585 if VERSION in ('10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') else 6573 if VERSION == '9.00.0' else 5605 if VERSION == '8.00.0' else 3925 if VERSION in ('7.00.0','7.10.0','7.10.1','8.00.0','9.00.0','10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') else 3861 if VERSION == '6.00.1' else 2901 if VERSION in ('5.00.0','5.00.1','6.00.0','6.00.1','7.00.0','7.10.0','7.10.1','8.00.0','9.00.0','10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') else 2701)
    count += 2
    wrappers = ast.parse((ROOT / 'admin/audits.py').read_text(encoding='utf-8'))
    pure_source = ast.parse((ROOT / 'admin/audit_rules_v406.py').read_text(encoding='utf-8'))
    funcs = {n.name: n for n in wrappers.body if isinstance(n, ast.FunctionDef)}
    pure_funcs = {n.name: n for n in pure_source.body if isinstance(n, ast.FunctionDef)}
    assert all(name in funcs and name in pure_funcs for name in NAMES)
    count += len(NAMES)
    assert all(isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom)) or
               (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
               for node in pure_source.body)
    count += 1
    for name in NAMES:
        w = funcs[name]
        p = pure_funcs[name]
        assert not w.args.args and not w.args.kwonlyargs
        assert set(DEPENDENCIES[name]) == {a.arg for a in p.args.kwonlyargs}
        count += 2
        assert hasattr(server, name) and callable(getattr(server, name))
        count += 1
        runtime_fn = getattr(legacy, name)
        rule_fn = getattr(audit_rules_v406, name)
        assert callable(runtime_fn) and callable(rule_fn)
        args = {key: runtime_fn.__globals__[key] for key in DEPENDENCIES[name]}
        expected = rule_fn(**args)
        actual = runtime_fn()
        assert expected == actual, name
        count += 3
    return count
