# -*- coding: utf-8 -*-
"""v108: no invisible WSH launch; real amount comparison, safe autostart migration.

Only temporary APPDATA and dummy BAT are used. No system startup is changed.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import unittest

ROOT = Path(__file__).resolve().parents[1]


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

    import windows_autostart as autostart
    with TemporaryDirectory(prefix='sb108_visible_start_') as temp:
        home = Path(temp)
        project = home/'DummyGame'
        project.mkdir()
        (project/'START_Soulbound.bat').write_text('@echo off\n',encoding='utf-8')
        appdata = home/'fake_appdata'
        with patch.dict(os.environ, {'APPDATA':str(appdata)}), patch.object(autostart,'ROOT',project):
            target = autostart.install()
            assert target.name.endswith('.cmd') and target.is_file()
            checks += 1
            assert autostart._cmd_owned(target)
            checks += 1
            # Existing v107 autostart for THIS install may migrate to CMD.
            old = autostart.legacy_startup_file()
            old.write_text('Option Explicit\r\npath = "'+str(project/'START_Soulbound_UKRYTY.vbs')+'"\r\n',encoding='utf-16')
            autostart.install()
            assert not old.exists() and target.exists()
            checks += 1
            # Other-install file must never be silently removed.
            old.write_text('path = "C:\\OtherGame\\START_Soulbound_UKRYTY.vbs"',encoding='utf-16')
            with unittest.TestCase().assertRaises(RuntimeError):
                autostart.install()
            assert old.exists()
            checks += 1
            old.unlink()
            autostart.uninstall()
            assert not target.exists()
            checks += 1

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
