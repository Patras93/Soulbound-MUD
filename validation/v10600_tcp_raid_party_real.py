# -*- coding: utf-8 -*-
"""Prawdziwy localhost TCP, 3/6 sesji, zespół i podział zabicia rajdu v106.

To NIE jest naturalny pomiar DPS/czasu walki. Zwycięstwo wywołuje kanoniczną
ścieżkę mob_defeated przez jawny atak admina na WYŁĄCZNIE testowym serwerze.
"""
from __future__ import annotations
import argparse
import asyncio
from contextlib import suppress, closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time

from validation.v2102_tcp_six_players import (
    TcpPlayer,guarded_child_env,free_local_port,wait_for_world_server,_stop_child)

ROOT=Path(__file__).resolve().parents[1]

async def observe(player,cmd,predicate,tries=4):
    outputs=[]
    for _ in range(tries):
        res=await player.command(cmd,quiet=.26)
        outputs.append(res)
        if predicate(res):return res
        await asyncio.sleep(.28)
    raise AssertionError(f'{player.name}: {cmd!r} brak odpowiedzi: {outputs[-1][-550:]!r}')

async def scenario(port,count,raid):
    players=[TcpPlayer(f'raid106{i:02d}',f'Raid106{i:02d}',port)
             for i in range(1,count+1)]
    checks=0
    try:
        for player in players:
            await player.connect_and_login()
            checks+=1
            print(f'RAJD TCP login {player.name}/{count}',flush=True)
        leader=players[0]
        expected=f'Rajd {raid}'
        for player in (players[0],players[-1]):
            r=await observe(player,'look',lambda text:expected in text)
            assert expected in r; checks+=1
        status=await observe(leader,'druzyna limit',lambda text:'28' in text)
        assert '28' in status,status;checks+=1
        status=await observe(leader,'druzyna zaloz',lambda text:'Zakładasz drużynę' in text)
        checks+=1
        for member in players[1:]:
            result=await observe(leader,'druzyna zapros '+member.name,
                lambda text,n=member.name:n in text and 'Zapraszasz' in text)
            checks+=1
            result=await observe(member,'dolacz',
                lambda text:'dołącza do drużyny' in text or 'do drużyny' in text)
            checks+=1
        party=await observe(leader,'druzyna',lambda text:players[-1].name in text)
        assert all(x.name in party for x in (players[0],players[-1])),party[-1200:]
        checks+=1
        await observe(leader,'admin status',lambda text:'Administrator: TAK' in text)
        await observe(leader,'admin god on',lambda text:'GOD WLACZONY' in text)
        checks+=2
        # A low-level test account must explicitly disable newbie protection
        # before engaging the real encounter; this is a test-only decision.
        await observe(leader,'newbieprotect off',lambda t:'wyłączone' in t.casefold())
        checks+=1
        # God/wyrok is a test strike, NOT naturally played combat. The real
        # mob_defeated handler must then distribute party quest credit.
        boss='Strażnik Progu'
        # Test child binds only the synthetic leader to the real boss;
        # preserve actual production victory/quest/reward code unchanged.
        strike=await leader.command('admin cios wyrok '+boss,quiet=.7)
        strike+=await leader.drain_idle(quiet=.65,total=5)
        print('RAJD TCP cios, fragment:',repr(strike[-550:]),flush=True)
        if 'ADMIN CIOS' not in strike:
            raise AssertionError('admin strike did not reach real combat: '+strike[-1000:])
        checks+=1
        for _ in range(5):
            state=await leader.command('look',quiet=.25)
            if 'NPC:' in state or 'Rajd' in state:break
            await asyncio.sleep(.3)
        # Do not trust notifications: database is checked for EVERY recipient after stop.
        print('RAJD TCP: sprawdzono komendy i kanoniczne uderzenie testowe',flush=True)
        return checks
    finally:
        await asyncio.gather(*(p.close() for p in players),return_exceptions=True)

def run(count=6,raid=26):
    assert count in (3,6) and raid in (26,35)
    assert os.environ.get('SOULBOUND_V106_STAGING')!='1','rodzic nie uruchamia staging globalnie'
    with tempfile.TemporaryDirectory(prefix='soulbound-v106-raid-party-') as directory:
        work=Path(directory)
        port=free_local_port()
        env,path=guarded_child_env(work,port)
        path=work/'raid_party.sqlite'
        env['SOULBOUND_DB']=str(path)
        env.update(SOULBOUND_V106_STAGING='1',SOULBOUND_V106_RAID_PARTY_TEST='1',
            SOULBOUND_V106_RAID_PARTY_COUNT=str(count),
            SOULBOUND_V106_RAID_PARTY_RAID=str(raid),
            SOULBOUND_MAX_CLIENTS=str(count),
            SOULBOUND_ADMIN_ACCOUNTS='raid10601',
            PYTHONPATH=str(ROOT))
        proc=None;log=work/'raid_party.log'; checks=0
        try:
            with log.open('w',encoding='utf-8') as sink:
                proc=subprocess.Popen([sys.executable,'-B','-u',
                    str(ROOT/'validation/v10600_tcp_raid_party_child.py')],
                    env=env,cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=sink,stderr=subprocess.STDOUT)
                wait_for_world_server(proc,log,seconds=210)
                print(f'RAJD {raid} TCP {count} graczy, serwer gotowy',flush=True)
                checks=asyncio.run(scenario(port,count,raid))
            _stop_child(proc);proc=None
            with closing(sqlite3.connect(path)) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
                records=db.execute('''SELECT a.username,q.status,q.progress,q.completion_count
                    FROM quests q JOIN accounts a ON a.id=q.account_id
                    WHERE q.quest_id=? ORDER BY a.username''',
                    (f'v10600_raid_{raid}_quest_1',)).fetchall()
                assert len(records)==count,(len(records),records)
                checks+=1
                for name,status,progress,completions in records:
                    assert status=='active' and progress==1 and completions==0,(name,status,progress,completions)
                    checks+=1
            logtext=log.read_text(encoding='utf-8',errors='replace')
            assert 'Traceback (most recent call last)' not in logtext,logtext[-1400:]
            checks+=1
            print(f'V106 TCP RAID PARTY {count} PLAYERS RAID {raid}: {checks} PASS; no natural combat timing',flush=True)
            return checks
        except BaseException:
            if log.exists():
                print('RAJD TCP BŁĄD, koniec logu:',log.read_text(encoding='utf8',errors='replace')[-1800:],flush=True)
            raise
        finally:_stop_child(proc)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--gracze',type=int,choices=[3,6],default=6)
    p.add_argument('--rajd',type=int,choices=[26,35],default=26)
    a=p.parse_args()
    run(a.gracze,a.rajd)
