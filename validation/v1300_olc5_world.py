# -*- coding: utf-8 -*-
"""v13.00.0: real OLC 5.0 catalog / SQLite / rollback and NVDA smoke tests.

No production databases, no real players, no synthetic change to EXP maths.
"""
import copy
import json
import sqlite3
import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace

from core.classes_skills import CLASS_SKILLS
from data.items import ITEMS
from data.quests import QUESTS
from data.crafting_recipes import CRAFT_RECIPES
from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc4_new_skills import new_skill_definition
from systems.live_olc5_audit import live_audit_summary
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.encounter_brain_v1230 import tactical_element_v1230


def run():
    checks=0
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    db=SimpleNamespace(conn=conn)
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(world=world,sessions=[])
    previous={k:tuple(row['id'] for row in rows) for k,rows in CLASS_SKILLS.items()}
    old_boss=copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    svc=LiveContentV1204(db)
    reopened=None
    try:
        assert 'Bez zapisu SQLite' in live_audit_summary(svc);checks+=1
        assert svc.revision==0 and svc.draft==svc.active;checks+=1
        for kind, effect, class_name, expected_key in (
            ('drain',.25,'Mag','drain_pct'),
            ('regen',None,'Druid',None),
            ('evade',None,'Łotrzyk','evade'),
        ):
            sid='live_v1300_'+kind
            svc.stage_new_skill(sid,class_name,'Umiejętność V13 '+kind,kind,40,10,1.5,'wisdom','Test działania',effect)
            meta=svc.draft['skills'][sid]
            definition=new_skill_definition(sid,meta)
            assert definition['kind']==kind;checks+=1
            assert definition['cooldown']==0;checks+=1
            if expected_key:
                assert definition[expected_key]==(.25 if kind=='drain' else True);checks+=1
            else:
                assert 'effect' not in meta;checks+=1
        for kind,bad in (('drain',0),('drain',1.1),('drain',float('nan')),
                         ('regen',.1),('evade',100)):
            draft=copy.deepcopy(svc.draft)
            try:svc.stage_new_skill('live_invalid_kinds','Mag','Niebezpieczny '+kind,kind,40,10,1.5,'wisdom','Test',bad)
            except ValueError:checks+=1
            else:raise AssertionError('Invalid effect accepted')
            assert svc.draft==draft;checks+=1
        svc.stage_new_jewelry('live_v13_ring','Pierścień Świata','ring','constitution',77,65,3300,'Test biżuterii');checks+=1
        assert svc.draft['items']['live_v13_ring']['stats']=={'constitution':77};checks+=1
        assert '77' in describe_current_edit(svc,'item','live_v13_ring','stats');checks+=1
        svc.stage_edit('item','live_v13_ring','stats',json.dumps({'strength':94}));checks+=1
        assert svc.draft['item_edits']['live_v13_ring']['stats']=={'strength':94};checks+=1
        for slot,stat,amount in (('weapon','strength',3),('ring','hacking',3),('ring','wisdom',0)):
            draft=copy.deepcopy(svc.draft)
            try:svc.stage_new_jewelry('live_bad_ring','Błędny','%s'%slot,stat,amount,5,5,'Test')
            except ValueError:checks+=1
            else:raise AssertionError('Illegal jewelry accepted')
            assert svc.draft==draft;checks+=1
        svc.stage_copy_recipe('live_v13_plank','oak_plank','Deska Treningowa');checks+=1
        assert svc.draft['recipes']['live_v13_plank']['profession']=='Drwalstwo';checks+=1
        assert svc.draft['recipes']['live_v13_plank']['min_profession_level']==1;checks+=1
        draft=copy.deepcopy(svc.draft)
        try:svc.stage_copy_recipe('live_duplicate_recipe','does_not_exist','Test')
        except ValueError:checks+=1
        else:raise AssertionError('Unknown recipe accepted')
        assert svc.draft==draft;checks+=1
        svc.stage_new_quest('live_v13_quest_one','Pierwszy etap','Rybak Borys','kill','temple_rat',2,50,'Pierwszy rozdział');checks+=1
        svc.stage_new_quest('live_v13_quest_two','Drugi etap','Rybak Borys','kill','temple_rat',3,75,'Drugi rozdział');checks+=1
        svc.stage_quest_chain('live_v13_quest_two','live_v13_quest_one');checks+=1
        assert svc.draft['quest_edits']['live_v13_quest_two']['requires_quest']=='live_v13_quest_one';checks+=1
        draft=copy.deepcopy(svc.draft)
        try:svc.stage_quest_chain('live_v13_quest_one','live_v13_quest_two')
        except ValueError:checks+=1
        else:raise AssertionError('Cyclic quest chain accepted')
        assert svc.draft==draft;checks+=1
        svc.stage_edit('mob','bandit_captain','olc_boss_tactic_element','fire');checks+=1
        assert svc.draft['mob_edits']['bandit_captain']['olc_boss_tactic_element']=='fire';checks+=1
        svc.stage_edit('mob','bandit_captain','olc_boss_tactic_interval','6');checks+=1
        assert svc.draft['mob_edits']['bandit_captain']['olc_boss_tactic_interval']==6;checks+=1
        for mid,value in [('temple_rat','fire'),('bandit_captain','python')]:
            draft=copy.deepcopy(svc.draft)
            try:svc.stage_edit('mob',mid,'olc_boss_tactic_element',value)
            except ValueError:checks+=1
            else:raise AssertionError('Unprotected AI edit accepted')
            assert svc.draft==draft;checks+=1
        assert 'OLC AUDYT' in live_audit_summary(svc) and 'Walidacja PASS' in live_audit_summary(svc);checks+=1
        assert svc.revision==0;checks+=1
        original=copy.deepcopy(svc.active)
        svc.apply(server,'test_admin');checks+=1
        assert svc.revision==1 and svc.active != original;checks+=1
        assert ITEMS['live_v13_ring']['stats']=={'strength':94};checks+=1
        assert QUESTS['live_v13_quest_two']['requires_quest']=='live_v13_quest_one';checks+=1
        assert CRAFT_RECIPES['live_v13_plank']['profession']=='Drwalstwo';checks+=1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_tactic_element']=='fire';checks+=1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_tactic_interval']==6;checks+=1
        for kind in ('drain','regen','evade'):
            assert any(row['id']=='live_v1300_'+kind for rows in CLASS_SKILLS.values() for row in rows);checks+=1
        mob=SimpleNamespace(alive=True,engaged_by='player1',combat_turn=6,template_id='bandit_captain')
        profile=tactical_element_v1230(mob,MOB_TEMPLATES['bandit_captain']);
        assert profile is None or profile.get('element')=='fire';checks+=1
        svc._remove(world)
        reopened=LiveContentV1204(db);checks+=1
        assert reopened.revision==1;checks+=1
        assert reopened.active['items']['live_v13_ring']['required_level']==65;checks+=1
        assert reopened.active['recipes']['live_v13_plank']['quantity']==1;checks+=1
        assert reopened.active['quest_edits']['live_v13_quest_two']['requires_quest']=='live_v13_quest_one';checks+=1
        # New published IDs cannot be deleted by undo. Existing spell learning and
        # quest progression may reference their durable IDs.
        try:reopened.apply(server,'admin',rollback=True)
        except ValueError:checks+=1
        else:raise AssertionError('Unsafe deletion of published ID')
    finally:
        if svc._undo:svc._remove(world)
        if reopened and reopened._undo:reopened._remove(world)
        MOB_TEMPLATES['bandit_captain']=old_boss
        for key,ids in previous.items():
            CLASS_SKILLS[key][:]=[row for row in CLASS_SKILLS[key] if row['id'] in ids]
        conn.close()
    return checks + test_admin_commands()


