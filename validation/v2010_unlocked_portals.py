# -*- coding: utf-8 -*-
"""v2.00.10: real checkpoint-to-checkpoint portal and catacomb regression."""
import asyncio
from collections import defaultdict
from types import SimpleNamespace
import server as _server_initialized_v2010
from systems.dungeons_regions import (
    crypt_floor_id, astral_floor_id, mythic_crypt_floor_id, mythic_astral_floor_id,
)
from world.world_expansion_v import CATACOMB_LEVELS_V0900
from player.session_mixins.dungeon_progression import SessionDungeonProgressionMixin
from player.session_mixins.command_registry import COMMAND_REGISTRY

class MemoryDB:
    def __init__(self):
        self.floors=defaultdict(set)
        self.collection=defaultdict(set)
        self.saves=[]
    def instance_checkpoint_floors(self,account,kind):
        return set(self.floors[account,kind])
    def collection_entry_ids(self,account,kind):
        return set(self.collection[account,kind])
    def add_collection_entry(self,account,kind,entry):
        entries=self.collection[account,kind]
        before=len(entries)
        entries.add(str(entry))
        return len(entries)!=before
    def save_character(self,ch):
        self.saves.append((ch.name,ch.room_id))

class Dummy(SessionDungeonProgressionMixin):
    def __init__(self,server,account,room):
        self.server=server
        self.account_id=account
        self.character=SimpleNamespace(name=f'G{account}',room_id=room)
        self.previous_room_id=None
        self.combat_mob_key=None
        self.resting=self.rest_task=False
        self.auto_fishing=self.auto_fishing_task=False
        self.auto_mining=self.auto_mining_task=False
        self.auto_woodcutting=self.auto_woodcutting_task=False
        self.auto_herbalism=self.auto_herbalism_task=False
        self.messages=[]
        self.party_id=account
    def normalize_room_query(self,text): return str(text or '').strip().lower()
    def party_key(self): return self.party_id
    def portal_requires_local_leader_v12811(self):
        return self.party_id != self.account_id and any(
            m is not self and m.character.room_id==self.character.room_id
            for m in self.server.group if m.party_id==self.party_id)
    async def send(self,text): self.messages.append(str(text))
    async def look(self): self.messages.append('LOOK:'+self.character.room_id)
    async def stop_rest(self,**kwargs): self.resting=False
    async def stop_auto_fishing(self,**kwargs): self.auto_fishing=False
    async def stop_auto_mining(self,**kwargs): self.auto_mining=False
    async def stop_auto_woodcutting(self,**kwargs): self.auto_woodcutting=False
    async def stop_auto_herbalism(self,**kwargs): self.auto_herbalism=False

class Server:
    def __init__(self):
        self.db=MemoryDB()
        self.group=[]
        self.world=SimpleNamespace(ensure_infinite_dungeon_floor=lambda _: True)
    def party_sessions(self,account, same_room=None):
        return [m for m in self.group if m.party_id==account
                and (same_room is None or m.character.room_id==same_room)]
    def session_by_account(self,account):
        return next((m for m in self.group if m.account_id==account), None)

