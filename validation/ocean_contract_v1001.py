"""Persistence and delivery regression for Ocean 2.0 trade contracts."""
from __future__ import annotations

import asyncio
import sqlite3
from types import SimpleNamespace

from player.session_mixins.ocean import SessionOceanV1000Mixin
from core.classes_skills import ROOMS
from world.ocean_expansion import PORTS, ROUTES
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
        assert {"route_progress", "route_current_room", "arrival_verified"} <= columns
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
        asyncio.run(second.ocean_trade_v1000())
        assert any("350 złota" in message for message in second.messages)
        for old_room, new_room in zip(path[1:], path[2:]):
            second.ocean_contract_step_v1001(old_room, new_room)
        asyncio.run(second.ocean_trade_v1000("oddaj"))
        assert second.character.silver == 35_100
        assert any("Otrzymujesz 350 złota" in message for message in second.messages)
        assert conn.execute("SELECT COUNT(*) FROM ocean_trade_contract_v1000").fetchone()[0] == 0

        offers = first.ocean_trade_offers_v1000()
        assert len(offers) == 28
        assert len({offer[0] for offer in offers}) == 28
        port_rooms = {room_id for room_id, _label in PORTS.values()}
        assert {offer[1] for offer in offers} == port_rooms
        for origin in port_rooms:
            assert sum(1 for offer in offers if offer[1] == origin) == 4
        for offer in offers:
            assert 1 <= int(offer[5]) <= 5
            assert len(first.ocean_contract_path_v1001(offer[1], offer[2])) > 2
        # The older authored voyage via Fog Dock and Ardelia is also a real sea route.
        conn.execute(
            "INSERT INTO ocean_trade_contract_v1000(account_id,contract_key,origin_room,destination_room,cargo_label,reward_silver,required_cargo,accepted_at) "
            "VALUES(1,'korona','ocean_platform','silver_crown_harbor','towary',220000,4,1)"
        )
        conn.commit()
        legacy_route = (
            "ocean_platform", *(f"fog_crossing_{i:02d}" for i in range(1, 5)),
            "fog_dock", *(f"ardelia_crossing_{i:02d}" for i in range(1, 7)),
            "silver_crown_harbor",
        )
        for old_room, new_room in zip(legacy_route, legacy_route[1:]):
            second.ocean_contract_step_v1001(old_room, new_room)
        assert conn.execute("SELECT arrival_verified FROM ocean_trade_contract_v1000").fetchone()[0] == 1
        second.character.room_id = "silver_crown_harbor"
        asyncio.run(second.ocean_trade_v1000("oddaj"))
        assert second.character.silver == 255_100
        # A land approach to the destination never verifies a contract.
        conn.execute(
            "INSERT INTO ocean_trade_contract_v1000(account_id,contract_key,origin_room,destination_room,cargo_label,reward_silver,required_cargo,accepted_at) "
            "VALUES(1,'korona','ocean_platform','silver_crown_harbor','towary',220000,4,1)"
        )
        conn.commit()
        second.ocean_contract_step_v1001("silver_crown_square", "silver_crown_harbor")
        assert conn.execute("SELECT arrival_verified FROM ocean_trade_contract_v1000").fetchone()[0] == 0
        # The exact player report: direct Crown route from Ocean Platform,
        # including a visit to submerged ruins and return to the same sector.
        crown_lane = ("ocean_platform", *ROUTES["crown"]["rooms"], "silver_crown_harbor")
        for index, (old_room, new_room) in enumerate(zip(crown_lane, crown_lane[1:])):
            second.ocean_contract_step_v1001(old_room, new_room)
            if index == 10:
                anchor = new_room
                underwater = next(
                    room for room in ROOMS[anchor]["exits"].values()
                    if ROOMS[room].get("underwater")
                )
                second.ocean_contract_step_v1001(anchor, underwater)
                second.ocean_contract_step_v1001(underwater, anchor)
        row = conn.execute("SELECT route_progress,arrival_verified FROM ocean_trade_contract_v1000").fetchone()
        assert tuple(row) == (len(crown_lane) - 1, 1)
        endpoints = {route[side] for route in ROUTES.values() for side in ("origin", "destination")}
        assert endpoints == {room_id for room_id, _label in PORTS.values()}
        assert len(ROUTES) == 6
        return {
            "error_count": 0,
            "routes": len(ROUTES),
            "trade_offers": len(offers),
            "offers_per_port": 4,
            "legacy_schema_migrated": True,
        }
    finally:
        conn.close()
