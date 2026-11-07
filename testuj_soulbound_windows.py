# -*- coding: utf-8 -*-
"""Isolated Windows release gate. Readable by NVDA; returns FAIL on any skipped gate.

Runs the quick, exhaustive and five-player localhost TCP checks in disposable
workspaces. Stage processes have hard deadlines so the batch never hangs forever.
"""
from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor
import shutil
from contextlib import closing
import sqlite3
import os
from pathlib import Path
import platform
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parent
LOG = ROOT / 'logs' / 'TESTY_Soulbound.log'
STAGES = (
    ('SZYBKI PREDEPLOY', 'predeploy_check.py', 1800),
    ('PELNY AUDYT', 'predeploy_full.py', 2100),
    ('SCENARIUSZE 4.0 AI / OCEAN / PROFESJE', 'validation/v2200_master_depths_ai.py', 180),
    ('MISTRZOWSKIE RECEPTURY / MODULY FLOTY', 'validation/v2201_fleet_mastery.py', 180),
    ('SCENARIUSZE 5.0: AI / 42 RECEPTURY / OCEAN', 'validation/v2300_world_professions_ocean.py', 180),
    ('AUDYT POKRYCIA WZDLUZ I WSZERZ', 'validation/v2302_coverage_contract.py', 180),
    ('ZADANIA — PRAWDZIWE ZDARZENIA I IZOLACJA', 'validation/v2310_event_contract.py', 180),
    ('AUTOGRACZ — MAPA, NPC, SCIEZKI', 'validation/v2320_autonomous_routes.py', 180),
    ('5 KLIENTOW TCP + RESTART', 'validation/v2102_tcp_six_players.py', 900),
)
ULTRA_STAGES = (
    ('KLASY 14 - SKILLE I MISTRZOSTWO',10,120),
    ('RASY 14 - KOMBINACJE',11,120),
    ('PROFESJE - REGULY I NAGRODY',12,120),
    ('SWIAT - LOKACJE, QUESTY I ZDARZENIA',13,180),
    ('LOCHY I WYSOKIE TERENY LVL 100-600',14,120),
    ('BOSSOWIE - REGR. SPRAWNYCH SPAWNOW',15,120),
    ('NAJEMNICY - SKALOWANIE I DAMAGE',16,120),
    ('GOSPODARKA - CENY',17,120),
    ('GOSPODARKA - TRANSAKCJE I REGRESJE',18,120),
    ('BALANS REGIONALNY',19,120),
    ('QUESTY - EXP, FAME, ZLOTO',20,180),
    ('WINDOWS - ZAMYKANIE I BRAK BLOKAD',21,120),
    ('SQLITE WAL - BACKUP, RESTORE, BLAD',22,120),
    ('WATCHDOG - AWARIA, BACKOFF I STOP',23,120),
    ('5 SESJI TCP - PRYWATNY SERWER',24,240),
    ('SQLITE LIVE - KOPIA I MIGRACJA SCHEMATU',25,180),
)
STAGES = STAGES + tuple((name, f'validation/predeploy_ultra_v2327.py --case {number}', timeout)
                         for name, number, timeout in ULTRA_STAGES)
