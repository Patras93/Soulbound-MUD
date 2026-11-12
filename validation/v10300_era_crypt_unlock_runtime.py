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
    from systems.content_registry import QUESTS, MOB_TEMPLATES
    from data.rooms import ROOMS
    # The live engine resolves the *final* crypt builder through its explicit
    # gameplay rule registry. Older source-module imports bypass that builder.
    from core.runtime_rules import get_rule
    create_infinite_crypt_floor_definition = get_rule('create_infinite_crypt_floor_definition')
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
        # Historical test pre-v105 assumed that every new Tier needs its
        # own quest. The v105 contract requires trials ONLY for Tier 10n.
        # Check both paths against the real database and bound Session.unlock.
        with tempfile.TemporaryDirectory(prefix='sb-103-soul-unlock-') as td:
            db=Database(str(Path(td)/'soul.sqlite'))
            try:
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
                # Tier 81 is a normal tier; having a historical quest ID in
                # the catalog must not require completing that quest.
                check(QUESTS['soul_tier_81_trial']['unlocks_soul_tier']==81,
                      'historical Tier 81 quest remains registered')
                await sess.unlock()
                check(c.soul_tier==81,'Tier 81 unlocked at Soul Level 810 without trial')
                check(Character.from_row(db.character_for_account(aid)).soul_tier==81,
                      'Tier 81 persisted')
                check(any('Odblokowano Soul Tier 81' in m for m in messages),
                      'NVDA Tier 81 unlock notice')
                check(len(broadcasts)==1,'Tier 81 broadcast once')
                check(c.soul_xp==2468,'Soul XP bank unchanged at Tier 81')
                messages.clear()
                await sess.unlock()
                check(c.soul_tier==81,'Tier 82 blocked until Soul Level 820')
                check(any('Soul Level 820' in m for m in messages),
                      'Tier 82 Soul Level requirement announced')

                # Tier 90 is a mandatory milestone. A REAL completed quest
                # must be required, and the boss event must count via SQLite.
                c.soul_tier=89
                c.soul_level=900
                db.save_character(c)
                messages.clear()
                check(SOUL_TIER_THRESHOLDS[89]==900,'Tier 90 Soul Level')
                await sess.unlock()
                check(c.soul_tier==89,'Tier 90 requires completed trial')
                check(any('zadania' in m or 'Prób' in m for m in messages),
                      'player warned about Tier 90 trial')
                qid='soul_tier_90_trial'
                check(QUESTS[qid]['target']=='crypt_boss_900',
                      'Tier 90 real crypt boss target')
                db.start_quest(aid,qid)
                db.increment_quest(aid,'crypt_boss_900')
                check(db.quest(aid,qid)['progress']==1,'real Tier 90 boss kill credit')
                db.complete_quest(aid,qid)
                messages.clear()
                await sess.unlock()
                check(c.soul_tier==90,'Tier 90 unlocked after completed trial')
                check(Character.from_row(db.character_for_account(aid)).soul_tier==90,
                      'Tier 90 persisted')
                check(c.soul_xp==2468,'Soul XP bank unchanged at Tier 90')
                check(any('Odblokowano Soul Tier 90' in m for m in messages),
                      'NVDA Tier 90 unlock notice')
                check(len(broadcasts)==2,'exactly one broadcast per unlocked Tier')
                await sess.unlock()
                check(c.soul_tier==90,'Tier 91 blocked until Soul Level 910')
                check(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok',
                      'SQLite integrity')
            finally:
                # Windows requires every SQLite handle to be closed BEFORE
                # TemporaryDirectory can unlink the database file.
                db.conn.close()
    asyncio.run(trial())
    return checks

if __name__=='__main__':
    print(f'ERA 103 SOUL UNLOCK AND CRYPT REAL SQLITE: {run()} PASS',flush=True)
