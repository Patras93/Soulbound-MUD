# -*- coding: utf-8 -*-
"""OLC14: test real quest locks, DAG validation, atomic revisions and recipe/item batches."""
import copy
import sqlite3
from types import SimpleNamespace
from systems.live_olc17_quest_dependencies import (quest_requirements,
    validate_dependency_graph, validate_multi_dialogue, multi_dialogue_text)
from systems.live_olc13_batch import preview, stage
from systems.live_content_v1204 import LiveContentV1204
from player.session_mixins.quest_offers import SessionQuestOffersMixin
from data.quests import QUESTS
from data.items import ITEMS
from data.crafting_recipes import CRAFT_RECIPES


def run():
    count = 0
    def check(condition):
        nonlocal count
        assert condition, f'OLC14 check {count+1} failed'
        count += 1
    dependencies = {'a': {'requires_quests':['b','c']},
                    'b': {'requires_quest':'d'}, 'c': {'requires_quest':'d'}, 'd': {}}
    check(validate_dependency_graph(dependencies) == 4)
    check(validate_dependency_graph({'a':{'requires_quest':'retired_id'}})==1)
    rule={'quests':['a','b'],'text':'Brawo, bohaterze.'}
    check(validate_multi_dialogue(rule,{'a','b'}) is True)
    check(multi_dialogue_text({'olc_dialogue_after_quests':rule},lambda key:key in {'a','b'}) == 'Brawo, bohaterze.')
    check(multi_dialogue_text({'olc_dialogue_after_quests':rule},lambda key:key == 'a') is None)
    check(quest_requirements({'requires_quest':'b','requires_quests':['b','c']}) == ('b','c'))
    for bad in ({'a':{'requires_quests':['a']}},
                {'a':{'requires_quests':['b']},'b':{'requires_quest':'a'}},
                {'a':{'requires_quests':['b']},'b':{'requires_quests':['c']},'c':{'requires_quests':['a']}},
                {'a':{'requires_quests':['missing']}}):
        try:validate_dependency_graph(bad)
        except ValueError: count+=1
        else:raise AssertionError('An invalid quest prerequisite was accepted')
    check('bandit_patrol' in QUESTS and 'temple_rats' in QUESTS)
    conn=sqlite3.connect(':memory:'); conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    live=LiveContentV1204(SimpleNamespace(conn=conn))
    world=SimpleNamespace(mobs={},_register_runtime_spawn=lambda *args:None)
    server=SimpleNamespace(world=world,sessions=[])
    original=copy.deepcopy(QUESTS['bandit_patrol'])
    try:
        old=copy.deepcopy(live.draft)
        info=preview(live,'przedmiot','healing_potion','heal')
        check('healing_potion' in info and 'Niczego nie zapisano' in info)
        check(live.draft==old)
        check('iron_ingot' in CRAFT_RECIPES)
        check('iron_ingot' in preview(live,'receptura','iron_ingot','quantity'))
        stage(live,'przedmiot','healing_potion','heal','40')
        check(live.draft['item_edits']['healing_potion']['heal']==40)
        stage(live,'receptura','iron_ingot','quantity','2')
        check(live.draft['recipe_edits']['iron_ingot']['quantity']==2)
        live.stage_edit('quest','bandit_patrol','requires_quests','["temple_rats","haldor_crafting_order"]')
        check(live.draft['quest_edits']['bandit_patrol']['requires_quests']==['temple_rats','haldor_crafting_order'])
        check('requires_quests' not in QUESTS['bandit_patrol'])
        check('Niczego nie zapisano' in preview(live,'przedmiot','healing_potion','heal'))
        before=copy.deepcopy(live.draft)
        for field,value in [('requires_quests','["not_real_quest"]'),
                            ('requires_quests','["temple_rats","temple_rats"]'),
                            ('requires_quests','["bandit_patrol"]'),
                            ('requires_quests','["temple_rats",2]')]:
            try:live.stage_edit('quest','bandit_patrol',field,value)
            except ValueError:count+=1
            else:raise AssertionError('Invalid requires_quests accepted')
            check(live.draft==before)
        for category,prefix,field,amount in [
                ('przedmiot','healing_potion','weapon_power','100'),
                ('receptura','iron_ingot','quantity','-10'),
                ('przedmiot','healing_potion','heal','bad')]:
            try:stage(live,category,prefix,field,amount)
            except ValueError:count+=1
            else:raise AssertionError('Invalid mass edit accepted')
            check(live.draft==before)
        check('Aktywowano' in live.apply(server,'v1700_test'))
        check(QUESTS['bandit_patrol']['requires_quests']==['temple_rats','haldor_crafting_order'])
        check(ITEMS['healing_potion']['heal']==40)
        check(CRAFT_RECIPES['iron_ingot']['quantity']==2)
        check(conn.execute('SELECT revision FROM live_content_v1204').fetchone()[0]==1)
        # Actual offer lock method, no fake reward or level gates.
        checker=SimpleNamespace()
        class Probe(SessionQuestOffersMixin):
            def __init__(self, completed):
                self.completed=completed
                self.character=SimpleNamespace(room_id='temple')
            def quest_completed(self, qid):return qid in self.completed
            def active_class_names(self): return set()
        locked=Probe(set()).quest_lock_reasons('bandit_patrol')
        check(any('temple_rats' in text or QUESTS['temple_rats']['name'] in text for text in locked))
        check(len([text for text in locked if 'wymaga ukończenia' in text])==2)
        check(not Probe({'temple_rats','haldor_crafting_order'}).quest_lock_reasons('bandit_patrol'))
        live._remove(world)
        again=LiveContentV1204(SimpleNamespace(conn=conn))
        check(again.active['quest_edits']['bandit_patrol']['requires_quests']==['temple_rats','haldor_crafting_order'])
        again.stage_edit('quest','bandit_patrol','requires_quests','auto')
        check('requires_quests' not in again.draft['quest_edits'].get('bandit_patrol',{}))
        stage(again,'przedmiot','healing_potion','heal','auto')
        stage(again,'receptura','iron_ingot','quantity','auto')
        check('Aktywowano' in again.apply(server,'v1700_test'))
        check('requires_quests' not in QUESTS['bandit_patrol'])
        check(ITEMS['healing_potion']['heal']==original_potion_heal)
        again._remove(world)
    finally:
        live._remove(world)
        conn.close()
    check(QUESTS['bandit_patrol']==original)
    return count


original_potion_heal=ITEMS['healing_potion']['heal']
if __name__=='__main__':
    print('V17.00.0 OLC14:',run(),'checks PASS')
