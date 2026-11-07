# -*- coding: utf-8 -*-
"""Autostart per-user: standard CMD, no WScript or hidden VBS.

No admin privileges or task scheduler. Legacy autostart is migrated only when
its contents prove that it belongs to this same Soulbound root.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
LINK_FILENAME = 'Soulbound_Autostart.cmd'
LEGACY_FILENAME = 'Soulbound_Autostart.vbs'


def startup_file() -> Path:
    appdata = os.environ.get('APPDATA')
    if not appdata:
        raise RuntimeError('Nie znaleziono APPDATA. Zaloguj sie jako uzytkownik Windows.')
    return (Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu'
            / 'Programs' / 'Startup' / LINK_FILENAME)


def legacy_startup_file() -> Path:
    return startup_file().with_name(LEGACY_FILENAME)


def _legacy_owned(path: Path) -> bool:
    # The previous version wrote UTF-16 WScript that ran this exact VBS file.
    return str(ROOT / 'START_Soulbound_UKRYTY.vbs') in path.read_text(encoding='utf-16')


def _cmd_owned(path: Path) -> bool:
    return ('call "' + str(ROOT / 'START_Soulbound.bat') + '"') in path.read_text(
        encoding='utf-8-sig')


def install() -> Path:
    target = ROOT / 'START_Soulbound.bat'
    if not target.is_file():
        raise FileNotFoundError(str(target))
    path = startup_file()
    old = legacy_startup_file()
    # Refuse to touch another application's or another install's startup file.
    if path.exists() and not _cmd_owned(path):
        raise RuntimeError('Autostart CMD nalezy do innego folderu. Nie nadpisuje.')
    if old.exists() and not _legacy_owned(old):
        raise RuntimeError('Autostart VBS nalezy do innego folderu. Nie usuwa.')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('@echo off\ncall "' + str(target) + '"\n', encoding='utf-8')
    if old.exists():
        old.unlink()
    return path


def uninstall() -> Path:
    path = startup_file()
    old = legacy_startup_file()
    if path.exists() and not _cmd_owned(path):
        raise RuntimeError('Autostart CMD wskazuje inny folder Soulbound. Nie kasuje.')
    if old.exists() and not _legacy_owned(old):
        raise RuntimeError('Autostart VBS wskazuje inny folder Soulbound. Nie kasuje.')
    if path.exists():
        path.unlink()
    if old.exists():
        old.unlink()
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
