# -*- coding: utf-8 -*-
"""v5.00.0: additive continuation of existing content, no alternate game engines.

Continuations start AFTER the stable v4.00.0 quest IDs. Original IDs, rooms,
encounters and existing quest progress are never overwritten. New areas have
no traps, no mandatory PVP, one or zero NPCs per room, reciprocal paths.
"""
from world.legends_v3200 import _join, _mob, _room, _quest, _new
from world.imperium_v4000 import OLD_ARCS, PRADAWNI, SEA_ROUTES, PROF_STAGES
from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700
from systems.mastery_crafting_v2201 import TOOL_TYPES
from data.crafting_recipes import CRAFT_RECIPES

ARC_NAMES = (
    'Przerwana Przysięga','Ostatni Świadek','Zapis Niepokonanych','Zatrute Poselstwo',
    'Rozbite Przymierze','Granica Milczenia','Pieczęć Ocalonych','Cień na Trakcie',
)
STORY_ORDERS = (
    ('kill','collect','talk_npc','kill'),
    ('collect','kill','kill','talk_npc'),
    ('talk_npc','kill','collect','kill'),
    ('kill','talk_npc','kill','collect'),
)
DUNGEON_NAMES = (
    ('Archiwum Zgasłych Płomieni','Strażnik Płonącej Księgi','fire'),
    ('Krypta Przysięgi','Uwięziony Rycerz Koron','dark'),
    ('Katedra Wiecznego Mrozu','Sędzia Zimy','ice'),
    ('Galeria Odbitych Tronów','Kamienny Król','earth'),
    ('Obserwatorium Pradawnych Burz','Herold Pięciu Piorunów','lightning'),
    ('Ogród Bez Imienia','Strażniczka Cierni','poison'),
    ('Świątynia Pustego Eteru','Tkacz Złamanego Zaklęcia','arcane'),
    ('Krypta Milczących Przypływów','Władca Głębinowego Echa','water'),
)
MOTIFS = (
    'odnalezienie potomków', 'odzyskanie zerwanego traktatu', 'ocalenie karawany',
    'odsłonięcie zdrady', 'odbudowanie pamięci', 'pokonanie straży wygnania',
    'zabezpieczenie relikwii', 'poznanie drugiego świadectwa',
)


def add_room(rooms, key, title, zone, detail, level):
    _room(rooms,key,title,zone,detail+ ' Nie ma tu pułapek.',level)
    rooms[key]['v500_war_of_gods'] = True


def new_mob(mobs, key, title, level, element, drop, boss=False):
    _mob(mobs,key,title,level,element,boss,drop=drop)
    mobs[key]['v500_war_of_gods'] = True
    mobs[key]['fame_target'] = True
    if boss:
        mobs[key]['boss_mechanic_text'] = (
            f'{title} zmienia rytm ataku, używa {element} i przyzywa strażników. '
            'Wzmocnienia i przywołania są aktywnymi akcjami istniejącego silnika.')
    else:
        mobs[key]['rank'] = 'elite'
    return key


