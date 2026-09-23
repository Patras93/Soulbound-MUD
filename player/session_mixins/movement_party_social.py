# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: movement_party_social."""
from player.session_mixins.movement import SessionMovementMixin
from player.session_mixins.party import SessionPartyMixin
from player.session_mixins.exp_terrain import SessionExpTerrainMixin
from player.session_mixins.social_base import SessionBaseSocialMixin
from player.session_mixins.banking_charisma import SessionBankingCharismaMixin


class SessionMovementPartySocialMixin(
    SessionMovementMixin,
    SessionPartyMixin,
    SessionExpTerrainMixin,
    SessionBaseSocialMixin,
    SessionBankingCharismaMixin,
):
    """Compatibility aggregate; methods live in focused maintenance mixins."""
    pass
