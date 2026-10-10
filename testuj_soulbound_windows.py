# -*- coding: utf-8 -*-
"""Run the same predeploy checks as Railway, streaming into an NVDA-friendly log."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time
import traceback


ROOT = Path(__file__).resolve().parent
LOG = ROOT / "logs" / "TESTY_Soulbound.log"


def main() -> int:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # AUDIT_INTENTIONAL_PASS: older/noninteractive streams may not support reconfigure
        pass

    with LOG.open("w", encoding="utf-8", errors="replace", buffering=1) as logfile:
        def say(message: str = "") -> None:
            print(message, flush=True)
            logfile.write(message + "\n")
            logfile.flush()

        say("SOULBOUND - WYNIK TESTOW WINDOWS / RAILWAY")
        say("Start: " + dt.datetime.now().astimezone().isoformat(timespec="seconds"))
        say("Python: " + sys.version.replace("\n", " "))
        say("System: " + platform.system() + " " + platform.release())
        say("Sciezka: " + str(ROOT))
        say("Baza postaci: NIETKNIETA (testy uzywaja katalogow tymczasowych)")
        say("Dziennik testow: " + str(LOG))
        say("-" * 72)
        failures = []

        # Railway runs these in this order. Each stage gets its own disposable DB.
        for stage in ("predeploy_check.py", "predeploy_full.py"):
            start = time.monotonic()
            say("\n" + "=" * 72)
            say("START: " + stage)
            if not (ROOT / stage).is_file():
                say("BLAD: Nie ma pliku " + stage)
                failures.append(stage)
                continue
            with tempfile.TemporaryDirectory(prefix="soulbound-testy-") as temp:
                env = os.environ.copy()
                env.update({
                    "PYTHONUTF8": "1",
                    "PYTHONIOENCODING": "utf-8",
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "SOULBOUND_DB": str(Path(temp) / "test.db"),
                })
                env.pop("SOULBOUND_FULL_AUDIT", None)
                env.pop("SOULBOUND_HISTORICAL_AUDITS", None)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", 0))
                    env["SOULBOUND_PORT"] = str(s.getsockname()[1])
                cmd = [sys.executable, "-u", str(ROOT / stage)]
                try:
                    proc = subprocess.Popen(
                        cmd, cwd=str(ROOT), env=env,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        encoding="utf-8", errors="replace", bufsize=1,
                    )
                    assert proc.stdout is not None
                    for line in proc.stdout:
                        say(line.rstrip("\r\n"))
                    ret = proc.wait()
                except KeyboardInterrupt:
                    say("PRZERWANO przez Ctrl+C")
                    if "proc" in locals() and proc.poll() is None:
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait()
                    say("Testy przerwane. Dotychczasowe wyniki zostaly zapisane.")
                    return 130
                except Exception:
                    say("BLAD uruchomienia testu:")
                    say(traceback.format_exc().strip())
                    ret = 99
            seconds = round(time.monotonic() - start, 1)
            say("KONIEC: " + stage + " | " + ("PASS" if ret == 0 else "FAIL") +
                " | kod " + str(ret) + " | czas " + str(seconds) + " s")
            if ret != 0:
                failures.append(stage)

        say("\n" + "=" * 72)
        say("WYNIK KONCOWY: " + ("PASS - oba testy zaliczone" if not failures
                                 else "FAIL - wymagaja poprawy: " + ", ".join(failures)))
        say("Log do przeslania: " + str(LOG))
        say("Koniec: " + dt.datetime.now().astimezone().isoformat(timespec="seconds"))
        return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
