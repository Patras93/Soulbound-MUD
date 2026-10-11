# -*- coding: utf-8 -*-
"""Soulbound v2.10.0: additive titan arenas and optional dungeon secrets.

Only the visited floor is generated. No checkpoint, existing mob, or exit is
replaced; all entrances branch from a real, reachable dungeon floor.
"""
from __future__ import annotations

import re
from data import catalog_mutations as cm

TITANS = (
    ('ragnor','Ragnor, Tytan Wiecznego Ognia','fire','Rękawice Żaru Ragnora','hands', {'strength':1250,'constitution':730}, {'all_damage_pct':9}),
    ('velira','Velira, Królowa Wiecznego Lodu','ice','Kryształowe Serce Veliry','necklace', {'intelligence':1300,'willpower':850}, {'max_hp_pct':12}),
    ('ormak','Ormak, Żelazny Kolos','physical','Pancerz Ormaka','body', {'constitution':1750,'strength':600}, {'max_hp_pct':15}),
    ('morven','Morven, Władca Zapomnianych Dusz','dark','Pierścień Dusz Morvena','ring', {'intelligence':950,'willpower':900}, {'all_damage_pct':8}),
    ('althira','Althira, Cesarzowa Burz','lightning','Buty Burz Althiry','feet', {'dexterity':1400,'strength':600}, {'all_damage_pct':10}),
    ('vardun','Vardun, Strażnik Pradawnych Run','arcane','Korona Run Varduna','head', {'intelligence':1050,'constitution':800}, {'max_hp_pct':10}),
    ('kaelor','Kaelor, Władca Zatrzymanego Czasu','ice','Klepsydra Kaelora','cloak', {'dexterity':1100,'willpower':800}, {'all_damage_pct':8}),
    ('nharon','Nharon, Tytan Nieskończonej Pustki','void','Relikt Pustki Nharona','charm', {'strength':1050,'intelligence':1050,'constitution':1050}, {'all_damage_pct':11}),
)
TITAN_BY_SLUG = {row[0]: row for row in TITANS}
FAMILIES = {
    'crypt':'Krypta', 'mythic_crypt':'Mityczna Krypta',
    'astral':'Wieża Astralna', 'mythic_astral':'Mityczna Wieża',
    'deep':'Deep Dungeon', 'echo':'Labirynt Echa',
    'magitek':'Magitek', 'giant':'Twierdza Gigantów',
}
_CHAMBER_SOURCES = {}  # only rooms generated in the running process
CHAMBER = re.compile(r'^v2100_(titan|secret)_(crypt|mythic_crypt|astral|mythic_astral|deep|echo|magitek|giant)_([1-9][0-9]*)$')


def dungeon_identity(room_id):
    """Recognize only genuine canonical floor rooms, never extrapolated names."""
    rid = str(room_id or '')
    if rid.startswith('v2100_'):
        return None
    from systems.echo_dungeon_v1500 import echo_identity
    echo = echo_identity(rid)
    if echo and echo[1] == 'shrine':
        return 'echo', int(echo[0])
    from systems.dungeons_regions import (
        crypt_floor_id, crypt_floor_number, astral_floor_id, astral_floor_number,
        mythic_crypt_floor_id, mythic_crypt_floor_number,
        mythic_astral_floor_id, mythic_astral_floor_number,
        giant_fortress_floor_number,
    )
    from world.uoss_superboss_world import (
        uoss_deep_dungeon_floor_id_v11331,
        uoss_deep_dungeon_floor_number_v11331,
    )
    from world.magitek_infinite import magitek_floor_number
    specs = (
        ('crypt', crypt_floor_number, crypt_floor_id),
        ('mythic_crypt', mythic_crypt_floor_number, mythic_crypt_floor_id),
        ('astral', astral_floor_number, astral_floor_id),
        ('mythic_astral', mythic_astral_floor_number, mythic_astral_floor_id),
        ('deep', uoss_deep_dungeon_floor_number_v11331, uoss_deep_dungeon_floor_id_v11331),
    )
    for label, parser, canonical in specs:
        floor = parser(rid)
        if floor is not None and rid == canonical(floor):
            return label, int(floor)
    for label, parser in (('magitek',magitek_floor_number),('giant',giant_fortress_floor_number)):
        floor = parser(rid)
        if floor is not None and not re.search(r'_r\d+$', rid):
            return label, int(floor)
    return None


