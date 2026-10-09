"""v1.26.1 targeted runtime-method regression tests without mutating the world."""
from __future__ import annotations
import ast
import asyncio
import math
from pathlib import Path
from types import SimpleNamespace
from systems.adaptive_combat import adaptive_target_max_hp_v11330, adaptive_reward_multiplier_v11330, adaptive_combat_rank_v11330

ROOT = Path(__file__).resolve().parents[1]


def _mixin(relative, classname, globals_):
    source = ast.parse((ROOT / relative).read_text(encoding='utf8'))
    node = next(x for x in source.body if isinstance(x, ast.ClassDef) and x.name == classname)
    ns = dict(globals_)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(ROOT / relative), 'exec'), ns)
    return ns[classname]


def audit_v1261():
    checks = 0
    def check(condition, description):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError('v1.26.1: ' + description)

    templates = {'v1261_goblin': {'max_hp': 1000, 'rank': 'normal'}, 'v1261_boss': {'max_hp': 10000, 'rank': 'boss'}}
    Combat = _mixin('player/session_mixins/combat_damage.py', 'SessionCombatDamageMixin', {
        'math': math, 'MOB_TEMPLATES': templates,
        'adaptive_target_max_hp_v11330': adaptive_target_max_hp_v11330,
        'adaptive_reward_multiplier_v11330': adaptive_reward_multiplier_v11330,
        'adaptive_combat_rank_v11330': adaptive_combat_rank_v11330,
    })

    class Db:
        def __init__(self):
            self.hires = {}
            self.calls = 0
        def mercenary_contracts(self, aid):
            self.calls += 1
            return [{'role': r, 'expires_at': 0} for r in self.hires.get(aid, ())]
        def mercenary_progress_v1220(self, aid, role):
            return {'specialization':'automatyczna'}
    db = Db()
    server = SimpleNamespace(db=db, sessions=[], party_sessions=None)
    class Player(Combat):
        def __init__(self, aid, hit, level=10):
            self.account_id = aid
            self.character = SimpleNamespace(room_id='testroom', character_level=level, class_name='Wojownik', soul_tier=1, soul_weapon_mastery_level=1)
            self.closed = False
            self.current_hp = 1000
            self.combat_mob_key = None
            self.server = server
            self.hit = hit
        def consider_player_expected_hit(self): return self.hit
        def basic_attack_hit_count_v11196(self): return 2
        def player_action_interval_v11154(self): return 1.0
        def physical_power(self): return self.hit
        def spell_power(self): return self.hit // 2
    solo = Player(1, 1000, 400)
    weak = Player(2, 20, 10)
    server.party_sessions = lambda aid, same_room=None: [solo] if aid == 1 else [weak]
    mob = SimpleNamespace(key='mobA', template_id='v1261_goblin', room_id='testroom', hp=1000, alive=True)
    start = solo.apply_adaptive_mob_scale_v11330(mob)
    check(start['party_dps'] > 0, 'baseline party dps')
    check(start['max_hp'] >= 8000, 'solo normal HP target')
    db.hires[1] = ('wojownik', 'mag', 'kaplan')
    if hasattr(solo, '_adaptive_mercenary_dps_cache_v1261'): del solo._adaptive_mercenary_dps_cache_v1261
    with_hires = solo.apply_adaptive_mob_scale_v11330(mob)
    check(with_hires['max_hp'] > start['max_hp'], 'three hires must increase mob HP')
    check(with_hires['party_dps'] > start['party_dps'] * 2, 'hire DPS must be substantial')
    check(with_hires['party_size'] == 1, 'hires do not occupy player party slots')
    check(db.calls >= 2, 'active contracts checked')
    cache_reads = db.calls
    solo.apply_adaptive_mob_scale_v11330(mob)
    check(db.calls == cache_reads, 'hire count cached during combat for performance')
    check(with_hires['reward_multiplier'] > start['reward_multiplier'], 'rewards scale to actual party power')
    mob.hp = with_hires['max_hp'] // 2
    server.sessions = [solo]
    solo.combat_mob_key = mob.key
    in_fight = weak.apply_adaptive_mob_scale_v11330(mob)
    check(in_fight['max_hp'] == with_hires['max_hp'], 'cannot reduce HP of an active encounter')
    check(mob.hp == with_hires['max_hp'] // 2, 'active HP not healed or reduced')
    server.sessions = [weak]
    weak.combat_mob_key = None
    solo.combat_mob_key = None
    next_fight = weak.apply_adaptive_mob_scale_v11330(mob)
    check(next_fight['max_hp'] < with_hires['max_hp'], 'later low level player gets own scaled HP')
    check(0 < mob.hp <= next_fight['max_hp'], 'smaller HP is valid')
    check(0.45 <= mob.hp / next_fight['max_hp'] <= .55, 'HP fraction preserved on handoff')
    check(next_fight['rank'] == 'normal', 'normal rank preserved')

    party2 = Player(3, 200, 100)
    db.hires[3] = ('mag', 'wojownik', 'druid')
    server.party_sessions = lambda aid, same_room=None: [solo, party2] if aid == 1 else [weak]
    party_mob = SimpleNamespace(key='mobB', template_id='v1261_boss', room_id='testroom', hp=10000, alive=True)
    multi = solo.apply_adaptive_mob_scale_v11330(party_mob)
    check(multi['party_size'] == 2, 'two players count as two party members')
    check(multi['party_dps'] > with_hires['party_dps'], 'party members and their hires both count')
    check(multi['rank'] == 'boss', 'boss type not overwritten')
    # All four players and twelve individually contracted hires contribute DPS.
    party3, party4 = Player(4, 500, 600), Player(5, 100, 60)
    db.hires[4] = ('mag', 'wojownik', 'druid')
    db.hires[5] = ('berserker', 'lucznik', 'paladyn')
    server.party_sessions = lambda aid, same_room=None: [solo, party2, party3, party4] if aid == 1 else [weak]
    fresh = SimpleNamespace(key='mobC', template_id='v1261_boss', room_id='testroom', hp=10000, alive=True)
    combined = solo.apply_adaptive_mob_scale_v11330(fresh)
    check(combined['party_size'] == 4, 'four human players counted')
    check(combined['party_dps'] > multi['party_dps'], 'twelve mercenaries and four players increase expected throughput')
    check(combined['max_hp'] > multi['max_hp'], 'boss HP keeps pace with full group')
    check(all(db.mercenary_contracts(i) for i in (1, 3, 4, 5)), 'all four owners keep three hire contracts')
    check(adaptive_reward_multiplier_v11330(1000, 1000) == 1, 'base reward unchanged')
    check(adaptive_reward_multiplier_v11330(1000, 1000000) > 3, 'old 3x ceiling removed')
    check(adaptive_reward_multiplier_v11330(1000, 100000000) > adaptive_reward_multiplier_v11330(1000, 1000000), 'higher workload pays better')
    check(adaptive_reward_multiplier_v11330(1000, 1000000) < 10, 'no economic runaway at 1000x HP')

    # Call actual async implementation with fake inventory, without connecting DB.
    Smelt = _mixin('player/session_mixins/crafting_expansion.py', 'SessionCraftingExpansionV03114Mixin', {
        'normalize_lookup_text': lambda s: str(s).casefold().strip(),
        'ITEMS': {'iron_ingot': {'name':'Sztabka żelaza'}},
        'CRAFT_RECIPES': {}, 'SALVAGE_SMELT_FALLBACK_V03113': {'iron_ingot':'recycled_iron'},
    })
    class Smelter(Smelt):
        def __init__(self, ore, scrap):
            self.qty = {'ore': ore, 'scrap': scrap}
            self.messages = []
            self.crafted = []
            self.smelt_cancel_requested_v1124 = False
        async def send(self, text): self.messages.append(text)
        async def smelt_boss_keys_v11341(self, raw): return None
        def resolve_smelt_recipe(self, raw):
            if str(raw).casefold() in ('żelazo','zelazo','iron'):
                return ('iron_ingot', {'output':'iron_ingot','resource':'ore'})
            if str(raw).casefold() in ('odłamki żelaza','odlamki zelaza','iron scrap'):
                return ('recycled_iron', {'output':'iron_ingot','resource':'scrap'})
            return None
        def max_recipe_crafts_v03114(self, recipe): return self.qty[recipe['resource']]
        async def perform_recipe(self, rid, recipes, activity):
            material = 'ore' if rid == 'iron_ingot' else 'scrap'
            if self.qty[material] == 0: return False
            self.qty[material] -= 1
            self.crafted.append(rid)
            return True
    smith = Smelter(3, 5)
    check(asyncio.run(smith._smelt_execute_v1124('max żelazo')), 'max iron succeeds')
    check(smith.crafted == ['iron_ingot'] * 3, 'max iron consumes exactly 3 ore')
    check(smith.qty == {'ore':0,'scrap':5}, 'max iron leaves salvage untouched')
    check('3/3' in smith.messages[-1], 'max progress message correct for quest')
    check(not asyncio.run(smith._smelt_execute_v1124('max żelazo')), 'max iron without ore does not switch to salvage')
    check(smith.qty['scrap'] == 5, 'salvage retained when ore exhausted')
    check(asyncio.run(smith._smelt_execute_v1124('max odłamki żelaza')), 'explicit salvage still works')
    check(smith.qty['scrap'] == 0, 'explicit salvage consumes requested material')
    check(smith.crafted.count('recycled_iron') == 5, 'explicit salvage only selected recipe')
    return checks


if __name__ == '__main__':
    print(f'BALANCE + SMELT v1.26.1: {audit_v1261()} checks PASS')
