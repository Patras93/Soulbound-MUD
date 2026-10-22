# -*- coding: utf-8 -*-
"""Read-only, NVDA-friendly, copy-ready preview of current live OLC values.

Generic telnet clients cannot have their input line populated by the server;
this module returns an editable command with its *actual* current value.
Dynamic rewards are explicitly distinguished from a single fixed amount.
"""
import json

from data.quests import QUESTS
from data.items import ITEMS
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from data.npcs import NPCS
from data.crafting_recipes import CRAFT_RECIPES
from data.shops import SHOPS
from systems.live_quest_olc_v1209 import QUEST_EDIT_FIELDS, QUEST_XP_ALIASES
from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
from systems.live_content_v1204 import CLASS_SKILLS
from systems.live_olc6_skill_editor import EDITABLE_FIELDS
from systems.live_olc21_phase_strategy import PHASE_STRATEGY_FIELDS, PHASE_FALLBACKS


SECTIONS = {
    'quest': ('quest_edits', QUESTS), 'zadanie': ('quest_edits', QUESTS),
    'surowiec': ('resource_edits', ITEMS), 'resource': ('resource_edits', ITEMS),
    'profesja': ('profession_edits', PROFESSION_RANK_NAMES),
    'narzedzie': ('tool_edits', TOOL_PROFESSION_MAP),
    'mob': ('mob_edits', MOB_TEMPLATES), 'potwor': ('mob_edits', MOB_TEMPLATES),
    'pokoj': ('room_edits', ROOMS), 'room': ('room_edits', ROOMS),
    'przedmiot': ('item_edits', ITEMS), 'item': ('item_edits', ITEMS),
    'npc': ('npc_edits', NPCS),
    'sklep': ('shop_edits', SHOPS), 'shop': ('shop_edits', SHOPS),
    'receptura': ('recipe_edits', CRAFT_RECIPES),
    'skill': ('skill_edits', None), 'umiejetnosc': ('skill_edits', None),
}
FIELDS = {
    'quest_edits': QUEST_EDIT_FIELDS,
    'resource_edits': frozenset({'prof_xp', 'tool_xp', 'prof_percent', 'tool_percent',
                               'prof_fixed', 'tool_fixed', 'prof_scale', 'tool_scale',
                               'prof_mode', 'tool_mode'}),
    'profession_edits': frozenset({'xp_percent', 'xp_scale'}),
    'tool_edits': frozenset({'xp_percent', 'xp_scale'}),
    'mob_edits': frozenset({'name','max_hp','damage','class_xp_reward','soul_reward',
                           'stat_reward','drops','auto_aggro','silver','gold','mithril',
                           'respawn_seconds','damage_type','olc_boss_phases','olc_boss_tactic_element','olc_boss_tactic_interval','olc_boss_support_interval',
                           'olc_boss_support_duration','olc_boss_rally_interval',
                           'olc_boss_rally_duration','olc_boss_guard_threshold','olc_boss_element_cycle','olc_boss_guardian_interval','olc_boss_guardian_roles','olc_boss_guardian_hp_threshold', 'olc_boss_guardian_phase_roles', 'olc_boss_phase_element_cycles', 'olc_boss_rally_hp_threshold', 'olc_boss_guardian_rewards','boss','olc_ancient_phases'}) | frozenset(PHASE_STRATEGY_FIELDS),
    'room_edits': frozenset({'name','desc','zone','generator_level'}),
    'item_edits': frozenset({'name','desc','price','currency','sell_silver','sell_gold',
                            'heal','defense','attack','magic_attack','magic_defense','weapon_power','required_level','stats'}),
    'npc_edits': frozenset({'name','dialogue','room','quest','shopkeeper','olc_dialogue_after_quest','olc_dialogue_after_quests'}),
    'recipe_edits': frozenset({'name','desc','min_profession_level','ingredients',
                                  'stations','output','quantity','min_tool_level','tool_xp','profession_xp'}),
    'shop_edits': frozenset({'inventory'}),
    'skill_edits': EDITABLE_FIELDS,
}


