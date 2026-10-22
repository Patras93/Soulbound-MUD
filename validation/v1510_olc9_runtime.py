# -*- coding: utf-8 -*-
"""V15.10 OLC: runtime-backed safe additions, isolated SQLite only."""
import copy
import sqlite3
from types import SimpleNamespace
from systems.live_content_v1204 import LiveContentV1204
from core.classes_skills import CLASS_SKILLS
from data.mobs import MOB_TEMPLATES
from data.crafting_recipes import CRAFT_RECIPES
from systems.encounter_brain_v1230 import tactical_element_v1230


def run():
    checks = 0
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.0,_register_runtime_spawn=lambda *args:None)
    server=SimpleNamespace(world=world,sessions=[])
    svc=LiveContentV1204(SimpleNamespace(conn=conn))
    old_boss=copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    baseline=sum(len(v) for v in CLASS_SKILLS.values())
    old_recipes=set(CRAFT_RECIPES)
    try:
        svc.stage_new_skill('live_v1510_cold_test', 'Mag', 'Test OLC9 Szron',
                'damage',40,10,1.5,'intelligence','Testowy czar',element='ice',cooldown=90)
        assert svc.draft['skills']['live_v1510_cold_test']['cooldown']==90;checks+=1
        from systems.live_olc4_new_skills import new_skill_definition
        sk=new_skill_definition('live_v1510_cold_test',svc.draft['skills']['live_v1510_cold_test'])
        assert sk['cooldown']==90 and sk['mechanic_cooldown'] is True;checks+=1
        svc.stage_edit('skill','live_v1510_cold_test','cooldown','35')
        assert svc.draft['skills']['live_v1510_cold_test']['cooldown']==35;checks+=1
        svc.stage_edit('skill','live_v1510_cold_test','element','fire')
        assert svc.draft['skills']['live_v1510_cold_test']['element']=='fire';checks+=1
        svc.stage_edit('skill','live_v1510_cold_test','element','auto')
        assert 'element' not in svc.draft['skills']['live_v1510_cold_test'];checks+=1
        svc.stage_edit('skill','live_v1510_cold_test','element','ice')
        for field,value in [('cooldown','-1'),('cooldown','3601'),('element','unobtanium')]:
            old=copy.deepcopy(svc.draft)
            try: svc.stage_edit('skill','live_v1510_cold_test',field,value)
            except ValueError:checks+=1
            else:raise AssertionError(f'invalid {field}={value} accepted')
            assert old == svc.draft;checks+=1
        svc.stage_edit('mob','bandit_captain','olc_boss_element_cycle','["fire","ice","lightning"]');checks+=1
        for bad in ('["fire","hacks"]','[]','{"x":1}'):
            before=copy.deepcopy(svc.draft)
            try:svc.stage_edit('mob','bandit_captain','olc_boss_element_cycle',bad)
            except ValueError:checks+=1
            else:raise AssertionError('invalid boss cycle accepted')
            assert before==svc.draft;checks+=1
        candidate=next((r for r in CRAFT_RECIPES.values() if r.get('profession')=='Drwalstwo' and r.get('tool_item_id')=='saw'),None)
        assert candidate is not None;checks+=1
        svc.stage_new_recipe('live_v1510_plank','Nowa deska OLC','Drwalstwo','saw','oak_plank',
                             '{"oak_log":3}',candidate['stations'][0],25,2,'Obrob deski pilą')
        assert svc.draft['recipes']['live_v1510_plank']['tool_type']==candidate['tool_type'];checks+=1
        for field in ('nonexistent_tool','nonexistent_profession'):
            before=copy.deepcopy(svc.draft)
            try:
                svc.stage_new_recipe('live_v1510_invalid','Błąd','Drwalstwo' if field=='nonexistent_tool' else 'Fikcyjna',
                                     field if field=='nonexistent_tool' else 'saw','oak_plank',
                                     '{"oak_log":3}',candidate['stations'][0],25,2,'Błąd')
            except ValueError:checks+=1
            else:raise AssertionError('Unsupported profession/tool accepted')
            assert svc.draft==before;checks+=1
        previous_draft=copy.deepcopy(svc.draft)
        from systems.live_olc4_diff import describe_diff
        assert describe_diff(svc.active,svc.draft);checks+=1
        assert svc.draft==previous_draft;checks+=1
        assert 'live_v1510_plank' not in CRAFT_RECIPES;checks+=1
        assert sum(len(v) for v in CLASS_SKILLS.values())==baseline;checks+=1
        svc.apply(server,'admin_olc9');checks+=1
        assert svc.revision==1;checks+=1
        assert 'live_v1510_plank' in CRAFT_RECIPES;checks+=1
        assert sum(len(v) for v in CLASS_SKILLS.values())==baseline+1;checks+=1
        found=next(s for s in CLASS_SKILLS['Mag'] if s['id']=='live_v1510_cold_test')
        assert found['cooldown']==35 and found['mechanic_cooldown'] is True;checks+=1
        from systems.elemental_combat import skill_element_v11339
        assert skill_element_v11339('Mag','Test OLC9 Szron')=='ice';checks+=1
        # Isolate the OLC mechanic from any *authored* elemental affinity of
        # bandit_captain: authored combat may legitimately override OLC AI.
        synthetic_boss = {'boss':True, 'name':'Boss testowy',
                          'olc_boss_tactic_interval':4,
                          'olc_boss_element_cycle':['fire','ice','lightning']}
        mob=SimpleNamespace(template_id='live_v1510_test_boss',alive=True,
                            engaged_by={'x'},combat_turn=4,hp=100)
        for turn, expected in [(4,'fire'),(8,'ice'),(12,'lightning'),(16,'fire')]:
            mob.combat_turn=turn
            observed=tactical_element_v1230(mob,synthetic_boss)
            assert observed and observed['element']==expected,(turn,observed);checks+=1
        # OLC active state reload simulated through SQLite without restart data loss
        svc._remove(world)
        svc2=LiveContentV1204(SimpleNamespace(conn=conn));checks+=1
        assert svc2.revision==1 and 'live_v1510_plank' in svc2.active['recipes'];checks+=1
        svc2._remove(world)
        svc._install(svc.active,world)
        svc.stage_edit('mob','bandit_captain','olc_boss_element_cycle','auto')
        assert 'olc_boss_element_cycle' not in svc.draft['mob_edits'].get('bandit_captain',{});checks+=1
        svc.apply(server,'admin_olc9');checks+=1
        assert 'olc_boss_element_cycle' not in MOB_TEMPLATES['bandit_captain'];checks+=1
    finally:
        svc._remove(world)
        assert MOB_TEMPLATES['bandit_captain']==old_boss
        assert sum(len(v) for v in CLASS_SKILLS.values())==baseline
        from systems.elemental_combat import OLC_SKILL_ELEMENTS_V1500
        assert ('Mag','Test OLC9 Szron') not in OLC_SKILL_ELEMENTS_V1500
        # Published recipes cannot be removed via rollback, but temporary tests
        # must remove changes from process-global registry on cleanup.
        assert set(CRAFT_RECIPES)==old_recipes
        conn.close()
    return checks

if __name__=='__main__':
    print('OLC 9.0:',run(),'PASS')
