# -*- coding: utf-8 -*-
"""1.80.0: authored Chaos gods, 14 class masteries and elemental reactions.

All additions use the existing combat/quest/drop engines and keep historical
levels, SQLite rows and rewards intact.
"""
from __future__ import annotations
from data import catalog_mutations as cm
from core.classes_skills import CLASSES

CHAOS_REALMS = (
    ('popiol', 'Sanktuarium Popiołu', 'fire', 630,
     ('Hetman Płomiennej Korony','Strażnik Rozżarzonego Serca','Azhur, Bóg Żywego Ognia')),
    ('szron', 'Pałac Pękniętego Szronu', 'ice', 665,
     ('Widmo Wiecznej Zamieci','Prorok Kryształowego Snu','Nivara, Bogini Zimy')),
    ('burza', 'Cytadela Błyskawic', 'lightning', 705,
     ('Łowca Burzowych Głosów','Hegemon Gromowej Kuźni','Voltrax, Bóg Burz')),
    ('pustka', 'Katedra Rozdartej Pustki', 'dark', 750,
     ('Strażnik Zapomnianych Imion','Sędzia Czarnej Gwiazdy','Orrath, Pan Chaosu')),
)

# One clearly distinct combat technique per class; old skills aren't overwritten.
CLASS_MASTERY = {
 'Wojownik': ('Przełamanie Przysięgi','strike','physical'),
 'Berserker': ('Furia Krwawego Ostrza','strike','physical'),
 'Łotrzyk': ('Egzekucja Cienia','strike','physical'),
 'Łowca': ('Sokoli Deszcz','strike','physical'),
 'Mnich': ('Uderzenie Siedmiu Bram','strike','physical'),
 'Strażnik': ('Niezłomna Cytadela','guard','physical'),
 'Mag': ('Arkaniczne Załamanie','strike','arcane'),
 'Nekromanta': ('Żniwa Wiecznych Dusz','strike','dark'),
 'Kapłan': ('Światło Odrodzenia','heal','holy'),
 'Czarownik': ('Otchłanny Rozbłysk','strike','dark'),
 'Druid': ('Serce Prastarego Gaju','heal','nature'),
 'Psionik': ('Pęknięcie Umysłu','strike','arcane'),
 'Mec': ('Rdzeń Absolutny','guard','physical'),
 'Inżynier': ('Bastion Automatu','guard','physical'),
}

REACTIONS = {
 frozenset(('fire','ice')): ('Szok Termiczny', .09),
 frozenset(('ice','lightning')): ('Kruche Wyładowanie', .10),
 frozenset(('fire','lightning')): ('Burza Plazmy', .10),
 frozenset(('dark','holy')): ('Zaćmienie Duszy', .08),
 frozenset(('arcane','lightning')): ('Przeciążenie Runiczne', .09),
 frozenset(('poison','fire')): ('Spalona Toksyna', .08),
}
ELEMENT_ALIASES = {
 'ogien':'fire','ognia':'fire','fire':'fire','lod':'ice','lodu':'ice','ice':'ice',
 'blyskawice':'lightning','blyskawic':'lightning','lightning':'lightning',
 'dark':'dark','mrok':'dark','holy':'holy','arcane':'arcane',
 'poison':'poison','trucizna':'poison',
}


def put(catalog_name,catalog,key,value):
    if key in catalog:raise RuntimeError('1.80 duplicated catalog ID '+key)
    cm.catalog_assign(value,catalog_name,catalog,(key,))


