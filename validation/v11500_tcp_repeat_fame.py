# -*- coding: utf-8 -*-
"""Real TCP boss-kill regression for delayed repeat EXP and Fame uniqueness.

Uses a disposable SQLite account with its previous one-time Fame credit
explicitly seeded INSIDE the guarded test fixture. Actual `k boss` combat is
run through the full world server. Boss HP is reduced; this is not a balance gate.
"""
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
    TcpPlayer,guarded_child_env,free_local_port,wait_for_world_server,_stop_child,
)
from validation.v11500_tcp_real_fame import ROOT,BOSS_ID,BOSS_NAME


async def repeat_kill(port,db_path):
    hero=TcpPlayer('tcpcheck1','Testtcp1',port)
    await hero.connect_and_login()
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            aid=int(conn.execute("SELECT id FROM accounts WHERE username='tcpcheck1'").fetchone()[0])
            credited=conn.execute('''SELECT region,boss_id FROM fame_bosses_v1702
                WHERE account_id=?''',(aid,)).fetchall()
            assert len(credited)==1 and credited[0][1]==BOSS_ID,repr(credited)
            before=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
        looking=await hero.command('look '+BOSS_NAME,quiet=.18)
        if BOSS_NAME not in looking:
            raise AssertionError('Repeat Fame boss missing in TCP look: '+repr(looking[-800:]))
        await hero.send('k '+BOSS_NAME)
        transcript=''
        waiting=None
        end=time.monotonic()+65
        while time.monotonic()<end:
            try:
                chunk=await asyncio.wait_for(hero.reader.read(16384),1.5)
            except asyncio.TimeoutError:
                chunk=b''
            if chunk: transcript+=chunk.decode('utf8','replace')
            with closing(sqlite3.connect(db_path)) as conn:
                if conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_repeat_exp'").fetchone():
                    waiting=conn.execute('''SELECT kill_token,account_id,boss_id,status,due_at,snapshot
                        FROM v115_fame_repeat_exp WHERE account_id=?''',(aid,)).fetchall()
            if waiting:break
            if 'Wystąpił błąd' in transcript:
                raise AssertionError('Error during repeat kill: '+repr(transcript[-1500:]))
        if len(waiting or [])!=1 or waiting[0][2]!=BOSS_ID or waiting[0][3]!='PENDING':
            raise AssertionError('Actual repeat kill did not create PENDING EXP: '+repr(waiting))
        token,_,boss,status,due_at,snapshot=waiting[0]
        delay=due_at-time.time()
        if not 55<=delay<=305:
            raise AssertionError('Incorrect repeat-kill delay: '+repr(delay))
        content=json.loads(snapshot)
        if not any(content[key]>0 for key in ('character_xp','soul_xp','class_xp','stat_xp')):
            raise AssertionError('Real repeated kill queued zero XP '+repr(content))
        with closing(sqlite3.connect(db_path)) as conn:
            immediate=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
            if immediate!=before:
                raise AssertionError('Repeated Fame EXP incorrectly paid immediately')
            # Allow the real scheduler to execute the due reward by moving only
            # the disposable test row's timestamp, never production constants.
            conn.execute('UPDATE v115_fame_repeat_exp SET due_at=? WHERE kill_token=?',
                         (time.time()-1,token))
            conn.commit()
        exp_pattern='FAME MOB: zaległy EXP za '+BOSS_NAME
        famine='FAMA: +1 za '+BOSS_NAME
        exp_found=False
        end=time.monotonic()+18
        while time.monotonic()<end and not exp_found:
            try:
                piece=await asyncio.wait_for(hero.reader.read(16384),1.8)
            except asyncio.TimeoutError:
                continue
            if not piece: raise AssertionError('Socket dropped before repeat EXP')
            transcript+=piece.decode('utf8','replace')
            exp_found=exp_pattern in transcript
        if not exp_found:
            raise AssertionError('EXP from real repeat kill never delivered: '+repr(transcript[-1200:]))
        # Wait at least one more scheduler interval to prove Fame does not recur.
        await asyncio.sleep(4.0)
        try:
            chunk=await asyncio.wait_for(hero.reader.read(16384),0.3)
        except asyncio.TimeoutError:
            chunk=b''
        transcript+=chunk.decode('utf8','replace')
        if famine in transcript:
            raise AssertionError('Repeat kill incorrectly awarded additional Fame')
        with closing(sqlite3.connect(db_path)) as conn:
            status=conn.execute('SELECT status FROM v115_fame_repeat_exp WHERE kill_token=?',(token,)).fetchone()[0]
            fame=conn.execute('SELECT count(*) FROM fame_bosses_v1702 WHERE account_id=?',(aid,)).fetchone()[0]
            after=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
            check=conn.execute('PRAGMA integrity_check').fetchone()[0]
            if status!='DONE' or fame!=1 or after==before or check!='ok':
                raise AssertionError(f'Invalid repeat payout: {status=}, {fame=}, {after=}, {check=}')
        print('REAL REPEAT TCP PASS: kill stage->60..300 sec pending EXP; '
              'deferred payment; exactly one historical Fame; SQLite intact; soundpack off',flush=True)
    finally:
        await hero.close()


def main():
    with tempfile.TemporaryDirectory(prefix='soulbound-tcp5-v115-repeat-') as td:
        port=free_local_port()
        env,db_path=guarded_child_env(td,port)
        env['SOULBOUND_V115_REAL_FAME_TEST']='1'
        env['SOULBOUND_V115_REPEAT_FAME_TEST']='1'
        env['SOULBOUND_SOUND_EVENTS']='0'
        log=Path(td)/'repeat.log'
        with log.open('w',encoding='utf8') as stream:
            proc=subprocess.Popen([sys.executable,'-u',str(ROOT/'validation/v11500_tcp_real_fame_child.py')],
                cwd=str(ROOT),env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
            try:
                wait_for_world_server(proc,log,seconds=130)
                asyncio.run(repeat_kill(port,db_path))
                stream.flush()
                errors=log.read_text(encoding='utf8',errors='replace')
                if 'Traceback (most recent call last)' in errors:
                    raise AssertionError('Server traceback '+repr(errors[-1500:]))
            except BaseException:
                stream.flush()
                print('REPEAT SERVER LOG TAIL:',log.read_text(encoding='utf8',errors='replace')[-2600:],flush=True)
                raise
            finally:
                _stop_child(proc)

if __name__=='__main__':
    main()
    sys.stdout.flush()
    os._exit(0)