def add_story(rooms, npcs, mobs, spawns, quests, items):
    count = 0
    for i,(arc_name, backstory, witness) in enumerate(OLD_ARCS):
        base=f'v4000_old_{i:02d}'
        npc_id=f'{base}_n'
        npc=npcs[npc_id]
        zone=rooms[f'{base}_r3']['zone']
        level=max(25,int(rooms[f'{base}_r3'].get('generator_level',25)))
        r4=f'v500_arc_{i:02d}_archive';r5=f'v500_arc_{i:02d}_sanctuary'
        add_room(rooms,r4,f'{arc_name} — Archiwum Zaginionych',zone,
            f'{backstory} Szukasz prawdy o: {MOTIFS[i%8]}.',level+32)
        add_room(rooms,r5,f'{arc_name} — Sala Rozstrzygnięcia',zone,
            f'Ukryta część opowieści: {MOTIFS[i%8]}. Tutaj rozstrzyga się los ocalałych.',level+62)
        _join(rooms,f'{base}_r3',r4);_join(rooms,r4,r5)
        token=f'v500_arc_{i:02d}_proof'; enemy=f'v500_arc_{i:02d}_enemy'
        _new(items,token,{'name':f'{arc_name} — Ślad Drugiego Świadka',
            'type':'quest','price':None,'sell_silver':(level+30)*350,
            'desc':f'Dowód potrzebny do odnowienia paktu: {MOTIFS[i%8]}.',
            'v500_war_of_gods':True})
        new_mob(mobs,enemy,f'Wysłannik {ARC_NAMES[i%8]}',level+65,
                ('dark','holy','fire','ice','lightning','poison','earth','arcane')[i%8],token)
        mobs[enemy]['drops']={token:1.0,'soul_shard':.8}
        spawns.append((r5,enemy))
        order=STORY_ORDERS[i%len(STORY_ORDERS)]
        prev=f'{base}_q5'
        new_ids=[]
        for j,kind in enumerate(order,1):
            q=f'v500_arc_{i:02d}_q{j}'
            target=enemy if kind=='kill' else token if kind=='collect' else npc_id
            needed=(5+j) if kind=='kill' else 2 if kind=='collect' else 1
            _quest(quests,q,f'{arc_name}: {ARC_NAMES[(i+j-1)%8]}',npc['name'],kind,target,needed,
                f'{backstory} Rozdział drugi: {MOTIFS[(i+j-1)%8]}. '
                f'Zadanie: {"pokonaj wysłanników" if kind=="kill" else "odzyskaj ślady" if kind=="collect" else "porozmawiaj ze świadkiem"}.',
                level+40+j*14,requires=prev,target_npc=npc_id if kind=='talk_npc' else None)
            quests[q]['v500_war_of_gods']=True
            quests[q]['reward_items']={'soul_shard':3+j}
            prev=q;new_ids.append(q);count+=1
        npc['quest_chain']=list(npc.get('quest_chain') or ()) + new_ids
    return count


def add_boss_profiles(mobs):
    for i, (_name,*_) in enumerate(PRADAWNI):
        boss=mobs[f'v4000_ancient_{i:02d}_boss']
        boss['v500_ancient_profile']=i
        from systems.war_of_gods_bosses_v5000 import PROFILES
        thresholds,names,multipliers,elements=PROFILES[i]
        boss['boss_mechanic_text']=(
            f'{_name}. Unikalne fazy przy '+', '.join(str(x)+'% HP' for x in thresholds)+'. '
            'Ataki: '+', '.join(elements)+'. '+', '.join(names)+'. '
            'Wszystkie potężne uderzenia są zapowiadane.')
    return len(PRADAWNI)


def add_dungeon_trials(rooms,npcs,mobs,spawns,quests,items):
    count=0
    for i,(title,guardian,element) in enumerate(DUNGEON_NAMES):
        origin=f'v4000_old_{i*4:02d}_r1'
        zone=title
        level=360+i*50
        path=[]
        for j,stage in enumerate(('Wejście','Korytarz Śladów','Sala Próby','Przedpole','Tron')):
            rid=f'v500_trial_{i}_{j}'
            add_room(rooms,rid,f'{title} — {stage}',zone,
                f'Stara komnata {title}. {stage}. Przejścia są jawne; pokonaj strażników, aby zdobyć ślady.',
                level+j*12)
            if path:_join(rooms,path[-1],rid)
            path.append(rid)
        _join(rooms,origin,path[0]);count+=len(path)
        fragment=f'v500_trial_{i}_fragment';sentry=f'v500_trial_{i}_sentry';boss=f'v500_trial_{i}_boss'
        _new(items,fragment,{'name':f'{title} — Pieczęć Próby','type':'resource','price':None,
              'sell_silver':(level+120)*650,'desc':f'Łup ze starcia w {title}.',
              'v500_war_of_gods':True})
        new_mob(mobs,sentry,f'Zbrojny {title}',level,element,fragment)
        mobs[sentry]['drops']={fragment:.65,'soul_shard':.75}
        new_mob(mobs,boss,guardian,min(800,level+160),element,fragment,True)
        mobs[boss]['drops']={fragment:1.0,'soul_shard':1.0}
        spawns.extend(((path[1],sentry),(path[2],sentry),(path[4],boss)))
        npc=npcs[f'v4000_old_{i*4:02d}_n']
        prior=f'v4000_old_{i*4:02d}_q5'
        names=(('Odłamki zapisów','collect',fragment,3),
               ('Strażnicy próby','kill',sentry,5),('Władca komnaty','kill',boss,1))
        ids=[]
        for j,(label,kind,target,needed) in enumerate(names,1):
            q=f'v500_trial_{i}_q{j}'
            _quest(quests,q,f'{title}: {label}',npc['name'],kind,target,needed,
                  f'Zejdź do {title} i wykonaj próbę. Nie ma pułapek ani blokady poziomu.',
                  level+j*22,requires=prior,repeatable=j==3)
            quests[q]['v500_war_of_gods']=True
            if j==3:quests[q]['repeat_cooldown']=7200
            prior=q;ids.append(q)
        npc['quest_chain']=list(npc.get('quest_chain') or ())+ids
    return count


