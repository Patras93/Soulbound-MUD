# -*- coding: utf-8 -*-
"""v108: no invisible WSH launch; real amount comparison, safe autostart migration.

Only temporary APPDATA and dummy BAT are used. No system startup is changed.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))


def run():
    checks = 0
    launcher = (ROOT/'START_Soulbound.bat').read_text(encoding='ascii')
    updater = (ROOT/'aktualizuj_soulbound.py').read_text(encoding='utf-8')
    docker = (ROOT/'Dockerfile').read_text(encoding='utf-8')
    assert 'call "%~dp0Start-Soulbound-Windows.bat"' in launcher
    checks += 1
    assert 'exit /b !errorlevel!' in launcher
    checks += 1
    assert 'wscript' not in launcher.lower() and 'wscript.exe' not in updater.lower()
    checks += 1
    assert not (ROOT/'START_Soulbound_UKRYTY.vbs').exists()
    checks += 1
    assert 'START_Soulbound_UKRYTY.vbs' not in docker
    checks += 1
    assert "launcher = root / 'START_Soulbound.bat'" in updater
    checks += 1

    # v113+ replacement for earlier CMD-based autostart contract:
    # synthetic HKCU Run proves a totally hidden login start, and verifies
    # ownership of legacy CMD/VBS entries without touching the real registry.
    from validation.current_windows_autostart_background_regression import run_regression
    checks += run_regression()

    from validation.v2102_tcp_six_players import _money_snapshot
    clean='Masz 1 mithril, 12 złota, 9 srebra.\r\nTo jedno wspólne saldo.\r\n'
    assert _money_snapshot(clean)==(1,12,9)
    checks += 1
    assert _money_snapshot('Powiadomienie\n'+clean+'Info\n') == (1,12,9)
    checks += 1
    assert _money_snapshot(clean) != _money_snapshot('Masz 1 mithril, 12 złota, 10 srebra.')
    checks += 1
    for reply in ('Pusta odpowiedz', clean+clean):
        with unittest.TestCase().assertRaises(AssertionError):
            _money_snapshot(reply)
        checks += 1
    return checks


if __name__ == '__main__':
    print('V108 WIDOCZNY START I WALUTA TCP:',run(),'PASS',flush=True)
