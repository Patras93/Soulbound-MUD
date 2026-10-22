# -*- coding: utf-8 -*-
"""Soulbound v29 / OLC 68-75 — authored data, not executable scripts.

Published records are installed in place and reverted on revision rollback.
New summon types are genuine summon catalog entries with MP, class and combat scaling.
"""
import copy
import json
import re

CATEGORIES = ('bosses','professions','summons','skills','events','story','guilds','world')
EMPTY = {key:{} for key in CATEGORIES}
ACTIVE = copy.deepcopy(EMPTY)
ALIASES = {
    'boss29':'bosses','uoss29':'bosses',
    'fach29':'professions','praca29':'professions',
    'summon29':'summons','przywolany29':'summons',
    'skill29':'skills','magia29':'skills',
    'event29':'events','wydarzenie29':'events',
    'fabula29':'story','wybor29':'story',
    'gildia29':'guilds','frakcja29':'guilds',
    'swiat29':'world','ekonomia29':'world',
}
CUSTOM = re.compile(r'^live_[a-z0-9_]{3,45}$')


def _int(value,lo,hi,desc):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{desc}: wymagana liczba całkowita {lo}–{hi}.')


def _name(value,desc,maximum=90):
    if type(value) is not str or not 1<=len(value.strip())<=maximum or any(ord(c)<32 for c in value):
        raise ValueError(f'{desc}: tekst 1–{maximum} znaków bez znaków sterujących.')


def validate(config, *, payload=None):
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES
    from data.rooms import ROOMS
    from data.quests import QUESTS
    from data.crafting_recipes import CRAFT_RECIPES
    if type(config) is not dict or set(config)!=set(CATEGORIES):
        raise ValueError('OLC29: osiem wymaganych sekcji.')
    payload = payload or {}
    new_rooms = payload.get('rooms',{})
    new_quests = payload.get('quests',{})
    new_recipes = payload.get('recipes',{})
    new_prof = payload.get('v24_rules',{}).get('professions',{})
    custom_events = payload.get('v26_rules',{}).get('events',{})
    for category,rows in config.items():
        if type(rows) is not dict or len(rows)>100:
            raise ValueError(f'OLC29 {category}: maksymalnie 100 rekordów.')
    for key,row in config['bosses'].items():
        if (key not in UOSS_SUPERBOSS_ENCOUNTERS_V11134 or type(row) is not dict or
                not {'cycle','extra_damage_percent'} <= set(row) or
                set(row)-{'cycle','extra_damage_percent','phase_threshold_percent','phase_damage_percent'}):
            raise ValueError('OLC30 boss: cycle i extra_damage_percent wymagane, opcjonalnie phase_threshold_percent i phase_damage_percent.')
        _int(row['cycle'],2,20,'Rytm bossa');_int(row['extra_damage_percent'],100,500,'Impuls bossa')
        if ('phase_threshold_percent' in row) != ('phase_damage_percent' in row):
            raise ValueError('OLC30 boss: podaj obie wartości progu i siły fazy.')
        if 'phase_threshold_percent' in row:
            _int(row['phase_threshold_percent'],1,99,'Próg fazy HP')
            _int(row['phase_damage_percent'],100,500,'Wzmocnienie fazy')
    for key,row in config['professions'].items():
        if not CUSTOM.fullmatch(key) or key not in set(CRAFT_RECIPES)|set(new_recipes) or type(row) is not dict or set(row)!={'label'}:
            raise ValueError('OLC29 fach: wymagany istniejący przepis live_ i etykieta pracy.')
        _name(row['label'],'Etykieta czynności')
    for key,row in config['summons'].items():
        if not CUSTOM.fullmatch(key) or (key in SUMMONS and key not in ACTIVE['summons']):
            raise ValueError('OLC29 summon: wolne ID live_ wymagane.')
        if (type(row) is not dict or not {'name','class','mana','kind','power','materials'} <= set(row)
                or set(row)-{'name','class','mana','kind','power','materials','hp_percent','attack_percent'}):
            raise ValueError('OLC30 summon: name,class,mana,kind,power,materials; opcjonalnie hp_percent,attack_percent.')
        _name(row['name'],'Nazwa przywołania')
        if row['class'] not in ('Mag','Druid','Nekromanta') or row['kind'] not in ('physical','magic'):
            raise ValueError('OLC29: dozwolone klasy Mag, Druid, Nekromanta; typ physical/magic.')
        _int(row['mana'],1,1000000,'Mana');_int(row['power'],10,300,'Siła procent')
        if 'hp_percent' in row: _int(row['hp_percent'],100,500,'HP przywołania')
        if 'attack_percent' in row: _int(row['attack_percent'],100,500,'Siła ataku przywołania')
        materials=row['materials']
        if type(materials) is not dict or len(materials)>5:
            raise ValueError('Summon: maksymalnie pięć materiałów.')
        from data.items import ITEMS
        item_ids=set(ITEMS)|set(payload.get('items',{}))
        for mat,qty in materials.items():
            if mat not in item_ids:raise ValueError('Summon: materiał nie istnieje: '+str(mat))
            _int(qty,1,1000,'Ilość materiału')
    from core.classes_skills import CLASS_SKILLS
    skill_ids={row['id'] for group in CLASS_SKILLS.values() for row in group}|set(payload.get('skills',{}))
    for key,row in config['skills'].items():
        if key not in skill_ids or type(row) is not dict or set(row)!={'name'}:
            raise ValueError('OLC29 skill: wymagany istniejący skill i nazwa techniki.')
        _name(row['name'],'Nazwa kombinacji')
    for key,row in config['events'].items():
        if key not in custom_events or type(row) is not dict or set(row)!={'arena'} or row['arena'] not in set(ROOMS)|set(new_rooms):
            raise ValueError('OLC29 event: istniejący event26 i istniejący pokój/arena.')
    quest_ids=set(QUESTS)|set(new_quests)
    for key,row in config['story'].items():
        if (key not in quest_ids or type(row) is not dict or 'text' not in row
                or set(row)-{'text','ending'}):
            raise ValueError('OLC30 fabuła: ID questa, tekst wyboru, opcjonalne ending.')
        _name(row['text'],'Tekst decyzji fabularnej',300)
        if 'ending' in row: _name(row['ending'],'Alternatywne zakonczenie',450)
    for key,row in config['guilds'].items():
        if key!='global' or type(row) is not dict or set(row)!={'level_step','bonus_per_step','maximum_bonus'}:
            raise ValueError('OLC29 gildia: global, level_step, bonus_per_step, maximum_bonus.')
        _int(row['level_step'],1,100,'Co ile poziomów');_int(row['bonus_per_step'],0,10,'Premia na próg')
        _int(row['maximum_bonus'],0,100,'Maksymalna premia')
    for key,row in config['world'].items():
        if key not in set(ROOMS)|set(new_rooms) or type(row) is not dict or set(row)!={'buy_percent','sell_percent'}:
            raise ValueError('OLC29 ekonomia: pokój + buy_percent,sell_percent.')
        _int(row['buy_percent'],25,500,'Cena zakupu');_int(row['sell_percent'],25,500,'Cena sprzedaży')
    return True


