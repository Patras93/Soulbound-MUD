# -*- coding: utf-8 -*-
"""Required v105 quality gates for the same ZIP used by Windows 60 PLUS.

Each child is isolated so bootstrap mutations from older v103/v104 tests cannot
make a false positive (or trigger duplicate historical catalogs).
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
TESTS=(
    ('v105 regiony, questy, Soul Tier i EQ', 'validation.v10500_first_integrity', 180),
    ('v105 osiągalność 1000 questów', 'validation.v10500_quest_reachability', 180),
    ('v105 księgowanie 600 questów bojowych SQLite', 'validation.v10500_kill_quest_sqlite', 180),
    ('v105 bossowie runtime i odradzanie', 'validation.v10500_boss_runtime_audit', 180),
    ('v105 balans numeryczny 160 mobów i 40 bossów', 'validation.v10500_high_level_balance_audit', 180),
)
def main():
    assert (ROOT/'validation/v10500_first_integrity.py').exists()
    env=os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
    for title,module,deadline in TESTS:
        print('V105 RELEASE CHECK: '+title,flush=True)
        p=subprocess.run([sys.executable,'-u','-m',module],cwd=ROOT,
                         env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                         encoding='utf-8',errors='replace',timeout=deadline)
        print(p.stdout[-4000:],flush=True)
        if p.returncode:
            raise RuntimeError('V105 CHECK FAIL: '+title+' | code '+str(p.returncode))
        if 'PASS' not in p.stdout:
            raise RuntimeError('V105 CHECK bez potwierdzenia PASS: '+title)
    print('V105 EXTRA RELEASE QUALITY GATE: '+str(len(TESTS))+'/'+str(len(TESTS))+' PASS',flush=True)
if __name__=='__main__':main()
