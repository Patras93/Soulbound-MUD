# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: professions_storage_guide."""
from player.session_mixins.profession_storage import SessionProfessionStorageMixin
from player.session_mixins.guide_navigation import SessionGuideNavigationMixin
from player.session_mixins.gathering import SessionGatheringMixin


class SessionProfessionsStorageGuideMixin(
    SessionProfessionStorageMixin,
    SessionGuideNavigationMixin,
    SessionGatheringMixin,
):
    """Compatibility aggregate; gameplay methods live in focused mixins."""
    pass
