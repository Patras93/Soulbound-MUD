V021_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0210-ascension-world-tiers-mythic"
V021_ASCENSION_MAX_RANK = 1000
V021_WORLD_TIER_MAX = 10
V021_ASCENSION_REQ = (
    (1,100_000_000_000_000),(10,500_000_000_000_000),(25,2_000_000_000_000_000),
    (50,8_000_000_000_000_000),(100,40_000_000_000_000_000),(250,200_000_000_000_000_000),
    (500,800_000_000_000_000_000),(1000,8_000_000_000_000_000_000),
)
V021_WORLD_TIER_ASCENSION_REQUIREMENT={1:0,2:0,3:5,4:10,5:20,6:35,7:55,8:80,9:120,10:180}

def v0210_ascension_xp_to_next(rank):
    rank=max(0,int(rank or 0))
    if rank>=V021_ASCENSION_MAX_RANK: return 0
    return v0190_log_curve(rank+1,V021_ASCENSION_REQ)

def v0210_world_tier_multipliers(tier):
    tier=max(1,min(V021_WORLD_TIER_MAX,int(tier or 1))); step=tier-1
    return {
        "effective_hp":1.0+0.22*step,
        "enemy_damage":1.0+0.16*step,
        "reward":1.0+0.25*step,
    }

V021_ENDGAME_MATERIALS={
    "v021_ascension_crystal":("Kryształ Wzniesienia","Materiał z bossów megalochów używany w najwyższych progach artefaktów."),
    "v021_world_tier_crest":("Herb World Tieru","Mityczny znak zdobywany z najwyższych world bossów i prób World Tier."),
    "v021_eternal_sigil":("Wieczny Sigil","Rzadki materiał z finałów i Endless Gauntletu; wymagany przez artefakty Tier 8-10."),
}
for _iid,(_name,_desc) in V021_ENDGAME_MATERIALS.items():
    ITEMS[_iid]={"name":_name,"type":"material","price":None,"rarity":"mythic","rarity_name":"Mityczny","desc":_desc}
    UNIQUE_ITEM_COLLECTION_CATALOG.setdefault(_iid,_name)

# Existing v0.20 bosses feed the new material loop.
for _tid,_t in list(MOB_TEMPLATES.items()):
    if _t.get("v020_mythic_world_boss"):
        _t.setdefault("drops",{}).setdefault("v021_world_tier_crest",0.50)
    if _t.get("v020_gauntlet") and int(_t.get("v020_gauntlet_round",0) or 0)==5:
        _t.setdefault("drops",{}).setdefault("v021_eternal_sigil",0.35)

# Five 13-piece mythic sets, one per v0.20 megadungeon.
V021_MYTHIC_SET_ITEMS={}
V021_MYTHIC_SET_NAMES={
    "echo":"Regalia Tysiąca Ech","abyss":"Regalia Otchłannego Archiwum",
    "forge":"Regalia Pierwszych Tytanów","verdant":"Regalia Wiecznych Korzeni",
    "null":"Regalia Bezimiennej Korony",
}
V021_MYTHIC_SET_BONUS={"hp":1.06,"damage":1.06,"defense":1.08,"complete":1.05}
_v021_slots=tuple(CLASS_EQUIPMENT_SLOT_DEFS.items())
for _set_index,(_key,_spec) in enumerate(V020_MEGADUNGEONS.items()):
    _ids=[]; _stage=int(_spec["stage"]); _label=V021_MYTHIC_SET_NAMES[_key]
    for _slot_index,(_slot,(_slot_name,_def_delta,_price)) in enumerate(_v021_slots):
        _iid=f"v021_mythicset_{_key}_{_slot}"
        _def=max(25,int(round(v0190_log_curve(_stage,V019_DAMAGE_NORMAL)*0.018))) + _slot_index*3
        _affix={
            "head":"strength", "body":"constitution", "hands":"dexterity", "legs":"constitution",
            "feet":"dexterity", "charm":"willpower", "ring":"dexterity", "necklace":"willpower",
            "shoulders":"constitution", "belt":"constitution", "cloak":"dexterity",
            "bracers":"strength", "relic":"willpower",
        }.get(_slot, "constitution")
        _amount=max(20,int(round(_stage*0.22)))
        ITEMS[_iid]={"name":f"{_slot_name} — {_label}","type":"armor","slot":_slot,"defense":_def,"price":None,
            "rarity":"mythic","rarity_name":"Mityczny","sockets":4,"affix":_affix,"affix_amount":_amount,
            "required_mastery":400,"v021_mythic_set":_key,
            "desc":f"Część 14-elementowego zestawu {_label}. Progi bonusów pozostają 2/4/6/8. Wymaga Biegłości 400. Bez RNG i bez pułapek."}
        EQUIPMENT_COLLECTION_CATALOG[_iid]=ITEMS[_iid]["name"]; UNIQUE_ITEM_COLLECTION_CATALOG[_iid]=ITEMS[_iid]["name"]; _ids.append(_iid)
    V021_MYTHIC_SET_ITEMS[_key]=tuple(_ids)

# -------------------- ENDLESS GAUNTLET --------------------
V021_ENDLESS_GAUNTLET_PREFIX="v021_endless_gauntlet_"
def v0210_endless_gauntlet_room_id(round_no): return f"{V021_ENDLESS_GAUNTLET_PREFIX}{max(1,int(round_no)):06d}"
def v0210_endless_gauntlet_identity(room_id):
    m=re.fullmatch(r"v021_endless_gauntlet_(\d{6})",str(room_id or ""))
    return int(m.group(1)) if m and int(m.group(1))>=1 else None

def v0210_endless_gauntlet_band(round_no): return min(100,1+(max(1,int(round_no))-1)//5)

def v0210_endless_gauntlet_template(round_no):
    band=v0210_endless_gauntlet_band(round_no); tid=f"v021_endless_gauntlet_boss_b{band:03d}"
    if tid in MOB_TEMPLATES: return tid
    mult=min(4000.0,1.0+(band-1)*0.20)
    reward_mult=min(400000.0,1.0+(band-1)*0.35)
    base_hp=int(round(v0190_log_curve(400,V019_HP_NORMAL)*12.0*mult))
    base_dmg=int(round(v0190_log_curve(400,V019_DAMAGE_NORMAL)*1.75*(1.0+(band-1)*0.06)))
    MOB_TEMPLATES[tid]={"name":f"Strażnik Endless Gauntlet — pasmo {band}","max_hp":min(V019_SAFE_INT,max(1,base_hp)),
        "damage":min(V019_SAFE_INT,max(1,base_dmg)),"damage_type":"magic" if band%2 else "physical",
        "class_xp_reward":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_CLASS_KILL_BOSS)*reward_mult)),
        "soul_reward":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_SOUL_KILL_BOSS)*reward_mult)),
        "stat_reward":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_STAT_KILL_BOSS)*reward_mult)),
        "silver":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_COIN_KILL_BOSS)*reward_mult)),"gold":0,"mithril":0,
        "drops":{"v021_eternal_sigil":1.0,"v021_ascension_crystal":0.75,"v021_world_tier_crest":0.45,"v020_mythic_essence":1.0},
        "auto_aggro":False,"stationary_mob":True,"boss_mechanic":"two_hundred_lord","boss_mechanic_text":"Endless Gauntlet; fazy 75/50/25%. PASSIVE WORLD.",
        "v017_boss_phases":True,"v021_endless_gauntlet":True,"v021_endless_band":band,"v019_stage":400,"world_boss":True,"respawn_seconds":6*60*60}
    BOSS_COLLECTION_CATALOG[tid]=MOB_TEMPLATES[tid]["name"]
    return tid

def v0210_create_endless_gauntlet_room_definition(room_id):
    round_no=v0210_endless_gauntlet_identity(room_id)
    if round_no is None: return None,()
    if room_id in ROOMS: return room_id,()
    prev=V020_GAUNTLET_LOBBY if round_no==1 else v0210_endless_gauntlet_room_id(round_no-1)
    nxt=v0210_endless_gauntlet_room_id(round_no+1)
    band=v0210_endless_gauntlet_band(round_no)
    ROOMS[room_id]={"zone":"Endless Gauntlet","name":f"Endless Gauntlet — runda {round_no}",
        "desc":f"Nieskończona próba bossów. Runda {round_no}, pasmo {band}/100. Boss blokuje tylko przejście dalej; nie atakuje pierwszy. Brak pułapek.",
        "exits":{"south":prev,"north":nxt},"recommended_mastery":400,"generated_on_demand":True,
        "v021_endless_gauntlet_round":round_no,"v021_endless_band":band}
    return room_id,((room_id,v0210_endless_gauntlet_template(round_no)),)

HELP_TOPICS["ascension_v021"]=[
    "wzniesienie / ascension pokazuje progresję klasy po osiągnięciu Biegłości 400. Biegłość nie resetuje się.",
    "Każdy dalszy Class XP trafia do Rangi Wzniesienia. Maksymalna ranga techniczna to 1000; wymagania rosną do ekstremalnego endgame.",
]
HELP_TOPICS["worldtier_v021"]=[
    "worldtier / poziomswiata pokazuje lub ustawia osobisty World Tier 1-10. Zmiana jest możliwa tylko poza walką.",
    "Wyższy Tier zwiększa efektywną wytrzymałość i obrażenia przeciwników oraz nagrody. Tier 2+ wymaga Biegłości 400 i dalszych Rang Wzniesienia.",
    "World Tier nie włącza auto-aggro: PASSIVE WORLD nadal obowiązuje.",
]
HELP_TOPICS["mythicsets_v021"]=[
    "setymityczne / mythicsets pokazuje pięć 13-częściowych setów z megalochów; progi bonusów pozostają 2/4/6/8.",
    "Progi 2/4/6 dają HP, obrażenia i obronę; próg 8/13 daje dodatkowy mały bonus do wszystkich trzech. Dalsze sloty zwiększają swobodę doboru, nie dodają nowego progu setowego.",
]
HELP_TOPICS["endlessgauntlet_v021"]=[
    "wiecznagauntlet / endlessgauntlet uruchamia z Sali Boss Gauntletów nieskończoną próbę bossów.",
    "Co 5 rund rośnie pasmo trudności, do bezpiecznego pasma 100. Boss zawsze jest pasywny i blokuje wyłącznie przejście do następnej rundy.",
]
HELP_TOPIC_ALIASES.update({"wzniesienie":"ascension_v021","ascension":"ascension_v021","world tier":"worldtier_v021","poziom swiata":"worldtier_v021",
    "sety mityczne":"mythicsets_v021","mythic sets":"mythicsets_v021","wieczny gauntlet":"endlessgauntlet_v021","endless gauntlet":"endlessgauntlet_v021"})
