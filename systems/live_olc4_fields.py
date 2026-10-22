# -*- coding: utf-8 -*-
"""OLC 4.0: safe extensions of existing catalog fields.

Not a scripting language. Editing a catalog definition cannot introduce new
runtime behavior and never updates a player's stored character state.
"""
from data.items import ITEMS
from data.npcs import NPCS
from data.quests import QUESTS
from data.crafting_recipes import CRAFT_RECIPES
from data.rooms import ROOMS
from data.shops import SHOPS


def validate_extra(section, key, field, value, data, room_ids, mob_ids):
    # Return True only if the field was explicitly and fully checked.
    from systems.live_content_v1204 import _integer
    items = set(ITEMS) | set(data['items'])
    if section == 'shop_edits':
        if field != 'inventory' or not isinstance(value, list) or len(value) > 120:
            raise ValueError('Sklep: towary to lista JSON, maks. 120 pozycji.')
        if key not in room_ids or any(
                not isinstance(v, str) or v not in items for v in value) or len(value) != len(set(value)):
            raise ValueError('Sklep: nieznana lokacja, duplikat lub nieznany przedmiot.')
        return True
    if section == 'mob_edits':
        if field == 'olc_ancient_phases':
            from systems.live_olc22_empire import validate_ancient
            from data.mobs import MOB_TEMPLATES
            base = MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {}
            if 'v500_ancient_profile' not in base or 'uoss_unique_superboss_key' in base:
                raise ValueError('OLC22: tylko 12 pradawnych bossów v500, nie UOSS.')
            return validate_ancient(value)
        from systems.live_olc21_phase_strategy import PHASE_STRATEGY_FIELDS, validate_phase_strategy
        if field in PHASE_STRATEGY_FIELDS:
            from data.mobs import MOB_TEMPLATES
            from systems.live_olc4_boss_phases import eligible_boss
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base):
                raise ValueError('OLC18: zmiany strategii fazowej tylko dla zwykłych, nieskryptowanych bossów.')
            return validate_phase_strategy(field, value)
        if field == 'boss':
            if key not in data['mobs'] or not isinstance(value, bool):
                raise ValueError('Boss true/false: tylko dla nowego potwora live_.')
            return True
        if field == 'olc_boss_phases':
            from systems.live_olc4_boss_phases import validate_boss_phases
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            return validate_boss_phases(base, value)
        if field == 'olc_boss_tactic_interval':
            from systems.live_olc4_boss_phases import eligible_boss
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base):
                raise ValueError('Częstość taktyki tylko dla zwykłego bossa.')
            _integer(value, 2, 12, 'Interwał taktyki')
            return True
        if field == 'olc_boss_tactic_element':
            from systems.live_olc4_boss_phases import eligible_boss
            from systems.encounter_brain_v1230 import _ELEMENTS
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base) or value not in _ELEMENTS:
                raise ValueError('OLC: żywioł taktyki tylko dla zwykłych bossów; dozwolone: ' + ', '.join(_ELEMENTS))
            return True
        if field == 'olc_boss_element_cycle':
            from systems.live_olc4_boss_phases import eligible_boss
            from systems.encounter_brain_v1230 import _ELEMENTS
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if (not eligible_boss(base) or not isinstance(value, list) or
                    not 1 <= len(value) <= 12 or
                    any(type(e) is not str or e not in _ELEMENTS for e in value)):
                raise ValueError('Cykl żywiołów: zwykły boss, lista JSON 1–12 znanych żywiołów.')
            return True
        if field in ('olc_boss_guardian_phase_roles', 'olc_boss_phase_element_cycles',
                     'olc_boss_guardian_hp_threshold', 'olc_boss_rally_hp_threshold'):
            from data.mobs import MOB_TEMPLATES
            from systems.live_olc4_boss_phases import eligible_boss
            from systems.live_olc20_phase_tactics import validate_stage_map, ROLES, ELEMENTS
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base):
                raise ValueError('OLC17: tylko zwykli, nieskryptowani bossowie.')
            if field.endswith('_roles'):
                validate_stage_map(value, ROLES, 'Role faz pomocników')
            elif field.endswith('_cycles'):
                validate_stage_map(value, ELEMENTS, 'Żywioły faz bossa')
            else:
                _integer(value, 1 if field == 'olc_boss_guardian_hp_threshold' else 5,
                         100 if field == 'olc_boss_guardian_hp_threshold' else 95, field)
            return True
        if field == 'olc_boss_guardian_interval':
            from systems.live_olc4_boss_phases import eligible_boss
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base):
                raise ValueError('Fale pomocników OLC: tylko zwykły, nieskryptowany boss.')
            _integer(value, 2, 12, 'Odstęp między falami pomocników')
            return True
        if field == 'olc_boss_guardian_rewards':
            from systems.live_olc4_boss_phases import eligible_boss
            from systems.guardian_rewards_v1540 import validate_guardian_rewards_v1540
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base):
                raise ValueError('Nagrody pomocników: tylko zwykły, nieskryptowany boss.')
            validate_guardian_rewards_v1540(value)
            return True
        if field == 'olc_boss_guardian_roles':
            from systems.live_olc4_boss_phases import eligible_boss
            from systems.boss_companions_v1281 import GUARDIAN_ROLES_V12811
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            keys = {row[0] for row in GUARDIAN_ROLES_V12811}
            if (not eligible_boss(base) or not isinstance(value, list)
                    or not 1 <= len(value) <= 10
                    or any(type(role) is not str or role not in keys for role in value)):
                raise ValueError('Role pomocników: lista JSON 1–10; zbrojny, arkaniczny, obronca, furia, uzdrowiciel. Tylko zwykli bossowie.')
            return True
        if field == 'olc_boss_support_priority':
            from systems.live_olc4_boss_phases import eligible_boss
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base) or type(value) is not str or value not in ('weakest', 'strongest'):
                raise ValueError('Priorytet osłony: tylko zwykły boss; weakest albo strongest.')
            return True
        if field == 'olc_boss_guard_threshold':
            from systems.live_olc4_boss_phases import eligible_boss
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base):
                raise ValueError('Próg ochrony tylko dla zwykłych bossów.')
            _integer(value, 5, 95, 'Procent HP dla wsparcia')
            return True
        if field in ('olc_boss_support_interval', 'olc_boss_support_duration',
                     'olc_boss_rally_interval', 'olc_boss_rally_duration'):
            from systems.live_olc4_boss_phases import eligible_boss
            from data.mobs import MOB_TEMPLATES
            base = dict(MOB_TEMPLATES.get(key) or data['mobs'].get(key) or {})
            base.update(data['mob_edits'].get(key, {}))
            if not eligible_boss(base):
                raise ValueError('Taktyka wsparcia: tylko zwykli, nieskryptowani bossowie.')
            if field.endswith('_interval'):
                _integer(value, 2, 12, field)
            else:
                _integer(value, 1, 30, field)
            return True
        if field == 'damage_type':
            if value not in ('physical', 'magic'):
                raise ValueError('Typ obrażeń: physical lub magic.')
            return True
        if field == 'respawn_seconds':
            _integer(value, 0, 365 * 86400, field)
            return True
        if field in ('silver', 'gold', 'mithril'):
            _integer(value, 0, 10**12, field)
            return True
    if section == 'item_edits':
        item = ITEMS.get(key, data['items'].get(key, {}))
        if field == 'stats':
            allowed_stats = {'strength','dexterity','intelligence','wisdom','willpower','constitution'}
            limit = 6 if 'attack' in item else 1
            if (key not in data['items'] or 'stats' not in item or not isinstance(value, dict)
                    or not 1 <= len(value) <= limit or not set(value) <= allowed_stats):
                raise ValueError('Bonusy: tylko nowy sprzęt OLC, od 1 do 6 istniejących statystyk.')
            for amount in value.values():
                _integer(amount, 1, 10**7, 'Bonus')
            return True
        if field == 'currency':
            if 'currency' not in item or value not in ('silver', 'gold', 'mithril'):
                raise ValueError('Walutę można zmieniać tylko dla przedmiotów z istniejącym polem currency.')
            return True
        if field in ('heal', 'defense', 'attack', 'magic_attack', 'magic_defense', 'weapon_power', 'required_level', 'sell_silver', 'sell_gold'):
            # Prevent accidentally adding engine-specific semantics to items.
            if field not in item:
                raise ValueError('Przedmiot nie ma tego parametru w swojej definicji.')
            _integer(value, 0 if field != 'required_level' else 1,
                     800 if field == 'required_level' else 10**12, field)
            return True
    if section == 'npc_edits':
        if field == 'olc_dialogue_after_quests':
            from systems.live_olc17_quest_dependencies import validate_multi_dialogue
            validate_multi_dialogue(value, set(QUESTS) | set(data['quests']))
            return True
        if field == 'olc_dialogue_after_quest':
            from systems.live_content_v1204 import _text
            if not isinstance(value, dict) or set(value) != {'quest_id', 'text'}:
                raise ValueError('Dialog warunkowy: JSON {"quest_id":"ID","text":"Treść"}.')
            if value['quest_id'] not in set(QUESTS) | set(data['quests']):
                raise ValueError('Dialog warunkowy: nieznany quest.')
            _text(value['text'], 700, 'Tekst dialogu')
            return True
        if field == 'room':
            if not isinstance(value, str) or value not in room_ids:
                raise ValueError('NPC: podana lokacja nie istnieje.')
            return True
        if field == 'shopkeeper':
            if not isinstance(value, bool):
                raise ValueError('NPC: shopkeeper wymaga true/false.')
            return True
        if field == 'quest':
            npc = NPCS.get(key, data['npcs'].get(key, {}))
            quest = QUESTS.get(value, data['quests'].get(value)) if isinstance(value, str) else None
            if quest is None or str(quest.get('giver', '')).casefold() != str(npc.get('name', '')).casefold():
                raise ValueError('NPC: nieznany quest lub zadanie przypisano innemu zleceniodawcy.')
            return True
    if section == 'recipe_edits':
        recipe = CRAFT_RECIPES.get(key, data['recipes'].get(key, {}))
        if field in ('min_tool_level', 'tool_xp') and field not in recipe:
            raise ValueError('Receptura: ten parametr nie istnieje w definicji.')
        if field == 'min_tool_level':
            _integer(value, 1, 800, field)
            return True
        if field == 'tool_xp':
            _integer(value, 0, 10**12, field)
            return True
        if field == 'quantity':
            _integer(value, 1, 10000, field)
            return True
        if field == 'output':
            if not isinstance(value, str) or value not in items:
                raise ValueError('Receptura: produkt musi istnieć w katalogu przedmiotów.')
            return True
        if field == 'stations':
            if not isinstance(value, list) or not 1 <= len(value) <= 40 or any(
                    not isinstance(room, str) or room not in room_ids for room in value) or len(value) != len(set(value)):
                raise ValueError('Receptura: stacje to niepusta lista istniejących pokojów.')
            return True
    return False