def chamber_identity(rid):
    found = CHAMBER.fullmatch(str(rid or ''))
    if not found:
        return None
    return found.group(1), found.group(2), int(found.group(3))


def chamber_id(kind, family, floor):
    if kind not in {'secret','titan'} or family not in FAMILIES or int(floor)<1:
        raise ValueError('Nieprawidłowe legowisko')
    return f'v2100_{kind}_{family}_{int(floor)}'


def challenge_kind(floor):
    floor = int(floor)
    if floor >= 50 and floor % 50 == 0:
        return 'titan'
    if floor >= 25 and floor % 25 == 0:
        return 'secret'
    return None


def titan_for_floor(floor):
    floor = int(floor)
    if floor < 50 or floor % 50:
        return None
    return TITANS[(floor // 50 - 1) % len(TITANS)]


def _source_room(family, floor):
    from systems.echo_dungeon_v1500 import echo_floor_id
    from systems.dungeons_regions import (
        crypt_floor_id, mythic_crypt_floor_id, astral_floor_id, mythic_astral_floor_id,
    )
    from world.uoss_superboss_world import uoss_deep_dungeon_floor_id_v11331
    known = {'crypt':crypt_floor_id,'mythic_crypt':mythic_crypt_floor_id,
             'astral':astral_floor_id,'mythic_astral':mythic_astral_floor_id,
             'deep':uoss_deep_dungeon_floor_id_v11331,
             'echo':lambda x: echo_floor_id(x,'shrine')}
    if family in known:
        return known[family](floor)
    # Other dungeon families are parsed by their canonical room identifiers;
    # the exact visited source is recorded on creation, not guessed.
    return None


def _build_chamber(world, rooms, templates, family, floor, kind, source):
    room_id = chamber_id(kind, family, floor)
    if room_id in rooms:
        return room_id
    from systems.content_registry import ITEMS
    if kind == 'titan':
        slug, name, element, *_ = titan_for_floor(floor)
        stage = min(800, 300 + floor * 2)
        depth = 1 + floor / 100.0
        boss_id = f'v2100_titan_{family}_{floor}_boss'
        cm.catalog_assign({
            'name':f'Legowisko Tytana: {name} — piętro {floor}',
            'zone':f'{FAMILIES[family]} — Pradawni Tytani',
            'desc':f'Opcjonalne starcie z {name}. Zapowiedzi ataków są jawne. '
                   'Wpisz tytani info, tytani obrona w walce; POŁUDNIE lub WYJSCIE prowadzi na to samo piętro.',
            'exits':{'south':source}, 'recommended_mastery':stage,
            'procedural_dynamic':True,'generated_on_demand':True,
            'v2100_chamber':True, 'v2100_floor':floor,
        },'ROOMS',rooms,(room_id,))
        cm.catalog_assign({
            'name':name, 'max_hp':int((950_000 + stage * 3800) * depth),
            'damage':int((9_000 + stage * 25) * (depth ** .60)),
            'damage_type':'physical' if element=='physical' else 'magic',
            'attack_elements_v11339':() if element=='physical' else (element,),
            'boss':True,'world_boss':True,'rank':'world_boss',
            'generator_level':stage,
            'stat_reward':int((stage * 5500 + floor * 800) * depth),
            'class_xp_reward':int((stage * 14000 + floor * 1800) * depth),
            'soul_reward':int((stage * 7500 + floor * 850) * depth),
            'silver':int((stage * 2700 + floor * 400) * depth),
            'gold':0,'mithril':0,
            'drops':{'soul_shard':1.0},
            'stationary_mob':True,'auto_aggro':False,
            'v2100_titan':slug,'v2100_floor':floor,'v2100_family':family,
            'quest_target':boss_id,
        },'MOB_TEMPLATES',templates,(boss_id,))
        world._generatorize_runtime_room(room_id)
        world._register_runtime_spawn(room_id, boss_id)
    else:
        cm.catalog_assign({
            'name':f'Sekretna Komnata, piętro {floor} — {FAMILIES[family]}',
            'zone':f'{FAMILIES[family]} — Tajemnice Głębin',
            'desc':'Spokojne miejsce bez pułapek. Wpisz lochy7 sekret, aby zbadać artefakty '
                   'i odebrać osobistą nagrodę za odkrycie. POŁUDNIE lub WYJSCIE do lochu.',
            'exits':{'south':source},'procedural_dynamic':True,
            'generated_on_demand':True,'v2100_chamber':True,
            'v2100_floor':floor,
        },'ROOMS',rooms,(room_id,))
        world._generatorize_runtime_room(room_id)
    return room_id


def install_titans_v2100(rooms, items, world_class):
    """Attach lazy side branches after all legacy dungeon wrappers, never override exits."""
    for slug, name, element, relic_name, slot, stats, properties in TITANS:
        cm.catalog_assign({
            'name':relic_name,'type':'armor','slot':slot,'rarity':'legendary',
            'defense':370,'stats':stats,'properties':properties,'price':None,
            'desc':f'Unikalne trofeum Tytana {name}. Można łączyć z innym EQ.'
        },'ITEMS',items,(f'v2100_relic_{slug}',))
    cm.catalog_assign({'name':'Esencja Pradawnego Tytana','type':'craft_material',
        'rarity':'legendary','price':1_600_000,
        'desc':'Rzadki materiał zdobywany za rzeczywiste zwycięstwa z Tytanami i odkrycia głębin.'},
        'ITEMS',items,('v2100_titan_essence',))
    def attach_side_entrance(room_id, family, floor):
        kind = challenge_kind(floor)
        if not kind or room_id not in rooms:
            return False
        exits = rooms[room_id].get('exits', {})
        if not isinstance(exits, dict):
            return False
        candidate = chamber_id(kind,family,floor)
        _CHAMBER_SOURCES.setdefault(candidate,room_id)
        if candidate in exits.values():
            return True
        direction = next((d for d in ('north','northeast','northwest','forward') if d not in exits),None)
        if direction is None:
            return False  # preserve every authored exit
        cm.catalog_assign(candidate,'ROOMS',rooms,(room_id,'exits',direction))
        extra = (' Opcjonalne legowisko Tytana: ' if kind=='titan' else
                 ' Sekretna komnata: ') + direction.upper() + '.'
        cm.catalog_assign(str(rooms[room_id].get('desc','')) + extra,
                          'ROOMS',rooms,(room_id,'desc'))
        return True

    # Important: many of the first 200 floors were authored at startup.
    # ensure_runtime_room() fast-paths existing ROOMS, so attach their optional
    # doors *now*, without generating either the boss or the side room.
    for _existing in tuple(rooms):
        if 'floor_' not in str(_existing) and not str(_existing).startswith('v1500_echo_'):
            continue
        _identity = dungeon_identity(_existing)
        if _identity:
            attach_side_entrance(_existing, *_identity)

    previous = world_class.ensure_infinite_dungeon_floor
    def ensure_v2100(self, room_id):
        room_id = str(room_id or '')
        chamber = chamber_identity(room_id)
        if chamber:
            kind,family,floor = chamber
            origin = _CHAMBER_SOURCES.get(room_id) or _source_room(family,floor)
            if origin is None:
                return False
            if origin not in rooms:
                previous(self, origin)
            if origin not in rooms:
                return False
            _build_chamber(self,rooms,templates,family,floor,kind,origin)
            return True
        result = previous(self,room_id)
        source = dungeon_identity(room_id)
        entrance_room = room_id
        # Echo generates all five cells when the gate is first entered. The
        # runtime may skip ensure() on the already-existing shrine, so install
        # the side exit onto the shrine immediately at floor generation.
        if source is None:
            from systems.echo_dungeon_v1500 import echo_identity, echo_floor_id
            e = echo_identity(room_id)
            if e:
                source = ('echo', int(e[0]))
                entrance_room = echo_floor_id(e[0], 'shrine')
        if not result or not source or entrance_room not in rooms:
            return result
        family, floor = source
        attach_side_entrance(entrance_room, family, floor)
        return result
    from systems.content_registry import MOB_TEMPLATES as templates
    # The Echo Labyrinth's on-demand floor generator is wrapped above, not
    # replaced. Preserve its capability marker for the *strict* full-game
    # exit audit: a static down-exit into an as-yet ungenerated Echo floor
    # is safe only if the actual installed generator can resolve it.
    # Without forwarding this marker the audit incorrectly reports
    # broken_exit(v1500_echo_entry, down, v1500_echo_1_gate).
    ensure_v2100._v1500_echo = bool(getattr(previous, '_v1500_echo', False))
    world_class.ensure_infinite_dungeon_floor = ensure_v2100
    return True


def titan_round_v2100(mob, template):
    """One deterministic telegraph and phase announcement per boss turn."""
    slug = str(template.get('v2100_titan') or '')
    if slug not in TITAN_BY_SLUG:
        return ''
    turn = max(0,int(getattr(mob,'combat_turn',0) or 0))
    if getattr(mob,'v2100_last_turn',-1)==turn:
        return ''
    if turn == 1:
        # Respawn reuses the MobState in historical dungeon engines.
        # An old fight must not leave a burst/phase armed for the next party.
        mob.v2100_phase = 0
        mob.v2100_warning_turn = -1
        mob.v2100_burst_turn = -1
    mob.v2100_last_turn=turn
    name=TITAN_BY_SLUG[slug][1]
    maximum=max(1,int(getattr(mob,'adaptive_max_hp_v11330',0) or template.get('max_hp',1)))
    hp=max(0,int(getattr(mob,'hp',maximum)))
    ratio=hp/maximum
    phase=4 if ratio<=.15 else 3 if ratio<=.40 else 2 if ratio<=.70 else 1
    old=int(getattr(mob,'v2100_phase',0) or 0)
    mob.v2100_phase=phase
    msgs=[]
    if not old:
        msgs.append(f'TYTAN: {name}. Faza I. Uważaj na zapowiedzi ataków.')
    elif phase>old:
        msgs.append(f'TYTAN: {name}, faza {phase}. Zmiana stylu ataków!')
    # Minor signature tactics: self-sustain has hard limits, no percentage
    # damage against players and no involuntary loss of player actions.
    if slug in ('morven','velira','nharon') and phase>=2 and turn>0 and turn%7==0:
        restore={'morven':.035,'velira':.025,'nharon':.020}[slug]
        healed=min(max(0,maximum-hp), max(1,int(maximum*restore)))
        if healed:
            mob.hp=hp+healed
            msgs.append(f'TYTAN: {name} odzyskuje {healed} HP dzięki własnej mocy.')
    if turn>0 and turn % 4 == 3:
        mob.v2100_warning_turn=turn
        msgs.append(f'TYTAN: {name} przygotowuje {titan_ability_v2100(slug)}. Następny jego atak będzie potężniejszy. Wpisz tytani obrona.')
    elif turn>0 and turn%4 == 0 and getattr(mob,'v2100_warning_turn',-1)==turn-1:
        mob.v2100_burst_turn=turn
        msgs.append(f'TYTAN: {name} uwalnia {titan_ability_v2100(slug)}! Osłona zmniejsza obrażenia.')
    else:
        mob.v2100_burst_turn=-1
    return ' '.join(msgs)


def titan_ability_v2100(slug):
    return {'ragnor':'Płomienną Zagładę','velira':'Kryształowy Mróz',
            'ormak':'Żelazne Miażdżenie','morven':'Krzyk Dusz',
            'althira':'Sąd Burzy','vardun':'Runiczne Załamanie',
            'kaelor':'Echo Czasu','nharon':'Rozdarcie Pustki'}.get(slug,'Pradawny Atak')


def titan_attack_multiplier_v2100(mob, template, target):
    if not template.get('v2100_titan'):
        return 1.0
    turn=int(getattr(mob,'combat_turn',0) or 0)
    if getattr(mob,'v2100_burst_turn',-1)!=turn:
        return 1.0
    # Guard is per player, per encounter and only spent on a real announced burst.
    guarded = getattr(target,'v2100_guard_mob','') == str(mob.key)
    if guarded:
        target.v2100_guard_mob=''
    phase=max(1,int(getattr(mob,'v2100_phase',1) or 1))
    slug = str(template.get('v2100_titan'))
    # Different signature attack cadences; guard always removes the burst.
    force = {'ragnor':.18,'velira':.10,'ormak':.22,'morven':.13,
             'althira':.20,'vardun':.15,'kaelor':.17,'nharon':.23}.get(slug,.14)
    return (0.65 if guarded else 1.0+force*phase)
