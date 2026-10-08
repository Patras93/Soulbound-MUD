# -*- coding: utf-8 -*-
"""Runtime regression gate: Zaklinanie tool seller survives separate class EQ shops."""
from __future__ import annotations

from types import SimpleNamespace


def audit_enchanting_vendor_v1202():
    from data.catalogs import NPCS, ROOMS, ITEMS
    from systems.equipment_crafting import SHOPS, SHOP_SELLERS
    from systems.items_resources import CLASS_SHOP_CLASSES_BY_ROOM
    from core.mines_threat import TOOL_SHOP_ROOMS
    from player.session_mixins.command_registry import resolve_session_command
    from player.session_mixins.shops_teachers import SessionShopsTeachersMixin

    checks = 0
    errors = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(label)

    room_id = 'guild_arcane_chamber'
    seller_id = 'guild_quartermaster_arcane'
    item_id = 'runic_focus'
    seller = NPCS.get(seller_id, {})
    tool = ITEMS.get(item_id, {})
    offers = list(SHOPS.get(room_id, ()))
    check(room_id in ROOMS, 'Zaklinanie chamber missing')
    check(seller.get('room') == room_id, 'Selene moved away from the workshop')
    check(seller.get('shopkeeper') is True, 'Selene is not a shopkeeper')
    check(SHOP_SELLERS.get(room_id) == seller_id, 'Selene seller mapping missing')
    check(offers == [item_id], f'Runic Focus offer not isolated: {offers[:5]}')
    check(tool.get('name') == 'Fokus Runiczny', 'Runic Focus item missing')
    check(tool.get('type') == 'tool' and tool.get('tool_type') == 'enchanting', 'wrong tool type')
    check(int(tool.get('price') or 0) > 0, 'Runic Focus has invalid price')
    check(TOOL_SHOP_ROOMS.get(item_id) == room_id, 'tool navigation points to wrong room')
    check(room_id not in CLASS_SHOP_CLASSES_BY_ROOM, 'class shop accidentally restored in shared chamber')
    check(len(CLASS_SHOP_CLASSES_BY_ROOM) == 14, 'separate class shops missing')
    check(resolve_session_command('list') == 'shop', 'list command no longer opens shop')
    check(resolve_session_command('kup') == 'buy', 'kup command no longer opens buy')
    sample = SimpleNamespace(character=SimpleNamespace(room_id=room_id))
    check(SessionShopsTeachersMixin.current_shop_offers(sample) == [item_id],
          'player cannot see Runic Focus at Selene')
    # Distinct class shops must still show class EQ rather than profession tools.
    check(all(item_id not in SHOPS.get(room, ()) for room in CLASS_SHOP_CLASSES_BY_ROOM),
          'profession tool leaked into class-specific EQ shops')
    return {'checks': checks, 'error_count': len(errors), 'errors': errors}
