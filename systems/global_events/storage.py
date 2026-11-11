# -*- coding: utf-8 -*-
"""Tylko nowe tabele v110; nigdy nie przepisuje istniejących danych SQLite."""

def create_schema(conn):
    commands=(
       'CREATE TABLE IF NOT EXISTS v110_event_progress ('
       'slot INTEGER PRIMARY KEY, slug TEXT NOT NULL, kills INTEGER NOT NULL DEFAULT 0 CHECK(kills>=0), '
       'completed_at INTEGER NOT NULL DEFAULT 0)',
       'CREATE TABLE IF NOT EXISTS v110_event_death_receipts ('
       'slot INTEGER NOT NULL, encounter TEXT NOT NULL, PRIMARY KEY(slot,encounter))',
       'CREATE TABLE IF NOT EXISTS v110_event_participants ('
       'slot INTEGER NOT NULL, account_id INTEGER NOT NULL, PRIMARY KEY(slot,account_id))',
       'CREATE TABLE IF NOT EXISTS v110_event_reward_receipts ('
       'slot INTEGER NOT NULL, account_id INTEGER NOT NULL, item_id TEXT NOT NULL, '
       'PRIMARY KEY(slot,account_id))',
    )
    for command in commands:conn.execute(command)
    return len(commands)
