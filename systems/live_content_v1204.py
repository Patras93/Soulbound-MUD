# -*- coding: utf-8 -*-
"""v12.00.4: additive, validated hot content for a running Soulbound world.

No Python eval/import/reload; admin-submitted content is inert JSON in SQLite.
The existing ROOMS / MOB_TEMPLATES registries are kept *in place* so imported
references used by old code see changes immediately.  Changes to existing mob
statistics take effect for subsequent spawns, never mid-attack.
"""
import copy
import json
import re

from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from data.items import ITEMS
from data.npcs import NPCS
from data.shops import SHOPS
from data.quests import QUESTS
from data.crafting_recipes import CRAFT_RECIPES
from core.classes_skills import CLASS_SKILLS
from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
from systems.live_progression_v1206 import install as install_live_xp
from systems.live_olc21_phase_strategy import PHASE_STRATEGY_FIELDS
from systems.live_quest_olc_v1209 import (QUEST_XP_ALIASES, QUEST_AUTO_FIELDS, QUEST_EDIT_FIELDS, parse_quest_edit, validate_quest_edit, news_summary)

ID = re.compile(r"^live_[a-z0-9_]{3,55}$")
DIRECTIONS = frozenset(("north", "south", "east", "west", "up", "down", "northeast", "northwest", "southeast", "southwest"))
FIELDS = frozenset(("max_hp", "damage", "class_xp_reward", "soul_reward", "stat_reward"))
MISSING = object()


def _live_level_bound_v5900(kind):
    # v59: the administrator may raise progression ceilings without bypassing
    # existing OLC validation. Default remains the historical 800.
    from core.live_level_caps_v5200 import cap, effective_number
    return effective_number(cap(kind))


def blank():
    return {"rooms": {}, "links": [], "mobs": {}, "spawns": [], "balances": {},
            "room_edits": {}, "mob_edits": {}, "items": {}, "item_edits": {},
            "npcs": {}, "npc_edits": {}, "shops": {}, "quests": {},
            "quest_edits": {}, "recipes": {}, "recipe_edits": {},
            "profession_edits": {}, "tool_edits": {}, "skill_edits": {},
            "resource_edits": {}, "shop_edits": {}, "skills": {},
            "summon_edits": {}, "world_overrides": {}, "v24_rules": {
                "professions": {}, "uoss": {}, "summons": {}, "cap": {},
                "events": {}, "story": {}, "world": {}}, "v26_rules": {
                "uoss": {}, "professions": {}, "summons": {}, "events": {},
                "story": {}, "factions": {}, "world": {}}, "v27_rules": {
                "uoss": {}, "professions": {}, "summons": {}, "skills": {},
                "events": {}, "story": {}, "factions": {}, "shops": {}}, "v28_rules": {
                "uoss": {}, "professions": {}, "summons": {}, "skills": {},
                "events": {}, "story": {}, "guilds": {}, "economy": {}}, "v29_rules": {
                "bosses": {}, "professions": {}, "summons": {}, "skills": {},
                "events": {}, "story": {}, "guilds": {}, "world": {}}, "v32_rules": {
                "uoss": {}, "professions": {}, "summons": {}, "skills": {},
                "events": {}, "story": {}, "guilds": {}, "world": {}}, "v33_rules": {
                "uoss": {}, "professions": {}, "summons": {}, "skills": {},
                "events": {}, "story": {}, "guilds": {}, "world": {}}, "v34_rules": {
                "uoss": {}, "professions": {}, "summons": {}, "skills": {},
                "events": {}, "story": {}, "guilds": {}, "world": {}}, "v35_rules": {
                "bosses": {}, "activities": {}, "wars": {}, "cities": {}}, "v98_rules": {}, "v99_rules": {}, "v100_rules": {}, "v101_rules": {}}


def _text(value, limit, field):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(x) < 32 for x in value):
        raise ValueError(f"{field}: wymagany tekst bez znaków sterujących, maks. {limit} znaków.")
    return value.strip()


def _integer(value, minimum, maximum, label):
    if isinstance(value, bool):
        raise ValueError(f"{label}: nieprawidłowa liczba.")
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label}: wymagana liczba całkowita.") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{label}: zakres {minimum}–{maximum}.")
    return number


