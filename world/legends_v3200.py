# -*- coding: utf-8 -*-
"""v3.20.0 — the Seven Legends systems, additive authored content.

Extends the already installed v3.10.0 realms. Only NEW IDs are registered; all
legacy rooms, NPCs, quests, inventory and SQLite tables remain untouched except
for safe bidirectional exits into new zones and appended NPC quest offers.
"""
from __future__ import annotations
from collections import deque
from world.legends_v3100 import REALMS, CLASS_NAMES, PROFESSIONS, OPPOSITE, PROFESSION_REWARD_TOOL_TYPES

# Narrative chapters, not procedural numbered NPC names. A substantial selection
# of pre-existing, navigable regions receives an independently playable story.
OLD_ARCS = (
    ('Ostatni List Strażnika', 'Nadchodzący zwiadowcy zostawili list z pieczęcią przed wielką wojną.', 'Aldena'),
    ('Przysięga Pustych Bram', 'Ktoś zamykał drogi uciekinierom i ukrył prawdziwy powód.', 'Orven'),
    ('Żelazna Zmowa', 'Ślady kuźni wskazują na nielegalny handel zaklętym żelazem.', 'Edrika'),
    ('Kronika Zaginionych Dzieci', 'Ocaleni słyszą głosy tych, którzy nie powrócili do domów.', 'Mirena'),
    ('Zdrada na Moście', 'Dwaj posłańcy podali różne wersje tej samej zasadzki.', 'Tavorn'),
    ('Noc Srebrnych Masek', 'Pod maskami kupców działają słudzy nieznanego władcy.', 'Vespera'),
    ('Milcząca Pieśń Lasu', 'Drzewa pamiętają balladę, której nie zna już żaden bard.', 'Eliara'),
    ('Kamień bez Imienia', 'Odkryto stary drogowskaz do zapomnianego królestwa.', 'Thoren'),
    ('Ostatni Ogień Obozu', 'Zgasłe ogniska prowadzą do zaginionego oddziału.', 'Darien'),
    ('Sól i Proroctwo', 'Z dna dawnej studni wydobyto zaszyfrowane ostrzeżenie.', 'Kallina'),
    ('Pieczęć Przechodniów', 'Pieczęć otwiera drogę, lecz dzieli tych, którzy jej strzegą.', 'Borhen'),
    ('Obcy pod Sztandarem', 'Zwiadowcy podejrzewają, że jeden z sojuszników jest zdrajcą.', 'Isvera'),
    ('Głosy Starej Kopalni', 'Kamień powtarza imiona górników, którzy zaginęli.', 'Durgan'),
    ('Utracona Księga Przysiąg', 'Strażnik archiwum odnalazł wyrwane stronice historii.', 'Sariel'),
    ('Łowcy Czarnego Szlaku', 'Konwoje giną tam, gdzie niegdyś kupcy świętowali.', 'Rovik'),
    ('Tajemnica Trzech Kluczy', 'Trzy rodziny ukryły wspólną tajemnicę w odległych kryptach.', 'Rella'),
    ('Złoto w Popiele', 'Po pożarze osady ktoś rozrzucił fałszywe tropy.', 'Thalia'),
    ('Stracona Godzina', 'W pewnym miejscu zegary i zaklęcia przestały działać.', 'Norel'),
    ('Powrót Samotnej Floty', 'Dzwony zwiastują statek, którego nikt nie widział od lat.', 'Aevira'),
    ('Oczy pod Ziemią', 'Górnicy zgłaszają, że ktoś obserwuje ich z dawnych tuneli.', 'Gorlen'),
    ('Zamknięta Komnata Szeptów', 'Dawne listy kryją zapis o zdradzie pradawnego cechu.', 'Velna'),
    ('Płomień Bez Cienia', 'Wędrowcy widzą nocą ogień, który nie rozjaśnia mroku.', 'Morrik'),
    ('Błękitny Kwiat Pamięci', 'Zielarze zbierają roślinę, która pozwala usłyszeć wspomnienia.', 'Liris'),
    ('Trzy Dni Ciszy', 'Ocaleni z wyprawy nie chcą wypowiedzieć imienia wroga.', 'Ravenna'),
    ('Most z Połamanych Mieczy', 'Na szlaku leżą ostrza należące do jednego królestwa.', 'Fendar'),
    ('Kruki i Zegar', 'Kruki powtarzają ostrzeżenie tuż przed każdą burzą.', 'Selwen'),
    ('Biały Kamień', 'Odkryty drogowskaz łączy niegdyś wrogie ziemie.', 'Elmar'),
    ('Czerwony Kontrakt', 'W karczmach pojawiło się zlecenie bez podpisu.', 'Navira'),
    ('Kwiat Ostatniej Wiosny', 'Pradawny ogród zakwitł na ziemi spustoszonej wojną.', 'Althea'),
    ('Zakon Bez Chorągwi', 'Zaginieni rycerze pozostawili znak, który wciąż ktoś chroni.', 'Edryn'),
    ('Przełęcz Zamilkłych', 'Pielgrzymi nie wrócili z dobrze znanego szlaku.', 'Ivaren'),
    ('Świadectwo Dawnika', 'Ostatni skryba zebrał dowody sprzed upadku miasta.', 'Orelia'),
)
BRANCH_TITLES = (
    ('Szlak Ostatniego Śladu', 'Przysięga Świadków', 'Archiwum Głosów'),
    ('Wąwóz Niewypowiedzianych Słów', 'Pogranicze Zgliszczy', 'Galeria Pamięci'),
    ('Przełęcz Powracających', 'Ogrodzone Włości', 'Sala Dawnej Rady'),
    ('Wschodnia Strażnica', 'Most Niegasnących Świateł', 'Droga Nieobecnych'),
    ('Komnaty Pieczęci', 'Korytarz Nocnych Znaków', 'Sala Ocalonych'),
    ('Trakt Samotnych Wież', 'Zapomniany Przyczółek', 'Archiwum Kręgu'),
    ('Podziemia Starej Pieśni', 'Bastion Kamiennego Snu', 'Sala Milczących'),
    ('Wzgórza Pierwszego Świtu', 'Aleja Połamanych Chorągwi', 'Ścieżka Odkrywców'),
)
BOSS_IDENTITIES = (
    ('Strażnik Upadłej Pieczęci', ('dark','physical')),
    ('Władca Runicznego Echa', ('lightning','arcane')),
    ('Skażone Serce Puszczy', ('poison','earth')),
    ('Admirał Bezimiennej Głębi', ('ice','dark')),
    ('Herold Pękniętego Nieba', ('fire','lightning')),
    ('Kat Wiecznego Zegara', ('arcane','ice')),
    ('Królowa Rozszczepionego Roju', ('poison','physical')),
    ('Cień Srebrnego Dworu', ('holy','dark')),
)


