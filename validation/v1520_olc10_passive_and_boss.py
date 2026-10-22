# -*- coding: utf-8 -*-
"""v15.20.0: passive skill and support target priorities; isolated SQLite."""
import copy
import sqlite3
from types import SimpleNamespace

from core.classes_skills import CLASS_SKILLS
from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc4_new_skills import new_skill_definition


def run():
    checks = 0
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world = SimpleNamespace(mobs={}, _last_refresh_at=0., _register_runtime_spawn=lambda *args: None)
    srv = SimpleNamespace(world=world, sessions=[])
    svc = LiveContentV1204(SimpleNamespace(conn=conn))
    baseline = sum(map(len, CLASS_SKILLS.values()))
    original_boss = copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    try:
        svc.stage_new_skill('live_v1520_boost', 'Wojownik', 'Wzmacniający Sztandar Próby',
                            'boost', 51, 0, 1., 'strength', 'Pasywna premia po nauce.', 1.2)
        meta = svc.draft['skills']['live_v1520_boost']
        skill = new_skill_definition('live_v1520_boost', meta)
        assert skill['kind'] == 'boost' and skill['boost'] == 1.2; checks += 1
        assert skill['mana'] == 0 and skill['cooldown'] == 0; checks += 1
        assert 'mechanic_cooldown' not in skill; checks += 1
        for invalid in [(0, 120, 1.2), (10, 0, 1.2), (0, 0, .99), (0, 0, 2.0)]:
            draft = copy.deepcopy(svc.draft)
            m = svc.draft['skills']['live_v1520_boost']
            try:
                svc.stage_new_skill('live_v1520_boost', 'Wojownik', 'Wzmacniający Sztandar Próby',
                                    'boost', 51, invalid[0], 1., 'strength', 'Opis', invalid[2], cooldown=invalid[1])
            except ValueError: checks += 1
            else: raise AssertionError(f'Nieprawidłowy boost zaakceptowany: {invalid}')
            assert svc.draft == draft; checks += 1
        svc.stage_edit('mob', 'bandit_captain', 'olc_boss_support_priority', 'strongest')
        assert svc.draft['mob_edits']['bandit_captain']['olc_boss_support_priority']=='strongest'; checks+=1
        for bad in ['random', 'strongest;import os', '']:
            draft = copy.deepcopy(svc.draft)
            try: svc.stage_edit('mob','bandit_captain','olc_boss_support_priority',bad)
            except ValueError: checks+=1
            else: raise AssertionError('Zły priorytet zaakceptowany')
            assert svc.draft == draft; checks += 1
        from systems.encounter_brain_v1230 import ordinary_tactics_v1230
        # Behavioral check with actual AI function, never patched mock implementation.
        weak = SimpleNamespace(room_id='test', template_id='temple_rat', hp=20,
                               adaptive_max_hp_v11330=100, alive=True,
                               engaged_by={'player'}, monster_ai_summoned_v1160=False,
                               monster_ai_guard_until_v1160=0)
        strong = SimpleNamespace(room_id='test', template_id='temple_rat', hp=40,
                                 adaptive_max_hp_v11330=100, alive=True,
                                 engaged_by={'player'}, monster_ai_summoned_v1160=False,
                                 monster_ai_guard_until_v1160=0)
        boss = SimpleNamespace(room_id='test',template_id='bandit_captain',hp=80,
                               adaptive_max_hp_v11330=100,alive=True,engaged_by={'player'},
                               monster_ai_summoned_v1160=False,combat_turn=4,
                               monster_ai_next_action_v1160=0)
        world.room_mobs=lambda room:[boss, weak, strong]
        boss_definition = {'boss': True, 'name':'Boss Próby', 'max_hp':100,
                           'olc_boss_support_priority':'strongest', 'olc_boss_guard_threshold':55}
        out=ordinary_tactics_v1230(world,boss,boss_definition,now=100)
        assert out and strong.monster_ai_guard_until_v1160 > 100 and weak.monster_ai_guard_until_v1160 == 0,(out,weak,strong)
        checks+=1
        boss.monster_ai_next_action_v1160=0
        strong.monster_ai_guard_until_v1160=0
        boss_definition['olc_boss_support_priority']='weakest'
        out=ordinary_tactics_v1230(world,boss,boss_definition,now=200)
        assert out and weak.monster_ai_guard_until_v1160 > 200;checks+=1
        world.mobs={}
        svc.apply(srv, 'olc_test')
        assert svc.revision==1; checks+=1
        assert sum(map(len,CLASS_SKILLS.values()))==baseline+1;checks+=1
        published = next(s for s in CLASS_SKILLS['Wojownik'] if s['id']=='live_v1520_boost')
        assert published['boost']==1.2 and published['kind']=='boost';checks+=1
        # Use the original player buff method: learned skill affects physical
        # damage but not the unrelated magic/feedback channels.
        # Compile the original method without importing the entire server
        # module graph (which requires the Windows runtime catalogue bootstrap).
        import ast
        from pathlib import Path
        path=Path('player/session_mixins/skill_queue_buffs.py')
        tree=ast.parse(path.read_text('utf8'))
        cls=next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name=='SessionSkillQueueBuffsMixin')
        method=next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name=='passive_class_boost_multiplier_v11134')
        env={'CLASS_SKILLS': CLASS_SKILLS, 'SKILL_MAX_LEVEL': 800,
             'class_type_for_name': lambda name: 'physical' if name=='Wojownik' else 'magic'}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),
                     '<real-passive-boost>', 'exec'), env)
        from types import SimpleNamespace as NS
        class SkillDB:
            def knows_skill(self, account_id, skill_id):
                return skill_id == 'live_v1520_boost'
            def skill_progress(self, account_id, skill_id):
                return {'level': 51}
        class Player:
            account_id = 1
            character = NS(soul_level=1)
            server = NS(db=SkillDB())
            def active_class_names(self):return ['Wojownik']
            def skill_mastery_unlocked(self, skill):return True
        player=Player()
        assert env['passive_class_boost_multiplier_v11134'](player, target_type='physical') > 1.0;checks+=1
        assert env['passive_class_boost_multiplier_v11134'](player, target_type='magic') == 1.0;checks+=1
        assert env['passive_class_boost_multiplier_v11134'](player, target_type='feedback') == 1.0;checks+=1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_support_priority']=='strongest';checks+=1
        svc._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn))
        assert reopened.revision==1 and reopened.active['skills']['live_v1520_boost']['effect']==1.2;checks+=1
        reopened.stage_edit('mob','bandit_captain','olc_boss_support_priority','auto')
        assert 'olc_boss_support_priority' not in reopened.draft['mob_edits'].get('bandit_captain',{});checks+=1
        reopened.apply(srv,'olc_test')
        assert 'olc_boss_support_priority' not in MOB_TEMPLATES['bandit_captain'];checks+=1
        reopened._remove(world)
    finally:
        svc._remove(world)
        assert sum(map(len, CLASS_SKILLS.values())) == baseline
        assert MOB_TEMPLATES['bandit_captain'] == original_boss
        conn.close()
    return checks

if __name__ == '__main__':
    print('OLC 10.0:',run(),'PASS')
