# -*- coding: utf-8 -*-
"""v1.40.0: isolated kill idempotence and unlimited-summon lifecycle checks.

No live clients, user accounts, production files, or network sockets.
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from types import SimpleNamespace


def run_combat_stability_v1400():
    from player.session_mixins.combat_rewards import deferred_kill_commits_v11125
    from world.world_state import World
    from data.mobs import MOB_TEMPLATES

    errors = []
    checks = 0

    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(reason)

    class FakeConn:
        @contextmanager
        def deferred_commits(self):
            yield

    session = SimpleNamespace(server=SimpleNamespace(db=SimpleNamespace(conn=FakeConn())))
    calls = []

    @deferred_kill_commits_v11125
    async def settle(_, mob):
        calls.append(mob.key)
        # Intentionally interleave four kill handlers on one encounter.
        await asyncio.sleep(0)
        mob.alive = False

    async def racing():
        mob = SimpleNamespace(key='simulated-boss', alive=True)
        await asyncio.gather(*(settle(session, mob) for _ in range(4)))
        check(calls == ['simulated-boss'], 'the same kill was rewarded more than once')
        await settle(session, mob)
        check(len(calls) == 1, 'stale defeated mob rewarded again')
        mob.alive = True  # Simulates a legitimate boss respawn.
        await settle(session, mob)
        check(len(calls) == 2, 'fresh boss respawn cannot grant another reward')

        @deferred_kill_commits_v11125
        async def failing(_, mob):
            await asyncio.sleep(0)
            raise RuntimeError('simulated transient reward error')

        retry = SimpleNamespace(key='retry-boss', alive=True)
        error_seen = False
        try:
            await failing(session, retry)
        except RuntimeError:
            error_seen = True
        check(error_seen, 'the failing reward test did not raise')
        check(not getattr(retry, 'v1400_kill_in_progress', False),
              'failed reward left boss permanently locked')
        await settle(session, retry)
        check(calls[-1] == 'retry-boss', 'failed reward cannot retry')

    asyncio.run(racing())

    world = World()  # Disposable world; no persistent users or DB.
    boss = next((m for m in world.mobs.values()
                 if any(MOB_TEMPLATES[m.template_id].get(flag) for flag in
                        ('crypt_boss', 'mythic_crypt_boss', 'boss'))
                 and not MOB_TEMPLATES[m.template_id].get('uoss_unique_superboss_key')),
                None)
    check(boss is not None, 'no ordinary boss available for summon stress')
    if boss:
        boss.engaged_by = 'synthetic-session'
        boss.hp = max(1, int(boss.hp))
        children = [world.spawn_boss_companion_v1281(boss) for _ in range(24)]
        check(all(children), 'unlimited waves stopped early')
        check(len({m.key for m in children if m}) == 24, 'summon key collision')
        world.refresh(force=True)
        present = {m.key for m in world.room_mobs(boss.room_id)}
        check(all(m.key in present for m in children if m),
              'living summoned guards missing from local room')
        boss.alive = False
        boss.engaged_by = None
        world.refresh(force=True)
        check(not any(m.alive for m in children if m),
              'summons continued fighting after boss death')
        check(all(m.key not in world.mobs for m in children if m),
              'expired summons stayed in global monster registry')

    return {'checks': checks, 'errors': len(errors), 'failures': errors,
            'simulated_concurrent_callbacks': 4, 'summoned_guards': 24,
            'scope': 'disposable World and synchronous-memory callback; NOT 4 TCP clients'}
