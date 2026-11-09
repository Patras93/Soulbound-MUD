# -*- coding: utf-8 -*-
"""All 33 v107 safety/content slots on v110, adapting legacy-only assumptions.

Obsolete installer checks, exactly-30 registry assumptions, and an obsolete
TCP scratch-path are replaced by v110 compatibility checks. The functional
EQ/quest/combat coverage remains active in v110 equivalents, and the real
six-player TCP test runs separately as an obligatory fourth v110 gate. Independent v110 6/6 TCP, release, and
snapshot checks remain separately mandatory during Windows PREDEPLOY.
"""
from __future__ import annotations
import ast,os,shutil,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audyt_v107_windows_przed_predeploy import SUITES,call,ignored
REPLACEMENTS={
 'v8500_native_tcp_full_journey':('V110: dawna bramka TCP zachowana; 6 graczy osobno obowiązkowo','v11000_v85_tcp_compat'),
 'v10700_consolidated_content_regression':('V110: komplet zawartości v107, 30 historycznych klas i ras','v11000_v107_catalog_compat'),
 'v10700_equipment_write_barrier_regression':('V110: pełna ochrona fizycznego EQ bez starych instalatorów','v11000_equipment_barrier_compat'),
 'v10700_activation_regression':('V110: manifest instalacji i niezmienność plików','v11000_activation_regression'),
 'v10700_upgrade_activation_install_regression':('V110: rzeczywisty test aktualizatora i backupu','v11000_release_install_regression'),
 'v10700_installer_bridge_regression':('V110: tylko WDRAZAM oraz SHA','v11000_update_consent_regression'),
}

def main():
    if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()!='110.00.0':
        print('V110/V107 AUDIT FAIL: expected v110 source, never an old release',flush=True)
        return 2
    checked=0;fails=[]
    with tempfile.TemporaryDirectory(prefix='sb110_audit_code_') as temp:
        stage=Path(temp)/'Soulbound-MUD'
        shutil.copytree(ROOT,stage,ignore=ignored)
        srcs=list(stage.rglob('*.py'))
        for p in srcs:
            ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
        if not srcs:raise AssertionError('No source files in private audit')
        print(f'V110 V107 AUDIT: {len(srcs)} AST-valid sources, private TEMP only',flush=True)
        for n,(title,module,args,deadline) in enumerate(SUITES,1):
            if module in REPLACEMENTS:
                title,module=REPLACEMENTS[module]
                args=()
            code,output,duration=call(stage,'validation.'+module,args,deadline)
            checked+=1
            print(f'{n:02d}/{len(SUITES)} {"PASS" if code==0 else "FAIL"} '
                  f'{title}: {duration}s',flush=True)
            if code:
                fails.append((title,output[-550:]))
                print('REASON: '+output[-550:],flush=True)
        code,output,duration=call(stage,'validation.v11000_release_readiness',(),60)
        if code: fails.append(('V110 readiness',output[-550:]));print('READINESS FAIL '+output[-550:],flush=True)
        else:print('V110 READINESS: PASS',flush=True)
    if fails:
        print(f'V110/V107 FUNCTIONAL AUDIT FAIL: {len(fails)} failures / {checked} historical slots',flush=True)
        return 1
    print(f'V110/V107 FUNCTIONAL AUDIT PASS: {checked}/{len(SUITES)} slots; '
          f'{len(REPLACEMENTS)} legacy-only slots adapted with v110 safety and functional tests',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
