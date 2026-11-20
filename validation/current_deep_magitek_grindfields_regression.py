# -*- coding: utf-8 -*-
from __future__ import annotations
from collections import deque
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from world.dynamic_content import v0100_expand_instance_floor,v0100_subroom_id
from world.uoss_superboss_world import create_infinite_uoss_deep_dungeon_floor_definition_v11331 as deep_create
from systems.current_deep_dungeon_grindfields import _room_id

count=0
def check(expr, message):
    global count
    assert expr, message
    count+=1

def reach(ids, first):
    seen={first}; q=deque([first])
    while q:
        src=q.popleft()
        for dst in ROOMS[src]['exits'].values():
            if dst in ids and dst not in seen:
                seen.add(dst);q.append(dst)
    return seen

for floor in (1,25,100):
    canonical,pairs=deep_create(floor)
    old_exits=dict(ROOMS[canonical]['exits'])
    global_spawns=list(MOB_SPAWNS)
    created=v0100_expand_instance_floor(canonical,pairs,runtime=True)
    ids={_room_id(canonical,n) for n in range(144)}
    check(all(i in ROOMS for i in ids),f'deep {floor}: all rooms')
    check(len([i for i in ROOMS if str(i).startswith(f'{canonical}_v11628_')])==144,f'deep {floor}: count')
    check(all(ROOMS[i].get('exploration_ep')==0 and ROOMS[i]['zone']==ROOMS[canonical]['zone'] for i in ids),f'deep {floor}: zone/exp')
    check(all(not any(ROOMS[i].get(k) for k in ('trap','auto_aggro','boss','min_level')) for i in ids),f'deep {floor}: no traps')
    check(all(ROOMS[canonical]['exits'][d]==dst for d,dst in old_exits.items()),f'deep {floor}: old exit')
    check(len(ROOMS[canonical]['exits'])==len(old_exits)+1,f'deep {floor}: one new exit')
    entry=next(dst for d,dst in ROOMS[canonical]['exits'].items() if d not in old_exits)
    check(entry in ids and reach(ids,entry)==ids,f'deep {floor}: reach')
    check(all(ROOMS[b]['exits'].get({'north':'south','south':'north','east':'west','west':'east'}[d])==a for a in ids for d,b in ROOMS[a]['exits'].items() if d in ('north','south','east','west') and b in ROOMS),f'deep {floor}: reversibility')
    added=[(r,t) for r,t in created if r in ids]
    check(len(added)==72 and not any(MOB_TEMPLATES[t].get('boss') for r,t in added),f'deep {floor}: regular spawn only')
    check(MOB_SPAWNS==global_spawns,f'deep {floor}: global spawns unchanged')
    check(v0100_expand_instance_floor(canonical,pairs,runtime=True)==pairs,f'deep {floor}: idempotent')
    if floor % 25 == 0:
        check(any(MOB_TEMPLATES[t].get('uoss_deep_dungeon_apanda_floor')==floor and r==canonical for r,t in pairs),f'deep {floor}: apanda stays')
    print('PASS Deep Dungeon',floor,flush=True)

