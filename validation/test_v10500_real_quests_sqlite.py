# -*- coding: utf-8 -*-
"""Real Session/NPC handlers and SQLite quest loop across all 20 v105 regions.

Not a substitute for five-player live TCP or a production database backup.
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


class V105RegionalQuestRuntimeTests(unittest.TestCase):
    def test_all_twenty_regions_accept_progress_turn_in_and_restart(self):
        # A full server bootstrap must run in a clean interpreter: the other
        # v105 tests import some world catalogs already, and reloading all of
        # them in the same interpreter duplicates legacy Boris quest IDs.
        if os.environ.get('SOULBOUND_V105_REAL_QUEST_CHILD') != '1':
            env=dict(os.environ, SOULBOUND_V105_REAL_QUEST_CHILD='1')
            result=subprocess.run([
                sys.executable,'-m','unittest',
                'validation.test_v10500_real_quests_sqlite.'
                'V105RegionalQuestRuntimeTests.'
                'test_all_twenty_regions_accept_progress_turn_in_and_restart','-q',
            ],cwd=str(Path(__file__).resolve().parents[1]),env=env,
              stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=150)
            self.assertEqual(result.returncode,0,
                'Izolowana prawdziwa sesja NPC/SQLite v105 FAIL:\n'+result.stdout+'\n'+result.stderr)
            self.assertIn('OK',result.stderr)
            return
        import server
        from storage.database import Database
        from player.character import Character
        from player.session import Session
        from core.classes_skills import CLASSES, RACES
        from systems.content_registry import NPCS, QUESTS
        from world.v10500_region_index import REGIONS
        with tempfile.TemporaryDirectory(prefix='sb105_quest_runtime_') as td:
            path=str(Path(td)/'real_session.sqlite')
            db=Database(path)
            account=db.create_account('V105RegionalQuest','safe_test_pass')
            db.create_character(account,'V105QuestTester',RACES[0],CLASSES[0],{
                'nom':'Test','gen':'Testu','dat':'Testowi','acc':'Test',
                'ins':'Testem','loc':'Teście','voc':'Teście'})
            s=Session.__new__(Session)
            ev=[]
            async def publish(event):ev.append(event)
            s.server=SimpleNamespace(db=db,events=SimpleNamespace(publish=publish),
                                     party_key_for_account=lambda a:None)
            s.account_id=account
            s.character=Character.from_row(db.character_for_account(account))
            s.combat_mob_key=None
            s.quest_list_context=None
            sent=[]
            async def send(msg,*_,**__):sent.append(str(msg))
            async def nothing(*_,**__):return []
            s.send=send
            s.grant_profession_reward_xp=nothing
            s.grant_tool_reward_xp=nothing
            s.grant_combat_quest_stat_xp=nothing
            s.grant_class_xp=nothing
            s.grant_soul_xp=nothing
            s.add_character_xp_with_event=lambda *a,**k: []
            s.record_item_collection=nothing

            async def scenario():
                for slug,*_ in REGIONS:
                    prefix='v10500_'+slug
                    npc_id=prefix+'_npc_1'
                    npc=NPCS[npc_id]
                    s.character.room_id=npc['room']
                    qid=prefix+'_story_01'
                    offers=s.quest_ids_for_npc(npc_id,npc)
                    self.assertIn(qid,offers,'first story quest must be visible')
                    # Existing v103 offer filtering keeps one story stage.
                    # This NPC has 6 stories plus 15 profession quests;
                    # three pages total, numbers local to each page.
                    regional_specialist=NPCS[prefix+'_npc_3']
                    s.character.room_id=regional_specialist['room']
                    await s.show_quest_npc_list(regional_specialist['name'])
                    self.assertEqual(len(s.quest_list_context['quest_ids']),10)
                    self.assertEqual(s.quest_list_context['quest_ids'][0],prefix+'_story_15')
                    await s.show_quest_npc_list(regional_specialist['name']+' strona 2')
                    self.assertEqual(len(s.quest_list_context['quest_ids']),10)
                    self.assertEqual(s.quest_list_context['quest_ids'][0],prefix+'_prof_05')
                    await s.show_quest_npc_list(regional_specialist['name']+' strona 3')
                    self.assertEqual(len(s.quest_list_context['quest_ids']),1)
                    self.assertEqual(s.quest_list_context['quest_ids'][0],prefix+'_prof_15')
                    previous_context=list(s.quest_list_context['quest_ids'])
                    await s.show_quest_npc_list(regional_specialist['name']+' strona 4')
                    self.assertEqual(s.quest_list_context['quest_ids'],previous_context,
                                     'invalid page must not replace previous context')
                    # v105 contract: *all* 50 authored quests must be browseable,
                    # not just the v103 legacy one-current-story subset.
                    offered=set()
                    for variant in (1,2,3):
                        member_id=prefix+'_npc_'+str(variant)
                        member=NPCS[member_id]
                        offered.update(s.quest_ids_for_npc(member_id,member))
                    authored={prefix+'_'+kind+'_'+f'{n:02d}'
                              for kind,size in (('story',20),('prof',15),('hunt',10),('explore',5))
                              for n in range(1,size+1)}
                    self.assertEqual(offered,authored)
                    # Real number from second NPC page must accept the boss
                    # hunt, NOT the same numbered story from the unpaged list.
                    hunter_id=prefix+'_npc_2'
                    hunter=NPCS[hunter_id]
                    s.character.room_id=hunter['room']
                    await s.show_quest_npc_list(hunter['name']+' strona 2')
                    boss_quest=prefix+'_hunt_09'
                    self.assertIn(boss_quest,s.quest_list_context['quest_ids'])
                    boss_ordinal=s.quest_list_context['quest_ids'].index(boss_quest)+1
                    await s.accept_quest_from_context(str(boss_ordinal))
                    self.assertEqual(db.quest(account,boss_quest)['status'],'active')
                    # The old story chain remains guarded even though its
                    # later entries can now be previewed.
                    locked=prefix+'_story_13'
                    self.assertTrue(s.quest_lock_reasons(locked))
                    s.character.room_id=npc['room']
                    await s.show_npc_quest_offers(npc_id,npc)
                    self.assertIn(qid,s.quest_list_context['quest_ids'])
                    index=s.quest_list_context['quest_ids'].index(qid)+1
                    await s.quests('accept '+str(index))
                    self.assertEqual(db.quest(account,qid)['status'],'active')
                    quest=QUESTS[qid]
                    for _ in range(int(quest['needed'])):
                        db.increment_quest(account,quest['target'])
                    self.assertGreaterEqual(int(db.quest(account,qid)['progress']),int(quest['needed']))
                    await s.quests('oddaj '+str(index))
                    self.assertEqual(db.quest(account,qid)['status'],'completed')
                    self.assertIn(prefix+'_story_02',s.quest_ids_for_npc(npc_id,npc))
                self.assertEqual(db.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            asyncio.run(scenario())
            db.conn.close()
            reopened=Database(path)
            self.addCleanup(reopened.conn.close)
            for slug,*_ in REGIONS:
                self.assertEqual(reopened.quest(account,'v10500_'+slug+'_story_01')['status'],'completed')

if __name__ == '__main__':unittest.main()
