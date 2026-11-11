# -*- coding: utf-8 -*-
"""Runtime-registry OLC regression: edits, additions, persistence and safety."""
import copy
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from systems.live_content_v1204 import (LiveContentV1204, ROOMS, MOB_TEMPLATES,
    ITEMS, NPCS, SHOPS, QUESTS, CRAFT_RECIPES, MOB_SPAWNS)


def run_regression():
    import server  # Assemble runtime catalogs before adding live records.
    count = 0
    reg = (ROOMS, MOB_TEMPLATES, ITEMS, NPCS, SHOPS, QUESTS, CRAFT_RECIPES)
    baselines = [copy.deepcopy(x) for x in reg]
    original_spawns = list(MOB_SPAWNS)
    with tempfile.TemporaryDirectory() as dirname:
        dbname = Path(dirname) / 'live.db'
        conn = sqlite3.connect(dbname)
        conn.row_factory = sqlite3.Row
        # A real Soulbound database always has the quest-progress table.
        # Include it in this intentionally minimal OLC fixture: the current
        # publisher must guard active quests even in legacy OLC scenarios.
        conn.execute("CREATE TABLE quests (account_id INTEGER, quest_id TEXT, status TEXT, progress INTEGER)")
        conn.commit()
        db = SimpleNamespace(conn=conn)
        m = LiveContentV1204(db)
        world = SimpleNamespace(mobs={}, _last_refresh_at=123.0)
        world._register_runtime_spawn = lambda rid, mid: None
        server = SimpleNamespace(world=world, sessions=[])
        try:
            main = 'live_olc_valley_1205'
            npcroom = 'live_olc_npc_hut_1205'
            monster = 'live_olc_wolf_1205'
            item = 'live_olc_gem_1205'
            npc = 'live_olc_keeper_1205'
            quest = 'live_olc_hunt_1205'
            recipe = 'live_olc_cut_gem_1205'
            payload = {
                'rooms': {
                    main: {'name':'Przełęcz', 'desc':'Kamienista droga.', 'zone':'OLC', 'generator_level': 90},
                    npcroom: {'name':'Chata Strażnika', 'desc':'Osobny pokój.', 'zone':'OLC','generator_level':90},
                },
                'links': [['temple_basement','northeast',main],[main,'southwest','temple_basement'],[main,'east',npcroom],[npcroom,'west',main]],
                'mobs': {monster: {'name':'Wilk OLC', 'generator_level':90,'max_hp':100000,'damage':300,'class_xp_reward':5000}},
                'spawns': [[main,monster]],
                'room_edits': {'temple_basement': {'desc': 'Tymczasowo poprawiony opis.'}},
                'mob_edits': {'temple_rat': {'name':'Szczur OLC', 'damage': 11, 'drops':{item:0.20}}},
                'items': {item:{'name':'Klejnot OLC','desc':'Materiał.','type':'craft_material','price':100,'currency':'silver'}},
                'item_edits': {'healing_potion':{'price':28}},
                'npcs': {npc:{'name':'Opiekun OLC', 'room':npcroom, 'dialogue':'Witaj.', 'quest':quest, 'shopkeeper':True}},
                'npc_edits': {'fisher_tomas':{'dialogue':'Nowa, niedestrukcyjna wypowiedź.'}},
                'shops': {npcroom:[item]},
                'quests': {quest:{'name':'Wilcza próba', 'giver':'Opiekun OLC','kind':'kill','target':monster,'needed':2,'description':'Pokonaj dwa wilki.','reward_silver':1000}},
                'quest_edits': {'fisher_30_fish':{'reward_profession_xp':1200}},
                'recipes': {recipe:{'name':'Szlif OLC','desc':'Szlifuj kamień.','stations':[npcroom],
                           'ingredients':{'iron_ore':1},'output':item,'quantity':1,
                           'min_profession_level':1,'profession':'Górnictwo','tool_type':'mining',
                           'tool_item_id':'pickaxe','tool_name':'Kilof'}},
                'recipe_edits': {'iron_ingot':{'desc':'Nowy opis sztabki.'}},
            }
            # Full content package imported as one atomic draft.
            source = Path(dirname)/'publish.json'
            source.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
            assert '1 questów' in m.stage_file(source); count += 1
            assert m.draft['mob_edits']['temple_rat']['damage'] == 11; count += 1
            bad = {'npcs':{'live_npc_collision_1205':{'name':'Niepoprawny NPC', 'room':'fish_market','dialogue':'Błąd.'}}}
            source.write_text(json.dumps(bad),encoding='utf-8')
            try: m.stage_file(source)
            except ValueError: count += 1
            else: raise AssertionError('NPC collision accepted')
            assert npc in m.draft['npcs']; count += 1
            try: m.stage_edit('mob', 'temple_rat', 'drops', '{broken')
            except ValueError: count += 1
            else: raise AssertionError('invalid JSON accepted')
            m.stage_edit('mob','temple_rat','class_xp_reward','9000'); count += 1
            assert int(m.draft['mob_edits']['temple_rat']['class_xp_reward']) == 9000; count += 1
            m.export(Path(dirname)/'export.json'); count += 1
            assert json.loads((Path(dirname)/'export.json').read_text('utf-8'))['npcs'][npc]['room'] == npcroom; count += 1
            # Fight blocks hot changes to existing mobs.
            world.mobs['fight'] = SimpleNamespace(room_id='temple_basement',home_room_id='temple_basement', template_id='temple_rat', engaged_by='hero',aoe_engaged_by=None)
            try: m.apply(server, 'admin')
            except ValueError as exc: assert 'walki' in str(exc); count += 1
            else: raise AssertionError('edit during fight accepted')
            world.mobs.clear()
            assert 'rewizję 1' in m.apply(server,'admin'); count += 1
            assert ROOMS[main]['exits']['east']==npcroom and ROOMS['temple_basement']['desc']=='Tymczasowo poprawiony opis.'; count += 1
            assert MOB_TEMPLATES['temple_rat']['drops'][item] == .2; count += 1
            assert ITEMS[item]['type'] == 'craft_material' and ITEMS['healing_potion']['price']==28; count += 1
            assert NPCS[npc]['room']==npcroom and NPCS['fisher_tomas']['dialogue']=='Nowa, niedestrukcyjna wypowiedź.'; count += 1
            assert SHOPS[npcroom] == [item] and QUESTS[quest]['target'] == monster; count += 1
            # Actual player-session discovery paths for the shop and local quest.
            from player.session_mixins.quest_turnin import SessionQuestTurninMixin
            from player.session_mixins.shops_teachers import SessionShopsTeachersMixin
            fake = SimpleNamespace(character=SimpleNamespace(room_id=npcroom),
                normalize_description_query=lambda value: str(value).strip().casefold())
            assert quest in SessionQuestTurninMixin.local_quest_ids(fake); count += 1
            assert SessionShopsTeachersMixin.current_shop_offers(fake) == [item]; count += 1
            from world.generation_systems import v0160_npcs_in_room
            assert npc in v0160_npcs_in_room(npcroom); count += 1
            assert CRAFT_RECIPES[recipe]['stations'] == (npcroom,); count += 1
            assert QUESTS['fisher_30_fish']['reward_profession_xp']==1200; count += 1
            assert (main,monster) in MOB_SPAWNS; count += 1
            # Persistence survives a new service instance, with live entries already present.
            m._remove(world)
            m = LiveContentV1204(db)
            assert m.revision == 1 and QUESTS[quest]['name'] == 'Wilcza próba'; count += 1
            assert len([n for n in NPCS.values() if n.get('room') == npcroom])==1; count += 1
            # Rollback must NOT delete an ID that may already be in saved player quest/item data.
            try: m.apply(server, 'admin', rollback=True)
            except ValueError as exc: assert 'quest' in str(exc) or 'items' in str(exc); count += 1
            else: raise AssertionError('unsafe published quest rollback accepted')
            # A safe revision changing just an existing mob is reversible.
            m.reset_draft()
            m.stage_edit('mob','temple_rat','damage','22')
            assert 'rewizję 2' in m.apply(server,'admin'); count += 1
            assert MOB_TEMPLATES['temple_rat']['damage']==22; count += 1
            assert 'rewizję 3' in m.apply(server,'admin',rollback=True); count += 1
            assert MOB_TEMPLATES['temple_rat']['damage']==11; count += 1
            # Harden legacy payload: v12.00.4 on-disk schema is still readable.
            assert len(m._compat({'rooms':{},'links':[],'mobs':{},'spawns':[],'balances':{}})) == len(m.active); count += 1
        finally:
            m._remove(world)
            for cur, baseline in zip(reg, baselines):
                cur.clear(); cur.update(baseline)
            MOB_SPAWNS[:] = original_spawns
            conn.close()
    return count

if __name__=='__main__':
    print('V12.00.5 PELNE OLC / NPC / PRZEDMIOTY / QUESTY / RECEPTURY:',run_regression(),'checks PASS')
