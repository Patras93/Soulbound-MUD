# -*- coding: utf-8 -*-
"""Soulbound v4.00.0 — Imperium Pradawnych Legend.

Additive narrative regions, ocean passages, bosses, quests and true craft recipes.
Uses ONLY existing tool types/roles and existing quest/combat/ocean engines.
No player-database migration, no destructive world update, no new tool item.
"""
from __future__ import annotations

from world.legends_v3200 import _join, _new, _reachable, _anchors, OLD_ARCS, _room, _npc, _mob, _quest
from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
from systems.mastery_crafting_v2201 import TOOL_TYPES
from data.crafting_recipes import CRAFT_RECIPES

# Stable, descriptive identities: no numbered display names for players.
SEA_ROUTES = (
    ('widm','Morze Widm','v2200_row_1','Kapitan Bladych Żagli','Sól Zatopionej Pamięci','dark',510),
    ('lewiatanow','Cieśnina Lewiatanów','v2200_row_2','Strażniczka Siedmiu Prądów','Łuska Pierwszego Lewiatana','water',600),
    ('koron','Imperium Zatopionych Królów','v2200_stolica_2','Marszałek Koron Głębin','Pieczęć Morskiego Tronu','arcane',650),
    ('raf','Labirynt Bursztynowych Raf','v2200_rafy_1','Wiedźma Rafowych Zwierciadeł','Bursztyn Szeptów','poison',500),
    ('sztormow','Szlak Dziewięciu Sztormów','v2200_burze_1','Admirał Ostatniej Burzy','Kryształ Dziewiątego Sztormu','lightning',740),
)
PRADAWNI = (
    ('Król Koron bez Dziedzica','dark','holy','Korona Króla Wygnańców'),
    ('Arcykapłanka Pustego Słońca','holy','fire','Zgaszona Korona Słońca'),
    ('Tkacz Niekończącej Się Nocy','dark','arcane','Nić Nocy Pierwotnej'),
    ('Strażniczka Pradawnych Run','arcane','earth','Matryca Pradawnych Run'),
    ('Cesarz Kryształowych Burz','lightning','ice','Sercokrystal Burz'),
    ('Władczyni Milczącego Boru','poison','earth','Nasiono Pierwszego Lasu'),
    ('Herold Lodowego Sądu','ice','holy','Lodowa Pieczęć Sądu'),
    ('Generał Spopielonego Horyzontu','fire','physical','Sztandar Ostatniej Bitwy'),
    ('Pan Echa Podziemnych Tronów','earth','dark','Klejnot Echa Tronów'),
    ('Królowa Bezgwiezdnego Oceanu','water','dark','Gwiazda Zatopionych Mórz'),
    ('Władca Pięciu Pękniętych Pieczęci','arcane','lightning','Okruch Pięciu Pieczęci'),
    ('Ostatni Strażnik Korony Dusz','holy','dark','Rdzeń Korony Dusz'),
)
CHAPTERS = (
    'Przebudzenie świadków','Zapomniane przymierze','Cienie dawnych królestw',
    'Zew otchłani','Sztorm przeznaczenia','Władcy legend','Korona Dusz',
)
SEA_ROOMS = ('Nabrzeże Ocalonych','Przesmyk Map','Przystań Rozbitków',
             'Archiwum Nawigatorów','Prąd Zapomnienia','Bastion Fal',
             'Brama Admirała','Komnata Flagowego Okrętu')
CRAFT_STAGES = (1, 30, 100, 250, 500)
PROF_STAGES = (1, 5, 15, 40, 90, 180, 350, 700)


def _safe_add_room(rooms, rid, name, zone, desc, level):
    _room(rooms,rid,name,zone,desc,level)
    rooms[rid]['v4000_imperium']=True


