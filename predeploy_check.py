#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast Railway predeploy gate for Soulbound v1.13.29.

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
    print(f"Soulbound v1.13.29 FAST PREDEPLOY FAILED: database import: {type(exc).__name__}: {exc}")
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
        "Soulbound v1.13.29 FAST PREDEPLOY FAILED: "
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

# v1.13.10 hotfix: Generator Core now preserves authored item prices, so all
# one-time starter profession tools must carry the same canonical authored
# price instead of relying on a later generator rewrite.
_data_items_source = (_root / "data/items.py").read_text(encoding="utf-8")
_equipment_crafting_source_v11310 = (_root / "systems/equipment_crafting.py").read_text(encoding="utf-8")
_professions_source_v11310 = (_root / "systems/professions.py").read_text(encoding="utf-8")
_equipment_help_source_v11310 = (_root / "world/equipment_help.py").read_text(encoding="utf-8")
for _tool_id in (
    "fishing_rod", "pickaxe", "saw", "crafting_hammer", "chef_knife",
    "herbalist_sickle", "alchemy_mortar",
):
    _match = re.search(
        rf'"{re.escape(_tool_id)}"\s*:\s*\{{.*?"price"\s*:\s*(\d+)',
        _data_items_source,
        re.DOTALL,
    )
    if not _match or int(_match.group(1)) != 1200:
        _semantic_errors.append(
            f"starter tool authored price regression: {_tool_id} != 1200"
        )
_match = re.search(
    r'"jeweler_pliers"\s*,?\s*\)\s*\)',
    _equipment_crafting_source_v11310,
)
_jeweler_block = re.search(
    r'"name"\s*:\s*"Szczypce Jubilerskie".*?"price"\s*:\s*(\d+)',
    _equipment_crafting_source_v11310,
    re.DOTALL,
)
if not _match or not _jeweler_block or int(_jeweler_block.group(1)) != 1200:
    _semantic_errors.append("starter tool authored price regression: jeweler_pliers != 1200")
# v1.13.10: the historical v0.8.61 runtime rebalance runs after the authored
# item catalog and must not overwrite the canonical starter-tool price.
for _tool_id in (
    "fishing_rod", "pickaxe", "saw", "crafting_hammer", "chef_knife",
    "herbalist_sickle", "alchemy_mortar", "jeweler_pliers",
):
    _match = re.search(
        rf'"{re.escape(_tool_id)}"\s*:\s*(\d+)',
        _equipment_help_source_v11310,
    )
    if not _match or int(_match.group(1)) != 1200:
        _semantic_errors.append(
            f"late runtime starter tool price regression: {_tool_id} != 1200"
        )

for _tool_id in (
    "tailor_kit", "tanning_knife", "carpenter_tools", "runic_focus",
    "archaeology_brush", "surveyor_compass",
):
    _match = re.search(
        rf'"{re.escape(_tool_id)}"\s*:\s*\{{.*?"price"\s*:\s*(\d+)',
        _professions_source_v11310,
        re.DOTALL,
    )
    if not _match or int(_match.group(1)) != 1200:
        _semantic_errors.append(
            f"starter tool authored price regression: {_tool_id} != 1200"
        )

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

# v1.13.10: Generator Core is a fallback, not an unconditional overwrite layer.
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
_courier_source = (_root / "player/session_mixins/courier_delivery.py").read_text(encoding="utf-8")
_exploration_progress_source = (_root / "player/session_mixins/exploration_progress.py").read_text(encoding="utf-8")
_ocean_session_source = (_root / "player/session_mixins/ocean.py").read_text(encoding="utf-8")
_generation_systems_source = (_root / "world/generation_systems.py").read_text(encoding="utf-8")
for _needle in (
    "def _write_record_numeric_fallback(",
    "def _write_nested_numeric_fallback(",
    "Authored combat/reward/economy values are design decisions.",
    "has_authored_sale = any(",
    "preserve_none=True",
    '"""Attach stage and fill only genuinely missing item numeric fields."""',
    '"""Attach stage and fill only skill numbers that authored content omitted."""',
):
    if _needle not in _generator_source:
        _semantic_errors.append("generator restraint regression: missing " + _needle)
for _forbidden in (
    "authored_numeric = {",
    "authored_nested = {",
    "QUEST_CURRENCY_ANCHORS = (",
    "def _economy_anchor_value(",
):
    if _forbidden in _generator_source:
        _semantic_errors.append(
            "Generator cleanup regression: stale pattern remains " + _forbidden
        )
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
_economy_curve_source_v11317 = (_root / "core/economy_curve.py").read_text(encoding="utf-8")
for _needle in ("(50, 15_000)", "(100, 100_000)", "(200, 1_250_000)", "(600, 100_000_000)"):
    if _needle not in _economy_curve_source_v11317:
        _semantic_errors.append("quest income progression regression: missing shared anchor " + _needle)

# v1.13.11: the late 1-600 income finalizer must never rewrite quests marked
# by Hybrid Quest Rewards as manually balanced.
for _needle in (
    'manual_marker = quest.get("manual_currency_reward_coins")',
    'manual_mode = quest.get("currency_reward_mode") == "manual"',
    'result["manual_protected"] += 1',
    'if manual_marker is not None or manual_mode:',
):
    if _needle not in _economy_source:
        _semantic_errors.append(
            "manual quest currency protection regression: missing " + _needle
        )

# v1.13.12: Equipment Completeness must compare the complete mechanical class-EQ
# profile introduced in v1.13.8, including flat Attack/Magic Attack channels.
_audits_source_v11312 = (_root / "admin/audits.py").read_text(encoding="utf-8")

