# -*- coding: utf-8 -*-
"""Soulbound v3.10.0: authored realm/campaign content, additive to v3.00.7.

No existing catalog identifier, player table, EXP curve or quest record is replaced.
This is the playable world/story foundation, not a claim that all mastery
spells or all planned expansion stages are finished.
"""
from __future__ import annotations

from data.catalog_mutations import catalog_assign, catalog_set_path
from systems.mastery_crafting_v2201 import TOOL_TYPES as PROFESSION_REWARD_TOOL_TYPES

# Authored realm identity, lore, places, foes and bosses. Each has a unique
# campaign (one-shot) and a repeatable expedition, backed by existing SQLite.
REALMS = (
    ("crowns", "Dolina Upadłych Koron", 35, "Pieczęć Ostatniego Króla",
     "Zrujnowane rody walczą o prawo do dawnych grobowców; karawany znikają na trakcie.",
     ("Brama Bez Króla", "Rynek Pękniętej Korony", "Dziedziniec Sztandarów", "Biblioteka Dynastii",
      "Zawalony Most", "Koszary Wygnańców", "Kaplica Przysięgi", "Kuźnia Strażnicza",
      "Zapomniany Ogród", "Wieża Heroldów", "Droga Banitów", "Sala Rady"),
     ("Rabujący Rycerz", "Herold Uzurpatora", "Zakuty w Pancerz Wyrzutek"),
     "Uzurpator Bez Korony", "Archiwistka Seria", "Marszałek Korvin"),
    ("khardum", "Podziemne Królestwo Khar-Dum", 65, "Serce Kamiennego Tronu",
     "Zamknięte szyby i głosy spod skał zdradzają bunt pradawnych górniczych maszyn.",
     ("Szyb Północny", "Targ Pod Skałą", "Most Nad Magmą", "Archiwum Run",
      "Sala Geodów", "Kopalnia Echa", "Kuźnia Głębin", "Stalowa Śluza",
      "Ogrody Grzybów", "Studnia Rezonansu", "Komora Mistrzów", "Brama Kwarcowa"),
     ("Głodny Tunelowiec", "Zbuntowany Runiczny Golem", "Kamienny Egzekutor"),
     "Król Żelaznych Korzeni", "Mistrzyni Dagna", "Runicznik Brodor"),
    ("wildwood", "Szmaragdowa Dzicz", 95, "Ziarno Pierwszego Dębu",
     "Pradawne drzewo choruje, a jego strażnicy nie odróżniają już przyjaciół od wrogów.",
     ("Korzenna Brama", "Osada Mchu", "Półka Paproci", "Drzewna Czytelnia",
      "Most Lian", "Zarośnięty Krąg", "Źródło Rosy", "Dolina Entów",
      "Ogród Zarodników", "Obserwatorium Ptaków", "Jar Wilków", "Sanktuarium Dębu"),
     ("Skażony Dzik", "Widmo Boru", "Rozgniewany Ent"),
     "Pradawny Pożeracz Korzeni", "Druidka Lareth", "Strażnik Thalen"),
    ("souls", "Morze Zapomnianych Dusz", 125, "Latarnia Zaginionych Żagli",
     "Światła na pustych okrętach prowadzą marynarzy do zatopionych świątyń.",
     ("Nabrzeże Bez Żagli", "Targ Rozbitków", "Molo Szeptów", "Archiwum Kapitanów",
      "Rafa Umilkłych", "Pomost Wodorostów", "Latarnia Wichru", "Wrota Syren",
      "Zalany Amfiteatr", "Brzeg Zjaw", "Wrak Nawigatora", "Świątynia Przypływów"),
     ("Widmowy Marynarz", "Łowca z Otchłani", "Strażnik Zatopionego Portu"),
     "Lewiatan Milczących Wód", "Nawigatorka Ailea", "Kapitan Morwen"),
    ("chaos", "Pustkowia Chaosu", 170, "Odłamek Pękniętego Nieba",
     "Cztery żywioły walczą o pustynię, a każde przymierze budzi kolejny kataklizm.",
     ("Brama Popiołów", "Bazar Burz", "Płaskowyż Piorunów", "Krypta Żywiołów",
      "Szczelina Żarłocznych Płomieni", "Dolina Mrozu", "Obóz Ocalałych", "Próba Ognia",
      "Cmentarz Meteorytów", "Wieża Wiatru", "Piaskowy Krąg", "Sanktuarium Burzy"),
     ("Ognisty Maruder", "Lodowy Egzekutor", "Burzowy Fanatyk"),
     "Cesarz Rozdartego Nieba", "Badaczka Niva", "Wieszcz Huron"),
    ("eternity", "Cytadela Wieczności", 225, "Księga Pękniętej Wieczności",
     "Kolejne wersje historii nakładają się na siebie, a strażnicy pragną zatrzymać czas.",
     ("Przedbramie Czasu", "Targ Wiecznych", "Korytarz Zegarów", "Archiwum Eonów",
      "Most Bez Jutra", "Komnata Odbić", "Dziedziniec Minut", "Galeria Utraconych Lat",
      "Ogród Zegarów", "Wieża Wspomnień", "Wrota Eonów", "Sala Ostatniego Tykania"),
     ("Czasowy Ścigacz", "Strażnik Eonów", "Rycerz Bez Daty"),
     "Władca Zerwanej Chronologii", "Kronikarka Veyra", "Strażniczka Amon"),
    ("insects", "Kraina Owadów — Chitynowy Tron", 120, "Jajo Pierwszej Królowej",
     "Rozdzielone roje prowadzą wojnę o królewskie komnaty; jedne kolonie proszą o pomoc.",
     ("Wrota Wielkiego Ula", "Targ Mrówczych Kupców", "Galeria Bursztynu", "Księga Feromonów",
      "Most Pajęczy", "Gniazdo Szerszeni", "Ścieżka Modliszek", "Kopalnia Chityny",
      "Ogród Zarodników Ula", "Świątynia Larw", "Arena Chrząszczy", "Tron Królowej"),
     ("Wściekły Szerszeń", "Opancerzony Chrząszcz", "Zatruty Skorpion"),
     "Pradawna Matka Roju", "Posłanka Myrra", "Strażnik Karnax"),
    ("elves", "Kraina Elfów — Wieczny Świt", 145, "Pieśń Srebrnych Liści",
     "Elfie rody dzielą się przez zaginiony hymn, który chronił światło pradawnego drzewa.",
     ("Aleja Srebrnych Liści", "Targ Wiecznego Świtu", "Dziedziniec Harf", "Biblioteka Pieśni",
      "Most Księżycowego Szkła", "Gaj Gwiazd", "Szkoła Łuczników", "Kuźnia Run Elfów",
      "Ogrody Błękitnych Róż", "Świątynia Półksiężyca", "Wzgórze Strażniczek", "Pałac Świtu"),
     ("Upadły Elficki Łucznik", "Przeklęty Ent Świtu", "Mag Cienia Dworu"),
     "Upadły Książę Gwiazd", "Księżniczka Lethiel", "Mistrzyni Elaria"),
)

