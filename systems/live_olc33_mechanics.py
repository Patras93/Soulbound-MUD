# -*- coding: utf-8 -*-
"""Soulbound v33: eight executable, bounded OLC mechanics.

Only typed JSON is accepted. Nothing runs arbitrary admin-supplied code.
All state is loaded from the existing versioned SQLite live-content payload.
"""
import copy
import json

CATEGORIES = ('uoss','professions','summons','skills','events','story','guilds','world')
ACTIVE = {name:{} for name in CATEGORIES}
ALIASES = {
    'boss33':'uoss','uoss33':'uoss',
    'fach33':'professions','profesja33':'professions',
    'summon33':'summons','przywolanie33':'summons',
    'skill33':'skills','magia33':'skills',
    'event33':'events','wydarzenie33':'events',
    'quest33':'story','fabula33':'story',
    'gildia33':'guilds','frakcja33':'guilds',
    'swiat33':'world','portal33':'world',
}


def _int(value, minimum, maximum, name):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'OLC33 {name}: liczba {minimum}–{maximum}.')


def validate(config, *, payload=None):
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from data.crafting_recipes import CRAFT_RECIPES
    from data.items import ITEMS
    from data.quests import QUESTS
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from core.classes_skills import CLASS_SKILLS
    from systems.live_olc26_world import event_catalog
    from systems.live_olc32_finale import CATEGORIES as OLDER_CATEGORIES
    if type(config) is not dict or set(config) != set(CATEGORIES) or set(OLDER_CATEGORIES) != set(CATEGORIES):
        raise ValueError('OLC33: nieprawidłowe osiem działów.')
    payload=payload or {}
    recipes=set(CRAFT_RECIPES)|set(payload.get('recipes',{}))
    items=set(ITEMS)|set(payload.get('items',{}))
    quests=set(QUESTS)|set(payload.get('quests',{}))
    rooms={**ROOMS,**payload.get('rooms',{})}
    skills={s['id'] for group in CLASS_SKILLS.values() for s in group}|set(payload.get('skills',{}))
    summons=set(SUMMONS)|set(payload.get('v29_rules',{}).get('summons',{}))
    events={row[0] for row in __import__('systems.world_events_v12812',fromlist=['EVENTS']).EVENTS}|set(event_catalog())
    mobs=set(MOB_TEMPLATES)|set(payload.get('mobs',{}))
    for category,entries in config.items():
        if type(entries) is not dict or len(entries)>300:
            raise ValueError('OLC33: maksymalnie 300 wpisów na dział.')
        for key,row in entries.items():
            if type(key) is not str or type(row) is not dict:
                raise ValueError('OLC33: identyfikator i definicja JSON wymagane.')
            if category=='uoss':
                if key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or set(row)!={'below_hp','every','restore_percent'}:
                    raise ValueError('boss33: UOSS, below_hp, every, restore_percent.')
                _int(row['below_hp'],1,99,'próg HP');_int(row['every'],2,30,'rytm leczenia')
                _int(row['restore_percent'],1,10,'procent leczenia')
            elif category=='professions':
                if key not in recipes or set(row)!={'byproduct','amount','every'} or row['byproduct'] not in items:
                    raise ValueError('fach33: receptura, byproduct (istniejący przedmiot), amount, every.')
                _int(row['amount'],1,10,'ilość produktu ubocznego');_int(row['every'],1,50,'rytm craftingu')
                # No output-as-input self multiplication, and no free tools.
                recipe={**CRAFT_RECIPES,**payload.get('recipes',{})}[key]
                if row['byproduct'] == recipe.get('output') or row['byproduct'] == key:
                    raise ValueError('Produkt uboczny nie może być głównym produktem.')
                item={**ITEMS,**payload.get('items',{})}[row['byproduct']]
                if item.get('type') not in ('resource','material','craft_material','gem_raw','archaeology_find'):
                    raise ValueError('Produkt uboczny musi być materiałem, nie narzędziem ani walutą.')
            elif category=='summons':
                if key not in summons or set(row)!={'heal_owner_percent','every'}:
                    raise ValueError('summon33: heal_owner_percent, every.')
                _int(row['heal_owner_percent'],1,5,'leczenie właściciela');_int(row['every'],2,30,'rytm pomocy')
            elif category=='skills':
                if key not in skills or set(row)!={'alternate_with','bonus_percent'} or row['alternate_with'] not in skills or key==row['alternate_with']:
                    raise ValueError('skill33: alternate_with (inny skill), bonus_percent.')
                _int(row['bonus_percent'],101,250,'premia kombinacji')
            elif category=='events':
                if key not in events or set(row)!={'guardian','count'} or row['guardian'] not in mobs:
                    raise ValueError('event33: guardian (istniejący mob), count.')
                _int(row['count'],1,3,'liczba strażników')
                # Keep event template as boss only; do not recursively spawn the event itself.
                if str(row['guardian']).startswith(('v12812_event_','v26_event_')):
                    raise ValueError('Strażnik nie może być bossem wydarzenia.')
            elif category=='story':
                if key not in quests or set(row)!={'guild_class','guild_rep'}:
                    raise ValueError('fabula33: guild_class, guild_rep.')
                from core.classes_skills import CLASSES
                known_classes={entry[0] for entry in CLASSES}
                if type(row['guild_class']) is not str or row['guild_class'] not in known_classes:
                    raise ValueError('Nieznana gildia klasowa; wpisz istniejącą klasę.')
                _int(row['guild_rep'],1,100,'reputacja gildii za quest')
            elif category=='guilds':
                if key!='global' or set(row)!={'boss_class_xp_percent'}:
                    raise ValueError('gildia33 global: boss_class_xp_percent.')
                _int(row['boss_class_xp_percent'],100,250,'bonus EXP klas za bossów')
            elif category=='world':
                if key not in rooms or set(row)!={'direction','destination'} or row['destination'] not in rooms:
                    raise ValueError('swiat33: pokój, direction, destination (istniejący pokój).')
                from systems.live_content_v1204 import DIRECTIONS
                if row['direction'] not in DIRECTIONS or key==row['destination']:
                    raise ValueError('Nieprawidłowy kierunek lub przejście do siebie.')
                exit_name=row['direction']
                current=rooms[key].get('exits',{}).get(exit_name)
                previous=ACTIVE['world'].get(key,{}).get('destination') if ACTIVE['world'].get(key,{}).get('direction')==exit_name else None
                if current is not None and current!=row['destination'] and current!=previous:
                    raise ValueError('Przejście jest zajęte; nie nadpisuję oryginalnego świata.')
    return True