# Magitek publishes an active rule override when its large world module loads.
# Here we isolate the same runtime slot, avoiding an unsafe partial import of
# Magitek/World during the standalone catalogue regression.
from core.runtime_rules import register_rule, get_rule
from systems.current_procedural_grindfields import extend_instance_floor
old_rule=get_rule('v0100_instance_spec')
mock_room='magitek_floor_9999'
for old_total in (12,20):
    canonical=f'{mock_room}_{old_total}'
    # Regression fixture: same floor naming and regular-mob identifiers, but no
    # modification to source catalogue or actual world generation algorithms.
    if canonical in ROOMS:
        raise AssertionError('Existing fixture room name')
    ROOMS[canonical]={'zone':'Nieskończony Kompleks Magitek','name':'Test Magitek',
                       'exits': {'up':'magitek_zero_final', 'down':'magitek_floor_10000'},
                       'recommended_mastery': 390}
    for i in range(1,old_total):
        ROOMS[v0100_subroom_id(canonical,i)]={'zone':ROOMS[canonical]['zone'],
            'exits': {}}
    def magitek_rule(rid, room=canonical, count=old_total):
        if rid==room:
            return {'kind':'magitek','floor':9999,'next_dir':'down',
                    'rooms':count, 'boss_flag':'magitek_boss'}
        return old_rule(rid)
    register_rule('v0100_instance_spec',magitek_rule)
    src=[(canonical,'uoss_deep_dungeon_mob_1_v11331')]
    original_global=list(MOB_SPAWNS)
    result=extend_instance_floor(canonical,src,runtime=True)
    ids={v0100_subroom_id(canonical,old_total+n) for n in range(144)}
    check(all(i in ROOMS for i in ids),f'magitek runtime slot {old_total}: new rooms')
    check(all(ROOMS[i]['zone']==ROOMS[canonical]['zone'] for i in ids),f'magitek {old_total}: zone')
    check(all(ROOMS[i]['exploration_ep']==0 for i in ids),f'magitek {old_total}: EP')
    check(len([x for x in result if x[0] in ids])==72,f'magitek {old_total}: 72 regular mobs')
    start=v0100_subroom_id(canonical,old_total)
    check(reach(ids,start)==ids,f'magitek {old_total}: all reachable')
    check(all(ROOMS[b]['exits'].get({'north':'south','south':'north','east':'west','west':'east'}[d])==a
              for a in ids for d,b in ROOMS[a]['exits'].items()
              if d in ('north','south','east','west') and b in ROOMS),f'magitek {old_total}: directions reversible')
    check(MOB_SPAWNS==original_global,f'magitek {old_total}: no static spawns')
    check(extend_instance_floor(canonical,src,runtime=True)==src,f'magitek {old_total}: idempotent')
    print('PASS Magitek active rule fixture',old_total,flush=True)
# Regression v116.00.29: a collision at the LAST room must leave the old
# floor, its canonical exits and every unrelated spawn exactly as before.
collision_room = 'magitek_v11629_collision_fixture'
old_total = 20
ROOMS[collision_room] = {'zone': 'Nieskończony Kompleks Magitek',
                         'name': 'Collision fixture', 'exits': {'up': 'magitek_zero_final'}}
for index in range(1, old_total):
    ROOMS[v0100_subroom_id(collision_room, index)] = {
        'zone': ROOMS[collision_room]['zone'], 'exits': {}}
late_id = v0100_subroom_id(collision_room, old_total + 143)
ROOMS[late_id] = {'zone': 'Reserved fixture', 'name': 'Existing saved room',
                  'exits': {'west': 'reserved_saved_destination'}}
original_late = dict(ROOMS[late_id])
original_exits = dict(ROOMS[collision_room]['exits'])
original_spawns = list(MOB_SPAWNS)
register_rule('v0100_instance_spec',
              lambda rid: ({'kind': 'magitek', 'floor': 29, 'rooms': old_total,
                            'next_dir': 'down', 'boss_flag': 'magitek_boss'}
                           if rid == collision_room else old_rule(rid)))
try:
    extend_instance_floor(collision_room, [], runtime=True)
except RuntimeError as exc:
    check('Kolizja identyfikatora' in str(exc), 'late collision reported')
else:
    raise AssertionError('late room collision silently accepted')
check(not any(v0100_subroom_id(collision_room, old_total + index) in ROOMS
              for index in range(143)), 'collision: no partial rooms')
check(ROOMS[late_id] == original_late, 'collision: saved room untouched')
check(ROOMS[collision_room]['exits'] == original_exits,
      'collision: old exits untouched')
check(MOB_SPAWNS == original_spawns, 'collision: old spawns untouched')

# Prevent any future regression to tiny ordinary exp fields. Special arenas,
# checkpoint hubs and cities need not be expanded into combat maps.
from collections import Counter
zone_sizes = Counter(room.get('zone', '') for room in ROOMS.values())
ordinary = Counter()
for rid, tid in MOB_SPAWNS:
    if rid not in ROOMS:
        continue
    template = MOB_TEMPLATES.get(tid, {})
    if any(template.get(key) for key in ('boss', 'is_boss', 'mini_boss',
                                         'boss_mechanic', 'stationary_mob')):
        continue
    ordinary[ROOMS[rid].get('zone', '')] += 1
