# -*- coding: utf-8 -*-
"""Isolated actual reward method + real SQLite regression for boosted skill XP."""
from __future__ import annotations
import ast
import asyncio
import tempfile
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

from core.classes_skills import CLASS_SKILLS, CLASSES, RACES, MEC_PROTOCOL_SKILLS_V11155
from core.progression_resources import v0190_scaled_gain, skill_xp_to_next
from core.bootstrap_economy_professions import V019_SAFE_INT
from core.progression_600 import SKILL_MAX_LEVEL
from systems.experience_bank_v2011 import banked_experience_v2011
from systems.achievement_rewards_v11331 import skill_milestone_exp_v11332
from storage.database import Database
from unittest.mock import patch
import random

# Load the exact release method body without booting a full live world into an
# already running SQLite fixture. A separate standalone-server smoke validates
# the assembled MRO in the real runtime.
SOURCE = ROOT/'player/session_mixins/skills_combat.py'
file_ast = ast.parse(SOURCE.read_text(encoding='utf-8'))
actual_class = next(n for n in file_ast.body if isinstance(n, ast.ClassDef) and n.name=='SessionSkillsCombatMixin')
actual_method = next(n for n in actual_class.body if isinstance(n, ast.AsyncFunctionDef) and n.name=='grant_skill_use_xp')
copy = ast.ClassDef(name='RealSkillUseMethod', bases=[], keywords=[], body=[actual_method], decorator_list=[])
ns = {
    'random': random,
    'CLASS_SKILLS': CLASS_SKILLS,
    'MEC_PROTOCOL_SKILLS_V11155': MEC_PROTOCOL_SKILLS_V11155,
    'v0190_scaled_gain': v0190_scaled_gain,
    'V019_SAFE_INT': V019_SAFE_INT,
    'SKILL_MAX_LEVEL': SKILL_MAX_LEVEL,
    'banked_experience_v2011': banked_experience_v2011,
}
exec(compile(ast.fix_missing_locations(ast.Module(body=[copy],type_ignores=[])), str(SOURCE), 'exec'),ns)
RealSkillUseMethod=ns['RealSkillUseMethod']

class Actor(RealSkillUseMethod):
    def __init__(self,db,aid,class_name):
        self.server=SimpleNamespace(db=db)
        self.account_id=aid
        self.character=SimpleNamespace(class_name=class_name)
        self.combat_mob_key=None
        self.sent=[]
    def skill_progress_data(self,skill):
        row=self.server.db.skill_progress(self.account_id,skill['id'])
        return {k: int(row[k]) for k in ('level','xp','uses')}
    def skill_class_name(self,skill):
        return self.character.class_name
    def skill_content_stage_v11342(self,skill):
        return 1
    def progression_content_multiplier_v11342(self,stage):
        return 1.0+(stage-1)/599
    def apply_double_xp(self,amount):
        return min(V019_SAFE_INT,int(amount))
    async def send(self,text,**kwargs):
        self.sent.append(str(text))


