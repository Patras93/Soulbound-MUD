# -*- coding: utf-8 -*-
"""Soulbound 34.00.0 — OLC92–99, eight cross-system, data-only mechanics.

This module never runs Python supplied by an administrator. Published rules
are revisioned by LiveContentV1204. Empty rules preserve vanilla behavior.
"""
import copy
import json

CATEGORIES = ('uoss','professions','summons','skills','events','story','guilds','world')
ACTIVE = {name:{} for name in CATEGORIES}
ALIASES = {
    'boss34':'uoss','uoss34':'uoss',
    'fach34':'professions','profesja34':'professions',
    'summon34':'summons','przywolanie34':'summons',
    'skill34':'skills','magia34':'skills',
    'event34':'events','wydarzenie34':'events',
    'quest34':'story','fabula34':'story',
    'gildia34':'guilds','miasto34':'guilds',
    'swiat34':'world','portal34':'world',
}


def _number(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'OLC34 {name}: liczba calkowita {low}–{high}.')


def validate(rules,*,payload=None):
    from data.rooms import ROOMS
    from data.quests import QUESTS
    from data.items import ITEMS
    from data.mobs import MOB_TEMPLATES
    from data.crafting_recipes import CRAFT_RECIPES
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from core.classes_skills import CLASS_SKILLS
    from systems.live_olc26_world import event_catalog, FACTION_IDS
    from systems.live_content_v1204 import DIRECTIONS
    if type(rules) is not dict or set(rules)!=set(CATEGORIES):
        raise ValueError('OLC34: osiem wymaganych kategorii.')
    payload=payload or {}
    recipes={**CRAFT_RECIPES, **payload.get('recipes',{})}
    items={**ITEMS, **payload.get('items',{})}
    summons=set(SUMMONS)|set(payload.get('v29_rules',{}).get('summons',{}))
    skills={s['id'] for group in CLASS_SKILLS.values() for s in group}|set(payload.get('skills',{}))
    events={r[0] for r in __import__('systems.world_events_v12812',fromlist=['EVENTS']).EVENTS}|set(event_catalog())|set(payload.get('v26_rules',{}).get('events',{}))
    rooms={**ROOMS,**payload.get('rooms',{})}
    for category,entries in rules.items():
        if type(entries) is not dict or len(entries)>250:
            raise ValueError('OLC34: kategoria wymaga maksymalnie 250 wpisow.')
        for key,row in entries.items():
            if type(key) is not str or type(row) is not dict:
                raise ValueError('OLC34: ID i definicja JSON wymagane.')
            if category=='uoss':
                if key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or set(row)!={'every','stack_percent','max_stacks'}:
                    raise ValueError('Boss34: every, stack_percent, max_stacks.')
                _number(row['every'],1,20,'rytm');_number(row['stack_percent'],100,150,'wzmocnienie')
                _number(row['max_stacks'],1,10,'liczba ladunkow')
            elif category=='professions':
                if key not in recipes or set(row)!={'material','amount','every'} or row['material'] not in items:
                    raise ValueError('Fach34: znana receptura i material, amount, every.')
                item=items[row['material']]
                if item.get('type') not in ('resource','material','craft_material','gem_raw','archaeology_find'):
                    raise ValueError('Fach34: tylko material zasobowy, nie narzedzie ani pieniadze.')
                if row['material']==recipes[key].get('output'):
                    raise ValueError('Fach34: material nie moze byc produktem receptury.')
                _number(row['amount'],1,5,'ilosc materialu');_number(row['every'],2,50,'co ile craftow')
            elif category=='summons':
                if key not in summons or set(row)!={'below_hp','damage_percent'}:
                    raise ValueError('Summon34: below_hp, damage_percent.')
                _number(row['below_hp'],1,75,'prog HP');_number(row['damage_percent'],100,300,'obrazenia')
            elif category=='skills':
                if key not in skills or set(row)!={'after','bonus_percent'} or row['after'] not in skills or row['after']==key:
                    raise ValueError('Skill34: after (inny skill), bonus_percent.')
                _number(row['bonus_percent'],100,300,'premia kombinacji')
            elif category=='events':
                if key not in events or set(row)!={'reinforcement','count'} or row['reinforcement'] not in MOB_TEMPLATES:
                    raise ValueError('Event34: znane wydarzenie, reinforcement i count.')
                if str(row['reinforcement']).startswith(('v12812_event_','v26_event_')):
                    raise ValueError('Event34: boss eventu nie moze byc straznikiem.')
                _number(row['count'],1,5,'liczba posilkow')
            elif category=='story':
                if key not in QUESTS and key not in payload.get('quests',{}):
                    raise ValueError('Fabula34: quest nie istnieje.')
                if set(row)!={'faction','reputation'} or row['faction'] not in FACTION_IDS:
                    raise ValueError('Fabula34: faction oraz reputation istniejącej frakcji.')
                _number(row['reputation'],1,100,'reputacja')
            elif category=='guilds':
                if key!='global' or set(row)!={'treasury_bonus_percent'}:
                    raise ValueError('Gildia34 global: treasury_bonus_percent.')
                _number(row['treasury_bonus_percent'],100,300,'premia skarbca')
            elif category=='world':
                if key not in rooms or set(row)!={'direction','destination','return_direction'} or row['destination'] not in rooms or key==row['destination']:
                    raise ValueError('Swiat34: znany pokoj, direction, destination, return_direction.')
                if row['direction'] not in DIRECTIONS or row['return_direction'] not in DIRECTIONS:
                    raise ValueError('Swiat34: nieprawidlowy kierunek.')
                # Check both ends against the world BEFORE applying this revision.
                # Reusing the current OLC34 exit for updates/undo is allowed.
                for origin,direction,dest in ((key,row['direction'],row['destination']),
                                              (row['destination'],row['return_direction'],key)):
                    existing=rooms[origin].get('exits',{}).get(direction)
                    prior=ACTIVE['world'].get(origin)
                    previous_dest=prior.get('destination') if prior and prior['direction']==direction else None
                    for old_origin,old in ACTIVE['world'].items():
                        if old['destination']==origin and old['return_direction']==direction:
                            previous_dest=old_origin
                    if existing is not None and existing!=dest and existing!=previous_dest:
                        raise ValueError('Swiat34: wyjscie zajete przez istniejacy swiat.')
                # An OLC33 one-way route staged in the same publication must
                # never be silently overwritten by an OLC34 two-way route.
                for older_origin,older in payload.get('v33_rules',{}).get('world',{}).items():
                    for new_origin,new_direction,new_destination in (
                        (key,row['direction'],row['destination']),
                        (row['destination'],row['return_direction'],key)):
                        if older_origin==new_origin and older['direction']==new_direction:
                            raise ValueError('Swiat34: kolizja przejscia z OLC33.')
                for link in payload.get('links',[]):
                    if len(link)==3:
                        for new_origin,new_direction,new_destination in (
                            (key,row['direction'],row['destination']),
                            (row['destination'],row['return_direction'],key)):
                            if link[0]==new_origin and link[1]==new_direction:
                                raise ValueError('Swiat34: kolizja z przejsciem OLC.')
                # A staged set cannot put two portals on the same direction.
                for other,route in rules['world'].items():
                    if other==key:continue
                    if (other,route.get('direction'))==(row['destination'],row['return_direction']) or \
                       (route.get('destination'),route.get('return_direction'))==(key,row['direction']):
                        raise ValueError('Swiat34: kolizja dwukierunkowych przejsc.')
    return True


