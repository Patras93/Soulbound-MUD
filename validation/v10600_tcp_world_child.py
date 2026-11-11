# -*- coding: utf-8 -*-
"""ONLY private disposable v106 localhost TCP test server, never production."""
from __future__ import annotations
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    dbpath=Path(os.environ['SOULBOUND_DB']).resolve()
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_V106_STAGING')=='1'
            and os.environ.get('SOULBOUND_V106_TCP_WORLD_TEST')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
            and os.environ.get('SOULBOUND_MAX_CLIENTS')=='5'
            and dbpath.name=='five_players.sqlite'
            and dbpath.parent.name.startswith('soulbound-tcp5-v106-'))
    import server
    from storage.database import Database
    from core.classes_skills import CLASSES,RACES
    from world.dynamic_content import NPCS,QUESTS,ROOMS
    from world.v10600_region_index import REGIONS
    assert 'v10600_przedmurze_story_01' in QUESTS
    assert 'soul_tier_6000_trial' in QUESTS
    locations={}
    for index in (0,1,29):
        slug=REGIONS[index][0]
        for npc_no in (1,2,4):
            npc=f'v10600_{slug}_npc_{npc_no}'
            assert NPCS[npc]['room'] in ROOMS
            locations[(index,npc_no)]=NPCS[npc]['room']
    db=Database(str(dbpath))
    try:
        for i in range(1,6):
            user=f'tcp106{i}';name=f'Test106{i}'
            if db.account_by_name(user) is None:
                aid=db.create_account(user,'test_only_tcp_2026_password')
                db.create_character_for_master(aid,name,RACES[0],CLASSES[i-1],
                    {k:name for k in ('nom','gen','dat','acc','ins','loc','voc')})
        db.conn.commit()
    finally:db.conn.close()
    from player.session import Session
    prior=Session.enter_world
    async def enter(self):
        await prior(self)
        placement={
            'Test1061':locations[(0,1)],
            'Test1062':locations[(0,2)],
            'Test1063':locations[(1,1)],
            'Test1064':locations[(1,4)],
            'Test1065':locations[(29,1)],
        }
        room=placement.get(str(self.character.name))
        if room:
            self.character.room_id=room
            self.server.db.save_character(self.character)
            await self.look()
    Session.enter_world=enter
    print('TEST_TCP_ACCOUNTS_READY V106_STAGING',flush=True)
    server.main()

if __name__=='__main__':main()
