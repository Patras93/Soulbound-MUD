# -*- coding: utf-8 -*-
"""v9: real world/catalog/weapon/SQLite audit without mutating production data."""
import tempfile
from pathlib import Path
from collections import Counter

def run_regression(runtime=None):
    if runtime is None:
        import server as runtime
    from core.classes_skills import (CLASSES,RACES,CLASS_SKILLS,SOUL_WEAPON_ATTACK_TECHNIQUES,
                                      CLASS_STARTING_STAT_BONUSES,starting_hp_mana_for)
    from core.character_resources import race_passive_profile,class_passive_profile
    from core.progression_600 import SOUL_TIER_TRAITS_BY_CLASS, soul_weapon_trait_for_tier_v11193
    from systems.new_heroes_v900 import NEW_CLASSES,NEW_RACES, EQUIPMENT
    from systems.class_legend_paths_v900 import QUEST_IDS,MENTOR_ROOMS,ALL_IDS
    from systems.equipment_crafting import class_equipment_base_stat_triplet,class_equipment_flat_power_channels
    from world.legends_v3200 import _reachable
    from storage.database import Database
    checks=0
    def ck(flag,reason):
        nonlocal checks
        if not flag:raise AssertionError('v9: '+reason)
        checks+=1
    ck(runtime.VERSION in ('9.00.0','10.00.0','10.00.1','10.00.2','11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18','11.00.19','11.00.20','12.00.0','12.00.1','12.00.2','12.00.3','12.00.4','12.00.5','12.00.6','12.00.7','12.00.8','12.00.9','12.00.10','12.00.11', '12.00.12','12.00.13','12.10.0','13.00.0','13.10.0','14.00.0','15.00.0','15.10.0','15.20.0','15.30.0','15.40.0','16.00.0','17.00.0','18.00.0','19.00.0','20.00.0','21.00.0','22.00.0','35.00.0','35.00.1','35.00.2','35.00.3','35.00.4',),'release identity')
    ck(len(CLASSES)==22 and len(RACES)==22,'22 classes/races')
    ck(len({x[0] for x in CLASSES})==22 and len({x[0] for x in RACES})==22,'unique names')
    ck(len(runtime.QUESTS)>=6573 and len(ALL_IDS)==960,f'5605+960 quests: runtime={len(runtime.QUESTS)}, new={len(ALL_IDS)}')
    ck(len(QUEST_IDS)==8 and all(len(v)==120 for v in QUEST_IDS.values()),'8x120 sagas')
    ck(len(runtime.QUESTS.keys() & set(ALL_IDS))==960,'no lost new quests')
    ck(len(SOUL_TIER_TRAITS_BY_CLASS)==22,'all 22 class Soul Weapon trait profiles')
    ck(set(CLASS_SKILLS)=={c[0] for c in CLASSES},'skill coverage')
    active_rooms=Counter(npc.get('room') for npc in runtime.NPCS.values())
    reachable=_reachable(runtime.ROOMS)
    from systems.class_legend_paths_v800 import MENTOR_ROOMS as OLD_MENTOR_ROOMS
    ck(all(len(runtime.ROOMS[rid]['exits'])==1 for rid in OLD_MENTOR_ROOMS.values()),
       'v8 mentor rooms still have exactly one exit')
    for klass,kind,weapon,power,slug,theme,scale,passive,value,element,titles in NEW_CLASSES:
        ck((klass,kind,weapon,power) in CLASSES,'class registration '+klass)
        ck(SOUL_WEAPON_ATTACK_TECHNIQUES[klass]==titles[0],'unique auto attack '+klass)
        ck(all(soul_weapon_trait_for_tier_v11193(i,klass)['name'].endswith(theme) for i in (1,25,60,80)), 'no Wojownik weapon trait fallback '+klass)
        ck(len(SOUL_TIER_TRAITS_BY_CLASS[klass])==80,'full soul tiers '+klass)
        ck(class_passive_profile(klass)=={'kind':passive,'value':value},'authored class passive '+klass)
        ck(sum(CLASS_STARTING_STAT_BONUSES[klass].values())==9,'9-point class stat budget '+klass)
        skills=CLASS_SKILLS[klass]
        ck(len(skills)==(245 if runtime.VERSION.startswith('35.') or runtime.VERSION in ('11.00.0','11.00.1','11.00.2','11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18','11.00.19','11.00.20','12.00.0','12.00.1','12.00.2','12.00.3','12.00.4','12.00.5','12.00.6','12.00.7','12.00.8','12.00.9','12.00.10','12.00.11', '12.00.12','12.00.13','12.10.0','13.00.0','13.10.0','14.00.0','15.00.0','15.10.0','15.20.0','15.30.0','15.40.0','16.00.0','17.00.0','18.00.0','19.00.0','20.00.0','21.00.0','22.00.0',) else 243) and skills[0]['unlock']==1 and skills[-1]['unlock']==800,'three skills per mastery 1-800 '+klass)
        ck(all(sum(int(s['unlock'])==level for s in skills if not s['id'].startswith('v1100_tech_'))==3 for level in __import__('core.classes_skills',fromlist=['_V0922_MASTERY_LEVELS'])._V0922_MASTERY_LEVELS),'all original mastery tiers preserved '+klass)
        ck(len({s['name'] for s in skills})==len(skills) and all(not __import__('re').search(r'\s\d+$',s['name']) for s in skills),'descriptive unique NVDA skill names '+klass)
        ck(len({s['id'] for s in skills})==len(skills),'unique skills '+klass)
        ck(all(int(s.get('cooldown',-1))==0 for s in skills),'global no cooldown retained '+klass)
        ck(any(s['unlock']>=500 and s['kind'] in ('damage','aoe_damage','execute') for s in skills),'real endgame offense '+klass)
        ck(class_equipment_base_stat_triplet(klass)==(('intelligence','willpower','constitution') if kind=='magic' else ('strength','dexterity','constitution')),'EQ stat split '+klass)
        power_channels=class_equipment_flat_power_channels(klass,100,'hands')
        ck((power_channels['attack']>0)==(kind=='physical') and (power_channels['magic_attack']>0)==(kind=='magic'), 'no hybrid EQ except Mec '+klass)
        cid=MENTOR_ROOMS[klass];nid='v900_legend_mentor_'+slug;teacher_id='teacher_v900_'+slug
        ck(cid in reachable and active_rooms[cid]==1,'mentor reachable alone '+klass)
        ck(runtime.NPCS[nid].get('v800_required_class')==klass,'mentor class lock '+klass)
        teach=runtime.NPCS[teacher_id]
        ck(teach['teacher_class']==klass and active_rooms[teach['room']]==1 and teach['room'] in reachable,'independent teacher '+klass)
        ids=QUEST_IDS[klass]
        ck(len(ids)==120 and len(set(ids))==120,'distinct saga '+klass)
        for index,qid in enumerate(ids):
            q=runtime.QUESTS[qid]
            ck(q['required_class']==klass and q['v800_stage']==index+1,'correct class and stage '+qid)
            ck(q.get('requires_quest')==(ids[index-1] if index else None),'strict sequence '+qid)
            ck(q['kind'] in ('kill','collect','explore_frontier') and q['needed']>0,'actual event '+qid)
            ck(q['reward_silver']>0 and not q['repeatable'],'worthwhile unique reward '+qid)
    for name,desc,s,d,c,i,w,p_kind,p_value in NEW_RACES:
        row=next(r for r in RACES if r[0]==name)
        ck(row[2:]==(s,d,c,i,w) and sum(row[2:])==50,'authored race stats '+name)
        ck(race_passive_profile(name)=={'kind':p_kind,'value':p_value},'race passive '+name)
        for cls in CLASSES:
            hp,mana=starting_hp_mana_for(row,cls)
            ck(hp>0 and mana>=0,'real start stats '+name+'/'+cls[0])
    with tempfile.TemporaryDirectory(prefix='soulbound_v900_') as d:
        path=Path(d)/'heroes.db';db=Database(str(path))
        account=db.create_account('TesterNowychBohaterow9','VeryLongSafePassword_V900!')
        cases={k:'Wędrowiec' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        a,_=db.create_character_for_master(account,'PaladynProby9',next(r for r in RACES if r[0]=='Wampir'),next(c for c in CLASSES if c[0]=='Paladyn'),cases)
        b,_=db.create_character_for_master(account,'MagProby9',RACES[0],next(c for c in CLASSES if c[0]=='Mag'),cases)
        ch=db.character_for_account(a)
        ck(ch['class_name']=='Paladyn' and ch['soul_weapon']=='Święty Miecz Duszy' and ch['race']=='Wampir','stored class/race/weapon')
        q=QUEST_IDS['Paladyn'][0]
        db.start_quest(a,q)
        ck(db.quest(a,q) is not None,'start real v9 quest')
        ck(db.quest(b,q) is None,'separate characters')
        ck(db.increment_class_legend_kill_v800(a,'Paladyn',1),'Paladyn combat quest kill')
        ck(db.quest(a,q)['progress']==1,'real SQLite kill increment')
        db.conn.close()
        db=Database(str(path))
        ck(db.quest(a,q)['progress']==1 and db.quest(b,q) is None,'SQLite restart isolation')
        ck(db.character_for_account(a)['soul_weapon']=='Święty Miecz Duszy','weapon remains after restart')
        ck(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        db.conn.close()
    return checks

if __name__=='__main__':
    print('V9 BOHATEROW',run_regression(),'PASS')
