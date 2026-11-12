# -*- coding: utf-8 -*-
"""Deploy only the tested, unchanged candidate ZIP after explicit user consent."""
from __future__ import annotations
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from predeploy_nowej_wersji import (ROOT,STATE,sha256,inspect_zip,
                                     version_tuple,installed_version)


def main():
    # Old unconditional block on a bundled v106 test module prevented even a
    # verified, newer release from upgrading. Keep all checks below: 60/60,
    # exact ZIP SHA256, target newer than installed and manual confirmation.
    try:
        if not STATE.is_file():
            raise ValueError('Nie ma zatwierdzonego PREDEPLOY. Najpierw uruchom PREDEPLOY_NOWEJ_WERSJI.bat.')
        s=json.loads(STATE.read_text(encoding='utf-8'))
        if (s.get('status')!='PASS' or s.get('quality_gate')!='ULTIMATE-60-PLUS'
                or s.get('completed_stages')!=60 or s.get('required_stages')!=60):
            raise ValueError('Brak zatwierdzonego wyniku ULTIMATE 60/60 PLUS. Poprzednie PASS 9/9 nie uprawnia do wdrozenia.')
        z=Path(s['zip']).resolve()
        if not z.is_file() or sha256(z)!=s.get('sha256'):
            raise ValueError('ZIP zostal zmieniony po predeploy. Wykonaj test ponownie.')
        ver,_=inspect_zip(z)
        if version_tuple(ver) > (112, 0, 0):
            if (s.get('release_gates_pass') is not True
                    or s.get('installed_at_test') != installed_version()
                    or s.get('returncode') != 0):
                raise ValueError('Brak zgodnego zatwierdzenia 60/60 PLUS dla tej aktualizacji.')
        if ver == '112.00.0':
            if (s.get('v112_release_gates_pass') is not True
                    or s.get('installed_at_test') not in ('110.00.0','111.00.0')
                    or s.get('returncode')!=0):
                raise ValueError('v112: wymagany zgodny PREDEPLOY 60/60 PLUS dla bazy v110/v111.')
        elif ver == '111.00.0':
            if (s.get('v111_release_gates_pass') is not True
                    or s.get('installed_at_test')!='110.00.0'
                    or s.get('returncode')!=0):
                raise ValueError('v111: brak zatwierdzonej bramki lub wersji bazowej.')
        elif ver == '110.00.0':
            if (s.get('v110_release_gates_pass') is not True
                    or s.get('installed_at_test')!='109.00.0'
                    or s.get('returncode')!=0):
                raise ValueError('v110: brak zatwierdzonej osobnej bramki 60/60 PLUS.')
        elif ver == '109.00.0':
            if (s.get('v109_release_gates_pass') is not True
                    or s.get('installed_at_test')!='108.00.0'
                    or s.get('returncode')!=0):
                raise ValueError('v109: brak odrębnego zatwierdzenia PREDEPLOY i wersji bazowej.')
            # Full revalidation (including installed v108 marker) happens
            # in updater before any server STOP, and again after staging.
        elif version_tuple(ver) >= (108, 0, 0) and version_tuple(ver) <= (112, 0, 0):
            raise ValueError('Nieautoryzowana wersja: brak testow LIVE; nie zatrzymano serwera.')
        current=installed_version()
        if ver!=s.get('version') or version_tuple(ver)<=version_tuple(current):
            raise ValueError(f'Wersja kandydata v{ver} nie jest nowsza niz produkcyjna v{current}.')
        print(f'SERWER: v{current}; TESTOWANA WERSJA: v{ver}',flush=True)
        print(f'ZIP: {z}',flush=True)
        print(f'Testy PASS: {s.get("finished_at")}',flush=True)
        print('Stary silnik pozostanie nietkniety; backup zapisow i NOWY katalog gry.',flush=True)
        print('SQLite zostanie skopiowane do nowego katalogu z WAL; stare zapisy pozostana nietkniete.',flush=True)
        print('Zmienione pliki kodu gry: '+str(s.get('changed_game_file_count','brak raportu')),flush=True)
        print('Upewnij sie, ze gracze zakonczyli gre.',flush=True)
        if input('Aby wdrozyc, wpisz dokladnie WDRAZAM: ').strip()!='WDRAZAM':
            print('Anulowano. Gra pozostaje bez zmian.',flush=True)
            return 2
        if sha256(z)!=s['sha256']:
            raise ValueError('Zmiana paczki w trakcie potwierdzania. Wdrozenie anulowane.')
        # The certified candidate supplies its own universal updater. Never
        # execute the installed v109 updater: it does not know v110's safety
        # gate and might reintroduce historical installer dependencies.
        updater = Path(__file__).resolve().with_name('aktualizuj_soulbound.py')
        if not updater.is_file() or updater.is_symlink():
            raise ValueError('Brak bezpiecznego aktualizatora z zatwierdzonego ZIP.')
        env = os.environ.copy()
        env['SOULBOUND_LIVE_ROOT'] = str(ROOT)
        cmd=[sys.executable,'-u',str(updater),str(z),'--yes','--fresh']
        return subprocess.call(cmd,cwd=ROOT,env=env)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('WDROZENIE ZABLOKOWANE: '+str(exc),file=sys.stderr,flush=True)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
