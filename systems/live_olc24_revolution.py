# -*- coding: utf-8 -*-
"""v24 OLC28–35: data-only rules, no executable scripts or player-save mutation.

All rules live inside the original revisioned SQLite OLC payload.
Missing keys preserve the exact v23 behavior. Each rule has a real engine consumer.
"""
import copy
import json
import re

ACTIVE = {'professions': {}, 'uoss': {}, 'summons': {}, 'cap': {},
          'events': {}, 'story': {}, 'world': {}}
DOMAINS = tuple(ACTIVE)
FACH_ID = re.compile(r'^live_[a-z0-9_]{3,55}$')
UOSS_FIELDS = {'lockout_hours', 'max_hp_percent', 'damage_percent', 'gold', 'silver', 'mithril', 'source_xp'}
SUMMON_FIELDS = {'hp_percent', 'damage_percent', 'mana_percent', 'regen_percent'}
CAP_FIELDS = {'step_extra_exp'}
EVENT_FIELDS = {'title', 'boss_name', 'style', 'element'}
WORLD_FIELDS = {'respawn_percent', 'event_hp_percent', 'event_damage_percent'}


def _strict_int(value, low, high, what):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{what}: liczba całkowita {low}–{high}.')


def _name(value, label, limit=90):
    if type(value) is not str or not 1 <= len(value.strip()) <= limit or any(ord(c) < 32 for c in value):
        raise ValueError(f'{label}: wymagany tekst 1–{limit} znaków bez znaków sterujących.')