# v1.13.21: Hybrid Quest Reward Audit must follow authored-wins. The legacy
# Generator fallback floor of 1001 silver cannot reject authored quest payouts.
if 'if reward < 1001:' in _audits_source_v11312:
    _semantic_errors.append(
        "hybrid quest audit regression: stale Generator-owned 1001 silver floor"
    )
if 'if reward < SILVER_PER_GOLD:' not in _audits_source_v11312:
    _semantic_errors.append(
        "hybrid quest audit regression: missing shared 1 Gold economy floor"
    )

# v1.13.22: Terrain Threat Audit must verify the actual runtime-room floor,
# not the historical v0.36.2 wrapper/function identity that was later folded
# into Generator Core.
if '"_v0362_recommended_room_floor" in gsrc' in _audits_source_v11312:
    _semantic_errors.append(
        "terrain threat audit regression: obsolete wrapper-name release gate"
    )
for _needle in (
    'recommended = int(room.get("recommended_mastery", 0) or 0)',
    'lvl = max(lvl, recommended)',
):
    if _needle not in _generator_source:
        _semantic_errors.append(
            "terrain recommended mastery floor regression: missing " + _needle
        )

# v1.13.29 hotfix: the historical party-drop audit must validate the
# single shared roll contract after authored_drop_chance_v11329 transforms
# the configured chance. Do not regress to matching the pre-v1.13.29 source.
_party_drop_audit_source_v11329 = (_root / "admin/audits.py").read_text(encoding="utf-8")
for _needle in (
    "_effective_roll = \"if random.random() <= _effective_drop_chance_v11329:\"",
    "_recipient_expand = \"drop_recipients = party_drop_recipients_v0359(item_id, recipients)\"",
    'count("random.random()") == 1',
):
    if _needle not in _party_drop_audit_source_v11329:
        _semantic_errors.append(
            "party drop single-roll audit v1.13.29 regression: missing " + _needle
        )
if '"if random.random() <= chance" in combat_source' in _party_drop_audit_source_v11329:
    _semantic_errors.append(
        "party drop single-roll audit v1.13.29 still matches stale pre-transform roll"
    )

# v1.13.29: drop chance / reward excitement contracts.
_drop_excitement_source_v11329 = (_root / "systems/drop_excitement.py").read_text(encoding="utf-8")
_equipment_help_source_v11329 = (_root / "world/equipment_help.py").read_text(encoding="utf-8")
_combat_rewards_source_v11329 = (_root / "player/session_mixins/combat_rewards.py").read_text(encoding="utf-8")
_dungeons_source_v11329 = (_root / "systems/dungeons_regions.py").read_text(encoding="utf-8")
_uoss_runtime_source_v11329 = (_root / "world/uoss_superboss_runtime.py").read_text(encoding="utf-8")
_help_truth_source_v11329 = (_root / "admin/help_truth_current.py").read_text(encoding="utf-8")

for _needle in (
    '"normal": 0.07',
    '"elite": 0.18',
    '"rare": 0.28',
    '"mini_boss": 0.40',
    '"boss": 0.55',
    '"world_boss": 0.70',
    '"world_boss": 0.60',
    "rare_mob",
    "v016_legendary_rare",
    "v016_world_boss",
    "def authored_drop_chance_v11329",
    "DROP_EXCITEMENT_AUDIT_V11329",
):
    if _needle not in _drop_excitement_source_v11329:
        _semantic_errors.append("drop excitement v1.13.29 regression: missing " + _needle)

for _needle in (
    "class_equipment_drop_chance_v11329",
    "return class_equipment_drop_chance_v11329(template)",
):
    if _needle not in _equipment_help_source_v11329:
        _semantic_errors.append("rank-aware corpse EQ v1.13.29 regression: missing " + _needle)

for _needle in (
    "authored_drop_chance_v11329",
    "_effective_drop_chance_v11329",
):
    if _needle not in _combat_rewards_source_v11329:
        _semantic_errors.append("named boss drop floor v1.13.29 regression: missing " + _needle)

for _needle in (
    "V11329_CRYPT_END_WEIGHTS",
    "def crypt_rarity_weights_v11329",
    "def crypt_rarity_progression_audit_v11329",
    "CRYPT_RARITY_PROGRESSION_AUDIT_V11329",
    '"common": 30.0',
    '"mythic": 7.0',
    '"common": 3.0',
    '"mythic": 22.0',
):
    if _needle not in _dungeons_source_v11329:
        _semantic_errors.append("Crypt rarity v1.13.29 regression: missing " + _needle)

# UOSS already has the desired high-value reward loop. v1.13.29 must not
# accidentally replace it with generic boss RNG.
for _needle in (
    "def superboss_personal_reward_v11135",
    "db.add_item(account_id, item_id, 1)",
    "def superboss_personal_unique_drops_v11158",
    "def superboss_shared_drop_v11135",
    "SUPERBOSS_LOCKOUT_SECONDS_V11157 = 24 * 60 * 60",
):
    if _needle not in _uoss_runtime_source_v11329:
        _semantic_errors.append("UOSS reward contract regression: missing " + _needle)

for _needle in (
    "Rare 28%",
    "World Boss 70%",
    "30/30/20/13/7",
    "3/17/30/28/22",
    "osobistą nagrodę tokenową",
):
    if _needle not in _help_truth_source_v11329:
        _semantic_errors.append("HELP drop excitement v1.13.29 regression: missing " + _needle)

