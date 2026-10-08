# -*- coding: utf-8 -*-
"""v1.20.3: end-to-end shop and profession-tool smoke tests on a disposable SQLite DB.

These tests execute the actual Session shop, item-info and buy methods. They do
not contact the production server or modify real accounts.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from types import SimpleNamespace


def audit_final_stability_v1203():
    from core.classes_skills import CLASSES, RACES
    from core.mines_threat import TOOL_SHOP_ROOMS
    from data.catalogs import ITEMS, NPCS, ROOMS
    from player.character import Character
    from player.session import Session
    from player.session_mixins.command_registry import resolve_session_command
    from storage.database import Database
    from systems.equipment_crafting import SHOPS, SHOP_SELLERS

    errors = []
    checks = 0

    def check(condition, description):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(description)

    check(resolve_session_command('list') == 'shop', 'list command routing')
    check(resolve_session_command('kup') == 'buy', 'kup command routing')
    check(len(TOOL_SHOP_ROOMS) == 14, 'expected 14 profession tools')

    for room_id, offers in SHOPS.items():
        check(room_id in ROOMS, f'shop room is missing: {room_id}')
        seller_id = SHOP_SELLERS.get(room_id)
        check(bool(seller_id), f'shop has no seller: {room_id}')
        check(seller_id in NPCS and NPCS[seller_id].get('room') == room_id,
              f'shopkeeper is outside the shop: {room_id}')
        check(all(item_id in ITEMS for item_id in offers), f'missing item in shop {room_id}')
        for item_id in offers:
            item = ITEMS.get(item_id)
            if item:
                try:
                    cash_price = Session.__new__(Session).shop_item_base_value_silver(item)
                    token_cost = int(item.get('fur_shop_token_cost', 0) or 0)
                    check(cash_price > 0 or token_cost > 0,
                          f'item with no real cost in {room_id}: {item_id}')
                except (TypeError, ValueError, KeyError) as exc:
                    errors.append(f'bad shop price {room_id}/{item_id}: {exc}')

    for tool_id, room_id in TOOL_SHOP_ROOMS.items():
        tool = ITEMS.get(tool_id, {})
        check(tool.get('type') == 'tool' and bool(tool.get('tool_type')),
              f'incorrect profession tool: {tool_id}')
        check(tool_id in SHOPS.get(room_id, ()), f'tool unavailable at seller: {tool_id}')
        check(room_id in ROOMS, f'unknown tool seller room: {tool_id}')

    grammar = {key: 'Kontrola' for key in ('nom', 'gen', 'dat', 'acc', 'ins', 'loc', 'voc')}

    async def run(db):
        number = 0

        def new_session(room_id):
            nonlocal number
            number += 1
            account_id = db.create_account(f'final_shop_{number}', 'test-only')
            db.create_character(account_id, f'Audyt{number}', RACES[0], CLASSES[0], grammar)
            session = Session.__new__(Session)
            session.server = SimpleNamespace(db=db, sessions=set(), parties={})
            session.account_id = account_id
            session.character = Character.from_row(db.character_for_account(account_id))
            session.character.room_id = room_id
            messages = []

            async def send(message, *args, **kwargs):
                messages.append(str(message))

            session.send = send
            return session, messages

        # All 36 shops: real listing and item-info, no missing NPC or bad item ID.
        for room_id, offers in SHOPS.items():
            session, messages = new_session(room_id)
            try:
                await session.shop()
                if offers:
                    check(any('Oferta sklepu' in m for m in messages),
                          f'shop list missing in {room_id}')
                    before = len(messages)
                    await session.shop('info 1')
                    check(any('INFORMACJE O SKLEPIE' in m for m in messages[before:]),
                          f'shop info missing in {room_id}')
                else:
                    check(any('nie ma sklepu' in m for m in messages),
                          f'empty shop behaves unexpectedly: {room_id}')
            except Exception as exc:
                errors.append(f'shop {room_id} crashed: {type(exc).__name__}: {exc}')

        # All profession tools: insufficient funds -> successful purchase ->
        # duplicate purchase denied without a second payment. SQLite persists it.
        for tool_id, room_id in TOOL_SHOP_ROOMS.items():
            session, messages = new_session(room_id)
            account_id = session.account_id
            idx = list(SHOPS[room_id]).index(tool_id) + 1
            try:
                session.character.gold = session.character.silver = session.character.mithril = 0
                await session.buy(str(idx))
                check(db.item_qty(account_id, tool_id) == 0,
                      f'free tool with empty wallet: {tool_id}')
                check(not any('Kupujesz:' in m for m in messages),
                      f'false purchase success without money: {tool_id}')
                session.character.gold = 10_000_000
                before = session.character_wallet_silver_value()
                await session.buy(str(idx))
                after = session.character_wallet_silver_value()
                check(db.item_qty(account_id, tool_id) == 1,
                      f'purchase failed: {tool_id}')
                check(0 < before - after <= before,
                      f'wrong purchase cost: {tool_id}')
                check(db.item_qty(account_id, tool_id) == 1 and
                      db.character_for_account(account_id)['silver'] == session.character.silver,
                      f'purchase not persisted: {tool_id}')
                await session.buy(ITEMS[tool_id]['name'])
                check(db.item_qty(account_id, tool_id) == 1,
                      f'duplicate bound tool: {tool_id}')
                check(session.character_wallet_silver_value() == after,
                      f'duplicate tool charged player again: {tool_id}')
            except Exception as exc:
                errors.append(f'tool {tool_id} crashed: {type(exc).__name__}: {exc}')

    with tempfile.TemporaryDirectory(prefix='sb-final-1203-') as folder:
        db = Database(os.path.join(folder, 'audit.db'))
        try:
            asyncio.run(run(db))
        finally:
            db.conn.close()

    return {'checks': checks, 'errors': errors, 'error_count': len(errors),
            'shops': len(SHOPS), 'profession_tools': len(TOOL_SHOP_ROOMS)}
