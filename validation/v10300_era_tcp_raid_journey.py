# -*- coding: utf-8 -*-
"""Optional REAL TCP raid scenario on two disposable owner-test accounts.

Uses production server.py, character sessions, party engine, NPC quest handlers,
combat victory handler, quest rewards and durable SQLite. Never production DB.
Admin powers are granted ONLY to synthetic accounts in the private child process
so the test can reach authored level-801 content without weakening gameplay.
"""
from __future__ import annotations
import asyncio
from contextlib import suppress
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from validation.v10300_era_tcp_smoke import ROOT
from validation.v2102_tcp_six_players import TcpPlayer, free_local_port, guarded_child_env
from arena_real_izolowana import _ignore

ACCOUNT_NAMES = (('era103tcpone', 'Era103One'), ('era103tcptwo', 'Era103Two'))
NPC_ROOM = 'v10300_swit_04'
BOSS_ROOM = 'v10300_swit_raid_1'
NPC_NAME = 'Mistrz Bramy Nowego Świtu'
BOSS_NAME = 'Bramy Nowego Świtu: Władca Rajdu, etap 1'
QUEST_ID = 'v10300_swit_raid_quest_1'
QUEST_TITLE = 'Bramy Nowego Świtu: rajd, etap 1 z 3'

async def observe(player, command, predicate, *, attempts=7, interval=0.35):
    outputs=[]
    for attempt in range(attempts):
        response=await player.command(command,quiet=.35)
        outputs.append(response)
        if predicate(response):
            return response
        await asyncio.sleep(interval+attempt*.15)
    raise AssertionError(f'{player.name}: no verified {command!r} response: '
                         +repr(' | '.join(x[-400:] for x in outputs[-3:])))

async def scenario(port):
    a,b=[TcpPlayer(account,name,port) for account,name in ACCOUNT_NAMES]
    checks=0
    try:
        await asyncio.gather(a.connect_and_login(),b.connect_and_login());checks+=2
        for player in (a,b):
            await observe(player,'admin status',lambda x:'Administrator: TAK' in x)
            await observe(player,'admin god on',lambda x:'GOD' in x and 'WLACZ' in x.upper())
            checks+=2
        await observe(a,'druzyna zaloz',lambda x:'drużyn' in x.casefold() or 'druzyn' in x.casefold())
        await a.command('druzyna zapros Era103Two')
        await observe(b,'dolacz',lambda x:'drużyn' in x.casefold() or 'druzyn' in x.casefold())
        await observe(a,'druzyna',lambda x:'Era103Two' in x)
        checks+=3
        for stage in (1,2,3):
            title=f'Bramy Nowego Świtu: rajd, etap {stage} z 3'
            boss_room=f'v10300_swit_raid_{stage}'
            for player in (a,b):
                await observe(player,'admin goto '+NPC_ROOM,lambda x:NPC_NAME in x)
                await observe(player,'look',lambda x:('NPC: '+NPC_NAME) in x)
                await observe(player,'talk '+NPC_NAME,lambda x:title in x or 'LISTA ZADAŃ' in x)
                checks+=3
                qtext=await observe(player,'quest list '+NPC_NAME,lambda x:title in x)
                pattern=re.compile(r'(?m)^\s*(\d+)\.\s*'+re.escape(title))
                found=pattern.search(qtext)
                if not found:
                    raise AssertionError('No numbered raid quest in NPC offer: '+qtext[-1500:])
                await player.command('quest accept '+found.group(1))
                await observe(player,'quests',lambda x:title in x)
                checks+=2
            for player in (a,b):
                await observe(player,'admin goto '+boss_room,lambda x:'Władca Rajdu' in x)
                await observe(player,'look',lambda x:'Władca Rajdu' in x)
                checks+=2
            response=await a.command('admin cios wyrok Władca Rajdu',quiet=.5)
            for attempt in range(12):
                states=await asyncio.gather(a.command('quests'),b.command('quests'))
                if all(title in x and re.search(r'Postęp\s+1\s+z\s+1',x,re.I) for x in states):
                    checks+=2
                    break
                if attempt==11:
                    raise AssertionError('Boss not credited at stage '+str(stage)+': strike='
                        +response[-650:]+' quests='+repr([x[-500:] for x in states]))
                await asyncio.sleep(1)
            for player in (a,b):
                await observe(player,'admin goto '+NPC_ROOM,lambda x:NPC_NAME in x)
                listing=await observe(player,'quest list '+NPC_NAME,lambda x:title in x)
                match=re.search(r'(?m)^\s*(\d+)\.\s*'+re.escape(title),listing)
                if not match:
                    raise AssertionError('NPC lost active raid quest on turnin: '+listing[-850:])
                await player.command('quest oddaj '+match.group(1))
                await observe(player,'quest ukończone',lambda x:title in x)
                checks+=3
            print(f'ERA TCP RAID: 2 players completed stage {stage}/3',flush=True)
        return checks
    finally:
        await asyncio.gather(a.close(),b.close())


