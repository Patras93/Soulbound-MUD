# -*- coding: utf-8 -*-
"""v12.00.10 — real live OLC reward-mode regression on isolated SQLite.

Protects old auto formulas, atomic publication, rollback and character progress.
"""
import copy
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace as Obj


def run_regression():
    from systems.live_content_v1204 import LiveContentV1204
    from systems.live_progression_v1206 import (
        resource_rule_xp, xp_with_live_bonus, RESOURCE_XP_RULES,
        PROFESSION_XP_SCALE, TOOL_XP_SCALE)
    from systems.live_quest_olc_v1209 import profession_quest_ids
    from data.quests import QUESTS
    from data.items import ITEMS
    count = 0
    assert 'bandit_patrol' in QUESTS and 'iron_ore' in ITEMS
    count += 1
    start_quest = copy.deepcopy(QUESTS['bandit_patrol'])
    with tempfile.TemporaryDirectory() as temp:
        conn = sqlite3.connect(str(Path(temp) / 'test.db'))
        conn.row_factory = sqlite3.Row
        conn.execute('CREATE TABLE quests (account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER, PRIMARY KEY(account_id,quest_id))')
        db = Obj(conn=conn)
        world = Obj(mobs={}, _last_refresh_at=1., _register_runtime_spawn=lambda *a: None)
        server = Obj(world=world, sessions=[])
        live = LiveContentV1204(db)
        try:
            assert live.draft == live.active; count += 1
            for name, value in [('reward_xp','12345'),('reward_stat_xp','0'),
                                ('reward_class_xp','600'),('repeatable','true'),
                                ('repeat_cooldown','0')]:
                live.stage_edit('quest','bandit_patrol',name,value)
                count += 1
            assert live.draft['quest_edits']['bandit_patrol']['olc_reward_xp']==12345; count+=1
            assert QUESTS['bandit_patrol']==start_quest;count+=1
            old = copy.deepcopy(live.active)
            live.apply(server, 'test')
            assert QUESTS['bandit_patrol']['olc_reward_stat_xp']==0;count+=1
            assert QUESTS['bandit_patrol']['repeat_cooldown']==0;count+=1
            assert 'quest' in live.describe_news(old);count+=1
            live.stage_edit('quest','bandit_patrol','reward_xp','auto')
            live.stage_edit('quest','bandit_patrol','reward_stat_xp','auto')
            live.stage_edit('quest','bandit_patrol','reward_class_xp','auto')
            assert live.draft['quest_edits']['bandit_patrol'] == {'repeatable':True,'repeat_cooldown':0}; count+=1
            conn.execute('INSERT INTO quests VALUES (1,?,"active",7)',('bandit_patrol',));conn.commit()
            live.apply(server,'test')
            assert 'olc_reward_xp' not in QUESTS['bandit_patrol'];count+=1
            assert conn.execute('SELECT progress FROM quests WHERE quest_id=?',('bandit_patrol',)).fetchone()[0] == 7;count+=1
            # Old v12.00.7 floor semantics are preserved on explicit legacy fields.
            live.stage_edit('surowiec','iron_ore','prof_xp','1000')
            live.apply(server,'test')
            assert resource_rule_xp(50,'iron_ore')==1000;count+=1
            live.stage_edit('surowiec','iron_ore','prof_fixed','10')
            live.stage_edit('surowiec','iron_ore','tool_fixed','0')
            live.apply(server,'test')
            assert resource_rule_xp(9999,'iron_ore')==10;count+=1
            assert resource_rule_xp(9999,'iron_ore',tool=True)==0;count+=1
            assert resource_rule_xp(0,'iron_ore')==10;count+=1
            live.stage_edit('surowiec','iron_ore','prof_scale','35')
            live.apply(server,'test')
            assert resource_rule_xp(1000,'iron_ore')==350;count+=1
            live.stage_edit('surowiec','iron_ore','prof_mode','auto')
            live.stage_edit('surowiec','iron_ore','tool_mode','auto')
            live.apply(server,'test')
            assert resource_rule_xp(1000,'iron_ore')==1000;count+=1
            assert resource_rule_xp(800,'iron_ore',tool=True)==800;count+=1
            assert 'iron_ore' not in RESOURCE_XP_RULES;count+=1
            # Changing global percent < 100 works only through the new xp_scale.
            from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
            profession = next(iter(PROFESSION_RANK_NAMES))
            tool = next(iter(TOOL_PROFESSION_MAP))
            live.stage_edit('profesja',profession,'xp_scale','20')
            live.stage_edit('narzedzie',tool,'xp_scale','0')
            live.apply(server,'test')
            assert xp_with_live_bonus(100,profession)==20;count+=1
            assert xp_with_live_bonus(100,tool,tool=True)==0;count+=1
            assert PROFESSION_XP_SCALE[profession]==20;count+=1
            assert TOOL_XP_SCALE[tool]==0;count+=1
            live.stage_edit('profesja',profession,'xp_scale','auto')
            live.stage_edit('narzedzie',tool,'xp_scale','auto')
            live.apply(server,'test')
            assert xp_with_live_bonus(100,profession)==100;count+=1
            assert xp_with_live_bonus(100,tool,tool=True)==100;count+=1
            # Real profession quests are discoverable, editable and never cause a Soul XP rule change.
            from systems.profession_projects_v1200 import PROJECTS
            first = next(iter(PROJECTS))
            qids = profession_quest_ids(QUESTS,first)
            assert qids;count+=1
            qid = next((q for q in qids if QUESTS[q].get('reward_profession_xp')),qids[0])
            original = copy.deepcopy(QUESTS[qid]);count+=1
            live.stage_edit('quest',qid,'xp_profesji','0')
            assert live.draft['quest_edits'][qid]['reward_profession_xp']==0;count+=1
            live.stage_edit('quest',qid,'xp_profesji','auto')
            assert qid not in live.draft['quest_edits'];count+=1
            assert QUESTS[qid] == original;count+=1
            # Backward compatibility, invalid fields and negative XP remain rejected.
            for obj, key, field, value in [('quest','bandit_patrol','reward_xp','-3'),
                                          ('quest','bandit_patrol','needed','0'),
                                          ('surowiec','iron_ore','prof_fixed','-1'),
                                          ('surowiec','iron_ore','prof_scale','1001'),
                                          ('profesja',profession,'xp_scale','-1'),
                                          ('surowiec','iron_ore','prof_mode','python')]:
                try: live.stage_edit(obj,key,field,value)
                except ValueError: count+=1
                else: raise AssertionError(f'Accepted invalid {obj} {field} {value}')
            live.reset_draft()
            assert live.draft==live.active;count+=1
            assert conn.execute('SELECT progress FROM quests WHERE quest_id=?',('bandit_patrol',)).fetchone()[0]==7;count+=1
        finally:
            live._remove(world)
            assert QUESTS['bandit_patrol'] == start_quest
            conn.close()
    return count

if __name__ == '__main__':
    print('V12.00.10 OLC AUTO/MANUAL/REDUCTION:', run_regression(),'checks PASS')
