# -*- coding: utf-8 -*-
"""Static/source-and-live-helper regression; isolated in-memory SQLite only."""
from __future__ import annotations
import ast
import asyncio
from datetime import date,datetime
from pathlib import Path
import sqlite3
from unittest.mock import patch
from systems.v10800_seasonal_events import advent_day,advent_reward_silver,overcap_event_state
from core.bootstrap_economy_professions import double_xp_event_state
from systems.experience_bank_v2011 import banked_experience_v2011

ROOT = Path(__file__).resolve().parents[1]

class DB:
    def __init__(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''
        CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,silver INTEGER,gold INTEGER,mithril INTEGER);
        CREATE TABLE characters(account_id INTEGER PRIMARY KEY);
        CREATE TABLE account_characters(character_account_id INTEGER PRIMARY KEY,master_account_id INTEGER NOT NULL);
        INSERT INTO characters VALUES(11); INSERT INTO characters VALUES(12);
        INSERT INTO account_characters VALUES(11,1); INSERT INTO account_characters VALUES(12,1);
        INSERT INTO account_wallet VALUES(1,3000,0,0);
        ''')
        self.conn.commit()
        self.inject_error=False
    def master_account_for_character(self,aid):
        return self.conn.execute('SELECT master_account_id FROM account_characters WHERE character_account_id=?',(aid,)).fetchone()[0]
    def shared_wallet_for_master(self,master):
        r=self.conn.execute('SELECT silver,gold,mithril FROM account_wallet WHERE master_account_id=?',(master,)).fetchone()
        return tuple(r)
    def set_shared_wallet_for_master(self,master,silver,gold,mithril,*,commit=True):
        if self.inject_error:raise RuntimeError('Injected wallet failure')
        self.conn.execute('UPDATE account_wallet SET silver=?,gold=?,mithril=? WHERE master_account_id=?',(silver,gold,mithril,master))
        if commit:self.conn.commit()
    def apply_shared_wallet_to_character(self,character):
        character.silver=self.shared_wallet_for_master(self.master_account_for_character(character.account_id))[0]

class Session:
    def __init__(self,db,aid):
        self.server=type('S',(),{'db':db})()
        self.account_id=aid
        self.character=type('C',(),{'account_id':aid,'silver':0})()
        self.messages=[]
    async def send(self,text):self.messages.append(text)

async def _exercise_claims(claim):
    count=0
    def ck(condition,label):
        nonlocal count
        assert condition,label
        count+=1
    db=DB(); a=Session(db,11);b=Session(db,12)
    await claim(a,_today=date(2026,11,30))
    ck(db.shared_wallet_for_master(1)[0]==3000,'no November reward')
    ck(not db.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v108_advent_claims'").fetchone(),'no November schema mutation')
    await claim(a,_today=date(2026,12,1))
    ck(db.shared_wallet_for_master(1)[0]==4250,'first reward')
    ck(a.character.silver==4250,'character wallet mirror')
    await claim(a,_today=date(2026,12,1))
    ck(db.shared_wallet_for_master(1)[0]==4250,'same character double claim')
    await claim(b,_today=date(2026,12,1))
    ck(db.shared_wallet_for_master(1)[0]==4250,'alt double claim')
    await claim(b,_today=date(2026,12,2))
    ck(db.shared_wallet_for_master(1)[0]==5750,'second day')
    ck(db.conn.execute('SELECT COUNT(*) FROM v108_advent_claims').fetchone()[0]==2,'ledger two dates')
    db.inject_error=True
    error_observed = False
    try:
        await claim(a,_today=date(2026,12,3))
    except RuntimeError as exc:
        error_observed = str(exc) == 'Injected wallet failure'
    ck(error_observed,'injected wallet error propagates')
    ck(db.shared_wallet_for_master(1)[0]==5750,'rollback wallet error')
    ck(db.conn.execute('SELECT COUNT(*) FROM v108_advent_claims').fetchone()[0]==2,'rollback claim error')
    db.inject_error=False
    await claim(a,_today=date(2026,12,3))
    ck(db.shared_wallet_for_master(1)[0]==7500,'retry after rollback')
    await claim(a,_today=date(2027,1,1))
    ck(db.shared_wallet_for_master(1)[0]==17500,'January 1 included')
    await claim(a,_today=date(2027,1,2))
    ck(db.shared_wallet_for_master(1)[0]==17500,'January 2 excluded')
    db.conn.close()
    return count


def run():
    count=0
    def ck(cond,label):
        nonlocal count
        assert cond,label
        count+=1
    for m in range(60):
        sec = 3600*100000+m*60
        over=overcap_event_state(sec)
        double=double_xp_event_state(sec)
        ck(over['active']==(30<=m<45),f'overcap minute {m}')
        ck(double['active']==(m<15),f'double minute {m}')
        ck(not(over['active'] and double['active']),'events may not overlap')
        ck(over['multiplier']==(2 if 30<=m<45 else 1),'overcap multiplier')
    for m,remaining,start in [(0,0,1800),(29,0,60),(30,900,3600),(44,60,2760),(45,0,2700)]:
        st=overcap_event_state(3600*100000+m*60)
        ck(st['remaining_seconds']==remaining,f'remaining {m}')
        ck(st['next_start_seconds']==start,f'next {m}')
    for day in range(1,32):
        ck(advent_day(date(2026,12,day))==day,'December calendar')
        ck(advent_reward_silver(day)==1000+250*day,'December money')
    ck(advent_day(date(2027,1,1))==32,'January 1')
    ck(advent_reward_silver(32)==10000,'January gift')
    for d in (date(2026,11,30),date(2026,1,2),date(2027,1,2),date(2027,11,7)):
        ck(advent_day(d)==0,'out of window')
    for invalid in (-1,0,33,999):
        try:advent_reward_silver(invalid)
        except ValueError:count+=1
        else:raise AssertionError('Invalid day accepted')
    # Apply the real command method, transplanted via AST to avoid unrelated
    # side effects of loading massive session/catalog dependencies.
    tree=ast.parse((ROOT/'player/session_mixins/social_expansion.py').read_text(encoding='utf-8'))
    cl=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionSocialExpansionMixin')
    fn=next(n for n in cl.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='advent_v108')
    scope={'CURRENCY_SQLITE_SAFE_TOTAL':9_000_000_000_000_000_000,
           'currency_reading_text':lambda s,g,m:f'{s} srebra'}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(ROOT/'player/session_mixins/social_expansion.py'),'exec'),scope)
    fn=scope['advent_v108']
    # The function is unbound in this test; real SessionSocialExpansionMixin
    # provides it through Python MRO at runtime.
    count+=asyncio.run(_exercise_claims(fn))
    # EXP bank single cap: x2 during :30..:45 only, boss already overcap can't become x4.
    class Bank:
        def multi_cap_v23215(self,aid):return 100
        def allocate_experience_bank_v2011(self,aid,amount,kind,source,cap):return min(amount,cap)
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.execute('CREATE TABLE characters(account_id INTEGER)')
    bank=Bank()
    bank._v108_live_event_caps = True  # Real v108 runtime opts in.
    with patch('systems.v10800_seasonal_events.time.time',return_value=3600*100000+30*60):
        ck(banked_experience_v2011(bank,7,450,'class',1)==200,'event double cap')
        ck(banked_experience_v2011(bank,7,450,'class',1,overcap=True)==200,'boss not x4')
    with patch('systems.v10800_seasonal_events.time.time',return_value=3600*100000+16*60):
        ck(banked_experience_v2011(bank,7,450,'class',1)==100,'normal cap')
        ck(banked_experience_v2011(bank,7,450,'class',1,overcap=True)==200,'boss still x2')
    # Historical standalone databases remain deterministic even at :30.
    del bank._v108_live_event_caps
    with patch('systems.v10800_seasonal_events.time.time',return_value=3600*100000+30*60):
        ck(banked_experience_v2011(bank,7,450,'class',1)==100,
           'offline fixtures must not get live event cap')
        ck(banked_experience_v2011(bank,7,450,'class',1,overcap=True)==200,
           'explicit boss overcap remains enabled')
    bank.conn.close()
    # Read-only session pacing: real committed EXP/h (not theoretical grants).
    from systems.v10800_pacing_metrics import xp_per_hour,level_eta_seconds
    ck(xp_per_hour(3600,3600)==3600,'one hour rate')
    ck(xp_per_hour(100,600)==600,'ten minute rate')
    ck(xp_per_hour(0,1800)==0,'no rewards')
    ck(level_eta_seconds(2000,1000,3600)==7200,'ETA from committed rate')
    ck(level_eta_seconds(500,50,200) is None,'short session no ETA')
    ck(level_eta_seconds(500,0,1800) is None,'no gain no ETA')
    ck(level_eta_seconds(0,100,600)==0,'already reached threshold')
    # Extract real user command from its class and exercise with a fake
    # logged-in session. No player file, server or catalog is started.
    pacing_method=next(n for n in cl.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='tempo_exp_v108')
    pace_scope={'time':__import__('time')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[pacing_method],type_ignores=[])),
                 str(ROOT/'player/session_mixins/social_expansion.py'),'exec'),pace_scope)
    pace_fn=pace_scope['tempo_exp_v108']
    class PaceSession:
        character=type('Char',(),{'character_level':10,'character_xp':0})()
        _session_summary={'started_at':0, 'character_xp':1000,'class_xp':400,
                          'soul_xp':600,'stat_xp':30,'soul_weapon_mastery_xp':20,
                          'profession_xp':{'Górnictwo':200},'tool_xp':{'mining':100}}
        messages=[]
        async def send(self,msg):self.messages.append(msg)
        def format_duration_short(self,seconds):return f'{seconds}s'
    with patch.object(pace_scope['time'],'time',return_value=600.0):
        asyncio.run(pace_fn(PaceSession()))
    result=PaceSession.messages[-1]
    ck('TEMPO EXP' in result and '6000 EXP/h' in result,'live pace actual paid')
    ck('statystyki z walk' in result and '180 EXP/h' in result,'stat xp pace')
    ck('profesje: 1200 EXP/h' in result,'profession xp pace')
    ck('narzędzia: 600 EXP/h' in result,'tool xp pace')
    ck('do następnego poziomu' in result,'remaining xp display')
    # Command names registered in actual router. No invented alias conflicts.
    from player.session_mixins.command_registry import COMMAND_REGISTRY,resolve_session_command
    ck(COMMAND_REGISTRY['adwent'][0]=='advent_v108','command exists')
    ck(COMMAND_REGISTRY['tempoexp'][0]=='tempo_exp_v108','pacing command exists')
    ck(resolve_session_command('prezent')=='adwent','gift alias')
    ck(COMMAND_REGISTRY['eventxp'][0]=='show_double_xp_event','existing event status')
    return count

if __name__=='__main__':
    print('V108 KALENDARZ ADWENT OVERCAP I PORTFEL:',run(),'PASS',flush=True)
