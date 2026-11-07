# -*- coding: utf-8 -*-
"""1–6 real TCP players, no admin strike, actual boss weapon rounds.

Never connects to production. Separate disposable SQLite, private TCP port.
Combat metrics are read from server-side action telemetry, NOT command text
(which can arrive in a different order after the opening boss summon).
"""
from __future__ import annotations
import argparse
import asyncio
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from validation.v2102_tcp_six_players import (
    TcpPlayer, guarded_child_env, free_local_port, wait_for_world_server, _stop_child,
)
from validation.v10600_tcp_raid_party_real import observe

ROOT=Path(__file__).resolve().parents[1]
PARTY=6  # real-world maximum; the engine supports other sizes

def read_jsonl(path):
    if not path.exists():return []
    return [json.loads(s) for s in path.read_text(encoding='utf8').splitlines() if s.strip()]

async def scenario(port, work, *, count=6, raid=26, stage=1, full=False, claim=False):
    players=[TcpPlayer(f'natural106{i:02d}',f'Natural106{i:02d}',port)
             for i in range(1,count+1)]
    draining=[]
    disconnected=[]
    async def consume_combat_feed(player):
        # Real MUD client keeps reading as the fight runs. Without this, TCP
        # backpressure and writer.drain artificially stall the entire party.
        while True:
            chunk=await player.reader.read(65536)
            if not chunk:
                disconnected.append(player.name)
                break
            for needle in ('Wystąpił błąd sesji','Pętla walki została zatrzymana',
                           'Wystąpił błąd komendy'):
                if needle.encode('utf-8') in chunk:
                    disconnected.append(player.name+' ('+needle+'): '
                                        +chunk.decode('utf-8','replace')[-700:])
    try:
        for p in players:
            await p.connect_and_login()
        leader=players[0]
        if count > 1:
            await observe(leader,'druzyna zaloz',lambda t:'Zakładasz drużynę' in t)
        for p in players[1:]:
            await observe(leader,'druzyna zapros '+p.name,
                          lambda t,n=p.name:n in t and 'Zapraszasz' in t)
            await observe(p,'dolacz',lambda t:'do drużyny' in t)
        if count > 1:
            party=await observe(leader,'druzyna',lambda t:players[-1].name in t)
            assert all(p.name in party for p in players),f'Niekompletna drużyna {count}/{count}.'
        # All commands are REAL ordinary attack actions, not admin or mock kills.
        # Later idle reads are ignored; server telemetry is the authority.
        from world.v10600_raids_26_35 import STAGES
        boss_name=STAGES[stage-1]
        result=await asyncio.gather(*(p.command('attack '+boss_name,quiet=.18)
                                      for p in players),return_exceptions=True)
        for p,r in zip(players,result):
            if isinstance(r,BaseException):
                raise AssertionError(f'{p.name}: attack: {r}')
        print(f'NATURALNY RAJD: {count} zwykłych komend attack wysłano.',flush=True)
        draining=[asyncio.create_task(consume_combat_feed(p)) for p in players]
        deadline=time.monotonic()+85
        hit_file=work/'natural_hits.jsonl'
        opening_hits=0
        while time.monotonic()<deadline:
            hits=[r for r in read_jsonl(hit_file)
                  if r.get('template','').startswith(f'v10600_raid_{raid}_boss_{stage}')
                  and r.get('damage',0)>0]
            first_by_player={r['name'] for r in hits}
            if len(first_by_player)==count:
                # A first real round from every player is already meaningful.
                opening_hits=len(hits)
                break
            await asyncio.sleep(.5)
        hits=[r for r in read_jsonl(hit_file)
              if r.get('template','').startswith(f'v10600_raid_{raid}_boss_{stage}')]
        unique={r['name'] for r in hits if r['damage']>0}
        if disconnected:
            raise AssertionError(f'Zerwane sesje TCP podczas walki: {disconnected}')
        if len(unique)!=count:
            raise AssertionError(f'Tylko {len(unique)}/{count} graczy wykonało prawdziwy cios; trafienia={len(hits)}')
        print(f'NATURALNY RAJD: {len(unique)}/{count} graczy trafiło realnie, obserwacje {len(hits)}.',flush=True)
        if full:
            deadline=time.monotonic()+75
            while time.monotonic()<deadline:
                all_hits=[r for r in read_jsonl(hit_file)
                          if r.get('template','').startswith(f'v10600_raid_{raid}_boss_{stage}')]
                if disconnected:
                    raise AssertionError(f'Zerwane sesje TCP podczas walki: {disconnected}')
                if any(r.get('mob_id')==f'v10600_raid_{raid}_boss_{stage}'
                       for r in read_jsonl(work/'natural_settled.jsonl')):
                    print('NATURALNY RAJD: boss pokonany bez admina; rozliczenie ukończone.',flush=True)
                    if claim:
                        # The raid boss dies through the real game engine. After
                        # settlement, travel by ordinary player movement commands
                        # back to the existing regional quest-giver NPC.  No
                        # admin teleport, DB credit edit, or artificial rewards.
                        for task in draining:
                            task.cancel()
                        await asyncio.gather(*draining,return_exceptions=True)
                        draining.clear()
                        from world.v10600_raids_26_35 import RAID_ROWS
                        name=f'Rajd {raid}: {RAID_ROWS[raid-26][2]}, etap {stage}/3'
                        # World topology: stage3->2->1 (south), stage1->entry
                        # (west), then 23->22->21 (west) and 21->20 (south).
                        steps=('south',)*(stage-1)+('west','west','west','south')
                        # Reading a single command-response frame does not
                        # guarantee that earlier broadcasts are drained for a
                        # busy six-player party.  TCP preserves command order;
                        # observe the actual reward marker across all chunks.
                        for direction in steps:
                            await asyncio.gather(*(p.send(direction) for p in players))
                            await asyncio.gather(*(p.drain_idle(quiet=.18,total=2.5) for p in players))
                        async def claim_once(p):
                            await p.send('oddaj '+name)
                            deadline=time.monotonic()+55
                            observed=''
                            while time.monotonic()<deadline:
                                try:
                                    chunk=await asyncio.wait_for(p.reader.read(16384),
                                        timeout=min(10,max(.1,deadline-time.monotonic())))
                                except asyncio.TimeoutError:
                                    continue
                                if not chunk:raise AssertionError(f'{p.name}: rozłączono przy oddawaniu')
                                # Check the entire newly received TCP frame BEFORE
                                # truncating diagnostics. A long battle broadcast
                                # (up to 16 KB) can otherwise erase the successful
                                # NPC reward marker from the 12 KB rolling buffer.
                                combined=observed+chunk.decode('utf-8','replace')
                                if 'Zadanie ukończone:' in combined:
                                    return combined[-12000:]
                                if 'Wystąpił błąd sesji' in combined or 'Wystąpił błąd komendy' in combined:
                                    raise AssertionError(f'{p.name}: błąd w komendzie oddaj: {combined[-1000:]}')
                                observed=combined[-12000:]
                            raise AssertionError(f'{p.name}: brak nagrody po realnym zabiciu: {observed[-1400:]}')
                        await asyncio.gather(*(claim_once(p) for p in players))
                        # One second attempt per player, independently verified
                        # after quit by completion_count==1 and craftbox data.
                        await asyncio.gather(*(p.send('oddaj '+name) for p in players))
                        repeats=await asyncio.gather(*(p.drain_idle(quiet=.35,total=3.5) for p in players))
                        if any('Zadanie ukończone:' in answer for answer in repeats):
                            raise AssertionError('Zduplikowano wypłatę questa po ponownym oddaj.')
                        print(f'NATURALNY RAID NPC: {count}/{count} realnych odbiorów '
                              'questu, brak duplikacji nagród.',flush=True)
                    # Prawdziwi klienci koncza sesje normalnym QUIT. TCP
                    # close() zamyka tylko socket i poprzedni test zabijal
                    # serwer PRZED zapisaniem transakcji nagrod grupy.
                    await asyncio.gather(*(p.send('quit') for p in players),return_exceptions=True)
                    deadline_save=time.monotonic()+25
                    while time.monotonic()<deadline_save:
                        try:
                            with closing(sqlite3.connect(work/'natural_raid.sqlite',timeout=1.0)) as _read_db:
                                _rows=_read_db.execute('''SELECT q.progress,q.status,q.completion_count FROM quests q
                                    WHERE q.quest_id=? ORDER BY q.account_id''',
                                    (f'v10600_raid_{raid}_quest_{stage}',)).fetchall()
                            if len(_rows)==count and all(int(row[0])>=1 for row in _rows) and (not claim or all(row[1]=='completed' and int(row[2])==1 for row in _rows)):
                                if claim:
                                    with closing(sqlite3.connect(work/'natural_raid.sqlite')) as cbox:
                                        amounts=cbox.execute('''SELECT a.username, COALESCE(SUM(s.quantity),0)
                                            FROM accounts a LEFT JOIN profession_storage s ON
                                              s.account_id=a.id AND s.container='craftbox' AND s.item_id=?
                                            WHERE a.username LIKE 'natural106%' GROUP BY a.id''',
                                            (f'v10600_raid_{raid}_fragment',)).fetchall()
                                    if len(amounts)!=count or any(int(qty)<1 for _,qty in amounts):
                                        await asyncio.sleep(.3)
                                        continue
                                print(f'RAJD QUEST COMMIT: {count}/{count} na dysku SQLite.'+
                                    (' Odbiór NPC i Szkatułka Rzemieślnicza PASS.' if claim else ''),flush=True)
                                return len(all_hits)
                        except sqlite3.Error:  # AUDIT_INTENTIONAL_PASS: concurrent SQLite commit; retry until deadline
                            pass
                        await asyncio.sleep(.35)
                    raise AssertionError('Boss martwy, ale brak trwalego quest-credit po normalnym QUIT.')
                await asyncio.sleep(.5)
            deaths=read_jsonl(work/'natural_deaths.jsonl')
            if deaths: print('ZGONY TESTOWE: '+str([(r['name'],r['killer']) for r in deaths]),flush=True)
            if all_hits:
                last=all_hits[-1]
                print(f'BRAK KONCA WALKI: {len(all_hits)} akcji, ostatnie HP bossa '
                      f'{last["after"]:,} / {last["adaptive_hp"]}, '
                      f'ostatni gracz {last["name"]}, '
                      f'obrazenia ogolem {sum(int(x["damage"]) for x in all_hits):,}.', flush=True)
            raise AssertionError('Po 75 s dalszej realnej walki boss nie został pokonany; brak PASS pełnego rajdu.')
        return len(hits)
    finally:
        for task in draining:
            task.cancel()
        if draining:
            await asyncio.gather(*draining,return_exceptions=True)
        await asyncio.gather(*(p.close() for p in players),return_exceptions=True)

