# -*- coding: utf-8 -*-
"""Backward compatible check of hidden Windows start after v1.70.6 redesign."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run_regression():
    launcher = (ROOT / 'START_Soulbound.bat').read_text(encoding='ascii')
    hidden = (ROOT / 'START_Soulbound_UKRYTY.vbs').read_text(encoding='ascii')
    visible = (ROOT / 'Start-Soulbound-Windows.bat').read_text(encoding='ascii')
    stop = (ROOT / 'STOP_Soulbound.bat').read_text(encoding='ascii')
    bg = (ROOT / 'uruchom_w_tle.py').read_text(encoding='utf-8')
    checks = {
        'default invokes WSH': 'wscript.exe' in launcher and 'START_Soulbound_UKRYTY.vbs' in launcher,
        'default fallback': 'call "%~dp0Start-Soulbound-Windows.bat"' in launcher,
        'WSH waits for short CMD': ', 0, True)' in hidden,
        'WSH cwd TEMP': 'CurrentDirectory = shell.ExpandEnvironmentStrings("%TEMP%")' in hidden,
        'visible starter exits': 'uruchom_w_tle.py' in visible and 'exit /b %errorlevel%' in visible,
        'detached Python': 'DETACHED_PROCESS' in bg and 'CREATE_NO_WINDOW' in bg,
        'safe STOP': 'stop_soulbound_windows.py' in stop and 'taskkill' not in stop.lower(),
        'STOP working dir outside game': 'cd /d "%TEMP%"' in stop,
        'no force kill': 'taskkill' not in launcher.lower() and 'taskkill' not in bg.lower(),
    }
    errors = [key for key,passed in checks.items() if not passed]
    if errors:
        raise AssertionError('Windows background regression: '+', '.join(errors))
    return len(checks)

if __name__ == '__main__':
    print(f'WINDOWS BACKGROUND v1.70.6: {run_regression()} checks PASS')
