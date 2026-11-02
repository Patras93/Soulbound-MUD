# -*- coding: utf-8 -*-
"""Actual 5-client TCP in first/last v105 regions, two sessions and SQLite restart.

Uses only disposable localhost server, and no production SQLite or user accounts.
Completes no bosses: validates NPC quest offers and acceptance over real TCP,
negative turn-in, durable persistence and game/help commands in endgame rooms.
"""
from __future__ import annotations
import asyncio
from contextlib import closing
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
from validation.v2102_tcp_six_players import (
    TcpPlayer,guarded_child_env,free_local_port,wait_for_world_server,_stop_child,
    PLAYERS,PASSWORD,
)
from world.v10500_region_index import REGIONS

ROOT=Path(__file__).resolve().parents[1]
TESTS=((0,1,'story_01'),(19,1,'story_01'),(0,2,'hunt_09'),(19,2,'hunt_09'))

async def observe(player,cmd,match, attempts=7):
    reports=[]
    for _ in range(attempts):
        response=await player.command(cmd,quiet=.3)
        reports.append(response)
        if match(response):return response
        await asyncio.sleep(.25)
    raise AssertionError(f'{player.name}: {cmd} mismatch: '+repr(reports[-2:])[-1500:])


def quest_info(idx,npcidx,kind):
    from world.dynamic_content import NPCS,QUESTS
    slug=REGIONS[idx][0]
    npc=NPCS[f'v10500_{slug}_npc_{npcidx}']
    qid=f'v10500_{slug}_{kind}'
    return npc['name'],qid,QUESTS[qid]['name']


async def exercise(port,restarted):
    print('TCP V105: sesje logowania, restart='+str(restarted),flush=True)
    clients=[TcpPlayer(f'tcpcheck{i}',f'Testtcp{i}',port) for i in range(1,PLAYERS+1)]
    checks=0
    try:
        await asyncio.gather(*(c.connect_and_login() for c in clients))
        checks+=5
        print('TCP V105: pięć sesji zalogowanych',flush=True)
        if not restarted:
            for c,(idx,npcidx,kind) in zip(clients,TESTS):
                npc,qid,quest_name=quest_info(idx,npcidx,kind)
                print('TCP V105: test NPC '+npc,flush=True)
                look=await observe(c,'look',lambda text:npc.casefold() in text.casefold())
                checks+=1
                # The boss hunt is on page 2; `przyjmij N` must use that
                # exact last displayed page, not the NPC's full 16-entry list.
                page=' strona 2' if kind=='hunt_09' else ''
                listing=await observe(c,'quest list '+npc+page,
                                      lambda text:quest_name.casefold() in text.casefold())
                match=re.search(r'(?m)^\s*(\d+)\.\s*'+re.escape(quest_name)+r'\.',listing)
                if not match:
                    raise AssertionError('Missing actual quest ordinal '+repr(listing[-1400:]))
                checks+=1
                await c.command('przyjmij '+match.group(1))
                await observe(c,'quests',lambda text:quest_name.casefold() in text.casefold())
                checks+=1
                # Only server-sided real quest progress can unlock payment.
                attempt=await c.command('oddaj '+match.group(1))
                status=await observe(c,'quests',lambda text:quest_name.casefold() in text.casefold())
                checks+=1
            # Fifth account remains in the old Temple; v104 commands still respond.
            soul=await observe(clients[4],'help dusza',lambda t:'dus' in t.casefold())
            checks+=1
        else:
            for c,(idx,npcidx,kind) in zip(clients,TESTS):
                npc,qid,quest_name=quest_info(idx,npcidx,kind)
                from world.dynamic_content import MOB_TEMPLATES
                boss_name=MOB_TEMPLATES[f'v10500_{REGIONS[idx][0]}_boss_1']['name']
                await observe(c,'look',lambda t:boss_name.casefold() in t.casefold())
                await observe(c,'quests',lambda t:quest_name.casefold() in t.casefold())
                print('TCP V105: fizyczny boss '+boss_name+' i trwały quest PASS',flush=True)
                checks+=2
        return checks
    finally:
        await asyncio.gather(*(c.close() for c in clients),return_exceptions=True)


def verify(db_path):
    with closing(sqlite3.connect(db_path)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        for i,(idx,npcidx,kind) in enumerate(TESTS,1):
            slug=REGIONS[idx][0]
            qid=f'v10500_{slug}_{kind}'
            row=db.execute('SELECT q.status,q.progress FROM quests q JOIN accounts a '
                'ON q.account_id=a.id WHERE a.username=? AND q.quest_id=?',
                (f'tcpcheck{i}',qid)).fetchone()
            assert row is not None and row[0]=='active' and int(row[1])==0,(i,qid,row)
        return len(TESTS)


def cycle(temp,path,restarted):
    port=free_local_port()
    env,real_path=guarded_child_env(temp,port)
    assert real_path==path
    env['SOULBOUND_V105_TCP_ENDGAME_TEST']='1'
    if restarted:env['SOULBOUND_V105_TCP_ENDGAME_BOSS_STAGE']='1'
    logfile=Path(temp)/('endgame-restart.log' if restarted else 'endgame-start.log')
    proc=None
    try:
        with logfile.open('w',encoding='utf-8') as log:
            proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'validation/v10500_tcp_endgame_child.py')],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            wait_for_world_server(proc,logfile,seconds=240)
            checks=asyncio.run(exercise(port,restarted))
        txt=logfile.read_text(encoding='utf-8',errors='replace')
        if 'Traceback (most recent call last)' in txt:
            raise AssertionError('Serwer TCP wypisał traceback: '+txt[-1500:])
        return checks
    except BaseException:
        print('V105 ENDGAME TCP FAILURE; private server log:',flush=True)
        if logfile.exists():print('\n'.join(logfile.read_text(encoding='utf-8',errors='replace').splitlines()[-30:]),flush=True)
        raise
    finally:_stop_child(proc)


def run():
    print('TCP V105: start izolowany',flush=True)
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v105-endgame-') as temp:
        dbpath=Path(temp).resolve()/'five_players.sqlite'
        checks=cycle(temp,dbpath,False)
        checks+=verify(dbpath)
        checks+=cycle(temp,dbpath,True)
        checks+=verify(dbpath)
        print('V105 TCP HIGH REGIONS 5 CLIENTS: '+str(checks)+' PASS, SQLite restart, private DB removed',flush=True)
        return checks

if __name__=='__main__':run()
