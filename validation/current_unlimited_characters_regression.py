# -*- coding: utf-8 -*-
"""Stała regresja nieograniczonej liczby postaci. Izolowana baza."""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.bootstrap_economy_professions import MAX_CHARACTERS_PER_ACCOUNT
from core.classes_skills import CLASSES, RACES
from player.session_mixins.io_auth_character import SessionIOAuthCharacterMixin
from storage.database import Database


def run_regression():
    assert MAX_CHARACTERS_PER_ACCOUNT is None, 'limit w konfiguracji nadal jest aktywny'
    checks = 1
    with tempfile.TemporaryDirectory(prefix='soulbound_current_unlimited_') as td:
        path = Path(td) / 'only_test.sqlite'
        db = Database(str(path))
        owner = db.create_account('UnlimitedTester', 'test-very-long-password')
        ids = {}
        for i in range(1, 26):
            name = f'Unlimit{i:02d}'
            cases = {key: name for key in ('nom','gen','dat','acc','ins','loc','voc')}
            character_id, slot = db.create_character_for_master(owner,name,RACES[0],CLASSES[0],cases)
            assert slot == i, (i,slot)
            assert db.character_count_for_master(owner) == i
            ids[i] = character_id
            checks += 2
        assert len(db.characters_for_master(owner)) == 25
        checks += 1
        # Usuniecie jednego alta nie moze usunac pozostalych ani konta logowania.
        result = db.delete_character_for_master(owner, ids[5])
        assert result and result['slot']==5
        assert db.account_by_name('UnlimitedTester') is not None
        checks += 2
        replacement = 'NowaPiatka'
        cases = {key: replacement for key in ('nom','gen','dat','acc','ins','loc','voc')}
        new_id, new_slot = db.create_character_for_master(owner,replacement,RACES[0],CLASSES[0],cases)
        assert new_slot == 5
        assert new_id not in ids.values()
        checks += 2
        assert len(db.characters_for_master(owner)) == 25
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        checks += 2
        db.conn.close()
        db = Database(str(path))
        rows = db.characters_for_master(owner)
        assert len(rows) == 25 and rows[-1]['slot']==25
        assert rows[4]['name']=='NowaPiatka'
        assert db.character_count_for_master(owner)==25
        assert db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        checks += 4
        # Faktyczny ekran postaci nie moze twierdzic, ze limit jest 14.
        class SampleSession(SessionIOAuthCharacterMixin):
            def __init__(self):
                self.master_account_id = owner
                self.server = SimpleNamespace(db=db)
                self.messages=[]
            async def send(self, message, *args, **kwargs):
                self.messages.append(str(message))
        sess = SampleSession()
        listed = asyncio.run(sess.send_character_list())
        assert len(listed) == 25 and listed[-1]['slot']==25
        assert any('POSTACIE NA KONCIE: 25' in m for m in sess.messages)
        assert not any('25/14' in m or 'limit 14' in m for m in sess.messages)
        checks += 3
        # Wybór 25. postaci rzeczywista metoda sesji (nie sama lista SQL).
        sess = SampleSession()
        sess.server.world = SimpleNamespace(ensure_runtime_room=lambda _room: None)
        async def answer_slot(_prompt):
            return '25'
        sess.ask = answer_slot
        sess.refresh_guild_bonus_v0926 = lambda: None
        selected = asyncio.run(sess.choose_existing_character())
        assert selected is True and sess.character.name == 'Unlimit25'
        assert sess.account_id == ids[25]
        assert any('Slot 25.' in message for message in sess.messages)
        checks += 3
        # Opcja tworzenia nie moze byc blokowana przez liczbe 25 postaci.
        creator_session = SampleSession()
        async def create_answer(_prompt):
            return '2'
        async def creator():
            return 'creator_allowed'
        creator_session.ask = create_answer
        creator_session.character_creator = creator
        creator_session.is_admin = lambda: False
        assert asyncio.run(creator_session.character_selection_flow()) == 'creator_allowed'
        assert not any('Osiągnięto limit' in message for message in creator_session.messages)
        checks += 2
        db.conn.close()
    print(f'UNLIMITED CHARACTERS CURRENT: {checks}/{checks} PASS (25 postaci, usuniecie, slot, restart, menu)')
    return checks

if __name__=='__main__':
    run_regression()
