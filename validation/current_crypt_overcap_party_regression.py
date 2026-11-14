# -*- coding: utf-8 -*-
"""Isolated real-logic regressions: crypt kill alias, live Over Cap bank, party feed.

No production database, no live port, no real player's data. These tests do not
replace the Windows PREDEPLOY 60/60 PLUS or a true six-player TCP trial.
"""
from __future__ import annotations
import asyncio
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def run():
    checks=0
    def check(condition, reason):
        nonlocal checks
        assert condition, reason
        checks+=1

    from world.dynamic_content import quest_kill_targets_v0389
    from data.mobs import MOB_TEMPLATES
    from data.quests import QUESTS
    from storage.database import _DeferredCommitConnection
    from systems.atomic_kill_quest_progress_v10400 import settle_kill_quest_progress_v10400
    quest = QUESTS['soul_tier_05_trial']
    check(quest['kind']=='kill' and quest['target']=='crypt_wraith',
          'unchanged authored soul-tier crypt quest')
    check('crypt_floor_mob_2' in MOB_TEMPLATES, 'real floor-two crypt mob exists')
    check('crypt_wraith' in quest_kill_targets_v0389('crypt_floor_mob_2', MOB_TEMPLATES['crypt_floor_mob_2']),
          'real wraith grants quest target alias')
    check('crypt_wraith' not in quest_kill_targets_v0389('crypt_floor_mob_3', MOB_TEMPLATES['crypt_floor_mob_3']),
          'other floor mobs are not broadly treated as wraiths')
    # Test the exact atomic kill-to-quest SQL path used by combat_rewards.py.
    raw=sqlite3.connect(':memory:')
    raw.row_factory=sqlite3.Row
    conn=_DeferredCommitConnection(raw)
    conn.execute('CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,PRIMARY KEY(account_id,quest_id))')
    conn.execute('INSERT INTO quests VALUES(101,?,?,0)',('soul_tier_05_trial','active'))
    conn.execute('INSERT INTO quests VALUES(102,?,?,0)',('soul_tier_05_trial','active'))
    conn.commit()
    class QuestDB:
        def __init__(self):self.conn=conn
        def increment_multi_objective_v1800(self,*args,**kw):return []
    db=QuestDB()
    aliases=quest_kill_targets_v0389('crypt_floor_mob_2', MOB_TEMPLATES['crypt_floor_mob_2'])
    for expected in range(1,int(quest['needed'])+1):
        simple,_ = settle_kill_quest_progress_v10400(db,101,'crypt_floor_mob_2',aliases=aliases)
        check(simple==[('soul_tier_05_trial',expected)],'exactly one quest step per real crypt kill')
        check(conn.execute('SELECT progress FROM quests WHERE account_id=101').fetchone()[0]==expected,
              'kill step saved to SQLite')
    check(settle_kill_quest_progress_v10400(db,101,'crypt_floor_mob_2',aliases=aliases)==([],[]),
          'quest cannot overcount after completion')
    check(conn.execute('SELECT progress FROM quests WHERE account_id=102').fetchone()[0]==0,
          'another account not credited')
    conn.commit();conn.close()

    from systems.experience_bank_v2011 import banked_experience_v2011
    from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
    class Bank(DatabaseExperienceBankV2011Mixin):
        def __init__(self,path):
            self.conn=sqlite3.connect(path)
            self.conn.execute('CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY)')
            self.conn.execute('INSERT OR IGNORE INTO accounts VALUES(101)')
            self.conn.commit()
            self.create_experience_bank_schema_v2011()
            self._v108_live_event_caps=True
        def multi_cap_v23215(self,account_id):
            return 100  # Controlled real-account Multi Cap; never override a real DB.

    times={'before':3600*100000+20*60,'during':3600*100000+35*60,
           'after':3600*100000+50*60}
    with tempfile.TemporaryDirectory(prefix='soulbound_v113_overcap_') as tmp:
        path=str(Path(tmp)/'test_bank.sqlite')
        bank=Bank(path)
        def award(amount,when,overcap=False):
            with patch('systems.v10800_seasonal_events.time.time',return_value=times[when]):
                return banked_experience_v2011(bank,101,amount,'class',10,
                                                source_key='Mec',overcap=overcap)
        def balance():
            return next((amount for kind,key,amount in bank.experience_bank_rows_v2011(101)
                         if kind=='class' and key=='Mec'),0)
        check(award(180,'before')==100,'outside event, 100 of 180 EXP actually paid')
        check(balance()==80,'80 surplus saved, not discarded')
        check(award(450,'during')==200,'event actually pays 200 > normal cap 100')
        check(balance()==330,'250 new surplus saved in bank during event')
        check(award(120,'during')==200,'event pays 80 old EXP in addition to 120 fresh')
        check(balance()==250,'bank repays only paid difference')
        check(award(180,'after')==100,'after event normal 100 cap returns')
        check(balance()==330,'new after-event surplus saved')
        with patch('systems.v10800_seasonal_events.time.time',return_value=times['during']):
            check(banked_experience_v2011(bank,101,450,'class',10,
                      source_key='Mec',overcap=True)==200,'boss overcap does not stack to x4')
        check(balance()==580,'boss surplus still persisted')
        bank.conn.close()
        bank=Bank(path)
        check(balance()==580,'surplus survives SQLite close and reopen')
        bank._v108_live_event_caps=False
        check(award(450,'during')==100,'offline staging cannot activate production event')
        check(balance()==930,'offline award surplus remains in bank')
        bank.conn.close()

        # Through the production atomic award gateway as well: EXP must reach
        # the durable mastery row, not stop at a positive bank return value.
        from systems.atomic_progression_rewards_v10400 import award_class_xp_atomic_v10400
        class AtomicBank(Bank):
            def __init__(self, path):
                super().__init__(path)
                self.conn=_DeferredCommitConnection(self.conn)
                self.conn.execute('CREATE TABLE class_progress(account_id INTEGER, class_name TEXT, xp INTEGER)')
                self.conn.execute('INSERT INTO class_progress VALUES(101,\"Mec\",0)')
                self.conn.commit()
            def add_class_mastery_xp(self,account_id,class_name,amount,single_level_cap=False):
                self.conn.execute('UPDATE class_progress SET xp=xp+? WHERE account_id=? AND class_name=?',
                                  (amount,account_id,class_name))
                self.conn.commit()
                return []
        atomic_path=str(Path(tmp)/'atomic.sqlite')
        atomic=AtomicBank(atomic_path)
        with patch('systems.v10800_seasonal_events.time.time',return_value=times['during']):
            paid,_=award_class_xp_atomic_v10400(atomic,101,'Mec',450,10)
        check(paid==200,'atomic event gateway actually pays EXP > normal cap')
        check(atomic.conn.execute('SELECT xp FROM class_progress').fetchone()[0]==200,
              'the paid event EXP reaches persistent mastery progression')
        check(atomic.experience_bank_rows_v2011(101)==[('class','Mec',250)],
              'atomic event payout banks the remaining EXP')
        atomic.conn.close()
        persisted=sqlite3.connect(atomic_path)
        check(persisted.execute('SELECT xp FROM class_progress').fetchone()[0]==200,
              'EXP remains earned after closing and reopening SQLite')
        persisted.close()

    # Exercise the real same-room, party-only delivery helper, not a fake
    # "send to all clients" test. The caster gets no duplicated party message.
    # Extract the exact method without importing server.py, whose activation
    # guard correctly forbids booting an unapproved release against SQLite.
    import ast
    tree=ast.parse((ROOT/'server/mud_server.py').read_text(encoding='utf-8'))
    owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MudServer')
    method=next(n for n in owner.body if isinstance(n,ast.AsyncFunctionDef)
                and n.name=='party_nearby_broadcast')
    scope={}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),
                 str(ROOT/'server/mud_server.py'),'exec'),scope)
    party_feed=scope['party_nearby_broadcast']
    class Player:
        def __init__(self,name,room):
            self.account_id=name
            self.character=SimpleNamespace(name=name,room_id=room)
            self.closed=False
            self.messages=[]
        async def send(self,text,**kwargs):self.messages.append((text,kwargs))
        async def send_combat(self,text,detail='essential'):
            await self.send(text,combat_detail=detail,history_category='combat')
    caster=Player('caster','crypt2')
    ally=Player('ally','crypt2')
    distant=Player('distant','temple')
    stranger=Player('stranger','crypt2')
    class PartyServer:
        party_nearby_broadcast=party_feed
        def party_key_for_account(self,account_id):
            return 'ourparty' if account_id in ('caster','ally','distant') else None
        def party_sessions(self,account_id,same_room=None):
            return [p for p in (caster,ally,distant,stranger)
                    if self.party_key_for_account(p.account_id)==self.party_key_for_account(account_id)
                    and (same_room is None or p.character.room_id==same_room)]
    srv=PartyServer()
    count=asyncio.run(srv.party_nearby_broadcast(caster,'Jammer: 1 zatrzymany',
                                                  exclude=[caster],detail='essential',
                                                  history_category='combat'))
    check(count==1,'exactly one online co-located teammate notified')
    check(len(ally.messages)==1 and ally.messages[0][1]['combat_detail']=='essential',
          'NVDA essential message reaches the teammate')
    check(not caster.messages and not stranger.messages and not distant.messages,
          'no duplicate to caster, no outsider or remote party spam')

    # Exercise the actual real-time Jammer decrement AST without changing the
    # source-protected v4.20 combat method. Trigger a callback through the
    # genuine server broadcaster with real room / party filtering.
    from copy import deepcopy
    combat_method=deepcopy(next(n for n in owner.body if isinstance(n,ast.AsyncFunctionDef)
                     and n.name=='party_combat_broadcast'))
    combat_method.decorator_list=[]  # remove performance decorator for isolated test
    scope={}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[combat_method],type_ignores=[])),
                 str(ROOT/'server/mud_server.py'),'exec'),scope)
    PartyServer.party_combat_broadcast=scope['party_combat_broadcast']
    caster.server=srv
    native=ast.parse((ROOT/'player/session_mixins/combat_realtime.py').read_text(encoding='utf-8'))
    owner_native=next(n for n in native.body if isinstance(n,ast.ClassDef)
                      and n.name=='SessionCombatRealtimeMixin')
    loop=next(n for n in owner_native.body if isinstance(n,ast.AsyncFunctionDef)
              and n.name=='realtime_combat_loop')
    block=next(n for n in ast.walk(loop) if isinstance(n,ast.If)
               and ast.unparse(n.test)=='_jammer_rounds > 0'
               and 'enemy_mob.v11196_jammer_stop_rounds' in ast.unparse(n))
    assign=next(n for n in ast.walk(loop) if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='_jammer_rounds' for t in n.targets)
                and 'v11196_jammer_stop_rounds' in ast.unparse(n.value))
    args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self'),ast.arg(arg='enemy_mob')],
                       kwonlyargs=[],kw_defaults=[],defaults=[],vararg=None,kwarg=None)
    simulation=ast.AsyncFunctionDef(name='real_jammer_tick',args=args,
            body=[ast.For(target=ast.Name(id='enemy_mob',ctx=ast.Store()),
              iter=ast.List(elts=[ast.Name(id='enemy_mob',ctx=ast.Load())],ctx=ast.Load()),
              body=[deepcopy(assign),deepcopy(block)],orelse=[])],
            decorator_list=[],returns=None,type_comment=None)
    scope={'MOB_TEMPLATES':{'test_upior':{'name':'Upiór Velsal'}}}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[simulation],type_ignores=[])),
                 str(ROOT/'player/session_mixins/combat_realtime.py'),'exec'),scope)
    tick=scope['real_jammer_tick']
    mob=SimpleNamespace(template_id='test_upior',v11196_jammer_stop_rounds=2)
    caster.messages.clear(); ally.messages.clear(); stranger.messages.clear(); distant.messages.clear()
    asyncio.run(tick(caster,mob))
    check(mob.v11196_jammer_stop_rounds==1,'one real mob action decrements Stop from two to one')
    check(not caster.messages and len(ally.messages)==1
          and 'Pozostało 1 akcji Stop' in ally.messages[0][0],
          'non-final action uses ordinary old combat feed, no early end notice')
    caster.messages.clear(); ally.messages.clear()
    asyncio.run(tick(caster,mob))
    end='Jammer na Upiór Velsal zakończył działanie.'
    check(mob.v11196_jammer_stop_rounds==0,'final real mob action expires Jammer')
    check([x[0] for x in caster.messages]==[end]
          and caster.messages[0][1].get('combat_detail')=='essential',
          'fighting player receives one audible, essential Jammer-end event')
    check([x[0] for x in ally.messages]==[end]
          and ally.messages[0][1].get('combat_detail')=='essential',
          'same-room party member receives exactly one essential Jammer-end event')
    check(not stranger.messages and not distant.messages,
          'foreign player and distant party member never hear expiration')
    asyncio.run(tick(caster,mob))
    check(len(caster.messages)==1 and len(ally.messages)==1,
          'expired Jammer cannot announce again on later mob actions')
    caster.messages.clear(); ally.messages.clear()
    asyncio.run(srv.party_combat_broadcast(caster,'Zwykłe obrażenia.',detail='normal'))
    check(not caster.messages and len(ally.messages)==1
          and ally.messages[0][0]=='Zwykłe obrażenia.',
          'ordinary combat messages keep original recipient behavior')
    caster.messages.clear(); ally.messages.clear()
    caster.account_id='solo'
    solo=SimpleNamespace(template_id='test_upior',v11196_jammer_stop_rounds=1)
    asyncio.run(tick(caster,solo))
    check(caster.messages and caster.messages[0][0]==end,
          'solo player receives end notice without being in any party')
    check(not ally.messages,'solo player does not leak announcement to former party')
    print(f'CURRENT CRYPT/OVER CAP/JAMMER PARTY/END: {checks}/{checks} PASS')

if __name__=='__main__':run()
