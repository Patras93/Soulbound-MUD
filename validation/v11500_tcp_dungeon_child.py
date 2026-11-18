# -*- coding: utf-8 -*-
"""Guarded disposable TCP child for real v115 dungeon exploration and boss defeat.

No production game/DB/port or soundpack; changes enemy HP only in this child.
"""
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from storage.database import Database
from core.classes_skills import CLASSES,RACES
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import room_id,warden_id,WIDTH,HEIGHT,is_authored_warden_template
from data.mobs import MOB_TEMPLATES

REGION=REGIONS[0].key
BOSS_ID=warden_id(REGION)
LAST_ROOM=room_id(REGION,WIDTH-1,HEIGHT-1)
START_ROOM=room_id(REGION,0,0) if os.environ.get('SOULBOUND_V115_DUNGEON_ROUTE_TEST')=='1' else LAST_ROOM

def main():
    db_path=Path(os.environ['SOULBOUND_DB']).resolve()
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_V115_DUNGEON_TEST')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
            and os.environ.get('SOULBOUND_SOUND_EVENTS')=='0'
            and os.environ.get('SOULBOUND_MAX_CLIENTS')=='5'
            and db_path.name=='five_players.sqlite'
            and db_path.parent.name.startswith('soulbound-tcp5-'))
    db=Database(str(db_path))
    try:
        user='tcpcheck1'; name='Testtcp1'
        if db.account_by_name(user) is None:
            aid=db.create_account(user,'test_only_tcp_2026_password')
            db.create_character_for_master(aid,name,RACES[0],CLASSES[0],
                {part:name for part in ('nom','gen','dat','acc','ins','loc','voc')})
        # Route-only fixture: suppress EP level-up cascades while measuring
        # actual movement. Separate tests cover first-visit EP accounting.
        # No production account/database can enter this guarded TCP child.
        if os.environ.get('SOULBOUND_V115_DUNGEON_ROUTE_TEST') == '1':
            row=db.conn.execute('SELECT id FROM accounts WHERE username=?',(user,)).fetchone()
            aid=int(row[0])
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    db.conn.execute('INSERT OR IGNORE INTO exploration_rooms(account_id,room_id) VALUES(?,?)',
                                    (aid,room_id(REGION,x,y)))
        db.conn.commit()
    finally:db.conn.close()
    from player.session import Session
    old_enter=Session.enter_world
    async def enter(self):
        await old_enter(self)
        if str(self.character.name)=='Testtcp1':
            self.character.room_id=START_ROOM
            self.server.db.save_character(self.character)
            candidates=[m for m in self.server.world.mobs.values()
                        if m.alive and m.room_id==LAST_ROOM and is_authored_warden_template(
                            m.template_id,MOB_TEMPLATES[m.template_id],REGION)]
            assert len(candidates)==1, ('Actual scaled dungeon warden missing',len(candidates))
            candidates[0].hp=1
            candidates[0].v115_dungeon_test_lowhp=True
            await self.look()
    Session.enter_world=enter
    old_scale=Session.apply_adaptive_mob_scale_v11330
    def scale(self,mob):
        result=old_scale(self,mob)
        if getattr(mob,'v115_dungeon_test_lowhp',False):
            mob.hp=1
        return result
    Session.apply_adaptive_mob_scale_v11330=scale
    print('TEST_TCP_ACCOUNTS_READY V115_DUNGEON',flush=True)
    server.main()

if __name__=='__main__':main()
