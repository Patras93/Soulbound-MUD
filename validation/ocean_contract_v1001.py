"""Persistence and delivery regression for Ocean 2.0 trade contracts."""
from __future__ import annotations

import asyncio
import sqlite3
from types import SimpleNamespace

from player.session_mixins.ocean import SessionOceanV1000Mixin
from storage.schema_world_quests import create_world_quests_schema


def audit_ocean_contract_v1001():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("CREATE TABLE crafting_orders_v0600(account_id INTEGER, completed_count INTEGER)")
        conn.execute(
            "CREATE TABLE ocean_trade_contract_v1000("
            "account_id INTEGER PRIMARY KEY, contract_key TEXT, origin_room TEXT,"
            "destination_room TEXT, cargo_label TEXT, reward_silver INTEGER,"
            "required_cargo INTEGER, accepted_at INTEGER)"
        )
        conn.execute(
            "INSERT INTO ocean_trade_contract_v1000 VALUES"
            "(1,'rafy','ocean_platform','fog_square','ładunek',35000,1,1)"
        )
        create_world_quests_schema(SimpleNamespace(conn=conn))
        columns = {row[1] for row in conn.execute("PRAGMA table_info(ocean_trade_contract_v1000)")}
        assert {"route_progress", "arrival_verified"} <= columns
        assert conn.execute("SELECT contract_key FROM ocean_trade_contract_v1000").fetchone()[0] == "rafy"

        class Session(SessionOceanV1000Mixin):
            async def send(self, message):
                self.messages.append(message)

            def character_wallet_silver_value(self):
                return self.character.silver

            def ocean_ship_owned_v1000(self):
                return True

            def ocean_ship_level_v1000(self, key):
                return 5

        def session():
            instance = Session()
            instance.account_id = 1
            instance.messages = []
            instance.character = SimpleNamespace(room_id="fog_square", silver=100, gold=0, mithril=0)
            instance.server = SimpleNamespace(db=SimpleNamespace(conn=conn, save_character=lambda character: conn.commit()))
            return instance

        first = session()
        asyncio.run(first.ocean_trade_v1000("oddaj"))
        assert first.character.silver == 100
        assert conn.execute("SELECT COUNT(*) FROM ocean_trade_contract_v1000").fetchone()[0] == 1
        path = first.ocean_contract_path_v1001("ocean_platform", "fog_square")
        assert len(path) == 12
        first.ocean_contract_step_v1001(path[0], path[1])
        second = session()  # New session reads the persisted route progress.
        for old_room, new_room in zip(path[1:], path[2:]):
            second.ocean_contract_step_v1001(old_room, new_room)
        asyncio.run(second.ocean_trade_v1000("oddaj"))
        assert second.character.silver == 35_100
        assert conn.execute("SELECT COUNT(*) FROM ocean_trade_contract_v1000").fetchone()[0] == 0

        for offer in first.ocean_trade_offers_v1000():
            assert len(first.ocean_contract_path_v1001(offer[1], offer[2])) > 2
        return {"error_count": 0, "routes": 5, "legacy_schema_migrated": True}
    finally:
        conn.close()
