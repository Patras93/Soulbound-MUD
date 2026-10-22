# -*- coding: utf-8 -*-
"""v27 / OLC52–59. Revisioned JSON controls, never executable admin code.

Every override defaults to exact v26 behavior. Game consumers read ACTIVE,
not the pending DRAFT, and the existing LiveContent SQLite transaction is
responsible for durable publish and rollback.
"""
import copy
import re

DOMAINS=('uoss','professions','summons','skills','events','story','factions','shops')
EMPTY={domain:{} for domain in DOMAINS}
ACTIVE=copy.deepcopy(EMPTY)
RANGES={
 'uoss':{'desperation_damage_percent':(100,400)},
 'professions':{'tool_xp_percent':(100,500)},
 'summons':{'intercept_min_hp_percent':(0,100)},
 'skills':{'mana_percent':(25,500)},
 'events':{'class_xp_reward':(1,10**14),'soul_reward':(1,10**14),'stat_reward':(1,10**14)},
 'story':{'quest_xp_percent':(100,500)},
 'factions':{'reputation_extra':(0,10000)},
 'shops':{'price_percent':(25,500)},
}
ALIASES={
 'uoss27':'uoss', 'boss27':'uoss',
 'fach27':'professions','prof27':'professions',
 'summon27':'summons','przywolany27':'summons',
 'magia27':'skills','skill27':'skills',
 'event27':'events','wydarzenie27':'events',
 'fabula27':'story','quest27':'story',
 'frakcja27':'factions','sklep27':'shops',
}

def validate(rules, *, v26_events=None, v24_professions=None, live_shops=None):
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES
    from data.shops import SHOPS
    from systems.live_olc26_world import FACTION_IDS
    if type(rules) is not dict or set(rules)!=set(DOMAINS):
        raise ValueError('OLC27: wymaganych jest osiem poprawnych dziedzin.')
    professions=set(PROFESSION_RANK_NAMES)|{x['name'] for x in (v24_professions or {}).values()}
    event_ids=set(v26_events or {})
    shop_ids=set(SHOPS)|set(live_shops or {})
    for domain,entries in rules.items():
        if type(entries) is not dict or len(entries)>200:
            raise ValueError('OLC27: domena '+domain+' musi mieć do 200 wpisów.')
        for key, fields in entries.items():
            if type(key) is not str or type(fields) is not dict or not fields or not set(fields)<=set(RANGES[domain]):
                raise ValueError('OLC27: niepoprawny identyfikator lub pole '+str(domain))
            if (domain=='uoss' and key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or
                domain=='professions' and key not in professions or
                domain=='summons' and key not in SUMMONS or
                domain=='skills' and key!='global' or
                domain=='events' and key not in event_ids or
                domain=='story' and key!='global' or
                domain=='factions' and key not in FACTION_IDS or
                domain=='shops' and key not in shop_ids):
                raise ValueError(f'OLC27 {domain}: nieznany identyfikator {key!r}.')
            for field,value in fields.items():
                low,high=RANGES[domain][field]
                if type(value) is not int or not low<=value<=high:
                    raise ValueError(f'{domain}/{key}/{field}: wymagane całkowite {low}–{high}.')
    return True

def sync(rules):
    for domain in DOMAINS:
        ACTIVE[domain].clear()
        ACTIVE[domain].update(copy.deepcopy(rules[domain]))

def stage(service, category, key, field, raw):
    domain=ALIASES.get(category)
    if domain is None:return False
    if field not in RANGES[domain]:
        raise ValueError('OLC27: dozwolone pola: '+', '.join(sorted(RANGES[domain])))
    staged=copy.deepcopy(service.draft)
    section=staged['v27_rules'][domain]
    if str(raw).strip().casefold() in ('auto','automatyczny'):
        if key in section:
            section[key].pop(field,None)
            if not section[key]:section.pop(key,None)
    else:
        if not re.fullmatch(r'[0-9]{1,16}',str(raw)):
            raise ValueError('OLC27: wymagana nieujemna liczba całkowita lub auto.')
        section.setdefault(key,{})[field]=int(raw)
    service.validate(staged)
    service.draft=staged
    return True

def preview(service,category,key,field):
    domain=ALIASES.get(category)
    if domain is None:return None
    if field not in RANGES[domain]:
        raise ValueError('OLC27: pola '+', '.join(sorted(RANGES[domain])))
    default=0 if field in ('reputation_extra','intercept_min_hp_percent') else 100
    if domain=='events': default='wartość starego szablonu areny'
    old=service.active['v27_rules'][domain].get(key,{}).get(field,default)
    new=service.draft['v27_rules'][domain].get(key,{}).get(field,default)
    return (f'OLC27 {category} {key} {field}. Aktualnie: {old}; DRAFT: {new}. '
            f'Edytuj: admin live edytuj {category} {key} {field} | LICZBA. Cofnij: auto.')

def uoss_desperation_factor(mob,template):
    key=template.get('uoss_unique_superboss_key') or ''
    setting=ACTIVE['uoss'].get(key,{}).get('desperation_damage_percent',100)
    if setting==100:return 1.0
    max_hp=max(1,int(getattr(mob,'adaptive_max_hp_v11330',0) or template.get('max_hp',1)))
    hp=min(max_hp,max(0,int(getattr(mob,'hp',max_hp))))
    return 1.0+(setting-100)/100.0*(max_hp-hp)/max_hp

def profession_tool_xp(profession,value):
    value=max(0,int(value))
    return value*ACTIVE['professions'].get(profession,{}).get('tool_xp_percent',100)//100

def summon_may_intercept(kind,hp,max_hp):
    threshold=ACTIVE['summons'].get(kind,{}).get('intercept_min_hp_percent',0)
    return int(hp)>0 and int(hp)*100>=max(1,int(max_hp))*threshold

def skill_mana_cost(value):
    value=max(0,int(value))
    return (value*ACTIVE['skills'].get('global',{}).get('mana_percent',100)+99)//100 if value else 0

def quest_character_xp(value):
    value=max(0,int(value))
    return value*ACTIVE['story'].get('global',{}).get('quest_xp_percent',100)//100

def faction_extra(faction,value):
    value=max(0,int(value))
    return value+(ACTIVE['factions'].get(faction,{}).get('reputation_extra',0) if value else 0)

def shop_room_price(room,value):
    value=max(0,int(value))
    return value*ACTIVE['shops'].get(room,{}).get('price_percent',100)//100

def event_rewards(slug):
    return ACTIVE['events'].get(slug,{})

def help_text():
    return ('OLC52–59 / v27: uoss27 BOSS desperation_damage_percent (100–400); '
            'fach27 PROFESJA tool_xp_percent (100–500); summon27 TYP intercept_min_hp_percent (0–100); '
            'magia27 global mana_percent (25–500); '
            'event27 live_ID class_xp_reward/soul_reward/stat_reward (dla event26); '
            'fabula27 global quest_xp_percent (100–500); '
            'frakcja27 FRAKCJA reputation_extra (0–10000); '
            'sklep27 ID_SKLEPU price_percent (25–500). '
            'Najpierw: admin live edytuj KATEGORIA ID POLE (aktualna wartość). '
            'Zmień: admin live edytuj KATEGORIA ID POLE | LICZBA; '
            'sprawdz; porownaj; aktywuj POTWIERDZAM. Cofnij wartością auto. '
            'Zapis i przywracanie: wspólne rewizje SQLite Live OLC.')
