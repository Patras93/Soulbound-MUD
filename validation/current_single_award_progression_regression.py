# -*- coding: utf-8 -*-
"""Current progression: at most one level per credited award, no XP loss."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from player.character import Character
from core.progression_resources import (character_xp_to_next,
    soul_xp_to_next, soul_weapon_mastery_xp_to_next,
    class_mastery_xp_to_next, skill_xp_to_next)

class SingleAwardProgression(unittest.TestCase):
    def test_soul_preserves_large_saved_pool_and_respects_tier(self):
        c=object.__new__(Character)
        c.soul_level=80; c.soul_tier=8; c.soul_xp=225_047_361
        c.race='Człowiek';c._guild_bonus_percent=0
        c.racial_soul_xp_multiplier=lambda:1.0
        needed=soul_xp_to_next(80)
        notes=c.add_soul_xp(1)
        self.assertEqual(c.soul_level,81,notes)
        self.assertEqual(c.soul_xp,225_047_361+1-needed,notes)
        self.assertGreater(c.soul_xp,0)
        self.assertEqual(len([x for x in notes if 'osiąga Soul Level' in x]),1)
        # Tier boundary freezes NEW awards, preserves previously earned XP.
        c.soul_level=90;c.soul_xp=12345
        notes=c.add_soul_xp(999)
        self.assertEqual((c.soul_level,c.soul_xp),(90,12345))
        self.assertTrue(any('nie naliczono' in line for line in notes))

    def test_character_soul_weapon_and_stats_one_step(self):
        c=object.__new__(Character)
        c.character_level=10;c.character_xp=character_xp_to_next(10)*12
        old=c.character_xp; needed=character_xp_to_next(10)
        lines=c.add_character_xp(4)
        self.assertEqual((c.character_level,c.character_xp),(11,old+4-needed),lines)
        c.soul_weapon_mastery_level=1;c.soul_weapon_mastery_xp=0
        amount=soul_weapon_mastery_xp_to_next(1)*12
        result=c.add_soul_weapon_mastery_xp(amount)
        self.assertEqual(result['level_ups'],1)
        self.assertEqual(result['level'],2)
        self.assertEqual(result['xp'],amount-soul_weapon_mastery_xp_to_next(1))
        c.STAT_PROGRESS_FIELDS={
            k:(name,k,k+'_progress') for k,name in (
            ('strength','Siła'),('dexterity','Zręczność'),
            ('constitution','Kondycja'),('intelligence','Inteligencja'),
            ('willpower','Siła Woli'),('charisma','Charyzma'))}
        for k in c.STAT_PROGRESS_FIELDS:
            setattr(c,k,10);setattr(c,k+'_progress',0)
        c.stat_progress=0;c.race='Człowiek';c._guild_bonus_percent=0
        c.racial_stat_progress_multiplier=lambda:1.0
        c.stat_growth_threshold_for=lambda _:100
        c.add_stat_progress(100_000)
        for k in c.STAT_PROGRESS_FIELDS:
            self.assertEqual(getattr(c,k),11,k)
            self.assertGreater(getattr(c,k+'_progress'),0,k)

    def test_live_sqlite_class_and_skill_one_level(self):
        from storage.database import Database
        from core.classes_skills import RACES,CLASSES,CLASS_SKILLS
        with tempfile.TemporaryDirectory(prefix='sb-award-v1169-') as td:
            db=Database(str(Path(td)/'award.sqlite'))
            aid=db.create_account('SoloAwans','secure-long-password')
            forms={k:'SoloAwans' for k in ('nom','gen','dat','acc','ins','loc','voc')}
            db.create_character(aid,'SoloAwans',RACES[0],CLASSES[0],forms)
            classname=CLASSES[0][0]
            db.ensure_class_progress(aid,classname)
            before=db.class_progress_row(aid,classname)
            initial=int(before['level']);amount=class_mastery_xp_to_next(initial)*12
            out=db.add_class_mastery_xp(aid,classname,amount)
            self.assertEqual(out['level'],initial+1)
            self.assertEqual(out['level_ups'],1)
            self.assertEqual(out['xp'],amount-class_mastery_xp_to_next(initial))
            skill=CLASS_SKILLS[classname][0]['id']
            db.learn_skill(aid,skill)
            before=db.skill_progress(aid,skill)
            first=int(before['level']);needed=skill_xp_to_next(first)
            paid=needed*12
            outcome=db.add_skill_xp(aid,skill,paid)
            self.assertEqual(outcome['level'],first+1)
            self.assertEqual(outcome['level_ups'],1)
            self.assertEqual(outcome['xp'],int(before['xp'])+paid-needed)
            db.conn.close()

    def test_active_profession_runtime_overrides_protected_native(self):
        from player.session_mixins.professions_storage_guide import SessionProfessionsStorageGuideMixin
        from player.session_mixins.profession_storage import SessionProfessionStorageMixin
        from validation.current_native_v420_contract import verify_native_method, EXPECTED
        for name in ('grant_profession_progress','grant_tool_progress',
                     'grant_tool_reward_xp','grant_profession_reward_xp'):
            current=getattr(SessionProfessionsStorageGuideMixin,name)
            native=getattr(SessionProfessionStorageMixin,name)
            self.assertNotEqual(current,native)
            self.assertIn('current_profession_awards.py',current.__code__.co_filename)
            self.assertIn('min',current.__code__.co_names)
            protected='SessionProfessionStorageMixin.'+name
            root=Path(__file__).resolve().parents[1]
            self.assertTrue(verify_native_method(root/'player/session_mixins/profession_storage.py',protected))

if __name__=='__main__':
    unittest.main()