def validate(rules, *, items=None, rooms=None):
    from data.items import ITEMS
    from data.rooms import ROOMS
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES, TOOL_PROFESSION_MAP
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from systems.world_events_v12812 import EVENTS
    items = ITEMS if items is None else items
    rooms = ROOMS if rooms is None else rooms
    if type(rules) is not dict or set(rules) != set(DOMAINS):
        raise ValueError('OLC24: nieprawidłowy zestaw siedmiu dziedzin.')
    for domain in DOMAINS:
        if type(rules[domain]) is not dict or len(rules[domain]) > 100:
            raise ValueError(f'OLC24 {domain}: wymagany słownik, maksymalnie 100 wpisów.')
    for key, row in rules['professions'].items():
        if not FACH_ID.fullmatch(key) or type(row) is not dict or set(row) != {'name','tool_type','tool_item_id','tool_name','station'}:
            raise ValueError('Nowa profesja: live_ID i JSON name/tool_type/tool_item_id/tool_name/station.')
        for f in ('name','tool_type','tool_item_id','tool_name','station'):
            _name(row[f],f,100)
        if not re.fullmatch(r'[a-z][a-z0-9_]{2,50}', row['tool_type']):
            raise ValueError('Nowa profesja: tool_type ma być bezpiecznym identyfikatorem.')
        old = ACTIVE['professions'].get(key)
        if old and (old['name'] != row['name'] or old['tool_type'] != row['tool_type'] or old['tool_item_id'] != row['tool_item_id']):
            raise ValueError('Po publikacji ID, nazwa i narzędzie profesji są trwałe ze względu na zapis postaci.')
        if ((row['name'] in PROFESSION_RANK_NAMES and (not old or old['name'] != row['name'])) or
            (row['tool_type'] in TOOL_PROFESSION_MAP and (not old or old['tool_type'] != row['tool_type']))):
            raise ValueError('Nowa profesja: nazwa lub rodzaj narzędzia już istnieje.')
        if row['tool_item_id'] not in items:
            raise ValueError('Nowa profesja: narzędzie musi istnieć w katalogu przedmiotów.')
        item=items[row['tool_item_id']]
        if item.get('type')!='tool' or item.get('tool_type') != row['tool_type']:
            raise ValueError('Nowa profesja: narzędzie musi mieć ten sam tool_type i typ tool.')
        if row['station'] not in rooms:
            raise ValueError('Nowa profesja: stanowisko musi być istniejącą lokacją.')
    names = [v['name'].casefold() for v in rules['professions'].values()]
    types = [v['tool_type'] for v in rules['professions'].values()]
    if len(names) != len(set(names)) or len(types) != len(set(types)):
        raise ValueError('Nowe profesje: nazwy i typy narzędzi bez duplikatów.')
    for key, row in rules['uoss'].items():
        if key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or type(row) is not dict or not row or not set(row) <= UOSS_FIELDS:
            raise ValueError('UOSS: nieznany boss lub pole.')
        for field, value in row.items():
            if field == 'lockout_hours': lo,hi = 1,168
            elif field in ('max_hp_percent', 'damage_percent'): lo,hi = 100,500
            elif field=='source_xp': lo,hi = 1,10**15
            else: lo,hi = 0,10**15
            _strict_int(value, lo, hi, f'UOSS {key}.{field}')
        from core.bootstrap_economy_professions import (SILVER_PER_GOLD,
            SILVER_PER_MITHRIL, CURRENCY_SQLITE_SAFE_TOTAL)
        manual_total = (row.get('silver',0) + SILVER_PER_GOLD*row.get('gold',0)
                        + SILVER_PER_MITHRIL*row.get('mithril',0))
        if manual_total > CURRENCY_SQLITE_SAFE_TOTAL:
            raise ValueError('UOSS: ręczne monety przekraczają bezpieczny zakres SQLite.')
    for key, row in rules['summons'].items():
        if key not in SUMMONS or type(row) is not dict or not row or not set(row) <= SUMMON_FIELDS:
            raise ValueError('Summon: nieznany typ lub pole.')
        for field, value in row.items():
            _strict_int(value, 10 if field == 'regen_percent' else 100, 1000 if field == 'regen_percent' else 500, f'Summon {key}.{field}')
    for key, val in rules['cap'].items():
        if key not in CAP_FIELDS or type(val) is not list or not 1 <= len(val) <= 80:
            raise ValueError('Cap: step_extra_exp to JSON z 1–80 nieujemnymi bonusami na przedziały 10 poziomów.')
        for x in val: _strict_int(x,0,10**9,'Bonus kroku Multi Cap')
    slugs = {e[0] for e in EVENTS}
    for key, row in rules['events'].items():
        if key not in slugs or type(row) is not dict or not row or not set(row) <= EVENT_FIELDS:
            raise ValueError('Event: nieznana inwazja lub pole.')
        for field,value in row.items():
            if field == 'style':
                if value not in ('physical','magic'): raise ValueError('Event.style: physical lub magic.')
            elif field == 'element':
                from systems.live_olc22_empire import ANCIENT_ELEMENTS
                if value not in ANCIENT_ELEMENTS: raise ValueError('Event.element: nieznany żywioł.')
            else: _name(value, 'Event '+field)
    # v24 story arcs are modifications of real authored quests and NPCs;
    # they are persisted in normal quests/npc_edits by the atomic editor, not
    # stored in this shadow section. Keep this reserved section empty.
    if rules['story']:
        raise ValueError('OLC24: fabuła używa realnych quest_edits/npc_edits, nie osobnego shadow registry.')
    for key, row in rules['world'].items():
        if key != 'global' or type(row) is not dict or not row or not set(row) <= WORLD_FIELDS:
            raise ValueError('Świat: global respawn_percent.')
        for field,value in row.items():
            _strict_int(value, 100, 1000 if field=='respawn_percent' else 500,field)
    return True


def natural(domain, key, field):
    if domain == 'uoss':
        if field=='lockout_hours': return 24
        if field in ('max_hp_percent','damage_percent'): return 100
        from data.mobs import MOB_TEMPLATES
        return MOB_TEMPLATES.get('uoss_superboss_'+key+'_v11136',{}).get(field,0)
    if domain == 'summons': return 100
    if domain == 'cap': return []
    if domain == 'world': return 100
    if domain == 'events':
        from systems.world_events_v12812 import EVENTS
        event = next((e for e in EVENTS if e[0]==key), None)
        return event[{'title':1,'boss_name':2,'style':3,'element':4}[field]] if event else None
    return None


