# -*- coding: utf-8 -*-
"""Isolated real 2-player TCP smoke for v103 (no production accounts/database).

Actual server.py, TCP telnet, login, commands, party creation/invitation.
NPC quest SQLite and raid phases remain separately tested: this test does not
claim full boss combat or endgame quest turn-in over TCP.
"""
from __future__ import annotations
import asyncio
from contextlib import suppress
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from arena_real_izolowana import _ignore
from validation.v2102_tcp_six_players import TcpPlayer, free_local_port, guarded_child_env

ROOT = Path(__file__).resolve().parents[1]

async def journey(port):
    players = [TcpPlayer('era103tcpone','Era103One',port),
               TcpPlayer('era103tcptwo','Era103Two',port)]
    checks=0
    try:
        for c in players:
            await c.connect_and_login()
            checks+=1
        for c in players:
            for cmd, words in [('who',('Era103','gracz','online')),
                               ('look',('Świątyn','Swiatyn','Miejsce','Wyjści')),
                               ('quests',('ZADAN','Zada','quest')),
                               ('expbank',('EXP','exp'))]:
                out=await c.command(cmd)
                assert out.strip() and any(w.casefold() in out.casefold() for w in words), (cmd,out[-600:])
                checks+=1
        lead, guest=players
        out=await lead.command('druzyna zaloz')
        assert 'drużyn' in out.casefold() or 'druzyn' in out.casefold(),out[-500:]
        checks+=1
        invite=await lead.command('druzyna zapros Era103Two')
        checks+=int(bool(invite.strip()))
        answer=await guest.command('dolacz')
        assert 'dołącza' in answer.casefold() or 'drużyn' in answer.casefold() or 'druzyn' in answer.casefold(),answer[-450:]
        checks+=1
        state=await lead.command('druzyna')
        assert 'Era103Two' in state, state[-500:]
        checks+=1
        # The newly authored world must be visible from the actual game process;
        # start at Temple per the documented player-login rule.
        out=await lead.command('expareas')
        assert out.strip(), 'No XP areas response'
        checks+=1
        return checks
    finally:
        await asyncio.gather(*(c.close() for c in players))


def run():
    with tempfile.TemporaryDirectory(prefix='sb103-real-tcp-') as td:
        work=Path(td)
        source=work/'server_source'
        shutil.copytree(ROOT,source,ignore=_ignore)
        assert not (source/'soulbound.db').exists(), 'Test accidentally copied a player database'
        port=free_local_port()
        env,db_path=guarded_child_env(source,port)
        # Only isolated test accounts, created before the private child launches.
        from core.classes_skills import CLASSES, RACES
        from storage.database import Database
        db=Database(str(db_path))
        for username,char in [('era103tcpone','Era103One'),('era103tcptwo','Era103Two')]:
            aid=db.create_account(username,'test_only_tcp_2026_password')
            db.create_character_for_master(aid,char,RACES[0],CLASSES[0],
                {k:char for k in ('nom','gen','dat','acc','ins','loc','voc')})
        db.conn.commit()
        for username, char in [('era103tcpone','Era103One'),('era103tcptwo','Era103Two')]:
            account = db.account_by_name(username)
            selected = db.characters_for_master(int(account['id']))
            assert len(selected) == 1 and selected[0]['name'] == char, (username, 'Missing linked character')
        db.conn.close()
        logfile=work/'tcp_stage7.log'
        proc=None
        try:
            with logfile.open('w',encoding='utf-8') as sink:
                proc=subprocess.Popen([sys.executable,'-u','server.py'],cwd=source,env=env,
                    stdout=sink,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
                deadline=time.monotonic()+190
                while time.monotonic()<deadline:
                    if proc.poll() is not None:
                        raise RuntimeError('Server failed to boot: '+logfile.read_text(errors='replace')[-2400:])
                    if 'World Core nasłuchuje:' in logfile.read_text(errors='replace'):
                        break
                    time.sleep(.3)
                else:
                    raise TimeoutError('No readiness: '+logfile.read_text(errors='replace')[-1800:])
                import asyncio
                checks=asyncio.run(journey(port))
                assert checks>=14,(checks,'Too few real TCP checks')
                print(f'ERA v103 REAL 2-PLAYER TCP LOGIN/PARTY/COMMANDS: {checks} PASS',flush=True)
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=16)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait(timeout=6)
        text=logfile.read_text(encoding='utf-8',errors='replace')
        assert 'Traceback (most recent call last)' not in text,text[-1500:]
        return checks+2

if __name__=='__main__':
    print(f'ERA v103 TCP ISOLATED SMOKE: {run()} checks PASS',flush=True)