# v1.13.28: HELP must describe the final runtime, not historical milestone prose.
_help_truth_source_v11328 = (_root / "admin/help_truth_current.py").read_text(encoding="utf-8")
_help_system_source_v11328 = (_root / "player/session_mixins/help_system.py").read_text(encoding="utf-8")
_runtime_manifest_source_v11328 = (_root / "core/runtime_manifest.py").read_text(encoding="utf-8")

for _needle in (
    "def refresh_help_truth_current_v11328",
    "def help_freshness_audit_v11328",
    "HELP_FRESHNESS_AUDIT_V11328",
    "Scan every public topic",
    "COMMAND_CATALOG.bind_help",
    '"tempo_profesji"',
    '"gamefeel"',
    '"zrodla_eq"',
    '"Brakujące price=None/0',
    '"Etap źródła EQ',
    '"handel morski pokazuje oferty; handel morski wez <nr>, handel morski oddaj, handel morski porzuc obsługują kontrakt.',
):
    if _needle not in _help_truth_source_v11328:
        _semantic_errors.append("HELP truth v1.13.28 regression: missing " + _needle)

for _needle in (
    "aoe on / aoe off",
    "kolejka usuń <nr>",
    "handel morski wez <nr> / oddaj / porzuc",
    "Tożsamość EQ",
    "Etap źródła",
    "Brak price=None/0",
    "gdzie zdobyc <przedmiot> [pelne]",
    "przetop stop",
):
    if _needle not in _help_system_source_v11328:
        _semantic_errors.append("HELP command index v1.13.28 regression: missing " + _needle)

_manifest_help = "'admin/help_truth_current.py'"
_manifest_late_layers = (
    "'world/uoss_superboss_world.py'",
    "'world/global_difficulty_overdrive.py'",
    "'systems/smithing_materials.py'",
    "'systems/runtime_memory.py'",
    "'admin/release_integrity_v0369.py'",
)
if _manifest_help not in _runtime_manifest_source_v11328:
    _semantic_errors.append("HELP truth v1.13.28 missing from runtime manifest")
elif 'EXPLICIT_RUNTIME_EXPORTS["admin/help_truth_current.py"]' not in _runtime_manifest_source_v11328:
    _semantic_errors.append(
        "HELP truth v1.13.28 must stay on explicit runtime lane"
    )
else:
    _help_index_v11328 = _runtime_manifest_source_v11328.index(_manifest_help)
    for _late_layer_v11328 in _manifest_late_layers:
        if (
            _late_layer_v11328 in _runtime_manifest_source_v11328
            and _help_index_v11328
            < _runtime_manifest_source_v11328.index(_late_layer_v11328)
        ):
            _semantic_errors.append(
                "HELP truth v1.13.28 is not final after " + _late_layer_v11328
            )

# v1.13.27: loot source progression must remain monotonic and source-aware.
_equipment_source_progression_v11327 = (_root / "systems/equipment_crafting.py").read_text(encoding="utf-8")
_items_source_progression_v11327 = (_root / "systems/items_resources.py").read_text(encoding="utf-8")
_dungeons_source_progression_v11327 = (_root / "systems/dungeons_regions.py").read_text(encoding="utf-8")
_shop_source_progression_ui_v11327 = (_root / "player/session_mixins/shops_teachers.py").read_text(encoding="utf-8")
_compare_source_progression_ui_v11327 = (_root / "player/session_mixins/equipment_compare.py").read_text(encoding="utf-8")

for _needle in (
    '"source_progression_stage": required_mastery',
    '"source_progression_stage": mastery',
    "boss set source regression",
):
    if _needle not in _equipment_source_progression_v11327:
        _semantic_errors.append("loot source class/boss progression regression: missing " + _needle)

for _needle in (
    '"source_progression_stage": level',
    '"equipment_identity_source": "corpse_drop"',
    "LOOT_SOURCE_EQUIPMENT_AUDIT_V11327",
):
    if _needle not in _items_source_progression_v11327:
        _semantic_errors.append("loot source craft/corpse progression regression: missing " + _needle)

for _needle in (
    "LEGACY_NAMED_UNIQUE_SOURCES_V11327",
    "def _upgrade_named_unique_from_source_v11327",
    "source_progression_floor_v11327",
    "LOOT_SOURCE_PROGRESSION_AUDIT_V11327",
    '"source_progression_stage": mastery',
):
    if _needle not in _dungeons_source_progression_v11327:
        _semantic_errors.append("loot source dungeon/boss progression regression: missing " + _needle)

for _source, _label in (
    (_shop_source_progression_ui_v11327, "shop info"),
    (_compare_source_progression_ui_v11327, "equipment compare"),
):
    if "Etap źródła EQ:" not in _source or "source_progression_stage" not in _source:
        _semantic_errors.append(f"loot source progression UI regression: {_label}")

# v1.13.26: Equipment Identity 2.0 keeps acquisition sources materially distinct.
_equipment_identity_source_v11326 = (_root / "systems/equipment_crafting.py").read_text(encoding="utf-8")
_items_resources_identity_source_v11326 = (_root / "systems/items_resources.py").read_text(encoding="utf-8")
_dungeons_identity_source_v11326 = (_root / "systems/dungeons_regions.py").read_text(encoding="utf-8")
_uoss_identity_source_v11326 = (_root / "world/uoss_superboss_world.py").read_text(encoding="utf-8")
_shop_identity_ui_source_v11326 = (_root / "player/session_mixins/shops_teachers.py").read_text(encoding="utf-8")
_compare_identity_ui_source_v11326 = (_root / "player/session_mixins/equipment_compare.py").read_text(encoding="utf-8")

