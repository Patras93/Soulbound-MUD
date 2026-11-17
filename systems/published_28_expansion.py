"""Retained gameplay/validation helpers for published content; no editor API."""

import copy

import re

DOMAINS = ('uoss','professions','summons','skills','events','story','guilds','economy')

EMPTY = {name:{} for name in DOMAINS}

ACTIVE = copy.deepcopy(EMPTY)

FIELDS = {
 'uoss': {'finisher_target_hp_percent':(1,80),'finisher_damage_percent':(100,500)},
 'professions': {'craft_yield_percent':(100,300)},
 'summons': {'outgoing_damage_percent':(100,500)},
 'skills': {'damage_percent':(100,500)},
 'events': {'rotation_weight':(1,5)},
 'story': {'quest_currency_percent':(100,500)},
 'guilds': {'bonus_extra_percent':(0,100)},
 'economy': {'sell_value_percent':(100,500)},
}

ALIASES = {'uoss28':'uoss','boss28':'uoss',
           'fach28':'professions','rzemioslo28':'professions',
           'summon28':'summons','przywolany28':'summons',
           'skill28':'skills','magia28':'skills',
           'event28':'events','wydarzenie28':'events',
           'fabula28':'story','quest28':'story',
           'gildia28':'guilds','frakcja28':'guilds',
           'ekonomia28':'economy','swiat28':'economy'}

def validate(config, *, professions=None, events=None):
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES
    from player.session_mixins.era_sky_v1700 import SUMMONS
    if type(config) is not dict or set(config)!=set(DOMAINS):
        raise ValueError('OLC28: wymaganych jest osiem dziedzin.')
    allowed_professions=set(PROFESSION_RANK_NAMES)|{x['name'] for x in (professions or {}).values()}
    event_ids=set(events or {})
    for domain, rows in config.items():
        if type(rows) is not dict or len(rows)>200:
            raise ValueError('OLC28: niewłaściwa lista '+domain)
        for key,record in rows.items():
            if (type(key) is not str or type(record) is not dict or not record or
                    not set(record)<=set(FIELDS[domain])):
                raise ValueError('OLC28: niedozwolony identyfikator/pole '+str(key))
            if (domain=='uoss' and key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or
                domain=='professions' and key not in allowed_professions or
                domain=='summons' and key not in SUMMONS or
                domain=='skills' and key!='global' or
                domain=='events' and key not in event_ids or
                domain in ('story','guilds','economy') and key!='global'):
                raise ValueError(f'OLC28: nieznany identyfikator {domain}/{key}')
            for field,value in record.items():
                low,high=FIELDS[domain][field]
                if type(value) is not int or not low<=value<=high:
                    raise ValueError(f'OLC28 {domain}/{field}: wymagane {low}–{high}.')
    return True

def sync(config):
    for domain in DOMAINS:
        ACTIVE[domain].clear()
        ACTIVE[domain].update(copy.deepcopy(config[domain]))

def boss_finisher_factor(template,target_hp,target_max_hp):
    settings=ACTIVE['uoss'].get(template.get('uoss_unique_superboss_key',''),{})
    threshold=settings.get('finisher_target_hp_percent',25)
    if target_max_hp>0 and 0<int(target_hp)*100<=int(target_max_hp)*threshold:
        return settings.get('finisher_damage_percent',100)/100.0
    return 1.0

def craft_yield(profession,amount):
    value=max(0,int(amount));pct=ACTIVE['professions'].get(profession,{}).get('craft_yield_percent',100)
    return value*pct//100

def summon_outgoing(kind,amount):
    return max(1,int(amount)*ACTIVE['summons'].get(kind,{}).get('outgoing_damage_percent',100)//100)

def skill_damage_multiplier(value):
    return float(value)*ACTIVE['skills'].get('global',{}).get('damage_percent',100)/100.0

def event_weight(slug):
    return ACTIVE['events'].get(slug,{}).get('rotation_weight',1)

def quest_coins(value):
    return max(0,int(value))*ACTIVE['story'].get('global',{}).get('quest_currency_percent',100)//100

def guild_extra_bonus(is_member):
    return ACTIVE['guilds'].get('global',{}).get('bonus_extra_percent',0) if is_member else 0

def sale_coins(value):
    return max(0,int(value))*ACTIVE['economy'].get('global',{}).get('sell_value_percent',100)//100
