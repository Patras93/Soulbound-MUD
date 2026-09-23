# -*- coding: utf-8 -*-
"""Soulbound v0.47.0 combat compatibility aggregate.

Combat implementation is split by responsibility so fixes no longer require
editing one 2000-line module. All focused combat modules use explicit imports.
"""
from player.session_mixins.combat_skills import SessionCombatSkillsMixin
from player.session_mixins.combat_damage import SessionCombatDamageMixin
from player.session_mixins.combat_realtime import SessionCombatRealtimeMixin
from player.session_mixins.combat_rewards import SessionCombatRewardsMixin
from player.session_mixins.combat_survival import SessionCombatSurvivalMixin


class SessionCombatMixin(
    SessionCombatSkillsMixin,
    SessionCombatDamageMixin,
    SessionCombatRealtimeMixin,
    SessionCombatRewardsMixin,
    SessionCombatSurvivalMixin,
):
    """Compatibility aggregate for the public Session combat API."""
    pass
