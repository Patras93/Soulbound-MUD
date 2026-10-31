# -*- coding: utf-8 -*-
"""Runtime SQLite write barrier for existing INTEGER persistence.

Does NOT enable BigNumber or rewrite old balances. Its purpose is to block
accidental REAL/TEXT storage on high-value axes through *direct SQL writers*,
including paths that never call the Python preflight guards.  The triggers
are deliberately additive and only inspect columns present in this schema.
"""
from __future__ import annotations

# Internal allowlist only; values and identifiers never come from players.
NUMERIC_FIELDS = {
    'characters': (
        'character_xp', 'soul_xp', 'character_level', 'soul_level', 'soul_tier',
        'soul_weapon_mastery_level', 'soul_weapon_mastery_xp', 'stat_progress',
        'strength_progress', 'dexterity_progress', 'constitution_progress',
        'intelligence_progress', 'willpower_progress', 'charisma_progress',
        'silver', 'gold', 'mithril',
    ),
    'class_progress': ('level', 'xp'),
    'professions': ('level', 'xp', 'actions'),
    'tools': ('level', 'xp', 'uses'),
    'account_wallet': ('silver', 'gold', 'mithril'),
    'bank_balances': ('silver', 'gold', 'mithril'),
}


def install_numeric_write_barriers(conn) -> int:
    """Install non-destructive, transaction-aware constraints at game boot.

    Does not scan/rewrite old records or COMMIT a transaction belonging to
    another component.  Compatible with SQLite's ordinary upsert semantics.
    """
    installed = 0
    for table, candidate_fields in NUMERIC_FIELDS.items():
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if exists is None:
            continue
        actual = {row[1] for row in conn.execute('PRAGMA table_info("' + table + '")')}
        fields = tuple(field for field in candidate_fields if field in actual)
        if not fields:
            continue
        # Zero tolerance for REAL/TEXT in the legacy INTEGER mirrors.  NULL is
        # accepted for historical nullable schema columns; migration audits
        # check missing values separately.
        assertions = ' OR '.join(
            f'typeof(NEW."{field}") NOT IN (\'integer\',\'null\')'
            for field in fields
        )
        message = 'SB104: odmowa utraty precyzji w ' + table
        for action in ('INSERT', 'UPDATE'):
            name = f'sb104_int_guard_{table}_{action.lower()}'
            when = '' if action == 'INSERT' else (
                ' OF ' + ','.join('"' + field + '"' for field in fields)
            )
            conn.execute(
                f'CREATE TRIGGER IF NOT EXISTS "{name}" '
                f'BEFORE {action}{when} ON "{table}" BEGIN '
                f"SELECT RAISE(ABORT, '{message}') WHERE {assertions}; END"
            )
            installed += 1
    return installed