for _needle in (
    "def class_equipment_style_properties_v11326",
    "def legendary_class_set_properties_v11326",
    '"equipment_identity_source": "class_shop"',
    '"equipment_identity_source": "boss_set"',
    '"equipment_identity_source": "boss_relic"',
    "EQUIPMENT_IDENTITY_AUDIT_V11326",
):
    if _needle not in _equipment_identity_source_v11326:
        _semantic_errors.append("equipment identity shop/boss regression: missing " + _needle)

for _needle in (
    '"equipment_identity_source": "blacksmith"',
    '"equipment_identity_role": "masterwork_customization"',
    '"sockets": int(masterwork["sockets"])',
):
    if _needle not in _items_resources_identity_source_v11326:
        _semantic_errors.append("equipment identity craft regression: missing " + _needle)

for _needle in (
    '"equipment_identity_source": "crypt"',
    '"equipment_identity_role": "random_affix"',
    '"equipment_identity_source": "crypt_boss"',
):
    if _needle not in _dungeons_identity_source_v11326:
        _semantic_errors.append("equipment identity crypt regression: missing " + _needle)

for _needle in (
    '"equipment_identity_source", "uoss_unique"',
    '"equipment_identity_role", "special_effects"',
):
    if _needle not in _uoss_identity_source_v11326:
        _semantic_errors.append("equipment identity UOSS regression: missing " + _needle)

for _source, _needle, _label in (
    (_shop_identity_ui_source_v11326, '"Tożsamość EQ: "', "shop info"),
    (_compare_identity_ui_source_v11326, '"Tożsamość EQ: "', "equipment compare"),
):
    if _needle not in _source:
        _semantic_errors.append(f"equipment identity UI regression: {_label}")

# v1.13.25: old authored values may not bypass current loot/EQ value floors.
_legacy_value_source_v11325 = (_root / "systems/legacy_value_sweep.py").read_text(encoding="utf-8")
_sales_source_v11325 = (_root / "player/session_mixins/sales.py").read_text(encoding="utf-8")
_combat_rewards_source_v11325 = (_root / "player/session_mixins/combat_rewards.py").read_text(encoding="utf-8")
_items_source_v11325 = (_root / "data/items.py").read_text(encoding="utf-8")

for _needle in (
    "def shop_money_price_v11325",
    "explicit token-only contract",
    "def legacy_explicit_sale_floor_v11325",
    "def legacy_explicit_sale_value_v11325",
    "def legacy_identity_drop_spec_v11325",
    "manual_sale_value_exact",
    'sale_value_mode") == "manual"',
    "LEGACY_VALUE_SWEEP_AUDIT_V11325",
):
    if _needle not in _legacy_value_source_v11325:
        _semantic_errors.append("legacy value sweep helper regression: missing " + _needle)

for _needle in (
    "legacy_explicit_sale_value_v11325(item_id, item)",
    'if item.get("type") == "armor":',
    'total = max(',
    'result["silver"], result["gold"], result["mithril"]',
):
    if _needle not in _sales_source_v11325:
        _semantic_errors.append("legacy sale floor regression: missing " + _needle)

for _needle in (
    "def _v11325_legacy_identity_drop_spec",
    "legacy_identity_drop_spec_v11325",
    "Łup charakterystyczny:",
):
    if _needle not in _combat_rewards_source_v11325:
        _semantic_errors.append("legacy mob identity drop regression: missing " + _needle)

for _item_id in (
    "legacy_rat_tail",
    "legacy_goblin_salvage",
    "legacy_bandit_purse",
    "legacy_ancient_fragment",
):
    if f'"{_item_id}"' not in _items_source_v11325:
        _semantic_errors.append("legacy mob material regression: missing " + _item_id)

_banking_shop_source_v11325 = (_root / "player/session_mixins/banking_charisma.py").read_text(encoding="utf-8")
_shop_runtime_source_v11325 = (_root / "player/session_mixins/shops_teachers.py").read_text(encoding="utf-8")

for _needle in (
    "from systems.legacy_value_sweep import shop_money_price_v11325",
    "return shop_money_price_v11325(item)",
):
    if _needle not in _banking_shop_source_v11325:
        _semantic_errors.append("shop zero-price regression: banking helper missing " + _needle)

for _needle in (
    "def shop_offer_unit_cashback_silver",
    "def shop_offer_effective_money_silver",
    "def shop_offer_token_parts",
    "def shop_offer_cost_text",
    "price_text = self.shop_offer_cost_text(item)",
    "purchase_cost_text = self.shop_offer_cost_text(item, quantity)",
):
    if _needle not in _shop_runtime_source_v11325:
        _semantic_errors.append("shop price parity regression: missing " + _needle)

for _forbidden in (
    'price = int(item.get("price") or 0)\n            currency = item.get("currency", "silver")',
    'price_text = currency_reading_text(effective, 0, 0)',
    'unit_price = int(source_gold) * 100 if source_gold is not None',
):
    if _forbidden in _shop_runtime_source_v11325 or _forbidden in _banking_shop_source_v11325:
        _semantic_errors.append("shop zero-price regression: stale pricing path " + _forbidden)

