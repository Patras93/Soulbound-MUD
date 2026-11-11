# -*- coding: utf-8 -*-
"""v111 roboczy: bezpieczny rejestr polowań dziennych i tygodniowych.

Nie wypłaca EXP/waluty. Wydanie nagród ma zostać podłączone do istniejącego
jednorazowego mechanizmu, po certyfikacji v111. Stan jest na *konto główne*.
Rejestrację wywołuje się tylko po potwierdzonej walce, nie z komendy gracza.
"""
from __future__ import annotations
import sqlite3
from systems.holiday.schedule import active_schedule

DAILY_KILLS = 5
WEEKLY_BOSSES = 1
PREFIX = 'v11100_holiday_'


def _catalog_id(mob_id):
    if not isinstance(mob_id, str) or not mob_id.startswith(PREFIX):
        return None
    tail = mob_id[len(PREFIX):]
    month, sep, kind = tail.partition('_')
    if not sep or not month.isdigit() or len(month) != 2 or not 1 <= int(month) <= 12:
        return None
    if kind not in ('mob_1','mob_2','mob_3','mob_4','boss'):
        return None
    return int(month), kind


def _init(conn):
    conn.execute('CREATE TABLE IF NOT EXISTS v111_holiday_challenge_progress ('
                 'master_id INTEGER NOT NULL, period_type TEXT NOT NULL '
                 'CHECK (period_type IN (\'D\',\'W\')), period TEXT NOT NULL, '
                 'count INTEGER NOT NULL DEFAULT 0 CHECK (count>=0), '
                 'PRIMARY KEY(master_id,period_type,period))')
    conn.execute('CREATE TABLE IF NOT EXISTS v111_holiday_challenge_kills ('
                 'master_id INTEGER NOT NULL, fight_id TEXT NOT NULL, '
                 'PRIMARY KEY(master_id,fight_id))')


def record_kill(conn:sqlite3.Connection, master_id:int, mob_id:str, fight_id:str, *, day=None):
    """Zapisz jedno unikalne zabicie. Wymaga niepustego stabilnego fight_id.

    Jeśli powtórzono callback, nic nie dopisze. Rzut błędu cofa całe wywołanie.
    Operuje na istniejącej transakcji z savepointem, nie wykonuje commit.
    """
    state = active_schedule(day)
    parsed = _catalog_id(mob_id)
    if parsed is None or parsed[0] != state['month']:
        return {'credited':False,'reason':'inactive_month_or_mob'}
    master = int(master_id)
    if master <= 0 or not isinstance(fight_id,str) or not 1 <= len(fight_id) <= 160:
        raise ValueError('Invalid verified fight identity')
    if any(ord(c)<32 for c in fight_id):raise ValueError('Control character in fight ID')
    # Kontrakt: wywołanie przez warstwę po bezpiecznym potwierdzeniu wyniku walki.
    conn.execute('SAVEPOINT v111_holiday_kill')
    try:
        _init(conn)
        found = conn.execute('SELECT 1 FROM v111_holiday_challenge_kills '
                             'WHERE master_id=? AND fight_id=?',(master,fight_id)).fetchone()
        if found:
            conn.execute('RELEASE SAVEPOINT v111_holiday_kill')
            return {'credited':False,'reason':'duplicate'}
        conn.execute('INSERT INTO v111_holiday_challenge_kills(master_id,fight_id) VALUES(?,?)',
                     (master,fight_id))
        periods=[('D',state['daily_key'],DAILY_KILLS)]
        if parsed[1]=='boss':periods.append(('W',state['weekly_key'],WEEKLY_BOSSES))
        for period_type,key,limit in periods:
            conn.execute('INSERT INTO v111_holiday_challenge_progress'
                         '(master_id,period_type,period,count) VALUES(?,?,?,1) '
                         'ON CONFLICT(master_id,period_type,period) DO UPDATE SET '
                         'count=MIN(count+1,?)',(master,period_type,key,limit))
        conn.execute('RELEASE SAVEPOINT v111_holiday_kill')
        return {'credited':True,'daily':state['daily_key'],
                'weekly':state['weekly_key'] if parsed[1]=='boss' else None}
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v111_holiday_kill')
        conn.execute('RELEASE SAVEPOINT v111_holiday_kill')
        raise


def progress(conn, master_id:int, day=None):
    state=active_schedule(day)
    exists=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                        "name='v111_holiday_challenge_progress'").fetchone()
    result={'daily':0,'daily_goal':DAILY_KILLS,'weekly':0,
            'weekly_goal':WEEKLY_BOSSES,'daily_key':state['daily_key'],
            'weekly_key':state['weekly_key']}
    if not exists:return result
    for tag,key,field in (('D',state['daily_key'],'daily'),('W',state['weekly_key'],'weekly')):
        row=conn.execute('SELECT count FROM v111_holiday_challenge_progress '
                         'WHERE master_id=? AND period_type=? AND period=?',
                         (int(master_id),tag,key)).fetchone()
        result[field]=int(row[0]) if row else 0
    return result
