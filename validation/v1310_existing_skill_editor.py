# -*- coding: utf-8 -*-
"""v13.10.0 - actual OLC publication/undo/SQLite tests for old class skills."""
import copy
import json
import sqlite3
from types import SimpleNamespace
from core.classes_skills import CLASS_SKILLS
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.live_olc4_browse import fields_for
from systems.live_olc6_skill_editor import parse_existing_skill_field


def run():
    n = 0
    original = next(row.copy() for row in CLASS_SKILLS['Wojownik'] if row['id']=='warrior_power_slash')
    amount = sum(len(group) for group in CLASS_SKILLS.values())
    assert amount == 5461;n+=1
    conn = sqlite3.connect(':memory:');conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT,status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.0,_register_runtime_spawn=lambda *_:None)
    server=SimpleNamespace(world=world,sessions=[])
    svc=LiveContentV1204(SimpleNamespace(conn=conn))
    sid=original['id']
    try:
        for field,value in (('name','Nowe Ostrze Wojownika'),('desc','Ulepszony opis.'),
                            ('unlock','80'),('mana','150'),('mult','87.5'),
                            ('scale','willpower'),('kind','aoe_damage')):
            svc.stage_edit('skill',sid,field,value);n+=1
        assert 'name' in fields_for(svc,'skill',sid);n+=1
        assert 'Nowe Ostrze Wojownika' in describe_current_edit(svc,'skill',sid,'name');n+=1
        assert '87.5' in describe_current_edit(svc,'skill',sid,'mult');n+=1
        assert any(a.casefold() == original['name'].casefold() or a == 'potezne ciecie' for a in svc.draft['skill_edits'].get(sid, {}).get('aliases', original['aliases']));n+=1
        assert original['id']==sid;n+=1
        try:svc.stage_edit('skill',sid,'id','evil')
        except ValueError:n+=1
        else:raise AssertionError('Editing immutable skill id allowed')
        try:svc.stage_edit('skill',sid,'mult','inf')
        except ValueError:n+=1
        else:raise AssertionError('Infinite multiplier allowed')
        try:svc.stage_edit('skill',sid,'kind','heal')
        except ValueError:n+=1
        else:raise AssertionError('Dangerous change of target kind allowed')
        try:svc.stage_edit('skill',sid,'aliases','["Healing Wind"]')
        except ValueError:n+=1
        else:raise AssertionError('Lost historical aliases allowed')
        try:svc.stage_edit('skill',sid,'name','Healing Wind')
        except ValueError:n+=1
        else:raise AssertionError('Another skill name allowed')
        assert svc.active['skill_edits']=={};n+=1
        before=copy.deepcopy(svc.active)
        svc.apply(server,'owner');n+=1
        changed=next(row for row in CLASS_SKILLS['Wojownik'] if row['id']==sid)
        assert changed['name']=='Nowe Ostrze Wojownika';n+=1
        assert changed['mult']==87.5 and changed['kind']=='aoe_damage';n+=1
        assert 'potezne ciecie' in changed['aliases'];n+=1
        assert sum(len(group) for group in CLASS_SKILLS.values())==amount;n+=1
        assert svc.revision==1;n+=1
        assert svc.active['skill_edits'][sid]['name']=='Nowe Ostrze Wojownika';n+=1
        svc._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn));n+=1
        assert next(row for row in CLASS_SKILLS['Wojownik'] if row['id']==sid)['unlock']==80;n+=1
        reopened.stage_edit('skill',sid,'mana','auto');n+=1
        assert 'mana' not in reopened.draft['skill_edits'][sid];n+=1
        reopened.stage_edit('skill',sid,'mult','4.5')
        reopened.apply(server,'owner');n+=1
        assert next(row for row in CLASS_SKILLS['Wojownik'] if row['id']==sid)['mult']==4.5;n+=1
        reopened.apply(server,'owner',rollback=True);n+=1
        assert next(row for row in CLASS_SKILLS['Wojownik'] if row['id']==sid)['mult']==87.5;n+=1
        reopened._remove(world)
        assert next(row for row in CLASS_SKILLS['Wojownik'] if row['id']==sid)==original;n+=1
    finally:
        svc._remove(world)
        conn.close()
    # Schema compatibility: not all 5461 skills have every effect field.
    for row in CLASS_SKILLS['Wojownik'][:30]:
        try:parse_existing_skill_field(row,'heal_pct','0.2')
        except ValueError:n+=1
        else:
            assert 'heal_pct' in row
    return n

if __name__=='__main__':
    print('V13.10.0 EXISTING SKILLS OLC:',run(),'checks PASS')
