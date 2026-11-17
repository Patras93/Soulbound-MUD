"""Retained gameplay/validation helpers for published content; no editor API."""

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
    from systems.published_26_world import FACTION_IDS
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
