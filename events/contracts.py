# -*- coding: utf-8 -*-
"""Typed domain events for Soulbound.

Events describe facts that already happened.  Producers do not need to know
which quest, chronicle, bounty or analytics systems react to them.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True, frozen=True)
class MobDefeatedEvent:
    killer_session: Any
    mob: Any
    recipients: tuple[Any, ...]
    template_id: str
    template: Mapping[str, Any]
    fight_duration_ms: int | None


@dataclass(slots=True, frozen=True)
class PlayerMobKillQuestEvent:
    session: Any
    mob: Any


@dataclass(slots=True, frozen=True)
class PlayerMobKillProgressionEvent:
    session: Any
    mob: Any
    template: Mapping[str, Any]
    bestiary_id: str
    fight_duration_ms: int | None
    party_size: int
    is_boss: bool
    is_world_boss: bool
    is_legendary_rare: bool
    is_v016_world_boss: bool
    is_great_ruin_guardian: bool
    is_legendary_event_boss: bool
    biome: str


@dataclass(slots=True, frozen=True)
class ResourceGatheredEvent:
    session: Any
    action: str
    item_id: str
    quantity: int
    category: str
    bounty_kind: str
    dynamic_kind: str
    legendary_kind: str
    faction: str
    faction_reason: str
    lifetime_stat: str
    secondary_category: str | None = None
    distinct_category: str | None = None
    distinct_item_id: str | None = None
    rare_achievement: str | None = None
    rare_lifetime_stat: str | None = None


@dataclass(slots=True, frozen=True)
class QuestCompletedEvent:
    session: Any
    quest_id: str
    quest: Mapping[str, Any]


@dataclass(slots=True, frozen=True)
class PlayerDiedEvent:
    session: Any
    killer: str
    room_id: str
