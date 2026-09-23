# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: core_progression."""
from player.session_mixins.session_runtime_state import SessionRuntimeStateMixin
from player.session_mixins.dungeon_progression import SessionDungeonProgressionMixin
from player.session_mixins.rest_mana import SessionRestManaMixin
from player.session_mixins.class_progression import SessionClassProgressionMixin


class SessionCoreProgressionMixin(
    SessionRuntimeStateMixin,
    SessionDungeonProgressionMixin,
    SessionRestManaMixin,
    SessionClassProgressionMixin,
):
    """Compatibility aggregate; methods live in focused maintenance mixins."""
    pass
