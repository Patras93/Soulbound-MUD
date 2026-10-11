# -*- coding: utf-8 -*-
"""v2.30: two optional four-room Ocean story routes with stable identifiers.

Does not modify old IDs or change old ship schemas. Only new fleet enemies
receive the additional encounter hazard mechanic; original fights untouched.
"""
from data import catalog_mutations as cm

ROUTES = (
  ('cisza','Skarbiec Milczących Wód','v2200_row_2','north','south',
   'Strażnik Ciszy Głębin','Władca Skarbca Bezdennego','v2200_leviathan_heart',610),
  ('nawa','Nawa Potępionych Żagli','v2200_burze_2','south','north',
   'Gwardzista Widmowych Żagli','Admirał Wiecznej Burzy','v2200_storm_core',710),
)

def install(rooms,npcs,mobs,spawns,quests,navy):
    for slug,zone,origin,direction,reverse,enemy,boss,material,level in ROUTES:
        if origin not in rooms or direction in rooms[origin].get('exits',{}):
            raise RuntimeError('Brak wolnego wyjścia dla trasy '+zone)
        for idx,stage in enumerate(('Ukryte Wejście','Droga Strażników','Komnata Próby','Tron Głębin')):
            rid=f'v2300_{slug}_{idx}'
            if rid in rooms:raise RuntimeError('Kolizja pokoju '+rid)
            exits={reverse: origin if idx==0 else f'v2300_{slug}_{idx-1}'}
            if idx<3:exits[direction]=f'v2300_{slug}_{idx+1}'
            cm.catalog_assign({'name':f'{stage} — {zone}', 'zone':zone,
                  'desc':f'{zone}. {stage}. Bez pułapek. Przejścia w obie strony.',
                  'exits':exits,'recommended_mastery':level,'generator_level':level,
                  'ocean_sagas_v2300':slug},'ROOMS',rooms,(rid,))
        cm.catalog_assign(f'v2300_{slug}_0','ROOMS',rooms,(origin,'exits',direction))
        for num,mname in enumerate((enemy,'Zaklinacz '+zone,'Ochroniarz '+zone)):
            mid=f'v2300_{slug}_mob_{num}'
            if mid in mobs:raise RuntimeError('Kolizja moba '+mid)
            cm.catalog_assign({'name':mname,'max_hp':level*(650+num*130),
                'damage':level*(40+num*6),'generator_level':level,'rank':'elite' if num else 'normal',
                'damage_type':'magic' if num==1 else 'physical',
                'tactical_role_v2200':('obronca','uzdrowiciel','dowodca')[num],
                'stat_reward':level*240,'class_xp_reward':level*3800,
                'soul_reward':level*1400,'silver':level*850,'gold':0,'mithril':0,
                'fame_target':True,'drops':{material:.16,'soul_shard':.45},
                'quest_target':mid,'stationary_mob':True,'auto_aggro':False},
                'MOB_TEMPLATES',mobs,(mid,))
            spawns.append((f'v2300_{slug}_1' if num<2 else f'v2300_{slug}_2',mid))
        boss_id=f'v2300_{slug}_boss'
        cm.catalog_assign({'name':boss,'max_hp':level*14500,'damage':level*210,
            'generator_level':level,'rank':'world_boss','boss':True,'world_boss':True,
            'boss_mechanic':'elemental_overdrive','damage_type':'magic',
            'fame_target':True,'stat_reward':level*760,'class_xp_reward':level*12000,
            'soul_reward':level*5200,'silver':level*7200,'gold':0,'mithril':0,
            'drops':{material:1.0,'soul_shard':1.0},'quest_target':boss_id,
            'stationary_mob':True,'auto_aggro':False},'MOB_TEMPLATES',mobs,(boss_id,))
        spawns.append((f'v2300_{slug}_3',boss_id))
        qid=f'v2300_{slug}_quest'
        cm.catalog_assign({'name':'Legenda: '+zone,'giver':'Kronikarz '+zone,
            'kind':'kill','target':boss_id,'needed':1,
            'description':'Pokonaj '+boss+' w prawdziwej walce. Każdy uczestnik ma własny postęp.',
            'reward_silver':level*8500,'reward_gold':0,'reward_mithril':0,
            'reward_items':{'soul_shard':5},'repeatable':True,'repeat_cooldown':7200},'QUESTS',quests,(qid,))
        cm.catalog_assign({'name':'Kronikarz '+zone,'room':f'v2300_{slug}_0',
            'dialogue':'Poznaj legendę mórz. Nagroda za pokonanie strażnika czeka.',
            'quest_chain':(qid,)},'NPCS',npcs,(f'v2300_{slug}_npc',))
        code=f'legenda_{slug}'
        if code in navy.ENEMIES:raise RuntimeError('Kolizja bitwy '+code)
        navy.ENEMIES[code]=(f'Flota: {zone}',level*8200,level*160,level*2250,'monster',level*620)
        navy.MATERIALS[code]=material
    return {'rooms':8,'mobs':8,'quests':2,'fleet_targets':2}


def hazard(enemy, turn, command):
    """Return hazard multiplier and NEXT turn's warning, only new boss fleets.

    No random damage. Previous-turn warning lets a blind player choose guard.
    """
    if enemy not in ('legenda_cisza','legenda_nawa'):
        return 100, ''
    cycle=4 if enemy=='legenda_cisza' else 5
    if turn % cycle==0:
        return 135, 'Nadmorski kolos kończy silny atak. Można ograniczyć straty osłoną i manewrem.'
    if (turn+1)%cycle==0:
        return 100, 'UWAGA: następna tura przyniesie potężny atak floty. Wybierz osłona lub manewr.'
    return 100, ''
