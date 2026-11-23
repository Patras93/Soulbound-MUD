# -*- coding: utf-8 -*-
"""Required v116.64 global EXP source balance; uncapped means no award clipping."""
import unittest
from types import SimpleNamespace
from core.progression_resources import character_xp_to_next
from systems.independent_milestone_xp_v11664 import ep_xp_per_point_v11664,fame_xp_per_first_v11664
from systems.progression_rebalance_v11664 import (live_kill_reward_v11664,
    rebalanced_quest_plan_v11664,kills_per_level_target_v11664,content_relevance_v11664)

class MockSession:
    def __init__(self, lvl=92):
        self.character=SimpleNamespace(character_level=lvl,soul_level=lvl-4,
            strength=lvl, dexterity=lvl, constitution=lvl,
            intelligence=lvl,willpower=lvl,charisma=lvl,
            STAT_PROGRESS_FIELDS={s:None for s in ('strength','dexterity','constitution','intelligence','willpower','charisma')},
            stat_growth_threshold_for=lambda n:1000*max(1,lvl))
        self.server=SimpleNamespace(db=SimpleNamespace(
            profession=lambda *x:{'level':1},tool=lambda *x:{'level':1}))
        self.account_id=1
    def active_class_names(self):return ('Mec',)
    def class_mastery_level(self,name):return max(1,self.character.character_level-1)
    def profession_xp_to_next(self,level,profession=None):return 10000*max(1,level)
    def tool_xp_to_next(self,level,tool_type=None):return 10000*max(1,level)

class GlobalRebalanceTests(unittest.TestCase):
    def test_early_kill_requires_repeated_combat_not_one_shot_level(self):
        s=MockSession(1); r=live_kill_reward_v11664(s,{},stage=1,class_levels=(('Mec',1),))
        self.assertGreater(r['character'],0)
        self.assertLess(r['character'],character_xp_to_next(1)//50)
        self.assertGreater(r['soul'],0)
    def test_high_level_normal_is_meaningful_but_not_an_instant_level(self):
        s=MockSession(92)
        r=live_kill_reward_v11664(s,{},stage=92,class_levels=(('Mec',91),))
        n=character_xp_to_next(92)
        self.assertGreaterEqual(r['character'],n//320)
        self.assertLessEqual(r['character'],n//150)
        self.assertGreater(r['class'],0)
        self.assertEqual(r['stat']>0,True)
        self.assertGreater(kills_per_level_target_v11664(92),150)
    def test_bosses_and_elites_more_rewarding(self):
        s=MockSession(92)
        normal=live_kill_reward_v11664(s,{},stage=92)['character']
        elite=live_kill_reward_v11664(s,{'elite':True},stage=92)['character']
        boss=live_kill_reward_v11664(s,{'boss':True},stage=92)['character']
        self.assertGreater(boss,elite)
        self.assertGreater(elite,normal)
        self.assertLess(boss,character_xp_to_next(92)//10)
    def test_old_zones_dont_mass_grind_and_future_zones_not_powerlevel(self):
        s=MockSession(92)
        low=live_kill_reward_v11664(s,{},stage=2)['character']
        same=live_kill_reward_v11664(s,{},stage=92)['character']
        high=live_kill_reward_v11664(s,{},stage=400)['character']
        self.assertLess(low,same//5)
        self.assertLessEqual(high,same*2)
        self.assertGreater(content_relevance_v11664(92,92),.99)
        exact=live_kill_reward_v11664(s,{'source_xp_exact':True,'boss':True,'source_xp':10**15},stage=92)
        self.assertLess(exact['character'],character_xp_to_next(92)//10)
        self.assertEqual(live_kill_reward_v11664(s,{},stage=92,combat_multiplier=0)['character'],0)
    def test_novice_quest_no_200k_floor_no_mass_level(self):
        s=MockSession(1)
        original={'character':200000,'soul':200000,'class_xp':200000,
                  'stats':{n:200000 for n in s.character.STAT_PROGRESS_FIELDS},
                  'profession':0,'tool':0}
        q={'generator_level':1,'kind':'kill','needed':3}
        plan=rebalanced_quest_plan_v11664(s,'starter',q,original)
        self.assertLess(plan['character'],character_xp_to_next(1)//5)
        self.assertLess(plan['character'],original['character'])
        self.assertGreater(plan['class_xp'],0)
        self.assertEqual(plan['profession'],0)
    def test_quest_level_92_hero_highly_rewarding_with_no_cap(self):
        s=MockSession(92)
        original={'character':200000,'soul':200000,'class_xp':200000,
                  'stats':{n:200000 for n in s.character.STAT_PROGRESS_FIELDS},
                  'profession':200000,'tool':200000}
        q={'generator_level':92,'kind':'kill','needed':10,'reward_tool_type':'alchemy','reward_profession':'Alchemia'}
        p=rebalanced_quest_plan_v11664(s,'progressive',q,original)
        self.assertGreater(p['character'],3000000)
        self.assertLess(p['character'],10000000)
        self.assertGreater(p['profession'],0)
        self.assertGreater(p['tool'],0)
        self.assertGreater(p['soul'],0)
        repeat=rebalanced_quest_plan_v11664(s,'repeat',{**q,'repeatable':True},original)
        self.assertLess(repeat['character'],p['character'])
    def test_milestones_tied_to_real_requirement_not_old_cap(self):
        n=character_xp_to_next(92)
        ep=ep_xp_per_point_v11664(92);fame=fame_xp_per_first_v11664(92)
        self.assertGreater(ep,100000)
        self.assertLess(ep,300000)
        self.assertGreater(fame,ep)
        self.assertEqual(ep,n//500)
        self.assertEqual(fame,n//200)
    def test_no_hires_no_bank_no_caps_flags_are_separate(self):
        import inspect
        from systems.experience_bank_v2011 import banked_experience_v2011
        src=inspect.getsource(banked_experience_v2011)
        self.assertIn("'_uncapped_awards_v11664'",src)
        self.assertIn('return number(amount if amount is not None else 0)',src)
        # The live quest/combat gates must be active, not only this test helper.
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        for name in ('combat_rewards','quest_commands','quest_offers'):
            source=(root/'player'/'session_mixins'/(name+'.py')).read_text('utf8')
            self.assertIn('_rebalanced_awards_v11664',source)

def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(GlobalRebalanceTests)
    res=unittest.TextTestRunner(verbosity=0).run(suite)
    if not res.wasSuccessful():raise AssertionError('Globalny rebalans 116.64 FAIL')
    return res.testsRun
if __name__=='__main__':print('GLOBAL REBALANCE v116.64: %s/8 PASS'%run())
