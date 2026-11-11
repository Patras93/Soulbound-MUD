# -*- coding: utf-8 -*-
"""Real v106 world/login/NPC/quest TCP smoke on isolated localhost SQLite.

No production access, no high-level combat balance claims. Five actual logins.
"""
from __future__ import annotations
from contextlib import closing
import asyncio,os,re,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from validation.v2102_tcp_six_players import (TcpPlayer,guarded_child_env,free_local_port,wait_for_world_server,_stop_child)
from world.v10600_region_index import REGIONS
from world.v10600_krainy_30001_60000 import NPC_LABELS

def cases():
    return [(0,1),(0,2),(1,1),(1,4),(29,1)]

async def read_full_quest_page(client, npc):
    await client.drain_idle(quiet=.05,total=.18)
    await client.send('quest list '+npc+' strona 1')
    data=bytearray();deadline=time.monotonic()+75
    marker=b'quest info <numer>.'
    while time.monotonic()<deadline:
        try:
            chunk=await asyncio.wait_for(client.reader.read(16384),timeout=1.8)
        except asyncio.TimeoutError:continue
        if not chunk:raise ConnectionError(client.name+': unexpected TCP close')
        data.extend(chunk)
        if len(data)>2_000_000:raise AssertionError('oversized quest listing')
        if marker in data or b'Numery przyjmij i quest info' in data:
            result=data.decode('utf8','replace')
            if 'Wystąpił błąd' in result:raise AssertionError('runtime quest error '+result[-900:])
            if f'LISTA ZADAŃ: {npc}.' not in result:raise AssertionError('missing NPC header '+result[:700])
            if 'Strona ' in result and 'Strona 1' not in result:raise AssertionError('unexpected page '+result[:700])
            return result
    raise TimeoutError('quest listing did not finish: '+data[-1000:].decode('utf8','replace'))

async def story_turnin(lead):
    """Finish one authored NPC talk quest via actual navigation, dialogue and payout."""
    from validation.v2320_autonomous_tcp import _observe
    first=REGIONS[0]
    npc1=NPC_LABELS[0]+' '+first[1]
    npc2=NPC_LABELS[1]+' '+first[1]
    checks=0
    protect=await lead.command('newbieprotect off',quiet=.35)
    assert 'wyłączone' in protect.casefold(),protect[-400:]
    checks+=1
    for step in range(3):
        moved=await lead.command('north',quiet=.4)
        assert 'blokuje ten teren' not in moved,moved[-500:]
        await asyncio.sleep(1.1)
    arrival=await _observe(lead,'look',lambda t:('NPC: '+npc2) in t,attempts=8)
    checks+=1
    dialogue=await lead.command('talk '+npc2,quiet=.4)
    # Historical talk_npc handler automatically completes and rewards the
    # quest at the destination NPC; a second manual turn-in is not needed.
    history=await _observe(lead,'quest ukończone',
        lambda t:'Pierwszy ślad' in t,attempts=8)
    assert 'Pierwszy ślad' in history
    checks+=1
    for _ in range(3):
        await lead.command('south',quiet=.4)
        await asyncio.sleep(1.1)
    arrival=await _observe(lead,'look',lambda t:('NPC: '+npc1) in t,attempts=8)
    checks+=1
    listing=await read_full_quest_page(lead,npc1)
    assert not re.search(r'(?m)^\s*\d+\.\s*'+re.escape(first[1])+r': Pierwszy ślad 1\.',listing),listing[-1400:]
    checks+=1
    print('V106 TCP story talk + auto reward + hidden one-time quest PASS',flush=True)
    return checks

