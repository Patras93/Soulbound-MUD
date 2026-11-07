# -*- coding: utf-8 -*-
"""Isolated TEST fixture for genuine TCP NPC turn-in, NEVER production.

Prepares already-earned kill credit because this test measures only the
claim/reward pipeline; natural boss kills are covered by a separate test.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
CASES=((26,1,1),(26,2,1),(26,3,1),(35,3,1),(26,1,0))

def main():
    dbpath=Path(os.environ['SOULBOUND_DB']).resolve()
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
        and os.environ.get('SOULBOUND_V106_STAGING')=='1'
        and os.environ.get('SOULBOUND_V106_TURNIN_TEST')=='1'
        and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
        and os.environ.get('SOULBOUND_MAX_CLIENTS')==str(len(CASES))
        and dbpath.name=='raid_turnin.sqlite'
        and dbpath.parent.name.startswith('soulbound-v106-turnin-')
        and not os.environ.get('SOULBOUND_ADMIN_ACCOUNTS'))
    import server
    from storage.database import Database
    from core.classes_skills import CLASSES,RACES
    from world.dynamic_content import NPCS,QUESTS
    rooms={}
    db=Database(str(dbpath))
    try:
        for i,(raid,stage,progress) in enumerate(CASES,1):
            account=f'turnin106{i:02d}'
            name=f'Turnin106{i:02d}'
            qid=f'v10600_raid_{raid}_quest_{stage}'
            quest=QUESTS[qid]
            npcs=[npc for npc in NPCS.values() if npc['name']==quest['giver']]
            assert len(npcs)==1 and npcs[0]['room'],(qid,npcs)
            rooms[name]=npcs[0]['room']
            aid=db.create_account(account,'test_only_tcp_2026_password')
            db.create_character_for_master(aid,name,RACES[0],CLASSES[0],
                {key:name for key in ('nom','gen','dat','acc','ins','loc','voc')})
            db.conn.execute('UPDATE characters SET soul_level=?, soul_tier=?, character_level=800, '
                            'strength=5000, dexterity=5000, constitution=5000, intelligence=5000, '
                            'willpower=5000, charisma=5000 WHERE account_id=?',
                            (34001 if raid==26 else 59001,3400 if raid==26 else 5900,aid))
            for prev in range(1,stage):
                prior=f'v10600_raid_{raid}_quest_{prev}'
                assert db.start_quest(aid,prior) is not False
                db.complete_quest(aid,prior)
            assert db.start_quest(aid,qid) is not False
            if progress:
                db.conn.execute('UPDATE quests SET progress=1 WHERE account_id=? AND quest_id=?',
                                (aid,qid))
        db.conn.commit()
    finally: db.conn.close()
    from player.session import Session
    prior_enter=Session.enter_world
    async def enter(self):
        await prior_enter(self)
        if self.character and self.character.name in rooms:
            self.character.room_id=rooms[self.character.name]
            self.server.db.save_character(self.character)
            await self.look()
    Session.enter_world=enter
    print('TEST_TCP_ACCOUNTS_READY RAJD TURNIN',len(CASES),flush=True)
    server.main()

if __name__=='__main__':main()
