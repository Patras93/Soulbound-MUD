# -*- coding: utf-8 -*-
"""v12.00.9: data-only OLC quest overrides and human-readable NEWS summaries.

All patches go through the existing validated, atomic live-content revision.
Player progress, quest identifiers and character XP formulas are not migrated.
An explicit OLC XP override affects future quest turn-ins only; unset
fields retain the exact preexisting generated game award.
"""
import json

STAT_XP_FIELDS_V3900 = {
    'strength': 'olc_reward_stat_strength',
    'dexterity': 'olc_reward_stat_dexterity',
    'constitution': 'olc_reward_stat_constitution',
    'intelligence': 'olc_reward_stat_intelligence',
    'willpower': 'olc_reward_stat_willpower',
    'charisma': 'olc_reward_stat_charisma',
}

QUEST_XP_ALIASES = {
    'reward_xp': 'olc_reward_xp',
    'xp_bieglosci': 'olc_reward_class_xp',
    'xp_duszy': 'olc_reward_soul_xp',
    'xp_statystyk': 'olc_reward_stat_xp',
    'reward_class_xp': 'olc_reward_class_xp',
    'reward_soul_xp': 'olc_reward_soul_xp',
    'reward_stat_xp': 'olc_reward_stat_xp',
    'reward_stat_strength': STAT_XP_FIELDS_V3900['strength'],
    'reward_stat_dexterity': STAT_XP_FIELDS_V3900['dexterity'],
    'reward_stat_constitution': STAT_XP_FIELDS_V3900['constitution'],
    'reward_stat_intelligence': STAT_XP_FIELDS_V3900['intelligence'],
    'reward_stat_willpower': STAT_XP_FIELDS_V3900['willpower'],
    'reward_stat_charisma': STAT_XP_FIELDS_V3900['charisma'],
    'xp_sila': STAT_XP_FIELDS_V3900['strength'],
    'xp_zrecznosc': STAT_XP_FIELDS_V3900['dexterity'],
    'xp_kondycja': STAT_XP_FIELDS_V3900['constitution'],
    'xp_inteligencja': STAT_XP_FIELDS_V3900['intelligence'],
    'xp_wola': STAT_XP_FIELDS_V3900['willpower'],
    'xp_charyzma': STAT_XP_FIELDS_V3900['charisma'],
    # Krótkie aliasy komend; w pliku JSON używaj kanonicznych nazw pól.
    'xp_profesji': 'reward_profession_xp',
    'xp_narzedzia': 'reward_tool_xp',
    'prof_xp': 'reward_profession_xp',
    'tool_xp': 'reward_tool_xp',
    'xp_postaci': 'olc_reward_xp',
    'poziom_profesji': 'min_profession_level',
    'poziom_narzedzia': 'min_tool_level',
}
QUEST_AUTO_FIELDS = frozenset({'olc_reward_xp','olc_reward_class_xp',
    'olc_reward_soul_xp','olc_reward_stat_xp','reward_profession_xp','reward_tool_xp'})

QUEST_EDIT_FIELDS = frozenset({
    'name', 'description', 'giver', 'kind', 'target', 'needed',
    'reward_silver', 'reward_gold', 'reward_mithril', 'reward_items',
    'reward_profession_xp', 'reward_tool_xp', 'reward_stat_progress',
    'generator_level', 'min_profession_level', 'min_tool_level',
    'repeatable', 'repeat_cooldown', 'requires_quest', 'requires_quests', 'resource_targets', 'objectives',
    *QUEST_XP_ALIASES.values(),
})
INTEGER_FIELDS = frozenset({
    'needed', 'reward_silver', 'reward_gold', 'reward_mithril',
    'reward_profession_xp', 'reward_tool_xp', 'reward_stat_progress',
    'generator_level', 'min_profession_level', 'min_tool_level',
    'repeat_cooldown', *QUEST_XP_ALIASES.values(),
})
FIELD_TITLES = {
    'olc_reward_xp': 'EXP postaci',
    'olc_reward_class_xp': 'EXP biegłości',
    'olc_reward_soul_xp': 'EXP Duszy',
    'olc_reward_stat_xp': 'EXP statystyk',
    'reward_profession_xp': 'EXP profesji',
    'reward_tool_xp': 'EXP narzędzia',
    'olc_reward_stat_strength': 'EXP Siły',
    'olc_reward_stat_dexterity': 'EXP Zręczności',
    'olc_reward_stat_constitution': 'EXP Kondycji',
    'olc_reward_stat_intelligence': 'EXP Inteligencji',
    'olc_reward_stat_willpower': 'EXP Siły Woli',
    'olc_reward_stat_charisma': 'EXP Charyzmy',
    'min_profession_level': 'poziom profesji (informacyjny)',
    'min_tool_level': 'poziom narzędzia (informacyjny)',
    'reward_stat_progress': 'postęp statystyk',
    'needed': 'wymagane', 'target': 'cel', 'kind': 'rodzaj',
    'reward_silver': 'srebro', 'reward_gold': 'złoto',
    'reward_mithril': 'mithril', 'repeat_cooldown': 'odnowienie (s)',
    'reward_items': 'nagrody przedmiotowe', 'requires_quests': 'wymagane questy', 'repeatable': 'powtarzalność',
    'name': 'nazwa', 'description': 'opis', 'giver': 'zleceniodawca',
}