async def exercise(port,*,include_story=False):
    clients=[TcpPlayer(f'tcp106{i}',f'Test106{i}',port) for i in range(1,6)]
    checks=0; accepted=[]
    try:
        # The server has one SQLite writer and a shared world-init lock.
        # Keep all five sessions online concurrently, but serialize login
        # to avoid testing an unrelated initial database-write stampede.
        for client in clients:
            await client.connect_and_login()
            checks+=1
            print('V106 TCP zalogowano:',client.name,flush=True)
        for client,(region,npcno) in zip(clients,cases()):
            slug=REGIONS[region][0];npcid=f'v10600_{slug}_npc_{npcno}'
            npc={"name":NPC_LABELS[npcno-1]+" "+REGIONS[region][1]}
            look=await client.command('look',quiet=.3)
            assert npc['name'].casefold() in look.casefold(),(npc['name'],look[-800:]);checks+=1
            listing=await read_full_quest_page(client,npc['name'])
            assert npc['name'] in listing,(npc['name'],listing[-800:]);checks+=1
            assert re.search(r'(?m)^\s*1\.\s+',listing),listing[-1200:];checks+=1
            first_available=re.search(r'(?m)^\s*(\d+)\.\s+[^\n]*?\. dostępne\.',listing)
            assert first_available,('no available NPC quest',npc['name'],listing[-1600:])
            number=first_available.group(1)
            print('V106 TCP quest offered:',client.name,npc['name'],'number',number,flush=True)
            response=await client.command('przyjmij '+number,quiet=.4)
            assert 'Quest przyjęty' in response,(npc['name'],response[-1500:]);checks+=1
            if region==0 and npcno==1:
                wanted='v10600_przedmurze_story_01'
                assert REGIONS[0][1] in listing,(wanted,listing[-1200:]);checks+=1
            accepted.append((client.account,region,npcno))
        if include_story:
            checks+=await story_turnin(clients[0])
        return checks,accepted
    finally:await asyncio.gather(*(c.close() for c in clients),return_exceptions=True)

def _quest_persistence_snapshot(path):
    """Read-only durable state. No production paths or manual progress updates."""
    with closing(sqlite3.connect(path)) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        quests=tuple(db.execute("""SELECT a.username,q.quest_id,q.status,q.progress
             FROM quests q JOIN accounts a ON a.id=q.account_id
             WHERE a.username LIKE 'tcp106%' AND q.quest_id LIKE 'v10600_%'
             ORDER BY a.username,q.quest_id""").fetchall())
        wallets=tuple(db.execute("""SELECT a.username,c.silver,c.gold
             FROM characters c JOIN accounts a ON a.id=c.account_id
             WHERE a.username LIKE 'tcp106%' ORDER BY a.username""").fetchall())
        materials=tuple(db.execute("""SELECT a.username,i.item_id,i.quantity
             FROM inventory i JOIN accounts a ON a.id=i.account_id
             WHERE a.username LIKE 'tcp106%' AND i.item_id LIKE 'v10600_%'
             ORDER BY a.username,i.item_id""").fetchall())
        storage=tuple(db.execute("""SELECT a.username,p.item_id,p.quantity
             FROM profession_storage p JOIN accounts a ON a.id=p.account_id
             WHERE a.username LIKE 'tcp106%' AND p.item_id LIKE 'v10600_%'
             ORDER BY a.username,p.item_id""").fetchall())
    return (quests,wallets,materials,storage)

async def recheck_after_real_restart(port):
    """Re-log five live players; confirm completion is still hidden at NPC."""
    from validation.v2320_autonomous_tcp import _observe
    players=[TcpPlayer(f'tcp106{i}',f'Test106{i}',port) for i in range(1,6)]
    checks=0
    try:
        for player in players:
            await player.connect_and_login()
            checks+=1
            print('V106 TCP restart zalogowano:',player.name,flush=True)
        for client,(region,npcno) in zip(players,cases()):
            target=NPC_LABELS[npcno-1]+' '+REGIONS[region][1]
            await _observe(client,'look',lambda t,n=target:n in t,attempts=8)
            checks+=1
        first=REGIONS[0]
        npc=NPC_LABELS[0]+' '+first[1]
        history=await _observe(players[0],'quest ukończone',
            lambda t:'Pierwszy ślad' in t,attempts=8)
        assert 'Pierwszy ślad' in history
        checks+=1
        offering=await read_full_quest_page(players[0],npc)
        assert not re.search(r'(?m)^\s*\d+\.\s*'+re.escape(first[1])
            +r': Pierwszy ślad 1\.',offering),offering[-1300:]
        checks+=1
        print('V106 TCP REALNY RESTART: 5 zalogowanych, historia i ukrycie questa PASS',flush=True)
        return checks
    finally:
        await asyncio.gather(*(p.close() for p in players),return_exceptions=True)

