# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: help_codex_profile."""
from player.session_mixins.help_system import SessionHelpSystemMixin
from player.session_mixins.atlas_codex import SessionAtlasCodexMixin
from player.session_mixins.character_profile import SessionCharacterProfileMixin
from player.session_mixins.class_guild_progress import SessionClassGuildProgressMixin


class SessionHelpCodexProfileMixin(
    SessionHelpSystemMixin,
    SessionAtlasCodexMixin,
    SessionCharacterProfileMixin,
    SessionClassGuildProgressMixin,
):
    """Compatibility aggregate; methods live in focused maintenance mixins."""
    pass
