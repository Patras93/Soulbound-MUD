# -*- coding: utf-8 -*-
"""One continuous 12-chapter story through 12 actual v11 regions.

Each chapter uses an existing NPC, a persistent SQLite quest, and a natural
battle-earned target or relic. History in all pre-v11 quest IDs is untouched.
"""
from systems.forgotten_horizons_v1000 import _insert
from systems.eternal_glory_world_v1100 import REGIONS

CHAPTERS = (
    ('Pierwsza Przysięga','Odszukaj głos tych, których pamięć wymazano z ołtarzy.'),
    ('Biała Korona','Zaśnieżone drzewa ukrywają świadectwo zdradzonej królowej.'),
    ('Sąd Popiołu','Bóg wygnania ukrywa pieczęć, której ogień nie może zniszczyć.'),
    ('Pamięć Głębin','W zatopionych kronikach czekają imiona dawnych żeglarzy.'),
    ('Ostatnia Godzina','Klepsydra pradawnych zapisuje cenę niespełnionej obietnicy.'),
    ('Róża Cierni','Matka puszczy odda świadectwo tylko obrońcom żywych.'),
    ('Gwiazda Wojny','Proroczy meteor wskazuje przejście do grobowca bogów.'),
    ('Milcząca Armada','Znalezienie utraconych żagli odsłania szlak przez ocean.'),
    ('Sąd Serafinów','Płonące niebo kryje tych, którzy wydali wyrok na bogów.'),
    ('Wieczna Zima','Cesarz mrozu strzeże imienia pierwszego zdrajcy.'),
    ('Burza Pamięci','Pioruny wyryły na wyspach nazwy zabronionych królestw.'),
    ('Korona Wieczności','Ostatnia pieczęć kończy wojnę pamięci i zapomnienia.'),
)
CHAPTER_IDS = tuple(f'v1100_story_{idx:02d}' for idx in range(len(REGIONS)))
FINAL_ARTIFACT_ID = 'v1100_eternal_crown'


def install(npcs,quests,items,help_topics,help_aliases):
    if len(CHAPTERS)!=len(REGIONS):
        raise RuntimeError('v11 story: chapters and regions must correspond')
    _insert(items,'ITEMS',FINAL_ARTIFACT_ID,{
        'name':'Korona Wiecznej Chwały', 'type':'armor','slot':'charm',
        'defense':110,'price':None,'sell_silver':780000,
        'desc':'Relikt zakończenia Wielkiej Kroniki; zachowuje pamięć dwunastu krain.',
        'v1100_story_legendary':True,
    })
    previous=None
    for idx,(key,zone,level,element,guide,elite,boss,places) in enumerate(REGIONS):
        title,description=CHAPTERS[idx]
        quest_id=CHAPTER_IDS[idx]
        # Gathering the seal is real progression: the unique floor boss drops it.
        objective_kind='kill' if idx%2==0 else 'collect'
        target=(f'v1100_vault_{key}_guardian' if objective_kind=='kill'
                else f'v1100_vault_{key}_seal')
        quest={
            'name':f'Wojna Pradawnych: {title}',
            'giver':guide, 'kind':objective_kind,
            'target':target,'needed':1,
            'description':f'Rozdział {idx+1} z 12. {description} Wyprawa prowadzi do {zone}.',
            'generator_level':level,'repeatable':False,
            'reward_silver':(level+50)*23000,
            'reward_gold':0,'reward_mithril':0,
            'reward_items':({FINAL_ARTIFACT_ID:1} if idx==len(REGIONS)-1 else {}),
            'v1100_world_story':True,
        }
        # Each chapter also requires finishing the local regional story.
        # The global chain from chapter two onward is the prerequisite.
        quest['requires_quest']=(previous if previous else f'v1100_vault_{key}_quest_2')
        _insert(quests,'QUESTS',quest_id,quest)
        npc=npcs[f'v1100_eg_{key}_guide']
        npc['specialist_quests'] = tuple(npc.get('specialist_quests',()))+(quest_id,)
        previous=quest_id
    help_topics['fabuła11'] = [
        'Wielka Fabuła 2.0: Wojna Pradawnych ma 12 kolejnych rozdziałów obejmujących nowe kontynenty, puszcze, pustynie i ocean.',
        'U przewodników nowych krain wpisz quest list. W kolejnych rozdziałach naprawdę pokonujesz bossów i zbierasz ich pieczęcie.',
        'Ostatni rozdział nagradza Koroną Wiecznej Chwały. Postęp i nagrody zapisują się w dotychczasowym SQLite.',
    ]
    help_aliases['wojna pradawnych'] = 'fabuła11'
    return {'chapters':len(CHAPTER_IDS),'legendary_rewards':1}
