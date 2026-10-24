# -*- coding: utf-8 -*-
"""Soulbound v32 OLC 76–83: safe data-only expansion in eight gameplay paths.

No eval, no executable administrator payloads. Data persists in existing
live_content_v1204 revisions; an empty configuration preserves v31 exactly.
"""
import copy
import datetime
import json
import re

CATEGORIES = ('uoss', 'professions', 'summons', 'skills', 'events', 'story', 'guilds', 'world')
ACTIVE = {name: {} for name in CATEGORIES}
ALIASES = {
    'uoss32': 'uoss', 'boss32': 'uoss',
    'fach32': 'professions', 'profesja32': 'professions',
    'summon32': 'summons', 'przywolanie32': 'summons',
    'skill32': 'skills', 'magia32': 'skills',
    'event32': 'events', 'wydarzenie32': 'events',
    'fabula32': 'story', 'quest32': 'story',
    'gildia32': 'guilds', 'frakcja32': 'guilds',
    'swiat32': 'world', 'warsztat32': 'world',
}


def _number(value, low, high, field):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{field}: wymagane {low}–{high}.')


def validate(rows, *, payload=None):
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from data.crafting_recipes import CRAFT_RECIPES
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from core.classes_skills import CLASS_SKILLS
    from data.quests import QUESTS
    from data.items import ITEMS
    from data.rooms import ROOMS
    from systems.live_olc26_world import event_catalog
    if type(rows) is not dict or set(rows) != set(CATEGORIES):
        raise ValueError('OLC32: wymaganych jest osiem obszarów.')
    payload = payload or {}
    skill_ids={skill['id'] for group in CLASS_SKILLS.values() for skill in group}
    skill_ids.update(payload.get('skills',{}))
    known_recipes=set(CRAFT_RECIPES)|set(payload.get('recipes',{}))
    known_summons=set(SUMMONS)|set(payload.get('v29_rules',{}).get('summons',{}))
    known_events=set(event_catalog())|set(payload.get('v26_rules',{}).get('events',{}))
    known_quests=set(QUESTS)|set(payload.get('quests',{}))
    known_items=set(ITEMS)|set(payload.get('items',{}))
    known_rooms=set(ROOMS)|set(payload.get('rooms',{}))
    for category, entries in rows.items():
        if type(entries) is not dict or len(entries)>250:
            raise ValueError('OLC32: za dużo wpisów '+category)
        for key, setting in entries.items():
            if type(key) is not str or type(setting) is not dict or not setting:
                raise ValueError('OLC32: nieprawidłowy identyfikator lub pusty wpis.')
            if category == 'uoss':
                if key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or set(setting) != {'phases'}:
                    raise ValueError('UOSS32: istniejący boss, pole phases.')
                phases=setting['phases']
                if type(phases) is not list or not 1<=len(phases)<=5:
                    raise ValueError('UOSS32: od 1 do 5 faz.')
                previous=101
                for phase in phases:
                    if type(phase) is not dict or set(phase)!= {'below_hp','interval','damage_percent'}:
                        raise ValueError('UOSS32: below_hp,interval,damage_percent.')
                    _number(phase['below_hp'],1,99,'Próg HP bossa')
                    _number(phase['interval'],1,20,'Co ile ataków')
                    _number(phase['damage_percent'],100,500,'Premia fazy')
                    if phase['below_hp']>=previous:
                        raise ValueError('Fazy UOSS muszą mieć malejące progi HP.')
                    previous=phase['below_hp']
            elif category=='professions':
                if key not in known_recipes or set(setting)!={'extra_output'}:
                    raise ValueError('Fach32: istniejąca receptura + extra_output.')
                _number(setting['extra_output'],1,10,'Dodatkowe sztuki')
            elif category=='summons':
                if key not in known_summons or set(setting)!={'combo_every','combo_percent'}:
                    raise ValueError('Summon32: istniejący typ, combo_every,combo_percent.')
                _number(setting['combo_every'],2,20,'Rytm serii summona')
                _number(setting['combo_percent'],100,500,'Premia serii')
            elif category=='skills':
                if key not in skill_ids or set(setting)!={'combo_every','combo_percent'}:
                    raise ValueError('Skill32: istniejący skill, combo_every,combo_percent.')
                _number(setting['combo_every'],2,20,'Rytm serii skilla')
                _number(setting['combo_percent'],100,500,'Premia skilla')
            elif category=='events':
                if key not in known_events or set(setting)!={'hours_utc'}:
                    raise ValueError('Event32: istniejący własny event, hours_utc.')
                hours=setting['hours_utc']
                if type(hours) is not list or not hours or len(hours)>24 or len(set(map(str,hours)))!=len(hours):
                    raise ValueError('Event32: unikalne godziny UTC 0–23.')
                for hour in hours: _number(hour,0,23,'Godzina UTC')
            elif category=='story':
                if key not in known_quests or set(setting)!={'bonus_items'} or not setting['bonus_items']:
                    raise ValueError('Fabula32: istniejący quest i bonus_items.')
                bonus=setting['bonus_items']
                if type(bonus) is not dict or len(bonus)>8:
                    raise ValueError('Fabula32: najwyżej 8 przedmiotów nagród.')
                for item,amount in bonus.items():
                    if item not in known_items:raise ValueError('Nieznany przedmiot nagrody '+str(item))
                    _number(amount,1,100,'Ilość nagrody')
            elif category=='guilds':
                if key!='global' or set(setting)!={'milestones'}:
                    raise ValueError('Gildia32: global i milestones.')
                milestones=setting['milestones']
                if type(milestones) is not list or not 1<=len(milestones)<=15:
                    raise ValueError('Gildia32: 1–15 progów.')
                previous=0
                for milestone in milestones:
                    if type(milestone) is not dict or set(milestone)!={'level','bonus_percent'}:
                        raise ValueError('Gildia32: level,bonus_percent.')
                    from systems.olc_level_bounds_v7003 import level_bound
                    _number(milestone['level'],1,level_bound('gildia'),'Poziom gildii')
                    _number(milestone['bonus_percent'],1,30,'Bonus gildii')
                    if milestone['level']<=previous: raise ValueError('Progi gildii muszą rosnąć.')
                    previous=milestone['level']
            elif category=='world':
                if key not in known_rooms or set(setting)!={'workshop_yield_percent'}:
                    raise ValueError('Swiat32: pokój i workshop_yield_percent.')
                _number(setting['workshop_yield_percent'],100,300,'Bonus warsztatu')
    return True