ULTIMATE_STAGES = (
    ('KOMENDY I QUESTY - POKRYCIE REJESTRU', 26, 240),
    ('KOPALNIE - KIERUNKI', 27, 180),
    ('KOPALNIE - TRWALOSC TUNELI', 28, 180),
    ('OBRAZENIA ZYWIOLOWE', 29, 180),
    ('AOE - AI I OPTYMALIZACJA', 30, 180),
    ('PROGRESJA 50+', 31, 240),
    ('BALANS TEMPA GRINDU', 32, 180),
    ('PROFESJE - KRZYWE EXP', 33, 180),
    ('NARZEDZIA - KRZYWE EXP', 34, 180),
    ('ZAMOWIENIA I ODDANIE', 35, 180),
    ('ODRADZANIE MOBOW', 36, 180),
    ('EXP CAP I FAME', 37, 180),
    ('ROWNOLEGLE SWIATY', 38, 180),
    ('FAUNA TERENOW', 39, 180),
    ('POCZATKOWE WALKI', 40, 180),
    ('CONSIDER - REGIONY', 41, 180),
    ('TYTANI', 42, 180),
    ('WINDOWS - KOPANIE', 43, 180),
    ('STAROZYTNE KROLESTWA', 44, 180),
    ('SQLite - NAGLA AWARIA I WAL', 45, 120),
    ('SQLite - 4 PISARZY 400 COMMITOW', 46, 120),
    ('SECURITY - ZLE ZIPY BLOKOWANE', 47, 120),
    ('SECURITY - STARY PASS I PODMIENIONY ZIP BLOKOWANY', 48, 120),
    ('SQLITE - ZACHOWANIE DANYCH POSTACI NA KLONIE', 49, 180),
    ('TCP - 3 FALE PO 5 POLACZEN', 50, 240),
)
STAGES = STAGES + tuple((name, f'validation/predeploy_ultimate_v2328.py --case {number}', timeout)
                         for name, number, timeout in ULTIMATE_STAGES)


ULTIMATE60_STAGES = (
    ('KOMENDY - ROUTING, ALIASY, IZOLACJA',51,240),
    ('LOWCY I NAJEMNICY - ZALICZANIE',52,120),
    ('GŁĘBOKIE LOCHY - PRESJA I BALANS',53,120),
    ('PORTALE DRUZYNY I CHECKPOINTY',54,180),
    ('ZAMOWIENIA - RZECZYWISTE NAGRODY',55,180),
    ('AUTOMATYCZNA EKSPLORACJA - TRWALOSC',56,120),
    ('ZADANIA KLASOWE - CYKL ODNOWY',57,180),
    ('GILDIE - SKALOWANIE I KOSZTY',58,120),
    ('LECZENIE I PRZYWOLANIA W DRUZYNIE',59,120),
    ('SQLITE KLON / MIGRACJA / PLUS 5000+ REGRESJI',60,240),
)
STAGES = STAGES + tuple((name, ('validation/predeploy_plus_gate_v2330.py' if number == 60 else
                          f'validation/predeploy_ultimate60_v2329.py --case {number}'), timeout)
                         for name,number,timeout in ULTIMATE60_STAGES)




def source_db_for_gate():
    """Discover actual existing SQLite for read-only migration verification.

    No test DB, backup, or release-bundled DB is accepted as a substitute for
    a live installation. Explicit paths are authoritative (including errors).
    """
    configured = os.environ.get('SOULBOUND_ULTRA_SOURCE_DB', '').strip()
    inherited = os.environ.get('SOULBOUND_DB', '').strip()
    if configured:
        candidates = [Path(configured)]
    elif inherited:
        candidates = [Path(inherited)]
    else:
        candidates = [ROOT/'soulbound.db']
        # Standard Windows installation; only use it if the file truly exists.
        if os.name == 'nt':
            candidates.append(Path('C:/Soulbound-MUD/soulbound.db'))
    problems = []
    for candidate in candidates:
        try:
            candidate = candidate.expanduser().resolve()
            if not candidate.is_file():
                problems.append(f'nie istnieje: {candidate}')
                continue
            # Open strictly read-only: a malformed file is not an acceptable
            # "production snapshot" and must never generate a false PASS.
            with closing(sqlite3.connect(candidate.as_uri()+'?mode=ro',
                                         uri=True, timeout=10)) as db:
                db.execute('PRAGMA query_only=ON')
                table_names = {r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                if not {'accounts','characters'} <= table_names:
                    problems.append(f'brak kont/postaci w SQLite: {candidate}')
                    continue
            return candidate
        except (OSError, sqlite3.Error) as exc:
            problems.append(f'{candidate}: {type(exc).__name__}: {exc}')
    raise RuntimeError(
        'Brak prawdziwej bazy Soulbound do trzech testow migracji. '
        'Podaj sciezke: TESTUJ_Soulbound.bat "C:\\Soulbound-MUD\\soulbound.db" '
        'lub uruchom PREDEPLOY_NOWEJ_WERSJI.bat z folderu dzialajacej instalacji. '
        'Sprawdzone: ' + ('; '.join(problems) if problems else '(brak)'))


def kill_owned_process(proc):
    """Stop *only* a child started by this runner, including its TCP subprocess."""
    if proc.poll() is not None:
        return
    if os.name == 'nt':
        try:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=8, check=False)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
    else:
        import signal
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except OSError:
            proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=8)


