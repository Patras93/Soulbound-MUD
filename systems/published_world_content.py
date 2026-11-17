"""Read-only restoration of previously published world data. Editing is not supported."""


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

from systems.published_21_phase_strategy import PHASE_STRATEGY_FIELDS

from systems.published_quest_fields_v1209 import (QUEST_XP_ALIASES, QUEST_AUTO_FIELDS, QUEST_EDIT_FIELDS, parse_quest_edit, validate_quest_edit, news_summary)

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

class PublishedWorldContent:
    def __init__(self, db):
        self.db = db
        self.conn = db.conn
        row_table = self.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='live_content_v1204'").fetchone()
        if row_table is None:
            row = None
        else:
            row = self.conn.execute("SELECT revision,payload FROM live_content_v1204 WHERE id=1").fetchone()
        self.revision = int(row['revision']) if row else 0
        self.active = self._compat(json.loads(row['payload'])) if row else blank()
        self._spawned_runtime = set()
        # Even read-only published revisions may contain registered edits.
        # _remember() must have a journal before installing them at startup.
        self._undo = []
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
        # v102.00.9: same effective IDs for every edit in this validation.
        # Never persist/cache across hot reloads: staged additions must be visible.
        effective_items = set(ITEMS) | set(data['items'])
        effective_mobs = set(MOB_TEMPLATES) | set(data['mobs'])
        effective_quests = set(QUESTS) | set(data['quests'])
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
                        validate_quest_edit(key, quest_base, patch, effective_items,
                                            effective_mobs, effective_quests, NPCS, data['npcs'])
                        break
                    if section == 'npc_edits' and field == 'name' and key in NPCS:
                        old_name = str(NPCS[key]['name']).casefold()
                        if str(value).casefold() != old_name and any(
                                str(q.get('giver', '')).casefold() == old_name
                                for q in list(QUESTS.values()) + list(data['quests'].values())):
                            raise ValueError('NPC prowadzi questy; nie zmieniam nazwy zleceniodawcy na żywo.')
                    # OLC 4.0 — reuse the same strict checks for JSON imports
                    # and in-game typed edits. No executable formulas or scripts.
                    from systems.published_4_fields import validate_extra
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
                        self._validate_drops(value, effective_items)
                    elif field == 'ingredients':
                        self._validate_ingredients(value, effective_items)
                    else:
                        _integer(value, 1 if field in ('max_hp','damage','generator_level','min_profession_level') else 0,
                                 800 if field in ('generator_level','min_profession_level') else 10**15, field)
        # One NPC per accessible room, also when moving two NPCs in one
        # revision. This includes NPCs added earlier by this OLC service.
        from systems.published_4_fields import validate_npc_locations
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
        from systems.published_22_empire import validate_summons, validate_world
        validate_summons(data['summon_edits'])
        validate_world(data['world_overrides'])
        from systems.published_24_revolution import validate as validate_v24
        from systems.v11000_olc_validation_views import combined_catalog
        validate_v24(data['v24_rules'], items=combined_catalog(ITEMS, data['items']),
                     rooms=combined_catalog(ROOMS, data['rooms']))
        from systems.published_26_world import validate as validate_v26
        validate_v26(data['v26_rules'], quests=data['quests'], professions=data['v24_rules']['professions'])
        from systems.published_27_master import validate as validate_v27
        validate_v27(data['v27_rules'], v26_events=data['v26_rules']['events'],
                     v24_professions=data['v24_rules']['professions'], live_shops=data['shops'])
        from systems.published_28_expansion import validate as validate_v28
        validate_v28(data['v28_rules'], professions=data['v24_rules']['professions'],
                     events=data['v26_rules']['events'])
        from systems.published_29_creation import validate as validate_v29
        validate_v29(data['v29_rules'], payload=data)
        from systems.published_32_finale import validate as validate_v32
        validate_v32(data['v32_rules'], payload=data)
        from systems.published_33_mechanics import validate as validate_v33
        validate_v33(data['v33_rules'], payload=data)
        from systems.published_34_integration import validate as validate_v34
        validate_v34(data['v34_rules'], payload=data)
        from systems.published_35_finale import validate as validate_v35
        validate_v35(data['v35_rules'], payload=data)
        from systems.uoss_tactics_v9800 import validate as validate_v98
        validate_v98(data['v98_rules'])
        from systems.uoss_regeneration_v9900 import validate as validate_v99
        validate_v99(data['v99_rules'])
        from systems.uoss_ai_v10000 import validate as validate_v100
        validate_v100(data['v100_rules'])
        from systems.live_mechanics_v10100 import validate as validate_v101
        validate_v101(data['v101_rules'])
        from systems.published_4_new_skills import validate_new_skills
        validate_new_skills(data['skills'], self.active['skills'])
        from systems.published_skill_validation import validate_existing_skill_edits
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
        # Build large catalogue views only when a staged definition needs them.
        # Each downstream consumer is guarded by its corresponding section.
        item_ids = (set(ITEMS) | set(data['items'])
                    if any(data[k] for k in ('shops', 'quests', 'recipes')) else set())
        quest_ids = (set(QUESTS) | set(data['quests'])
                     if data['quests'] or data['npcs'] else set())
        npc_names = ({n['name'].casefold() for key, n in NPCS.items()
                      if key not in self.active['npcs']}
                     if data['npcs'] or data['quests'] else set())
        occupied = ({n['room'] for key, n in NPCS.items()
                     if key not in self.active['npcs']} if data['npcs'] else set())
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
            from systems.published_17_quest_dependencies import validate_dependencies
            validate_dependencies(qid, quest, quest_ids)
            if 'requires_quest' in quest and (quest['requires_quest'] not in quest_ids or quest['requires_quest'] == qid):
                raise ValueError(f'Quest {qid}: nieznany lub własny poprzednik.')
            _text(quest['name'], 120, 'Quest'); _text(quest['description'], 1600, 'Opis questa')
            _text(quest['giver'], 100, 'Zleceniodawca')
            if quest['giver'].casefold() not in npc_names:
                raise ValueError(f'Quest {qid}: nie ma NPC o nazwie {quest["giver"]}.')
            if quest['kind'] == 'multi_objective':
                from systems.published_18_multi_objective import validate_objectives
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
        from systems.v11000_olc_validation_views import quest_dependency_view
        from systems.published_17_quest_dependencies import validate_dependency_graph
        validate_dependency_graph(quest_dependency_view(
            QUESTS, data['quests'], data['quest_edits']))
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
            if npc.get('quest') and npc['quest'] not in quest_ids:
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
        from systems.published_4_new_skills import new_skill_definition
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
        from systems.published_24_revolution import sync_active
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
        from systems.published_26_world import sync as sync_v26
        sync_v26(data['v26_rules'])
        # New timed event bosses use the original four city arenas and rewards.
        # Their templates are registered only on publish, and restored by _undo.
        from systems.published_26_world import event_catalog
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
        from systems.published_27_master import sync as sync_v27, event_rewards
        sync_v27(data['v27_rules'])
        for slug in data['v27_rules']['events']:
            template_id='v26_event_'+slug
            updated=dict(MOB_TEMPLATES[template_id],**event_rewards(slug))
            self._remember(MOB_TEMPLATES,template_id,updated)
        from systems.published_28_expansion import sync as sync_v28
        sync_v28(data['v28_rules'])
        from systems.published_29_creation import sync as sync_v29
        sync_v29(data['v29_rules'])
        from systems.published_32_finale import sync as sync_v32
        sync_v32(data['v32_rules'])
        from systems.published_33_mechanics import sync as sync_v33
        sync_v33(data['v33_rules'])
        from systems.published_34_integration import sync as sync_v34
        sync_v34(data['v34_rules'])
        from systems.published_35_finale import sync as sync_v35
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
        from systems.published_33_mechanics import world_portals
        for _origin33, _route33 in world_portals().items():
            _room33 = dict(ROOMS[_origin33])
            _exits33 = dict(_room33.get('exits', {}))
            _exits33[_route33['direction']] = _route33['destination']
            _room33['exits'] = _exits33
            self._remember(ROOMS, _origin33, _room33)
        # OLC34: two-way portals, reversible by the existing registry undo log.
        from systems.published_34_integration import two_way_portals
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
        from systems.published_22_state import WORLD_OVERRIDES
        WORLD_OVERRIDES.clear()
        WORLD_OVERRIDES.update(data['world_overrides'])
        from systems.published_23_state import SUMMON_TACTICS
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
