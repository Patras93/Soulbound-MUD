# -*- coding: utf-8 -*-
"""Bieżąca mapa: połączenia Stary Cmentarz/Krypta/Nekropolia i krawędzie siatek.

Używa realnego, pełnego katalogu po rejestracji dawnych/proceduralnych terenów.
Nie zastępuje PREDEPLOY Windows 60/60 PLUS.
"""
from __future__ import annotations
import re,sys,unittest
from pathlib import Path
from collections import defaultdict,deque
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
import world.dynamic_content  # side effects: rzeczywista instalacja krain
from systems.current_world_perimeter import CEMETERY_CRYPT_EDGE,CEMETERY_NECROPOLIS_EDGE

class WorldBorderRoutes(unittest.TestCase):
    def test_cemetery_crypt_and_necropolis_at_opposite_edges(self):
        a='graveyard';c=CEMETERY_CRYPT_EDGE;n=CEMETERY_NECROPOLIS_EDGE
        self.assertEqual(ROOMS[a]['zone'],'Stary Cmentarz')
        self.assertEqual(ROOMS[a]['exits']['up'],'v115_graveyard_00_00')
        self.assertIn('północno-wschodnim',ROOMS[a]['desc'])
        self.assertNotIn('down',ROOMS[a]['exits'])
        self.assertNotIn('east',ROOMS[a]['exits'])
        self.assertEqual(ROOMS[c]['exits']['down'],'crypt_entrance')
        self.assertEqual(ROOMS['crypt_entrance']['exits']['up'],c)
        self.assertEqual(ROOMS[n]['exits']['east'],'necropolis_gate')
        self.assertEqual(ROOMS['necropolis_gate']['exits']['west'],n)
        self.assertEqual({c,n},{'v115_graveyard_11_11','v115_graveyard_11_00'})
        self.assertEqual(ROOMS[c]['zone'],ROOMS[n]['zone'])
        self.assertEqual(ROOMS['crypt_entrance']['exits']['south'],'crypt_hall')
        self.assertEqual(ROOMS['crypt_entrance']['exits']['west'],'v116_depths_krypta_19_00')

    def test_all_existing_grid_interzone_doors_at_perimeter(self):
        """Wszystkie prostokątne strefy (w tym 30 Horyzontów, 30 lochów)."""
        pat=re.compile(r'(?:_p)?_(\d{2})_(\d{2})$')
        grid=defaultdict(list)
        for rid,room in ROOMS.items():
            m=pat.search(rid)
            if m:grid[room['zone']].append((rid,int(m[1]),int(m[2])))
        bounds={z:(min(x for _,x,y in entries),max(x for _,x,y in entries),
                   min(y for _,x,y in entries),max(y for _,x,y in entries))
                for z,entries in grid.items() if len(entries)>=20}
        checked=0;outward=0
        for rid,room in ROOMS.items():
            for direction,other in room.get('exits',{}).items():
                # Część pięter powstaje na żądanie; nie są statycznym pokojem.
                if other not in ROOMS or room['zone']==ROOMS[other]['zone']:continue
                outward+=1
                for endpoint in (rid,other):
                    z=ROOMS[endpoint]['zone'];m=pat.search(endpoint)
                    if z not in bounds or not m:continue
                    x,y=int(m[1]),int(m[2]);lowx,highx,lowy,highy=bounds[z]
                    self.assertTrue(x in (lowx,highx) or y in (lowy,highy),
                                    (rid,direction,other,z,endpoint))
                    checked+=1
        self.assertGreater(outward,400)
        self.assertGreater(checked,400)

    def test_30_horizon_gateways_have_long_border_trails(self):
        from systems.v115.playable_regions import HUB, room_id
        from systems.v115.high_level_world import REGIONS
        from systems.current_world_perimeter import horizon_approach_id, HORIZON_APPROACH_LENGTH
        self.assertEqual((len(REGIONS),HORIZON_APPROACH_LENGTH),(30,12))
        for index, region in enumerate(REGIONS, 1):
            node = HUB if index == 1 else f'v115_wezel_{index:02d}'
            entry = room_id(region.key,0,0)
            first = horizon_approach_id(index,1)
            last = horizon_approach_id(index,12)
            self.assertEqual(ROOMS[node]['exits']['east'],first)
            self.assertEqual(ROOMS[entry]['exits']['west'],last)
            self.assertEqual(ROOMS[node]['zone'],'Szlak Horyzontów')
            self.assertNotEqual(ROOMS[entry]['zone'],ROOMS[node]['zone'])
            for step in range(1,13):
                rid = horizon_approach_id(index,step)
                exits = ROOMS[rid]['exits']
                self.assertEqual(ROOMS[rid]['zone'],'Szlak Horyzontów')
                self.assertEqual(exits['west'],node if step==1 else horizon_approach_id(index,step-1))
                self.assertEqual(exits['east'],entry if step==12 else horizon_approach_id(index,step+1))
                self.assertNotIn('min_level',ROOMS[rid])
                self.assertNotIn('trap',ROOMS[rid])
                self.assertNotIn('auto_aggro',ROOMS[rid])
            self.assertEqual(ROOMS[last]['exits']['east'],entry)
        self.assertEqual(sum(rid.startswith('v116_horizon_border_') for rid in ROOMS),360)


    def test_dzicz_gory_bagna_have_true_perimeter_gateways(self):
        from systems.current_world_perimeter import wild_border_id, WILD_BORDER_SIZE
        self.assertEqual(WILD_BORDER_SIZE, 12)
        self.assertEqual(sum(i.startswith('v116_wild_edge_') for i in ROOMS), 432)
        attachments = (
            ('forester_lodge','north','dzicz','south','Północne Rubieże Dziczy'),
            ('lava_fissure','north','gory','south','Grzbiet Górski'),
            ('swamp_hunter_post','east','bagna','west','Rubieże Czarnych Bagien'),
        )
        for anchor,direction,key,back,zone in attachments:
            start = wild_border_id(key,0,0)
            self.assertEqual(ROOMS[anchor]['exits'][direction],start)
            self.assertEqual(ROOMS[start]['exits'][back],anchor)
            for y in range(12):
                for x in range(12):
                    rid=wild_border_id(key,x,y)
                    r=ROOMS[rid]
                    self.assertEqual(r['zone'],zone)
                    self.assertNotIn('trap',r)
                    self.assertNotIn('auto_aggro',r)
                    self.assertNotIn('min_level',r)
                    for d,v in r['exits'].items():
                        if v in ROOMS and ROOMS[v]['zone']!=zone:
                            self.assertTrue(x in (0,11) or y in (0,11),(rid,d,v))
        # Nie wolno zostawić skrótów w środkowych pokojach dawnych tras.
        self.assertNotIn('east',ROOMS['hill']['exits'])
        self.assertNotIn('west',ROOMS['mountain_pass']['exits'])
        # Dawny skrót w Bagna pozostaje usunięty; south służy teraz
        # wyłącznie do powrotu na Rozdroże w obrębie Dziczy.
        self.assertEqual(ROOMS['deep_grove']['exits']['south'], 'crossroads')
        self.assertNotIn('north',ROOMS['swamp_boardwalk']['exits'])
        links = (
            (('dzicz',11,11,'east'),('gory',0,11,'west')),
            (('dzicz',11,0,'east'),('bagna',0,11,'west')),
        )
        for (ka,xa,ya,da),(kb,xb,yb,db) in links:
            a,b=wild_border_id(ka,xa,ya),wild_border_id(kb,xb,yb)
            self.assertEqual(ROOMS[a]['exits'][da],b)
            self.assertEqual(ROOMS[b]['exits'][db],a)
            self.assertNotEqual(ROOMS[a]['zone'],ROOMS[b]['zone'])

    def test_wild_perimeter_grid_is_reachable_from_legacy_start(self):
        from systems.current_world_perimeter import wild_border_id
        # Wszystkie sektory są osiągalne bez walki, bossa, bramki czy teleportu.
        for old,key in (('forester_lodge','dzicz'),('lava_fissure','gory'),
                        ('swamp_hunter_post','bagna')):
            start = wild_border_id(key,0,0)
            reached = {start};q=deque([start])
            while q:
                rid=q.popleft()
                for dest in ROOMS[rid]['exits'].values():
                    if dest.startswith('v116_wild_edge_'+key+'_') and dest not in reached:
                        reached.add(dest);q.append(dest)
            self.assertEqual(len(reached),144,(old,key))


    def test_whisper_grove_to_meadows_travels_only_at_both_borders(self):
        from systems.current_world_perimeter import historical_border_id, HISTORICAL_BORDER_LENGTH
        self.assertEqual(HISTORICAL_BORDER_LENGTH, 12)
        self.assertEqual(sum(k.startswith('v116_meadow_wild_border_') for k in ROOMS),24)
        self.assertEqual(ROOMS['whisper_grove']['exits']['east'],historical_border_id('dzicz',1))
        self.assertEqual(ROOMS['flower_meadow']['exits']['west'],historical_border_id('laki',12))
        self.assertNotIn('flower_meadow', ROOMS['whisper_grove']['exits'].values())
        self.assertNotIn('whisper_grove', ROOMS['flower_meadow']['exits'].values())
        for key,zone in (('dzicz','Dzicz'),('laki','Łąki')):
            for step in range(1,13):
                rid=historical_border_id(key,step)
                room=ROOMS[rid];self.assertEqual(room['zone'],zone)
                self.assertNotIn('trap',room)
                self.assertNotIn('auto_aggro',room)
                self.assertNotIn('min_level',room)
                for direction,dest in room['exits'].items():
                    self.assertIn(rid,ROOMS[dest]['exits'].values(),(rid,direction,dest))
                    if ROOMS[dest]['zone'] != zone:
                        self.assertEqual((key,step,direction),('dzicz',12,'east') if key=='dzicz' else ('laki',1,'west'))
        self.assertEqual(ROOMS[historical_border_id('dzicz',12)]['exits']['east'],historical_border_id('laki',1))
        self.assertEqual(ROOMS[historical_border_id('laki',1)]['exits']['west'],historical_border_id('dzicz',12))
        # Od Gaju do Łąki rzeczywiście prowadzi długa, bezpieczna droga.
        cursor='whisper_grove';steps=0
        while cursor != 'flower_meadow' and steps < 30:
            cursor = ROOMS[cursor]['exits']['east'];steps+=1
        self.assertEqual((cursor,steps),('flower_meadow',25))

    def test_ruined_watchtower_has_no_one_way_shortcut_from_crossroads(self):
        self.assertNotIn('east',ROOMS['crossroads']['exits'])
        self.assertEqual(ROOMS['stone_bridge']['exits']['east'],'ruined_watchtower')
        self.assertEqual(ROOMS['ruined_watchtower']['exits']['west'],'stone_bridge')
        # Do Ruin nadal można dotrzeć z Rozdroża zwykłą drogą i wrócić.
        for start,end in (('crossroads','ruined_watchtower'),('ruined_watchtower','crossroads')):
            seen={start};q=deque([start])
            while q and end not in seen:
                current=q.popleft()
                for other in ROOMS[current]['exits'].values():
                    if other in ROOMS and other not in seen:
                        seen.add(other);q.append(other)
            self.assertIn(end,seen,(start,end))


    def test_three_old_interzone_links_now_cross_only_at_both_route_ends(self):
        from systems.current_world_perimeter import legacy_border_id, LEGACY_BORDER_LENGTH
        self.assertEqual(LEGACY_BORDER_LENGTH, 12)
        self.assertEqual(sum(rid.startswith('v116_old_border_') for rid in ROOMS), 72)
        routes = (
            ('jezioro', 'lakeside_meadow', 'south', 'lake_shore', 'north'),
            ('rzeka', 'mint_meadow', 'east', 'riverbank', 'west'),
            ('las', 'deep_grove', 'west', 'forest_edge', 'east'),
        )
        opposites = {'north':'south','south':'north','east':'west','west':'east'}
        for key, old_a, forward_a, old_b, forward_b in routes:
            self.assertEqual(ROOMS[old_a]['exits'][forward_a], legacy_border_id(key,'a',1))
            self.assertEqual(ROOMS[old_b]['exits'][forward_b], legacy_border_id(key,'b',1))
            self.assertNotIn(old_b,ROOMS[old_a]['exits'].values())
            self.assertNotIn(old_a,ROOMS[old_b]['exits'].values())
            for side,old,forward in (('a',old_a,forward_a),('b',old_b,forward_b)):
                back=opposites[forward]
                other='b' if side=='a' else 'a'
                for step in range(1,13):
                    rid=legacy_border_id(key,side,step)
                    room=ROOMS[rid]
                    self.assertEqual(room['zone'],ROOMS[old]['zone'])
                    self.assertNotIn('trap',room)
                    self.assertNotIn('auto_aggro',room)
                    self.assertNotIn('min_level',room)
                    self.assertEqual(room['exploration_ep'],0)
                    self.assertEqual(room['exits'][back],
                                     old if step==1 else legacy_border_id(key,side,step-1))
                    expected=(legacy_border_id(key,other,12) if step==12
                              else legacy_border_id(key,side,step+1))
                    self.assertEqual(room['exits'][forward],expected)
                    self.assertIn(rid,ROOMS[expected]['exits'].values())
                    if ROOMS[expected]['zone']!=room['zone']:
                        self.assertEqual(step,12)
            # Pełna trasa od starego pokoju do starego pokoju trwa 25 kroków.
            cursor=old_a
            for _ in range(12):cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,legacy_border_id(key,'a',12))
            cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,legacy_border_id(key,'b',12))
            for _ in range(12):cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,old_b)


    def test_v11619_laki_zielarskie_both_sides_finish_at_border(self):
        from systems.current_world_perimeter import HERBAL_BORDER_LENGTH, herbal_border_id
        self.assertEqual(HERBAL_BORDER_LENGTH, 12)
        self.assertEqual(sum(k.startswith('v116_herbal_border_') for k in ROOMS), 48)
        pairs=(('mieta','meadow','east','mint_meadow','west'),
               ('ziola','flower_meadow','north','herb_meadow_hub','south'))
        opposite={'north':'south','south':'north','east':'west','west':'east'}
        for key,a,forward_a,b,forward_b in pairs:
            self.assertEqual(ROOMS[a]['exits'][forward_a],herbal_border_id(key,'a',1))
            self.assertEqual(ROOMS[b]['exits'][forward_b],herbal_border_id(key,'b',1))
            self.assertNotEqual(ROOMS[a]['zone'],ROOMS[b]['zone'])
            self.assertNotIn(b,ROOMS[a]['exits'].values())
            self.assertNotIn(a,ROOMS[b]['exits'].values())
            for side,old,forward in (('a',a,forward_a),('b',b,forward_b)):
                reverse=opposite[forward]; other='b' if side=='a' else 'a'
                for step in range(1,13):
                    rid=herbal_border_id(key,side,step)
                    room=ROOMS[rid]
                    self.assertEqual(room['zone'],ROOMS[old]['zone'])
                    self.assertNotIn('trap',room)
                    self.assertNotIn('auto_aggro',room)
                    self.assertNotIn('min_level',room)
                    self.assertEqual(room['exploration_ep'],0)
                    self.assertEqual(room['exits'][reverse],old if step==1 else herbal_border_id(key,side,step-1))
                    target=(herbal_border_id(key,other,12) if step==12
                            else herbal_border_id(key,side,step+1))
                    self.assertEqual(room['exits'][forward],target)
                    self.assertIn(rid,ROOMS[target]['exits'].values())
                    if ROOMS[target]['zone']!=room['zone']:
                        self.assertEqual(step,12)
            cursor=a
            for _ in range(12): cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,herbal_border_id(key,'a',12))
            cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,herbal_border_id(key,'b',12))
            for _ in range(12): cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,b)


    def test_v11620_five_mountain_village_cave_camp_routes_on_both_edges(self):
        from systems.current_world_perimeter import MOUNTAIN_BORDER_LENGTH, mountain_border_id
        self.assertEqual(MOUNTAIN_BORDER_LENGTH,12)
        self.assertEqual(sum(k.startswith('v116_mountain_border_') for k in ROOMS),120)
        pairs=(('wioska','mountain_pass','east','mountain_village','west'),
               ('trolle','mountain_troll_trail','south','troll_cave_entrance','north'),
               ('lod','ice_pass','east','ice_cave_mouth','west'),
               ('gobliny','goblin_camp','east','goblin_cave_mouth','west'),
               ('bandyci','frontier_watchpost','east','bandit_camp','west'))
        opposite={'north':'south','south':'north','east':'west','west':'east'}
        for key,a,forward_a,b,forward_b in pairs:
            self.assertNotEqual(ROOMS[a]['zone'],ROOMS[b]['zone'])
            self.assertEqual(ROOMS[a]['exits'][forward_a],mountain_border_id(key,'a',1))
            self.assertEqual(ROOMS[b]['exits'][forward_b],mountain_border_id(key,'b',1))
            self.assertNotIn(b,ROOMS[a]['exits'].values())
            self.assertNotIn(a,ROOMS[b]['exits'].values())
            for side,old,forward in (('a',a,forward_a),('b',b,forward_b)):
                other = 'b' if side=='a' else 'a'
                back = opposite[forward]
                for step in range(1,13):
                    rid=mountain_border_id(key,side,step)
                    r=ROOMS[rid]
                    self.assertEqual(r['zone'],ROOMS[old]['zone'])
                    self.assertNotIn('trap',r)
                    self.assertNotIn('auto_aggro',r)
                    self.assertNotIn('min_level',r)
                    self.assertEqual(r['exploration_ep'],0)
                    self.assertEqual(r['exits'][back],old if step==1 else mountain_border_id(key,side,step-1))
                    target=(mountain_border_id(key,other,12) if step==12
                            else mountain_border_id(key,side,step+1))
                    self.assertEqual(r['exits'][forward],target)
                    self.assertIn(rid,ROOMS[target]['exits'].values())
                    if ROOMS[target]['zone']!=r['zone']:
                        self.assertEqual(step,12)
            cursor=a
            for _ in range(12):cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,mountain_border_id(key,'a',12))
            cursor=ROOMS[cursor]['exits'][forward_a]
            self.assertEqual(cursor,mountain_border_id(key,'b',12))
            for _ in range(12):cursor=ROOMS[cursor]['exits'][opposite[forward_b]]
            self.assertEqual(cursor,b)

    def test_all_crosszone_routes_are_reversible_except_serpentarius_trial(self):
        """An arena gate is not a regular world-border passage."""
        special = (
            'uoss_deep_dungeon_floor_0_v11331',
            'forward',
            'uoss_superboss_arena_serpentarius_v11136',
        )
        crosszone = [
            (rid, direction, other)
            for rid, room in ROOMS.items()
            for direction, other in room.get('exits', {}).items()
            if other in ROOMS and room['zone'] != ROOMS[other]['zone']
        ]
        missing_return = [
            route for route in crosszone
            if route[0] not in ROOMS[route[2]].get('exits', {}).values()
        ]
        self.assertGreaterEqual(len(crosszone), 440)
        self.assertEqual(missing_return, [special])
        floor0, direction, arena = special
        self.assertEqual(ROOMS[floor0]['exits'][direction], arena)
        self.assertEqual(ROOMS[floor0]['exits']['up'],
                         'uoss_deep_dungeon_entry_v11331')
        # Preserve the historic boss-chain exit: never silently turn it into
        # an unrestricted shortcut to the Floor 0 checkpoint.
        self.assertEqual(ROOMS[arena]['exits']['back'],
                         'uoss_superboss_arena_black_rabite_v11136')

    def test_serpentarius_personal_floor100_and_lockout_are_enforced(self):
        """Existing movement and elevator guards must not be bypassed."""
        from datetime import datetime, timedelta, timezone
        from types import SimpleNamespace
        from data.mobs import MOB_TEMPLATES
        from player.session_mixins.dungeon_progression import SessionDungeonProgressionMixin
        from world.uoss_superboss_runtime import superboss_member_entry_error_v11331

        class DB:
            discovery = ()
            cleared_at = None
            def collection_entry_ids(self, account, collection):
                return self.discovery if collection == 'deep_dungeon_discovery' else ()
            def collection_entry_discovered_at(self, account, collection, key):
                return self.cleared_at

        db = DB()
        session = SimpleNamespace(
            account_id='fixture-serpentarius',
            character=SimpleNamespace(name='Audyt', character_level=250),
            server=SimpleNamespace(db=db),
        )
        target = 'uoss_superboss_arena_serpentarius_v11136'
        gate = SessionDungeonProgressionMixin.uoss_serpentarius_room_entry_error_v11331

        self.assertIn('piętra 100', gate(session, target))
        self.assertEqual(gate(session, 'uoss_superboss_arena_odin_v11136'), '')
        db.discovery = ('floor_100',)
        self.assertEqual(superboss_member_entry_error_v11331(session, 'serpentarius'), '')
        self.assertEqual(gate(session, target), '')

        db.cleared_at = datetime.now(timezone.utc).isoformat()
        self.assertIn('blokadę', gate(session, target))
        db.cleared_at = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        self.assertEqual(gate(session, target), '')

        spec = MOB_TEMPLATES['uoss_superboss_serpentarius_v11136']
        self.assertTrue(spec.get('no_exit_after_start'))
        self.assertFalse(spec.get('auto_aggro'))
        self.assertEqual(spec.get('round_limit'), 100)


    def test_guild_monk_and_guardian_shops_are_reachable_again(self):
        """Sale klasowe nie mogą znikać po podłączeniu Hangaru Meca."""
        from collections import deque
        martial = ROOMS['guild_martial_hall']['exits']
        body = ROOMS['guild_body_hall']['exits']
        self.assertEqual(martial['east'], 'guild_mec_chamber')
        self.assertEqual(ROOMS['guild_mec_chamber']['exits']['south'],
                         'guild_martial_hall')
        self.assertEqual(martial['down'], 'guild_body_hall')
        self.assertEqual(body['up'], 'guild_martial_hall')
        self.assertEqual(body['west'], 'guild_martial_hall')
        self.assertEqual(body['north'], 'guild_monk_chamber')
        self.assertEqual(body['east'], 'guild_guardian_chamber')
        # Świątynia jest zawsze pierwszym pokojem po zalogowaniu.
        visited = {'temple'}
        queue = deque(['temple'])
        while queue:
            current = queue.popleft()
            for dest in ROOMS[current].get('exits', {}).values():
                if dest in ROOMS and dest not in visited:
                    visited.add(dest)
                    queue.append(dest)
        for rid in ('guild_body_hall', 'guild_monk_chamber',
                    'guild_guardian_chamber', 'guild_mec_chamber'):
            self.assertIn(rid, visited)
        # Floor 0 jest wyjątkową, odblokowywaną osobno windą.
        self.assertEqual(set(ROOMS) - visited,
                         {'uoss_deep_dungeon_floor_0_v11331'})

    def test_guild_training_install_is_atomic_when_direction_occupied(self):
        from copy import deepcopy
        from systems.current_world_perimeter import install_guild_training_access
        keys = ('guild_martial_hall', 'guild_body_hall', 'guild_mec_chamber',
                'guild_monk_chamber', 'guild_guardian_chamber')
        clean = {key: deepcopy(ROOMS[key]) for key in keys}
        for rid, direction in (('guild_martial_hall', 'down'),
                               ('guild_body_hall', 'up')):
            fixture = deepcopy(clean)
            fixture[rid]['exits'][direction] = 'zajety_stary_kierunek'
            before = deepcopy(fixture)
            with self.assertRaisesRegex(ValueError, 'Zajety kierunek'):
                install_guild_training_access(fixture)
            self.assertEqual(fixture, before)
        fixture = deepcopy(clean)
        del fixture['guild_martial_hall']['exits']['down']
        del fixture['guild_body_hall']['exits']['up']
        self.assertEqual(install_guild_training_access(fixture), 2)
        self.assertEqual(fixture, clean)


    def test_lazy_dungeon_gateways_have_safe_first_floor_and_deeper_returns(self):
        """11 statycznych wejsc: zwrotne krawedzie prawdziwych generatorow.

        Kontrola z AST nie uruchamia masowych spawnów ani produkcyjnej bazy.
        Sprawdza dokladne wyrazenia kierunkow w istniejacych generatorach.
        """
        import ast
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        economy = root / 'world/economy_quests.py'
        deep = root / 'world/uoss_superboss_world.py'
        cache = {}
        def exits_from_function(source, name, position, floor, dungeon=''):
            if source not in cache:
                cache[source] = ast.parse(source.read_text(encoding='utf-8'))
            funcs = [n for n in cache[source].body if isinstance(n, ast.FunctionDef)
                     and n.name == name]
            self.assertEqual(len(funcs), 1, name)
            assignments = [n.value for n in ast.walk(funcs[0])
                           if isinstance(n, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == 'exits'
                                   for t in n.targets)]
            self.assertGreater(len(assignments), position, name)
            # Source expressions may use only these hand-picked helpers,
            # allowing validation without evaluating a whole gameplay module.
            context = {'floor':floor, 'dungeon':dungeon,
                       'ASTRAL_MIN_FLOOR':100, 'MINE_MIN_FLOOR':1,
                       'UOSS_DEEP_DUNGEON_ENTRY_V11331':'uoss_deep_dungeon_entry_v11331',
                       'previous': 'LEVEL_BEFORE', 'next_room': 'LEVEL_AFTER'}
            context.update({key: (lambda f, prefix=prefix: f'{prefix}{f}')
                            for key, prefix in (
                                ('crypt_floor_id','crypt_floor_'),
                                ('mythic_crypt_floor_id','mythic_crypt_floor_'),
                                ('astral_floor_id','astral_floor_'),
                                ('mythic_astral_floor_id','mythic_astral_floor_'),
                                ('giant_fortress_floor_id','giant_fortress_'),
                                ('mine_floor_id','mine_floor_'),
                                ('uoss_deep_dungeon_floor_id_v11331','uoss_deep_dungeon_floor_'),
                            )})
            context['uoss_deep_dungeon_floor_id_v11331'] = (
                lambda f: f'uoss_deep_dungeon_floor_{f}_v11331')
            expr = assignments[position]
            self.assertTrue(isinstance(expr, (ast.Dict, ast.IfExp)), name)
            result = eval(compile(ast.Expression(expr), str(source), 'eval'),
                          {'__builtins__': {}}, context)
            self.assertIsInstance(result, dict, name)
            return result

        cases = (
            # Zrodlo, kierunek, pokoj na zadanie, kierunek powrotny,
            # generator, pozycja pierwszej definicji, pietro, rodzina.
            ('astral_gate','up','astral_floor_100','down', economy,
             'create_infinite_astral_floor_definition',0,100,''),
            ('crypt_hall','down','crypt_floor_1','up', economy,
             'create_infinite_crypt_floor_definition',0,1,''),
            ('crystal_chamber','down','mine_floor_1','up', economy,
             'create_infinite_mine_floor_definition',0,1,''),
            ('crystal_chamber','east','prof_crystal_mine_1','west', economy,
             'create_infinite_profession_dungeon_floor_definition',0,1,'crystal_mine'),
            ('deep_grove','down','prof_ancient_forest_1','up', economy,
             'create_infinite_profession_dungeon_floor_definition',2,1,'ancient_forest'),
            ('giant_fortress_gate','up','giant_fortress_1','down', economy,
             'create_infinite_giant_fortress_floor_definition',0,1,''),
            ('herbalist_hut','north','prof_alchemy_garden_1','south', economy,
             'create_infinite_profession_dungeon_floor_definition',3,1,'alchemy_garden'),
            ('mythic_astral_gate','up','mythic_astral_floor_1','down', economy,
             'create_infinite_astral_floor_definition',1,1,''),
            ('mythic_crypt_gate','down','mythic_crypt_floor_1','up', economy,
             'create_infinite_crypt_floor_definition',1,1,''),
            ('sea_pier','down','prof_sunken_grotto_1','up', economy,
             'create_infinite_profession_dungeon_floor_definition',1,1,'sunken_grotto'),
            ('uoss_deep_dungeon_entry_v11331','down',
             'uoss_deep_dungeon_floor_1_v11331','up', deep,
             'create_infinite_uoss_deep_dungeon_floor_definition_v11331',0,1,''),
        )
        missing = [(src, direction, destination)
                   for src, room in ROOMS.items()
                   for direction, destination in room.get('exits', {}).items()
                   if destination not in ROOMS]
        self.assertCountEqual(missing, [(src, d, t) for src,d,t,*_ in cases])
        for src, direction, target, reverse, source, func, position, floor, family in cases:
            self.assertEqual(ROOMS[src]['exits'][direction], target)
            returns = exits_from_function(source, func, position, floor, family)
            self.assertEqual(returns.get(reverse), src, (src, func, returns))
            # An existing normal floor must be able to go to the next one and
            # back. Do not add any shortcuts through a boss checkpoint.
            if 'down' in returns and reverse != 'down':
                self.assertNotEqual(returns['down'], target)
            if 'up' in returns and reverse != 'up':
                self.assertNotEqual(returns['up'], target)
            next_level = floor + 1
            deeper = exits_from_function(source, func, position, next_level, family)
            if func == 'create_infinite_profession_dungeon_floor_definition':
                inward_direction = {'crystal_mine':'up','sunken_grotto':'up',
                                   'ancient_forest':'north','alchemy_garden':'west'}[family]
                self.assertEqual(deeper[inward_direction], 'LEVEL_BEFORE', family)
            elif func == 'create_infinite_uoss_deep_dungeon_floor_definition_v11331':
                self.assertEqual(deeper['up'], target)
            else:
                self.assertEqual(deeper[reverse], target)
        self.assertEqual(len(cases), 11)

    def test_all_11_lazy_floor_transitions_fail_closed_before_save_or_party_move(self):
        """Real movement method must not commit an unresolved lazy target."""
        import asyncio
        from types import SimpleNamespace
        from player.session_mixins.movement import SessionMovementMixin

        missing = [
            (src, direction, target)
            for src, room in ROOMS.items()
            for direction, target in room.get('exits', {}).items()
            if target not in ROOMS
        ]
        self.assertEqual(len(missing), 11)
        self.assertTrue(all(target not in ROOMS for _, _, target in missing))

        class Stub:
            closed = False
            moving = False
            def __init__(self, source):
                self.character = SimpleNamespace(room_id=source, name='Audyt')
                self.account_id = None
                self.sent = []
                self.generated = []
                self.saved = []
                self.server = SimpleNamespace(
                    world=SimpleNamespace(ensure_runtime_room=self.fail_generate),
                    db=SimpleNamespace(save_character=self.save))
            async def party_movement_barrier_v1130020(self, target):
                return True
            async def send(self, message):
                self.sent.append(message)
            def fail_generate(self, room_id):
                self.generated.append(room_id)
                return False
            def save(self, *args, **kwargs):
                self.saved.append((args, kwargs))

        for source, direction, target in missing:
            with self.subTest(source=source, target=target):
                stub = Stub(source)
                result = asyncio.run(SessionMovementMixin.walk_room_transition(
                    stub, direction, target, guided=True, show_room=False))
                self.assertFalse(result)
                self.assertEqual(stub.generated, [target])
                self.assertEqual(stub.character.room_id, source)
                self.assertEqual(stub.saved, [])
                self.assertEqual(stub.sent, [
                    'Nie udało się przygotować przejścia. Pozostajesz w bieżącej lokacji.'])

    def test_named_dungeon_entry_fails_closed_if_floor_not_generated(self):
        """Nie wolno ruszyc do brakujacego pokoju po nieudanym generatorze."""
        import ast, asyncio
        from types import SimpleNamespace
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / 'systems/dungeon_entry_commands.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        name = '_try_dungeon_entry_command_v03812'
        node = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
        env = {'ROOMS': {'crypt_hall': {'exits': {'down': 'crypt_floor_1'}}}}
        spec = {'label':'Krypta','anchor':'crypt_hall','target':'crypt_floor_1',
                'aliases':('krypta',), 'guide':'krypta'}
        env['_v03812_norm'] = lambda raw: str(raw or '').lower().strip()
        env['_v03812_specs_for_anchor'] = lambda anchor: [spec] if anchor=='crypt_hall' else []
        env['_v03812_direction_to'] = lambda anchor, target: next(
            (d for d, t in env['ROOMS'][anchor]['exits'].items() if t==target), None)
        exec(compile(ast.Module(body=[node],type_ignores=[]), str(path), 'exec'),env)
        entry = env[name]
        class Stub:
            def __init__(self, answer, inject=False):
                self.character = SimpleNamespace(room_id='crypt_hall')
                self.sent=[]; self.moved=[]; self.generated=[]
                def ensure(target):
                    self.generated.append(target)
                    if inject: env['ROOMS'][target] = {'zone':'Krypta Nieskonczona','exits':{}}
                    return answer
                self.server=SimpleNamespace(world=SimpleNamespace(ensure_runtime_room=ensure))
            async def send(self, message):self.sent.append(message)
            async def move(self, direction):self.moved.append(direction)
        try:
            for answer, inject in ((False,False),(True,False)):
                stub=Stub(answer,inject)
                self.assertTrue(asyncio.run(entry(stub,'krypta')))
                self.assertEqual(stub.generated,['crypt_floor_1'])
                self.assertEqual(stub.moved,[])
                self.assertEqual(stub.sent,['Nie udało się przygotować wejścia. Spróbuj ponownie.'])
            stub=Stub(True,True)
            self.assertTrue(asyncio.run(entry(stub,'krypta')))
            self.assertEqual(stub.generated,['crypt_floor_1'])
            self.assertEqual(stub.sent,[])
            self.assertEqual(stub.moved,['down'])
            self.assertEqual(getattr(stub,'_dungeon_entry_label_v03812',None),'')
            already=Stub(False)
            self.assertTrue(asyncio.run(entry(already,'krypta')))
            self.assertEqual(already.generated,[])
            self.assertEqual(already.moved,['down'])
        finally:
            env['ROOMS'].pop('crypt_floor_1',None)

    def test_three_historical_one_way_paths_now_offer_direct_return(self):
        """Zwykły powrót bez nadpisania starych kierunków i bez boss-gate."""
        pairs = (
            ('crossroads','west','deep_grove','south','Dzicz'),
            ('cinder_ravine','north','ember_ruins','west','Popielne Pustkowia'),
            ('absolute_gallery','north','crown_stair','west','Korona Świata'),
        )
        for old,forward,new,return_direction,zone in pairs:
            self.assertEqual(ROOMS[old]['zone'], zone)
            self.assertEqual(ROOMS[new]['zone'], zone)
            self.assertEqual(ROOMS[old]['exits'][forward], new)
            self.assertEqual(ROOMS[new]['exits'][return_direction], old)
        self.assertEqual(ROOMS['deep_grove']['exits']['east'], 'hill')
        self.assertEqual(ROOMS['ember_ruins']['exits']['south'], 'ashen_waste')
        self.assertEqual(ROOMS['crown_stair']['exits']['south'], 'eternal_causeway')
        # Wyjątki w Floor 0 pozostają w pełni rozdzielone od normalnych tras.
        self.assertEqual(ROOMS['uoss_deep_dungeon_floor_0_v11331']['exits']['forward'],
                         'uoss_superboss_arena_serpentarius_v11136')
        self.assertEqual(ROOMS['uoss_deep_dungeon_floor_0_v11331']['exits']['up'],
                         'uoss_deep_dungeon_entry_v11331')
        ordinary_oneway = [
            (src,direction,dest)
            for src,room in ROOMS.items()
            for direction,dest in room['exits'].items()
            if dest in ROOMS
            and src not in ROOMS[dest].get('exits', {}).values()
            and src != 'uoss_deep_dungeon_floor_0_v11331'
        ]
        self.assertEqual(ordinary_oneway, [])

    def test_historical_return_paths_preflight_is_atomic(self):
        from copy import deepcopy
        from systems.current_world_perimeter import install_historical_return_paths
        names = ('crossroads','deep_grove','cinder_ravine','ember_ruins',
                 'absolute_gallery','crown_stair')
        old = {rid: deepcopy(ROOMS[rid]) for rid in names}
        for incoming, direction in (('deep_grove','south'),
                                    ('ember_ruins','west'),
                                    ('crown_stair','west')):
            fixture = deepcopy(old)
            del fixture['deep_grove']['exits']['south']
            del fixture['ember_ruins']['exits']['west']
            del fixture['crown_stair']['exits']['west']
            fixture[incoming]['exits'][direction] = 'zajete_historyczne_wyjscie'
            before = deepcopy(fixture)
            with self.assertRaisesRegex(ValueError,'Zajety kierunek powrotny'):
                install_historical_return_paths(fixture)
            self.assertEqual(fixture,before)
        fixture = deepcopy(old)
        for incoming, direction in (('deep_grove','south'),
                                    ('ember_ruins','west'),
                                    ('crown_stair','west')):
            del fixture[incoming]['exits'][direction]
        self.assertEqual(install_historical_return_paths(fixture),3)
        self.assertEqual(fixture,old)

    def test_no_shortcut_from_middle_and_legacy_ids_unchanged(self):
        self.assertEqual(len({f'v115_graveyard_{x:02d}_{y:02d}' for x in range(12)
                                  for y in range(12)} & set(ROOMS)),144)
        start='v115_graveyard_00_00';end=CEMETERY_CRYPT_EDGE
        visited={start};q=deque([(start,0)]);distance=None
        while q:
            rid,steps=q.popleft()
            if rid==end:distance=steps;break
            for dst in ROOMS[rid]['exits'].values():
                if dst.startswith('v115_graveyard_') and dst not in visited:
                    visited.add(dst);q.append((dst,steps+1))
        self.assertEqual(len(visited),144)
        self.assertEqual(distance,22)
        for rid in ('graveyard','crypt_entrance','crypt_hall','crypt_depths',
                    'v115_graveyard_11_00','v115_graveyard_11_11','necropolis_gate'):
            for key in ('name','desc','zone'):
                self.assertIn(key,ROOMS[rid])

if __name__=='__main__':unittest.main()