def stage(service, category, key, field, raw):
    domain=ALIASES.get(category)
    if not domain:return False
    if field!='definicja':raise ValueError('OLC29: użyj pola definicja z JSON lub auto.')
    staged=copy.deepcopy(service.draft)
    if str(raw).strip().casefold() in ('auto','automatyczny'):
        staged['v29_rules'][domain].pop(key,None)
    else:
        try:staged['v29_rules'][domain][key]=json.loads(raw)
        except (TypeError,ValueError) as exc:raise ValueError('OLC29: wymagany poprawny obiekt JSON.') from exc
    service.validate(staged)
    service.draft=staged
    return True


def preview(service,category,key,field):
    domain=ALIASES.get(category)
    if not domain:return None
    if field!='definicja':raise ValueError('OLC29: pole definicja.')
    active=service.active['v29_rules'][domain].get(key,'auto')
    draft=service.draft['v29_rules'][domain].get(key,'auto')
    return (f'OLC29 {domain}/{key} — aktywne: {json.dumps(active,ensure_ascii=False)}; '
            f'DRAFT: {json.dumps(draft,ensure_ascii=False)}. '
            f'admin live edytuj {category} {key} definicja | JSON; auto cofa.')


def sync(config):
    for name in CATEGORIES:
        ACTIVE[name].clear();ACTIVE[name].update(copy.deepcopy(config[name]))


def boss_pulse_factor(mob, template):
    key=template.get('uoss_unique_superboss_key','')
    row=ACTIVE['bosses'].get(key)
    if not row:return 1.0
    counter=getattr(mob,'_olc29_attack_turn',0)+1
    mob._olc29_attack_turn=counter
    pulse = row['extra_damage_percent']/100.0 if counter%row['cycle']==0 else 1.0
    if 'phase_threshold_percent' in row:
        hp = max(0, int(getattr(mob, 'hp', getattr(mob, 'current_hp', 0)) or 0))
        maximum = max(1, int(getattr(mob, 'max_hp', 0) or template.get('max_hp',1)))
        if hp*100 <= maximum*row['phase_threshold_percent']:
            pulse *= row['phase_damage_percent']/100.0
    return pulse


def authored_arena(slug,default):
    return ACTIVE['events'].get(slug,{}).get('arena',default)


def quest_choice_text(quest_id):
    return ACTIVE['story'].get(quest_id,{}).get('text','')


def quest_ending_text(quest_id):
    # OLC30: zakończenie zależy od wybranego questa, nie od kodu Python.
    return ACTIVE['story'].get(quest_id,{}).get('ending','')


