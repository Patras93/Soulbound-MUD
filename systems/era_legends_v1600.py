# -*- coding: utf-8 -*-
"""Soulbound 1.60: seven authored, connected PvE expansions.

Every reward uses the existing quest, drop, boss and bestiary engines.  No
changes to experience requirements, character saves or old room identities.
"""
from __future__ import annotations
import time
from data import catalog_mutations as cm

UNDERGROUND = (
 ('bazalt','Księstwo Bazaltowego Serca','Gildia Kamiennych Run','dark',480,
  ('Zbrojownia Run','Sala Kamiennych Tronów','Targ Mistrzów','Komnata Wiecznych Pieców'),
  ('Strażnik Kamiennych Run','Królowa Bazaltowego Serca')),
 ('grzyby','Królestwo Świetlistych Grzybów','Krąg Zarodników','poison',520,
  ('Świetlisty Zagajnik','Niebieska Pieczara','Zielony Pałac','Źródło Żywych Zarodników'),
  ('Łowca Ciemnych Zarodników','Matka Grzybowych Koron')),
 ('krysztal','Kryształowa Monarchia','Klan Lustrzanych Ostrzy','ice',560,
  ('Kopalnia Luster','Galeria Kryształów','Dźwięczące Arkady','Ołtarz Siedmiu Kryształów'),
  ('Strażnik Lustrzanej Bramy','Cesarz Kryształowych Serc')),
 ('glebia','Imperium Bezdennych Żył','Straż Bezdennego Tronu','earth',640,
  ('Przeprawa Starych Górników','Most Nad Otchłanią','Sala Królewskich Kotłów','Wrota Bezdennej Kuźni'),
  ('Żelazny Sędzia Otchłani','Władczyni Bezdennego Imperium')),
)
FRONTS = (
 ('ork','Wolne Klany Gor-Khaz','v1300_orc_outer','v1300_orc_throne_boss','v1600_front_orc'),
 ('bazalt','Przymierze Kamiennych Miast','v1600_bazalt_2','v1600_bazalt_monarch','v1600_front_bazalt'),
 ('szron','Straż Północnej Zorzy','v1500_szron_0_0','v1500_szron_boss_1','v1600_front_szron'),
 ('ocean','Przymierze Morskich Latarni','v1600_ocean_pier','v1600_ocean_leviathan','v1600_front_ocean'),
)
HUNTS = (
 ('ork','v1300_orc_throne_boss','Ślad Czterech Klanów'),
 ('szron','v1500_szron_boss_5','Korona Nocy'),
 ('zar','v1500_zar_boss_5','Płonąca Korona'),
 ('korzen','v1500_korzen_boss_5','Pieczęć Starego Lasu'),
 ('gwiazda','v1500_gwiazda_boss_5','Gwiezdny Spadek'),
 ('bazalt','v1600_bazalt_monarch','Kamienna Władczyni'),
 ('grzyby','v1600_grzyby_monarch','Matka Zarodników'),
 ('krysztal','v1600_krysztal_monarch','Kryształowa Korona'),
 ('glebia','v1600_glebia_monarch','Serce Otchłani'),
 ('ocean','v1600_ocean_leviathan','Oko Wielkich Głębin'),
)
INVASIONS = (
 ('ork','Najazd Popielnych Jeźdźców','v1300_orc_border','physical','earth',510),
 ('bazalt','Wojna Kamiennych Kolosów','v1600_bazalt_1','physical','dark',565),
 ('ocean','Szturm Głębinowego Zakonu','v1600_ocean_pier','magic','ice',610),
 ('szron','Pochód Burzowych Widm','v1500_szron_0_0','magic','lightning',670),
)
INVASION_SECONDS = 4*3600


def add(catalog_label,catalog,id,data):
    if id in catalog:
        raise RuntimeError('Soulbound 1.60: duplicate '+str(id))
    cm.catalog_assign(data,catalog_label,catalog,(id,))


def add_mob(mobs,spawns,id,name,room,level,element,loot,superboss=False,spawn=True):
    hp=max(5000,level*(3800 if superboss else 1700))
    add('MOB_TEMPLATES',mobs,id,{
        'name':name,'max_hp':hp,'damage':level*(95 if superboss else 46),
        'damage_type':'magic' if element in ('dark','ice','poison','lightning') else 'physical',
        'attack_elements_v11339':(element,),
        'boss':True,'rank':'world_boss' if superboss else 'boss','world_boss':superboss,
        'generator_level':min(800,level),
        'stat_reward':level*(290 if superboss else 130),
        'class_xp_reward':level*(3600 if superboss else 1900),
        'soul_reward':level*(1400 if superboss else 700),
        'silver':level*(900 if superboss else 450),'gold':0,'mithril':0,
        'drops':{loot:(.9 if superboss else .45),'soul_shard':1.0},
        'quest_target':id,'quest_targets':(id,),
        'boss_mechanic':'elemental_overdrive',
        'boss_mechanic_text':'Przeciwnik zmienia fazy walki i atakuje żywiołem '+element+'.',
        'stationary_mob':True,'auto_aggro':False,'v1600_boss':True,
    })
    if spawn:spawns.append((room,id))


