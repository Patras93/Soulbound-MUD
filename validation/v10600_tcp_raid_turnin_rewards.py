# -*- coding: utf-8 -*-
"""v106: real TCP quest claim and durable rewards, 1–6 player scenario.

All data are synthetic. Child is localhost-only, private port and SQLite.
This is NOT a natural kill, live-character migration or Windows PREDEPLOY.
"""
from __future__ import annotations
import asyncio
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from validation.v2102_tcp_six_players import (TcpPlayer,guarded_child_env,
                                        free_local_port,wait_for_world_server,_stop_child)
ROOT=Path(__file__).resolve().parents[1]
CASES=((26,1,1),(26,2,1),(26,3,1),(35,3,1),(26,1,0))

async def scenario(port):
    checks=0
    clients=[TcpPlayer(f'turnin106{i:02d}',f'Turnin106{i:02d}',port)
             for i in range(1,len(CASES)+1)]
    try:
        for client in clients:
            await client.connect_and_login()
            checks+=1
        from world.v10600_raids_26_35 import RAID_ROWS
        for client,(raid,stage,ready) in zip(clients,CASES):
            qname=f'Rajd {raid}: {RAID_ROWS[raid-26][2]}, etap {stage}/3'
            # Genuine player command to a real NPC in the quest-giver room.
            answer=await client.command('oddaj '+qname,quiet=.5)
            if ready:
                assert 'Zadanie ukończone:' in answer,(client.name,answer[-1200:])
            else:
                assert 'nie jest jeszcze gotowe' in answer,(client.name,answer[-1200:])
            checks+=1
            # Repeated request must not award money/items or complete twice.
            repeat=await client.command('oddaj '+qname,quiet=.4)
            assert 'Zadanie ukończone:' not in repeat,(client.name,repeat[-650:])
            checks+=1
        for client in clients:
            await client.send('quit')
        await asyncio.sleep(1)
        return checks
    finally:
        await asyncio.gather(*(c.close() for c in clients),return_exceptions=True)

def run():
    assert os.environ.get('SOULBOUND_V106_STAGING')!='1', 'Parent must not use staging.'
    with tempfile.TemporaryDirectory(prefix='soulbound-v106-turnin-') as directory:
        work=Path(directory); port=free_local_port()
        env,_=guarded_child_env(work,port)
        env.update(SOULBOUND_DB=str(work/'raid_turnin.sqlite'),
                   SOULBOUND_V106_STAGING='1',SOULBOUND_V106_TURNIN_TEST='1',
                   SOULBOUND_MAX_CLIENTS=str(len(CASES)),PYTHONPATH=str(ROOT))
        env.pop('SOULBOUND_ADMIN_ACCOUNTS',None)
        proc=None;log=work/'server.log'
        try:
            with log.open('w',encoding='utf8') as out:
                proc=subprocess.Popen([sys.executable,'-B','-u',
                     str(ROOT/'validation/v10600_tcp_raid_turnin_child.py')],
                    cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=out,
                    stderr=subprocess.STDOUT)
                wait_for_world_server(proc,log,seconds=180)
                checks=asyncio.run(scenario(port))
            _stop_child(proc);proc=None
            with closing(sqlite3.connect(work/'raid_turnin.sqlite',timeout=5)) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
                for i,(raid,stage,ready) in enumerate(CASES,1):
                    qid=f'v10600_raid_{raid}_quest_{stage}'
                    row=db.execute('''SELECT q.status,q.progress,q.completion_count,c.silver
                              FROM quests q JOIN characters c ON c.account_id=q.account_id
                              JOIN accounts a ON a.id=q.account_id
                              WHERE a.username=? AND q.quest_id=?''',
                              (f'turnin106{i:02d}',qid)).fetchone()
                    assert row,(i,qid)
                    status,progress,count,silver=row
                    assert (status,count)==(('completed',1) if ready else ('active',0)),(i,row)
                    checks+=1
                    qty=db.execute('''SELECT COALESCE(SUM(st.quantity),0)
                           FROM profession_storage st JOIN accounts a ON a.id=st.account_id
                           WHERE a.username=? AND st.container='craftbox' AND st.item_id=?''',
                           (f'turnin106{i:02d}',f'v10600_raid_{raid}_fragment')).fetchone()[0]
                    assert qty==(1 if ready else 0),(i,qty,ready)
                    checks+=1
                    if ready:
                        assert silver>0,(i,silver)
                        checks+=1
            trace=log.read_text(encoding='utf8',errors='replace')
            assert 'Traceback (most recent call last)' not in trace,trace[-1500:]
            checks+=1
            print(f'V106 TCP QUEST ODDANIE RAJD 26/35, ETAPY 1–3: {checks} PASS; '
                  '4 wypłaty, 1 odrzucona, 0 podwójnych nagród; trwały SQLite.',flush=True)
            return checks
        except BaseException:
            if log.exists():print('RAJD ODDANIE LOG: '+log.read_text(encoding='utf8',errors='replace')[-2200:],flush=True)
            raise
        finally:_stop_child(proc)

if __name__=='__main__':run()
