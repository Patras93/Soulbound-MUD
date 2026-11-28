# -*- coding: utf-8 -*-
"""Privacy-safe per-task latency breakdown without logging user input.

ContextVar scopes follow asyncio tasks. No SQLite SQL text or character names are
retained. The profiler only tracks calls executed on the active command task.
"""
from __future__ import annotations
from contextvars import ContextVar
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps
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
    phases: dict = field(default_factory=dict)


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
        if scope.phases:
            print('[PERF PHASE v11684] %s: %s (bez argumentow i danych graczy)' % (
                scope.kind, '; '.join('%s=%d/%.3fs/%d SQL/%d commit' % (
                    name, calls, seconds, queries, commits)
                    for name, (calls, seconds, queries, commits) in sorted(scope.phases.items()))), flush=True)
    return elapsed


@contextmanager
def performance_phase(name):
    """Aggregate a fixed internal phase into the current command task only."""
    scope = current()
    if scope is None or scope.closed:
        yield
        return
    start = perf_counter()
    queries, commits = scope.sql_queries, scope.sql_commits
    try:
        yield
    finally:
        if not scope.closed:
            calls, seconds, sql, writes = scope.phases.get(name, (0, 0.0, 0, 0))
            scope.phases[name] = (calls + 1, seconds + perf_counter() - start,
                                  sql + scope.sql_queries - queries,
                                  writes + scope.sql_commits - commits)


def equipment_read_snapshot(method):
    """Reuse EQ reads only inside one synchronous calculation, never across await.

    Callers can already own a forecast snapshot. Nested calculations reuse it;
    otherwise the local snapshot is discarded even on a failed calculation.
    No result or equipment state is cached between independent attacks/skills.
    """
    @wraps(method)
    def calculate(actor, *args, **kwargs):
        previous = getattr(actor, '_read_only_equipment_cache_v1262', None)
        if previous is not None:
            return method(actor, *args, **kwargs)
        had_attribute = '_read_only_equipment_cache_v1262' in actor.__dict__
        actor._read_only_equipment_cache_v1262 = {}
        try:
            return method(actor, *args, **kwargs)
        finally:
            if had_attribute:
                actor._read_only_equipment_cache_v1262 = previous
            else:
                actor.__dict__.pop('_read_only_equipment_cache_v1262', None)
    return calculate