def add_ocean(rooms,npcs,mobs,spawns,quests):
    count=0
    for idx,(slug,zone,origin,captain,material,element,level) in enumerate(SEA_ROUTES):
        prefix=f'v4000_sea_{slug}'
        npc_id=f'{prefix}_navigator';npc=npcs[npc_id]
        mob=f'v500_sea_{slug}_predator'
        new_mob(mobs,mob,f'Łowca Głębin {zone}',level+90,element,f'{prefix}_material')
        mobs[mob]['drops']={f'{prefix}_material':.6,'soul_shard':.95}
        spawns.append((f'{prefix}_r6',mob))
        prior=f'{prefix}_q5';chain=[]
        steps=(('Sygnały w ciemności','kill',mob,4),
               ('Artefakty szlaku','collect',f'{prefix}_material',2),
               ('Powrót z wyprawy','talk_npc',npc_id,1),
               ('Polowanie na głębinowego łowcę','kill',mob,7))
        for j,(label,kind,target,needed) in enumerate(steps,1):
            q=f'v500_sea_{slug}_q{j}'
            _quest(quests,q,f'{zone}: {label}',npc['name'],kind,target,needed,
                f'Zrealizuj kolejny etap wyprawy przez {zone}. Walki floty: ocean4 atak imperium_{slug}.',
                level+j*18,requires=prior,target_npc=npc_id if kind=='talk_npc' else None,
                repeatable=j==4)
            quests[q]['v500_war_of_gods']=True
            if j==4:quests[q]['repeat_cooldown']=5400
            prior=q;chain.append(q);count+=1
        npc['quest_chain']=list(npc.get('quest_chain') or ()) + chain
    return count


