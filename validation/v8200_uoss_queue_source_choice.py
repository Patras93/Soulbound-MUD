# -*- coding: utf-8 -*-
"""v82: normal combat and detached arena use the same side-effect-free chooser."""
import asyncio
import copy
import random
from types import SimpleNamespace
from unittest.mock import patch
from systems.uoss_queue_choice_shared_v8200 import choose_queued_skill
from systems.admin_live_queue_v8200 import inspect_queue, _ReadOnlyQueueDB
from validation.v8100_arena_soul_weapon_effects import ArenaOwner
# Load the actual queue methods without importing unrelated world catalogs too early.
# Runtime normally loads the global world catalogs first; stand-alone test
# executes only the unmodified class methods under test.
import ast
from pathlib import Path
import time
from core.classes_skills import effective_skill_mana_cost
_source = Path(__file__).resolve().parents[1]/'player/session_mixins/skill_queue_buffs.py'
_tree = ast.parse(_source.read_text(encoding='utf8'))
_cls = next(n for n in _tree.body if isinstance(n, ast.ClassDef) and n.name=='SessionSkillQueueBuffsMixin')
_methods = [n for n in _cls.body if isinstance(n, ast.FunctionDef) or isinstance(n, ast.AsyncFunctionDef)]
_scope = {'time':time,'effective_skill_mana_cost':effective_skill_mana_cost}
for _name in ('auto_queue_skill_usable','try_auto_skill_queue'):
    _method = next(m for m in _methods if m.name==_name)
    exec(compile(ast.Module(body=[_method],type_ignores=[]),str(_source),'exec'),_scope)


SKILLS = {
 's_low': {'id':'s_low','name':'Cios Burzy','kind':'damage','unlock':1,'mana':0},
 's_magic': {'id':'s_magic','name':'Fala Mocy','kind':'damage','unlock':1,'mana':15},
 's_cool': {'id':'s_cool','name':'Specjalne Ognie','kind':'damage','unlock':1,'mana':0,'mechanic_cooldown':True},
 's_pass': {'id':'s_pass','name':'Pasyw','kind':'passive','unlock':1,'mana':0},
}

class Owner(ArenaOwner):
    def __init__(self, owner=True, db=None):
        super().__init__(owner,db)
        self.character.class_name='Wojownik'
        self.skill_queue_next_type='physical'
        self.skill_queue_cursors={'physical':0,'magic':0,'feedback':0}
        self.skill_cooldowns={}
        self.active_skill_buffs={}
        self.skill_guard=0
        self.skill_evade=False
        self.queue_skills=dict(SKILLS)
        self.queue_rows={
            'physical':[{'skill_id':'s_pass'}, {'skill_id':'s_low'}, {'skill_id':'s_cool'}],
            'magic':[{'skill_id':'s_magic'}],
            'feedback':[],
        }
        self.queue_on=True
        self.cast_calls=[]
        self.server.db.skill_queue_enabled=lambda account: self.queue_on
        self.server.db.skill_queue_rows=lambda account,channel=None: (
            list(self.queue_rows.get(channel,[])) if channel else [x for rows in self.queue_rows.values() for x in rows])
        self.server.db.active_class_rows=lambda acc,cls: [{'class_name':'Wojownik','level':40}]
        self.server.db.knows_skill=lambda acc,sid: sid in SKILLS
        self.server.db.class_progress_row=lambda *a: {'level':40}
    auto_queue_skill_usable = _scope['auto_queue_skill_usable']
    try_auto_skill_queue = _scope['try_auto_skill_queue']
    def skill_queue_entries(self,channel,active_only=False):
        if active_only and channel != 'physical':return []
        return list(self.server.db.skill_queue_rows(self.account_id,channel))
    def skill_by_id(self,sid):return self.queue_skills.get(sid)
    def skill_class_name(self,skill):return 'Wojownik'
    def active_class_names(self):return {'Wojownik'}
    def skill_mastery_unlocked(self,skill):return True
    def skill_cooldown_ready_at_v0364(self,skill):return self.skill_cooldowns.get(skill['id'],0)
    async def use_class_skill(self,name):self.cast_calls.append(name)
    def auto_enroll_existing_skills_v3005(self):return 0
    def cleanup_unlearned_skill_queue_v11356(self):return 0
    def normalize_skill_queue_types_v1125(self):return 0

