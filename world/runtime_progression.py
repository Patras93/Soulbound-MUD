from core.legacy_function_binding_v410 import bind_legacy_function_v410 as _sb420_topbind
import world.v420_runtime_regions as _sb420_topsrc01
import world.v420_runtime_world_audits as _sb420_topsrc02
import world.v420_runtime_class_equipment as _sb420_topsrc03

from data import catalog_mutations as _catalog_mut
from systems.equipment_crafting import mec_hybrid_extra_stats
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
    from config.balance import scale_player_requirement_v1407, v4210_required_xp
    rank=max(0,int(rank or 0))
    if rank>=V021_ASCENSION_MAX_RANK: return 0
    level=rank+1
    return v4210_required_xp(scale_player_requirement_v1407(v0190_log_curve(level,V021_ASCENSION_REQ),level), "ascension", level)

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
    _catalog_mut.catalog_assign({"name":_name,"type":"material","price":None,"rarity":"mythic","rarity_name":"Mityczny","desc":_desc}, 'ITEMS', ITEMS, (_iid,))
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
        _catalog_mut.catalog_assign({"name":f"{_slot_name} — {_label}","type":"armor","slot":_slot,"defense":_def,"price":None,
            "rarity":"mythic","rarity_name":"Mityczny","sockets":4,"affix":_affix,"affix_amount":_amount,
            "required_mastery":400,"v021_mythic_set":_key,
            "desc":f"Część 14-elementowego zestawu {_label}. Progi bonusów pozostają 2/4/6/8. Wymaga Biegłości 600. Bez RNG i bez pułapek."}, 'ITEMS', ITEMS, (_iid,))
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
    _catalog_mut.catalog_assign({"name":"Strażnik Endless Gauntlet","max_hp":min(V019_SAFE_INT,max(1,base_hp)),
        "damage":min(V019_SAFE_INT,max(1,base_dmg)),"damage_type":"magic" if band%2 else "physical",
        "class_xp_reward":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_CLASS_KILL_BOSS)*reward_mult)),
        "soul_reward":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_SOUL_KILL_BOSS)*reward_mult)),
        "stat_reward":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_STAT_KILL_BOSS)*reward_mult)),
        "silver":min(V019_SAFE_INT,int(v0190_log_curve(400,V019_COIN_KILL_BOSS)*reward_mult)),"gold":0,"mithril":0,
        "drops":{"v021_eternal_sigil":1.0,"v021_ascension_crystal":0.75,"v021_world_tier_crest":0.45,"v020_mythic_essence":1.0},
        "auto_aggro":False,"stationary_mob":True,"boss_mechanic":"two_hundred_lord","boss_mechanic_text":"Endless Gauntlet; fazy 75/50/25%. PASSIVE WORLD.",
        "v017_boss_phases":True,"v021_endless_gauntlet":True,"v021_endless_band":band,"v019_stage":400,"world_boss":True,"respawn_seconds":6*60*60}, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
    BOSS_COLLECTION_CATALOG[tid]=MOB_TEMPLATES[tid]["name"]
    return tid

def v0210_create_endless_gauntlet_room_definition(room_id):
    round_no=v0210_endless_gauntlet_identity(room_id)
    if round_no is None: return None,()
    if room_id in ROOMS: return room_id,()
    prev=V020_GAUNTLET_LOBBY if round_no==1 else v0210_endless_gauntlet_room_id(round_no-1)
    nxt=v0210_endless_gauntlet_room_id(round_no+1)
    band=v0210_endless_gauntlet_band(round_no)
    _catalog_mut.catalog_assign({"zone":"Endless Gauntlet","name":f"Endless Gauntlet — runda {round_no}",
        "desc":f"Nieskończona próba bossów. Runda {round_no}, pasmo {band}/100. Boss blokuje tylko przejście dalej; nie atakuje pierwszy. Brak pułapek.",
        "exits":{"south":prev,"north":nxt},"recommended_mastery":400,"generated_on_demand":True,
        "v021_endless_gauntlet_round":round_no,"v021_endless_band":band}, 'ROOMS', ROOMS, (room_id,))
    return room_id,((room_id,v0210_endless_gauntlet_template(round_no)),)