class LiveContentV1204:
    def __init__(self, db):
        self.db = db
        self.conn = db.conn
        self.conn.execute("""CREATE TABLE IF NOT EXISTS live_content_v1204
            (id INTEGER PRIMARY KEY CHECK(id = 1), revision INTEGER NOT NULL,
             payload TEXT NOT NULL)""")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS live_content_history_v1204
            (revision INTEGER PRIMARY KEY, payload TEXT NOT NULL,
             admin_login TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        self.conn.commit()
        row = self.conn.execute("SELECT revision,payload FROM live_content_v1204 WHERE id=1").fetchone()
        self.revision = int(row['revision']) if row else 0
        self.active = self._compat(json.loads(row['payload'])) if row else blank()
        self.draft = copy.deepcopy(self.active)
        self._undo = []
        self._spawned_runtime = set()
        self.validate(self.active)
        self._install(self.active, None)

    @staticmethod
    def _compat(payload):
        # All previously published v12.00.4 revisions remain readable.
        if not isinstance(payload, dict):
            raise ValueError('Niepoprawny format zapisanej wersji świata.')
        return {**blank(), **payload}

    def validate(self, data):
        if not isinstance(data, dict) or set(data) != set(blank()):
            raise ValueError("Niepoprawny zestaw sekcji aktualizacji.")
        rooms, links, mobs, spawns, balances = (data[x] for x in ("rooms", "links", "mobs", "spawns", "balances"))
        if not isinstance(rooms, dict) or len(rooms) > 200 or not isinstance(mobs, dict) or len(mobs) > 200:
            raise ValueError("Maksymalnie 200 nowych lokacji i 200 nowych potworów.")
        if not isinstance(links, list) or len(links) > 800 or not isinstance(spawns, list) or len(spawns) > 400 or not isinstance(balances, dict) or len(balances) > 200:
            raise ValueError("Przekroczono limit przejść, spawnów lub ustawień balansu.")
        for rid, meta in rooms.items():
            if not ID.fullmatch(rid):
                raise ValueError(f"Id lokacji musi zaczynać się od live_: {rid}.")
            if rid in ROOMS and rid not in self.active['rooms']:
                raise ValueError(f"Id {rid} zajęte przez oryginalny świat.")
            if not isinstance(meta, dict) or set(meta) != {'name', 'desc', 'zone', 'generator_level'}:
                raise ValueError(f"Lokacja {rid}: niepoprawne pola.")
            _text(meta['name'], 100, 'Nazwa lokacji')
            _text(meta['desc'], 1600, 'Opis lokacji')
            _text(meta['zone'], 100, 'Region')
            _integer(meta['generator_level'], 1, _live_level_bound_v5900('postac'), 'Poziom lokacji')
        for mid, meta in mobs.items():
            if not ID.fullmatch(mid):
                raise ValueError(f"Id potwora musi zaczynać się od live_: {mid}.")
            if mid in MOB_TEMPLATES and mid not in self.active['mobs']:
                raise ValueError(f"Id {mid} zajęte przez oryginalny bestiariusz.")
            if not isinstance(meta, dict) or set(meta) != {'name', 'generator_level', 'max_hp', 'damage', 'class_xp_reward'}:
                raise ValueError(f"Potwór {mid}: niepoprawne pola.")
            _text(meta['name'], 100, 'Nazwa potwora')
            _integer(meta['generator_level'], 1, _live_level_bound_v5900('postac'), 'Poziom potwora')
            _integer(meta['max_hp'], 1, 10**15, 'HP')
            _integer(meta['damage'], 1, 10**12, 'Obrażenia')
            _integer(meta['class_xp_reward'], 1, 10**15, 'EXP')
        all_rooms = set(ROOMS) | set(rooms)
        all_mobs = set(MOB_TEMPLATES) | set(mobs)
        directions_seen = set()
        for link in links:
            if not isinstance(link, list) or len(link) != 3:
                raise ValueError("Przejście wymaga: [lokacja, kierunek, cel].")
            origin, direction, destination = link
            if origin not in all_rooms or destination not in all_rooms or direction not in DIRECTIONS:
                raise ValueError(f"Nieistniejąca lokacja lub niepoprawny kierunek: {link}.")
            if origin not in rooms and destination not in rooms:
                raise ValueError("Nowe przejście musi prowadzić do lub z lokacji live_. Nie obchodzę istniejących blokad świata.")
            if (origin, direction) in directions_seen:
                raise ValueError(f"Powtórzone przejście {origin} {direction}.")
            directions_seen.add((origin, direction))
            if origin in ROOMS and origin not in self.active['rooms']:
                existing = ROOMS[origin].get('exits', {}).get(direction)
                previously_live = next((p[2] for p in self.active['links'] if p[:2] == [origin, direction]), None)
                if existing is not None and existing != destination and previously_live != existing:
                    raise ValueError(f"Istniejące przejście {origin} {direction} jest zajęte; nie nadpisuję go.")
        used = set()
        for spawn in spawns:
            if not isinstance(spawn, list) or len(spawn) != 2 or spawn[0] not in all_rooms or spawn[1] not in all_mobs:
                raise ValueError(f"Nieznana lokacja lub potwór w spawnie {spawn}.")
            if tuple(spawn) in used:
                raise ValueError(f"Powtórzony spawn {spawn}.")
            used.add(tuple(spawn))
        for mob_id, setting in balances.items():
            if mob_id not in all_mobs or not isinstance(setting, dict) or not setting or not set(setting) <= FIELDS:
                raise ValueError(f"Nieprawidłowy balans potwora {mob_id}.")
            for field, value in setting.items():
                _integer(value, 1, 10**15, f"{mob_id}.{field}")
        detail = self._validate_olc(data, all_rooms, all_mobs)
        return (f"{len(rooms)} lokacji, {len(links)} przejść, {len(mobs)} potworów, "
                f"{len(spawns)} spawnów, {len(balances)} zmian balansu; {detail}")

    def _validate_olc(self, data, room_ids, mob_ids):
        """Strict data-only OLC: no arbitrary code or destructive schema changes."""
        allowed_fields = {
            'room_edits': {'name', 'desc', 'zone', 'generator_level'},
            'mob_edits': {'name', 'max_hp', 'damage', 'class_xp_reward',
                          'soul_reward', 'stat_reward', 'drops', 'auto_aggro',
                          'silver', 'gold', 'mithril', 'respawn_seconds', 'damage_type',
                          'olc_boss_phases', 'olc_boss_tactic_element', 'olc_boss_tactic_interval',
                          'olc_boss_support_interval', 'olc_boss_support_duration',
                          'olc_boss_rally_interval', 'olc_boss_rally_duration', 'olc_boss_guard_threshold',
                          'olc_boss_element_cycle', 'olc_boss_support_priority',
                          'olc_boss_guardian_interval', 'olc_boss_guardian_roles', 'olc_boss_guardian_hp_threshold', 'olc_boss_guardian_phase_roles', 'olc_boss_phase_element_cycles', 'olc_boss_rally_hp_threshold', 'olc_boss_guardian_rewards', 'boss', 'olc_ancient_phases'} | set(PHASE_STRATEGY_FIELDS),
            'item_edits': {'name', 'desc', 'price', 'currency', 'stats', 'sell_silver',
                           'sell_gold', 'heal', 'defense', 'attack', 'magic_attack', 'magic_defense', 'weapon_power', 'required_level'},
            'npc_edits': {'name', 'dialogue', 'room', 'quest', 'shopkeeper', 'olc_dialogue_after_quest', 'olc_dialogue_after_quests'},
            'quest_edits': QUEST_EDIT_FIELDS,
            'recipe_edits': {'name', 'desc', 'min_profession_level', 'ingredients',
                             'stations', 'quantity', 'output', 'min_tool_level', 'tool_xp', 'profession_xp'},
            'shop_edits': {'inventory'},
        }
        registry = {
            'room_edits': ROOMS, 'mob_edits': MOB_TEMPLATES,
            'item_edits': ITEMS, 'npc_edits': NPCS,
            'quest_edits': QUESTS, 'recipe_edits': CRAFT_RECIPES,
            'shop_edits': SHOPS,
        }
        for section, fields in allowed_fields.items():
            patches = data[section]
            limit = 8000 if section == 'quest_edits' else 400
            if not isinstance(patches, dict) or len(patches) > limit:
                raise ValueError(f'{section}: wymagany słownik (maks. {limit}).')
            for key, patch in patches.items():
                if key not in registry[section] and key not in (data.get({'item_edits':'items', 'npc_edits':'npcs', 'quest_edits':'quests', 'recipe_edits':'recipes', 'room_edits':'rooms', 'mob_edits':'mobs', 'shop_edits':'shops'}[section]) or {}):
                    raise ValueError(f'{section}: nieznany identyfikator {key}.')
                if not isinstance(patch, dict) or not patch or not set(patch) <= fields:
                    raise ValueError(f'{section}/{key}: niedozwolone pola edycji.')
                for field, value in patch.items():
                    # Renaming an existing quest giver would silently hide its quests.
                    if section == 'quest_edits':
                        quest_base = dict(QUESTS.get(key) or data['quests'].get(key) or {})
                        if not quest_base:
                            raise ValueError('Nieznana definicja questa.')
                        # Validate against all staged fields, not a partial update.
                        validate_quest_edit(key, quest_base, patch, set(ITEMS) | set(data['items']),
                                            set(MOB_TEMPLATES) | set(data['mobs']),
                                            set(QUESTS) | set(data['quests']), NPCS, data['npcs'])
                        break
                    if section == 'npc_edits' and field == 'name' and key in NPCS:
                        old_name = str(NPCS[key]['name']).casefold()
                        if str(value).casefold() != old_name and any(
                                str(q.get('giver', '')).casefold() == old_name
                                for q in list(QUESTS.values()) + list(data['quests'].values())):
                            raise ValueError('NPC prowadzi questy; nie zmieniam nazwy zleceniodawcy na żywo.')
                    # OLC 4.0 — reuse the same strict checks for JSON imports
                    # and in-game typed edits. No executable formulas or scripts.
                    from systems.live_olc4_fields import validate_extra
                    if validate_extra(section, key, field, value, data,
                                      room_ids, mob_ids):
                        continue
                    if field in ('name','zone'):
                        _text(value, 100, field)
                    elif field in ('desc','dialogue','description'):
                        _text(value, 1600, field)
                    elif field == 'auto_aggro':
                        if not isinstance(value, bool): raise ValueError('auto_aggro wymaga true/false.')
                    elif field == 'drops':
                        self._validate_drops(value, set(ITEMS) | set(data['items']))
                    elif field == 'ingredients':
                        self._validate_ingredients(value, set(ITEMS) | set(data['items']))
                    else:
                        _integer(value, 1 if field in ('max_hp','damage','generator_level','min_profession_level') else 0,
                                 800 if field in ('generator_level','min_profession_level') else 10**15, field)
        # One NPC per accessible room, also when moving two NPCs in one
        # revision. This includes NPCs added earlier by this OLC service.
        from systems.live_olc4_fields import validate_npc_locations
        validate_npc_locations(data, room_ids)
        # v12.00.6: existing professions/tools and existing real skill fields.
        for section, catalogue in (('profession_edits', PROFESSION_RANK_NAMES),
                                   ('tool_edits', TOOL_PROFESSION_MAP)):
            entries = data[section]
            if not isinstance(entries, dict) or len(entries) > 200:
                raise ValueError(f'{section}: maksymalnie 200 ustawień.')
            for key, fields in entries.items():
                if key not in catalogue or not isinstance(fields, dict) or not fields or not set(fields) <= {'xp_percent','xp_scale'} or len(fields) != 1:
                    raise ValueError(f'{section}: nieznana profesja/narzędzie albo niedozwolona zmiana {key}.')
                if 'xp_percent' in fields: _integer(fields['xp_percent'], 100, 1000, 'EXP procent (100–1000)')
                if 'xp_scale' in fields: _integer(fields['xp_scale'], 0, 1000, 'EXP skala (0–1000)')
        # v12.00.7: per-resource awards (ores, fish, herbs, timber, and
        # recognized resource materials) are published as validated data.
        resource_edits = data['resource_edits']
        if not isinstance(resource_edits, dict) or len(resource_edits) > 5000:
            raise ValueError('resource_edits: maksymalnie 5000 surowców.')
        for item_id, fields in resource_edits.items():
            item = ITEMS.get(item_id)
            if (not isinstance(item_id, str) or not isinstance(item, dict) or
                    item.get('type') not in ('resource', 'material', 'craft_material',
                                              'gem_raw', 'archaeology_find')):
                raise ValueError(f'Nieznany surowiec lub niedozwolony typ: {item_id}.')
            allowed = {'prof_xp', 'tool_xp', 'prof_percent', 'tool_percent',
                       'prof_fixed', 'tool_fixed', 'prof_scale', 'tool_scale',
                       'prof_mode', 'tool_mode'}
            if not isinstance(fields, dict) or not fields or not set(fields) <= allowed:
                raise ValueError(f'{item_id}: dozwolone prof_xp/tool_xp/prof_percent/tool_percent.')
            for field, value in fields.items():
                if field.endswith('mode'):
                    if value not in ('auto','manual','percent'):
                        raise ValueError(f'{item_id}.{field}: auto/manual/percent.')
                elif field.endswith('scale'):
                    _integer(value, 0, 1000, f'{item_id}.{field}')
                elif field.endswith('fixed'):
                    _integer(value, 0, 10**12, f'{item_id}.{field}')
                elif field.endswith('percent'):
                    _integer(value, 100, 1000, f'{item_id}.{field}')
                else:
                    _integer(value, 1, 10**12, f'{item_id}.{field}')
            for side in ('prof','tool'):
                mode = fields.get(side + '_mode')
                if mode == 'manual' and side + '_fixed' not in fields:
                    raise ValueError(f'{item_id}: najpierw ustaw {side}_fixed, potem manual.')
                if mode == 'percent' and side + '_scale' not in fields:
                    raise ValueError(f'{item_id}: najpierw ustaw {side}_scale, potem percent.')
        from systems.live_olc22_empire import validate_summons, validate_world
        validate_summons(data['summon_edits'])
        validate_world(data['world_overrides'])
        from systems.live_olc24_revolution import validate as validate_v24
        validate_v24(data['v24_rules'], items={**ITEMS, **data['items']}, rooms={**ROOMS,**data['rooms']})
        from systems.live_olc26_world import validate as validate_v26
        validate_v26(data['v26_rules'], quests=data['quests'], professions=data['v24_rules']['professions'])
        from systems.live_olc27_master import validate as validate_v27
        validate_v27(data['v27_rules'], v26_events=data['v26_rules']['events'],
                     v24_professions=data['v24_rules']['professions'], live_shops=data['shops'])
        from systems.live_olc28_expansion import validate as validate_v28
        validate_v28(data['v28_rules'], professions=data['v24_rules']['professions'],
                     events=data['v26_rules']['events'])
        from systems.live_olc29_creation import validate as validate_v29
        validate_v29(data['v29_rules'], payload=data)
        from systems.live_olc32_finale import validate as validate_v32
        validate_v32(data['v32_rules'], payload=data)
        from systems.live_olc33_mechanics import validate as validate_v33
        validate_v33(data['v33_rules'], payload=data)
        from systems.live_olc34_integration import validate as validate_v34
        validate_v34(data['v34_rules'], payload=data)
        from systems.live_olc35_finale import validate as validate_v35
        validate_v35(data['v35_rules'], payload=data)
        from systems.uoss_tactics_v9800 import validate as validate_v98
        validate_v98(data['v98_rules'])
        from systems.uoss_regeneration_v9900 import validate as validate_v99
        validate_v99(data['v99_rules'])
        from systems.uoss_ai_v10000 import validate as validate_v100
        validate_v100(data['v100_rules'])
        from systems.live_mechanics_v10100 import validate as validate_v101
        validate_v101(data['v101_rules'])
        from systems.live_olc4_new_skills import validate_new_skills
        validate_new_skills(data['skills'], self.active['skills'])
        from systems.live_olc6_skill_editor import validate_existing_skill_edits
        validate_existing_skill_edits(data['skill_edits'], data['skills'])
        self._validate_catalog_additions(data, room_ids, mob_ids)
        return (f"{sum(len(data[k]) for k in allowed_fields)} edycji, "
                f"{len(data['items'])} przedmiotów, {len(data['npcs'])} NPC, "
                f"{len(data['quests'])} questów, {len(data['recipes'])} receptur, "
                f"{len(data['shops'])} sklepów, "
                f"{len(data['profession_edits'])} reguł profesji, "
                f"{len(data['tool_edits'])} reguł narzędzi, "
                f"{len(data['skill_edits'])} edycji skilli, {len(data['skills'])} nowych skilli, "
                f"{len(data['resource_edits'])} indywidualnych reguł surowców, "
                f"{len(data['summon_edits'])} profili summonów, "
                f"{len(data['world_overrides'])} globalnych reguł")

    @staticmethod
    def _validate_drops(drops, items):
        if not isinstance(drops, dict) or len(drops) > 30:
            raise ValueError('Drop: wymagany słownik z maks. 30 przedmiotami.')
        for item, chance in drops.items():
            if item not in items or isinstance(chance, bool) or not isinstance(chance, (int, float)) or not 0 <= chance <= 1:
                raise ValueError(f'Drop {item}: szansa musi być od 0 do 1, przedmiot musi istnieć.')

    @staticmethod
    def _validate_ingredients(ingredients, items):
        if not isinstance(ingredients, dict) or not 1 <= len(ingredients) <= 12:
            raise ValueError('Receptura wymaga 1–12 materiałów.')
        for item, amount in ingredients.items():
            if item not in items:
                raise ValueError(f'Nieznany materiał {item}.')
            _integer(amount, 1, 10000, 'Ilość materiału')

    def _validate_catalog_additions(self, data, room_ids, mob_ids):
        item_ids = set(ITEMS) | set(data['items'])
        npc_names = {n['name'].casefold() for key, n in NPCS.items() if key not in self.active['npcs']}
        occupied = {n['room'] for key, n in NPCS.items() if key not in self.active['npcs']}
        for section, max_count in (('items', 200), ('npcs', 100), ('quests', 200),
                                   ('recipes', 200), ('shops', 200)):
            if not isinstance(data[section], dict) or len(data[section]) > max_count:
                raise ValueError(f'{section}: zbyt wiele wpisów lub błędny format.')
        for iid, item in data['items'].items():
            if not ID.fullmatch(iid) or (iid in ITEMS and iid not in self.active['items']):
                raise ValueError(f'Przedmiot wymaga wolnego ID live_: {iid}.')
            if not isinstance(item, dict) or not {'name','desc','type','price','currency'} <= set(item):
                raise ValueError(f'Przedmiot {iid}: wymagane name, desc, type, price, currency.')
            _text(item['name'], 100, 'Nazwa przedmiotu')
            _text(item['desc'], 500, 'Opis przedmiotu')
            if item['currency'] != 'silver':
                raise ValueError('Nowe przedmioty OLC używają srebra; pozostałe waluty można przypisać dopiero, gdy obsługuje je silnik.')
            _integer(item['price'], 0, 10**10, 'Cena')
            # These three pre-existing item mechanics have complete runtime
            # support. All quest tokens, soul relics and authored rewards stay
            # excluded to avoid cloning hidden effects.
            if item['type'] == 'craft_material':
                if set(item) != {'name','desc','type','price','currency'}:
                    raise ValueError('Materiał: niedozwolone dodatkowe właściwości.')
            elif item['type'] == 'armor':
                ordinary = {'name','desc','type','price','currency','slot','defense'}
                jewelry = ordinary | {'stats', 'required_level'}
                advanced = jewelry | {'attack'}
                magical = advanced | {'magic_attack', 'magic_defense', 'weapon_power'}
                if set(item) not in (ordinary, jewelry, advanced, magical):
                    raise ValueError('Zbroja: niedozwolone dodatkowe efekty.')
                if item['slot'] not in ('body','head','hands','legs','feet','ring','bracelet','charm','accessory','shield'):
                    raise ValueError('Zbroja: nieznany slot.')
                _integer(item['defense'], 1, 10**12, 'Obrona')
                if set(item) in (jewelry, advanced, magical):
                    if set(item) == jewelry and item['slot'] not in ('ring','bracelet','charm','accessory'):
                        raise ValueError('Bonusy OLC 5.0 wyłącznie dla biżuterii.')
                    if set(item) in (advanced, magical):
                        _integer(item['attack'], 0, 10**12, 'Atak wyposażenia')
                    if set(item) == magical:
                        for power_field in ('magic_attack', 'magic_defense', 'weapon_power'):
                            _integer(item[power_field], 0, 10**12, power_field)
                    _integer(item['required_level'], 1, 800, 'Poziom biżuterii')
                    stats = item['stats']
                    if (not isinstance(stats, dict) or not 1 <= len(stats) <= (6 if set(item) in (advanced, magical) else 1)
                            or not set(stats) <= {'strength','dexterity','intelligence','wisdom','willpower','constitution'}):
                        raise ValueError('Wyposażenie: od jednej do sześciu podstawowych statystyk.')
                    for stat, amount in stats.items():
                        _integer(amount, 1, 10**7, stat)
            elif item['type'] == 'tool':
                if set(item) != {'name','desc','type','price','currency','tool_type'}:
                    raise ValueError('Nowe narzędzie: wymagane pola name,desc,type,price,currency,tool_type.')
                tool = item['tool_type']
                if not any(profile['tool_type']==tool and profile['tool_item_id']==iid
                           for profile in data['v24_rules']['professions'].values()):
                    raise ValueError('Nowe narzędzie musi być przypisane do nowej profesji OLC24.')
            elif item['type'] == 'consumable':
                if set(item) != {'name','desc','type','price','currency','heal'}:
                    raise ValueError('Mikstura: jedyny dopuszczalny efekt to heal.')
                _integer(item['heal'], 1, 10**12, 'Leczenie')
            else:
                raise ValueError('Nowy przedmiot: wyłącznie craft_material, armor lub consumable z heal.')
        # NPCs may be added ONLY in a room without any existing registered NPC.
        for nid, npc in data['npcs'].items():
            if not ID.fullmatch(nid) or (nid in NPCS and nid not in self.active['npcs']):
                raise ValueError(f'NPC wymaga wolnego ID live_: {nid}.')
            if not isinstance(npc, dict) or not {'name','room','dialogue'} <= set(npc) or not set(npc) <= {'name','room','dialogue','quest','shopkeeper'}:
                raise ValueError(f'NPC {nid}: wymagane name,room,dialogue; opcjonalnie quest,shopkeeper.')
            _text(npc['name'], 100, 'Nazwa NPC'); _text(npc['dialogue'], 1600, 'Dialog NPC')
            if npc['room'] not in room_ids or npc['room'] in occupied:
                raise ValueError(f'NPC {nid}: lokacja nie istnieje lub jest już zajęta przez NPC.')
            if npc['name'].casefold() in npc_names:
                raise ValueError(f'NPC {nid}: nazwa zajęta.')
            occupied.add(npc['room']); npc_names.add(npc['name'].casefold())
            if 'shopkeeper' in npc and not isinstance(npc['shopkeeper'], bool):
                raise ValueError('shopkeeper musi być true/false.')
        for shop_room, inventory in data['shops'].items():
            if shop_room not in room_ids or not isinstance(inventory, list) or len(inventory) > 120 or len(set(inventory)) != len(inventory) or any(item not in item_ids for item in inventory):
                raise ValueError(f'Sklep {shop_room}: wymagany pokój i unikalne istniejące towary.')
        for qid, quest in data['quests'].items():
            if not ID.fullmatch(qid) or (qid in QUESTS and qid not in self.active['quests']):
                raise ValueError(f'Quest wymaga wolnego ID live_: {qid}.')
            required = {'name','giver','kind','target','needed','description','reward_silver'}
            if not isinstance(quest, dict) or not required <= set(quest) or not set(quest) <= required | {'requires_quest', 'requires_quests', 'resource_targets', 'objectives'}:
                raise ValueError(f'Quest {qid}: wymagane {sorted(required)}, opcjonalne requires_quest.')
            from systems.live_olc17_quest_dependencies import validate_dependencies
            validate_dependencies(qid, quest, set(QUESTS) | set(data['quests']))
            if 'requires_quest' in quest and (quest['requires_quest'] not in set(QUESTS) | set(data['quests']) or quest['requires_quest'] == qid):
                raise ValueError(f'Quest {qid}: nieznany lub własny poprzednik.')
            _text(quest['name'], 120, 'Quest'); _text(quest['description'], 1600, 'Opis questa')
            _text(quest['giver'], 100, 'Zleceniodawca')
            if quest['giver'].casefold() not in npc_names:
                raise ValueError(f'Quest {qid}: nie ma NPC o nazwie {quest["giver"]}.')
            if quest['kind'] == 'multi_objective':
                from systems.live_olc18_multi_objective import validate_objectives
                clean, total = validate_objectives(
                    quest.get('objectives'), mob_ids, item_ids,
                    set(NPCS) | set(data['npcs'])
                )
                if quest['objectives'] != clean or quest['needed'] != total:
                    raise ValueError(f'Quest {qid}: needed musi być sumą celów.')
            elif quest['kind'] == 'collect_resource_set':
                requirements = quest.get('resource_targets')
                if not isinstance(requirements, dict) or not 2 <= len(requirements) <= 8:
                    raise ValueError(f'Quest {qid}: wymagane 2–8 surowców w resource_targets.')
                if (quest['target'] not in requirements or
                        any(item not in item_ids or (ITEMS.get(item) or data['items'].get(item, {})).get('type')
                                not in ('resource','material','craft_material','gem_raw','archaeology_find')
                                for item in requirements)):
                    raise ValueError(f'Quest {qid}: wymagane rzeczywiste surowce.')
                quantity = sum(_integer(v, 1, 10000, 'Liczba surowca') for v in requirements.values())
                if quest['needed'] != quantity:
                    raise ValueError(f'Quest {qid}: needed musi być sumą ilości surowców.')
            elif quest['kind'] not in ('kill','collect') or (quest['target'] not in (mob_ids if quest['kind']=='kill' else item_ids)):
                raise ValueError(f'Quest {qid}: nieznany cel lub niedozwolony rodzaj.')
            _integer(quest['needed'], 1, 10000, 'Wymagana liczba')
            _integer(quest['reward_silver'], 0, 10**12, 'Srebro')
        # A cycle would make every quest in it impossible to start. Check the
        # full effective chain, including staged changes to older quests.
        effective_chains = {q:dict(v) for q,v in QUESTS.items()}
        effective_chains.update({q:dict(v) for q,v in data['quests'].items()})
        for q, patch in data['quest_edits'].items():
            effective_chains[q] = dict(effective_chains.get(q, {}), **patch)
        from systems.live_olc17_quest_dependencies import validate_dependency_graph
        validate_dependency_graph(effective_chains)
        for rid, recipe in data['recipes'].items():
            if not ID.fullmatch(rid) or (rid in CRAFT_RECIPES and rid not in self.active['recipes']):
                raise ValueError(f'Receptura wymaga wolnego ID live_: {rid}.')
            if not isinstance(recipe, dict) or set(recipe) != {'name','desc','stations','ingredients','output','quantity','min_profession_level','profession','tool_type','tool_item_id','tool_name'}:
                raise ValueError(f'Receptura {rid}: niepoprawne pola.')
            _text(recipe['name'], 100, 'Receptura'); _text(recipe['desc'], 500, 'Opis')
            for field in ('profession','tool_type','tool_item_id','tool_name'):
                _text(recipe[field], 100, field)
            if recipe['tool_item_id'] not in item_ids or recipe['output'] not in item_ids:
                raise ValueError('Receptura musi używać istniejącego narzędzia i produktu.')
            if not isinstance(recipe['stations'], list) or not recipe['stations'] or any(room not in room_ids for room in recipe['stations']):
                raise ValueError('Nieznana stacja receptury.')
            self._validate_ingredients(recipe['ingredients'], item_ids)
            _integer(recipe['quantity'], 1, 1000, 'Ilość produktu')
            _integer(recipe['min_profession_level'], 1, _live_level_bound_v5900('profesje'), 'Poziom profesji')
        for npc in data['npcs'].values():
            if npc.get('quest') and npc['quest'] not in (set(QUESTS) | set(data['quests'])):
                raise ValueError('NPC wskazuje na nieistniejący quest.')

    def _remember(self, registry, key, value):
        old = copy.deepcopy(registry[key]) if key in registry else MISSING
        self._undo.append((registry, key, old))
        registry[key] = value

    def _install(self, data, world):
        # Definition registration is synchronous and designed never to invoke user code.
        for rid, meta in data['rooms'].items():
            self._remember(ROOMS, rid, dict(meta, exits={}))
        for start, direction, end in data['links']:
            old_exits = ROOMS[start].get('exits', {})
            self._remember(ROOMS, start, dict(ROOMS[start], exits=dict(old_exits, **{direction: end})))
        for mid, meta in data['mobs'].items():
            self._remember(MOB_TEMPLATES, mid, {
                **meta, 'silver': 0, 'gold': 0, 'mithril': 0,
                'stat_reward': max(1, int(meta['class_xp_reward']) // 20),
                'soul_reward': max(1, int(meta['class_xp_reward']) // 10),
                'drops': {}, 'quest_target': mid, 'auto_aggro': False,
                'damage_type': 'physical', 'live_v1204': True,
            })
        # OLC katalogi: aktualizujemy istniejące rejestry IN PLACE.
        for section, registry in (('items', ITEMS), ('npcs', NPCS), ('quests', QUESTS), ('recipes', CRAFT_RECIPES)):
            for key, definition in data[section].items():
                content = dict(definition)
                if section == 'quests':
                    content.update({'reward_gold': 0, 'reward_mithril': 0, 'reward_items': {}, 'repeatable': False})
                if section == 'recipes':
                    content['stations'] = tuple(content['stations'])
                self._remember(registry, key, content)
        for key, stock in data['shops'].items():
            self._remember(SHOPS, key, list(stock))
        for key, patch in data['shop_edits'].items():
            self._remember(SHOPS, key, list(patch['inventory']))
        for section, registry in (('room_edits', ROOMS), ('mob_edits', MOB_TEMPLATES),
                                  ('item_edits', ITEMS), ('npc_edits', NPCS),
                                  ('quest_edits', QUESTS), ('recipe_edits', CRAFT_RECIPES)):
            for key, changes in data[section].items():
                updated = dict(registry[key], **changes)
                if section == 'quest_edits' and any(
                        field in changes for field in ('reward_silver', 'reward_gold', 'reward_mithril')):
                    # v24.00.1: the quest engine prioritizes manual_currency_reward_coins.
                    # Merely editing reward_gold left that older marker intact,
                    # so a published edit did not change the actual turn-in payout.
                    # An explicit OLC denomination edit becomes an exact manual
                    # total, while ordinary untouched quests keep their generator.
                    from core.bootstrap_economy_professions import legacy_currency_to_coins
                    coins = legacy_currency_to_coins(
                        updated.get('reward_silver', 0),
                        updated.get('reward_gold', 0),
                        updated.get('reward_mithril', 0))
                    updated.update(reward_silver=coins, reward_gold=0,
                                   reward_mithril=0, currency_reward_mode='manual',
                                   manual_currency_reward_coins=coins)
                if section == 'recipe_edits' and 'stations' in changes:
                    updated['stations'] = tuple(updated['stations'])
                self._remember(registry, key, updated)
        for mid, values in data['balances'].items():
            self._remember(MOB_TEMPLATES, mid, dict(MOB_TEMPLATES[mid], **values))
        # OLC skill fields are read from the existing live catalog; do not
        # mutate the skill in place because rollback must restore old data.
        for skill_id, fields in data['skill_edits'].items():
            for class_name, rows in CLASS_SKILLS.items():
                if any(row['id'] == skill_id for row in rows):
                    changed = [dict(row, **fields) if row['id'] == skill_id else row
                               for row in rows]
                    self._remember(CLASS_SKILLS, class_name, changed)
                    break
        # New skills join the live class registry, and the combat queue's fast
        # index gets the same definitions. Both are restored on _remove().
        from systems.live_olc4_new_skills import new_skill_definition
        import sys
        cache_module = sys.modules.get('player.session_mixins.skill_queue_buffs')
        cache = getattr(cache_module, '_SKILLS_BY_ID_V3005', None)
        from systems.elemental_combat import OLC_SKILL_ELEMENTS_V1500
        for skill_id, meta in data['skills'].items():
            if meta.get('element'):
                self._remember(OLC_SKILL_ELEMENTS_V1500,
                               (meta['class_name'], meta['name']), meta['element'])
            definition = new_skill_definition(skill_id, meta)
            class_name = meta['class_name']
            self._remember(CLASS_SKILLS, class_name, list(CLASS_SKILLS[class_name]) + [definition])
        if isinstance(cache, dict):
            for skill_id in set(data['skill_edits']) | set(data['skills']):
                found = next((row for rows in CLASS_SKILLS.values() for row in rows
                              if row['id'] == skill_id), None)
                if found:
                    self._remember(cache, skill_id, found)
        # Atomic undo for original class AI. Overrides apply to real summon turns.
        from systems.summon_ai_v1200 import CLASS_AI
        for cls, patch in data['summon_edits'].items():
            name, role, bonus = CLASS_AI[cls]
            self._remember(CLASS_AI, cls, (
                patch.get('ability',name), patch.get('role',role),
                bonus*patch.get('bonus_percent',100)/100.0))
        # OLC24: live profession registry, UOSS per-boss stats, and domain rules.
        # No player account row is touched here; only future spawns/commands.
        from systems.live_olc24_revolution import sync_active
        from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
        for prof in data['v24_rules']['professions'].values():
            self._remember(TOOL_PROFESSION_MAP, prof['tool_type'], prof['name'])
            base = next(iter(PROFESSION_RANK_NAMES.values()))
            self._remember(PROFESSION_RANK_NAMES, prof['name'], tuple(
                f'{str(rank).split(" ", 1)[0]} {prof["name"]}' for rank in base))
        for key, rules in data['v24_rules']['uoss'].items():
            template_id = f'uoss_superboss_{key}_v11136'
            if template_id in MOB_TEMPLATES:
                meta = dict(MOB_TEMPLATES[template_id])
                for attr, field in (('max_hp','max_hp_percent'),('damage','damage_percent')):
                    if field in rules:
                        meta[attr] = max(1, int(meta[attr]) * rules[field] // 100)
                if 'source_xp' in rules:
                    # UOSS exact-XP branch of real combat_rewards.py reads source_xp.
                    meta['source_xp'] = rules['source_xp']
                override = {f:rules[f] for f in ('gold','silver','mithril') if f in rules}
                if override:
                    meta['olc_uoss_currency_override'] = override
                self._remember(MOB_TEMPLATES, template_id, meta)
        # The four authentic city event templates are changed in place only
        # at publish time; old versions are restored by the existing _undo.
        from systems.world_events_v12812 import EVENTS
        w = data['v24_rules']['world'].get('global',{})
        for slug, _title, _boss, _style, _element in EVENTS:
            template_id = 'v12812_event_'+slug
            if template_id not in MOB_TEMPLATES: continue
            event = data['v24_rules']['events'].get(slug,{})
            if not event and not any(f in w for f in ('event_hp_percent','event_damage_percent')):
                continue
            meta = dict(MOB_TEMPLATES[template_id])
            if 'style' in event: meta['damage_type'] = event['style']
            if 'element' in event: meta['attack_elements_v11339'] = (event['element'],)
            for attr, fld in (('max_hp','event_hp_percent'),('damage','event_damage_percent')):
                if fld in w: meta[attr] = max(1,int(meta[attr])*w[fld]//100)
            self._remember(MOB_TEMPLATES, template_id, meta)
        sync_active(data['v24_rules'])
        from systems.live_olc26_world import sync as sync_v26
        sync_v26(data['v26_rules'])
        # New timed event bosses use the original four city arenas and rewards.
        # Their templates are registered only on publish, and restored by _undo.
        from systems.live_olc26_world import event_catalog
        for slug, spec in event_catalog().items():
            template_id = 'v26_event_' + slug
            base_id = 'v12812_event_' + spec['city']
            base = dict(MOB_TEMPLATES[base_id])
            base.update(name=spec['boss_name'], max_hp=spec['hp'],
                        damage=spec['damage'], damage_type=spec['style'],
                        attack_elements_v11339=(spec['element'],),
                        silver=spec['silver'], gold=0, mithril=0,
                        quest_target=template_id, quest_targets=(template_id,))
            self._remember(MOB_TEMPLATES, template_id, base)
        from systems.live_olc27_master import sync as sync_v27, event_rewards
        sync_v27(data['v27_rules'])
        for slug in data['v27_rules']['events']:
            template_id='v26_event_'+slug
            updated=dict(MOB_TEMPLATES[template_id],**event_rewards(slug))
            self._remember(MOB_TEMPLATES,template_id,updated)
        from systems.live_olc28_expansion import sync as sync_v28
        sync_v28(data['v28_rules'])
        from systems.live_olc29_creation import sync as sync_v29
        sync_v29(data['v29_rules'])
        from systems.live_olc32_finale import sync as sync_v32
        sync_v32(data['v32_rules'])
        from systems.live_olc33_mechanics import sync as sync_v33
        sync_v33(data['v33_rules'])
        from systems.live_olc34_integration import sync as sync_v34
        sync_v34(data['v34_rules'])
        from systems.live_olc35_finale import sync as sync_v35
        sync_v35(data['v35_rules'])
        from systems.uoss_tactics_v9800 import sync as sync_v98
        sync_v98(data['v98_rules'])
        from systems.uoss_regeneration_v9900 import sync as sync_v99
        sync_v99(data['v99_rules'])
        from systems.uoss_ai_v10000 import sync as sync_v100
        sync_v100(data['v100_rules'])
        from systems.live_mechanics_v10100 import sync as sync_v101
        sync_v101(data['v101_rules'])
        # Author reversible, unoccupied room exits without mutating original room dictionaries.
        from systems.live_olc33_mechanics import world_portals
        for _origin33, _route33 in world_portals().items():
            _room33 = dict(ROOMS[_origin33])
            _exits33 = dict(_room33.get('exits', {}))
            _exits33[_route33['direction']] = _route33['destination']
            _room33['exits'] = _exits33
            self._remember(ROOMS, _origin33, _room33)
        # OLC34: two-way portals, reversible by the existing registry undo log.
        from systems.live_olc34_integration import two_way_portals
        for _origin34, _direction34, _dest34 in two_way_portals():
            _room34 = dict(ROOMS[_origin34])
            _exits34 = dict(_room34.get('exits', {}))
            _exits34[_direction34] = _dest34
            _room34['exits'] = _exits34
            self._remember(ROOMS, _origin34, _room34)
        # Publish real new summon kinds into the existing summoning runtime.
        # _remember restores entries without deleting original minions on rollback.
        from player.session_mixins.era_sky_v1700 import SUMMONS, SUMMON_MANA
        for summon_id, row in data['v29_rules']['summons'].items():
            self._remember(SUMMONS, summon_id,
                (row['name'],row['class'],dict(row['materials']),row['kind'],
                 row['power']/100.0 * row.get('attack_percent',100)/100.0))
            self._remember(SUMMON_MANA, summon_id, row['mana'])
        # OLC29 authored work recipes and skill variants run in the actual
        # crafting/skill registries; no detached catalogue of unusable labels.
        from data.crafting_recipes import CRAFT_RECIPES as _RECIPES29
        for recipe_id, row in data['v29_rules']['professions'].items():
            definition=dict(_RECIPES29[recipe_id],name=row['label'])
            self._remember(_RECIPES29,recipe_id,definition)
        from core.classes_skills import CLASS_SKILLS as _CLASS29
        import sys as _sys29
        cache_module29=_sys29.modules.get('player.session_mixins.skill_queue_buffs')
        cache29=getattr(cache_module29,'_SKILLS_BY_ID_V3005',None)
        for skill_id, row in data['v29_rules']['skills'].items():
            for class_name, skill_list in _CLASS29.items():
                if any(skill['id']==skill_id for skill in skill_list):
                    updated=[dict(skill,name=row['name']) if skill['id']==skill_id else skill
                             for skill in skill_list]
                    self._remember(_CLASS29,class_name,updated)
                    if isinstance(cache29,dict):
                        found=next(skill for skill in updated if skill['id']==skill_id)
                        self._remember(cache29,skill_id,found)
                    break
        from data.quests import QUESTS as _QUESTS29
        for quest_id, row in data['v29_rules']['story'].items():
            original=_QUESTS29[quest_id]
            description=str(original.get('description','')).strip()
            message=str(row['text'])
            self._remember(_QUESTS29,quest_id,dict(original,description=(description+' '+message).strip()))
        from systems.live_olc22_state import WORLD_OVERRIDES
        WORLD_OVERRIDES.clear()
        WORLD_OVERRIDES.update(data['world_overrides'])
        from systems.live_olc23_state import SUMMON_TACTICS
        SUMMON_TACTICS.clear()
        for cls, edits in data['summon_edits'].items():
            active = {field: edits[field] for field in ('guard_threshold_percent',
                 'execute_threshold_percent', 'tactic_interval') if field in edits}
            if active:
                SUMMON_TACTICS[cls] = active
        install_live_xp(data['profession_edits'], data['tool_edits'], data['resource_edits'])
        for room, mob in data['spawns']:
            if (room, mob) not in MOB_SPAWNS:
                MOB_SPAWNS.append((room, mob))
                self._spawned_runtime.add((room, mob))
                if world is not None:
                    world._register_runtime_spawn(room, mob)

    @staticmethod
    def _matches_spawn(room_id, template_id, pairs):
        # The World generator adds __terrain/__world/__elite suffixes when a mob
        # appears.  These are still the same spawn as the original live mob.
        return any(room == room_id and
                   (template_id == mob or str(template_id).startswith(mob + '__'))
                   for room, mob in pairs)

    def _remove(self, world):
        # Remove only this extension's own mob records.  Do not touch fights.
        added = set(self._spawned_runtime)
        if world is not None:
            for key, state in list(world.mobs.items()):
                if (self._matches_spawn(state.home_room_id or state.room_id, state.template_id, added)
                        and not state.engaged_by and not state.aoe_engaged_by):
                    del world.mobs[key]
        # The live World may register an additional terrain-scaled spawn ID.
        # Those IDs are *not* present in the original SQLite payload.
        for spawn in list(MOB_SPAWNS):
            if self._matches_spawn(spawn[0], spawn[1], added):
                MOB_SPAWNS.remove(spawn)
        self._spawned_runtime.clear()
        for registry, key, old in reversed(self._undo):
            if old is MISSING:
                registry.pop(key, None)
            else:
                registry[key] = old
        self._undo.clear()
        from systems.live_olc22_state import WORLD_OVERRIDES
        WORLD_OVERRIDES.clear()
        from systems.live_olc23_state import SUMMON_TACTICS
        SUMMON_TACTICS.clear()
        from systems.live_olc24_revolution import sync_active
        sync_active(blank()['v24_rules'])
        from systems.live_olc26_world import sync as sync_v26
        sync_v26(blank()['v26_rules'])
        from systems.live_olc27_master import sync as sync_v27
        sync_v27(blank()['v27_rules'])
        from systems.live_olc28_expansion import sync as sync_v28
        sync_v28(blank()['v28_rules'])
        from systems.live_olc29_creation import sync as sync_v29
        sync_v29(blank()['v29_rules'])
        from systems.live_olc32_finale import sync as sync_v32
        sync_v32(blank()['v32_rules'])
        from systems.live_olc33_mechanics import sync as sync_v33
        sync_v33(blank()['v33_rules'])
        from systems.live_olc34_integration import sync as sync_v34
        sync_v34(blank()['v34_rules'])
        from systems.live_olc35_finale import sync as sync_v35
        sync_v35(blank()['v35_rules'])
        from systems.uoss_tactics_v9800 import sync as sync_v98
        sync_v98(blank()['v98_rules'])
        from systems.uoss_regeneration_v9900 import sync as sync_v99
        sync_v99(blank()['v99_rules'])
        from systems.uoss_ai_v10000 import sync as sync_v100
        sync_v100(blank()['v100_rules'])
        from systems.live_mechanics_v10100 import sync as sync_v101
        sync_v101(blank()['v101_rules'])
        install_live_xp({}, {}, {})
        # Avoid reusing a stale stat-scaled derivative when admins replace a
        # live custom mob.  Keep any still-in-combat variant until it ends.
        live_ids = tuple(self.active['mobs'])
        used_templates = ({state.template_id for state in world.mobs.values()}
                          if world is not None else set())
        for mid in list(MOB_TEMPLATES):
            if (mid not in used_templates and any(mid.startswith(src + '__') for src in live_ids)):
                MOB_TEMPLATES.pop(mid, None)

    def stage_new_skill(self, skill_id, class_name, name, kind, unlock, mana,
                        mult, scale, description, effect=None, element=None, cooldown=0):
        staged = copy.deepcopy(self.draft)
        staged['skills'][skill_id] = {
            'class_name':class_name, 'name':name, 'desc':description,
            'kind':kind, 'unlock':_integer(unlock, 1, 800, 'Biegłość'),
            'mana':_integer(mana, 0, 1000000, 'Mana'),
            'cooldown':_integer(cooldown, 0, 3600, 'Cooldown'), 'scale':scale, 'mult':float(mult), 'aliases':[],
        }
        if kind in ('heal', 'group_heal', 'drain', 'execute', 'boost'):
            staged['skills'][skill_id]['effect'] = (1.5 if kind == 'execute' else 1.15 if kind == 'boost' else 0.10) if effect is None else float(effect)
        elif kind == 'guard':
            staged['skills'][skill_id]['effect'] = 100 if effect is None else _integer(effect, 1, 10**9, 'Siła ochrony')
        elif effect is not None:
            raise ValueError('Ten rodzaj skilla nie obsługuje parametru EFFECT.')
        if element is not None:
            staged['skills'][skill_id]['element'] = element
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_new_profession_and_tool_v2400(self, pid, profession, tool_id, tool_type,
                                           tool_name, station, price, description):
        """Add genuine catalogue tool and profession together, transactionally staged."""
        staged=copy.deepcopy(self.draft)
        staged['items'][tool_id]={
            'name':tool_name, 'desc':description, 'type':'tool',
            'price':_integer(price,1,10**10,'Cena narzędzia'),
            'currency':'silver', 'tool_type':tool_type,
        }
        staged['v24_rules']['professions'][pid]={
            'name':profession, 'tool_type':tool_type, 'tool_item_id':tool_id,
            'tool_name':tool_name, 'station':station,
        }
        result=self.validate(staged)
        self.draft=staged
        return result

    def stage_new_profession_recipe_v2400(self, recipe_id, name, profession_id,
                                          output, ingredients_json, level,
                                          quantity, description):
        """Real craft recipe for a staged new profession and its registered tool.

        Unlike stage_new_recipe, it doesn't need a legacy exemplar with
        the same profession/tool. It is validated with the entire OLC draft.
        """
        staged = copy.deepcopy(self.draft)
        profile = staged['v24_rules']['professions'].get(profession_id)
        if profile is None:
            raise ValueError('Nie ma nowej profesji OLC24 o podanym identyfikatorze.')
        if not ID.fullmatch(recipe_id) or recipe_id in CRAFT_RECIPES or recipe_id in staged['recipes']:
            raise ValueError('Receptura wymaga wolnego identyfikatora live_.')
        try:
            ingredients = json.loads(ingredients_json)
        except (ValueError, TypeError) as exc:
            raise ValueError('Materiały: wymagany słownik JSON.') from exc
        material = dict(ITEMS, **staged['items'])
        if output not in material or material[output].get('type') not in ('craft_material', 'armor', 'consumable'):
            raise ValueError('Nowa receptura profesji: produkt musi być materiałem, wyposażeniem lub miksturą.')
        if isinstance(ingredients, dict) and output in ingredients:
            raise ValueError('Nowa receptura profesji: produkt nie może być jednocześnie składnikiem.')
        staged['recipes'][recipe_id] = {
            'name': name, 'desc': description, 'stations': [profile['station']],
            'ingredients': ingredients, 'output': output,
            'quantity': _integer(quantity, 1, 1000, 'Ilość produktu'),
            'min_profession_level': _integer(level, 1, _live_level_bound_v5900('profesje'), 'Poziom profesji'),
            'profession': profile['name'], 'tool_type': profile['tool_type'],
            'tool_item_id': profile['tool_item_id'], 'tool_name': profile['tool_name'],
        }
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_new_item(self, iid, item_type, name, description, variant, power, price):
        item = {
            'name': name, 'desc': description, 'type': item_type,
            'price': _integer(price, 0, 10**10, 'Cena'), 'currency': 'silver'
        }
        if item_type == 'armor':
            item['slot'] = variant
            item['defense'] = _integer(power, 1, 10**12, 'Obrona')
        elif item_type == 'consumable':
            if variant not in ('heal','leczenie'):
                raise ValueError('Mikstura OLC obsługuje wyłącznie heal.')
            item['heal'] = _integer(power, 1, 10**12, 'Leczenie')
        elif item_type != 'craft_material' or variant not in ('-', 'brak'):
            raise ValueError('Rodzaj: armor, consumable lub craft_material.')
        staged = copy.deepcopy(self.draft)
        staged['items'][iid] = item
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_new_jewelry(self, iid, name, slot, stat, amount, level, price, description):
        """Create jewelry using the existing armor/equipment stat engine."""
        staged = copy.deepcopy(self.draft)
        staged['items'][iid] = {
            'name': name, 'desc': description, 'type': 'armor',
            'slot': slot, 'defense': 1, 'stats': {stat: _integer(amount, 1, 10**7, 'Bonus statystyki')},
            'required_level': _integer(level, 1, 800, 'Wymagany poziom'),
            'price': _integer(price, 0, 10**10, 'Cena'), 'currency': 'silver',
        }
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_new_equipment(self, iid, name, slot, defense, attack, stats_json, level, price, description):
        """Armor-based equipment only: all fields are already consumed by the old engine."""
        try:
            stats = json.loads(stats_json)
        except (TypeError, ValueError) as exc:
            raise ValueError('Statystyki wymagają JSON, np. {"strength":5,"constitution":3}.') from exc
        staged = copy.deepcopy(self.draft)
        staged['items'][iid] = {
            'name': name, 'desc': description, 'type': 'armor', 'slot': slot,
            'defense': _integer(defense, 1, 10**12, 'Obrona'),
            'attack': _integer(attack, 0, 10**12, 'Atak'), 'stats': stats,
            'required_level': _integer(level, 1, 800, 'Poziom'),
            'price': _integer(price, 0, 10**10, 'Cena'), 'currency': 'silver',
        }
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_magic_equipment(self, iid, name, slot, defense, attack, magic_attack,
                              magic_defense, weapon_power, stats_json, level, price, description):
        try: stats = json.loads(stats_json)
        except (TypeError, ValueError) as exc: raise ValueError('Statystyki: poprawny JSON.') from exc
        staged = copy.deepcopy(self.draft)
        staged['items'][iid] = {
            'name':name, 'desc':description, 'type':'armor', 'slot':slot,
            'defense':_integer(defense, 1, 10**12, 'Obrona'),
            'attack':_integer(attack, 0, 10**12, 'Atak'),
            'magic_attack':_integer(magic_attack, 0, 10**12, 'Atak magiczny'),
            'magic_defense':_integer(magic_defense, 0, 10**12, 'Obrona magiczna'),
            'weapon_power':_integer(weapon_power, 0, 10**12, 'Moc broni'),
            'stats':stats, 'required_level':_integer(level, 1, 800, 'Poziom'),
            'price':_integer(price, 0, 10**10, 'Cena'), 'currency':'silver'}
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_change_multi_objectives_v1800(self, quest_id, objectives_json):
        """Atomically change the goals + needed count; reject active quests on publish."""
        from systems.live_olc18_multi_objective import validate_objectives
        staged = copy.deepcopy(self.draft)
        quest = dict(QUESTS.get(quest_id) or staged['quests'].get(quest_id) or {})
        if quest.get('kind') != 'multi_objective':
            raise ValueError('Ta komenda dotyczy wyłącznie questów wielocelowych.')
        goals, needed = validate_objectives(
            objectives_json, set(MOB_TEMPLATES) | set(staged['mobs']),
            set(ITEMS) | set(staged['items']), set(NPCS) | set(staged['npcs'])
        )
        if quest_id in staged['quests']:
            staged['quests'][quest_id]['objectives'] = goals
            staged['quests'][quest_id]['needed'] = needed
        else:
            staged['quest_edits'].setdefault(quest_id, {}).update(
                {'objectives': goals, 'needed': needed}
            )
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_new_multi_objective_quest_v1800(self, qid, name, giver, objectives_json, silver, description):
        from systems.live_olc18_multi_objective import validate_objectives
        staged = copy.deepcopy(self.draft)
        objectives, total = validate_objectives(
            objectives_json, set(MOB_TEMPLATES) | set(staged['mobs']),
            set(ITEMS) | set(staged['items']), set(NPCS) | set(staged['npcs'])
        )
        first = next(iter(objectives.get('kill', {})), '*')
        staged['quests'][qid] = {
            'name': name, 'giver': giver, 'kind': 'multi_objective',
            'target': first, 'needed': total, 'objectives': objectives,
            'reward_silver': _integer(silver, 0, 10**12, 'Srebro'),
            'description': description,
        }
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_new_resource_set_quest(self, qid, name, giver, requirements_json, silver, description):
        """Multi-resource quest uses the EXISTING collect_resource_set runtime.

        Each resource maintains its own durable progress and is physically consumed
        on turn-in by the native quest engine. No separate quest progress format.
        """
        try:
            resources = json.loads(requirements_json)
        except (TypeError, ValueError) as exc:
            raise ValueError('Zestaw: JSON, np. {"iron_ore":3,"copper_ore":2}.') from exc
        if not isinstance(resources, dict) or not 2 <= len(resources) <= 8:
            raise ValueError('Zestaw: od 2 do 8 różnych surowców.')
        total = sum(_integer(qty, 1, 10000, 'Ilość surowca') for qty in resources.values())
        first = next(iter(resources))
        staged = copy.deepcopy(self.draft)
        staged['quests'][qid] = {'name':name,'giver':giver,'kind':'collect_resource_set',
            'target':first,'needed':_integer(total, 2, 10000, 'Łączna liczba'),
            'resource_targets':resources,'description':description,
            'reward_silver':_integer(silver, 0, 10**12, 'Srebro')}
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_quest_materials(self, quest_id, requirements_json):
        """Update the live multi-resource objective atomically, never reset quest progress."""
        from data.quests import QUESTS
        quest = QUESTS.get(quest_id) or self.draft['quests'].get(quest_id)
        if not quest or quest.get('kind') != 'collect_resource_set':
            raise ValueError('Zestaw surowców: podaj ID questa collect_resource_set.')
        try:
            resources = json.loads(requirements_json)
        except (TypeError, ValueError) as exc:
            raise ValueError('Wymagany JSON surowców, np. {"iron_ore":2,"copper_ore":3}.') from exc
        if not isinstance(resources, dict) or not 2 <= len(resources) <= 8:
            raise ValueError('Wymagane 2–8 surowców.')
        from data.items import ITEMS
        allowed = {'resource','material','craft_material','gem_raw','archaeology_find'}
        total = 0
        cleaned = {}
        for item_id, count in resources.items():
            item = ITEMS.get(item_id) or self.draft['items'].get(item_id)
            if not item or item.get('type') not in allowed or type(count) is not int:
                raise ValueError(f'Nieznany surowiec lub liczba niecałkowita: {item_id}.')
            cleaned[item_id] = _integer(count, 1, 10000, 'Ilość surowca')
            total += cleaned[item_id]
        resources = cleaned
        staged = copy.deepcopy(self.draft)
        change = {'target': next(iter(resources)), 'needed': _integer(total, 2, 10000, 'Łącznie'),
                  'resource_targets': resources}
        if quest_id in staged['quests']:
            staged['quests'][quest_id].update(change)
        else:
            staged['quest_edits'].setdefault(quest_id, {}).update(change)
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_progression_group(self, category, scale):
        """Stage a reversible, exact percent for all already registered professions/tools.

        Never changes defaults automatically, never creates a new profession, and
        always waits for explicit admin publication + NEWS.
        """
        group = {'profesje': ('profession_edits', PROFESSION_RANK_NAMES),
                 'narzedzia': ('tool_edits', TOOL_PROFESSION_MAP)}.get(category)
        if group is None:
            raise ValueError('Grupa: profesje albo narzedzia.')
        section, registry = group
        staged = copy.deepcopy(self.draft)
        if str(scale).strip().casefold() in ('auto', 'automatyczny'):
            staged[section].clear()
        else:
            number = _integer(scale, 0, 1000, 'Procent EXP')
            for key in registry:
                staged[section][key] = {'xp_scale': number}
        result = self.validate(staged)
        self.draft = staged
        return f'{len(registry)} ustawień; {result}'

    def stage_respawn_group(self, prefix, seconds):
        if not isinstance(prefix, str) or len(prefix) < 3:
            raise ValueError('Podaj prefiks ID o długości co najmniej 3.')
        ids = sorted(k for k in MOB_TEMPLATES if k.startswith(prefix))
        if not 1 <= len(ids) <= 400:
            raise ValueError(f'Znaleziono {len(ids)} mobów; wymagane 1–400.')
        value = _integer(seconds, 0, 365 * 86400, 'Czas odradzania')
        staged = copy.deepcopy(self.draft)
        for mid in ids:
            staged['mob_edits'].setdefault(mid, {})['respawn_seconds'] = value
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_balance_group(self, prefix, field, amount):
        """Explicit ID-prefix batch, staged atomically; NEVER auto-publishes."""
        if field not in FIELDS:
            raise ValueError('Grupowa edycja: max_hp, damage, class_xp_reward, soul_reward, stat_reward.')
        if not isinstance(prefix, str) or len(prefix) < 3:
            raise ValueError('Grupowy balans: prefiks ID musi mieć minimum 3 znaki.')
        ids = sorted(k for k in MOB_TEMPLATES if k.startswith(prefix))
        if not 1 <= len(ids) <= 100:
            raise ValueError(f'Grupowy balans: znaleziono {len(ids)} mobów; wymagane 1–100.')
        number = _integer(amount, 1, 10**15, field)
        staged = copy.deepcopy(self.draft)
        for key in ids:
            staged['balances'].setdefault(key, {})[field] = number
        result = self.validate(staged)
        self.draft = staged
        return f'{len(ids)} potworów; {result}'

    def stage_new_quest(self, qid, name, giver, kind, target, needed, silver, description):
        staged = copy.deepcopy(self.draft)
        staged['quests'][qid] = {
            'name':name, 'giver':giver, 'kind':kind, 'target':target,
            'needed':_integer(needed, 1, 10000, 'Cel'),
            'description':description,
            'reward_silver':_integer(silver, 0, 10**12, 'Srebro'),
        }
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_quest_chain(self, qid, required_id):
        """Set the prerequisite through the same guarded OLC edit machinery."""
        return self.stage_edit('quest', qid, 'requires_quest', required_id)

    def stage_copy_recipe(self, new_id, source_id, new_name):
        """Clone a safe EXISTING recipe with its original tools and profession.

        Source-specific scripted fields are deliberately excluded. The new recipe
        is then editable using the existing whitelist and can be rolled back.
        """
        base = dict(CRAFT_RECIPES.get(source_id) or self.draft['recipes'].get(source_id) or {})
        if not base:
            raise ValueError('Nieznana receptura źródłowa.')
        if not ID.fullmatch(new_id) or new_id in CRAFT_RECIPES or new_id in self.draft['recipes']:
            raise ValueError('Nowa receptura wymaga wolnego ID live_.')
        safe_keys = ('desc','stations','ingredients','output','quantity',
                     'profession','tool_type','tool_item_id','tool_name')
        if any(key not in base for key in safe_keys):
            raise ValueError('Ta receptura ma specyficzną mechanikę i nie może być bezpiecznie skopiowana.')
        copied = {'name':new_name}
        for field in safe_keys:
            copied[field] = list(base[field]) if field == 'stations' else copy.deepcopy(base[field])
        copied['min_profession_level'] = int(base.get('min_profession_level') or 1)
        staged = copy.deepcopy(self.draft)
        staged['recipes'][new_id] = copied
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_new_recipe(self, recipe_id, name, profession, tool_id, output,
                         ingredients_json, station, level, quantity, description):
        """New recipe with proven engine tool contract; no arbitrary effects."""
        if not ID.fullmatch(recipe_id) or recipe_id in CRAFT_RECIPES or recipe_id in self.draft['recipes']:
            raise ValueError('Receptura wymaga wolnego identyfikatora live_.')
        try:
            ingredients = json.loads(ingredients_json)
        except (ValueError, TypeError) as exc:
            raise ValueError('Materiały: wymagany słownik JSON.') from exc
        # Model names/types from an existing supported recipe, not guessed from
        # an arbitrary user-controlled tool_type field.
        candidates = list(CRAFT_RECIPES.values()) + list(self.draft['recipes'].values())
        source = next((r for r in candidates if r.get('profession') == profession
                       and r.get('tool_item_id') == tool_id
                       and r.get('tool_type') and r.get('tool_name')), None)
        if source is None:
            raise ValueError('Nie istnieje receptura z tą profesją i narzędziem. Użyj recepturyprof.')
        obj = {'name':name, 'desc':description, 'stations':[station],
               'ingredients':ingredients, 'output':output,
               'quantity':_integer(quantity,1,1000,'Ilość produktu'),
               'min_profession_level':_integer(level,1,_live_level_bound_v5900('profesje'),'Poziom profesji'),
               'profession':profession, 'tool_type':source['tool_type'],
               'tool_item_id':tool_id, 'tool_name':source['tool_name']}
        staged = copy.deepcopy(self.draft)
        staged['recipes'][recipe_id] = obj
        result = self.validate(staged)
        self.draft = staged
        return result

    def stage_room(self, rid, level, name, desc, zone):
        self.draft['rooms'][rid] = {'name': name, 'desc': desc, 'zone': zone, 'generator_level': level}
        return self.validate(self.draft)

    def stage_link(self, origin, direction, destination):
        self.draft['links'] = [x for x in self.draft['links'] if x[:2] != [origin, direction]]
        self.draft['links'].append([origin, direction, destination])
        return self.validate(self.draft)

    def stage_mob(self, mid, name, level, hp, damage, exp):
        self.draft['mobs'][mid] = {'name': name, 'generator_level': level, 'max_hp': hp, 'damage': damage, 'class_xp_reward': exp}
        return self.validate(self.draft)

    def stage_spawn(self, rid, mid):
        if [rid, mid] not in self.draft['spawns']:
            self.draft['spawns'].append([rid, mid])
        return self.validate(self.draft)

    def stage_balance(self, mid, field, amount):
        self.draft['balances'].setdefault(mid, {})[field] = amount
        return self.validate(self.draft)

    def stage_edit(self, section, key, field, value):
        """Edit whitelisted catalog field. Complex JSON values are JSON literals."""
        mapping = {
            'pokoj': 'room_edits', 'room': 'room_edits',
            'mob': 'mob_edits', 'potwor': 'mob_edits',
            'przedmiot': 'item_edits', 'item': 'item_edits',
            'npc': 'npc_edits', 'quest': 'quest_edits', 'zadanie': 'quest_edits',
            'receptura': 'recipe_edits', 'recipe': 'recipe_edits',
            'profesja': 'profession_edits', 'profession': 'profession_edits',
            'narzedzie': 'tool_edits', 'tool': 'tool_edits',
            'skill': 'skill_edits', 'umiejetnosc': 'skill_edits',
            'surowiec': 'resource_edits', 'resource': 'resource_edits',
            'sklep': 'shop_edits', 'shop': 'shop_edits',
        }
        from systems.live_olc35_finale import stage as stage_v35
        if stage_v35(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc34_integration import stage as stage_v34
        if stage_v34(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc33_mechanics import stage as stage_v33
        if stage_v33(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc32_finale import stage as stage_v32
        if stage_v32(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc29_creation import stage as stage_v29
        if stage_v29(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc28_expansion import stage as stage_v28
        if stage_v28(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc27_master import stage as stage_v27
        if stage_v27(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc26_world import stage as stage_v26
        if stage_v26(self, section, key, field, value):
            return self.validate(self.draft)
        from systems.live_olc22_empire import stage_extra
        if stage_extra(self, section, key, field, value):
            return self.validate(self.draft)
        name = mapping.get(section)
        if not name:
            raise ValueError('Edycja: pokoj/mob/przedmiot/npc/quest/receptura.')
        if name == 'skill_edits' and key in self.draft['skills']:
            draft = copy.deepcopy(self.draft)
            editable = {'name', 'desc', 'unlock', 'mana', 'mult', 'scale', 'effect', 'element', 'cooldown', 'olc_status', 'olc_statuses'}
            if field not in editable:
                raise ValueError('Nowy skill: nazwa, opis, biegłość, mana, mult, scale lub effect.')
            if field in ('olc_status','olc_statuses'):
                from systems.live_olc19_status_skills import parse_status, parse_statuses
                if draft['skills'][key].get('kind') not in ('damage','aoe_damage'):
                    raise ValueError('Statusy wymagaja skilla obrazeniowego.')
                if field == 'olc_statuses' and draft['skills'][key].get('olc_status') is not None:
                    raise ValueError('Usun najpierw stary olc_status.')
                if field == 'olc_status' and draft['skills'][key].get('olc_statuses') is not None:
                    raise ValueError('Usun najpierw liste olc_statuses.')
                parsed = parse_statuses(value) if field == 'olc_statuses' else parse_status(value)
            elif field in ('unlock', 'mana', 'cooldown'):
                parsed = _integer(value, 1 if field == 'unlock' else 0,
                                  800 if field == 'unlock' else 3600 if field == 'cooldown' else 1000000, field)
            elif field in ('mult', 'effect'):
                try: parsed = float(value) if field == 'mult' or draft['skills'][key]['kind'] != 'guard' else int(value)
                except (TypeError, ValueError, OverflowError) as exc: raise ValueError('Nieprawidłowy mnożnik.') from exc
            else:
                parsed = value
            if field in ('olc_status', 'olc_statuses') and parsed is None:
                draft['skills'][key].pop(field, None)
            elif field == 'element' and str(value).casefold().strip() in ('auto', 'automatyczny'):
                draft['skills'][key].pop('element', None)
            else:
                draft['skills'][key][field] = parsed
            result = self.validate(draft)
            self.draft = draft
            return result
        if name in ('profession_edits', 'tool_edits', 'skill_edits', 'resource_edits'):
            if '|' in value:
                raise ValueError('Wartość nie może zawierać |.')
            if name == 'resource_edits':
                # v12.00.10: legacy prof_xp/tool_xp are still MINIMUM rewards;
                # new *_fixed and *_scale make reductions explicit and safe.
                if field in ('prof_mode','tool_mode'):
                    parsed = str(value).casefold().strip()
                    if parsed not in ('auto','manual','percent'):
                        raise ValueError('Tryb EXP: auto, manual albo percent.')
                elif field in ('prof_fixed','tool_fixed','prof_scale','tool_scale'):
                    parsed = _integer(value, 0, 1000 if field.endswith('scale') else 10**12, field)
                else:
                    parsed = _integer(value, 100 if field.endswith('percent') else 1,
                                      1000 if field.endswith('percent') else 10**12, field)
            elif name == 'skill_edits':
                # Validated data-only edits of existing 5461 authored skills.
                from systems.live_olc6_skill_editor import stage_existing_skill
                staged = copy.deepcopy(self.draft)
                stage_existing_skill(staged, key, field, value)
                result = self.validate(staged)
                self.draft = staged
                return result
            else:
                if str(value).strip().casefold() in ('auto','automatyczny'):
                    parsed = None
                else:
                    parsed = _integer(value, 0 if field == 'xp_scale' else 100,
                                      1000, 'Procent EXP')
            staged = copy.deepcopy(self.draft)
            if name == 'resource_edits':
                side = field.split('_', 1)[0]
                if field in ('prof_mode','tool_mode') and parsed == 'auto':
                    for suffix in ('mode','fixed','scale','xp','percent'):
                        staged[name].get(key, {}).pop(side + '_' + suffix, None)
                    if not staged[name].get(key):
                        staged[name].pop(key, None)
                else:
                    entry = staged[name].setdefault(key, {})
                    entry[field] = parsed
                    if field.endswith('_fixed'):
                        entry[side + '_mode'] = 'manual'
                    elif field.endswith('_scale'):
                        entry[side + '_mode'] = 'percent'
            elif parsed is None:
                staged[name].pop(key, None)
            else:
                entry = staged[name].setdefault(key, {})
                if field == 'xp_scale':
                    entry.pop('xp_percent', None)
                if field == 'xp_percent':
                    entry.pop('xp_scale', None)
                entry[field] = parsed
            result = self.validate(staged)
            self.draft = staged
            return result
        registry = {'room_edits': ROOMS, 'mob_edits': MOB_TEMPLATES,
                    'item_edits': ITEMS, 'npc_edits': NPCS,
                    'quest_edits': QUESTS, 'recipe_edits': CRAFT_RECIPES,
                    'shop_edits': SHOPS}[name]
        if key not in registry and key not in self.draft.get({
                'room_edits':'rooms', 'mob_edits':'mobs', 'item_edits':'items',
                'npc_edits':'npcs', 'quest_edits':'quests', 'recipe_edits':'recipes',
                'shop_edits':'shops'}[name], {}):
            raise ValueError('Nieznany identyfikator katalogu.')
        if name == 'quest_edits':
            draft = copy.deepcopy(self.draft)
            canonical = QUEST_XP_ALIASES.get(field, field)
            if (isinstance(value, str) and value.strip().casefold() in ('auto','automatyczny')
                    and canonical in QUEST_EDIT_FIELDS):
                # Do not persist "auto"; deleting an OLC override restores the
                # real native award after the atomic publish/rollback.
                current = draft[name].get(key)
                if current:
                    current.pop(canonical, None)
                    if not current:
                        draft[name].pop(key, None)
            else:
                field, parsed = parse_quest_edit(field, value)
                draft[name].setdefault(key, {})[field] = parsed
            result = self.validate(draft)
            self.draft = draft
            return result
        if field in ('olc_boss_phases', 'olc_boss_tactic_element', 'olc_boss_tactic_interval',
                      'olc_boss_support_interval', 'olc_boss_support_duration',
                      'olc_boss_rally_interval', 'olc_boss_rally_duration', 'olc_boss_guard_threshold',
                      'olc_boss_element_cycle', 'olc_boss_support_priority',
                      'olc_boss_guardian_interval', 'olc_boss_guardian_roles', 'olc_boss_guardian_rewards',
                      'olc_boss_guardian_hp_threshold', 'olc_boss_guardian_phase_roles',
                      'olc_boss_phase_element_cycles', 'olc_boss_rally_hp_threshold',
                      *PHASE_STRATEGY_FIELDS, 'olc_ancient_phases') and str(value).strip().casefold() in ('auto', 'automatyczny'):
            draft = copy.deepcopy(self.draft)
            entry = draft[name].get(key)
            if entry:
                entry.pop(field, None)
                if not entry:
                    draft[name].pop(key, None)
            result = self.validate(draft)
            self.draft = draft
            return result
        if name == 'quest_edits' and field == 'requires_quests' and str(value).strip().casefold() in ('auto', 'automatyczny'):
            draft = copy.deepcopy(self.draft)
            existing = draft[name].get(key, {})
            existing.pop(field, None)
            if not existing:
                draft[name].pop(key, None)
            result = self.validate(draft)
            self.draft = draft
            return result
        if field in ('drops', 'ingredients', 'stations', 'inventory', 'requires_quests', 'objectives', 'olc_boss_phases', 'stats', 'olc_dialogue_after_quest', 'olc_dialogue_after_quests', 'olc_boss_element_cycle', 'olc_boss_guardian_roles', 'olc_boss_guardian_rewards',
                     'olc_boss_guardian_phase_roles', 'olc_boss_phase_element_cycles',
                     *PHASE_STRATEGY_FIELDS, 'olc_ancient_phases'):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError('Słownik lub lista wymaga poprawnego JSON.') from exc
        elif field in ('auto_aggro', 'shopkeeper', 'boss'):
            if value.lower() not in ('true', 'false'):
                raise ValueError('Pole logiczne wymaga true lub false.')
            parsed = value.lower() == 'true'
        elif field in ('name', 'desc', 'zone', 'dialogue', 'description',
                       'room', 'quest', 'output', 'damage_type', 'currency', 'olc_boss_tactic_element', 'olc_boss_support_priority'):
            parsed = value
        else:
            parsed = _integer(value, 0, 10**15, field)
        draft = copy.deepcopy(self.draft)
        draft[name].setdefault(key, {})[field] = parsed
        result = self.validate(draft)
        self.draft = draft
        return result

    def stage_clear_resource(self, item_id):
        if item_id not in self.draft['resource_edits']:
            raise ValueError('Surowiec nie ma ustawień OLC do usunięcia.')
        staged = copy.deepcopy(self.draft)
        del staged['resource_edits'][item_id]
        result = self.validate(staged)
        self.draft = staged
        return result

    def export(self, path, *, draft=True):
        """Export inert versionable UTF-8 JSON, atomically, to trusted directory."""
        from pathlib import Path
        import os
        target = Path(path)
        content = self.draft if draft else self.active
        self.validate(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + '.tmp')
        temp.write_text(json.dumps(content, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
        os.replace(temp, target)
        return target

    def stage_file(self, path):
        """Import inert JSON from one trusted local file, never execute source."""
        from pathlib import Path
        source = Path(path)
        if not source.is_file():
            raise ValueError(f'Nie ma pliku: {source}.')
        if source.stat().st_size > 1024 * 1024:
            raise ValueError('Pakiet świata jest za duży (limit 1 MB).')
        try:
            incoming = json.loads(source.read_text('utf-8'))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('Plik musi być poprawnym JSON w UTF-8.') from exc
        if not isinstance(incoming, dict) or not set(incoming) <= set(blank()):
            raise ValueError('Nieznana sekcja pakietu OLC.')
        draft = copy.deepcopy(self.draft)
        for section in tuple(blank()):
            if section in ('links', 'spawns'):
                continue
            incoming_section = incoming.get(section, {})
            if not isinstance(incoming_section, dict):
                raise ValueError(f'Sekcja {section} musi być słownikiem JSON.')
            for key, value in incoming_section.items():
                if section in ('balances', 'room_edits', 'mob_edits', 'item_edits', 'npc_edits', 'quest_edits', 'recipe_edits', 'profession_edits', 'tool_edits', 'skill_edits', 'resource_edits', 'shop_edits', 'summon_edits') and key in draft[section] and isinstance(value, dict):
                    draft[section][key].update(value)
                else:
                    draft[section][key] = value
        for section in ('links', 'spawns'):
            incoming_section = incoming.get(section, [])
            if not isinstance(incoming_section, list):
                raise ValueError(f'Sekcja {section} musi być listą JSON.')
            for entry in incoming_section:
                if section == 'links' and isinstance(entry, list) and len(entry) == 3:
                    draft['links'] = [old for old in draft['links'] if old[:2] != entry[:2]]
                if entry not in draft[section]:
                    draft[section].append(entry)
        result = self.validate(draft)
        self.draft = draft
        return result

    def reset_draft(self):
        self.draft = copy.deepcopy(self.active)

    def describe_news(self, previous, *, rollback=False):
        """Safe public 1-line NEWS, only after a successful revision commit."""
        return news_summary(previous, self.active, rollback=rollback, revision=self.revision)

    def apply(self, server, login, rollback=False, *, dry_run=False, candidate=None):
        # Reject stale in-memory OLC before touching a single live registry. An
        # external process or second server must never silently overwrite its
        # published revision. This check also applies to read-only preflight.
        from systems.admin_live_v9000 import _db_current
        stored_row = _db_current(self)
        if candidate is not None and (not dry_run or rollback):
            raise ValueError('Migawka do sprawdzenia jest dozwolona tylko w trybie dry_run.')
        payload = copy.deepcopy(self.draft if candidate is None else candidate)
        if rollback:
            row = self.conn.execute('SELECT payload FROM live_content_history_v1204 WHERE revision=?', (self.revision,)).fetchone()
            if not row:
                raise ValueError('Brak poprzedniej wersji do cofnięcia.')
            payload = self._compat(json.loads(row['payload']))
        result = self.validate(payload)
        # Published persistent quest/item IDs must not vanish after a rollback.
        for section in ('items', 'quests', 'skills'):
            removed = set(self.active[section]) - set(payload[section])
            if removed:
                raise ValueError(f'Nie wycofuję opublikowanych {section}: {sorted(removed)}. Dane graczy mogą ich używać.')
        lost_professions = set(self.active['v24_rules']['professions']) - set(payload['v24_rules']['professions'])
        if lost_professions:
            raise ValueError('Opublikowane nowe profesje nie mogą być usunięte: postacie mogą mieć ich poziomy.')
        if payload == self.active:
            return 'Nie ma nowych zmian.'
        # A removed room occupied by a connected player must not disappear.
        removed_rooms = set(self.active['rooms']) - set(payload['rooms'])
        removed_spawns = {tuple(x) for x in self.active['spawns']} - {tuple(x) for x in payload['spawns']}
        for s in server.sessions:
            if s.character and s.character.room_id in removed_rooms:
                raise ValueError('Gracz jest w usuwanej lokacji. Poproś go o wyjście przed cofnięciem.')
        for state in server.world.mobs.values():
            if self._matches_spawn(state.home_room_id or state.room_id, state.template_id, removed_spawns) and (state.engaged_by or state.aoe_engaged_by):
                raise ValueError('Nie można wycofać przeciwnika podczas walki.')
        for quest_id in set(self.active['quest_edits']) | set(payload['quest_edits']):
            before = self.active['quest_edits'].get(quest_id, {})
            after = payload['quest_edits'].get(quest_id, {})
            if any(before.get(f) != after.get(f) for f in ('kind', 'target', 'resource_targets', 'objectives')) or (
                    (self.active.get('quests', {}).get(quest_id, {}) or {}).get('kind') == 'multi_objective'
                    and before.get('needed') != after.get('needed')):
                # Never reassign already accepted objective progress to a new target.
                started = self.conn.execute(
                    "SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'", (quest_id,)
                ).fetchone()[0]
                if started:
                    raise ValueError(f'Quest {quest_id} jest aktywny u {started} graczy; '
                                     'nie zmieniam rodzaju/celu. Nagrody i licznik needed można zmienić.')
        # v91: changing already accepted quest prerequisites mid-progress may
        # retroactively unlock/lock a quest. Protect *all* OLC publication
        # routes, including revision restores and old single-field editors.
        for quest_id in set(self.active['quest_edits']) | set(payload['quest_edits']):
            previous=self.active['quest_edits'].get(quest_id,{})
            proposed=payload['quest_edits'].get(quest_id,{})
            if any(previous.get(k)!=proposed.get(k) for k in ('requires_quest','requires_quests')):
                started=self.conn.execute(
                    "SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'",(quest_id,)
                ).fetchone()[0]
                if started:
                    raise ValueError(f'Quest {quest_id} jest aktywny u {started} graczy; '
                                     'nie zmieniam wymaganych poprzednikow w trakcie zadania.')
        for quest_id in set(self.active['quests']) & set(payload['quests']):
            previous=self.active['quests'][quest_id]
            proposed=payload['quests'][quest_id]
            if any(previous.get(k)!=proposed.get(k) for k in ('requires_quest','requires_quests')):
                started=self.conn.execute(
                    "SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'",(quest_id,)
                ).fetchone()[0]
                if started:
                    raise ValueError(f'Quest {quest_id} jest aktywny u {started} graczy; '
                                     'nie zmieniam wymaganych poprzednikow w trakcie zadania.')
        # v92: never redirect an accepted quest to a different giver in any
        # publication route, including revisions and old single-field editors.
        for section in ('quest_edits','quests'):
            old_entries=self.active[section]
            new_entries=payload[section]
            for quest_id in set(old_entries)|set(new_entries):
                old=(old_entries.get(quest_id) or {}).get('giver')
                new=(new_entries.get(quest_id) or {}).get('giver')
                if old==new:continue
                started=self.conn.execute(
                    "SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'",(quest_id,)
                ).fetchone()[0]
                if started:
                    raise ValueError(f'Quest {quest_id} jest aktywny u {started} graczy; '
                                     'nie zmieniam zleceniodawcy w trakcie zadania.')
        # v29: do not orphan durable summoned companions by deleting their
        # catalog entry after players have acquired that creature.
        removed_summons = (set(self.active['v29_rules']['summons']) -
                           set(payload['v29_rules']['summons']))
        if removed_summons:
            has_summon_table = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='summons_v1700'"
            ).fetchone()
            if has_summon_table:
                for summon_id in removed_summons:
                    owner = self.conn.execute(
                        'SELECT 1 FROM summons_v1700 WHERE summon_type=? LIMIT 1',
                        (summon_id,)).fetchone()
                    if owner:
                        raise ValueError('Nie można usunąć przywołania '+summon_id+
                                         ': gracz ma już zapisane takie stworzenie.')
        # Published live quests can themselves be edited in the `quests`
        # section. Protect their accepted objectives as well as quest_edits.
        for quest_id in set(self.active['quests']) & set(payload['quests']):
            before = self.active['quests'][quest_id]
            after = payload['quests'][quest_id]
            if any(before.get(f) != after.get(f) for f in ('kind', 'target', 'resource_targets', 'objectives')) or (
                    (self.active.get('quests', {}).get(quest_id, {}) or {}).get('kind') == 'multi_objective'
                    and before.get('needed') != after.get('needed')):
                started = self.conn.execute(
                    "SELECT COUNT(*) FROM quests WHERE quest_id=? AND status='active'", (quest_id,)
                ).fetchone()[0]
                if started:
                    raise ValueError(f'Quest {quest_id} jest aktywny u {started} graczy; '
                                     'nie zmieniam jego celów w trakcie wykonywania.')
        changed_mobs = {mid for mid in set(self.active['mobs']) | set(payload['mobs'])
                        if self.active['mobs'].get(mid) != payload['mobs'].get(mid)}
        changed_mobs.update(mid for mid in set(self.active['mob_edits']) | set(payload['mob_edits'])
                            if self.active['mob_edits'].get(mid) != payload['mob_edits'].get(mid))
        changed_mobs.update(mid for mid in set(self.active['balances']) | set(payload['balances'])
                            if self.active['balances'].get(mid) != payload['balances'].get(mid))
        if (payload['v101_rules'] != self.active['v101_rules'] or
            payload['v100_rules'] != self.active['v100_rules'] or
            payload['v99_rules'] != self.active['v99_rules'] or
            payload['v98_rules'] != self.active['v98_rules'] or
            payload['v32_rules']['uoss'] != self.active['v32_rules']['uoss'] or
            payload['v33_rules']['uoss'] != self.active['v33_rules']['uoss'] or
            payload['v34_rules']['uoss'] != self.active['v34_rules']['uoss'] or
            payload['v32_rules']['summons'] != self.active['v32_rules']['summons'] or
            payload['v32_rules']['skills'] != self.active['v32_rules']['skills'] or
            payload['v29_rules']['bosses'] != self.active['v29_rules']['bosses'] or
            payload['v29_rules']['summons'] != self.active['v29_rules']['summons'] or
            payload['v26_rules']['uoss'] != self.active['v26_rules']['uoss'] or
            payload['v26_rules']['summons'] != self.active['v26_rules']['summons'] or
            payload['v24_rules']['uoss'] != self.active['v24_rules']['uoss'] or
            payload['v24_rules']['summons'] != self.active['v24_rules']['summons'] or
            any(payload['v24_rules']['world'].get('global',{}).get(k) !=
                self.active['v24_rules']['world'].get('global',{}).get(k)
                for k in ('event_hp_percent','event_damage_percent'))):
            if any((m.engaged_by or m.aoe_engaged_by) for m in server.world.mobs.values()):
                raise ValueError('OLC24: bossów i przywołań nie zmieniaj w trakcie walki.')
        event_fields = ('event_cycle_minutes', 'event_order', 'event_offset_minutes')
        event_changed = any(self.active['world_overrides'].get(k) != payload['world_overrides'].get(k)
                            for k in event_fields)
        event_changed |= payload['v24_rules']['events'] != self.active['v24_rules']['events']
        event_changed |= payload['v26_rules']['events'] != self.active['v26_rules']['events']
        event_changed |= payload['v29_rules']['events'] != self.active['v29_rules']['events']
        event_changed |= payload['v32_rules']['events'] != self.active['v32_rules']['events']
        if event_changed and any((m.engaged_by or m.aoe_engaged_by)
                                 for m in server.world.mobs.values()):
            raise ValueError('Czas i kolejność eventów zmieniaj między walkami, aby nie przerwać starcia.')
        if (payload['skill_edits'] != self.active['skill_edits'] or
                payload['skills'] != self.active['skills'] or
                payload['summon_edits'] != self.active['summon_edits']):
            if any((state.engaged_by or state.aoe_engaged_by)
                   for state in server.world.mobs.values()):
                raise ValueError('Edycję skilli aktywuj między walkami; gracze pozostają połączeni.')
        if changed_mobs:
            for state in server.world.mobs.values():
                if (state.engaged_by or state.aoe_engaged_by) and any(
                        state.template_id == mid or str(state.template_id).startswith(mid + '__')
                        for mid in changed_mobs):
                    raise ValueError('Nie zmieniam statystyk potwora live_ podczas trwającej walki.')
        # v89: exact read-only publication preflight. All validation and runtime
        # safety guards above are identical to the actual activation path.
        # Do not call _remove/_install or begin any SQLite writes in this mode.
        if dry_run:
            return (f'PRZEDPUBLIKACJA OK: rewizja {self.revision}, '
                    f'kontrole aktywnych questow, walk i referencji: OK. {result}. '
                    'BEZ ZAPISU. Stan moze sie zmienic; przy aktywacji '
                    'wszystkie warunki zostana sprawdzone ponownie.')
        old = copy.deepcopy(self.active)
        previous_revision = self.revision
        self._remove(server.world)
        try:
            self._install(payload, server.world)
            encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            # Never REPLACE historical revisions. A stale or duplicate write
            # must fail rather than destroying an audit snapshot.
            self.conn.execute('INSERT INTO live_content_history_v1204 (revision,payload,admin_login) VALUES(?,?,?)', (previous_revision + 1, json.dumps(old, ensure_ascii=False, sort_keys=True), login))
            if stored_row is None:
                self.conn.execute('INSERT INTO live_content_v1204 (id,revision,payload) VALUES(1,?,?)', (previous_revision + 1, encoded))
            else:
                update=self.conn.execute('UPDATE live_content_v1204 SET revision=?,payload=? WHERE id=1 AND revision=? AND payload=?',
                    (previous_revision + 1, encoded, previous_revision, stored_row['payload']))
                if update.rowcount!=1:
                    raise ValueError('Konflikt publikacji OLC: inny proces opublikowal nowsza rewizje. Zmiany odrzucone.')
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            self._remove(server.world)
            self._install(old, server.world)
            raise
        self.active = payload
        self.revision += 1
        self.reset_draft()
        if event_changed:
            # Old epoch-key city boss must not coexist with newly scheduled
            # invasion after a hot-published offset/duration/order change.
            # The preflight above has forbidden all combat in this case.
            for key, state in list(server.world.mobs.items()):
                if (str(key).startswith('v12812:event:') and
                        not (state.engaged_by or state.aoe_engaged_by)):
                    del server.world.mobs[key]
        if hasattr(server.world, '_last_refresh_at'):
            server.world._last_refresh_at = 0.0
        return f'Aktywowano rewizję {self.revision} bez restartu: {result}.'
