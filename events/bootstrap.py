# -*- coding: utf-8 -*-
"""Default Soulbound event subscriptions."""
from events.bus import EventBus
from events.contracts import (MobDefeatedEvent, PlayerMobKillProgressionEvent, PlayerMobKillQuestEvent, ResourceGatheredEvent)
from events.listeners.chronicle import record_server_kill
from events.listeners.gathering_progression import credit_resource_progression
from events.listeners.kill_progression import credit_extended_kill_progression, credit_primary_kill_quest


def build_default_event_bus(server):
    bus = EventBus(error_reporter=server.report_runtime_error)
    # Chronicle was historically best-effort (try/except pass), preserve that.
    bus.subscribe(MobDefeatedEvent, record_server_kill, name="chronicle.server_kill", critical=False)
    # These replace direct gameplay progression calls, so failures remain critical.
    bus.subscribe(PlayerMobKillQuestEvent, credit_primary_kill_quest, name="quests.kill_credit", critical=True)
    bus.subscribe(PlayerMobKillProgressionEvent, credit_extended_kill_progression, name="progression.kill_extended", critical=True)
    bus.subscribe(ResourceGatheredEvent, credit_resource_progression, name="progression.gathering", critical=True)
    return bus
