# -*- coding: utf-8 -*-
"""Soulbound v1.13.14 - final income balance for the 1-600 economy.

This pass runs after authored world/quest expansions. It keeps positive quest
currency inside a progression band and also exposes shared payout floors for
runtime systems that bypass the static quest finalizer (Courier, exploration
milestones, dynamic world tasks and Ocean 2.0). Item-only quests still remain
item-only. The goal is a coherent loop: play -> earn/sell -> afford meaningful
equipment, without making 5,000,000 Gold late-game equipment trivial.
"""
from __future__ import annotations

import math

from core.bootstrap_economy_professions import (
    legacy_currency_to_coins,
)
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from systems.items_resources import (
    V11314_ECONOMY_STAGE_ANCHORS,
    economy_stage_anchor_v11314,
)
from world.equipment_help import HELP_TOPICS, HELP_TOPIC_ALIASES


V1124_ECONOMY_INCOME_VERSION = "1.13.14"
V1124_ECONOMY_MAX_STAGE = 600

# Values are internal silver. 100 silver = 1 Gold.
# v1.13.8: midgame starts paying meaningfully and late game keeps scaling.
# stage 100 ~= 1k Gold, 300 ~= 75k, 400 ~= 300k, 600 ~= 1M before quest modifiers.
# Public legacy name retained for callers/audits.
V1124_QUEST_INCOME_ANCHORS = V11314_ECONOMY_STAGE_ANCHORS

V1138_ACTIVITY_INCOME_MULTIPLIER = {
    # Repeatable/small activities stay below a full quest payout.
    "courier": 0.30,
    "dynamic_world": 0.85,
    # Milestones and treasure are supposed to feel like a jackpot.
    "exploration100": 3.00,
    "ocean_trade": 0.55,
    "ocean_treasure": 2.50,
}


def v1138_activity_income(stage: int, kind: str, difficulty: float = 1.0) -> int:
    """Shared payout floor for systems that bypass the normal quest finalizer."""
    stage = max(1, min(V1124_ECONOMY_MAX_STAGE, int(stage or 1)))
    mult = float(V1138_ACTIVITY_INCOME_MULTIPLIER.get(str(kind), 1.0))
    difficulty = max(0.10, float(difficulty or 1.0))
    return max(1, int(round(v1124_income_anchor(stage) * mult * difficulty)))


V1124_QUEST_KIND_MULTIPLIER = {
    "talk_npc": 0.65,
    "talk_class_teacher": 0.65,
    "deliver_npc": 0.90,
    "collect": 1.00,
    "collect_resource": 1.00,
    "collect_category": 1.10,
    "collect_distinct_category": 1.18,
    "collect_resource_set": 1.25,
    "craft_set": 1.35,
    "kill": 1.25,
    "explore_frontier": 1.20,
    "discover_secret": 1.55,
    # These are the "worth waiting for" payouts.
    "mini_dungeon": 2.00,
    "legendary_rare": 2.50,
    "world_event": 2.75,
    "world_boss": 3.50,
}


def v1124_income_anchor(stage: int) -> int:
    """Compatibility API routed to the shared v1.13.14 economy curve."""
    return economy_stage_anchor_v11314(stage)


def _v1124_numeric_stage(record) -> int:
    keys = (
        "generator_level", "level", "required_character_level", "required_level",
        "required_soul_level", "min_profession_level", "required_profession_level",
        "min_tool_level", "required_mastery",
    )
    values = []
    for key in keys:
        try:
            value = int(record.get(key, 0) or 0)
        except (TypeError, ValueError, OverflowError):
            value = 0
        if value > 0:
            values.append(value)
    return max(values) if values else 0


def v1124_quest_stage(quest) -> int:
    """Infer economic stage from the quest itself and its real target."""
    stage = _v1124_numeric_stage(quest)

    target = str(quest.get("target") or "")
    mob = MOB_TEMPLATES.get(target)
    if isinstance(mob, dict):
        stage = max(stage, _v1124_numeric_stage(mob))

    item = ITEMS.get(target)
    if isinstance(item, dict):
        stage = max(stage, _v1124_numeric_stage(item))

    resource_targets = quest.get("resource_targets") or {}
    if isinstance(resource_targets, dict):
        for item_id in resource_targets:
            row = ITEMS.get(str(item_id))
            if isinstance(row, dict):
                stage = max(stage, _v1124_numeric_stage(row))

    return max(1, min(V1124_ECONOMY_MAX_STAGE, int(stage or 1)))