def run(*, count=6, raid=26, stage=1, full=False, claim=False):
    assert 1 <= count <= 6 and 26 <= raid <= 35 and 1 <= stage <= 3, 'Testy faktycznych składów 1–6 i etapów 1–3.'
    assert not claim or full, 'Odbiór u NPC wymaga naturalnego zwycięstwa.'
    assert os.environ.get('SOULBOUND_V106_STAGING')!='1', 'Rodzic poza staging.'
    with tempfile.TemporaryDirectory(prefix='soulbound-v106-natural-party-') as directory:
        work=Path(directory);port=free_local_port()
        env,_=guarded_child_env(work,port)
        env.update(SOULBOUND_DB=str(work/'natural_raid.sqlite'),
                   SOULBOUND_V106_STAGING='1',
                   SOULBOUND_V106_NATURAL_RAID_TEST='1',
                   SOULBOUND_V106_NATURAL_COUNT=str(count),
                   SOULBOUND_V106_NATURAL_RAID=str(raid),
                   SOULBOUND_V106_NATURAL_STAGE=str(stage),
                   SOULBOUND_MAX_CLIENTS=str(count),
                   PYTHONPATH=str(ROOT))
        env.pop('SOULBOUND_ADMIN_ACCOUNTS',None)
        proc=None;log=work/'server.log'
        try:
            with log.open('w',encoding='utf8') as sink:
                proc=subprocess.Popen([sys.executable,'-B','-u',str(ROOT/'validation/v10600_tcp_raid_normal_attack_child.py')],
                  cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=sink,stderr=subprocess.STDOUT)
                wait_for_world_server(proc,log,seconds=200)
                n=asyncio.run(scenario(port,work,count=count,raid=raid,stage=stage,full=full,claim=claim))
            _stop_child(proc);proc=None
            scales=[r for r in read_jsonl(work/'natural_scale.jsonl')
                    if r.get('mob_id')==f'v10600_raid_{raid}_boss_{stage}']
            assert scales,'Nie ma pomiarów skalowania'
            highest=max(scales,key=lambda r:int(r['new_max'] or 0))
            assert highest['partysize']==count,highest
            assert int(highest['new_max'])>int(highest['base_hp']), 'Niedoskalowane HP mimo mocnych postaci'
            hits=[r for r in read_jsonl(work/'natural_hits.jsonl')
                  if r.get('template','').startswith(f'v10600_raid_{raid}_boss_{stage}')]
            dealt=sum(int(r['damage']) for r in hits)
            distinct={r['name'] for r in hits if r['damage']>0}
            with closing(sqlite3.connect(work/'natural_raid.sqlite')) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                if full:
                    records=db.execute("""SELECT a.username,q.status,q.progress,q.completion_count
                        FROM quests q JOIN accounts a ON a.id=q.account_id
                        WHERE q.quest_id=? ORDER BY a.username""",
                        (f'v10600_raid_{raid}_quest_{stage}',)).fetchall()
                    assert len(records)==count,records
                    assert all(row[2]>=1 for row in records),records
                    if claim:
                        assert all(row[1]=='completed' and row[3]==1 for row in records),records
            logs=log.read_text(encoding='utf8',errors='replace')
            assert 'Traceback (most recent call last)' not in logs
            print(f'NATURALNY RAID {raid} ETAP {stage} TCP: {count}/{count} graczy, {n} akcji Broni Duszy. '
                  f'HP bossa {int(highest["new_max"]):,}, '
                  f'suma obrażeń w obserwacji {dealt:,}, '
                  f'gracze z trafieniami {len(distinct)}. '
                  +(f'Pełne naturalne zabicie i {count} quest-credit PASS.' if full else
                    'Pierwsza runda PASS. Pełne zabicie nadal osobnym pomiarem.'),flush=True)
            if full:
                first=min(r['at'] for r in hits if r.get('at'))
                final=next((r for r in hits if r.get('alive') is False),None)
                if final:
                    print(f'CZAS od pierwszego naturalnego trafienia do zabicia: '
                          f'{final["at"]-first:.1f} s; rundy {n}.',flush=True)
            return len(distinct)
        except BaseException:
            # Keep synthetic state diagnostics only when the test fails.
            # Distinguish missed TCP text from a genuinely missing settlement.
            if (work/'natural_raid.sqlite').is_file():
                try:
                    with closing(sqlite3.connect(work/'natural_raid.sqlite',timeout=2)) as _failure_db:
                        _failure_data=_failure_db.execute('''SELECT a.username,q.progress,q.status,q.completion_count
                            FROM accounts a LEFT JOIN quests q ON q.account_id=a.id
                              AND q.quest_id=? WHERE a.username LIKE 'natural106%'
                            ORDER BY a.username''', (f'v10600_raid_{raid}_quest_{stage}',)).fetchall()
                        print('V106 TEST DIAGNOSTYKA QUEST/SQLITE: '+str(_failure_data),flush=True)
                        _columns={x[1] for x in _failure_db.execute('PRAGMA table_info(characters)')}
                        if 'room_id' in _columns:
                            _rooms=_failure_db.execute('''SELECT a.username,c.room_id FROM accounts a
                                JOIN characters c ON c.account_id=a.id WHERE a.username LIKE 'natural106%'
                                ORDER BY a.username''').fetchall()
                            print('V106 TEST DIAGNOSTYKA POKOJE: '+str(_rooms),flush=True)
                except (sqlite3.Error,ValueError) as _diag_exc:
                    print('V106 TEST DIAGNOSTYKA BAZA: '+str(_diag_exc),flush=True)
            if log.exists():
                print('NATURALNY RAJD LOG: '+log.read_text(encoding='utf8',errors='replace')[-1800:],flush=True)
            # Keep synthetic diagnostics after the disposable SQLite is deleted.
            # Never retain accounts or real user data: all players are generated.
            import shutil
            for artifact in ('natural_hits.jsonl','natural_scale.jsonl','natural_timing.jsonl',
                             'natural_credit_trace.jsonl','natural_settled.jsonl'):
                source=work/artifact
                if source.exists():
                    shutil.copy2(source,Path('/mnt/data')/('V106_DIAG_'+artifact))
            timing=read_jsonl(work/'natural_timing.jsonl')
            if timing:
                from collections import defaultdict
                groups=defaultdict(list)
                for rec in timing:groups[rec['method']].append(rec['seconds'])
                print('CZASY TCP '+str({k:(len(v),round(max(v),2),round(sum(v)/len(v),2))
                           for k,v in groups.items()}),flush=True)
            raise
        finally:_stop_child(proc)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--pelna-walka',action='store_true')
    parser.add_argument('--oddaj-po-walce',action='store_true',help='Prawdziwe komendy powrotu i oddaj u NPC po naturalnej walce')
    parser.add_argument('--gracze',type=int,choices=range(1,7),default=6)
    parser.add_argument('--rajd',type=int,choices=range(26,36),default=26)
    parser.add_argument('--etap',type=int,choices=range(1,4),default=1)
    opt=parser.parse_args()
    run(full=(opt.pelna_walka or opt.oddaj_po_walce),count=opt.gracze,raid=opt.rajd,stage=opt.etap,claim=opt.oddaj_po_walce)