def add_quest(quests,id,title,giver,target,needed,level,*,repeat=True):
    add('QUESTS',quests,id,{
        'name':title,'giver':giver,'kind':'kill','target':target,'needed':needed,
        'description':'Pokonaj rzeczywistych przeciwników wskazanych w zleceniu. Zalicza walkę drużyny.',
        'reward_silver':int(level)*900*max(1,needed),'reward_gold':0,'reward_mithril':0,
        'repeatable':repeat,'repeat_cooldown':7200,
    })


def install_era_legends_v1600(rooms,npcs,shops,mobs,spawns,quests,items,shop_sellers):
    """Register 7 independent systems; preserve original roads and progression."""
    # (0) Surface connection repairing the unreachable orc continent in 1.50.1.
    hub='v1200_four_winds_gate'; valdoria='v1300_lost_border'
    if hub not in rooms or valdoria not in rooms:
        raise RuntimeError('1.60: missing Four Winds or Valdoria entrance')
    if 'northeast' in rooms[hub]['exits'] or 'south' in rooms[valdoria]['exits']:
        raise RuntimeError('1.60: surface road would overwrite an existing exit')
    road_names=('Gościniec Wielkich Wypraw','Kamienny Most Traktatów',
                'Warta Północnych Rubieży','Wioska Wędrownych Kupców',
                'Granica Zapomnianej Valdorii')
    for index,name in enumerate(road_names):
        rid=f'v1600_road_{index+1}'
        exits={}
        if index:exits['west']=f'v1600_road_{index}'
        if index<4:exits['east']=f'v1600_road_{index+2}'
        if index==0:exits['southwest']=hub
        if index==4:exits['north']=valdoria
        add('ROOMS',rooms,rid,{'name':name,'zone':'Trakt Czterech Wiatrów',
            'desc':'Bezpieczny lądowy szlak łączy główne królestwa z Valdorią i Wolnymi Klanami Gor-Khaz. '
                   'Nie wymaga przechodzenia przez Kryptę i nie omija żadnej walki w podziemiach.',
            'exits':exits,'recommended_mastery':140})
    cm.catalog_assign('v1600_road_1','ROOMS',rooms,(hub,'exits','northeast'))
    cm.catalog_assign('v1600_road_5','ROOMS',rooms,(valdoria,'exits','south'))
    from core.mines_threat import GUIDE_DESTINATION_ALIASES
    for alias in ('orki','orkowie','kraina orkow','gor khaz','gor-khaz','orc'):
        GUIDE_DESTINATION_ALIASES[alias]='v1300_orc_border'
    GUIDE_DESTINATION_ALIASES['valdoria']='v1300_lost_border'
    # (1) Four underground realms: own towns and bosses, branch via a real doorway.
    entrance='v1600_road_3'
    rooms[entrance]['exits']['down']='v1600_deep_hub'
    add('ROOMS',rooms,'v1600_deep_hub',{'name':'Wielka Brama Podziemnych Królestw',
      'zone':'Podziemne Królestwa','desc':'Rozdroże czterech dawnych krain; nie ma losowych pułapek ani blokady solo.',
      'exits':{'up':entrance,'north':'v1600_bazalt_0','east':'v1600_grzyby_0',
               'south':'v1600_krysztal_0','west':'v1600_glebia_0'}})
    for realm,title,faction,element,level,places,(guard,queen) in UNDERGROUND:
        mat=f'v1600_ore_{realm}'
        add('ITEMS',items,mat,{'name':f'Legendarne Złoże — {title}', 'type':'material',
            'rarity':'legendary','price':2400000+level*2500,
            'desc':f'Rzadki minerał krainy {title}. Wartościowy łup i materiał handlowy.'})
        for idx in range(24):
            room=f'v1600_{realm}_{idx}'; pattern=places[idx%len(places)]
            exits={}
            if idx:exits['south' if realm=='glebia' else 'west']=f'v1600_{realm}_{idx-1}'
            if idx<23:exits['north' if realm=='glebia' else 'east']=f'v1600_{realm}_{idx+1}'
            if idx==0:
                directions={'bazalt':'south','grzyby':'west','krysztal':'north','glebia':'east'}
                exits={d:y for d,y in exits.items() if y is not None}
                exits[directions[realm]]='v1600_deep_hub'
            add('ROOMS',rooms,room,{'name':f'{pattern} — {title}, sektor {idx+1}',
                'zone':title,'desc':f'Autorska lokacja podziemnej cywilizacji {faction}. '
                    'Mieszkańcy handlują i walczą z oddziałami dawnych tyranów. '
                    'Wzdłuż szlaku znajdują się drogowskazy i jawne przejścia.',
                'exits':exits,'recommended_mastery':min(800,level+idx*9)})
        # Real, varied regional patrols, each with kills, drops and full combat
        # scaling through the normal MobState encounter engine.
        for patrol_index, patrol_name in enumerate((
            'Zwiadowca Zapomnianych Run','Żelazny Strażnik Progu',
            'Mroczny Poszukiwacz Żył','Elitarny Łowca Starożytnych',
            'Weteran Zagubionej Armii','Szaman Głębokich Jaskiń',
        )):
            tid=f'v1600_{realm}_patrol_{patrol_index+1}'
            patrol_level=min(800,level+patrol_index*28)
            add('MOB_TEMPLATES',mobs,tid,{
                'name':f'{patrol_name} — {title}',
                'max_hp':patrol_level*550,'damage':patrol_level*35,
                'damage_type':'magic' if patrol_index%2 else 'physical',
                'attack_elements_v11339':(element,),
                'rank':'elite' if patrol_index>=3 else 'normal',
                'generator_level':patrol_level,
                'stat_reward':patrol_level*135,'class_xp_reward':patrol_level*1800,
                'soul_reward':patrol_level*650,'silver':patrol_level*380,
                'gold':0,'mithril':0,'drops':{mat:.12+.025*patrol_index,'soul_shard':.05},
                'quest_target':tid,'stationary_mob':True,'auto_aggro':False,
                'v1600_regional_enemy':True,
            })
            for sector in (1+patrol_index*3,2+patrol_index*3,3+patrol_index*3):
                spawns.append((f'v1600_{realm}_{sector}',tid))
        guardian=f'v1600_{realm}_guard'; monarch=f'v1600_{realm}_monarch'
        add_mob(mobs,spawns,guardian,guard,f'v1600_{realm}_10',level,element,mat)
        add_mob(mobs,spawns,monarch,queen,f'v1600_{realm}_23',level+105,element,mat,True)
        leader=f'Kronikarz {title}'
        add('NPCS',npcs,f'v1600_{realm}_scribe',{'name':leader,'room':f'v1600_{realm}_1',
            'dialogue':'Nowe królestwa poznaje się przez walki i zapisy historii.',
            'quest_chain':(f'v1600_{realm}_quest_1',f'v1600_{realm}_quest_2')})
        add_quest(quests,f'v1600_{realm}_quest_1','Wyprawa do '+title,leader,guardian,1,level)
        add_quest(quests,f'v1600_{realm}_quest_2','Tron '+title,leader,monarch,1,level+105)
        trade=f'v1600_{realm}_trader'; trg=f'v1600_{realm}_2'
        add('NPCS',npcs,trade,{'name':'Kupiec Podziemny '+title,'room':trg,
            'shopkeeper':True,'dialogue':'Wymieniaj łupy za złoto i przygotuj się na dalszą wyprawę.'})
        shops[trg]=['healing_potion','mana_potion','soul_elixir','iron_guard']
        shop_sellers[trg]=trade
    # (2) PvE war fronts based on genuine kills. Repeatable, shared-by-party
    # quest records; nothing turns on player-versus-player combat.
    for slug,title,room,target,qid in FRONTS:
        giver='Dowódca Frontu '+title
        add('NPCS',npcs,f'v1600_war_npc_{slug}',{'name':giver,'room':room,
            'dialogue':'Wojna PvE jest otwarta samotnym i drużynom. Wpisz quest list.',
            'quest':qid})
        add_quest(quests,qid,'Wojna PvE: '+title,giver,target,1,560)
    # (3) Guild castles expand EXISTING per-guild estates and building levels,
    # not a second guild economy nor fake independent character progression.
    # Actual rooms are attached when a member visits their own estate.
    # (4) Mercenary 6.0 uses the unchanged 100% owner power and an additional
    # reactive boss-defense tactic installed by Session's existing combat loop.
    # (5) New sea-port route, bosses, materials, and Fleet 5.0 battles.
    port='v0800_harbor'
    if port not in rooms or 'down' in rooms[port]['exits']:
        raise RuntimeError('1.60: ocean port missing or route occupied')
    rooms[port]['exits']['down']='v1600_ocean_pier'
    ocean_names=(
      'Pomost Wielkich Głębin','Świątynia Zanurzonych Żagli','Skarbiec Rafy Duchów',
      'Miasto Srebrnych Meduz','Zatoka Rozbitych Koron','Pałac Bezdennych Prądów',
      'Pochylony Obelisk Lewiatana','Sanktuarium Morskiego Cesarza',
    )
    add('ITEMS',items,'v1600_ocean_pearl',{'name':'Perła Morskiego Cesarza','type':'material',
        'rarity':'legendary','price':7200000,'desc':'Niezwykle cenna perła z najgłębszych ruin.'})
    for i,name in enumerate(ocean_names):
        exits={}
        if i:exits['west']=f'v1600_ocean_{i-1}' if i>1 else 'v1600_ocean_pier'
        if i<7:exits['east']=f'v1600_ocean_{i+1}'
        if i==0:exits['up']=port
        add('ROOMS',rooms,'v1600_ocean_pier' if i==0 else f'v1600_ocean_{i}',{
            'name':name,'zone':'Ocean 5.0 — Wielkie Głębiny',
            'desc':'Wody pradawnego archipelagu ukrywają historie dawnych flot. '
                   'Bez pułapek, z przeciwnikami i możliwym powrotem normalną drogą.',
            'exits':exits,'recommended_mastery':460+20*i})
    add_mob(mobs,spawns,'v1600_ocean_sentinel','Strażniczka Tronu Meduz','v1600_ocean_3',610,
            'ice','v1600_ocean_pearl')
    add_mob(mobs,spawns,'v1600_ocean_leviathan','Morski Cesarz Lewiatan','v1600_ocean_7',755,
            'dark','v1600_ocean_pearl',True)
    giver='Admiralissa Wielkich Głębin'
    add('NPCS',npcs,'v1600_ocean_npc',{'name':giver,'room':'v1600_ocean_pier',
        'dialogue':'Wielkie głębiny odkrywa się pod wodą i podczas bitew flot.',
        'quest_chain':('v1600_ocean_task_1','v1600_ocean_task_2')})
    add_quest(quests,'v1600_ocean_task_1','Próba Strażniczki Rafy',giver,'v1600_ocean_sentinel',1,610)
    add_quest(quests,'v1600_ocean_task_2','Serce Morskiego Cesarza',giver,'v1600_ocean_leviathan',1,755)
    from systems import ocean4_v1350
    for key,name,hp,dmg,reward,style,pressure,mat in (
        ('glebiny','Wojenna Flota Głębin',2100000,46000,420000,'siege',235000,'v1600_ocean_pearl'),
        ('meduzy','Legion Kryształowych Meduz',2750000,54000,570000,'monster',280000,'v1600_ocean_pearl'),
        ('cesarz','Armada Morskiego Cesarza',3800000,73000,720000,'monster',360000,'v1600_ocean_pearl'),
    ):
        if key in ocean4_v1350.ENEMIES:raise RuntimeError('1.60: duplicate naval encounter '+key)
        ocean4_v1350.ENEMIES[key]=(name,hp,dmg,reward,style,pressure)
        ocean4_v1350.MATERIALS[key]=mat
    # (6) Timed invasions: templates are dormant unless their time slot is
    # active. World asks again when visitors actually enter the event region.
    for slug,title,room,damage_type,element,level in INVASIONS:
        add_mob(mobs,spawns,'v1600_invasion_'+slug,title,room,level,element,
                'soul_shard',True,spawn=False)
    # (7) Real legendary hunt objectives; existing bestiary stores actual kill
    # counts and the same quest engine grants rewards to eligible party members.
    for slug,target,title in HUNTS:
        if target not in mobs:raise RuntimeError('1.60 missing hunt boss '+target)
        giver='Mistrz Łowów '+title
        room=('v1600_deep_hub' if slug in ('bazalt','grzyby','krysztal','glebia')
              else ('v1600_ocean_pier' if slug=='ocean' else 'v1600_road_4'))
        add('NPCS',npcs,f'v1600_hunter_npc_{slug}',{'name':giver,'room':room,
            'dialogue':'Wytrop legendarnego przeciwnika, zapisz go w bestiariuszu i odbierz nagrodę.',
            'quest':f'v1600_hunt_{slug}'})
        add_quest(quests,f'v1600_hunt_{slug}','Łowcy Legend: '+title,giver,target,1,700)
    return {'surface_road':len(road_names),'underground_rooms':len(UNDERGROUND)*24+1,
      'underground_bosses':len(UNDERGROUND)*2,'underground_patrol_templates':len(UNDERGROUND)*6,'war_fronts':len(FRONTS),
      'ocean_rooms':len(ocean_names),'ocean_enemies':3,
      'invasions':len(INVASIONS),'hunts':len(HUNTS)}


def active_invasion_v1600(now=None):
    slot=int((time.time() if now is None else now)//INVASION_SECONDS)
    slug,title,room,style,element,level=INVASIONS[slot%len(INVASIONS)]
    return {'slug':slug,'title':title,'room_id':room,'template_id':'v1600_invasion_'+slug,
        'slot':slot,'expires_at':(slot+1)*INVASION_SECONDS}
