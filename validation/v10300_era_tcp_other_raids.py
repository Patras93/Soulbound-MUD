# -*- coding: utf-8 -*-
"""Optional independent TCP acceptance of Era v103 raids in OTHER regions.

Uses the real server, normal NPC/quest/party handlers, and canonical boss
victory via isolated synthetic administrator accounts. It does NOT claim
natural four-phase combat. Default: two regions, all 3 stages each.
"""
from __future__ import annotations
import argparse
import asyncio
from contextlib import suppress
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from arena_real_izolowana import _ignore
from validation.v10300_era_tcp_smoke import ROOT
from validation.v10300_era_tcp_raid_journey import observe
from validation.v2102_tcp_six_players import TcpPlayer, free_local_port, guarded_child_env
from world.v10300_era_bez_granic import ERAS

ACCOUNT_NAMES = (('era103tcpone', 'Era103One'), ('era103tcptwo', 'Era103Two'))
REGIONS = {slug: zone for slug, zone, *_ in ERAS}

async def scenario(port: int, slugs: tuple[str,...]) -> int:
    a, b = [TcpPlayer(account, name, port) for account, name in ACCOUNT_NAMES]
    checks = 0
    try:
        await asyncio.gather(a.connect_and_login(), b.connect_and_login())
        checks += 2
        for player in (a, b):
            await observe(player, 'admin status', lambda x: 'Administrator: TAK' in x)
            await observe(player, 'admin god on', lambda x: 'GOD' in x and 'WLACZ' in x.upper())
            checks += 2
        await observe(a, 'druzyna zaloz', lambda x: 'drużyn' in x.casefold() or 'druzyn' in x.casefold())
        await a.command('druzyna zapros Era103Two')
        await observe(b, 'dolacz', lambda x: 'drużyn' in x.casefold() or 'druzyn' in x.casefold())
        await observe(a, 'druzyna', lambda x: 'Era103Two' in x)
        checks += 3
        for slug in slugs:
            zone = REGIONS[slug]
            npc = f'Mistrz {zone}'
            npc_room = f'v10300_{slug}_04'
            for stage in (1, 2, 3):
                title = f'{zone}: rajd, etap {stage} z 3'
                boss_room = f'v10300_{slug}_raid_{stage}'
                for player in (a, b):
                    await observe(player, f'admin goto {npc_room}', lambda x, name=npc: name in x)
                    await observe(player, 'look', lambda x, name=npc: 'NPC: ' + name in x)
                    await observe(player, 'talk ' + npc,
                                  lambda x, title=title: title in x or 'LISTA ZADAŃ' in x)
                    checks += 3
                    listing = await observe(player, 'quest list ' + npc,
                                            lambda x, title=title: title in x)
                    found = re.search(r'(?m)^\s*(\d+)\.\s*' + re.escape(title), listing)
                    if not found:
                        raise AssertionError(f'Missing NPC quest {slug}/{stage}: {listing[-1000:]}')
                    await player.command('quest accept ' + found.group(1))
                    await observe(player, 'quests', lambda x, title=title: title in x)
                    checks += 2
                for player in (a, b):
                    await observe(player, 'admin goto ' + boss_room,
                                  lambda x: 'Władca Rajdu' in x)
                    await observe(player, 'look', lambda x: 'Władca Rajdu' in x)
                    checks += 2
                # Canonical victory/kill-credit; isolated admin acceleration.
                response = await a.command('admin cios wyrok Władca Rajdu', quiet=.5)
                for attempt in range(12):
                    states = await asyncio.gather(a.command('quests'), b.command('quests'))
                    if all(title in x and re.search(r'Postęp\s+1\s+z\s+1', x, re.I)
                           for x in states):
                        checks += 2
                        break
                    if attempt == 11:
                        raise AssertionError(f'Kill credit missing {slug}/{stage}: '
                                             + response[-450:] + repr([x[-450:] for x in states]))
                    await asyncio.sleep(1)
                for player in (a,b):
                    await observe(player, f'admin goto {npc_room}', lambda x, name=npc: name in x)
                    listing = await observe(player, 'quest list ' + npc,
                                            lambda x, title=title: title in x)
                    found = re.search(r'(?m)^\s*(\d+)\.\s*' + re.escape(title), listing)
                    if not found:
                        raise AssertionError('Missing turn-in offer ' + title + ': ' + listing[-800:])
                    await player.command('quest oddaj ' + found.group(1))
                    await observe(player, 'quest ukończone', lambda x, title=title: title in x)
                    checks += 3
                print(f'ERA TCP OTHER RAIDS: {slug} stage {stage}/3: both players PASS', flush=True)
        return checks
    finally:
        await asyncio.gather(a.close(), b.close())


