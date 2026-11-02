# -*- coding: utf-8 -*-
"""v105 endgame TCP private child: five genuine accounts in two new regions.

ONLY allowed inside isolated disposable localhost five-player test directory.
Never accepts account IDs, DB paths, or destinations from in-game commands.
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


def main():
    path=Path(os.environ['SOULBOUND_DB']).resolve()
    assert (os.environ.get('SOULBOUND_TCP_TEST_CHILD')=='1'
            and os.environ.get('SOULBOUND_V105_TCP_ENDGAME_TEST')=='1'
            and os.environ.get('SOULBOUND_HOST')=='127.0.0.1'
            and os.environ.get('SOULBOUND_MAX_CLIENTS')=='5'
            and path.name=='five_players.sqlite'
            and path.parent.name.startswith('soulbound-tcp5-')),'Isolated TCP testing only'
    # Two frontier regions, two NPC types, fifth at Temple for backward compatibility.
    positions=[(0,1),(19,1),(0,2),(19,2),(None,None)]
    db=Database(str(path))
    try:
        for i,(region,npc_index) in enumerate(positions,1):
            username=f'tcpcheck{i}'
            name=f'Testtcp{i}'
            account=db.account_by_name(username)
            if account is None:
                aid=db.create_account(username,'test_only_tcp_2026_password')
                cid,_=db.create_character_for_master(aid,name,RACES[0],CLASSES[i-1],
                    {part:name for part in ('nom','gen','dat','acc','ins','loc','voc')})
                if region is not None:
                    room=server.NPCS[f'v10500_{REGIONS[region][0]}_npc_{npc_index}']['room']
                    assert room in server.ROOMS
                    db.conn.execute('UPDATE characters SET room_id=? WHERE account_id=?',(room,cid))
            else:
                aid=int(account['id'])
                rows=db.characters_for_master(aid)
                assert len(rows)==1 and rows[0]['name']==name,'Fixture tampering'
        db.conn.commit()
    finally:
        db.conn.close()
    # Guarded private TCP test overrides Temple relocation in this process only.
    # Real production login and saved room behavior remain completely untouched.
    from player.session import Session
    original_enter_world=Session.enter_world
    async def private_endgame_enter_world(self):
        await original_enter_world(self)
        name=str(self.character.name)
        if name.startswith('Testtcp') and name[7:].isdigit():
            number=int(name[7:])
            if 1 <= number <= 4:
                region,npc_index=positions[number-1]
                if os.environ.get('SOULBOUND_V105_TCP_ENDGAME_BOSS_STAGE')=='1':
                    room=f'v10500_{REGIONS[region][0]}_10'
                    boss_id=f'v10500_{REGIONS[region][0]}_boss_1'
                    assert (room,boss_id) in server.MOB_SPAWNS
                else:
                    room=server.NPCS[f'v10500_{REGIONS[region][0]}_npc_{npc_index}']['room']
                self.character.room_id=room
                self.server.db.save_character(self.character)
                await self.send('TEST TCP v105: odizolowana pozycja '+room)
                await self.look()
    Session.enter_world=private_endgame_enter_world
    print('TEST_TCP_ACCOUNTS_READY',flush=True)
    server.main()

if __name__=='__main__':main()
