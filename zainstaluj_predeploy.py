# -*- coding: utf-8 -*-
"""Bootstrap only predeploy tools into the already installed production folder."""
from pathlib import Path
import shutil
import sys

SOURCE=Path(__file__).resolve().parent
TOOLS=('PREDEPLOY_NOWEJ_WERSJI.bat','predeploy_nowej_wersji.py',
       'WDROZ_PO_PREDEPLOY.bat','wdroz_po_predeploy.py',
       'aktualizuj_soulbound.py')

def main():
    target=Path(sys.argv[1] if len(sys.argv)>1 else 'C:/Soulbound-MUD').resolve()
    if not (target/'server.py').is_file() or not (target/'aktualizuj_soulbound.py').is_file():
        print('BLAD: '+str(target)+' nie jest folderem glownej instalacji Soulbound.')
        print('Mozesz przekazac inna sciezke: ZAINSTALUJ_PREDEPLOY.bat "D:\\Soulbound-MUD"')
        return 2
    if target==SOURCE:
        print('To ten sam folder. Narzedzia sa juz tutaj.')
        return 0
    if not all((SOURCE/x).is_file() for x in TOOLS):
        print('BLAD: w paczce brakuje narzedzi predeploy.')
        return 2
    for name in TOOLS:
        shutil.copy2(SOURCE/name,target/name)
    (target/'NOWE_WERSJE').mkdir(exist_ok=True)
    print('GOTOWE: zainstalowano 5 narzedzi predeploy / bezpiecznego aktualizatora w '+str(target))
    print('Nie zatrzymywano gry. Baza, seed, kod serwera, watchdog i backupy sa NIETKNIETE.')
    print('Skopiuj nowy ZIP do NOWE_WERSJE i uruchom PREDEPLOY_NOWEJ_WERSJI.bat.')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