def run():
    with tempfile.TemporaryDirectory(prefix='sb103-tcp-raid-real-') as temp:
        work=Path(temp); source=work/'private_game'
        shutil.copytree(ROOT,source,ignore=_ignore)
        assert not (source/'soulbound.db').exists(), 'Player DB must never be copied'
        port=free_local_port();env,dbpath=guarded_child_env(source,port)
        # Admin powers are restricted to the two accounts created inside THIS
        # private test server. They are never exported to the user's server.
        env['SOULBOUND_ADMIN_ACCOUNTS']=','.join(x[0] for x in ACCOUNT_NAMES)
        from storage.database import Database
        from core.classes_skills import CLASSES,RACES
        db=Database(str(dbpath))
        for login,name in ACCOUNT_NAMES:
            aid=db.create_account(login,'test_only_tcp_2026_password')
            db.create_character_for_master(aid,name,RACES[0],CLASSES[0],
                {k:name for k in ('nom','gen','dat','acc','ins','loc','voc')})
            assert len(db.characters_for_master(aid))==1
        db.conn.commit();db.conn.close()
        logfile=work/'private_game.log'
        checks=0;proc=None
        try:
            with logfile.open('w',encoding='utf-8') as sink:
                proc=subprocess.Popen([sys.executable,'-u','server.py'],cwd=source,env=env,
                    stdout=sink,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
                deadline=time.monotonic()+230
                while time.monotonic()<deadline:
                    if proc.poll() is not None:
                        raise RuntimeError('Private server failed to start: '+logfile.read_text(errors='replace')[-2500:])
                    if 'World Core nasłuchuje:' in logfile.read_text(errors='replace'):
                        break
                    time.sleep(.4)
                else:
                    raise TimeoutError('Private server not ready: '+logfile.read_text(errors='replace')[-1400:])
                print('ERA TCP RAID: server ready; 2 disposable accounts',flush=True)
                checks=asyncio.run(scenario(port))
        except BaseException:
            print('ERA TCP RAID FAILURE LOG TAIL: '+logfile.read_text(errors='replace')[-1500:],flush=True)
            raise
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                with suppress(subprocess.TimeoutExpired):proc.wait(timeout=15)
                if proc.poll() is None:proc.kill();proc.wait(timeout=8)
        assert 'Traceback (most recent call last)' not in logfile.read_text(errors='replace')
        db=Database(str(dbpath))
        for login,_ in ACCOUNT_NAMES:
            acc=db.account_by_name(login)
            for stage in (1,2,3):
                qid=f'v10300_swit_raid_quest_{stage}'
                q=db.quest(int(acc['id']),qid)
                assert q and q['status']=='completed' and q['completion_count']==1,(login,qid,dict(q) if q else None)
                checks+=1
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
        db.conn.close()
        return checks

if __name__=='__main__':
    print(f'ERA v103 REAL TCP NPC/RAID/PARTY/QUEST: {run()} PASS',flush=True)
