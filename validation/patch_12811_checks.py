# -*- coding: utf-8 -*-
"""Independent, opt-in regression checks for v1.28.11 additions."""
from __future__ import annotations

import asyncio
import inspect
from types import SimpleNamespace


def run_checks():
    checks = 0
    from storage.database import Database  # canonical bootstrap import order
    from player.session_mixins.dungeon_progression import SessionDungeonProgressionMixin
    from systems.boss_companions_v1281 import boss_guardian_role_v12811, boss_companion_due_v1281
    from data.items import ITEMS
    from data.crafting_recipes import CRAFT_RECIPES
    # Drive's app initialization extends recipes elsewhere; import the runtime
    # catalog in a normal bootstrapped environment in integration tests.
    for iid in ("v12811_leviathan_pearl", "v12811_worldheart_core",
                "v12811_eternal_timber", "v12811_phoenix_bloom",
                "v12811_ancient_blueprint", "v12811_explorer_relic"):
        assert iid in ITEMS
        checks += 1

    class Player(SessionDungeonProgressionMixin):
        def party_key(self):
            return self.key

    me = Player()
    me.account_id = 11
    me.key = None
    me.character = SimpleNamespace(room_id="crypt_floor_20")
    another = SimpleNamespace(account_id=12, character=SimpleNamespace(room_id="crypt_floor_20"), closed=False)
    me.server = SimpleNamespace(party_sessions=lambda *args, **kwargs: [me])
    assert me.portal_requires_local_leader_v12811() is False
    checks += 1
    me.key = 12
    assert me.portal_requires_local_leader_v12811() is False
    checks += 1
    me.server.party_sessions = lambda *args, **kwargs: [me, another]
    assert me.portal_requires_local_leader_v12811() is True
    checks += 1
    another.closed = True
    assert me.portal_requires_local_leader_v12811() is False
    checks += 1
    me.key = me.account_id
    another.closed = False
    assert me.portal_requires_local_leader_v12811() is False
    checks += 1

    mob = SimpleNamespace(alive=True, engaged_by="player", combat_turn=4,
                          v1230_boss_phase=0, boss_last_summon_turn_v1281=-1)
    for index in range(1, 26):
        row = boss_guardian_role_v12811({"name": "Władca Krypty"}, mob, index)
        assert row[0] in {"zbrojny", "arkaniczny", "obronca", "furia", "uzdrowiciel"}
        checks += 1
    assert boss_companion_due_v1281(mob, {"crypt_boss": True})
    checks += 1
    mob.boss_last_summon_turn_v1281 = 4
    assert not boss_companion_due_v1281(mob, {"crypt_boss": True})
    checks += 1
    mob.combat_turn = 11
    assert boss_companion_due_v1281(mob, {"crypt_boss": True})
    checks += 1
    from player.session_mixins.gathering_actions import SessionGatheringActionsMixin
    assert 'direction' in inspect.signature(SessionGatheringActionsMixin.mine).parameters
    checks += 1
    import systems.public_records as records
    assert 'direction' in inspect.signature(records._v0370_set_auto_mining).parameters
    assert 'direction' in inspect.signature(records._v0370_mine).parameters
    checks += 2

    async def exercise_wrappers():
        original_auto = records._V0370_SET_AUTO_MINING_BEFORE
        original_mine = records._V0370_MINE_BEFORE
        calls = []
        async def mock_auto(self, enabled, direction=None):
            calls.append(("auto", enabled, direction))
            return True
        async def mock_mine(self, from_auto=False, direction=None):
            calls.append(("mine", from_auto, direction))
            return True
        try:
            records._V0370_SET_AUTO_MINING_BEFORE = mock_auto
            records._V0370_MINE_BEFORE = mock_mine
            self = SimpleNamespace(account_id=77,
                character=SimpleNamespace(name="Test"),
                server=SimpleNamespace(db=SimpleNamespace(lifetime_stat=lambda *a: 0)))
            assert await records._v0370_set_auto_mining(self, True, direction="east")
            assert await records._v0370_mine(self, from_auto=False, direction="west")
            assert calls == [("auto", True, "east"), ("mine", False, "west")], calls
        finally:
            records._V0370_SET_AUTO_MINING_BEFORE = original_auto
            records._V0370_MINE_BEFORE = original_mine
    asyncio.run(exercise_wrappers())
    checks += 3

    from systems.crafting_expansion import CRAFT_RECIPES as runtime_recipes
    recipe = runtime_recipes["v12811_explorer_relic"]
    assert recipe["min_profession_level"] == 160
    assert set(recipe["ingredients"]).issubset(ITEMS)
    assert recipe["output"] in ITEMS
    checks += 3
    print(f'V1.28.11 REGRESSION: {checks} checks, 0 errors')


if __name__ == '__main__':
    run_checks()
