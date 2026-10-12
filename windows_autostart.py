# -*- coding: utf-8 -*-
"""Autostart Soulbound bez administratora: per-user folder Autostart Windows.

Działa po zalogowaniu danego użytkownika. Nie obiecuje uruchomienia przed
zalogowaniem, ani automatycznego włączenia fizycznie wyłączonego komputera.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
LINK_FILENAME = 'Soulbound_Autostart.vbs'


def startup_file() -> Path:
    appdata = os.environ.get('APPDATA')
    if not appdata:
        raise RuntimeError('Nie znaleziono APPDATA. Zaloguj sie jako uzytkownik Windows.')
    folder = Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    return folder / LINK_FILENAME


def install() -> Path:
    target = ROOT / 'START_Soulbound_UKRYTY.vbs'
    if not target.is_file():
        raise FileNotFoundError(str(target))
    path = startup_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    escaped = str(target).replace('"', '""')
    body = ('Option Explicit\r\n'
            'Dim sh, fs, path\r\n'
            'Set sh = CreateObject("WScript.Shell")\r\n'
            'Set fs = CreateObject("Scripting.FileSystemObject")\r\n'
            'path = "' + escaped + '"\r\n'
            'If fs.FileExists(path) Then sh.Run Chr(34) & path & Chr(34), 0, False\r\n')
    # WSH odczytuje UTF-16 BOM; obsługa ścieżek zawierających polskie znaki.
    path.write_text(body, encoding='utf-16')
    return path


def uninstall() -> Path:
    path = startup_file()
    if path.exists():
        raw = path.read_text(encoding='utf-16')
        if str(ROOT / 'START_Soulbound_UKRYTY.vbs') not in raw:
            raise RuntimeError('Autostart wskazuje inny folder Soulbound. Nie kasuje obcego skrotu.')
        path.unlink()
    return path


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in ('install', 'uninstall'):
            print('Uzycie: python windows_autostart.py install|uninstall')
            raise SystemExit(2)
        result = install() if sys.argv[1] == 'install' else uninstall()
        print('AUTOSTART ' + ('WLACZONY' if sys.argv[1] == 'install' else 'WYLACZONY'))
        print('Plik: ' + str(result))
        print('Start po zalogowaniu do Windows; komputer musi byc wlaczony.')
    except Exception as exc:
        print(f'BLAD AUTOSTARTU: {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