def _s(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def _auto_quest_xp(field, definition):
    """Display native BASE amounts, not inflated or player-specific final XP."""
    from core.progression_resources import (
        v0270_quest_character_reward, v0522_combat_quest_class_reward,
        v0522_is_profession_quest, v0190_quest_soul_reward,
    )
    from core.progression_resources import v0190_quest_stat_reward
    if field == 'olc_reward_xp':
        return v0270_quest_character_reward(definition)
    if field == 'olc_reward_class_xp':
        return v0522_combat_quest_class_reward(definition)
    if field == 'olc_reward_stat_xp':
        return v0190_quest_stat_reward(definition)
    if field == 'olc_reward_soul_xp':
        if v0522_is_profession_quest(definition):
            return 0
        return v0190_quest_soul_reward(definition)
    raise ValueError('Nieznany typ automatycznego EXP.')


def describe_current_edit(service, section, key, field):
    """Return one read-only preview plus a pre-filled command to copy and edit.

    This must neither change the draft nor trigger NEWS, commits or recompiles.
    """
    section = str(section).lower().strip()
    key = str(key).strip()
    field = str(field).lower().strip()
    from systems.live_olc28_expansion import preview as preview_v28
    result_v28=preview_v28(service,section,key,field)
    if result_v28 is not None:return result_v28
    from systems.live_olc27_master import preview as preview_v27
    result_v27=preview_v27(service,section,key,field)
    if result_v27 is not None:return result_v27
    from systems.live_olc26_world import preview as preview_v26
    result_v26 = preview_v26(service, section, key, field)
    if result_v26 is not None: return result_v26
    from systems.live_olc22_empire import extra_preview
    preview = extra_preview(service, section, key, field)
    if preview is not None:
        return preview
    if section not in SECTIONS:
        raise ValueError('Nieznana kategoria. Wpisz admin live help.')
    group, registry = SECTIONS[section]
    canonical = QUEST_XP_ALIASES.get(field, field) if group == 'quest_edits' else field
    live_skill = group == 'skill_edits' and key in service.draft['skills']
    extra_skill_fields = {'name','desc','unlock','mana','mult','scale','effect','olc_status'} if live_skill else set()
    if canonical not in FIELDS[group] | extra_skill_fields:
        raise ValueError(f'{section}: nieobsługiwane pole {field}.')
    if group == 'skill_edits':
        # New OLC metadata contains authoring fields like 'effect'; the
        # published class catalog stores their runtime equivalents heal_pct
        # or guard. Preview must show the editable metadata, not the runtime
        # projection, even after this skill has been published.
        definition = (service.draft['skills'][key] if live_skill else
                      next((row for skills in CLASS_SKILLS.values() for row in skills
                            if row['id'] == key), None))
        if definition is None or (canonical not in definition and canonical != 'olc_status'):
            raise ValueError('Nieznany skill lub jego parametr.')
    elif key not in registry:
        # Include objects created by the existing OLC, but not arbitrary IDs.
        source = {'shop_edits':'shops', 'quest_edits':'quests','room_edits':'rooms','mob_edits':'mobs',
                  'item_edits':'items','npc_edits':'npcs','recipe_edits':'recipes'}.get(group)
        definition = service.draft[source].get(key) if source else None
        if definition is None:
            raise ValueError('Nieznany identyfikator katalogu.')
    else:
        definition = registry[key]
    if group == 'resource_edits' and definition.get('type') not in (
            'resource','material','craft_material','gem_raw','archaeology_find'):
        raise ValueError('To nie jest obsługiwany surowiec.')

    active = (service.active['skills'].get(key, {}) if live_skill
              else service.active[group].get(key, {}))
    draft = (service.draft['skills'].get(key, {}) if live_skill
             else service.draft[group].get(key, {}))
    source = 'aktywne'
    note = ''
    suggestion_override = None
    # For real catalog definitions, the active registry has already been updated
    # by LiveContent._install. The active dictionary retains explicit overrides.
    if group == 'quest_edits' and canonical.startswith('olc_reward_'):
        if canonical in active:
            value = active[canonical]
            note = 'ręczna wartość bazowa'
        else:
            value = _auto_quest_xp(canonical, definition)
            note = 'automatycznie wyliczona wartość bazowa'
    elif group == 'resource_edits':
        side = canonical.split('_', 1)[0]
        mode = active.get(side + '_mode')
        if canonical.endswith('_mode'):
            value = mode or 'auto'
            note = 'tryb EXP'
        elif canonical.endswith('_scale'):
            value = active.get(canonical, active.get(side + '_percent', 100))
            note = ('stary mnożnik minimum (liczba pokazana informacyjnie); nowa komenda ustawia ścisły procent'
                    if canonical not in active and side + '_percent' in active else
                    'procent bazowego EXP; 100 = bez zmiany')
        elif canonical.endswith('_fixed'):
            if mode == 'manual':
                value = active[canonical]
                note = 'ręczna stała nagroda EXP'
            else:
                value = None
                note = 'brak jednej kwoty w trybie automatycznym; zależy od poziomu i czynności'
        else:
            value = active.get(canonical)
            if value is None:
                value = 100 if canonical.endswith('_percent') else None
                note = 'starsza reguła minimum EXP; brak nadpisania' if value is None else 'starszy mnożnik 100%'
            else:
                note = 'starsza reguła minimum EXP'
    elif group in ('profession_edits','tool_edits'):
        value = active.get(canonical, active.get('xp_percent', 100))
        note = ('stara premia z minimalną wypłatą; nowa komenda ustawia ścisły procent'
                if canonical == 'xp_scale' and 'xp_percent' in active and 'xp_scale' not in active
                else 'mnożnik EXP (%)')
    elif group == 'mob_edits' and canonical in ('olc_boss_support_interval', 'olc_boss_support_duration',
                                                  'olc_boss_rally_interval', 'olc_boss_rally_duration'):
        defaults = {'olc_boss_support_interval': 4, 'olc_boss_support_duration': 10,
                    'olc_boss_rally_interval': 5, 'olc_boss_rally_duration': 12}
        value = active.get(canonical, 'auto: 5 lub 7, zależnie od HP' if canonical == 'olc_boss_rally_interval' else defaults[canonical])
        note = 'automatyczny rytm zachowania bossa; ściśle określone wartości po nadpisaniu'
    elif group == 'mob_edits' and canonical in ('olc_boss_guardian_hp_threshold',
                                                'olc_boss_rally_hp_threshold',
                                                'olc_boss_guardian_phase_roles',
                                                'olc_boss_phase_element_cycles'):
        defaults = {'olc_boss_guardian_hp_threshold':'auto: przywołania od początku walki',
                    'olc_boss_rally_hp_threshold':40,
                    'olc_boss_guardian_phase_roles':'auto: oryginalne role pomocników',
                    'olc_boss_phase_element_cycles':'auto: oryginalna kolejność żywiołów'}
        value = active.get(canonical, defaults[canonical])
        note = ('ręczne ustawienie OLC; auto przywraca wcześniejszą taktykę'
                if canonical in active else 'domyślne zachowanie zwykłego bossa')
    elif group == 'mob_edits' and canonical in PHASE_STRATEGY_FIELDS:
        inherited = PHASE_FALLBACKS[canonical]
        default = {'olc_boss_phase_tactic_intervals': 4,
                   'olc_boss_phase_guardian_intervals': 3,
                   'olc_boss_phase_guard_thresholds': 55,
                   'olc_boss_phase_support_intervals': 4,
                   'olc_boss_phase_support_durations': 10,
                   'olc_boss_phase_support_priorities': 'weakest',
                   'olc_boss_phase_rally_hp_thresholds': 40,
                   'olc_boss_phase_rally_intervals': 5,
                   'olc_boss_phase_rally_durations': 12}[canonical]
        base_value = definition.get(inherited, default)
        if canonical in active:
            value = active[canonical]
            note = 'ręczne nadpisanie faz; pozostałe fazy dziedziczą ' + inherited
        else:
            value = f'auto (dziedziczy {inherited}={base_value})'
            suggestion_override = _s({'0': base_value})
            note = ('brak ręcznego nadpisania; przykład do skopiowania, nie aktywna wartość'
                    if canonical != 'olc_boss_phase_rally_intervals' else
                    'brak nadpisania; natywna wartość to 5 lub 7 w zależności od HP; przykład 5')
    elif group == 'mob_edits' and canonical == 'olc_ancient_phases':
        from systems.war_of_gods_bosses_v5000 import PROFILES
        idx = definition.get('v500_ancient_profile')
        if idx is None:
            raise ValueError('Ten mob nie jest pradawnym bossem v500.')
        thresholds, names, multipliers, elements=PROFILES[int(idx)]
        default = [dict(hp_percent=t,name=n,attack_percent=round(m*100),element=e,
                        duration_seconds=int(16+(i+1)*7))
                   for i,(t,n,m,e) in enumerate(zip(thresholds,names,multipliers,elements))]
        value = active.get(canonical, default)
        suggestion_override = _s(value)
        note = 'OLC22: trzy realne fazy pradawnego bossa; auto cofa do oryginału'
    elif group == 'mob_edits' and canonical == 'olc_boss_guardian_rewards':
        from systems.guardian_rewards_v1540 import default_guardian_rewards_v1540
        value = active.get(canonical, default_guardian_rewards_v1540(definition))
        note = ('Ręczne nagrody na osobę za pokonanego zwykłego pomocnika.'
                if canonical in active else
                'Auto: pokazano obecną bazową nagrodę EXP i walutę; możesz wpisać auto. Nie dotyczy UOSS.')
    elif group == 'mob_edits' and canonical == 'olc_boss_tactic_interval':
        value = active.get(canonical, 4)
        note = 'liczba rund pomiędzy istniejącymi atakami taktycznymi (domyślnie 4)'
    elif group == 'mob_edits' and canonical == 'olc_boss_tactic_element':
        value = active.get(canonical, 'auto')
        note = 'ręczny żywioł ataku taktycznego' if canonical in active else 'automatyczny wybór istniejącego AI'
    elif group == 'mob_edits' and canonical == 'olc_boss_phases':
        from systems.live_olc4_boss_phases import default_boss_phases
        # New live_ boss has its boss=True flag in the *draft* patch.
        # The preview is read-only and must support that staged flag.
        effective_template = dict(definition, **service.draft[group].get(key, {}))
        if canonical in active:
            value = active[canonical]
            note = 'aktywne ręczne fazy bossa; auto przywraca ustawienia oryginalne'
        else:
            value = default_boss_phases(effective_template)
            note = 'oryginalne fazy automatyczne; wywołaj auto, by je przywrócić'
    elif group == 'skill_edits' and canonical == 'olc_status' and canonical not in active and canonical not in definition:
        value = 'auto'
        note = 'brak efektu okresowego; użyj JSON albo auto'
    elif canonical in active:
        value = active[canonical]
        note = 'ręczne nadpisanie OLC'
    else:
        value = list(definition) if group == 'shop_edits' else (definition.get(canonical) if isinstance(definition, dict) else None)
        note = 'oryginalna wartość katalogowa'
    if group == 'quest_edits' and canonical in ('reward_silver', 'reward_gold', 'reward_mithril'):
        note = ('OLC: ręcznie ustawiony nominał, wypłata dokładna (bez losowej premii); '
                'całkowita nagroda to suma srebra, złota i mithrilu po publikacji'
                if any(k in active for k in ('reward_silver', 'reward_gold', 'reward_mithril'))
                else 'oryginalny nominał; bez edycji OLC wypłata może być generowana lub ustalona ręcznie')
    if group == 'quest_edits' and canonical in ('reward_profession_xp','reward_tool_xp') and value is None:
        value = 0
        note = 'bazowa wartość questu; wypłata końcowa może się skalować'
    if group == 'quest_edits' and canonical == 'repeat_cooldown' and value is None:
        # No default time is guaranteed to be the same for all quest families.
        note = 'brak jawnego odnowienia; czas może zależeć od rodzaju zadania'
    if group == 'quest_edits' and canonical == 'repeatable' and value is None:
        value = False
    staged = draft.get(canonical, None)
    staged_message = (f'; przygotowane: {_s(staged)}' if canonical in draft and staged != value else '')
    # Do not invent a numeric current value for dynamically derived resource XP.
    # A starting zero is only an editable example, labelled as such.
    suggestion = suggestion_override if suggestion_override is not None else ('0' if value is None else _s(value))
    if len(suggestion) > 1100 or any(ch in suggestion for ch in ('\n','\r','|')):
        return (f'OLC PODGLĄD {section} {key} {field}: obecnie: '
                f'{_s(value) if value is not None else "brak stałej wartości"}; {note}{staged_message}. '
                'Wartość zawiera znaki wymagające ręcznego wpisania; użyj edytuj z separatorem |.')
    return (f'OLC PODGLĄD {section} {key} {field}: obecnie: '
            f'{_s(value) if value is not None else "brak stałej wartości"} ({note}){staged_message}. '
            f'Do skopiowania i zmiany: admin live edytuj {section} {key} {field} | {suggestion}'
            + (' (zero jest przykładem, NIE aktualnym EXP).' if value is None else '')
            + (' Możesz też wpisać auto, aby przywrócić wyliczanie.'
               if (group == 'quest_edits' and canonical.startswith('olc_reward_')
                   or group == 'mob_edits' and canonical in ('olc_boss_phases', 'olc_boss_guardian_rewards', *PHASE_STRATEGY_FIELDS)
                   or group == 'skill_edits' and not live_skill) else ''))