def add_professions(rooms,npcs,quests,items):
    from systems.professions import V03053_CRAFT_RECIPES
    # Real, existing workstations and tool types; one unique two-material
    # creation plus an elite variant per profession.
    stations={'Wędkarstwo':'inn','Górnictwo':'forge','Drwalstwo':'lumberjack_camp',
      'Kowalstwo':'forge','Gotowanie':'inn','Zielarstwo':'guild_arcane_chamber',
      'Alchemia':'guild_arcane_chamber','Jubilerstwo':'forge',
      'Krawiectwo':'tailor_workshop','Garbarstwo':'leatherworker_workshop',
      'Stolarstwo':'carpenter_workshop','Zaklinanie':'guild_arcane_chamber',
      'Archeologia':'library','Kartografia':'v016_cartographers_archive'}
    professions=0
    for index,(prof,tool,npc_id,action) in enumerate(PROFESSION_QUEST_SPECS_V0700):
        assert prof in TOOL_TYPES and TOOL_TYPES[prof]==tool
        npc=npcs[npc_id]
        station=stations[prof]
        assert station in rooms
        chain=[];prior=f'v4000_prof_{tool}_90'
        for step,(level,extra) in enumerate(((150,3),(400,6)),1):
            key=f'v500_work_{tool}_{level}';recipe_id=f'v500_recipe_{tool}_{level}'
            material=f'v4000_sea_{SEA_ROUTES[(index+step)%5][0]}_material'
            ing={'soul_shard':4+step*2,material:extra}
            _new(items,key,{'name':f'{prof} — Wyrób {"Przymierza" if step==1 else "Wojny Bogów"}',
               'type':'resource','price':None,'sell_silver':180000+level*850,
               'desc':f'Prawdziwy wyrób profesji {prof} z rzadkich materiałów.',
               'v500_war_of_gods':True})
            rec={'name':items[key]['name'],'profession':prof,'tool_type':tool,
                 'stations':(station,),'ingredients':ing,'output':key,'quantity':1,
                 'min_profession_level':level,'min_tool_level':1,
                 'profession_xp':5000+level*45,'tool_xp':3000+level*23,
                 'desc':f'Receptura {prof}: {extra} rzadkich materiałów i {4+step*2} odłamków duszy.'}
            if prof in ('Krawiectwo','Garbarstwo','Stolarstwo'):
                from systems.professions import V03053_PROFESSIONS
                cfg=V03053_PROFESSIONS[prof]
                rec['tool_item_id']=cfg['tool_item_id'];rec['tool_name']=items[cfg['tool_item_id']]['name']
                _new(V03053_CRAFT_RECIPES,recipe_id,rec)
            else:_new(CRAFT_RECIPES,recipe_id,rec)
            # Recipe-driven delivery, not another flat click-counter quest.
            q=f'v500_prof_{tool}_{level}_delivery'
            _new(quests,q,{'name':f'{prof}: Dostawa {items[key]["name"]}',
                 'giver':npc['name'],'kind':'collect','target':key,'needed':1,
                 'description':f'Wytwórz przedmiot {items[key]["name"]} przy stanowisku i dostarcz go mistrzowi.',
                 'required_profession':prof,'min_profession_level':level,
                 'generator_level':level,'requires_quest':prior,
                 'reward_profession':prof,'reward_profession_xp':5000+level*30,
                 'reward_tool_type':tool,'reward_tool_xp':3000+level*17,
                 'reward_silver':250000+level*8000,'reward_gold':0,'reward_mithril':0,
                 'reward_items':{'soul_shard':2+step},'repeatable':False,
                 'v500_war_of_gods':True})
            chain.append(q);prior=q;professions+=1
        npc['quest_chain']=list(npc.get('quest_chain') or ())+chain
    return professions


def install(rooms,npcs,mobs,spawns,quests,items,help_topics,help_aliases):
    before=(len(rooms),len(npcs),len(mobs),len(spawns),len(quests),len(items))
    from systems.war_of_gods_bosses_v5000 import validate_profiles
    validate_profiles()
    boss=add_boss_profiles(mobs)
    story=add_story(rooms,npcs,mobs,spawns,quests,items)
    trial_rooms=add_dungeon_trials(rooms,npcs,mobs,spawns,quests,items)
    ocean=add_ocean(rooms,npcs,mobs,spawns,quests)
    craft=add_professions(rooms,npcs,quests,items)
    help_topics['wojnabogow'] = [
      'Soulbound v5.00.0: Wojna Bogów. Kontynuacje 32 Kronik Korony Dusz zaczynają się u dotychczasowych kronikarzy.',
      'Dwunastu Pradawnych ma różne progi i nazwy faz oraz zmieniające się ataki żywiołów. Wpisz consider na bossie.',
      'Osiem prób lochowych łączących się ze starszymi regionami; bez pułapek. Istniejące portale i checkpointy pozostają.',
      'Ocean 7.0: ocean4 cele; ocean4 atak imperium_widm / imperium_lewiatanow / imperium_koron / imperium_raf / imperium_sztormow.',
      '14 profesji: dwie rzadkie receptury i prawdziwe dostawy nowych wyrobów u dotychczasowych mistrzów.',
      '14 klas: dwie nowe umiejętności na poziomach biegłości 350 i 700.',
      'EXP nagród nie zależy od progów levelowania; wszystkie poziomy i zapis SQLite są zachowane.',
    ]
    help_aliases['wojna']='wojnabogow'
    result=(len(rooms),len(npcs),len(mobs),len(spawns),len(quests),len(items))
    return {'bosses_upgraded':boss,'story_quests':story,'trial_rooms':trial_rooms,
            'ocean_quests':ocean,'profession_deliveries':craft,
            **dict(zip(('rooms','npcs','mobs','spawns','quests','items'),(x-y for x,y in zip(result,before))))}
