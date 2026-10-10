# -*- coding: utf-8 -*-
"""Regression: 10 AoE mobs should NOT scan every monster in the world per AI turn."""
from types import SimpleNamespace
from systems.monster_ai import (
    monster_ai_due_v1901,
    monster_ai_room_candidates_v1901,
    monster_ai_plan_v1160,
)


def run_regression():
    checks = 0
    def check(condition, message):
        nonlocal checks
        assert condition, 'v1.90.1 AoE AI: ' + message
        checks += 1

    def mob(key, room='arena', alive=True, engaged='druzyna', hp=100):
        return SimpleNamespace(
            key=key, template_id=key, room_id=room, alive=alive,
            engaged_by=engaged, hp=hp, combat_turn=3,
        )

    class TrackedMobs(dict):
        values_calls = 0
        def values(self):
            self.values_calls += 1
            return super().values()

    class World:
        def __init__(self):
            self.locals = [mob(f'enemy_{j}') for j in range(10)]
            self.dead = mob('corpse', alive=False, engaged=None, hp=0)
            far = {f'far_{j}': mob(f'far_{j}', room='other') for j in range(20000)}
            self.mobs = TrackedMobs(far)
            self.mobs.update({m.key: m for m in self.locals + [self.dead]})
            self.room_lookups = 0

        def room_mobs(self, room_id):
            self.room_lookups += 1
            return [m for m in self.locals if m.alive and m.room_id == room_id]

    world = World()
    template = {'name': 'Magiczny przeciwnik', 'damage_type': 'magic', 'max_hp': 100}
    for enemy in world.locals:
        check(monster_ai_due_v1901(enemy, template, 100), 'ready every third attack')
        live, dead = monster_ai_room_candidates_v1901(world, enemy, template)
        check(len(live) == 10 and not dead, 'same-room alive aggro only')
        check(monster_ai_plan_v1160(enemy, template, live, dead, now=100) is not None,
              'ordinary support AI still selects an action')
    check(world.mobs.values_calls == 0, 'ten regular monsters must not scan global mobs')
    check(world.room_lookups == 10, 'ten regular monsters use room index')

    world.locals[0].monster_ai_next_action_v1160 = 200
    check(not monster_ai_due_v1901(world.locals[0], template, 150), 'cooldown skips candidate lookup')
    check(monster_ai_due_v1901(world.locals[0], template, 200), 'cooldown expires')
    world.locals[0].combat_turn = 4
    check(not monster_ai_due_v1901(world.locals[0], template, 200), 'not every enemy turn gets support action')
    world.locals[0].combat_turn = 3
    check(not monster_ai_due_v1901(world.locals[0], {'uoss_superboss': True, **template}, 200),
          'scripted superboss still excludes ordinary AI')

    necro = {'name': 'Nekromanta', 'damage_type': 'magic', 'max_hp': 100}
    live, dead = monster_ai_room_candidates_v1901(world, world.locals[1], necro)
    check(len(live) == 10 and dead == [world.dead], 'necromancer can target unengaged dead in room')
    check(world.mobs.values_calls == 1, 'necromancer compatibility uses world scan only when required')
    check(monster_ai_plan_v1160(world.locals[1], necro, live, dead, now=100)['kind'] == 'resurrect',
          'necro resurrection works')
    other = mob('stranger', engaged='obcy')
    world.locals.append(other)
    live, dead = monster_ai_room_candidates_v1901(world, world.locals[1], template)
    check(other not in live, 'no support for another player combat')
    return checks


if __name__ == '__main__':
    print('AOE AI v1.90.1:', run_regression(), 'checks PASS')
