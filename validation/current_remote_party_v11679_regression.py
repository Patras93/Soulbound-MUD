# -*- coding: utf-8 -*-
"""Remote party requests; production handlers on isolated actors."""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import patch


def run():
    from player.session_mixins.minions_party_monitor_v11665 import SessionMinionsPartyMonitorV11665Mixin
    from player.session_mixins.command_registry import COMMAND_REGISTRY, resolve_session_command, SessionCommandRegistryMixin, command_state_safe
    from data.rooms import ROOMS
    # Initialize the real dungeon catalogue before inserting test rooms.
    from world.generation_systems import v0200_mega_identity
    checks = 0
    def check(value, label):
        nonlocal checks
        assert value, label
        checks += 1
    class DB:
        def __init__(self):self.saved=[];self.cleared=set();self.fail=False
        def save_character(self,c):
            if self.fail:raise RuntimeError('fixture save failure')
            self.saved.append((c.name,c.room_id))
        def boss_floor_cleared(self,aid,kind,floor):return (aid,kind,floor) in self.cleared
    class Server:
        def __init__(self):
            self.parties={};self.party_goals={};self.party_ready_checks={};self.party_invites={}
            self.db=DB();self.sessions={};self.messages=[]
        def session_by_account(self,aid):return self.sessions.get(aid)
        async def broadcast_room(self,*args,**kwargs):self.messages.append(args)
        async def party_broadcast(self,*args,**kwargs):self.messages.append(args)
    class Legacy:
        async def handle_party(self,args):self.legacy.append(args)
        async def leave_party(self,announce=True):
            k=self.party_key()
            if k==self.account_id:self.server.parties.pop(k,None)
            elif k is not None:self.server.parties[k].discard(self.account_id)
        async def disband_party(self):self.server.parties.pop(self.account_id,None)
    class Actor(SessionMinionsPartyMonitorV11665Mixin,Legacy,SessionCommandRegistryMixin):
        def __init__(self,server,aid,name,room):
            self.server=server;self.account_id=aid;self.character=SimpleNamespace(name=name,room_id=room,party_capacity=lambda:3)
            self.closed=False;self.current_hp=100;self.previous_room_id='old';self.messages=[];self.legacy=[];self.ignored=set();self.looks=0
            server.sessions[aid]=self
        def party_key(self):return next((k for k,m in self.server.parties.items() if self.account_id in m),None)
        def normalize_description_query(self,raw):return str(raw).strip().lower().translate(str.maketrans('ąćęłńóśźż','acelnoszz'))
        async def send(self,msg):self.messages.append(msg)
        async def look(self):self.looks+=1
        def is_downed_v0371(self):return False
        def guide_task_active(self):return False
        def smelt_task_active_v1124(self):return False
        def is_ignored_v03051(self,owner,other):return other in self.ignored
        def newbie_entry_block_v03051(self,target):return ''
        def mythic_entry_error(self,target):return ''
        def profession_dungeon_access_error(self,target):return ''
        def mine_progress(self):return {'max_floor_unlocked':1}
        def uoss_deep_dungeon_apanda_cleared_v11331(self,gate):return False
    async def exercise():
        s=Server();a=Actor(s,1,'Ala','__remote_a');b=Actor(s,2,'Bartek','__remote_b');c=Actor(s,3,'Celina','__remote_c')
        s.parties={2:{2},3:{3}}
        check(resolve_session_command('druzyny')=='druzyny' and resolve_session_command('drużyny')=='druzyny','list command')
        check(COMMAND_REGISTRY['druzyny'][0]=='show_remote_parties_v11679','registered method')
        check(resolve_session_command('druzyna')=='party','old Polish party alias')
        check(command_state_safe('druzyny','rest') and command_state_safe('druzyny','guide') and command_state_safe('druzyny','downed'),'read-only list does not interrupt activities')
        check(await a.dispatch_registered_command('druzyny','') and not a._remote_party_dispatching_v11679,'registry dispatch list')
        check('1. Lider: Bartek' in a.messages[-1] and '2. Lider: Celina' in a.messages[-1],'list sorted')
        check(await a.dispatch_registered_command('party','dołącz 1') and not a._remote_party_dispatching_v11679,'registry dispatch remote request')
        check(a.party_key() is None and a.character.room_id=='__remote_a','request does not move or join')
        check('Ala' in b.messages[-1] and 'akceptuj' in b.messages[-1],'leader notification')
        await a.handle_party('dolacz Celina');check(s.party_join_requests_v11679[1][1] is b,'duplicate cannot overwrite')
        await c.handle_party('akceptuj Ala');check(a.party_key() is None and 1 in s.party_join_requests_v11679,'wrong leader blocked')
        await b.handle_party('prosby');check('Ala' in b.messages[-1],'leader pending')
        b.moving=True;await b.handle_party('akceptuj Ala');check(a.party_key() is None and 1 in s.party_join_requests_v11679,'moving leader blocks')
        b.moving=False;a.combat_mob_key='mob';await b.handle_party('akceptuj Ala');check(a.party_key() is None,'combat requester blocks')
        a.combat_mob_key=None;a._remote_party_dispatching_v11679=True;await b.handle_party('akceptuj Ala');check(a.party_key() is None,'command in progress blocks remote transfer')
        a._remote_party_dispatching_v11679=False;s.db.fail=True
        try:await b.handle_party('akceptuj Ala')
        except RuntimeError as exc:check(str(exc)=='fixture save failure','save exception retained')
        check(a.character.room_id=='__remote_a' and a.previous_room_id=='old' and a.party_key() is None and 1 in s.party_join_requests_v11679,'save failure rolled back')
        s.db.fail=False;b.character.room_id='__remote_c';s.party_invites[1]=3;s.party_ready_checks[2]={1,2}
        await b.handle_party('akceptuj Ala');check(a.party_key()==2 and a.character.room_id=='__remote_c','joins current leader location')
        check(s.db.saved==[('Ala','__remote_c')] and a.previous_room_id is None and a.looks==1,'saved teleport, no back bypass, look')
        check(1 not in s.party_join_requests_v11679 and 1 not in s.party_invites and s.party_ready_checks[2]=={2},'request consumed and old invite cleared')
        await b.handle_party('akceptuj Ala');check(len(s.db.saved)==1,'no duplicate acceptance')
        await a.handle_party('dolacz Celina');check(a.party_key()==2,'no second party')
        await a.leave_party();await a.handle_party('dolacz Celina');await c.handle_party('odrzuć Ala');check(a.party_key() is None and 1 not in s.party_join_requests_v11679,'decline')
        await a.handle_party('dolacz Celina');await a.handle_party('anuluj');check(1 not in s.party_join_requests_v11679,'cancel')
        await a.handle_party('dolacz Celina');old=s.party_join_requests_v11679[1];s.party_join_requests_v11679[1]=(*old[:3],time.monotonic()-1)
        await c.handle_party('akceptuj Ala');check(a.party_key() is None and 1 not in s.party_join_requests_v11679,'expired')
        await a.show_remote_parties_v11679();await a.handle_party('dolacz Celina');s.parties[3]={3};await c.handle_party('akceptuj Ala');check(a.party_key() is None,'recreated party invalidates request')
        await a.handle_party('dolacz 2');check(1 not in s.party_join_requests_v11679,'stale number invalidated')
        await a.handle_party('dolacz Celina');s.parties[3].update({4,5});await c.handle_party('akceptuj Ala');check(a.party_key() is None and 1 in s.party_join_requests_v11679,'capacity rechecked')
        s.parties[3]={3};await a.handle_party('dolacz Celina');await a.leave_party(announce=False);check(1 not in s.party_join_requests_v11679,'logout invalidates')
        c.ignored.add(1);await a.handle_party('dolacz Celina');check(1 not in s.party_join_requests_v11679,'ignore respected');c.ignored.clear()
        await a.handle_party('dolacz Celina');await c.disband_party();check(1 not in s.party_join_requests_v11679,'disband invalidates')
        await a.handle_party('dolacz');check(a.legacy==['dolacz'],'legacy invite accept preserved')
        await a.handle_party('odrzuc');check(a.legacy[-1]=='odrzuc','legacy decline preserved')
        check(bool(a.remote_party_entry_error_v11679('__private')),'secret room blocked')
        check(bool(a.remote_party_entry_error_v11679('crypt_floor_11')),'personal boss gate blocked')
        s.db.cleared.add((1,'crypt',10));check(not a.remote_party_entry_error_v11679('crypt_floor_11'),'personal clear permits crypt')
        check(bool(a.remote_party_entry_error_v11679('uoss_deep_dungeon_floor_26_v11331')),'Apanda gate blocked')
        check(bool(a.remote_party_entry_error_v11679('uoss_superboss_arena_odin_v11136')),'UOSS arena requires proper entry')
        check(bool(a.remote_party_entry_error_v11679('__sea')),'ship gate protected')
        check(bool(a.remote_party_entry_error_v11679('__missing')),'unknown destination blocked')
    names={f'__remote_{letter}':{'name':letter} for letter in 'abc'}
    names.update({'__private':{'v1190_secret_role':'chamber'},'crypt_floor_11':{},'uoss_deep_dungeon_floor_26_v11331':{},'uoss_superboss_arena_odin_v11136':{},'__sea':{'requires_ship':True}})
    with patch.dict(ROOMS,names):asyncio.run(exercise())
    print(f'REMOTE PARTY REQUEST / TELEPORT v11679: {checks}/{checks} PASS',flush=True)
    return checks

if __name__=='__main__':run()
