# -*- coding: utf-8 -*-
"""Only a disposable localhost TCP fixture. No production modification.

Creates the normal v105 Fame boss, with its HP set to 1 AFTER adaptive scaling.
This checks kill->v115 queue, not normal combat balance or boss durability.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from storage.database import Database
from core.classes_skills import CLASSES, RACES
from world.v10500_region_index import REGIONS
from world.dynamic_content import quest_kill_targets_v0389

BOSS_ID='v10500_'+REGIONS[0][0]+'_boss_1'
BOSS_ROOM='v10500_'+REGIONS[0][0]+'_10'


def main():
    db_path=Path(os.environ['SOULBOUND_DB']).resolve()
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_V115_REAL_FAME_TEST')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
            and os.environ.get('SOULBOUND_SOUND_EVENTS')=='0'
            and os.environ.get('SOULBOUND_MAX_CLIENTS')=='5'
            and db_path.name=='five_players.sqlite'
            and db_path.parent.name.startswith('soulbound-tcp5-'))
    db=Database(str(db_path))
    try:
        for index in range(1,6):
            user=f'tcpcheck{index}'; name=f'Testtcp{index}'
            if db.account_by_name(user) is None:
                aid=db.create_account(user,'test_only_tcp_2026_password')
                db.create_character_for_master(aid,name,RACES[0],CLASSES[index-1],
                    {part:name for part in ('nom','gen','dat','acc','ins','loc','voc')})
        db.conn.commit()
    finally:
        db.conn.close()
    from player.session import Session
    original_enter=Session.enter_world
    async def enter(self):
        await original_enter(self)
        if str(self.character.name)=='Testtcp1':
            self.character.room_id=BOSS_ROOM
            self.server.db.save_character(self.character)
            matches=[mob for mob in self.server.world.mobs.values()
                if mob.alive and mob.room_id==BOSS_ROOM
                and BOSS_ID in quest_kill_targets_v0389(mob.template_id)]
            assert len(matches)==1, (BOSS_ID,len(matches))
            mob=matches[0]
            assert mob.hp>1
            mob.hp=1
            mob.v115_real_fame_test_lowhp=True
            if os.environ.get('SOULBOUND_V115_REPEAT_FAME_TEST') == '1':
                # The repeat test starts with the exact historical one-time
                # Fame credit for this NATURAL boss. This is a fixture only.
                from systems.fame_v1702 import (
                    _fame_target_identity, fame_catalog, ensure_schema,
                )
                from world.dynamic_content import MOB_TEMPLATES
                target = _fame_target_identity(mob, fame_catalog(), MOB_TEMPLATES[mob.template_id])
                assert target is not None, 'Test Fame boss has no canonical identity'
                region, boss_id = target
                conn = self.server.db.conn
                ensure_schema(conn)
                conn.execute('''INSERT OR IGNORE INTO fame_bosses_v1702
                    (account_id,region,boss_id) VALUES (?,?,?)''',
                    (self.account_id, region, boss_id))
                conn.commit()
            await self.look()
    Session.enter_world=enter
    old_adaptive=Session.apply_adaptive_mob_scale_v11330
    def adaptive(self,mob):
        result=old_adaptive(self,mob)
        if getattr(mob,'v115_real_fame_test_lowhp',False):
            mob.hp=1
        return result
    Session.apply_adaptive_mob_scale_v11330=adaptive
    print('TEST_TCP_ACCOUNTS_READY V115_REAL_FAME',flush=True)
    server.main()

if __name__=='__main__':
    main()