def sync(config):
    for name in CATEGORIES:
        ACTIVE[name].clear()
        ACTIVE[name].update(copy.deepcopy(config[name]))


def stage(service,category,key,field,value):
    domain=ALIASES.get(category)
    if domain is None:return False
    if field!='definicja':raise ValueError('OLC33: użyj pola definicja.')
    draft=copy.deepcopy(service.draft)
    if str(value).strip().lower() in ('auto','automatyczny'):
        draft['v33_rules'][domain].pop(key,None)
    else:
        try:draft['v33_rules'][domain][key]=json.loads(value)
        except (ValueError,TypeError) as exc:raise ValueError('OLC33: niepoprawny JSON.') from exc
    service.validate(draft)
    service.draft=draft
    return True


def preview(service,category,key,field):
    domain=ALIASES.get(category)
    if domain is None:return None
    if field!='definicja':raise ValueError('OLC33: pole definicja.')
    current=service.active['v33_rules'][domain].get(key,'auto')
    staged=service.draft['v33_rules'][domain].get(key,'auto')
    return f'OLC33 {domain}/{key}. Obecnie {json.dumps(current,ensure_ascii=False)}. DRAFT {json.dumps(staged,ensure_ascii=False)}. Pole: definicja | JSON; auto cofa.'


def package(service,raw):
    try:spec=json.loads(raw)
    except (ValueError,TypeError) as exc:raise ValueError('Pakiet33: JSON.') from exc
    if type(spec) is not dict or not spec or set(spec)-set(CATEGORIES):
        raise ValueError('Pakiet33: osiem obsługiwanych kategorii.')
    draft=copy.deepcopy(service.draft)
    for category,entries in spec.items():
        if type(entries) is not dict:raise ValueError('Pakiet33: słownik ID -> definicja.')
        draft['v33_rules'][category].update(copy.deepcopy(entries))
    result=service.validate(draft)
    service.draft=draft
    return f'Pakiet33 DRAFT: {sum(map(len,spec.values()))} definicji. {result}'


