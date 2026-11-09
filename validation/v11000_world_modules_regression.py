# -*- coding: utf-8 -*-
"""v110: 12 odrębnych krain, 700 questów, 40 bossów; bez zmian starych katalogów."""
from __future__ import annotations
import copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from world.v11000_realms import install,PARENT,REGIONS,planned_ids
from core.v11000_archetypes import CLASS_SPECS,RACE_SPECS,PROFESSION_SPECS


def fixture():
    return dict(rooms={PARENT:{'v109_horizon':True,'exits':{}}},mobs={},spawns=[],
                npcs={},quests={},items={'soul_shard':{'name':'Historyczny'}},
                recipes={},zones={},categories={},guides={},power={})


def apply(state):
    return install(*(state[k] for k in ('rooms','mobs','spawns','npcs','quests','items',
                                      'recipes','zones','categories','guides','power')))


def run():
    assert len(CLASS_SPECS)==len(RACE_SPECS)==len(PROFESSION_SPECS)==8
    assert len(REGIONS)==12
    state=fixture()
    before=copy.deepcopy(state)
    result=apply(state)
    for key,value in dict(regions=12,rooms=360,mobs=184,bosses=40,spawns=328,
                          npcs=48,quests=700,items=72,recipes=12).items():
        assert result[key]==value,(key,result[key])
    assert state['items']['soul_shard']==before['items']['soul_shard']
    assert len(set(state['quests']))==700
    # 444 of the 700 v110 quests repeat. Their one-hour cooldown is now
    # explicit (equal to the historical runtime fallback), not missing.
    from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
    repeatable=[q for q in state['quests'].values() if q.get('repeatable')]
    assert len(repeatable)==444,len(repeatable)
    assert all(q.get('repeat_cooldown')==QUEST_REPEAT_COOLDOWN_SECONDS
               for q in repeatable)
    assert len(set(state['mobs']))==184
    # Real crafting UI requires a description for each of the twelve new recipes.
    assert len(state['recipes'])==12
    assert all(recipe.get('desc') and recipe.get('stations')
               and recipe.get('ingredients') and recipe.get('output')
               for recipe in state['recipes'].values())
    # Real teacher NPCs and their dedicated physical classrooms, one per new class.
    teacher_rooms=set()
    for index, class_row in enumerate(CLASS_SPECS):
        slug=REGIONS[index][0]
        npc_id='v11000_realm_'+slug+'_npc_2'
        teacher=state['npcs'][npc_id]
        assert teacher['teacher_class']==class_row[0], npc_id
        assert teacher['room'] in state['rooms'], npc_id
        assert teacher['room'] not in teacher_rooms, npc_id
        teacher_rooms.add(teacher['room'])
        assert 'learn' in teacher['dialogue'], npc_id
    assert len(teacher_rooms)==8
    after=copy.deepcopy(state)
    again=apply(state)
    assert again['already_installed'] and state==after
    # Unauthorized content collision must fail before any world mutation.
    state=fixture()
    state['quests']['v11000_event_kontynent_quest_01']={'name':'Tylko test'}
    frozen=copy.deepcopy(state)
    try:apply(state)
    except RuntimeError as exc:assert 'kolizja' in str(exc)
    else:raise AssertionError('Expected ID collision failure')
    assert state==frozen
    print('V110 WORLD PASS: 12 independent regions, 360 rooms, 700 unique quests, '
          '40 bosses, 328 spawns; idempotent and collision-atomic',flush=True)

if __name__=='__main__':run()