def _number(value, low, high, field):
    if isinstance(value, bool):
        raise ValueError(f'{field}: oczekiwano liczby.')
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f'{field}: oczekiwano liczby całkowitej.') from exc
    if not low <= result <= high:
        raise ValueError(f'{field}: wymagany zakres {low}–{high}.')
    return result


def parse_quest_edit(field, value):
    field = QUEST_XP_ALIASES.get(field, field)
    if field not in QUEST_EDIT_FIELDS:
        raise ValueError(f'Quest: niedozwolone pole {field}.')
    if field in INTEGER_FIELDS:
        # v59: OLC respects owner-adjusted caps while retaining the historical
        # limit 800 unless deliberately changed through admin live.
        if field in ('generator_level','min_profession_level','min_tool_level'):
            from core.live_level_caps_v5200 import cap,effective_number
            axis={'generator_level':'postac','min_profession_level':'profesje','min_tool_level':'narzedzia'}[field]
            ceiling=effective_number(cap(axis))
        else:
            ceiling=365 * 86400 if field == 'repeat_cooldown' else 10**15
        floor = 1 if field in ('generator_level', 'needed', 'min_profession_level', 'min_tool_level') else 0
        return field, _number(value, floor, ceiling, field)
    if field == 'repeatable':
        if not isinstance(value, (str, bool)):
            raise ValueError('repeatable: true albo false.')
        if isinstance(value, bool):
            return field, value
        if value.lower() not in ('true', 'false', 'tak', 'nie', '1', '0'):
            raise ValueError('repeatable: true albo false.')
        return field, value.lower() in ('true', 'tak', '1')
    if field == 'requires_quest' and value is None:
        return field, None
    if field == 'requires_quests':
        if isinstance(value, str):
            try: value = json.loads(value)
            except json.JSONDecodeError as exc: raise ValueError('requires_quests: wymagana lista JSON ID.') from exc
        if (not isinstance(value, list) or len(value) > 8 or
                any(not isinstance(qid, str) or not qid for qid in value) or
                len(set(value)) != len(value)):
            raise ValueError('requires_quests: lista JSON maks. 8 różnych ID (albo []).')
        return field, value
    if field == 'objectives':
        if isinstance(value, str):
            try: value = json.loads(value)
            except json.JSONDecodeError as exc: raise ValueError('objectives: wymagany słownik JSON.') from exc
        if not isinstance(value, dict):
            raise ValueError('objectives: wymagany słownik JSON.')
        return field, value
    if field == 'resource_targets':
        if isinstance(value, str):
            try: value = json.loads(value)
            except json.JSONDecodeError as exc: raise ValueError('resource_targets: wymagany JSON.') from exc
        if not isinstance(value, dict):
            raise ValueError('resource_targets: słownik surowiec -> ilość.')
        return field, value
    if field == 'reward_items':
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError('reward_items: wymagany JSON, np. {"healing_potion":2}.') from exc
        if not isinstance(value, dict):
            raise ValueError('reward_items: wymagany słownik JSON.')
        return field, value
    if not isinstance(value, str) or not value.strip() or len(value) > 1600 or any(ord(c) < 32 for c in value):
        raise ValueError(f'{field}: pusty lub nieprawidłowy tekst.')
    return field, value.strip()