HELP_TOPICS["ascension_v021"]=[
    f"wzniesienie / ascension pokazuje progresję klasy po osiągnięciu Biegłości {CLASS_MASTERY_MAX_LEVEL}. Biegłość nie resetuje się.",
    "Każdy dalszy Class XP trafia do Rangi Wzniesienia. Maksymalna ranga techniczna to 1000; wymagania rosną do ekstremalnego endgame.",
]
HELP_TOPICS["worldtier_v021"]=[
    "worldtier / poziomswiata pokazuje lub ustawia osobisty World Tier 1-10. Zmiana jest możliwa tylko poza walką.",
    f"Wyższy Tier zwiększa efektywną wytrzymałość i obrażenia przeciwników oraz nagrody. Tier 2+ wymaga Biegłości {CLASS_MASTERY_MAX_LEVEL}; wyższe Tiery mogą wymagać też Rang Wzniesienia.",
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
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.

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
    _stage=balance_math.stage_from_index(_idx,len(V022_WORLD_PROJECTS))
    _spec["stage"]=_stage
    _spec["min_points"]=balance_math.generated_count(_stage,"world-project-points:"+_pkey,200,5000)
    _requirements={}
    for _cat in _spec.pop("categories"):
        if _cat=="coins":
            _requirements[_cat]=balance_math.system_cost(_stage,"world-project:"+_pkey,20000.0)
        else:
            _requirements[_cat]=balance_math.generated_count(_stage,f"world-project:{_pkey}:{_cat}",2500,100000)
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
        "character_xp": balance_math.axis_gain("character",stage,complexity),
        "class_xp": balance_math.axis_gain("class",stage,complexity),
        "soul_xp": balance_math.axis_gain("soul",stage,complexity),
        "coins": min(CURRENCY_SQLITE_SAFE_TOTAL,balance_math.system_reward(stage,"world-project:"+project_key,complexity*3.0)),
    }

V022_LEGENDARY_KINDS=("kill","boss","worldboss","fish","gather","explore")
V022_LEGENDARY_LABELS={
    "kill":"Wielkie Polowanie","boss":"Łańcuch Bossów","worldboss":"Łowy na World Bossy",
    "fish":"Legendarna Wyprawa Rybacka","gather":"Kontrakt Wielkiego Zbioru","explore":"Ekspedycja Kartograficzna",
}

V027_LEGENDARY_MIN_MASTERY = 1 + int(balance_math.stable_unit("legendary-contract-unlock") * 399)

def v022_legendary_contract_offer(kind, stage):
    stage=max(V027_LEGENDARY_MIN_MASTERY,min(CLASS_MASTERY_MAX_LEVEL,int(stage or V027_LEGENDARY_MIN_MASTERY)))
    base=balance_math.generated_count(stage,"legendary:"+kind,30,300)
    divisors={"kill":1,"boss":12,"worldboss":35,"fish":1,"gather":1,"explore":2}
    needed=max(1,int(round(base/divisors.get(kind,1))))
    complexity=2.5 + (stage/120.0) + balance_math.stable_unit("legendary-complexity:"+kind)*2.0
    return {
        "kind":kind,"label":f"{V022_LEGENDARY_LABELS[kind]}: {needed}","needed":needed,"stage":stage,
        "reward_character_xp":balance_math.axis_gain("character",stage,complexity),
        "reward_class_xp":balance_math.axis_gain("class",stage,complexity),
        "reward_soul_xp":balance_math.axis_gain("soul",stage,complexity),
        "reward_coins":min(CURRENCY_SQLITE_SAFE_TOTAL,balance_math.system_reward(stage,"legendary:"+kind,complexity*2.0)),
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
    "Soulbound ma 14 klas. Level postaci i każda klasa rozwijają się niezależnie; Biegłość każdej klasy ma zakres 1-600.",
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
    "100 srebra = 1 złoto. 1 000 000 złota = 1 mithril. Wewnętrznie to jedno saldo, a nominały są sposobem prezentacji i wpisywania kwot.",
    "Portfel jest wspólny dla postaci na koncie; zmiana postaci nie tworzy osobnej waluty.",
    "Zakupy korzystają z rabatu Charyzmy. Sprzedaż pojedyncza i skup profesyjny dopisują wartość do tego samego salda.",
    "bank obsługuje wpłaty/wypłaty waluty i przedmiotów; wpisz bank bez argumentu, aby usłyszeć składnię.",
]
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.


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
    return seq[int(balance_math.stable_unit(f"{V028_WORLD_SEED}:{key}") * len(seq)) % len(seq)]