# v1.13.24: Global "O Kurde" Game Feel must remain activity-specific and
# preserve exact authored/manual rewards.
_game_feel_source_v11324 = (_root / "systems/game_feel_rewards.py").read_text(encoding="utf-8")
_combat_realtime_source_v11324 = (_root / "player/session_mixins/combat_realtime.py").read_text(encoding="utf-8")
_gathering_source_v11324 = (_root / "player/session_mixins/gathering_actions.py").read_text(encoding="utf-8")
_crafting_source_v11324 = (_root / "player/session_mixins/crafting.py").read_text(encoding="utf-8")
_quest_commands_source_v11324 = (_root / "player/session_mixins/quest_commands.py").read_text(encoding="utf-8")
_exploration_source_v11324 = (_root / "player/session_mixins/exploration_progress.py").read_text(encoding="utf-8")

for _needle in (
    "def gather_jackpot_v11324",
    "def craft_inspiration_v11324",
    "def quest_completion_bonus_v11324",
    "def exploration_find_v11324",
    "def mob_attack_flavor_v11324",
    'quest.get("manual_currency_reward_coins") is not None',
    'quest.get("currency_reward_mode") == "manual"',
    "GAME_FEEL_AUDIT_V11324",
):
    if _needle not in _game_feel_source_v11324:
        _semantic_errors.append("global game feel helper regression: missing " + _needle)

if _gathering_source_v11324.count("gather_jackpot_v11324(") < 4:
    _semantic_errors.append("global game feel regression: not all four core gathering actions have jackpot rolls")
if _gathering_source_v11324.count("* _o_kurde_gather_xp_v11324") < 8:
    _semantic_errors.append("global game feel regression: gathering jackpot XP not applied to profession+tool")

for _source, _needles, _label in (
    (_combat_realtime_source_v11324, ("mob_attack_flavor_v11324", "_enemy_action_mult_v11324"), "combat identity"),
    (_crafting_source_v11324, ("craft_inspiration_v11324", "_o_kurde_craft_xp_v11324"), "craft inspiration"),
    (_quest_commands_source_v11324, ("quest_completion_bonus_v11324", "quest_bonus_coins_v11324"), "quest bonus"),
    (_exploration_source_v11324, ("exploration_find_v11324", "exploration_jackpots_v11324"), "exploration find"),
):
    for _needle in _needles:
        if _needle not in _source:
            _semantic_errors.append(f"global game feel regression: {_label} missing {_needle}")

# v1.13.23: ordinary mobs must keep real danger and a rare stage-scaled payout.
_global_difficulty_source_v11323 = (_root / "world/global_difficulty_overdrive.py").read_text(encoding="utf-8")
_combat_rewards_source_v11323 = (_root / "player/session_mixins/combat_rewards.py").read_text(encoding="utf-8")
_items_source_v11323 = (_root / "data/items.py").read_text(encoding="utf-8")
for _needle in (
    '"normal": 1.08',
    '"world_boss": 1.20',
    '"normal": 0.08',
    '"world_boss": 1.00',
    'def mob_trophy_spec_v11323(template):',
    'GLOBAL_MOB_FEEL_AUDIT_V11323',
):
    if _needle not in _global_difficulty_source_v11323:
        _semantic_errors.append("global mob feel regression: missing " + _needle)
for _needle in (
    'def _v11323_mob_trophy_spec(template):',
    'Rzadki łup bojowy: otrzymujesz',
):
    if _needle not in _combat_rewards_source_v11323:
        _semantic_errors.append("mob trophy reward boundary regression: missing " + _needle)
for _tier in range(1, 9):
    if f'"mob_trophy_t{_tier}"' not in _items_source_v11323:
        _semantic_errors.append(f"mob trophy catalog regression: missing tier {_tier}")
for _needle in (
    'int(item.get("attack", 0) or 0)',
    'int(item.get("magic_attack", 0) or 0)',
    'obrona + Attack/Magic Attack + staty + właściwości',
):
    if _needle not in _audits_source_v11312:
        _semantic_errors.append(
            "equipment completeness full-profile regression: missing " + _needle
        )

# v1.13.13: dedicated Crypt difficulty must be based on at least the current
# Generator Core stage/rank baseline even though generic runtime refresh now
# preserves authored combat numbers.
_crypt_party_source_v11313 = (_root / "world/crypt_party_rebalance.py").read_text(encoding="utf-8")
_crypt_floor_source_v11313 = (_root / "world/crypt_floor_progression.py").read_text(encoding="utf-8")
for _label, _source in (
    ("crypt_party", _crypt_party_source_v11313),
    ("crypt_floor", _crypt_floor_source_v11313),
):
    for _needle in (
        'template.get("_v1138_authored_max_hp"',
        'template.get("_v1138_authored_damage"',
        "generator_core_v027.mob_hp(stage, rank)",
        "generator_core_v027.mob_damage(stage, rank)",
        "base_hp = max(authored_hp, generator_hp)",
        "base_damage = max(authored_damage, generator_damage)",
    ):
        if _needle not in _source:
            _semantic_errors.append(
                f"crypt Generator baseline regression ({_label}): missing {_needle}"
            )
# v1.13.14: one shared 1-600 economy reference keeps earnings, prices,
# resale and renewable chest rewards in the same scale.
_crafting_quality_source_v11314 = (_root / "systems/crafting_quality.py").read_text(encoding="utf-8")
_sales_source_v11314 = (_root / "player/session_mixins/sales.py").read_text(encoding="utf-8")
_world_state_source_v11314 = (_root / "world/world_state.py").read_text(encoding="utf-8")
for _needle in (
    "ECONOMY_STAGE_ANCHORS = (",
    "def economy_stage_anchor(stage: int) -> int:",
    "ECONOMY_LANE_SHARE_ANCHORS = {",
    '"mob_currency": (',
    '"item_price": (',
    '"resource_sale": (',
    "def economy_lane_amount(stage: int, lane: str, multiplier: float = 1.0) -> int:",
):
    if _needle not in _economy_curve_source_v11317:
        _semantic_errors.append("shared o-kurde economy regression: missing " + _needle)
