# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: world_progression."""
from player.session_mixins.museum_bounty import SessionMuseumBountyMixin
from player.session_mixins.world_events_endgame import SessionWorldEventsEndgameMixin
from player.session_mixins.exploration_progress import SessionExplorationProgressMixin
from player.session_mixins.collection_loot_records import SessionCollectionLootRecordsMixin


class SessionWorldProgressionMixin(
    SessionMuseumBountyMixin,
    SessionWorldEventsEndgameMixin,
    SessionExplorationProgressMixin,
    SessionCollectionLootRecordsMixin,
):
    """Compatibility aggregate; methods live in focused maintenance mixins."""
    pass
