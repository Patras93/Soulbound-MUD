# -*- coding: utf-8 -*-
"""New post-Legend class trials and optional team contracts.

Existing class mentors and guild/party mechanics are reused, instead of
creating fake progression tables or replacing any learned skills.
"""
from systems.forgotten_horizons_v1000 import _insert
from systems.eternal_glory_world_v1100 import REGIONS
from systems.class_legend_paths_v800 import CLASSES as FIRST_CLASSES, QUEST_IDS as FIRST_QUESTS
from systems.class_legend_paths_v900 import QUEST_IDS as LATER_QUESTS
from core.classes_skills import CLASSES

STAGES = ('Ostatnia Przysięga','Straż Świata','Korona Wieczności')
CLASS_QUEST_IDS = frozenset(
    f'v1100_class_{index:02d}_{stage}'
    for index in range(22) for stage in range(1,4)
)
TEAM_CONTRACT_IDS = frozenset(f'v1100_party_{key}' for key,*_ in REGIONS)


def install(npcs, quests, help_topics):
    historical = {}
    for klass, slug, *_ in FIRST_CLASSES:
        historical[klass] = (f'v800_class_mentor_{slug}', FIRST_QUESTS[klass][-1])
    for klass, old_quests in LATER_QUESTS.items():
        for npc_id,npc in npcs.items():
            if npc.get('v800_class_mentor') and npc.get('v800_required_class')==klass:
                historical[klass]=(npc_id,old_quests[-1]);break
    playable = [row[0] for row in CLASSES]
    if len(playable)!=22 or len(historical)!=22:
        raise RuntimeError('v11 class mastery: missing old class or mentor')
    for index,klass in enumerate(playable):
        npc_id, previous = historical[klass]
        guide=npcs[npc_id]['name']
        key,zone,level,element,*_=REGIONS[index%len(REGIONS)]
        for stage in range(1,4):
            qid=f'v1100_class_{index:02d}_{stage}'
            # All encounters are world-spawned. Class mastery cannot be bought,
            # faked with mock data or automatically completed on acceptance.
            target=(f'v1100_eg_{key}_elite' if stage==1 else
                    f'v1100_vault_{key}_sentinel' if stage==2 else
                    f'v1100_vault_{key}_guardian')
            _insert(quests,'QUESTS',qid,{
                'name':f'{klass}: {STAGES[stage-1]}',
                'giver':guide,'kind':'kill','target':target,
                'needed':(3 if stage<3 else 1),
                'requires_quest':previous,'required_class':klass,
                'description':f'Próba klasy {klass}. Odszukaj przeciwnika w krainie {zone} i pokonaj go po przyjęciu zadania.',
                'generator_level':min(800,level + stage*20),
                'reward_silver':(level+60)*15000*stage,
                'reward_gold':0,'reward_mithril':0,'reward_items':{},
                'repeatable':False,'v1100_class_mastery':True,
            })
            previous=qid
            npcs[npc_id]['specialist_quests'] = tuple(npcs[npc_id]['specialist_quests'])+(qid,)
    # Optional group-only combat contracts use the game's existing party
    # quest event handler. They do not block solo quests or raise mob scaling.
    lyra=next((npc for npc in npcs.values() if npc.get('name')=='Koordynatorka Kontraktów Lyra'),None)
    if not lyra:raise RuntimeError('v11 guild: missing existing contract coordinator Lyra')
    for index,(key,zone,level,*_) in enumerate(REGIONS):
        qid=f'v1100_party_{key}'
        _insert(quests,'QUESTS',qid,{
            'name':f'Gildyjna Ekspedycja: {zone}',
            'giver':'Koordynatorka Kontraktów Lyra',
            'kind':'party_contract','target':'boss' if index%3==0 else 'elite',
            'needed':1+index//3,
            'description':f'W lokalnej drużynie pokonajcie silnych przeciwników podczas wypraw. Cel: {zone}. Zadanie dodatkowe; gra solo pozostaje dostępna.',
            'generator_level':level,'repeatable':True,
            'repeat_cooldown':3600*12,
            'reward_silver':(level+50)*25000+100*max(5,level//30),
            'reward_gold':0,
            'reward_mithril':0,'reward_items':{'soul_shard':3+index},
            'party_contract_v11339':True,'minimum_party_size':2,
            'v1100_guild_contract':True,
        })
        lyra['specialist_quests'] = tuple(lyra.get('specialist_quests',()))+(qid,)
    help_topics['klasy11'] = [
        'Klasy 7.0: trzy dodatkowe próby bojowe u dotychczasowego mentora dla każdej z 22 klas.',
        'Próby zaczynają się po 120 etapach starej Drogi Legendy; każda prowadzi do prawdziwego przeciwnika nowej krainy.',
        'Stare umiejętności, Broń Duszy, nauczyciele i wybór jednej klasy pozostają nienaruszone.',
    ]
    help_topics['gildia11'] = [
        'Gildie 7.0: 12 nowych opcjonalnych kontraktów drużynowych u Koordynatorki Lyry.',
        'Kontrakty wymagają drużyny lokalnej, prawdziwych walk i mają 12 godzin odnowienia.',
        'Solo nadal może wykonywać całą zwykłą fabułę. Istniejące twierdze i budynki bez resetu.',
    ]
    return {'classes':22,'class_quests':len(CLASS_QUEST_IDS),'team_contracts':len(TEAM_CONTRACT_IDS)}
