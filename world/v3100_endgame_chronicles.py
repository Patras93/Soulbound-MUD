# -*- coding: utf-8 -*-
"""v31.00.0: additional 401–800 regions with playable quest chapters.

Uses existing room, mob, NPC and quest registries: real combat credit,
party cooperation, standard quest rewards, existing OLC edits and SQLite saves.
No new tables, no traps and never more than one NPC per room.
"""

CHAPTERS = (
    ('scarlet', 'Szkarłatne Pogranicze', 401, 500,
     'Kapitan Ardel', 'Wartownia Popiołów',
     ('Przyczółek Rubieży', 'Droga Spopielonych Chorągwi', 'Wypalona Reduta',
      'Dziedziniec Rozbitego Muru', 'Zbrojownia Ostatniej Straży', 'Sala Szkarłatnego Sztandaru'),
     ('Zwiadowca Popiołów', 'Wojownik Żelaznego Żaru', 'Mag Krwawej Burzy',
      'Pogromca Rubieży'), 'Generał Płonącego Sztandaru',
     'Płomień pod murem'),
    ('crystal', 'Kryształowe Bezmiary', 501, 600,
     'Badaczka Eryna', 'Przystań Pryzmatów',
     ('Przystań Pryzmatów', 'Aleja Szklanych Echa', 'Ogrody Zamrożonych Barw',
      'Taras Błękitnej Burzy', 'Archiwum Pękniętych Klejnotów', 'Sanktuarium Serca Kryształu'),
     ('Łowca Pryzmatów', 'Kryształowy Czarownik', 'Wojownik Lustrzany',
      'Strażnik Błękitnej Iskry'), 'Arcymistrz Rozbitego Zwierciadła',
     'Tajemnica pękniętych zwierciadeł'),
    ('abyss', 'Otchłań Nieskończoności', 601, 700,
     'Strażniczka Myra', 'Ostoja Echa',
     ('Ostoja Echa', 'Korytarz Szeptanych Imion', 'Czeluść Bez Świtu',
      'Grota Ciemnych Przysiąg', 'Most Zapomnianych', 'Tron Pustego Głosu'),
     ('Cień Dawnego Króla', 'Łowca Bezkresu', 'Szeptacz Próżni',
      'Rycerz Bez Imienia'), 'Herold Ciszy',
     'Przysięga bez imienia'),
    ('eternal', 'Tron Wieczności', 701, 800,
     'Kronikarz Lorian', 'Izba Ostatniej Kroniki',
     ('Izba Ostatniej Kroniki', 'Schody Przeszłych Epok', 'Komnata Wyblakłych Gwiazd',
      'Most Ruchomego Czasu', 'Galleria Tysiąca Losów', 'Sanktuarium Prawdziwego Tronu'),
     ('Rycerz Zatrzymanego Czasu', 'Posłaniec Wieczności', 'Tkacz Przeznaczenia',
      'Strażnik Pierwszej Ery'), 'Sędzia Ostatniej Kroniki',
     'Kronika bez końca'),
)