def install_chaos_v1800(rooms,npcs,shops,mobs,spawns,quests,items,shop_sellers):
    """Four accessible wings, three distinct fixed boss encounters each."""
    anchor='v1700_city_market'
    assert anchor in rooms and 'west' not in rooms[anchor]['exits']
    cm.catalog_assign('v1800_portal','ROOMS',rooms,(anchor,'exits','west'))
    put('ROOMS',rooms,'v1800_portal',{'name':'Rozdroże Bogów Chaosu','zone':'Wojny Bogów Chaosu',
        'desc':'Cztery jawne, ręcznie opisane ścieżki. Samotna postać i drużyna mają jednakowy dostęp. Bez pułapek.',
        'exits':{'east':anchor,'north':'v1800_popiol_0','south':'v1800_szron_0',
                 'west':'v1800_burza_0','up':'v1800_pustka_0'}})
    ways=(('north','south'),('south','north'),('west','east'),('up','down'))
    for realm, (slug,title,element,level,bosses) in enumerate(CHAOS_REALMS):
        forward,back=ways[realm]
        trophy=f'v1800_{slug}_sigil'
        put('ITEMS',items,trophy,{'name':'Pieczęć '+title,'type':'material',
            'rarity':'legendary','price':2500000+level*1000,
            'desc':'Trofeum z Wojny Bogów Chaosu. Zachowuje normalny drop i ekonomię gry.'})
        hunter=f'Kronikarz Wojny Chaosu — {title}'
        ids=[]
        for j in range(4):
            room=f'v1800_{slug}_{j}'
            exits={back:'v1800_portal' if j==0 else f'v1800_{slug}_{j-1}'}
            if j<3:exits[forward]=f'v1800_{slug}_{j+1}'
            put('ROOMS',rooms,room,{'name':f'{title} — '+('Przedmurze','Sala Przysiąg','Bastion Mocy','Tron Chaosu')[j],
                'zone':title,'desc':f'Szlak {title}; trzy widoczne walki z bossami, fazy 75/50/25% HP. '
                'Połączenia są dwukierunkowe i nie ma losowych pułapek.',
                'exits':exits,'recommended_mastery':min(800,level+j*20)})
        for j,name in enumerate(bosses):
            mid=f'v1800_{slug}_boss_{j}'
            power=level+j*44
            super_boss=j==2
            put('MOB_TEMPLATES',mobs,mid,{
                'name':name,'max_hp':power*(6500 if super_boss else 3000),
                'damage':power*(145 if super_boss else 85),'damage_type':'magic',
                'attack_elements_v11339':(element,'dark' if j==1 else 'lightning'),
                'generator_level':min(800,power),'boss':True,'world_boss':super_boss,
                'rank':'world_boss' if super_boss else 'boss',
                'boss_mechanic':'elemental_overdrive',
                'boss_mechanic_text':'Bogowie Chaosu: trzy fazy przy 75%, 50% i 25% HP; kolejne kontrataki i rezonanse.',
                'v1800_chaos_boss':True,'v1800_chaos_element':element,
                'stat_reward':power*450,'class_xp_reward':power*6300,
                'soul_reward':power*2700,'silver':power*2500,'gold':0,'mithril':0,
                'drops':{trophy:1.0,'soul_shard':1.0,'v1700_dragon_tooth':.45},
                'quest_target':mid,'stationary_mob':True,'auto_aggro':False})
            spawns.append((f'v1800_{slug}_{j+1}',mid))
            quest=f'v1800_hunt_{slug}_{j}';ids.append(quest)
            put('QUESTS',quests,quest,{'name':f'Wojny Bogów Chaosu: {name}',
                'giver':hunter,'kind':'kill','target':mid,'needed':1,
                'description':f'Pokonaj {name} w {title} i odbierz nagrodę kronikarza.',
                'reward_silver':power*3900,'reward_gold':0,'reward_mithril':0,
                'reward_items':{trophy:2+j},'repeatable':True,'repeat_cooldown':7200})
        put('NPCS',npcs,f'v1800_hunter_{slug}',{'name':hunter,
            'room':f'v1800_{slug}_0','dialogue':'Trzy wyprawy: dwóch strażników i bóstwo chaosu. Quest list.',
            'quest_chain':tuple(ids)})
    return {'regions':4,'rooms':17,'bosses':12,'quests':12,'masteries':len(CLASS_MASTERY)}


def compute_reaction(previous, current, damage):
    """Limited additive reaction, at most 10% of the current dealt hit."""
    name,mult=REACTIONS.get(frozenset((previous,current)),('',0))
    return name,max(0,int(max(0,int(damage))*mult)) if previous!=current else 0

assert len(CLASS_MASTERY)==len(CLASSES)==14