def run(slugs: tuple[str,...] = ('kuznie','gwiazdy')) -> int:
    if not slugs or any(s not in REGIONS for s in slugs) or len(set(slugs))!=len(slugs):
        raise ValueError('Invalid unique raid region slugs')
    with tempfile.TemporaryDirectory(prefix='sb103-other-raids-') as td:
        work = Path(td)
        source = work / 'private_game'
        shutil.copytree(ROOT, source, ignore=_ignore)
        assert not (source / 'soulbound.db').exists(), 'Production database copied into test'
        port = free_local_port()
        env, dbpath = guarded_child_env(source, port)
        env['SOULBOUND_ADMIN_ACCOUNTS'] = ','.join(login for login,_ in ACCOUNT_NAMES)
        from storage.database import Database
        from core.classes_skills import CLASSES, RACES
        db = Database(str(dbpath))
        for login, name in ACCOUNT_NAMES:
            aid = db.create_account(login, 'test_only_tcp_2026_password')
            db.create_character_for_master(aid, name, RACES[0], CLASSES[0],
                {k:name for k in ('nom','gen','dat','acc','ins','loc','voc')})
            assert len(db.characters_for_master(aid))==1
        db.conn.commit(); db.conn.close()
        logfile = work / 'test_server.log'
        proc = None
        try:
            with logfile.open('w', encoding='utf-8') as sink:
                proc = subprocess.Popen([sys.executable,'-u','server.py'],cwd=source,env=env,
                    stdout=sink,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
                deadline=time.monotonic()+240
                while time.monotonic()<deadline:
                    if proc.poll() is not None:
                        raise RuntimeError('Private server exit: '+logfile.read_text(errors='replace')[-1800:])
                    if 'World Core nasłuchuje:' in logfile.read_text(errors='replace'):
                        break
                    time.sleep(.4)
                else:
                    raise TimeoutError('Private server startup timeout: '+logfile.read_text(errors='replace')[-1300:])
                print('ERA TCP OTHER RAIDS: isolated server ready, regions='+','.join(slugs), flush=True)
                checks=asyncio.run(scenario(port, slugs))
        except BaseException:
            print('ERA TCP OTHER RAIDS ERROR LOG: '+logfile.read_text(errors='replace')[-1400:],flush=True)
            raise
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                with suppress(subprocess.TimeoutExpired): proc.wait(timeout=15)
                if proc.poll() is None:
                    proc.kill();proc.wait(timeout=8)
        logtext = logfile.read_text(errors='replace')
        assert 'Traceback (most recent call last)' not in logtext, logtext[-1500:]
        db = Database(str(dbpath))
        for login,_ in ACCOUNT_NAMES:
            acc = db.account_by_name(login)
            for slug in slugs:
                for stage in (1,2,3):
                    qid=f'v10300_{slug}_raid_quest_{stage}'
                    q=db.quest(int(acc['id']),qid)
                    assert q and q['status']=='completed' and q['completion_count']==1, (login,qid,dict(q) if q else None)
                    checks+=1
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        checks+=1
        db.conn.close()
        return checks


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Isolated TCP other Era v103 raid journeys')
    parser.add_argument('--regions', default='kuznie,gwiazdy',
                        help='Comma-separated region ids; use all for all 11')
    args=parser.parse_args()
    slugs=tuple(REGIONS if args.regions=='all' else [x.strip() for x in args.regions.split(',')])
    print(f'ERA 103 REAL TCP OTHER RAIDS: {run(slugs)} checks PASS',flush=True)
