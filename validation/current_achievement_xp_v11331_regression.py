# -*- coding: utf-8 -*-
"""Live SQLite/real progression gateways for achievement-specific XP rewards."""
from __future__ import annotations
import asyncio
from datetime import date
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
        self.closed=False
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
        db._manual_bank_only_v11325=True  # align fixture with real live session
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
        # CURRENT v116.00.42: daily/advent grants all *existing* progression
        # axes without unlocked content, fake actions or multiple payouts.
        from systems.gift_parts.payout import claim_once
        from systems.gift_parts.rewards import _daily_growth_amount
        # Live gameplay keeps old bank balances manual-only.
        db._manual_bank_only_v11325=True
        daily=make('DailyGiftGrowth')
        daily_aid=daily.account_id
        skill_ids=[row['id'] for row in CLASS_SKILLS[daily.character.class_name][:2]]
        for skill_id in skill_ids:
            db.learn_skill(daily_aid,skill_id)
        # One played profession/tool and one dormant placeholder each.
        db.profession(daily_aid,'Wędkarstwo')
        db.save_profession(daily_aid,'Wędkarstwo',1,0,1)
        db.tool(daily_aid,'fishing')
        db.save_tool(daily_aid,'fishing',1,0,1)
        db.profession(daily_aid,'Górnictwo')
        db.tool(daily_aid,'mining')
        skill_uses={sk:db.skill_progress(daily_aid,sk)['uses'] for sk in skill_ids}
        before_level=daily.character.character_level
        gift=claim_once(daily,day=date(2026,11,21))
        ok(gift is not None and gift['kind']=='daily','daily gift delivered')
        ok(gift['other_xp']['soul']>0 and daily.character.soul_xp>0,'daily Soul XP')
        ok(gift['other_xp']['stats']>0 and all(
            daily.character.stat_progress_for(k)>0 for k in daily.character.STAT_PROGRESS_FIELDS),
            'daily all six stats')
        ok(gift['other_xp']['class']>0 and
           int(db.class_progress_row(daily_aid,daily.character.class_name)['xp'])>0,
           'daily primary class XP')
        ok(gift['other_xp']['weapon']>0 and daily.character.soul_weapon_mastery_xp>0,
           'daily Soul Weapon Mastery')
        ok(gift['other_xp']['skills']>0 and all(
            db.skill_progress(daily_aid,sk)['xp']>0 for sk in skill_ids),
           'daily all known skills')
        ok(all(db.skill_progress(daily_aid,sk)['uses']==skill_uses[sk] for sk in skill_ids),
           'daily is not a skill cast')
        ok(gift['other_xp']['profession']>0 and db.profession(daily_aid,'Wędkarstwo')['xp']>0,
           'daily played profession')
        ok(gift['other_xp']['tool']>0 and db.tool(daily_aid,'fishing')['xp']>0,
           'daily used tool')
        ok(db.profession(daily_aid,'Górnictwo')['xp']==0 and
           db.tool(daily_aid,'mining')['xp']==0,
           'no phantom growth for only queried inactive tracks')
        ok(db.profession(daily_aid,'Wędkarstwo')['actions']==1 and
           db.tool(daily_aid,'fishing')['uses']==1,
           'no fake profession or tool action')
        ok(daily.character.character_level<=before_level+1,'no multilevel daily character')
        snapshot=(daily.character.character_xp,daily.character.soul_xp,
                  db.class_progress_row(daily_aid,daily.character.class_name)['xp'])
        ok(claim_once(daily,day=date(2026,11,21)) is None,'same day no duplicate')
        ok(snapshot==(daily.character.character_xp,daily.character.soul_xp,
                     db.class_progress_row(daily_aid,daily.character.class_name)['xp']),
           'no duplicate across axes')
        ok(_daily_growth_amount(10000,'advent') > _daily_growth_amount(10000,'daily'),
           'advent all axes bonus higher')
        from systems.gift_parts.delivery import announce_gift
        asyncio.run(announce_gift(daily,gift))
        ok(daily.messages[-1].startswith('DZIENNY PREZENT:'),
           'daily NVDA announcement name unchanged')
        mag=make('MagitekBonus')
        # Synthetic active Magitek profile: actual UOSS classes are registered
        # by later world content and not part of the original 22-class fixture.
        mag.character.class_name='Magitek'
        db.conn.execute('UPDATE characters SET class_name=? WHERE account_id=?',
                        ('Magitek',mag.account_id))
        db.conn.commit()
        db.ensure_primary_class(mag.account_id,'Magitek')
        db.learn_skill(mag.account_id,'v107_magitek_runicweapon')
        magic=claim_once(mag,day=date(2026,12,6))
        ok(magic is not None and magic['kind']=='advent','advent delivered')
        ok(db.class_progress_row(mag.account_id,'Magitek')['xp']>0,
           'Magitek mastery from Advent')
        ok(db.skill_progress(mag.account_id,'v107_magitek_runicweapon')['xp']>0,
           'learned Magitek skill from Advent')
        ok(magic['other_xp']['stats']>0 and magic['other_xp']['soul']>0,
           'advent grows all same domains')
        ok(db.conn.execute('SELECT COUNT(*) FROM learned_skills WHERE account_id=?',
                           (mag.account_id,)).fetchone()[0]==1,
           'advent does not unlock new Magitek skills')
        # Late failure must roll back every axis and the per-day receipt.
        roll=make('DailyGiftRollback')
        rid=roll.account_id
        db.tool(rid,'fishing'); db.save_tool(rid,'fishing',1,0,1)
        db.profession(rid,'Wędkarstwo'); db.save_profession(rid,'Wędkarstwo',1,0,1)
        before_roll=dict(roll.character.__dict__)
        before_class=dict(db.class_progress_row(rid,roll.character.class_name))
        with patch.object(db,'save_tool',side_effect=RuntimeError('daily injected tool failure')):
            try: claim_once(roll,day=date(2026,11,23))
            except RuntimeError as exc:
                ok(str(exc)=='daily injected tool failure','injected late failure')
            else: raise AssertionError('Gift tool error must abort whole gift')
        ok(dict(roll.character.__dict__)==before_roll,'rollback all character axes')
        ok(dict(db.class_progress_row(rid,roll.character.class_name))==before_class,
           'rollback class XP')
        ok(db.profession(rid,'Wędkarstwo')['xp']==0 and db.tool(rid,'fishing')['xp']==0,
           'rollback all career progress')
        ok(db.conn.execute('SELECT 1 FROM v109_gift_claims WHERE master_account_id=? '
                           'AND gift_date=?',(db.master_account_for_character(rid),'2026-11-23')).fetchone() is None,
           'rollback receipt')
        ok(claim_once(roll,day=date(2026,11,23)) is not None,'retry after failure')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # No automatic EXP Bank deposit or withdrawal is permitted.
        ok(db.conn.execute('SELECT COUNT(*) FROM experience_bank_v2011 WHERE balance != ?',('0',)).fetchone()[0]==0,'old EXP Bank not modified')
        db.conn.close()
    print(f'ACHIEVEMENT-BASED XP v113.00.31: {checks}/{checks} PASS')
    return checks

if __name__=='__main__':test()