def validate_npc_locations(data, room_ids):
    """Effective final state must have at most one registered NPC per room."""
    occupants = {}
    effective = dict(NPCS)
    effective.update(data['npcs'])
    for npc_id, patch in data['npc_edits'].items():
        effective[npc_id] = dict(effective[npc_id], **patch)
    for npc_id, npc in effective.items():
        room = npc.get('room')
        if room not in room_ids:
            # Do not convert pre-existing references in legacy world into fatal
            # errors; only validate explicitly relocated or newly added NPCs.
            if npc_id in data['npc_edits'] or npc_id in data['npcs']:
                raise ValueError(f'NPC {npc_id}: nieznana lokacja.')
            continue
        if room in occupants and occupants[room] != npc_id:
            # Existing legacy collisions are not created by this patch.
            # Changing a legacy NPC dialogue must not reject an *existing*
            # historic room collision. Only NEW NPCs or changed rooms may
            # introduce a new collision; the rule for room changes stays strict.
            if (npc_id in data['npcs'] or occupants[room] in data['npcs'] or
                    'room' in data['npc_edits'].get(npc_id, {}) or
                    'room' in data['npc_edits'].get(occupants[room], {})):
                raise ValueError(f'W lokacji {room} jest już NPC; każdy NPC wymaga własnego pokoju.')
        else:
            occupants[room] = npc_id
