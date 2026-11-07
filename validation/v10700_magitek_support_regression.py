# -*- coding: utf-8 -*-
"""Stage 2 real v107 support command and defensive combat integration checks."""
from __future__ import annotations
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import patch
from core.magitek_v107 import skill_catalogue
from systems.magitek_support_v107 import (
    WARD_KEY, RUNIC_KEY, active_ward, runic_weapon_active, duration_seconds,
    use_support_skill, install_defense_adapter, install_runic_adapter,
)

SKILLS = {row['v107_skill']: row for row in skill_catalogue()}

class DB:
    def __init__(self):
        self.learned = set(row['id'] for row in skill_catalogue())
        self.saved = []
        self.fail_on = None
        self.counter = None
    def knows_skill(self, _, skill): return skill in self.learned
    def skill_progress(self, _, skill): return {'level': 40}
    def job_ability_slot(self, _, __): return self.counter
    def save_character(self, character):
        if character.name == self.fail_on: raise RuntimeError('simulated disk failure')
        self.saved.append((character.name, character.room_id))

class Server:
    def __init__(self):
        self.db = DB()
        self.members = []
        self.broadcasts=[]
    def party_sessions(self, _, same_room=None):
        return [m for m in self.members if same_room is None or m.character.room_id == same_room]
    async def broadcast_room(self, room, message, exclude=None):
        self.broadcasts.append((room,message))

class Actor:
    def __init__(self, name, server, room='temple_basement'):
        self.character=SimpleNamespace(name=name,class_name='Magitek',room_id=room)
        self.server=server
        self.account_id=len(server.members)+1
        self.current_hp=100
        self.current_mana=50
        self.closed=False
        self.combat_mob_key=None
        self.active_skill_buffs={}
        self.sent=[]; self.xp=[]; self.visited=0
        self.level=40
        server.members.append(self)
    def is_downed_v0371(self): return False
    def class_mastery_level(self, cls): return self.level
    def effective_willpower(self): return 120
    def effective_intelligence(self): return 100
    def equipment_flat_power_totals_v11187(self): return {'attack':20}
    def max_mana(self): return 100
    def permanence_active_v11154(self): return False
    async def grant_skill_use_xp(self, skill): self.xp.append(skill['v107_skill'])
    async def send(self, message): self.sent.append(message)
    async def skill_combat_target(self, query):
        self.sent.append('Nie widzę tutaj takiego przeciwnika.')
        return None
    async def look(self): self.visited+=1
    async def apply_boss_defense(self, mob, damage): return damage
    async def mob_defeated(self, mob): self.sent.append('KILL')


