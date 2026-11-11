# -*- coding: utf-8 -*-
"""Runtime validation for event subscriptions."""
from __future__ import annotations
from events.contracts import MobDefeatedEvent, PlayerMobKillProgressionEvent, PlayerMobKillQuestEvent, ResourceGatheredEvent

EXPECTED = {
    MobDefeatedEvent: ("chronicle.server_kill",),
    PlayerMobKillQuestEvent: ("quests.kill_credit",),
    PlayerMobKillProgressionEvent: ("progression.kill_extended",),
    ResourceGatheredEvent: ("progression.gathering",),
}


def validate_event_bus(bus):
    errors = []
    details = {}
    for event_type, expected_names in EXPECTED.items():
        names = tuple(row.name for row in bus.listeners_for(event_type))
        details[event_type.__name__] = names
        if names != expected_names:
            errors.append(f"{event_type.__name__}: listeners={names!r}, expected={expected_names!r}")
    return {"error_count": len(errors), "errors": errors, "listeners": details}
