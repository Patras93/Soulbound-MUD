# -*- coding: utf-8 -*-
"""Bounded, fail-closed executor for historically isolated PREDEPLOY gates.

Only separately launched, explicitly enumerated historical child processes are
eligible. No shared-runtime gameplay or mutable in-process test is parallelized.
Every child has its own ephemeral localhost port and disposable SQLite path.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import os
import socket
import subprocess
import tempfile

from validation.current_private_predeploy import isolated_predeploy_env


class HistoricalGateBatch:
    def __init__(self, max_workers=2):
        if not isinstance(max_workers, int) or not 1 <= max_workers <= 2:
            raise ValueError('Bounded historic gate concurrency must be 1 or 2')
        self.max_workers = max_workers
        self.tasks = []
        self.finished = False

    def add(self, gate, report):
        if self.finished or not callable(gate) or not callable(report):
            raise ValueError('Invalid or closed historical PREDEPLOY gate')
        self.tasks.append((gate, report))

    def run(self):
        if self.finished:
            raise RuntimeError('Historical PREDEPLOY batch cannot run twice')
        self.finished = True
        gates = tuple(self.tasks)
        if not gates:
            raise AssertionError('Missing historical PREDEPLOY gates')
        results = [None] * len(gates)
        failures = []
        with ThreadPoolExecutor(max_workers=self.max_workers,
                                thread_name_prefix='sb-history-gate') as pool:
            future_indices = {
                pool.submit(task): index
                for index, (task, _report) in enumerate(gates)
            }
            for future in as_completed(future_indices):
                if future.cancelled():
                    continue
                index = future_indices[future]
                try:
                    results[index] = future.result()
                except BaseException as exc:
                    failures.append((index, exc))
                    # Stop queueing work after the first blocking historical FAIL.
                    # Already-running isolated tests are joined safely.
                    for waiting in future_indices:
                        if waiting is not future:
                            waiting.cancel()
        # Errors are never masked by a different successful historical check.
        if failures:
            details = '; '.join(
                f'gate {index + 1}/{len(gates)}: {type(error).__name__}: {error}'
                for index, error in sorted(failures)
            )
            raise AssertionError('Historical PREDEPLOY FAIL: ' + details)
        if any(result is None for result in results):
            raise AssertionError('Historical PREDEPLOY: missing gate result')
        for (_task, report), result in zip(gates, results):
            report(result)
        return len(results)


def private_historical_subprocess_run(argv, **kwargs):
    """Run a historical child with its complete original command/checks.

    No production SQLite path, port or inherited secrets can enter the child.
    The disposable directory exists for the whole subprocess lifetime.
    """
    if 'env' in kwargs or 'shell' in kwargs:
        raise ValueError('Historic subprocess must use a private environment')
    with tempfile.TemporaryDirectory(prefix='sbcurrent_fast_') as directory:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        if port == 4000:
            raise PermissionError('Production TCP port not allowed')
        env = isolated_predeploy_env(dict(os.environ), directory, port)
        # Preserve ONLY the full-audit mode; isolated_predeploy_env removes all
        # other SOULBOUND_/RAILWAY_ inherited variables as a safety boundary.
        if os.environ.get('SOULBOUND_FULL_AUDIT') == '1':
            env['SOULBOUND_FULL_AUDIT'] = '1'
        kwargs['env'] = env
        kwargs.setdefault('cwd', str(Path(__file__).resolve().parents[1]))
        kwargs.setdefault('stdin', subprocess.DEVNULL)
        return subprocess.run(argv, **kwargs)