def test():
    checks = 0
    def ck(value,what):
        nonlocal checks
        assert value,what
        checks+=1

    ck(skill_milestone_exp_v11332(60_500,'Bronze')==6050,'10% of first-level skill requirement')
    ck(skill_milestone_exp_v11332(60_500,'Mythic')==18150,'30% mythical milestone')
    ck(skill_milestone_exp_v11332(100_000_000,'Gold')==20_000_000,'no obsolete 1M skill cap')
    ck(skill_milestone_exp_v11332(9_000_000_000,'Mythic')==1_000_000_000,'skill-only technical bound')
    ck(skill_milestone_exp_v11332(0,'Bronze')==0,'max level not rewarded')
    ck('grant_skill_use_xp' not in (ROOT/'player/session_methods_v4200/skilllearning_part01.py').read_text(encoding='utf-8'),'historical parts intact')
    with tempfile.TemporaryDirectory(prefix='sb-skill-v11332-') as td:
        db=Database(str(Path(td)/'test.sqlite'))
        db._manual_bank_only_v11325=True
        db._v108_live_event_caps=False
        def make(name,class_name):
            aid=db.create_account(name,'secure-pass-test-11332')
            cases={key:name for key in ('nom','gen','dat','acc','ins','loc','voc')}
            # v115: only Cyborg may select Mec. Preserve the real skill
            # progression test using a legal character, not a bypass.
            race = next(r for r in RACES if r[0] == 'Cyborg') if class_name == 'Mec' else RACES[0]
            db.create_character(aid,name,race,next(c for c in CLASSES if c[0]==class_name),cases)
            return Actor(db,aid,class_name)
        user=make('SkillUser','Wojownik')
        skill=next(s for s in CLASS_SKILLS['Wojownik'] if s.get('kind')=='damage')
        db.learn_skill(user.account_id,skill['id'])
        before_cap=db.multi_cap_v23215(user.account_id)
        before=db.skill_progress(user.account_id,skill['id'])
        base=v0190_scaled_gain(30,1,'skill',30)
        with patch.object(random,'randint',return_value=5):
            result=asyncio.run(user.grant_skill_use_xp(skill))
        award=min(base*48,before_cap)
        ck(result['xp']==award,f'first-level actual new XP: expected {award}, got {result}')
        ck(result['uses']==1,'one real use')
        ck(result['level']==1,'no unintentional immediate level jump')
        ck(any(f'Skill XP +{award}' in s for s in user.sent),'correct NVDA reward')
        ck(before['uses']==0,'source unchanged')
        before=result['xp']
        with patch.object(random,'randint',return_value=5):
            result=asyncio.run(user.grant_skill_use_xp(skill))
        ck(result['uses']==2 and result['xp']>before,'consecutive casts get consecutive payout')
        ck(db.conn.execute('SELECT COUNT(*) FROM experience_bank_v2011 WHERE balance != ?',('0',)).fetchone()[0]==0,'manual bank never auto credited')
        stranger=make('SkillStranger','Wojownik')
        db.learn_skill(stranger.account_id,skill['id'])
        ck(db.skill_progress(stranger.account_id,skill['id'])['xp']==0,'no leakage to another account')
        # High-level value scales with skill mastery, not future requirements.
        db.conn.execute('UPDATE skill_progress SET level=600,xp=0 WHERE account_id=? AND skill_id=?',(user.account_id,skill['id']))
        db.conn.commit()
        hi_cap=db.multi_cap_v23215(user.account_id)
        with patch.object(random,'randint',return_value=5):
            hi=asyncio.run(user.grant_skill_use_xp(skill))
        hi_base=v0190_scaled_gain(30,600,'skill',30)
        ck(hi['xp']==min(hi_base*(48+600//2),hi_cap),'600-level payout bounded by real Multi Cap')
        ck(hi['uses']==3,'high level use counted once')
        ck(db.skill_progress(stranger.account_id,skill['id'])['xp']==0,'high-level gain not shared')
        # A previously reached max level cannot grow beyond the real maximum.
        db.conn.execute('UPDATE skill_progress SET level=?,xp=0 WHERE account_id=? AND skill_id=?',(SKILL_MAX_LEVEL,user.account_id,skill['id']))
        db.conn.commit()
        with patch.object(random,'randint',return_value=5):
            result=asyncio.run(user.grant_skill_use_xp(skill))
        ck(result['level']==SKILL_MAX_LEVEL,'maximum level preserved')
        ck(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        # Passive learnings are credited only for legitimate learned skills
        # and remain 25% of the capped active cast reward.
        mec=make('SkillMec','Mec')
        active=next(s for s in CLASS_SKILLS['Mec'] if s.get('mec_special')=='crosshair')
        matching=next(s for s in CLASS_SKILLS['Mec'] if s['id']=='v0319_mec_ranged_protocol')
        unrelated=next(s for s in CLASS_SKILLS['Mec'] if s['id']=='v0319_mec_magic_protocol')
        for s in (active,matching,unrelated):db.learn_skill(mec.account_id,s['id'])
        with patch.object(random,'randint',return_value=5):
            got=asyncio.run(mec.grant_skill_use_xp(active))
        ck(db.skill_progress(mec.account_id,active['id'])['xp']==got['xp'],'mec active XP real')
        ck(db.skill_progress(mec.account_id,matching['id'])['xp']>0,'matching passive gets 25%')
        ck(db.skill_progress(mec.account_id,unrelated['id'])['xp']==0,'unrelated protocol gets no XP')
        ck(db.skill_progress(mec.account_id,matching['id'])['uses']==1,'one passive record update')
        db.conn.close()
    print(f'SKILL EXP V113.00.32: {checks}/{checks} PASS')

if __name__=='__main__': test()