def uoss_restore(mob,template):
    """Heal an authored UOSS in its active phase every N real attacks."""
    row=ACTIVE['uoss'].get(template.get('uoss_unique_superboss_key',''))
    if not row:return 0
    maximum=max(1,int(getattr(mob,'max_hp',0) or template.get('max_hp',1)))
    current=max(0,int(getattr(mob,'hp',0)))
    if current==0 or current>=maximum or current*100>maximum*row['below_hp']:
        return 0
    turns=int(getattr(mob,'_olc33_boss_turns',0))+1
    mob._olc33_boss_turns=turns
    if turns%row['every']:return 0
    restored=min(maximum-current,max(1,maximum*row['restore_percent']//100))
    mob.hp=current+restored
    return restored


def craft_byproduct(owner,recipe_id):
    """Return a (material, amount) on every Nth successful craft or None."""
    row=ACTIVE['professions'].get(recipe_id)
    if not row:return None
    counts=getattr(owner,'_olc33_craft_counts',None)
    if counts is None:counts={};owner._olc33_craft_counts=counts
    turn=counts.get(recipe_id,0)+1
    counts[recipe_id]=turn
    return (row['byproduct'],row['amount']) if turn%row['every']==0 else None


def summon_support(owner,summon_id):
    row=ACTIVE['summons'].get(summon_id)
    if not row or not getattr(owner,'current_hp',0):return 0
    counts=getattr(owner,'_olc33_summon_support',None)
    if counts is None:counts={};owner._olc33_summon_support=counts
    turn=counts.get(summon_id,0)+1
    counts[summon_id]=turn
    if turn%row['every']:return 0
    maximum=max(1,int(owner.max_hp()))
    missing=max(0,maximum-int(owner.current_hp))
    if not missing:return 0
    from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
    if superboss_healing_blocked_v11179(owner):return 0
    healed=min(missing,max(1,maximum*row['heal_owner_percent']//100))
    owner.current_hp+=healed
    return healed


def skill_alternation(owner,skill_id,multiplier):
    row=ACTIVE['skills'].get(skill_id)
    previous=getattr(owner,'_olc33_previous_skill',None)
    owner._olc33_previous_skill=skill_id
    return multiplier*row['bonus_percent']/100.0 if row and previous==row['alternate_with'] else multiplier


def event_guardians(slug):
    row=ACTIVE['events'].get(slug)
    return (row['guardian'],row['count']) if row else None


def spawn_guardians(event, room_id, mobs, templates, mob_factory):
    """Create ephemeral event companions once per slot; never create NPCs."""
    rule=event_guardians(event['slug'])
    if not rule:return 0
    template_id,count=rule
    if template_id not in templates:return 0
    created=0
    for idx in range(1,count+1):
        key=f"v12812:event:{event['slot']}:{event['slug']}:guardian:{idx}"
        if key in mobs:continue
        mob=mob_factory(
            key=key, room_id=str(room_id), template_id=template_id,
            hp=max(1,int(templates[template_id]['max_hp'])),
            home_room_id=str(room_id),next_wander_at=event['expires_at'])
        mob.v016_ephemeral=True
        mob.v029_expires_at=float(event['expires_at'])
        mobs[key]=mob
        created+=1
    return created


def quest_guild_reward(quest_id):
    return ACTIVE['story'].get(quest_id)


def guild_boss_class_xp(template,session,value):
    from core.mines_threat import v0866_is_boss_template
    if not v0866_is_boss_template(template) or template.get('uoss_unique_superboss_key'):
        return value
    row=ACTIVE['guilds'].get('global')
    if not row or not session.guild_row_v0926():return value
    return min(2**62,max(0,int(value))*row['boss_class_xp_percent']//100)


def world_portals():
    return ACTIVE['world']


def help_text():
    return ('OLC33: osiem nowych, wykonywalnych reguł. '
        'admin live edytuj boss33 black_rabite definicja | {"below_hp":35,"every":3,"restore_percent":2}; '
        'fach33 ID_RECEPTURY | {"byproduct":"iron_ore","amount":2,"every":3}; '
        'summon33 pajak | {"heal_owner_percent":2,"every":4}; '
        'skill33 ID_SKILLA | {"alternate_with":"ID_INNEGO_SKILLA","bonus_percent":130}; '
        'event33 basalt | {"guardian":"bandit","count":2}; '
        'fabula33 bandit_patrol | {"guild_class":"Wojownik","guild_rep":10}; '
        'gildia33 global | {"boss_class_xp_percent":125}; '
        'swiat33 ID_POKOJU | {"direction":"north","destination":"ID_CELU"}. '
        'Każda komenda ma pole definicja przed | JSON. '
        'admin live pakiet33 | JSON. Bez wartości pokazuje aktualne i DRAFT; auto usuwa. '
        'Sprawdz; porownaj; aktywuj POTWIERDZAM. Bez skryptów Python i bez restartu.')
