# -*- coding: utf-8 -*-
"""v108 isolated-only regression suite, safe to run on Windows without a server.

Only fixtures in the temporary folder may be mutated. Does not start a server,
touch production databases, alter the installed game or grant release approval.
"""
from __future__ import annotations
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

MODULES = (
    'validation.v10800_recovered_features_regression',
    'validation.v10600_manual_evolved_duplicates',
    'validation.v10800_suite_environment_regression',
    'validation.v10800_bat_cleanup_regression',
    'validation.v10800_visible_start_and_tcp_currency_regression',
    'validation.v10800_release_guard_regression',
    'validation.v10800_predeploy_snapshot_regression',
    'validation.v10800_predeploy_v107_state_isolation_regression',
    'validation.v10800_predeploy_tcp_isolation_regression',
    'validation.v10800_activation_install_cutover_regression',
    'validation.v10800_eq_cutover_bridge_regression',
    'validation.v10800_no_eq2_contract_regression',
    'validation.v10800_v107_drift_details_regression',
    'validation.v10800_v107_gate_loss_repro_regression',
    'validation.v10800_eq107_readonly_reconcile_regression',
    'validation.v10800_eq107_slot_details_regression',
    'validation.v10800_eq_rebuild_copy_regression',
    'validation.v10800_eq_dynamic_craft_regression',
    'validation.v10800_seasonal_events_regression',
    'validation.v10800_preserve_v107_content_regression',
    'validation.v10700_production_eq_cutover_regression',
    'validation.v10700_eq_real_backup_rehearsal_regression',
    'validation.v10700_windows_sqlite_handle_regression',
    'validation.v10700_eq_ledger_live_clone_regression',
    'validation.v10700_equipment_write_barrier_regression',
    'validation.v10700_equipment_barrier_real_adapters',
    'validation.v10700_eq_route_guards_regression',
    'validation.v10700_eq_untracked_locations_regression',
    'validation.v10700_forge_resource_guard_regression',
    'validation.v10700_activation_regression',
    'validation.v10700_upgrade_activation_install_regression',
    'validation.v10700_installer_bridge_regression',
    'validation.v10700_predeploy_output_regression',
    'validation.v10700_events_rotation_regression',
    'validation.test_v10400_atomic_crafting_consumption',
    # Heavy catalog-boot test last to avoid contention with other checks.
)


ROOT = Path(__file__).resolve().parents[1]


def _private_test_environment(original, workspace):
    """Never inherit a production database, control token or host location.

    The module's temporary folder is created before this configuration, so
    no two tests share an on-disk database or seed path. Work is confined to
    disposable copies even if the caller has SOULBOUND_DB in their shell.
    """
    sandbox = dict(original)
    for key in tuple(sandbox):
        upper = key.upper()
        if (upper.startswith(('SOULBOUND_', 'RAILWAY_')) or
                upper in ('DATABASE_URL', 'PYTHONPATH', 'SMTP_PASSWORD',
                          'PGPASSWORD', 'AWS_SECRET_ACCESS_KEY',
                          'AWS_SESSION_TOKEN', 'OPENAI_API_KEY')):
            sandbox.pop(key, None)
    sandbox.update({
        'SOULBOUND_DB': str(Path(workspace) / 'offline_synthetic.sqlite'),
        'SOULBOUND_WORLD_SEED_FILE': str(Path(workspace) / 'offline_seed.txt'),
        'SOULBOUND_HOST': '127.0.0.1',
        'PYTHONUTF8': '1',
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONDONTWRITEBYTECODE': '1',
    })
    return sandbox


def _one_module(index, module, env, timeout_seconds=90):
    """Return module result without inheritable stdout/stderr pipes.

    Some legacy validation commands start children which inherit stdio.
    subprocess.run(PIPE) may wait forever for such a grandchild even after
    a timeout. File-backed output and bounded tree cleanup avoid this trap.
    Every module still runs as a separate process, isolated from game state.
    """
    with tempfile.TemporaryDirectory(prefix='sb108_offline_module_') as home:
        output = Path(home) / 'stdout.txt'
        errors = Path(home) / 'stderr.txt'
        sandbox_env = _private_test_environment(env, home)
        with output.open('wb') as stdout, errors.open('wb') as stderr:
            kw = {'start_new_session': True} if os.name != 'nt' else {
                'creationflags': getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)}
            proc = subprocess.Popen([sys.executable, '-m', module],
                                    stdout=stdout, stderr=stderr,
                                    env=sandbox_env, cwd=ROOT, **kw)
            timed_out = False
            try:
                code = proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                code = 124
                if os.name == 'nt':
                    try:
                        subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                       timeout=8, check=False)
                    except (OSError, subprocess.TimeoutExpired):  # AUDIT_INTENTIONAL_PASS: best-effort taskkill, fallback proc.kill below
                        pass
                else:
                    try: os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:  # AUDIT_INTENTIONAL_PASS: process group already exited
                        pass
                if proc.poll() is None:proc.kill()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:  # AUDIT_INTENTIONAL_PASS: bounded cleanup, process kill already issued
                    pass
        # Bound memory and privacy exposure; the complete logs stay only in
        # short-lived local temp files and never in a release ZIP.
        def tail(path):
            with path.open('rb') as f:
                f.seek(0, 2)
                f.seek(max(0, f.tell()-8192))
                return f.read().decode('utf-8', errors='replace')
        return index, module, code, tail(output), (
            'TIMEOUT po '+str(timeout_seconds)+' s' if timed_out else tail(errors))


def main():
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    failures = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(_one_module, pos, module, env)
                for pos, module in enumerate(MODULES, 1)]
        for finished in as_completed(jobs):
            pos, module, code, stdout, stderr = finished.result()
            if code:
                failures.append((module, 'kod='+str(code)))
                print(f'[{pos}/{len(MODULES)}] FAIL: {module}: kod={code}', flush=True)
                print((stderr or stdout)[-1200:], flush=True)
            else:
                lines = [line.strip() for line in stdout.splitlines() if line.strip()]
                summary = lines[-1] if lines else 'PASS'
                print(f'[{pos}/{len(MODULES)}] PASS: {summary[:170]}', flush=True)
    if failures:
        print(f'V108: {len(failures)} NIEUDANYCH Z {len(MODULES)} REGRESJI; NIE WDRAŻAĆ.',flush=True)
        return 2
    print(f'V108: {len(MODULES)}/{len(MODULES)} MODUŁÓW REGRESJI PASS. '
          'NIE OZNACZA WINDOWS PREDEPLOY 60/60 PLUS ANI ZGODY NA WDROŻENIE.', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