small = {zone: zone_sizes[zone] for zone, count in ordinary.items()
         if count >= 2 and zone_sizes[zone] < 144}
check(not small, f'undersized ordinary grind zones: {small}')
check(len(ordinary) > 100, 'ordinary world zones audited')

register_rule('v0100_instance_spec',old_rule)
magitek_source=(ROOT/'world/magitek_infinite.py').read_text(encoding='utf-8')
check("_register_current_rule('v0100_instance_spec', v0100_instance_spec)" in magitek_source,
      'Magitek installs active spec')
check('spawns = v0100_expand_instance_floor(created_room, spawns, runtime=True)' in magitek_source,
      'Magitek runtime calls expansion')
print(f'CURRENT DEEP/MAGITEK GRINDFIELDS {count}/{count} PASS')


# SAVED SIDE ROOM REHYDRATION v11631: a login after reboot must not
# teleport a character standing in a valid generated Deep Dungeon wing
# back to the city. Never treat an invented/out-of-range ID as valid.
from systems.current_deep_dungeon_grindfields import deep_dungeon_saved_side_parent
from world.uoss_superboss_world import uoss_deep_dungeon_floor_id_v11331
from world.world_state import World
new_floor = uoss_deep_dungeon_floor_id_v11331(222)
saved = _room_id(new_floor, 143)
check(new_floor not in ROOMS and saved not in ROOMS, 'login fixture not pre-created')
check(deep_dungeon_saved_side_parent(saved) == new_floor, 'saved last wing cell parsed')
for invalid in (f'{new_floor}_v11628_144', f'{new_floor}_v11628_999',
                f'{new_floor}_v11628_-01', f'{new_floor}_v11628_143_extra',
                'uoss_deep_dungeon_floor_0_v11331_v11628_000'):
    check(deep_dungeon_saved_side_parent(invalid) is None, 'invalid generated cell rejected')
# Do not import the full Magitek runtime in a partial catalogue test:
# keep the production wrapper, stub only the unrelated existing generic
# login handler, and use the REAL Deep Dungeon floor generator/expander.
import world.world_state as world_state
world = World.__new__(World)
created_log = []
def ensure_saved_floor(canonical):
    created_log.append(canonical)
    new_room, base_pairs = deep_create(222)
    check(new_room == canonical, 'rehydration creates correct canonical floor')
    v0100_expand_instance_floor(new_room, base_pairs, runtime=True)
    return True
world.ensure_infinite_dungeon_floor = ensure_saved_floor
previous_login_handler = world_state._v11631_previous_ensure_runtime_room
world_state._v11631_previous_ensure_runtime_room = lambda self, rid: str(rid) in ROOMS
try:
    check(world.ensure_runtime_room(saved), 'login creates existing saved side room')
    check(new_floor in ROOMS and saved in ROOMS, 'login preserves side room ID')
    wing = {_room_id(new_floor, i) for i in range(144)}
    check(all(rid in ROOMS for rid in wing) and len(wing) == 144,
          'recreated complete 144-room deep side wing')
    check(saved in reach(wing, _room_id(new_floor, 0)), 'saved cell reachable from landing')
    check(any(new_floor in ROOMS[rid]['exits'].values() for rid in wing),
          'wing has a walkable return to original landing')
    check(world.ensure_runtime_room(saved), 'repeating saved login is idempotent')
    check(len(created_log) == 1, 'already present room is not regenerated')
    check(not world.ensure_runtime_room(f'{new_floor}_v11628_999'),
          'invalid cell cannot become a valid player position')
finally:
    world_state._v11631_previous_ensure_runtime_room = previous_login_handler
print('SAVED DEEP DUNGEON LOGIN REHYDRATION PASS', flush=True)