def v1124_quest_income_target(quest) -> int:
    stage = v1124_quest_stage(quest)
    base = float(v1124_income_anchor(stage))
    kind = str(quest.get("kind") or "").strip().lower()
    base *= float(V1124_QUEST_KIND_MULTIPLIER.get(kind, 1.0))

    needed = max(1, int(quest.get("needed", 1) or 1))
    # Workload matters, but quantity alone cannot multiply a payout without bound.
    base *= 1.0 + min(0.54, 0.06 * (needed - 1))

    if quest.get("repeatable"):
        base *= 0.85
    else:
        base *= 1.25

    # Soul trials are milestone progression and should feel more valuable than
    # ordinary jobs at the same stage, while still respecting the global band.
    if int(quest.get("required_soul_level", 0) or 0) > 0:
        base *= 2.25

    return max(1, int(round(base)))


def v1124_rebalance_positive_quest_currency():
    result = {
        "version": V1124_ECONOMY_INCOME_VERSION,
        "positive_quests": 0,
        "raised": 0,
        "lowered": 0,
        "unchanged": 0,
        "manual_protected": 0,
        "max_before_silver": 0,
        "max_after_silver": 0,
    }
    for quest in QUESTS.values():
        current = legacy_currency_to_coins(
            quest.get("reward_silver", 0),
            quest.get("reward_gold", 0),
            quest.get("reward_mithril", 0),
        )

        # v1.13.11: Hybrid Quest Rewards are an authored contract. This income
        # finalizer may rebalance automatic quests only; a manual marker must
        # win exactly, even when this module is imported after Generator Core.
        manual_marker = quest.get("manual_currency_reward_coins")
        manual_mode = quest.get("currency_reward_mode") == "manual"
        if manual_marker is not None or manual_mode:
            result["manual_protected"] += 1
            if current > 0:
                result["positive_quests"] += 1
                result["max_before_silver"] = max(
                    result["max_before_silver"], int(current)
                )
            if manual_marker is not None:
                manual = max(0, int(manual_marker))
                quest["reward_silver"] = manual
                quest["reward_gold"] = 0
                quest["reward_mithril"] = 0
                result["max_after_silver"] = max(
                    result["max_after_silver"], int(manual)
                )
            # If mode=manual is malformed and lacks a marker, leave it untouched
            # so the audit below can fail loudly instead of silently rebalancing it.
            continue

        if current <= 0:
            # Deliberately item-only / progression-only quests stay item-only.
            continue

        result["positive_quests"] += 1
        result["max_before_silver"] = max(result["max_before_silver"], int(current))

        target = v1124_quest_income_target(quest)
        floor = max(1, int(round(target * 0.60)))
        cap = max(floor, int(round(target * 1.60)))
        balanced = max(floor, min(cap, int(current)))

        if balanced > current:
            result["raised"] += 1
        elif balanced < current:
            result["lowered"] += 1
        else:
            result["unchanged"] += 1

        quest["reward_silver"] = int(balanced)
        quest["reward_gold"] = 0
        quest["reward_mithril"] = 0
        result["max_after_silver"] = max(result["max_after_silver"], int(balanced))

    return result


ECONOMY_INCOME_BALANCE_V1124 = v1124_rebalance_positive_quest_currency()


