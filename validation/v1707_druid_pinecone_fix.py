# -*- coding: utf-8 -*-
"""Regression SB-5AD59274: real Character exposes character_level, never level."""
import asyncio
import sqlite3
from types import SimpleNamespace

from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin, ensure_schema


async def _run():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    checks = 0

    class DB:
        _v1700_ready = True
        def __init__(self):
            self.conn = conn
            self.inventory = {}
        def item_qty(self, aid, item):
            return self.inventory.get((aid, item), 0)
        def storage_qty(self, aid, place, item):
            return 0
        def add_item(self, aid, item, qty=1, commit=True):
            self.inventory[(aid,item)] = self.item_qty(aid,item) + qty
            if commit: self.conn.commit()

    class Druid(SessionSkyV1700Mixin):
        def __init__(self):
            self.account_id=42
            self.server=SimpleNamespace(db=DB())
            # A production Character has character_level and no attribute named level.
            self.character=SimpleNamespace(class_name='Druid', room_id='whisper_grove', character_level=1)
            self.combat_mob_key=None
            self.current_mana=1000
            self.messages=[]
        def active_class_names(self): return ('Druid',)
        async def send(self, message): self.messages.append(str(message))
        def max_hp(self): raise AttributeError('resource not initialized')

    d=Druid()
    assert not hasattr(d.character,'level')
    checks+=1
    for level, expected in ((1,2),(199,2),(200,3),(399,3),(400,4),(800,4)):
        d.character.character_level=level
        conn.execute('DELETE FROM druid_pinecones_v1702 WHERE account_id=?',(d.account_id,))
        old=d.server.db.item_qty(d.account_id,'v1702_pinecone')
        mana=d.current_mana
        await d.druid_call_v1708('squirrel')
        assert d.server.db.item_qty(d.account_id,'v1702_pinecone')==old+expected, (level,d.messages[-1])
        assert d.current_mana==mana-20
        assert 'wiewiórka' in d.messages[-1]
        checks+=3
        await d.druid_call_v1708('squirrel')
        assert 'za' in d.messages[-1] and 's' in d.messages[-1]
        assert d.server.db.item_qty(d.account_id,'v1702_pinecone')==old+expected
        checks+=2
    # After v1.70.8 the old command is a no-cost hint, not a free item generator.
    before=d.server.db.item_qty(d.account_id,'v1702_pinecone')
    await d.druid_v1700('zbierz')
    assert 'call squirrel' in d.messages[-1]
    assert d.server.db.item_qty(d.account_id,'v1702_pinecone')==before
    checks+=2
    # Squirrel summoning never steals mana in combat; no double-charge.
    conn.execute('DELETE FROM druid_pinecones_v1702 WHERE account_id=?',(d.account_id,))
    d.combat_mob_key='fight'
    mana=d.current_mana
    await d.druid_call_v1708('squirrel')
    assert d.server.db.item_qty(d.account_id,'v1702_pinecone')==before
    assert d.current_mana==mana
    checks+=2
    # Character HP fallback must also use character_level, not an absent level alias.
    d.combat_mob_key=None
    d.character.character_level=200
    assert d._v1702_summon_max_hp('wojownik')==16000
    checks+=1
    conn.close()
    return checks


def run_regression():
    return asyncio.run(_run())


if __name__ == '__main__':
    print(f'DRUID PINECONES v1.70.7: {run_regression()} checks PASS')
