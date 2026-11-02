# -*- coding: utf-8 -*-
"""Isolated private TCP reward test fixture; NEVER used by production server.

Only localhost and disposable SQLite in specially named temp directory.
A test-only low-HP/low-offense override separates kill/quest/reward integration
from normal high-tier time-to-kill/balance, which is NOT measured here.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from storage.database import Database
from core.classes_skills import CLASSES,RACES
from world.v10500_region_index import REGIONS
from world.dynamic_content import quest_kill_targets_v0389


def main():
    dbpath=Path(os.environ['SOULBOUND_DB']).resolve()
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_V105_BOSS_REWARDS_TEST')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
            and os.environ.get('SOULBOUND_MAX_CLIENTS')=='5'
            and dbpath.name=='five_players.sqlite'
            and dbpath.parent.name.startswith('soulbound-tcp5-'))
    stage=os.environ.get('SOULBOUND_V105_BOSS_REWARDS_STAGE')
    assert stage in {'offer','battle','reward'}
    db=Database(str(dbpath))
    try:
        for i in range(1,6):
            user=f'tcpcheck{i}'; name=f'Testtcp{i}'
            account=db.account_by_name(user)
            if account is None:
                aid=db.create_account(user,'test_only_tcp_2026_password')
                db.create_character_for_master(aid,name,RACES[0],CLASSES[i-1],
                    {part:name for part in ('nom','gen','dat','acc','ins','loc','voc')})
        db.conn.commit()
    finally: db.conn.close()
    from player.session import Session
    old_enter=Session.enter_world
    async def enter(self):
        await old_enter(self)
        name=str(self.character.name)
        if name in {'Testtcp3','Testtcp4'}:
            index=0 if name=='Testtcp3' else 19
            slug=REGIONS[index][0]
            if stage=='battle': room=f'v10500_{slug}_10'
            else:room=server.NPCS[f'v10500_{slug}_npc_2']['room']
            self.character.room_id=room
            self.server.db.save_character(self.character)
            if stage=='battle':
                mid=f'v10500_{slug}_boss_1'
                matches=[m for m in self.server.world.mobs.values()
                         if m.alive and m.room_id==room and mid in quest_kill_targets_v0389(m.template_id)]
                assert len(matches)==1,(mid,len(matches))
                m=matches[0]
                assert m.hp>1
                # Narrow fixture changes only current combatant, not catalog,
                # persistent character, any real game global or another mob.
                m.hp=1
                setattr(m,'v105_test_lowhp',True)
            await self.look()
    Session.enter_world=enter
    old_adaptive=Session.apply_adaptive_mob_scale_v11330
    def test_adaptive(self,mob):
        result=old_adaptive(self,mob)
        if getattr(mob,'v105_test_lowhp',False):
            mob.hp=1   # AFTER normal adaptation, not before scaling.
            mob.adaptive_max_hp_v11330=max(1,int(getattr(mob,'adaptive_max_hp_v11330',1) or 1))
        return result
    Session.apply_adaptive_mob_scale_v11330=test_adaptive
    print('TEST_TCP_ACCOUNTS_READY BOSS_'+stage,flush=True)
    server.main()

if __name__=='__main__':main()
