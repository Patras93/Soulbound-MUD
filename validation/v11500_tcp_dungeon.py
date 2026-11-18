# -*- coding: utf-8 -*-
"""Real v115 dungeon-warden TCP kill and objective/SQLite payout.

Starts inside the final chamber of a disposable server with 1-HP boss.
Separate world graph tests cover navigation. This does NOT test normal balance.
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
    TcpPlayer,guarded_child_env,free_local_port,wait_for_world_server,_stop_child,
)
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import room_id,warden_id,WIDTH,HEIGHT
from data.mobs import MOB_TEMPLATES

ROOT=Path(__file__).resolve().parents[1]
REGION=REGIONS[0].key
BOSS_ID=warden_id(REGION)
BOSS_NAME=MOB_TEMPLATES[BOSS_ID]['name']
LAST_ROOM=room_id(REGION,WIDTH-1,HEIGHT-1)
START_ROOM=LAST_ROOM

async def real_dungeon(port,db_path):
    hero=TcpPlayer('tcpcheck1','Testtcp1',port)
    await hero.connect_and_login()
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            aid=int(conn.execute("SELECT id FROM accounts WHERE username='tcpcheck1'").fetchone()[0])
            silver_before=int(conn.execute('SELECT silver FROM characters WHERE account_id=?',(aid,)).fetchone()[0])
        await hero.command('look',quiet=.15)
        # The movement can award sizeable EP and enqueue many skill/level
        # messages. Do not mistake that backlog for the response to `look`.
        # A verified SQLite combat objective is the authoritative kill signal.
        await hero.send('k Strażnik Podziemi')
        deadline=time.monotonic()+18
        confirmed=False
        transcript=''
        while time.monotonic()<deadline:
            try:
                data=await asyncio.wait_for(hero.reader.read(16384),timeout=1.5)
            except asyncio.TimeoutError:
                data=b''
            if data:transcript+=data.decode('utf8','replace')
            if 'Wystąpił błąd' in transcript:
                raise AssertionError('Runtime failure during boss kill: '+transcript[-1500:])
            with closing(sqlite3.connect(db_path)) as conn:
                table=conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='v115_objective_totals'").fetchone()
                if table:
                    row=conn.execute("SELECT amount FROM v115_objective_totals WHERE account_id=? AND region=? AND objective='finish_dungeon'",(aid,REGION)).fetchone()
                    if row and int(row[0])>=1:
                        confirmed=True
                        break
        if not confirmed:
            raise AssertionError('Natural TCP warden kill did not credit finish_dungeon; '+repr(transcript[-1500:]))
        with closing(sqlite3.connect(db_path)) as conn:
            objectives=dict(conn.execute("SELECT objective, amount FROM v115_objective_totals WHERE account_id=? AND region=?",(aid,REGION)).fetchall())
            assert objectives.get('finish_dungeon')==1,objectives
            assert objectives.get('defeat_boss')==1,objectives
            assert objectives.get('defeat_enemy')==1,objectives
            claims=conn.execute("SELECT COUNT(*) FROM v115_objective_claims WHERE account_id=?",(aid,)).fetchone()[0]
            silver_after=int(conn.execute('SELECT silver FROM characters WHERE account_id=?',(aid,)).fetchone()[0])
            integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
            if integrity!='ok' or claims<1 or silver_after<silver_before:
                raise AssertionError(f'Incorrect rewards: {claims=} {silver_before=} {silver_after=} {integrity=}')
        print('LIVE DUNGEON TCP PASS: final-room fixture, real warden kill, '
              f'objectives {objectives}, claims {claims}, SQLite {integrity}, '
              'soundpack off, isolated disposable test',flush=True)
    finally:await hero.close()


def main():
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v115-dungeon-') as td:
        port=free_local_port()
        env,db_path=guarded_child_env(td,port)
        env['SOULBOUND_SOUND_EVENTS']='0'
        env['SOULBOUND_V115_DUNGEON_TEST']='1'
        log=Path(td)/'dungeon_server.log'
        with log.open('w',encoding='utf8') as out:
            proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'validation/v11500_tcp_dungeon_child.py')],
                cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT)
            try:
                wait_for_world_server(proc,log,seconds=130)
                asyncio.run(real_dungeon(port,db_path))
                out.flush()
                content=log.read_text(encoding='utf8',errors='replace')
                if 'Traceback (most recent call last)' in content:
                    raise AssertionError('Server traceback '+repr(content[-1700:]))
            except BaseException:
                out.flush()
                print('DUNGEON TCP LOG:',log.read_text(encoding='utf8',errors='replace')[-3000:],flush=True)
                raise
            finally:
                _stop_child(proc)

if __name__=='__main__':
    main()
    sys.stdout.flush()
    os._exit(0)
