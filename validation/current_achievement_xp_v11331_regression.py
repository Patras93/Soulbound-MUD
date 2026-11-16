# -*- coding: utf-8 -*-
"""Live SQLite/real progression gateways for achievement-specific XP rewards."""
from __future__ import annotations
import asyncio
import tempfile
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))

from storage.database import Database
from player.character import Character
from core.classes_skills import RACES,CLASSES,CLASS_SKILLS
from player.session_mixins.achievement_xp_v11331 import SessionAchievementXpV11331Mixin
from player.session_mixins.profession_storage import SessionProfessionStorageMixin
from systems.achievement_rewards_v11331 import reward_domains_v11331

class TestSession(SessionAchievementXpV11331Mixin,SessionProfessionStorageMixin):
    def __init__(self,db,aid):
        self.server=SimpleNamespace(db=db)
        self.account_id=aid
        self.character=Character.from_row(db.character_for_account(aid))
        self.messages=[]
    async def send(self,text,*args,**kwargs):self.messages.append(str(text))
    async def unlock_title(self,key,name,announce=True):
        self.server.db.unlock_title(self.account_id,key,name)
    def class_mastery_level(self,name):
        row=self.server.db.class_progress_row(self.account_id,name)
        return int(row['level']) if row else 1

def test():
    checks=0
    def ok(condition,label):
        nonlocal checks
        assert condition,label
        checks+=1
    for metric,expected in (
       ('rare_fish_caught',('profession:Wędkarstwo','tool:fishing')),
       ('gems_found',('profession:Górnictwo','tool:mining')),
       ('boss_kills',('character','soul','class','stats','combat_skill')),
       ('exploration_rooms',('character','profession:Kartografia','tool:cartography_profession')),
       ('soul_level',('character','soul_weapon')),
       ('multiclass_classes',('character','class','stats')),
    ):
        ok(reward_domains_v11331(metric)==expected,'mapping '+metric)
    with tempfile.TemporaryDirectory(prefix='sb-current-achievement-11331-') as td:
        db=Database(str(Path(td)/'test.sqlite'))
        def make(name):
            aid=db.create_account(name,'secure-pass-test-11331')
            cases={key:name for key in ('nom','gen','dat','acc','ins','loc','voc')}
            db.create_character(aid,name,RACES[0],CLASSES[0],cases)
            return TestSession(db,aid)
        fish=make('RybakXP')
        before_p=dict(db.profession(fish.account_id,'Wędkarstwo'))
        before_t=dict(db.tool(fish.account_id,'fishing'))
        asyncio.run(fish.check_achievement_tiers('rare_fish_caught',1))
        ok(db.profession(fish.account_id,'Wędkarstwo')['xp']>before_p['xp'],'fishing profession gained')
        ok(db.tool(fish.account_id,'fishing')['xp']>before_t['xp'],'fishing rod gained')
        ok(fish.character.character_xp==0 and fish.character.soul_xp==0,'no combat/soul from fish')
        ok(len([m for m in fish.messages if m.startswith('Nagroda EXP:')])==1,'one notice')
        before=(db.profession(fish.account_id,'Wędkarstwo')['xp'],db.tool(fish.account_id,'fishing')['xp'])
        asyncio.run(fish.check_achievement_tiers('rare_fish_caught',1))
        ok((db.profession(fish.account_id,'Wędkarstwo')['xp'],db.tool(fish.account_id,'fishing')['xp'])==before,'no replay on repeated checking')
        ok(len([m for m in fish.messages if m.startswith('Nagroda EXP:')])==1,'no replay message')
        miner=make('GornikXP')
        asyncio.run(miner.check_achievement_tiers('gems_found',1))
        ok(db.tool(miner.account_id,'mining')['xp']>0,'mining tool XP')
        ok(db.tool(miner.account_id,'fishing')['xp']==0,'no fishing rod for gems')
        ok(db.profession(miner.account_id,'Górnictwo')['xp']>0,'mining profession XP')
        hero=make('WojownikXP')
        skill=next(s for s in CLASS_SKILLS[hero.character.class_name] if s.get('kind')=='damage')
        db.learn_skill(hero.account_id,skill['id'])
        before_uses=db.skill_progress(hero.account_id,skill['id'])['uses']
        asyncio.run(hero.check_achievement_tiers('goblin_kills',10))
        ok(hero.character.character_xp>0,'combat char XP')
        ok(hero.character.soul_xp>0,'combat soul XP')
        ok(db.class_progress_row(hero.account_id,hero.character.class_name)['xp']>0,'combat class XP')
        ok(db.skill_progress(hero.account_id,skill['id'])['xp']>0,'known offensive skill XP')
        ok(db.skill_progress(hero.account_id,skill['id'])['uses']==before_uses,'no fake skill use')
        ok(hero.character.strength_progress>0,'combat stat XP')
        ok(db.tool(hero.account_id,'fishing')['xp']==0,'no fish rod for combat')
        before_state=(hero.character.character_xp,hero.character.soul_xp,db.skill_progress(hero.account_id,skill['id'])['xp'])
        asyncio.run(hero.check_achievement_tiers('goblin_kills',10))
        ok(before_state==(hero.character.character_xp,hero.character.soul_xp,db.skill_progress(hero.account_id,skill['id'])['xp']),'combat idempotent')
        ok(db.tool(fish.account_id,'fishing')['xp']==before[1],'account isolation')
        soul=make('SoulXP')
        asyncio.run(soul.check_achievement_tiers('soul_level',50))
        ok(soul.character.character_xp>0,'soul milestone gives character XP')
        ok(soul.character.soul_weapon_mastery_xp>0,'soul milestone gives mastery XP')
        ok(soul.character.soul_xp==0,'no self-triggering soul XP')
        cart=make('KartografXP')
        asyncio.run(cart.check_achievement_tiers('exploration_rooms',100))
        ok(db.profession(cart.account_id,'Kartografia')['xp']>0,'cartography profession XP')
        ok(db.tool(cart.account_id,'cartography_profession')['xp']>0,'cartography tool XP')
        bad=make('RollbackXP')
        original=db.save_tool
        def fail(*args,**kw):raise RuntimeError('SQLite simulated write fail')
        with patch.object(db,'save_tool',side_effect=fail):
            try: asyncio.run(bad.check_achievement_tiers('rare_fish_caught',1))
            except RuntimeError as exc:
                assert str(exc) == "SQLite simulated write fail", "Nieoczekiwany blad SQLite w tescie cofniecia"
            else: raise AssertionError('failing SQLite write must fail whole achievement')
        ok(db.conn.execute('SELECT 1 FROM achievements WHERE account_id=? AND achievement_id=?',(bad.account_id,'rare_fish_caught:bronze')).fetchone() is None,'rollback achievement')
        ok(db.profession(bad.account_id,'Wędkarstwo')['xp']==0,'rollback partial profession XP')
        ok(db.tool(bad.account_id,'fishing')['xp']==0,'rollback tool XP')
        ok(not bad.messages,'no false notice after rollback')
        asyncio.run(bad.check_achievement_tiers('rare_fish_caught',1))
        ok(db.profession(bad.account_id,'Wędkarstwo')['xp']>0,'retry after rollback')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # No automatic EXP Bank deposit or withdrawal is permitted.
        ok(db.conn.execute('SELECT COUNT(*) FROM experience_bank_v2011 WHERE balance != ?',('0',)).fetchone()[0]==0,'old EXP Bank not modified')
        db.conn.close()
    print(f'ACHIEVEMENT-BASED XP v113.00.31: {checks}/{checks} PASS')
    return checks

if __name__=='__main__':test()
