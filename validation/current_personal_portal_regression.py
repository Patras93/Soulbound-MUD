# -*- coding: utf-8 -*-
"""Personal portal status through installed handlers; isolated actors and storage."""
import asyncio
import ast
import re
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace


def run():
    from systems import dungeons_regions as regions
    from systems.eternal_glory import infinite
    from player.session_mixins.command_registry import SessionCommandRegistryMixin
    root=Path(__file__).resolve().parents[1]
    tree=ast.parse((root/'player/session_mixins/dungeon_progression.py').read_text('utf-8'))
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionDungeonProgressionMixin')
    names={'use_crypt_portal','use_astral_portal','use_catacomb_portal_v2010','use_giant_fortress_portal_v10800','portal_requires_local_leader_v12811','checkpoint_portal_origin_v2010','catacomb_floor_v2010','catacomb_unlocked_floors_v2010','remember_catacomb_floor_v2010','checkpoint_portal_floors_v11331','checkpoint_portal_unlocked_v11331','show_checkpoint_portal_status_v11331','show_portal_status','show_astral_portal_status','party_checkpoint_portal_exit_v11331'}
    klass.body=[n for n in klass.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
    assert len(klass.body)==len(names)
    env=dict(vars(regions),re=re)
    exec(compile(ast.Module(body=[klass],type_ignores=[]),str(root),'exec'),env)
    Native=env[klass.name]
    class World:
        def __init__(self):self.generated=[]
        def ensure_infinite_dungeon_floor(self,rid):self.generated.append(rid);return True
        def ensure_runtime_room(self,rid):self.generated.append(rid);return True
        def _generatorize_runtime_room(self,rid):self.generated.append(rid)
        def _register_runtime_spawn(self,*args):pass
    class DB:
        def __init__(self):self.floors=defaultdict(set);self.collection=defaultdict(set);self.writes=[]
        def instance_checkpoint_floors(self,aid,kind):return set(self.floors.get((aid,kind),()))
        def collection_entry_ids(self,aid,kind):return set(self.collection.get((aid,kind),()))
        def add_collection_entry(self,aid,kind,entry):self.writes.append(('collection',aid,kind,entry));self.collection[aid,kind].add(entry)
        def save_character(self,ch):self.writes.append(('save',ch.name,ch.room_id))
    class Server:
        def __init__(self):self.db=DB();self.world=World();self.group=[]
        def party_sessions(self,aid,same_room=None):return [m for m in self.group if same_room is None or m.character.room_id==same_room]
        def session_by_account(self,aid):return next((m for m in self.group if m.account_id==aid),None)
    class Session(Native,SessionCommandRegistryMixin):
        def __init__(self,s,aid,rid):
            self.server=s;self.account_id=aid;self.character=SimpleNamespace(name=f'G{aid}',room_id=rid)
            self.previous_room_id='old';self.messages=[];self.current_hp=100;self.closed=False
            self.combat_mob_key=None;self.moving=self.guiding=False
            self.resting=self.rest_task=False;self.auto_fishing=self.auto_fishing_task=False
            self.auto_mining=self.auto_mining_task=False;self.auto_woodcutting=self.auto_woodcutting_task=False
            self.auto_herbalism=self.auto_herbalism_task=False;s.group.append(self)
        def party_key(self):return 1
        def normalize_room_query(self,raw):return str(raw or '').strip().lower()
        def is_downed_v0371(self):return False
        def dungeon_exit_destination(self,*a):return None
        async def discover_room(self,*a,**kw):return None
        async def send(self,msg):self.messages.append(str(msg))
        async def look(self):self.messages.append('LOOK')
        async def stop_rest(self,**kw):self.resting=False
        async def stop_auto_fishing(self,**kw):self.auto_fishing=False
        async def stop_auto_mining(self,**kw):self.auto_mining=False
        async def stop_auto_woodcutting(self,**kw):self.auto_woodcutting=False
        async def stop_auto_herbalism(self,**kw):self.auto_herbalism=False
        def report_runtime_error(self,exc,**kw):raise exc
    rooms={f'v1100_vault_{anchor}_09':{'exits':{}} for _,anchor,_,_ in infinite.ENDLESS.values()}
    infinite.install(rooms,{},[],{}, {},World,Session)
    checks=0
    def ck(condition,label):
        nonlocal checks
        assert condition,label
        checks+=1
    async def command(p,cmd,arg):
        assert await p.dispatch_registered_command(cmd,arg) is True
    async def exercise():
        cases=[('crypt','crypt_floor_30',30,10,20,'portal'),('mythic_crypt','mythic_crypt_floor_30_r1',30,10,20,'portal'),('astral','astral_floor_150',150,100,120,'portal'),('mythic_astral','mythic_astral_floor_30',30,10,20,'portal'),('astral','astral_floor_150',150,100,120,'astralportal'),('giant','giant_fortress_30',30,10,20,'gigantportal'),('giant','giant_fortress_30_r1',30,10,20,'portal'),('catacomb','catacomb_f2_r1',2,1,2,'portal')]
        cases += [(key,infinite.floor_id(key,30),30,10,20,'portal') for key in infinite.ENDLESS]
        cases += [('wieza',infinite.floor_id('wieza',30),30,10,20,'astralportal')]
        for kind,rid,current,low,high,cmd in cases:
            s=Server();lead=Session(s,1,rid);p=Session(s,2,rid)
            if kind in infinite.ENDLESS:
                s.db.collection[1,f'v1100_checkpoint_{kind}']={str(high),str(current)}
                s.db.collection[2,f'v1100_checkpoint_{kind}']={str(low)}
            elif kind=='catacomb':
                s.db.collection[1,'catacomb_portal_floors_v2010']={'1','2','3'}
                s.db.collection[2,'catacomb_portal_floors_v2010']={'1'}
            else:
                s.db.floors[1,kind]={high,current};s.db.floors[2,kind]={low}
            ck(p.portal_requires_local_leader_v12811(),kind+' member blocked for travel')
            for arg in ('','lista','status','list'):
                p.messages.clear();await command(p,cmd,arg);msg=' '.join(p.messages)
                ck(f'Bieżące piętro: {current}.' in msg,kind+' personal current floor '+arg)
                expected=(f'Checkpointy: {low}.' if kind in infinite.ENDLESS else 'twoje odblokowane piętra: 1.' if kind=='catacomb' else f'Odblokowane checkpointy: {low}.')
                ck(expected in msg,kind+' personal checkpoint '+msg)
                ck('uruchamia lider' not in msg and 'LOOK' not in p.messages,kind+' status not blocked or moved')
                ck(p.character.room_id==rid and lead.character.room_id==rid and not s.db.writes and not s.world.generated,kind+' read-only')
            lead.messages.clear();await command(lead,cmd,'');msg=' '.join(lead.messages)
            ck(f'Bieżące piętro: {current}.' in msg and lead.character.room_id==rid and p.character.room_id==rid and not s.db.writes,kind+' leader blank does not exit')
            p.messages.clear();await command(p,cmd,str(low))
            ck(p.character.room_id==rid and lead.character.room_id==rid and not s.db.writes,kind+' explicit member travel denied')
        s=Server();lead=Session(s,1,'crypt_floor_30');p=Session(s,2,'crypt_floor_30')
        s.db.floors[1,'crypt']={10,20,30};s.db.floors[2,'crypt']={30}
        await command(lead,'portal','20')
        ck(lead.character.room_id=='crypt_floor_20' and p.character.room_id=='crypt_floor_30','leader only moves unlocked members')
        await command(lead,'portal','wyjdz')
        ck(lead.character.room_id=='crypt_hall','explicit exit preserved')
        s=Server();p=Session(s,1,'crypt_floor_30');s.db.floors[1,'crypt']={30}
        await command(p,'portal','');ck(p.character.room_id=='crypt_floor_30' and not s.db.writes,'solo blank is status')
    asyncio.run(exercise())
    print(f'PERSONAL PORTAL STATUS / PARTY v11680: {checks}/{checks} PASS',flush=True)
    return checks


if __name__=='__main__':run()