def _v028_connect(a, direction, b, reverse):
    _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (a,), "exits", {})[direction] = b
    _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (b,), "exits", {})[reverse] = a


def _v028_region_room_id(index, x, y):
    return f"v028_region_{int(index):02d}_{int(x):02d}_{int(y):02d}"


def _v028_build_regions(*args, **kwargs):
    """Native compatibility entrypoint; rebound to unmodified function."""
    raise RuntimeError("unbound _v028_build_regions")
_v028_build_regions = _sb420_topbind(_sb420_topsrc01._v028_build_regions, globals())


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
            _catalog_mut.catalog_assign({
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
            }, 'ROOMS', ROOMS, (private_id,))
            npc["room"] = private_id
            moved.append((npc_id, room_id, private_id))
            created.append(private_id)

            # Jeśli przenoszony NPC był sprzedawcą, jego prywatny pokój
            # odziedziczy ofertę sklepu. Nie duplikujemy sklepu dla NPC,
            # którzy nie są sprzedawcami.
            if npc.get("shopkeeper") and room_id in SHOPS:
                _catalog_mut.catalog_assign(list(SHOPS.get(room_id, ())), 'SHOPS', SHOPS, (private_id,))
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

# ============================================================
# v0.38.13 - UNDERGROUND ROUTE ISOLATION
# Historycznie kilka niezależnych obszarów miało wspólną etykietę strefy
# "Podziemia". Semantic topology traktowała więc piwnicę Świątyni, Kopalnię
# Głębinową i Kryptę jak jeden region i dodawała między nimi filler-links.
# To zamieniało Piwnicę Świątyni w przypadkowy skrót dla `prowadz`.
#
# Zachowujemy wszystkie stare room_id (ważne dla save'ów), ale rozdzielamy
# semantyczne strefy przed zrobieniem snapshotu backbone i przed generacją
# topologii. Dzięki temu generator może rozbudować każdą część osobno, lecz
# nie wolno mu scalać niezależnych wejść pod ziemią.
_V03813_UNDERGROUND_ZONE_OVERRIDES = {
    "temple_basement": "Piwnica Świątyni",
    "cave_entrance": "Kopalnia Głębinowa",
    "cave_tunnel": "Kopalnia Głębinowa",
    "crystal_chamber": "Kopalnia Głębinowa",
    "miners_guild": "Kopalnia Głębinowa",
    "crypt_entrance": "Krypta",
    "crypt_hall": "Krypta",
    "crypt_depths": "Krypta",
}
for _rid, _zone in _V03813_UNDERGROUND_ZONE_OVERRIDES.items():
    if _rid in ROOMS:
        _catalog_mut.catalog_assign(_zone, 'ROOMS', ROOMS, (_rid, "zone"))

# v0.10.0 utworzył rozszerzenie Podziemi z trwałymi ID v0100_podziemia_*.
# Jego historyczny authored anchor prowadzi przez Gildię Górników, dlatego
# traktujemy te pokoje jako część wejściowych tuneli Kopalni Głębinowej.
# Zmieniamy tylko etykietę strefy, nigdy ID: stare save'y pozostają zgodne.
for _rid, _room in ROOMS.items():
    if str(_rid).startswith("v0100_podziemia_"):
        _room["zone"] = "Kopalnia Głębinowa"

# Zachowaj dotychczasową klasyfikację trudności mimo dokładniejszych nazw stref.
if isinstance(globals().get("EXP_ZONE_AREA_ID"), dict):
    EXP_ZONE_AREA_ID.update({
        "Piwnica Świątyni": "podziemia",
        "Kopalnia Głębinowa": "podziemia",
        "Krypta": "krypta",
    })

SEMANTIC_BACKBONE_V03013 = _snapshot_semantic_backbone_v03013(ROOMS)
SEMANTIC_BACKBONE_PAIR_COUNT_V03013 = sum(len(v) for v in SEMANTIC_BACKBONE_V03013.values())

def _generate_zone_semantic_v03013(*args, **kwargs):
    """Native compatibility entrypoint; rebound to unmodified function."""
    raise RuntimeError("unbound _generate_zone_semantic_v03013")
_generate_zone_semantic_v03013 = _sb420_topbind(_sb420_topsrc01._generate_zone_semantic_v03013, globals())

world_topology_generator_v0281._generate_zone = _generate_zone_semantic_v03013