async def run():
    total=0
    def check(x,msg):
        nonlocal total
        if not x:raise AssertionError(msg)
        total+=1
    sample={'physical':[{'skill_id':'a'},{'skill_id':'b'}],'magic':[{'skill_id':'c'}],'feedback':[]}
    for preferred in ('physical','magic','feedback','bad'):
        for pos in range(5):
            for disabled in (set(),{'a'},{'a','b'},{'a','b','c'}):
                out=choose_queued_skill(preferred,{'physical':pos},lambda c: sample[c],
                    lambda sid: {'id':sid},lambda s:s['id'] not in disabled)
                if len(disabled)==3:check(out is None,'all unusable')
                else:check(out is not None and out[3]['id'] not in disabled,'sourced rotation')
    o=Owner()
    await o.admin_command('live arena start black_rabite 100000000 1000')
    check('ARENA11 START' in o.messages[-1],'arena created')
    state_before=copy.deepcopy(o.guardian7_lab)
    before_rng=random.getstate(); before_db=o.server.db.conn.total_changes
    check('POMOC 42' in await _send(o,'pomoc 42'),'help wired')
    txt=await _send(o,'arena uoss kolejka nastepny')
    check('Cios Burzy' in txt and '2/3' in txt,'real selector skips passive')
    check(o.skill_queue_cursors['physical']==0,'no queue cursor mutation')
    check(not o.cast_calls,'no real casting from preview')
    check(o.server.db.conn.total_changes==before_db and random.getstate()==before_rng,'DB RNG unchanged')
    check(o.guardian7_lab['round']==state_before['round'] and o.guardian7_lab['boss'].hp==state_before['boss'].hp and o.guardian7_lab['notes']==state_before['notes'],'LAB unchanged')
    o.skill_queue_cursors['physical']=2
    o.skill_cooldowns['s_cool']=10**12
    txt=await _send(o,'arena uoss kolejka nastepny')
    check('Cios Burzy' in txt,'skip active mechanical cooldown and wrap')
    o.skill_queue_cursors['physical']=2
    o.skill_cooldowns['s_cool']=0
    txt=await _send(o,'arena uoss kolejka nastepny')
    check('Specjalne Ognie' in txt,'cooldown elapsed')
    o.queue_rows['physical']=[{'skill_id':'s_pass'}]
    check('brak gotowego' in await _send(o,'arena uoss kolejka nastepny'),'no eligible skill')
    o.queue_on=False
    check('wylaczona' in await _send(o,'arena uoss kolejka nastepny'),'disabled queue')
    o.queue_on=True
    check('zablokowana' in _rejected_read(o.server.db),'unknown DB operation blocked')
    o.queue_rows['physical']=[{'skill_id':'s_low'}]
    o.skill_queue_cursors['physical']=0
    actor_mob=SimpleNamespace(alive=True,room_id='temple')
    o._queue_ready_account_v3005=o.account_id
    check(await o.try_auto_skill_queue(actor_mob),'normal combat queue uses shared chooser')
    check(o.cast_calls==['Cios Burzy'] and o.skill_queue_cursors['physical']==0,'real cast exactly once')
    check(o.skill_queue_next_type=='magic','production next channel rotated')
    check(o.server.db.conn.total_changes==before_db,'test fixture no DB updates')
    outsider=Owner(False,o.server.db)
    outsider.queue_on=True
    check('Nieznana komenda' in await _send(outsider,'arena uoss kolejka nastepny'),'admin only')
    await o.admin_command('live arena wyjdz')
    check('ADMIN LIVE V78' in await _send(o,'arena uoss kolejka nastepny'),'arena required')
    check(random.getstate()==before_rng,'global RNG unchanged after checks')
    return total

async def _send(owner,tail):
    await owner.admin_command('live '+tail)
    return owner.messages[-1]

def _rejected_read(db):
    view=_ReadOnlyQueueDB(db)
    try:view.save_character(None)
    except ValueError as exc:return str(exc)
    return ''

if __name__=='__main__':
    print('V82 REAL SKILL QUEUE CHOICE + DB ISOLATION:',asyncio.run(run()),'PASS')