# Authored expedition identity per realm: special rooms and the episode's boss.
EXPEDITION_STAGES = (
    "Szept Pierwszych Wrót", "Próba Zwiadowców", "Sala Dawnych Pieczęci",
    "Przejście Bez Powrotu", "Komnata Władcy",
)

# Old-world cities and settlements. Names are deliberately not generic numbered quests.
OLD_STORIES = (
    ("temple", "Świątynia Odrodzenia", "Kapłanka Remia", "Szept spod fundamentów", "temple_rat", "healing_potion", 5),
    ("market", "Targ Dusz", "Kupiec Odran", "Zaginiony konwój", "bandit", "healing_potion", 9),
    ("forge", "Kuźnia Dusz", "Kowalka Isdra", "Ostrza bez pieczęci", "goblin", "iron_ore", 15),
    ("fish_market", "Targ Rybny", "Szyper Nariel", "Zaginione sieci", "bandit", "river_bleak", 12),
    ("lumberjack_camp", "Obóz Drwali", "Zwiadowczyni Iska", "Dym pośród drzew", "shadow_wolf", "oak_log", 17),
    ("cave_entrance", "Wejście do Kopalni", "Górnik Loran", "Złamane stemple", "goblin", "copper_ore", 18),
    ("herbalist_hut", "Chata Zielarki", "Zielarka Sora", "Płacz trującej łąki", "shadow_wolf", "healing_potion", 22),
    ("south_street", "Południowa Ulica", "Strażniczka Dorsa", "Księga utraconych imion", "bandit", "healing_potion", 14),
)

