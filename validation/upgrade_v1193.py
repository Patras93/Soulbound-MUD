# -*- coding: utf-8 -*-
"""Fast non-destructive integration checks for releases v1.19.1..v1.19.3."""
from __future__ import annotations

import asyncio
import sqlite3
from types import SimpleNamespace


def audit_upgrade_v1193():
    # Normal runtime bootstrap loads the world's catalogs first.
    import server
    from player.session import Session
    from player.session_mixins.upgrade_v1193 import next_career_milestone_v1192, SessionUpgradeV1193Mixin
    from player.session_mixins.command_registry import resolve_session_command, COMMAND_REGISTRY
    from core.classes_skills import ROOMS

    issues = []
    count = 0
    def check(condition, label):
        nonlocal count
        count += 1
        if not condition:
            issues.append(label)

    for alias, canonical in (("nawigacja", "navigation2"), ("kariera", "career2"),
                             ("osiagniecia", "achievements"), ("druzyna", "party")):
        check(resolve_session_command(alias) == canonical, f"command alias {alias}")
    for command, method in (("navigation2", "navigation_v1191"), ("career2", "career_v1192"),
                            ("achievements", "achievements_plus_v1192")):
        check(COMMAND_REGISTRY[command][0] == method, f"command handler {command}")
        check(callable(getattr(Session, method, None)), f"session method {method}")
    for value, expected in ((0,(10,10)), (10,(100,90)), (99,(100,1)), (100000,None)):
        check(next_career_milestone_v1192(value,(10,100,1000,10000,100000)) == expected,
              f"threshold {value}")

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE combat_recaps_v03052(account_id INTEGER,damage_dealt INTEGER,damage_taken INTEGER,healing INTEGER)")
    conn.executemany("INSERT INTO combat_recaps_v03052 VALUES(?,?,?,?)", [(1,125,20,15),(1,250,10,0),(2,500000,1,5)])
    conn.commit()
    class Db:
        def lifetime_stats(self, account):
            return ({'kills_total':7, 'boss_kills':2, 'rooms_discovered':3, 'profession_actions':40, 'quests_completed':5}
                    if account == 1 else {'kills_total':9999})
        def discovered_room_ids(self, account):
            return {'square','market','temple'} if account == 1 else set()
        def achievement_rows(self, account):
            return [{'name':'Odkrywca'}] if account == 1 else [{'name':'Inny'}]
    # Avoid relying on a real server/database, and do not mutate player state.
    class Dummy(SessionUpgradeV1193Mixin):
        def __init__(self, server, account, name, room):
            self.server, self.account_id = server, account
            self.character = SimpleNamespace(name=name, room_id=room, class_name="Wojownik", character_level=25, deaths=3)
            self.messages = []
            self.current_hp, self.current_mana = 800, 40
            self.route_target_room = None
            self.route_target_label = ""
            self.guide_task = None
            self.closed = False
        async def send(self, msg, **kwargs):
            self.messages.append(str(msg))
        def normalize_room_query(self, value):
            return Session.normalize_room_query(self, value)
        def route_direction_name(self, direction):
            return Session.route_direction_name(self, direction)
        def shortest_path(self, origin, goal):
            return Session.shortest_path(self, origin, goal)
        def party_key(self):
            return self.server.party_key_for_account(self.account_id)
        def normalize_description_query(self, text):
            return Session.normalize_description_query(self, text)
        def clean_party_player_argument(self, text, relation=None):
            return Session.clean_party_player_argument(self, text, relation=relation)
        def is_downed_v0371(self):
            return False
        def max_hp(self):
            return 1000
        def max_mana(self):
            return 200
        def find_guide_npc(self, value):
            return None
        def find_room_matches(self, value):
            return ["market"] if self.normalize_room_query(value) in ("rynek", "market") else []
        def guide_exploration_safe_target(self, room):
            return room
        async def show_route_next_step(self):
            await self.send("Następny krok: " + (str(self.route_target_room) if self.route_target_room else "brak celu"))
        async def show_route(self, goal):
            await self.send("TRASA: " + str(goal))
        async def show_achievements(self):
            await self.send("STARE OSIĄGNIĘCIA")
    class FakeServer:
        def __init__(self):
            self.db = Db()
            self.db.conn = conn
            self.party_routes_v1193 = {}
            self.party_ready_checks = {1: {1,2}}
            self.party_goals = {1: "Wyprawa"}
            self.party_protectors = {}
            self.party_invites = {}
            self.parties = {1: {1,2}}
            self.world = SimpleNamespace(ensure_runtime_room=lambda room:None)
            self.sent = []
            self.sessions = []
        def party_key_for_account(self, account):
            for key, members in self.parties.items():
                if account in members:return key
            return None
        def party_sessions(self, account):
            key = self.party_key_for_account(account)
            return [s for s in self.sessions if s.account_id in self.parties.get(key, ())]
        def session_by_account(self, account):
            return next((s for s in self.sessions if s.account_id == account),None)
        def find_character_session(self, name):
            return next((s for s in self.sessions if s.character.name.casefold() == name.casefold()),None)
        async def party_broadcast(self, key, message, **kwargs):
            self.sent.append((key,message))
    server_stub=FakeServer()
    a=Dummy(server_stub,1,"Ala","square")
    b=Dummy(server_stub,2,"Beata","market")
    server_stub.sessions=[a,b]
    before=conn.total_changes
    async def run():
        await Session.dispatch_registered_command(a, "navigation2", "status")
        check("NAWIGACJA 2.0" in " ".join(a.messages), "navigation dispatch")
        a.messages.clear()
        await a.navigation_v1191("")
        check("NAWIGACJA 2.0" in " ".join(a.messages), "navigation status")
        a.messages.clear()
        await a.navigation_v1191("okolica")
        check(any("wschód:" in x for x in a.messages), "accessible nearby directions")
        a.messages.clear()
        await a.career_v1192("")
        summary=" ".join(a.messages)
        check("zwycięstwa 7" in summary and "bossowie 2" in summary, "career uses real saved metrics")
        check("9999" not in summary, "other account is isolated")
        a.messages.clear()
        await a.career_v1192("postep")
        check("Zwycięstwa: 7 z 10; brakuje 3" in " ".join(a.messages), "milestone remaining")
        a.messages.clear()
        await a.career_v1192("rekordy")
        check("maks. obrażenia zadane w walce 250" in " ".join(a.messages), "combat max per account")
        check("500000" not in " ".join(a.messages), "private recap isolation")
        a.messages.clear()
        await a.achievements_plus_v1192("")
        check("STARE OSIĄGNIĘCIA" in " ".join(a.messages), "legacy achievements preserved")
        a.messages.clear()
        await a.achievements_plus_v1192("postep")
        check("NASTĘPNE PROGI" in " ".join(a.messages), "achievements progress dispatch")
        a.messages.clear()
        await Session.handle_party(a, "raport")
        report=" ".join(a.messages)
        check("PARTY 4.0" in report and "Ala" in report and "Beata" in report, "party health report")
        a.messages.clear()
        await a.party_gather_v1193()
        check("ZBIÓRKA" in " ".join(a.messages), "gather positions")
        a.messages.clear()
        await b.party_route_v1193("rynek")
        check(not server_stub.party_routes_v1193, "only leader sets route")
        await a.party_route_v1193("no such target")
        check(not server_stub.party_routes_v1193, "unknown target not saved")
        await a.party_route_v1193("rynek")
        check(server_stub.party_routes_v1193[1] == ("market",ROOMS["market"]["name"]), "leader route saved")
        check(1 not in server_stub.party_ready_checks, "new route resets readiness")
        b.messages.clear()
        await b.party_route_v1193("krok")
        check("jesteś na miejscu" in " ".join(b.messages), "member route from own location")
        b.messages.clear()
        await b.party_route_v1193("off")
        check(bool(server_stub.party_routes_v1193), "member cannot clear route")
        await Session.transfer_party_leader(a, "Beata")
        check(server_stub.party_routes_v1193.get(2, (None,))[0] == "market", "route transfers with leadership")
        check(1 not in server_stub.party_routes_v1193, "old leader route removed")
        await a.party_route_v1193("off")
        check(2 in server_stub.party_routes_v1193, "old leader cannot clear")
        await b.party_route_v1193("off")
        check(not server_stub.party_routes_v1193, "new leader can clear route")
        await b.party_route_v1193("rynek")
        await Session.disband_party(b)
        check(not server_stub.party_routes_v1193 and not server_stub.parties, "disband clears party route")
        check(all("teleport" not in item[1].lower() for item in server_stub.sent), "route does not teleport")
    asyncio.run(run())
    check(before == conn.total_changes, "all new reports and group routes do not write database")
    conn.close()
    return {"checks":count,"error_count":len(issues),"errors":issues}


if __name__ == "__main__":
    result=audit_upgrade_v1193()
    print(f"UPGRADES v1.19.1-1.19.3: {result['checks']} checks, {result['error_count']} errors")
    for issue in result['errors']:
        print("FAIL:",issue)
    if result['errors']:
        raise SystemExit(1)