def stage_env(temp):
    # Never inherit production DB, tokens, Railway ports, persistent seed paths.
    env = os.environ.copy()
    for key in ('PORT', 'RAILWAY_TCP_APPLICATION_PORT', 'RAILWAY_VOLUME_MOUNT_PATH',
                'DATABASE_URL', 'SOULBOUND_WORLD_SEED_FILE', 'SOULBOUND_WORLD_SEED',
                'SOULBOUND_ADMIN_ACCOUNTS', 'SOULBOUND_CONTROL_FILE',
                'SOULBOUND_CONTROL_TOKEN', 'SOULBOUND_FULL_AUDIT',
                'SOULBOUND_HISTORICAL_AUDITS', 'SOULBOUND_SMTP_PASSWORD',
                'SOULBOUND_MAIL_PASSWORD', 'SMTP_PASSWORD'):
        env.pop(key, None)
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
               PYTHONDONTWRITEBYTECODE='1', SOULBOUND_HOST='127.0.0.1',
               SOULBOUND_V108_PREDEPLOY='1',
               SOULBOUND_DB=str(Path(temp) / 'audit.sqlite'),
               SOULBOUND_WORLD_SEED_FILE=str(Path(temp) / 'audit_seed.txt'))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        env['SOULBOUND_PORT'] = str(sock.getsockname()[1])
    return env


def run_stage(path, env, deadline, say, *, root=None):
    """Run one gate with a hard deadline and a spool file, never stdout PIPE.

    Some historical tests launch subprocesses that inherit stdout.  A reader
    waiting for pipe EOF can hang after the actual gate process has exited,
    which used to report a false timeout (124).  Only the gate PID determines
    success; a timeout still kills its own process tree and reports FAIL.
    """
    root = root or ROOT
    proc = None
    try:
        parts = path.split(' ')
        cmd = [sys.executable, '-u', str(root / parts[0]), *parts[1:]]
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        # TemporaryFile is seekable and does not rely on pipe EOF.  The file
        # also safely handles large verbose audits without PIPE deadlocks.
        with tempfile.TemporaryFile(mode='w+b') as output:
            proc = subprocess.Popen(
                cmd, cwd=str(root), env=env, creationflags=flags,
                start_new_session=(os.name != 'nt'), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT,
            )
            timed_out = False
            try:
                code = proc.wait(timeout=deadline)
            except subprocess.TimeoutExpired:
                timed_out = True
                code = 124
                kill_owned_process(proc)
            # Read *after* the direct PID ends; descendants cannot keep the
            # audit blocked merely by holding their inherited stdout open.
            output.seek(0)
            for line in output:
                say(line.decode('utf-8', errors='replace').rstrip('\r\n'))
            if timed_out:
                say(f'FAIL: Przekroczony limit czasu {deadline} sekund. Proces zakonczony.')
            return code
    finally:
        if proc is not None and proc.poll() is None:
            kill_owned_process(proc)


# Separate disposable source trees prevent concurrent tests from sharing file
# output, ports, generated seeds or game-state artifacts. Release checks and
# their numeric count are unchanged; only their schedule is shortened.
PARALLEL_WORKERS = 3


