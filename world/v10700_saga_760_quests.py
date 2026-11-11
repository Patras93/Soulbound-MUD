# -*- coding: utf-8 -*-
"""v107: 760 real, native quest records in six documented categories.

Exactly 2000 new quests incl 1240 existing (1200 regional +40 insects).
All targets are existing spawned mobs or their genuine drops. No fabricated
kill counters. The 60 real regional Chaos threats rotate hourly: 10 available
per window, each eligible once in six hours; accepted hunts stay playable.
"""
from __future__ import annotations
from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
from collections import Counter
from core.archetypes.chaos import CLASS_SPECS, RACE_SPECS, PROFESSION_SPECS
from world.v10700_chaos_chapter_one import prefix
from world.v10700_region_index import CHAPTER_ONE
from world.v10700_region_index_chapters_2_6 import ALL_NEXT

ALL_REALMS=tuple(CHAPTER_ONE)+tuple(ALL_NEXT)
EXPECTED=dict(prof=320,cls=160,race=80,dungeon=120,events=60,final=20)
assert sum(EXPECTED.values())==760 and len(ALL_REALMS)==30


def install(rooms,mobs,spawns,npcs,quests,items):
    """Preflight all 760 IDs and real targets; publish only after validation."""
    ids={f'v10700_saga_{part}_{i:03d}' for part,count in EXPECTED.items()
         for i in range(1,count+1)}
    if ids.intersection(quests):
        raise RuntimeError('v107 saga: ponowna instalacja lub kolizja ID')
    if len(ids)!=760:
        raise RuntimeError('v107 saga: niepoprawna liczba zadań')
    all_spawns={mid for room,mid in spawns if room in rooms}
    for region in ALL_REALMS:
        p=prefix(region[0])
        if any(f'{p}_mob_{j}' not in mobs or f'{p}_mob_{j}' not in all_spawns for j in range(1,11)):
            raise RuntimeError('v107 saga: niepełne rzeczywiste odrodzenia '+p)
        if any(f'{p}_npc_{j}' not in npcs for j in range(1,5)):
            raise RuntimeError('v107 saga: brak prawdziwego NPC '+p)
    for name,*_ in CLASS_SPECS:
        if 'teacher_v107_'+name.casefold().replace(' ','_') in npcs:
            raise RuntimeError('v107 saga: kolizja nowego nauczyciela')
    for name,*_ in PROFESSION_SPECS:
        if 'artisan_v107_'+name.casefold().replace(' ','_') in npcs:
            raise RuntimeError('v107 saga: kolizja specjalisty')
    for name,*_ in PROFESSION_SPECS:
        if any(q.get('required_profession')==name for q in quests.values()):
            raise RuntimeError('v107 saga: duplikat profesjonalizacji')
    # Stage all new data locally; no intermediate mutation of production catalog.
    newquests={}; newnpcs={}; assign={}
    class_names=('Magitek',)+tuple(row[0] for row in CLASS_SPECS)
    race_names=tuple(row[0] for row in RACE_SPECS)
    prof_names=tuple(row[0] for row in PROFESSION_SPECS)
    def realm(i):
        row=ALL_REALMS[i%30]
        return prefix(row[0]),row[1]
    def offer(npc_id,qid):
        assign.setdefault(npc_id,[]).append(qid)
    def common(p,name,giver,mid,needed,idx, *, repeat=True):
        assert mid in mobs and mid in all_spawns
        material=f'{p}_material_{1+idx%4}'
        assert material in items
        lvl=max(1,int(mobs[mid].get('generator_level',100)))
        return dict(giver=giver,kind='kill',target=mid,needed=needed,
            description=f'Pokonaj {needed} × {mobs[mid]["name"]} w {name}. Wróć do {giver}.',
            generator_level=lvl,reward_stat_progress=lvl*850,
            olc_reward_xp=lvl*1250,olc_reward_class_xp=lvl*1200,
            olc_reward_soul_xp=lvl*1050,reward_gold=500+idx*13,
            reward_mithril=2+idx//100,reward_items={material:1},
            repeatable=repeat,**({'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS} if repeat else {}),v10700_saga=True)

    # Eight truly separate profession action tracks; actual events must be
    # emitted by the new 'profesja107' processor for the native quest counter.
    for n,prof in enumerate(prof_names):
        p,region=realm(n*3)
        nid='artisan_v107_'+prof.casefold().replace(' ','_')
        newnpcs[nid]=dict(name='Mistrz '+prof,room=p+'_02',
           dialogue=f'Zawód {prof}: wpisz profesja107 lista, następnie profesja107 {n+1}.',
           specialist_tool_type=PROFESSION_SPECS[n][1],specialist_quests=(),
           v10700_saga=True)
        for j in range(1,41):
            i=n*40+j
            qid=f'v10700_saga_prof_{i:03d}'
            row=common(p,region,newnpcs[nid]['name'],f'{p}_mob_{1+j%10}',3+(j%6),i)
            row.update(name=f'{prof}: Próba rzemiosła {j}/40',kind='profession_action',
                       target=prof,needed=3+j%7,
                       required_profession=prof,reward_profession=prof,
                       reward_tool_type=PROFESSION_SPECS[n][1],
                       reward_profession_xp=row['generator_level']*2400,
                       reward_tool_xp=row['generator_level']*1900,
                       description=f'Wykonaj {3+j%7} prawdziwych czynności profesji {prof}, następnie wróć do specjalisty.')
            newquests[qid]=row;offer(nid,qid)
    # Eight classes incl Magitek, all with a real trainer and native class gate.
    for n,cls in enumerate(class_names):
        p,region=realm(n*3+1)
        nid=('teacher_magitek_v107' if n==0 and 'teacher_magitek_v107' in npcs else
             f'{p}_npc_3' if n==0 else
             'teacher_v107_'+cls.casefold().replace(' ','_'))
        if n:
            newnpcs[nid]=dict(name='Mistrz '+cls,room=p+'_03',teacher_class=cls,
                dialogue=f'Szkolenie {cls}. Przypomnij: skille. Questy: quest list.',
                specialist_quests=(),v10700_saga=True)
        for j in range(1,21):
            i=n*20+j
            qid=f'v10700_saga_cls_{i:03d}'
            row=common(p,region,(npcs[nid]['name'] if n==0 else newnpcs[nid]['name']),
                       f'{p}_mob_{1+(j-1)%10}',3+j%4,i)
            row.update(name=f'{cls}: Ścieżka Mistrzostwa {j}/20',required_class=cls,
                       description=f'Jako {cls} pokonaj {row["needed"]} × {mobs[row["target"]]["name"]}.')
            if j>1: row['requires_quest']=f'v10700_saga_cls_{i-1:03d}'
            newquests[qid]=row;offer(nid,qid)
    # Race gate is handled by SessionQuestOffersMixin, never edits race of old characters.
    for n,race in enumerate(race_names):
        p,region=realm(n*3+2)
        nid=f'{p}_npc_1';giver=npcs[nid]['name']
        for j in range(1,11):
            i=n*10+j;qid=f'v10700_saga_race_{i:03d}'
            row=common(p,region,giver,f'{p}_mob_{j}',3+(j%3),i)
            row.update(name=f'{race}: Dziedzictwo {j}/10',required_race=race,
                       description=f'Próba rasy {race}. Pokonaj {row["needed"]} × {mobs[row["target"]]["name"]}.')
            newquests[qid]=row;offer(nid,qid)
    # Real regional bosses rather than invented crypt instance IDs.
    for i in range(1,121):
        p,region=realm(i-1);nid=f'{p}_npc_4'
        mid=f'{p}_boss_{1+(i//30)%2}'
        row=common(p,region,npcs[nid]['name'],mid,1,i,repeat=False)
        row.update(name=f'Próba Głębi: {region} {i}/120',
            description=f'Pokonaj bossa {mobs[mid]["name"]}. Próbę można przejść samotnie.')
        newquests[f'v10700_saga_dungeon_{i:03d}']=row
        offer(nid,f'v10700_saga_dungeon_{i:03d}')
    # Hourly rotating region threats, with real native kill objectives.
    for i in range(1,61):
        p,region=realm(i-1);nid=f'{p}_npc_2';mid=f'{p}_mob_{1+(i%10)}'
        row=common(p,region,npcs[nid]['name'],mid,5+(i%4),i)
        row.update(name=f'Zagrożenie Chaosu: {region} {i}/60',
                   v10700_event_rotation=True, repeat_cooldown=3600)
        newquests[f'v10700_saga_events_{i:03d}']=row
        offer(nid,f'v10700_saga_events_{i:03d}')
    # True linear final plot, all 20 kills playable and predecessors retained.
    for i in range(1,21):
        p,region=realm(i+9);nid=f'{p}_npc_1';mid=f'{p}_boss_2'
        row=common(p,region,npcs[nid]['name'],mid,1,i,repeat=False)
        row.update(name=f'Serce Wiecznego Chaosu: Rozdział {i}/20')
        if i>1:row['requires_quest']=f'v10700_saga_final_{i-1:03d}'
        newquests[f'v10700_saga_final_{i:03d}']=row
        offer(nid,f'v10700_saga_final_{i:03d}')
    counts=Counter(qid.split('_')[2] for qid in newquests)
    if len(newquests)!=760 or set(newquests)!=ids or dict(counts)!=EXPECTED:
        raise RuntimeError(f'v107 saga: niespójne zadania {len(newquests)} {counts}')
    if any(q.get('target') not in mobs for q in newquests.values() if q['kind']=='kill'):
        raise RuntimeError('v107 saga: brak fizycznego celu')
    for nid in assign:
        if nid not in npcs and nid not in newnpcs:
            raise RuntimeError('v107 saga: brak oferenta '+nid)
    # Check new profession outputs before mutating any existing catalogs.
    from systems.profession_generations.chaos import install_products
    for i in range(1,9):
        if f'v10700_prof_product_{i}' in items:
            raise RuntimeError('v107: kolizja wyrobów profesji')
    # Preflight complete. Each NPC retains all his former offers and quest IDs.
    for nid,npc in newnpcs.items():
        offers=tuple(assign.get(nid,()))
        npc['specialist_quests']=offers
        npc['quest_chain']=offers
        if offers:npc['quest']=offers[0]
    install_products(items)
    quests.update(newquests)
    npcs.update(newnpcs)
    for nid,qids in assign.items():
        if nid in newnpcs:continue
        npc=npcs[nid]
        old=tuple(npc.get('specialist_quests') or ())
        npc['specialist_quests']=tuple(dict.fromkeys(old+tuple(qids)))
        # Do NOT turn all unrelated quests into a chained plotline.
    return {'quests':len(newquests),'npcs':len(newnpcs),**counts}
