# -*- coding: utf-8 -*-
"""Persistent v115 objective counters. No soundpack, runtime or old schema dependency.

Event recording and reward claiming are separated. An event identifier must be
unique for each *actual* combat/craft/exploration event; retries are idempotent.
Callers supply authoritative server event IDs, never client-provided IDs.
This module does NOT autonomously grant character rewards.
"""
from __future__ import annotations
import sqlite3
from .content_catalog import quest_catalog, achievement_catalog, repeatable_threshold

OBJECTIVE_KEYS = frozenset((q.region,q.objective) for q in quest_catalog())
QUESTS = {q.key: q for q in quest_catalog()}
ACHIEVEMENTS = {a.key: a for a in achievement_catalog()}

def ensure_schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS v115_objective_events (
       account_id INTEGER NOT NULL, event_id TEXT NOT NULL,
       region TEXT NOT NULL, objective TEXT NOT NULL, amount INTEGER NOT NULL,
       PRIMARY KEY(account_id,event_id))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS v115_objective_totals (
       account_id INTEGER NOT NULL, region TEXT NOT NULL, objective TEXT NOT NULL,
       amount INTEGER NOT NULL DEFAULT 0 CHECK(amount >= 0),
       PRIMARY KEY(account_id,region,objective))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS v115_objective_claims (
       account_id INTEGER NOT NULL, claim_key TEXT NOT NULL, cycle INTEGER NOT NULL,
       PRIMARY KEY(account_id,claim_key,cycle))""")

def record_event(conn, account_id, event_id, region, objective, amount=1):
    """Record once in current SQL transaction; caller commits alongside game event."""
    if not isinstance(account_id,int) or isinstance(account_id,bool) or account_id < 1:
        raise ValueError('account_id')
    if not isinstance(event_id,str) or not 1 <= len(event_id) <= 160:
        raise ValueError('event_id')
    if (region,objective) not in OBJECTIVE_KEYS:
        raise ValueError('unknown v115 region/objective')
    if isinstance(amount,bool) or not isinstance(amount,int) or not 1 <= amount <= 10000:
        raise ValueError('amount')
    ensure_schema(conn)
    inserted=conn.execute("""INSERT OR IGNORE INTO v115_objective_events
        (account_id,event_id,region,objective,amount) VALUES(?,?,?,?,?)""",
        (account_id,event_id,region,objective,amount)).rowcount
    if inserted:
        conn.execute("""INSERT INTO v115_objective_totals(account_id,region,objective,amount)
            VALUES(?,?,?,?) ON CONFLICT(account_id,region,objective)
            DO UPDATE SET amount=amount+excluded.amount""",
            (account_id,region,objective,amount))
    return bool(inserted)

def total(conn, account_id, region, objective):
    ensure_schema(conn)
    row=conn.execute("""SELECT amount FROM v115_objective_totals
        WHERE account_id=? AND region=? AND objective=?""",
        (account_id,region,objective)).fetchone()
    return int(row[0]) if row else 0

def available_claims(conn, account_id, kind='achievement', limit=50):
    """Return pending reward identifiers, not payout instructions."""
    if kind not in ('achievement','quest'): raise ValueError('kind')
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=200:
        raise ValueError('limit')
    ensure_schema(conn)
    catalog=ACHIEVEMENTS if kind=='achievement' else QUESTS
    result=[]
    for item in catalog.values():
        progress=total(conn,account_id,item.region,item.objective)
        base=item.threshold if kind=='achievement' else item.target
        if progress<base:continue
        # Cycles are incremental milestones, never duplicate the same award.
        max_cycle=min(1000000, progress//base-1) if kind=='achievement' and item.repeatable else 0
        rows=conn.execute("""SELECT cycle FROM v115_objective_claims
             WHERE account_id=? AND claim_key=? AND cycle<=?""",
             (account_id,item.key,max_cycle)).fetchall()
        paid={int(row[0]) for row in rows}
        for cycle in range(max_cycle+1):
            if cycle not in paid:
                result.append((item.key,cycle))
                if len(result)>=limit:return result
    return result

def mark_claimed(conn, account_id, key, cycle):
    """Reserve settlement in SAME transaction as authoritative reward payout.

    Caller must rollback entire transaction if reward credit fails. Never call
    in a separate transaction *after* granting payout, to avoid duplicates.
    """
    item=ACHIEVEMENTS.get(key) or QUESTS.get(key)
    if item is None:raise ValueError('unknown reward')
    if isinstance(cycle,bool) or not isinstance(cycle,int) or not 0<=cycle<=1000000:
        raise ValueError('cycle')
    if key in QUESTS and cycle!=0:raise ValueError('non-repeatable quest')
    base=item.threshold if key in ACHIEVEMENTS else item.target
    needed=repeatable_threshold(base,cycle)
    if total(conn,account_id,item.region,item.objective)<needed:
        return False
    inserted=conn.execute("""INSERT OR IGNORE INTO v115_objective_claims
        (account_id,claim_key,cycle) VALUES(?,?,?)""",(account_id,key,cycle)).rowcount
    return bool(inserted)
