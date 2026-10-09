# -*- coding: utf-8 -*-
"""Soulbound v1.20.0 — four authored, traversable regions and regional events.

No account migrations, quest shortcuts or trap rolls. The ordinary World, item,
quest, chest and generator mechanisms remain authoritative.
"""
from __future__ import annotations

import hashlib
import time

from data.catalog_mutations import catalog_assign, catalog_set_path
from data.catalogs import ITEMS, MOB_TEMPLATES, NPCS, QUESTS, ROOMS
from systems.content_registry import MOB_SPAWNS, HELP_TOPICS
from world.expansions import TREASURE_CHESTS

V1200_WORLD_VERSION = "1.20.0"
V1200_GATE = "v1200_four_winds_gate"

# (id, name, theme, element, start stage, boss, archivist)
V1200_REGIONS = (
    ("aurora", "Ogrody Zorzy", "szkliste drzewa i pasma niebiańskiego światła", "holy", 110,
     "Królowa Szklanych Korzeni", "Kronikarka Elys"),
    ("thunder", "Burzowe Stepy", "grzmoty, wysokie trawy i kamienne piorunochrony", "electric", 235,
     "Władca Tysiąca Gromów", "Wieszczka Merra"),
    ("coral", "Koralowe Urwiska", "koralowe tarasy, wodospady i morskie mgły", "water", 350,
     "Lewiatan Suchych Głębin", "Kartograf Orlen"),
    ("clock", "Mechaniczna Dolina", "zegarowe wieże i samonaprawiające się automaty", "arcane", 475,
     "Serce Zatrzymanego Czasu", "Archiwistka Vena"),
)

V1200_ROOM_NAMES = {
    "aurora": ("Pierwszy Blask", "Ścieżka Latarni", "Łąka Płomyków", "Brzozy Słońca",
               "Zielone Lustra", "Korytarz Liści", "Korona Ogrodu", "Staw Echa",
               "Srebrzysty Sad", "Święte Polany", "Ścieżka Spadających Gwiazd", "Złoty Zakątek",
               "Taras Poranka", "Kapliczka Zorzy", "Ogród Wspomnień", "Krąg Świtania"),
    "thunder": ("Próg Gromów", "Trawy Burzowe", "Kamień Zwiadowcy", "Przełęcz Wiatru",
                "Skalny Ołtarz", "Wysokie Łąki", "Rów Piorunów", "Błyskawiczny Szlak",
                "Złamana Chorągiew", "Kotlina Gromów", "Dolina Burz", "Grzbiet Pochmurny",
                "Piorunowy Most", "Kamienna Iglica", "Rozstaje Grzmotów", "Oko Burzy"),
    "coral": ("Piaszczysty Próg", "Taras Koralu", "Biała Piana", "Wilgotny Klif",
              "Schody Rafy", "Morska Grota", "Brama Muszli", "Stare Cumowisko",
              "Szmaragdowy Prąd", "Płacząca Skała", "Ogród Meduz", "Korytarz Fal",
              "Szlak Pereł", "Brzeg Rozbitków", "Kamienna Rafa", "Gardziel Przypływu"),
    "clock": ("Pierwsze Koło", "Aleja Przekładni", "Plac Tykania", "Żelazny Promień",
              "Warsztat Cieni", "Trybowy Most", "Plac Wahadeł", "Złoty Zegar",
              "Pole Magnesów", "Złamana Sprężyna", "Wąwóz Mechanizmów", "Piaskowe Tryby",
              "Wielka Tarcza", "Sala Sekundnika", "Korytarz Echa", "Cisza Mechanizmu"),
}
V1200_MOB_NAMES = {
    "aurora": ("Świetlisty Jeleń", "Szklany Strażnik", "Duch Korzeni", "Łowca Zorzy"),
    "thunder": ("Stepowy Gromownik", "Wicher z Ostrzami", "Kamienny Burzownik", "Wilk Burzy"),
    "coral": ("Koralowy Drapieżnik", "Morski Strażnik", "Widmo Przypływu", "Krab Głębinowy"),
    "clock": ("Mechaniczny Łowca", "Żywy Wahadłowiec", "Strażnik Trybów", "Magitekowy Sentinel"),
}
V1200_EVENT_NAMES = ("Najazd zwiadowców", "Elitarna obława", "Rzadki intruz", "Regionalny czempion")
V1200_EVENT_RANKS = ("normal", "elite", "rare", "mini")
V1200_REGIONAL_INDEX = {}
V1200_REGISTERED = False


