# -*- coding: utf-8 -*-
"""v16.00.0 bounded batch-edit safety, actual SQLite and catalog regression."""
import copy
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch
import systems.live_olc13_batch as batch_editor

from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc13_batch import preview, stage, _selection, MAX_BATCH
from data.quests import QUESTS
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from core.classes_skills import CLASS_SKILLS


def run():
    checks=0
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    service=LiveContentV1204(SimpleNamespace(conn=conn))
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *args: None)
    server=SimpleNamespace(world=world,sessions=[])
    originals={'quest':copy.deepcopy(QUESTS['bandit_patrol']),
               'mob':copy.deepcopy(MOB_TEMPLATES['bandit_captain']),
               'items':{i:copy.deepcopy(ITEMS[i]) for i in ('iron_ore','iron_ingot') if i in ITEMS}}
    try:
        original_draft=copy.deepcopy(service.draft)
        report=preview(service,'quest','bandit','reward_xp')
        assert 'bandit_patrol' in report and 'Niczego nie zapisano' in report;checks+=1
        assert service.draft==original_draft;checks+=1
        # The broad 'bandit' prefix grows with new worlds and can exceed
        # MAX_BATCH. Select the stable captain family without weakening
        # the live editor's safety limit.
        mob_prefix='bandit_cap'
        section,catalog,keys=_selection('mob',mob_prefix,'silver')
        assert section=='mob_edits' and 'bandit_captain' in keys and 1 <= len(keys) <= MAX_BATCH;checks+=1
        # Verify that broad selections are still REJECTED atomically.
        with patch.object(batch_editor, '_catalogue', return_value={
                f'bandit_cap_{n:03}': {'silver': 1}
                for n in range(MAX_BATCH+1)}):
            try: _selection('mob',mob_prefix,'silver')
            except ValueError as error:
                assert 'maks.' in str(error);checks+=1
            else: raise AssertionError('Oversized mob batch was accepted')
        bad_inputs=[('quest','ban','kind'),('quest','bandit','needed'),
                    ('surowiec','iron','foo'),('mob','bandit','damage'),
                    ('skill','warrior','aliases'),('quest','b*','reward_xp'),
                    ('quest','ba','reward_xp'),('mob','unknown_xyz','silver'),
                    ('mob','bandit','silver')]
        for cat,prefix,field in bad_inputs[:-1]:
            try: preview(service,cat,prefix,field)
            except ValueError:checks+=1
            else: raise AssertionError(f'Bad preview accepted: {cat} {prefix} {field}')
        try: stage(service,'mob','bandit','silver','-1')
        except ValueError: checks+=1
        else: raise AssertionError('Negative mob money accepted')
        assert service.draft==original_draft;checks+=1
        assert stage(service,'quest','bandit','reward_xp','50000').startswith('OLC:');checks+=1
        assert service.draft['quest_edits']['bandit_patrol']['olc_reward_xp']==50000;checks+=1
        assert QUESTS['bandit_patrol']==originals['quest'];checks+=1
        assert '50000' in preview(service,'quest','bandit','reward_xp');checks+=1
        stage(service,'surowiec','iron','prof_scale','65')
        assert service.draft['resource_edits']['iron_ore']['prof_scale']==65;checks+=1
        assert service.draft['resource_edits']['iron_ore']['prof_mode']=='percent';checks+=1
        stage(service,'surowiec','iron','tool_fixed','0')
        assert service.draft['resource_edits']['iron_ore']['tool_fixed']==0;checks+=1
        assert service.draft['resource_edits']['iron_ore']['tool_mode']=='manual';checks+=1
        stage(service,'mob',mob_prefix,'silver','123')
        assert service.draft['mob_edits']['bandit_captain']['silver']==123;checks+=1
        assert MOB_TEMPLATES['bandit_captain']==originals['mob'];checks+=1
        # Batch skills: choose a real skill whose existing field can be edited.
        all_skills=[r for rows in CLASS_SKILLS.values() for r in rows]
        skill=next(r for r in all_skills if r.get('mana') is not None and len(r['id'])>=3)
        stage(service,'skill',skill['id'],'mana','1')
        assert service.draft['skill_edits'][skill['id']]['mana']==1;checks+=1
        snapshot=copy.deepcopy(service.draft)
        try:stage(service,'skill',skill['id'],'mult','NaN')
        except ValueError:checks+=1
        else:raise AssertionError('NaN accepted in skill batch')
        assert service.draft==snapshot;checks+=1
        assert 'Aktywowano' in service.apply(server,'v1600_validation');checks+=1
        assert QUESTS['bandit_patrol']['olc_reward_xp']==50000;checks+=1
        assert MOB_TEMPLATES['bandit_captain']['silver']==123;checks+=1
        assert service.active['resource_edits']['iron_ore']['prof_scale']==65;checks+=1
        assert conn.execute('SELECT revision FROM live_content_v1204').fetchone()[0]==1;checks+=1
        service._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn))
        assert reopened.revision==1 and reopened.active['mob_edits']['bandit_captain']['silver']==123;checks+=1
        old=copy.deepcopy(reopened.draft)
        # Reset one side without erasing the other.
        stage(reopened,'surowiec','iron','prof_mode','auto')
        assert 'prof_scale' not in reopened.draft['resource_edits']['iron_ore'];checks+=1
        assert reopened.draft['resource_edits']['iron_ore']['tool_fixed']==0;checks+=1
        stage(reopened,'quest','bandit','reward_xp','auto')
        assert 'olc_reward_xp' not in reopened.draft['quest_edits'].get('bandit_patrol',{});checks+=1
        stage(reopened,'mob',mob_prefix,'silver','auto')
        assert 'silver' not in reopened.draft['mob_edits'].get('bandit_captain',{});checks+=1
        assert 'Aktywowano' in reopened.apply(server,'v1600_validation');checks+=1
        assert QUESTS['bandit_patrol']==originals['quest'];checks+=1
        assert MOB_TEMPLATES['bandit_captain']==originals['mob'];checks+=1
        reopened._remove(world)
        # Existing fields only: never modify a skill lacking the field.
        no_mana=next((s for s in all_skills if 'mana' not in s),None)
        if no_mana:
            fresh=LiveContentV1204(SimpleNamespace(conn=conn))
            try:
                prior=copy.deepcopy(fresh.draft)
                try:stage(fresh,'skill',no_mana['id'],'mana','10')
                except ValueError:checks+=1
                else:raise AssertionError('Invented a new mechanic for existing skill')
                assert fresh.draft==prior;checks+=1
            finally:fresh._remove(world)
    finally:
        service._remove(world)
        assert QUESTS['bandit_patrol']==originals['quest']
        assert MOB_TEMPLATES['bandit_captain']==originals['mob']
        conn.close()
    return checks

if __name__=='__main__':
    print('V16.00.0 OLC MASS EDIT:',run(),'checks PASS')
