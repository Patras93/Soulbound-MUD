# -*- coding: utf-8 -*-
"""Real Session NPC quest offers and acceptance on isolated SQLite.

No live player DB, no network. Checks independent story / class / raid chains,
numbered NVDA offers, next stages and permissions of legacy NPCs.
"""
from __future__ import annotations
import asyncio
import tempfile
from pathlib import Path
from types import SimpleNamespace


def run():
    import server  # install real world registries
    from core.classes_skills import CLASSES, RACES
    from storage.database import Database
    from player.character import Character
    from player.session import Session
    from systems.content_registry import NPCS, QUESTS
    from world.v10300_era_bez_granic import ERAS

    total = 0
    def ck(condition, label):
        nonlocal total
        if not condition:
            raise AssertionError(label)
        total += 1

    async def inner():
        with tempfile.TemporaryDirectory(prefix='sb103-npc-real-') as td:
            db = Database(str(Path(td) / 'npc.sqlite'))
            account = db.create_account('EraNpcStage5', 'private_test_pass')
            db.create_character(account, 'EraNpcTester', RACES[0], CLASSES[0], {
                'nom': 'Test', 'gen': 'Testu', 'dat': 'Testowi',
                'acc': 'Test', 'ins': 'Testem', 'loc': 'Teście', 'voc': 'Teście'})
            session = Session.__new__(Session)
            events = []
            async def publish(event): events.append(event)
            session.server = SimpleNamespace(
                db=db, events=SimpleNamespace(publish=publish),
                party_key_for_account=lambda account_id: None)
            session.account_id = account
            session.character = Character.from_row(db.character_for_account(account))
            session.combat_mob_key = None
            session.quest_list_context = None
            texts = []
            async def send(msg, *args, **kwargs):
                texts.append(str(msg))
            session.send = send
            # Leave all real NPC/quest dispatch and SQLite intact; only isolate
            # EXP awards, which were already checked separately in stage 4.
            async def xp_sink(*args, **kwargs): return []
            async def stat_sink(*args, **kwargs): return []
            async def item_sink(*args, **kwargs): return None
            session.grant_profession_reward_xp = xp_sink
            session.grant_tool_reward_xp = xp_sink
            session.grant_combat_quest_stat_xp = stat_sink
            session.grant_class_xp = xp_sink
            session.grant_soul_xp = xp_sink
            session.add_character_xp_with_event = lambda *a, **k: []
            session.record_item_collection = item_sink

            for slug, *rest in ERAS:
                prefix = 'v10300_' + slug
                master_id = prefix + '_npc_2'
                master = NPCS[master_id]
                session.character.room_id = master['room']
                classes_here = [QUESTS[qid]['required_class']
                    for qid in master['specialist_quests'] if '_class_' in qid]
                for klass in dict.fromkeys(classes_here):
                    session.character.class_name = klass
                    ids = session.quest_ids_for_npc(master_id, master)
                    ck(prefix+'_raid_quest_1' in ids, f'raid hidden {slug}/{klass}: {ids}')
                    ck(any('_class_' in q and QUESTS[q]['required_class']==klass for q in ids),
                       f'own class hidden {slug}/{klass}: {ids}')
                    ck(all(QUESTS[q].get('required_class') in (None, klass) for q in ids),
                       f'other class offered {slug}/{klass}: {ids}')
                    ck(len([q for q in ids if '_story_' in q])<=1, f'long story {slug}')
                    ck(len(ids)<=3, f'NVDA too many offers {slug}: {ids}')
                    texts.clear()
                    await session.show_npc_quest_offers(master_id,master)
                    ck(bool(texts) and len(texts)<=5 and texts[0].startswith('LISTA ZADAŃ'),
                       f'bad NPC dialogue {slug}/{klass}: {texts}')
                    ck(session.quest_list_context['quest_ids']==ids, f'numbering {slug}/{klass}')

                # Confirm genuine numbered quest acceptance through the Session
                # handler, not by writing quest rows by hand.
                session.character.class_name = classes_here[0]
                raid1 = prefix + '_raid_quest_1'
                texts.clear()
                await session.quests('list')
                ids = session.quest_list_context['quest_ids']
                ck(raid1 in ids, f'raid not listed by /quest list {slug}')
                await session.quests('accept ' + str(ids.index(raid1)+1))
                ck(db.quest(account,raid1)['status']=='active', f'numbered quest accept failed {slug}: {texts[-8:]}')
                ids = session.quest_ids_for_npc(master_id,master)
                ck(raid1 in ids, f'active raid disappeared {slug}')
                db.increment_quest(account, prefix+'_raid_boss_1')
                ck(db.quest(account,raid1)['progress']==1, f'raid boss not credited {slug}')
                events.clear()
                texts.clear()
                await session.quests('oddaj ' + str(ids.index(raid1)+1))
                ck(db.quest(account,raid1)['status']=='completed',f'numbered NPC raid turn-in failed {slug}: {texts[-8:]}')
                ck(len(events)==1, f'NPC raid completion event {slug}')
                ids = session.quest_ids_for_npc(master_id,master)
                ck(prefix+'_raid_quest_2' in ids, f'next raid not offered {slug}: {ids}')
                ck(raid1 not in ids, f'old raid offered {slug}')

                # Class quests must remain separately available even after a
                # raid, and must never cross class boundaries.
                own = [q for q in ids if '_class_' in q]
                ck(len(own)==1, f'no own class quest {slug}: {ids}')
                ck(await session.accept_quest_id(own[0],npc_id=master_id), f'own class not accepted {slug}')
                db.set_quest_progress(account,own[0],QUESTS[own[0]]['needed'])
                db.complete_quest(account,own[0])
                ids = session.quest_ids_for_npc(master_id,master)
                ck(len([q for q in ids if '_class_' in q])==1 and
                    [q for q in ids if '_class_' in q][0]!=own[0], f'class stage2 hidden {slug}')

                # NPC3 offers all independent profession contracts, even when
                # story chapter 9 is still locked behind NPC2's story quests.
                npc3_id = prefix+'_npc_3'
                npc3 = NPCS[npc3_id]
                session.character.room_id = npc3['room']
                professions = [q for q in npc3['specialist_quests'] if '_prof_' in q]
                offers = session.quest_ids_for_npc(npc3_id,npc3)
                ck(len(professions)==14, f'profession count {slug}')
                ck(set(professions).issubset(offers), f'professions hidden {slug}')
                ck(not any('_story_' in q for q in offers), f'locked story leaked {slug}')
                ck(len(offers)<=14, f'NVDA profession list too long {slug}')

            # v105 replaces all individual Soul quests with mandatory milestones.
            # Keep the v104 checks intact when this historical test runs on v104.
            from core.progression_600 import SOUL_MAX_TIER
            is_v105 = SOUL_MAX_TIER >= 3000
            elor = NPCS['priest_elor']
            session.character.room_id = elor['room']
            if is_v105:
                for tier in (1, 9, 10, 79, 80, 81, 250, 499, 500, 1000, 2990, 2999, 3000, 10000):
                    session.character.soul_tier=tier
                    offered=session.quest_ids_for_npc('priest_elor',elor)
                    got=[QUESTS[q]['unlocks_soul_tier'] for q in offered if 'unlocks_soul_tier' in QUESTS[q]]
                    start=((tier//10)+1)*10
                    expected=list(range(start, min(3001,start+100),10))
                    ck(got==expected, f'Elor v105 Tier {tier}: expected {expected}, got {got}')
                    ck(len(offered)<=11, f'Elor NVDA too many quests Tier {tier}: {len(offered)}')
                session.character.soul_tier=9
                for requested in (10,81,501,801,991,1000,1001,1501,2991,3000):
                    texts.clear()
                    await session.show_quest_npc_list(f'Elor {requested}')
                    got=[QUESTS[q]['unlocks_soul_tier'] for q in session.quest_list_context['quest_ids']]
                    first=((requested+9)//10)*10
                    expected=list(range(first,min(3001,first+100),10))
                    ck(got==expected,f'Elor page v105 {requested}: {got} vs {expected}')
                    ck(any(f'Tiery {first}–{expected[-1]}' in line for line in texts),
                       f'Elor page {requested} range incorrect: {texts[:2]}')
                    ck(len(texts)<=14,f'Elor page {requested} too long for NVDA')
                texts.clear()
                await session.show_quest_npc_list('Elor 3001')
                ck(any('Podaj Tier' in line for line in texts),'v105 invalid tier accepted')
                from systems.content_registry import HELP_TOPICS,HELP_TOPIC_ALIASES
                ck('3000' in ' '.join(HELP_TOPICS['dusza']) and 'co 10 Tierów' in ' '.join(HELP_TOPICS['dusza']), 'v105 help dusza stale')
                ck(HELP_TOPIC_ALIASES.get('proby duszy')=='proby_duszy','help missing alias')
                ck('quest list Elor 1001' in ' '.join(HELP_TOPICS['proby_duszy']), 'help Elor page missing')
            else:
                # Original v104 assertions, including first 80 historical trials.
                for tier in (1, 79, 80, 81, 250, 499, 500, 10000):
                    session.character.soul_tier=tier
                    offered=session.quest_ids_for_npc('priest_elor', elor)
                    new_trials=[q for q in offered if QUESTS[q].get('unlocks_soul_tier',0)>=81]
                    expected=[f'soul_tier_{n:02d}_trial' for n in range(tier+1,min(1001,tier+11))
                              if f'soul_tier_{n:02d}_trial' in QUESTS]
                    if tier<80 or not expected:
                        ck(not new_trials,f'future soul trials leaked Tier {tier}')
                    else:
                        ck(new_trials==expected,f'wrong Elor trial page Tier {tier}: {new_trials[:5]}')
                    ck(len(offered)<90, f'Elor overwhelming NVDA Tier {tier}: {len(offered)}')
                session.character.soul_tier=80
                for first in (81,501,801,991,1000):
                    texts.clear()
                    await session.show_quest_npc_list(f'Elor {first}')
                    shown=session.quest_list_context['quest_ids']
                    expected_page=[f'soul_tier_{n:02d}_trial' for n in range(first,min(1001,first+10))]
                    ck(shown==expected_page, f'Elor page {first} wrong context: {shown[:3]}')
                    ck(any(f'Tiery {first}' in line for line in texts),f'Elor page {first} invisible')
                    ck(len(texts)<=14,f'Elor page {first} too long for NVDA')
                texts.clear()
                await session.show_quest_npc_list('Elor 1001')
                ck(any('Podaj Tier' in line for line in texts),'v104 invalid tier accepted')
                from systems.content_registry import HELP_TOPICS,HELP_TOPIC_ALIASES
                ck('Tier 1000' in ' '.join(HELP_TOPICS['dusza']), 'runtime help dusza overwritten')
                ck(HELP_TOPIC_ALIASES.get('proby duszy')=='proby_duszy','help missing alias')
                ck('quest list Elor 801' in ' '.join(HELP_TOPICS['proby_duszy']),'help page missing')
                ck('1000' in str(elor.get('dialogue')),'Elor old dialog')
            # Existing NPCs without v103 marker keep their old result path.
            old = [x for x in NPCS.items() if x[1].get('v700_story_npc') and
                   not x[1].get('v10300_era_npc')]
            ck(bool(old), 'legacy NPC fixture')
            ck(all(not data.get('v10300_era_npc') for _,data in old[:5]), 'legacy flag changed')
            ck(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
            db.conn.close()

    asyncio.run(inner())
    return total

if __name__ == '__main__':
    print(f'ERA 103 NPC REAL OFFERS/ACCEPT SQLITE: {run()} PASS', flush=True)