def _join(rooms, a, b, preferred=('north','east','west','south','up','down','northeast','northwest','southeast','southwest')):
    """Never overwrite an exit; preserve reciprocal navigation."""
    if a not in rooms or b not in rooms:
        raise AssertionError('v3.20: missing room for path')
    for direction in preferred:
        opposite=OPPOSITE[direction]
        if direction not in rooms[a]['exits'] and opposite not in rooms[b]['exits']:
            rooms[a]['exits'][direction]=b
            rooms[b]['exits'][opposite]=a
            return direction
    raise AssertionError(f'v3.20: no safe free reciprocal exit from {a} to {b}')


def _new(catalog, key, value):
    if key in catalog:
        raise AssertionError('v3.20 catalog collision: '+key)
    catalog[key]=value


def _room(rooms,key,name,zone,desc,stage):
    _new(rooms,key,{'name':name,'zone':zone,'desc':desc,'exits':{},
                    'generator_level':int(stage),'recommended_mastery':int(stage),
                    'v3200_seven_legends':True})
    return key


def _npc(npcs,key,name,room,speech,chain):
    _new(npcs,key,{'name':name,'room':room,'dialogue':speech,
                    'quest_chain':list(chain),'v3200_seven_legends':True})


def _mob(mobs,key,name,stage,element='physical',boss=False,drop='soul_shard'):
    # The existing ordinary-boss phase engine owns 75/50/25% transitions and
    # elemental combat. No invented independent combat loop or HP cap.
    value={'name':name,'generator_level':int(stage),
       'max_hp':int((3800 if boss else 280)*stage),
       'damage':int((56 if boss else 7)*stage),
       'damage_type':'physical' if element=='physical' else 'magic',
       'attack_elements_v11339':(element,) if element!='physical' else (),
       'v017_boss_phases':bool(boss),'boss_mechanic': 'ancient' if boss else None,
       'boss_mechanic_text':('Trzy jawne etapy walki przy 75, 50 i 25 procent HP. '
                              'Ataki zmieniają żywioły, a boss przyspiesza w finale.' if boss else ''),
       'stat_reward':int(stage*(410 if boss else 75)),
       'class_xp_reward':int(stage*(13800 if boss else 3100)),
       'soul_reward':int(stage*(4600 if boss else 960)),
       'silver':int(stage*(4300 if boss else 570)),
       'gold':0,'mithril':0,'drops':{drop:1.0,'soul_shard':1.0} if drop!='soul_shard' else {'soul_shard':1.0},
       'boss':bool(boss),'world_boss':bool(boss),
       'rank':'world_boss' if boss else 'elite',
       'quest_target':key,'stationary_mob':True,'auto_aggro':False,
       'v3200_seven_legends':True}
    _new(mobs,key,value)
    return key