CLASS_NAMES = (
    "Mec", "Kapłan", "Druid", "Mag", "Wojownik", "Nekromanta", "Berserker",
    "Łowca", "Mnich", "Łotrzyk", "Strażnik", "Psionik", "Czarownik", "Inżynier",
)
PROFESSIONS = (
    ("Alchemia", "healing_potion"), ("Archeologia", "soul_shard"),
    ("Drwalstwo", "oak_log"), ("Garbarstwo", "leather_vest"),
    ("Gotowanie", "river_fish_stew"), ("Górnictwo", "copper_ore"),
    ("Jubilerstwo", "forge_charm"), ("Kartografia", "soul_shard"),
    ("Kowalstwo", "iron_ingot"), ("Krawiectwo", "leather_vest"),
    ("Stolarstwo", "oak_plank"), ("Wędkarstwo", "river_bleak"),
    ("Zaklinanie", "soul_shard"), ("Zielarstwo", "chamomile"),
)

OPPOSITE = {
    "north":"south", "south":"north", "east":"west", "west":"east",
    "northeast":"southwest", "southwest":"northeast", "northwest":"southeast",
    "southeast":"northwest", "up":"down", "down":"up",
}
DIRECTIONS = ("north", "south", "east", "west", "northeast", "northwest", "southwest", "up")


