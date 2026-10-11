# -*- coding: utf-8 -*-
"""14-profession mastery, non-destructive SQLite ledger and action-backed orders.

Orders use snapshots of the existing *successful profession action counter*.
Merely sending commands or collecting inventory cannot complete an order.
"""
from __future__ import annotations
import time
from systems.imperial_economy_v1320 import atomic
from core.bootstrap_economy_professions import normalize_profession_name, TOOL_PROFESSION_MAP

SPECIALTIES = {
    'Wędkarstwo': ('Łowca Głębin','Mistrz Sieci','Tropiciel Ławic'),
    'Górnictwo': ('Poszukiwacz Złóż','Mistrz Kryształów','Górnik Otchłani'),
    'Drwalstwo': ('Strażnik Lasu','Mistrz Pni','Cieśla Leśny'),
    'Kowalstwo': ('Płatnerz','Mistrz Broni','Kowal Runiczny'),
    'Gotowanie': ('Kucharz Wypraw','Mistrz Uczt','Kucharz Głębin'),
    'Zielarstwo': ('Odkrywca Roślin','Mistrz Ziół','Badacz Raf'),
    'Alchemia': ('Mistrz Eliksirów','Badacz Żywiołów','Alchemik Otchłani'),
    'Jubilerstwo': ('Szlifierz Gwiazd','Mistrz Klejnotów','Jubiler Głębin'),
    'Krawiectwo': ('Tkacz Run','Krawiec Mistrzów','Tkacz Astralny'),
    'Garbarstwo': ('Płatnerz Skór','Garbarz Mistrzów','Garbarz Lewiatana'),
    'Stolarstwo': ('Budowniczy Statków','Mistrz Warsztatu','Cieśla Runiczny'),
    'Zaklinanie': ('Mistrz Run','Zaklinacz Żywiołów','Zaklinacz Dusz'),
    'Archeologia': ('Badacz Reliktów','Strażnik Dziedzictwa','Odkrywca Głębin'),
    'Kartografia': ('Kartograf Oceanów','Mistrz Szlaków','Kartograf Otchłani'),
}
MILESTONES = (100, 250, 450)
COOLDOWN = 3600
TOOLS = {name:tool for tool,name in TOOL_PROFESSION_MAP.items()}


def canonical(text):
    value = normalize_profession_name(str(text or ''))
    if value not in SPECIALTIES:
        raise ValueError('Nieznana profesja. Wpisz mistrzprof lista.')
    return value


def init(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS profession_specialties_v2200 (
        account_id INTEGER NOT NULL, profession TEXT NOT NULL, specialty TEXT NOT NULL,
        unlocked_at INTEGER NOT NULL, PRIMARY KEY(account_id,profession,specialty))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS profession_master_orders_v2200 (
        account_id INTEGER NOT NULL, profession TEXT NOT NULL,
        start_actions INTEGER NOT NULL, goal_actions INTEGER NOT NULL,
        started_at INTEGER NOT NULL, last_claim_at INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL CHECK(status IN ('active','claimed','abandoned')),
        completions INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(account_id,profession))""")
    conn.commit()


def unlock(conn, account, profession, specialty, level, *, now=None):
    profession=canonical(profession)
    if specialty not in SPECIALTIES[profession]:
        raise ValueError('Nieznana specjalizacja tej profesji.')
    now=int(time.time()) if now is None else int(now)
    with atomic(conn):
        unlocked={r[0] for r in conn.execute(
            'SELECT specialty FROM profession_specialties_v2200 WHERE account_id=? AND profession=?',
            (account,profession))}
        if specialty in unlocked: raise ValueError('Specjalizacja już odblokowana.')
        required=MILESTONES[len(unlocked)] if len(unlocked)<3 else 999999
        if int(level)<required: raise ValueError(f'Wymagany poziom profesji {required}.')
        conn.execute('INSERT INTO profession_specialties_v2200 VALUES (?,?,?,?)',
                     (account,profession,specialty,now))
    return required


def start_order(conn, account, profession, level, actions, *, now=None):
    profession=canonical(profession)
    now=int(time.time()) if now is None else int(now)
    if int(level)<100:raise ValueError('Mistrzowskie zamówienia od poziomu 100 profesji.')
    with atomic(conn):
        old=conn.execute('SELECT * FROM profession_master_orders_v2200 WHERE account_id=? AND profession=?',
                         (account,profession)).fetchone()
        if old and old['status']=='active': raise ValueError('Zamówienie jest już aktywne.')
        if old and now-int(old['last_claim_at'])<COOLDOWN:
            raise ValueError('Zamówienie odnawia się po godzinie od odbioru.')
        needed=max(3,min(30,3+int(level)//70))
        conn.execute("""INSERT INTO profession_master_orders_v2200
            (account_id,profession,start_actions,goal_actions,started_at,last_claim_at,status,completions)
            VALUES(?,?,?,?,?,0,'active',0) ON CONFLICT(account_id,profession) DO UPDATE SET
            start_actions=excluded.start_actions,goal_actions=excluded.goal_actions,
            started_at=excluded.started_at,status='active' """,
            (account,profession,int(actions),needed,now))
    return needed


def status(conn, account, profession, actions):
    profession=canonical(profession)
    row=conn.execute('SELECT * FROM profession_master_orders_v2200 WHERE account_id=? AND profession=?',
                     (account,profession)).fetchone()
    if not row:return 'brak zamówienia'
    if row['status']!='active':return str(row['status'])
    done=max(0,int(actions)-int(row['start_actions']))
    return f'{min(done,int(row["goal_actions"]))}/{row["goal_actions"]} prawdziwych czynności'


def claim(conn, account, profession, level, actions, *, now=None):
    profession=canonical(profession)
    now=int(time.time()) if now is None else int(now)
    with atomic(conn):
        row=conn.execute('SELECT * FROM profession_master_orders_v2200 WHERE account_id=? AND profession=?',
                         (account,profession)).fetchone()
        if not row or row['status']!='active':raise ValueError('Brak aktywnego zamówienia.')
        if int(actions)-int(row['start_actions'])<int(row['goal_actions']):
            raise ValueError('Zamówienie niegotowe. Wykonaj wymagane czynności profesji.')
        unlocked=conn.execute('SELECT COUNT(*) FROM profession_specialties_v2200 WHERE account_id=? AND profession=?',
                              (account,profession)).fetchone()[0]
        silver=int(row['goal_actions'])*(1200+int(level)*55)*(100+10*int(unlocked))//100
        if silver<=0:raise ValueError('Błąd wyceny zamówienia.')
        cur=conn.execute('UPDATE profession_master_orders_v2200 SET status=?,last_claim_at=?,completions=completions+1 '
                         'WHERE account_id=? AND profession=? AND status=?',
                         ('claimed',now,account,profession,'active'))
        if cur.rowcount!=1:raise ValueError('Nagroda została już odebrana.')
        # Use the game's canonical wallet conversion, without touching inventory or levels.
        from systems.imperial_economy_v1321 import _wallet
        balance=_wallet(conn,account)
        if balance+silver>=8_000_000_000_000_000_000:raise ValueError('Przekroczono limit salda.')
        conn.execute('UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?',
                     (balance+silver,account))
    return silver,balance+silver


def abandon(conn, account, profession):
    profession=canonical(profession)
    with atomic(conn):
        cur=conn.execute('UPDATE profession_master_orders_v2200 SET status=? '
                         'WHERE account_id=? AND profession=? AND status=?',
                         ('abandoned',account,profession,'active'))
        if cur.rowcount!=1:raise ValueError('Brak aktywnego zamówienia.')
