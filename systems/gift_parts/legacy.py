"""Odporne na duplikaty przejscie z prezentow v108."""
import datetime as dt

def _legacy_claimed(db, master, day, kind):
    """Never pay again after either old v108 gift on the same calendar day.

    v108 allowed Daily + manual Advent on the same date. An upgrade during
    December or on January 1 must not mint an additional v109 reward.
    """
    conn = db.conn
    existing = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='v108_advent_claims'").fetchone()
    if existing and conn.execute(
            'SELECT 1 FROM v108_advent_claims '
            'WHERE master_account_id=? AND gift_date=?',
            (master, day.isoformat())).fetchone():
        return True
    existing = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='daily_login_v03051'").fetchone()
    if not existing:
        return False
    return bool(conn.execute(
        'SELECT 1 FROM daily_login_v03051 dl JOIN account_characters ac '
        'ON ac.character_account_id=dl.account_id '
        'WHERE ac.master_account_id=? AND dl.last_day=? LIMIT 1',
        (master, day.isoformat())).fetchone())

def _update_daily_streak(conn, account_id, day):
    """Preserve old daily streak and best, but do not count Advent as Daily."""
    row=conn.execute('SELECT last_day,streak,best_streak FROM daily_login_v03051 '
                     'WHERE account_id=?',(account_id,)).fetchone()
    streak=1
    best=1
    if row:
        prev=dt.date.fromisoformat(row[0]) if row[0] else None
        if prev is not None and (day-prev).days == 1:
            streak=max(1,int(row[1])+1)
        best=max(1,int(row[2] or 0),streak)
    conn.execute(
        'INSERT INTO daily_login_v03051(account_id,last_day,streak,best_streak) '
        'VALUES(?,?,?,?) ON CONFLICT(account_id) DO UPDATE SET '
        'last_day=excluded.last_day,streak=excluded.streak,best_streak=excluded.best_streak',
        (account_id,day.isoformat(),streak,best))
    return streak
