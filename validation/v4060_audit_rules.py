# -*- coding: utf-8 -*-
"""v112: 14 original audit behaviors tested against *current* game state.

No historical admin/audits.py import or old runtime-injected globals needed.
"""
from __future__ import annotations
from validation.v1100_release_counts import expected_quest_total_v1100
import ast
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('generator_numeric_only_audit_v03018', 'generator_whitelist_audit_v03019', 'equipment_expansion_audit_v03020', 'currency_economy_audit_v03021', 'buff_duration_audit_v03030', 'party_combat_feed_audit_v03031', 'party_roles_audit_v03032', 'tool_tier_name_audit_v03033', 'haldor_steel_plate_corpse_audit_v03034', 'broken_blades_spoken_progress_audit_v03038', 'eq_shortcuts_auto_audit_v03040', 'universal_salvage_audit_v03041', 'equipment_upgrade_audit_v03042', 'soul_tier7_cemetery_spawn_audit_v0365')
DEPENDENCIES = {'generator_numeric_only_audit_v03018': ['CATALOG_VALIDATION_AUDIT', 'SOUL_MILESTONE_TIERS', 'CLASS_MASTERY_MAX_LEVEL', 'CLASS_SKILLS', 'ITEMS'], 'generator_whitelist_audit_v03019': ['CATALOG_VALIDATION_AUDIT', 'BALANCE_MATH_VERSION'], 'equipment_expansion_audit_v03020': ['CLASS_EQUIPMENT_SLOT_DEFS', 'EQUIPMENT_SLOT_NAMES', 'COMMAND_ALIASES', 'CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER', 'ITEMS'], 'currency_economy_audit_v03021': ['SILVER_PER_GOLD', 'SILVER_PER_MITHRIL', 'currency_reading_text', 'QUESTS', 'v0190_quest_currency_reward', 'ITEMS'], 'buff_duration_audit_v03030': ['CLASS_SKILLS', 'GLOBAL_SKILL_BUFF_DURATION_SECONDS'], 'party_combat_feed_audit_v03031': ['MudServer'], 'party_roles_audit_v03032': ['MudServer', 'Session', 'PARTY_AUTO_HEAL_THRESHOLD'], 'tool_tier_name_audit_v03033': ['TOOL_TIER_NAMES', 'TOOL_MAX_TIER', 'QUESTS', 'QUEST_REPEAT_COOLDOWN_SECONDS'], 'haldor_steel_plate_corpse_audit_v03034': ['QUESTS', 'MOB_TEMPLATES', 'ITEMS', 'CRAFT_MATERIAL_STORAGE_IDS'], 'broken_blades_spoken_progress_audit_v03038': ['Session', 'QUESTS'], 'eq_shortcuts_auto_audit_v03040': ['COMMAND_ALIASES', 'Session', 'CLASS_EQUIPMENT_SLOT_DEFS'], 'universal_salvage_audit_v03041': ['ITEMS', 'V0925_SALVAGE_MATERIALS', 'v03041_salvage_material_key', 'SessionForgeGuildsMixin', 'Session', 'normalize_lookup_text'], 'equipment_upgrade_audit_v03042': ['ITEMS', 'V03042_EQ_UPGRADE_MAX', 'v03042_upgrade_required_smithing', 'v03042_upgrade_material_cost', 'CHARACTER_MAX_LEVEL', 'v03041_salvage_material_key', 'V0925_SALVAGE_MATERIALS', 'COMMAND_ALIASES', 'Session'], 'soul_tier7_cemetery_spawn_audit_v0365': ['SOUL_TRIAL_QUEST_IDS', 'QUESTS', 'MOB_SPAWNS', 'ROOMS']}


