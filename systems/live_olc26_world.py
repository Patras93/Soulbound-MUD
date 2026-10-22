# -*- coding: utf-8 -*-
"""Soulbound v26 / OLC44-51: strictly declarative, revisioned content.

All keys default to vanilla behavior. No user-authored Python, no save edits.
"""
import copy
import json
import re

EMPTY = {'uoss':{},'professions':{},'summons':{},'events':{},
         'story':{},'factions':{},'world':{}}
ACTIVE = copy.deepcopy(EMPTY)
CUSTOM_ID = re.compile(r'^live_[a-z0-9_]{3,45}$')
UOSS_FIELDS = {'berserk_hp_percent':(1,95),'berserk_damage_percent':(100,500)}
SUMMON_FIELDS = {'intercept_chance_percent':(1,95),'incoming_damage_percent':(25,100)}
WORLD_FIELDS = {'shop_price_percent':(25,500)}
EVENT_FIELDS = {'name','boss_name','city','style','element','hp','damage','silver'}
FACTION_IDS = frozenset(('cartographers','waters','miners','green_path','frontier_watch'))


def integer(value, lo, hi, label):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{label}: liczba całkowita {lo}–{hi}.')


def label(value, name):
    if type(value) is not str or not 1 <= len(value.strip()) <= 90 or any(ord(c)<32 for c in value):
        raise ValueError(f'{name}: 1–90 znaków tekstu bez znaków sterujących.')


def validate(rules, *, quests=None, professions=None):
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES
    from data.quests import QUESTS
    from systems.live_olc22_empire import ANCIENT_ELEMENTS
    if type(rules) is not dict or set(rules)!=set(EMPTY):
        raise ValueError('OLC26: nieprawidłowe domeny. Wymagane '+', '.join(EMPTY))
    for section, values in rules.items():
        if type(values) is not dict or len(values)>100:
            raise ValueError(f'OLC26 {section}: wymagany słownik do 100 wpisów.')
    for boss, fields in rules['uoss'].items():
        if boss not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or type(fields) is not dict or not fields or not set(fields)<=set(UOSS_FIELDS):
            raise ValueError('OLC26: nieznany UOSS lub pole berserk.')
        for field,val in fields.items(): integer(val,*UOSS_FIELDS[field],field)
    all_prof = set(PROFESSION_RANK_NAMES) | {p['name'] for p in (professions or {}).values()}
    for prof, fields in rules['professions'].items():
        if prof not in all_prof or type(fields) is not dict or set(fields)!={'xp_percent'}:
            raise ValueError('OLC26: profesja wymaga znanej nazwy i pola xp_percent.')
        integer(fields['xp_percent'],100,500,prof+' XP')
    for kind, fields in rules['summons'].items():
        if kind not in SUMMONS or type(fields) is not dict or not fields or not set(fields)<=set(SUMMON_FIELDS):
            raise ValueError('OLC26: nieznany summon lub pole.')
        for field,val in fields.items(): integer(val,*SUMMON_FIELDS[field],field)
    for slug, event in rules['events'].items():
        if not CUSTOM_ID.fullmatch(slug) or type(event) is not dict or set(event)!=EVENT_FIELDS:
            raise ValueError('Nowy event: live_ID oraz komplet name,boss_name,city,style,element,hp,damage,silver.')
        label(event['name'],'Nazwa wydarzenia'); label(event['boss_name'],'Boss wydarzenia')
        if event['city'] not in ('basalt','echo','star','myth'):
            raise ValueError('Event.city: basalt/echo/star/myth (istniejące areny).')
        if event['style'] not in ('physical','magic') or event['element'] not in ANCIENT_ELEMENTS:
            raise ValueError('Event: nieznany styl lub żywioł.')
        for field,lo,hi in (('hp',100,10**12),('damage',1,10**10),('silver',0,10**12)):
            integer(event[field],lo,hi,'Event.'+field)
    qids=set(QUESTS)|set(quests or {})
    seen=set()
    for group, quests_in_group in rules['story'].items():
        if not CUSTOM_ID.fullmatch(group) or type(quests_in_group) is not list or not 2<=len(quests_in_group)<=8:
            raise ValueError('Wybór fabularny: live_ID i lista 2–8 ID questów.')
        if any(type(q) is not str or q not in qids or q in seen for q in quests_in_group):
            raise ValueError('Quest fabularny nie istnieje lub występuje w dwóch wykluczających się grupach.')
        seen.update(quests_in_group)
    for faction, values in rules['factions'].items():
        if faction not in FACTION_IDS or type(values) is not dict or set(values)!={'reputation_percent'}:
            raise ValueError('Frakcja: wymagany znany identyfikator i reputation_percent.')
        integer(values['reputation_percent'],100,500,'Reputacja')
    if set(rules['world'])-set(WORLD_FIELDS):
        raise ValueError('Świat OLC26: nieznane pole.')
    for field,val in rules['world'].items(): integer(val,*WORLD_FIELDS[field],field)
    return True


def sync(rules):
    for section in EMPTY:
        ACTIVE[section].clear()
        ACTIVE[section].update(copy.deepcopy(rules[section]))