COMMAND_ALIASES.update({"wzniesienie":"ascension","ascension":"ascension","poziomswiata":"worldtier","worldtier":"worldtier","worldtiers":"worldtier",
    "setymityczne":"mythicsets","mythicsets":"mythicsets","wiecznagauntlet":"endlessgauntlet","endlessgauntlet":"endlessgauntlet","mythicprogression":"mythicprogression","mitycznaprogresja":"mythicprogression"})

# ============================================================
# v0.22.0 - WORLD PROJECTS, LEGENDARY CONTRACTS, FISHING RECORDS 2.0
# ============================================================
V022_WORLD_PROJECTS = {
    "port": {
        "name": "Odbudowa Wielkiego Portu Dusz", "categories": ("wood","ore","fish","coins"),
        "title": "Budowniczy Wielkiego Portu",
        "desc": "Wspólna odbudowa nabrzeży, pomostów i magazynów Portu Dusz.",
    },
    "bridge": {
        "name": "Most Północnych Rubieży", "categories": ("wood","ore","herbs","coins"),
        "title": "Budowniczy Mostu Rubieży",
        "desc": "Wielki most łączący bezpieczny trakt z północnymi rubieżami.",
    },
    "tower": {
        "name": "Wieża Wielkich Kartografów", "categories": ("ore","wood","herbs","coins"),
        "title": "Fundator Wieży Kartografów",
        "desc": "Odbudowa wieży obserwacyjnej, archiwum map i latarni dla podróżników.",
    },
    "settlement": {
        "name": "Osada Końca Świata", "categories": ("wood","ore","fish","herbs","coins"),
        "title": "Założyciel Osady Końca Świata",
        "desc": "Największy projekt: stała osada dla wypraw w najdalszy endgame.",
    },
}
for _idx,(_pkey,_spec) in enumerate(V022_WORLD_PROJECTS.items(),1):
    _stage=generator_core_v027.stage_from_index(_idx,len(V022_WORLD_PROJECTS))
    _spec["stage"]=_stage
    _spec["min_points"]=generator_core_v027.generated_count(_stage,"world-project-points:"+_pkey,200,5000)
    _requirements={}
    for _cat in _spec.pop("categories"):
        if _cat=="coins":
            _requirements[_cat]=generator_core_v027.system_cost(_stage,"world-project:"+_pkey,20000.0)
        else:
            _requirements[_cat]=generator_core_v027.generated_count(_stage,f"world-project:{_pkey}:{_cat}",2500,100000)
    _spec["requirements"]=_requirements

V022_PROJECT_CATEGORY_LABELS={"wood":"drewno","ore":"rudy i minerały","fish":"ryby","herbs":"zioła","coins":"waluta"}
V022_PROJECT_RESOURCE_SOURCES={
    # Projekty automatycznie zużywają tylko zwykłe zasoby; rzadkie warianty,
    # surowe klejnoty i geody nie są zabierane bez wyraźnej decyzji gracza.
    "wood": ("woodpile", lambda: tuple(i for i in WOOD_STORAGE_IDS if not ITEMS.get(i,{}).get("rare_resource_variant"))),
    "ore": ("bag", lambda: tuple(ORE_STORAGE_IDS)),
    "fish": ("net", lambda: tuple(i for i in FISH_STORAGE_IDS if not ITEMS.get(i,{}).get("rare_resource_variant"))),
    "herbs": ("herbbag", lambda: tuple(i for i in HERB_STORAGE_IDS if not ITEMS.get(i,{}).get("rare_resource_variant"))),
}

def v022_project_reward(project_key):
    spec=V022_WORLD_PROJECTS[project_key]
    stage=int(spec["stage"])
    complexity=2.0 + len(spec.get("requirements",{})) * 0.75 + stage/160.0
    return {
        "character_xp": generator_core_v027.axis_gain("character",stage,complexity),
        "class_xp": generator_core_v027.axis_gain("class",stage,complexity),
        "soul_xp": generator_core_v027.axis_gain("soul",stage,complexity),
        "coins": min(CURRENCY_SQLITE_SAFE_TOTAL,generator_core_v027.system_reward(stage,"world-project:"+project_key,complexity*3.0)),
    }

V022_LEGENDARY_KINDS=("kill","boss","worldboss","fish","gather","explore")
V022_LEGENDARY_LABELS={
    "kill":"Wielkie Polowanie","boss":"Łańcuch Bossów","worldboss":"Łowy na World Bossy",
    "fish":"Legendarna Wyprawa Rybacka","gather":"Kontrakt Wielkiego Zbioru","explore":"Ekspedycja Kartograficzna",
}

V027_LEGENDARY_MIN_MASTERY = 1 + int(generator_core_v027.stable_unit("legendary-contract-unlock") * 399)

def v022_legendary_contract_offer(kind, stage):
    stage=max(V027_LEGENDARY_MIN_MASTERY,min(400,int(stage or V027_LEGENDARY_MIN_MASTERY)))
    base=generator_core_v027.generated_count(stage,"legendary:"+kind,30,300)
    divisors={"kill":1,"boss":12,"worldboss":35,"fish":1,"gather":1,"explore":2}
    needed=max(1,int(round(base/divisors.get(kind,1))))
    complexity=2.5 + (stage/120.0) + generator_core_v027.stable_unit("legendary-complexity:"+kind)*2.0
    return {
        "kind":kind,"label":f"{V022_LEGENDARY_LABELS[kind]}: {needed}","needed":needed,"stage":stage,
        "reward_character_xp":generator_core_v027.axis_gain("character",stage,complexity),
        "reward_class_xp":generator_core_v027.axis_gain("class",stage,complexity),
        "reward_soul_xp":generator_core_v027.axis_gain("soul",stage,complexity),
        "reward_coins":min(CURRENCY_SQLITE_SAFE_TOTAL,generator_core_v027.system_reward(stage,"legendary:"+kind,complexity*2.0)),
    }

def v022_fish_rarity_score(item_id):
    base=base_fish_species_id(item_id); base_rank={"common":1,"uncommon":2,"rare":3,"epic":4,"legendary":5}.get(fish_species_rarity(base),1)
    variant=str(ITEMS.get(item_id,{}).get("rare_resource_variant") or "")
    bonus={"":0,"albino":1,"golden":2,"giant":3,"ancient":5}.get(variant,0)
    return base_rank*10+bonus

def v022_fish_rarity_text(item_id):
    base=base_fish_species_id(item_id); text=fish_rarity_label(base); variant=str(ITEMS.get(item_id,{}).get("rare_resource_variant") or "")
    if variant in FISH_RARE_VARIANTS: text += f" + {FISH_RARE_VARIANTS[variant]['label']}"
    return text

HELP_TOPICS["worldprojects_v022"]=[
    "projekty / worldprojects pokazuje wspólne, trwałe projekty całego świata i ich globalny postęp.",
    "projekt <nazwa> pokazuje szczegóły. projekt oddaj <nazwa> <drewno|rudy|ryby|ziola> <ilość> przekazuje zasoby z magazynu profesji.",
    "projekt wplac <nazwa> <kwota> <srebro|zloto|mithril> przekazuje walutę. projekt odbierz <nazwa> odbiera nagrodę po ukończeniu, jeśli masz wymagany osobisty wkład.",
]
HELP_TOPICS["legendarycontracts_v022"]=[
    f"legendarycontracts / legendarnekontrakty pokazuje trzy wielkie kontrakty. Wymagają wygenerowanej Biegłości co najmniej {V027_LEGENDARY_MIN_MASTERY}.",
    "Każdy przyjęty kontrakt startuje 0/x. Cel, Character XP, Class XP, Soul XP i waluta są liczone przez Generator Core v0.30.0.",
    "Komendy: legendarycontracts accept <1-3>; legendarycontracts aktywne; legendarycontracts odbierz; legendarycontracts odswiez.",
]
HELP_TOPICS["fishingrecords_v022"]=[
    "rekordyryb / fishrecords pokazuje Fishing Records 2.0: osobiste rekordy, najrzadszy okaz i rekordy całego serwera.",
    "rekordyryb <gatunek> pokazuje rekord masy i długości gatunku wraz z właścicielami rekordów.",
]
HELP_TOPIC_ALIASES.update({"projekty swiata":"worldprojects_v022","world projects":"worldprojects_v022","legendarne kontrakty":"legendarycontracts_v022","legendary contracts":"legendarycontracts_v022","rekordy ryb":"fishingrecords_v022","fishing records":"fishingrecords_v022"})