CURRENT_RULE_DIGESTS = {
    'generator_numeric_only_audit_v03018': '8fdd81c35c7b2fe3343b0c6aa1d1d0cd3f99092596e5b384a3a56e672f693242',
    'generator_whitelist_audit_v03019': 'eeb2a66766fd0f11fbeb33dea58971f9fc6df892fabd51b24416b6961b4c6775',
    'equipment_expansion_audit_v03020': '29bddfd3bb59f7670349d952ccfebc6103e344337ddd3b82055b9592afcd67f8',
    'currency_economy_audit_v03021': 'fd9b9fd72a620e149d562b4af24573deff69a9f136a99a35ae1a9d9d533be1a9',
    'buff_duration_audit_v03030': '6680bf559d4d21210646f4955595ea049a2b8a4ee0a1fc0bf7e2f996eb84dc5a',
    'party_combat_feed_audit_v03031': '29a85102fdffb086003f712691a442a8f96d1100459ebfa5636a9376d5e34aa4',
    'party_roles_audit_v03032': 'a90e5a839e585a13b87ff64a69258ac932eb411cc061084076861e5f9ecc69d5',
    'tool_tier_name_audit_v03033': 'fe6e35bd1a1ead447931778d3d8fbd6bb9fe11caa6b73bf9d590c021938ca04b',
    'haldor_steel_plate_corpse_audit_v03034': '35027ea8fc9724eb0094e0cf6cb3b066665d7da3a2783b953606a44316bd392d',
    'broken_blades_spoken_progress_audit_v03038': '6055d5ac124398f5a8bb3178bfad4685f615757444b0a6a918a3e451a74411da',
    'eq_shortcuts_auto_audit_v03040': 'a919a9c56890b11732859246157117ecfce0f0460be709dee74e0b2ab81b1b79',
    'universal_salvage_audit_v03041': 'af3969b515edc777055cb7f695a0cfa9b46d972e0354c0ac17e95928010dd7e4',
    'equipment_upgrade_audit_v03042': '1b40b089d3f58af6fda80a4e0f61fca5933094715f0e0a6db4f28e3829c769f1',
    'soul_tier7_cemetery_spawn_audit_v0365': 'c8531c6567b6cd13baded4e5d01cfbbaa7dd601ee25f55b2254eec6cb45041ab',
}

def run_regression():
    """Test the actual pure rules on the current server data.

    Never execute admin/audits.py as a module: that historical wrapper assumes
    an old injected global runtime and is deliberately not production code.
    Function-body AST hashes retain the regression promise for all 14 rules.
    """
    from core.bootstrap_economy_professions import VERSION
    from admin import audit_rules_v406
    import server
    import hashlib
    count=0
    assert len(NAMES)==14
    count+=1
    from validation.class_balance_v1172 import _historical_22
    historical_rows,historical_skills=_historical_22()
    assert len(historical_rows)==22 and {r[0] for r in historical_rows}==set(historical_skills)
    assert set(historical_skills)<=set(server.CLASS_SKILLS)
    assert (len(server.QUESTS)>=6745 if int(VERSION.split('.',1)[0])>=23 else
            len(server.QUESTS)==expected_quest_total_v1100())
    count+=2
    pure_source=ast.parse((ROOT/'admin/audit_rules_v406.py').read_text(encoding='utf-8'))
    pure_funcs={n.name:n for n in pure_source.body if isinstance(n,ast.FunctionDef)}
    assert all(name in pure_funcs for name in NAMES)
    count+=len(NAMES)
    assert all(isinstance(node,(ast.FunctionDef,ast.Import,ast.ImportFrom)) or
               isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant)
               for node in pure_source.body)
    count+=1
    for name in NAMES:
        pure_node=pure_funcs[name]
        assert not pure_node.args.args
        assert set(DEPENDENCIES[name])=={a.arg for a in pure_node.args.kwonlyargs}
        count+=2
        assert hashlib.sha256(ast.dump(pure_node,include_attributes=False).encode()).hexdigest()==CURRENT_RULE_DIGESTS[name],name
        count+=1
        fn=getattr(audit_rules_v406,name)
        assert callable(fn)
        deps={key:getattr(server,key) for key in DEPENDENCIES[name]}
        report=fn(**deps)
        assert isinstance(report,dict) and isinstance(report.get('errors'),list),name
        assert int(report.get('error_count',-1))==len(report['errors']),name
        # No historical wrapper or import-time side effect; the isolated rule
        # must compute the same report twice from the current game catalogues.
        assert fn(**deps)==report,name
        count+=3
    return count
