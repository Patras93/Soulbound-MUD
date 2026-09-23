# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: crafting_inventory_equipment."""
from player.session_mixins.crafting import SessionCraftingMixin
from player.session_mixins.inventory_equipment import SessionInventoryEquipmentMixin
from player.session_mixins.shops_teachers import SessionShopsTeachersMixin


class SessionCraftingInventoryEquipmentMixin(
    SessionCraftingMixin,
    SessionInventoryEquipmentMixin,
    SessionShopsTeachersMixin,
):
    """Compatibility aggregate; gameplay methods live in focused mixins."""
    pass