def stage(service, category, identifier, field, raw):
    aliases={'uoss26':'uoss','boss26':'uoss', 'fach26':'professions',
             'summon26':'summons','przywolany26':'summons','event26':'events',
             'wybor26':'story','frakcja26':'factions','ekonomia26':'world'}
    domain=aliases.get(category)
    if domain is None: return False
    staged=copy.deepcopy(service.draft)
    rules=staged['v26_rules']
    reset=str(raw).casefold().strip() in ('auto','automatyczny')
    if domain=='story':
        if field!='questy': raise ValueError('Wybór: pole questy.')
        if reset:rules['story'].pop(identifier,None)
        else:
            try: rules['story'][identifier]=json.loads(raw)
            except (ValueError,TypeError): raise ValueError('Wybór: lista JSON questów.')
    elif domain=='events':
        if field!='definicja': raise ValueError('Nowy event: pole definicja.')
        if reset:rules['events'].pop(identifier,None)
        else:
            try: rules['events'][identifier]=json.loads(raw)
            except (ValueError,TypeError): raise ValueError('Event: obiekt JSON.')
    else:
        fields={'uoss':UOSS_FIELDS,'professions':{'xp_percent':(100,500)},
                'summons':SUMMON_FIELDS,'factions':{'reputation_percent':(100,500)},
                'world':WORLD_FIELDS}[domain]
        if field not in fields: raise ValueError('Nieznane pole. Dozwolone: '+', '.join(sorted(fields)))
        key='global' if domain=='world' else identifier
        if domain=='world' and identifier!='global':raise ValueError('Ekonomia26: wymagane global.')
        if reset:
            if domain=='world': rules['world'].pop(field,None)
            else:
                rules[domain].get(key,{}).pop(field,None)
                if not rules[domain].get(key):rules[domain].pop(key,None)
        else:
            if not re.fullmatch(r'\d{1,12}',str(raw)):raise ValueError('Wymagana liczba całkowita.')
            if domain=='world':rules[domain][field]=int(raw)
            else:rules[domain].setdefault(key,{})[field]=int(raw)
    service.validate(staged)
    service.draft=staged
    return True


def preview(service, category, identifier, field):
    aliases={'uoss26':'uoss','boss26':'uoss','fach26':'professions','summon26':'summons',
             'przywolany26':'summons','event26':'events','wybor26':'story',
             'frakcja26':'factions','ekonomia26':'world'}
    domain=aliases.get(category)
    if domain is None:return None
    if domain in ('events','story'):
        current=service.active['v26_rules'][domain].get(identifier)
        draft=service.draft['v26_rules'][domain].get(identifier)
    elif domain=='world':
        current=service.active['v26_rules'][domain].get(field)
        draft=service.draft['v26_rules'][domain].get(field)
    else:
        current=service.active['v26_rules'][domain].get(identifier,{}).get(field)
        draft=service.draft['v26_rules'][domain].get(identifier,{}).get(field)
    default=100 if domain in ('world','professions','factions') or field.endswith('percent') else None
    formatted=json.dumps(draft if draft is not None else (current if current is not None else default),ensure_ascii=False)
    return (f'OLC26 {category} {identifier} {field}. Aktywne: {current if current is not None else default} '
            f'; DRAFT: {draft if draft is not None else "auto"}. '
            f'Komenda: admin live edytuj {category} {identifier} {field} | {formatted}. Cofnij: auto.')


def uoss_berserk_factor(mob, template):
    key=template.get('uoss_unique_superboss_key') or ''
    row=ACTIVE['uoss'].get(key,{})
    if not row or 'berserk_damage_percent' not in row:return 1.0
    maximum=max(1,int(getattr(mob,'adaptive_max_hp_v11330',0) or template.get('max_hp',1)))
    hp=max(0,int(getattr(mob,'hp',maximum)))
    return row['berserk_damage_percent']/100.0 if hp*100 <= maximum*row.get('berserk_hp_percent',30) else 1.0


def profession_xp_bonus(profession, xp):
    return max(0,int(xp))*ACTIVE['professions'].get(profession,{}).get('xp_percent',100)//100


def summon_intercept_chance(kind, guarding=False):
    default=52 if guarding else 32
    return ACTIVE['summons'].get(kind,{}).get('intercept_chance_percent',default)/100.0


def summon_incoming_damage(kind, amount):
    return max(1,max(1,int(amount))*ACTIVE['summons'].get(kind,{}).get('incoming_damage_percent',100)//100)


def faction_reward(faction, amount):
    base=max(0,int(amount))
    return base*ACTIVE['factions'].get(faction,{}).get('reputation_percent',100)//100


def shop_price(value):
    return max(0,int(value))*ACTIVE['world'].get('shop_price_percent',100)//100


def conflicting_quests(quest_id):
    for group in ACTIVE['story'].values():
        if quest_id in group:return tuple(x for x in group if x != quest_id)
    return ()


def event_catalog():
    return ACTIVE['events']


def help_text():
    return ('OLC44–51: uoss26 BOSS berserk_hp_percent/berserk_damage_percent; '
            'fach26 NAZWA_PROFESJI xp_percent; summon26 TYP intercept_chance_percent/incoming_damage_percent; '
            'event26 live_ID definicja | JSON(name,boss_name,city,style,element,hp,damage,silver); '
            'wybor26 live_ID questy | ["quest1","quest2"]; frakcja26 ID reputation_percent; '
            'ekonomia26 global shop_price_percent; pakietskilli | JSON lista nowych skilli. '
            'Każde pole: podgląd, auto, sprawdz, porownaj, aktywuj POTWIERDZAM. '
            'Modyfikacje bez wykonywalnego kodu użytkownika; nie edytuje zapisów postaci.')
