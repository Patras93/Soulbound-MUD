# -*- coding: utf-8 -*-
"""Stop only the Soulbound instance belonging to this extracted folder."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sys
import time
from windows_launcher_state import wait_gone, process_alive

ROOT = Path(__file__).resolve().parent
CANDIDATES = (ROOT / 'logs' / 'soulbound_control.json',
              Path(os.environ.get('TEMP') or os.environ.get('TMP') or ROOT) / 'Soulbound-MUD-logs' / 'soulbound_control.json')


def main() -> int:
    try:
        found = []
        for candidate in CANDIDATES:
            if candidate.is_file():
                entry = json.loads(candidate.read_text(encoding='utf-8'))
                if Path(str(entry.get('root', ''))).resolve() == ROOT:
                    found.append((candidate, entry))
        if not found:
            # Nadzorca moze byc w opoznionej probie ponownego uruchomienia.
            watch = ROOT / 'logs' / 'soulbound_supervisor.json'
            try:
                entry = json.loads(watch.read_text(encoding='utf-8'))
                pid = int(entry['pid'])
                rid = str(entry['run_id'])
                if (Path(str(entry.get('root', ''))).resolve() == ROOT and
                        len(rid) >= 32 and process_alive(pid)):
                    request = ROOT / 'logs' / 'soulbound_stop_request.json'
                    temp = request.with_name(request.name + f'.{os.getpid()}.new')
                    try:
                        temp.write_text(json.dumps({'run_id': rid, 'root': str(ROOT)}), encoding='utf-8')
                        os.replace(temp, request)
                    finally:
                        temp.unlink(missing_ok=True)
                    if wait_gone(pid, timeout=15):
                        print('Soulbound: nadzorca zatrzymany w trakcie oczekiwania na restart.')
                        return 0
                    print('UWAGA: nadzorca jeszcze dziala; sprawdz logs\\watchdog.log.')
                    return 4
            except (OSError, KeyError, ValueError, TypeError):  # AUDIT_INTENTIONAL_PASS: opcjonalny plik stanu Windows
                pass
            print('Soulbound nie jest uruchomiony przez START_Soulbound.bat w tym folderze.')
            return 2
        META, meta = found[0]
        port = int(meta['port'])
        token = str(meta['token'])
        if not (1024 <= port <= 65535 and len(token) >= 32):
            raise ValueError('nieprawidlowe dane sterowania')
        launcher_pid = None
        launcher_state = META.parent / 'soulbound_launcher.json'
        try:
            state = json.loads(launcher_state.read_text(encoding='utf-8'))
            if Path(str(state.get('root', ''))).resolve() == ROOT:
                launcher_pid = int(state['pid'])
        except (OSError, ValueError, KeyError, TypeError):  # AUDIT_INTENTIONAL_PASS: no marker in older releases
            pass
        # Prosimy nadzorce o NIEwznawianie gry po autoryzowanym STOP.
        supervisor_state = META.parent / 'soulbound_supervisor.json'
        stop_request = META.parent / 'soulbound_stop_request.json'
        request_run_id = ''
        state = {}
        try:
            state = json.loads(supervisor_state.read_text(encoding='utf-8'))
            if (Path(str(state.get('root', ''))).resolve() == ROOT and
                isinstance(state.get('run_id'), str) and len(state['run_id']) >= 32 and
                int(state.get('pid', -1)) == launcher_pid):
                request_run_id = state['run_id']
                request_temp = stop_request.with_name(stop_request.name + f'.{os.getpid()}.new')
                try:
                    request_temp.write_text(json.dumps({'run_id': request_run_id, 'root': str(ROOT)}), encoding='utf-8')
                    os.replace(request_temp, stop_request)
                finally:
                    request_temp.unlink(missing_ok=True)
        except (OSError, ValueError, TypeError, KeyError):
            request_run_id = ''

        def undo_unsent_request() -> None:
            if request_run_id:
                try:
                    current = json.loads(stop_request.read_text(encoding='utf-8'))
                    if current.get('run_id') == request_run_id:
                        stop_request.unlink(missing_ok=True)
                except (OSError, ValueError):  # AUDIT_INTENTIONAL_PASS: opcjonalny plik stanu Windows
                    pass

        # The loopback socket requires the private per-process token, so it
        # cannot accidentally shut down another Python program.
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=4) as connection:
                connection.settimeout(5)
                connection.sendall(('STOP ' + token + '\n').encode('ascii'))
                reply = connection.recv(128).decode('ascii', 'replace').strip()
        except (OSError, ValueError, UnicodeError):
            undo_unsent_request()
            raise
        if reply != 'ZATRZYMYWANIE':
            undo_unsent_request()
            print('BLAD: Soulbound nie potwierdzil polecenia STOP. Niczego nie zabito.')
            return 3
        print('Soulbound: rozpoczęto bezpieczne zamykanie i zapis postaci.')
        for _ in range(150):  # 30 seconds to finish and remove our token file.
            if not META.is_file():
                if launcher_pid and not wait_gone(launcher_pid, timeout=15):
                    print('UWAGA: serwer zapisal dane, ale launcher nadal dziala. Folder moze byc zajety.')
                    return 4
                print('Soulbound: serwer i launcher zakonczone, folder mozna aktualizowac.')
                return 0
            try:
                current = json.loads(META.read_text(encoding='utf-8'))
                if current.get('token') != token:
                    if launcher_pid and not wait_gone(launcher_pid, timeout=15):
                        print('UWAGA: stary launcher nie zakonczyl pracy.')
                        return 4
                    print('Soulbound: uruchomiona zostala nowa instancja; stara zamknieta.')
                    return 0
            except (OSError, ValueError):  # AUDIT_INTENTIONAL_PASS: control file may disappear during shutdown
                pass
            time.sleep(.2)
        print('UWAGA: serwer potwierdzil STOP, ale nie zakonczyl zamykania w 30 s. Sprawdz okno START i logs\\serwer.log. Nie wymuszono zabicia procesu.')
        return 4
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(f'BLAD: nie mozna polaczyc sie z uruchomionym Soulbound: {exc}. Inne programy nie zostaly zatrzymane.')
        return 3


if __name__ == '__main__':
    sys.exit(main())
