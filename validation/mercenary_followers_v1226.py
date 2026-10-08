# -*- coding: utf-8 -*-
"""Regression: permanent mercenaries follow the owner and speak to the owner in combat."""
import asyncio
import ast
import time
from pathlib import Path
from types import SimpleNamespace
from systems.mercenary_taverns import (MERCENARIES, COOLDOWN,
    pick_next_contract, mercenary_owner_power_v1213, mercenary_damage_cap_ratio_v12212, mercenary_owner_full_power_v12213)
from systems.mercenary_growth_v1220 import (mercenary_owner_level_v1228, mercenary_attack_multiplier,
    mercenary_unlocked, mercenary_tactic)


class _Db:
    def __init__(self):
        self.hires = {1: ["mag", "paladyn"], 2: ["wojownik"]}
        self.exp = 0

    def mercenary_contracts(self, account_id, now=None):
        return [{"role": role, "expires_at": 0.0}
                for role in self.hires.get(account_id, ())]

    def mercenary_progress_v1220(self, account_id, role):
        return {"xp": 0, "specialization": "", "actions": 0}

    def mercenary_gain_xp_v1220(self, account_id, role, xp):
        self.exp += 1
        return {"xp": xp, "specialization": "", "actions": 1}

    def nemesis_row_v029(self, account_id):
        return None


# Extract and run the actual game methods without importing the unfinished world
# catalog. This matches how older predeploy tests verify live combat methods.
_base = Path(__file__).resolve().parents[1]
_source = (_base / "player/session_mixins/mercenary_taverns.py").read_text(encoding="utf-8")
_tree = ast.parse(_source)
_class = next(node for node in _tree.body if isinstance(node, ast.ClassDef)
              and node.name == "SessionMercenaryTavernsMixin")
_names = ("nearby_mercenaries_v1226", "visible_mercenary_for_look_v1226",
          "mercenary_combat_turn_v1170")
_methods = [node for node in _class.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in _names]
assert len(_methods) == len(_names)
_npc_adjust = lambda template, damage, dtype, role: (damage, None)
_namespace = dict(time=time, COOLDOWN=COOLDOWN, MERCENARIES=MERCENARIES,
                  pick_next_contract=pick_next_contract,
                  mercenary_owner_power_v1213=mercenary_owner_power_v1213,
                  mercenary_damage_cap_ratio_v12212=mercenary_damage_cap_ratio_v12212,
                  mercenary_owner_full_power_v12213=mercenary_owner_full_power_v12213,
                  mercenary_owner_level_v1228=mercenary_owner_level_v1228,
                  mercenary_attack_multiplier=mercenary_attack_multiplier,
                  mercenary_unlocked=mercenary_unlocked, mercenary_tactic=mercenary_tactic,
                  superboss_healing_blocked_v11179=lambda session: False,
                  MOB_TEMPLATES={"test_enemy": {"name": "Strażnik", "level": 8}},
                  v0314_adjust_damage_vs_template=_npc_adjust)
exec(compile(ast.fix_missing_locations(ast.Module(body=_methods, type_ignores=[])),
             "player/session_mixins/mercenary_taverns.py", "exec"), _namespace)


class _GameSession:
    nearby_mercenaries_v1226 = _namespace["nearby_mercenaries_v1226"]
    visible_mercenary_for_look_v1226 = _namespace["visible_mercenary_for_look_v1226"]
    mercenary_combat_turn_v1170 = _namespace["mercenary_combat_turn_v1170"]
    closed = False
    current_hp = 100
    skill_guard = 0
    _mercenary_next_action_v1170 = 0.0
    _mercenary_last_role_v1170 = None

    def __init__(self, server, account_id, name, room):
        self.server, self.account_id = server, account_id
        self.character = SimpleNamespace(
            name=name, room_id=room, character_level=10)
        self.messages = []

    def normalize_description_query(self, text):
        return str(text).casefold().strip()

    def visible_player_for_look(self, text):
        return None

    def max_hp(self):
        return 100

    def physical_power(self):
        return 100

    def spell_power(self):
        return 60

    async def apply_boss_defense(self, mob, damage):
        return damage

    def mob_effective_max_hp_v11330(self, mob):
        return 1000

    async def send(self, msg, **kwargs):
        self.messages.append(str(msg))

    async def send_combat(self, msg, detail="essential"):
        self.messages.append(f"{detail}: {msg}")


def validate_mercenary_followers_v1226():
    checks = 0
    db = _Db()
    server = SimpleNamespace(
        sessions=set(), db=db,
        party_sessions=lambda account_id, same_room: [],
        party_combat_broadcast=None,
    )
    first = _GameSession(server, 1, "A", "room")
    second = _GameSession(server, 2, "B", "room")
    third = _GameSession(server, 3, "C", "elsewhere")
    server.sessions = {first, second, third}
    followers = first.nearby_mercenaries_v1226()
    assert len(followers) == 3
    checks += 1
    assert {(f[0].character.name, f[2]["name"]) for f in followers} == {
        ("A", "Vael"), ("A", "Seren"), ("B", "Gareth")}
    checks += 1
    assert first.visible_mercenary_for_look_v1226("Vael")[0] is first
    checks += 1
    assert second.visible_mercenary_for_look_v1226("Seren")[0] is first
    checks += 1
    assert third.nearby_mercenaries_v1226() == []
    checks += 1
    assert first.visible_mercenary_for_look_v1226("nieistnieje") is None
    checks += 1
    # Leaving and returning should not create extra NPCs or contracts.
    first.character.room_id = "elsewhere"
    assert [f[2]["name"] for f in third.nearby_mercenaries_v1226()] == [
        MERCENARIES[r]["name"] for r in db.hires[1]]
    checks += 1
    first.character.room_id = "room"
    assert len(first.nearby_mercenaries_v1226()) == 3
    checks += 1

    # Combat owner must hear the action; party also receives one broadcast.
    calls = []

    async def broadcast(owner, message, detail="normal"):
        calls.append((owner, message, detail))

    server.party_combat_broadcast = broadcast
    server.party_sessions = lambda account_id, same_room: [first, second]
    mob = SimpleNamespace(template_id="test_enemy", room_id="room", hp=1000, alive=True)
    asyncio.run(first.mercenary_combat_turn_v1170(mob))
    assert any("essential: " in m and ("Vael" in m or "Seren" in m)
               for m in first.messages)
    checks += 1
    assert len(calls) == 2 and all(call[2] == "essential" for call in calls)
    assert any("Vael" in call[1] for call in calls) and any("Seren" in call[1] for call in calls)
    checks += 1
    assert db.exp == 0  # v1.22.8: combat does not award independent EXP.
    checks += 1
    assert mob.hp < 1000 or first.skill_guard > 0
    checks += 1
    assert len(db.mercenary_contracts(1)) == 2
    checks += 1
    # Ensure the look command actually uses the tested virtual follower list.
    source = (_base / "player/session_mixins/perception_maps.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    look_cls = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                    and node.name == "SessionPerceptionMapsMixin")
    look = next(node for node in look_cls.body if isinstance(node, ast.AsyncFunctionDef)
                and node.name == "look")
    look_code = ast.get_source_segment(source, look)
    assert "self.nearby_mercenaries_v1226()" in look_code
    checks += 1
    assert "self.visible_mercenary_for_look_v1226(query)" in look_code
    checks += 1
    return checks