# v0.23: finalny audit HELP — naprawa aktywnych aliasów wskazujących na brakujące tematy.
HELP_TOPICS["klasy"] = [
    "Soulbound ma 14 klas. Nie ma levelu postaci; każda klasa rozwija własną Biegłość 1-400.",
    "Klasa główna jest wybierana przy tworzeniu postaci. Dodatkowe aktywne klasy obsługuje multiclass / multiklasa.",
    "multiclass pokazuje aktywne klasy i komendy dodawania/usuwania klas zgodnie z aktualnymi wymaganiami.",
    "kodeksklasowy info pokazuje wszystkie klasy; kodeksklasowy <klasa> czyta nauczyciela, skille, wymagania Biegłości, koszt i status nauki.",
    "skills pokazuje skille aktywnych klas, a help <nazwa skilla> daje szczegóły konkretnej umiejętności.",
]
HELP_TOPICS["odmiana_imienia"] = [
    "odmiana / przypadki / declension pokazuje siedem zapisanych form imienia postaci.",
    "Czytane są: mianownik, dopełniacz, celownik, biernik, narzędnik, miejscownik i wołacz.",
    "Formy są ustawiane przy tworzeniu postaci. Dla starszych postaci bez pełnej odmiany gra bezpiecznie używa zapisanego imienia jako formy awaryjnej.",
]
HELP_TOPICS["pieniadze"] = [
    "portfel / wallet / saldo pokazuje jedno wspólne saldo konta w czytelnych nominałach.",
    "100 srebra = 1 złoto. 1000 złota = 1 mithril. Wewnętrznie to jedno saldo, a nominały są sposobem prezentacji i wpisywania kwot.",
    "Portfel jest wspólny dla postaci na koncie; zmiana postaci nie tworzy osobnej waluty.",
    "Zakupy korzystają z rabatu Charyzmy. Sprzedaż pojedyncza i skup profesyjny dopisują wartość do tego samego salda.",
    "bank obsługuje wpłaty/wypłaty waluty i przedmiotów; wpisz bank bez argumentu, aby usłyszeć składnię.",
]
COMMAND_ALIASES.update({
    "projekty":"worldprojects","projektyswiata":"worldprojects","worldprojects":"worldprojects",
    "projekt":"worldproject","worldproject":"worldproject",
    "legendarnekontrakty":"legendarycontracts","legendarycontracts":"legendarycontracts","legendarycontract":"legendarycontracts",
    "rekordyryb":"fishrecords","fishrecords":"fishrecords","fishingrecords":"fishrecords",
})


# ============================================================
# v0.28.0 - PROCEDURAL WORLD REGIONS 2.0
# Pełne regiony tworzone z seedu i etapu Generator Core: biom, graf,
# zwykłe moby, Elite/Rare, boss, sekrety, zasoby oraz quest chain.
# ============================================================
V028_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0280-regions"
V028_REGION_COUNT = 7
V028_PROCEDURAL_REGIONS = {}
V028_BIOMES = {
    "ancient_forest": {
        "label": "Pradawny Bór",
        "titles": ("Omszała Knieja", "Dolina Starych Dębów", "Korzenna Polana", "Cichy Zagajnik", "Las Kamiennych Pni"),
        "features": ("pradawny pień", "krąg mchu", "zarośnięty menhir", "zwalone drzewo", "świetlistą paproć"),
        "mob_words": ("Wilk", "Dzik", "Strażnik Korzeni", "Leśny Cień"),
        "resources": ("wood", "herb_forest"), "damage_type": "physical",
    },
    "mist_wetlands": {
        "label": "Mgliste Mokradła",
        "titles": ("Trzcinowe Rozlewisko", "Mglista Grobla", "Czarne Torfowisko", "Zatopiona Niecka", "Bagienny Przesmyk"),
        "features": ("martwe drzewo", "gęste trzciny", "zielone bajoro", "kamienną groblę", "świecący grzyb"),
        "mob_words": ("Pełzacz", "Bagienny Wąż", "Topielczy Cień", "Strażnik Trzcin"),
        "resources": ("herb_water", "fish_river"), "damage_type": "magic",
    },
    "storm_coast": {
        "label": "Burzowe Wybrzeże",
        "titles": ("Skalisty Brzeg", "Zatoka Nawałnicy", "Pęknięty Klif", "Molo Sztormów", "Rafa Gromu"),
        "features": ("rozbity maszt", "basen pływowy", "czarną rafę", "stary pomost", "uderzony piorunem głaz"),
        "mob_words": ("Krab Gromu", "Morski Maruder", "Sztormowy Upiór", "Strażnik Rafy"),
        "resources": ("fish_sea",), "damage_type": "magic",
    },
    "silver_lakes": {
        "label": "Srebrne Pojezierze",
        "titles": ("Cicha Zatoka", "Srebrny Brzeg", "Leśne Jezioro", "Kamienny Cypel", "Trzcinowa Toń"),
        "features": ("pas lilii", "zatopiony pień", "stary pomost", "jasny kamień", "głęboką zatokę"),
        "mob_words": ("Jeziorny Wilk", "Wodny Cień", "Strażnik Brzegu", "Srebrny Drapieżca"),
        "resources": ("fish_lake", "herb_water"), "damage_type": "physical",
    },
    "wind_highlands": {
        "label": "Wietrzne Wyżyny",
        "titles": ("Wysoka Grań", "Kamienna Półka", "Wietrzna Przełęcz", "Zielony Taras", "Urwisty Szlak"),
        "features": ("kamienny krąg", "stary drogowskaz", "wysoką trawę", "skalny schron", "źródło pod głazem"),
        "mob_words": ("Górski Wilk", "Skalny Dzik", "Harpia Wiatru", "Strażnik Grani"),
        "resources": ("herb_meadow", "wood"), "damage_type": "physical",
    },
    "star_grove": {
        "label": "Gwiezdny Gaj",
        "titles": ("Polana Gwiazd", "Lśniący Zagajnik", "Niebieska Knieja", "Krąg Światła", "Astralny Parów"),
        "features": ("świetlisty korzeń", "gwiezdny pył", "błękitny menhir", "krystaliczne liście", "krąg nieruchomego światła"),
        "mob_words": ("Astralny Jeleń", "Gwiezdny Cień", "Strażnik Światła", "Lśniący Drapieżca"),
        "resources": ("herb_forest", "wood"), "damage_type": "magic",
    },
    "void_delta": {
        "label": "Delta Pustki",
        "titles": ("Czarny Brzeg", "Bezgwiezdne Rozlewisko", "Martwy Przypływ", "Ciemna Odnoga", "Zatopiony Taras"),
        "features": ("czarną sadzawkę", "milczący dzwon", "ciemną rafę", "pęknięty posąg", "wir bez światła"),
        "mob_words": ("Rycerz Pustki", "Czarny Upiór", "Abyssalny Łowca", "Strażnik Delty"),
        "resources": ("fish_ocean", "herb_water"), "damage_type": "magic",
    },
    "eternal_meadow": {
        "label": "Łąki Wieczności",
        "titles": ("Biała Polana", "Łąka Bez Cienia", "Koniczynowa Grań", "Ponadczasowa Niecka", "Pole Milczących Kwiatów"),
        "features": ("biały monolit", "krąg kwiatów", "nieruchomy strumień", "stary kamień", "świetlistą trawę"),
        "mob_words": ("Wieczny Jeleń", "Biały Wilk", "Strażnik Łąki", "Ponadczasowy Cień"),
        "resources": ("herb_meadow", "wood"), "damage_type": "physical",
    },
}