def guild_level_bonus(level):
    spec=ACTIVE['guilds'].get('global')
    if not spec:return 0
    return min(spec['maximum_bonus'],max(0,int(level))//spec['level_step']*spec['bonus_per_step'])


def trade_price(room_id,value,action):
    row=ACTIVE['world'].get(room_id,{})
    field='buy_percent' if action=='buy' else 'sell_percent'
    return max(0,int(value))*row.get(field,100)//100


def help_text():
    return ('OLC68–75 / v29. Edytuj: admin live edytuj KATEGORIA ID definicja | JSON, '
            'bez | JSON odczyt obecnej wartości; auto usuwa. '
            'boss29: UOSS -> {"cycle":3,"extra_damage_percent":180,"phase_threshold_percent":25,"phase_damage_percent":160}; '
            'fach29: ID istniejącej nowej receptury -> {"label":"Nowa czynność"}; '
            'summon29: live_ID -> {"name":"Widmowy Wilk","class":"Druid","mana":100,"kind":"physical","power":80,"materials":{},"hp_percent":150,"attack_percent":120}; '
            'skill29: ID istniejącego skilla -> {"name":"Technika"}; '
            'event29: live_ID istniejącego event26 -> {"arena":"live_id_pokoju"}; '
            'fabula29: ID questa -> {"text":"Tekst decyzji","ending":"Alternatywne zakonczenie"}; '
            'gildia29 global -> {"level_step":10,"bonus_per_step":1,"maximum_bonus":50}; '
            'swiat29 ID_pokoju -> {"buy_percent":110,"sell_percent":95}. '
            'Tworzenie bossów, profesji i skilli pozostaje w komendach nowymob/pakietfach/pakietskilli. '
            'pakiet29 | JSON scala osiem obszarów, story._groups tworzy wzajemnie wykluczające wybory questów. '
            'Sprawdz, porownaj, aktywuj POTWIERDZAM, auto. Zmiany w SQLite bez skryptów Python.')


def package(service,raw):
    """Atomically stage eight types of authored content in the existing OLC draft.

    Existing schema validators protect every referenced item, room, class and quest.
    Calling this never publishes; only an explicit admin live aktywuj publishes.
    """
    from systems.live_olc25_workflows import profession_package, bundle_new_skills
    try: spec=json.loads(raw)
    except (ValueError,TypeError) as exc:raise ValueError('pakiet29: obiekt JSON.') from exc
    if type(spec) is not dict or not spec or set(spec)-set(CATEGORIES):
        raise ValueError('pakiet29: tylko bosses,professions,summons,skills,events,story,guilds,world.')
    backup=copy.deepcopy(service.draft)
    total=0
    try:
        # First create the arena and boss using the existing real registries.
        for row in spec.get('bosses',[]):
            if type(row) is not dict or set(row)!={'id','name','level','hp','damage','exp','room'}:
                raise ValueError('Boss: id,name,level,hp,damage,exp,room.')
            service.stage_mob(row['id'],row['name'],int(row['level']),int(row['hp']),int(row['damage']),int(row['exp']))
            service.stage_spawn(row['room'],row['id'])
            total+=1
        for row in spec.get('professions',[]):
            if type(row) is not list or len(row)!=16 or any(type(x) not in (str,int) for x in row):
                raise ValueError('Profesja: lista 16 pól nowafach + fachreceptura.')
            profession_package(service,' | '.join(map(str,row)));total+=1
        if spec.get('skills'):
            bundle_new_skills(service,json.dumps(spec['skills'],ensure_ascii=False))
            total+=len(spec['skills'])
        for row in spec.get('events',[]):
            if type(row) is not dict or set(row)!={'id','definition','arena'}:
                raise ValueError('Event: id,definition,arena.')
            service.stage_edit('event26',row['id'],'definicja',json.dumps(row['definition'],ensure_ascii=False))
            service.stage_edit('event29',row['id'],'definicja',json.dumps({'arena':row['arena']},ensure_ascii=False))
            total+=1
        storyline=spec.get('story',{})
        if type(storyline) is not dict:
            raise ValueError('Fabuła: mapa quest_id -> {text}, opcjonalnie _groups.')
        for group, quest_ids in storyline.get('_groups',{}).items():
            service.stage_edit('wybor26',group,'questy',json.dumps(quest_ids,ensure_ascii=False));total+=1
        for quest,row in storyline.items():
            if quest=='_groups':continue
            service.stage_edit('fabula29',quest,'definicja',json.dumps(row,ensure_ascii=False));total+=1
        for ident,row in spec.get('summons',{}).items():
            service.stage_edit('summon29',ident,'definicja',json.dumps(row,ensure_ascii=False));total+=1
        for ident,row in spec.get('guilds',{}).items():
            service.stage_edit('gildia29',ident,'definicja',json.dumps(row,ensure_ascii=False));total+=1
        for ident,row in spec.get('world',{}).items():
            service.stage_edit('swiat29',ident,'definicja',json.dumps(row,ensure_ascii=False));total+=1
        service.validate(service.draft)
    except Exception:
        service.draft=backup
        raise
    return f'OLC29: przygotowano {total} elementów (DRAFT). Użyj sprawdz, porownaj, aktywuj POTWIERDZAM.'
