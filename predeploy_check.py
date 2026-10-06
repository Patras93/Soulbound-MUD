#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast Railway predeploy gate for Soulbound v1.13.8.

This is the normal deploy check.  It intentionally avoids assembling the full
world/runtime.  Use predeploy_full.py when an exhaustive historical audit is
wanted before a major release.
"""
from __future__ import annotations

import re
import traceback

# Railway/admin tools import the database facade directly. Keep this as an
# explicit smoke test so direct-import regressions fail the deploy gate.
try:
    from storage.database import Database as _DatabaseImportSmoke
except Exception as exc:
    print(f"Soulbound v1.13.8 FAST PREDEPLOY FAILED: database import: {type(exc).__name__}: {exc}")
    traceback.print_exc()
    raise SystemExit(1)

from admin.fast_predeploy_audit_v0571 import FAST_PREDEPLOY_AUDIT_V0571 as audit

# v1.11.96 semantic gameplay gates. These import only the static class/skill
# catalog and are intentionally kept out of the full world/runtime loader.
try:
    from core.classes_skills import (
        MEC_CONTRACT_AUDIT_V11149,
        ENGINEER_AP_SEMANTICS_AUDIT_V11196,
        ALL_CLASS_SKILL_TARGET_AUDIT_V11196,
        CLASS_HEALING_SCALE_AUDIT_V11196,
        HARMFUL_DEBUFF_TARGET_AUDIT_V11196,
        PRIEST_HEALING_CONTRACT_AUDIT_V11196,
        UOSS_STATUS_SOURCE_CONTRACT_AUDIT_V11196,
        ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196,
    )
except Exception as exc:
    print(
        "Soulbound v1.13.8 FAST PREDEPLOY FAILED: "
        f"skill semantic import: {type(exc).__name__}: {exc}"
    )
    traceback.print_exc()
    raise SystemExit(1)

_semantic_audits = {
    "mec_contract": MEC_CONTRACT_AUDIT_V11149,
    "engineer_ap": ENGINEER_AP_SEMANTICS_AUDIT_V11196,
    "all_class_targets": ALL_CLASS_SKILL_TARGET_AUDIT_V11196,
    "healing_scales": CLASS_HEALING_SCALE_AUDIT_V11196,
    "harmful_debuff_targets": HARMFUL_DEBUFF_TARGET_AUDIT_V11196,
    "priest_healing": PRIEST_HEALING_CONTRACT_AUDIT_V11196,
    "uoss_status_contracts": UOSS_STATUS_SOURCE_CONTRACT_AUDIT_V11196,
    "endgame_damage": ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196,
}
_semantic_errors = []
for _name, _result in _semantic_audits.items():
    if int(_result.get("error_count", 0) or 0):
        for _error in _result.get("errors", ()):
            _semantic_errors.append(f"{_name}: {_error}")

# AP is a learning-point cost, never authored combat power. Keep a small
# source-level regression guard around the two runtime files that previously
# leaked UOSS Base AP into Mec/Engineer damage.
from pathlib import Path as _Path
_root = _Path(__file__).resolve().parent

# Release identity guard: the login banner uses VERSION from bootstrap, while
# CHANGELOG_PL.txt announces the current package. Reject deploys when those two
# sources drift apart so the public banner cannot lag behind the shipped build.
_bootstrap_source = (_root / "core/bootstrap_economy_professions.py").read_text(encoding="utf-8")
_changelog_source = (_root / "CHANGELOG_PL.txt").read_text(encoding="utf-8")
_version_match = re.search(r'^VERSION\s*=\s*"([^"]+)"', _bootstrap_source, re.MULTILINE)
_package_match = re.search(r'^Aktualna paczka:\s*v([^\s]+)', _changelog_source, re.MULTILINE)
if not _version_match:
    _semantic_errors.append("release identity: missing canonical VERSION in bootstrap")
elif not _package_match:
    _semantic_errors.append("release identity: missing current package in CHANGELOG_PL.txt")
elif _version_match.group(1) != _package_match.group(1):
    _semantic_errors.append(
        "release identity mismatch: "
        f"VERSION={_version_match.group(1)} vs changelog={_package_match.group(1)}"
    )
_forbidden_ap_runtime = {
    "player/session_mixins/combat_skills.py": (
        'skill.get("base_power"',
    ),
    "player/session_mixins/skill_learning.py": (
        '_intercept.get("base_power"',
    ),
}
for _rel, _needles in _forbidden_ap_runtime.items():
    _source = (_root / _rel).read_text(encoding="utf-8")
    for _needle in _needles:
        if _needle in _source:
            _semantic_errors.append(
                f"AP semantics regression: {_rel} contains forbidden {_needle}"
            )

# v1.13.1 regression guard: Heal Beam target preparation checks support_effect
# before the authored-Mec execution block. The variable must therefore be
# resolved earlier in use_class_skill, otherwise combat crashes at runtime.
_combat_skills_source = (_root / "player/session_mixins/combat_skills.py").read_text(encoding="utf-8")
_support_init_pos = _combat_skills_source.find(
    "support_effect = bool(\n                    skill.get(\"mec_authored\")"
)
_heal_beam_precheck_pos = _combat_skills_source.find("_heal_beam_targets = []")
if (
    _support_init_pos < 0
    or _heal_beam_precheck_pos < 0
    or _support_init_pos > _heal_beam_precheck_pos
):
    _semantic_errors.append(
        "Heal Beam support regression: support_effect must be initialized before target preparation"
    )

# v1.13.1 regression guard: authored troll quest stat rewards must bypass
# Generator Core's generated reward_stat_progress so the explicit balance
# values remain exact and visible to players.
_progression_source = (_root / "core/progression_resources.py").read_text(encoding="utf-8")
_troll_rewards_source = (_root / "world/troll_shaman_density.py").read_text(encoding="utf-8")
if 'manual_reward = quest.get("manual_stat_progress")' not in _progression_source:
    _semantic_errors.append(
        "troll stat reward regression: manual_stat_progress override missing"
    )
_troll_reward_needles = (
    '"mountain_troll_hunt": 15_000',
    '"mountain_trail_patrol": 15_000',
    '"stolen_mountain_ores": 15_000',
    '"troll_shaman_hunt": 18_000',
    '"deep_troll_clearance": 20_000',
    '"troll_king_hunt": 25_000',
)
for _needle in _troll_reward_needles:
    if _needle not in _troll_rewards_source:
        _semantic_errors.append(
            "troll stat reward regression: missing " + _needle
        )

# v1.13.8: Generator Core is a fallback, not an unconditional overwrite layer.
_generator_source = (_root / "core/generator_core.py").read_text(encoding="utf-8")
_equipment_source = (_root / "systems/equipment_crafting.py").read_text(encoding="utf-8")
_items_resource_source = (_root / "systems/items_resources.py").read_text(encoding="utf-8")
_dungeon_source = (_root / "systems/dungeons_regions.py").read_text(encoding="utf-8")
_economy_source = (_root / "systems/economy_income_balance.py").read_text(encoding="utf-8")
_runtime_progression_source = (_root / "core/progression_resources.py").read_text(encoding="utf-8")
_sales_source = (_root / "player/session_mixins/sales.py").read_text(encoding="utf-8")
_gathering_source = (_root / "player/session_mixins/gathering_actions.py").read_text(encoding="utf-8")
_protocol_utils_source = (_root / "network/protocol_gameplay_utils.py").read_text(encoding="utf-8")
_exploration_prof_source = (_root / "player/session_mixins/exploration_professions.py").read_text(encoding="utf-8")
_inventory_equipment_source = (_root / "player/session_mixins/inventory_equipment.py").read_text(encoding="utf-8")
for _needle in (
    "def _write_record_numeric_fallback(",
    "Authored combat/reward/economy values are design decisions.",
    "authored_numeric = {",
):
    if _needle not in _generator_source:
        _semantic_errors.append("generator restraint regression: missing " + _needle)
for _needle in (
    "def equipment_progression_budget_v1138(level):",
    "(50, 38)", "(100, 100)", "(200, 240)", "(600, 1200)",
    "def equipment_defense_step_v1138(level):",
):
    if _needle not in _items_resource_source:
        _semantic_errors.append("shared EQ progression regression: missing " + _needle)
if "return equipment_progression_budget_v1138(mastery)" not in _equipment_source:
    _semantic_errors.append(
        "class EQ progression regression: shop no longer uses shared progression budget"
    )
for _needle in ("(50, 15_000)", "(100, 100_000)", "(200, 1_250_000)", "(600, 100_000_000)"):
    if _needle not in _economy_source:
        _semantic_errors.append("quest income progression regression: missing " + _needle)
for _needle in ('baseline_key = f"_v1138_authored_{key}"', "procedural_no_limit", '"world_boss": 3.00'):
    if _needle not in _runtime_progression_source:
        _semantic_errors.append("runtime progression feel regression: missing " + _needle)

for _needle in (
    "V1138_RESOURCE_SALE_ANCHORS = (",
    "(100, 700)",
    "(200, 3_000)",
    "(600, 90_000)",
    "def v1138_resource_sale_base_coins(stage):",
):
    if _needle not in _runtime_progression_source:
        _semantic_errors.append(
            "profession income progression regression: missing " + _needle
        )

for _needle in (
    "def fish_trophy_value_multiplier_v1138(",
    "def fish_jackpot_xp_multiplier_v1138(",
    "def rare_resource_xp_multiplier_v1138(",
    '"value_mult": 15',
    '"value_mult": 20',
):
    if _needle not in _items_resource_source:
        _semantic_errors.append(
            "profession jackpot resource regression: missing " + _needle
        )

for _needle in (
    "def profession_resource_sale_value_v1138(",
    "fish_trophy_value_multiplier_v1138(item_id)",
    "values = self.generic_item_sale_value(item_id, item)",
):
    if _needle not in _sales_source:
        _semantic_errors.append(
            "profession sale jackpot regression: missing " + _needle
        )

for _needle in (
    "TROFEUM WĘDKARSKIE",
    "BONUS ZA WYJĄTKOWY POŁÓW",
    "JACKPOT GÓRNICZY",
    "BONUS ZA WYJĄTKOWE DREWNO",
    "BONUS ZA WYJĄTKOWĄ ROŚLINĘ",
):
    if _needle not in _gathering_source:
        _semantic_errors.append(
            "profession jackpot feedback regression: missing " + _needle
        )

for _needle in (
    "def v1138_boss_chest_gold_anchor(power):",
    "(200, 8_000)",
    "(600, 700_000)",
):
    if _needle not in _protocol_utils_source:
        _semantic_errors.append(
            "boss chest income regression: missing " + _needle
        )

for _needle in (
    "discovery_mult = 2.00 if is_new else 1.00",
    "discovery_reward_silver",
    "v1138_resource_sale_base_coins(_level)",
):
    if _needle not in _exploration_prof_source:
        _semantic_errors.append(
            "exploration profession reward regression: missing " + _needle
        )

for _needle in (
    '"sell_gold": 900',
    '"gold": (400, 1_500)',
):
    if _needle not in _equipment_source:
        _semantic_errors.append(
            "geode reward regression: missing " + _needle
        )
if "JACKPOT GEODY" not in _inventory_equipment_source:
    _semantic_errors.append("geode jackpot feedback regression: missing JACKPOT GEODY")

_equipment_stats_source = (_root / "player/session_mixins/equipment_stats.py").read_text(encoding="utf-8")
_combat_feedback_source = (_root / "player/session_mixins/skill_learning.py").read_text(encoding="utf-8")
for _needle in (
    "def physical_defense_base(",
    "constitution * 0.42",
):
    if _needle not in _generator_source:
        _semantic_errors.append("physical defense progression regression: missing " + _needle)
if "generator_core_v027.physical_defense_base(" not in _equipment_stats_source:
    _semantic_errors.append("equipment CON defense regression: physical_defense_base not used")
for _needle in (
    "defense_cap_ratio = 0.60 if v0863_is_boss_template(template) else 0.75",
    'f"{defense_name.capitalize()} zatrzymuje {reduction} obrażeń. "',
):
    if _needle not in _combat_feedback_source:
        _semantic_errors.append("defense feel regression: missing " + _needle)

# Smoczy Świat v1.13.0 feature contract retained by v1.13.2. Fast predeploy stays source-only,
# while the module itself performs the full assembled-world runtime audit.
_manifest_source = (_root / "core/runtime_manifest.py").read_text(encoding="utf-8")
_dragon_world_source = (_root / "world/dragon_world.py").read_text(encoding="utf-8")
if "'world/dragon_world.py'" not in _manifest_source:
    _semantic_errors.append("dragon world regression: module missing from runtime manifest")
if 'EXPLICIT_RUNTIME_EXPORTS["world/dragon_world.py"]' not in _manifest_source:
    _semantic_errors.append(
        "dragon world architecture regression: module must stay on explicit runtime lane"
    )
try:
    from core.runtime_manifest import (
        RUNTIME_MODULES as _runtime_modules,
        EXPLICIT_RUNTIME_EXPORTS as _explicit_runtime_exports,
        LEGACY_COMPATIBILITY_ALLOWLIST as _legacy_compatibility_allowlist,
    )
    _observed_legacy = tuple(
        _path for _path in _runtime_modules
        if _path not in _explicit_runtime_exports
    )
    if _observed_legacy != tuple(_legacy_compatibility_allowlist):
        _missing_legacy_review = [
            _path for _path in _observed_legacy
            if _path not in _legacy_compatibility_allowlist
        ]
        _stale_legacy_review = [
            _path for _path in _legacy_compatibility_allowlist
            if _path not in _observed_legacy
        ]
        _semantic_errors.append(
            "maintainable-core compatibility regression: "
            f"unreviewed={_missing_legacy_review}; stale={_stale_legacy_review}"
        )
except Exception as exc:
    _semantic_errors.append(
        f"maintainable-core compatibility precheck failed: {type(exc).__name__}: {exc}"
    )
_dragon_world_needles = (
    'DRAGON_WORLD_VERSION = "1.13.0"',
    'if len(DRAGON_WORLD_ROOMS) != 64:',
    'if len(DRAGON_WORLD_LORDS) != 5:',
    'if len(DRAGON_WORLD_QUESTS) != 12:',
    '"dragon_q_ashen_hunt"',
    '30_000',
    '"dragon_q_sovereign"',
    '75_000',
    'GUIDE_DESTINATION_ALIASES["smoczy swiat"] = gate',
    'manual_stat_progress',
)
for _needle in _dragon_world_needles:
    if _needle not in _dragon_world_source:
        _semantic_errors.append(
            "dragon world regression: missing " + _needle
        )

# v1.13.2: modules loaded through native_runtime share a compatibility namespace.
# Generic helper names from world_expansion_i.py must therefore never be
# redefined by dragon_world.py, even when they start with an underscore.
_dragon_forbidden_runtime_helpers = (
    "def _room(",
    "def _link(",
    "def _mob(",
    "def _spawn(",
    "def _quest(",
    "def _npc(",
)
for _needle in _dragon_forbidden_runtime_helpers:
    if _needle in _dragon_world_source:
        _semantic_errors.append(
            "dragon runtime symbol collision regression: " + _needle
        )
_dragon_required_namespaced_helpers = (
    "def _dragon_room(",
    "def _dragon_link(",
    "def _dragon_mob(",
    "def _dragon_spawn(",
    "def _dragon_quest(",
    "def _dragon_npc(",
)
for _needle in _dragon_required_namespaced_helpers:
    if _needle not in _dragon_world_source:
        _semantic_errors.append(
            "dragon runtime helper namespace regression: missing " + _needle
        )

# v1.13.1: uncapped stats must stay generous globally. The natural stat
# requirement curve is used without the old x2 tax and every source is
# accelerated x4 before race/guild bonuses and uncapped post-400 scaling.
_balance_source = (_root / "config/balance.py").read_text(encoding="utf-8")
_character_source = (_root / "player/character.py").read_text(encoding="utf-8")
_stat_pace_needles = (
    "STAT_XP_REQUIREMENT_MULTIPLIER = 1.0",
    "STAT_XP_REWARD_MULTIPLIER = 4.0",
)
for _needle in _stat_pace_needles:
    if _needle not in _balance_source:
        _semantic_errors.append(
            "stat XP pace regression: missing " + _needle
        )
if "base_amount * STAT_XP_REWARD_MULTIPLIER" not in _character_source:
    _semantic_errors.append(
        "stat XP pace regression: global reward multiplier not applied in add_stat_progress"
    )
if "racial_amount - accelerated_amount" not in _character_source:
    _semantic_errors.append(
        "stat XP pace regression: global boost would be misreported as racial bonus"
    )

# v1.13.3: help_refresh has multiple historical refresh layers. The final
# v1.11.97 truth layer must carry the live stat-XP wording because it overwrites
# the earlier Generator Core help before HELP_SURFACE_AUDIT_V11197 runs.
_help_source = (_root / "admin/help_refresh.py").read_text(encoding="utf-8")
_final_help_start = _help_source.find("def refresh_help_truth_v11197():")
_final_help_end = _help_source.find("\n\nrefresh_help_truth_v11197()", _final_help_start)
if _final_help_start < 0 or _final_help_end < 0:
    _semantic_errors.append(
        "final stat HELP regression: refresh_help_truth_v11197 block missing"
    )
else:
    _final_help_block = _help_source[_final_help_start:_final_help_end]
    _final_stat_help_needles = (
        'HELP_TOPICS["statystyki"]',
        "bez twardego limitu",
        "x4",
        "15 akcji",
    )
    for _needle in _final_stat_help_needles:
        if _needle not in _final_help_block:
            _semantic_errors.append(
                "final stat HELP regression: missing " + _needle
            )

_runtime_progression_source = (_root / "world/runtime_progression.py").read_text(encoding="utf-8")
_runtime_triplet_needles = (
    "tertiary_stat, tertiary_amount",
    "tertiary_stat: tertiary_amount",
    "generated_budget = max(3",
)
for _needle in _runtime_triplet_needles:
    if _needle not in _runtime_progression_source:
        _semantic_errors.append(
            "runtime class EQ triplet regression: missing " + _needle
        )
if "primary_stat, primary_amount, secondary_stat, secondary_amount = (" in _runtime_progression_source:
    _semantic_errors.append(
        "runtime class EQ triplet regression: stale four-value unpack remains"
    )
if 'item["stats"] = {secondary_stat: secondary_amount}' in _runtime_progression_source:
    _semantic_errors.append(
        "runtime class EQ triplet regression: tertiary stat would be discarded"
    )

_class_eq_source = (_root / "systems/equipment_crafting.py").read_text(encoding="utf-8")
_class_eq_three_stat_needles = (
    "def class_equipment_base_stat_triplet(class_name):",
    'return "intelligence", "willpower", "constitution"',
    'return "dexterity", "strength", "constitution"',
    'return "strength", "dexterity", "constitution"',
    "budget = max(3, int(legacy_amount or 0))",
    '"class_base_stat_triplet": (',
    "Class EQ stat triplet mismatch",
    "Legendary class EQ stat triplet mismatch",
    "Legendary class relic stat triplet mismatch",
)
for _needle in _class_eq_three_stat_needles:
    if _needle not in _class_eq_source:
        _semantic_errors.append(
            "class EQ three-stat regression: missing " + _needle
        )

for _needle in (
    "CLASS_EQUIPMENT_STYLE_PROFILES = {",
    '"role": "zbalansowany"',
    '"role": "ofensywny"',
    '"role": "pancerny"',
    "def class_equipment_flat_power_channels(",
    'if class_name == "Mec":',
    'return {"attack": hybrid, "magic_attack": hybrid}',
    "class_name, legacy_affix_amount, slot, style_index",
):
    if _needle not in _class_eq_source:
        _semantic_errors.append(
            "class EQ style/power regression: missing " + _needle
        )

for _needle in (
    'int(item.get("class_equipment_style", 1) or 1)',
    "linie stylu nadal identyczne",
    "nie ma obu kanałów Attack/Magic Attack",
):
    if _needle not in _runtime_progression_source:
        _semantic_errors.append(
            "runtime class EQ style regression: missing " + _needle
        )

_equipment_stats_source = (_root / "player/session_mixins/equipment_stats.py").read_text(encoding="utf-8")
if "Linie można mieszać." not in _equipment_stats_source:
    _semantic_errors.append(
        "class EQ mixed-style set regression: set status no longer confirms mixing"
    )

_class_set_start = _equipment_stats_source.find("    def class_set_counts(self):")
_class_set_end = _equipment_stats_source.find(
    "    def class_set_stat_bonus_totals(self):",
    _class_set_start,
)
if _class_set_start < 0 or _class_set_end < 0:
    _semantic_errors.append("class EQ mixed-style set regression: class_set_counts block missing")
else:
    _class_set_block = _equipment_stats_source[_class_set_start:_class_set_end]
    if "class_set_name" in _class_set_block:
        _semantic_errors.append(
            "class EQ mixed-style set regression: set thresholds depend on style name"
        )
    if "logical_slots.setdefault(class_name, set()).add(item.get(\"slot\"))" not in _class_set_block:
        _semantic_errors.append(
            "class EQ mixed-style set regression: thresholds no longer count class logical slots"
        )

_shops_source = (_root / "player/session_mixins/shops_teachers.py").read_text(encoding="utf-8")
for _needle in (
    "class_equipment_style_role",
    "Style tej samej klasy można mieszać bez utraty progów setu 2/4/6/8",
):
    if _needle not in _shops_source:
        _semantic_errors.append(
            "class EQ shop style regression: missing " + _needle
        )

_equipment_compare_source = (_root / "player/session_mixins/equipment_compare.py").read_text(encoding="utf-8")
for _needle in ('"attack": "Attack"', '"magic_attack": "Magic Attack"'):
    if _needle not in _equipment_compare_source:
        _semantic_errors.append(
            "EQ compare flat-power regression: missing " + _needle
        )

# v1.13.8: sklep, crafting i drop mają różne role, ale wspólną epokę mocy.
for _needle in (
    "BLACKSMITH_MASTERWORK_STAT_PROFILE = {",
    "def _blacksmith_masterwork_profile_v1138(",
    '"crafted_masterwork": True',
    '"sockets": int(masterwork["sockets"])',
    "progression_budget = equipment_progression_budget_v1138(required_mastery)",
    "quality = 0.80 + rng.random() * 0.30",
    '"drop_quality": round(float(quality), 3)',
):
    if _needle not in _items_resource_source:
        _semantic_errors.append(
            "craft/drop EQ identity regression: missing " + _needle
        )

for _needle in (
    "def crypt_affix_amount(tier, rarity_key, affix_key):",
    "budget = equipment_progression_budget_v1138(mastery)",
    '"mythic": 0.38',
    '"Unikalny Bossowy"',
    '"sockets": sockets',
):
    if _needle not in _dungeon_source:
        _semantic_errors.append(
            "crypt loot progression regression: missing " + _needle
        )


_final_help_source = (_root / "admin/help_refresh.py").read_text(encoding="utf-8")
for _needle in (
    "Siłę + Zręczność + Kondycję",
    "Inteligencję + Siłę Woli + Kondycję",
    "legendarnych setów i reliktów klasowych",
    "trzy linie klasowego EQ",
    "Możesz dowolnie mieszać style",
    "Mec jako hybryda dostaje oba kanały",
    "zwykłe zbieractwo daje sensowny zarobek",
    "Rekiny, legendarne ryby i lewiatany",
    "JACKPOT",
):
    if _needle not in _final_help_source:
        _semantic_errors.append(
            "class EQ HELP regression: missing " + _needle
        )

_long_term_balance_source = (_root / "admin/long_term_balance_audit_v0502.py").read_text(encoding="utf-8")
_long_term_stat_needles = (
    "STAT_XP_REWARD_MULTIPLIER",
    'errors.append("stat requirement multiplier must be 1.0")',
    'errors.append("stat reward multiplier must be 4.0")',
    '"profession": 50, "tool": 65, "stat": 15,',
    "14.0 <= actions <= 16.0",
)
for _needle in _long_term_stat_needles:
    if _needle not in _long_term_balance_source:
        _semantic_errors.append(
            "long-term stat audit regression: missing " + _needle
        )
if 'stat requirement multiplier must be 2.0' in _long_term_balance_source:
    _semantic_errors.append(
        "long-term stat audit regression: stale x2 stat requirement contract"
    )
if '"stat": 120' in _long_term_balance_source:
    _semantic_errors.append(
        "long-term stat audit regression: stale 120-action stat target"
    )

try:
    from config.balance import (
        STAT_XP_REQUIREMENT_MULTIPLIER as _stat_req_mult,
        STAT_XP_REWARD_MULTIPLIER as _stat_reward_mult,
    )
    from core.generator_core import AXIS_TARGET_ACTIONS as _axis_target_actions
    _effective_stat_actions = (
        float(_axis_target_actions["stat"])
        * float(_stat_req_mult)
        / max(0.000001, float(_stat_reward_mult))
    )
    if _effective_stat_actions > 15.01:
        _semantic_errors.append(
            f"stat XP pace regression: effective actions per point {_effective_stat_actions:.2f} > 15"
        )
except Exception as exc:
    _semantic_errors.append(
        f"stat XP pace audit failed: {type(exc).__name__}: {exc}"
    )

if _semantic_errors:
    print("Soulbound v1.13.8 FAST PREDEPLOY FAILED: semantic contracts")
    for _error in _semantic_errors:
        print(f"ERROR: {_error}")
    raise SystemExit(1)

if audit["error_count"]:
    print("Soulbound v1.13.8 FAST PREDEPLOY FAILED")
    for error in audit["errors"]:
        print(f"ERROR: {error}")
    raise SystemExit(1)

print("Soulbound v1.13.8 FAST PREDEPLOY PASS")
print(
    "Semantic contracts: "
    f"{len(_semantic_audits)} audits PASS; AP runtime guards PASS"
)
print(f"Runtime manifest: {audit['runtime_module_count']} modules; {len(audit['missing_manifest_files'])} missing; {audit['syntax_error_count']} syntax errors")
print(
    f"Whole repo Python: {audit['all_python_source_count']} files; "
    f"{audit['all_source_syntax_error_count']} syntax errors; "
    f"{audit['duplicate_literal_key_count']} duplicate dict keys; "
    f"{audit['swallowed_exception_count']} swallowed exceptions; "
    f"{audit.get('intentional_swallowed_exception_count', 0)} intentional passes; "
    f"{audit['todo_fixme_count']} TODO/FIXME"
)
print(f"Docker COPY sources: {len(audit['missing_docker_copy_sources'])} missing")
print(f"Railway critical import: {'PASS' if audit['critical_import_ok'] else 'FAIL'}")
print(f"SQLite smoke: {audit['schema_table_count']} tables; {audit['schema_object_count']} objects")
print(f"Commands: {audit['alias_count']} aliases; {audit['registered_command_count']} registered handlers")
if audit.get("warning_count"):
    print(f"FAST PREDEPLOY WARNINGS: {audit['warning_count']}")
    for warning in audit.get("warnings", ())[:50]:
        print(f"WARNING: {warning}")
print("Full historical audit remains available with: python predeploy_full.py")