def validate_quest_edit(quest_id, base, patch, items, mobs, quests, npcs, live_npcs):
    # Validate even imported JSON data, not only typed admin commands.
    effective = dict(base)
    for field, value in patch.items():
        normalized, value = parse_quest_edit(field, value)
        if normalized != field:
            raise ValueError(f'{field}: użyj zapisanego pola {normalized}.')
        effective[field] = value
    if effective.get('kind') in ('kill', 'collect'):
        target = effective.get('target')
        allowed = mobs if effective['kind'] == 'kill' else items
        if 'kind' in patch or 'target' in patch:
            if target not in allowed and not (target == '*' and effective['kind'] == 'kill'):
                raise ValueError('Quest: wskazany cel nie istnieje w odpowiednim katalogu.')
    elif effective.get('kind') == 'collect_resource_set':
        # v61: permit synchronized target + resource set edits, but never a
        # standalone redirect. The resource-set validator below checks every
        # material, count, total and whether target belongs to the new set.
        if 'kind' in patch or ('target' in patch and 'resource_targets' not in patch):
            raise ValueError('Zestaw surowcow: cel zmieniaj tylko razem z resource_targets.')
    elif 'kind' in patch or 'target' in patch:
        raise ValueError('Zmiana rodzaju/celu jest bezpieczna tylko dla prostych questów kill/collect.')
    if 'objectives' in patch or (effective.get('kind') == 'multi_objective' and 'needed' in patch):
        if effective.get('kind') != 'multi_objective':
            raise ValueError('objectives: wyłącznie dla zadania wielocelowego.')
        from systems.live_olc18_multi_objective import validate_objectives
        known_npcs = set(npcs) | set(live_npcs)
        clean, total = validate_objectives(effective.get('objectives'), mobs, items, known_npcs)
        if effective.get('objectives') != clean or effective.get('needed') != total:
            raise ValueError('objectives: needed musi równać się sumie celów.')
    if 'resource_targets' in patch:
        if effective.get('kind') != 'collect_resource_set':
            raise ValueError('resource_targets: tylko istniejące zadanie zbierania zestawu surowców.')
        requirements = effective['resource_targets']
        if not 2 <= len(requirements) <= 8:
            raise ValueError('Zestaw: od 2 do 8 surowców.')
        from data.items import ITEMS
        for resource, quantity in requirements.items():
            if resource not in items or (ITEMS.get(resource) or {}).get('type') not in ('resource', 'material', 'craft_material', 'gem_raw', 'archaeology_find'):
                raise ValueError('Zestaw: nieznany surowiec.')
            if type(quantity) is not int:
                raise ValueError('Ilość surowca musi być liczbą całkowitą JSON.')
            _number(quantity, 1, 10000, 'Ilość surowca')
        if sum(requirements.values()) != int(effective.get('needed', 0)):
            raise ValueError('Zestaw: ustaw needed na sumę ilości w resource_targets.')
        if effective.get('target') not in requirements:
            raise ValueError('Zestaw: target musi wskazywać jeden z surowców zestawu.')
    if 'giver' in patch:
        names = {str(n.get('name', '')).casefold() for n in list(npcs.values()) + list(live_npcs.values())}
        if str(effective['giver']).casefold() not in names:
            raise ValueError('Quest: nie ma NPC o wskazanej nazwie.')
    if 'requires_quests' in patch:
        required = effective['requires_quests']
        if any(qid not in quests or qid == quest_id for qid in required):
            raise ValueError('requires_quests: nieznane ID lub odwołanie do samego siebie.')
    if 'requires_quest' in patch:
        target = effective['requires_quest']
        if target is not None and (target not in quests or target == quest_id):
            raise ValueError('requires_quest: nieznany quest lub odwołanie do samego siebie.')
    if any(field in patch for field in ('reward_silver', 'reward_gold', 'reward_mithril')):
        from core.bootstrap_economy_professions import (
            legacy_currency_to_coins, CURRENCY_SQLITE_SAFE_TOTAL,
        )
        exact_coins = legacy_currency_to_coins(
            effective.get('reward_silver', 0),
            effective.get('reward_gold', 0),
            effective.get('reward_mithril', 0),
        )
        if exact_coins > CURRENCY_SQLITE_SAFE_TOTAL:
            raise ValueError('Nagroda walutowa: przekroczono bezpieczny limit SQLite.')
    if 'reward_items' in patch:
        loot = effective['reward_items']
        if len(loot) > 30 or any(item_id not in items or
                                    _number(qty, 1, 100000, 'Ilość przedmiotu') < 1
                                    for item_id, qty in loot.items()):
            raise ValueError('Quest: nieznany przedmiot nagrody lub zbyt wiele pozycji.')
    if ('min_profession_level' in patch or 'min_tool_level' in patch):
        if (effective.get('kind') not in ('profession_action', 'craft_set')
                and not effective.get('required_profession')
                and not effective.get('reward_profession')):
            raise ValueError('Progi poziomu profesji i narzędzia dotyczą questów profesyjnych.')
    from systems.quest_combat_salvage_v102007 import is_combat_salvage_quest
    if ('olc_reward_class_xp' in patch
            and effective.get('kind') not in ('kill', 'legendary_rare', 'world_boss', 'party_contract')
            and not is_combat_salvage_quest(effective, quest_id)):
        raise ValueError('EXP biegłości dotyczy questów walki lub trzech zleceń z łupami z pokonanych wrogów.')
    if 'repeat_cooldown' in patch and not effective.get('repeatable', False):
        raise ValueError('Najpierw ustaw repeatable na true, aby zmienić czas odnowienia.')
    return effective


