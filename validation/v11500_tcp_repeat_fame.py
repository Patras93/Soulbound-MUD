# -*- coding: utf-8 -*-
"""Real TCP boss-kill regression for immediate repeat EXP and Fame uniqueness.

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
        # The login prompt may arrive before the test fixture finishes
        # enter_world() and writes its one-time Fame ledger. The `look`
        # response confirms the character has entered the game world.
        looking=await hero.command('look '+BOSS_NAME,quiet=.18)
        if BOSS_NAME not in looking:
            raise AssertionError('Repeat Fame boss missing in TCP look: '+repr(looking[-800:]))
        with closing(sqlite3.connect(db_path)) as conn:
            aid=int(conn.execute("SELECT id FROM accounts WHERE username='tcpcheck1'").fetchone()[0])
            credited=conn.execute('''SELECT region,boss_id FROM fame_bosses_v1702
                WHERE account_id=?''',(aid,)).fetchall()
            assert len(credited)==1 and credited[0][1]==BOSS_ID,repr(credited)
            before=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
        await hero.send('k '+BOSS_NAME)
        transcript=''
        deadline=time.monotonic()+65
        paid=False
        while time.monotonic()<deadline:
            try:
                chunk=await asyncio.wait_for(hero.reader.read(16384),1.5)
            except asyncio.TimeoutError:
                chunk=b''
            if chunk:
                transcript+=chunk.decode('utf8','replace')
            if 'Wystąpił błąd' in transcript:
                raise AssertionError('Error during repeat kill: '+repr(transcript[-1500:]))
            if 'FAME MOB: zwykły EXP za zabicie otrzymujesz od razu.' in transcript:
                paid=True
                break
        if not paid:
            raise AssertionError('Real repeat kill did not finish immediate EXP award: '+repr(transcript[-1800:]))
        # The game emits its combat messages before the outer kill SAVEPOINT
        # finishes all unrelated loot/quest bookkeeping. Confirm EXP after
        # durable COMMIT, not merely after the first socket notification.
        after=before
        commit_deadline=time.monotonic()+25
        while after==before and time.monotonic()<commit_deadline:
            with closing(sqlite3.connect(db_path)) as conn:
                after=conn.execute('SELECT character_xp,soul_xp,stat_progress FROM characters WHERE account_id=?',(aid,)).fetchone()
            if after==before:
                await asyncio.sleep(0.25)
        if after==before:
            raise AssertionError(f'Repeat Fame boss EXP not committed: {before=}, {after=}; output '+repr(transcript[-1800:]))
        with closing(sqlite3.connect(db_path)) as conn:
            queued=conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_repeat_exp'").fetchone()
            repeats=conn.execute('SELECT COUNT(*) FROM v115_fame_repeat_exp WHERE account_id=?',(aid,)).fetchone()[0] if queued else 0
            fame=conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702 WHERE account_id=?',(aid,)).fetchone()[0]
            integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
            if repeats!=0 or fame!=1 or integrity!='ok':
                raise AssertionError(f'Repeat credited wrong queue/fame/integrity {repeats=}, {fame=}, {integrity=}')
        # A Fame point is once per boss; repeated kill never produces another.
        if 'FAMA: +1 za '+BOSS_NAME in transcript:
            raise AssertionError('Repeat kill incorrectly awarded extra Fame')
        print('REAL REPEAT TCP PASS: normal EXP at death; no new delayed row; '
              'exactly one historical Fame; SQLite intact; soundpack off',flush=True)
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
