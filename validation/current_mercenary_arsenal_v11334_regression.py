# -*- coding: utf-8 -*-
"""Real class skill selection and combat safety for 38 mercenary contracts."""
import asyncio
from types import SimpleNamespace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.mercenary_taverns import MERCENARIES
from systems.mercenary_class_skills_v11334 import (
    available_attacks, pick_skill, execute_attack, engaged_targets,
)
from core.classes_skills import CLASS_SKILLS


def run():
    checks = 0
    def check(value, note):
        nonlocal checks
        assert value, note
        checks += 1
    check(len(MERCENARIES) == 38, '38 contracts must remain available')
    for role, spec in MERCENARIES.items():
        low = available_attacks(role, 1)
        high = available_attacks(role, 800)
        check(bool(low), 'missing level-one attack ' + role)
        check(len(high) >= 3, 'not enough real attacks ' + role)
        ids = {s['id'] for s in high}
        check(len(ids) == len(high), 'duplicate skill ids ' + role)
        known = {s['id'] for s in CLASS_SKILLS.get(spec['class'], ())}
        check(not known or ids.issubset(known), 'source catalogue mismatch ' + role)
        session = SimpleNamespace()
        # Disable periodic Mec V-MAX only for the ordinary round-robin proof;
        # special Cosmic Rave override is verified independently below.
        if role == 'mec':
            session._mercenary_class_ai_v11334 = {role: {'turn': 0, 'vmax_until': 0., 'vmax_next': float('inf')}}
        chosen = [pick_skill(session, role, 800, 10.+n*5, False)[0]['id'] for n in range(len(high))]
        check(set(chosen) == ids, 'AI does not use the full unlocked offensive catalogue ' + role)
        check(len(set(chosen[:min(20, len(chosen))])) >= 3,
              'AI repeats only one skill ' + role)
        for s in low:
            check(int(s['unlock']) <= 1, 'locked level-one ability '+role)
    mec = 'mec'
    session = SimpleNamespace()
    for i in range(5):
        skill, started, vmax = pick_skill(session, mec, 110, 100+i*5)
        check(not vmax and not started, 'V-MAX before level 130')
    skill, started, vmax = pick_skill(session, mec, 130, 1000)
    check((skill['name'],started,vmax) == ('Cosmic Rave',True,True), 'Mec must cast V-MAX Cosmic Rave at 130')
    check(int(skill['vmax_random_hits']) == 5, 'five hits from source catalogue')
    unlocked = [s['name'] for s in available_attacks('mec', 110)]
    check('Cosmic Rave' in unlocked, 'Cosmic Rave unlocked at 110')
    check(not any(s.get('mec_special') in ('jammer','hypno_flash','logic_bomb')
                  for s in available_attacks('mec',800)), 'do not fake control status')

    class FakeWorld:
        def __init__(self,mobs): self.mobs=mobs
        def room_mobs(self,room_id): return [m for m in self.mobs if m.room_id==room_id and m.alive]

    def m(key,room,engaged=None,hp=300):
        return SimpleNamespace(key=key, room_id=room, alive=True, hp=hp,
            template_id='goblin', engaged_by=engaged, aoe_engaged_by=None)

    async def combat():
        owner='Owner'
        one=m('1','r',owner,900)
        two=m('2','r',owner,900)
        passive=m('3','r',None,900)
        other=m('4','other',owner,900)
        enemy=m('5','r','SomebodyElse',900)
        mobs=[one,two,passive,other,enemy]
        char=SimpleNamespace(name=owner,room_id='r')
        sess=SimpleNamespace(character=char,account_id=42,combat_mob_key='1')
        sess.server=SimpleNamespace(world=FakeWorld(mobs),party_sessions=lambda *a,**k:[sess])
        async def defense(target,value):return value
        sess.apply_boss_defense=defense
        sess.v0210_adjust_player_damage=lambda n:n
        choices=engaged_targets(sess,one)
        check([x.key for x in choices] == ['1','2'],'cross-room/cross-fight auto-agro')
        cosmic=next(s for s in available_attacks('mec',130) if s['name']=='Cosmic Rave')
        total,first,killed,hits=await execute_attack(sess,one,150,cosmic,'mec',True)
        check(hits==5,'Cosmic must strike five times')
        check(total>0 and first>=0,'Cosmic must deal real HP damage')
        check(passive.hp==900 and other.hp==900 and enemy.hp==900,'never hit unengaged mobs')
        check(one.hp<900 or two.hp<900,'engaged enemies take damage')
        one.hp=45;two.hp=45
        total,first,killed,hits=await execute_attack(sess,one,1000,cosmic,'mec',True)
        check(0<=hits<=5 and bool(killed),'Cosmic kills only real engaged targets')
        check(passive.hp==900 and other.hp==900 and enemy.hp==900,'no collateral after kill')
        one.alive=True;one.hp=100
        char.room_id='other'
        total,first,killed,hits=await execute_attack(sess,one,100,cosmic,'mec',True)
        check((total,hits)==(0,0),'moving away must abort attack')
    asyncio.run(combat())
    print(f'MERCENARY REAL CLASS ARSENAL v113.00.34: {checks} checks PASS')
    return checks

if __name__=='__main__':
    run()
