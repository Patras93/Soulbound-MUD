# -*- coding: utf-8 -*-
"""v107: invoke the ACTUAL legacy character-selection coroutine with fake DB."""
from __future__ import annotations
import asyncio
import os


async def main():
    os.environ['SOULBOUND_V107_STAGING'] = '1'
    os.environ['SOULBOUND_V106_STAGING'] = '0'
    from world import dynamic_content as world
    from player.session_methods_v4200 import ioauthcharacter_part02 as source

    assert world.V10700_RAIDS_RETIRED['retired_raids'] == 35
    source.ROOMS = world.ROOMS
    source.MAX_CHARACTERS_PER_ACCOUNT = 8
    source.normalize_lookup_text = lambda x: str(x).strip().casefold()

    class Character:
        @classmethod
        def from_row(cls,row):
            obj = cls()
            obj.name = row['name']
            obj.room_id = row['room_id']
            return obj
    source.Character = Character

    class DummyDB:
        def __init__(self, fail=False):
            self.saved=[]
            self.fail=fail
            self.guild_calls=0
        def ensure_character_guild_from_master_v0345(self,*a):
            self.guild_calls += 1
            return {'status':'unchanged'}
        def apply_shared_wallet_to_character(self,*a):
            pass
        def save_character(self,c):
            if self.fail:raise ValueError('test: persistence error')
            self.saved.append(c.room_id)

    class DummyWorld:
        def __init__(self):self.ensured=[]
        def ensure_runtime_room(self,room_id):
            self.ensured.append(room_id)

    class Session:
        def __init__(self,room,fail=False):
            self.account_id = None
            self.master_account_id = 7
            self.server = type('Server',(),{'db':DummyDB(fail), 'world':DummyWorld()})()
            self.messages=[]
            self.rows=[{'character_account_id':12,'slot':1,'name':'Sympatyczna',
                        'room_id':room}]
            self.character=None
            self.refresh_count=0
        async def send_character_list(self):return self.rows
        async def ask(self,_prompt):return '1'
        async def send(self,msg):self.messages.append(msg)
        def refresh_guild_bonus_v0926(self):self.refresh_count += 1

    cases = (
        ('v10300_swit_raid_1','v10300_swit_09'),
        ('v10300_swit_raid_3','v10300_swit_09'),
        ('v10400_raid_12_stage_1','v10400_sztorm_11'),
        ('v10400_raid_25_stage_3','v10400_tron_13'),
        ('v10600_raid_35_stage_2','v10600_serce_23'),
        ('square','square'),
    )
    checks=0
    for room, expected in cases:
        s=Session(room)
        result=await source.choose_existing_character(s)
        assert result is True
        assert s.character.room_id==expected,(room,s.character.room_id,expected)
        assert len(s.server.db.saved)==(0 if room==expected else 1)
        assert (s.server.db.saved==[expected] if room!=expected else not s.server.db.saved)
        assert s.server.world.ensured==[],('must not regenerate retired raid',room)
        assert s.account_id==12 and s.refresh_count==1
        assert (any('wycofana' in m for m in s.messages))==(room!=expected)
        checks+=6
    s=Session('v10300_swit_raid_3',fail=True)
    try:await source.choose_existing_character(s)
    except ValueError as exc:assert 'persistence' in str(exc)
    else:raise AssertionError('save failure must block login to prevent silent loss')
    assert s.character.room_id=='v10300_swit_raid_3'
    assert not s.server.db.saved
    checks+=3
    # Critical regression from Windows PREDEPLOY 2026-11-05: extracted code
    # imports the activation helper, but its function is REBOUND into the
    # session mixin's globals by bind_legacy_method_v4200(). The real TCP
    # login path must find the helper in the destination namespace.
    from unittest.mock import patch
    from player.session_mixins.io_auth_character import SessionIOAuthCharacterMixin
    bound = SessionIOAuthCharacterMixin.choose_existing_character
    assert bound.__module__ == 'player.session_mixins.io_auth_character'
    assert callable(bound.__globals__.get('_sb107_runtime_enabled')), (
        'v107 activation missing in the real bound TCP login namespace')
    checks += 2
    with patch.dict(bound.__globals__, {
        'ROOMS': world.ROOMS, 'Character': Character,
        'MAX_CHARACTERS_PER_ACCOUNT': 8,
        'normalize_lookup_text': lambda x: str(x).strip().casefold(),
    }):
        s=Session('v10600_raid_35_stage_2')
        result=await bound(s)
        assert result is True
        assert s.character.room_id=='v10600_serce_23'
        assert s.server.db.saved==['v10600_serce_23']
        checks+=3
    print('V107 RATOWANIE POSTACI Z WYCOFANEGO RAJDU:',checks,'kontroli PASS')

if __name__=='__main__':
    asyncio.run(main())
