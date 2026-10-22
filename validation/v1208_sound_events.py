# -*- coding: utf-8 -*-
"""Soundpack transport tests on real DB allocation and fake network/world I/O."""
import asyncio
import sqlite3
from types import SimpleNamespace


def run_regression():
    import server  # identical runtime bootstrap to other full validators
    from systems.sound_events_v1208 import install_sound_hooks_v1208
    class Session:
        async def send(self, text='', combat_detail=None, history_category=None, history_store=True):
            self.messages.append((text,{'history_store':history_store}))
        async def send_combat(self, text, detail='essential'):
            await self.send(text)
        async def mob_defeated(self, mob):
            mob.alive = False
            return 'killed'
        async def tell(self, args, *, _is_reply=False):
            target = self.server.find_character_session(args.split()[0])
            if not target or target is self or len(args.split()) < 2:
                return None
            await target.send('[TELL] '+args)
            return True
        async def enter_world(self):
            return True
        async def leave_current_character_for_selection(self):
            self.character=None
        async def close(self):
            self.closed=True
    install_sound_hooks_v1208(Session)
    from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
    from systems.sound_events_v1208 import _emit_hp_changes, _emit_defeat_hp, _event
    from player.session_mixins.social_expansion import SessionSocialExpansionMixin
    from player.session_mixins.social_base import SessionBaseSocialMixin
    n = 0
    db = DatabaseExperienceBankV2011Mixin()
    db.conn = sqlite3.connect(':memory:')
    db.create_experience_bank_schema_v2011()
    db.conn.execute('CREATE TABLE social_afk_v03051(account_id INTEGER, message TEXT)')
    assert Session._sound_hooks_installed_v1208
    assert db._sound_hooks_installed_v1208
    n += 2
    # Character experience: preserved original formula on exact deposit and repayment.
    paid = db.allocate_experience_bank_v2011(10, 550, 'character', '', 100)
    assert paid == 100
    assert db.experience_bank_rows_v2011(10) == [('character','',450)]
    assert db._sound_events_v1208[10] == ['SOUND_EVENT EXP_BANK amount=450 kind=character',
                                         'SOUND_EVENT FULL_CAP cap=100 kind=character']
    n += 3
    db._sound_events_v1208[10] = []
    paid = db.allocate_experience_bank_v2011(10, 25, 'character', '', 100)
    assert paid == 50
    assert db.experience_bank_rows_v2011(10) == [('character','',425)]
    assert db._sound_events_v1208[10] == ['SOUND_EVENT HALF_CAP cap=100 kind=character']
    n += 3
    # Stat and character balances never mingle, no notifications for read-only calls.
    assert db.allocate_experience_bank_v2011(10, 150, 'stat', 'strength', 100) == 100
    assert db.experience_bank_rows_v2011(10) == [('character','',425),('stat','strength',50)]
    before = dict((k,tuple(v)) for k,v in db._sound_events_v1208.items())
    assert db.experience_bank_rows_v2011(10) and db._sound_events_v1208[10] == list(before[10])
    n += 3
    assert db.allocate_experience_bank_v2011(10, 0, 'character', '', 100) == 0
    assert db._sound_events_v1208[10] == list(before[10])
    n += 2

    db._sound_events_v1208[10] = []
    class FakeSession(Session):
        tell = SessionSocialExpansionMixin.tell
        is_ignored_v03051 = lambda self, owner_id, other_id: False
        def __init__(self, name):
            self.character=SimpleNamespace(name=name,room_id='room')
            self.closed=False
            self.account_id=10
            self.messages=[]
            self.combat_mob_key='mob1'
            self.last_private_sender_name=None
        def mob_effective_max_hp_v11330(self,mob):
            return mob.maximum
    a=FakeSession('Ala'); b=FakeSession('Bela')
    mobs=[SimpleNamespace(key='mob1',hp=500,maximum=1000,room_id='room',alive=True,
                          engaged_by='Ala',aoe_engaged_by=None),
          SimpleNamespace(key='mob2',hp=150,maximum=200,room_id='room',alive=True,
                          engaged_by=None,aoe_engaged_by='Ala')]
    world=SimpleNamespace(room_mobs=lambda room:mobs)
    srv=SimpleNamespace(world=world,db=db,sessions=[a,b],party_sessions=lambda *args,**kwargs:[a,b],find_character_session=lambda name:next((x for x in [a,b] if x.character and x.character.name==name),None))
    a.server=b.server=srv
    async def check_hp():
        await _emit_hp_changes(a)
        assert len(a.messages)==2
        assert [line.split()[2] for line,_ in a.messages]==['id=mob1','id=mob2']
        await _emit_hp_changes(a)
        assert len(a.messages)==2
        mobs[1].hp=90
        await _emit_hp_changes(a)
        assert len(a.messages)==3 and 'current=90' in a.messages[-1][0]
        mobs[0].hp=0
        mobs[0].alive=False
        await _emit_defeat_hp(a,mobs[0])
        assert 'MOB_HP id=mob1 current=0 max=1000' in a.messages[-1][0]
        assert b.messages[-1][0]==a.messages[-1][0]
        await _emit_defeat_hp(a,mobs[0])
        assert len(a.messages)==4 and len(b.messages)==4
        # All transport events suppress history, retaining normal game messages.
        assert all(opts.get('history_store') is False for _,opts in a.messages+b.messages)
    asyncio.run(check_hp())
    n += 7
    async def check_messages():
        a.messages.clear(); b.messages.clear()
        await a.tell('Bela witaj')
        assert b.messages[-1][0]=='SOUND_EVENT TELL_RECEIVED from=Ala'
        await b.tell('Ala pytanie')
        assert a.last_private_sender_name=='Bela'
        await SessionBaseSocialMixin.reply_private_v0928(a, 'odpowiedz')
        assert b.messages[-1][0]=='SOUND_EVENT REPLY_RECEIVED from=Ala'
        assert any('REPLY: odpowiedź wysłana do Bela.' in line for line,_ in a.messages)
        old_count = len(b.messages)
        await a.tell('NieMa brak')
        assert len(b.messages)==old_count
        b.character.room_id='other'
        await a.enter_world()
        assert b.messages[-1][0]=='SOUND_EVENT PLAYER_LOGIN name=Ala'
        await a.leave_current_character_for_selection()
        assert b.messages[-1][0]=='SOUND_EVENT PLAYER_LOGOUT name=Ala'
        await a.close()
        assert b.messages[-1][0]=='SOUND_EVENT PLAYER_LOGOUT name=Ala'
    asyncio.run(check_messages())
    n += 6
    # A read-only command never creates new audio, and drained rewards are not replayed.
    async def check_informational_commands():
        b.character.room_id='room'
        db._sound_events_v1208[10] = []
        a.account_id=10
        a.messages.clear()
        assert db.allocate_experience_bank_v2011(10, 300, 'character', '', 100)==100
        await a.send('EXP przyznane')
        assert a.messages[0][0]=='SOUND_EVENT EXP_BANK amount=200 kind=character'
        assert a.messages[1][0]=='SOUND_EVENT FULL_CAP cap=100 kind=character'
        assert a.messages[2][0]=='EXP przyznane'
        a.messages.clear()
        for cmd in ('look','score','expbank'):
            await a.send(cmd, history_store=False)
        assert [line for line,_ in a.messages]==['look','score','expbank']
        assert not db._sound_events_v1208.get(10)
    asyncio.run(check_informational_commands())
    n += 5
    assert '\n' not in _event('PLAYER_LOGIN',name='a\nb')
    assert _event('REPLY_RECEIVED',**{'from':'Bela'})=='SOUND_EVENT REPLY_RECEIVED from=Bela'
    n += 2
    db.conn.close()
    return n


if __name__=='__main__':
    print(f'V12.00.8 SOUNDPACK: {run_regression()} checks PASS')
