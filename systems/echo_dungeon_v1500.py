# -*- coding: utf-8 -*-
"""The Echo Labyrinth 5.0: lazy, uncapped, five-room dungeon floors.

No persistent room cache and no background tasks.  The existing World spawn,
combat, quest, and SQLite systems provide actual gameplay and save progression.
"""
from __future__ import annotations

import re
from data import catalog_mutations as cm

PATTERN = re.compile(r'^v1500_echo_([1-9][0-9]*)_(gate|hall|branch|shrine|boss)$')
ROLES = ('gate', 'hall', 'branch', 'shrine', 'boss')
THEMES = (
    ('Echo Wody', 'water', 'Woda odbija dawne wspomnienia; dźwięk pomaga znaleźć drogę.'),
    ('Echo Płomienia', 'fire', 'Płomień opowiada o upadku pierwszych twierdz.'),
    ('Echo Cienia', 'dark', 'Zagubione słowa starożytnych brzmią zza murów.'),
    ('Echo Burzy', 'lightning', 'Grzmot rozświetla runy starej podróży.'),
    ('Echo Lodu', 'ice', 'Kryształowe ściany wzmacniają kroki eksploratorów.'),
    ('Echo Pustki', 'void', 'Dźwięki zawieszonej magii wracają w dzikich falach.'),
)
BOSSES = ('Nadzorca Wspomnień', 'Król Zapomnianych Głosów', 'Strażniczka Dusz',
          'Władca Cichych Otchłani', 'Prawodawca Echa', 'Głos Czasu')


def echo_floor_id(floor, role='gate'):
    floor = int(floor)
    if floor < 1:
        raise ValueError('Piętro musi być dodatnie')
    return f'v1500_echo_{floor}_{role}'


def echo_identity(room_id):
    match = PATTERN.fullmatch(str(room_id or ''))
    if not match:
        return None
    floor = int(match.group(1))
    return (floor, match.group(2)) if floor >= 1 else None


def boss_floor(floor):
    return int(floor) % 10 == 0


def generate_echo_floor(floor, rooms, templates):
    """Return authored local topology and spawn plan, without eagerly building deeper levels."""
    floor = int(floor)
    if floor < 1:
        raise ValueError('Niedodatnie piętro')
    name, element, atmosphere = THEMES[(floor-1) % len(THEMES)]
    stage = min(800, 280 + floor * 4)
    intensity = 1 + floor / 25.0
    base_hp = int((120000 + stage * 230) * intensity)
    base_damage = int((3400 + stage * 12) * (intensity ** .68))
    rids = [echo_floor_id(floor, role) for role in ROLES]
    for index, role in enumerate(ROLES):
        exits = {}
        if index: exits['west'] = rids[index - 1]
        if index < 4: exits['east'] = rids[index + 1]
        if index == 0: exits['up'] = ('v1500_echo_entry' if floor == 1
                                       else echo_floor_id(floor-1,'boss'))
        if index == 4: exits['down'] = echo_floor_id(floor+1)
        cm.catalog_assign({
            'name':f'Labirynt Echa: piętro {floor} — {name}, {("Przedsionek","Galeria","Rozstaje","Sanktuarium","Sala Władcy")[index]}',
            'zone':'Nieskończony Labirynt Echa',
            'desc':f'{atmosphere} Komora {index+1}/5, piętro {floor}. '
                  + ('Co dziesięć pięter w ostatniej sali czeka potężny boss.' if boss_floor(floor) else
                     'Pokonaj strażników, zdobywaj łupy i zejdź głębiej.'),
            'exits':exits, 'recommended_mastery':stage,
            'procedural_dynamic':True,'generated_on_demand':True,
            'v1500_echo_floor':floor,
        },'ROOMS', rooms,(rids[index],))
    spawn_rows=[]
    for index in range(1,5):
        mob_id=f'v1500_echo_{floor}_mob_{index}'
        mob_name=(f'{("Szept Lasu", "Poszukiwacz Nocy", "Obrońca Reliktów", "Strażnik Głosu")[index-1]} '
                  f'— {name} {floor}')
        elite = index == 4 and floor % 5 == 0 and not boss_floor(floor)
        cm.catalog_assign({
          'name':mob_name,'max_hp':int(base_hp*(2.5 if elite else 1.0 + index*.12)),
          'damage':int(base_damage*(1.25 if elite else 1.0+index*.06)),
          'damage_type':'magic' if index%2 else 'physical',
          'attack_elements_v11339':(element,),
          'rank':'elite' if elite else 'normal',
          'generator_level':stage,'stat_reward':int((stage*105+floor*50)*intensity),
          'class_xp_reward':int((stage*2800+floor*400)*intensity),
          'soul_reward':int((stage*950+floor*100)*intensity),
          'silver':int((stage*200+floor*120)*intensity),
          'gold':0,'mithril':0,
          'drops':{'soul_shard':.10, 'v1500_echo_fragment':min(.55,.06+floor/400)},
          'stationary_mob':True,'auto_aggro':False,
          'v1500_echo_mob':True,'quest_target':mob_id,
        }, 'MOB_TEMPLATES',templates,(mob_id,))
        spawn_rows.append((rids[index],mob_id))
    if boss_floor(floor):
        boss_id=f'v1500_echo_{floor}_boss_entity'
        cm.catalog_assign({
          'name':f'{BOSSES[(floor//10-1) % len(BOSSES)]} — piętro {floor}',
          'max_hp':base_hp*9,'damage':base_damage*3,
          'damage_type':'magic','attack_elements_v11339':(element,'dark','lightning'),
          'boss':True,'world_boss':True,'rank':'world_boss',
          'boss_mechanic':'elemental_overdrive',
          'boss_mechanic_text':f'Próba Echa {floor}: fazy żywiołów {element}, dark i lightning.',
          'generator_level':stage,'stat_reward':int(stage*1200*intensity),
          'class_xp_reward':int(stage*12000*intensity),
          'soul_reward':int(stage*4400*intensity),
          'silver':int(stage*2800*intensity),'gold':0,'mithril':0,
          'drops':{'v1500_echo_fragment':1.0,'soul_shard':1.0,
                   'v12812_legendary_seal':.75},
          'stationary_mob':True,'auto_aggro':False,
          'v1500_echo_boss':True,'quest_target':boss_id,
        },'MOB_TEMPLATES',templates,(boss_id,))
        spawn_rows.append((rids[-1], boss_id))
    return rids, spawn_rows