def _v028_pick(seq, key):
    seq = tuple(seq)
    return seq[int(generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:{key}") * len(seq)) % len(seq)]


def _v028_connect(a, direction, b, reverse):
    ROOMS[a].setdefault("exits", {})[direction] = b
    ROOMS[b].setdefault("exits", {})[reverse] = a


def _v028_region_room_id(index, x, y):
    return f"v028_region_{int(index):02d}_{int(x):02d}_{int(y):02d}"


def _v028_build_regions():
    if "cartographer_house" not in ROOMS:
        return
    # Deterministic biome permutation; no region carries a hand-authored level.
    biome_order = sorted(V028_BIOMES, key=lambda key: generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:biome:{key}"))
    gate_ids=[]
    for index in range(1, V028_REGION_COUNT + 1):
        stage = generator_core_v027.stage_from_index(index, V028_REGION_COUNT)
        biome_key = biome_order[(index - 1) % len(biome_order)]
        theme = V028_BIOMES[biome_key]
        gate_id=f"v028_region_gate_{index:02d}"; gate_ids.append(gate_id)
        width=4 + int(generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:{index}:w") > .52)
        height=4 + int(generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:{index}:h") > .52)
        max_distance=max(1,(width-1)+(height-1))
        zone=f"Proceduralny Region: {theme['label']}"
        ROOMS[gate_id]={
            "zone":"Pracownia Kartografa", "name":f"Brama Ekspedycji {index}: {theme['label']}",
            "desc":f"Stabilna brama do wygenerowanego regionu {theme['label']}. Docelowy etap Generator Core: {stage}.",
            "exits":{}, "safe_hub":True, "procedural_region_stage":stage, "v028_region_gate":index,
        }
        # Create grid rooms first.
        room_ids=[]
        for y in range(height):
            for x in range(width):
                rid=_v028_region_room_id(index,x,y); room_ids.append(rid)
                dist=x+y
                span=max(6,min(28,400-stage))
                room_stage=min(400,stage+int(round((dist/max_distance)*span)))
                title=_v028_pick(theme["titles"],f"r{index}:{x}:{y}:title")
                feature=_v028_pick(theme["features"],f"r{index}:{x}:{y}:feature")
                ROOMS[rid]={
                    "zone":zone,"name":f"{title} — sektor {x+1}-{y+1}",
                    "desc":f"Wygenerowany sektor biomu {theme['label']}. Wyróżnia się tu {feature}. Układ, przeciwnicy i zasoby wynikają z trwałego seedu świata.",
                    "exits":{},"procedural_region_v028":index,"procedural_biome_v028":biome_key,
                    "procedural_region_stage":room_stage,"procedural_x":x,"procedural_y":y,
                }
        # Spanning comb guarantees connectivity; seeded extra edges create loops.
        for y in range(height):
            for x in range(width):
                rid=_v028_region_room_id(index,x,y)
                if x>0:
                    left=_v028_region_room_id(index,x-1,y)
                    _v028_connect(left,"east",rid,"west")
                if y>0:
                    below=_v028_region_room_id(index,x,y-1)
                    must_connect=(x==0)
                    extra=generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:edge:{index}:{x}:{y}")>.47
                    if must_connect or extra:
                        _v028_connect(below,"north",rid,"south")
        entry=_v028_region_room_id(index,0,0)
        boss_room=_v028_region_room_id(index,width-1,height-1)
        ROOMS[gate_id]["exits"]["down"]=entry; ROOMS[entry]["exits"]["up"]=gate_id

        # Secrets are side rooms chosen by seed, never the entry or boss room.
        secret_candidates=[rid for rid in room_ids if rid not in (entry,boss_room)]
        secret_candidates.sort(key=lambda rid: generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:secret:{rid}"), reverse=True)
        secret_ids=[]
        for sn,base in enumerate(secret_candidates[:2],1):
            sid=f"v028_region_{index:02d}_secret_{sn:02d}"; secret_ids.append(sid)
            sstage=ROOMS[base]["procedural_region_stage"]
            ROOMS[sid]={"zone":zone,"name":f"Sekret {theme['label']} {sn}",
                "desc":f"Ukryta odnoga regionu {theme['label']}. Generator oznaczył to miejsce jako sekret ekspedycji.",
                "exits":{"up":base},"procedural_region_v028":index,"procedural_secret":True,
                "procedural_region_stage":sstage}
            ROOMS[base]["exits"]["down"]=sid

        # Real gathering locations are generated from biome semantics.
        resource_rooms=[]
        for rid in room_ids:
            if generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:resource:{rid}")>.66:
                _v0130_apply_resources(rid,{"resources":theme["resources"]}); resource_rooms.append(rid)
        if not resource_rooms:
            _v0130_apply_resources(entry,{"resources":theme["resources"]}); resource_rooms=[entry]

        # Region-specific relic; Generator Core owns its value/price/drop rate.
        relic_id=f"v028_region_{index:02d}_relic"
        ITEMS[relic_id]={"name":f"Relikt: {theme['label']}","type":"material","price":1,"currency":"silver",
            "desc":f"Relikt znaleziony w proceduralnym regionie {theme['label']}.","procedural_region_stage":stage,
            "resource_category":"procedural_relic"}

        normal_ids=[]
        for mi in range(4):
            mid=f"v028_region_{index:02d}_mob_{mi+1}"
            word=theme["mob_words"][mi % len(theme["mob_words"])]
            MOB_TEMPLATES[mid]={"name":f"{word} {theme['label']}","damage_type":theme["damage_type"],
                "drops":{relic_id:.05},"procedural_region_stage":stage,"quest_targets":(f"v028_region_{index:02d}_threat",),
                "elite_eligible":True,"rare_eligible":True}
            normal_ids.append(mid)
        elite_id=f"v028_region_{index:02d}_elite"
        MOB_TEMPLATES[elite_id]={"name":f"Elitarny Strażnik — {theme['label']}","damage_type":theme["damage_type"],
            "drops":{relic_id:.18},"procedural_region_stage":min(400,stage+6),"elite_affix":"procedural",
            "quest_targets":(f"v028_region_{index:02d}_threat",f"v028_region_{index:02d}_elite_target")}
        rare_id=f"v028_region_{index:02d}_rare"
        MOB_TEMPLATES[rare_id]={"name":f"Rzadki Wędrowiec — {theme['label']}","damage_type":theme["damage_type"],
            "drops":{relic_id:.30},"procedural_region_stage":min(400,stage+10),"rare_mob":True,
            "quest_targets":(f"v028_region_{index:02d}_threat",f"v028_region_{index:02d}_rare_target")}
        boss_id=f"v028_region_{index:02d}_boss"
        MOB_TEMPLATES[boss_id]={"name":f"Władca Regionu — {theme['label']}","damage_type":theme["damage_type"],
            "drops":{relic_id:1.0},"procedural_region_stage":min(400,stage+18),"boss_mechanic":"procedural_region",
            "boss_mechanic_text":"Generator regionu wybiera fazę presji na podstawie etapu i biomu.",
            "quest_targets":(f"v028_region_{index:02d}_boss_target",),"leave_corpse":True}

        # Seeded spawn layout: normal population everywhere, one Elite, one Rare and final boss.
        non_boss=[rid for rid in room_ids if rid!=boss_room]
        for rid in non_boss:
            pick=int(generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:spawn:{rid}")*len(normal_ids))%len(normal_ids)
            MOB_SPAWNS.append((rid,normal_ids[pick]))
            if generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:spawn2:{rid}")>.74:
                MOB_SPAWNS.append((rid,normal_ids[(pick+1)%len(normal_ids)]))
        elite_room=sorted(non_boss,key=lambda rid:generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:elite:{rid}"),reverse=True)[0]
        rare_room=sorted([rid for rid in non_boss if rid!=elite_room],key=lambda rid:generator_core_v027.stable_unit(f"{V028_WORLD_SEED}:rare:{rid}"),reverse=True)[0]
        MOB_SPAWNS.extend(((elite_room,elite_id),(rare_room,rare_id),(boss_room,boss_id)))

        # Three generated quests per region. Their levels/rewards are recalculated by the final Core pass.
        guide_id=f"v028_region_{index:02d}_guide"; guide_name=f"Przewodnik {theme['label']}"
        q1=f"v028_region_{index:02d}_hunt"; q2=f"v028_region_{index:02d}_elite_quest"; q3=f"v028_region_{index:02d}_boss_quest"
        QUESTS[q1]={"name":f"Ekspedycja {theme['label']}: Czystka","giver":guide_name,"kind":"kill",
            "target":f"v028_region_{index:02d}_threat","needed":generator_core_v027.generated_count(stage,f"v028:{index}:hunt",8,18),
            "description":f"Pokonaj zagrożenia wygenerowanego regionu {theme['label']}.","reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS}
        QUESTS[q2]={"name":f"Ekspedycja {theme['label']}: Elita","giver":guide_name,"kind":"kill",
            "target":f"v028_region_{index:02d}_elite_target","needed":1,"requires_quest":q1,
            "description":f"Pokonaj elitarnego strażnika regionu {theme['label']}.","reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS}
        QUESTS[q3]={"name":f"Ekspedycja {theme['label']}: Władca","giver":guide_name,"kind":"kill",
            "target":boss_id,"needed":1,"requires_quest":q2,
            "description":f"Pokonaj bossa proceduralnego regionu {theme['label']}.","reward_items":{relic_id:1},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS}
        NPCS[guide_id]={"name":guide_name,"room":gate_id,
            "dialogue":f"Prowadzę wyprawy do regionu {theme['label']}. Generator Core dobiera trudność do etapu tej ekspedycji.",
            "quest":q1,"quest_chain":(q1,q2,q3)}
        V028_PROCEDURAL_REGIONS[index]={"index":index,"stage":stage,"biome":biome_key,"name":theme["label"],"gate":gate_id,
            "entry":entry,"boss_room":boss_room,"boss":boss_id,"elite":elite_id,"rare":rare_id,"rooms":tuple(room_ids),
            "secrets":tuple(secret_ids),"resource_rooms":tuple(resource_rooms),"quests":(q1,q2,q3),"relic":relic_id}

    # Safe corridor of expedition gates, attached to the Cartographer workshop.
    for i,gate in enumerate(gate_ids):
        if i>0: _v028_connect(gate_ids[i-1],"east",gate,"west")
    if "east" not in ROOMS["cartographer_house"].setdefault("exits",{}):
        ROOMS["cartographer_house"]["exits"]["east"]=gate_ids[0]
        ROOMS[gate_ids[0]]["exits"]["west"]="cartographer_house"


_v028_build_regions()

HELP_TOPICS["procedural_regions_v028"]=[
    "generator regiony pokazuje regiony Procedural World Generator 2.0 wraz z wygenerowanym etapem.",
    "Wejście: z Pracowni Kartografa idź na wschód do korytarza Bram Ekspedycji; każda brama ma zejście do własnego regionu.",
    "Każdy region generuje biom, zapętlony układ sektorów, normalne moby, Elite, Rare, bossa, dwa sekrety, miejsca zbieractwa, relikt i trzy questy.",
    "HP, damage, XP, monety, ceny, drop-rate i wymagania questów nie są wpisywane per region — wylicza je Generator Core.",
]
HELP_TOPIC_ALIASES.update({"regiony proceduralne":"procedural_regions_v028","procedural regions":"procedural_regions_v028","region generator":"procedural_regions_v028"})

HELP_TOPICS["generator_swiata_v0281"]=[
    "v0.30.0: Semantic Total Procedural World — generator topologii respektuje role lokacji, geografię i semantyczne bramy; zwykłe połączenia są poziome, a góra/dół zostają dla prawdziwych pionowych przejść.",
    "World Logic Validator blokuje nielogiczne skoki typu miasto -> góry/endgame, sprawdza pełną osiągalność i drogę powrotną dla całego świata.",
    "Dostępne są także kierunki ukośne: NE/SE/SW/NW oraz polskie skróty PNW/PDW/PDZ/PNZ.",
    "generator logika pokazuje audyt logiki świata.",
    "v0.28.1: Universal World Topology Generator generuje układ wszystkich dawniej stałych stref, w tym całego Miasta Dusz i Gildii.",
    "Nazwy i funkcje miejsc są semantyką świata, ale połączenia poziome nie są już źródłem ręcznym: generator tworzy spójny graf z pętlami na podstawie stałego seedu.",
    "Bramy między strefami oraz pionowe wejścia są kotwicami kompatybilności; Krypty, rubieże, regiony v0.28 i inne dynamiczne obszary mają własne generatory.",
    "generator topologia pokazuje audyt całej wygenerowanej mapy; generator miasto podaje parametry wygenerowanego Miasta Dusz.",
]
HELP_TOPIC_ALIASES.update({"generator swiata":"generator_swiata_v0281","topologia":"generator_swiata_v0281","procedural city":"generator_swiata_v0281","miasto proceduralne":"generator_swiata_v0281"})

# ============================================================
# v0.30.12 - NPC PRIVATE ROOMS + CHARACTER LEVEL AREA PROGRESSION
# ============================================================

def split_static_npcs_into_private_rooms_v03012():
    """Zapewnia maksymalnie jednego stałego NPC na pokój.

    Jeśli kilka stałych NPC dzieliło lokację, właściciel sklepu/usługi zostaje
    w dotychczasowym pokoju, a pozostali dostają osobne pokoje w tej samej
    strefie. Universal World Topology Generator podłącza te pokoje do grafu.
    Wędrowni NPC v0.16 zachowują swoją trasę i nie są przenoszeni.
    """
    by_room = {}
    travelers = set(globals().get("V016_TRAVELERS", {}) or {})
    for npc_id, npc in list(NPCS.items()):
        room_id = npc.get("room")
        if not room_id or room_id not in ROOMS or npc_id in travelers:
            continue
        # Dynamiczne NPC gildii powstają później i mają własne pokoje.
        if str(npc_id).startswith("player_guild_"):
            continue
        by_room.setdefault(room_id, []).append(npc_id)

    created = []
    moved = []
    for room_id, npc_ids in sorted(by_room.items()):
        if len(npc_ids) <= 1:
            continue

        seller = SHOP_SELLERS.get(room_id) if "SHOP_SELLERS" in globals() else None
        def priority(nid):
            npc = NPCS[nid]
            return (
                0 if nid == seller else 1,
                0 if npc.get("shopkeeper") else 1,
                0 if npc.get("teacher_class") else 1,
                str(npc.get("name", nid)).casefold(),
            )
        ordered = sorted(npc_ids, key=priority)
        keeper = ordered[0]
        base = ROOMS[room_id]
        zone = base.get("zone", "Miasto Dusz")
        base_level = int(base.get("generator_level", 1) or 1)

        for index, npc_id in enumerate(ordered[1:], 1):
            npc = NPCS[npc_id]
            private_id = f"npc_room_v03012_{npc_id}"
            # Bez ręcznych poziomych wyjść: generator topologii osadzi pokój
            # logicznie wewnątrz tej samej strefy.
            ROOMS[private_id] = {
                "zone": zone,
                "name": f"Pokój: {npc.get('name', npc_id)}",
                "desc": (
                    f"Osobne pomieszczenie NPC {npc.get('name', npc_id)}. "
                    f"Znajduje się w obrębie strefy {zone}."
                ),
                "exits": {},
                "npc_private_room_v03012": True,
                "npc_owner_v03012": npc_id,
                "npc_parent_room_v03012": room_id,
                "recommended_mastery": base_level,
            }
            npc["room"] = private_id
            moved.append((npc_id, room_id, private_id))
            created.append(private_id)

            # Jeśli przenoszony NPC był sprzedawcą, jego prywatny pokój
            # odziedziczy ofertę sklepu. Nie duplikujemy sklepu dla NPC,
            # którzy nie są sprzedawcami.
            if npc.get("shopkeeper") and room_id in SHOPS:
                SHOPS[private_id] = list(SHOPS.get(room_id, ()))
                SHOP_SELLERS[private_id] = npc_id

        base["npc_room_keeper_v03012"] = keeper

    return {"created": len(created), "moved": len(moved), "rooms": tuple(created), "moves": tuple(moved)}

NPC_PRIVATE_ROOMS_AUDIT_V03012 = split_static_npcs_into_private_rooms_v03012()

# ============================================================
# v0.28.1 - UNIVERSAL WORLD TOPOLOGY GENERATOR
# Wszystkie dotąd statyczne strefy tracą ręcznie wpisaną topologię poziomą.
# Układ jest deterministycznie generowany z seedu; zachowane są jedynie
# semantyczne bramy między strefami i pionowe kotwice. Regiony v0.28
# oraz runtime/infinite dungeons zachowują własne generatory.
# ============================================================

# ============================================================
# v0.30.13 - FULL WORLD TOPOLOGY AUDIT + SEMANTIC BACKBONE
# Universal World Topology nadal proceduralnie układa rozszerzenia/fillery,
# ale nie wolno mu niszczyć ręcznie zaprojektowanych relacji między
# semantycznymi lokacjami fabularnymi, boss-roomami, próbami i hubami.
# ============================================================
_V03013_HORIZONTAL = ("north", "east", "south", "west", "northeast", "southeast", "southwest", "northwest")
_V03013_OPPOSITE = {
    "north":"south", "south":"north", "east":"west", "west":"east",
    "northeast":"southwest", "southwest":"northeast",
    "northwest":"southeast", "southeast":"northwest",
}
_V03013_FILLER_PREFIXES = ("v0930_", "v0100_", "npc_room_v03012_")
_V03013_ORDERED_TRIAL_ZONES = {"Stalowa Próba", "Mityczna Próba", "Astralna Próba", "Wieczna Próba"}

def _topology_semantic_room_v03013(room_id, room):
    rid = str(room_id)
    if room.get("procedural_dynamic"):
        return False
    return not rid.startswith(_V03013_FILLER_PREFIXES)

def _snapshot_semantic_backbone_v03013(rooms):
    result = {}
    seen = set()
    for rid in sorted(rooms):
        room = rooms[rid]
        if not _topology_semantic_room_v03013(rid, room):
            continue
        zone = str(room.get("zone") or "Bez strefy")
        exits = room.get("exits", {}) or {}
        for direction in _V03013_HORIZONTAL:
            target = exits.get(direction)
            if target not in rooms:
                continue
            target_room = rooms[target]
            if str(target_room.get("zone") or "Bez strefy") != zone:
                continue
            if not _topology_semantic_room_v03013(target, target_room):
                continue
            pair = tuple(sorted((rid, str(target))))
            if pair in seen:
                continue
            seen.add(pair)
            # Prefer the authored direction when possible, but adjacency itself
            # is the invariant. The generator may rotate an edge if a gateway,
            # portal or vertical anchor already occupies that compass slot.
            preferred = direction if pair[0] == rid else _V03013_OPPOSITE[direction]
            result.setdefault(zone, []).append((pair[0], pair[1], preferred))
    for zone in result:
        result[zone].sort()
    return result

SEMANTIC_BACKBONE_V03013 = _snapshot_semantic_backbone_v03013(ROOMS)
SEMANTIC_BACKBONE_PAIR_COUNT_V03013 = sum(len(v) for v in SEMANTIC_BACKBONE_V03013.values())

def _generate_zone_semantic_v03013(rooms, zone, ids):
    """Generator strefy zachowujący ręcznie zaprojektowany semantic backbone."""
    mod = world_topology_generator_v0281
    ids = list(ids)
    if len(ids) <= 1:
        for rid in ids:
            rooms[rid]["topology_generated_v0281"] = True
            rooms[rid]["topology_generated_v030"] = True
            rooms[rid]["topology_semantic_backbone_v03013"] = True
            rooms[rid]["world_role"] = mod._room_role(rid, rooms[rid])
        return {"rooms":len(ids), "links":0, "loops":0, "semantic_backbone_links":0, "root":ids[0] if ids else None}

    seed = f"{mod.WORLD_TOPOLOGY_SEED}:{zone}"
    # Zachowujemy tylko pion, lazy/runtime i granice stref. Poziome krawędzie
    # wewnętrzne odbudujemy: najpierw semantic backbone, potem filler.
    for rid in ids:
        old = dict(rooms[rid].get("exits", {})); new = {}
        for d, target in old.items():
            if d in ("up", "down"):
                new[d] = target
            elif target not in rooms:
                new[d] = target
            elif str(rooms[target].get("zone") or "Bez strefy") != zone:
                new[d] = target
        rooms[rid]["exits"] = new

    # Normalize vertical semantic links exactly as the v0.30 generator does.
    for rid in sorted(ids):
        for d, target in list(rooms[rid].get("exits", {}).items()):
            if d not in ("up", "down") or target not in rooms:
                continue
            if str(rooms[target].get("zone") or "Bez strefy") != zone:
                continue
            rev = mod.OPPOSITE[d]
            rooms[target].setdefault("exits", {})
            back = rooms[target]["exits"].get(rev)
            if back == rid:
                continue
            if back is None:
                rooms[target]["exits"][rev] = rid
            else:
                del rooms[rid]["exits"][d]

    # Rebuild every authored semantic adjacency before procedural filler links.
    backbone_links = 0
    zone_ids = set(ids)
    for a, b, preferred in SEMANTIC_BACKBONE_V03013.get(zone, ()): 
        if a not in zone_ids or b not in zone_ids:
            continue
        if b in rooms[a].get("exits", {}).values() or a in rooms[b].get("exits", {}).values():
            backbone_links += 1
            continue
        choices = [preferred] + [d for d in mod.GENERATED_DIRS if d != preferred]
        # Stable ordering after the authored direction keeps the result deterministic.
        tail = choices[1:]
        tail.sort(key=lambda d: mod._unit(f"{seed}:backbone:{a}:{b}:{d}"), reverse=True)
        choices = choices[:1] + tail
        connected = False
        for da in choices:
            db = mod.OPPOSITE[da]
            if mod._free(rooms[a], da) and mod._free(rooms[b], db):
                if mod._connect(rooms, a, da, b, db):
                    connected = True
                    backbone_links += 1
                    break
        if not connected:
            raise RuntimeError(f"semantic backbone has no free direction in zone {zone!r}: {a}<->{b}")

    root = mod._choose_root(zone, ids, rooms)
    comps = mod._components(rooms, ids, zone)
    comps.sort(key=lambda c: (0 if root in c else 1, mod._unit(f"{seed}:component:{'|'.join(c)}")))
    connected = list(comps[0])
    links = 0
    for comp in comps[1:]:
        cand = mod._candidate_links(rooms, connected, comp, seed)
        if not cand:
            raise RuntimeError(f"Topology generator has no free slots in zone {zone!r} for component {comp[:3]}")
        _, a, da, b, db = cand[0]
        if not mod._connect(rooms, a, da, b, db):
            raise RuntimeError(f"Topology generator failed to connect {a} and {b}")
        links += 1
        connected.extend(comp)

    # Ordered five-round trials must stay a chain. A generated loop can let the
    # player skip rounds, so those zones deliberately get no procedural shortcut.
    loop_target = 0 if zone in _V03013_ORDERED_TRIAL_ZONES else (max(1, len(ids)//6) if len(ids) >= 5 else 0)
    loops = 0
    pair_candidates = []
    ordered = sorted(ids)
    for i, a in enumerate(ordered):
        for b in ordered[i+1:]:
            if b in rooms[a].get("exits", {}).values():
                continue
            for da in mod.GENERATED_DIRS:
                db = mod.OPPOSITE[da]
                if mod._free(rooms[a], da) and mod._free(rooms[b], db):
                    compat = mod._role_compat(mod._room_role(a, rooms[a]), mod._room_role(b, rooms[b]))
                    pair_candidates.append((compat*10.0 + mod._unit(f"{seed}:loop:{a}:{da}:{b}"), a, da, b, db))
    pair_candidates.sort(reverse=True)
    for _, a, da, b, db in pair_candidates:
        if loops >= loop_target:
            break
        if mod._connect(rooms, a, da, b, db):
            loops += 1

    depth = {root:0}; q = __import__('collections').deque([root])
    while q:
        cur = q.popleft()
        for nxt in mod._internal_neighbors(rooms, cur, zone):
            if nxt not in depth:
                depth[nxt] = depth[cur] + 1; q.append(nxt)
    if len(depth) != len(ids):
        missing = sorted(set(ids)-set(depth))[:10]
        raise RuntimeError(f"Generated zone {zone!r} disconnected: {missing}")
    for rid in ids:
        rooms[rid]["topology_generated_v0281"] = True
        rooms[rid]["topology_generated_v030"] = True
        rooms[rid]["topology_semantic_backbone_v03013"] = True
        rooms[rid]["world_role"] = mod._room_role(rid, rooms[rid])
        rooms[rid]["topology_zone_depth"] = depth[rid]
        rooms[rid]["topology_seed"] = seed
    return {
        "rooms":len(ids), "links":links, "loops":loops,
        "semantic_backbone_links":backbone_links,
        "root":root, "max_depth":max(depth.values(), default=0),
    }

world_topology_generator_v0281._generate_zone = _generate_zone_semantic_v03013

WORLD_TOPOLOGY_AUDIT = world_topology_generator_v0281.apply_world_topology(ROOMS)
if WORLD_TOPOLOGY_AUDIT.get("error_count"):
    raise RuntimeError("World Topology validation failed: " + "; ".join(WORLD_TOPOLOGY_AUDIT.get("errors", [])[:20]))


# ============================================================
# v0.30.24 - HYBRID QUEST CURRENCY REWARDS
# ============================================================
# Ważne, ręcznie projektowane zadania mają od tej wersji chronioną kwotę
# wspólnej waluty. Wartości zostały dobrane tak, aby żaden z tych questów
# nie dostał nerfa względem v0.30.23, a wcześniejsze ręczne premie (np.
# Odłamki dla kowala, próby profesji i późne Próby Broni Duszy) odzyskały
# swoje znaczenie. Pozostałe questy nadal skaluje Generator Core.
V03024_MANUAL_QUEST_REWARDS_COINS = {
    'neris_fish_1': 1_757,
    'sol_starter_blacksmith_delivery': 1_220,
    'sol_starter_inn_delivery': 1_243,
    'sol_starter_guard_delivery': 1_170,
    'sol_starter_herbalist_delivery': 1_147,
    'sol_starter_class_teacher': 1_500,
    'temple_rats': 1_885,
    'goblin_problem': 2_243,
    'shadow_wolves': 1_636,
    'bandit_patrol': 1_829,
    'soul_shards': 7_500,
    'fisher_30_fish': 2_500,
    'herbalist_30_herbs': 2_500,
    'lumberjack_30_wood': 2_500,
    'miner_30_ore': 2_500,
    'mountain_trail_patrol': 5_000,
    'stolen_mountain_ores': 6_000,
    'troll_shaman_hunt': 12_000,
    'mountain_troll_hunt': 15_000,
    'wild_frontier_hunt': 20_000,
    'high_mountain_patrol': 30_000,
    'deep_troll_clearance': 50_000,
    'troll_king_hunt': 75_000,
    'swamp_purge': 100_000,
    'desert_patrol': 150_000,
    'soul_tier_02_trial': 2_040,
    'soul_tier_03_trial': 2_662,
    'soul_tier_2_trial': 3_786,
    'soul_tier_05_trial': 4_942,
    'soul_tier_06_trial': 6_256,
    'soul_tier_3_trial': 15_000,
    'soul_tier_08_trial': 30_000,
    'soul_tier_09_trial': 50_000,
    'soul_tier_10_trial': 80_000,
    'soul_tier_11_trial': 150_000,
    'soul_tier_12_trial': 300_000,
    'soul_tier_4_trial': 600_000,
    'soul_tier_14_trial': 1_200_000,
    'soul_tier_15_trial': 2_500_000,
    'soul_tier_16_trial': 5_000_000,
    'soul_tier_17_trial': 10_000_000,
    'soul_tier_18_trial': 20_000_000,
    'soul_tier_5_trial': 75_000_000,
    'soul_tier_20_trial': 500_000_000,
    'soul_tier_21_trial': 512_499_999,
    'soul_tier_22_trial': 525_000_000,
    'soul_tier_23_trial': 537_500_000,
    'soul_tier_24_trial': 550_000_000,
    'soul_tier_25_trial': 562_500_000,
    'soul_tier_26_trial': 575_000_000,
    'soul_tier_27_trial': 587_500_000,
    'soul_tier_28_trial': 600_000_000,
    'soul_tier_29_trial': 612_500_000,
    'soul_tier_30_trial': 625_000_000,
    'soul_tier_31_trial': 637_500_000,
    'soul_tier_32_trial': 650_000_000,
    'soul_tier_33_trial': 662_500_000,
    'soul_tier_34_trial': 675_000_000,
    'soul_tier_35_trial': 687_500_000,
    'soul_tier_36_trial': 700_000_000,
    'soul_tier_37_trial': 712_500_000,
    'soul_tier_38_trial': 725_000_000,
    'soul_tier_39_trial': 737_500_000,
    'soul_tier_40_trial': 750_000_000,
}

def apply_manual_quest_currency_rewards_v03024():
    missing = []
    for quest_id, coins in V03024_MANUAL_QUEST_REWARDS_COINS.items():
        quest = QUESTS.get(quest_id)
        if quest is None:
            missing.append(quest_id)
            continue
        quest["manual_currency_reward_coins"] = max(0, int(coins))
        quest["currency_reward_mode"] = "manual"
    return {"marked": len(V03024_MANUAL_QUEST_REWARDS_COINS) - len(missing), "missing": missing}

V03024_MANUAL_QUEST_REWARD_MARKING = apply_manual_quest_currency_rewards_v03024()

# ============================================================
# v0.27.0 - FULL GENERATOR CORE - FINAL REGISTRY PASS
# Ten przebieg jest wykonywany dopiero po zbudowaniu WSZYSTKICH statycznych
# i proceduralnie pre-generowanych rejestrów treści.
# ============================================================
GENERATOR_CORE_AUDIT = generator_core_v027.apply_generator_core(globals())

# v0.31.3: Moogle Board jest specjalnym rasowym Boardem Cyborga.
# Generator Core nie może nadpisywać jego skalowania z Biegłością Meca.
if "moogle_board" in ITEMS:
    ITEMS["moogle_board"].update({
        "defense": 0,
        "price": 1000,
        "required_mastery": 1,
        "required_character_level": 1,
        "generator_level": 1,
        "stats": {},
        "cyborg_board_scaling": "mec_mastery",
    })

# v0.30.30: wszystkie bojowe skille typu boost mają jeden, czytelny czas działania.
# Ta reguła jest nakładana PO Generator Core, aby generator nie skracał buffów.
def normalize_global_skill_buff_duration_v03030():
    changed = 0
    for _class_name, _skills in CLASS_SKILLS.items():
        for _skill in _skills:
            if str(_skill.get("kind") or "").lower() != "boost":
                continue
            if int(_skill.get("duration", 0) or 0) != GLOBAL_SKILL_BUFF_DURATION_SECONDS:
                changed += 1
            _skill["duration"] = GLOBAL_SKILL_BUFF_DURATION_SECONDS
            _desc = str(_skill.get("desc") or "").strip()
            if re.search(r"\bPrzez \d+ sekund", _desc, flags=re.IGNORECASE):
                _desc = re.sub(
                    r"\bPrzez \d+ sekund",
                    f"Przez {GLOBAL_SKILL_BUFF_DURATION_SECONDS} sekund",
                    _desc,
                    flags=re.IGNORECASE,
                )
            elif re.search(r"\b\d+ sekund", _desc, flags=re.IGNORECASE):
                _desc = re.sub(
                    r"\b\d+ sekund",
                    f"{GLOBAL_SKILL_BUFF_DURATION_SECONDS} sekund",
                    _desc,
                    count=1,
                    flags=re.IGNORECASE,
                )
            elif _desc:
                _desc += f" Działa {GLOBAL_SKILL_BUFF_DURATION_SECONDS} sekund."
            else:
                _desc = f"Czasowy buff. Działa {GLOBAL_SKILL_BUFF_DURATION_SECONDS} sekund."
            _skill["desc"] = _desc
    return changed

V03030_BUFF_DURATIONS_NORMALIZED = normalize_global_skill_buff_duration_v03030()

# v0.30.16: jednoznaczne skalowanie ofensywnych umiejętności po finalnym
# przejściu Generator Core. Dane skilla i HELP mają odpowiadać temu, co liczy walka.
def _apply_v03015_offensive_stat_scaling():
    changed = 0
    for class_name, skills in CLASS_SKILLS.items():
        expected = "intelligence" if class_type_for_name(class_name) == "magic" else "strength"
        for skill in skills:
            if skill.get("kind") not in ("damage", "aoe_damage", "execute", "drain"):
                continue
            if skill.get("scale") != expected:
                skill["legacy_scale_v03014"] = skill.get("scale")
                skill["scale"] = expected
                changed += 1
    return changed

V03015_SKILL_SCALES_NORMALIZED = _apply_v03015_offensive_stat_scaling()
if GENERATOR_CORE_AUDIT.get("error_count"):
    raise RuntimeError("Generator Core validation failed: " + "; ".join(GENERATOR_CORE_AUDIT.get("errors", [])[:20]))


# ============================================================
# v0.30.16 - CLASS EQ POST-GENERATOR CONSISTENCY FIX
# Generator Core owns generated numeric power, but class mastery gates are
# authored progression semantics. After generation, split the generated
# single-stat budget across the two requested archetype stats and refresh
# descriptions so displayed values equal runtime values.
# ============================================================
def finalize_class_equipment_v03015():
    errors = []
    touched = 0

    expected_mastery = {}
    expected_class = {}
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for mastery, item_ids in tiers.items():
            for item_id in item_ids:
                expected_mastery[item_id] = int(mastery)
                expected_class[item_id] = class_name
    for class_name, tiers in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER.items():
        for mastery, item_ids in tiers.items():
            for item_id in item_ids:
                expected_mastery[item_id] = int(mastery)
                expected_class[item_id] = class_name
    for class_name, tiers in LEGENDARY_CLASS_RELIC_BY_CLASS_TIER.items():
        for mastery, item_id in tiers.items():
            expected_mastery[item_id] = int(mastery)
            expected_class[item_id] = class_name

    labels = {
        "strength": "Siła", "constitution": "Kondycja",
        "intelligence": "Inteligencja", "willpower": "Siła Woli",
    }
    for item_id, mastery in expected_mastery.items():
        item = ITEMS.get(item_id)
        if not item:
            errors.append(f"brak class EQ {item_id}")
            continue
        class_name = expected_class[item_id]
        primary_stat, secondary_stat = class_equipment_base_stat_pair(class_name)
        # Generator Core określa łączny budżet; v0.30.16 rozdziela go według
        # klasy i slotu zamiast identycznego 50/50 dla wszystkich.
        generated_budget = max(2, int(item.get("affix_amount", 1) or 1))
        primary_stat, primary_amount, secondary_stat, secondary_amount = (
            class_equipment_split_stat_budget(
                class_name, generated_budget, item.get("slot")
            )
        )
        item["affix"] = primary_stat
        item["affix_amount"] = primary_amount
        item["stats"] = {secondary_stat: secondary_amount}
        item["class_base_stat_pair"] = (primary_stat, secondary_stat)
        item["required_class"] = class_name
        item["required_mastery"] = mastery
        item["class_equipment_profile"] = class_equipment_profile(class_name).get("identity")
        item["properties"] = class_equipment_profile_properties(
            class_name, mastery, item.get("slot")
        )

        stat_text = (
            f"{labels[primary_stat]} +{primary_amount}, "
            f"{labels[secondary_stat]} +{secondary_amount}"
        )
        profile_text = str(item.get("class_equipment_profile") or "")
        defense = int(item.get("defense", 0) or 0)
        set_name = item.get("class_set_name") or "Klasowy"
        if item.get("legendary_class_relic"):
            item["desc"] = (
                f"Legendarny relikt klasy {class_name} z bossa kamienia milowego. "
                f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                f"Obrona +{defense}. Podstawowe statystyki EQ: {stat_text}. Profil klasy: {profile_text}. "
                f"Właściwości: {item.get('properties', {})}."
            )
        elif item.get("legendary_set_loot"):
            item["desc"] = (
                f"Legendarna część zestawu {set_name} dla klasy {class_name}. "
                f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                f"Obrona +{defense}. Podstawowe statystyki EQ: {stat_text}. Profil klasy: {profile_text}. "
                f"Właściwości: {item.get('properties', {})}."
            )
        else:
            item["desc"] = (
                f"Wyposażenie klasowe dla {class_name}. Linia: {set_name}. "
                f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                f"Tier: {_class_equipment_tier_label(mastery)}. Obrona +{defense}. "
                f"Podstawowe statystyki EQ: {stat_text}. Profil klasy: {profile_text}. "
                f"Właściwości: {item.get('properties', {})}."
            )
        touched += 1

    # Remove stale seller entries left after moving profession NPCs to private rooms.
    stale_sellers = []
    for room_id in list(SHOP_SELLERS):
        if room_id not in SHOPS:
            stale_sellers.append(room_id)
            SHOP_SELLERS.pop(room_id, None)

    return {
        "version": "0.30.16",
        "touched": touched,
        "stale_shop_sellers_removed": tuple(sorted(stale_sellers)),
        "error_count": len(errors),
        "errors": errors,
    }

CLASS_EQ_AUDIT_V03015 = finalize_class_equipment_v03015()
if CLASS_EQ_AUDIT_V03015["error_count"]:
    raise RuntimeError("Class EQ v0.30.16 audit failed: " + "; ".join(CLASS_EQ_AUDIT_V03015["errors"][:20]))


def class_equipment_identity_audit_v03016():
    errors = []
    signatures = {}
    # Biegłość 400 daje wystarczający budżet liczb, by sprawdzić realny rozkład.
    for class_name in CLASS_EQUIPMENT_SETS:
        ids = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name, {}).get(400, ())
        sample = None
        for item_id in ids:
            item = ITEMS.get(item_id, {})
            if item.get("slot") == "body":
                sample = item
                break
        if not sample and ids:
            sample = ITEMS.get(ids[0], {})
        if not sample:
            errors.append(f"brak próbki EQ 400 dla {class_name}")
            continue
        signature = (
            sample.get("affix"), int(sample.get("affix_amount", 0) or 0),
            tuple(sorted((stat, int(value or 0)) for stat, value in (sample.get("stats") or {}).items())),
            tuple(sorted((prop, round(float(value or 0), 2)) for prop, value in (sample.get("properties") or {}).items())),
        )
        if signature in signatures:
            errors.append(f"identyczny profil EQ: {class_name} == {signatures[signature]}")
        signatures[signature] = class_name

    # Sloty jednej klasy również nie powinny wszystkie mieć identycznego rozkładu.
    for class_name in CLASS_EQUIPMENT_SETS:
        ids = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name, {}).get(400, ())
        split_signatures = set()
        for item_id in ids:
            item = ITEMS.get(item_id, {})
            split_signatures.add((
                int(item.get("affix_amount", 0) or 0),
                tuple(sorted(int(v or 0) for v in (item.get("stats") or {}).values())),
            ))
        if len(split_signatures) < 2:
            errors.append(f"brak różnic slotów EQ dla {class_name}")

    return {
        "version": "0.30.16",
        "class_count": len(signatures),
        "unique_profile_signatures": len(signatures),
        "error_count": len(errors),
        "errors": errors,
    }

CLASS_EQ_IDENTITY_AUDIT_V03016 = class_equipment_identity_audit_v03016()
if CLASS_EQ_IDENTITY_AUDIT_V03016["error_count"]:
    raise RuntimeError(
        "Class EQ Identity Audit v0.30.16 failed: " +
        "; ".join(CLASS_EQ_IDENTITY_AUDIT_V03016["errors"][:20])
    )

# ============================================================
# v0.30.0 - SEMANTIC WORLD LOGIC VALIDATOR
# Proceduralna topologia musi pozostać geograficznie logiczna i w pełni
# nawigowalna. Generator nie może łączyć miasta bezpośrednio z endgame ani
# używać przypadkowych pionowych ulic.
# ============================================================
WORLD_LOGIC_AUDIT = world_logic_validator_v030.validate_world_logic(ROOMS)
if WORLD_LOGIC_AUDIT.get("error_count"):
    raise RuntimeError("World Logic validation failed: " + "; ".join(WORLD_LOGIC_AUDIT.get("errors", [])[:20]))


def audit_entire_world_topology_v03013(rooms):
    """Deep static topology audit including authored semantics, not just reachability."""
    from collections import defaultdict, deque
    errors = []
    warnings = []
    opposite = dict(_V03013_OPPOSITE, up="down", down="up")

    # 1. Static edges must be reciprocal. Lazy/runtime exits are counted separately.
    lazy = []
    static_edges = 0
    for rid, room in rooms.items():
        for direction, target in (room.get("exits", {}) or {}).items():
            if target not in rooms:
                lazy.append((rid, direction, target))
                continue
            static_edges += 1
            if direction in opposite:
                rev = opposite[direction]
                if rooms[target].get("exits", {}).get(rev) != rid:
                    errors.append(f"one-way static edge: {rid}.{direction}->{target}")

    # 2. Every static room reachable from square and able to return to square.
    def reachable(start, reverse=False):
        if start not in rooms:
            return set()
        graph = defaultdict(list)
        if reverse:
            for a, room in rooms.items():
                for b in (room.get("exits", {}) or {}).values():
                    if b in rooms:
                        graph[b].append(a)
        seen = {start}; q = deque([start])
        while q:
            cur = q.popleft()
            nxts = graph.get(cur, ()) if reverse else [x for x in rooms[cur].get("exits", {}).values() if x in rooms]
            for nxt in nxts:
                if nxt not in seen:
                    seen.add(nxt); q.append(nxt)
        return seen
    fwd = reachable("square")
    back = reachable("square", reverse=True)
    if len(fwd) != len(rooms):
        errors.append(f"unreachable from square: {len(rooms)-len(fwd)}")
    if len(back) != len(rooms):
        errors.append(f"cannot return to square: {len(rooms)-len(back)}")

    # 3. Every generated static zone must itself be connected internally.
    zones = defaultdict(list)
    for rid, room in rooms.items():
        if room.get("procedural_dynamic"):
            continue
        zones[str(room.get("zone") or "Bez strefy")].append(rid)
    disconnected_zones = []
    for zone, ids in zones.items():
        if len(ids) <= 1:
            continue
        allowed = set(ids); start = ids[0]; seen = {start}; q = deque([start])
        while q:
            cur = q.popleft()
            for target in rooms[cur].get("exits", {}).values():
                if target in allowed and target not in seen:
                    seen.add(target); q.append(target)
        if seen != allowed:
            disconnected_zones.append((zone, len(allowed-seen)))
    if disconnected_zones:
        errors.append("internally disconnected zones: " + repr(disconnected_zones[:10]))

    # 4. Every authored semantic adjacency captured before generation must survive.
    actual_pairs = set()
    for rid, room in rooms.items():
        for target in (room.get("exits", {}) or {}).values():
            if target in rooms and rooms[target].get("zone") == room.get("zone"):
                actual_pairs.add(tuple(sorted((rid, target))))
    missing_backbone = []
    for zone, pairs in SEMANTIC_BACKBONE_V03013.items():
        for a, b, _ in pairs:
            if tuple(sorted((a, b))) not in actual_pairs:
                missing_backbone.append((zone, a, b))
    if missing_backbone:
        errors.append(f"missing semantic backbone links: {len(missing_backbone)} sample={missing_backbone[:10]}")

    # 5. Ordered five-round trials must be exact chains without shortcuts.
    trial_errors = []
    trial_prefix = {
        "Stalowa Próba":"v020_gauntlet_stalowa_",
        "Mityczna Próba":"v020_gauntlet_mityczna_",
        "Astralna Próba":"v020_gauntlet_astralna_",
        "Wieczna Próba":"v020_gauntlet_wieczna_",
    }
    for zone, prefix in trial_prefix.items():
        ids = [f"{prefix}{i}" for i in range(1, 6)]
        expected = {tuple(sorted((ids[i], ids[i+1]))) for i in range(4)}
        got = set()
        for a in ids:
            if a not in rooms:
                trial_errors.append(f"{zone}: missing {a}"); continue
            for b in rooms[a].get("exits", {}).values():
                if b in ids:
                    got.add(tuple(sorted((a, b))))
        if got != expected:
            trial_errors.append(f"{zone}: expected chain {sorted(expected)}, got {sorted(got)}")
    if trial_errors:
        errors.extend(trial_errors)

    # 6. Explicit regression for the broken Stary Cmentarz story chain.
    cemetery_pairs = {
        tuple(sorted(("cemetery_ossuary_path", "cemetery_fallen_chapel"))),
        tuple(sorted(("cemetery_fallen_chapel", "cemetery_bell_tower"))),
        tuple(sorted(("cemetery_bone_field", "cemetery_bell_tower"))),
        tuple(sorted(("cemetery_bell_tower", "cemetery_keeper_tomb"))),
    }
    missing_cemetery = sorted(cemetery_pairs - actual_pairs)
    if missing_cemetery:
        errors.append(f"Stary Cmentarz semantic chain broken: {missing_cemetery}")

    return {
        "version":"0.30.13",
        "room_count":len(rooms),
        "static_directed_edges":static_edges,
        "lazy_runtime_exits":len(lazy),
        "zone_count":len(zones),
        "semantic_backbone_pairs":SEMANTIC_BACKBONE_PAIR_COUNT_V03013,
        "missing_semantic_backbone_pairs":len(missing_backbone),
        "disconnected_zones":len(disconnected_zones),
        "reachable_from_square":len(fwd),
        "returnable_to_square":len(back),
        "error_count":len(errors),
        "warning_count":len(warnings),
        "errors":errors,
        "warnings":warnings,
    }

FULL_WORLD_TOPOLOGY_AUDIT_V03013 = audit_entire_world_topology_v03013(ROOMS)
if FULL_WORLD_TOPOLOGY_AUDIT_V03013.get("error_count"):
    raise RuntimeError("Full World Topology Audit v0.30.13 failed: " + "; ".join(FULL_WORLD_TOPOLOGY_AUDIT_V03013.get("errors", [])[:20]))


# HELP i atlasy nie przechowują osobnego balansu: czytają wartości wygenerowane.
HELP_TOPICS["generator"] = [
    "Generator Core pozostaje jedynym źródłem aktywnego balansu Soulbound; v0.30.0 dodaje semantyczny generator geografii i World Logic Validator.",
    "Generowane są: Level postaci 1-400, nielimitowane statystyki, moby i bossowie, HP, obrażenia, EXP, monety, drop-rate, przedmioty, wymagania, questy, skille i spelle, Soul 1-400, profesje, narzędzia, receptury, ceny oraz atlasy.",
    "Nowa zawartość nie wymaga ręcznego liczenia wartości. Nadaj jej nazwę, typ i powiązania ze światem; liczby wylicza Generator Core.",
    "Balance Validator sprawdza zakresy osi 1-400, dodatnie wartości oraz monotoniczność także nielimitowanej krzywej statystyk.",
]
HELP_TOPICS["level"] = [
    "Level postaci ma zakres 1-400. EXP postaci pochodzi z walki, questów i aktywności profesyjnych.",
    "Próg EXP i nagrody wylicza Generator Core; nie są wpisywane osobno dla poziomów ani przeciwników.",
    "Level postaci zwiększa bazowe HP, Manę i moc. Biegłość, Soul, Skill Level i profesje mają własne osie 1-400, a statystyki rozwijają się bez twardego limitu.",
]
HELP_TOPICS["klasy"] = [
    "Soulbound ma 14 klas. Level postaci, Biegłość klasy i Skill Level mają zakres 1-400 i są liczone przez Generator Core.",
    "Klasa główna jest wybierana przy tworzeniu postaci. Dodatkowe aktywne klasy obsługuje multiclass / multiklasa.",
    "skills pokazuje skille aktywnych klas, a help <nazwa skilla> podaje aktualne wygenerowane wymagania i parametry.",
]
HELP_TOPIC_ALIASES.update({"level postaci":"level","poziom postaci":"level","generator core":"generator"})

# Oczyść stare komunikaty HELP, które twierdziły, że postać nie ma levelu.
for _topic, _lines in list(HELP_TOPICS.items()):
    if not isinstance(_lines, list):
        continue
    _clean=[]
    for _line in _lines:
        _text=str(_line)
        _low=normalize_lookup_text(_text) if 'normalize_lookup_text' in globals() else _text.lower()
        if ("nie ma levelu postaci" in _low or "brak levelu postaci" in _low or "postac nie ma levelu" in _low):
            _text="Level postaci 1-400 i główne osie progresji są wyliczane przez Generator Core v0.30.0; statystyki są nielimitowane."
        _clean.append(_text)
    HELP_TOPICS[_topic]=_clean


# ============================================================
# v0.33.6 - RUNTIME NUMERIC DESCRIPTION SYNCHRONIZER
# Generator Core is authoritative for numeric balance. Player-facing item
# descriptions must therefore mirror the generated values instead of old
# authored numbers retained in legacy descriptions.
# ============================================================

def _fmt_runtime_number_v0336(value):
    try:
        value=float(value)
    except Exception:
        return str(value)
    if abs(value-round(value)) < 1e-9:
        return str(int(round(value)))
    return (f"{value:.3f}").rstrip("0").rstrip(".")


def sync_item_numeric_description_v0336(item):
    desc=str(item.get("desc") or "")
    if not desc:
        return desc

    # Direct defense.
    if "defense" in item:
        desc=re.sub(r"(?i)(Obrona\s*\+)\s*-?\d+(?:[.,]\d+)?", lambda m: m.group(1)+_fmt_runtime_number_v0336(item.get("defense",0)), desc)

    stats=dict(item.get("stats") or {})
    affix=str(item.get("affix") or "")
    affix_amount=item.get("affix_amount")
    stat_labels={
        "strength": r"Siła",
        "dexterity": r"Zręczność",
        "constitution": r"Kondycja",
        "intelligence": r"Inteligencja",
        "willpower": r"Siła Woli",
        "charisma": r"Charyzma",
    }
    for key,label in stat_labels.items():
        actual=stats.get(key)
        if actual is None and affix==key:
            actual=affix_amount
        if actual is None:
            continue
        pat=rf"(?i)({label}\s*\+)\s*-?\d+(?:[.,]\d+)?"
        desc=re.sub(pat, lambda m,v=actual: m.group(1)+_fmt_runtime_number_v0336(v), desc)

    # Generic legacy affix wording.
    if affix_amount is not None:
        desc=re.sub(r"(?i)(Bonus statystyki\s*\+)\s*-?\d+(?:[.,]\d+)?", lambda m: m.group(1)+_fmt_runtime_number_v0336(affix_amount), desc)
        if affix=="hp":
            desc=re.sub(r"(?i)(?<!maksymalne )(?<!maksymalne)(HP\s*\+)\s*-?\d+(?:[.,]\d+)?", lambda m: m.group(1)+_fmt_runtime_number_v0336(affix_amount), desc)
        if affix=="mana":
            desc=re.sub(r"(?i)(?<!maksymalna )(?<!maksymalna)(Mana\s*\+)\s*-?\d+(?:[.,]\d+)?", lambda m: m.group(1)+_fmt_runtime_number_v0336(affix_amount), desc)

    props=dict(item.get("properties") or {})
    prop_labels={
        "max_hp_pct": r"maksymalne HP",
        "max_mana_pct": r"maksymalna Mana",
        "physical_damage_pct": r"obrażenia fizyczne",
        "magic_damage_pct": r"obrażenia magiczne",
        "physical_defense_pct": r"obrona fizyczna",
        "magic_defense_pct": r"obrona magiczna",
        "dodge_pct": r"unik",
        "all_damage_pct": r"obrażenia",
    }
    for key,label in prop_labels.items():
        if key not in props:
            continue
        actual=props[key]
        pat=rf"(?i)({label}\s*\+)\s*-?\d+(?:[.,]\d+)?(?=%)"
        desc=re.sub(pat, lambda m,v=actual: m.group(1)+_fmt_runtime_number_v0336(v), desc)

    item["desc"]=desc
    return desc


ITEM_DESCRIPTION_SYNC_V0336={"checked":0,"changed":0}
for _iid_v0336,_item_v0336 in ITEMS.items():
    _before_v0336=str(_item_v0336.get("desc") or "")
    sync_item_numeric_description_v0336(_item_v0336)
    ITEM_DESCRIPTION_SYNC_V0336["checked"]+=1
    if str(_item_v0336.get("desc") or "") != _before_v0336:
        ITEM_DESCRIPTION_SYNC_V0336["changed"]+=1
