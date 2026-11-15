# -*- coding: utf-8 -*-
"""Never touches actual Windows Startup or HKCU: synthetic Run registry only."""
from __future__ import annotations
from pathlib import Path
import tempfile
from unittest.mock import patch
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import windows_autostart as w


class RegistryKey:
    def __init__(self, registry):
        self.registry = registry
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class FakeWinReg:
    HKEY_CURRENT_USER = object()
    KEY_READ = 0x20019
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self):
        self.entries = {}
        self.writes = 0

    def OpenKey(self, root, path, *args):
        assert root is self.HKEY_CURRENT_USER and path == w.RUN_KEY
        if not self.entries:
            raise FileNotFoundError(path)
        return RegistryKey(self)

    def CreateKeyEx(self, root, path, *args):
        assert root is self.HKEY_CURRENT_USER and path == w.RUN_KEY
        return RegistryKey(self)

    def QueryValueEx(self, key, value):
        if value not in self.entries:
            raise FileNotFoundError(value)
        return self.entries[value]

    def SetValueEx(self, key, name, unused, value_type, value):
        self.entries[name] = (value, value_type)
        self.writes += 1

    def DeleteValue(self, key, name):
        del self.entries[name]
        self.writes += 1


def run_regression():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb_autostart_registry_') as td:
        home = Path(td)
        root = home / 'Soulbound Demo'
        root.mkdir()
        (root/'START_Soulbound.bat').write_text('@echo off\n', encoding='ascii')
        (root/'uruchom_w_tle.py').write_text('print("start")\n', encoding='utf-8')
        pythonw = home / 'Python' / 'pythonw.exe'
        pythonw.parent.mkdir()
        pythonw.write_bytes(b'test')
        reg = FakeWinReg()
        with patch.object(w, 'ROOT', root), patch.object(w,'_winreg',return_value=reg), \
             patch.object(w,'_on_windows',return_value=True), \
             patch.object(w,'_pythonw',return_value=pythonw), \
             patch.dict(os.environ, {'APPDATA':str(home/'AppData')}):
            cmd, vbs = w.startup_file(), w.legacy_startup_file()
            assert not w.migrate_if_enabled() and not reg.entries
            checks += 2
            w.install()
            value = reg.entries[w.RUN_VALUE][0]
            assert w._registry_owned(value)
            assert str(root/'uruchom_w_tle.py') in value
            assert 'pythonw.exe' in value and '.cmd' not in value.lower()
            assert not cmd.exists() and not vbs.exists()
            checks += 5
            # Repeated enable leaves one exact entry.
            w.install()
            assert len(reg.entries) == 1
            checks += 1
            # Even a moved Python installation remains owned by this root.
            previous = value
            new_pythonw = home/'Another Python'/'pythonw.exe'
            new_pythonw.parent.mkdir();new_pythonw.write_bytes(b'test')
            with patch.object(w,'_pythonw',return_value=new_pythonw):
                w.install()
            assert reg.entries[w.RUN_VALUE][0] != previous and w._registry_owned(previous)
            checks += 1
            # Foreign registry and foreign Startup files cannot be overwritten.
            reg.entries[w.RUN_VALUE] = ('"C:\\Foreign\\pythonw.exe" -u "C:\\Other\\uruchom_w_tle.py"', reg.REG_SZ)
            try: w.install()
            except RuntimeError: checks += 1
            else: raise AssertionError('Foreign HKCU Run entry was overwritten')
            reg.entries[w.RUN_VALUE] = (value, reg.REG_SZ)
            w.uninstall()
            assert not reg.entries
            checks += 1
            cmd.parent.mkdir(parents=True)
            cmd.write_text('@echo off\ncall "'+str(root/'START_Soulbound.bat')+'"\n',encoding='utf-8')
            assert w._cmd_owned(cmd) and w.migrate_if_enabled()
            assert not cmd.exists() and reg.entries[w.RUN_VALUE][0] == value
            checks += 3
            w.uninstall()
            vbs.write_text('path = "'+str(root/'START_Soulbound_UKRYTY.vbs')+'"\r\n',encoding='utf-16')
            assert w._legacy_owned(vbs) and w.migrate_if_enabled()
            assert not vbs.exists() and w.RUN_VALUE in reg.entries
            checks += 3
            w.uninstall()
            cmd.write_text('call "C:\\Other\\START_Soulbound.bat"\n',encoding='utf-8')
            try:w.install()
            except RuntimeError:checks += 1
            else:raise AssertionError('Foreign Startup CMD was overwritten')
            assert cmd.exists() and not reg.entries
            checks += 1
            cmd.unlink()
            vbs.write_text('path = "C:\\Foreign\\START_Soulbound_UKRYTY.vbs"\r\n',encoding='utf-16')
            try:w.migrate_if_enabled()
            except RuntimeError:checks += 1
            else:raise AssertionError('Foreign Startup VBS was removed')
            assert vbs.exists() and not reg.entries
            checks += 1
            vbs.unlink()
    update = (ROOT/'systems/universal_release_update.py').read_text(encoding='utf-8')
    assert 'migrate_if_enabled()' in update and 'publish_in_place(stage,root,backup,protected)' in update
    checks += 1
    launch = (ROOT/'uruchom_w_tle.py').read_text(encoding='utf-8')
    assert all(x in launch for x in ('DETACHED_PROCESS','CREATE_NO_WINDOW','pythonw.exe'))
    checks += 1
    return checks

if __name__ == '__main__':
    print('AUTOSTART WINDOWS UKRYTY: '+str(run_regression())+' checks PASS', flush=True)
