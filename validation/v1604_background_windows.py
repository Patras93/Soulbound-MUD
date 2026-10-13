# -*- coding: utf-8 -*-
"""Backward compatible check of hidden Windows start after v1.70.6 redesign."""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]

def _visible_starter_preserves_exit_code(visible: str) -> bool:
    """Verify both Windows launch branches return their real child exit codes.

    A percent expansion inside an IF (...) block can capture the prior errorlevel
    while CMD parses the entire block. With EnableDelayedExpansion, !errorlevel!
    is evaluated only after the detached launcher has returned.
    """
    if not re.search(r'(?im)^\s*setlocal\s+EnableExtensions\s+EnableDelayedExpansion\s*$', visible):
        return False
    for exe in (r'py\s+-3', r'python'):
        pattern = (
            r'(?im)^\s*if\s+not\s+errorlevel\s+1\s*\(\s*\n'
            + r'\s*' + exe + r'\s+-u\s+"%ROOT%uruchom_w_tle\.py"\s*\n'
            + r'\s*exit\s+/b\s+!errorlevel!\s*\n\s*\)'
        )
        if not re.search(pattern, visible):
            return False
    return True


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
        'visible starter exits': _visible_starter_preserves_exit_code(visible),
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
