# -*- coding: utf-8 -*-
"""Synthetic proof for version-specific v109 predeploy, no server/real SQLite."""
from __future__ import annotations
import hashlib
import tempfile
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from predeploy_nowej_wersji import (inspect_zip,verified_staged_pass,
                                    REQUIRED as BASIC)
from aktualizuj_soulbound import archive_mapping,UpdateError
from systems.v10900_activation import REQUIRED as V109_FILES,MARKER

ROOT=Path(__file__).resolve().parents[1]
V108_FILES=('validation/v10800_release_readiness.py',
            'validation/v10800_offline_suite.py',
            'systems/v10800_activation.py',
            'validation/v10800_v107_equipment_compat_gate.py')

def run():
    count=0
    def ck(v,message):
        nonlocal count
        assert v,message
        count+=1
    with tempfile.TemporaryDirectory(prefix='soulbound-v109-pd-') as td:
        home=Path(td)
        names=set(V109_FILES)|set(BASIC)|set(V108_FILES)|{
            'validation/v10900_release_suite.py','CHANGELOG_PL.txt',
            'core/bootstrap_economy_professions.py','VERSION',
        }
        archive=home/'Soulbound-MUD-v109.00.0-test.zip'
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            for rel in sorted(names):z.write(ROOT/rel,'Soulbound-MUD/'+rel)
        version,mapping=inspect_zip(archive)
        ck(version=='109.00.0','version coherent in ZIP / source / title')
        ck('systems/v10900_activation.py' in mapping,'new activation included')
        for invalid in ('','WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\nPLUS CHECKS PASS',
                        'V109 RELEASE GATES PASS\nPLUS CHECKS PASS'):
            log=home/'log.txt'
            log.write_text(invalid,encoding='utf-8')
            ck(not verified_staged_pass(0,log,'109.00.0'),'incomplete proof rejected')
        log.write_text('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\n'
                       'PLUS CHECKS PASS\nV109 RELEASE GATES PASS',encoding='utf-8')
        ck(verified_staged_pass(0,log,'109.00.0'),'all required gates proof recognized')
        ck(not verified_staged_pass(1,log,'109.00.0'),'nonzero exit denies approval')
        ck(not verified_staged_pass(0,log,'108.00.0'),'old release proof not accepted')
        with ZipFile(archive) as z:
            ck(Path('VERSION') in archive_mapping(z),'install mapping retains canonical version')
        forged=home/'Soulbound-MUD-v109.00.0-forged.zip'
        with ZipFile(archive) as source,ZipFile(forged,'w',ZIP_DEFLATED) as target:
            for member in source.namelist():target.writestr(member,source.read(member))
            target.writestr('Soulbound-MUD/'+MARKER,'fake approval')
        try:inspect_zip(forged)
        except ValueError:ck(True,'ZIP-embedded approval denied by PREDEPLOY')
        else:raise AssertionError('fake activation in ZIP accepted')
        with ZipFile(forged) as z:
            try:archive_mapping(z)
            except UpdateError:ck(True,'ZIP-embedded approval denied by installer')
            else:raise AssertionError('installer accepted bundled approval')
    print('V109 PREDEPLOY PROOF:',count,'checks PASS; synthetic only')
    return count

if __name__=='__main__':run()