for _needle in (
    "from core.economy_curve import (",
    "V11314_ECONOMY_STAGE_ANCHORS,",
    "economy_stage_anchor_v11314,",
    "def class_equipment_shop_price_v11314(level, slot_base_price):",
):
    if _needle not in _items_resource_source:
        _semantic_errors.append("shared economy compatibility regression: missing " + _needle)
if "class_equipment_shop_price_v11314(" not in _equipment_source:
    _semantic_errors.append("class EQ price progression regression")
for _needle in (
    "V1124_QUEST_INCOME_ANCHORS = V11314_ECONOMY_STAGE_ANCHORS",
    "return economy_stage_anchor_v11314(stage)",
):
    if _needle not in _economy_source:
        _semantic_errors.append("shared quest economy regression: missing " + _needle)
if '"attack","magic_attack","power"' not in _crafting_quality_source_v11314:
    _semantic_errors.append("craft quality regression: Magic Attack is not scaled")
for _needle in (
    "V11314_ARMOR_RESALE_QUEST_FRACTION = {",
    "flat_power = attack + magic_attack",
    "economy_stage_anchor_v11314(stage)",
    "silver = min(silver, smith_cap)",
):
    if _needle not in _sales_source_v11314:
        _semantic_errors.append("valuable EQ resale regression: missing " + _needle)
for _needle in (
    "from core.bootstrap_economy_professions import SILVER_PER_GOLD",
    "from core.mines_threat import v0866_room_threat_profile",
    "from systems.items_resources import economy_stage_anchor_v11314",
    "V11314_TREASURE_CHEST_PAYOUT_MULTIPLIERS = {",
    "def treasure_chest_economy_stage_v11314(room_id):",
    "v0866_room_threat_profile(room_id, fallback=fallback)",
    "economy_stage_anchor_v11314(stage)",
    "V11314_TREASURE_CHEST_LEGACY_COINS",
):
    if _needle not in _world_state_source_v11314:
        _semantic_errors.append("treasure chest economy regression: missing " + _needle)

# v1.13.15: authored character/progression content must never be rebalanced
# by Generator Core. Generator owns stage math, procedural content and missing-value
# fallbacks only.
_character_resources_source_v11315 = (_root / "core/character_resources.py").read_text(encoding="utf-8")
_character_source_v11315 = (_root / "player/character.py").read_text(encoding="utf-8")
_classes_source_v11315 = (_root / "core/classes_skills.py").read_text(encoding="utf-8")
_progression600_source_v11315 = (_root / "core/progression_600.py").read_text(encoding="utf-8")

for _needle in (
    'return authored_character_hp_base(character_level, constitution)',
    'return authored_character_mana_base(character_level, intelligence, willpower)',
    'return authored_class_passive_profile(class_name)',
    'return authored_race_passive_profile(race_name)',
    'GENERATOR_TOP_LEVEL_VALUE_WHITELIST = frozenset({\n    "EXP_AREA_TARGET_POWER",\n})',
    '_write_record_numeric_fallback("QUESTS", q, "character_xp_reward"',
    '_write_record_numeric_fallback("QUESTS", q, "reward_soul_xp"',
    '_write_record_numeric_fallback("QUESTS", q, "reward_stat_progress"',
    '_write_record_numeric_fallback(table_name, recipe, "profession_xp", xp)',
    'has_authored_currency = any(',
    'protected.append(("CLASSES", _freeze_semantic(ns.get("CLASSES", ()))))',
    '"SOUL_TIER_POWER_BONUSES", "SOUL_TIER_CLASS_BONUS_PERCENT"',
    '"CLASS_SET_BONUSES",',
    "def authored_reward_snapshot(ns: dict) -> dict:",
    'audit["authored_rewards_preserved"] = authored_rewards_ok',
    "def authored_rewards_preserved(ns: dict, before: dict) -> bool:",
    "authored_rewards_ok = authored_rewards_preserved(",
    "Generator Core cannot mutate authored CLASS_SET_BONUSES",
    "Generator Core cannot mutate authored CLASSES Soul Weapon bases",
    'if field in q and int(q.get(field, 0) or 0) < 0:',
):
    if _needle not in _generator_source:
        _semantic_errors.append(
            "Generator authored-authority regression: missing " + _needle
        )

for _forbidden in (
    "    _generate_soul(ns)\n",
    "    _generate_class_race_numeric(ns)\n",
    "    _generate_class_set_bonuses(ns)\n",
):
    if _forbidden in _generator_source:
        _semantic_errors.append(
            "Generator still mutates authored progression: " + _forbidden.strip()
        )

for _needle in (
    'AUTHORED_CLASS_PASSIVE_PROFILES = {',
    '"Wojownik": {"kind": "physical_damage", "value": 0.10}',
    '"Strażnik": {"kind": "damage_reduction", "value": 0.10}',
    '"Mag": {"kind": "magic_damage", "value": 0.10}',
    '"Ork": {"kind": "max_hp", "value": 0.10}',
    '"Gnom": {"kind": "max_mana", "value": 0.15}',
    "def character_hp_base(character_level: int, constitution: int) -> int:",
    "def character_mana_base(",
):
    if _needle not in _character_resources_source_v11315:
        _semantic_errors.append(
            "authored character resource regression: missing " + _needle
        )