def install(rooms, npcs, mobs, spawns, quests, items, help_topics, help_aliases):
    """Install once during content bootstrap. Raises on collisions, never rewrites old IDs."""
    stats = {"rooms": 0, "npcs": 0, "mobs": 0, "spawns": 0, "quests": 0, "items": 0}

    def add(catalog, label, key, value):
        if key in catalog:
            raise RuntimeError(f"v3.10.0 kolizja katalogu {label}:{key}")
        catalog_assign(value, label, catalog, (key,))
        stats["mobs" if label == "MOB_TEMPLATES" else label.lower()] += 1
        return key

    def room(key, zone, name, description, stage):
        return add(rooms, "ROOMS", key, {
            "name": name, "zone": zone, "desc": description,
            "exits": {}, "generator_level": stage,
            "recommended_mastery": stage, "v3100_legends": True,
        })

    def link(a, direction, b):
        reverse = OPPOSITE[direction]
        for source, dr, destination in ((a, direction, b), (b, reverse, a)):
            if destination not in rooms or source not in rooms:
                raise RuntimeError("Nieistniejący pokój przy połączeniu v3.10.0")
            old = rooms[source].get("exits", {}).get(dr)
            if old is not None and old != destination:
                raise RuntimeError(f"Zajęte wyjście {source}:{dr}; nie nadpisuję: {old}")
            catalog_set_path("ROOMS", rooms, (source, "exits", dr), destination)

    def npc(key, name, place, speech, chain=()):
        value = {"name": name, "room": place, "dialogue": speech, "v3100_legends": True}
        if chain:
            value["quest_chain"] = tuple(chain)
        add(npcs, "NPCS", key, value)
        return key

    def monster(key, name, stage, rank="normal", relic=None):
        boss = rank in ("boss", "world_boss")
        hp = int((900 if boss else 140) * max(15, stage))
        dmg = int((20 if boss else 5) * max(15, stage))
        value = {
            "name": name, "generator_level": stage, "max_hp": hp,
            "damage": dmg, "damage_type": "magic" if "Mag" in name or "Widmo" in name else "physical",
            "stat_reward": int(stage * (250 if boss else 55)),
            "class_xp_reward": int(stage * (12500 if boss else 2100)),
            "soul_reward": int(stage * (4200 if boss else 750)),
            "silver": int(stage * (3400 if boss else 450)),
            "gold": 0, "mithril": 0,
            "drops": ({relic: 1.0, "soul_shard": .6} if relic else {"soul_shard": .25}),
            "rank": rank, "boss": boss, "world_boss": rank == "world_boss",
            "quest_target": key, "stationary_mob": True, "auto_aggro": False,
            "v3100_legends": True,
        }
        add(mobs, "MOB_TEMPLATES", key, value)
        return key

    def spawn(where, mob_id):
        if where not in rooms or mob_id not in mobs:
            raise RuntimeError(f"Brak miejsca lub moba dla respawnu {mob_id}")
        spawns.append((where, mob_id))
        stats["spawns"] += 1

    def quest(key, name, giver, kind, target, needed, description, stage, *, requires=None,
              repeatable=False, required_class=None, reward_profession=None, target_npc=None):
        value = {
            "name": name, "giver": giver, "kind": kind,
            "target": target, "needed": needed, "description": description,
            "generator_level": stage, "character_xp_reward": stage * (9000 if not repeatable else 3200),
            "reward_stat_progress": stage * 900,
            "reward_silver": stage * (5000 if not repeatable else 1700),
            "reward_gold": 0, "reward_mithril": 0,
            "reward_items": {"soul_shard": 3 if not repeatable else 1},
            "repeatable": repeatable, "v3100_legends": True,
        }
        if requires:
            value["requires_quest"] = requires
        if repeatable:
            value["repeat_cooldown"] = 3600
        if required_class:
            value["required_class"] = required_class
        if reward_profession:
            value["reward_profession"] = reward_profession
            value["reward_profession_xp"] = stage * (165 if not repeatable else 125)
            # Quest turn-in requires a real, valid profession tool type even
            # when no extra tool XP is awarded. Without it the 28 orders
            # could be accepted but never rewarded.
            value["reward_tool_type"] = PROFESSION_REWARD_TOOL_TYPES[reward_profession]
        if target_npc:
            value["target_npc"] = target_npc
        return add(quests, "QUESTS", key, value)

    # At runtime numerous older expansions already occupy square directions.
    # Find a truly FREE existing hub exit; never overwrite a legacy route.
    origin = None
    direction = None
    for source in ("square", "market", "temple", "north_street", "south_street",
                   "library", "fish_market", "forge"):
        if source not in rooms:
            continue
        used = rooms[source].get("exits", {})
        for candidate in ("northwest", "southeast", "northeast", "north", "south", "west"):
            if candidate not in used:
                origin, direction = source, candidate
                break
        if origin:
            break
    if not origin:
        raise RuntimeError("v3.10.0: żadna z istniejących lokacji startowych nie ma wolnego wyjścia")
    entrance_label = rooms[origin]["name"]
    return_label = OPPOSITE[direction]
    hall = room("v3100_hall", "Sala Legend", "Sala Drogowskazów Ośmiu Krain",
                "Sala kartografów. Osiem przejść prowadzi do osobnych krain. "
                f"Powrót przez {return_label} do: {entrance_label}.", 35)
    link(origin, direction, hall)
    class_hall = room("v3100_class_hall", "Sala Legend", "Dom Mistrzów Klas",
                      "Czternastu mistrzów klas gromadzi się przy tablicach prób. Powrót: dół.", 35)
    link(hall, "up", class_hall)
    prof_hall = room("v3100_prof_hall", "Sala Legend", "Cech Czternastu Rzemiosł",
                     "Wszystkie profesje mają tu mistrzów opowieści i zlecenia. Powrót: góra.", 35)
    link(hall, "down", prof_hall)
    lore_hall = room("v3100_lore_hall", "Sala Legend", "Archiwum Kronik Bohaterów",
                     "Tu zapisuje się wyczyny bez końcowego etapu: historia i odnawialne kontrakty.", 35)
    link(hall, "west", lore_hall)

    # One exit per realm from a two-stage ferry foyer, so no direction is reused.
    gates = room("v3100_gates", "Sala Legend", "Galeria Ośmiu Bram",
                 "Osiem bram prowadzi do regionów. Odkryj je po kolei lub odwiedź wybrany region.", 35)
    link(hall, "northeast", gates)
    # The gallery has back 'southwest', leaving nine usable directions.
    region_dirs = ("north", "south", "east", "west", "northeast", "northwest", "southeast", "up")

    for index, (slug, zone, stage, relic_label, lore, sites, enemies, final_boss, guide, witness) in enumerate(REALMS):
        prefix = "v3100_" + slug
        entry_ids = []
        for i, site in enumerate(sites):
            rid = f"{prefix}_room_{i:02d}"
            detail = (
                f"{site}. {lore} "
                + ("Znajduje się tu kronikarz i tablica zadań." if i == 0 else
                   "Na ścieżce można spotkać przeciwników i ślady dawnej historii." if i in (2,5,8,10) else
                   "Warto odszukać miejscowych świadków i sprawdzić kierunki.")
            )
            room(rid, zone, site, detail, stage + (i * 2))
            entry_ids.append(rid)
        # Roads form a loop around the realm; extra shortcuts lead to NPCs.
        for i in range(11):
            road_direction = "east" if i == 0 and region_dirs[index] == "south" else ("north" if i % 2 == 0 else "east")
            link(entry_ids[i], road_direction, entry_ids[i+1])
        # Due to alternating directions, reverse path is always unique for internal points.
        link(gates, region_dirs[index], entry_ids[0])

        relic_id = f"{prefix}_relic"
        add(items, "ITEMS", relic_id, {
            "name": relic_label, "type": "quest", "price": None,
            "desc": f"Dowód wyprawy w regionie {zone}: {lore}", "v3100_legends": True,
        })
        foe_ids = []
        for j, enemy in enumerate(enemies):
            mid = monster(f"{prefix}_enemy_{j}", enemy, stage + 5*j, relic=relic_id if j==1 else None)
            foe_ids.append(mid)
            for where in (entry_ids[2+j], entry_ids[5+j]):
                spawn(where, mid)
        boss_id = monster(f"{prefix}_boss", final_boss, stage + 65, "world_boss", relic=relic_id)
        spawn(entry_ids[11], boss_id)

        guide_key = f"{prefix}_guide"
        witness_key = f"{prefix}_witness"
        guide_name = guide
        witness_name = witness
        qids = []
        chapter_data = (
            ("Pierwsza wieść", "kill", foe_ids[0], 4,
             f"{guide_name} prosi o pokonanie czterech przeciwników: {enemies[0]}. Odnajdziesz ich w {zone}."),
            ("Ślad dawnej pieczęci", "collect", relic_id, 2,
             f"Zdobądź 2 przedmioty {relic_label} z przeciwników {enemies[1]} po przyjęciu tego etapu. Przynieś je {guide_name}."),
            ("Świadek tajemnicy", "talk_npc", witness_key, 1,
             f"Porozmawiaj z {witness_name} w {zone}; dowiedz się, kto odpowiada za konflikt."),
            ("Strażnicy szlaku", "kill", foe_ids[2], 4,
             f"Pokonaj czterech przeciwników {enemies[2]}, by utorować drogę do finału."),
            ("Władca krainy", "kill", boss_id, 1,
             f"Pokonaj {final_boss} w sali głównej regionu i wróć do {guide_name}."),
        )
        prev = None
        for ch, (title, kind, target, needed, desc) in enumerate(chapter_data, 1):
            qid = f"{prefix}_story_{ch}"
            quest(qid, f"{zone} — {title}", guide_name, kind, target, needed, desc,
                  stage + ch * 8, requires=prev, target_npc=witness_key if kind=="talk_npc" else None)
            qids.append(qid)
            prev = qid
        # Expedition: 5 rooms, 2 extra guards and the realm's world boss.
        exp_ids = []
        for j, name in enumerate(EXPEDITION_STAGES):
            rid = f"{prefix}_exp_{j}"
            room(rid, f"Ekspedycja: {zone}", f"{name} — {zone}",
                 f"Legendarny loch regionu {zone}. {lore} "
                 "Nie ma losowych pułapek ani obowiązku gry drużynowej.", stage + 70 + j*8)
            exp_ids.append(rid)
        link(entry_ids[11], "east", exp_ids[0])
        for j in range(4):
            link(exp_ids[j], "north", exp_ids[j+1])
        elite_id = monster(f"{prefix}_exp_elite", f"Mistrz Straży: {zone}", stage + 85, "elite")
        spawn(exp_ids[1], elite_id)
        spawn(exp_ids[2], elite_id)
        exp_boss = monster(f"{prefix}_exp_boss", f"Legenda Podziemi: {zone}", stage + 120, "boss", relic=relic_id)
        spawn(exp_ids[-1], exp_boss)
        for ch, target in enumerate((elite_id, exp_boss), 1):
            qid = f"{prefix}_expedition_{ch}"
            quest(qid, f"Ekspedycja {zone} — {'Pierwsza próba' if ch==1 else 'Finał'}",
                  guide_name, "kill", target, 3 if ch==1 else 1,
                  f"Przejdź ekspedycję {zone} i pokonaj {3 if ch==1 else 1} przeciwników: "
                  f"{mobs[target]['name']}. Wróć po nagrodę; nagrody za ukończenie pierwszego razu są trwałe.",
                  stage+80+ch*35, requires=qids[-1] if ch==1 else f"{prefix}_expedition_1")
            qids.append(qid)
        # Repeatable chronicle for farming without infinitely many quest rows.
        for cycle, target in enumerate((foe_ids[0], foe_ids[1], exp_boss), 1):
            qid = f"{prefix}_chronicle_{cycle}"
            quest(qid, f"Kronika {zone} — {'Patrol' if cycle==1 else 'Łowca' if cycle==2 else 'Legenda'}",
                  guide_name, "kill", target, 8 if cycle < 3 else 1,
                  f"Powtarzalne wyzwanie kroniki {zone}: pokonaj {mobs[target]['name']}. "
                  "Postęp zlicza się po przyjęciu i zapisuje niezależnie.",
                  stage+cycle*25, requires=f"{prefix}_story_1", repeatable=True)
            qids.append(qid)
        npc(guide_key, guide_name, entry_ids[0],
            f"{lore} Pokażę ci historię krainy i wyprawy. Wpisz quest list {guide_name}.", qids)
        npc(witness_key, witness_name, entry_ids[7],
            f"Słyszałem o {relic_label}. Musisz poznać historię {zone}, zanim wyruszysz na finał.")

    # Old-world campaigns: the existing destinations keep all original NPCs and quests.
    for i, (place, zone, speaker, story, target_mob, resource, stage) in enumerate(OLD_STORIES):
        if place not in rooms or target_mob not in mobs:
            # Fail rather than advertising an impossible historical quest.
            raise RuntimeError(f"v3.10.0: brak starej lokacji lub celu {place}/{target_mob}")
        if resource not in items:
            raise RuntimeError(f"v3.10.0: brak istniejącego przedmiotu {resource}")
        speaker_key = f"v3100_old_{i}_npc"
        ids = []
        defs = (
            ("Wieści z miasta", "kill", target_mob, 3,
             f"Zbadaj {story.lower()}. Najpierw pokonaj 3 przeciwników: {mobs[target_mob]['name']}."),
            ("Zapasy dla ocalałych", "collect", resource, 2,
             f"Po przyjęciu tego etapu zdobądź 2 sztuki {items[resource]['name']}; dostarcz je NPC: {speaker}."),
            ("Ostatni napastnicy", "kill", target_mob, 6,
             f"Pokonaj jeszcze 6 przeciwników: {mobs[target_mob]['name']}. Rozwiąż sprawę {story.lower()}."),
            ("Raport dla miasta", "talk_npc", speaker_key, 1,
             f"Porozmawiaj z {speaker} w {zone}, by zakończyć sprawę {story.lower()}."),
        )
        for ch,(title,kind,target,needed,desc) in enumerate(defs, 1):
            qid = f"v3100_old_{i}_{ch}"
            quest(qid, f"{story} — {title}", speaker, kind, target, needed,
                  desc, stage + ch*3, requires=ids[-1] if ids else None,
                  target_npc=speaker_key if kind=="talk_npc" else None)
            ids.append(qid)
        npc(speaker_key, speaker, place,
            f"Mamy kłopoty: {story}. Pomóż mieszkańcom, a wynagrodzimy cię za każdy etap.", ids)

    # Mastery story campaigns for all 14 classes: no trained skill is removed,
    # and these quests intentionally do NOT pretend to grant new combat skills.
    class_targets = [f"v3100_{REALMS[i % 8][0]}_enemy_{i % 3}" for i in range(len(CLASS_NAMES))]
    for i, class_name in enumerate(CLASS_NAMES):
        key = f"v3100_class_{i:02d}"
        teacher_name = f"Kronikarz Mistrzostwa — {class_name}"
        target = class_targets[i]
        ids = []
        for ch, needed in ((1, 3), (2, 7)):
            qid = f"{key}_quest_{ch}"
            quest(qid, f"Droga Mistrza {class_name} — rozdział {ch}", teacher_name,
                  "kill", target, needed,
                  f"Aktywuj klasę {class_name}. Pokonaj {needed} przeciwników "
                  f"{mobs[target]['name']} w nowym świecie. "
                  "Nauczone wcześniej umiejętności pozostają aktywne.",
                  45 + (i%8)*22 + ch*14, requires=ids[-1] if ids else None,
                  required_class=class_name)
            ids.append(qid)
        npc(key, teacher_name, class_hall,
            f"Opowiem ci dzieje klasy {class_name}. To fabularne wyzwania, nie nowa umiejętność.", ids)

    # Professions: quests on truly existing catalog items (validated below).
    for i, (prof_name, item_id) in enumerate(PROFESSIONS):
        if item_id not in items:
            # Some professions have no matching craft output in old catalogs;
            # don't invent items that would be impossible to obtain.
            item_id = "soul_shard"
        if item_id not in items:
            raise RuntimeError("v3.10.0: brak soul_shard")
        key = f"v3100_prof_{i:02d}"
        teacher_name = f"Mistrz Wielkich Opowieści — {prof_name}"
        ids = []
        for ch, needed in ((1, 2), (2, 5)):
            qid = f"{key}_order_{ch}"
            quest(qid, f"{prof_name}: zamówienie mistrzowskie {ch}", teacher_name,
                  "collect", item_id, needed,
                  f"Po przyjęciu zamówienia zgromadź {needed} szt. {items[item_id]['name']} "
                  f"i oddaj u {teacher_name}. Łańcuch nie usuwa starego postępu profesji.",
                  30 + 35*ch + (i%5)*8, requires=ids[-1] if ids else None,
                  reward_profession=prof_name)
            ids.append(qid)
        npc(key, teacher_name, prof_hall,
            f"Prowadzę opowieść rzemiosła {prof_name}. Zlecenia to kolejne etapy, "
            "a nie obowiązek wyboru tylko jednej profesji.", ids)

    npc("v3100_chronicle_keeper", "Archiwista Kronik Bohaterów", lore_hall,
        "Osiem krain prowadzi własne kroniki bez ostatniego rozdziału. "
        "Po ukończeniu pierwszej części kampanii wracaj po godzinnych polowaniach.")

    if "legendy" in help_topics:
        raise RuntimeError("v3.10.0 kolizja pomocy legendy")
    help_topics["legendy"] = [
        f"ERA NIESKOŃCZONYCH LEGEND: wejście z {entrance_label}, kierunek {direction}; "
        f"powrót: {return_label}.",
        "Następnie idź na północny wschód do Galerii Ośmiu Bram. Stamtąd dojdziesz do każdej krainy, także Owadów i Elfów.",
        "Każdy region: kronikarz, pięć rozdziałów historii, dwa etapy ekspedycji i trzy godzinne Kroniki.",
        "Stare miasta również dostały odrębne czteroczęściowe historie; wpisz quest list <imię NPC>.",
        "Dom Mistrzów Klas: z Sali Drogowskazów w górę. Cech Rzemiosł: w dół. Archiwum Kronik: na zachód.",
        "Zadania: quest list <NPC>, quest accept <numer>, quest info <numer>, questy lub quest status.",
        "Przynieś = zdobądź przedmioty po przyjęciu zlecenia; zabij = walcz po przyjęciu; rozmowa = odwiedź wskazaną osobę.",
        "Nie dodano blokad poziomu, utrzymano SQLite, EXP Bank i Multi Cap. Nie ma pułapek losowych ani wymogu drużyny.",
        "Nowe bojowe skille mistrzostwa klas to dalszy etap aktualizacji, nie są jeszcze dostępne w tym wydaniu.",
    ]
    help_aliases["legenda"] = "legendy"
    help_aliases["zapomniane_krainy"] = "legendy"
    return stats
