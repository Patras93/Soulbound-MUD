# -*- coding: utf-8 -*-
"""Regression tests for v1.28.1 summons, real XP and cleanup."""
from __future__ import annotations
import asyncio
from types import SimpleNamespace


def test_v1281():
    from data.mobs import MOB_TEMPLATES
    from world.world_state import MobState, World
    from world.uoss_superboss_runtime import superboss_source_ability_v11162, superboss_source_summons_v11162
    from systems.boss_companions_v1281 import boss_companion_due_v1281, boss_jammer_immune_v1281
    from player.session_mixins.combat_rewards import SessionCombatRewardsMixin
    checks=0

    def check(ok, msg):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(msg)

    # Boss immunities cover every marker family, all Jammer casting modes.
    from systems.elite_variants import _V11338_BOSS_FLAGS
    for marker in _V11338_BOSS_FLAGS:
        check(boss_jammer_immune_v1281({marker:True}), f"Jammer boss flag {marker}")
    for rank in ("boss", "world_boss", "mini", "miniboss", "mini_boss"):
        check(boss_jammer_immune_v1281({"rank":rank}), f"Jammer boss rank {rank}")
    for marker in ("uoss_unique_superboss_key","uoss_superboss_key","v0140_mini_boss"):
        check(boss_jammer_immune_v1281({marker:"black_rabite"}),f"legacy boss {marker}")
    for kind in ("normal", "elite", "rare", "legendary"):
        check(not boss_jammer_immune_v1281({"rank":kind, "name":"Wilk"}),f"regular {kind} stunnable")
    check(not boss_jammer_immune_v1281({"uoss_superboss_add":True,"name":"Greater Demon"}),"helper can be stopped")
    runtime_source = (__import__('pathlib').Path(__file__).parents[1] / "player/session_mixins/combat_skills.py").read_text(encoding="utf-8")
    check("if boss_jammer_immune_v1281(_jam_template):" in runtime_source, "single and AoE Jammer guarded")
    world=World()
    for boss_key, turns, expected in (
        ("black_rabite", (2,5,8,11,14,17,20), "uoss_add_greater_demon_v11156"),
        ("serpentarius", (4,11,18), "uoss_add_zodiac_sentinel_v11156"),
        ("yiazmat", (4,11,18), "uoss_add_dragon_guardian_v11156"),
    ):
        template={"uoss_unique_superboss_key":boss_key}
        owner=MobState(key="boss:"+boss_key,room_id="bossarena:"+boss_key,
                       template_id="uoss_superboss_"+boss_key+"_v11136",
                       hp=10000000,engaged_by="Tester")
        world.mobs[owner.key]=owner
        for turn in turns:
            owner.combat_turn=turn
            ability=superboss_source_ability_v11162(template,owner)
            ids=superboss_source_summons_v11162(None,template,owner,ability)
            check(ids==(expected,),(boss_key,turn,ability,ids))
            check(not superboss_source_summons_v11162(None,template,owner,ability),"one add per action")
            add=world.spawn_superboss_summon_v1144(owner,ids[0])
            check(add is not None and add.alive and add.engaged_by=="Tester", "spawned")
            check(add.key!=owner.key, "separate mob identity")
            check(int(MOB_TEMPLATES[ids[0]]["source_xp"])>0, "source XP")
        live=sum(1 for m in world.mobs.values() if getattr(m,'uoss_summon_parent_v1144',None)==owner.key and m.alive)
        check(live==len(turns),"unlimited repeated Greater Demons / own sentinels")
        check(world.clear_superboss_companions_v1144(owner)==len(turns),"remove on death")

    boss_tid=next((tid for tid,t in MOB_TEMPLATES.items()
                   if t.get('boss') and not t.get('uoss_unique_superboss_key') and t.get('max_hp')),None)
    check(bool(boss_tid),"generic boss exists")
    boss=MobState(key='testboss', room_id='testarena',template_id=boss_tid,
                  hp=10000, engaged_by='Tester',combat_turn=4)
    world.mobs[boss.key]=boss
    check(boss_companion_due_v1281(boss,MOB_TEMPLATES[boss_tid]),"generic boss due")
    extra=world.spawn_boss_companion_v1281(boss)
    check(extra is not None and extra.alive, "generic summon created")
    check(extra.monster_ai_summoned_v1160,"XP branch flag")
    extra_2=world.spawn_boss_companion_v1281(boss)
    check(extra_2 is not None and extra_2.alive and extra_2.key != extra.key,
          "generic summon no living guardian limit")
    boss.combat_turn=11
    check(boss_companion_due_v1281(boss,MOB_TEMPLATES[boss_tid]),
          "boss can summon on next scheduled wave while previous guardians live")
    extra_3=world.spawn_boss_companion_v1281(boss)
    check(extra_3 is not None and extra_3.alive and extra_3.key != extra_2.key,
          "third consecutive live guardian spawned")
    check(world.clear_monster_ai_adds_v1160(boss)==3,"all generic guardians cleared on boss death")
    check(not extra.alive and not extra_2.alive and not extra_3.alive,"all helpers gone")
    second=world.spawn_boss_companion_v1281(boss)
    check(second is not None and second.key!=extra.key,"generic replacement")
    check(not boss_companion_due_v1281(boss,MOB_TEMPLATES[extra.template_id]),"generic helper can't summon")

    class Character:
        room_id='testarena'
        STAT_PROGRESS_FIELDS=('strength','intelligence')
        def __init__(self): self.stats=[]
        def add_stat_progress(self,xp,targets=(),single_level_cap=False):
            self.stats.append((xp,targets)); return []

    class Participant:
        def __init__(self,name):
            self.character=Character()
            self.name=name; self.character.name=name; self.account_id=1 if name=='a' else 2
            self.combat_mob_key=second.key
            self.xp=[]; self.messages=[]
        async def send(self,msg): self.messages.append(msg)
        def apply_double_xp(self,xp): return xp
        async def grant_combat_soul_xp_v11350(self,xp,**kwargs): self.xp.append(('soul',xp))
        async def grant_class_xp(self,xp,**kwargs): self.xp.append(('class',xp))
        def add_character_xp_with_event(self,xp,**kwargs):
            self.xp.append(('character',xp)); return []

    a,b=Participant('a'),Participant('b')
    fake=SimpleNamespace(character=a.character, account_id=1, auto_queue_casting=True)
    fake.server=SimpleNamespace(sessions=[a,b],party_sessions=lambda *args,**kwargs:[a,b])
    reward=SessionCombatRewardsMixin.mob_defeated.__wrapped__
    asyncio.run(reward(fake,second))
    check(not second.alive,'defeated summoned guardian dies')
    check(second.summon_xp_awarded_v1281,'reward marker')
    check(all(len(p.xp)==3 and len(p.character.stats)==2 for p in (a,b)), 'four XP axes for all party')
    check(all(any('EXP +' in msg for msg in p.messages) for p in (a,b)), 'clear XP message')
    check(a.combat_mob_key is None and b.combat_mob_key is None,'combat pointers released')
    before=len(a.xp)
    asyncio.run(reward(fake,second))
    check(len(a.xp)==before, 'no repeat kill payout')

    # Existing UOSS source add is rewarded too (and never becomes permanent).
    owner=MobState(key='br2',room_id='testarena',template_id='uoss_superboss_black_rabite_v11136',
                   hp=10000,engaged_by='Tester')
    world.mobs[owner.key]=owner
    greater=world.spawn_superboss_summon_v1144(owner,'uoss_add_greater_demon_v11156')
    a.combat_mob_key=greater.key
    fake.character=a.character
    asyncio.run(reward(fake,greater))
    check(any(kind=='character' and xp==300000 for kind,xp in a.xp),'Greater Demon XP exact 300k')
    check(greater.respawn_at==float('inf'),'killed add cannot respawn')
    print(f'BOSS SUMMONS v1.28.1: {checks} checks PASS')

if __name__=='__main__':
    import server # canonical bootstrap order is required
    test_v1281()
