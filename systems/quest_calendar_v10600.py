# -*- coding: utf-8 -*-
"""Adapter v106 do istniejącego zegara questów; jeden licznik SQLite."""
from systems.quest_calendar_v10400 import remaining_seconds, cadence_for_quest


def cadence_for_v106_quest(quest_id, definition):
    if not str(quest_id).startswith('v10600_contract_'):
        return None
    return cadence_for_quest(quest_id, definition)