def _quest(quests,key,title,giver,kind,target,needed,desc,stage,requires=None,repeatable=False,
           profession=None,required_class=None,target_npc=None):
    # These are incremental rewards. Existing Multi Cap/EXP Bank calculation
    # remains the sole authority; we do not rewrite its math.
    data={'name':title,'giver':giver,'kind':kind,'target':target,'needed':needed,
          'description':desc,'generator_level':int(stage),
          'character_xp_reward':int(stage*(7800 if repeatable else 14500)),
          'reward_stat_progress':int(stage*(620 if repeatable else 1750)),
          'reward_silver':int(stage*(2700 if repeatable else 6800)),
          'reward_gold':0,'reward_mithril':0,
          'reward_items':{'soul_shard':2 if repeatable else 5},
          'repeatable':repeatable,'v3200_seven_legends':True}
    if requires:
        data['requires_quest']=requires
    if repeatable:
        data['repeat_cooldown']=3600
    if profession:
        data['reward_profession']=profession
        data['reward_profession_xp']=int(stage*(230 if repeatable else 390))
        # The genuine quest turn-in guard rejects profession XP without this.
        data['reward_tool_type']=PROFESSION_REWARD_TOOL_TYPES[profession]
    if required_class:
        data['required_class']=required_class
    if target_npc:
        data['target_npc']=target_npc
    _new(quests,key,data)
    return key


def _reachable(rooms, start='square'):
    found={start}
    todo=deque([start])
    while todo:
        room=rooms[todo.popleft()]
        for destination in room.get('exits',{}).values():
            if isinstance(destination,str) and destination in rooms and destination not in found:
                found.add(destination)
                todo.append(destination)
    return found