def _add_quest(quests, qid, title, giver, kind, target, needed, narrative, level, previous=None, repeatable=False, profession=None, npc_id=None):
    _quest(quests, qid, title, giver, kind, target, needed, narrative, level,
           requires=previous, repeatable=repeatable, profession=profession, target_npc=npc_id)
    quests[qid]['v4000_imperium']=True
    return qid


def _record_material(items,key,name,description,value=85000,quest_only=False):
    _new(items,key,{'name':name,'type':'quest' if quest_only else 'resource',
                    'price':None,'sell_silver':value,'desc':description,'v4000_imperium':True})


def install(rooms,npcs,mobs,spawns,quests,items,help_topics,help_aliases,navy):
    """Register side branches before NPC single-room conversion; return real counts."""
    from systems.professions import V03053_CRAFT_RECIPES
    start=(len(rooms),len(npcs),len(mobs),len(spawns),len(quests),len(items),len(CRAFT_RECIPES),len(V03053_CRAFT_RECIPES))

    # 32 regional story arcs reach pre-existing zones, not only the new continent.
    anchors=_anchors(rooms)
    if len(anchors)!=len(OLD_ARCS):
        raise AssertionError('v4.00.0 requires 32 existing-world anchors')
    for i,(zone,anchor) in enumerate(anchors):
        arc_name, backstory, witness=OLD_ARCS[i]
        slug=f'v4000_old_{i:02d}'
        stage=max(10,min(600,int(rooms[anchor].get('recommended_mastery') or rooms[anchor].get('generator_level') or 25)))
        names=('Posterunek Świadków','Ślady Przymierza','Próg Sprawiedliwości','Archiwum Korony')
        path=[]
        for step,label in enumerate(names):
            rid=f'{slug}_r{step}'
            _safe_add_room(rooms,rid,f'{arc_name} — {label}',zone,
                     f'{backstory} Część {step+1} historii. Bez pułapek i bez nowej blokady poziomu.',stage+step*8)
            path.append(rid)
            if step: _join(rooms,path[step-1],rid)
        _join(rooms,anchor,path[0])
        npc_id=f'{slug}_n'; person=f'Kronikarz Korony {witness}'
        guard=f'{slug}_guardian'; proof=f'{slug}_proof'
        _mob(mobs,guard,f'Strażnik {arc_name}',stage+20,'dark')
        mobs[guard]['rank']='elite';mobs[guard]['fame_target']=True
        spawns.extend(((path[2],guard),(path[3],guard)))
        _record_material(items,proof,f'{arc_name} — Fragment Prawdy',backstory,quest_only=True)
        mobs[guard]['drops']={proof:1.0,'soul_shard':.75}
        tasks=(('Świadectwo', 'talk_npc',npc_id,1,'Wysłuchaj wersji ocalonych u kronikarza.'),
               ('Przerwany konwój','kill',guard,4,'Pokonaj strażników traktu po przyjęciu zadania.'),
               ('Ślad pieczęci','collect',proof,2,'Zbierz dwa dowody z pokonanych strażników.'),
               ('Ostatnia zasadzka','kill',guard,6,'Powstrzymaj ostatni oddział nieprzyjaciół.'),
               ('Prawda zapisana','talk_npc',npc_id,1,'Wróć z odkryciami do kronikarza.'))
        chain=[];last=None
        for k,(title,kind,target,amount,detail) in enumerate(tasks,1):
            q=f'{slug}_q{k}'
            _add_quest(quests,q,f'{arc_name}: {title}',person,kind,target,amount,
                 f'{backstory} {detail} Rozdział Kronik: {CHAPTERS[min(6,i//5)]}.',stage+k*12,last,npc_id=npc_id if kind=='talk_npc' else None)
            chain.append(q);last=q
        _npc(npcs,npc_id,person,path[0],f'{backstory} Opowiadam historię tej ziemi.',chain)

    # Ocean 5.0: FIVE playable routes, existing ships and real registered fleet enemies.
    ocean_materials=[]
    for idx,(slug,zone,origin,captain,material,element,level) in enumerate(SEA_ROUTES):
        prefix=f'v4000_sea_{slug}'
        relic=f'{prefix}_material'; ocean_materials.append(relic)
        _record_material(items,relic,material,f'Rzadki łup morskiej wyprawy przez {zone}.',level*180)
        passage=[]
        for r,label in enumerate(SEA_ROOMS):
            rid=f'{prefix}_r{r}'
            _safe_add_room(rooms,rid,f'{label} — {zone}',zone,
               f'{zone}. {label}. Z zachodniej przystani przejdziesz do kolejnej komnaty. Bez pułapek.',level+r*9)
            passage.append(rid)
            if r: _join(rooms,passage[r-1],rid)
        _join(rooms,origin,passage[0])
        npc_id=f'{prefix}_navigator'; guide=f'Nawigator {zone}'
        mob=f'{prefix}_corsair'; boss=f'{prefix}_admiral'
        _mob(mobs,mob,f'Korsarz {zone}',level,element)
        mobs[mob]['rank']='elite';mobs[mob]['fame_target']=True
        mobs[mob]['drops']={relic:.28,'soul_shard':.7}
        spawns.extend(((passage[3],mob),(passage[5],mob)))
        _mob(mobs,boss,captain,level+145,element,True,drop=relic)
        mobs[boss]['fame_target']=True
        mobs[boss]['attack_elements_v11339']=(element,'dark' if element!='dark' else 'lightning')
        spawns.append((passage[7],boss))
        tasks=(('Sygnał z portu','talk_npc',npc_id,1),('Pierwszy zwiad','kill',mob,4),
               ('Zaginiony ładunek','collect',relic,2),('Przełamana blokada','kill',mob,7),
               ('Znak admiralski','kill',boss,1),('Ocalała załoga','talk_npc',npc_id,1),
               ('Kronika morskich zwycięstw','kill',boss,1))
        chain=[];previous=None
        for j,(title,kind,target,amount) in enumerate(tasks,1):
            q=f'{prefix}_q{j}'
            _add_quest(quests,q,f'{zone}: {title}',guide,kind,target,amount,
                f'{zone}. {title}. Pokonaj prawdziwych przeciwników lub porozmawiaj z nawigatorem.',
                level+j*10,previous,repeatable=(j==7),npc_id=npc_id if kind=='talk_npc' else None)
            previous=q;chain.append(q)
        _npc(npcs,npc_id,guide,passage[0],f'Prowadzę wyprawy przez {zone}. Ocal marynarzy i przełam blokadę.',chain)
        fleet=f'imperium_{slug}'
        if fleet in navy.ENEMIES:raise AssertionError(f'v4 ocean fleet collision: {fleet}')
        navy.ENEMIES[fleet]=(f'Armada: {zone}',level*9000,level*180,level*2750,'siege',level*700)
        navy.MATERIALS[fleet]=relic

    # 12 distinct multi-phase superbosses, each in a four-room accessible side wing.
    for i,(name,primary,secondary,artifact) in enumerate(PRADAWNI):
        slug=f'v4000_ancient_{i:02d}'
        region=anchors[(i*3)%len(anchors)][0]
        origin=f'v4000_old_{(i*3)%32:02d}_r2'
        stage=310+i*55
        path=[]
        for j,label in enumerate(('Przedsionek Pradawnych','Komnata Zapisów','Strażnica Ostatniej Próby','Tron Legend')):
            rid=f'{slug}_r{j}'
            _safe_add_room(rooms,rid,f'{label} — {name}',region,
                f'Ślad {artifact}. {name} broni tej świątyni. Ostrzeżenia faz walki są jawne. Bez pułapek.',stage+j*12)
            path.append(rid)
            if j:_join(rooms,path[j-1],rid)
        _join(rooms,origin,path[0])
        npc_id=f'{slug}_chronicler';mentor=f'Strażnik Kronik {name}'
        sentry=f'{slug}_sentry';boss=f'{slug}_boss';relic=f'{slug}_relic'
        _record_material(items,relic,artifact,f'Pamiątka po przeciwniku: {name}.',stage*220)
        _mob(mobs,sentry,f'Herold {name}',stage,primary)
        mobs[sentry]['fame_target']=True
        mobs[sentry]['drops']={relic:.20,'soul_shard':.8}
        spawns.append((path[2],sentry))
        _mob(mobs,boss,name,stage+130,primary,True,drop=relic)
        mobs[boss]['attack_elements_v11339']=(primary,secondary)
        mobs[boss]['fame_target']=True
        mobs[boss]['boss_mechanic_text']=(f'{name}: fazy walki przy 75%, 50% i 25% HP; '
                                         f'żywioły {primary} oraz {secondary}.')
        spawns.append((path[3],boss))
        tasks=(('Przysięga świadka','talk_npc',npc_id,1),('Obrona archiwum','kill',sentry,4),
               ('Pradawny relikt','collect',relic,1),('Upadek władcy','kill',boss,1),
               ('Ponowna próba legendy','kill',boss,1))
        chain=[];previous=None
        for j,(title,kind,target,amount) in enumerate(tasks,1):
            q=f'{slug}_q{j}'
            _add_quest(quests,q,f'{name}: {title}',mentor,kind,target,amount,
               f'{name} strzeże artefaktu {artifact}. Wyrusz na wyprawę i wróć po nagrodę.',
               stage+j*25,previous,repeatable=(j==5),npc_id=npc_id if kind=='talk_npc' else None)
            previous=q;chain.append(q)
        _npc(npcs,npc_id,mentor,path[0],f'Studiuję legendę: {name}. Pomożesz odzyskać {artifact}?',chain)

    # Real action-backed quest ladders; only the 14 EXISTING tool types.
    for prof,tool,npc_id,activity in PROFESSION_QUEST_SPECS_V0700:
        if npc_id not in npcs or prof not in TOOL_TYPES:
            raise AssertionError(f'v4 profession unavailable: {prof} {npc_id}')
        npc=npcs[npc_id];giver=str(npc['name'])
        prev=None;chain=[]
        for j,level in enumerate(PROF_STAGES):
            q=f'v4000_prof_{tool}_{level}'
            amount=4+j*3
            quest={'name':f'Dziedzictwo {prof}: {("Początek", "Czeladnik", "Wyprawa", "Próba", "Zlecenie", "Mistrz", "Arcymistrz", "Legenda")[j]}',
               'giver':giver,'kind':'profession_action','target':prof,'needed':amount,
               'description':f'Po przyjęciu wykonaj {amount} nowych czynności profesji {prof}: {activity}. '
                             'Etapy przechodź po kolei. Powtórka za godzinę.',
               'required_profession':prof,'min_profession_level':level,'generator_level':level,
               'specialist_tool_type':tool,
               'reward_profession':prof,'reward_profession_xp':2200+j*2100,
               'reward_tool_type':tool,'reward_tool_xp':1200+j*1400,
               'reward_silver':4200*(j+1),'reward_gold':0,'reward_mithril':0,
               'reward_items':{},'repeatable':True,'repeat_cooldown':3600,'v4000_imperium':True}
            if prev:quest['requires_quest']=prev
            _new(quests,q,quest);chain.append(q);prev=q
        npc['quest_chain']=list(npc.get('quest_chain') or ())+chain

    # 70 actual craft definitions, one set of five per profession.
    # Existing crafting engine consumes ingredients and grants outputs; no tool
    # registration or tool replacement. New items are resources, not fake gear.
    workstations={
      'Wędkarstwo':'inn', 'Górnictwo':'forge','Drwalstwo':'lumberjack_camp',
      'Kowalstwo':'forge','Gotowanie':'inn','Zielarstwo':'guild_arcane_chamber',
      'Alchemia':'guild_arcane_chamber','Jubilerstwo':'forge',
      'Krawiectwo':'tailor_workshop','Garbarstwo':'leatherworker_workshop',
      'Stolarstwo':'carpenter_workshop','Zaklinanie':'guild_arcane_chamber',
      'Archeologia':'library','Kartografia':'v016_cartographers_archive',
    }
    for i,(prof,tool,_,_) in enumerate(PROFESSION_QUEST_SPECS_V0700):
        station=workstations[prof]
        if station not in rooms:
            raise AssertionError(f'v4 station missing: {prof} -> {station}')
        for j,level in enumerate(CRAFT_STAGES):
            material=ocean_materials[(i+j)%len(ocean_materials)]
            key=f'v4000_craft_{tool}_{level}'
            output=f'v4000_work_{tool}_{level}'
            _record_material(items,output,f'{prof} — Dziedzictwo {CHAPTERS[j]}',
                f'Wyrób profesji {prof}, poziom {level}; wykonany ze znanych już narzędzi.',max(2500,level*130))
            ingredients={'soul_shard':max(1,2+j)} if j<2 else {material:1,'soul_shard':3+j}
            recipe={'name':items[output]['name'],'profession':prof,'tool_type':tool,
                    'stations':(station,),'ingredients':ingredients,'output':output,'quantity':1,
                    'min_profession_level':level,'min_tool_level':1,
                    'profession_xp':125+j*175,'tool_xp':70+j*90,
                    'desc':f'Wyrób {prof}. Materiały: '+', '.join(ingredients)+'. Nie wymaga nowego narzędzia.'}
            if prof in ('Krawiectwo','Garbarstwo','Stolarstwo'):
                from systems.professions import V03053_PROFESSIONS
                config=V03053_PROFESSIONS[prof]
                recipe['tool_item_id']=config['tool_item_id']
                recipe['tool_name']=items[config['tool_item_id']]['name']
                _new(V03053_CRAFT_RECIPES,key,recipe)
            else:
                _new(CRAFT_RECIPES,key,recipe)

    help_topics['imperium']=[
      'v4.00.0: Kroniki Korony Dusz w 32 starszych regionach; porozmawiaj z lokalnymi kronikarzami.',
      'Nowe pięć tras Imperium Morskiego jest połączone z istniejącymi Głębinami Oceanu 5.0.',
      'ocean4 cele; ocean4 atak imperium_widm / imperium_lewiatanow / imperium_koron / imperium_raf / imperium_sztormow.',
      '12 pradawnych superbossów: osobne komnaty, ostrzegane fazy walki, osobisty postęp drużynowy.',
      '14 profesji: po osiem godzinnych etapów praktyki u dotychczasowych mistrzów. Bez nowych narzędzi.',
      '70 nowych receptur: receptury profesji i craft; nowe materiały z wypraw morskich i bossów.',
      'Nie ma nowej blokady poziomów, losowych pułapek, obowiązkowego PvP ani końca gry.',
    ]
    help_aliases['koronadusz']='imperium'
    help_topics.setdefault('legendy',[]).append('Wielka kampania v4.00.0: wpisz help imperium.')
    help_topics.setdefault('ocean5',[]).append('Imperium Morskie v4.00.0: pięć nowych tras i pięć wrogich flot.')
    help_topics.setdefault('profesje',[]).append('Rzemiosło 7.0: nowe praktyczne zlecenia i receptury, bez nowych narzędzi.')
    stats=tuple(map(len,(rooms,npcs,mobs,spawns,quests,items,CRAFT_RECIPES,V03053_CRAFT_RECIPES)))
    return dict(zip(('rooms','npcs','mobs','spawns','quests','items','common_recipes','profession_recipes'),
                    (end-begin for end,begin in zip(stats,start))))