WORLD_TOPOLOGY_AUDIT = world_topology_generator_v0281.apply_world_topology(ROOMS)
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
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
# v1.28.3: static legacy numeric defaults; no procedural generator writes.
from core.catalog_fallback_v1283 import apply_catalogue_defaults_v1283
CATALOG_DEFAULTS_AUDIT_V1283 = apply_catalogue_defaults_v1283(globals())
from core.catalog_validation import validate_catalog
CATALOG_VALIDATION_AUDIT = validate_catalog(globals())
BALANCE_MATH_VERSION = balance_math.BALANCE_MATH_VERSION

# v0.31.3: Moogle Board jest specjalnym rasowym Boardem Cyborga.
# Generator Core nie może nadpisywać jego skalowania z Biegłością Meca.
if "moogle_board" in ITEMS:
    _catalog_mut.catalog_update_path('ITEMS', ITEMS, ("moogle_board",), {
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

# v0.34.6: zachowujemy autorskie skalowanie każdego skilla. Generator Core
# gwarantuje, że pole scale jest semantyką chronioną i nie powinno być
# nadpisywane po generowaniu. Dzięki temu Łowca/Łotrzyk/Mnich używają
# Zręczności, klasy magiczne Inteligencji, a Mec/Inżynier mogą zachować
# własne gałęzie ranged/magic/melee.
def _apply_v03015_offensive_stat_scaling():
    restored = 0
    for _class_name, skills in CLASS_SKILLS.items():
        for skill in skills:
            if skill.get("kind") not in ("damage", "aoe_damage", "execute", "drain"):
                continue
            # Obsługa save/source z warstwy v0.30.16, jeśli pole zostało już
            # wcześniej oznaczone jako legacy_scale_v03014. W świeżym runtime
            # pole nie występuje i niczego nie zmieniamy.
            legacy = skill.pop("legacy_scale_v03014", None)
            if legacy and skill.get("scale") != legacy:
                skill["scale"] = legacy
                restored += 1
    return restored

V03015_SKILL_SCALES_NORMALIZED = _apply_v03015_offensive_stat_scaling()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# ============================================================
# v0.30.16 - CLASS EQ POST-GENERATOR CONSISTENCY FIX
# Generator Core owns generated numeric power, but class mastery gates are
# authored progression semantics. After generation, split the generated
# single-stat budget across the three required class-EQ stats and refresh
# descriptions so displayed values equal runtime values.
# ============================================================
def finalize_class_equipment_v03015(*args, **kwargs):
    """Native compatibility entrypoint; rebound to unmodified function."""
    raise RuntimeError("unbound finalize_class_equipment_v03015")
finalize_class_equipment_v03015 = _sb420_topbind(_sb420_topsrc03.finalize_class_equipment_v03015, globals())

CLASS_EQ_AUDIT_V03015 = finalize_class_equipment_v03015()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
def class_equipment_identity_audit_v03016(*args, **kwargs):
    """Native compatibility entrypoint; rebound to unmodified function."""
    raise RuntimeError("unbound class_equipment_identity_audit_v03016")
class_equipment_identity_audit_v03016 = _sb420_topbind(_sb420_topsrc02.class_equipment_identity_audit_v03016, globals())

CLASS_EQ_IDENTITY_AUDIT_V03016 = class_equipment_identity_audit_v03016()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# ============================================================
# v0.30.0 - SEMANTIC WORLD LOGIC VALIDATOR
# Proceduralna topologia musi pozostać geograficznie logiczna i w pełni
# nawigowalna. Generator nie może łączyć miasta bezpośrednio z endgame ani
# używać przypadkowych pionowych ulic.
# ============================================================
WORLD_LOGIC_AUDIT = world_logic_validator_v030.validate_world_logic(ROOMS)
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
def audit_entire_world_topology_v03013(*args, **kwargs):
    """Native compatibility entrypoint; rebound to unmodified function."""
    raise RuntimeError("unbound audit_entire_world_topology_v03013")
audit_entire_world_topology_v03013 = _sb420_topbind(_sb420_topsrc02.audit_entire_world_topology_v03013, globals())

def audit_underground_route_isolation_v03813():
    errors = []
    expected_zones = {
        "temple_basement": "Piwnica Świątyni",
        "cave_entrance": "Kopalnia Głębinowa",
        "cave_tunnel": "Kopalnia Głębinowa",
        "crystal_chamber": "Kopalnia Głębinowa",
        "miners_guild": "Kopalnia Głębinowa",
        "crypt_entrance": "Krypta",
        "crypt_hall": "Krypta",
        "crypt_depths": "Krypta",
    }
    for rid, zone in expected_zones.items():
        if rid not in ROOMS:
            errors.append(f"missing room {rid}")
        elif ROOMS[rid].get("zone") != zone:
            errors.append(f"{rid} zone={ROOMS[rid].get('zone')!r}, expected {zone!r}")

    # Piwnica może prowadzić do Świątyni i swojego historycznego rozszerzenia,
    # ale nigdy bezpośrednio do Kopalni/Krypty. Te obszary mają własne wejścia.
    forbidden = {"cave_entrance", "cave_tunnel", "crystal_chamber", "miners_guild",
                 "crypt_entrance", "crypt_hall", "crypt_depths"}
    basement_targets = set((ROOMS.get("temple_basement", {}).get("exits", {}) or {}).values())
    bad = sorted(basement_targets & forbidden)
    if bad:
        errors.append(f"temple basement has forbidden shortcuts: {bad}")

    # Historyczne v0100_podziemia_* należą teraz do tuneli Kopalni i również
    # nie mogą mieć żadnego łącznika z Piwnicą Świątyni.
    expansion_ids = {rid for rid in ROOMS if str(rid).startswith("v0100_podziemia_")}
    for rid in sorted(expansion_ids):
        if ROOMS[rid].get("zone") != "Kopalnia Głębinowa":
            errors.append(f"{rid} not assigned to Kopalnia Głębinowa")
        if "temple_basement" in set((ROOMS[rid].get("exits", {}) or {}).values()):
            errors.append(f"historical expansion still links to temple basement: {rid}")

    return {
        "version": "0.38.13",
        "basement_rooms": sum(1 for rid, room in ROOMS.items() if room.get("zone") == "Piwnica Świątyni"),
        "mine_expansion_rooms": len(expansion_ids),
        "error_count": len(errors),
        "errors": errors,
    }

UNDERGROUND_ROUTE_ISOLATION_AUDIT_V03813 = audit_underground_route_isolation_v03813()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
FULL_WORLD_TOPOLOGY_AUDIT_V03013 = audit_entire_world_topology_v03013(ROOMS)
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# HELP i atlasy nie przechowują osobnego balansu: czytają wartości wygenerowane.
HELP_TOPICS["generator"] = [
    "Generator Core pozostaje jedynym źródłem aktywnego balansu Soulbound; v0.30.0 dodaje semantyczny generator geografii i World Logic Validator.",
    "Generowane są: Level postaci 1-600, nielimitowane statystyki, moby i bossowie, HP, obrażenia, EXP, monety, drop-rate, przedmioty, wymagania, questy, skille i spelle, Soul 1-600, profesje, narzędzia, receptury, ceny oraz atlasy.",
    "Nowa zawartość nie wymaga ręcznego liczenia wartości. Nadaj jej nazwę, typ i powiązania ze światem; liczby wylicza Generator Core.",
    "Balance Validator sprawdza zakresy osi 1-600, dodatnie wartości oraz monotoniczność także nielimitowanej krzywej statystyk.",
]
HELP_TOPICS["level"] = [
    "Komenda level pokazuje wszystkie rzeczywiste poziomy: postać, Dusza, Soul Tier, Broń Duszy, każda odblokowana klasa (w tym nieaktywna), statystyki, poznane skille, profesje, narzędzia i wzniesienia.",
    "Na końcu wyniku: Your experience cap is N EXP. To jeden globalny Multi Cap: +500 EXP za każdy trwały poziom, bez podwójnego liczenia i bez dzielenia puli pomiędzy systemy.",
    "Walka nie rozwija profesji ani narzędzi. Poziomy profesji i narzędzi podnoszą globalny cap. Komenda expcap wyświetla zbiorczy podział capu.",
]
HELP_TOPICS["klasy"] = [
    "Soulbound ma 14 klas. Level postaci, Biegłość klasy i Skill Level mają zakres 1-600 i są liczone przez Generator Core.",
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
            _text="Level postaci 1-600 i główne osie progresji są wyliczane przez Generator Core v0.30.0; statystyki są nielimitowane."
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
