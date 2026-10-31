# -*- coding: utf-8 -*-
"""Real infinite Crypt bosses and Tier 81 unlocking on private SQLite."""
from __future__ import annotations
import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace


def run():
    import server
    from storage.database import Database
    from player.character import Character
    from player.session import Session
    from core.classes_skills import CLASSES, RACES
    from core.progression_600 import SOUL_TIER_THRESHOLDS
    from systems.content_registry import QUESTS, MOB_TEMPLATES, ROOMS
    # The world runtime binds historical native definitions to their globals.
    from world.dynamic_content import create_infinite_crypt_floor_definition
    checks=0
    def check(value,label):
        nonlocal checks
        if not value: raise AssertionError(label)
        checks+=1
    for floor in (810,1000,2000,5000):
        for mythic in (False, True):
            room_id,spawns=create_infinite_crypt_floor_definition(floor, mythic=mythic)
            mid=f'{"mythic_" if mythic else ""}crypt_boss_{floor}'
            label=f'{"mythic " if mythic else ""}floor {floor}'
            check(room_id in ROOMS,f'room {label}')
            check(mid in MOB_TEMPLATES,f'mob {label}')
            check((room_id,mid) in spawns,f'boss spawn {label}')
            check(all(item in server.ITEMS for item in MOB_TEMPLATES[mid].get('corpse_equipment_pool',())),f'EQ for {label}')
            if not mythic:
                check(MOB_TEMPLATES[mid].get('quest_target')==mid,f'kill target {label}')
                tier=floor//10
                q=QUESTS[f'soul_tier_{tier:02d}_trial']
                check(q['target']==mid and q['unlocks_soul_tier']==tier,f'trial quest {tier}')
    async def trial():
        nonlocal checks
        with tempfile.TemporaryDirectory(prefix='sb-103-soul-unlock-') as td:
            db=Database(str(Path(td)/'soul.sqlite'))
            aid=db.create_account('era103_soul_tester','pass_to_database')
            db.create_character(aid,'SoulEra103',RACES[0],CLASSES[0],{
                'nom':'Tester','gen':'Testera','dat':'Testerowi','acc':'Testera',
                'ins':'Testerem','loc':'Testerze','voc':'Testerze'})
            c=Character.from_row(db.character_for_account(aid))
            c.soul_tier=80
            c.soul_level=810
            c.soul_xp=2468
            db.save_character(c)
            sess=Session.__new__(Session)
            sess.character=c;sess.account_id=aid
            messages=[];broadcasts=[]
            async def send(s,*a,**k):messages.append(str(s))
            async def broadcast(*a,**k):broadcasts.append((a,k))
            sess.send=send
            sess.server=SimpleNamespace(db=db,broadcast_room=broadcast)
            check(SOUL_TIER_THRESHOLDS[80]==810,'Tier 81 Soul Level')
            await sess.unlock()
            check(c.soul_tier==80,'tier 81 must require completed trial')
            check(any('Prób' in m or 'zadania' in m for m in messages),'player warned about trial')
            qid='soul_tier_81_trial'
            db.start_quest(aid,qid)
            db.increment_quest(aid,'crypt_boss_810')
            check(db.quest(aid,qid)['progress']==1,'real crypt boss kill credit')
            db.complete_quest(aid,qid)
            messages.clear()
            await sess.unlock()
            check(c.soul_tier==81,'tier 81 unlocked')
            check(Character.from_row(db.character_for_account(aid)).soul_tier==81,'tier 81 persisted')
            check(c.soul_xp==2468,'banked Soul XP unchanged')
            check(any('Odblokowano Soul Tier 81' in m for m in messages),'NVDA unlock notice')
            check(len(broadcasts)==1,'broadcast once')
            await sess.unlock()
            check(c.soul_tier==81,'tier 82 blocked until level 820')
            check(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
            db.conn.close()
    asyncio.run(trial())
    return checks

if __name__=='__main__':
    print(f'ERA 103 SOUL UNLOCK AND CRYPT REAL SQLITE: {run()} PASS',flush=True)