def install(rooms, mobs, spawns, npcs, quests, areas):
    """Install additively after v30; return added chapter slugs. Idempotent."""
    added=[]
    for slug, zone, low, high, mentor, camp, titles, enemies, miniboss, theme in CHAPTERS:
        origin=f'v3000_{slug}_3'
        first=f'v3100_{slug}_1'
        if first in rooms:
            continue
        if origin not in rooms:
            raise RuntimeError('v31 brak v30: '+origin)
        if 'east' in rooms[origin].get('exits',{}):
            raise RuntimeError('v31 przejscie zajete: '+origin)
        chapter_ids=[f'v3100_{slug}_quest_{j}' for j in range(1,7)]
        for i,title in enumerate(titles,1):
            rid=f'v3100_{slug}_{i}'
            level=min(high, low+(i-1)*18)
            exits={}
            if i==1:
                exits['west']=origin
            else:
                exits['south']=f'v3100_{slug}_{i-1}'
            if i<6:
                exits['north']=f'v3100_{slug}_{i+1}'
            rooms[rid]={
                'zone':zone, 'name':title,
                'desc':f'{zone}. {theme}. Rozdzial kroniki dla poziomow {low}-{high}. '
                       'Brak pułapek. Powrot ta sama droga.',
                'generator_level':level,'recommended_mastery':level,'exits':exits,
            }
        rooms[origin].setdefault('exits',{})['east']=first
        npc_id=f'v3100_{slug}_guide'
        if any(n.get('room')==first for n in npcs.values()):
            raise RuntimeError('v31: kolizja NPC w '+first)
        npcs[npc_id]={
            'name':mentor,'room':first,
            'dialogue':f'{mentor}: {theme}. Mam szesc rozdzialow kroniki. '
                       'Wpisz quest list i przyjmij 1, gdy bedziesz gotowy.',
            'v700_story_npc':True,'specialist_quests':tuple(chapter_ids),
            'quest_chain':tuple(chapter_ids),'quest':chapter_ids[0],
        }
        for j,name in enumerate(enemies,1):
            mid=f'v3100_{slug}_mob_{j}'
            level=min(high,low+9+(j-1)*20)
            diff=level-400
            mobs[mid]={
                'name':name,'generator_level':level,
                'max_hp':22000+diff*235+j*2200,'damage':350+diff*3+j*18,
                'damage_type':'magic' if j%2==0 else 'physical',
                'class_xp_reward':70000+diff*1350+j*12000,
                'soul_reward':18000+diff*260+j*1300,
                'stat_reward':6500+diff*56,'silver':2300+diff*19,
                'gold':25+diff//10,'mithril':0,
                'drops':{'soul_shard':.40},'endgame_region_mastery':level,
                'quest_target':mid,
            }
            # Every objective has a physical spawn; no imaginary targets.
            spawns.append((f'v3100_{slug}_{j+1}',mid))
            spawns.append((f'v3100_{slug}_{min(6,j+2)}',mid))
        boss_id=f'v3100_{slug}_boss'
        diff=high-400
        mobs[boss_id]={
            'name':miniboss,'generator_level':high,'max_hp':450000+diff*9500,
            'damage':690+diff*6,'damage_type':'magic',
            'class_xp_reward':190000+diff*5600,
            'soul_reward':39000+diff*1050,'stat_reward':15000+diff*170,
            'silver':9000+diff*72,'gold':100+diff//3,'mithril':1+diff//180,
            'drops':{'soul_shard':1.0},'world_boss':True,
            'boss_mechanic':'endgame_region_boss',
            'boss_mechanic_text':'Strzeze ostatniego rozdzialu tej krainy.',
            'endgame_region_mastery':high,'quest_target':boss_id,
            'leave_corpse':True,
        }
        spawns.append((f'v3100_{slug}_6',boss_id))
        targets=[f'v3100_{slug}_mob_{j}' for j in range(1,5)]+[
            boss_id, f'v3000_{slug}_boss',
        ]
        for j,(qid,target) in enumerate(zip(chapter_ids, targets),1):
            needed=3 if j<=4 else 1
            target_name=(enemies[j-1] if j<=4 else
                         miniboss if j==5 else mobs[f'v3000_{slug}_boss']['name'])
            quests[qid]={
                'name':f'{theme} — rozdzial {j}: {target_name}',
                'giver':mentor,'kind':'kill','target':target,'needed':needed,
                'description':f'Pokonaj {needed} x {target_name} w krainie {zone} '
                              f'i wroc do {mentor} w {camp}.',
                'generator_level':min(high,low+(j-1)*19),
                'reward_stat_progress':(low+(j-1)*19)*14,
                'reward_silver':1200+j*900+low*7,
                'reward_gold':10+j*5+(low-400)//4,
                'reward_mithril':1 if j==6 else 0,
                'reward_items':{'soul_shard':j if j==6 else 1},
                **({'requires_quest':chapter_ids[j-2]} if j>1 else {}),
            }
        for area in areas:
            if area.get('id')==f'v3000_{slug}':
                area['description']=(
                    f'Otwarty region poziomow {low}-{high}, rozbudowany o kronike: '
                    '12 pokojow, osiem odmian potworow, dwoch bossow, szesc questow.'
                )
                area['note']=(str(area.get('note',''))+
                    f' Poboczny szlak: na trzecim odcinku idz na wschod. '
                    f'NPC {mentor}: quest list, przyjmij 1.')
                area['enemies']=str(area.get('enemies',''))+', '+', '.join(enemies)+', '+miniboss
                break
        added.append(slug)
    return tuple(added)
