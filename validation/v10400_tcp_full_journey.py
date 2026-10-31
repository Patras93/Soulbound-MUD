# -*- coding: utf-8 -*-
"""Rzeczywiste TCP v104: 2 konta, drużyna, walka, quest, SQLite.

Uruchamia WYŁĄCZNIE kopię źródeł, własny losowy port loopback i prywatną
bazę w TemporaryDirectory. Nie łączy się z produkcyjnym serwerem.
Test opcjonalny (nie należy go uruchamiać przy zwykłym imporcie modułów).
"""
from __future__ import annotations

import asyncio
from contextlib import closing
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

from validation.v10400_release_isolation_guard import private_tcp_environment
from validation.v2102_tcp_six_players import TcpPlayer

ROOT = Path(__file__).resolve().parents[1]
PLAYERS = (("lab104alpha", "Lab104Alpha"), ("lab104beta", "Lab104Beta"))
PASSWORD = "test_only_tcp_2026_password"  # wyłącznie konta testowe
QUEST = "temple_rats"


def _progress(db_path: Path) -> int:
    with closing(sqlite3.connect(str(db_path), timeout=5)) as conn:
        if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise AssertionError("Blad integralnosci prywatnej bazy testowej.")
        rows = conn.execute('''SELECT q.progress FROM quests q
            JOIN accounts a ON a.id=q.account_id
            WHERE a.username=? AND q.quest_id=?''',
            (PLAYERS[0][0], QUEST)).fetchall()
    return max((int(r[0]) for r in rows), default=0)


async def _journey(port: int, db_path: Path):
    clients = [TcpPlayer(account, name, port) for account, name in PLAYERS]
    checks = 0
    try:
        for c in clients:
            await c.connect_and_login()
            checks += 1
        for command in ("look", "quests", "expbank", "who"):
            out = await clients[0].command(command)
            if not out.strip():
                raise AssertionError("Brak odpowiedzi na " + command)
            checks += 1
        lead, guest = clients
        offer = await lead.command("quest list Kapłan Elor")
        if "Szczury pod świątynią" not in offer:
            raise AssertionError("Nie znaleziono NPC i jego questa.")
        await lead.command("przyjmij 1")
        if _progress(db_path):
            raise AssertionError("Quest ma postep przed walka.")
        await lead.command("down")
        # Podroz bywa asynchroniczna; czekamy na rzeczywista lokacje,
        # a nie tylko potwierdzenie rozpoczecia przemieszczania.
        room = ""
        for _ in range(16):
            room = await lead.command("look")
            if "Piwnic" in room and ("Strefa:" in room or "Docierasz" in room):
                break
            await asyncio.sleep(.5)
        else:
            raise AssertionError("Nie dotarto do piwnicy po down: " + repr(room[:300]))
        fight = await lead.command("attack Szczur")
        if not any(word in fight.casefold() for word in ("walka", "szczur", "walcz")):
            raise AssertionError("Nie rozpoczeto naturalnej walki TCP: " + repr(fight[:500]))
        checks += 4
        deadline = time.monotonic() + 110
        while time.monotonic() < deadline:
            await asyncio.sleep(2)
            await lead.command("quests")
            if _progress(db_path) >= 1:
                # Druzyna sprawdzana po walce, aby ewentualna automatyczna
                # podroz lidera nie zaklocala testu lokacji i respawnu.
                out = await lead.command("druzyna zaloz")
                if "drużyn" not in out.casefold() and "druzyn" not in out.casefold():
                    raise AssertionError("Nie utworzono druzyny.")
                await lead.command("druzyna zapros " + guest.name)
                out = await guest.command("dolacz")
                if "drużyn" not in out.casefold() and "druzyn" not in out.casefold():
                    raise AssertionError("Nie dolaczono do druzyny.")
                out = await lead.command("druzyna status")
                if guest.name.casefold() not in out.casefold():
                    raise AssertionError("Nie widac drugiej postaci w druzynie.")
                checks += 3
                return checks + 2
        raise TimeoutError("Nie zaliczono prawdziwego zabicia szczura w SQLite.")
    finally:
        await asyncio.gather(*(c.close() for c in clients))


def run():
    # Kopia chroni oryginalne pliki nawet przed nieoczekiwanymi zapisami.
    from arena_real_izolowana import _ignore
    with tempfile.TemporaryDirectory(prefix="sb104_tcp_lab_") as tmp:
        work = Path(tmp)
        source = work / "source"
        shutil.copytree(ROOT, source, ignore=_ignore)
        from core.classes_skills import CLASSES, RACES
        from storage.database import Database
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        if port == 4000:
            raise AssertionError("Port produkcyjny jest zabroniony.")
        env = private_tcp_environment(os.environ, work, port)
        db_path = work / "tcp_test.sqlite"
        db = Database(str(db_path))
        try:
            for username, name in PLAYERS:
                aid = db.create_account(username, PASSWORD)
                db.create_character_for_master(
                    aid, name, RACES[0], CLASSES[0],
                    {key: name for key in ("nom", "gen", "dat", "acc", "ins", "loc", "voc")})
            db.conn.commit()
        finally:
            db.conn.close()
        logfile = work / "test_server.log"
        with logfile.open("w", encoding="utf-8") as log:
            child = subprocess.Popen(
                [sys.executable, "-u", "server.py"], cwd=source,
                env=env, stdout=log, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 170
                while time.monotonic() < deadline:
                    if child.poll() is not None:
                        raise RuntimeError("Serwer testowy zakonczyl prace przed startem.")
                    if "World Core nasłuchuje:" in logfile.read_text(
                            encoding="utf-8", errors="replace"):
                        break
                    time.sleep(.5)
                else:
                    raise TimeoutError("Brak gotowosci serwera przed limitem.")
                checks = asyncio.run(_journey(port, db_path))
                print(f"V104 TCP: 2 konta, druzyna, naturalna walka, SQLite: {checks} PASS")
                return checks
            finally:
                child.terminate()
                try:
                    child.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)


if __name__ == "__main__":
    run()
