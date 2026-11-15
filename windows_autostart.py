# -*- coding: utf-8 -*-
"""Windows per-user background autostart, without a console at sign-in.

HKCU Run launches pythonw.exe directly.  No admin rights, Task Scheduler,
Windows Script Host or additional BAT files are needed.  Existing owned CMD
and VBS autostart entries are migrated once, without touching other programs.
"""
from __future__ import annotations
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
LINK_FILENAME = 'Soulbound_Autostart.cmd'  # legacy entry, not used for new starts
LEGACY_FILENAME = 'Soulbound_Autostart.vbs'
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'
RUN_VALUE = 'Soulbound_MUD'


def startup_file() -> Path:
    appdata = os.environ.get('APPDATA')
    if not appdata:
        raise RuntimeError('Nie znaleziono APPDATA. Zaloguj sie jako uzytkownik Windows.')
    return (Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu'
            / 'Programs' / 'Startup' / LINK_FILENAME)


def legacy_startup_file() -> Path:
    return startup_file().with_name(LEGACY_FILENAME)


def _legacy_owned(path: Path) -> bool:
    return str(ROOT / 'START_Soulbound_UKRYTY.vbs').casefold() in path.read_text(encoding='utf-16').casefold()


def _cmd_owned(path: Path) -> bool:
    return ('call "' + str(ROOT / 'START_Soulbound.bat') + '"').casefold() in path.read_text(
        encoding='utf-8-sig').casefold()


def _winreg():
    # Kept lazy so Linux-side synthetic regression needs no Windows package.
    import winreg
    return winreg


def _registry_get():
    reg = _winreg()
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY, 0, reg.KEY_READ) as key:
            value, value_type = reg.QueryValueEx(key, RUN_VALUE)
        if value_type != reg.REG_SZ or not isinstance(value, str):
            raise RuntimeError('Wpis autostartu ma obcy typ. Nie nadpisuje.')
        return value
    except FileNotFoundError:
        return None


def _registry_owned(value: str) -> bool:
    # Only a single, quoted pythonw.exe and exactly this installed script.
    match = re.fullmatch(r'"([^"\r\n]+pythonw\.exe)" -u "([^"\r\n]+uruchom_w_tle\.py)"',
                         value, flags=re.IGNORECASE)
    if not match:
        return False
    return Path(match.group(2)).resolve() == (ROOT / 'uruchom_w_tle.py').resolve()


def _pythonw() -> Path:
    exe = Path(sys.executable)
    candidate = exe.with_name('pythonw.exe')
    if exe.name.casefold() == 'pythonw.exe':
        candidate = exe
    if not candidate.is_file():
        raise RuntimeError('Brak pythonw.exe obok interpretera Pythona. Nie wlaczam widocznego autostartu.')
    return candidate.resolve()


def _command() -> str:
    script = ROOT / 'uruchom_w_tle.py'
    if not script.is_file() or not (ROOT / 'START_Soulbound.bat').is_file():
        raise FileNotFoundError('Brak uruchom_w_tle.py albo START_Soulbound.bat')
    return '"' + str(_pythonw()) + '" -u "' + str(script.resolve()) + '"'


def _check_legacy_ownership() -> tuple[Path, Path]:
    cmd = startup_file()
    vbs = legacy_startup_file()
    if cmd.exists() and not _cmd_owned(cmd):
        raise RuntimeError('Autostart CMD nalezy do innego folderu. Nie nadpisuje.')
    if vbs.exists() and not _legacy_owned(vbs):
        raise RuntimeError('Autostart VBS nalezy do innego folderu. Nie usuwa.')
    return cmd, vbs


def _on_windows() -> bool:
    return os.name == 'nt'


def install() -> str:
    if not _on_windows():
        raise RuntimeError('Autostart w rejestrze dotyczy tylko Windows.')
    cmd, vbs = _check_legacy_ownership()
    value = _registry_get()
    if value is not None and not _registry_owned(value):
        raise RuntimeError('Wpis autostartu w rejestrze nalezy do innej instalacji. Nie nadpisuje.')
    command = _command()  # Fail BEFORE touching any current startup entry.
    reg = _winreg()
    with reg.CreateKeyEx(reg.HKEY_CURRENT_USER, RUN_KEY, 0, reg.KEY_SET_VALUE) as key:
        reg.SetValueEx(key, RUN_VALUE, 0, reg.REG_SZ, command)
    # New entry exists: remove ONLY the old entries owned by this same root.
    if cmd.exists(): cmd.unlink()
    if vbs.exists(): vbs.unlink()
    return RUN_KEY + ' :: ' + RUN_VALUE


def uninstall() -> str:
    if not _on_windows():
        raise RuntimeError('Autostart w rejestrze dotyczy tylko Windows.')
    cmd, vbs = _check_legacy_ownership()
    value = _registry_get()
    if value is not None and not _registry_owned(value):
        raise RuntimeError('Wpis autostartu w rejestrze wskazuje inny folder. Nie kasuje.')
    if value is not None:
        reg = _winreg()
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY, 0, reg.KEY_SET_VALUE) as key:
            reg.DeleteValue(key, RUN_VALUE)
    if cmd.exists(): cmd.unlink()
    if vbs.exists(): vbs.unlink()
    return RUN_KEY + ' :: ' + RUN_VALUE


def migrate_if_enabled() -> bool:
    """Upgrade current user's *existing* autostart; never enable it by surprise."""
    if not _on_windows():
        return False
    cmd, vbs = startup_file(), legacy_startup_file()
    value = _registry_get()
    if value is None and not cmd.exists() and not vbs.exists():
        return False
    # Do not hijack a previous or unrelated install.
    if value is not None and not _registry_owned(value):
        raise RuntimeError('Autostart w rejestrze wskazuje inny folder.')
    _check_legacy_ownership()
    install()
    return True


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in ('install', 'uninstall', 'migrate'):
            print('Uzycie: python windows_autostart.py install|uninstall|migrate')
            raise SystemExit(2)
        action = sys.argv[1]
        if action == 'migrate':
            changed = migrate_if_enabled()
            print('AUTOSTART: ' + ('przeniesiony do niewidocznego startu' if changed else 'wylaczony, bez zmian'))
        else:
            result = install() if action == 'install' else uninstall()
            print('AUTOSTART ' + ('WLACZONY' if action == 'install' else 'WYLACZONY'))
            print('Rejestr HKCU: ' + result)
        print('Start bez okna po zalogowaniu do Windows. Zatrzymanie: STOP_Soulbound.bat.')
    except Exception as exc:
        print(f'BLAD AUTOSTARTU: {type(exc).__name__}: {exc}', file=sys.stderr)
        raise SystemExit(1)