def sync(config):
    for category in CATEGORIES:
        ACTIVE[category].clear()
        ACTIVE[category].update(copy.deepcopy(config[category]))


def stage(service, category, key, field, value):
    domain=ALIASES.get(category)
    if domain is None:return False
    if field!='definicja':raise ValueError('OLC32: pole definicja (JSON).')
    updated=copy.deepcopy(service.draft)
    if str(value).strip().casefold() in ('auto','automatyczny'):
        updated['v32_rules'][domain].pop(key,None)
    else:
        try:updated['v32_rules'][domain][key]=json.loads(value)
        except (TypeError,ValueError) as exc:raise ValueError('OLC32: podaj poprawny JSON.') from exc
    service.validate(updated)
    service.draft=updated
    return True


def preview(service,category,key,field):
    domain=ALIASES.get(category)
    if domain is None:return None
    if field!='definicja':raise ValueError('OLC32: pole definicja.')
    current=service.active['v32_rules'][domain].get(key,'auto')
    proposed=service.draft['v32_rules'][domain].get(key,'auto')
    return (f'OLC32 {domain}/{key}: aktualnie {json.dumps(current,ensure_ascii=False)}; '
            f'DRAFT {json.dumps(proposed,ensure_ascii=False)}. '
            f'admin live edytuj {category} {key} definicja | JSON; auto przywraca.')


