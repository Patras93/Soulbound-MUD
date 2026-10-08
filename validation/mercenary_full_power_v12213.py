# -*- coding: utf-8 -*-
"""v1.22.13: full equipped owner power and mercenary lethal hits with kill credit."""
import ast
import asyncio
import time
from pathlib import Path
from types import SimpleNamespace

from systems.mercenary_taverns import (MERCENARIES, COOLDOWN, pick_next_contract,
    mercenary_owner_power_v1213, mercenary_damage_cap_ratio_v12212,
    mercenary_owner_full_power_v12213)
from systems.mercenary_growth_v1220 import (mercenary_owner_level_v1228,
    mercenary_attack_multiplier, mercenary_tactic)


def validate_mercenary_full_power_v12213():
    checks = 0
    def check(predicate, label):
        nonlocal checks
        if not predicate:
            raise AssertionError('MERCENARY FULL POWER v1.22.13: ' + label)
        checks += 1

    # Full base scaling, cross-class hiring, ALL equipped flat and percent bonuses.
    for phys, magic, expected in ((40000,1000,40000), (1000,40000,40000),
                                 (40000,40000,40000), (100,20,100)):
        check(mercenary_owner_full_power_v12213(phys, magic) == expected,
              '100 percent offensive channel')
    check(mercenary_owner_full_power_v12213(40000,1000,1.5,1.0,1.2) == 72000,
          'physical EQ damage bonus and set')
    check(mercenary_owner_full_power_v12213(1000,40000,1.0,1.5,1.2) == 72000,
          'magical EQ damage bonus and set')
    check(mercenary_owner_full_power_v12213(40000,1000,1.0,1.5,1.0) == 40000,
          'owner choice is not penalized by unrelated school EQ')
    check(mercenary_owner_full_power_v12213(1000,35000,2.0,1.0,1.0) == 35000,
          'best final equipped channel is selected')
    for template in ({}, {'elite': True}, {'rank':'boss'},
                     {'uoss_unique_superboss_key':'black_rabite'}):
        check(mercenary_damage_cap_ratio_v12212(template) == 1.0,
              'no enemy HP percentage cap')

    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root/'player/session_mixins/mercenary_taverns.py').read_text('utf8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'SessionMercenaryTavernsMixin')
    fn = next(n for n in cls.body if isinstance(n, ast.AsyncFunctionDef)
              and n.name == 'mercenary_combat_turn_v1170')
    namespace = dict(time=time, COOLDOWN=COOLDOWN, MERCENARIES=MERCENARIES,
        pick_next_contract=pick_next_contract,
        mercenary_owner_power_v1213=mercenary_owner_power_v1213,
        mercenary_owner_full_power_v12213=mercenary_owner_full_power_v12213,
        mercenary_damage_cap_ratio_v12212=mercenary_damage_cap_ratio_v12212,
        mercenary_owner_level_v1228=mercenary_owner_level_v1228,
        mercenary_attack_multiplier=mercenary_attack_multiplier,
        mercenary_tactic=mercenary_tactic,
        superboss_healing_blocked_v11179=lambda p: False,
        MOB_TEMPLATES={'enemy': {'name':'Boss', 'rank':'boss'},
                       'elite': {'name':'Elite', 'elite':True},
                       'super': {'name':'Superboss', 'superboss':True}},
        v0314_adjust_damage_vs_template=lambda template,power,damage_type,role:(power,None))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),
                 'player/session_mixins/mercenary_taverns.py', 'exec'), namespace)

    class Session:
        mercenary_combat_turn_v1170 = namespace['mercenary_combat_turn_v1170']
        def __init__(self, role, phys=1000, magic=1, phys_eq=1.0, magic_eq=1.0, set_eq=1.0):
            self.character=SimpleNamespace(name='Owner',room_id='room',character_level=1)
            self.account_id=1
            self.current_hp=100000
            self.skill_guard=1
            self._mercenary_next_action_v1170=0.0
            self._mercenary_last_role_v1170=None
            self._physical,self._magic=phys,magic
            self._phys_eq,self._magic_eq,self._set_eq=phys_eq,magic_eq,set_eq
            self.messages=[]
            self.kills=0
            self.server=SimpleNamespace(db=SimpleNamespace(
                mercenary_contracts=lambda aid,now:[{'role':role,'expires_at':0}],
                mercenary_progress_v1220=lambda aid,r:{'xp':0,'specialization':'automatyczna','actions':0}),
                party_sessions=lambda aid,same_room=None:[self],
                party_combat_broadcast=self.broadcast)
        def physical_power(self): return self._physical
        def spell_power(self): return self._magic
        def equipment_damage_multiplier(self,channel):
            return self._phys_eq if channel=='physical' else self._magic_eq
        def total_set_damage_multiplier(self): return self._set_eq
        def max_hp(self): return 100000
        async def apply_boss_defense(self,mob,power): return power
        async def send_combat(self,msg,detail='essential'): self.messages.append(msg)
        async def broadcast(self,owner,msg,detail='essential'): self.messages.append(msg)
        async def mob_defeated(self,mob):
            check(mob.hp <= 0, 'real defeat requires zero HP')
            check(mob.alive, 'no duplicate defeat processing')
            mob.alive=False
            self.kills+=1

    async def run_turn(role,template='enemy',hp=100000,phys=1000,magic=1,
                       phys_eq=1.0,magic_eq=1.0,set_eq=1.0):
        owner=Session(role,phys,magic,phys_eq,magic_eq,set_eq)
        mob=SimpleNamespace(template_id=template,room_id='room',alive=True,hp=hp)
        await owner.mercenary_combat_turn_v1170(mob)
        return owner,mob

    async def run():
        for role,spec in MERCENARIES.items():
            physical,mob=await run_turn(role,phys=40000,magic=1000)
            magical,mob2=await run_turn(role,phys=1000,magic=40000)
            check(physical.messages and magical.messages, role+' reports attacks')
            check(mob.hp == mob2.hp, role+' cross-class hiring yields equal damage')
            check(100000-mob.hp >= 40000, role+' no 42% coefficient')
            check(physical.kills==0 and magical.kills==0,role+' living mob not marked defeated')
        for role in ('mag','wojownik'):
            basic,foe=await run_turn(role, phys=1000,magic=50)
            improved,better=await run_turn(role, phys=1000,magic=50,phys_eq=1.8,set_eq=1.2)
            check(100000-better.hp > 100000-foe.hp,role+' actual equipped percent and sets')
        for role in ('mag','wojownik','paladyn'):
            for kind in ('enemy','elite','super'):
                hero,foe=await run_turn(role,template=kind,hp=1000,phys=5000)
                check(foe.hp == 0 and hero.kills == 1 and not foe.alive,
                      role+' can finish '+kind+' and credit once')
                check(any('0 HP przeciwnika' in s for s in hero.messages),
                      role+' readable kill message')
    asyncio.run(run())
    src=(root/'player/session_mixins/combat_realtime.py').read_text('utf8')
    check('if not mob.alive or mob.hp <= 0:' in src and
          'await self.mercenary_combat_turn_v1170(mob)' in src,
          'player turn stops after mercenary kill')
    return checks

if __name__ == '__main__':
    print('MERCENARY FULL POWER v1.22.13:',validate_mercenary_full_power_v12213(),'checks PASS')
