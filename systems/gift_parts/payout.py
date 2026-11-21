"""Atomowa wyplata SQLite, EXP i portfela z rollbackiem."""
import datetime as dt
from .rewards import reward_plan, award_daily_growth
from .legacy import _legacy_claimed, _update_daily_streak

def claim_once(session, *, day=None):
    """Award with rollback if anything (wallet, XP, SQL) fails. No await inside."""
    from systems.atomic_character_experience_v10400 import award_character_xp_atomic_v10400
    from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, legacy_currency_to_coins
    if day is None:
        day=dt.datetime.now().astimezone().date()
    if session.closed or not session.character or session.account_id is None:
        return None
    db=session.server.db
    conn=db.conn
    if conn.in_transaction:
        raise RuntimeError('Transakcja SQLite zajęta; nagroda nieprzyznana')
    account=int(session.account_id)
    char=session.character
    master=int(db.master_account_for_character(account))
    plan=reward_plan(day,master,char)
    # A single gift must roll back *every* character axis if any domain fails.
    old=dict(char.__dict__)
    from systems.v115.optional_sound import (
        sound_reward_queue_checkpoint_v11329, sound_reward_queue_rollback_v11329)
    audio_before=sound_reward_queue_checkpoint_v11329(db,account)
    with conn.deferred_commits():
        conn.execute('SAVEPOINT v109_daily_gift_once')
        try:
            conn.execute(
                'CREATE TABLE IF NOT EXISTS v109_gift_claims('
                'master_account_id INTEGER NOT NULL, gift_date TEXT NOT NULL, '
                'gift_kind TEXT NOT NULL CHECK(gift_kind IN (\'advent\',\'daily\')), '
                'reward_silver INTEGER NOT NULL, reward_exp INTEGER NOT NULL, '
                'PRIMARY KEY(master_account_id,gift_date))')
            if conn.execute('SELECT 1 FROM v109_gift_claims '
                            'WHERE master_account_id=? AND gift_date=?',
                            (master,day.isoformat())).fetchone():
                conn.execute('ROLLBACK TO SAVEPOINT v109_daily_gift_once')
                conn.execute('RELEASE SAVEPOINT v109_daily_gift_once')
                return None
            if _legacy_claimed(db,master,day,plan['kind']):
                # Old v108 payout was already made on this date; no second gift.
                conn.execute('ROLLBACK TO SAVEPOINT v109_daily_gift_once')
                conn.execute('RELEASE SAVEPOINT v109_daily_gift_once')
                return None
            current=legacy_currency_to_coins(*db.shared_wallet_for_master(master))
            if current > CURRENCY_SQLITE_SAFE_TOTAL - plan['silver']:
                raise OverflowError('Brak miejsca w portfelu na prezent')
            db.set_shared_wallet_for_master(master,current+plan['silver'],0,0,commit=False)
            db.apply_shared_wallet_to_character(char)
            paid,notes=award_character_xp_atomic_v10400(db,char,account,plan['exp'])
            other_xp=award_daily_growth(session,plan['kind'])
            if plan['kind']=='daily':
                _update_daily_streak(conn,account,day)
            conn.execute('INSERT INTO v109_gift_claims '
                         '(master_account_id,gift_date,gift_kind,reward_silver,reward_exp) '
                         'VALUES(?,?,?,?,?)',
                         (master,day.isoformat(),plan['kind'],plan['silver'],paid))
            conn.execute('RELEASE SAVEPOINT v109_daily_gift_once')
        except BaseException:
            try:
                conn.execute('ROLLBACK TO SAVEPOINT v109_daily_gift_once')
                conn.execute('RELEASE SAVEPOINT v109_daily_gift_once')
            finally:
                char.__dict__.clear()
                char.__dict__.update(old)
                sound_reward_queue_rollback_v11329(db,account,audio_before)
            raise
    return dict(plan,exp=paid,level_notes=notes,other_xp=other_xp)