def package(service,source):
    """Stage one validated, atomic eight-domain payload without publishing."""
    try: spec=json.loads(source)
    except (ValueError,TypeError) as exc:raise ValueError('Pakiet32: podaj JSON.') from exc
    if type(spec) is not dict or not spec or set(spec)-set(CATEGORIES):
        raise ValueError('Pakiet32: osiem dostępnych kategorii OLC32.')
    proposed=copy.deepcopy(service.draft)
    for category,entries in spec.items():
        if type(entries) is not dict: raise ValueError('Pakiet32: słownik ID -> definicja.')
        proposed['v32_rules'][category].update(copy.deepcopy(entries))
    result=service.validate(proposed)
    service.draft=proposed
    return f'Pakiet32 przygotowany: {sum(map(len,spec.values()))} obiektów. {result}'


def uoss_phase_multiplier(mob,template):
    row=ACTIVE['uoss'].get(template.get('uoss_unique_superboss_key',''))
    if not row:return 1.0
    hp=max(0,int(getattr(mob,'hp',getattr(mob,'current_hp',0)) or 0))
    maximum=max(1,int(getattr(mob,'max_hp',0) or template.get('max_hp',1)))
    turns=int(getattr(mob,'_olc32_attack_turn',0))+1
    mob._olc32_attack_turn=turns
    active=None
    for phase in row['phases']:
        if hp*100<=maximum*phase['below_hp']:
            active=phase
    return active['damage_percent']/100.0 if active and turns%active['interval']==0 else 1.0


def crafting_bonus(recipe_id,room_id,quantity):
    """Called once after the original yield calculation, never on ingredients."""
    quantity=max(0,int(quantity))
    if quantity==0:return 0
    quantity+=ACTIVE['professions'].get(recipe_id,{}).get('extra_output',0)
    pct=ACTIVE['world'].get(room_id,{}).get('workshop_yield_percent',100)
    return max(quantity,quantity*pct//100)


def summon_combo(owner,summon_id,damage):
    row=ACTIVE['summons'].get(summon_id)
    if not row:return damage
    counters=getattr(owner,'_olc32_summon_combo',None)
    if counters is None:counters={};owner._olc32_summon_combo=counters
    count=counters.get(summon_id,0)+1
    counters[summon_id]=count
    return max(1,int(damage)*row['combo_percent']//100) if count%row['combo_every']==0 else damage


def skill_combo(owner,skill_id,multiplier):
    row=ACTIVE['skills'].get(skill_id)
    if not row:return multiplier
    counters=getattr(owner,'_olc32_skill_combo',None)
    if counters is None:counters={};owner._olc32_skill_combo=counters
    count=counters.get(skill_id,0)+1
    counters[skill_id]=count
    return multiplier*row['combo_percent']/100.0 if count%row['combo_every']==0 else multiplier


def event_allowed(slug, moment):
    settings=ACTIVE['events'].get(slug)
    if not settings:return True
    hour=datetime.datetime.fromtimestamp(float(moment),datetime.timezone.utc).hour
    return hour in settings['hours_utc']


def quest_bonus_items(quest_id):
    return dict(ACTIVE['story'].get(quest_id,{}).get('bonus_items',{}))


def guild_milestone_bonus(level):
    milestones=ACTIVE['guilds'].get('global',{}).get('milestones',[])
    return sum(row['bonus_percent'] for row in milestones if max(0,int(level))>=row['level'])


def help_text():
    return ('SOULBOUND OLC32 / 76–83: admin live edytuj KATEGORIA ID definicja | JSON; '
        'bez JSON pokazuje aktualne i DRAFT; auto usuwa. '
        'boss32 black_rabite -> {"phases":[{"below_hp":50,"interval":3,"damage_percent":150}]}; '
        'fach32 ID_RECEPTURY -> {"extra_output":2}; '
        'summon32 pajak -> {"combo_every":3,"combo_percent":150}; '
        'skill32 ID_SKILLA -> {"combo_every":3,"combo_percent":140}; '
        'event32 live_ID -> {"hours_utc":[8,9,10]}; '
        'fabula32 bandit_patrol -> {"bonus_items":{"iron_ore":2}}; '
        'gildia32 global -> {"milestones":[{"level":10,"bonus_percent":2}]}; '
        'swiat32 ID_POKOJU -> {"workshop_yield_percent":125}. '
        'pakiet32 | JSON atomowo grupuje osiem kategorii; sprawdz, porownaj, '
        'aktywuj POTWIERDZAM. Zmiany bez restartu, bez skryptów Python.')