def run():
    checks=0
    def ok(result, text):
        nonlocal checks
        if not result: raise AssertionError(text)
        checks+=1
    def cast(a, slug, target=''):
        return asyncio.run(use_support_skill(a,SKILLS[slug],target))

    srv=Server(); a=Actor('Magitek',srv); b=Actor('Sympatyczna',srv); stranger=Actor('Inny',srv,'square')
    cast(a,'tekshield','Sympatyczna')
    ok(active_ward(b)=='tekshield','ward to local party member')
    ok(b.active_skill_buffs[WARD_KEY]['beneficial'] is True,'ward benefit visible')
    ok(a.xp==['tekshield'] and b.sent,'cast xp once and notify recipient')
    cast(a,'tekbarrier','Sympatyczna')
    ok(active_ward(b)=='tekbarrier' and len(b.active_skill_buffs)==1,'exclusive ward')
    cast(a,'tekshield','Inny')
    ok(len(a.xp)==2 and active_ward(stranger) is None,'no remote buff exploit')
    cast(a,'runicweapon')
    ok(runic_weapon_active(a),'temporary runic')
    ok(a.xp[-1]=='runicweapon','runic XP')
    ok(not runic_weapon_active(a,now=time.time()+1000),'runic expires')
    ok(duration_seconds('tekshield',10000,10000)==80,'duration bounded')
    ok(duration_seconds('runicweapon',10000,10000)==60,'runic duration bounded')

    class Defense:
        def defense(self): return 100
        def magic_defense(self): return 200
    install_defense_adapter(Defense)
    class DefenseCharacter(Defense):
        active_skill_buffs = {}
    d=DefenseCharacter()
    ok(d.defense()==100 and d.magic_defense()==200,'no ward unchanged')
    d.active_skill_buffs={WARD_KEY:dict(until=time.time()+100,magitek_mode='tekshield')}
    ok(d.defense()==125 and d.magic_defense()==250,'shield native defense and magic')
    d.active_skill_buffs[WARD_KEY]['magitek_mode']='tekbarrier'
    ok(d.defense()==125 and d.magic_defense()==200,'barrier physical defense only')
    d.active_skill_buffs[WARD_KEY]['until']=1
    ok(d.defense()==100 and d.magic_defense()==200,'expired ward has no defense')

    b.active_skill_buffs['other']={'name':'Other', 'beneficial':True,'until':time.time()+90}
    cast(a,'diffuser','Sympatyczna')
    ok(not b.active_skill_buffs, 'diffuser removes beneficial wards and buffs')
    ok(a.xp[-1]=='diffuser','successful diffuser XP')
    b.active_skill_buffs['other']={'name':'Other','beneficial':False,'until':time.time()+90}
    cast(a,'diffuser','Sympatyczna')
    ok('other' in b.active_skill_buffs and a.xp[-1]=='diffuser','no debuff removal and no XP')
    cast(a,'diffuser','Inny')
    ok(a.xp[-1]=='diffuser','no enemy/remote dispel')

    a.level=7
    cast(a,'diffuser')
    ok('wymaga poziomu' in a.sent[-1] and len(a.xp)==4,'level gate prior to use')
    a.level=40
    srv.db.learned.remove(SKILLS['tekshield']['id'])
    cast(a,'tekshield')
    ok('naucz się' in a.sent[-1] and active_ward(a) is None,'learned gate prior to use')
    srv.db.learned.add(SKILLS['tekshield']['id'])
    a.current_hp=0
    cast(a,'tekshield')
    ok('powalona' in a.sent[-1] and active_ward(a) is None,'dead cast blocked')
    a.current_hp=100

    # X-Fer: all present, living, same-room members and durable DB save.
    cast(a,'xfer')
    ok(a.character.room_id=='square' and b.character.room_id=='square','party teleported to square')
    ok(stranger.character.room_id=='square','remote player unchanged')
    ok(a.visited==1 and b.visited==1,'all moved members get look')
    ok(len(a.xp)==4+1 and a.xp[-1]=='xfer','xfer one skill award')
    ok(any(x[0]=='Sympatyczna' and x[1]=='square' for x in srv.db.saved),'position saved to DB')

    # Failed persistence must leave both members where they were.
    for m in (a,b): m.character.room_id='temple_basement'
    srv.db.fail_on='Sympatyczna'; old=len(a.xp)
    cast(a,'xfer')
    ok(a.character.room_id=='temple_basement' and b.character.room_id=='temple_basement', 'rollback memory')
    ok(len(a.xp)==old,'no XP on save failure')
    srv.db.fail_on=None
    b.combat_mob_key='monster'; cast(a,'xfer')
    ok(a.character.room_id=='temple_basement','block party combat escape')
    b.combat_mob_key=None
    cast(a,'xfer','Inny')
    ok(a.character.room_id=='temple_basement','reject targeted xfer')

    # Runic: real bound interception only for magical attacks, MP capped.
    from data.mobs import MOB_TEMPLATES
    mob_id='v107_magitek_regression_magic'
    MOB_TEMPLATES[mob_id]={'name':'Testowy Żywiołak','damage_type':'magic','damage':60}
    class Interception:
        async def mec_intercept_incoming_attack_v11196(self,mob):
            self.old_calls+=1
            return False
    install_runic_adapter(Interception)
    class InterceptActor(Actor,Interception):
        def __init__(self,name,server):
            super().__init__(name,server)
            self.old_calls=0
    try:
        s2=Server(); g=InterceptActor('Obronca',s2)
        mob=SimpleNamespace(template_id=mob_id,hp=100,alive=True,combat_turn=1)
        g.active_skill_buffs[RUNIC_KEY]={'until':time.time()+100}
        with patch('systems.magitek_support_v107.random.random', return_value=0.0):
            result=asyncio.run(g.mec_intercept_incoming_attack_v11196(mob))
        ok(result is True and g.current_mana>50 and g.old_calls==0,'runic intercept and restore real MP')
        with patch('systems.magitek_support_v107.random.random', return_value=0.0):
            repeat=asyncio.run(g.mec_intercept_incoming_attack_v11196(mob))
        ok(repeat is False and g.old_calls==1,'no duplicate roll same turn')
        mob.combat_turn+=1
        with patch('systems.magitek_support_v107.random.random', return_value=0.999):
            missed=asyncio.run(g.mec_intercept_incoming_attack_v11196(mob))
        ok(missed is False and g.old_calls==2,'failed runic uses canonical enemy attack')
        mob.template_id='v107_magitek_regression_physical'
        MOB_TEMPLATES[mob.template_id]={'name':'Testowy Wojownik','damage_type':'physical','damage':60}
        with patch('systems.magitek_support_v107.random.random',side_effect=AssertionError('physical must not roll')):
            physical=asyncio.run(g.mec_intercept_incoming_attack_v11196(mob))
        ok(physical is False and g.old_calls==3,'physical attack unaffected')
        mob.template_id=mob_id
        g.active_skill_buffs.pop(RUNIC_KEY)
        g.active_skill_buffs[WARD_KEY]={'until':time.time()+100,'magitek_mode':'tekbarrier'}
        with patch('systems.magitek_support_v107.random.random',side_effect=AssertionError('reflect should not roll')):
            reflected=asyncio.run(g.mec_intercept_incoming_attack_v11196(mob))
        ok(reflected is True and mob.hp<100 and g.old_calls==3,'barrier reflects magic through boss defense')
        # TekBarrier from a Magitek must also reflect on an allied non-Magitek class.
        ally=InterceptActor('Sprzymierzeniec',s2)
        ally.character.class_name='Wojownik'
        ally.active_skill_buffs[WARD_KEY]={'until':time.time()+100, 'magitek_mode':'tekbarrier'}
        mob.hp=100
        ally_reflect=asyncio.run(ally.mec_intercept_incoming_attack_v11196(mob))
        ok(ally_reflect is True and mob.hp<100, 'barrier reflects for non-Magitek ally')
        g.active_skill_buffs[WARD_KEY]['until']=0
        without=asyncio.run(g.mec_intercept_incoming_attack_v11196(mob))
        ok(without is False and g.old_calls==4,'barrier expires and stops reflecting')
    finally:
        MOB_TEMPLATES.pop(mob_id,None)
        MOB_TEMPLATES.pop('v107_magitek_regression_physical',None)
    ok(SKILLS['runic'].get('mec_role')=='counter' and 'magitek runic' in SKILLS['runic']['aliases'],
       'real counter slot and native UOSS job command')
    print(f'V107 MAGITEK ETAP 2 SUPPORT: {checks} kontroli PASS')
    return checks

if __name__=='__main__': run()
