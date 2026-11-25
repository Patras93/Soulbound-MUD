# -*- coding: utf-8 -*-
"""v116.70 real SQLite hot-path test; no production data or network."""
from __future__ import annotations
import sqlite3
from core.perf_diagnostics_v11320 import begin, finish
from storage.database import _DeferredCommitConnection
from storage.db_progression import DatabaseProgressionMixin


def run():
    checks = 0
    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError('SKILL SQLITE v11670: ' + label)

    raw = sqlite3.connect(':memory:')
    raw.row_factory = sqlite3.Row
    raw.executescript('''
        CREATE TABLE skill_progress (
            account_id INTEGER NOT NULL, skill_id TEXT NOT NULL,
            level INTEGER NOT NULL, xp INTEGER NOT NULL, uses INTEGER NOT NULL,
            PRIMARY KEY (account_id, skill_id)
        );
    ''')
    class DB(DatabaseProgressionMixin):
        def __init__(self, conn): self.conn = conn
    db = DB(_DeferredCommitConnection(raw))
    for idx in range(480):
        db.conn.execute('INSERT INTO skill_progress VALUES(7, ?, 8, 44, 19)', (f'skill_{idx}',))
    db.conn.execute('INSERT INTO skill_progress VALUES(8, ?, 33, 900, 40)', ('skill_0',))
    db.conn.commit()
    baseline = raw.total_changes
    trace = []
    raw.set_trace_callback(trace.append)

    scope, token = begin('v11670_test_read')
    for idx in range(480):
        row = db.skill_progress(7, f'skill_{idx}')
        check((row['level'], row['xp'], row['uses']) == (8, 44, 19),
              'read existing level, XP and uses')
    finish(scope, token, minimum=100000)
    check(scope.sql_queries == 480, 'exactly one SELECT per existing skill')
    check(scope.sql_commits == 0, 'no COMMIT for existing skill reads')
    check(raw.total_changes == baseline, 'no write for existing skill reads')
    check(not any(q.lstrip().upper().startswith(('INSERT', 'UPDATE', 'COMMIT')) for q in trace),
          'SQL trace must have no writes')
    check(db.skill_progress(8, 'skill_0')['level'] == 33,
          'account-specific level unchanged')

    trace.clear()
    lazy = db.skill_progress(7, 'brand_new_skill')
    check((lazy['level'], lazy['xp'], lazy['uses']) == (1, 0, 0),
          'new skill initialized at exact historical default')
    check(any('INSERT' in q.upper() for q in trace),
          'new skill must still be persisted')
    check(db.skill_progress(7, 'brand_new_skill')['level'] == 1,
          'persisted lazy skill visible again')

    # Single-skill XP is still committed and uses grow by one; no phantom
    # multi-level jump. 500 consecutive XP writes have exactly 500 COMMITs
    # rather than 1500 COMMITs from redundant initialization calls.
    scope, token = begin('v11670_test_xp')
    for idx in range(480):
        result = db.add_skill_xp(7, f'skill_{idx}', 37)
        check((result['level'], result['xp'], result['uses'], result['level_ups'])
              == (8, 81, 20, 0), 'real XP gain preserved exactly once')
    finish(scope, token, minimum=100000)
    check(scope.sql_commits == 480, 'exactly one COMMIT per real XP gain')
    check(scope.sql_queries == 960, 'one SELECT plus one UPDATE per XP gain')
    check(db.skill_progress(8, 'skill_0')['xp'] == 900,
          'other account skill XP isolated')
    check(db.skill_progress(7, 'skill_479')['xp'] == 81,
          'last skill update persisted')

    result = db.add_skill_xp(7, 'brand_new_xp_skill', 37)
    check((result['level'], result['xp'], result['uses']) == (1, 37, 1),
          'first XP use still initializes and updates missing row')
    check(db.skill_progress(7, 'brand_new_xp_skill')['xp'] == 37,
          'missing row first use persisted')

    # Existing deferred transaction for a multi-skill payout must keep its
    # rollback boundary: the improvement must not auto-commit other awards.
    prior = db.skill_progress(7, 'skill_1')['xp']
    try:
        with db.conn.deferred_commits():
            db.add_skill_xp(7, 'skill_1', 100)
            db.add_skill_xp(7, 'skill_2', 100)
            raise RuntimeError('intentional test rollback')
    except RuntimeError as error:
        assert str(error) == 'intentional test rollback', (
            'unexpected RuntimeError in skill XP rollback regression'
        )
    check(db.skill_progress(7, 'skill_1')['xp'] == prior,
          'rollback restores skill_1 XP')
    check(db.skill_progress(7, 'skill_2')['xp'] == prior,
          'rollback restores skill_2 XP')
    with db.conn.deferred_commits():
        db.add_skill_xp(7, 'skill_1', 17)
        db.add_skill_xp(7, 'skill_2', 17)
    check(db.skill_progress(7, 'skill_1')['xp'] == prior + 17,
          'grouped skill XP committed')
    check(db.skill_progress(7, 'skill_2')['xp'] == prior + 17,
          'second grouped skill XP committed')
    check(db.skill_progress(7, 'skill_2')['uses'] == 21,
          'grouped XP tracks exactly one use')
    check(db.skill_progress(8, 'skill_0')['uses'] == 40,
          'other account uses unchanged')
    raw.close()
    print(f'SKILL PROGRESS SQLITE v116.70: {checks}/{checks} PASS; 480 existing reads: 0 COMMIT; 480 real XP: 480 COMMIT', flush=True)
    return checks


if __name__ == '__main__':
    run()
