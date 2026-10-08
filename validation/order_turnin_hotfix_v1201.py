# -*- coding: utf-8 -*-
"""Live SQLite turn-in regression for all profession NPCs; never touches game data."""
from __future__ import annotations

import asyncio
import os
import tempfile
from types import SimpleNamespace


def audit_order_turnin_hotfix_v1201():
    from core.classes_skills import RACES, CLASSES
    from player.character import Character
    from player.session import Session
    from player.session_mixins.crafting_orders import (
        CRAFTING_ORDER_NPCS_V0600,
        CRAFTING_ORDER_BROKEN_TURNIN_CUTOFF_V1201,
    )
    from storage.database import Database
    from systems.content_registry import NPCS

    errors = []
    checks = 0

    def check(condition, description):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(description)

    async def run(db):
        counter = 0
        cases = {key: "Kontrola" for key in ("nom", "gen", "dat", "acc", "ins", "loc", "voc")}

        def make(npc_id, *, cycle=1000, physical=True, old=False):
            nonlocal counter
            counter += 1
            account_id = db.create_account(f"orders_hotfix_{counter}", "temporary-test-only")
            db.create_character(account_id, f"Kontrola{counter}", RACES[0], CLASSES[0], cases)
            session = Session.__new__(Session)
            session.server = SimpleNamespace(db=db, sessions=set(), parties={})
            session.account_id = account_id
            session.character = Character.from_row(db.character_for_account(account_id))
            session.character.room_id = NPCS[npc_id]["room"]
            messages = []

            async def send(message, *args, **kwargs):
                messages.append(str(message))

            session.send = send
            spec = CRAFTING_ORDER_NPCS_V0600[npc_id]
            source = spec["source"]
            if source == "gather":
                item_id = f"__gather__:{spec['gather_category']}:1"
                ids, _, _ = session.quest_collect_category_info(spec["gather_category"])
                physical_id = sorted(ids)[0]
            elif source == "action":
                item_id = f"__action__:{spec['action_type']}:1"
                physical_id = None
            else:
                recipes = session.crafting_order_recipe_rows_v0600(npc_id)
                if not recipes:
                    raise AssertionError(f"Brak receptur zamówień: {npc_id}")
                item_id = recipes[0][2]
                physical_id = item_id
            if physical and physical_id:
                db.add_item(account_id, physical_id, 1)
            offer = {
                "cycle": cycle, "npc_id": npc_id, "profession": spec["profession"],
                "item_id": item_id, "item_name": "Testowe zamówienie", "needed": 1,
                "reward_coins": 150, "reward_profession_xp": 100, "reward_tool_xp": 100,
                "tool_type": spec["tool_type"],
            }
            db.start_crafting_order_v0600(account_id, offer)
            db.increment_crafting_order_v0600(account_id, item_id, 1)
            if old:
                db.conn.execute("UPDATE crafting_orders_v0600 SET accepted_at=? WHERE account_id=?", (
                    CRAFTING_ORDER_BROKEN_TURNIN_CUTOFF_V1201 - 1, account_id,
                ))
                db.conn.commit()
            return session, messages, offer, physical_id

        def wallet_in_silver(character):
            return int(character.silver) + 100 * int(character.gold) + 100_000_000 * int(character.mithril)

        # One complete, real SQLite order per specialist, with exact inventory debit.
        for npc_id in CRAFTING_ORDER_NPCS_V0600:
            session, msgs, offer, physical_id = make(npc_id)
            before_silver = wallet_in_silver(session.character)
            await session.handle_crafting_orders_v0600("oddaj")
            account_id = session.account_id
            completed = db.crafting_order_offer_completed_v0700(
                account_id, offer["cycle"], npc_id, offer["item_id"], 1,
            )
            check(completed, f"{npc_id}: zapis ukończenia")
            check(any("ZAMÓWIENIE WYKONANE" in msg for msg in msgs), f"{npc_id}: komunikat sukcesu")
            check(wallet_in_silver(session.character) == before_silver + 150, f"{npc_id}: waluta")
            if physical_id:
                check(db.item_qty(account_id, physical_id) == 0, f"{npc_id}: dokładne pobranie towaru")
            before_retry = wallet_in_silver(session.character)
            await session.handle_crafting_orders_v0600("oddaj")
            check(wallet_in_silver(session.character) == before_retry, f"{npc_id}: brak drugiej nagrody")

        # v1.20.0 failed *after* consuming stock; recover only pre-hotfix orders.
        for npc_id in ("specialist_mining", "specialist_crafting"):
            session, msgs, offer, physical_id = make(npc_id, physical=False, old=True, cycle=2000)
            await session.handle_crafting_orders_v0600("oddaj")
            check(db.crafting_order_offer_completed_v0700(
                session.account_id, 2000, npc_id, offer["item_id"], 1
            ), f"{npc_id}: stare zamówienie bez towaru odzyskane")
            check(any("NAPRAWA ZAMÓWIENIA v1.20.1" in msg for msg in msgs),
                  f"{npc_id}: jasny komunikat odzyskania")
        for npc_id in ("specialist_mining", "specialist_crafting"):
            session, msgs, offer, physical_id = make(npc_id, physical=False, old=False, cycle=2001)
            await session.handle_crafting_orders_v0600("oddaj")
            check(not db.crafting_order_offer_completed_v0700(
                session.account_id, 2001, npc_id, offer["item_id"], 1
            ), f"{npc_id}: nowych zamówień nie można oddać bez towaru")
            check(any("Masz tylko" in msg for msg in msgs),
                  f"{npc_id}: komunikat brakujących materiałów")
        session, msgs, offer, physical_id = make("specialist_crafting", cycle=3000)
        session.character.room_id = "square"
        await session.handle_crafting_orders_v0600("oddaj")
        check(not db.crafting_order_offer_completed_v0700(
            session.account_id, 3000, offer["npc_id"], offer["item_id"], 1
        ), "oddanie u niewłaściwego NPC nie kończy zamówienia")
        check(db.item_qty(session.account_id, physical_id) == 1,
              "oddanie u niewłaściwego NPC nie pobiera materiałów")

    with tempfile.TemporaryDirectory(prefix="sb-orders-hotfix-") as directory:
        db = Database(os.path.join(directory, "test.db"))
        asyncio.run(run(db))
        db.conn.close()

    return {"checks": checks, "errors": errors, "error_count": len(errors), "professions": 14}
