# -*- coding: utf-8 -*-
"""Isolated full 24-room TCP dungeon walk, victory and return.

Tests real direction commands and persisted objectives. Boss is 1 HP in the
child ONLY; this is not a combat-duration or native Windows benchmark.
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
import time

from validation.v2102_tcp_six_players import (
    TcpPlayer, guarded_child_env, free_local_port, wait_for_world_server, _stop_child,
)
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import WIDTH, HEIGHT, room_id

ROOT=Path(__file__).resolve().parents[1]
REGION=REGIONS[0].key


def snake_walk():
    """Visit every chamber with actual exits, then end at the real boss."""
    x=y=0
    visited={(x,y)}
    route=[]
    for row in range(HEIGHT):
        if row:
            y+=1
            route.append(('north',x,y))
            visited.add((x,y))
        direction=1 if row%2==0 else -1
        for _ in range(WIDTH-1):
            x+=direction
            route.append(('east' if direction>0 else 'west',x,y))
            visited.add((x,y))
    # Even-height serpentine terminates at x=0, unlike the boss at (5,3).
    while x<WIDTH-1:
        x+=1
        route.append(('east',x,y))
    assert len(visited)==WIDTH*HEIGHT and (x,y)==(WIDTH-1,HEIGHT-1)
    return route


async def await_room(hero, target_x, target_y, *, timeout=12):
    marker=f'Sektor {target_x+1}/{WIDTH}, pas {target_y+1}/{HEIGHT}'
    data=''
    deadline=time.monotonic()+timeout
    while marker not in data and time.monotonic()<deadline:
        try:
            fragment=await asyncio.wait_for(hero.reader.read(16384),
                                            max(.05,min(2,deadline-time.monotonic())))
        except asyncio.TimeoutError:
            continue
        if not fragment:
            raise AssertionError('TCP rozłączone w trakcie podróży')
        data+=fragment.decode('utf8','replace')
        if len(data)>200000:
            data=data[-100000:]
        if 'Wystąpił błąd komendy' in data or 'Wystąpił błąd sesji' in data:
            raise AssertionError('Błąd ruchu TCP: '+data[-600:])
        if ('Nie możesz iść' in data or 'Trwa poprzedni krok' in data):
            raise AssertionError('Ruch nie wykonany: '+data[-600:])
    if marker not in data:
        raise AssertionError(f'Nie osiągnięto {marker}: '+data[-800:])


async def test_walk(port, db_path):
    hero=TcpPlayer('tcpcheck1','Testtcp1',port)
    await hero.connect_and_login()
    try:
        await hero.send('look')
        await await_room(hero,0,0,timeout=35)
        route=snake_walk()
        for n,(direction,x,y) in enumerate(route,1):
            await hero.send(direction)
            await await_room(hero,x,y)
        with closing(sqlite3.connect(db_path)) as conn:
            account_id=conn.execute("SELECT id FROM accounts WHERE username='tcpcheck1'").fetchone()[0]
            row=conn.execute("SELECT amount FROM v115_objective_totals WHERE account_id=? AND region=? AND objective='finish_dungeon'",(account_id,REGION)).fetchone()
            if row and row[0]:
                raise AssertionError('Ukończenie lochu przed pokonaniem strażnika')
        await hero.send('k Strażnik Podziemi')
        deadline=time.monotonic()+24
        defeated=False
        while time.monotonic()<deadline:
            with closing(sqlite3.connect(db_path)) as conn:
                row=conn.execute("SELECT amount FROM v115_objective_totals WHERE account_id=? AND region=? AND objective='finish_dungeon'",(account_id,REGION)).fetchone()
                if row and row[0]==1:
                    defeated=True
                    break
            # Clear pending text without assuming a particular notification order.
            try:
                await asyncio.wait_for(hero.reader.read(16384),.5)
            except asyncio.TimeoutError:
                # Only the optional TCP text drain timed out; SQLite below
                # remains the authoritative victory signal.
                continue
        if not defeated:
            raise AssertionError('Zabicie strażnika nie ukończyło podziemi')
        # Return along real exits, not teleport/recall. From (5,3) to (0,0).
        for x in range(WIDTH-2,-1,-1):
            await hero.send('west')
            await await_room(hero,x,HEIGHT-1)
        for y in range(HEIGHT-2,-1,-1):
            await hero.send('south')
            await await_room(hero,0,y)
        with closing(sqlite3.connect(db_path)) as conn:
            assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            row=conn.execute("SELECT amount FROM v115_objective_totals WHERE account_id=? AND region=? AND objective='finish_dungeon'",(account_id,REGION)).fetchone()
            assert row and row[0]==1
        print(f'DUNGEON FULL ROUTE TCP PASS: {WIDTH*HEIGHT} chambers, {len(route)} onward moves, '
              f'{WIDTH-1+HEIGHT-1} return moves; boss defeat once, SQLite OK; soundpack OFF',flush=True)
    finally:
        await hero.close()


def main():
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v115-dungeon-route-') as td:
        port=free_local_port()
        env,db_path=guarded_child_env(td,port)
        env['SOULBOUND_SOUND_EVENTS']='0'
        env['SOULBOUND_V115_DUNGEON_TEST']='1'
        env['SOULBOUND_V115_DUNGEON_ROUTE_TEST']='1'
        log=Path(td)/'dungeon_route_server.log'
        with log.open('w',encoding='utf8') as output:
            proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'validation/v11500_tcp_dungeon_child.py')],
                cwd=str(ROOT),env=env,stdout=output,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
            try:
                wait_for_world_server(proc,log,seconds=130)
                asyncio.run(test_walk(port,db_path))
                output.flush()
                log_text=log.read_text(encoding='utf8',errors='replace')
                if 'Traceback (most recent call last)' in log_text:
                    raise AssertionError('Server traceback '+repr(log_text[-1200:]))
            except BaseException:
                output.flush()
                print('ROUTE TCP SERVER LOG:',log.read_text(encoding='utf8',errors='replace')[-3000:],flush=True)
                raise
            finally:
                _stop_child(proc)

if __name__=='__main__':
    main()
