# -*- coding: utf-8 -*-
"""Isolated OLC skill publication / backup / queue / regression checks."""
import copy
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from core.classes_skills import CLASS_SKILLS
from data.quests import QUESTS
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc4_browse import find_catalog, fields_for
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.live_quest_olc_v1209 import news_summary
import ast
import sys


def _lookup_for_test(skill_id):
    # Compile the actual source method, not a mocked copy of its logic.
    code = Path('player/session_mixins/skill_queue_buffs.py').read_text('utf8')
    tree = ast.parse(code)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'SessionSkillQueueBuffsMixin')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'skill_by_id')
    scope = {'CLASS_SKILLS':CLASS_SKILLS, '_SKILLS_BY_ID_V3005':{}}
    exec(compile(ast.Module(body=[method],type_ignores=[]),'<combat-skill-lookup>','exec'), scope)
    return scope['skill_by_id'](SimpleNamespace(), skill_id)


def run():
    count = 0
    original = {k: tuple(s['id'] for s in v) for k, v in CLASS_SKILLS.items()}
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE quests (quest_id TEXT, status TEXT)")
    db = SimpleNamespace(conn=conn)
    world = SimpleNamespace(mobs={}, _last_refresh_at=0.0,
                            _register_runtime_spawn=lambda *args:None)
    server = SimpleNamespace(world=world, sessions=[])
    svc = LiveContentV1204(db)
    assert len(CLASS_SKILLS) == 22;count+=1
    assert sum(map(len, CLASS_SKILLS.values())) == 5461;count+=1
    assert svc.validate(svc.active);count+=1
    skill='live_soulbound_ostrze'
    base = svc.stage_new_skill(skill,'Wojownik','Ostrze Zorzy','damage',40,0,1.5,'strength','Pierwszy testowy atak.')
    assert '1 nowych skilli' in base;count+=1
    assert skill not in str(CLASS_SKILLS['Wojownik']);count+=1
    assert skill in find_catalog(svc,'skill','Ostrze Zorzy');count+=1
    assert 'mult' in fields_for(svc,'skill',skill);count+=1
    assert '1.5' in describe_current_edit(svc,'skill',skill,'mult');count+=1
    before=copy.deepcopy(svc.draft)
    assert '1.5' in describe_current_edit(svc,'skill',skill,'mult')
    assert svc.draft == before and svc.revision == 0;count+=1
    for kwargs in (
       ('live_other_skill','Wojownik','Ostrze Zorzy','damage',40,0,1.5,'strength','opis'),
       ('invalid','Wojownik','Miecz','damage',40,0,1.5,'strength','opis'),
       ('live_other_skill','Nie ma','Miecz','damage',40,0,1.5,'strength','opis'),
       ('live_other_skill','Wojownik','Inna Moc','python',40,0,1.5,'strength','opis'),
       ('live_other_skill','Wojownik','Inna Moc','damage',801,0,1.5,'strength','opis'),
       ('live_other_skill','Wojownik','Inna Moc','damage',1,0,31.0,'strength','opis'),
       ('live_other_skill','Wojownik','Inna Moc','damage',1,0,1.5,'__import__','opis'),
    ):
        try:svc.stage_new_skill(*kwargs)
        except ValueError:count+=1
        else:raise AssertionError('Accepted dangerous skill spec')
    assert svc.draft==before;count+=1
    svc.stage_edit('skill',skill,'mult','2.25');count+=1
    assert '2.25' in describe_current_edit(svc,'skill',skill,'mult');count+=1
    assert svc.revision==0 and skill not in [s['id'] for s in CLASS_SKILLS['Wojownik']];count+=1
    with TemporaryDirectory() as td:
        pkg=Path(td)/'skill.json'
        svc.export(pkg);count+=1
        loaded=json.loads(pkg.read_text('utf8'))
        assert loaded['skills'][skill]['mult']==2.25;count+=1
    baseline = copy.deepcopy(svc.active)
    svc.apply(server,'owner');count+=1
    skill_record=next(s for s in CLASS_SKILLS['Wojownik'] if s['id']==skill)
    assert skill_record['mult']==2.25 and skill_record['kind']=='damage';count+=1
    assert _lookup_for_test(skill) == skill_record;count+=1
    assert len(CLASS_SKILLS['Wojownik'])==len(original['Wojownik'])+1;count+=1
    assert 'nowe skille' in news_summary(baseline,svc.active,revision=svc.revision);count+=1
    assert svc.revision==1 and svc.active['skills'][skill]['mult']==2.25;count+=1
    # Simulate restart of OLC service with the same SQLite database.
    svc._remove(world)
    reopened=LiveContentV1204(db);count+=1
    assert next(s for s in CLASS_SKILLS['Wojownik'] if s['id']==skill)['mult']==2.25;count+=1
    assert reopened.revision==1;count+=1
    reopened.stage_new_skill('live_drugi_ostrze','Mag','Ognista Próba','aoe_damage',1,10,1.75,'intelligence','Magiczny atak grupowy')
    assert '2 nowych skilli' in reopened.validate(reopened.draft);count+=1
    reopened.apply(server,'owner');count+=1
    assert _lookup_for_test('live_drugi_ostrze')['kind']=='aoe_damage';count+=1
    try:reopened.apply(server,'owner',rollback=True)
    except ValueError as exc:
        assert 'skills' in str(exc);count+=1
    else:raise AssertionError('Published skill removed despite possible player progress')
    assert len(CLASS_SKILLS['Mag'])==len(original['Mag'])+1;count+=1
    reopened.stage_edit('skill',skill,'mult','3.0');count+=1
    reopened.apply(server,'owner');count+=1
    assert _lookup_for_test(skill)['mult']==3.0;count+=1
    assert reopened.apply(server,'owner',rollback=True).startswith('Aktywowano');count+=1
    assert _lookup_for_test(skill)['mult']==2.25;count+=1
    # Verify a blocked hot publish if fights exist.
    reopened.stage_edit('skill',skill,'mult','4.0')
    world.mobs['x']=SimpleNamespace(engaged_by='p',aoe_engaged_by=set(),template_id='temple_rat',home_room_id='market',room_id='market')
    try:reopened.apply(server,'owner')
    except ValueError:count+=1
    else:raise AssertionError('Skills changed during battle')
    world.mobs.clear()
    reopened._remove(world)
    assert all(tuple(s['id'] for s in CLASS_SKILLS[k]) == old for k,old in original.items());count+=1
    conn.close()
    return count

if __name__=='__main__':
    print('V12.00.13 OLC NEW SKILLS:',run(),'checks PASS')