def stage(service, category, key, field, raw):
    categories = {'fach':'professions','nowaprofesja':'professions',
                  'uoss':'uoss','superboss':'uoss',
                  'przywolany':'summons','summontyp':'summons',
                  'capkroki':'cap','event':'events','wydarzenie':'events',
                  'kontrola':'world','swiat24':'world'}
    domain = categories.get(category)
    if not domain: return False
    rules = copy.deepcopy(service.draft['v24_rules'])
    reset = str(raw).strip().casefold() in ('auto','automatyczny')
    if domain == 'professions':
        if field != 'definicja': raise ValueError('Nowa profesja: pole definicja (JSON).')
        if reset: rules[domain].pop(key,None)
        else:
            try: rules[domain][key] = json.loads(raw)
            except (ValueError,TypeError): raise ValueError('Nowa profesja: podaj JSON.')
    else:
        if domain == 'cap' and (key != 'global' or field != 'step_extra_exp'):
            raise ValueError('Cap: global step_extra_exp.')
        if domain == 'world' and key != 'global':
            raise ValueError('Świat: global respawn_percent.')
        allowed = {'uoss':UOSS_FIELDS,'summons':SUMMON_FIELDS,'cap':CAP_FIELDS,
                   'events':EVENT_FIELDS,'world':WORLD_FIELDS}[domain]
        if field not in allowed: raise ValueError('Nieznane pole '+field+'. Dostępne: '+', '.join(sorted(allowed)))
        if reset and domain=='cap':
            rules[domain].pop(field,None)
        elif reset:
            rules[domain].get(key,{}).pop(field,None)
            if not rules[domain].get(key): rules[domain].pop(key,None)
        elif domain=='cap':
            try: rules[domain][field] = json.loads(raw)
            except (ValueError,TypeError): raise ValueError('Cap: wymagany JSON listy liczb.')
        else:
            if field in ('title','boss_name','style','element'):
                value=str(raw)
            else:
                if not re.fullmatch(r'[0-9]{1,12}',str(raw)):
                    raise ValueError('Wymagana liczba całkowita.')
                value=int(raw,10)
            rules[domain].setdefault(key,{})[field]=value
    staged = copy.deepcopy(service.draft)
    staged['v24_rules']=rules
    service.validate(staged)
    service.draft=staged
    return True


def preview(service, category, key, field):
    categories={'fach':'professions','nowaprofesja':'professions',
                'uoss':'uoss','superboss':'uoss','przywolany':'summons','summontyp':'summons',
                'capkroki':'cap','event':'events','wydarzenie':'events',
                'kontrola':'world','swiat24':'world'}
    domain=categories.get(category)
    if not domain: return None
    current=service.active['v24_rules'][domain]
    draft=service.draft['v24_rules'][domain]
    if domain=='professions':
        if field!='definicja': raise ValueError('Pole: definicja.')
        v=current.get(key)
        d=draft.get(key)
    elif domain=='cap':
        if key!='global' or field!='step_extra_exp': raise ValueError('Pole: global step_extra_exp.')
        v=current.get(field)
        d=draft.get(field)
    else:
        allowed={'uoss':UOSS_FIELDS,'summons':SUMMON_FIELDS,'events':EVENT_FIELDS,'world':WORLD_FIELDS}[domain]
        if field not in allowed: raise ValueError('Nieznane pole; dozwolone: '+', '.join(sorted(allowed)))
        v=current.get(key,{}).get(field)
        d=draft.get(key,{}).get(field)
    default=natural(domain,key,field)
    tocopy = d if d is not None else (v if v is not None else default)
    arg = json.dumps(tocopy,ensure_ascii=False) if type(tocopy) in (dict,list) else str(tocopy)
    return (f'OLC24 {category} {key} {field}. Obecnie: {v if v is not None else default} '
            f'({"ręczne" if v is not None else "auto"}); projekt: {d if d is not None else "auto"}. '
            f'Skopiuj: admin live edytuj {category} {key} {field} | {arg}; przywróć: auto; '
            'publikacja: admin live aktywuj POTWIERDZAM.')


def sync_active(rules):
    for section in DOMAINS:
        ACTIVE[section].clear()
        ACTIVE[section].update(copy.deepcopy(rules[section]))


