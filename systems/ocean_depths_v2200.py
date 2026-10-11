# -*- coding: utf-8 -*-
"""Ocean 5.0 Głębie Lewiatana: four authored connected PvE expedition routes.

Uses stable room/mob/quest IDs; no procedural remapping, no PvP, no traps.
"""
from data import catalog_mutations as cm

REGIONS=(
 ('row','Rów Lewiatana','water',550,'Matka Otchłani','Łowca Głębin','Strażnik Pływów','Oko Rowu','v2200_leviathan_heart'),
 ('stolica','Zatopiona Stolica','dark',610,'Cesarz Zatopionego Tronu','Strażnik Pałacu','Zaklinacz Perłowy','Skarbnik Ruin','v2200_ancient_pearl'),
 ('rafy','Rafy Szeptów','poison',460,'Królowa Koralowych Gniazd','Koralowy Łowca','Zwiadowca Raf','Opiekun Raf','v2200_whisper_coral'),
 ('burze','Archipelag Wiecznych Burz','lightning',700,'Gromowładny Kolos','Wartownik Sztormu','Rycerz Burz','Mag Piorunów','v2200_storm_core'),
)
ROOM_LABELS=('Przystań Odkrywców','Sanktuarium Głębin','Podwodna Przeprawa','Komnata Starożytnego Władcy')


def _add(label,catalog,key,data):
    if key in catalog:raise ValueError('Ocean 5.0: zduplikowany identyfikator '+key)
    cm.catalog_assign(data,label,catalog,(key,))


def install(rooms,npcs,shops,mobs,spawns,quests,items,shop_sellers,navy):
    hub='v2000_ocean_hub'
    if hub not in rooms or 'northeast' in rooms[hub].get('exits',{}):
        raise RuntimeError('Ocean 5.0 wymaga wolnego północnego wschodu w Porcie Nieznanych Mórz.')
    _add('ROOMS',rooms,'v2200_depths_gate',{
        'name':'Brama Nowych Głębin','zone':'Ocean 5.0 — Głębie Lewiatana',
        'desc':'Cztery nowe trasy: północ Rów Lewiatana, wschód Zatopiona Stolica, południe Rafy Szeptów, zachód Archipelag Burz. Południowy zachód: port.',
        'exits':{'southwest':hub,'north':'v2200_row_0','east':'v2200_stolica_0','south':'v2200_rafy_0','west':'v2200_burze_0'},
        'recommended_mastery':400})
    cm.catalog_assign('v2200_depths_gate','ROOMS',rooms,(hub,'exits','northeast'))
    opposite=('south','west','north','east')
    for i,(slug,name,element,level,boss,*mobs_names,material) in enumerate(REGIONS):
        for k,label in enumerate(ROOM_LABELS):
            rid=f'v2200_{slug}_{k}'
            exits=({opposite[i]:'v2200_depths_gate'} if k==0 else {'west':f'v2200_{slug}_{k-1}'})
            if k<3:
                exits['south' if slug=='burze' and k==0 else 'east']=f'v2200_{slug}_{k+1}'
            if slug=='burze' and k==1:
                exits.pop('west',None);exits['north']='v2200_burze_0'
            _add('ROOMS',rooms,rid,{'name':f'{label} — {name}', 'zone':name,
                'generator_level':min(800,level+k*25),'recommended_mastery':min(800,level+k*25),
                'desc':f'{name}: {label}. Stałe, dwukierunkowe przejścia. W ostatniej komnacie strażnik. Bez pułapek.',
                'exits':exits, 'ocean_depths_v2200':slug})
        _add('ITEMS',items,material,{'name':{'row':'Serce Lewiatana','stolica':'Perła Pradawnej Stolicy','rafy':'Koral Szeptów','burze':'Rdzeń Wiecznych Burz'}[slug],
                  'type':'resource','price':None,'sell_silver':max(40000,level*120),
                  'desc':'Rzadki materiał z wypraw Oceanu 5.0. Wysoka wartość handlowa.'})
        for j,mname in enumerate(mobs_names):
            key=f'v2200_{slug}_mob_{j}'
            power=min(800,level+j*35)
            _add('MOB_TEMPLATES',mobs,key,{
                'name':mname,'max_hp':power*(580+120*j),'damage':power*(38+4*j),
                'generator_level':power,'damage_type':'magic' if j==2 else 'physical',
                'attack_elements_v11339':(element,),'rank':'elite' if j==2 else 'normal',
                'tactical_role_v2200':('obronca','dowodca','uzdrowiciel')[j],
                'stat_reward':power*230,'class_xp_reward':power*3400,'soul_reward':power*1300,
                'silver':power*800,'gold':0,'mithril':0,'fame_target':True,
                'drops':{'soul_shard':.45,material:.05},'quest_target':key,
                'stationary_mob':True,'auto_aggro':False})
            spawns.append((f'v2200_{slug}_2',key))
        key=f'v2200_{slug}_boss'
        _add('MOB_TEMPLATES',mobs,key,{
            'name':boss,'max_hp':min(800,level+130)*10500,'damage':min(800,level+130)*180,
            'generator_level':min(800,level+130),'rank':'world_boss',
            'boss':True,'world_boss':True,'boss_mechanic':'elemental_overdrive',
            'damage_type':'magic','attack_elements_v11339':(element,),
            'fame_target':True,'stat_reward':level*650,'class_xp_reward':level*10000,
            'soul_reward':level*4800,'silver':level*6000,'gold':0,'mithril':0,
            'drops':{'soul_shard':1.0,material:1.0},'quest_target':key,
            'stationary_mob':True,'auto_aggro':False})
        spawns.append((f'v2200_{slug}_3',key))
        qid=f'v2200_{slug}_hunt';npc=f'v2200_{slug}_guide'
        _add('QUESTS',quests,qid,{
            'name':f'Wyprawa w głębiny: {name}','giver':f'Przewodnik {name}',
            'kind':'kill','target':key,'needed':1,
            'description':f'Pokonaj {boss} w prawdziwej walce PvE. Drużyna otrzymuje własny postęp.',
            'reward_silver':level*6500,'reward_gold':0,'reward_mithril':0,
            'reward_items':{'soul_shard':4},'repeatable':True,'repeat_cooldown':7200})
        _add('NPCS',npcs,npc,{'name':f'Przewodnik {name}', 'room':f'v2200_{slug}_0',
            'dialogue':'Prowadzę łowy na władcę tego regionu. Za pokonanie dostaniesz złoto i materiały.',
            'quest_chain':(qid,)})
        code=f'glebiny_{slug}'
        if code in navy.ENEMIES:raise RuntimeError('Kolizja celu flot: '+code)
        navy.ENEMIES[code]=(f'Flota: {name}',level*6500,level*130,level*1800,'monster' if i in (0,2) else 'siege',level*530)
        navy.MATERIALS[code]=material
    return {'regions':len(REGIONS),'rooms':1+4*4,'mobs':4*4,'quests':4}
