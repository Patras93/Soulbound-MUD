# -*- coding: utf-8 -*-
"""v14 real registry/SQLite/publish safety; uses memory only, no player data."""
import copy
import sqlite3
from types import SimpleNamespace
from core.classes_skills import CLASS_SKILLS
from data.quests import QUESTS
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204, blank
from systems.live_olc4_new_skills import new_skill_definition
from systems.live_olc4_fields import validate_extra
from systems.live_olc_preview_v12010 import FIELDS


def run():
    n=0
    conn=sqlite3.connect(':memory:'); conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(world=world,sessions=[])
    svc=LiveContentV1204(SimpleNamespace(conn=conn))
    before=copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    count=sum(len(rows) for rows in CLASS_SKILLS.values())
    initial=copy.deepcopy(svc.draft)
    try:
        # One atomic draft containing all new feature families.
        svc.draft['skills']['live_v14_execute']={
            'class_name':'Mag','name':'Egzekucja V14','desc':'Cios kończący',
            'kind':'execute','unlock':40,'mana':60,'cooldown':0,
            'scale':'intelligence','mult':2.0,'aliases':[],'effect':1.75}
        assert new_skill_definition('live_v14_execute',svc.draft['skills']['live_v14_execute'])['execute_mult']==1.75;n+=1
        for field,val in (('olc_boss_support_interval',6),('olc_boss_support_duration',14),
                          ('olc_boss_rally_interval',8),('olc_boss_rally_duration',20)):
            svc.draft['mob_edits'].setdefault('bandit_captain',{})[field]=val
            assert field in FIELDS['mob_edits'];n+=1
        svc.draft['quests']['live_v14_ores']={
            'name':'Zestaw Rud','giver':'Rybak Borys','kind':'collect_resource_set',
            'target':'iron_ore','needed':5,'resource_targets':{'iron_ore':3,'copper_ore':2},
            'reward_silver':300,'description':'Dostarcz rudy.'}
        assert svc.draft['quests']['live_v14_ores']['needed']==5;n+=1
        svc.draft['items']['live_v14_armor']={
            'name':'Pancerz V14','desc':'Pancerz','type':'armor','slot':'body',
            'defense':100,'attack':20,'stats':{'strength':15,'constitution':10},
            'required_level':40,'price':2000,'currency':'silver'}
        assert len(svc.draft['items']['live_v14_armor']['stats'])==2;n+=1
        # Modern world has more than 100 bandit variants; exercise a stable
        # representative batch within the OLC atomic-edit limit.
        bandit_ids=sorted(k for k in MOB_TEMPLATES if k.startswith('bandit_'))
        assert 'bandit_captain' in bandit_ids
        selected=['bandit_captain']+[k for k in bandit_ids if k!='bandit_captain'][:99]
        bandits={k:MOB_TEMPLATES[k]['damage'] for k in selected}
        assert 1<=len(bandits)<=100;n+=1
        for mid in bandits: svc.draft['balances'][mid]={'damage':5432}
        # Profession/tool group uses strictly existing xp_scale mechanism, no new tools.
        from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
        svc.draft['profession_edits'].update({key:{'xp_scale':80} for key in PROFESSION_RANK_NAMES})
        svc.draft['tool_edits'].update({key:{'xp_scale':70} for key in TOOL_PROFESSION_MAP})
        assert len(svc.draft['profession_edits'])==len(PROFESSION_RANK_NAMES);n+=1
        assert len(svc.draft['tool_edits'])==len(TOOL_PROFESSION_MAP);n+=1
        assert svc.validate(svc.draft);n+=1
        assert all(MOB_TEMPLATES[k]['damage']==old for k,old in bandits.items());n+=1
        assert 'live_v14_ores' not in QUESTS and 'live_v14_armor' not in ITEMS;n+=1
        svc.apply(server,'test');n+=1
        assert svc.revision==1 and QUESTS['live_v14_ores']['kind']=='collect_resource_set';n+=1
        assert ITEMS['live_v14_armor']['attack']==20;n+=1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_support_interval']==6;n+=1
        assert all(MOB_TEMPLATES[k]['damage']==5432 for k in bandits);n+=1
        assert sum(len(rows) for rows in CLASS_SKILLS.values())==count+1;n+=1
        assert conn.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0]==1;n+=1
        try: svc.apply(server,'test',rollback=True)
        except ValueError as e: assert 'Nie wycofuję opublikowanych' in str(e);n+=1
        else: raise AssertionError('Cannot delete published quest/items/skils on rollback')
        assert svc.revision==1;n+=1
        # Negative checks use fast strict validators, not an expensive full-world rebuild.
        for field,val in (('olc_boss_support_interval',0),('olc_boss_support_duration',31)):
            try: validate_extra('mob_edits','bandit_captain',field,val,svc.draft,set(),set())
            except ValueError:n+=1
            else:raise AssertionError('Invalid boss control accepted')
        assert len(CLASS_SKILLS)==22;n+=1
    finally:
        svc._remove(world)
        assert sum(len(rows) for rows in CLASS_SKILLS.values())==count
        assert MOB_TEMPLATES['bandit_captain']==before
        assert all(MOB_TEMPLATES[k]['damage']==old for k,old in bandits.items())
        conn.close()
    return n+3

if __name__ == '__main__':
    print('V14.00.0 OLC7:',run(),'checks PASS')
