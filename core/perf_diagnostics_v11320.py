# -*- coding: utf-8 -*-
"""Privacy-safe per-task latency breakdown without logging user input.

ContextVar scopes follow asyncio tasks. No SQLite SQL text or character names are
retained. The profiler only tracks calls executed on the active command task.
"""
from __future__ import annotations
from contextvars import ContextVar
from dataclasses import dataclass
from time import perf_counter, process_time

_ACTIVE = ContextVar('sb_perf_current_command_v11320', default=None)

@dataclass
class PerformanceScope:
    kind: str
    start: float
    cpu_start: float
    sql_queries: int = 0
    sql_seconds: float = 0.0
    sql_max: float = 0.0
    sql_commits: int = 0
    sql_commit_seconds: float = 0.0
    closed: bool = False


def begin(kind):
    scope = PerformanceScope(str(kind)[:32], perf_counter(), process_time())
    return scope, _ACTIVE.set(scope)


def current():
    return _ACTIVE.get()


def note_sql(seconds, *, commit=False):
    scope = _ACTIVE.get()
    if scope is None or scope.closed:
        return
    if commit:
        scope.sql_commits += 1
        scope.sql_commit_seconds += seconds
    else:
        scope.sql_queries += 1
        scope.sql_seconds += seconds
        if seconds > scope.sql_max:
            scope.sql_max = seconds


def finish(scope, token, *, minimum=0.25):
    elapsed = perf_counter() - scope.start
    cpu = process_time() - scope.cpu_start
    scope.closed = True
    _ACTIVE.reset(token)
    if elapsed >= minimum:
        # process_time includes the whole process, not just the current task;
        # useful only as a rough upper estimate of process CPU activity.
        print('[PERF DETAIL] %s: czas=%.3fs, CPU_procesu=%.3fs, SQLite=%d zapytan/%.3fs, '
              'SQLite_max=%.3fs, commit=%d/%.3fs (bez argumentow i danych graczy)'
              % (scope.kind, elapsed, cpu, scope.sql_queries, scope.sql_seconds,
                 scope.sql_max, scope.sql_commits, scope.sql_commit_seconds), flush=True)
    return elapsed
