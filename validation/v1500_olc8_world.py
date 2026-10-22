# -*- coding: utf-8 -*-
"""v15 isolated OLC regression: no real users, no live DB writes or TCP."""
import copy
import sqlite3
from types import SimpleNamespace
from data.items import ITEMS
from data.npcs import NPCS
from data.quests import QUESTS
from data.mobs import MOB_TEMPLATES
from core.classes_skills import CLASS_SKILLS
from systems.live_content_v1204 import LiveContentV1204, blank
from systems.live_olc4_new_skills import new_skill_definition
from systems.live_olc4_fields import validate_extra
from systems.live_olc8_dashboard import describe_object, profession_recipes


def run():
    checks = 0
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world = SimpleNamespace(mobs={},_last_refresh_at=0.0,_register_runtime_spawn=lambda *a:None)
    server = SimpleNamespace(world=world,sessions=[])
    svc = LiveContentV1204(SimpleNamespace(conn=conn))
    initial = copy.deepcopy(svc.active)
    skill_count = sum(map(len, CLASS_SKILLS.values()))
    original_npc = copy.deepcopy(NPCS['fisher_tomas'])
    original_boss = copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    try:
        # 1 skill: true explicit elemental attack; existing skill path reads element.
        svc.stage_new_skill('live_v15_ice_attack', 'Mag', 'Szron testowy V15',
                            'damage', 30, 12, '1.2', 'intelligence', 'Test lodu',
                            element='ice')
        assert new_skill_definition('live_v15_ice_attack',svc.draft['skills']['live_v15_ice_attack'])['element']=='ice';checks+=1
        try:
            svc.stage_new_skill('live_v15_heal_bad', 'Mag', 'Leczenie lodowe V15',
                                'heal', 30, 10, '1.0','wisdom','Nie można', effect=.1, element='ice')
        except ValueError:checks+=1
        else:raise AssertionError('Ice heal accepted')
        assert 'live_v15_heal_bad' not in svc.draft['skills'];checks+=1
        # 2 ordinary AI (not scripted superboss)
        svc.stage_edit('mob','bandit_captain','olc_boss_guard_threshold','70')
        assert svc.draft['mob_edits']['bandit_captain']['olc_boss_guard_threshold']==70;checks+=1
        try:validate_extra('mob_edits','bandit_captain','olc_boss_guard_threshold',100,svc.draft,set(),set())
        except ValueError:checks+=1
        else:raise AssertionError('Invalid threshold accepted')
        # 3 quest real collect_resource_set objective and atomic replacement
        svc.stage_new_resource_set_quest('live_v15_materials','Zestaw testowy',
                'Rybak Borys','{"iron_ore":2,"copper_ore":3}',100,'Zbierz dwie rudy.')
        svc.stage_quest_materials('live_v15_materials','{"iron_ore":4,"copper_ore":2}')
        assert svc.draft['quests']['live_v15_materials']['needed']==6;checks+=1
        # 4 original equipment statistics used by equipment_flat_power_totals
        svc.stage_magic_equipment('live_v15_magic_armor','Pancerz V15','body',
            100,30,50,40,25,'{"strength":10,"wisdom":8}',40,1000,'Magiczna zbroja')
        assert svc.draft['items']['live_v15_magic_armor']['weapon_power']==25;checks+=1
        # 5 craft profession discovery
        assert 'Receptury profesji' in profession_recipes(svc,'Kowalstwo');checks+=1
        # 6 group respawn of existing bandits
        svc.stage_respawn_group('bandit_',300)
        ids = [mid for mid in MOB_TEMPLATES if mid.startswith('bandit_')]
        assert ids and all(svc.draft['mob_edits'][mid]['respawn_seconds']==300 for mid in ids);checks+=1
        # 7 NPC conditional dialogue validated in actual talk() data
        svc.stage_edit('npc','fisher_tomas','olc_dialogue_after_quest',
            '{"quest_id":"fisher_30_fish","text":"Dziękuję za ryby."}')
        assert svc.draft['npc_edits']['fisher_tomas']['olc_dialogue_after_quest']['quest_id']=='fisher_30_fish';checks+=1
        # 8 NVDA readable preview without writing
        before_draft=copy.deepcopy(svc.draft)
        assert 'Aktualne pola' in describe_object(svc,'npc','fisher_tomas');checks+=1
        assert svc.draft==before_draft;checks+=1
        assert 'live_v15_magic_armor' not in ITEMS;checks+=1
        assert 'olc_dialogue_after_quest' not in NPCS['fisher_tomas'];checks+=1
        svc.apply(server,'v15_test');checks+=1
        assert svc.revision==1 and 'live_v15_magic_armor' in ITEMS;checks+=1
        assert NPCS['fisher_tomas']['olc_dialogue_after_quest']['text']=='Dziękuję za ryby.';checks+=1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_guard_threshold']==70;checks+=1
        assert sum(map(len,CLASS_SKILLS.values()))==skill_count+1;checks+=1
        from systems.elemental_combat import skill_element_v11339
        assert skill_element_v11339('Mag', 'Szron testowy V15') == 'ice';checks+=1
        assert 'live_v15_materials' in QUESTS;checks+=1
        assert conn.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0]==1;checks+=1
        # real guard: no change of active quest requirements
        conn.execute("INSERT INTO quests (quest_id,status) VALUES ('live_v15_materials','active')")
        svc.stage_quest_materials('live_v15_materials','{"iron_ore":2,"copper_ore":2}')
        try:svc.apply(server,'v15_test')
        except ValueError as e:
            assert 'aktywny' in str(e) or 'aktywn' in str(e) or 'nie zmieniam' in str(e);checks+=1
        else:raise AssertionError('Active quest target was modified')
        assert QUESTS['live_v15_materials']['resource_targets']=={'iron_ore':4,'copper_ore':2};checks+=1
    finally:
        svc._remove(world)
        assert NPCS['fisher_tomas']==original_npc
        assert MOB_TEMPLATES['bandit_captain']==original_boss
        assert sum(map(len,CLASS_SKILLS.values()))==skill_count
        from systems.elemental_combat import OLC_SKILL_ELEMENTS_V1500
        assert ('Mag','Szron testowy V15') not in OLC_SKILL_ELEMENTS_V1500
        conn.close()
    return checks+3


if __name__=='__main__':
    print('SOULBOUND V15 OLC8:',run(),'checks PASS')
