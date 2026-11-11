# -*- coding: utf-8 -*-
"""Real localhost TCP quest kill/reward after fixture-shortened boss combat.

The isolated fixture shortens boss HP to 1 *after adaptive scaling*.
This proves the genuine auto-attack->death->quest credit->NPC payout path,
NOT authentic high-level balance, HP scaling or typical time to kill.
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
import time
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.v2102_tcp_six_players import (
    TcpPlayer,guarded_child_env,free_local_port,wait_for_world_server,_stop_child,PLAYERS,
)
from world.v10500_region_index import REGIONS
from world.dynamic_content import MOB_TEMPLATES,NPCS,QUESTS
CASES=((3,0),(4,19))

def info(index):
    slug=REGIONS[index][0]
    return (NPCS[f'v10500_{slug}_npc_2']['name'],
            QUESTS[f'v10500_{slug}_hunt_09']['name'],
            f'v10500_{slug}_hunt_09',
            MOB_TEMPLATES[f'v10500_{slug}_boss_1']['name'])

async def quest_page_number(client, npc, qname):
    """Read the entire TCP quest page, not just its first delayed fragment.

    The server sends one header, ten numbered quests and closing guidance in
    separate writes. On slower Windows machines an incomplete header can be
    mistaken for a complete response by the short-quiet-period helper. Require
    the real final page marker and the exact requested quest before selecting
    its number; never infer the position from the catalogue or database.
    """
    await client.drain_idle(quiet=.06, total=.18)
    command = 'quest list ' + npc + ' strona 2'
    await client.send(command)
    result = bytearray()
    # The full page can be slow to render while other clients trigger world
    # events and SQLite payouts. The deadline is bounded and fails closed.
    deadline = time.monotonic() + 65
    end_marker = b'Numery przyjmij i quest info'
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        try:
            chunk = await asyncio.wait_for(client.reader.read(16384),
                                           timeout=min(2.0, max(.01, remaining)))
        except asyncio.TimeoutError:
            continue
        if not chunk:
            raise ConnectionError(client.name + ': TCP closed during ' + command)
        result.extend(chunk)
        if len(result) > 2_000_000:
            raise AssertionError(client.name + ': oversized quest response')
        if b'Wyst' in result and (b'd komendy' in result or b'd sesji' in result):
            raise AssertionError(client.name + ': quest list server error '
                                 + repr(result[-1000:]))
        if end_marker not in result:
            continue
        listing = result.decode('utf-8', 'replace')
        assert f'LISTA ZADAŃ: {npc}. Strona 2' in listing, (
            client.name, 'wrong quest page', listing[-1400:])
        match = re.search(r'(?m)^\s*(\d+)\.\s*' + re.escape(qname) + r'\.', listing)
        assert match, (client.name, 'quest absent from complete NPC page',
                       qname, listing[-1800:])
        return match.group(1)
    raise AssertionError((client.name, 'incomplete quest page after 65s',
                          command, bytes(result[-1600:]).decode('utf-8', 'replace')))


async def tcp_confirm_boss(client, boss):
    """Do not mistake the first TCP room-header chunk for a complete `look`.

    Looking directly at the named living mob returns its name followed by
    a separate HP line. Require BOTH genuine server messages, with a bounded
    deadline; missing bosses and truncated replies still fail this gate.
    """
    await client.drain_idle(quiet=.08, total=.25)
    await client.send('look ' + boss)
    response = bytearray()
    deadline = time.monotonic() + 65
    name_line = boss + '. Przeciwnik.'
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        try:
            piece = await asyncio.wait_for(client.reader.read(16384),
                                           timeout=min(2, max(.01, remaining)))
        except asyncio.TimeoutError:
            continue
        if not piece:
            raise AssertionError((client.name, boss, 'TCP closed before full mob description',
                                  response[-800:].decode('utf-8', 'replace')))
        response.extend(piece)
        if len(response) > 100_000:
            raise AssertionError((client.name, boss, 'oversized mob description'))
        text = response.decode('utf-8', 'replace').replace('\r', '')
        if 'Wystąpił błąd komendy' in text or 'Wystąpił błąd sesji' in text:
            raise AssertionError((client.name, boss, 'server error', text[-850:]))
        if 'Nie widzisz tutaj takiego gracza' in text:
            raise AssertionError((client.name, boss, 'mob not visible', text[-850:]))
        if (name_line in text and re.search(r'(?m)^HP:\s*\d+\s+z\s+\d+\.', text)):
            return text
    raise AssertionError((client.name, boss, 'incomplete boss look after 65 seconds',
                          response[-1000:].decode('utf-8', 'replace')))


async def tcp_start_boss_combat(client, boss):
    """Await the genuine combat acknowledgement instead of a partial TCP read."""
    await client.drain_idle(quiet=.1, total=.4)
    await client.send('k ' + boss)
    response = bytearray()
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        try:
            piece = await asyncio.wait_for(client.reader.read(16384),
                                           timeout=min(2, max(.01, remaining)))
        except asyncio.TimeoutError:
            continue
        if not piece:
            raise AssertionError((client.name, boss, 'TCP closed before combat',
                                  response[-850:].decode('utf-8', 'replace')))
        response.extend(piece)
        if len(response) > 200_000:
            raise AssertionError((client.name, boss, 'oversized combat response'))
        text = response.decode('utf-8', 'replace')
        if 'Wystąpił błąd komendy' in text or 'Wystąpił błąd sesji' in text:
            raise AssertionError((client.name, boss, 'server error', text[-850:]))
        if 'Walka w czasie rzeczywistym' in text or 'pokonany' in text.lower():
            return text
        if 'Nie widzisz tutaj' in text or 'Nie ma takiego' in text:
            raise AssertionError((client.name, boss, 'combat target absent', text[-850:]))
    raise AssertionError((client.name, boss, 'no combat acknowledgement after 65 seconds',
                          response[-1000:].decode('utf-8', 'replace')))


def run_tcp_stream_regression():
    """Fragmented TCP output and a missing boss must never become false PASS."""
    class Reader:
        def __init__(self, parts):
            self.parts = iter(parts)
        async def read(self, _size):
            await asyncio.sleep(0)
            return next(self.parts, b'')
    class Client:
        name = 'stream-test'
        def __init__(self, parts):
            self.reader = Reader(parts)
            self.sent = []
        async def send(self, cmd):
            self.sent.append(cmd)
        async def drain_idle(self, **_kwargs):
            return ''
    async def check():
        checks = 0
        boss = 'Strażnik Popiołu'
        client = Client([b'Arena Stra', 'żnika\n'.encode('utf-8'),
                         (boss + '. Przeciwnik.\nH').encode('utf-8'), b'P: 1 z 410040000.\n'])
        result = await tcp_confirm_boss(client, boss)
        assert 'HP: 1 z 410040000.' in result and client.sent == ['look '+boss]
        checks += 1
        for parts in (['Arena Strażnika. Strefa: test.\n'.encode('utf-8')],
                      ['Nie widzisz tutaj takiego gracza, NPC, przeciwnika ani przedmiotu.\n'.encode('utf-8')]):
            client = Client(parts)
            try:
                await tcp_confirm_boss(client, boss)
            except AssertionError:
                checks += 1
            else:
                raise AssertionError('Missing boss / truncated TCP incorrectly accepted')
        client = Client([b'SOUND_EVENT MOB_HP', b'Walka w czasie rzeczy',
                         'wistym rozpoczęta.\n'.encode('utf-8')])
        result = await tcp_start_boss_combat(client, boss)
        assert 'Walka w czasie rzeczywistym' in result and client.sent == ['k '+boss]
        checks += 1
        return checks
    return asyncio.run(check())


async def game(port,stage):
    print('BOSS clients login: '+stage,flush=True)
    clients=[TcpPlayer(f'tcpcheck{i}',f'Testtcp{i}',port) for i in range(1,PLAYERS+1)]
    checks=0
    try:
        await asyncio.gather(*(c.connect_and_login() for c in clients)); checks+=5
        print('BOSS clients 5/5 '+stage,flush=True)
        for i,region in CASES:
            c=clients[i-1];npc,qname,qid,boss=info(region)
            if stage=='offer':
                number=await quest_page_number(c,npc,qname);checks+=1
                response=await c.command('przyjmij '+number,quiet=.3)
                assert 'Quest przyjęty' in response,(i,response[-1100:]);checks+=1
            elif stage=='battle':
                look=await tcp_confirm_boss(c,boss)
                assert boss + '. Przeciwnik.' in look,(i,look[-750:]);checks+=1
                response=await tcp_start_boss_combat(c,boss)
                assert 'Walka w czasie rzeczywistym' in response or 'pokonany' in response.lower(),(i,response[-900:]);checks+=1
                print('BOSS ATTACK:',boss,repr(response[-380:]),flush=True)
            elif stage=='reward':
                number=await quest_page_number(c,npc,qname);checks+=1
                response=await c.command('oddaj '+number,quiet=.3)
                # Completion emits many real EXP/stat messages; the first read
                # can return while item/currency payouts are still running.
                # Never kill the test server until the FINAL completion signal.
                deadline=time.monotonic()+45
                while 'Zadanie ukończone:' not in response and time.monotonic()<deadline:
                    extra=await c.drain_idle(quiet=.55,total=3)
                    if extra:response+=extra
                    else:await asyncio.sleep(.15)
                print('BOSS TURNIN:',qname,repr(response[-700:]),flush=True)
                assert 'Zadanie ukończone:' in response,(qid,'payout not committed',response[-1100:]);checks+=1
        if stage=='battle':
            # Player action occurs on the real async combat task. Wait a bounded
            # period; no artificial quest progress or direct mob_defeated call.
            await asyncio.sleep(7)
        return checks
    finally:
        await asyncio.gather(*(c.close() for c in clients),return_exceptions=True)

def status(dbpath,expected,min_progress=0):
    count=0
    with closing(sqlite3.connect(dbpath)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        for i,region in CASES:
            npc,qname,qid,boss=info(region)
            row=db.execute('SELECT q.status,q.progress FROM quests q JOIN accounts a '
                           'ON a.id=q.account_id WHERE a.username=? AND q.quest_id=?',
                           (f'tcpcheck{i}',qid)).fetchone()
            assert row is not None,(qid,row)
            assert row[0]==expected,(qid,expected,row)
            assert int(row[1])>=min_progress,(qid,row)
            if expected=='completed':
                slug=REGIONS[region][0]
                # Check a REAL persisted quest item, not just a text announcement.
                iid=f'v10500_{slug}_material_1'
                # Regional crafting materials are routed to the craftbox, not inventory.
                quantity=db.execute('SELECT COALESCE(SUM(ps.quantity),0) FROM profession_storage ps '
                    'JOIN accounts a ON a.id=ps.account_id '
                    'WHERE a.username=? AND ps.container=? AND ps.item_id=?',
                    (f'tcpcheck{i}','craftbox',iid)).fetchone()[0]
                assert int(quantity)>=1,(qid,'missing paid quest item',quantity);count+=1
                wallet=db.execute('SELECT c.silver,c.gold,c.mithril FROM characters c '
                    'JOIN accounts a ON a.id=c.account_id WHERE a.username=?',
                    (f'tcpcheck{i}',)).fetchone()
                assert wallet is not None and any(int(v)>0 for v in wallet), (qid,'paid currency missing',wallet);count+=1
            count+=1
    return count

def cycle(directory,dbpath,stage):
    port=free_local_port()
    env,actual=guarded_child_env(directory,port)
    assert actual==dbpath
    env['SOULBOUND_V105_BOSS_REWARDS_TEST']='1'
    env['SOULBOUND_V105_BOSS_REWARDS_STAGE']=stage
    logpath=Path(directory)/('boss-'+stage+'.log')
    proc=None
    try:
        with logpath.open('w',encoding='utf-8') as logfile:
            proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'validation/v10500_tcp_boss_reward_child.py')],
                cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=logfile,stderr=subprocess.STDOUT)
            wait_for_world_server(proc,logpath,seconds=240)
            checks=asyncio.run(game(port,stage))
        txt=logpath.read_text(encoding='utf-8',errors='replace')
        if 'Traceback (most recent call last)' in txt:
            raise AssertionError('Server traceback '+txt[-1200:])
        return checks
    except BaseException:
        print('V105 BOSS TCP FAIL '+stage,flush=True)
        if logpath.exists():print('\n'.join(logpath.read_text(encoding='utf-8',errors='replace').splitlines()[-25:]),flush=True)
        raise
    finally:_stop_child(proc)

def run():
    stream_checks=run_tcp_stream_regression()
    assert stream_checks==4
    print('V105 TCP BOSS fragmented stream regression: 4/4 PASS',flush=True)
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v105-boss-') as temp:
        dbpath=Path(temp).resolve()/'five_players.sqlite'
        print('BOSS offer stage',flush=True)
        checks=stream_checks+cycle(temp,dbpath,'offer')
        checks+=status(dbpath,'active')
        print('BOSS battle stage',flush=True)
        checks+=cycle(temp,dbpath,'battle')
        checks+=status(dbpath,'active',min_progress=1)
        print('BOSS reward stage',flush=True)
        checks+=cycle(temp,dbpath,'reward')
        checks+=status(dbpath,'completed',min_progress=1)
        print('V105 TCP BOSS REWARDS: '+str(checks)+' PASS (fixture-low HP, NOT normal balance)',flush=True)
        return checks

if __name__=='__main__':run()
