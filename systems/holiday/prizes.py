# -*- coding: utf-8 -*-
"""Nagrody prób świątecznych. Jednorazowe odbieranie, na konto główne.

Rozliczenie na jednym SQLite SAVEPOINT, z odwróceniem stanu postaci przy błędzie.
Nie zmienia istniejącego mechanizmu prezentów v109 ani zwykłych walk.
"""
from __future__ import annotations
from systems.holiday.challenges import DAILY_KILLS, WEEKLY_BOSSES, progress
from systems.holiday.schedule import active_schedule


def prize_info(conn, master_id, day=None):
    state = progress(conn, master_id, day)
    table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v111_holiday_prize_claims'").fetchone()
    claimed = set()
    if table:
        claimed = {row[0] for row in conn.execute(
            'SELECT period_type FROM v111_holiday_prize_claims WHERE master_id=? '
            'AND ((period_type=\'D\' AND period=?) OR (period_type=\'W\' AND period=?))',
            (int(master_id), state['daily_key'], state['weekly_key']))}
    return {'daily':state['daily'], 'daily_goal':DAILY_KILLS,
            'weekly':state['weekly'], 'weekly_goal':WEEKLY_BOSSES,
            'daily_claimed':'D' in claimed, 'weekly_claimed':'W' in claimed}


def claim(session, kind, *, day=None):
    """Zwraca None, jeśli niegotowe/odebrane; w innym wypadku opis wypłaty.

    Wywoływane przez most potwierdzonej walki; bez await w transakcji.
    """
    from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, legacy_currency_to_coins
    from systems.atomic_character_experience_v10400 import award_character_xp_atomic_v10400
    if kind not in ('D','W'):
        raise ValueError('Nieznany rodzaj próby')
    if session.closed or session.character is None or session.account_id is None:
        return None
    db=session.server.db
    conn=db.conn
    if conn.in_transaction:
        raise RuntimeError('Transakcja SQLite zajęta; nagroda nieprzyznana')
    account=int(session.account_id)
    master=int(db.master_account_for_character(account))
    if master<=0:raise ValueError('Brak konta głównego')
    character=session.character
    state=active_schedule(day)
    period=state['daily_key'] if kind=='D' else state['weekly_key']
    reward_silver=2500 if kind=='D' else 15000
    reward_xp=10000 if kind=='D' else 60000
    # Różne poziomy postaci zachowują własną skalę starego silnika EXP.
    old=(character.character_level, character.character_xp,
         character.silver,character.gold,character.mithril)
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v111_holiday_prize')
        try:
            details=prize_info(conn,master,day)
            if (kind=='D' and (details['daily']<DAILY_KILLS or details['daily_claimed'])) or (kind=='W' and (details['weekly']<WEEKLY_BOSSES or details['weekly_claimed'])):
                conn.execute('RELEASE SAVEPOINT v111_holiday_prize')
                return None
            conn.execute('CREATE TABLE IF NOT EXISTS v111_holiday_prize_claims ('
                         'master_id INTEGER NOT NULL, period_type TEXT NOT NULL '
                         'CHECK(period_type IN (\'D\',\'W\')), period TEXT NOT NULL, '
                         'reward_silver INTEGER NOT NULL, reward_exp INTEGER NOT NULL, '
                         'PRIMARY KEY(master_id,period_type,period))')
            coins=legacy_currency_to_coins(*db.shared_wallet_for_master(master))
            if coins>CURRENCY_SQLITE_SAFE_TOTAL-reward_silver:
                raise OverflowError('Portfel nie pomieści nagrody')
            db.set_shared_wallet_for_master(master,coins+reward_silver,0,0,commit=False)
            db.apply_shared_wallet_to_character(character)
            paid,notes=award_character_xp_atomic_v10400(db,character,account,reward_xp)
            conn.execute('INSERT INTO v111_holiday_prize_claims VALUES (?,?,?,?,?)',
                         (master,kind,period,reward_silver,paid))
            conn.execute('RELEASE SAVEPOINT v111_holiday_prize')
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT v111_holiday_prize')
                conn.execute('RELEASE SAVEPOINT v111_holiday_prize')
            finally:
                (character.character_level,character.character_xp,
                 character.silver,character.gold,character.mithril)=old
            raise
    return {'kind':kind,'period':period,'silver':reward_silver,'exp':paid,'notes':notes}