def respawn_seconds(base):
    """Optional world setting, applied ONLY to new respawn timers."""
    value = max(0,int(base))
    factor = ACTIVE['world'].get('global',{}).get('respawn_percent',100)
    return (value*factor + 99)//100


def uoss_lockout_hours(boss_key):
    return ACTIVE['uoss'].get(str(boss_key),{}).get('lockout_hours',24)


def summon_factor(kind,field):
    return ACTIVE['summons'].get(str(kind),{}).get(field,100)


def extra_cap_value(level):
    """Additional cumulative Multi Cap per track, O(1) over <=8 brackets.

    The last configured bracket repeats to higher levels. No reward reductions.
    """
    bonuses=ACTIVE['cap'].get('step_extra_exp',[])
    n=max(1,int(level))
    return sum(max(0,min(10,n-10*i))*x for i,x in enumerate(bonuses[:-1])) + (max(0,n-10*(len(bonuses)-1))*bonuses[-1] if bonuses else 0)


def stage_story_arc(service, changes_json):
    """Atomic, genuine quest prerequisite/story + NPC text editor.

    Only edits existing quest dependencies and dialogues through the real
    legacy OLC sections and their full graph/location validators.
    """
    from data.quests import QUESTS
    from data.npcs import NPCS
    try: arc=json.loads(changes_json)
    except (ValueError,TypeError): raise ValueError('Wymagany JSON fabuły.')
    if type(arc) is not dict or not set(arc)<= {'quests','npcs'} or not arc:
        raise ValueError('Fabuła: JSON z quests i/lub npcs.')
    staged=copy.deepcopy(service.draft)
    for qid,req in arc.get('quests',{}).items():
        if qid not in QUESTS and qid not in staged['quests']:
            raise ValueError('Nieznany quest: '+qid)
        # Backward compatible with the v24 list-only form.
        patch = {'requires_quests':req} if type(req) is list else req
        if type(patch) is not dict or not patch or not set(patch) <= {
                'requires_quests','description','reward_gold','reward_silver',
                'reward_mithril','olc_reward_xp'}:
            raise ValueError('Fabuła: dozwolone requires_quests/description/reward_gold/reward_silver/reward_mithril/olc_reward_xp.')
        staged['quest_edits'].setdefault(qid,{}).update(patch)
    for nid,entry in arc.get('npcs',{}).items():
        if nid not in NPCS and nid not in staged['npcs'] or type(entry) is not dict:
            raise ValueError('Fabuła: nieznany NPC lub błędne pola.')
        if set(entry) != {'quests','text'}:
            raise ValueError('Fabuła: NPC musi mieć quests i text.')
        staged['npc_edits'].setdefault(nid,{})['olc_dialogue_after_quests']=entry
    service.validate(staged)
    service.draft=staged
    return f'Fabuła: {len(arc.get("quests",{}))} questów i {len(arc.get("npcs",{}))} NPC w projekcie.'


def stage_skill_combo(service, skill_id, element, status_json):
    """Atomically stage a REAL elemental attack + status for an existing skill."""
    import copy
    from systems.live_olc6_skill_editor import stage_existing_skill
    staged=copy.deepcopy(service.draft)
    if skill_id in staged['skills']:
        from systems.live_olc19_status_skills import parse_status
        from systems.elemental_combat import V11339_ELEMENT_LABELS
        skill=staged['skills'][skill_id]
        if skill.get('kind') not in ('damage','aoe_damage') or element not in V11339_ELEMENT_LABELS:
            raise ValueError('Komboskill: wymagany zwykły atak i realny żywioł.')
        parsed=parse_status(status_json)
        if parsed is None: raise ValueError('Komboskill: wymagany prawdziwy status.')
        skill['element']=element
        skill['olc_status']=parsed
    else:
        stage_existing_skill(staged,skill_id,'element',element)
        stage_existing_skill(staged,skill_id,'olc_status',status_json)
    service.validate(staged)
    service.draft=staged
    return 'Skill '+skill_id+': ustawiono żywioł i efekt w jednej rewizji DRAFT.'
