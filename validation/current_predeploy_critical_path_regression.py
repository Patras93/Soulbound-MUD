# -*- coding: utf-8 -*-
"""Critical-path scheduler proof: full 60 PLUS and extra checks never disappear.

Only synthetic isolated files and mocks; production SQLite is not touched.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import threading
import time


def run_regression():
    import testuj_soulbound_windows as runner
    tests=0
    legacy=len(runner.STAGES)
    assert legacy==60; tests+=1
    extra=(
        ('V105 KATALOGI I BALANS','balance.py',120),
        ('V105 MIGRACJA PRAWDZIWEJ BAZY TYLKO KOPIA','sqlite.py',120),
        ('V105 BOSSOWIE TCP 5 KLIENTOW / QUEST I NAGRODY','boss.py',120),
        ('FIZYCZNE EQ NA KOPII BAZY','eq.py',120),
        ('SZESC GRACZY TCP, QUESTY I RESTART','six.py',120),
    )
    all_gates=runner.STAGES+extra
    assert len(all_gates)==65;tests+=1
    indices=runner.critical_path_stage_order(all_gates,post60_count=len(extra))
    assert sorted(indices)==list(range(65));tests+=1
    first_names=[all_gates[index][0] for index in indices[:6]]
    assert first_names==[
        'SZYBKI PREDEPLOY','PELNY AUDYT','5 KLIENTOW TCP + RESTART',
        'V105 BOSSOWIE TCP 5 KLIENTOW / QUEST I NAGRODY',
        'SZESC GRACZY TCP, QUESTY I RESTART','V105 KATALOGI I BALANS',
    ],first_names
    tests+=1
    assert runner.critical_path_stage_order(runner.STAGES)==[
        *[i for i in range(60) if i!=8],8];tests+=1
    assert runner.recommended_predeploy_workers(16,12*1024**3)==8;tests+=1
    with TemporaryDirectory(prefix='sb_critical_path_') as temporary:
        root=Path(temporary)/'tiny';root.mkdir()
        (root/'VERSION').write_bytes(b'114.00.9\n')
        for _,script,_ in all_gates:
            path=root/script.split()[0]
            path.parent.mkdir(parents=True,exist_ok=True)
            path.touch()
        seen=[];roots=[];environments=[];lock=threading.Lock()
        def fake_stage(script,env,deadline,say,*,root=None,stop_event=None):
            with lock:
                seen.append(script)
                roots.append(root)
                environments.append(env['SOULBOUND_DB'])
            say('synthetic pass')
            return 0
        records=[]
        with patch.object(runner,'ROOT',root),\
             patch.object(runner,'stage_env',side_effect=lambda temp:{'SOULBOUND_DB':str(Path(temp)/'isolated.sqlite'),'SOULBOUND_HOST':'127.0.0.1'}),\
             patch.object(runner,'run_stage',side_effect=fake_stage):
            result=runner.run_parallel_stages(all_gates,records.append,
                 max_workers=1,post60_count=5)
        assert len(result)==65 and all(code==0 for _,code in result);tests+=1
        assert len(seen)==65 and sorted(seen)==sorted(s for _,s,_ in all_gates);tests+=1
        assert len(set(environments))==65;tests+=1
        assert all(Path(path).name=='isolated.sqlite' for path in environments);tests+=1
        assert any('START: ETAP 60/60:' in msg for msg in records);tests+=1
        assert any('START: DODATKOWE 5/5:' in msg for msg in records);tests+=1
        assert any('START: ETAP 9/60:' in msg for msg in records);tests+=1
        assert all('PASS' in msg for msg in records if msg.startswith('KONIEC:'));tests+=1
        # Confirm a failing future gate never becomes a fake pass. All
        # trailing not-started stages receive nonzero abort status (125).
        failed=[]
        def broken_stage(script,env,deadline,say,*,root=None,stop_event=None):
            failed.append(script)
            if script=='six.py':return 7
            return 0
        with patch.object(runner,'ROOT',root),\
             patch.object(runner,'stage_env',return_value={'SOULBOUND_DB':str(root/'fake.sqlite')}),\
             patch.object(runner,'run_stage',side_effect=broken_stage):
            results=runner.run_parallel_stages(all_gates,lambda _:None,
                 max_workers=1,post60_count=5)
        assert len(results)==65;tests+=1
        assert results[64][1]==7;tests+=1
        assert results[64][1]==7 and all(results[i][1]==125 for i in indices[5:]);tests+=1
        assert all(results[i][1]!=0 for i in range(60) if i not in (0,1,8));tests+=1
    print(f'CURRENT PREDEPLOY CRITICAL PATH: {tests}/{tests} PASS')
    return tests


if __name__=='__main__':run_regression()