def run_parallel_stages(stages, say, *, phase='ETAP', staging_v106=False,
                        max_workers=PARALLEL_WORKERS):
    """Run every mandatory gate exactly once, fail closed, with isolated roots.

    Return results in the original stage order. Each worker owns its private
    copy of the *exact* staged candidate; every stage still gets a fresh
    temporary SQLite DB and a separate localhost port via stage_env().
    """
    stages = tuple(stages)
    if not stages:
        return []
    workers = min(max(1, max_workers), len(stages))
    pending = queue.Queue()
    for index in range(len(stages)):
        pending.put(index)
    results = [None] * len(stages)
    report_lock = threading.Lock()

    with tempfile.TemporaryDirectory(prefix='soulbound-predeploy-workers-') as root_temp:
        roots = []
        # Read-only candidate source is cloned only once per worker, rather
        # than once per one of the 60 legacy stages.
        for worker_id in range(workers):
            worker_root = Path(root_temp) / f'candidate-{worker_id}'
            shutil.copytree(ROOT, worker_root, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'logs'))
            (worker_root / 'logs').mkdir(exist_ok=True)
            roots.append(worker_root)

        def worker(worker_id):
            root = roots[worker_id]
            while True:
                try:
                    index = pending.get_nowait()
                except queue.Empty:
                    return
                title, script, deadline = stages[index]
                began = time.monotonic()
                output_lines = []
                try:
                    with report_lock:
                        say(f'\nSTART: {phase} {index + 1}/{len(stages)}: {title} [{script}]')
                    if not (root / script.split()[0]).is_file():
                        output_lines.append('FAIL: Brak wymaganego pliku: ' + script)
                        code = 2
                    else:
                        with tempfile.TemporaryDirectory(prefix='soulbound-predeploy-stage-') as scratch:
                            env = stage_env(scratch)
                            if staging_v106 and 'KOPII' not in title:
                                env['SOULBOUND_V106_STAGING'] = '1'
                            code = run_stage(script, env, deadline, output_lines.append, root=root)
                except BaseException as exc:
                    code = 99
                    output_lines.append('BLAD TESTERA: ' + type(exc).__name__ + ': ' + str(exc))
                    output_lines.append(traceback.format_exc().strip())
                elapsed = time.monotonic() - began
                # Keep each stage's messages together for human/NVDA readability.
                with report_lock:
                    for line in output_lines:
                        say(line)
                    say(f'KONIEC: {title} | {"PASS" if code == 0 else "FAIL"} | '
                        f'kod {code} | czas {elapsed:.1f} s')
                results[index] = (title, code)
                pending.task_done()

        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix='sb-predeploy') as executor:
            jobs = [executor.submit(worker, i) for i in range(workers)]
            for job in jobs:
                job.result()
    if any(result is None for result in results):
        raise RuntimeError('PREDEPLOY: zabraklo wyniku jednego z etapow.')
    return results


