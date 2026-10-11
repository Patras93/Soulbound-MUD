# -*- coding: utf-8 -*-
"""Account-scoped, restart-safe Titan trophies and personal rewards."""
from __future__ import annotations
import time


class DatabaseTitansV2100Mixin:
    def create_titans_schema_v2100(self):
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS titan_records_v2100 (
            account_id INTEGER NOT NULL, titan_slug TEXT NOT NULL,
            defeats INTEGER NOT NULL DEFAULT 0, first_at INTEGER NOT NULL,
            last_at INTEGER NOT NULL, last_bonus_at INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(account_id, titan_slug),
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS titan_floor_clears_v2100 (
            account_id INTEGER NOT NULL, family TEXT NOT NULL,
            floor INTEGER NOT NULL, cleared_at INTEGER NOT NULL,
            PRIMARY KEY(account_id, family, floor),
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS titan_secrets_v2100 (
            account_id INTEGER NOT NULL, family TEXT NOT NULL,
            floor INTEGER NOT NULL, discovered_at INTEGER NOT NULL,
            PRIMARY KEY(account_id, family, floor),
            FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
        );
        ''')
        self.conn.commit()

    def record_titan_defeat_v2100(self, account_id, slug, family, floor, now=None):
        """Bookkeeping and reward inventory in the same SQLite transaction.

        The MobState kill lock is the outer idempotency guard per actual kill;
        these PKs ensure unique first victories and 24-hour repeat bonuses.
        """
        from systems.titans_v2100 import TITAN_BY_SLUG, FAMILIES
        from systems.content_registry import ITEMS
        aid, floor = int(account_id), int(floor)
        slug, family = str(slug), str(family)
        if slug not in TITAN_BY_SLUG or family not in FAMILIES or floor < 50 or floor % 50:
            raise ValueError('Nieprawidłowe zaliczenie Tytana')
        stamp = int(time.time() if now is None else now)
        row = self.conn.execute(
            'SELECT defeats,last_bonus_at FROM titan_records_v2100 '
            'WHERE account_id=? AND titan_slug=?',(aid,slug)
        ).fetchone()
        first_titan = row is None
        bonus = first_titan or stamp - int(row['last_bonus_at'] or 0) >= 24*3600
        if first_titan:
            self.conn.execute('INSERT INTO titan_records_v2100 '
                '(account_id,titan_slug,defeats,first_at,last_at,last_bonus_at) VALUES(?,?,1,?,?,?)',
                (aid,slug,stamp,stamp,stamp))
            relic = f'v2100_relic_{slug}'
            if relic not in ITEMS:
                raise RuntimeError('Brak autorskiego trofeum: '+relic)
            self.add_item(aid,relic,1,commit=False)
        else:
            self.conn.execute('UPDATE titan_records_v2100 '
                'SET defeats=defeats+1,last_at=?,last_bonus_at=? '
                'WHERE account_id=? AND titan_slug=?',
                (stamp,stamp if bonus else int(row['last_bonus_at']),aid,slug))
        floor_first = self.conn.execute(
            'INSERT OR IGNORE INTO titan_floor_clears_v2100 '
            '(account_id,family,floor,cleared_at) VALUES(?,?,?,?)',
            (aid,family,floor,stamp)
        ).rowcount > 0
        amount = min(25,4+floor//200) if bonus else 0
        if amount:
            self.add_item(aid,'v2100_titan_essence',amount,commit=False)
        self.conn.commit()
        return {'first_titan':first_titan,'first_floor':floor_first,
                'relic':f'v2100_relic_{slug}' if first_titan else '',
                'essence':amount}

    def claim_titan_secret_v2100(self, account_id, family, floor, now=None):
        from systems.titans_v2100 import FAMILIES
        aid, floor, family = int(account_id), int(floor), str(family)
        if family not in FAMILIES or floor < 25 or floor % 25 or floor % 50 == 0:
            raise ValueError('Nieprawidłowa sekretna komnata')
        stamp = int(time.time() if now is None else now)
        first = self.conn.execute(
            'INSERT OR IGNORE INTO titan_secrets_v2100 '
            '(account_id,family,floor,discovered_at) VALUES(?,?,?,?)',
            (aid,family,floor,stamp)
        ).rowcount > 0
        if first:
            self.add_item(aid,'v2100_titan_essence',min(8,1+floor//150),commit=False)
        self.conn.commit()
        return first

    def titan_records_v2100(self, account_id):
        return self.conn.execute(
            'SELECT titan_slug,defeats,last_bonus_at FROM titan_records_v2100 '
            'WHERE account_id=? ORDER BY titan_slug',(int(account_id),)
        ).fetchall()

    def titan_secret_known_v2100(self, account_id, family, floor):
        return bool(self.conn.execute(
            'SELECT 1 FROM titan_secrets_v2100 '
            'WHERE account_id=? AND family=? AND floor=?',
            (int(account_id),str(family),int(floor))
        ).fetchone())
