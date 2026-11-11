# -*- coding: utf-8 -*-
"""v108: real handler regressions for user-reported v107 gaps. Offline only."""
from __future__ import annotations
import asyncio
import tempfile
from pathlib import Path
from types import SimpleNamespace

from player.session_mixins.io_auth_character import SessionIOAuthCharacterMixin
from player.session_mixins.dungeon_progression import SessionDungeonProgressionMixin
from player.session_mixins.quest_turnin import SessionQuestTurninMixin
from player.session_mixins.command_registry import resolve_session_command
from player.session_mixins.movement import SessionMovementMixin
from core.classes_skills import RACES, CLASSES
from core.mine_tunnels import mine_tunnel_room_id
from storage.db_inventory import DatabaseInventoryMixin
from validation.v10700_production_eq_cutover_regression import DB, seed, CAT
from systems.v10700_live_equipment import activate_production_ledger
import systems.v10700_activation as act


def run():
    checked=0
    def ck(condition, reason):
        nonlocal checked
        assert condition,reason
        checked+=1

    class Creator:
        def __init__(self, cmd):
            self.inputs=iter(['TestPostac108',cmd,'1'])
            self.picks=iter(['kobieta', RACES[0],RACES[1]])
            self.output=[]
            self.server=SimpleNamespace(db=SimpleNamespace(character_name_exists=lambda _:False))
        async def ask(self, prompt):return next(self.inputs)
        async def choose_number(self, items, prompt):return next(self.picks)
        async def ask_name_declension(self,name):return None
        async def send(self, text):self.output.append(text)
    for cmd in ('0','wroc','wróć','rasy'):
        c=Creator(cmd)
        ck(asyncio.run(SessionIOAuthCharacterMixin.character_creator(c)) is False,
           'creator aborted only at declined grammatical forms '+cmd)
        ck(c.output.count('Wybierz rasę:')==2,'race menu did not repeat '+cmd)
        ck(any('Powrót do listy ras' in line for line in c.output),'no NVDA feedback '+cmd)
        ck(any('22 klas' in line for line in c.output), 'class count stale '+cmd)
    ck(resolve_session_command('gigantportal','10')=='gigantportal','fortress command missing')
    ck(resolve_session_command('portal','10')=='portal','legacy portal broken')

    class DummyDB:
        def __init__(self, clears):self.clears=clears;self.moved=[]
        def instance_checkpoint_floors(self, account,kind):
            return set(self.clears.get(account,set())) if kind=='giant' else set()
        def save_character(self,character):self.moved.append(character.room_id)
    class Portal:
        use_giant_fortress_portal_v10800=SessionDungeonProgressionMixin.use_giant_fortress_portal_v10800
        checkpoint_portal_floors_v11331=SessionDungeonProgressionMixin.checkpoint_portal_floors_v11331
        checkpoint_portal_unlocked_v11331=SessionDungeonProgressionMixin.checkpoint_portal_unlocked_v11331
        def __init__(self,db,account=1,room='giant_fortress_gate'):
            self.account_id=account
            self.character=SimpleNamespace(room_id=room,name='Gracz'+str(account))
            self.server=SimpleNamespace(db=db,world=SimpleNamespace(ensure_runtime_room=lambda _:None),
                                        party_sessions=lambda *a,**k:[self])
            self.current_hp=100;self.moving=False;self.guiding=False;self.combat_mob_key=None
            self.resting=False;self.rest_task=None;self.auto_mining=False;self.auto_mining_task=None
            self.auto_fishing=False;self.auto_fishing_task=None
            self.auto_woodcutting=False;self.auto_woodcutting_task=None
            self.auto_herbalism=False;self.auto_herbalism_task=None
            self.output=[];self.looks=0;self.previous_room_id=None
        def normalize_room_query(self,s):return str(s).strip().casefold()
        def is_downed_v0371(self):return False
        def party_key(self):return self.account_id
        def portal_requires_local_leader_v12811(self):return False
        async def show_checkpoint_portal_status_v11331(self,**kwargs):
            await self.send('Checkpointy '+str(self.checkpoint_portal_floors_v11331(kwargs['kind'])))
        async def party_checkpoint_portal_exit_v11331(self,**kwargs):
            self.character.room_id=kwargs['target_room']
            await self.send('Portal wyjście')
        async def stop_auto_mining(self,**kwargs):self.auto_mining=False
        async def stop_auto_fishing(self,**kwargs):self.auto_fishing=False
        async def stop_auto_woodcutting(self,**kwargs):self.auto_woodcutting=False
        async def stop_auto_herbalism(self,**kwargs):self.auto_herbalism=False
        async def stop_rest(self,**kwargs):self.resting=False
        async def send(self,text):self.output.append(text)
        async def look(self):self.looks+=1
    db=DummyDB({1:{10}})
    p=Portal(db)
    asyncio.run(p.use_giant_fortress_portal_v10800('20'))
    ck(p.character.room_id=='giant_fortress_gate','unearned checkpoint allowed')
    asyncio.run(p.use_giant_fortress_portal_v10800('10'))
    ck(p.character.room_id=='giant_fortress_10','earned checkpoint rejected')
    ck(p.looks==1 and p.previous_room_id=='giant_fortress_gate','NVDA room / rollback state')
    asyncio.run(p.use_giant_fortress_portal_v10800('wyjdz'))
    ck(p.character.room_id=='giant_fortress_gate','fortress exit rejected')
    p.character.room_id='giant_fortress_5'
    asyncio.run(p.use_giant_fortress_portal_v10800('10'))
    ck(p.character.room_id=='giant_fortress_5','portal allowed from uncleared regular floor')
    p.character.room_id='giant_fortress_gate'
    p.auto_mining=True
    asyncio.run(p.use_giant_fortress_portal_v10800('10'))
    ck(not p.auto_mining,'portal moved player without stopping mining')
    p2=Portal(db,account=2)
    p.character.room_id='giant_fortress_gate'
    p.server.party_sessions=lambda *args,**kwargs:[p,p2]
    asyncio.run(p.use_giant_fortress_portal_v10800('10'))
    ck(p.character.room_id=='giant_fortress_10' and p2.character.room_id=='giant_fortress_gate',
       'unearned teammate got carried')
    ck(any('nie zaliczono bossa' in line for line in p.output),'missing personal unlock feedback')
    # Return portal must not carry an ineligible/working teammate home.
    db.clears[2]={10}
    p2.character.room_id='giant_fortress_10'
    p2.moving=True
    asyncio.run(p.use_giant_fortress_portal_v10800('wyjdz'))
    ck(p.character.room_id=='giant_fortress_gate', 'boss checkpoint return blocked')
    ck(p2.character.room_id=='giant_fortress_10', 'moving teammate was forced through exit')
    p.character.room_id='giant_fortress_10'
    p2.moving=False
    p2.auto_mining=True
    asyncio.run(p.use_giant_fortress_portal_v10800('wyjdz'))
    ck(p.character.room_id=='giant_fortress_gate' and p2.character.room_id=='giant_fortress_gate',
       'cleared party could not return to gate')
    ck(not p2.auto_mining, 'teammate mining continued after portal exit')
    # Even if party_sessions returns stale records, never pull a player
    # from a different room into a fortress checkpoint.
    remote = Portal(db, account=2, room='crystal_chamber')
    remote.auto_mining=True
    p.character.room_id='giant_fortress_gate'
    p.server.party_sessions=lambda *args,**kwargs:[p,remote]
    asyncio.run(p.use_giant_fortress_portal_v10800('10'))
    ck(remote.character.room_id=='crystal_chamber',
       'stale remote party member was teleported')
    ck(remote.auto_mining, 'remote player auto mining was wrongly stopped')
    ck(any('nie jest przy portalu' in line for line in p.output),
       'no NVDA feedback for remote party member')

    class Mine:
        dungeon_exit_destination=SessionMovementMixin.dungeon_exit_destination
        dungeon_exit=SessionMovementMixin.dungeon_exit
        def __init__(self,room,account=1):
            self.account_id=account;self.character=SimpleNamespace(room_id=room,name='Górnik')
            self.auto_mining=True;self.auto_mining_task=None;self.combat_mob_key=None
            self.current_hp=100;self.moving=False;self.guiding=False
            self.previous_room_id=None;self.output=[];self.stops=0
            self.server=SimpleNamespace(db=SimpleNamespace(save_character=lambda c:None),
                 party_sessions=lambda *a,**k:[self],broadcast_room=self.broadcast)
        def party_key(self):return self.account_id
        async def broadcast(self,*args,**kwargs):pass
        async def send(self,text):self.output.append(text)
        async def stop_auto_mining(self,**kwargs):self.stops+=1;self.auto_mining=False
        async def look(self):pass
        def is_downed_v0371(self):return False
    mine=Mine(mine_tunnel_room_id(5,1,2,3))
    ck(mine.dungeon_exit_destination()==('crystal_chamber','Kopalnia Głębinowa'),
       'exit does not recognize personally dug tunnels')
    asyncio.run(mine.dungeon_exit())
    ck(mine.character.room_id=='crystal_chamber' and mine.stops==1,
       'mine exit left auto mining enabled')
    ck(any('Auto-kopanie wyłączone' in line for line in mine.output),'no NVDA mining announcement')
    foreign=Mine(mine_tunnel_room_id(5,9,1,1))
    ck(foreign.dungeon_exit_destination() is None,'another player tunnel treated as personal')
    # Active movement/guide and downed leader must never be teleported.
    # A rejected exit must not stop mining or mutate the character's room.
    for state in ('moving', 'guiding', 'current_hp', 'downed'):
        blocked=Mine(mine_tunnel_room_id(5,1,2,4))
        if state == 'current_hp':
            blocked.current_hp=0
        elif state == 'downed':
            blocked.is_downed_v0371=lambda: True
        else:
            setattr(blocked,state,True)
        room_before=blocked.character.room_id
        ck(asyncio.run(blocked.dungeon_exit()) is False,
           'mine exit did not reject state '+state)
        ck(blocked.character.room_id==room_before and blocked.stops==0 and blocked.auto_mining,
           'mine exit mutated a blocked player '+state)
        ck(any('wyjści' in line.casefold() or 'powalona' in line.casefold()
               for line in blocked.output), 'no readable rejection '+state)

    # Actual production-style per-instance ledger is activated ONLY on a temp
    # SQLite copy, and a temporary monkeypatch is restored in finally.
    original=act.production_approved
    with tempfile.TemporaryDirectory(prefix='sb108-quest-eq-') as temporary:
        path=Path(temporary)/'TEST_ONLY.sqlite'
        eqdb=DB(path)
        seed(eqdb)
        try:
            act.production_approved=lambda:True
            ck(activate_production_ledger(eqdb,CAT),'isolated EQ ledger activation')
            try:
                eqdb.consume_items_across_storage_and_inventory(1,('helm',),1,purpose='craft')
            except RuntimeError:
                checked+=1
            else:
                raise AssertionError('legacy crafting consumed physical EQ')
            ck(eqdb.consume_items_across_storage_and_inventory(1,('helm',),1,purpose='quest_turnin'),
               'quest cannot consume normal untouched EQ')
            ck(eqdb.item_qty(1,'helm')==1,'quest removed more than one gear copy')
            ck(not eqdb.consume_items_across_storage_and_inventory(1,('helm',),1,purpose='quest_turnin'),
               'quest consumed equipped EQ')
            ck(eqdb.conn.execute('SELECT COUNT(*) FROM v106_equipped_instances').fetchone()[0]==1,
               'equipped ledger lost identity')
            eqdb.add_item(1,'cloth',2)
            dbsess=SimpleNamespace(server=SimpleNamespace(db=eqdb),account_id=1,
                 resource_quest_equivalent_ids=lambda iid:{iid},resource_quest_container=lambda iid:None)
            fail=SessionQuestTurninMixin.consume_quest_items_batch_v10800(dbsess,
                            [('cloth',1,'resource'),('NOT_THERE',1,'resource')])
            ck(fail is False,'partial turnin unexpectedly succeeded')
            ck(eqdb.item_qty(1,'cloth')==2,'partial turnin lost earlier consumed resource')
            success=SessionQuestTurninMixin.consume_quest_items_batch_v10800(dbsess,
                            [('cloth',1,'resource'),('cloth',1,'resource')])
            ck(success and eqdb.item_qty(1,'cloth')==0,'multi-item batch failed to commit')
            eqdb.add_item(1,'cloth',3)
            fail = SessionQuestTurninMixin.consume_quest_items_batch_v10800(dbsess,
                        [('cloth',1,'resource'),('helm',1,'resource')])
            ck(not fail and eqdb.item_qty(1,'cloth')==3,
               'equipped physical EQ failed to abort entire quest batch')
            success = SessionQuestTurninMixin.consume_quest_items_batch_v10800(dbsess,
                        [(('cloth',),2,'resource_ids',None)])
            ck(success and eqdb.item_qty(1,'cloth')==1,
               'category collect resource_ids batch did not consume exactly needed')
            ck(eqdb.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok',
               'temporary SQLite failed integrity check')
        finally:
            act.production_approved=original
            eqdb.conn.close()
    return checked

if __name__=='__main__':
    print('SOULBOUND V108: ODZYSKANE POPRAWKI',run(),'KONTROLI PASS, KOD ROBOCZY, NIE WDRAŻAĆ',flush=True)
