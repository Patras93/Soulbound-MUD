# -*- coding: utf-8 -*-
"""Run fixed CREATE schema statements without sqlite3.executescript implicit COMMIT.

Use only for trusted, literal schema definitions; no SQL user input.
"""
import re
import sqlite3

_CREATE_DDL = re.compile(r'^CREATE\s+(?:UNIQUE\s+)?(?:TABLE|INDEX)\s+IF\s+NOT\s+EXISTS\b', re.I)

def apply_create_schema_v104(conn, script):
    """Preserve caller ownership of an already-open SQLite transaction."""
    outer = conn.in_transaction
    pending = ''
    conn.execute('SAVEPOINT v104_safe_ddl')
    try:
        for line in script.splitlines(keepends=True):
            pending += line
            if sqlite3.complete_statement(pending):
                statement = pending.strip()
                pending = ''
                if not statement or statement == ';':
                    continue
                if not _CREATE_DDL.match(statement):
                    raise ValueError('Niedozwolone polecenie inicjalizacji schematu SQLite.')
                conn.execute(statement)
        if pending.strip():
            raise ValueError('Niekompletne polecenie CREATE w schemacie SQLite.')
        conn.execute('RELEASE SAVEPOINT v104_safe_ddl')
    except BaseException:
        try:
            conn.execute('ROLLBACK TO SAVEPOINT v104_safe_ddl')
        finally:
            conn.execute('RELEASE SAVEPOINT v104_safe_ddl')
        raise
    if not outer:
        conn.commit()
