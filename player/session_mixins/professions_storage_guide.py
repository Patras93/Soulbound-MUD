# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: professions_storage_guide."""
from player.session_mixins.profession_storage import SessionProfessionStorageMixin
from player.session_mixins.guide_navigation import SessionGuideNavigationMixin
from player.session_mixins.gathering import SessionGatheringMixin



# The original native mixin keeps its protected published code unchanged.
# These are the current, explicitly imported award implementations.
from player.session_mixins import current_profession_awards as _current_prof

class SessionProfessionsStorageGuideMixin(
    SessionProfessionStorageMixin,
    SessionGuideNavigationMixin,
    SessionGatheringMixin,
):
    """Compatibility aggregate; native contracts stay intact on disk."""
    grant_profession_progress = _current_prof.grant_profession_progress
    grant_tool_progress = _current_prof.grant_tool_progress
    grant_tool_reward_xp = _current_prof.grant_tool_reward_xp
    grant_profession_reward_xp = _current_prof.grant_profession_reward_xp
