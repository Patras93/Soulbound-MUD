# -*- coding: utf-8 -*-
"""OLC 4.0 integration tests: actual published catalogs, SQLite, preview and rollback."""
import copy
import json
import sqlite3
from types import SimpleNamespace

from systems.live_content_v1204 import LiveContentV1204, ROOMS, MOB_TEMPLATES, ITEMS, NPCS, SHOPS, CRAFT_RECIPES
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.live_olc4_browse import find_catalog, fields_for


def run_regression():
    count = 0
    con = sqlite3.connect(':memory:')
    con.row_factory = sqlite3.Row
    con.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    db = SimpleNamespace(conn=con)
    catalogs = [ROOMS, MOB_TEMPLATES, ITEMS, NPCS, SHOPS, CRAFT_RECIPES]
    originals = [copy.deepcopy(cat) for cat in catalogs]
    world = SimpleNamespace(mobs={}, _last_refresh_at=0, _register_runtime_spawn=lambda *x: None)
    server = SimpleNamespace(world=world, sessions=[])
    m = LiveContentV1204(db)
    try:
        # Read-only preview must show actual stock, not a fictional numeric amount.
        before = copy.deepcopy(m.draft)
        summary = describe_current_edit(m, 'sklep', 'market', 'inventory')
        # Earlier runtime checks can dynamically expand/reorder market stock.
        # Compare to the actual live catalog rather than a hard-coded product.
        current_stock = json.dumps(SHOPS['market'], ensure_ascii=False, separators=(',', ':'))
        assert 'OLC PODGLĄD sklep market inventory:' in summary and current_stock in summary
        assert ('Do skopiowania i zmiany:' in summary or
                'Wartość zawiera znaki wymagające ręcznego wpisania' in summary)
        count += 1
        assert m.draft == before and m.revision == 0
        count += 1
        assert 'bandit_patrol' in find_catalog(m,'quest','bandit')
        count += 1
        assert 'inventory' in fields_for(m,'sklep','market')
        count += 1
        # Full OLC staging, without touching active catalog values.
        m.stage_room('live_olc4_npc_room', 10, 'Izba OLC 4', 'Izba strażnika.', 'Test')
        count += 1
        m.stage_edit('sklep', 'market', 'inventory', '["healing_potion","iron_ore"]')
        count += 1
        m.stage_edit('przedmiot', 'healing_potion', 'heal', '55')
        count += 1
        m.stage_edit('przedmiot', 'healing_potion', 'currency', 'silver')
        count += 1
        m.stage_edit('mob', 'temple_rat', 'silver', '0')
        count += 1
        m.stage_edit('mob', 'temple_rat', 'damage_type', 'magic')
        count += 1
        m.stage_edit('receptura', 'iron_ingot', 'stations', '["forge","live_olc4_npc_room"]')
        count += 1
        m.stage_edit('receptura', 'iron_ingot', 'quantity', '2')
        count += 1
        m.stage_edit('npc', 'fisher_tomas', 'room', 'live_olc4_npc_room')
        count += 1
        assert SHOPS['market'] != ['healing_potion','iron_ore'] and ITEMS['healing_potion']['heal'] != 55
        count += 1
        # Validation rejects injection, currency misuse, invalid references and collisions.
        invalid = [
            ('sklep','market','inventory','["not_item"]'),
            ('sklep','market','inventory','["healing_potion","healing_potion"]'),
            ('receptura','iron_ingot','stations','["nonexistent"]'),
            ('przedmiot','healing_potion','heal','-1'),
            ('mob','temple_rat','damage_type','python'),
            ('npc','fisher_tomas','room','market'),
            ('npc','fisher_tomas','quest','bandit_patrol'),
            ('mob','temple_rat','damage_type','__import__("os")'),
            ('sklep','market','inventory','{"malicious":"not_a_list"}'),
        ]
        for section,key,field,value in invalid:
            try:
                m.stage_edit(section,key,field,value)
            except (ValueError, TypeError):
                count += 1
            else:
                raise AssertionError(f'Invalid OLC accepted: {section} {key} {field}')
        # Check newly-allowed fields after successful publish.
        assert 'rewizję 1' in m.apply(server,'admin')
        count += 1
        assert SHOPS['market'] == ['healing_potion','iron_ore']
        count += 1
        assert ITEMS['healing_potion']['heal'] == 55
        count += 1
        assert MOB_TEMPLATES['temple_rat']['silver'] == 0
        count += 1
        assert MOB_TEMPLATES['temple_rat']['damage_type'] == 'magic'
        count += 1
        assert NPCS['fisher_tomas']['room'] == 'live_olc4_npc_room'
        count += 1
        assert CRAFT_RECIPES['iron_ingot']['stations'] == ('forge','live_olc4_npc_room')
        count += 1
        assert CRAFT_RECIPES['iron_ingot']['quantity'] == 2
        count += 1
        assert 'edycja sklepów' in m.describe_news(before)
        count += 1
        assert m.revision == 1 and m.active['shop_edits']['market']['inventory'] == ['healing_potion','iron_ore']
        count += 1
        # History rollback preserves live room and moves NPC back.
        m.stage_edit('sklep','market','inventory','["healing_potion"]')
        assert 'rewizję 2' in m.apply(server,'admin')
        count += 1
        assert 'rewizję 3' in m.apply(server,'admin',rollback=True)
        count += 1
        assert SHOPS['market'] == ['healing_potion','iron_ore']
        count += 1
        # Existing SQLite revisions with no shop_edits remain compatible.
        old = {k:v for k,v in m.active.items() if k != 'shop_edits'}
        assert m._compat(old)['shop_edits'] == {}
        count += 1
    finally:
        m._remove(world)
        for dst,orig in zip(catalogs, originals):
            dst.clear(); dst.update(orig)
        con.close()
    return count

if __name__=='__main__':
    print('OLC 4.0: realne katalogi, publikacja, SQLite, cofanie:',run_regression(),'PASS')
