# -*- coding: utf-8 -*-
"""v28: accessible number-only NEWS navigation and isolated read with old SQLite."""
import asyncio
from validation.v1204_news_channel import _DB, _Session, SessionSocialExpansionMixin
from types import SimpleNamespace

async def check():
    db = _DB()
    server = SimpleNamespace(db=db, sessions=[])
    admin = _Session(server, 1, True)
    user = _Session(server, 2, False)
    server.sessions = [admin, user]
    news = SessionSocialExpansionMixin.news_channel_v1204
    checks = 0
    async def ok(condition, label):
        nonlocal checks
        assert condition, label
        checks += 1
    try:
        await news(user, '')
        await ok(user.sent == ['NEWS: brak wiadomości.'], 'empty index')
        await news(user, 'read 1')
        await ok('brak wpisu' in user.sent[-1], 'empty read')
        first = 'Zmiany wielkiej aktualizacji. ' + 'Szczegóły, ' * 42 + 'KONIEC.'
        await news(admin, first)
        await news(admin, 'Druga aktualizacja - bossowie')
        await news(admin, 'Trzecia aktualizacja - questy')
        await ok(db.conn.execute("SELECT COUNT(*) FROM social_channel_history_v03051 WHERE channel='news'").fetchone()[0] == 3, 'persistent announcements')
        user.sent.clear()
        await news(user, '')
        await ok(len(user.sent) == 4, 'index only header and three lines')
        await ok('news read NUMER' in user.sent[0], 'help in index')
        await ok(user.sent[1].startswith('1. ') and 'Trzecia' in user.sent[1], 'newest first')
        await ok(user.sent[2].startswith('2. ') and 'Druga' in user.sent[2], 'second')
        await ok(user.sent[3].startswith('3. ') and 'Zmiany' in user.sent[3], 'oldest')
        await ok(all('KONIEC' not in msg for msg in user.sent), 'index does not leak full article')
        user.sent.clear()
        await news(user, 'read 3')
        await ok(len(user.sent) == 1 and first in user.sent[0], 'one selected article')
        await ok('Druga aktualizacja' not in user.sent[0], 'other articles not read')
        await news(user, 'czytaj 1')
        await ok('Trzecia aktualizacja' in user.sent[-1], 'polish alias')
        await news(user, 'read 0')
        await ok('od 1 do 500' in user.sent[-1], 'bounds lower')
        await news(user, 'read 999')
        await ok('od 1 do 500' in user.sent[-1], 'bounds upper')
        await news(user, 'read n')
        await ok('Użycie' in user.sent[-1] or 'użycie' in user.sent[-1], 'no arbitrary text')
        await news(user, 'read 4')
        await ok('brak wpisu' in user.sent[-1], 'out-of-range')
        await news(user, 'lista 2')
        await ok(user.sent[-3].startswith('NEWS: 2') and user.sent[-1].startswith('2.'), 'smaller index')
        await news(user, 'lista 0')
        await ok('zakres listy' in user.sent[-1], 'list bounds')
        await news(user, 'off')
        await news(user, 'read 2')
        await ok('Druga aktualizacja' in user.sent[-1], 'read possible with muted notifications')
        await ok(db.conn.execute("SELECT COUNT(*) FROM social_channel_history_v03051 WHERE channel='news'").fetchone()[0] == 3, 'no accidental posts')
        await ok(len(db.actions) == 3, 'only admins create audit events')
    finally:
        db.conn.close()
    return checks

def run():
    return asyncio.run(check())

if __name__ == '__main__':
    print(f'V28 NEWS READ: {run()} checks PASS')