def run(*,include_story=False):
    assert os.environ.get('SOULBOUND_V106_STAGING') != '1', 'parent must not inherit staging flag'
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v106-') as temp:
        port=free_local_port()
        env,path=guarded_child_env(temp,port)
        env.update(SOULBOUND_V106_STAGING='1',SOULBOUND_V106_TCP_WORLD_TEST='1',PYTHONPATH=str(ROOT))
        log=Path(temp)/'v106_world_smoke.log'
        proc=None
        try:
            with log.open('w',encoding='utf8') as file:
                proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'validation/v10600_tcp_world_child.py')],
                    cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,stdout=file,stderr=subprocess.STDOUT)
                print('V106 TCP child starting',flush=True)
                wait_for_world_server(proc,log,seconds=180)
                print('V106 TCP server ready; five clients logging in',flush=True)
                checks,accepted=asyncio.run(exercise(port,include_story=include_story))
            with closing(sqlite3.connect(path)) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
                for account,_,_ in accepted:
                    rows=db.execute('SELECT q.quest_id,q.status FROM quests q JOIN accounts a ON a.id=q.account_id WHERE a.username=? AND q.quest_id LIKE ?',
                        (account,'v10600_%')).fetchall()
                    expected='completed' if (include_story and account=='tcp1061') else 'active'
                    assert rows and any(r[1]==expected for r in rows),(account,expected,rows);checks+=1
            if include_story:
                with closing(sqlite3.connect(path)) as db:
                    qid='v10600_przedmurze_story_01'
                    row=db.execute('SELECT q.status,q.progress FROM quests q JOIN accounts a ON a.id=q.account_id WHERE a.username=? AND q.quest_id=?',('tcp1061',qid)).fetchone()
                    assert row and row[0]=='completed' and row[1]>=1,(qid,row)
                    checks+=1
                    item='v10600_przedmurze_material_1'
                    craftbox=db.execute("SELECT COALESCE(SUM(quantity),0) FROM profession_storage ps JOIN accounts a ON ps.account_id=a.id WHERE a.username='tcp1061' AND ps.item_id=?",(item,)).fetchone()[0]
                    inventory=db.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory i JOIN accounts a ON i.account_id=a.id WHERE a.username='tcp1061' AND i.item_id=?",(item,)).fetchone()[0]
                    assert int(craftbox)+int(inventory)>=1,(item,craftbox,inventory)
                    checks+=1
                    wallet=db.execute("SELECT silver,gold FROM characters c JOIN accounts a ON c.account_id=a.id WHERE a.username='tcp1061'").fetchone()
                    # The v105 quest engine credits canonical reward coins in the
                    # silver column; gold stays zero until currency conversion.
                    assert wallet and int(wallet[0])>0,('missing awarded silver',wallet)
                    checks+=1
            if include_story:
                # Real shutdown and restart on the SAME isolated SQLite DB.
                # Read-only snapshot proves that no reward, currency or quest
                # state was duplicated or lost during login after restart.
                before=_quest_persistence_snapshot(path)
                assert len(before[0])>=5 and len(before[1])==5,before[:2]
                _stop_child(proc)
                proc=None
                # Use a fresh log: the server-ready markers from first boot
                # must NOT be mistaken for successful readiness on restart.
                restart_log=Path(temp)/'v106_world_restart.log'
                with restart_log.open('w',encoding='utf8') as file:
                    proc=subprocess.Popen([sys.executable,'-u',
                        str(ROOT/'validation/v10600_tcp_world_child.py')],
                        cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,
                        stdout=file,stderr=subprocess.STDOUT)
                    print('V106 TCP restart na tej samej SQLite',flush=True)
                    wait_for_world_server(proc,restart_log,seconds=180)
                    checks+=asyncio.run(recheck_after_real_restart(port))
                restart_txt=restart_log.read_text(encoding='utf8',errors='replace')
                assert 'Traceback (most recent call last)' not in restart_txt,restart_txt[-1300:]
                after=_quest_persistence_snapshot(path)
                assert after==before,('stan zmieniony po restarcie',before,after)
                checks+=4
                print('V106 TCP QUESTY WALUTY EQ PO RESTARCIE: 4 NIEZMIENIONE ZESTAWY PASS',flush=True)
            txt=log.read_text(encoding='utf8',errors='replace')
            assert 'Traceback (most recent call last)' not in txt,txt[-1300:]
            print(f'V106 REAL TCP FIVE PLAYERS + QUEST SQLITE: {checks} PASS (not real combat balance)',flush=True)
            return checks
        except BaseException:
            print('V106 TCP FAIL; child tail:',flush=True)
            if log.exists():print('\n'.join(log.read_text(encoding='utf8',errors='replace').splitlines()[-30:]),flush=True)
            raise
        finally:_stop_child(proc)
if __name__=='__main__':run(include_story=('--story' in sys.argv))