# v116.00.32 — saved positions in old and new 12x12 instance sectors.
# Exercise all canonical floor families with their real active specs and
# the actual 144-room side generator, while stubbing unrelated combat/event
# callbacks. An unknown room must not be reported as recovered.
from systems.current_procedural_grindfields import extend_instance_floor
from core.runtime_rules import get_rule as _v11632_get_rule
from core.runtime_rules import register_rule as _v11632_register_rule
from world.dynamic_content import v0100_subroom_id as _v11632_subroom_id
_v11632_old_rule = _v11632_get_rule('v0100_instance_spec')
_v11632_magitek_parent = 'magitek_floor_98765'

def _v11632_instance_rule(parent):
    if parent == _v11632_magitek_parent:
        return {'kind': 'magitek', 'floor': 98765, 'next_dir': 'down',
                'rooms': 20, 'boss_flag': 'magitek_boss'}
    return _v11632_old_rule(parent)

_v11632_register_rule('v0100_instance_spec', _v11632_instance_rule)
try:
    _v11632_cases = (
        ('Krypta', 'crypt_floor_98765'),
        ('Mityczna Krypta', 'mythic_crypt_floor_98765'),
        ('Wieża Astralna', 'astral_floor_98765'),
        ('Mityczna Wieża Astralna', 'mythic_astral_floor_98765'),
        ('Twierdza Gigantów', 'giant_fortress_98765'),
        ('Kopalnia Głębinowa', 'mine_floor_98765'),
        ('Loch profesji', 'prof_crystal_mine_98765'),
        ('Magitek', _v11632_magitek_parent),
    )
    for label, parent in _v11632_cases:
        spec = _v11632_get_rule('v0100_instance_spec')(parent)
        check(spec is not None, f'{label}: real/spec mock found')
        old_total = int(spec['rooms'])
        last = _v11632_subroom_id(parent, old_total + 143)
        world = World.__new__(World)
        calls = []
        def fake_floor_build(canonical, p=parent, floor_spec=spec):
            calls.append(canonical)
            check(canonical == p, f'{label}: only canonical landing built')
            ROOMS[p] = {'zone': 'Test zapisu - ' + label, 'exits': {'up': 'test_exit'}}
            for idx in range(1, int(floor_spec['rooms'])):
                rid = _v11632_subroom_id(p, idx)
                ROOMS[rid] = {'zone': ROOMS[p]['zone'], 'exits': {}}
            extend_instance_floor(p, [], runtime=True)
            return True
        world.ensure_infinite_dungeon_floor = fake_floor_build
        invalid = (
            _v11632_subroom_id(parent, old_total + 144),
            parent + '_r00', parent + '_r1', parent + '_r99999',
        )
        for bad in invalid:
            check(not world.ensure_runtime_room(bad), f'{label}: invalid room rejected')
        check(not calls, f'{label}: invalid input cannot generate a floor')
        # The old generic callback is replaced ONLY for this tiny fixture;
        # its real production body remains unmodified and tested separately.
        _v11632_previous = world_state._v11631_previous_ensure_runtime_room
        world_state._v11631_previous_ensure_runtime_room = (
            lambda self, rid: str(rid) in ROOMS)
        try:
            check(world.ensure_runtime_room(last), f'{label}: last saved room restored')
            check(len(calls) == 1, f'{label}: single floor generation')
            all_side = {_v11632_subroom_id(parent, old_total + i) for i in range(144)}
            check(all_side <= ROOMS.keys(), f'{label}: complete 144-room wing')
            check(reach(all_side, _v11632_subroom_id(parent, old_total)) == all_side,
                  f'{label}: entire wing reachable')
            check(world.ensure_runtime_room(last), f'{label}: login idempotent')
            check(len(calls) == 1, f'{label}: no duplicate floor creation')
            check(not world.ensure_runtime_room(_v11632_subroom_id(parent, old_total + 144)),
                  f'{label}: no phantom room after generation')
        finally:
            world_state._v11631_previous_ensure_runtime_room = _v11632_previous
        print('PASS saved instance room', label, flush=True)
finally:
    _v11632_register_rule('v0100_instance_spec', _v11632_old_rule)
