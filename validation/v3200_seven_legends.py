# -*- coding: utf-8 -*-
"""v3.20.0: Seven Legends static contracts and realistic ore-to-ring smoke tests."""
import asyncio
import os
import tempfile
from types import SimpleNamespace


def check_all():
    import server
    from core.classes_skills import CLASS_SKILLS, CLASSES
    from systems.equipment_crafting import JEWELCRAFT_RECIPES, SHOPS
    from world.legends_v3200 import REALMS, OLD_ARCS, _reachable
    from storage.database import Database
    from player.character import Character
    from player.session import Session
    from data.catalogs import ITEMS

    counts = server.V3200_LEGENDS_STATS
    assert counts == {'rooms': 320, 'npcs': 56, 'mobs': 64,
                      'spawns': 120, 'quests': 392, 'items': 56}, counts
    rooms, npcs, mobs, quests = server.ROOMS, server.NPCS, server.MOB_TEMPLATES, server.QUESTS
    reach = _reachable(rooms)
    new_rooms = {k: v for k, v in rooms.items() if k.startswith('v3200_')}
    assert len(new_rooms) == 320 and set(new_rooms) <= reach, 'All routes must be accessible from the old world'
    for room_id, room in new_rooms.items():
        for direction, dst in room['exits'].items():
            assert dst in rooms, (room_id, direction, dst)
            from world.legends_v3100 import OPPOSITE
            assert rooms[dst]['exits'].get(OPPOSITE[direction]) == room_id, (room_id, direction, dst)
        assert not room.get('traps') and not room.get('random_traps'), room_id
    new_npcs = {k: v for k, v in npcs.items() if k.startswith('v3200_')}
    assert len(new_npcs) == 56
    occupied = set()
    for npc_id, npc in npcs.items():
        rid = npc.get('room')
        assert rid in rooms, (npc_id, rid)
        assert rid not in occupied, ('Two NPCs in one room', npc_id, rid)
        occupied.add(rid)
    new_quests = {k: v for k, v in quests.items() if k.startswith('v3200_')}
    assert len(new_quests) == 392
    for qid, quest in new_quests.items():
        prior = quest.get('requires_quest')
        assert not prior or prior in quests, (qid, prior)
        kind = quest['kind']
        if kind == 'talk_npc': assert quest['target'] in npcs, qid
        if kind == 'kill': assert quest['target'] in mobs, qid
        if kind == 'collect': assert quest['target'] in ITEMS, qid
        assert quest['needed'] > 0, qid
    from world.legends_v3100 import CLASS_NAMES as LEGACY_CLASS_NAMES
    assert len(LEGACY_CLASS_NAMES) == 14
    for cls in LEGACY_CLASS_NAMES:
        mastery = [s for s in CLASS_SKILLS[cls] if s['id'].startswith('v3200_')]
        assert len(mastery) == 3 and {s['unlock'] for s in mastery} == {260,420,600}, cls
    assert len(OLD_ARCS) == 32 and len(REALMS) == 8
    for realm in REALMS:
        slug=realm[0]
        boss=mobs['v3200_'+slug+'_superboss']
        assert boss['world_boss'] and boss['boss_mechanic'] and len(boss['attack_elements_v11339'])==2, slug
    for room_id,mob in server.MOB_SPAWNS:
        if str(mob).startswith('v3200_'):
            assert room_id in rooms and mob in mobs

    # Really buy ores in the normal old-world Forge shop, then travel to the
    # actual jeweler station to craft quality variants of two quest rings.
    assert 'iron_ore' in SHOPS['forge']
    assert JEWELCRAFT_RECIPES['jewel_iron_ring']['ingredients']=={'iron_ore':2}

    async def scenario():
        with tempfile.TemporaryDirectory(prefix='sb-v3200-ring-') as dirname:
            db=Database(os.path.join(dirname,'test.db'))
            aid=db.create_account('v3200_ore_test', 'test_pw')
            from core.classes_skills import CLASSES, RACES
            db.create_character(aid,'RingTester',RACES[0],CLASSES[0],
                                {'nom':'Tester','gen':'Testera','dat':'Testerowi',
                                 'acc':'Testera','ins':'Testerem','loc':'Testerze','voc':'Testerze'})
            sess=Session.__new__(Session)
            sess.account_id=aid
            sess.character=Character.from_row(db.character_for_account(aid))
            sess.character.gold=100000
            sess.character.room_id='forge'
            sess.server=SimpleNamespace(db=db,sessions=set(),parties={})
            sess.combat_mob_key=None
            messages=[]
            async def send(message,*args,**kwargs): messages.append(str(message))
            sess.send=send
            sess.recipe_action_seconds=lambda *args: 0
            # Purchasing in the two documented forms, old numeric and new name.
            number=SHOPS['forge'].index('iron_ore')+1
            await sess.buy(f'{number} 2')
            await sess.buy('2 ruda żelaza')
            assert db.storage_qty(aid,'bag','iron_ore') == 4, messages[-5:]
            assert sess.available_recipe_item('iron_ore') == 4
            sess.server.db.add_item(aid,'jeweler_pliers',1)
            sess.character.room_id='jeweler_workshop'
            for i in range(2):
                result=await sess.jewelcraft_item('Żelazny Pierścień Jubilerski')
                assert result, messages[-6:]
                assert sess.available_recipe_item('iron_ore') == 2*(1-i)
            rings=sum(row['quantity'] for row in db.inventory(aid)
                      if row['item_id']=='jewel_iron_ring'
                      or row['item_id'].startswith('jewel_iron_ring__')
                      or row['item_id'].startswith('crafted_jewel_iron_ring')
                      or row['item_id'].endswith('_jewel_iron_ring'))
            assert rings >= 2, [(row['item_id'],row['quantity']) for row in db.inventory(aid) if 'ring' in row['item_id']]
            assert not await sess.jewelcraft_item('Żelazny Pierścień Jubilerski')
            assert any('Brakuje składników' in m for m in messages)
            assert any('4 rud' in m for m in messages)
            db.conn.close()

    asyncio.run(scenario())
    print('SIEDEM LEGEND v3.20.0: 320 rooms, 56 NPC, 392 quests, 42 class skills, 8 superbosses, 32 older regions PASS')
    print('ŻELAZNY PIERŚCIEŃ: kupno w Kuźni (numer i nazwa), sakwa, 2 craft x2 rudy, odmowa trzeciego bez rudy PASS')


if __name__ == '__main__':
    check_all()