async def _run_portal_checks():
    n=0
    for kind,start,origin_func,gate,cmd,low,high in [
        ('crypt',crypt_floor_id(30),crypt_floor_id,'crypt_hall','use_crypt_portal',10,20),
        ('mythic_crypt',mythic_crypt_floor_id(30),mythic_crypt_floor_id,'mythic_crypt_gate','use_crypt_portal',10,20),
        ('astral',astral_floor_id(150),astral_floor_id,'astral_gate','use_astral_portal',100,120),
        ('mythic_astral',mythic_astral_floor_id(30),mythic_astral_floor_id,'mythic_astral_gate','use_astral_portal',10,20),
    ]:
        srv=Server(); player=Dummy(srv,1,start)
        srv.group=[player];srv.db.floors[1,kind]={low,high,30 if kind!='astral' else 150}
        # From a cleared checkpoint -> another cleared checkpoint (not the gate).
        await getattr(player,cmd)(str(low))
        assert player.character.room_id==origin_func(low),(kind,player.messages)
        assert player.previous_room_id==start
        assert srv.db.saves[-1][1]==origin_func(low)
        n+=3
        # Go from a different checkpoint without first exiting the dungeon.
        await getattr(player,cmd)(str(high))
        assert player.character.room_id==origin_func(high),(kind,player.messages)
        n+=1
        # A locked checkpoint is inaccessible even from an unlocked one.
        position=player.character.room_id
        await getattr(player,cmd)(str(60 if kind!='astral' else 160))
        assert player.character.room_id==position
        assert any('zablokowany' in m for m in player.messages)
        n+=2
        # A not-yet-cleared source cannot be used as an origin, even if the
        # target checkpoint is unlocked; this is not arbitrary teleport.
        player.character.room_id=origin_func(40 if kind!='astral' else 140)
        await getattr(player,cmd)(str(low))
        assert player.character.room_id==origin_func(40 if kind!='astral' else 140)
        n+=1
        # Existing portal 'wyjdz' behavior unchanged on cleared checkpoint.
        player.character.room_id=origin_func(high)
        await getattr(player,cmd)('wyjdz')
        assert player.character.room_id==gate,(kind,player.messages)
        n+=1
        # From gate -> already unlocked destination works.
        await getattr(player,cmd)(str(high))
        assert player.character.room_id==origin_func(high)
        n+=1
        # Solo portal works even when party does not have a local co-member.
    # A local leader may teleport only party members with own unlocked target.
    srv=Server(); leader=Dummy(srv,1,crypt_floor_id(30))
    good=Dummy(srv,2,crypt_floor_id(30));bad=Dummy(srv,3,crypt_floor_id(30))
    srv.group=[leader,good,bad];good.party_id=bad.party_id=1
    for account,floors in [(1,{10,20,30}),(2,{10,20,30}),(3,{30})]:
        srv.db.floors[account,'crypt']=floors
    await leader.use_crypt_portal('20')
    assert leader.character.room_id==crypt_floor_id(20)
    assert good.character.room_id==crypt_floor_id(20)
    assert bad.character.room_id==crypt_floor_id(30)
    assert any('nieodblokowan' not in m.lower() for m in leader.messages)
    n+=4
    # Combat blocks both leader and every follower in the same room.
    leader.character.room_id=crypt_floor_id(30)
    good.character.room_id=crypt_floor_id(30)
    bad.character.room_id=crypt_floor_id(30)
    good.combat_mob_key='fighting'
    await leader.use_crypt_portal('10')
    assert leader.character.room_id==crypt_floor_id(10)
    assert good.character.room_id==crypt_floor_id(30)
    assert bad.character.room_id==crypt_floor_id(30)
    n+=3
    # Catacombs: normal visit (including historic character currently deep
    # within the dungeon) unlocks only this and earlier, not future levels.
    srv=Server(); cats=Dummy(srv,1,CATACOMB_LEVELS_V0900[2][5]);srv.group=[cats]
    cats.remember_catacomb_floor_v2010(cats.character.room_id)
    assert cats.catacomb_unlocked_floors_v2010()==[1,2]
    await cats.use_crypt_portal('3')
    assert cats.character.room_id==CATACOMB_LEVELS_V0900[2][5]
    await cats.use_crypt_portal('1')
    assert cats.character.room_id==CATACOMB_LEVELS_V0900[1][0]
    await cats.use_crypt_portal('2')
    assert cats.character.room_id==CATACOMB_LEVELS_V0900[2][0]
    await cats.use_crypt_portal('wyjdz')
    assert cats.character.room_id=='temple_basement_deep_nest'
    n+=5
    cats.character.room_id=CATACOMB_LEVELS_V0900[3][0]
    cats.remember_catacomb_floor_v2010(cats.character.room_id)
    assert cats.catacomb_unlocked_floors_v2010()==[1,2,3]
    n+=1
    # Regression of unintended new command from 2.00.9.
    assert 'pietro' not in COMMAND_REGISTRY
    n+=1
    return n

def run_regression():
    return asyncio.run(_run_portal_checks())

if __name__=='__main__':
    print(f'PORTALS v2.00.10: {run_regression()} checks PASS')
