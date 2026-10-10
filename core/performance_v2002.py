# -*- coding: utf-8 -*-
"""Low-overhead opt-in measurement for real Soulbound server actions.

Set SOULBOUND_PERF_LOG=1 before starting the server to print periodic summaries
in the normal server log. Without the flag decorators return original callables
and add zero work to the combat loop. No character or account data is emitted.
"""
import functools
import os
import time

_ENABLED = os.environ.get("SOULBOUND_PERF_LOG", "").lower() in ("1", "true", "yes", "on")


def _record(stats, label, interval, elapsed_ns):
    stats[0] += 1
    stats[1] += elapsed_ns
    stats[2] = max(stats[2], elapsed_ns)
    if stats[0] >= interval:
        count = stats[0]
        print(f"SOULBOUND PERF {label}: calls={count} "
              f"avg_ms={stats[1] / count / 1_000_000:.3f} "
              f"max_ms={stats[2] / 1_000_000:.3f}", flush=True)
        stats[:] = [0, 0, 0]


def measure_sync(label, report_every=100):
    def decorate(func):
        if not _ENABLED:
            return func
        stats = [0, 0, 0]
        @functools.wraps(func)
        def measured(*args, **kwargs):
            started = time.perf_counter_ns()
            try:
                return func(*args, **kwargs)
            finally:
                _record(stats, label, report_every, time.perf_counter_ns() - started)
        return measured
    return decorate


def measure_async(label, report_every=50):
    def decorate(func):
        if not _ENABLED:
            return func
        stats = [0, 0, 0]
        @functools.wraps(func)
        async def measured(*args, **kwargs):
            started = time.perf_counter_ns()
            try:
                return await func(*args, **kwargs)
            finally:
                _record(stats, label, report_every, time.perf_counter_ns() - started)
        return measured
    return decorate
