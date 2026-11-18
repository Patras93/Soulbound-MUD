# -*- coding: utf-8 -*-
# Actual localhost TCP Fame boss kill -> delayed EXP/Fame.
# Only disposable low-HP fixture; not a normal difficulty test.
from __future__ import annotations
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
    guarded_child_env, free_local_port, wait_for_world_server, _stop_child,
    TcpPlayer,
)
from world.v10500_region_index import REGIONS
from world.dynamic_content import MOB_TEMPLATES
from systems.fame_v1702 import _is_fame_target

ROOT=Path(__file__).resolve().parents[1]
BOSS_ID='v10500_'+REGIONS[0][0]+'_boss_1'
BOSS_NAME=MOB_TEMPLATES[BOSS_ID]['name']
assert _is_fame_target(MOB_TEMPLATES[BOSS_ID])


def examine(conn, account_id):
    row=conn.execute('''SELECT region,boss_id,status,due_at,fame_due_at FROM
        v115_fame_delivery WHERE account_id=?''',(account_id,)).fetchall()
    return row


async def actual_boss_fight(port, db_path):
    hero=TcpPlayer('tcpcheck1','Testtcp1',port)
    await hero.connect_and_login()
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            aid=int(conn.execute("SELECT id FROM accounts WHERE username='tcpcheck1'").fetchone()[0])
            before=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
        # The `look` and `k` commands are handled by the actual TCP server.
        response=await hero.command('look '+BOSS_NAME,quiet=.15)
        if BOSS_NAME not in response:
            raise AssertionError('Expected natural boss not visible via TCP: '+repr(response[-800:]))
        await hero.send('k '+BOSS_NAME)
        output=''
        deadline=time.monotonic()+65
        waiting=None
        while time.monotonic()<deadline:
            try:
                chunk=await asyncio.wait_for(hero.reader.read(16384), timeout=2.0)
            except asyncio.TimeoutError:
                chunk=b''
            if chunk:
                output+=chunk.decode('utf-8','replace')
            with closing(sqlite3.connect(db_path)) as conn:
                try:
                    waiting=examine(conn,aid)
                except sqlite3.OperationalError:
                    waiting=[]
            if waiting:
                break
            if 'Wystąpił błąd' in output:
                raise AssertionError('Server error during kill: '+repr(output[-1600:]))
        if not waiting:
            raise AssertionError('Real TCP Fame boss kill did not stage a queue. '+repr(output[-1800:]))
        region,boss_id,status,due_at,fame_due_at=waiting[0]
        if boss_id!=BOSS_ID or status!='WAITING':
            raise AssertionError('Unexpected queue after actual kill: '+repr(waiting))
        if not 55<=due_at-time.time()<=305:
            raise AssertionError('Wrong 60-300 sec combat delay: '+repr(due_at-time.time()))
        with closing(sqlite3.connect(db_path)) as conn:
            after=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
            if after!=before:
                raise AssertionError(f'Fame mob credited XP immediately: {before=}, {after=}')
            try:
                credited=conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702 WHERE account_id=?',(aid,)).fetchone()[0]
            except sqlite3.OperationalError:
                credited=0
            if credited:
                raise AssertionError('Fame credited at kill, before delayed EXP')
            snapshot=conn.execute('''SELECT payload FROM v115_fame_reward_snapshot
                WHERE account_id=? AND region=? AND boss_id=?''',(aid,region,boss_id)).fetchone()
            if not snapshot:
                raise AssertionError('Real kill did not save Multi Cap EXP snapshot')
            numbers=json.loads(snapshot[0]); axes=('character_xp','soul_xp','class_xp','stat_xp')
            if not any(int(numbers[a])>0 for a in axes):
                raise AssertionError('Real boss kill generated all-zero EXP: '+repr(numbers))
            # Simulate passage of 60-300 seconds in the disposable DB only.
            # Keeps normal production delay untouched, never sleeps minutes.
            conn.execute('UPDATE v115_fame_delivery SET due_at=? WHERE account_id=?',
                         (time.time()-1,aid))
            conn.commit()
        exp_time=fame_time=None
        exp_pattern='FAME MOB: zaległy EXP za '+BOSS_NAME
        fame_pattern='FAMA: +1 za '+BOSS_NAME
        end=time.monotonic()+24
        while time.monotonic()<end and (exp_time is None or fame_time is None):
            try:
                piece=await asyncio.wait_for(hero.reader.read(16384),timeout=1.8)
            except asyncio.TimeoutError:
                continue
            if not piece:
                raise AssertionError('Disconnected during delayed payout')
            output+=piece.decode('utf-8','replace')
            t=time.monotonic()
            if exp_pattern in output and exp_time is None:exp_time=t
            if fame_pattern in output and fame_time is None:fame_time=t
        if exp_time is None or fame_time is None or fame_time-exp_time<1.8:
            raise AssertionError('Missing/incorrect EXP -> Fame TCP order '+repr(output[-1800:]))
        with closing(sqlite3.connect(db_path)) as conn:
            saved=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
            queue=examine(conn,aid)
            credited=conn.execute('''SELECT COUNT(*) FROM fame_bosses_v1702
                WHERE account_id=? AND boss_id=?''',(aid,BOSS_ID)).fetchone()[0]
            if queue[0][2]!='DONE' or credited!=1 or saved==before:
                raise AssertionError(f'Bad postkill EXP/Fame ledger {queue=} {credited=} {saved=} {before=}')
            integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
            if integrity!='ok':raise AssertionError('SQLite integrity failure: '+str(integrity))
        print('REAL BOSS TCP PASS: natural kill -> pending 60..300 sec; '
              'XP untouched until due; EXP->Fame gap '+str(round(fame_time-exp_time,2))+
              's; exact first Fame once; saved EXP; soundpack off',flush=True)
    finally:
        await hero.close()


def main():
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v115-real-fame-') as td:
        port=free_local_port()
        env,db_path=guarded_child_env(td,port)
        env['SOULBOUND_V115_REAL_FAME_TEST']='1'
        env['SOULBOUND_SOUND_EVENTS']='0'
        log=Path(td)/'live.log'
        with log.open('w',encoding='utf8') as stream:
            proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'validation/v11500_tcp_real_fame_child.py')],
                cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
            try:
                wait_for_world_server(proc,log,seconds=130)
                asyncio.run(actual_boss_fight(port,db_path))
                stream.flush()
                errors=log.read_text(encoding='utf8',errors='replace')
                if 'Traceback (most recent call last)' in errors:
                    raise AssertionError('Server traceback '+repr(errors[-1500:]))
            except BaseException:
                stream.flush()
                print('REAL FAME TCP SERVER LOG TAIL:',log.read_text(encoding='utf8',errors='replace')[-2700:],flush=True)
                raise
            finally:
                _stop_child(proc)

if __name__=='__main__':
    main()
    sys.stdout.flush()
    os._exit(0)
