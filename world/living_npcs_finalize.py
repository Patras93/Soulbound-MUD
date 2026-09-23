# -*- coding: utf-8 -*-
"""Late reconciliation for NPCs created after the main living-NPC pass.

Kept separate from audits so validation remains read-only.
"""
from world.living_npcs import ensure_hourly_quests_for_idle_npcs

LIVING_NPCS_FINALIZE_STATE = ensure_hourly_quests_for_idle_npcs()

__all__ = ["LIVING_NPCS_FINALIZE_STATE"]