def install_echo_dungeon_v1500(rooms, items, world_class):
    """Installed after the runtime manifest has assembled all historical wrappers."""
    if 'v1500_echo_entry' in rooms:
        raise RuntimeError('Repeated Echo Labyrinth installation')
    if 'v1500_gate' not in rooms:
        raise RuntimeError('Missing new continent gateway')
    cm.catalog_assign({'name':'Brama Nieskończonego Labiryntu Echa',
        'zone':'Zapomniane Światy',
        'desc':'Nowy nieskończony loch. Wejście nie wymaga poziomu ani ukończenia fabuły. '
               'Na każdym piętrze pięć komór; boss co dziesiąte piętro, brak losowych pułapek. '
               'Wpisz lochy50 po objaśnienie, walk dol aby dojść przed zejście, a wyjscie aby wrócić.',
        'exits':{'up':'v1500_gate','down':echo_floor_id(1)},
        'recommended_mastery':320}, 'ROOMS',rooms,('v1500_echo_entry',))
    cm.catalog_assign('v1500_echo_entry','ROOMS',rooms,('v1500_starlight_gate','exits','down'))
    cm.catalog_assign('v1500_starlight_gate','ROOMS',rooms,('v1500_echo_entry','exits','up'))
    cm.catalog_assign({'name':'Fragment Zapomnianego Echa',
        'type':'material','rarity':'rare','price':850000,
        'desc':'Nagroda z Labiryntu Echa; można ją sprzedać i zachować do przyszłych projektów.'},
        'ITEMS',items,('v1500_echo_fragment',))
    from systems.content_registry import MOB_TEMPLATES
    previous=world_class.ensure_infinite_dungeon_floor

    def ensure_echo_floor(self, room_id):
        found = echo_identity(room_id)
        if found is None:
            return previous(self, room_id)
        floor,_role = found
        gate_id=echo_floor_id(floor)
        if gate_id not in rooms:
            room_ids, spawned = generate_echo_floor(floor, rooms, MOB_TEMPLATES)
            for current_id in room_ids:
                self._generatorize_runtime_room(current_id)
            for spawn_room, mob_id in spawned:
                self._register_runtime_spawn(spawn_room, mob_id)
        if room_id in rooms:
            self._generatorize_runtime_room(room_id)
            return True
        return False
    ensure_echo_floor._v1500_echo = True
    world_class.ensure_infinite_dungeon_floor=ensure_echo_floor
    # Earlier Magitek/UOSS runtime compatibility patches install a method
    # directly on Session (shadowing inherited mixins), so the new dungeon's
    # emergency exit must wrap that actual final method, not only a mixin.
    from player.session import Session
    previous_exit=Session.dungeon_exit_destination
    def echo_exit_destination(self, room_id=None):
        rid=str(room_id or (self.character.room_id if self.character else ''))
        if echo_identity(rid) is not None:
            return 'v1500_echo_entry','Nieskończony Labirynt Echa'
        return previous_exit(self, room_id)
    echo_exit_destination._v1500_echo=True
    Session.dungeon_exit_destination=echo_exit_destination
    return True