def news_summary(previous, current, rollback=False, revision=0):
    """Compact non-spam summary; no description dumps, no private admin data."""
    changes = []
    for section, label in (
        ('quest_edits', 'zadania'), ('quests', 'nowe zadania'),
        ('mob_edits', 'potwory'), ('mobs', 'nowe potwory'),
        ('room_edits', 'lokacje'), ('rooms', 'nowe lokacje'),
        ('links', 'przejścia'), ('spawns', 'spawny'),
        ('items', 'przedmioty'), ('item_edits', 'przedmioty'),
        ('npcs', 'NPC'), ('npc_edits', 'NPC'), ('shops', 'sklepy'),
        ('shop_edits', 'edycja sklepów'),
        ('recipes', 'receptury'), ('recipe_edits', 'receptury'),
        ('balances', 'balans mobów'), ('profession_edits', 'profesje'),
        ('tool_edits', 'narzędzia'), ('skill_edits', 'skille'),
        ('skills', 'nowe skille'),
        ('resource_edits', 'EXP surowców'),
    ):
        before, after = previous.get(section, {}), current.get(section, {})
        if before == after:
            continue
        if section == 'quest_edits':
            for qid in sorted(set(before) | set(after)):
                setting = after.get(qid, {})
                old_setting = before.get(qid, {})
                keys = [key for key in set(setting) | set(old_setting)
                        if setting.get(key) != old_setting.get(key)]
                if not keys:
                    continue
                from data.quests import QUESTS
                quest_name = str(QUESTS.get(qid, {}).get('name', qid))[:65]
                priority = ('reward_profession_xp', 'reward_tool_xp', 'olc_reward_xp',
                            'needed', 'reward_silver', 'min_profession_level',
                            'min_tool_level', 'repeat_cooldown')
                shown = []
                for key in sorted((key for key in keys if key not in ('description', 'reward_items')),
                                  key=lambda item: (priority.index(item) if item in priority else 999, item)):
                    entry = (f'{FIELD_TITLES.get(key, key)}: {setting[key]}' if key in setting
                             else f'cofnięto {FIELD_TITLES.get(key, key)}')
                    if len(', '.join(shown + [entry])) > 205:
                        shown.append('inne pola')
                        break
                    shown.append(entry)
                if 'reward_items' in keys and len(', '.join(shown + ['przedmioty'])) <= 205:
                    shown.append('zmieniono przedmioty')
                details = ', '.join(shown)
                changes.append(f'quest „{quest_name}” ({details})' if details else f'quest „{quest_name}”')
        elif isinstance(before, dict) and isinstance(after, dict):
            ids = set(before) | set(after)
            altered = sum(1 for key in ids if before.get(key) != after.get(key))
            if altered:
                changes.append(f'{label}: {altered}')
        else:
            changes.append(f'{label}: zmieniono')
    if not changes:
        changes.append('zmiany konfiguracji świata')
    heading = 'Cofnięto OLC' if rollback else 'Aktualizacja świata OLC'
    prefix = f'{heading} (rewizja {revision}): '
    selected = []
    for entry in changes:
        trial = '; '.join(selected + [entry])
        if len(prefix) + len(trial) > 475:
            selected.append('pozostałe zmiany')
            break
        selected.append(entry)
    return (prefix + '; '.join(selected))[:500]


def profession_quest_ids(quests, profession):
    """List quest IDs by real profession, including generated master chains."""
    import unicodedata
    from systems.profession_projects_v1200 import PROJECTS
    from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP

    def folded(text):
        normal = unicodedata.normalize('NFKD', str(text or '').replace('ł', 'l').replace('Ł', 'L'))
        return ''.join(c for c in normal if not unicodedata.combining(c)).casefold().strip()

    lookup = folded(profession)
    resolved = next((name for name, project in PROJECTS.items()
                     if lookup in (folded(name), folded(project.code))), None)
    if resolved is None:
        raise ValueError('Nieznana profesja. Podaj nazwę jednej z 22 profesji, np. Wędkarstwo.')
    tool_to_profession = {project.tool: name for name, project in PROJECTS.items()}
    tool_to_profession.update(TOOL_PROFESSION_MAP)
    result = []
    for qid, quest in quests.items():
        candidates = (
            quest.get('required_profession'), quest.get('reward_profession'),
            tool_to_profession.get(quest.get('reward_tool_type')),
            tool_to_profession.get(quest.get('specialist_tool_type')),
            quest.get('target') if quest.get('kind') in ('profession_action', 'craft_set') else None,
        )
        if any(folded(p) == folded(resolved) for p in candidates if p):
            result.append(qid)
    return sorted(result)