for _needle in (
    "authored_character_hp_base(self.character_level, self.constitution)",
    "authored_character_mana_base(",
    "return authored_class_passive_profile(class_name)",
    "return authored_race_passive_profile(self.race)",
):
    if _needle not in _character_source_v11315:
        _semantic_errors.append(
            "Character still depends on Generator identity math: missing " + _needle
        )

for _forbidden in (
    "generator_core_v027.character_hp_base(",
    "generator_core_v027.character_mana_base(",
    "generator_core_v027.class_passive_profile(",
    "generator_core_v027.race_passive_profile(",
):
    if _forbidden in _character_source_v11315:
        _semantic_errors.append(
            "Character Generator dependency regression: " + _forbidden
        )

for _needle in (
    "authored_character_hp_base(1, stats[\"constitution\"])",
    "authored_character_mana_base(",
    "authored_race_passive_profile(race[0])",
):
    if _needle not in _classes_source_v11315:
        _semantic_errors.append(
            "character creation resource parity regression: missing " + _needle
        )

for _forbidden in (
    "generator_core_v027.MAX_LEVEL",
    "generator_core_v027.GENERATOR_VERSION",
    "_v0362_original_graph_room_levels",
    "_v0362_original_runtime_room_level",
):
    if _forbidden in _progression600_source_v11315:
        _semantic_errors.append(
            "progression_600 monkey-patch regression: " + _forbidden
        )
for _needle in (
    "MAX_LEVEL = 600",
    'recommended = int(room.get("recommended_mastery", 0) or 0)',
    "lvl = max(lvl, recommended)",
):
    if _needle not in _generator_source:
        _semantic_errors.append(
            "Generator canonical 1-600/recommended-floor regression: missing " + _needle
        )

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

for _needle in (
    '"courier": 0.30',
    '"dynamic_world": 0.85',
    '"exploration100": 3.00',
    '"ocean_trade": 0.55',
    '"ocean_treasure": 2.50',
    "def v1138_activity_income(",
):
    if _needle not in _economy_source:
        _semantic_errors.append(
            "global activity income loop regression: missing " + _needle
        )

for _needle in (
    'v1138_activity_income(stage, "courier", route_factor)',
    "route_factor = 1.0 + min(0.75",
):
    if _needle not in _courier_source:
        _semantic_errors.append(
            "courier income loop regression: missing " + _needle
        )

for _needle in (
    'v1138_activity_income(',
    '"exploration100"',
    "stage = max(stages) if stages else fallback_stage",
):
    if _needle not in _exploration_progress_source:
        _semantic_errors.append(
            "exploration milestone income regression: missing " + _needle
        )

for _needle in (
    'v1138_activity_income(stage, "dynamic_world", complexity)',
):
    if _needle not in _generation_systems_source:
        _semantic_errors.append(
            "dynamic world income loop regression: missing " + _needle
        )

for _needle in (
    "def ocean_economy_stage_v1138(",
    'v1138_activity_income(stage, "ocean_trade", difficulty)',
    '"ocean_treasure"',
):
    if _needle not in _ocean_session_source:
        _semantic_errors.append(
            "ocean income loop regression: missing " + _needle
        )

_equipment_stats_source = (_root / "player/session_mixins/equipment_stats.py").read_text(encoding="utf-8")
_combat_feedback_source = (_root / "player/session_mixins/skill_learning.py").read_text(encoding="utf-8")
_player_math_source_v11316 = (_root / "core/player_math.py").read_text(encoding="utf-8")
_profession_timing_source_v11316 = (_root / "core/profession_timing.py").read_text(encoding="utf-8")
_combat_damage_source_v11316 = (_root / "player/session_mixins/combat_damage.py").read_text(encoding="utf-8")
_combat_realtime_source_v11316 = (_root / "player/session_mixins/combat_realtime.py").read_text(encoding="utf-8")
_combat_skills_source_v11316 = (_root / "player/session_mixins/combat_skills.py").read_text(encoding="utf-8")
_gathering_source_v11316 = (_root / "player/session_mixins/gathering.py").read_text(encoding="utf-8")
_progression_resources_source_v11316 = (_root / "core/progression_resources.py").read_text(encoding="utf-8")

for _needle in (
    "def character_attribute_power(",
    "def character_offensive_build_multiplier(",
    "def speed_from_dexterity(",
    "def basic_attack_hits_from_speed(",
    "def critical_chance_from_dexterity(",
    "0.035 + 0.365 * (",
    "_clamp(value, 0.035, 0.40)",
    "def critical_multiplier(",
    "def physical_defense_base(",
    "constitution * 0.42",
    "def magic_defense_base(",
    "def skill_level_power(",
    "def skill_cooldown_factor(",
    "def uncapped_stat_xp_gain(",
    "def mec_vmax_duration_seconds(",
):
    if _needle not in _player_math_source_v11316:
        _semantic_errors.append("player math ownership regression: missing " + _needle)

for _needle in (
    "character_hp_base(",
    "character_mana_base(",
    "physical_defense_base(",
    "magic_defense_base(",
    "character_attribute_power(",
    "speed_from_dexterity(",
):
    if _needle not in _equipment_stats_source:
        _semantic_errors.append("equipment/player math wiring regression: missing " + _needle)

