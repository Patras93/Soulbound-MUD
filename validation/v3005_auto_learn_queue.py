# -*- coding: utf-8 -*-
"""v3.00.5: isolated exercise of production auto-learning and queue code.

Only original class definitions are extracted to avoid bringing an entire world
and its optional services into these unit-level SQLite contract tests.
"""
import ast
import asyncio
from pathlib import Path
import re
import sqlite3
from types import SimpleNamespace
from core.classes_skills import CLASS_SKILLS

ROOT = Path(__file__).resolve().parents[1]

def source_class(path, name, context):
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'), filename=path)
    klass = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    namespace = dict(context)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[klass], type_ignores=[])), path, 'exec'), namespace)
    return namespace[name]


def class_for_skill(skill):
    if str(skill['id']).startswith('warrior_') or 'warrior' in str(skill['id']):
        return 'Wojownik'
    return 'Mag'

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE accounts(id INTEGER PRIMARY KEY);
            INSERT INTO accounts VALUES(1); INSERT INTO accounts VALUES(2);
            CREATE TABLE skill_queue (
                account_id INTEGER NOT NULL, queue_type TEXT NOT NULL,
                position INTEGER NOT NULL, skill_id TEXT NOT NULL,
                PRIMARY KEY(account_id,queue_type,position), UNIQUE(account_id,skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            CREATE TABLE skill_queue_settings(account_id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE skill_queue_auto_enrollment_v3005(account_id INTEGER PRIMARY KEY);
            CREATE TABLE learned_skills(account_id INTEGER NOT NULL,skill_id TEXT NOT NULL,
                learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(account_id,skill_id));
        ''')

    def learned_skill_ids(self, account_id):
        return {r[0] for r in self.conn.execute('SELECT skill_id FROM learned_skills WHERE account_id=?',(account_id,))}

    def knows_skill(self, account_id, skill_id):
        return skill_id in self.learned_skill_ids(account_id)

    def learn_skill(self, account_id, skill_id):
        self.conn.execute('INSERT OR IGNORE INTO learned_skills(account_id,skill_id) VALUES(?,?)',(account_id,skill_id))
        self.conn.commit()

    def skill_queue_rows(self, account_id, queue_type=None):
        if queue_type:
            return list(self.conn.execute('SELECT queue_type,position,skill_id FROM skill_queue WHERE account_id=? AND queue_type=? ORDER BY position',(account_id,queue_type)))
        return list(self.conn.execute("SELECT queue_type,position,skill_id FROM skill_queue WHERE account_id=? ORDER BY CASE queue_type WHEN 'physical' THEN 0 WHEN 'magic' THEN 1 ELSE 2 END, position",(account_id,)))

    def add_skill_queue_entry(self, account_id, queue_type, skill_id):
        existing = self.conn.execute('SELECT 1 FROM skill_queue WHERE account_id=? AND skill_id=?',(account_id,skill_id)).fetchone()
        if existing: return False, 'already'
        pos = self.conn.execute('SELECT COALESCE(MAX(position),0)+1 FROM skill_queue WHERE account_id=? AND queue_type=?',(account_id,queue_type)).fetchone()[0]
        self.conn.execute('INSERT INTO skill_queue VALUES(?,?,?,?)',(account_id,queue_type,pos,skill_id))
        self.conn.commit()
        return True,pos

    def remove_skill_queue_skill(self, account_id, skill_id):
        result=self.conn.execute('DELETE FROM skill_queue WHERE account_id=? AND skill_id=?',(account_id,skill_id))
        self.conn.commit()
        return result.rowcount

    def skill_queue_enabled(self,account_id):
        row=self.conn.execute('SELECT enabled FROM skill_queue_settings WHERE account_id=?',(account_id,)).fetchone()
        return bool(row and row[0])

    def set_skill_queue_enabled(self, account_id, enabled):
        self.conn.execute('INSERT INTO skill_queue_settings VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET enabled=excluded.enabled',(account_id,int(bool(enabled))))
        self.conn.commit()

    def active_class_rows(self,account_id, primary):
        return [{'class_name':'Mag','level':1},{'class_name':'Wojownik','level':1}]

ctx={'CLASS_SKILLS':CLASS_SKILLS,'_SKILLS_BY_ID_V3005':{skill['id']:skill for skills in CLASS_SKILLS.values() for skill in skills},
     'class_type_for_name':lambda name: 'magic' if name=='Mag' else 'physical','re':re, 'time':__import__('time'), 'CHARACTER_MAX_LEVEL':800}
Mixin=source_class('player/session_mixins/skill_queue_buffs.py','SessionSkillQueueBuffsMixin',ctx)
DBMethods=source_class('storage/db_progression.py','DatabaseProgressionMixin',ctx)
DB.auto_enroll_learned_skills_v3005=DBMethods.auto_enroll_learned_skills_v3005

class Session(Mixin):
    def __init__(self, db, account_id):
        self.server=SimpleNamespace(db=db)
        self.account_id=account_id
        self.character=SimpleNamespace(class_name='Mag',character_level=1,room_id='x')
        self.skill_queue_cursors={'physical':0,'magic':0,'feedback':0}
        self.skill_queue_next_type='magic'
        self.auto_queue_casting=False
        self._messages=[]
        self._casts=[]
    def skill_class_name(self,skill):
        return next((c for c,skills in CLASS_SKILLS.items() if skill in skills),'Mag')
    def active_class_names(self):return ['Mag','Wojownik']
    def normalize_description_query(self,raw):return str(raw).casefold()
    async def send(self,msg):self._messages.append(str(msg))
    def auto_queue_skill_usable(self,skill,mob):
        return bool(skill and skill.get('kind') in ('damage','aoe_damage','heal'))
    async def use_class_skill(self,name):self._casts.append(name)


def test():
    checks=0
    def yes(value, why):
        nonlocal checks
        if not value:raise AssertionError('AUTO LEARN 3.00.5: '+why)
        checks+=1
    db=DB()
    mage=CLASS_SKILLS['Mag'][0]
    mage2=CLASS_SKILLS['Mag'][1]
    warrior=CLASS_SKILLS['Wojownik'][0]
    for x in (mage,mage2,warrior):db.learn_skill(1,x['id'])
    # Simulate previously manually configured queue, preserve its ordering.
    db.add_skill_queue_entry(1,'physical',warrior['id'])
    db.set_skill_queue_enabled(1,True)
    s=Session(db,1)
    yes(s.auto_enroll_existing_skills_v3005()>=2,'legacy skills imported')
    yes(s.skill_queue_entries('magic',True)[0]['skill_id']==mage['id'],'magic first')
    yes(s.skill_queue_entries('physical',True)[0]['skill_id']==warrior['id'],'manual order kept')
    yes(s.skill_queue_capacity('magic') is None,'no cap')
    yes(db.skill_queue_enabled(1),'previous ON preserved')
    yes(s.auto_enroll_existing_skills_v3005()==0,'never import twice')
    db.remove_skill_queue_skill(1,mage['id'])
    s2=Session(db,1)
    yes(s2.auto_enroll_existing_skills_v3005()==0,'manual delete remains')
    yes(not any(r['skill_id']==mage['id'] for r in s2.skill_queue_entries('magic')),'removed skill stays out')
    db.set_skill_queue_enabled(1,False)
    new_skill=CLASS_SKILLS['Mag'][2]
    db.learn_skill(1,new_skill['id'])
    yes(s2.auto_register_learned_skill_v3005(new_skill)=='magic','new spell enrolled')
    yes(any(r['skill_id']==new_skill['id'] for r in s2.skill_queue_entries('magic')),'new spell present')
    yes(not db.skill_queue_enabled(1),'manual off respected')
    db.set_skill_queue_enabled(1,True)
    asyncio.run(s2.try_auto_skill_queue(SimpleNamespace(alive=True,room_id='x')))
    yes(len(s2._casts)==1,'auto spell fires in combat')
    yes(s2._casts[0] in {x['name'] for x in (mage2,new_skill)},'correct cast')
    # Fresh first-time player with disabled legacy setting receives automatic ON.
    db.learn_skill(2,mage['id'])
    db.set_skill_queue_enabled(2,False)
    s3=Session(db,2)
    yes(s3.auto_enroll_existing_skills_v3005()==1,'fresh imported')
    yes(db.skill_queue_enabled(2),'fresh auto ON')
    yes(s3.auto_queue_eligible_v3005({'id':'x','kind':'passive'}) is False,'passive excluded')
    yes(s3.auto_queue_eligible_v3005({'id':'x','kind':'utility'}) is False,'utility excluded')
    # No level-based limit, even with a massive queue.
    for i in range(140):
        db.learn_skill(2,f'dummy-{i}')
        db.add_skill_queue_entry(2,'magic',f'dummy-{i}')
    yes(len(s3.skill_queue_entries('magic',active_only=True))>=141,'more than 120 active slots')
    asyncio.run(s3.show_skill_queue('magic',page=3))
    yes(sum('Slot ' in text for text in s3._messages)==25,'NVDA pagination exactly 25')
    yes(any('strona 3' in text for text in s3._messages),'NVDA page notice')
    # Execute the real learn_class_skill method with a fake teacher in the room.
    LearnMixin = source_class('player/session_mixins/skill_learning.py', 'SessionSkillLearningMixin', ctx)
    class Learner(Session, LearnMixin):
        def __init__(self, db, account_id):
            super().__init__(db, account_id)
            self.character.guild_training_discount=lambda _class: 0.0
            self.combat_mob_key=None
        def teacher_here_for_active_class(self):
            return 'teacher', {'teacher_class':'Mag', 'name':'Mistrz Magii'}
        def class_mastery_level(self,_name):return 1
        def skill_training_cost_silver(self,skill):return 5
        def training_cost_text(self,cost):return f'{cost} srebra'
        def pay_training_cost(self,cost):return True
    db.conn.execute('INSERT INTO accounts(id) VALUES(3)')
    learner=Learner(db,3)
    asyncio.run(learner.learn_class_skill('3'))
    yes(db.knows_skill(3,CLASS_SKILLS['Mag'][2]['id']),'real learn 3 saves spell')
    yes(any(r['skill_id']==CLASS_SKILLS['Mag'][2]['id'] for r in db.skill_queue_rows(3,'magic')),'real learn auto queues spell')
    yes(db.skill_queue_enabled(3),'real learn starts casting')
    yes(any('Automatyczne używanie:' in line for line in learner._messages),'real learn announces auto use')
    before=len(db.skill_queue_rows(3,'magic'))
    asyncio.run(learner.learn_class_skill('3'))
    yes(len(db.skill_queue_rows(3,'magic'))==before,'repeat learn does not duplicate queue')
    return checks

if __name__=='__main__':
    print(f'AUTO LEARN & NO LIMIT QUEUE v3.00.5: {test()} checks PASS')
