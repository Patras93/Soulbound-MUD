# -*- coding: utf-8 -*-
"""Wydzielone metody bazy kont: presence."""
from .dependencies import *

class PresenceV109Mixin:
    def mark_player_login_v0363(self, account_id, now_ts=None):
        now_ts = int(time.time() if now_ts is None else now_ts)
        self.conn.execute(
            "INSERT INTO player_presence_v0363(account_id,last_login_ts,last_seen_ts,login_count) VALUES(?,?,?,1) "
            "ON CONFLICT(account_id) DO UPDATE SET last_login_ts=excluded.last_login_ts,last_seen_ts=excluded.last_seen_ts,login_count=player_presence_v0363.login_count+1",
            (int(account_id), now_ts, now_ts),
        )
        self.conn.commit()

    def mark_player_logout_v0363(self, account_id, now_ts=None):
        now_ts = int(time.time() if now_ts is None else now_ts)
        self.conn.execute(
            "INSERT INTO player_presence_v0363(account_id,last_logout_ts,last_seen_ts,login_count) VALUES(?,?,?,0) "
            "ON CONFLICT(account_id) DO UPDATE SET last_logout_ts=excluded.last_logout_ts,last_seen_ts=excluded.last_seen_ts",
            (int(account_id), now_ts, now_ts),
        )
        self.conn.commit()

    def player_presence_v0363(self, account_id):
        return self.conn.execute(
            "SELECT last_login_ts,last_logout_ts,last_seen_ts,login_count FROM player_presence_v0363 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()