print('SAVED INSTANCE ROOM RESTORATION v11632 PASS', flush=True)


# v116.00.33 — protect the longstanding temple-on-login invariant.
# Room materialization at character selection is historically part of a
# protected method. Keep it unchanged: all spawns happen in temple on enter_world,
# including TCP reconnect and characters saved on dynamic dungeon floors.
import asyncio as _v11633_asyncio
import inspect as _v11633_inspect
from types import SimpleNamespace as _v11633_NS
from player.session_mixins.io_auth_character import (
    SessionIOAuthCharacterMixin as _v11633_auth,
)
from systems import fame_v1702 as _v11633_fame

for _method in (_v11633_auth.do_login, _v11633_auth.choose_existing_character):
    # Do not bypass historical protected character-selection methods or
    # silently remove the runtime room validation / safe-room fallback.
    _source = _v11633_inspect.getsource(_method)
    check('ensure_runtime_room(' in _source, f'{_method.__name__}: legacy room guard kept')
    check('self.character.room_id = "square"' in _source,
          f'{_method.__name__}: legacy fallback kept')

async def _v11633_noop_fame(_session):
    return None

class _v11633_db:
    def __init__(self):
        self.saved = []
        self.checkpoints = []
        self.login = []
    def mark_player_login_v0363(self, aid):
        self.login.append(aid)
    def sync_legacy_crypt_checkpoint(self, aid, rid):
        self.checkpoints.append((aid, rid))
    def save_character(self, character):
        self.saved.append((character.room_id, character.level, character.soul_xp))

class _v11633_actor:
    def __init__(self, room):
        self.account_id = 13
        self.character = _v11633_NS(name='Audyt', room_id=room,
                                      level=47, soul_xp=225047361,
                                      name_case=lambda case:'Audycie')
        self.db = _v11633_db()
        self.server = _v11633_NS(db=self.db, broadcast_room=self.broadcast_room)
        self.messages=[]
        self.current_hp = 1
        self.current_mana = 1
    def refresh_active_classes(self): pass
    def _v1703_dismiss_summons_on_login(self): return 0
    def start_session_summary(self): pass
    def migrate_raw_mining_gems_to_bag_v0867(self): return ()
    def migrate_craft_materials_to_casket_v0915(self): return ()
    def enforce_equipment_character_level(self): return ()
    def max_hp(self): return 700
    def max_mana(self): return 900
    def ensure_standing_regen_v1124(self): pass
    async def broadcast_room(self, *args, **kwargs): pass
    async def send(self, txt, **kwargs): self.messages.append(txt)
    async def daily_login_v03051(self): pass
    async def sync_extended_achievements(self): pass
    async def sync_titles_v0580(self, **kwargs): pass
    def double_xp_state(self): return {'active':False}
    async def look(self): self.messages.append('LOOK '+self.character.room_id)

async def _v11633_check_login():
    for saved in ('square', 'crypt_floor_99_r173',
                  'uoss_deep_dungeon_floor_100_v11331_v11628_143',
                  'magitek_floor_100_r155', 'room_from_removed_old_version'):
        actor = _v11633_actor(saved)
        await _v11633_auth.enter_world(actor)
        check(actor.character.room_id == 'temple', f'{saved}: temple entry')
        check(actor.db.saved == [('temple', 47, 225047361)], f'{saved}: saved temple, XP unchanged')
        check(actor.db.checkpoints == [(13, saved)], f'{saved}: old crypt checkpoint retained')
        check(actor.current_hp == 700 and actor.current_mana == 900,
              f'{saved}: recovery on login')
        check(actor.messages[-1] == 'LOOK temple', f'{saved}: appears at temple')
    return True

_v11633_original_fame = _v11633_fame.fame_pay_later
try:
    _v11633_fame.fame_pay_later = _v11633_noop_fame
    check(_v11633_asyncio.run(_v11633_check_login()), 'temple login regression')
finally:
    _v11633_fame.fame_pay_later = _v11633_original_fame
print('TEMPLE LOGIN v11633 PASS', flush=True)
