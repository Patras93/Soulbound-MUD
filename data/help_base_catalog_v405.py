# -*- coding: utf-8 -*-
"""API pomocy v4.00.5: zgodnosc z dawnym kodem; dane w osobnych modulach."""

def make_help_topic_aliases_v405():
    """Build the original v4.00.4 HELP_TOPIC_ALIASES data as a fresh dictionary."""
    return {
        "temat": "tematy", "topics": "tematy",
        "kategorie": "kategorie", "categories": "kategorie", "category": "kategorie",
        "all": "wszystko",
        "commands": "komendy", "command": "komendy",
        "basics": "podstawy",
        "movement": "nawigacja",
        "stats": "statystyki", "stat": "statystyki",
        "odmiana": "odmiana_imienia", "przypadki": "odmiana_imienia", "namecases": "odmiana_imienia", "declension": "odmiana_imienia",
        "combat": "walka", "fight": "walka", "combatlog": "walka", "logwalki": "walka",
        "walk": "nawigacja", "guide": "nawigacja", "prowadzenie": "nawigacja", "autowalk": "nawigacja", "navigation": "nawigacja",
        "endgameprof": "endgame_profesje", "profesje200": "endgame_profesje", "receptury200": "endgame_profesje",
        "login": "logowanie", "logowanie": "logowanie", "spawn": "logowanie", "start": "logowanie",
        "critical": "krytyki", "crit": "krytyki",
        "statgrowth": "rozwoj_statystyk", "rozwojstatystyk": "rozwoj_statystyk", "rozwoj": "rozwoj_statystyk",
        "uzyjskill": "uzywanie_umiejetnosci", "uzywanieumiejetnosci": "uzywanie_umiejetnosci", "useskill": "uzywanie_umiejetnosci",
        "criticalhits": "krytyki", "krytyk": "krytyki",
        "krytyki": "krytyki",
        "respawn": "respawn", "odrodzenie": "respawn",
        "odradzanie": "respawn",
        "bosses": "bossowie", "boss": "bossowie", "bossowie": "bossowie", "herszt": "bossowie",
        "mobhp": "hp_mobow", "hpmobow": "hp_mobow", "hpprzeciwnikow": "hp_mobow",
        "bosshp": "hp_bossow_lochow", "hpbossow": "hp_bossow_lochow",
        "soul": "dusza", "soulweapon": "dusza",
        "soulxp": "soul_xp_bloki",
        "duszaexp": "soul_xp_bloki", "expsoul": "soul_xp_bloki",
        "money": "pieniadze", "economy": "pieniadze",
        "kurs": "kurs_walut", "waluty": "kurs_walut", "currency": "kurs_walut",
        "wartoscsatki": "wartosc_siatki", "wartoscsiatki": "wartosc_siatki", "netvalue": "wartosc_siatki",
        "equipment": "ekwipunek", "items": "ekwipunek",
        "rarity": "loot_krypty", "rzadkosc": "loot_krypty", "rzadkość": "loot_krypty", "set": "loot_krypty", "lootkrypty": "loot_krypty", "sety krypty": "loot_krypty",
    
        "professions": "profesje",
        "fishing": "wedkarstwo", "fish": "wedkarstwo",
        "laki": "laki", "laka": "laki", "meadows": "laki", "meadow": "laki",
    
        "codex": "codex_swiata", "kodeks": "codex_swiata",
        "kodeksklasowy": "kodeks_klasowy", "kodeks klasowy": "kodeks_klasowy",
        "classcodex": "kodeks_klasowy", "class codex": "kodeks_klasowy",
        "skillcodex": "kodeks_klasowy", "skill codex": "kodeks_klasowy",
        "rarezasoby": "rare_resources", "rzadkiezasoby": "rare_resources",
        "atlaszasobow": "atlas_kompletny", "atlaszasobów": "atlas_kompletny",
        "zasobyswiata": "zasoby_swiata", "worldresources": "zasoby_swiata",
        "roslinyswiata": "zasoby_swiata", "rybyswiata": "zasoby_swiata",
        "autooff": "auto_off", "off": "auto_off",
        "autochodzenie": "auto_chodzenie", "automove": "auto_chodzenie",
        "kopalnia": "kopalnia_200", "mine200": "kopalnia_200",
        "water": "woda", "woda": "woda", "lowisko": "woda", "łowisko": "woda",
        "dziennikryb": "dziennik_ryb", "fishjournal": "dziennik_ryb", "fishlog": "dziennik_ryb",
        "wiecejryb": "wiecej_ryb", "moreryb": "wiecej_ryb", "morefish": "wiecej_ryb",
        "turnin": "oddawanie_zadan", "oddaj": "oddawanie_zadan",
        "mining": "gornictwo", "mine": "gornictwo",
        "woodcutting": "drwalstwo", "drwal": "drwalstwo",
        "crafting": "rzemioslo", "craft": "rzemioslo", "rzemiosło": "rzemioslo",
        "cooking": "gotowanie_rozbudowane", "cook": "gotowanie_rozbudowane",
        "gotowanie": "gotowanie_rozbudowane", "kuchnia": "gotowanie_rozbudowane",
        "herbalism": "zielarstwo", "zielarstwo": "zielarstwo",
        "alchemy": "alchemia", "alchemia": "alchemia",
        "recipes": "receptury", "recipe": "receptury", "przepisy": "receptury",
        "containers": "pojemniki",
        "shops": "sklepy", "shop": "sklepy",
        "multiplayer": "gracze", "players": "gracze",
        "death": "smierc",
        "races": "rasy", "race": "rasy",
        "classes": "klasy", "class": "klasy",
        "descriptions": "opisy", "describe": "opisy",
        "skills": "umiejetnosci", "abilities": "umiejetnosci",
        "skillnames": "nazwy_skilli", "nazwyskilli": "nazwy_skilli",
        "teachers": "nauczyciele", "trainers": "nauczyciele",
        "multiclass": "multiclass", "multiklasa": "multiclass",
        "multiklas": "multiclass", "klasy": "multiclass",
        "changes": "zmiany", "changelog": "zmiany",
        "quest": "questy", "quests": "questy", "questy": "questy", "zadania": "questy",
        "corpse": "zwloki", "body": "zwloki", "cialo": "zwloki", "ciało": "zwloki",
        "loot": "zwloki", "zwloki": "zwloki", "zwłoki": "zwloki",
        "crypt": "krypta", "krypta": "krypta",
        "portal": "portale", "portals": "portale", "portale": "portale",
        "portalkrypty": "portale", "cryptportal": "portale",
        "checkpoint": "portale", "checkpoints": "portale",
        "punktkrypty": "portale", "punktykrypty": "portale",
        "atlas": "atlas", "atlasy": "atlas",
        "party": "druzyny", "parties": "druzyny", "druzyna": "druzyny", "drużyna": "druzyny",
        "zaslon": "druzyny", "zasłoń": "druzyny", "oslon": "druzyny", "osłoń": "druzyny",
        "zaproś": "druzyny", "zapros": "druzyny", "opusc": "druzyny", "opuść": "druzyny",
        "charisma": "charyzma", "charyzma": "charyzma", "haryzma": "charyzma",
        "historia": "historia", "history": "historia", "lifetime": "historia", "lifestats": "historia",
    }

def make_help_topics_v405():
    """Nowy slownik przy kazdym wywolaniu; bez wspoldzielonych list."""
    catalog = {}
    from data.help_topics_v405 import economy_social
    catalog.update(economy_social.make_topics())
    from data.help_topics_v405 import navigation_craft
    catalog.update(navigation_craft.make_topics())
    from data.help_topics_v405 import quests_resources
    catalog.update(quests_resources.make_topics())
    from data.help_topics_v405 import world_exploration
    catalog.update(world_exploration.make_topics())
    from data.help_topics_v405 import professions_equipment
    catalog.update(professions_equipment.make_topics())
    from data.help_topics_v405 import progression
    catalog.update(progression.make_topics())
    return catalog