def test_admin_commands():
    """Real command parser, one NEWS after successful apply."""
    source=(Path(__file__).resolve().parents[1]/'player/session_mixins/admin_tools.py').read_text('utf8')
    tree=ast.parse(source)
    admin=next(c for c in tree.body if isinstance(c,ast.ClassDef) and any(getattr(m,'name',None)=='admin_live_v1204' for m in c.body))
    method=next(m for m in admin.body if getattr(m,'name',None)=='admin_live_v1204')
    unit=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Mini',bases=[],keywords=[],body=[method],decorator_list=[])],type_ignores=[]))
    env={}
    exec(compile(unit,'<olc5-admin>','exec'),env)
    mini=env['Mini']()
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    db=SimpleNamespace(conn=conn,account_name=lambda *x:'admin',record_admin_action_v1224=lambda *x:None)
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(world=world,sessions=[],db=db)
    svc=LiveContentV1204(db);server.live_content_v1204=svc
    mini.server=server;mini.master_account_id=1;mini.is_admin=lambda:True
    messages=[];news=[]
    async def send(msg):messages.append(msg)
    async def send_news(msg):news.append(msg)
    mini.send=send;mini.news_channel_v1204=send_news
    async def sequence():
        checks=0
        for cmd in (
            'nowabizuteria live_v13_admin_ring | Złoty Pierścień Testowy | ring | strength | 11 | 10 | 150 | Opis',
            'kopiujrecepture live_v13_admin_plank | oak_plank | Deska Admina',
            'nowyquest live_v13_admin_q1 | Etap pierwszy | Rybak Borys | kill | temple_rat | 1 | 10 | Początek',
            'nowyquest live_v13_admin_q2 | Etap drugi | Rybak Borys | kill | temple_rat | 2 | 20 | Koniec',
            'lancuch live_v13_admin_q2 live_v13_admin_q1',
        ):
            await mini.admin_live_v1204(cmd)
            assert 'przygotowano' in messages[-1],(cmd,messages[-1]);checks+=1
        await mini.admin_live_v1204('audyt')
        assert 'Walidacja PASS' in messages[-1] and not news;checks+=1
        await mini.admin_live_v1204('sprawdz')
        assert 'Przygotowane' in messages[-1] and not news;checks+=1
        await mini.admin_live_v1204('aktywuj POTWIERDZAM')
        assert 'Aktywowano' in messages[-1] and svc.revision==1;checks+=1
        assert len(news)==1;checks+=1
        return checks
    try:return asyncio.run(sequence())
    finally:
        if svc._undo:svc._remove(world)
        conn.close()

if __name__=='__main__':
    print('V13.00.0 OLC 5.0:',run(),'checks PASS')