def economy_income_audit_v1124():
    errors = []
    if v1124_income_anchor(50) != 15_000:
        errors.append("stage 50 anchor changed")
    if v1124_income_anchor(100) != 100_000:
        errors.append("stage 100 anchor changed")
    if v1124_income_anchor(300) != 7_500_000:
        errors.append("stage 300 anchor changed")
    if v1124_income_anchor(400) != 30_000_000:
        errors.append("stage 400 anchor changed")
    if v1124_income_anchor(600) != 100_000_000:
        errors.append("stage 600 anchor changed")
    if v1138_activity_income(100, "courier") != 30_000:
        errors.append("courier activity income floor changed")
    if v1138_activity_income(100, "exploration100") != 300_000:
        errors.append("exploration jackpot income floor changed")

    board = ITEMS.get("moogle_board") or {}
    if int(board.get("fur_shop_gold_cost", 0) or 0) != 5_000_000:
        errors.append("Moogle Board UOSS Gold cost changed")

    # Every positive quest must end inside its reviewed floor/cap.
    for quest_id, quest in QUESTS.items():
        current = legacy_currency_to_coins(
            quest.get("reward_silver", 0),
            quest.get("reward_gold", 0),
            quest.get("reward_mithril", 0),
        )
        manual_marker = quest.get("manual_currency_reward_coins")
        manual_mode = quest.get("currency_reward_mode") == "manual"
        if manual_marker is not None or manual_mode:
            if not manual_mode:
                errors.append(f"{quest_id}: manual currency marker without manual mode")
            if manual_marker is None:
                errors.append(f"{quest_id}: manual currency mode without marker")
            else:
                expected = max(0, int(manual_marker))
                if current != expected:
                    errors.append(
                        f"{quest_id}: manual reward changed {current}!={expected}"
                    )
                if (
                    int(quest.get("reward_gold", 0) or 0) != 0
                    or int(quest.get("reward_mithril", 0) or 0) != 0
                ):
                    errors.append(f"{quest_id}: manual reward uses split currency")
            continue
        if current <= 0:
            continue
        target = v1124_quest_income_target(quest)
        floor = max(1, int(round(target * 0.60)))
        cap = max(floor, int(round(target * 1.60)))
        if not (floor <= current <= cap):
            errors.append(
                f"{quest_id}: {current} outside {floor}-{cap} at stage "
                f"{v1124_quest_stage(quest)}"
            )
            if len(errors) >= 20:
                break

    return {
        "version": V1124_ECONOMY_INCOME_VERSION,
        "error_count": len(errors),
        "errors": errors,
        **ECONOMY_INCOME_BALANCE_V1124,
    }


ECONOMY_INCOME_AUDIT_V1124 = economy_income_audit_v1124()
if ECONOMY_INCOME_AUDIT_V1124["error_count"]:
    raise RuntimeError(
        "Economy Income Audit v1.13.14 failed: "
        + "; ".join(ECONOMY_INCOME_AUDIT_V1124["errors"])
    )


HELP_TOPICS["ekonomia"] = [
    "Ekonomia 1-600 ma kilka równoległych dróg zarobku: walka, bossowie, questy, profesje, sprzedaż zasobów, Kurierzy, eksploracja i handel morski.",
    "Główna pętla gry to: grasz i zdobywasz rzeczy -> sprzedajesz lub kończysz aktywności -> odkładasz realną sumę -> kupujesz, craftujesz albo farmisz wyraźnie lepsze EQ.",
    "Zwykła aktywność daje sensowny dochód, ale rzadkie sukcesy są jackpotami: rzadki połów, legendarna żyła, wyjątkowy drop, skarb, boss albo 100 procent strefy mają być wyraźnie odczuwalne.",
    "Docelowa baza pełnego zadania wynosi około: poziom 50 — 150 Gold, 100 — 1 000 Gold, 150 — 3 500 Gold, 200 — 12 500 Gold, 300 — 75 000 Gold, 400 — 300 000 Gold, 500 — 600 000 Gold, 600 — 1 000 000 Gold; rodzaj i trudność zadania modyfikują tę wartość.",
    "Powtarzalne aktywności, np. Kurierzy i handel morski, płacą mniej niż duży jednorazowy milestone, ale mają realnie finansować kolejne zakupy zamiast dawać symboliczne grosze.",
    "100 procent strefy oraz mapy skarbów są milestone/jackpot payouts; ich nagroda skaluje się z etapem zawartości, nie z przypadkowo wysokim levelem po powrocie do starej strefy.",
    "Questy celowo bez waluty, dające przedmioty lub nagrody progresji, pozostają bez wypłaty pieniężnej.",
    "Ceny źródłowego wyposażenia UOSSMUD, np. 5 000 000 Gold u Wattsa, nie są automatycznie obniżane przez ten balans.",
    "v1.13.14: klasowe EQ skaluje cenę z tą samą krzywą co zarobki, więc zakup jest realnym celem.",
    "v1.13.14: znalezione EQ i odnawialne skrzynie mają wartość zależną od etapu zamiast starych symbolicznych kwot.",
]
HELP_TOPIC_ALIASES.update({
    "zarobki": "ekonomia",
    "zarabianie": "ekonomia",
    "income": "ekonomia",
    "economy": "ekonomia",
})
