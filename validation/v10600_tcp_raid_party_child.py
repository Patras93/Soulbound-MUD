# -*- coding: utf-8 -*-
"""Odizolowany proces prawdziwego serwera TCP dla rajdowej drużyny v106.

Nie wolno używać z bazą ani portem produkcyjnym. Bez trwałych danych graczy.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    number=int(os.environ.get('SOULBOUND_V106_RAID_PARTY_COUNT','0'))
    raid=int(os.environ.get('SOULBOUND_V106_RAID_PARTY_RAID','0'))
    dbpath=Path(os.environ['SOULBOUND_DB']).resolve()
    assert number in (3,6) and raid in (26,35)
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_V106_STAGING')=='1'
            and os.environ.get('SOULBOUND_V106_RAID_PARTY_TEST')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
            and os.environ.get('SOULBOUND_MAX_CLIENTS')==str(number)
            and dbpath.name=='raid_party.sqlite'
            and dbpath.parent.name.startswith('soulbound-v106-raid-party-')
            and os.environ.get('SOULBOUND_ADMIN_ACCOUNTS')=='raid10601')
    import server
    from storage.database import Database
    from core.classes_skills import CLASSES,RACES
    from world.dynamic_content import ROOMS,QUESTS
    room_id=f'v10600_raid_{raid}_stage_1'
    quest_id=f'v10600_raid_{raid}_quest_1'
    assert room_id in ROOMS and quest_id in QUESTS
    db=Database(str(dbpath))
    try:
        for i in range(1,number+1):
            username=f'raid106{i:02d}'
            name=f'Raid106{i:02d}'
            assert db.account_by_name(username) is None, 'test DB must be empty'
            aid=db.create_account(username,'test_only_tcp_2026_password')
            db.create_character_for_master(aid,name,RACES[0],CLASSES[(i-1)%len(CLASSES)],
                {k:name for k in ('nom','gen','dat','acc','ins','loc','voc')})
            # Disposable synthetic endgame state. Without stage-appropriate
            # Soul Level the combat scaler sees a level-1 newbie, which is not
            # a valid raid 26/35 combat eligibility test.
            db.conn.execute('UPDATE characters SET soul_level=?, character_level=800 WHERE account_id=?',
                (34001 if raid==26 else 59001,aid))
            if i==1:
                # 8 base + 500/25 = 28 slots. Only on temporary test SQLite.
                db.conn.execute('UPDATE characters SET charisma=500 WHERE account_id=?',(aid,))
            assert db.start_quest(aid,quest_id) is not False,username
        db.conn.commit()
    finally:db.conn.close()
    from player.session import Session
    prior=Session.enter_world
    async def enter(self):
        await prior(self)
        if str(self.character.name).startswith('Raid106'):
            self.character.room_id=room_id
            self.server.db.save_character(self.character)
            await self.look()
    Session.enter_world=enter
    # Instrument ONLY this temporary child: directly enter the real boss
    # engagement before the admin's test strike. The real victory/reward
    # methods are untouched, but this is not a natural combat measurement.
    original_strike=Session.admin_unique_strike_v35005
    async def strike(self,args=''):
        if (self.account_id and str(self.character.name)=='Raid10601'
                and str(args).strip().startswith('wyrok')
                and self.character.room_id==room_id):
            import time
            found=[m for m in self.server.world.mobs.values()
                if m.room_id==room_id and m.alive and
                str(m.template_id).split('__')[0]==f'v10600_raid_{raid}_boss_1']
            assert len(found)==1,('niejednoznaczny cel w teście',len(found))
            mob=found[0]
            self.combat_mob_key=mob.key
            mob.engaged_by=self.character.name
            mob.engaged_at=time.monotonic()
        return await original_strike(self,args)
    Session.admin_unique_strike_v35005=strike
    print('TEST_TCP_ACCOUNTS_READY RAJD PARTY V106',number,raid,flush=True)
    server.main()

if __name__=='__main__':main()
