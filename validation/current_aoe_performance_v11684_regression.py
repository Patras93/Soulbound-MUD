# -*- coding: utf-8 -*-
"""Physical EQ bulk checks and command fairness, on disposable fixtures only."""
import ast
import asyncio
import os
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from core.perf_diagnostics_v11320 import begin, finish, current, note_sql, performance_phase
from systems.equipment_evolution_stats_v10600 import equipped_evolution_stage
from systems.equipment_shadow_slots_v10600 import equipped_copies_v11684


def run():
    checks=0
    def ck(condition,label):
        nonlocal checks
        assert condition,label
        checks+=1
    con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row
    con.executescript('''CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT,PRIMARY KEY(account_id,slot));
    CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER,PRIMARY KEY(account_id,item_id));
    CREATE TABLE v106_item_instances(instance_id TEXT PRIMARY KEY,account_id INTEGER,item_id TEXT,evolution_stage INTEGER);
    CREATE TABLE v106_equipped_instances(account_id INTEGER,slot TEXT,instance_id TEXT UNIQUE,PRIMARY KEY(account_id,slot));
    CREATE TABLE v106_stored_instances(instance_id TEXT PRIMARY KEY,account_id INTEGER,storage_kind TEXT,container TEXT);
    INSERT INTO inventory VALUES(1,'gear',12),(2,'gear',1);
    INSERT INTO equipment VALUES(2,'body','gear');
    INSERT INTO v106_item_instances VALUES('foreign',2,'gear',4);
    INSERT INTO v106_equipped_instances VALUES(2,'body','foreign');''')
    slots=[f'slot{i}' for i in range(12)]
    con.executemany('INSERT INTO equipment VALUES(1,?,\'gear\')',[(s,) for s in slots])
    con.executemany('INSERT INTO v106_item_instances VALUES(?,1,\'gear\',?)',[(s,i%11) for i,s in enumerate(slots)])
    con.executemany('INSERT INTO v106_equipped_instances VALUES(1,?,?)',[(s,s) for s in slots])
    con.executemany('INSERT INTO v106_item_instances VALUES(?,1,\'gear\',0)',[(f'bank{i}',) for i in range(600)])
    con.executemany('INSERT INTO v106_stored_instances VALUES(?,1,\'bank\',\'\')',[(f'bank{i}',) for i in range(600)])
    con.commit()
    db=SimpleNamespace(conn=con,_v106_shadow_slots_disposable_copy=True,_v106_shadow_item_catalog={'gear':{'type':'armor'}})
    trace=[];con.set_trace_callback(trace.append)
    def stages(snapshot):return [equipped_evolution_stage(db,1,s,'gear',read_snapshot=snapshot) for s in slots]
    with patch.dict(os.environ,{'SOULBOUND_V106_STAGING':'1'}):
        before=con.total_changes
        trace.clear();original=stages(None);single=len(trace)
        trace.clear();bulk=stages({});batched=len(trace)
        ck(original==bulk==[i%11 for i in range(12)],'exact per-copy stages')
        ck(single==72 and batched==6,'one audit per calculation')
        trace.clear()
        for i in range(50):assert stages({})==original
        ck(len(trace)==300,'50 independent target calculations')
        ck(con.total_changes==before and not con.in_transaction,'read-only')
        snapshot={};stages(snapshot)
        ck(equipped_evolution_stage(db,2,'body','gear',read_snapshot=snapshot)==4,'account separation')
        con.execute("UPDATE v106_item_instances SET evolution_stage=10 WHERE instance_id='slot0'");con.commit()
        ck(stages({})[0]==10,'fresh snapshot sees changed copy')
        def bad(sql,expected):
            con.execute('SAVEPOINT corrupt');con.execute(sql)
            try:
                stages({})
            except (RuntimeError,ValueError) as exc:ck(expected in str(exc),str(exc))
            else:raise AssertionError('corruption accepted: '+sql)
            finally:
                con.execute('ROLLBACK TO corrupt');con.execute('RELEASE corrupt')
        bad("UPDATE inventory SET quantity=11 WHERE account_id=1",'liczba kopii')
        bad("UPDATE v106_item_instances SET account_id=2 WHERE instance_id='bank0'",'magazyn wskazuje')
        bad("DELETE FROM v106_item_instances WHERE instance_id='bank0'",'magazyn wskazuje')
        bad("INSERT INTO v106_stored_instances VALUES('slot0',1,'bank','')",'założona sztuka')
        bad("DELETE FROM equipment WHERE slot='slot0' AND account_id=1",'nie są zgodne')
        bad("UPDATE v106_item_instances SET account_id=2 WHERE instance_id='slot0'",'cudzą')
        bad("UPDATE v106_item_instances SET evolution_stage=99 WHERE instance_id='slot0'",'etap ewolucji')
        ck(len(equipped_copies_v11684(con,1,db._v106_shadow_item_catalog))==12,'valid state restored')
    con.close()
    scope,token=begin('use')
    try:
        with performance_phase('kill_rewards'):
            note_sql(.001)
            with performance_phase('eq_ledger'):note_sql(.002)
        ck(scope.phases['kill_rewards'][2:]==(2,0),'inclusive rewards count')
        ck(scope.phases['eq_ledger'][2:]==(1,0),'ledger count')
    finally:finish(scope,token,minimum=100)
    ck(current() is None,'scope restored')
    # Execute exact command loop with buffered input and non-suspending dispatch.
    src=Path(__file__).resolve().parents[1]/'player/session_mixins/command_loop.py'
    node=next(n for n in ast.parse(src.read_text('utf8')).body if isinstance(n,ast.ClassDef))
    node.body=[n for n in node.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='command_loop']
    env=dict(time=time,sqlite3=sqlite3,COMMAND_LOOP_BREAK=object(),DIRECTION_ALIASES={},resolve_session_command=lambda token,args:token,command_state_safe=lambda *a:True)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),'exec'),env)
    class Actor(env[node.name]):
        closed=False;guide_choice_state=None;resting=False
        def __init__(self):self.server=SimpleNamespace(db=SimpleNamespace());self.count=0
        async def read_line(self):return 'use x' if self.count<30 else None
        def smelt_task_active_v1124(self):return False
        def is_downed_v0371(self):return False
        def guide_task_active(self):return False
        async def try_dungeon_entry_command_v03812(self,raw):return False
        async def dispatch_registered_command(self,command,args):self.count+=1;return True
    async def fairness():
        a=Actor();seen=[]
        async def observer():
            while a.count<30:
                seen.append(a.count);await asyncio.sleep(0)
        async def alias(self,raw):return False,raw
        with patch('systems.player_aliases.process_alias_input',alias):
            t=asyncio.create_task(observer());await a.command_loop();await t
        ck(a.count==30,'all queued commands executed')
        ck(len(set(seen))>=29,'other tasks run between queued commands')
    asyncio.run(fairness())
    print(f'AOE PERFORMANCE v11684: {checks}/{checks} PASS; per-slot SQL {single}->{batched}; 50 independent snapshots: 300 SQL',flush=True)
    return checks

if __name__=='__main__':run()
