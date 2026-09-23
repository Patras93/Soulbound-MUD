# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: admin_gathering_sales."""
from player.session_mixins.admin_tools import SessionAdminToolsMixin
from player.session_mixins.gathering_actions import SessionGatheringActionsMixin
from player.session_mixins.sales import SessionSalesMixin


class SessionAdminGatheringSalesMixin(
    SessionAdminToolsMixin,
    SessionGatheringActionsMixin,
    SessionSalesMixin,
):
    """Compatibility aggregate; methods live in focused maintenance mixins."""
    pass
