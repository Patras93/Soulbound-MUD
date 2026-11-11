# -*- coding: utf-8 -*-
"""v1.33.2 actual world-variant and realtime-hook regression checks.

Runs only on a disposable World object, without player accounts or persistent DB.
"""
import asyncio
import time


def audit_council_combat_v1332():
    from world.world_state import World
    from data.mobs import MOB_TEMPLATES
    from systems.soul_ancients_v1330 import ancient_attack
    from systems.soul_evolutions_v1332 import council_allies
    from player.session_mixins.combat_realtime import SessionCombatRealtimeMixin
    from player.session_mixins.skill_learning import SessionSkillLearningMixin

    room = 'v1332_ancients_council_arena'
    world = World()
    original = list(world.room_mobs(room))
    assert len(original) == 2, 'Two live Ancient entities must actually spawn'
    boss, ally = original
    assert {m.template_id.split('__', 1)[0] for m in original} == {
        'v1310_anc_deep_boss', 'v1310_anc_sky_boss'
    }
    assert council_allies(original, room, boss) == [ally]
    assert not council_allies(original, 'another_room', boss)
    assert ancient_attack(boss.template_id, 5, 3) is not None, 'Runtime variant lost its Ancient abilities'
    messages = []

    class ProbeServer:
        async def party_combat_broadcast(self, *args, **kwargs):
            messages.append(args[1])

    class ProbeSession(SessionCombatRealtimeMixin, SessionSkillLearningMixin):
        async def send(self, value):
            messages.append(value)

        async def boss_phase_multiplier(self, mob, template):
            return 1.0

    session = ProbeSession()
    session.server = ProbeServer()
    session.server.world = world
    boss.engaged_by = 'Probe'
    boss.engaged_at = time.monotonic()

    async def check():
        assert await session.boss_summon_wave_v1301(boss, opening=True)
        assert ally.engaged_by == boss.engaged_by
        assert any('dołącza do bitwy' in message for message in messages)
        assert len(world.room_mobs(room)) >= 3, 'Opening guardian did not spawn'
        full = ally.hp
        ally.hp //= 2
        boss.combat_turn = 3  # profile increments to four
        await session.boss_attack_profile(boss, MOB_TEMPLATES[boss.template_id])
        assert ally.hp > full // 2, 'Ally heal not applied to real mob'
        boss.combat_turn = 4  # profile increments to five
        profile = await session.boss_attack_profile(boss, MOB_TEMPLATES[boss.template_id])
        assert profile['damage_multiplier'] > 1.1, 'Coordinated attack not applied'
        assert any('uzdrawia' in message for message in messages)
        assert any('wspólny atak' in message for message in messages)

    asyncio.run(check())
    return {'checks': 13, 'live_bosses': 2}