def v1200_register_catalogs():
    """Idempotent world additions: all links verified and backwards traversable."""
    global V1200_REGISTERED
    if V1200_REGISTERED:
        return V1200_REGIONAL_INDEX
    if V1200_GATE in ROOMS:
        # Native-runtime importer may import this explicit module once through a
        # regular Python dependency and then a second time through its manifest.
        # Catalog additions must remain idempotent, not rewire or duplicate spawns.
        for key, name, _terrain, _element, stage, _boss, _archivist in V1200_REGIONS:
            V1200_REGIONAL_INDEX[key] = {
                "name":name, "entry":f"v1200_{key}_{(13 if key == 'aurora' else 4 if key == 'clock' else 1):02d}", "town":f"v1200_{key}_camp",
                "archive":f"v1200_{key}_archive", "arena":f"v1200_{key}_arena",
                "stage":stage, "rooms":tuple(f"v1200_{key}_{i:02d}" for i in range(1,17)),
                "boss":f"v1200_{key}_boss", "resource":f"v1200_{key}_essence",
                "relic":f"v1200_{key}_relic"}
        V1200_REGISTERED = True
        return V1200_REGIONAL_INDEX
    # Avoid overwriting routes introduced by earlier authored expansions.
    origin, outbound = None, None
    for hub in ("square", "crossroads", "frontier_watchpost", "library"):
        if hub not in ROOMS:
            continue
        for direction in ("up", "northeast", "northwest", "southeast", "southwest"):
            if direction not in ROOMS[hub].get("exits", {}):
                origin, outbound = hub, direction
                break
        if origin:
            break
    if not origin:
        raise RuntimeError("v1.20.0: no safe unoccupied entrance in the old world")
    backwards = {"up":"down", "northeast":"southwest", "northwest":"southeast",
                 "southeast":"northwest", "southwest":"northeast"}[outbound]
    catalog_assign({
        "name": "Rozdroże Czterech Wiatrów", "zone": "Wielki Świat",
        "desc": "Nowy kontynent otwiera cztery niezależne szlaki. Każdy ma osadę, potwory, kronikę i bossa. Bez pułapek.",
        "exits": {backwards: origin}, "recommended_level": 110, "generator_level": 110,
        "v1200_world_hub": True,
    }, "ROOMS", ROOMS, (V1200_GATE,))
    catalog_set_path("ROOMS", ROOMS, (origin, "exits", outbound), V1200_GATE)

    from world.generation_systems import v0130_refresh_exploration_catalog
    region_directions = ("north", "east", "south", "west")
    gate_entries = (12, 0, 0, 3)  # free outer edges: S, W, N, E
    gate_returns = ("south", "west", "north", "east")
    for region_index, (key, name, terrain, element, stage, boss_name, archivist) in enumerate(V1200_REGIONS):
        rooms = tuple(f"v1200_{key}_{i:02d}" for i in range(1, 17))
        settlement, archive, arena = (f"v1200_{key}_{suffix}" for suffix in ("camp", "archive", "arena"))
        first = rooms[0]
        entry = rooms[gate_entries[region_index]]
        # 4 x 4 connected grid. Its side paths are walkable, not boss bypasses.
        for i, rid in enumerate(rooms):
            x, y = i % 4, i // 4
            paths = {}
            if y > 0: paths["north"] = rooms[i-4]
            if y < 3: paths["south"] = rooms[i+4]
            if x > 0: paths["west"] = rooms[i-1]
            if x < 3: paths["east"] = rooms[i+1]
            if i == gate_entries[region_index]: paths[gate_returns[region_index]] = V1200_GATE
            if i == 0: paths["down"] = settlement
            if i == 15: paths["up"] = arena
            catalog_assign({
                "name": V1200_ROOM_NAMES[key][i], "zone": name,
                "desc": f"{V1200_ROOM_NAMES[key][i]}. Tu spotykają się {terrain}. "
                        f"Czterokierunkowa sieć ścieżek pozwala wracać i wybierać własną drogę.",
                "exits": paths, "recommended_level": stage + (i // 4)*16 + i,
                "generator_level": stage + (i // 4)*16 + i,
                "v1200_region": key,
            }, "ROOMS", ROOMS, (rid,))
        catalog_set_path("ROOMS", ROOMS, (V1200_GATE, "exits", region_directions[region_index]), entry)
        # Do not overwrite an existing grid connection when linking the world gate.
        for rid, loc_name, text, paths in (
            (settlement, f"Obozowisko: {name}", "Bezpieczny punkt spotkań, przyjmowania zadań i odpoczynku.",
             {"up": first, "east": archive}),
            (archive, f"Archiwum: {name}", f"Zapisy o regionie i jego historii. Pamiętaj, że {terrain}.",
             {"west": settlement}),
            (arena, f"Sanktuarium: {boss_name}", "Główna arena lokalnego bossa. Jego skarbiec stoi tutaj, nie na szlaku.",
             {"down": rooms[-1]}),
        ):
            catalog_assign({"name":loc_name, "zone":name, "desc":text, "exits":paths,
                            "recommended_level":stage + 90, "generator_level":stage + 90,
                            "v1200_region":key, "v1200_safe": rid!=arena}, "ROOMS", ROOMS, (rid,))
        V1200_REGIONAL_INDEX[key] = {"name":name, "entry":entry, "town":settlement, "archive":archive,
                                     "arena":arena, "stage":stage, "rooms":rooms,
                                     "boss":f"v1200_{key}_boss", "resource":f"v1200_{key}_essence",
                                     "relic":f"v1200_{key}_relic"}
        # Regional resources are real items with sell value. Boss relics are real equipment.
        resource_id=f"v1200_{key}_essence"
        relic_id=f"v1200_{key}_relic"
        catalog_assign({"name":f"Esencja: {name}", "type":"resource", "price":None,
                        "sell_gold":max(12, stage//7), "rarity":"rare", "rarity_name":"Rzadka",
                        "desc":f"Materiał kolekcjonerski zdobywany od stworzeń regionu {name}."},
                       "ITEMS", ITEMS, (resource_id,))
        bonuses = (("strength", "constitution"), ("dexterity", "constitution"),
                   ("willpower", "intelligence"), ("intelligence", "willpower"))[region_index]
        slot = ("charm", "ring", "cloak", "necklace")[region_index]
        relic = {"name":f"Relikt {name}", "type":"armor", "slot":slot,
                 "defense":int(stage*.28), "stats":{bonuses[0]:int(stage*.45), bonuses[1]:int(stage*.32)},
                 "element_wards":{element:0.09}, "sockets":2,
                 "rarity":"legendary", "rarity_name":"Legendarny", "price":None,
                 "required_mastery":max(1,stage-60),
                 "desc":f"Rzadki relikt {name}. Obrona +{int(stage*.28)}, "
                        f"{bonuses[0]} +{int(stage*.45)}, {bonuses[1]} +{int(stage*.32)}, "
                        f"odporność {element} 9%; 2 gniazda."}
        catalog_assign(relic, "ITEMS", ITEMS, (relic_id,))

        for variant, monster in enumerate(V1200_MOB_NAMES[key], 1):
            mid=f"v1200_{key}_mob_{variant}"
            lvl=stage+variant*20
            catalog_assign({"name":monster, "max_hp":max(10000,lvl*1800),
                            "damage":max(100,lvl*16), "damage_type":"magic" if variant%2 else "physical",
                            "attack_elements_v11339":(element,),
                            "silver":lvl*820, "stat_reward":lvl*2600,
                            "class_xp_reward":lvl*19000, "soul_reward":lvl*7600,
                            "generator_level":lvl, "auto_aggro":False,
                            "quest_target":f"v1200_{key}_hunt",
                            "drops":{resource_id:round(.09+variant*.02,2), "soul_shard":.08},
                            "v1200_region":key}, "MOB_TEMPLATES", MOB_TEMPLATES,(mid,))
        for i,rid in enumerate(rooms):
            MOB_SPAWNS.append((rid, f"v1200_{key}_mob_{(i%4)+1}"))
            if i in (5,10,14):
                MOB_SPAWNS.append((rid, f"v1200_{key}_mob_{((i+1)%4)+1}"))
        boss_id=f"v1200_{key}_boss"
        catalog_assign({"name":boss_name, "max_hp":max(250000, int(stage*50000)),
                        "damage":max(600,stage*43), "damage_type":"magic",
                        "attack_elements_v11339":(element,),
                        "silver":int(stage*18000), "stat_reward":int(stage*42000),
                        "class_xp_reward":int(stage*190000), "soul_reward":int(stage*61000),
                        "generator_level":stage+90, "auto_aggro":False,
                        "stationary_mob":True, "boss":True, "world_boss":True,
                        "boss_mechanic":"elemental_overdrive",
                        "boss_mechanic_text":f"Boss używa energii {element}; przygotuj osłony i drużynę.",
                        "quest_target":boss_id, "quest_targets":(boss_id,),
                        "drops":{relic_id:.07, resource_id:1.0, "soul_shard":1.0},
                        "v1200_region":key}, "MOB_TEMPLATES",MOB_TEMPLATES,(boss_id,))
        # v1.22.0: real siege/invasion/rescue mobs on traversable regional
        # routes, near (but not inside) the safe settlement. One spawn per
        # distinct room avoids duplicate spawn keys and forced waiting.
        from systems.world_crises_v1220 import CRISES
        for wave, count, start_index, title in (
            (1, 3, 1, "Zwiadowca kryzysu"),
            (2, 4, 4, "Najeźdźca kryzysu"),
        ):
            crisis_mid = f"v1220_{key}_crisis_wave_{wave}"
            crisis_level = stage + (35 if wave == 1 else 65)
            catalog_assign({
                "name": f"{title}: {name}",
                "max_hp": max(25000, crisis_level * 2500),
                "damage": max(120, crisis_level * 21),
                "damage_type": "magic" if wave == 2 else "physical",
                "attack_elements_v11339": (element,),
                "silver": crisis_level * 960,
                "stat_reward": crisis_level * 3100,
                "class_xp_reward": crisis_level * 23000,
                "soul_reward": crisis_level * 8800,
                "generator_level": crisis_level,
                "auto_aggro": False,
                "v1200_region": key,
                "v1220_crisis_wave": wave,
                "drops": {resource_id: 0.14 if wave == 1 else 0.22},
            }, "MOB_TEMPLATES", MOB_TEMPLATES, (crisis_mid,))
            for room_id in rooms[start_index:start_index+count]:
                MOB_SPAWNS.append((room_id, crisis_mid))
        MOB_SPAWNS.append((arena,boss_id))
        TREASURE_CHESTS[arena] = {"name":f"Skarbiec: {name}", "respawn":86400,
                                  "base_pool":("soul_shard",resource_id),
                                  "set_pool":(relic_id,)}
        # Each lore NPC offers a 3-stage story (one-time final boss/relic quest).
        npc_id=f"v1200_{key}_guide"
        quest_ids=tuple(f"v1200_{key}_q{i}" for i in range(1,4))
        npc_name=f"Przewodnik {name}"
        catalog_assign({"name":npc_name, "room":settlement,
                        "dialogue":f"Strzegę opowieści o {name}. Odkryj nasz szlak, pokonaj lokalne stwory i staw czoła bossowi."
                                   " Każdą drogę przejdziesz także solo; żadna nie ma pułapek.",
                        "quest":quest_ids[0], "quest_chain":quest_ids}, "NPCS",NPCS,(npc_id,))
        catalog_assign({"name":archivist, "room":archive,
                        "dialogue":f"Archiwum regionu {name}. Każde z 16 miejsc ma własną nazwę. "
                                   "Otwórz mapę, zapisuj odkrycia i wracaj do skarbca po zwycięstwie nad bossem."},
                       "NPCS",NPCS,(f"v1200_{key}_archivist",))
        for level in range(1,4):
            qid=quest_ids[level-1]
            target=f"v1200_{key}_hunt" if level < 3 else boss_id
            amount=3+level if level<3 else 1
            reward={resource_id:level} if level<3 else {relic_id:1}
            payload={"name":f"{name} — etap {level}: " + ("Patrole" if level==1 else "Obrona szlaku" if level==2 else boss_name),
                     "giver":npc_name,"kind":"kill", "target":target, "needed":amount,
                     "description":f"Pokonaj {amount} wskazanych przeciwników w regionie {name}." if level<3 else f"Pokonaj bossa {boss_name} w jego arenie.",
                     "reward_gold": 0,
                     "reward_silver":stage*100*level,"reward_mithril":0,
                     "reward_items":reward, "generator_level":stage+level*20,
                     "v1200_region":key}
            if level>1: payload["requires_quest"]=quest_ids[level-2]
            if level<3: payload.update({"repeatable":True,"repeat_cooldown":3600})
            catalog_assign(payload, "QUESTS",QUESTS,(qid,))
    HELP_TOPICS["wielki_swiat"] = [
        "WIELKI ŚWIAT v1.20.0: cztery regiony dostępne pieszo z Rozdroża Czterech Wiatrów.",
        "krainy: zestawienie. krainy wydarzenia: aktywne godzinne wydarzenia w nowych regionach.",
        "krainy <nazwa>: trasa, etap trudności, lokalny boss i skarb.",
        "Każdy region ma 16 terenów, obozowisko, archiwum, bossa, skrzynię i trzy zadania.",
        "Brak pułapek, zakazanych skrótów i wymogu drużyny. Bossowie są trudni; nie zmieniono istniejącego balansu.",
    ]
    # Explorer catalog is populated before this module is loaded; refresh it.
    v0130_refresh_exploration_catalog()
    V1200_REGISTERED=True
    return V1200_REGIONAL_INDEX


def v1200_rotating_events(now=None):
    """Four REAL hourly generated encounters, one in each new biome.

    Same event schema as v0.29. The existing World spawner turns these into
    temporary enemies only when somebody visits their current room.
    """
    now = time.time() if now is None else float(now)
    slot=int(now//3600)
    events=[]
    for index,(key,name,_flavor,_element,stage,_boss,_npc) in enumerate(V1200_REGIONS):
        spec=V1200_REGIONAL_INDEX.get(key)
        if not spec: continue
        roll=int.from_bytes(hashlib.sha256(f"v1200:{slot}:{key}".encode()).digest()[:8],"big")
        number=roll%len(spec["rooms"])
        room_id=spec["rooms"][number]
        kind=V1200_EVENT_RANKS[(slot+index)%len(V1200_EVENT_RANKS)]
        title=V1200_EVENT_NAMES[(slot+index)%len(V1200_EVENT_NAMES)]
        events.append({"type":f"v1200_{key}_{kind}","title":f"{name}: {title}",
                       "rank":kind,"count":2 if kind in ("normal","elite") else 1,
                       "room_id":room_id,"stage":max(1,min(800,stage+(number//4)*16)),
                       "base_templates":(f"v1200_{key}_mob_{(number%4)+1}",),
                       "slot":slot,"token":f"v1200:{slot}:{key}:{room_id}:{kind}",
                       "expires_at":(slot+1)*3600})
    return tuple(events)


v1200_register_catalogs()


# v1.21.0: Legendary Expeditions use the existing, durable quest/bestiary/loot
# systems, not a second expedition database or an intrusive level lock.
# A linear returnable path branches from each region's existing archive.
V1210_EXPEDITIONS = (
    ("aurora", "Pielgrzymka Pierwszego Światła", "Świetlisty Herold", "Matka Zorzy", "holy", "Pielgrzymia Iskra"),
    ("thunder", "Szlak Rozdartego Nieba", "Burzowy Egzekutor", "Tytan Błyskawic", "electric", "Rdzeń Burzy"),
    ("coral", "Pieśń Zatopionej Korony", "Strażnik Raf", "Królowa Bezdennych Mórz", "water", "Perła Głębokich Raf"),
    ("clock", "Ostatnia Godzina", "Mechaniczny Inkwizytor", "Wieczny Chronomanta", "arcane", "Zębatka Wieczności"),
)
V1270_QUARTERMASTERS = {
    "aurora": "Kwatermistrzyni Arlena Świt", "thunder": "Kwatermistrz Borin Grom",
    "coral": "Kwatermistrzyni Neris Fala", "clock": "Kwatermistrz Kael Zegar",
}
V1210_EXPEDITION_INDEX = {}
V1210_REGISTERED = False


def v1210_register_expeditions():
    """Extend existing regional topology and content once; no schema migrations."""
    global V1210_REGISTERED
    if V1210_REGISTERED:
        return V1210_EXPEDITION_INDEX
    from data.crafting_recipes import CRAFT_RECIPES
    for index, (key, title, mini_name, boss_name, element, material_name) in enumerate(V1210_EXPEDITIONS):
        spec = V1200_REGIONAL_INDEX[key]
        stage = spec['stage']
        prefix = f"v1210_{key}"
        rooms = tuple(f"{prefix}_room_{i}" for i in range(1, 6))
        scout, keeper, boss = (f"{prefix}_{type_name}" for type_name in ("scout", "keeper", "boss"))
        seal, heart, gear = (f"{prefix}_{type_name}" for type_name in ("seal", "heart", "gear"))
        quest_ids = tuple(f"{prefix}_q{i}" for i in range(1, 5))
        bounty_id = f"{prefix}_bounty"
        giver_id, witness_id, board_id = (f"{prefix}_{suffix}" for suffix in ("guide", "witness", "contractor"))
        # The runtime manifest may load an import under an alternate module name.
        # Rehydrate the index without duplicating spawns, NPCs or reward chests.
        if rooms[0] in ROOMS:
            V1210_EXPEDITION_INDEX[key]={
                "title":title,"region":spec['name'],"stage":stage,"entry":rooms[0],
                "rooms":rooms,"scout":scout,"keeper":keeper,"boss":boss,
                "giver":giver_id,"witness":witness_id,"contractor":board_id,
                "quests":quest_ids,"contract":bounty_id,"seal":seal,"heart":heart,"gear":gear,
            }
            continue
        # The archive's eastern exit was empty in v1.20.0. Other exits remain unchanged.
        if "east" in ROOMS[spec['archive']]['exits'] and ROOMS[spec['archive']]['exits']['east'] != rooms[0]:
            raise RuntimeError(f"Legendary expedition {key}: occupied archive exit")
        catalog_set_path("ROOMS", ROOMS, (spec['archive'], "exits", "east"), rooms[0])
        titles = ("Próg Legendy", "Kronika Wędrowca", "Szlak Próby", "Sala Strażnika", "Tron Legendy")
        for j, rid in enumerate(rooms):
            exits = {"west": spec['archive'] if j == 0 else rooms[j-1]}
            if j < len(rooms)-1:
                exits["east"] = rooms[j+1]
            catalog_assign({
                "name":f"{titles[j]}: {title}", "zone":f"Wyprawa: {title}",
                "desc":f"{titles[j]}. Ślady dawnej wyprawy prowadzą dalej. "
                       "Każde pomieszczenie ma drogę powrotną; nie ma pułapek ani teleportów.",
                "exits":exits, "recommended_level":stage + 30*(j+1),
                "generator_level":stage + 30*(j+1), "v1210_expedition":key,
                "v1200_region":key, "v1200_safe": j <= 1,
            }, "ROOMS", ROOMS, (rid,))
        catalog_assign({
            "name":material_name, "type":"resource", "price":None,
            "sell_gold":max(25,stage//2), "rarity":"epic", "rarity_name":"Epicka",
            "desc":f"Pieczęć z legendarnej wyprawy: {title}. Składnik wyposażenia, nie jednorazowa waluta."
        }, "ITEMS", ITEMS, (seal,))
        catalog_assign({
            "name":f"Serce: {title}", "type":"resource", "price":None,
            "sell_gold":max(60,stage), "rarity":"legendary", "rarity_name":"Legendarna",
            "desc":f"Serce pokonanego bossa. Składnik wyjątkowej receptury: {title}."
        }, "ITEMS", ITEMS, (heart,))
        stats = (("strength","constitution"),("dexterity","constitution"),
                 ("intelligence","willpower"),("willpower","constitution"))[index]
        bonus = max(80,int(stage*0.48))
        slot = ("charm","ring","necklace","cloak")[index]
        catalog_assign({
            "name":f"Dziedzictwo: {title}", "type":"armor", "slot":slot,
            "defense":max(50,int(stage*0.28)),
            "stats":{stats[0]:bonus,stats[1]:max(55,int(bonus*.75))},
            "element_wards":{element:0.11}, "sockets":3,
            "rarity":"legendary","rarity_name":"Legendarna", "price":None,
            "required_mastery":max(1,stage),
            "desc":f"Unikalny przedmiot wyprawy {title}. {stats[0]} +{bonus}; "
                   f"{stats[1]} +{max(55,int(bonus*.75))}; odporność na {element} 11%; 3 gniazda."
        }, "ITEMS", ITEMS, (gear,))
        for mob_id, name, level, hp, strength, drops, is_boss in (
            (scout, f"Zwiadowca: {title}", stage+20, 3200, 25,
             {spec['resource']:0.27,seal:0.025},False),
            (keeper,mini_name,stage+95,15000,48,{seal:1.0,spec['resource']:0.5},True),
            (boss,boss_name,stage+180,40000,75,{heart:1.0,seal:0.45,gear:0.035},True),
        ):
            catalog_assign({
                "name":name, "max_hp":max(25000,level*hp),
                "damage":max(800,level*strength), "damage_type":"magic",
                "attack_elements_v11339":(element,),
                "silver":level*1400, "stat_reward":level*4800,
                "class_xp_reward":level*32000, "soul_reward":level*15000,
                "generator_level":level,"auto_aggro":False,
                "stationary_mob":is_boss,"boss":is_boss,"world_boss":mob_id==boss,
                "boss_mechanic":(("stellar_barrier", "comet_evade", "firmament_guard", "crystal_lord")[index]
                                 if is_boss else None),
                "boss_mechanic_text":f"Etapy 75/50/25% HP. Żywioł {element}; "
                                     f"unikalna obrona {('Gwiezdna Bariera', 'Unik Komety', 'Straż Firmamentu', 'Kryształowa Bariera')[index]}." if is_boss else "",
                "v017_boss_phases":is_boss,
                "quest_target":mob_id,"quest_targets":(mob_id,),
                "drops":drops,"v1210_expedition":key,
            }, "MOB_TEMPLATES",MOB_TEMPLATES,(mob_id,))
        for rid, mid in ((rooms[2],scout),(rooms[2],scout), (rooms[2],scout),
                         (rooms[3],keeper),(rooms[4],boss)):
            MOB_SPAWNS.append((rid,mid))
        TREASURE_CHESTS[rooms[4]] = {
            "name":f"Skarbiec Legendy: {title}","respawn":86400,
            "base_pool":(seal,heart,spec['resource']), "set_pool":(gear,),
        }
        giver_name=f"Mistrz Wyprawy {spec['name']}"
        catalog_assign({
            "name":giver_name,"room":rooms[0],"quest":quest_ids[0],"quest_chain":quest_ids,
            "dialogue":f"{title}. Cztery etapy: kronika, zwiadowcy, strażnik, boss. "
                       "Przyjmij dostępny etap przez quest accept. Każdy gracz może wejść sam lub z drużyną."
        },"NPCS",NPCS,(giver_id,))
        catalog_assign({
            "name":f"Świadek Legendy {spec['name']}","room":rooms[1],
            "dialogue":f"Poznałem dzieje wyprawy {title}. Wróć do Mistrza po dalsze zadania."
        },"NPCS",NPCS,(witness_id,))
        catalog_assign({
            "name":V1270_QUARTERMASTERS[key],"room":rooms[2],
            "quest":bounty_id,
            "dialogue":"Przyjmuję odnawialne, godzinne kontrakty mistrzowskie na Szlaku Próby. "
                       "Ukończ je solo albo z drużyną i odbierz nagrodę tutaj."
        },"NPCS",NPCS,(board_id,))
        for j, qid in enumerate(quest_ids):
            kind = "talk_npc" if j==0 else "kill"
            targets = (witness_id,scout,keeper,boss)
            needed = (1,4,1,1)[j]
            reward_items = ({spec['resource']:2},{seal:1},{seal:2},{heart:1})[j]
            quest_data={
                "name":f"{title} — etap {j+1}: " + ("Kronika","Patrol","Strażnik","Finał")[j],
                "giver":giver_name,"kind":kind,"target":targets[j],"needed":needed,
                "description": ("Porozmawiaj ze Świadkiem w Kronice Wędrowca." if j==0 else
                                f"Pokonaj {needed} przeciwników: {MOB_TEMPLATES[targets[j]]['name']}."),
                "reward_gold":0,"reward_mithril":0,
                "reward_silver":stage*120*(j+1),
                "reward_items":reward_items, "generator_level":stage+(j+1)*50,
                "v1210_expedition":key,
            }
            if j==0:
                quest_data['target_npc']=witness_id
            if j>0:
                quest_data['requires_quest']=quest_ids[j-1]
            catalog_assign(quest_data,"QUESTS",QUESTS,(qid,))
        catalog_assign({
            "name":f"Kontrakt mistrzowski: {title}","giver":V1270_QUARTERMASTERS[key],
            "kind":"kill","target":scout,"needed":7,
            "description":"Pokonaj 7 zwiadowców w Szlaku Próby. Odnowienie po godzinie.",
            "reward_gold":0,"reward_mithril":0,"reward_silver":stage*500,
            "reward_items":{spec['resource']:3,seal:1},"generator_level":stage+70,
            "repeatable":True,"repeat_cooldown":3600,"v1210_expedition":key,
        },"QUESTS",QUESTS,(bounty_id,))
        craft_level = min(500,max(100,stage))
        ingot_id = ("cobalt_ingot", "runestone_ingot", "astral_ingot", "eternium_ingot")[index]
        catalog_assign({
            "name":f"Wykucie: Dziedzictwo {title}",
            "profession":"Kowalstwo","tool_type":"crafting","tool_item_id":"crafting_hammer",
            "tool_name":ITEMS['crafting_hammer']['name'],"stations":("forge",),
            "min_profession_level":craft_level,
            "ingredients":{heart:2,seal:4,spec['resource']:6,ingot_id:4,"soul_shard":4},
            "output":gear,"quantity":1,"generator_level":stage+120,
            "profession_xp":stage*14,"tool_xp":stage*9,"category":"crafting",
            "desc":f"Unikalna receptura wyprawy: {title}. "
                   f"2 Serca + 4 Pieczęcie + 6 esencji regionu + 4 sztabki ({ITEMS[ingot_id]['name']}) + 4 Odłamki Duszy.",
        },"CRAFT_RECIPES",CRAFT_RECIPES,(gear,))
        V1210_EXPEDITION_INDEX[key]={
            "title":title,"region":spec['name'],"stage":stage,"entry":rooms[0],
            "rooms":rooms,"scout":scout,"keeper":keeper,"boss":boss,
            "giver":giver_id,"witness":witness_id,"contractor":board_id,
            "quests":quest_ids,"contract":bounty_id,"seal":seal,"heart":heart,"gear":gear,
        }
    HELP_TOPICS['legendarne_wyprawy']=[
        "LEGENDARNE WYPRAWY v1.21.0: cztery wyprawy dostępne pieszo z archiwów nowych krain.",
        "legendarnewyprawy: lista; legendarnewyprawy <nazwa>: lokalizacja i kierunek.",
        "legendarnewyprawy postep: zapisany stan misji z SQLite, osobno dla każdej postaci.",
        "Mistrz Wyprawy czeka na Progu Legendy; Świadek w Kronice; Kwatermistrz Kontraktów na Szlaku Próby.",
        "Mistrz oferuje 4 zadania fabularne; Kwatermistrz godzinne powtarzalne wyzwania.",
        "Nowe materiały, bossowie 75/50/25% i receptury Kowalstwa w Kuźni. Bez pułapek, teleportu, limitów klas i wymogu party.",
    ]
    V1210_REGISTERED=True
    return V1210_EXPEDITION_INDEX


v1210_register_expeditions()