for _forbidden in (
    "generator_core_v027.character_hp_base(",
    "generator_core_v027.character_mana_base(",
    "generator_core_v027.character_attribute_power(",
    "generator_core_v027.speed_from_dexterity(",
    "generator_core_v027.critical_chance_from_dexterity(",
    "generator_core_v027.critical_multiplier(",
    "generator_core_v027.physical_defense_base(",
    "generator_core_v027.magic_defense_base(",
):
    if _forbidden in _equipment_stats_source:
        _semantic_errors.append("equipment still depends on Generator player math: " + _forbidden)

for _source_name, _source in (
    ("combat_damage", _combat_damage_source_v11316),
    ("combat_realtime", _combat_realtime_source_v11316),
    ("combat_skills", _combat_skills_source_v11316),
    ("character", _character_source_v11315),
):
    for _forbidden in (
        "generator_core_v027.character_attribute_power(",
        "generator_core_v027.character_offensive_build_multiplier(",
        "generator_core_v027.speed_from_dexterity(",
        "generator_core_v027.basic_attack_hits_from_speed(",
        "generator_core_v027.uncapped_stat_xp_gain(",
        "generator_core_v027.mec_vmax_duration_seconds(",
    ):
        if _forbidden in _source:
            _semantic_errors.append(
                f"{_source_name} still depends on Generator player math: {_forbidden}"
            )

for _needle in (
    '"fishing": 16',
    '"fishing": 3',
    '"mining": 40',
    '"mining": 10',
    "def profession_action_seconds(",
    "profession_action_seconds(\"fishing\", 1) != 16",
):
    if _needle not in _profession_timing_source_v11316:
        _semantic_errors.append("authored profession timing regression: missing " + _needle)

if "authored_profession_action_seconds" not in _gathering_source_v11316:
    _semantic_errors.append("gathering does not use authored profession timing")
if "generator_core_v027.profession_action_seconds(" in _gathering_source_v11316:
    _semantic_errors.append("gathering still uses Generator profession timing")

for _needle in (
    "return skill_level_power(level)",
    "return skill_cooldown_factor(level)",
):
    if _needle not in _progression_resources_source_v11316:
        _semantic_errors.append("Skill Level player-math regression: missing " + _needle)

# v1.13.17: Generator cleanup — one economy, true fill-missing-only and
# no progression_600 monkey patches.
_combat_realtime_source_v11317 = (_root / "player/session_mixins/combat_realtime.py").read_text(encoding="utf-8")
_admin_audits_source_v11317 = (_root / "admin/audits.py").read_text(encoding="utf-8")
_help_refresh_source_v11318 = (_root / "admin/help_refresh.py").read_text(encoding="utf-8")
for _needle in (
    "from core.economy_curve import (",
    'economy_lane_amount(level, "mob_currency"',
    'economy_lane_amount(level, "item_price"',
    'economy_lane_amount(level, "resource_sale"',
    "economy_stage_anchor(level) * work_mult * repeat_mult * identity_mult",
    "has_authored_sale = any(",
    "_write_nested_numeric_fallback(",
):
    if _needle not in _generator_source:
        _semantic_errors.append("Generator v1.13.17 cleanup regression: missing " + _needle)

if '_write_record_numeric("CLASS_SKILLS", skill, "cooldown"' in _generator_source:
    _semantic_errors.append("skill fallback regression: cooldown is still directly overwritten")
if "authored_numeric = {" in _generator_source:
    _semantic_errors.append("item/skill snapshot-restore regression returned")

for _needle in (
    'f"Trafiasz {_actual_hits} razy po {_per_hit_damage} obrażeń. Łącznie {damage}. "',
    "_per_hit_damage = max(0, int(damage))",
):
    if _needle not in _combat_realtime_source_v11317:
        _semantic_errors.append("UOSS-style multi-hit feedback regression: missing " + _needle)

# v1.13.21: audit behavior, never Generator version identity.
for _source_name, _source in (
    ("admin/audits.py", _admin_audits_source_v11317),
    ("admin/help_refresh.py", _help_refresh_source_v11318),
):
    if "GENERATOR_CORE_VERSION !=" in _source:
        _semantic_errors.append(
            f"{_source_name}: Generator version must not be a release gate"
        )
    if "GENERATOR_CORE_VERSION ==" in _source:
        _semantic_errors.append(
            f"{_source_name}: Generator version must not be a release gate"
        )
for _needle in (
    '"generator_version": str(GENERATOR_CORE_VERSION)',
):
    if _needle not in _admin_audits_source_v11317:
        _semantic_errors.append(
            "admin audits lost diagnostic Generator version reporting"
        )
    if _needle not in _help_refresh_source_v11318:
        _semantic_errors.append(
            "help_refresh audit lost diagnostic Generator version reporting"
        )


if re.search(r'GENERATOR_VERSION\s*=\s*["\']0\.\d+\.\d+["\']', _generator_source) is None:
    _semantic_errors.append("Generator version declaration missing")
# The declaration above is informational. No audit is allowed to depend on its value.

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

# v1.13.10: sklep, crafting i drop mają różne role, ale wspólną epokę mocy.
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
    "Jackpot",
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
    print("Soulbound v1.13.29 FAST PREDEPLOY FAILED: semantic contracts")
    for _error in _semantic_errors:
        print(f"ERROR: {_error}")
    raise SystemExit(1)

if audit["error_count"]:
    print("Soulbound v1.13.29 FAST PREDEPLOY FAILED")
    for error in audit["errors"]:
        print(f"ERROR: {error}")
    raise SystemExit(1)

print("Soulbound v1.13.29 FAST PREDEPLOY PASS")
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