def sync(rules):
    for domain in CATEGORIES:
        ACTIVE[domain].clear()
        ACTIVE[domain].update(copy.deepcopy(rules[domain]))


def stage(service,category,key,field,value):
    domain=ALIASES.get(category)
    if domain is None:return False
    if field!='definicja':raise ValueError('OLC34: pole definicja.')
    draft=copy.deepcopy(service.draft)
    if str(value).strip().casefold() in ('auto','automatyczny'):
        draft['v34_rules'][domain].pop(key,None)
    else:
        try: draft['v34_rules'][domain][key]=json.loads(value)
        except (ValueError,TypeError) as exc:raise ValueError('OLC34: bledny JSON.') from exc
    service.validate(draft)
    service.draft=draft
    return True


def preview(service,category,key,field):
    domain=ALIASES.get(category)
    if domain is None:return None
    if field!='definicja':raise ValueError('OLC34: tylko pole definicja.')
    before=service.active['v34_rules'][domain].get(key,'auto')
    after=service.draft['v34_rules'][domain].get(key,'auto')
    return (f'OLC34 {domain}/{key}. Obecnie: {json.dumps(before,ensure_ascii=False)}. '
            f'DRAFT: {json.dumps(after,ensure_ascii=False)}. Wpisz definicja | JSON lub auto.')