def main():
    LOG.parent.mkdir(exist_ok=True, parents=True)
    try:
        sys.stdout.reconfigure(errors='replace')
    except (ValueError, AttributeError):  # AUDIT_INTENTIONAL_PASS: non-console hosts may lack reconfigure
        pass
    status = []
    with LOG.open('w', encoding='utf-8', errors='replace', buffering=1) as logfile:
        def say(msg=''):
            print(msg, flush=True)
            logfile.write(msg + '\n')
            logfile.flush()

        say('SOULBOUND v3.31.5 - PREDEPLOY 5 GRACZY ULTIMATE 60 PLUS')
        say('Start: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
        say('Python: '+sys.version.splitlines()[0])
        say('System: '+platform.platform())
        say('Folder gry: '+str(ROOT))
        say('Baza prawdziwych graczy: tylko odczyt przez backup SQLite w etapach 25/49/60; zapisy wylacznie w TEMP')
        say('TCP: tylko 127.0.0.1, 5 zalogowanych graczy, 5 TCP i 3 fale po 5 TCP localhost')
        say('PASS: 60 etapow PLUS + 3 bramki v105; dla v106 osobne 2 bramki; dla v107 dodatkowo 33 regresje v107.')
        say('-' * 72)
        candidate_version = (ROOT/'VERSION').read_text(encoding='utf-8').strip()
        from validation.v10800_release_readiness import (release_at_least_108,
                                                          unmet_requirements as v108_missing)
        if release_at_least_108(candidate_version):
            missing_v108 = v108_missing(ROOT)
            if missing_v108:
                say('V108 PREDEPLOY: FAIL PRZED 60 ETAPAMI; stare 60/60 nie zatwierdza wersji v108.')
                for number, reason in enumerate(missing_v108, 1):
                    say(f'BLOKADA V108 {number}: {reason}')
                say('WYNIK KONCOWY: FAIL - NIE WDRAZAJ; produkcja i baza bez zmian.')
                return 3
        # v107: stop immediately if the staged release has known production
        # blockers. Historical 60/60 tests mostly inspect pre-v107 gameplay;
        # a green result without this gate would be dangerously misleading.
        if (ROOT/'VERSION').read_text(encoding='utf-8').strip() == '107.00.0':
            from validation.v10700_release_readiness import unmet_requirements, eq_readiness_diagnostics
            missing = unmet_requirements()
            if missing:
                say('V107 PREDEPLOY: FAIL PRZED STARTEM; nie tracimy godziny na 60 historycznych etapów.')
                for index,reason in enumerate(missing,1):
                    say(f'BLOKADA {index}: {reason}')
                for detail in eq_readiness_diagnostics():
                    say('V107 DIAGNOSTYKA TESTU EQ: '+detail)
                # The past Windows logs repeated only the known blockers;
                # collect the actionable physical-EQ counts on a read-only
                # snapshot so the owner needn't guess which BAT to launch.
                # Never turn that diagnostic into a release PASS.
                if any('EQ' in reason or 'ekwipunku' in reason for reason in missing):
                    say('V107 EQ: dodatkowy AUDYT KOPII PRAWDZIWEJ BAZY - bez STOP i bez zapisu do oryginalu.')
                    try:
                        real_db=source_db_for_gate()
                        test_env=os.environ.copy()
                        test_env['PYTHONDONTWRITEBYTECODE']='1'
                        test_env['SOULBOUND_HOST']='127.0.0.1'
                        report=subprocess.run(
                            [sys.executable,'-B','-m','validation.v10700_eq_ledger_live_clone',
                             '--db',str(real_db)], cwd=ROOT,env=test_env,
                            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,timeout=180,check=False)
                        for detail in report.stdout.decode('utf-8',errors='replace').splitlines():
                            say('  EQ: '+detail)
                        say('  EQ AUDYT KOD: '+str(report.returncode)+' (to NIE jest zgoda na wdrozenie).')
                        # The existing count-only audit cannot prove that
                        # trade/banking/evolution adapters actually work on
                        # a backup of the user's data. Rehearse transactions
                        # only on a SECOND disposable SQLite clone and roll
                        # back all hypothetical player changes.
                        if report.returncode == 4:
                            routes=subprocess.run(
                                [sys.executable,'-B','-m','validation.v10700_eq_routes_on_real_backup',
                                 '--db',str(real_db)],cwd=ROOT,env=test_env,
                                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,timeout=300,check=False)
                            for detail in routes.stdout.decode('utf-8',errors='replace').splitlines():
                                say('  EQ TRANSAKCJE: '+detail)
                            say('  EQ TRANSAKCJE KOD: '+str(routes.returncode)+
                                ' (bez zgody na wdrozenie).')
                    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as diagnostic_error:
                        say('  EQ AUDYT NIEPELNY: '+type(diagnostic_error).__name__+': '+str(diagnostic_error))
                say('WYNIK KONCOWY: FAIL - NIE WDRAZAJ; gra i baza bez zmian.')
                return 3
        try:
            source = source_db_for_gate()
            # Keep this setting when a stage overrides SOULBOUND_DB with its
            # private scratch SQLite. Stage migrations read source in mode=ro.
            os.environ['SOULBOUND_ULTRA_SOURCE_DB'] = str(source)
            say('SQLITE SOURCE (wylacznie do odczytu): '+str(source))
            say('Weryfikacja kont/postaci bazy wejsciowej: PASS')
        except (OSError, ValueError, RuntimeError) as exc:
            say('FAIL PRZED STARTEM: '+str(exc))
            say('WYNIK KONCOWY: FAIL - NIE WDRAZAJ, brak wymaganej bazy SQLite')
            say('Koniec: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
            return 2
        say(f'TRYB: {PARALLEL_WORKERS} izolowane kopie kodu; wszystkie 60 testow bez pomijania.')
        try:
            status = run_parallel_stages(STAGES, say)
        except KeyboardInterrupt:
            say('PRZERWANO: CTRL+C, nie wydawaj tej wersji jako PASS')
            status.append(('RECZNIE PRZERWANE', 130))
        except BaseException as exc:
            say('BLAD TESTERA: '+type(exc).__name__+': '+str(exc))
            say(traceback.format_exc().strip())
            status.append(('BLAD TESTERA', 99))
        # v105: additional mandatory checks are run on this exact staged
        # candidate, after historical 60 stages, but BEFORE final PASS.
        # They do not change the 60-stage historical count. Real player DB is
        # only opened by mode=ro; mutation rehearsal runs on a TEMP backup.
        v105_extra=[]
        if len(status)==60 and all(code==0 for _,code in status):
            v105_extra=run_parallel_stages((
                ('V105 KATALOGI I BALANS', 'validation/v10500_release_predeploy.py', 420),
                ('V105 MIGRACJA PRAWDZIWEJ BAZY TYLKO KOPIA', 'validation/v10500_windows_migration_gate.py', 240),
                ('V105 BOSSOWIE TCP 5 KLIENTOW / QUEST I NAGRODY', 'validation/v10500_tcp_boss_rewards.py', 900),
            ), say, phase='V105')
        # v106: Mandatory release-candidate checks. The 60 legacy stages run
        # with the historical defaults and cannot validate new staging-only v106.
        # Never advertise 60/60 PASS without exercising real v106 gameplay.
        v106_extra=[]
        actual_version=(ROOT/'VERSION').read_text(encoding='utf-8').strip()
        if actual_version == '106.00.0':
            if len(status)==60 and all(code==0 for _,code in status) and len(v105_extra)==3 and all(code==0 for _,code in v105_extra):
                v106_extra=run_parallel_stages((
                    ('V106 AKTYWNE NOWE RAJDY / TCP / NAGRODY 1-6',
                     'validation/v10600_kompletny_audyt_jedna_paczka.py --szybko', 2400),
                    ('V106 HISTORYCZNE EQ NA KOPII Z PRAWDZIWEJ BAZY',
                     'validation/v10600_kopia_realnego_eq_audyt.py', 420),
                ), say, phase='V106', staging_v106=True)
            else:
                say('V106: historyczne bramki nie zaliczone; dodatkowe testy nie mogą dać PASS.')
        # v107: all 33 dedicated gameplay/SQLite regressions are mandatory,
        # in addition to 60 legacy tests and 3 v105 checks. Unlike the old
        # predeploy, a green historical suite alone cannot approve v107.
        v107_extra=[]
        if actual_version in ('107.00.0', '108.00.0'):
            if (len(status)==60 and all(code==0 for _,code in status)
                    and len(v105_extra)==3 and all(code==0 for _,code in v105_extra)):
                v107_extra=run_parallel_stages((
                    ('V107 33 REGRESJE KODU I BLOKADY PRODUKCYJNE',
                     'audyt_v107_windows_przed_predeploy.py', 2400),
                ), say, phase='V107')
            else:
                say('V107: stare bramki nie przeszly; dodatkowy audyt nie daje PASS.')
        say('\n' + '=' * 72)
        say('PODSUMOWANIE ETAPOW:')
        for title, ret in status:
            say(('PASS' if ret == 0 else 'FAIL') + ' - ' + title + ' (kod '+str(ret)+')')
        # Check the PLUS sub-suite was *actually executed*, not merely skipped.
        logfile.flush()
        plus_proof = 'PLUS CHECKS PASS' in LOG.read_text(encoding='utf-8',errors='replace')
        if len(status)==len(STAGES) and all(ret == 0 for _,ret in status):
            for title,ret in v105_extra:
                say(('PASS' if ret == 0 else 'FAIL') + ' - '+title+' (kod '+str(ret)+')')
        extra_proof = (len(v105_extra)==3 and all(ret==0 for _,ret in v105_extra))
        if not extra_proof: say('FAIL: Nie przeszly wszystkie trzy dodatkowe bramki v105')
        if actual_version == '106.00.0':
            for title,ret in v106_extra:
                say(('PASS' if ret==0 else 'FAIL')+' - '+title+' (kod '+str(ret)+')')
            if len(v106_extra)!=2:
                say('FAIL: Nie wykonano dwoch dodatkowych bramek v106.')
        v106_proof = (actual_version!='106.00.0' or
                      (len(v106_extra)==2 and all(ret==0 for _,ret in v106_extra)))
        if actual_version in ('107.00.0', '108.00.0'):
            for title,ret in v107_extra:
                say(('PASS' if ret==0 else 'FAIL')+' - '+title+' (kod '+str(ret)+')')
            if len(v107_extra)!=1:
                say('FAIL: Nie wykonano obowiazkowego audytu regresji v107.')
        v107_proof = (actual_version not in ('107.00.0','108.00.0') or
                      (len(v107_extra)==1 and all(ret==0 for _,ret in v107_extra)))
        # v108 executes its own mandatory suite on an isolated candidate and
        # the FULL REAL snapshot (already detached by predeploy_nowej_wersji).
        v108_extra = []
        if actual_version == '108.00.0':
            if (len(status) == 60 and all(code == 0 for _,code in status)
                    and extra_proof and v107_proof and plus_proof):
                v108_extra = run_parallel_stages((
                    ('V108 27+ TESTOW BEZ REGRESJI',
                     'validation/v10800_offline_suite.py', 2400),
                    ('V108 ZGODNOSC ISTNIEJACEGO EQ V107 / BEZ MIGRACJI',
                     'validation/v10800_v107_equipment_compat_gate.py', 1200),
                ), say, phase='V108', max_workers=1)
            else:
                say('FAIL: V108 nie uruchamia bramek przed zaliczeniem 60 + v105 + v107.')
            for title,ret in v108_extra:
                say(('PASS' if ret==0 else 'FAIL')+' - '+title+' (kod '+str(ret)+')')
        v108_additional_proof = (not release_at_least_108(actual_version) or
                                 (actual_version=='108.00.0' and len(v108_extra)==2
                                  and all(ret==0 for _,ret in v108_extra)))
        if not v108_additional_proof:
            say('FAIL: V108 zgodnosc danych v107 i osobne regresje nie zaliczone.')
        good = (len(status) == len(STAGES) and all(ret == 0 for _,ret in status)
                and plus_proof and extra_proof and v106_proof and v107_proof
                and v108_additional_proof)
        if good and actual_version == '108.00.0':
            say('V108 RELEASE GATES PASS')
        if not plus_proof: say('FAIL: Brak dowodu wykonania regresji PLUS')
        say('WYNIK KONCOWY: '+('PASS - WSZYSTKIE 60 ETAPOW PLUS' if good else
                                'FAIL - NIE WDRAZAJ, popraw bledy wskazane wyzej'))
        say('Log do przeslania: '+str(LOG))
        say('Koniec: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
        return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
