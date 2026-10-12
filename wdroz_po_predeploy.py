# -*- coding: utf-8 -*-
"""Deploy only the tested, unchanged candidate ZIP after explicit user consent."""
from __future__ import annotations
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from predeploy_nowej_wersji import (ROOT,STATE,sha256,inspect_zip,
                                     version_tuple,installed_version)


def main():
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
        current=installed_version()
        if ver!=s.get('version') or version_tuple(ver)<=version_tuple(current):
            raise ValueError(f'Wersja kandydata v{ver} nie jest nowsza niz produkcyjna v{current}.')
        print(f'SERWER: v{current}; TESTOWANA WERSJA: v{ver}',flush=True)
        print(f'ZIP: {z}',flush=True)
        print(f'Testy PASS: {s.get("finished_at")}',flush=True)
        print('ZA CHWILE aktualizator zatrzyma gre, zrobi backup, podmieni kod i uruchomi serwer.',flush=True)
        print('NIE nadpisze baz SQLite, WAL/SHM, zapisow postaci ani logow.',flush=True)
        print('Zmienione pliki kodu gry: '+str(s.get('changed_game_file_count','brak raportu')),flush=True)
        print('Upewnij sie, ze gracze zakonczyli gre.',flush=True)
        if input('Aby wdrozyc, wpisz dokladnie WDRAZAM: ').strip()!='WDRAZAM':
            print('Anulowano. Gra pozostaje bez zmian.',flush=True)
            return 2
        if sha256(z)!=s['sha256']:
            raise ValueError('Zmiana paczki w trakcie potwierdzania. Wdrozenie anulowane.')
        cmd=[sys.executable,'-u',str(ROOT/'aktualizuj_soulbound.py'),str(z),'--yes']
        return subprocess.call(cmd,cwd=ROOT)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('WDROZENIE ZABLOKOWANE: '+str(exc),file=sys.stderr,flush=True)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
