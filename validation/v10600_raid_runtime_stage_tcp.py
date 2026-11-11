# -*- coding: utf-8 -*-
"""Jeden NATURALNY cios TCP w bossa rajdu 26 i zgodność realnej sali.

W przeciwieństwie do symulacji DPS i komendy admin `wyrok` rzeczywisty
klient wykonuje zwykłe `attack`; nie wykonuje sztucznego dobicia ani nie
zmienia HP, obrażeń lub zegara walki. Wyłącznie izolowana baza SQLite.
"""
from __future__ import annotations
import asyncio
from contextlib import suppress, closing
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
from validation.v2102_tcp_six_players import (
    TcpPlayer,guarded_child_env,free_local_port,wait_for_world_server,_stop_child)
ROOT=Path(__file__).resolve().parents[1]

async def encounter(port):
    player=TcpPlayer('natural10601','Natural10601',port)
    try:
        await player.connect_and_login()
        status=await player.command('attack Strażnik Progu',quiet=.25)
        if 'Trafiasz ' not in status or 'Przeciwnik:' not in status:
            raise AssertionError('Brak rzeczywistego normalnego trafienia: '+status[-900:])
        hp=re.findall(r'Przeciwnik:\s*(\d+)\s+z\s+(\d+)\s+życia',status)
        if not hp:
            raise AssertionError('Brak HP bossa po prawdziwym ataku: '+status[-650:])
        remain,maximum=map(int,hp[-1])
        assert 0<=remain<maximum,(remain,maximum)
        assert 'ADMIN CIOS' not in status
        return remain,maximum
    finally:
        await player.close()

def run():
    assert os.environ.get('SOULBOUND_V106_STAGING')!='1','testowy rodzic bez staging'
    with tempfile.TemporaryDirectory(prefix='soulbound-v106-natural-party-') as directory:
        work=Path(directory)
        port=free_local_port()
        env,_=guarded_child_env(work,port)
        db=work/'natural_raid.sqlite'
        env.update(SOULBOUND_DB=str(db),SOULBOUND_V106_STAGING='1',
                   SOULBOUND_V106_NATURAL_RAID_TEST='1',
                   SOULBOUND_V106_NATURAL_COUNT='2',
                   SOULBOUND_V106_NATURAL_RAID='26',
                   SOULBOUND_MAX_CLIENTS='2',PYTHONPATH=str(ROOT))
        env.pop('SOULBOUND_ADMIN_ACCOUNTS',None)
        log=work/'runtime_stage.log'
        process=None
        checks=0
        try:
            with log.open('w',encoding='utf-8') as sink:
                process=subprocess.Popen([sys.executable,'-B','-u',
                    str(ROOT/'validation/v10600_tcp_raid_normal_attack_child.py')],
                    env=env,cwd=ROOT,stdout=sink,stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL)
                wait_for_world_server(process,log,seconds=150)
                checks+=1
                remain,maximum=asyncio.run(encounter(port))
                checks+=1
            _stop_child(process);process=None
            # Stary błąd: 1,64 mld HP -> 12,95 biliarda HP nawet przy Soul34001.
            # Dopuszczamy naturalne Adaptive Combat, ale nie wzrost o miliony.
            record=work/'natural_scale.jsonl'
            assert record.exists(), 'Brak obserwacji realnego skalowania'
            records=[json.loads(line) for line in record.read_text(encoding='utf-8').splitlines() if line.strip()]
            boss_records=[r for r in records if r['mob_id']=='v10600_raid_26_boss_1']
            assert boss_records,records;checks+=1
            authored=int(boss_records[0]['base_hp'])
            assert authored>0 and maximum>=authored;checks+=1
            assert maximum<=authored*100,(maximum,authored);checks+=1
            assert all(r['effective']==34001 and r['room_stage']==34001 for r in boss_records),boss_records
            checks+=1
            assert all(r['soul']==34001 and r['staging']=='1' for r in boss_records)
            checks+=1
            hits=work/'natural_hits.jsonl'
            assert hits.exists();checks+=1
            rows=[json.loads(line) for line in hits.read_text(encoding='utf-8').splitlines() if line.strip()]
            assert rows and any(int(r['damage'])>0 for r in rows);checks+=1
            with closing(sqlite3.connect(db)) as conn:
                assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok';checks+=1
            text=log.read_text(encoding='utf-8',errors='replace')
            assert 'Traceback (most recent call last)' not in text;checks+=1
            print(f'V106 NATURAL TCP 1 gracz, raid 26: {checks} PASS; '
                  f'HP {remain:,}/{maximum:,}; bez admin kill i bez obniżenia bossa',flush=True)
            return checks
        except BaseException:
            if log.exists():print('V106 NATURAL BŁĄD SERWERA: '+log.read_text(encoding='utf8',errors='replace')[-1600:],flush=True)
            raise
        finally:
            _stop_child(process)

if __name__=='__main__':run()
