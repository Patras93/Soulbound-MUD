# -*- coding: utf-8 -*-
"""v12.00.9: 22-profession quest XP, tool XP, NEWS and progression safety."""
import copy
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace as S

from data.quests import QUESTS
from systems.profession_projects_v1200 import PROJECTS
from systems.live_quest_olc_v1209 import profession_quest_ids, parse_quest_edit
from systems.live_content_v1204 import LiveContentV1204
from core.progression_resources import v0522_is_profession_quest


def run_regression():
    count = 0
    original = copy.deepcopy(QUESTS)
    identifiers = {}
    for name, project in PROJECTS.items():
        qid = 'v1209_test_prof_' + project.code
        assert qid not in QUESTS
        identifiers[name] = qid
        QUESTS[qid] = {
            'name': 'Próba ' + name, 'description': 'Wykonaj prace profesji.',
            'giver': 'Mistrz', 'kind': 'profession_action', 'target': name,
            'needed': 3, 'required_profession': name,
            'reward_profession': name, 'reward_profession_xp': 100,
            'reward_tool_type': project.tool, 'reward_tool_xp': 70,
            'specialist_tool_type': project.tool,
            'min_profession_level': 1, 'reward_silver': 100,
            'reward_gold': 0, 'reward_mithril': 0, 'reward_items': {},
            'repeatable': True, 'repeat_cooldown': 3600,
        }
    svc = None
    try:
        for name, qid in identifiers.items():
            assert qid in profession_quest_ids(QUESTS, name), name
            count += 1
        # Silver-only profession contracts with no XP metadata are discoverable by objective.
        target_only = 'v1209_test_prof_target_only'
        QUESTS[target_only] = {'name': 'Zlecenie praktyczne', 'kind': 'profession_action',
                               'target': 'Żeglarstwo', 'needed': 1, 'reward_silver': 500}
        assert target_only in profession_quest_ids(QUESTS, 'Zeglarstwo'); count+=1
        QUESTS.pop(target_only)
        assert identifiers['Łowiectwo'] in profession_quest_ids(QUESTS, 'Lowiectwo'); count+=1
        assert identifiers['Wędkarstwo'] in profession_quest_ids(QUESTS, 'Wedkarstwo'); count+=1
        try: profession_quest_ids(QUESTS, 'Nieistniejaca')
        except ValueError: count += 1
        else: raise AssertionError('Accepted unknown profession')
        for field, desired in (('xp_profesji', 'reward_profession_xp'),
                               ('prof_xp', 'reward_profession_xp'),
                               ('xp_narzedzia', 'reward_tool_xp'),
                               ('tool_xp', 'reward_tool_xp'),
                               ('poziom_profesji', 'min_profession_level'),
                               ('poziom_narzedzia', 'min_tool_level')):
            assert parse_quest_edit(field, '111')[0] == desired; count+=1
        with tempfile.TemporaryDirectory() as temp:
            conn = sqlite3.connect(str(Path(temp)/'test.sqlite'))
            conn.row_factory=sqlite3.Row
            conn.execute('CREATE TABLE quests (account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER, PRIMARY KEY(account_id,quest_id))')
            db = S(conn=conn)
            world=S(mobs={}, _last_refresh_at=1., _register_runtime_spawn=lambda *_: None)
            srv=S(world=world, sessions=[])
            svc=LiveContentV1204(db)
            qid=identifiers['Wędkarstwo']
            other=identifiers['Łowiectwo']
            assert QUESTS[qid]['reward_profession_xp']==100;count+=1
            for field, value in (('xp_profesji','50000'), ('xp_narzedzia','25000'),
                                 ('reward_xp','120000'), ('needed','15'),
                                 ('poziom_profesji','25'),('poziom_narzedzia','10'),
                                 ('reward_silver','23456'),('repeat_cooldown','5400')):
                svc.stage_edit('quest',qid,field,value);count+=1
            svc.stage_edit('quest',other,'xp_profesji','77777');count+=1
            snapshot=copy.deepcopy(svc.draft)
            for field, value in (('xp_profesji','-5'),('xp_narzedzia','x'),
                                 ('poziom_profesji','0'),('poziom_profesji','801'),
                                 ('poziom_narzedzia','-1'),('reward_silver','1.5'),
                                 ('unlocks_soul_tier','10')):
                try: svc.stage_edit('quest',qid,field,value)
                except ValueError: 
                    assert svc.draft == snapshot;count+=1
                else: raise AssertionError('Invalid profession quest field accepted: '+field)
            try: svc.stage_edit('quest','bandit_patrol','poziom_profesji','25')
            except ValueError: count+=1
            else: raise AssertionError('Combat quest received profession threshold')
            # The reward is mutable, while an already accepted objective stays in SQLite.
            conn.execute('INSERT INTO quests(account_id,quest_id,status,progress) VALUES(?,?,?,?)', (42,qid,'active',7))
            conn.commit()
            previous=copy.deepcopy(svc.active)
            assert QUESTS[qid]['reward_profession_xp']==100; count+=1
            result=svc.apply(srv,'admin')
            assert 'rewizję 1' in result;count+=1
            changed=QUESTS[qid]
            assert changed['reward_profession_xp']==50000 and changed['reward_tool_xp']==25000;count+=1
            assert changed['olc_reward_xp']==120000 and changed['needed']==15;count+=1
            assert changed['min_profession_level']==25 and changed['min_tool_level']==10;count+=1
            assert changed['reward_silver']==23456 and changed['repeat_cooldown']==5400;count+=1
            assert QUESTS[other]['reward_profession_xp']==77777;count+=1
            assert v0522_is_profession_quest(changed);count+=1
            assert conn.execute('SELECT progress FROM quests WHERE account_id=42').fetchone()[0]==7;count+=1
            news=svc.describe_news(previous)
            assert 'EXP profesji: 50000' in news and 'EXP narzędzia: 25000' in news;count+=1
            assert 'Próba Wędkarstwo' in news;count+=1
            # A newer service instance must load the same published revision.
            svc._remove(None);svc=LiveContentV1204(db)
            assert QUESTS[qid]['reward_profession_xp']==50000;count+=1
            assert QUESTS[other]['reward_profession_xp']==77777;count+=1
            svc.apply(srv,'admin', rollback=True)
            assert QUESTS[qid]['reward_profession_xp']==100 and QUESTS[other]['reward_profession_xp']==100;count+=1
            assert conn.execute('SELECT progress FROM quests WHERE account_id=42').fetchone()[0]==7;count+=1
            conn.close()
    finally:
        if svc is not None:svc._remove(None)
        for name,qid in identifiers.items():QUESTS.pop(qid,None)
        assert QUESTS == original, 'Original quest catalog was modified';count+=1
    return count


if __name__=='__main__':
    print('V12.00.9 QUESTY 22 PROFESJI OLC:', run_regression(),'checks PASS')