def package(service,raw):
    try: spec=json.loads(raw)
    except (ValueError,TypeError) as exc:raise ValueError('Pakiet34: niepoprawny JSON.') from exc
    if type(spec) is not dict or not spec or set(spec)-set(CATEGORIES):
        raise ValueError('Pakiet34: slownik maksymalnie osmiu kategorii.')
    draft=copy.deepcopy(service.draft)
    for domain,entries in spec.items():
        if type(entries) is not dict:raise ValueError('Pakiet34: slownik ID -> definicja.')
        draft['v34_rules'][domain].update(copy.deepcopy(entries))
    service.validate(draft)
    service.draft=draft
    return f'Pakiet34 DRAFT: {sum(len(v) for v in spec.values())} reguł, walidacja PASS.'


def boss_pressure(mob,template):
    row=ACTIVE['uoss'].get(template.get('uoss_unique_superboss_key',''))
    if not row or int(getattr(mob,'hp',0))<=0:return 1.0
    count=int(getattr(mob,'_olc34_attacks',0))+1
    mob._olc34_attacks=count
    stacks=min(row['max_stacks'],count//row['every'])
    return (row['stack_percent']/100.0)**stacks


def profession_find(owner,recipe_id):
    """Deterministic exploration material after N successful recipes."""
    row=ACTIVE['professions'].get(recipe_id)
    if not row:return None
    counts=getattr(owner,'_olc34_craft_counts',None)
    if counts is None:counts={};owner._olc34_craft_counts=counts
    count=counts.get(recipe_id,0)+1
    counts[recipe_id]=count
    if count%row['every']==0:return row['material'],row['amount']
    return None


def summon_finisher(summon_id,mob,damage):
    row=ACTIVE['summons'].get(summon_id)
    if not row or int(getattr(mob,'hp',0))<=0:return damage
    maximum=max(1,int(getattr(mob,'max_hp',0)))
    if 100*int(mob.hp)>maximum*row['below_hp']:return damage
    return max(1,int(damage)*row['damage_percent']//100)


def skill_chain(owner,skill_id,multiplier):
    row=ACTIVE['skills'].get(skill_id)
    previous=getattr(owner,'_olc34_last_skill',None)
    owner._olc34_last_skill=skill_id
    if row and previous==row['after']:
        return multiplier*row['bonus_percent']/100.0
    return multiplier


def spawn_reinforcements(event,room_id,mobs,templates,mob_factory):
    row=ACTIVE['events'].get(event['slug'])
    if not row or row['reinforcement'] not in templates:return 0
    count=0
    for number in range(1,row['count']+1):
        key=f"v12812:event:{event['slot']}:{event['slug']}:v34:{number}"
        if key in mobs:continue
        state=mob_factory(key=key,room_id=str(room_id),template_id=row['reinforcement'],
            hp=max(1,int(templates[row['reinforcement']]['max_hp'])),
            home_room_id=str(room_id),next_wander_at=event['expires_at'])
        state.v016_ephemeral=True
        state.v029_expires_at=float(event['expires_at'])
        mobs[key]=state
        count+=1
    return count


def quest_faction_reward(quest_id):
    return ACTIVE['story'].get(quest_id)


def guild_treasury_reward(base):
    row=ACTIVE['guilds'].get('global')
    return int(base)*row['treasury_bonus_percent']//100 if row else base


def two_way_portals():
    for origin,row in ACTIVE['world'].items():
        yield origin,row['direction'],row['destination']
        yield row['destination'],row['return_direction'],origin


def help_text():
    return ('OLC v34 / 92-99: 8 integracji. Uzyj admin live edytuj KATEGORIA ID definicja | JSON, '
            'a przed edycja podglad: admin live edytuj KATEGORIA ID definicja. '
            'boss34: {"every":2,"stack_percent":110,"max_stacks":4}; '
            'fach34: {"material":"iron_ore","amount":1,"every":3}; '
            'summon34: {"below_hp":35,"damage_percent":150}; '
            'skill34: {"after":"ID_INNEGO_SKILLA","bonus_percent":150}; '
            'event34: {"reinforcement":"bandit","count":2}; '
            'fabula34: {"faction":"miners","reputation":20}; '
            'gildia34 global: {"treasury_bonus_percent":125}; '
            'swiat34: {"direction":"north","destination":"ID_POKOJU",'
            '"return_direction":"south"}. admin live pakiet34 | JSON. '
            'sprawdz, porownaj, aktywuj POTWIERDZAM. Auto cofa. '
            'Domyslne ustawienia sa neutralne. Zmiany kodu silnika nadal wymagaja wdrozenia.')
