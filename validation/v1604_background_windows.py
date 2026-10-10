# -*- coding: utf-8 -*-
"""Static regression checks for hidden WSH start; runnable on Linux CI."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_regression():
    launcher = (ROOT / "START_Soulbound.bat").read_text(encoding="ascii")
    hidden = (ROOT / "START_Soulbound_UKRYTY.vbs").read_text(encoding="ascii")
    visible = (ROOT / "Start-Soulbound-Windows.bat").read_text(encoding="utf-8")
    stop = (ROOT / "STOP_Soulbound.bat").read_text(encoding="utf-8")
    checks = {
        "default invokes hidden WSH": 'wscript.exe' in launcher and 'START_Soulbound_UKRYTY.vbs' in launcher,
        "default fallback remains": 'call "%~dp0Start-Soulbound-Windows.bat"' in launcher,
        "WSH launch uses hide style": 'shell.Run(Chr(34) & batPath & Chr(34), 0, False)' in hidden,
        "WSH launch is asynchronous": ', 0, False)' in hidden,
        "WD from script folder": 'shell.CurrentDirectory = gameFolder' in hidden,
        "visible launcher retains bootstrap": 'start_windows_bootstrap.py' in visible and 'serwer.log' in (ROOT/'host_windows.py').read_text(encoding='utf-8'),
        "STOP remains safe": 'stop_soulbound_windows.py' in stop and 'Stop-Process' not in stop and 'taskkill' not in stop.lower(),
        "no destructive termination": all(x not in launcher.lower() and x not in hidden.lower() for x in ('taskkill','stop-process','wmic process delete')),
    }
    failures=[k for k,ok in checks.items() if not ok]
    if failures:
        raise AssertionError('Windows background launcher: '+', '.join(failures))
    return len(checks)

if __name__=='__main__':
    print(f'WINDOWS BACKGROUND v1.60.4: {run_regression()} checks PASS')
