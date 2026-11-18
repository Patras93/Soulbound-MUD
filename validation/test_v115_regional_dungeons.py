# -*- coding: utf-8 -*-
"""Live catalog, SQLite and objective regression for 30 regional dungeons.
No soundpack, production DB, port, or player records required.
"""
import unittest
from collections import deque
from types import SimpleNamespace
from systems.v115.high_level_world import REGIONS
from systems.v115.playable_regions import room_id as sector_room_id
from systems.v115.regional_dungeons import (
    build_rooms, build_mobs, build_spawns, install_rooms, validate_spawns,
    is_authored_dungeon_room, room_id, warden_id, WIDTH, HEIGHT,
    ENTRY_X, ENTRY_Y,
)
from systems.v115.combat_objective_bridge import record_v115_victory
from systems.v115.objective_progress import total
from validation.test_v10400_atomic_live_character_xp import fixture

class RegionalDungeonsTest(unittest.TestCase):
    def test_full_catalog(self):
        self.assertEqual((len(build_rooms()),len(build_mobs()),len(build_spawns())),(720,60,360))
        self.assertEqual(len({x for x, y in build_spawns()}),360)
    def test_reachable_and_return(self):
        rooms=build_rooms()
        for region in REGIONS:
            start=room_id(region.key,0,0)
            visited={start}; frontier=deque([start]); edges=0
            while frontier:
                item=frontier.popleft()
                for direction,dest in rooms[item]['exits'].items():
                    if dest not in rooms:continue
                    edges+=1
                    reversed_dir={'north':'south','south':'north','east':'west','west':'east'}[direction]
                    self.assertEqual(rooms[dest]['exits'][reversed_dir],item)
                    if dest not in visited:visited.add(dest);frontier.append(dest)
            self.assertEqual(len(visited),24)
            self.assertIn(room_id(region.key,5,3),visited)
            self.assertGreater(edges//2,24)
    def test_real_world_anchors(self):
        from data.rooms import ROOMS
        from data.mobs import MOB_TEMPLATES
        from systems.content_registry import MOB_SPAWNS
        expected=build_spawns()
        for region in REGIONS:
            anchor=sector_room_id(region.key,ENTRY_X,ENTRY_Y)
            entry=room_id(region.key,0,0)
            self.assertEqual(ROOMS[anchor]['exits']['up'],entry)
            self.assertEqual(ROOMS[entry]['exits']['down'],anchor)
            self.assertIn(warden_id(region.key),MOB_TEMPLATES)
            self.assertEqual(MOB_TEMPLATES[warden_id(region.key)]['v115_dungeon_boss'],region.key)
        self.assertTrue(validate_spawns(ROOMS,MOB_TEMPLATES,expected))
        self.assertTrue(all(spawn in MOB_SPAWNS for spawn in expected))
        self.assertEqual(ROOMS['crossroads']['exits']['south'],'old_road')
    def test_every_dungeon_reachable_from_crossroads_and_back(self):
        from data.rooms import ROOMS
        def walk(start,reverse=False):
            graph={}
            for rid,room in ROOMS.items():
                for dest in room.get('exits',{}).values():
                    if dest not in ROOMS:continue
                    if reverse:graph.setdefault(dest,[]).append(rid)
                    else:graph.setdefault(rid,[]).append(dest)
            seen={start};q=deque([start])
            while q:
                for nxt in graph.get(q.popleft(),[]):
                    if nxt not in seen:seen.add(nxt);q.append(nxt)
            return seen
        all_from_crossroads=walk('crossroads')
        all_to_crossroads=walk('crossroads',reverse=True)
        for reg in REGIONS:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    rid=room_id(reg.key,x,y)
                    self.assertIn(rid,all_from_crossroads)
                    self.assertIn(rid,all_to_crossroads)
    def test_no_partial_map_on_missing_anchor(self):
        from systems.v115.playable_regions import build_rooms as base_rooms
        rooms=base_rooms()
        key=REGIONS[9].key
        del rooms[sector_room_id(key,ENTRY_X,ENTRY_Y)]
        before=len(rooms)
        with self.assertRaises(ValueError):install_rooms(rooms)
        self.assertEqual(len(rooms),before)
        self.assertNotIn('up',rooms[sector_room_id(REGIONS[0].key,ENTRY_X,ENTRY_Y)]['exits'])
    def test_no_partial_map_on_occupied_exit(self):
        from systems.v115.playable_regions import build_rooms as base_rooms
        rooms=base_rooms()
        anchor=sector_room_id(REGIONS[19].key,ENTRY_X,ENTRY_Y)
        rooms[anchor]['exits']['up']='existing_v115_path'
        before=len(rooms)
        with self.assertRaises(ValueError):install_rooms(rooms)
        self.assertEqual(len(rooms),before)
        self.assertNotIn('up',rooms[sector_room_id(REGIONS[0].key,ENTRY_X,ENTRY_Y)]['exits'])
    def test_live_adaptive_party_balance_one_to_six(self):
        """No multi-hour boss or lethal one-shot pressure at advertised level.

        Uses the existing adaptive engine, not a second v115 combat scaler.
        DPS is a deterministic unit-test profile, not a claim about real builds.
        No mercenaries count toward the six real-player slots.
        """
        from systems.adaptive_combat import (
            adaptive_target_max_hp_v11330,
            adaptive_target_incoming_fraction_v11330,
        )
        templates=build_mobs()
        rooms=build_rooms()
        for region in REGIONS:
            lvl=region.suggested_level
            boss=templates[warden_id(region.key)]
            chamber=rooms[room_id(region.key,WIDTH-1,HEIGHT-1)]
            self.assertEqual(chamber['generator_level'],lvl)
            self.assertEqual(boss['generator_level'],lvl)
            prev=0
            for real_players in range(1,7):
                dps=lvl*2*real_players
                hp=adaptive_target_max_hp_v11330(
                    boss['max_hp'],dps,boss,party_level=lvl,room=chamber)
                fight_seconds=hp/dps
                pressure=adaptive_target_incoming_fraction_v11330(
                    boss,real_players,player_level=lvl,room=chamber)
                # At appropriate level and a proportional party, the world
                # boss should last tens of seconds, not hours.
                self.assertGreaterEqual(fight_seconds,40)
                self.assertLessEqual(fight_seconds,70,
                    (region.key,real_players,fight_seconds))
                self.assertGreater(hp,prev)
                self.assertLess(pressure,0.3,(region.key,real_players,pressure))
                prev=hp

    def test_no_level_gates_and_optional_sound(self):
        import inspect, systems.v115.regional_dungeons as m
        self.assertNotIn('sound_events',inspect.getsource(m))
        for room in build_rooms().values():
            self.assertNotIn('min_level',room)
            self.assertNotIn('required_level',room)
            self.assertNotIn('soundpack',room)
    def test_dungeon_ep_visits_idempotent(self):
        from systems.v115.exploration_objective_bridge import record_v115_room_visit
        db, character=fixture()
        try:
            character.room_id=room_id(REGIONS[0].key,0,0)
            sess=SimpleNamespace(account_id=1,character=character,server=SimpleNamespace(db=db))
            from data.rooms import ROOMS
            rid=character.room_id
            self.assertEqual(record_v115_room_visit(sess,rid,ROOMS[rid])[0],2)
            self.assertEqual(record_v115_room_visit(sess,rid,ROOMS[rid])[0],0)
            self.assertEqual(total(db.conn,1,REGIONS[0].key,'explore'),1)
            self.assertEqual(total(db.conn,1,REGIONS[0].key,'discover_checkpoint'),1)
        finally:db.conn.close()
    def test_reject_spoofed_room(self):
        from systems.v115.exploration_objective_bridge import _valid_sector
        room=dict(build_rooms()[room_id(REGIONS[0].key,0,0)])
        self.assertEqual(_valid_sector(room_id(REGIONS[0].key,0,0),room),REGIONS[0].key)
        with self.assertRaises(ValueError):
            _valid_sector(room_id(REGIONS[1].key,0,0),room)
        with self.assertRaises(ValueError):
            _valid_sector('v115_dungeon_01_p_99_99',room)
    def _fight(self, template, room, mobid, event_id):
        db,c=fixture()
        try:
            c.room_id=room
            session=SimpleNamespace(account_id=1,character=c)
            session.server=SimpleNamespace(db=db,party_sessions=lambda *a,**kw:[session])
            mob=SimpleNamespace(alive=False,template_id=mobid)
            with db.conn.deferred_commits():
                count=record_v115_victory(session,mob,template,event_id=event_id)
            return (count,total(db.conn,1,REGIONS[0].key,'finish_dungeon'),
                db.conn.execute('SELECT COUNT(*) FROM v115_objective_claims').fetchone()[0])
        finally:db.conn.close()
    def test_finish_only_real_warden(self):
        region=REGIONS[0].key
        from data.mobs import MOB_TEMPLATES
        template=MOB_TEMPLATES[warden_id(region)]
        room=room_id(region,WIDTH-1,HEIGHT-1)
        count,progress,claims=self._fight(template,room,warden_id(region),'actual-dungeon-clear')
        self.assertEqual(count,3)
        self.assertEqual(progress,1)
        self.assertGreaterEqual(claims,3)
    def test_reject_wrong_boss_or_room(self):
        region=REGIONS[0].key
        from data.mobs import MOB_TEMPLATES
        template=MOB_TEMPLATES[warden_id(region)]
        with self.assertRaises(ValueError):
            self._fight(template,room_id(region,0,0),warden_id(region),'entry-not-clear')
        with self.assertRaises(ValueError):
            self._fight(template,room_id(region,WIDTH-1,HEIGHT-1),'random-mob','fake-kill')
        self.assertEqual(self._fight({'v115_region_key':region,'boss':True},
                            room_id(region,WIDTH-1,HEIGHT-1),warden_id(region),'unflagged')[1],0)
    def test_duplicate_boss_event_paid_once(self):
        db,c=fixture()
        try:
            region=REGIONS[0].key
            c.room_id=room_id(region,WIDTH-1,HEIGHT-1)
            sess=SimpleNamespace(account_id=1,character=c)
            sess.server=SimpleNamespace(db=db,party_sessions=lambda *a,**kw:[sess])
            from data.mobs import MOB_TEMPLATES
            template=MOB_TEMPLATES[warden_id(region)]
            mob=SimpleNamespace(alive=False,template_id=warden_id(region))
            with db.conn.deferred_commits():
                first=record_v115_victory(sess,mob,template,event_id='boss-abc')
            wallet_first=c.silver
            with db.conn.deferred_commits():
                second=record_v115_victory(sess,mob,template,event_id='boss-abc')
            self.assertEqual((first,second),(3,0))
            self.assertEqual(wallet_first,c.silver)
            self.assertEqual(total(db.conn,1,region,'finish_dungeon'),1)
        finally: db.conn.close()

    def test_runtime_scaled_warden_is_a_real_clear(self):
        from copy import deepcopy
        from data.mobs import MOB_TEMPLATES
        from systems.v115.regional_dungeons import is_authored_warden_template
        reg=REGIONS[0].key
        original=warden_id(reg)
        clone=deepcopy(MOB_TEMPLATES[original])
        clone['base_template']=original
        clone['world_threat_overdrive_v0384']=True
        runtime_id=f'{original}__world_v0384_850'
        self.assertTrue(is_authored_warden_template(runtime_id,clone,reg))
        count,cleared,claims=self._fight(clone,room_id(reg,WIDTH-1,HEIGHT-1),runtime_id,'runtime-real-kill')
        self.assertEqual((count,cleared),(3,1))
        self.assertGreaterEqual(claims,3)

    def test_spoofed_warden_clones_do_not_clear(self):
        from copy import deepcopy
        from data.mobs import MOB_TEMPLATES
        from systems.v115.regional_dungeons import is_authored_warden_template
        reg=REGIONS[0].key
        original=warden_id(reg)
        clone=deepcopy(MOB_TEMPLATES[original])
        clone['base_template']='unrelated_boss'
        fake_id=original+'__world_v0384_850'
        self.assertFalse(is_authored_warden_template(fake_id,clone,reg))
        with self.assertRaises(ValueError):
            self._fight(clone,room_id(reg,WIDTH-1,HEIGHT-1),fake_id,'fake-base')
        clone['base_template']=original
        self.assertFalse(is_authored_warden_template('other_boss__world_v0384_850',clone,reg))
        clone['v115_dungeon_boss']=REGIONS[1].key
        self.assertFalse(is_authored_warden_template(fake_id,clone,reg))

    def test_no_nonregional_warden_clear(self):
        from systems.v115.regional_dungeons import is_authored_warden_template
        for region in REGIONS:
            self.assertFalse(is_authored_warden_template('ordinary_mob',{'boss':True},region.key))

if __name__=='__main__':unittest.main()
