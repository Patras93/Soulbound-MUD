# -*- coding: utf-8 -*-
"""v12.00.1 chat `xp text` must coexist with legacy bare XP status."""
import asyncio
import sqlite3
from types import SimpleNamespace


def run_regression():
    import server  # bootstrap legacy session imports
    from player.session_mixins.social_expansion import SessionSocialExpansionMixin
    from player.session_mixins.command_registry import COMMAND_REGISTRY, COMMAND_TEXT
    from player.session_mixins.command_registry import resolve_session_command
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.executescript('''
      CREATE TABLE social_channel_settings_v03051(account_id INTEGER NOT NULL, channel TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(account_id,channel));
      CREATE TABLE social_channel_history_v03051(id INTEGER PRIMARY KEY AUTOINCREMENT,channel TEXT NOT NULL,sender_account_id INTEGER NOT NULL,sender_name TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    ''')
    server_fake=SimpleNamespace(sessions=[],db=SimpleNamespace(conn=conn))
    class MockSession(SessionSocialExpansionMixin):
        def __init__(self, aid, name):
            self.account_id=aid
            self.character=SimpleNamespace(name=name)
            self.server=server_fake
            self.closed=False
            self.received=[]
            self.status_calls=0
            self.muted=set()
        async def send(self, text, **kwargs):
            self.received.append((text,kwargs.get('history_category')))
        async def show_character_xp(self):
            self.status_calls+=1
            await self.send('EXP postaci: test status')
        def is_ignored_v03051(self, owner_id, other_id):
            return other_id in self.muted
    sender=MockSession(1,'Wojownik')
    friend=MockSession(2,'Kaplan')
    outside=MockSession(3,'Mag')
    outside.muted.add(1)
    server_fake.sessions=[sender,friend,outside]
    checks=0
    assert resolve_session_command('xp', 'Czesc druzyno')=='xp'
    assert COMMAND_REGISTRY['xp'][0]=='xp_chat_v1201' and COMMAND_REGISTRY['xp'][1]==(COMMAND_TEXT,)
    checks+=2
    async def scenario():
        nonlocal checks
        await sender.xp_chat_v1201('')
        assert sender.status_calls==1 and len(friend.received)==0
        checks+=1
        await sender.xp_chat_v1201('Kto idzie na Krypte?')
        assert friend.received==[('[XP] Wojownik: Kto idzie na Krypte?','chat')]
        assert sender.received[-1]==('[XP] Wojownik: Kto idzie na Krypte?','chat')
        assert not outside.received
        checks+=3
        rows=conn.execute("SELECT channel,sender_name,message FROM social_channel_history_v03051").fetchall()
        assert len(rows)==1 and tuple(rows[0])==('xp','Wojownik','Kto idzie na Krypte?')
        checks+=1
        await friend.show_channels_v03050()
        assert 'xp=on' in friend.received[-1][0]
        checks+=1
        await friend.show_channel_history_v03051('xp')
        assert any('Kto idzie na Krypte?' in text for text,cat in friend.received)
        checks+=1
        await friend.channel_broadcast_v03050('xp','off')
        assert not friend.channel_enabled_v03051('xp')
        checks+=1
        sender._channel_last_v03051=0.0
        await sender.xp_chat_v1201('Wyprawa od 80 poziomu.')
        assert sum(1 for text,cat in friend.received if text.startswith('[XP] '))==1
        checks+=1
        await friend.channel_broadcast_v03050('xp','on')
        assert friend.channel_enabled_v03051('xp')
        checks+=1
        await friend.show_channel_history_v03051('trade')
        assert friend.received[-1][0]=='Brak wiadomości.'
        checks+=1
    asyncio.run(scenario())
    conn.close()
    return checks

if __name__=='__main__':
    print('XP CHAT v12.00.1:',run_regression(),'checks PASS')