def _anchors(rooms):
    reachable=_reachable(rooms)
    candidates={}
    for rid in sorted(reachable):
        if rid.startswith(('v3100_','npc_v3101_','v3200_')):
            continue
        row=rooms[rid]
        zone=str(row.get('zone') or '').strip()
        if not zone or len(zone)>80 or row.get('procedural_dynamic') or row.get('generated_on_demand'):
            continue
        if len(row.get('exits',{}))>=10:
            continue
        candidates.setdefault(zone, rid)
    zones=sorted(candidates)
    if len(zones)<len(OLD_ARCS):
        raise AssertionError(f'v3.20: insufficient reachable old-world regions {len(zones)}')
    # Deterministically spread campaigns across the alphabetized zone catalogue.
    picks=[zones[(i*len(zones))//len(OLD_ARCS)] for i in range(len(OLD_ARCS))]
    return [(zone,candidates[zone]) for zone in picks]


def install(rooms,npcs,mobs,spawns,quests,items,help_topics,help_aliases):
    """Register all seven features before v3.10.1 single-NPC isolation runs."""
    initial=tuple(map(len,(rooms,npcs,mobs,spawns,quests,items)))
    # I. Exploration: three distinctive accessible branches in each realm,
    # eight chambers apiece. These are reachable in the existing world.
    for index,(slug,zone,stage,relic,lore,sites,enemies,boss,guide,witness) in enumerate(REALMS):
        for branch in range(3):
            title=BRANCH_TITLES[index][branch]
            path=[]
            for step in range(8):
                name=(f'{title} — {("Próg", "Sala Świadków", "Krużganek", "Tajemnica", "Przeprawa", "Komnata Śladów", "Brama Ocalonych", "Serce Szlaku")[step]}')
                rid=_room(rooms,f'v3200_{slug}_trail_{branch}_{step}',name,zone,
                    f'{title}. {lore} Odczytujesz ślady wyprawy, a dalsza droga jest bezpieczna od pułapek.',
                    stage+25+branch*20+step*3)
                path.append(rid)
                if step:
                    _join(rooms,path[-2],rid)
            _join(rooms,f'v3100_{slug}_room_{(2,6,10)[branch]:02d}',path[0])
            npc_id=f'v3200_{slug}_npc_{branch}'
            # One new NPC per branch; all old NPCs stay in their own places.
            speaker=f'{("Badacz", "Strażniczka", "Kronikarz")[branch]} {("Tharion", "Mevena", "Eldrin", "Ovarin", "Kaedra", "Solven", "Miryx", "Elaris")[index]} {("Szlaku", "Pieczęci", "Świadków")[branch]}'
            elite=f'v3200_{slug}_trail_guard_{branch}'
            _mob(mobs,elite,f'{("Wygnany Rycerz", "Wartownik Legend", "Herold Echa")[branch]} — {zone}',
                 stage+35+branch*22,('physical','dark','ice')[branch])
            for room_id in (path[3],path[6]):
                spawns.append((room_id,elite))
            loot=f'v3200_{slug}_fragment_{branch}'
            _new(items,loot,{'name':f'{title} — Fragment Pieczęci','type':'quest',
                             'price':None,'desc':f'Spór o {relic}. {lore}', 'v3200_seven_legends':True})
            # For narrative objectives the new elite drops its own fragment.
            mobs[elite]['drops']={loot:1.0,'soul_shard':1.0}
            prev=f'v3100_{slug}_story_2'
            seq=[]
            specs=(
                ('Wysłuchaj świadka','talk_npc',npc_id,1,
                 f'Porozmawiaj z {speaker}; opowie o zaginionych podróżnikach.'),
                ('Wrogowie na trakcie','kill',elite,4,
                 f'Przywróć bezpieczeństwo: pokonaj czterech wrogów na szlaku {title}.'),
                ('Okruch z pieczęci','collect',loot,2,
                 f'Zdobądź dwie pieczęcie po przyjęciu etapu; strażnicy noszą te fragmenty.'),
                ('Cisza po bitwie','kill',elite,7,
                 f'Wypędź siedmiu ostatnich strażników, aby mogli wrócić ocaleni.'),
                ('Kronika powrotu','talk_npc',npc_id,1,
                 f'Wróć do {speaker} i poznaj zakończenie tej historii.'),
            )
            for chapter,(label,kind,target,needed,desc) in enumerate(specs,1):
                qid=f'v3200_{slug}_trail_{branch}_q{chapter}'
                _quest(quests,qid,f'{title}: {label}',speaker,kind,target,needed,desc,
                       stage+branch*16+chapter*9,requires=prev,
                       target_npc=npc_id if kind=='talk_npc' else None)
                prev=qid
                seq.append(qid)
            _npc(npcs,npc_id,speaker,path[1],f'{lore} Odkryj kolejne rozdziały mojej opowieści.',seq)

        # II. Superbosses 8.0 + III. Expedition 2.0.
        # Existing phase engine handles true transitions at 75/50/25% HP.
        boss_id=f'v3200_{slug}_superboss'
        element_a,element_b=BOSS_IDENTITIES[index][1]
        elite_name=BOSS_IDENTITIES[index][0]
        stage2=stage+165
        _mob(mobs,boss_id,f'{elite_name} — {zone}',stage2,element_a,True,
             drop=f'v3100_{slug}_relic')
        mobs[boss_id]['attack_elements_v11339']=(element_a,element_b)
        mobs[boss_id]['boss_mechanic_text']=(
            f'{elite_name}: fazy przy 75%, 50%, 25% życia, techniki {element_a} i {element_b}. '
            'Skalowanie HP i obrażeń korzysta z obecnego silnika; zwycięstwo nie blokuje samotnej gry.')
        lair=f'v3200_{slug}_trail_2_7'
        spawns.append((lair,boss_id))
        giver=npcs[f'v3100_{slug}_guide']
        previous=f'v3100_{slug}_expedition_2'
        for chapter,(label,kind,target,needed) in enumerate((
                ('Odsiecz ekspedycji','kill',f'v3200_{slug}_trail_guard_0',5),
                ('Strażnicy dawnej bramy','kill',f'v3200_{slug}_trail_guard_1',5),
                ('Ostatnia pieczęć','collect',f'v3200_{slug}_fragment_2',2),
                ('Zwycięstwo nad legendą','kill',boss_id,1)),1):
            qid=f'v3200_{slug}_expedition_{chapter}'
            _quest(quests,qid,f'{zone} — ekspedycja: {label}',giver['name'],kind,target,needed,
                   f'{label}. Przejdź szlaki regionu {zone}, potem wróć do przewodnika.',
                   stage2+chapter*18,requires=previous)
            previous=qid
            giver['quest_chain']=list(giver.get('quest_chain') or [])+[qid]
        # IV. Chronicles: independent renewable contracts; no endgame flag.
        for chapter,(label,target,number) in enumerate((
            ('Patrole pogranicza',f'v3200_{slug}_trail_guard_0',8),
            ('Ocalona pieczęć',f'v3200_{slug}_trail_guard_1',10),
            ('Łowca legend',boss_id,1)),1):
            qid=f'v3200_{slug}_chronicle_{chapter}'
            _quest(quests,qid,f'Kroniki Bohaterów: {zone} — {label}',giver['name'],
                   'kill',target,number,f'Godzinna kronika: {label} w regionie {zone}.',
                   stage2+chapter*18,requires=f'v3100_{slug}_story_1',repeatable=True)
            giver['quest_chain']=list(giver.get('quest_chain') or [])+[qid]

    # V. Global old-world campaigns: 32 real pre-existing navigable regions.
    for index,(zone,anchor) in enumerate(_anchors(rooms)):
        label,plot,name=OLD_ARCS[index]
        stage=max(5,min(240,int(rooms[anchor].get('generator_level') or
                                rooms[anchor].get('recommended_mastery') or 30)))
        entry=[]
        for chamber in range(4):
            rid=_room(rooms,f'v3200_old_{index:02d}_room_{chamber}',
                  f'{label} — {("Posterunek", "Ślady", "Zagrożenie", "Kronika")[chamber]}',
                  zone, f'{plot} Rozdział tej historii: {chamber+1} z 4.',stage+chamber*8)
            entry.append(rid)
            if chamber:
                _join(rooms,entry[chamber-1],rid)
        _join(rooms,anchor,entry[0])
        npc_id=f'v3200_old_{index:02d}_npc'
        giver=f'{("Kronikarz", "Wartowniczka", "Posłaniec", "Badaczka")[index%4]} {name}'
        mob_id=f'v3200_old_{index:02d}_raider'
        _mob(mobs,mob_id,f'{("Strażnik Zmowy", "Napastnik Pogranicza", "Widmo Dawnego Traktu", "Łowca Pieczęci")[index%4]} — {zone}',
             stage+18+index//4,('physical','dark','poison','ice')[index%4])
        spawns.extend(((entry[2],mob_id),(entry[3],mob_id)))
        fragment=f'v3200_old_{index:02d}_proof'
        _new(items,fragment,{'name':f'{label} — Świadectwo','type':'quest','price':None,
                             'desc':plot,'v3200_seven_legends':True})
        mobs[mob_id]['drops']={fragment:1.0,'soul_shard':1.0}
        previous=None
        ids=[]
        for ch,(name_ch,kind,target,needed) in enumerate((
            ('Rozmowa w posterunku','talk_npc',npc_id,1),
            ('Przerwana droga','kill',mob_id,4),
            ('Dowód zaginionych','collect',fragment,2),
            ('Powstrzymanie napastników','kill',mob_id,7),
            ('Zapisana prawda','talk_npc',npc_id,1)),1):
            qid=f'v3200_old_{index:02d}_quest_{ch}'
            _quest(quests,qid,f'{label}: {name_ch}',giver,kind,target,needed,
                   f'{plot} {name_ch}. Region: {zone}.',stage+ch*10,
                   requires=previous,target_npc=npc_id if kind=='talk_npc' else None)
            previous=qid
            ids.append(qid)
        _npc(npcs,npc_id,giver,entry[0],f'{plot} Pytaj o {label}.',ids)

    # VI. Mastery of each playable class: two more chapters on the existing
    # instructors, plus real learnable skills in core/classes_skills.py.
    for i,class_name in enumerate(CLASS_NAMES):
        mentor=npcs[f'v3100_class_{i:02d}']
        guide=f'v3100_{REALMS[i%8][0]}_guide'
        target=f'v3200_{REALMS[i%8][0]}_trail_guard_{i%3}'
        for chapter,needed in ((3,9),(4,15)):
            qid=f'v3200_class_{i:02d}_{chapter}'
            _quest(quests,qid,f'Mistrzostwo {class_name}: księga {chapter}',mentor['name'],
                   'kill',target,needed,
                   f'Wyzwanie klasy {class_name}: pokonaj {needed} przeciwników ze szlaku legend. '
                   'Nowe skille klasowe są dostępne u nauczycieli po osiągnięciu wymaganego poziomu Biegłości.',
                   190+chapter*50+i*6,
                   requires=(f'v3100_class_{i:02d}_quest_2' if chapter==3 else f'v3200_class_{i:02d}_3'),
                   required_class=class_name)
            mentor['quest_chain']=list(mentor.get('quest_chain') or [])+[qid]

    # VII. Professions 5.0: diversified authored orders for each existing trade.
    for i,(profession,item_id) in enumerate(PROFESSIONS):
        if item_id not in items:
            item_id='soul_shard'
        mentor=npcs[f'v3100_prof_{i:02d}']
        for chapter,needed in ((3,9),(4,16)):
            qid=f'v3200_prof_{i:02d}_{chapter}'
            _quest(quests,qid,f'{profession} — wielkie zamówienie {chapter}',mentor['name'],
                   'collect',item_id,needed,
                   f'Zdobądź po przyjęciu zamówienia {needed} szt. {items[item_id]["name"]}. '
                   f'Nagroda wzmacnia {profession} i daje wysokie wynagrodzenie za mistrzowską pracę.',
                   130+chapter*60+i*6,
                   requires=(f'v3100_prof_{i:02d}_order_2' if chapter==3 else f'v3200_prof_{i:02d}_3'),
                   profession=profession)
            mentor['quest_chain']=list(mentor.get('quest_chain') or [])+[qid]

    help_topics['legendy'] = list(help_topics.get('legendy') or []) + [
       'WIELKI DODATEK v3.20: 24 dodatkowe szlaki krain, 32 kampanie w starym świecie, cztery nowe etapy każdej ekspedycji.',
       'Kroniki Bohaterów: nowe godzinne zlecenia w ośmiu krainach. Przyjmuj je u lokalnego przewodnika.',
       'Nowe mistrzowskie skille wszystkich 14 klas: ucz się ich u własnego nauczyciela po uzyskaniu wymaganej Biegłości.',
       'Każda z 14 profesji otrzymuje dalsze zamówienia mistrzowskie; nie trzeba resetować profesji ani narzędzi.',
       'Osiem nowych superbossów z 3 fazami i dwoma żywiołami. Każdą próbę możesz podjąć solo lub z drużyną.',
       'Dodatkowe historie mają własnych NPC w bocznych, zawsze dwustronnych drogach istniejącego świata, bez pułapek.',
    ]
    help_aliases['legenda320']='legendy'
    counts=tuple(map(len,(rooms,npcs,mobs,spawns,quests,items)))
    return dict(zip(('rooms','npcs','mobs','spawns','quests','items'),
                    (after-before for before,after in zip(initial,counts))))
