from validation.v4200_virtual_source import read_actual_refactored_source_v4200 as _sb420_view
from core.legacy_function_binding_v410 import bind_legacy_function_v410 as _sb410_bind

import admin.v410_release_audits as _sb410_mod_v410_release_audits
import admin.v410_equipment_audits as _sb410_mod_v410_equipment_audits

from data import catalog_mutations as _catalog_mut
from admin import audit_rules_v406 as _audit_rules_v406


def main():
    try:
        asyncio.run(MudServer().run())
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")




# v0.30.18 — Generator Core Numeric-Only semantic guard.
def generator_numeric_only_audit_v03018():
    return _audit_rules_v406.generator_numeric_only_audit_v03018(CATALOG_VALIDATION_AUDIT=CATALOG_VALIDATION_AUDIT, SOUL_MILESTONE_TIERS=SOUL_MILESTONE_TIERS, CLASS_MASTERY_MAX_LEVEL=CLASS_MASTERY_MAX_LEVEL, CLASS_SKILLS=CLASS_SKILLS, ITEMS=ITEMS)

GENERATOR_NUMERIC_ONLY_AUDIT_V03018 = generator_numeric_only_audit_v03018()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("generator", []).extend([
    "v0.30.18: Generator Core ma twardą granicę NUMERIC-ONLY. Semantyka jest hashowana przed i po generatorze; jakakolwiek zmiana chronionych pól blokuje start serwera.",
    "Chronione są m.in. nazwy/ID, unlocki skilli, Soul Milestones, wymagania EQ, questy, receptury, atlasy, gate'y świata, klasy/rasy i klucze statystyk/properties.",
])

LATEST_CHANGES_TITLE = "Soulbound v0.30.18 - Generator Core Numeric-Only"
LATEST_CHANGES = [
    "Generator Core zarządza wyłącznie wartościami liczbowego balansu; semantyka zawartości jest chroniona.",
    "Semantic Guard porównuje fingerprint przed/po generatorze i blokuje start przy zmianie nazwy, ID, progu, wymagania, struktury questu/receptury lub tożsamości EQ.",
    "Przywrócono ręczne Soul Milestones 5/10/15/20; generator nie może już ich zmieniać na 10/20/30/40.",
    "Generator nie nadpisuje required_mastery, min_profession_level, min_tool_level, unlocków skilli, atlasów ani gate'ów terenów.",
    "Ceny/HP/damage/EXP/nagrody/cooldown/mana/siła efektów pozostają generowane liczbowo.",
    "Auto kolejka startuje z 10 slotami na Levelu 1 i rośnie o 1 slot co 10 Leveli, do 50 na Levelu 400. Brak wipe.",
]


# ============================================================
# v0.30.19 - GENERATOR CORE EXPLICIT NUMERIC WRITE WHITELIST
# ============================================================
def generator_whitelist_audit_v03019():
    return _audit_rules_v406.generator_whitelist_audit_v03019(CATALOG_VALIDATION_AUDIT=CATALOG_VALIDATION_AUDIT, BALANCE_MATH_VERSION=BALANCE_MATH_VERSION)


GENERATOR_WHITELIST_AUDIT_V03019 = generator_whitelist_audit_v03019()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("generator", []).extend([
    "v0.30.19: Generator Core działa z jawną białą listą zapisu. Może zmienić wyłącznie konkretne pola liczbowego balansu.",
    "Mob: tylko generator_level/stage, HP, damage, EXP, waluta oraz prawdopodobieństwa istniejących dropów. Nie może zmienić rangi, nazw, quest-targetów ani listy dropów.",
    "Przedmiot/EQ: authored liczby są nadrzędne; Generator może tylko uzupełnić brakujące wartości liczbowe. Nie może dodać nowego statystyku, właściwości, slotu, klasy ani wymagania.",
    "Skill/spell: authored cooldown, mana i siła efektu są nadrzędne; Generator wypełnia tylko brakujące liczby. ID, nazwa, kind, scale i próg unlock są chronione.",
    "Quest/receptura: authored nagrody/XP są nadrzędne; Generator uzupełnia tylko braki i generator_level. Cele, wymagania, składniki, produkty i ilości pozostają ręcznie projektowane.",
    "Whitelist Guard obejmuje wszystkie dane projektowe UPPERCASE. Zapis poza białą listą zmienia fingerprint i blokuje start serwera.",
])

LATEST_CHANGES_TITLE = "Soulbound v0.30.19 - Generator Core Whitelist Guard"
LATEST_CHANGES = [
    "Generator Core ma teraz jawną białą listę ścieżek zapisu zamiast samej zasady NUMERIC-ONLY.",
    "Design wybiera CO istnieje; Generator może wyliczać wyłącznie ILE. Zapis poza whitelistą blokuje start serwera.",
    "Chronione są m.in. nazwy/ID, rank mobów, rodzaje efektów skilli, unlocki, staty-klucze EQ, listy dropów, cele i wymagania questów, składniki/produkty receptur oraz gate'y świata.",
    "W istniejących drops/stats/properties/runes Generator może zmieniać wyłącznie wartości liczbowe, nigdy ich klucze.",
    "Semantic Guard pozostaje drugą niezależną warstwą ochrony. Brak wipe i brak zmiany progresji 0.30.18.",
]


# ============================================================
# v0.30.20 - EXPANDED EQ / SAFE SELL ALL / EASY JEWELRY
# ============================================================
def equipment_expansion_audit_v03020():
    return _audit_rules_v406.equipment_expansion_audit_v03020(CLASS_EQUIPMENT_SLOT_DEFS=CLASS_EQUIPMENT_SLOT_DEFS, EQUIPMENT_SLOT_NAMES=EQUIPMENT_SLOT_NAMES, COMMAND_ALIASES=COMMAND_ALIASES, CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER=CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER, ITEMS=ITEMS)

EQUIPMENT_EXPANSION_AUDIT_V03020 = equipment_expansion_audit_v03020()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("eq", []).extend([
    "Pełna siatka klasowego EQ ma 17 logicznych slotów. Bransoletka i Akcesorium są generowane dla wszystkich 14 klas na każdym progu Levelu 1/10/20/.../600, obok naramienników, pasa, peleryny, karwaszy, kolczyków i reliktu.",
    "Nowe sloty mają różne role: naramienniki/pas są bardziej defensywne, karwasze bardziej ofensywne, peleryna bardziej utility, relikt ma mocniejszy profil klasowy.",
    "Pierścienie i talizmany nie wymagają już ręcznego wskazywania slotu 1/2: pełna nazwa albo zp/zt + numer używa wolnego slotu, a przy dwóch zajętych zastępuje słabszy.",
    "Ręczne zp1/zp2 oraz zt1/zt2 pozostają dostępne, gdy chcesz wymusić konkretny slot.",
])
HELP_TOPICS.setdefault("sprzedaj_wszystko", []).extend([
    "v0.30.20: sell all / sprzedaj wszystko sprzedaje tylko niezałożone EQ. Mikstury są zawsze chronione przed sell all.",
    "Sell all chroni również loot, consumables, materiały, narzędzia, quest itemy i wszystkie inne rzeczy, które nie są EQ.",
])

LATEST_CHANGES_TITLE = "Soulbound v0.30.20 - Expanded EQ + Safe Sell All + Easy Jewelry"
LATEST_CHANGES = [
    "Dodano pięć nowych slotów wyposażenia: naramienniki, pas, peleryna, karwasze, kolczyki i relikt; wszystkie klasy dostają je w pełnej progresji EQ.",
    "Sell all / sprzedaj wszystko sprzedaje wyłącznie niezałożone EQ. Mikstury i wszystkie nie-EQ są chronione.",
    "Pierścienie i talizmany można zakładać bez wybierania slotu 1/2: gra używa wolnego slotu, a przy pełnych slotach zastępuje słabszy.",
    "Dodano zp/zt oraz skróty nowych slotów; ręczne zp1/zp2 i zt1/zt2 pozostają.",
    "HELP zaktualizowany do nowych slotów, bezpiecznej sprzedaży hurtowej i prostszego zakładania biżuterii.",
]


# ============================================================
# v0.30.21 - FULL HELP / EQ SHOP / UNIFIED CURRENCY ECONOMY
# ============================================================
def refresh_help_v03021_full(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: refresh_help_v03021_full")
refresh_help_v03021_full = _sb410_bind(_sb410_mod_v410_equipment_audits.refresh_help_v03021_full, globals())

refresh_help_v03021_full()


def full_help_audit_v03021():
    errors=[]
    texts=[]
    for topic, rows in HELP_TOPICS.items():
        if not rows:
            errors.append(f"pusty HELP: {topic}")
            continue
        text="\n".join(str(x) for x in rows) if isinstance(rows,(list,tuple)) else str(rows)
        texts.append((topic,text))
    stale=(
        "pełny zestaw 8 części",
        "pełnym ośmioczęściowym",
        "sprzedaj inventory sprzedaje hurtowo",
        "123 skille/spelle rozłożone równomiernie",
        "sloty kolejki rosną wraz z Biegłością",
    )
    for topic,text in texts:
        low=normalize_lookup_text(text)
        for phrase in stale:
            if normalize_lookup_text(phrase) in low:
                errors.append(f"stary tekst HELP {topic}: {phrase}")
    for alias,target in HELP_TOPIC_ALIASES.items():
        if target in ("kategorie","help","pomoc","tematy","wszystko","komendy"):
            continue
        if target not in HELP_TOPICS:
            errors.append(f"alias HELP bez tematu: {alias}->{target}")
    return {
        "version":"0.30.21",
        "topics":len(HELP_TOPICS),
        "aliases":len(HELP_TOPIC_ALIASES),
        "error_count":len(errors),
        "errors":errors,
    }

FULL_HELP_AUDIT_V03021=full_help_audit_v03021()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
def eq_shop_audit_v03021():
    errors=[]
    slots=set(CLASS_EQUIPMENT_SLOT_DEFS)
    # v1.11.x: shields, bracelets and accessories are full stat-bearing
    # class-EQ progression slots. The canonical class shop grid has 17 slots.
    if len(slots)!=17:
        errors.append(f"logical EQ slots={len(slots)}, expected 17")
    if "shield" not in slots:
        errors.append("logical EQ slots missing shield")
    for class_name,definition in CLASS_EQUIPMENT_SETS.items():
        room=definition.get("room")
        if room not in SHOPS:
            errors.append(f"brak sklepu: {class_name}/{room}")
        for mastery in (1,100,200,300,400,600):
            ids=CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name,{}).get(mastery,())
            present={ITEMS[i].get("slot") for i in ids if i in ITEMS}
            if not slots.issubset(present):
                errors.append(f"{class_name} {mastery}: brakuje {sorted(slots-present)}")
                break
    return {"version":"0.30.21","shops":len(CLASS_SHOP_ITEMS_BY_ROOM),"slot_count":len(slots),"error_count":len(errors),"errors":errors}

EQ_SHOP_AUDIT_V03021=eq_shop_audit_v03021()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
def currency_economy_audit_v03021():
    return _audit_rules_v406.currency_economy_audit_v03021(SILVER_PER_GOLD=SILVER_PER_GOLD, SILVER_PER_MITHRIL=SILVER_PER_MITHRIL, currency_reading_text=currency_reading_text, QUESTS=QUESTS, v0190_quest_currency_reward=v0190_quest_currency_reward, ITEMS=ITEMS)

CURRENCY_ECONOMY_AUDIT_V03021=currency_economy_audit_v03021()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
LATEST_CHANGES_TITLE = "Soulbound v0.30.21 - Full HELP + Unified Currency Economy"
LATEST_CHANGES = [
    "Pełny audit finalnego HELP: wszystkie tematy i aliasy są sprawdzane po nałożeniu wszystkich historycznych warstw pomocy.",
    "Klasowe sklepy EQ są audytowane dla wszystkich 14 klas i pełnych 13 typów wyposażenia.",
    "Jedno saldo waluty jest zawsze prezentowane po normalizacji: mithril, złoto, srebro; 100 srebra jest czytane jako 1 złota.",
    "Nagrody questów zostały podniesione i skalowane tak, aby od początku zawierały co najmniej równowartość złota, a mithril pojawiał się dopiero w późnym endgame.",
    "Ceny podstawowych narzędzi nie zależą już od przypadkowego generator_level przedmiotu; wszystkie starterowe narzędzia mają spójny przedział cenowy.",
]


# ============================================================
# v0.30.22 - FULL REGRESSION / WORLD INTEGRITY RELEASE GATE
# ============================================================
def full_release_integrity_audit_v03022(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: full_release_integrity_audit_v03022")
full_release_integrity_audit_v03022 = _sb410_bind(_sb410_mod_v410_release_audits.full_release_integrity_audit_v03022, globals())

FULL_RELEASE_INTEGRITY_AUDIT_V03022 = full_release_integrity_audit_v03022()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.22: pełny regression pass całej gry i świata. Statyczna topologia, powroty, lazy-exity, profesje, sklepy, zasoby, spawny, NPC, EQ, Generator Core, HELP i ekonomia przechodzą wspólny release gate."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.22 - Full Regression + World Integrity"
LATEST_CHANGES = [
    "Pełna ponowna walidacja całej gry przed wydaniem: wszystkie aktywne audyty poprzednich systemów pozostają czyste.",
    "Cały statyczny świat musi być osiągalny ze square i mieć drogę powrotną; wszystkie zwykłe wyjścia są dwukierunkowe, a lazy-exity muszą należeć do znanych generatorów runtime.",
    "Osobny release gate sprawdza lokacje profesji, trasy auto, sklepy i ich przedmioty, zasoby, spawny, NPC oraz komplet referencji klasowego EQ.",
    "Generator Core v0.30.21 pozostaje bez zmian: Numeric-Only + Whitelist Guard; v0.30.22 nie zmienia balansu ani semantyki świata.",
    "Brak wipe. v0.30.22 jest wydaniem walidacyjno-stabilizacyjnym nad bazą v0.30.21.",
]


# v0.30.23 - ACCESSIBLE EXITS
HELP_TOPIC_ALIASES.update({"ex": "exits", "wyjscia": "exits", "wyjścia": "exits"})
HELP_TOPICS["exits"] = [
    "exits / ex pokazuje wszystkie dostępne kierunki razem z nazwą lokacji, do której każdy kierunek prowadzi.",
    "Przykład: północ — Północna Ulica; wschód — Targ Rybny.",
    "exits info pokazuje dodatkowo strefę oraz ocenę zagrożenia celu.",
    "Komenda niczego nie przesuwa i nie zmienia topologii świata.",
]
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.23: exits oraz skrót ex zawsze czytają kierunek i nazwę miejsca docelowego; exits info zachowuje rozszerzone informacje o strefie i zagrożeniu."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.23 - Accessible Exits"
LATEST_CHANGES = [
    "exits pokazuje teraz kierunek i nazwę lokacji docelowej zamiast samych kierunków.",
    "Dodano skrót ex działający identycznie jak exits.",
    "exits info nadal rozszerza wynik o strefę i ocenę zagrożenia.",
    "Lazy/runtime wyjścia materializują nazwę sąsiedniego pokoju do odczytu NVDA, bez poruszania postacią.",
    "Topologia, balans, ekonomia i baza danych pozostają bez zmian względem v0.30.22; brak wipe.",
]



# ============================================================
# v0.30.24 - HYBRID QUEST REWARD AUDIT + ECONOMY SAFETY
# ============================================================
def quest_reward_hybrid_audit_v03024(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: quest_reward_hybrid_audit_v03024")
quest_reward_hybrid_audit_v03024 = _sb410_bind(_sb410_mod_v410_release_audits.quest_reward_hybrid_audit_v03024, globals())

QUEST_REWARD_HYBRID_AUDIT_V03024 = quest_reward_hybrid_audit_v03024()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("quest", []).extend([
    "v0.30.24: ważne questy fabularne, próby profesji, wybrane duże zadania świata i Próby Broni Duszy mają ręcznie zbalansowaną, chronioną nagrodę walutową.",
    "Pozostałe questy zachowują authored walutę, jeśli ją mają; Generator Core uzupełnia tylko brakującą walutę fallbackową. Wszystkie wypłaty trafiają do jednego wspólnego salda.",
    "quest list <NPC> pokazuje teraz również nagrodę walutową przed przyjęciem zadania; quest info <numer> pokazuje pełny zestaw nagród.",
])
HELP_TOPICS.setdefault("waluta", []).extend([
    "v0.30.24 + v1.13.21: ręcznie oznaczone questy zachowują dokładną kwotę; pozostałe authored nagrody także są chronione, a Generator uzupełnia wyłącznie brakujące wartości.",
    "Generator Core nie może już nadpisać manual_currency_reward_coins. Złoto i mithril są nadal tylko sposobem prezentacji jednego salda w srebrze.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.24 + v1.13.21: Hybrid Quest Rewards respektuje authored-wins; ręczne markery są chronione dokładnie, authored nagrody pozostają własnością danych, a Generator uzupełnia tylko brakującą walutę. Quest list pokazuje nagrodę przed przyjęciem."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.24 - Hybrid Quest Rewards"
LATEST_CHANGES = [
    "Dodano hybrydowy balans waluty questów: ręczne nagrody dla ważnych zadań oraz automatyczny Generator Core dla pozostałych.",
    "64 ważne questy mają chronione kwoty; Generator Core v0.30.24 nie może ich nadpisać podczas finalnego registry pass.",
    "Odłamki dla kowala ponownie dają 7 złota i 500 srebra; cztery podstawowe Próby profesji dają po 2 złota i 500 srebra.",
    "Duże zadania świata odzyskały ręczne premie, m.in. Plaga Trolli 15 złota, Król Trolli 75 złota, a Bezpieczny Szlak Karawan 150 złota.",
    "Próby Broni Duszy używają chronionej krzywej kamieni milowych aż do Tier 40; nie są już przypadkowo spłaszczane przez ogólny wzór questu.",
    "quest list <NPC> pokazuje walutę przed przyjęciem, a quest info informuje, gdy kwota jest ręcznie chroniona.",
    "Wszystkie 307 questów nadal wypłacają do jednego wspólnego salda; reward_gold i reward_mithril pozostają wyzerowane w finalnym rejestrze.",
    "Brak wipe. Topologia świata, quest progress, walka, EQ i pozostałe systemy nie są przebudowywane przez tę zmianę.",
]


# ============================================================
# v0.30.25 - PROFESSION + TOOL XP INTEGRITY
# ============================================================
# Każda realna akcja profesyjna wykonywana narzędziem rozwija obie osie:
# profesję oraz odpowiadające jej narzędzie. Sprzedaż surowców nie jest
# akcją narzędzia i zachowuje dotychczasowe zasady.
V03025_PROFESSION_REWARD_REPAIRS = {}
for _quest_id, _quest in QUESTS.items():
    _tool_type = _quest.get("reward_tool_type")
    _expected_profession = profession_for_tool_type(_tool_type)
    _has_profession_reward = int(_quest.get("reward_profession_xp", 0) or 0) > 0
    _has_tool_reward = int(_quest.get("reward_tool_xp", 0) or 0) > 0
    if _has_profession_reward and _has_tool_reward and _expected_profession:
        if not _quest.get("reward_profession"):
            _quest["reward_profession"] = _expected_profession
            V03025_PROFESSION_REWARD_REPAIRS[_quest_id] = _expected_profession


def profession_tool_xp_audit_v03025(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: profession_tool_xp_audit_v03025")
profession_tool_xp_audit_v03025 = _sb410_bind(_sb410_mod_v410_release_audits.profession_tool_xp_audit_v03025, globals())


PROFESSION_TOOL_XP_AUDIT_V03025 = profession_tool_xp_audit_v03025()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
def full_release_integrity_audit_v03025():
    errors = []
    previous = globals().get("FULL_RELEASE_INTEGRITY_AUDIT_V03022") or {}
    if int(previous.get("error_count", 0) or 0):
        errors.append("v0.30.22 release gate regressed")
    if int(PROFESSION_TOOL_XP_AUDIT_V03025.get("error_count", 0) or 0):
        errors.append("profession/tool XP audit failed")
    if int(WORLD_LOGIC_AUDIT.get("error_count", 0) or 0):
        errors.append("world logic audit failed")
    if int(WORLD_LOGIC_AUDIT.get("warning_count", 0) or 0):
        errors.append("world logic warnings present")
    return {
        "version": "0.30.25",
        "generator_version": str(BALANCE_MATH_VERSION),
        "base_release_gate": previous.get("version", "v0.30.22"),
        "profession_tool_xp": PROFESSION_TOOL_XP_AUDIT_V03025.get("error_count") == 0,
        "world_logic": WORLD_LOGIC_AUDIT.get("error_count") == 0,
        "world_warnings": WORLD_LOGIC_AUDIT.get("warning_count", 0),
        "error_count": len(errors),
        "errors": errors,
    }

FULL_RELEASE_INTEGRITY_AUDIT_V03025 = full_release_integrity_audit_v03025()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("kowalstwo", []).extend([
    "v0.30.25: każde przetopienie rudy w sztabkę daje jednocześnie XP Kowalstwa i XP Młota Rzemieślniczego.",
    "Ta sama zasada obowiązuje każde kucie: akcja rozwija profesję Kowalstwo oraz Młot Rzemieślniczy.",
])
HELP_TOPICS.setdefault("profesje", []).extend([
    "v0.30.25: każda właściwa akcja wykonywana narzędziem rozwija równolegle profesję i odpowiadające jej narzędzie.",
    "Wędkarstwo/Wędka, Górnictwo/Kilof, Drwalstwo/Piła, Zielarstwo/Sierp, Kowalstwo/Młot, Gotowanie/Nóż, Alchemia/Moździerz i Jubilerstwo/Szczypce są audytowane jako pary XP.",
    "Sprzedaż surowców nadal może dawać XP profesji, ale nie daje XP narzędzia, ponieważ narzędzie nie jest używane przy sprzedaży.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.25: pełny audit profession+tool XP. Naprawiono 13 questów Gotowania Marcela, które mogły kierować XP profesji do Wędkarstwa zamiast Gotowania."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.25 - Profession + Tool XP Integrity"
LATEST_CHANGES = [
    "Każde przetopienie i każde kucie daje jednocześnie XP Kowalstwa oraz XP Młota Rzemieślniczego.",
    "Pełny audit objął wszystkie receptury Kowalstwa, Alchemii, Gotowania i Jubilerstwa oraz główne akcje czterech profesji zbierackich.",
    "Naprawiono 13 questów Gotowania Marcela: nagroda profesji jest teraz jawnie przypisana do Gotowania, a nie do awaryjnego Wędkarstwa.",
    "Nagroda profesyjna questu jest teraz wyprowadzana z reward_tool_type, jeśli stary wpis nie ma reward_profession; usunięto ryzykowny domyślny fallback na Wędkarstwo.",
    "Start serwera blokuje się, jeśli receptura nie ma dodatniego XP profesji i narzędzia albo jeśli quest profesyjny ma niespójną parę profesja/narzędzie.",
    "Generator Core pozostaje v0.30.24; v0.30.25 nie zmienia jego balansu, topologii świata ani ekonomii. Brak wipe.",
]


# ============================================================
# v0.30.26 - FULL GAMEPLAY FLOW + TOOL TIER GATING
# ============================================================
# `ex` jest publiczną komendą gry, nie tylko aliasem HELP.
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.

# Dedykowane pomieszczenia specjalistów są również prawdziwymi stanowiskami pracy.
# Deski należą do Drwalstwa, więc nie dostają Warsztatu Haldora jako stanowiska.
V03026_WOOD_RECIPES = []
for _recipe_id, _recipe in CRAFT_RECIPES.items():
    _output = str(_recipe.get("output") or "")
    if _output.endswith("_plank"):
        _recipe["profession"] = "Drwalstwo"
        _recipe["tool_type"] = "woodcutting"
        _recipe["tool_item_id"] = "saw"
        _recipe["tool_name"] = "Piła"
        _recipe["category"] = "woodworking"
        _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("forester_lodge",)))
        _recipe["profession_xp"] = max(1, int(_recipe.get("profession_xp", 10) or 10))
        _recipe["tool_xp"] = max(1, int(_recipe.get("tool_xp", 8) or 8))
        V03026_WOOD_RECIPES.append(_recipe_id)
    else:
        _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("crafting_workshop",)))
for _recipe in COOK_RECIPES.values():
    _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("blue_flame_kitchen",)))
for _recipe in ALCHEMY_RECIPES.values():
    _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("alchemy_lab",)))
for _recipe in JEWELCRAFT_RECIPES.values():
    _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("jeweler_workshop",)))

# Czysty Kowal może rozpocząć profesję bez rozwijania Górnictwa.
# Doran sprzedaje tylko podstawowe rudy; Kobalt+ pozostaje zdobyczą świata/Górnictwa.
for _starter_ore in ("iron_ore", "silver_ore", "gold_ore"):
    if _starter_ore not in _catalog_mut.catalog_setdefault_path('SHOPS', SHOPS, (), "forge", []):
        SHOPS["forge"].append(_starter_ore)

# v0.30.26: Odłamki Duszy są materiałem questowym Krypty i nie mogą być
# spłaszczane przez ogólny rebalance dropów Generator Core. Ten późny pass
# przywraca celowe szanse po wykonaniu Generator Core. Dynamiczne piętra
# tworzone później mają własne wysokie wartości w generatorze runtime.
def apply_soul_shard_drop_fix_v03026():
    # Klasyczne moby wejściowej Krypty.
    if "skeleton" in MOB_TEMPLATES:
        _catalog_mut.catalog_setdefault_path('MOB_TEMPLATES', MOB_TEMPLATES, ("skeleton",), "drops", {})["soul_shard"] = 1.0
    if "crypt_wraith" in MOB_TEMPLATES:
        _catalog_mut.catalog_setdefault_path('MOB_TEMPLATES', MOB_TEMPLATES, ("crypt_wraith",), "drops", {})["soul_shard"] = 1.0

    regular_fixed = 0
    boss_fixed = 0
    mythic_fixed = 0
    for _tid, _template in MOB_TEMPLATES.items():
        _crypt_floor = int(_template.get("crypt_floor", 0) or 0)
        _mythic_floor = int(_template.get("mythic_crypt_floor", 0) or 0)
        if _template.get("crypt_boss") or _template.get("mythic_crypt_boss"):
            _template.setdefault("drops", {})["soul_shard"] = 1.0
            boss_fixed += 1
        elif _crypt_floor > 0:
            # v0.59.1: zwykła Krypta gwarantuje Odłamek, aby quest na 20 sztuk nie zależał od RNG.
            _template.setdefault("drops", {})["soul_shard"] = 1.0
            regular_fixed += 1
        elif _mythic_floor > 0:
            # Mityczna Krypta jest późnym źródłem — odłamek ma być częsty.
            _template.setdefault("drops", {})["soul_shard"] = 1.0
            mythic_fixed += 1
    return {
        "regular_crypt": regular_fixed,
        "mythic_crypt": mythic_fixed,
        "bosses": boss_fixed,
    }

SOUL_SHARD_DROP_FIX_V03026 = apply_soul_shard_drop_fix_v03026()

# HELP: Tier narzędzia jest teraz twardym progiem zawartości.
HELP_TOPICS.setdefault("quest", []).append(
    "v0.59.1: Odłamki Duszy są gwarantowanym dropem z każdego zwykłego moba Krypty i Mitycznej Krypty; bossowie nadal gwarantują Odłamek. Quest Odłamki dla kowala wymaga 20 sztuk, więc nie zależy już od pechowych rzutów RNG."
)
HELP_TOPICS.setdefault("narzedzia", []).extend([
    "v0.30.26: nowy gatunek ryby, ruda, drewno lub zioło odblokowuje się dopiero przy wejściu narzędzia na wymagany Tier; pojedynczy level wewnątrz Tieru nie rozszerza puli zasobów.",
    "Receptury Kowalstwa, Gotowania, Alchemii, Jubilerstwa i obróbki drewna wymagają także odpowiedniego Tieru właściwego narzędzia. Próg Tieru wynika z wymaganego levelu profesji.",
])
HELP_TOPICS.setdefault("wedkarstwo", []).append(
    "v0.30.26: dostępne gatunki ryb zależą od Tieru Wędki. Awans levelu wewnątrz tego samego Tieru poprawia progres/bonus, ale nie odblokowuje nowego gatunku."
)
HELP_TOPICS.setdefault("gornictwo", []).append(
    "v0.30.26: dostępne rudy i minerały zależą od Tieru Kilofa oraz, w kopalniach piętrowych, od osiągniętej głębokości."
)
HELP_TOPICS.setdefault("drwalstwo", []).extend([
    "v0.30.26: dostępne gatunki drewna zależą od Tieru Piły.",
    "Obróbka desek używa teraz Drwalstwa + Piły i daje XP obu, zamiast błędnie używać Kowalstwa + Młota."
])
HELP_TOPICS.setdefault("zielarstwo", []).append(
    "v0.30.26: dostępne rośliny zależą od Tieru Sierpa Zielarskiego."
)
HELP_TOPICS.setdefault("kowalstwo", []).append(
    "v0.30.26: receptura wymaga zarówno odpowiedniego levelu Kowalstwa, jak i Tieru Młota Rzemieślniczego odpowiadającego temu progowi."
)
HELP_TOPICS.setdefault("gotowanie", []).append(
    "v0.30.26: receptura wymaga odpowiedniego levelu Gotowania i odpowiadającego mu Tieru Noża Kucharskiego."
)
HELP_TOPICS.setdefault("alchemia", []).append(
    "v0.30.26: receptura wymaga odpowiedniego levelu Alchemii i odpowiadającego mu Tieru Moździerza Alchemicznego."
)
HELP_TOPICS.setdefault("jubilerstwo", []).append(
    "v0.30.26: receptura wymaga odpowiedniego levelu Jubilerstwa i odpowiadającego mu Tieru Szczypiec Jubilerskich."
)
HELP_TOPICS["exits"] = [
    "exits / ex pokazuje wszystkie dostępne kierunki razem z nazwą lokacji, do której każdy kierunek prowadzi.",
    "Przykład: północ — Północna Ulica; wschód — Targ Rybny.",
    "ex jest twardym aliasem parsera i wywołuje dokładnie ten sam handler co exits.",
    "exits info pokazuje dodatkowo strefę oraz ocenę zagrożenia celu.",
]


def gameplay_flow_audit_v03026(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: gameplay_flow_audit_v03026")
gameplay_flow_audit_v03026 = _sb410_bind(_sb410_mod_v410_release_audits.gameplay_flow_audit_v03026, globals())

GAMEPLAY_FLOW_AUDIT_V03026 = gameplay_flow_audit_v03026()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.26: gameplay flow pass. Naprawiono ex->exits, Tier-gating zasobów i receptur, stanowiska specjalistów oraz deski Drwalstwo+Piła."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.26 - Gameplay Flow + Tool Tier Gating"

# ============================================================
# v0.30.27 - SILENT COMMAND PROMPT / NVDA
# ============================================================
LATEST_CHANGES = [
    "v0.30.27: po wykonaniu komendy gra nie wypisuje już znaku >. NVDA nie czyta zbędnego promptu; wejście komend działa bez zmian.",
] + LATEST_CHANGES
LATEST_CHANGES_TITLE = "Soulbound v0.30.27 - Silent NVDA Command Prompt"

LATEST_CHANGES = [
    "Naprawiono skrót ex: jest twardym aliasem parsera do exits i czyta kierunek oraz nazwę lokacji docelowej.",
    "Ryby, rudy, drewno i zioła są odblokowywane przez Tier właściwego narzędzia; pula nie zmienia się przy każdym levelu wewnątrz Tieru.",
    "Receptury wymagają teraz odpowiedniego Tieru narzędzia wynikającego z progu profesji, a nie tylko levelu profesji.",
    "Deski są poprawnie obsługiwane przez Drwalstwo + Piłę i dają XP obu osi, zamiast Kowalstwa + Młota.",
    "Warsztat Rzemieślniczy, Kuchnia Błękitnego Płomienia, Laboratorium Alchemiczne i Pracownia Jubilerska są prawdziwymi stanowiskami właściwych receptur.",
    "Poprawiono komunikaty o miejscach zakupu wszystkich narzędzi oraz stare wpisy HELP dotyczące XP i blokad receptur.",
    "Surowe klejnoty z Górnictwa są odblokowywane przez Tier Kilofa; level Górnictwa wpływa nadal na jakość i szansę, ale nie zmienia puli między Tierami.",
    "Doran sprzedaje podstawowe Rudy Żelaza, Srebra i Złota, więc czysty Kowal może rozpocząć profesję bez Górnictwa; Kobalt i wyżej pozostają zawartością świata/Górnictwa.",
    "Odłamki Duszy są teraz gwarantowane z każdego zwykłego moba Krypty i Mitycznej Krypty; bossowie również gwarantują Odłamek, więc quest na 20 sztuk nie zależy od RNG.",
    "Generator Core pozostaje v0.30.24. Brak wipe.",
]


# ============================================================
# v0.30.28 - ACCESSIBLE EXITS CLIENT COMPATIBILITY HOTFIX
# ============================================================
HELP_TOPICS["exits"] = [
    "exits / ex pokazuje każdy kierunek oraz nazwę miejsca, do którego prowadzi.",
    "Odpowiedź jest wysyłana w prostych osobnych liniach, np. północ: Północna Ulica.",
    "ex i exits używają dokładnie tego samego handlera.",
    "exits info dodaje strefę oraz ocenę zagrożenia celu.",
]
LATEST_CHANGES_TITLE = "Soulbound v0.30.28 - Accessible Exits Client Compatibility"
LATEST_CHANGES = [
    "v0.30.28: ex i exits zwracają prosty wieloliniowy blok kierunek: miejsce docelowe.",
    "v0.30.28: usunięto z podstawowego formatu wyjść znak półpauzy/em dash i długą linię ze średnikami dla lepszej zgodności z klientami MUD i NVDA.",
    "Brak zmian balansu, mapy, questów, profesji i Generator Core.",
    "Brak wipe.",
]



# ============================================================
# v0.30.29 - DEPLOY STARTUP HOTFIX
# ============================================================
# Historyczne audyty regresji sprawdzają zachowanie systemów, a nie
# bieżący numer release'u. Dzięki temu nowe wydanie nie blokuje startu
# tylko dlatego, że VERSION jest nowsze od wersji, w której audyt powstał.
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.29: naprawiono blokadę startu DEPLOY/Railway powodowaną przez historyczne audyty przypięte do starych numerów VERSION."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.29 - Deploy Startup Hotfix"

# ============================================================
# v0.30.30 - 30-SECOND BUFFS + NVDA LIFECYCLE ANNOUNCEMENTS
# ============================================================
HELP_TOPIC_ALIASES.update({
    "buff": "buffy", "buffs": "buffy", "boost": "buffy",
    "buffy": "buffy", "wzmocnienia": "buffy",
})
HELP_TOPICS["buffy"] = [
    "Wszystkie bojowe skille typu boost działają dokładnie 30 sekund.",
    "Po użyciu gra mówi: Buff aktywowany, nazwę buffa, czas 30 sekund oraz siłę wzmocnienia.",
    "Po naturalnym zakończeniu gra mówi dokładnie raz: Buff wygasł i nazwę buffa.",
    "Różne buffy mogą działać równocześnie i nadal sumują bonusy według dotychczasowych zasad.",
    "Auto Skill Queue nie odnawia tego samego buffa, dopóki jest aktywny; po wygaśnięciu może użyć go ponownie.",
]

def buff_duration_audit_v03030():
    return _audit_rules_v406.buff_duration_audit_v03030(CLASS_SKILLS=CLASS_SKILLS, GLOBAL_SKILL_BUFF_DURATION_SECONDS=GLOBAL_SKILL_BUFF_DURATION_SECONDS)

BUFF_DURATION_AUDIT_V03030 = buff_duration_audit_v03030()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.30: wszystkie bojowe buffy typu boost trwają 30 sekund; NVDA informuje o aktywacji i naturalnym wygaśnięciu."
)
LATEST_CHANGES = [
    "v0.30.30: wszystkie bojowe buffy typu boost mają dokładnie 30 sekund działania.",
    "v0.30.30: przy aktywacji NVDA czyta nazwę buffa, czas 30 sekund, jego bonus oraz łączne aktywne wzmocnienie.",
    "v0.30.30: po naturalnym wygaśnięciu NVDA mówi dokładnie raz: Buff wygasł: <nazwa>.",
    "v0.30.30: Generator Core nadal pozostaje v0.30.24; czas buffów jest finalną regułą gameplay po Generator Core.",
    "Brak wipe.",
] + LATEST_CHANGES
LATEST_CHANGES_TITLE = "Soulbound v0.30.30 - 30-Second Buffs + NVDA Lifecycle"

# ============================================================
# v0.30.31 - PARTY COMBAT FEED
# ============================================================
HELP_TOPICS.setdefault("party", []).extend([
    "Podczas wspólnej walki członkowie drużyny w tej samej lokacji widzą, kto atakuje, jakiego ataku lub skilla używa i ile obrażeń zadaje.",
    "Krytyki i pokonanie celu są oznaczane. Ataki obszarowe są czytane jako jeden krótki wynik łączny, aby nie spamować NVDA.",
    "Party Combat Feed respektuje filtr walki: combat normal i combat full pokazują feed, combat concise go ukrywa.",
])
HELP_TOPICS.setdefault("combat", []).append(
    "W drużynie tryb normal/full pokazuje także zwięzłe obrażenia innych członków będących w tej samej lokacji; concise pozostaje cichy."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.31: Party Combat Feed pokazuje w tej samej lokacji nazwę członka drużyny, atak/skill, dokładne obrażenia, krytyki i wynik AoE."
)
LATEST_CHANGES = [
    "v0.30.31: Party Combat Feed pokazuje obrażenia innych członków drużyny znajdujących się w tej samej lokacji.",
    "v0.30.31: autoatak i skill pokazują nazwę gracza, nazwę ataku, cel i dokładne obrażenia; krytyk i zabicie są oznaczane.",
    "v0.30.31: AoE daje jeden zwięzły wynik łączny zamiast osobnego spamu dla każdego celu.",
    "v0.30.31: feed respektuje combat normal/full; combat concise go ukrywa.",
    "Brak wipe.",
] + LATEST_CHANGES
LATEST_CHANGES_TITLE = "Soulbound v0.30.31 - Party Combat Feed"

def party_combat_feed_audit_v03031():
    return _audit_rules_v406.party_combat_feed_audit_v03031(MudServer=MudServer)

PARTY_COMBAT_FEED_AUDIT_V03031 = party_combat_feed_audit_v03031()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
# ============================================================
# v0.30.32 - PARTY ROLES: TARGETING, PRIEST AUTO-HEAL, PARTY BUFFS
# ============================================================
HELP_TOPICS.setdefault("party", []).extend([
    "Moby walczące z drużyną mogą atakować różnych żywych członków party będących w tej samej lokacji i zaangażowanych w tę walkę.",
    "Aktywne zasłoń Strażnika ma pierwszeństwo: gdy tank zasłania drużynę, przejmuje ataki moba.",
    "Kapłan w drużynie automatycznie reaguje na najbardziej rannego żywego członka w tej samej lokacji, gdy jego HP spadnie poniżej 85 procent. Dotyczy każdego członka, nie tylko lidera.",
    "Auto-leczenie używa wyłącznie faktycznie nauczonych i odblokowanych leczeń, zużywa normalną Manę i respektuje cooldown. Przy kilku rannych może wybrać leczenie grupowe.",
    "Każdy bojowy buff typu boost działa przez 30 sekund na żywych członków drużyny znajdujących się w tej samej lokacji co rzucający.",
])
HELP_TOPICS.setdefault("combat", []).append(
    "v0.30.32: walka drużynowa ma role: mob rozdziela cele po party, Strażnik może przejąć ataki przez zasłoń, Kapłan automatycznie leczy rannych, a boosty działają na drużynę w tej samej lokacji."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.32: Party Roles - ataki mobów na drużynę, auto-heal Kapłana każdego rannego członka i 30-sekundowe boosty drużynowe."
)
LATEST_CHANGES = [
    "v0.30.32: mob walczący z party może wybierać różnych aktywnych członków drużyny jako cel; Strażnik z zasłoń nadal ma pierwszeństwo.",
    "v0.30.32: Kapłan automatycznie leczy najbardziej rannego członka party w tej samej lokacji poniżej 85% HP; nie tylko lidera.",
    "v0.30.32: auto-heal respektuje nauczone skille, Biegłość, Manę i cooldown oraz może wybrać group heal przy kilku rannych.",
    "v0.30.32: wszystkie skille boost nakładają 30-sekundowy buff także na żywych członków party w tej samej lokacji.",
    "Brak wipe.",
] + LATEST_CHANGES
LATEST_CHANGES_TITLE = "Soulbound v0.30.32 - Party Roles"

def party_roles_audit_v03032():
    return _audit_rules_v406.party_roles_audit_v03032(MudServer=MudServer, Session=Session, PARTY_AUTO_HEAL_THRESHOLD=PARTY_AUTO_HEAL_THRESHOLD)

PARTY_ROLES_AUDIT_V03032 = party_roles_audit_v03032()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
# ============================================================
# v0.30.33 - UNIQUE TOOL TIER NAMES + RENEWABLE TAILOR QUEST
# ============================================================
def tool_tier_name_audit_v03033():
    return _audit_rules_v406.tool_tier_name_audit_v03033(TOOL_TIER_NAMES=TOOL_TIER_NAMES, TOOL_MAX_TIER=TOOL_MAX_TIER, QUESTS=QUESTS, QUEST_REPEAT_COOLDOWN_SECONDS=QUEST_REPEAT_COOLDOWN_SECONDS)

TOOL_TIER_NAME_AUDIT_V03033 = tool_tier_name_audit_v03033()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("narzedzia", []).append(
    "v0.30.33: wszystkie 40 Tierów każdego z 8 narzędzi ma własną unikalną nazwę; usunięto powtarzanie nazwy Tieru 20 z dopiskami +210, +220 itd."
)
HELP_TOPICS.setdefault("quest", []).append(
    "Miejska przysługa Krawcowej Lysy: Mundury dla straży jest odnawialna co 60 minut. Po ponownym przyjęciu postęp zaczyna się od 0/1 i trzeba ponownie wykonać dostawę."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.33: unikalne nazwy wszystkich Tierów narzędzi oraz odnawialne co 60 minut zadanie Krawcowej Lysy."
)
LATEST_CHANGES = [
    "v0.30.33: 8 narzędzi ma po 40 unikalnych nazw Tierów; łącznie 320 nazw bez duplikatów w obrębie narzędzia.",
    "v0.30.33: usunięto nazwy typu Wędka Wiecznego Oceanu +210/+220; Tiery 21-40 mają osobne nazwy tematyczne.",
    "v0.30.33: quest Krawcowej Lysy - Mundury dla straży - jest odnawialny co 60 minut i przy ponownym przyjęciu zaczyna od 0/1.",
    "Brak wipe.",
] + LATEST_CHANGES
LATEST_CHANGES_TITLE = "Soulbound v0.30.33 - Unique Tool Tiers + Renewable Tailor Quest"


# ============================================================
# v0.30.34 - HALDOR STEEL PLATE CORPSE QUEST FIX
# ============================================================
def haldor_steel_plate_corpse_audit_v03034():
    return _audit_rules_v406.haldor_steel_plate_corpse_audit_v03034(QUESTS=QUESTS, MOB_TEMPLATES=MOB_TEMPLATES, ITEMS=ITEMS, CRAFT_MATERIAL_STORAGE_IDS=CRAFT_MATERIAL_STORAGE_IDS)

HALDOR_STEEL_PLATE_CORPSE_AUDIT_V03034 = haldor_steel_plate_corpse_audit_v03034()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("kowalstwo", []).extend([
    "v0.30.34: quest Stal do Przetopu wymaga odzyskania Stalowych Płyt z ciał opancerzonych nieumarłych.",
    "Płyta pojawia się na ciele. Użyj ciało, przeszukaj ciało albo weź Stalową Płytę z ciała. Dopiero zabranie płyty zalicza postęp 0/4 i przenosi ją do Szkatułki Rzemieślniczej.",
])
HELP_TOPICS.setdefault("quest", []).append(
    "v0.30.34: Stal do Przetopu — Stalowe Płyty są realnym lootem z ciał na Starym Cmentarzu; samo zabicie moba nie zalicza płyty."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.34 - Haldor Steel Plate Corpse Fix"
LATEST_CHANGES = [
    "Naprawiono quest Haldora Stal do Przetopu: Stalowa Płyta z Pancerza pojawia się na ciele opancerzonego nieumarłego zamiast wpadać bezpośrednio do magazynu.",
    "Postęp 0/4 zwiększa się dopiero po zabraniu płyty z ciała; płyta następnie trafia do Szkatułki Rzemieślniczej.",
    "Szanse zachowane: Szkielet w Stalowym Kirysie 72%, Niespokojny Umarły 28%, Zbieracz Kości 42%.",
    "Generator Core pozostaje v0.30.24. Brak wipe.",
] + LATEST_CHANGES



# ============================================================
# v0.30.35 - BROKEN BLADES QUEST + LOSSLESS DEATH
# ============================================================
def v03035_broken_blades_and_death_audit(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: v03035_broken_blades_and_death_audit")
v03035_broken_blades_and_death_audit = _sb410_bind(_sb410_mod_v410_equipment_audits.v03035_broken_blades_and_death_audit, globals())

V03035_AUDIT = v03035_broken_blades_and_death_audit()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["śmierć"] = (
    "Po śmierci postać odradza się w Świątyni Odrodzenia z pełnym HP i Maną. "
    "Nie traci waluty, przedmiotów, EQ, XP, Biegłości, Soul XP, profesji ani poziomów narzędzi. "
    "Wyjątkiem niebędącym karą śmierci jest Phoenix Egg: gdy uruchamia Re-raise, samo jajko zostaje zużyte zgodnie z jego źródłową mechaniką. "
    "Aktywne buffy zachowują pozostały czas działania."
)
HELP_TOPICS["smierc"] = HELP_TOPICS["śmierć"]
HELP_TOPICS["death"] = HELP_TOPICS["śmierć"]
HELP_TOPICS.setdefault("questy godzinne", []).append(
    "v0.30.35: Złamane ostrza 0/6 działa na jawnej liście uzbrojonych nieumarłych Starego Cmentarza; każdy kwalifikujący się kill daje 1 Uszkodzone Ostrze i natychmiast zwiększa postęp."
)
HELP_TOPICS.setdefault("kowalstwo", []).append(
    "v0.30.35: Złamane ostrza nie zależy już od przypadkowego słowa w nazwie moba; źródła na Starym Cmentarzu są jawnie oznaczone."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.35: naprawiono Złamane ostrza oraz usunięto wszystkie trwałe kary śmierci."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.35 - Broken Blades + Lossless Death"
LATEST_CHANGES = [
    "v0.30.35: Złamane ostrza 0/6 ma jawne źródła na Starym Cmentarzu i nie zależy już wyłącznie od tekstu nazwy przeciwnika.",
    "v0.30.35: każdy kwalifikujący się kill przy aktywnym queście daje 1 Uszkodzone Ostrze i od razu podnosi postęp.",
    "v0.30.35: śmierć nie zabiera już 10% waluty ani żadnych przedmiotów, EQ czy progresji.",
    "v0.30.35: aktywne 30-sekundowe buffy nie są kasowane przez śmierć; zachowują pozostały czas.",
    "Po śmierci gracz odradza się w Świątyni z pełnym HP i Maną. Brak wipe.",
] + LATEST_CHANGES


# ============================================================
# v0.30.35 - CHARACTER LEVEL EQ + RELATED QUEST FLOW AUDIT
# ============================================================
# `required_mastery` remains a historical numeric tier field for item identity,
# balance and save compatibility. Runtime equipment gating uses Character Level.
for _item_id, _item in ITEMS.items():
    if _item.get("type") != "armor":
        continue
    _req = max(1, min(CHARACTER_MAX_LEVEL, int(_item.get("required_mastery", 1) or 1)))
    _item["required_character_level"] = _req
    _desc = str(_item.get("desc") or "")
    _desc = _desc.replace("Biegłości aktywnej klasy ", "Levelu postaci ")
    _desc = _desc.replace("i Biegłości ", "i Levelu postaci ")
    _desc = _desc.replace("Tier: Biegłość ", "Tier EQ: Level ")
    _item["desc"] = _desc


def v03035_related_quest_flow_audit(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: v03035_related_quest_flow_audit")
v03035_related_quest_flow_audit = _sb410_bind(_sb410_mod_v410_equipment_audits.v03035_related_quest_flow_audit, globals())

V03035_RELATED_QUEST_FLOW_AUDIT = v03035_related_quest_flow_audit()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
def v03035_equipment_level_audit():
    errors = []
    armor = 0
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        armor += 1
        req = int(item.get("required_character_level", 0) or 0)
        expected = max(1, min(CHARACTER_MAX_LEVEL, int(item.get("required_mastery", 1) or 1)))
        if req != expected:
            errors.append(f"{item_id}: level={req} expected={expected}")
    if not hasattr(Session, "enforce_equipment_character_level"):
        errors.append("missing equipment level enforcement")
    return {"version":"0.30.35","armor_checked":armor,"error_count":len(errors),"errors":errors}

V03035_EQUIPMENT_LEVEL_AUDIT = v03035_equipment_level_audit()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["smierc"] = [
    "Po śmierci postać odradza się w Świątyni Odrodzenia z pełnym HP i Maną.",
    "Śmierć nie zabiera waluty, przedmiotów, EQ, EXP postaci, Biegłości, Soul XP, profesji ani poziomów narzędzi.",
    "Aktywne 30-sekundowe buffy zachowują pozostały czas działania. Licznik śmierci i system Nemesis mogą nadal rejestrować zdarzenie, ale nie są karą majątkową ani progresyjną.",
]
HELP_TOPICS["śmierć"] = HELP_TOPICS["smierc"]
HELP_TOPICS["death"] = HELP_TOPICS["smierc"]
HELP_TOPICS["eq"] = [
    "equipment / eq pokazuje założone wyposażenie oraz Broń Duszy; eq info pokazuje szczegóły, bonusy, sockety i aktywne sety.",
    "EQ jest bramkowane przez Level postaci 1-400. Przedmiot można posiadać wcześniej, ale nie można go założyć ani kupić przed wymaganym Levelem.",
    "Klasowe EQ nadal wymaga aktywnej właściwej klasy. Biegłość klasy odblokowuje skille i spelle, ale nie jest już wymogiem założenia EQ.",
    "Aktualne logiczne sloty: głowa, korpus, dłonie, nogi, stopy, talizman, pierścień, naszyjnik, kolczyki, naramienniki, pas, peleryna, karwasze i relikt. Pierścienie, talizmany i kolczyki mają po dwa fizyczne miejsca 1/2.",
    "Pierścienie, talizmany i kolczyki zakładają się automatycznie: zp, zt i zkol wybierają wolny slot; przy obu zajętych zastępują słabszy. Ręcznie: zp1/zp2, zt1/zt2, zkol1/zkol2.",
    "Materiałowe EQ z mobów obejmuje wszystkie obecne logiczne sloty i materiały od Żelaza do Eternium. Każdy wariant ma unikalną nazwę oraz unikalny profil statów w obrębie materiału i slotu.",
    "Przy logowaniu EQ ponad aktualny Level postaci jest automatycznie zdejmowane, ale pozostaje w inventory; nic nie przepada.",
]
HELP_TOPICS["ekwipunek"] = HELP_TOPICS["eq"]

HELP_TOPIC_ALIASES.update({
    "kolczyk": "kolczyki", "kolczyki": "kolczyki", "earring": "kolczyki", "earrings": "kolczyki",
    "materialy eq": "materialy_eq", "materiały eq": "materialy_eq",
})
HELP_TOPICS["materialy_eq"] = [
    "Materiałowe EQ z ciał występuje jako Żelazne, Stalowe, Mithrilowe, Adamantytowe, Kobaltowe, Runiczne, ze Smoczej Stali, Astralne, Pustki i Eternium.",
    "Każdy z 10 materiałów obejmuje wszystkie 15 logicznych slotów: głowę, korpus, dłonie, nogi, stopy, talizman, pierścień, naszyjnik, kolczyk, naramienniki, pas, pelerynę, karwasze i relikt.",
    "Każdy materiał i slot ma 24 warianty. Nazwy nie powtarzają się, a profile statów nie powtarzają się w obrębie tego samego materiału i slotu.",
    "EQ wymaga Levelu postaci, nie Biegłości klasy. Materiałowe przedmioty można zdobyć wcześniej i przechować, ale nie założyć przed wymaganym Levelem.",
    "Zwykły świat jest ograniczony do niższych materiałów; wysokie materiały zdobywa się głównie w Kryptach, Wieżach, Twierdzy i bojowych lochach.",
    "Krypta rozciąga progresję materiałów przez Level 1-400: Żelazo, Stal, Mithril, Adamantyt, Kobalt, Runiczny, Smocza Stal, Astral, Pustka i Eternium.",
]
HELP_TOPICS["klasy"] = [
    "Soulbound ma 14 klas. Level postaci 1-400 jest wspólną osią postaci, a każda klasa ma osobną Biegłość 1-400.",
    "Level postaci bramkuje EQ. Biegłość właściwej aktywnej klasy odblokowuje skille/spelle i rozwija się przez Class XP.",
    "Każda klasa ma własną Broń Duszy, role, skille/spelle oraz osobny sklep EQ. Użyj help <klasa> albo walk eq <klasa>.",
    "Multiclass zachowuje osobną Biegłość każdej klasy; wyłączenie klasy nie kasuje jej progresji ani nauczonych umiejętności.",
]
HELP_TOPICS["zakladanie_lootu"] = [
    "Gracz sam wybiera konkretny element EQ. Zwykłe sloty nie podmieniają się bez wskazania przedmiotu.",
    "Całe EQ jest bramkowane przez Level postaci 1-400. Biegłość klasy odblokowuje skille/spelle, a nie możliwość założenia EQ.",
    "Pierścienie, talizmany i kolczyki mają po dwa miejsca. zp, zt i zkol wybierają wolne albo słabsze miejsce automatycznie; zp1/zp2, zt1/zt2 i zkol1/zkol2 wymuszają konkretny slot.",
    "Aktualne logiczne sloty: głowa, korpus, dłonie, nogi, stopy, talizman, pierścień, naszyjnik, kolczyk, naramienniki, pas, peleryna, karwasze i relikt.",
    "Zmiana EQ podczas aktywnej walki jest zablokowana. Założonego EQ nie można sprzedać ani przekazać.",
]
HELP_TOPICS["sklepy"] = [
    "shop / sklep / list / lista pokazuje numerowaną ofertę aktualnego sprzedawcy; shop info <numer> pokazuje pełny opis i porównanie.",
    "Każda z 14 klas ma osobny sklep EQ. walk eq <klasa> prowadzi bezpośrednio do właściwej sali klasowej.",
    "Klasowe sklepy mają pełne 14 logicznych typów EQ, w tym kolczyki, naramienniki, pas, pelerynę, karwasze i relikt.",
    "Oferta Tieru zależy od Levelu postaci, a zakup klasowego EQ wymaga aktywnej właściwej klasy.",
    "sell all / sprzedaj wszystko sprzedaje wyłącznie niezałożone EQ; materiały, narzędzia, quest itemy i consumables są chronione.",
]
HELP_TOPICS["sety_klasowe"] = [
    "Każda z 14 klas ma linie EQ obejmujące wszystkie 14 logicznych typów wyposażenia, w tym kolczyki.",
    "Bonusy zestawów pozostają na progach 2/4/6/8 części; większa liczba dostępnych slotów daje wybór, a nie nowy automatyczny próg mocy.",
    "Level postaci bramkuje założenie EQ; aktywna klasa nadal jest wymagana dla klasowych części.",
]
HELP_TOPICS.setdefault("questy godzinne", []).append(
    "v0.30.35: wykonano pełny audit podobnych questów. Złamane ostrza, Pancerz do przetopu, Toksyczne gruczoły, Dzisiejszy połów, Próbki rudy, Drewno na naprawy, Zestaw dla uzdrowiciela i Nieumarli znów wstali mają działające źródła oraz postęp 0/x."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.35: EQ zależy od Levelu postaci; pełny audit collect/resource questów nie wykazał brakujących targetów ani martwych źródeł."
)
HELP_TOPICS.setdefault("kopalnia_200", []).append(
    "v0.30.35: przy każdym starcie serwera/deployu Kopalnia Głębinowa resetuje odblokowaną głębokość do poziomu 1 i zeruje postęp ściany. Górnictwo, Kilof, Sakwa, przedmioty i pozostała progresja nie są resetowane. Postać zapisana na piętrze Kopalni wraca do wejścia."
)
HELP_TOPICS.setdefault("gornictwo", []).append(
    "v0.30.35: deploy/restart procesu resetuje tylko przejście Kopalni Głębinowej: głębokość i ścianę. Level Górnictwa, Kilofa i zdobyty urobek zostają."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.35 - Quest Integrity + Lossless Death + Character Level EQ + Mine Reset"
LATEST_CHANGES = [
    "v0.30.35: naprawiono Złamane ostrza i przetestowano 0/6 -> 1/6 na świeżej bazie.",
    "v0.30.35: audit objął wszystkie collect, collect_category, collect_resource, collect_resource_set i craft_set; brak brakujących targetów i martwych źródeł.",
    "v0.30.35: śmierć jest całkowicie bezstratna dla waluty, przedmiotów, EQ i całej progresji; respawn daje pełne HP i Manę.",
    "v0.30.35: wymagania EQ są oparte na Levelu postaci 1-400; Biegłość klasy pozostaje systemem skilli/spelli.",
    "v0.30.35: przy logowaniu zbyt wysokie EQ jest zdejmowane do inventory, nigdy usuwane.",
    "v0.30.35: po starcie serwera/deployu Kopalnia Głębinowa wraca do poziomu 1 i zerowej ściany; Górnictwo, Kilof i loot pozostają bez zmian. Brak wipe postaci.",
] + LATEST_CHANGES


# ============================================================
# v0.30.36 - ONE CLASS, ONE EQ SHOP
# Każda z 14 klas ma własny sklep EQ w swojej osobnej sali klasowej.
# Stare sześć wspólnych punktów sprzedaży pozostaje wyłącznie hubami.
# ============================================================
CLASS_SHOP_ROOM_BY_CLASS_V03036 = {
    "Wojownik": "guild_warrior_chamber",
    "Berserker": "guild_berserker_chamber",
    "Łotrzyk": "guild_rogue_chamber",
    "Łowca": "guild_hunter_chamber",
    "Mnich": "guild_monk_chamber",
    "Strażnik": "guild_guardian_chamber",
    "Mag": "guild_mage_chamber",
    "Nekromanta": "guild_necromancer_chamber",
    "Kapłan": "guild_priest_chamber",
    "Czarownik": "guild_warlock_chamber",
    "Druid": "guild_druid_chamber",
    "Psionik": "guild_psion_chamber",
    "Mec": "guild_mec_chamber",
    "Inżynier": "guild_engineer_chamber",
}

CLASS_SHOP_SELLER_NAMES_V03036 = {
    "Wojownik": "Kwatermistrz Wojownika",
    "Berserker": "Kwatermistrz Berserkera",
    "Łotrzyk": "Kwatermistrz Łotrzyka",
    "Łowca": "Kwatermistrz Łowcy",
    "Mnich": "Kwatermistrz Mnicha",
    "Strażnik": "Kwatermistrz Strażnika",
    "Mag": "Kwatermistrz Maga",
    "Nekromanta": "Kwatermistrz Nekromanty",
    "Kapłan": "Kwatermistrz Kapłana",
    "Czarownik": "Kwatermistrz Czarownika",
    "Druid": "Kwatermistrz Druida",
    "Psionik": "Kwatermistrz Psionika",
    "Mec": "Kwatermistrz Meca",
    "Inżynier": "Kwatermistrz Inżyniera",
}

OLD_SHARED_CLASS_SHOP_ROOMS_V03036 = (
    "guild_martial_hall",
    "guild_shadow_gallery",
    "guild_body_hall",
    "guild_arcane_chamber",
    "guild_dark_chamber",
    "guild_sanctuary",
)
OLD_SHARED_CLASS_SHOP_SELLERS_V03036 = (
    "guild_quartermaster_martial",
    "guild_quartermaster_shadow",
    "guild_quartermaster_body",
    "guild_quartermaster_arcane",
    "guild_quartermaster_dark",
    "guild_quartermaster_sanctuary",
)


def apply_separate_class_shops_v03036(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: apply_separate_class_shops_v03036")
apply_separate_class_shops_v03036 = _sb410_bind(_sb410_mod_v410_equipment_audits.apply_separate_class_shops_v03036, globals())


# v0.31.2: dwie nowe sale klas technologicznych.
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_mec_chamber", {
    "name": "Hangar Meca", "zone": "Gildia Dusz",
    "desc": "Wzmocniony hangar z rdzeniami energetycznymi i stanowiskami ciężkiego pancerza.",
    "exits": {"south": "guild_martial_hall"},
})
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_engineer_chamber", {
    "name": "Warsztat Inżyniera", "zone": "Gildia Dusz",
    "desc": "Warsztat pełen narzędzi, działek testowych, skanerów i mechanicznych konstrukcji.",
    "exits": {"east": "guild_shadow_gallery"},
})
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_martial_hall", {}).setdefault("exits", {})["east"] = "guild_mec_chamber"
_catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (), "guild_shadow_gallery", {}).setdefault("exits", {})["west"] = "guild_engineer_chamber"
_catalog_mut.catalog_assign("guild_mec_chamber", 'NPCS', NPCS, ("teacher_mec", "room"))
_catalog_mut.catalog_assign("guild_engineer_chamber", 'NPCS', NPCS, ("teacher_engineer", "room"))

apply_separate_class_shops_v03036()


def class_shop_audit_v03036(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: class_shop_audit_v03036")
class_shop_audit_v03036 = _sb410_bind(_sb410_mod_v410_equipment_audits.class_shop_audit_v03036, globals())


CLASS_SHOP_AUDIT_V03036 = class_shop_audit_v03036()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
LATEST_CHANGES_TITLE = "Soulbound v0.30.36 - Separate Class EQ Shops"
LATEST_CHANGES = [
    "v0.30.36: każda z 14 klas ma własny, osobny sklep EQ w swojej sali klasowej.",
    "v0.30.36: sześć dawnych wspólnych punktów sprzedaży jest teraz wyłącznie hubami; nie sprzedają już mieszanego EQ dwóch klas.",
    "v0.30.36: walk eq <klasa>, sklep eq <klasa> i sklep <klasa> prowadzą do właściwego osobnego sklepu.",
    "v0.30.36: oferta nadal zależy od Levelu postaci, a zakup wymaga aktywnej właściwej klasy. Brak wipe.",
] + LATEST_CHANGES


# ============================================================
# v0.30.37 - COMPLETE EQUIPMENT SLOT / MATERIAL DROP PASS
# ============================================================
def refresh_material_stat_profiles_v03037(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: refresh_material_stat_profiles_v03037")
refresh_material_stat_profiles_v03037 = _sb410_bind(_sb410_mod_v410_equipment_audits.refresh_material_stat_profiles_v03037, globals())

refresh_material_stat_profiles_v03037()


def equipment_completeness_audit_v03037(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: equipment_completeness_audit_v03037")
equipment_completeness_audit_v03037 = _sb410_bind(_sb410_mod_v410_equipment_audits.equipment_completeness_audit_v03037, globals())

V03037_EQUIPMENT_COMPLETENESS_AUDIT = equipment_completeness_audit_v03037()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["kolczyki"] = [
    "Kolczyki są pełnoprawnym EQ. Możesz nosić dwa naraz: kolczyk 1 i kolczyk 2.",
    "zkol pokazuje posiadane kolczyki i automatycznie wybiera wolne/słabsze miejsce; zkol1 i zkol2 wymuszają konkretny slot.",
    "Kolczyki występują jako klasowe EQ, materiałowy drop z mobów oraz receptury Jubilerstwa. Mogą mieć gniazda na oszlifowane klejnoty.",
    "Materiałowe kolczyki istnieją dla Żelaza, Stali, Mithrilu, Adamantytu, Kobaltu, Runicznego metalu, Smoczej Stali, Astralu, Pustki i Eternium.",
]
HELP_TOPICS.setdefault("materialy_eq", []).append(
    "v0.30.37: materiałowe EQ obejmuje wszystkie 15 logicznych slotów, w tym naramienniki, pas, pelerynę, karwasze, relikt i nowe kolczyki. Każdy wariant ma niepowtarzalną nazwę i profil statów w obrębie materiału/slotu."
)
HELP_TOPICS.setdefault("jubilerstwo", []).append(
    "v0.30.37: Jubilerstwo tworzy też kolczyki. Jedna receptura daje jedną sztukę; do obu uszu potrzebujesz dwóch. Kolczyki obsługują gniazda klejnotów."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.37: pełny pass EQ: 15 logicznych slotów, dwa miejsca na kolczyki, pełne materiałowe dropy wszystkich slotów i audit braku powtórek nazw/profili statów."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.37 - Complete EQ Slots + Earrings + Unique Material Stats"
LATEST_CHANGES = [
    "v0.30.37: dodano kolczyki jako pełnoprawne dwa sloty użytkowe: kolczyk 1 i kolczyk 2, z automatycznym zkol oraz ręcznym zkol1/zkol2.",
    "v0.30.37: kolczyki są dostępne w klasowym EQ, materiale z mobów oraz Jubilerstwie i obsługują gniazda klejnotów.",
    "v0.30.37: materiałowe EQ z ciał obejmuje teraz wszystkie 15 logicznych slotów dla wszystkich 10 materiałów od Żelaza do Eternium.",
    "v0.30.37: 24 warianty każdego materiału/slotu mają niepowtarzalne profile statów; nazwy materiałowego EQ są globalnie unikalne.",
    "v0.30.37: sloty mają własne preferencje statów/właściwości, więc np. korpus, karwasze, peleryna i kolczyki nie są statystycznymi kopiami.",
    "v1.11.96: pełna siatka EQ ma 17 logicznych slotów; Bransoletka i Akcesorium są obecne w klasowym EQ, dropach materiałowych, Krypcie i Wieży Astralnej.",
    "v0.30.37: globalny audit wymaga unikalnej nazwy każdego EQ typu armor i rozróżnia pełne profile klasowych slotów.",
    "v0.30.37: po dodaniu kolczyków podstawowe sloty wearable są kompletne; Broń Duszy pozostaje osobnym systemem broni i nie jest dublowana zwykłym main-hand/off-hand.",
] + LATEST_CHANGES



# ============================================================
# v0.30.38 - BROKEN BLADES SPOKEN PROGRESS HOTFIX
# ============================================================
def broken_blades_spoken_progress_audit_v03038():
    return _audit_rules_v406.broken_blades_spoken_progress_audit_v03038(Session=Session, QUESTS=QUESTS)

BROKEN_BLADES_SPOKEN_PROGRESS_AUDIT_V03038 = broken_blades_spoken_progress_audit_v03038()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("questy godzinne", []).append(
    "v0.30.38: Złamane ostrza, Pancerz do przetopu i Toksyczne gruczoły podają postęp X/Y natychmiast przy każdym kwalifikującym się dropie; licznik nie jest już zależny od pośredniej warstwy kolekcji."
)
HELP_TOPICS.setdefault("questy", []).append(
    "v0.30.38: specjalne questy kill->item zawsze czytają aktualny licznik po zdobyciu przedmiotu, np. Złamane ostrza: 1 z 6."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.38 - Broken Blades Spoken Progress Hotfix"
LATEST_CHANGES = [
    "v0.30.38: Złamane ostrza podaje teraz 1/6, 2/6 itd. bezpośrednio po przyznaniu Uszkodzonego Ostrza.",
    "v0.30.38: ten sam bezpośredni kanał postępu obejmuje Pancerz do przetopu i Toksyczne gruczoły, aby podobny błąd nie wrócił.",
    "v0.30.38: Collection/Museum nadal zapisuje zdobyty przedmiot, ale nie może naliczyć tego samego dropu drugi raz.",
]



# ============================================================
# v0.30.39 - RACE HELP + PROFESSION CARRYOVER + ANY RIVER FISH
# ============================================================
def _install_race_help_v03039():
    HELP_TOPICS["rasy"] = [
        "Soulbound ma 14 ras. Każda ma dokładnie 50 bazowych punktów w pięciu głównych statystykach oraz własny pasyw rasowy.",
        "Rasa nie blokuje żadnej klasy. Polecane klasy są tylko wskazówką wynikającą ze statystyk i pasywu.",
        "Osobna pomoc: help człowiek, ogr, elf, krasnolud, ork, niziołek, mroczny elf, gnom, smoczy, troll, diablę, aasimar, driada.",
        "Każdy temat rasy podaje bazowe statystyki, opis/pasyw oraz polecane klasy.",
    ]
    stat_labels = ("Siła", "Zręczność", "Kondycja", "Inteligencja", "Siła Woli")
    for row in RACES:
        race_name, description, *values = row
        slug = "rasa_" + normalize_lookup_text(race_name).replace(" ", "_")
        stats_text = ", ".join(
            f"{label} {int(value)}" for label, value in zip(stat_labels, values)
        )
        rec = RACE_CLASS_RECOMMENDATIONS.get(race_name, {})
        classes = ", ".join(rec.get("classes", ())) or "brak szczególnych zaleceń"
        reason = str(rec.get("reason") or "każda klasa jest dozwolona")
        HELP_TOPICS[slug] = [
            f"Rasa: {race_name}.",
            f"Bazowe statystyki: {stats_text}. Razem: {sum(int(v) for v in values)} punktów.",
            str(description),
            f"Polecane klasy: {classes}.",
            f"Dlaczego: {reason}.",
            "Polecenie jest wskazówką, nie blokadą; możesz wybrać dowolną z 14 klas.",
        ]
        aliases = {
            race_name.lower(),
            normalize_lookup_text(race_name),
            f"rasa {race_name.lower()}",
            f"rasa {normalize_lookup_text(race_name)}",
        }
        for alias in aliases:
            HELP_TOPIC_ALIASES[alias] = slug

_install_race_help_v03039()

# Finalna pomoc śmierci: od v0.30.35 śmierć jest całkowicie bezstratna.
HELP_TOPICS["smierc"] = [
    "Po śmierci postać odradza się w Świątyni Odrodzenia z pełnym HP i Maną.",
    "Śmierć nie zabiera waluty, przedmiotów, EQ, EXP, Levelu postaci, Biegłości, Soul XP, profesji ani levelu narzędzi.",
    "Nie ma trwałości ani utraty wyposażenia. Aktywne buffy nie są kasowane karą śmierci i wygasają według własnego czasu.",
]

HELP_TOPICS.setdefault("wedkarstwo", []).extend([
    "v0.30.39: pule ryb są kumulacyjne. Awans Tieru Wędki dodaje nowe gatunki, ale nie usuwa wcześniej odblokowanych gatunków z tego samego habitatu.",
    "Specjalne łowisko może zwiększać szansę swoich typowych gatunków, lecz nie ustawia wcześniejszych odblokowanych ryb na 0 procent.",
])
HELP_TOPICS.setdefault("gornictwo", []).append(
    "v0.30.39: pule rud/minerałów i surowych klejnotów są kumulacyjne; późniejszy Tier Kilofa nie usuwa wcześniej odblokowanych zasobów."
)
HELP_TOPICS.setdefault("drwalstwo", []).append(
    "v0.30.39: pula drewna jest kumulacyjna; późniejszy Tier Piły nadal może dać każdy wcześniej odblokowany rodzaj drewna."
)
HELP_TOPICS.setdefault("zielarstwo", []).append(
    "v0.30.39: pula ziół jest kumulacyjna; późniejszy Tier Sierpa nadal może dać każde wcześniej odblokowane zioło."
)
HELP_TOPICS.setdefault("receptury", []).append(
    "v0.30.39: receptury nie mają górnego limitu Levelu/Tieru. Po odblokowaniu wcześniejsza receptura Kowalstwa, Gotowania, Alchemii lub Jubilerstwa pozostaje dostępna na późniejszych Tierach."
)
HELP_TOPICS.setdefault("gotowanie", []).append(
    "v0.30.39: Pieczona ryba rzeczna do zlecenia Marcela przyjmuje 2 dowolne ryby rzeczne, również dwa takie same gatunki, późne gatunki i rzadkie warianty gatunków rzecznych."
)
HELP_TOPICS.setdefault("questy", []).append(
    "v0.30.39: Zlecenie Marcela I nie wymaga już trzech starych gatunków. Każde 2 ryby rzeczne mogą zostać użyte do Pieczonej ryby rzecznej, a gotowa potrawa zalicza quest."
)


def profession_carryover_audit_v03039(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: profession_carryover_audit_v03039")
profession_carryover_audit_v03039 = _sb410_bind(_sb410_mod_v410_equipment_audits.profession_carryover_audit_v03039, globals())

PROFESSION_CARRYOVER_AUDIT_V03039 = profession_carryover_audit_v03039()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.39: dodano pełne pomoce 14 ras, kumulacyjny audit zasobów/profesji oraz dowolne ryby rzeczne w pierwszym zleceniu Gotowania Marcela."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.39 - Race HELP + Profession Carryover + Any River Fish"
LATEST_CHANGES = [
    "v0.30.39: help rasy ma indeks, a każda z 14 ras ma osobny help ze statystykami, pasywem i polecanymi klasami.",
    "v0.30.39: wszystkie pule zasobów są audytowane jako kumulacyjne przez 40 Tierów; starsze ryby, rudy, drewno, zioła i surowe klejnoty nie znikają po awansie.",
    "v0.30.39: specjalne łowiska tylko zwiększają wagi typowych gatunków; nie wycinają wcześniejszych odblokowanych ryb.",
    "v0.30.39: stare receptury Kowalstwa, Gotowania, Alchemii i Jubilerstwa nie mają górnego limitu i pozostają używalne na późniejszych Tierach.",
    "v0.30.39: Pieczona ryba rzeczna przyjmuje 2 dowolne ryby rzeczne, także dwa takie same gatunki, późne gatunki i rzadkie warianty.",
    "v0.30.39: help śmierć został zsynchronizowany z bezstratną śmiercią v0.30.35.",
]

# ============================================================
# v0.30.40 - COMPLETE EQ SHORTCUTS + OPTIONAL AUTO EQUIP
# ============================================================
def eq_shortcuts_auto_audit_v03040():
    return _audit_rules_v406.eq_shortcuts_auto_audit_v03040(COMMAND_ALIASES=COMMAND_ALIASES, Session=Session, CLASS_EQUIPMENT_SLOT_DEFS=CLASS_EQUIPMENT_SLOT_DEFS)

EQ_SHORTCUTS_AUTO_AUDIT_V03040 = eq_shortcuts_auto_audit_v03040()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["skroty_eq"] = [
    "Pełne skróty zakładania EQ: zhel hełm, zpan pancerz, ztar tarcza, zrek rękawice, znog nogawice, zbut buty.",
    "Biżuteria: ztal talizmany auto, zpier pierścienie auto, znasz naszyjnik, zkol kolczyki auto, zbra bransoletka, zakc akcesoria auto. Ręcznie nadal działają zt1/zt2, zp1/zp2 i zkol1/zkol2.",
    "Pozostałe: znar naramienniki, zpas pas, zpel peleryna, zkar karwasze, zrel relikt. Akcesoria używają dwóch slotów: Akcesorium 1 i Akcesorium 2.",
    "Stare skróty zh, zz, zr, zn, zb, zt, zp, zna itd. nadal działają.",
    "Samo wpisanie skrótu pokazuje numerowaną listę posiadanego EQ danego slotu; skrót + numer zakłada wybraną pozycję.",
    "eq auto, załóż auto, autoeq, eqauto albo zauto automatycznie wymienia dostępne części na indywidualnie najmocniejsze posiadane EQ.",
]
HELP_TOPIC_ALIASES.update({
    "skroty eq":"skroty_eq", "skróty eq":"skroty_eq", "eq skroty":"skroty_eq",
    "eq skróty":"skroty_eq", "auto eq":"skroty_eq", "autoeq":"skroty_eq",
})
HELP_TOPICS.setdefault("eq", []).extend([
    "Pełne czytelne skróty EQ obejmują także zbra dla bransoletki i zakc dla dwóch slotów akcesoriów. Stare skróty nadal działają.",
    "v0.30.40: eq auto / załóż auto / autoeq / zauto jednym poleceniem wymienia posiadane, dostępne EQ na indywidualnie najmocniejsze części. Auto respektuje Level postaci, aktywną klasę i liczbę posiadanych kopii.",
    "Auto EQ nie klonuje podwójnej biżuterii; do dwóch identycznych pierścieni, talizmanów, kolczyków lub akcesoriów potrzebujesz dwóch sztuk. Klejnoty z wymienianej biżuterii wracają do Szkatułki.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.40: komplet skrótów całego EQ oraz opcjonalny Auto Equip jednym poleceniem."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.40 - Complete EQ Shortcuts + Optional Auto Equip"
LATEST_CHANGES = [
    "v0.30.40: dodano czytelne skróty dla każdego logicznego slotu EQ; stare skróty zachowano bez zmian.",
    "v0.30.40: eq auto, załóż auto, autoeq, eqauto i zauto automatycznie dobierają najmocniejsze dostępne indywidualne części.",
    "v0.30.40: Auto EQ respektuje Level postaci, aktywne klasy, podwójne sloty i rzeczywistą liczbę posiadanych kopii.",
    "v0.30.40: przy automatycznej wymianie biżuterii osadzone klejnoty są bezpiecznie zwracane do Szkatułki Rzemieślniczej.",
    "v1.11.96: główna siatka EQ ma 17 logicznych slotów; Bracelet i Accessory są pełnoprawnym EQ, ale nie ułatwiają historycznych progów setów 2/4/6/8.",
]


# ============================================================
# v0.30.41 - UNIVERSAL EQUIPMENT SALVAGE
# ============================================================
def universal_salvage_audit_v03041():
    return _audit_rules_v406.universal_salvage_audit_v03041(ITEMS=ITEMS, V0925_SALVAGE_MATERIALS=V0925_SALVAGE_MATERIALS, v03041_salvage_material_key=v03041_salvage_material_key, SessionForgeGuildsMixin=SessionForgeGuildsMixin, Session=Session, normalize_lookup_text=normalize_lookup_text)

UNIVERSAL_SALVAGE_AUDIT_V03041 = universal_salvage_audit_v03041()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["rozkladanie_eq"] = [
    "rozloz / rozłóż działa u Haldora w Kuźni/Warsztacie Rzemieślniczym na każdym niezałożonym armor EQ: materiałowym, klasowym, bossowym, setowym, crafted, Krypta, Astral i innych liniach.",
    "Wpisz samo rozloz albo rozloz lista, aby dostać numerowaną listę wolnego EQ; potem rozloz <numer> albo rozloz <pełna nazwa>.",
    "Założona sztuka jest chroniona. Jeżeli masz dwie identyczne sztuki i jedna jest założona, wolną kopię nadal można rozłożyć.",
    "Materiał odzysku wynika z jawnego materiału przedmiotu, a dla pozostałego EQ z Levelu: 1-39 Żelazo, 40-79 Stal, 80-119 Mithril, 120-159 Adamantyt, 160-199 Kobalt, 200-239 Runiczny, 240-279 Smocza Stal, 280-319 Astral, 320-359 Pustka, 360-400 Eternium.",
    "Wyższy Level i rarity zwiększają liczbę odzyskanych fragmentów. Późne EQ daje także Esencję Przekucia i Pył Runiczny.",
    "Jeżeli rozkładasz ostatnią kopię EQ z osadzonymi runami, runy wracają do Szkatułki. Przekucie ostatniej kopii daje dodatkową Esencję Przekucia.",
    "Broń Duszy nie jest zwykłym przedmiotem inventory i nie podlega rozkładaniu.",
]
HELP_TOPIC_ALIASES.update({
    "rozkladanie": "rozkladanie_eq", "rozkładanie": "rozkladanie_eq",
    "rozloz eq": "rozkladanie_eq", "rozłóż eq": "rozkladanie_eq",
    "salvage": "rozkladanie_eq", "recycle eq": "rozkladanie_eq",
})
HELP_TOPICS.setdefault("eq", []).append(
    "v0.30.41: każde niezałożone armor EQ można rozłożyć u Haldora. Materiał odzysku odpowiada materiałowi lub Levelowi przedmiotu; runy z ostatniej kopii są zwracane."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.41: uniwersalne rozkładanie każdego niezałożonego EQ, numerowana lista i skalowany odzysk materiałów od Żelaza do Eternium."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.41 - Universal Equipment Salvage"
LATEST_CHANGES = [
    "v0.30.41: Haldor rozkłada każde niezałożone armor EQ, niezależnie od źródła: mob, boss, klasa, set, Krypta, Astral, Kowalstwo/Jubilerstwo i pozostałe linie.",
    "v0.30.41: rozloz / rozloz lista pokazuje numerowaną listę, a rozloz <numer> działa bez przepisywania długich nazw.",
    "v0.30.41: EQ bez jawnego materiału odzyskuje materiał według Levelu, więc endgameowe klasowe/bossowe EQ nie zamienia się już w Żelazo; Level 360-400 daje Eternium.",
    "v0.30.41: założone sztuki są chronione; wolna druga kopia identycznego EQ może być rozłożona.",
    "v0.30.41: przy rozłożeniu ostatniej kopii osadzone runy wracają do Szkatułki, a przekucie daje dodatkową Esencję Przekucia.",
]

# ============================================================
# v0.30.42 - BLACKSMITH EQUIPMENT UPGRADES +1..+10
# ============================================================
def equipment_upgrade_audit_v03042():
    return _audit_rules_v406.equipment_upgrade_audit_v03042(ITEMS=ITEMS, V03042_EQ_UPGRADE_MAX=V03042_EQ_UPGRADE_MAX, v03042_upgrade_required_smithing=v03042_upgrade_required_smithing, v03042_upgrade_material_cost=v03042_upgrade_material_cost, CHARACTER_MAX_LEVEL=CHARACTER_MAX_LEVEL, v03041_salvage_material_key=v03041_salvage_material_key, V0925_SALVAGE_MATERIALS=V0925_SALVAGE_MATERIALS, COMMAND_ALIASES=COMMAND_ALIASES, Session=Session)

EQUIPMENT_UPGRADE_AUDIT_V03042 = equipment_upgrade_audit_v03042()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["ulepszanie_eq"] = [
    "Ulepszanie EQ jest częścią Kowalstwa i wykonuje je Haldor w Kuźni/Warsztacie Rzemieślniczym.",
    "Komendy: ulepsz / ulepsz lista pokazuje numerowane EQ; ulepsz <numer> albo ulepsz <pełna nazwa> podnosi wybraną część o jeden poziom.",
    "Każde armor EQ może być ulepszone od +1 do +10: materiałowe, klasowe, bossowe, setowe, crafted, Krypta, Astral, biżuteria, relikty i pozostałe linie. Broń Duszy pozostaje osobnym systemem.",
    "Ulepszanie nie ma szansy niepowodzenia, nie niszczy przedmiotu i nie cofa poprzednich ulepszeń.",
    "Każdy poziom zwiększa realną obronę części; co dwa poziomy ulepszenia rośnie także jej główna statystyka. Główna statystyka jest dobierana z faktycznych bonusów przedmiotu.",
    "Wymagany level Kowalstwa zależy od Levelu EQ i poziomu ulepszenia; Młot Rzemieślniczy musi mieć odpowiadający Tier.",
    "Kosztem są fragmenty właściwego materiału z rozkładania EQ: Żelazo, Stal, Mithril, Adamantyt, Kobalt, Runiczny, Smocza Stal, Astral, Pustka albo Eternium.",
    "Ulepszanie rozwija Kowalstwo oraz Młot Rzemieślniczy i daje również Character XP przez zwykły system profesji.",
    "eq i eq info pokazują poziom ulepszenia, a eq auto uwzględnia ulepszenie przy wyborze lepszej części.",
]
HELP_TOPIC_ALIASES.update({
    "ulepszanie": "ulepszanie_eq", "ulepszanie eq": "ulepszanie_eq",
    "upgrade eq": "ulepszanie_eq", "upgrade": "ulepszanie_eq",
})
HELP_TOPICS.setdefault("kowalstwo", []).append(
    "v0.30.42: Haldor ulepsza każde armor EQ od +1 do +10. Koszt to fragment właściwego materiału z rozkładania; wymagane jest Kowalstwo i odpowiedni Tier Młota. Brak szansy na zniszczenie."
)
HELP_TOPICS.setdefault("eq", []).append(
    "v0.30.42: każde armor EQ można ulepszać u Haldora do +10. eq/eq info i eq auto uwzględniają poziom ulepszenia."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.42: pełne ulepszanie każdego EQ w Kowalstwie, +1 do +10, z kosztem fragmentów z salvage i bez ryzyka zniszczenia."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.42 - Blacksmith Equipment Upgrades"
LATEST_CHANGES = [
    "v0.30.42: Haldor może ulepszyć każde armor EQ od +1 do +10, niezależnie od źródła przedmiotu.",
    "v0.30.42: ulepsz / ulepsz lista daje numerowaną obsługę NVDA; ulepsz <numer> lub <pełna nazwa> wykonuje kolejny poziom.",
    "v0.30.42: ulepszenie zwiększa obronę, a co dwa poziomy główną statystykę przedmiotu; efekt działa w realnych obliczeniach walki.",
    "v0.30.42: wymagania zależą od Levelu EQ, Kowalstwa i Tieru Młota Rzemieślniczego. Brak faila, zniszczenia i cofnięcia.",
    "v0.30.42: koszt wykorzystuje fragment odpowiadającego materiału z systemu rozkładania EQ, łącząc salvage z Kowalstwem.",
    "v0.30.42: eq, eq info oraz eq auto uwzględniają poziomy ulepszeń.",
]


# ============================================================
# v0.30.55 - FULL GAME / COMMANDS / HELP AUDIT
# ============================================================
# Final truth layer for the current release. It intentionally runs after every
# historical HELP/audit patch above, so stale older release text cannot win.

# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.

HELP_TOPIC_ALIASES.update({
    "tailoring": "krawiectwo", "sewing": "krawiectwo",
    "leatherworking": "garbarstwo", "tanning": "garbarstwo",
    "carpentry": "stolarstwo", "woodworking": "stolarstwo",
    "enchanting": "zaklinanie", "enchant": "zaklinanie",
    "crafting mastery": "craftmastery", "craftingmastery": "craftmastery",
    "craft quality": "jakosccraftu", "craftquality": "jakosccraftu",
    "critical craft": "krytycznycraft", "criticalcraft": "krytycznycraft",
    "collection 2": "collection2", "collection2": "collection2",
    "completion": "completion2", "completion percent": "completion2",
    "leaderboards": "leaderboards2", "rankings": "leaderboards2",
    "mentor rankings": "mentor2", "mentor graduation": "mentor2",
    "housing 2": "housing2", "transport 2": "transport2",
    "death recap": "recaps", "combat recap": "recaps",
    "loot history": "loothistory2", "nvda": "accessibility_presets",
    "channels": "social2", "mail": "social2", "lfg": "social2",
})

HELP_TOPICS.update({
    "krawiectwo": [
        "Krawiectwo / Tailoring 1-400. NPC: Krawcowa Lysa, Pracownia Krawiecka.",
        "Komendy PL/EN: krawiectwo / tailoring; szyj <receptura> / sew <recipe>; szyj lista / sew list.",
        "Tworzy tkaniny, szaty, płaszcze i inne gotowe EQ. Gotowe EQ korzysta z jakości craftu i Crafting Mastery.",
    ],
    "garbarstwo": [
        "Garbarstwo / Leatherworking 1-400. NPC: Kaletnik Soren.",
        "Komendy PL/EN: garbarstwo / leatherworking; garbuj <receptura> / tan <recipe>; garbuj lista / tan list.",
        "Przerabia skóry bestii na materiały i lekkie EQ; gotowe EQ może otrzymać jakość oraz krytyczny affix.",
    ],
    "stolarstwo": [
        "Stolarstwo / Carpentry 1-400. NPC: Cieśla Edric.",
        "Komendy PL/EN: stolarstwo / carpentry; stolarka <receptura> / woodcraft <recipe>; stolarka lista / woodcraft list.",
        "Obrabia drewno i tworzy komponenty, totemy oraz elementy powiązane z housingiem.",
    ],
    "zaklinanie": [
        "Zaklinanie / Enchanting 1-400. Warsztat: Komnata Arkanów Gildii Dusz.",
        "Komendy PL/EN: zaklinanie / enchanting; zaklinaj <slot> <typ> / enchantitem <slot> <type>; enchants.",
        "Typy statystyk można podać po polsku lub angielsku: sila/strength, zrecznosc/dexterity, kondycja/constitution, inteligencja/intelligence, wola/will, hp/health, mana.",
        "Jedno trwałe zaklęcie na slot; nowe zaklęcie zastępuje poprzednie.",
    ],
    "jakosccraftu": [
        "Craft Quality / Jakość craftu: gotowe EQ może być Zwykłe, Dobre, Doskonałe, Mistrzowskie lub Legendarne.",
        "Wyższa jakość realnie zwiększa moc/statystyki gotowego EQ. Materiały i consumable pozostają kompatybilne ze starymi recepturami i stackowaniem.",
    ],
    "krytycznycraft": [
        "Critical Craft / Krytyczny craft: mała szansa na dodatkowy affix albo mocniejszy wynik.",
        "Szansa rośnie z levelem właściwej profesji i Crafting Mastery, ale ma bezpieczny limit.",
    ],
    "craftmastery": [
        "Crafting Mastery 1-100 jest osobne od levelu profesji i narzędzia i rośnie przez realne wykonywanie receptur w danej kategorii.",
        "Komendy: craftmastery [filtr] / craftingmastery [filter]. Mastery wpływa na jakość i krytyczny craft.",
    ],
    "collection2": [
        "Collection Codex 2.0: collection2; collection2 braki / collection2 missing.",
        "Pokazuje ryby, rudy, sety, bossów, rare moby i sekrety oraz brakujące wpisy.",
    ],
    "completion2": [
        "Completion % 2.0: completion. Pokazuje osobno świat, profesje, bossów, kolekcje i procent całej gry.",
    ],
    "leaderboards2": [
        "Leaderboards 2.0: leaderboards / leaderboard / rankings.",
        "Kategorie: professions, bosses, collection, records, guilds, mentor/mentorzy; starsze rankingi lochów pozostają dostępne.",
    ],
    "mentor2": [
        "Mentor 2.0: relacja mentor-uczeń nagradza realną wspólną aktywność. mentor ranking pokazuje ranking mentorów.",
        "mentor graduate / mentor graduation kończy naukę po spełnieniu progów i przyznaje nagrodę obu osobom.",
    ],
    "housing2": [
        "Housing 2.0: house status, house rooms, house room add <nazwa>, house station <roomN> <typ>, house gallery.",
        "Starsze funkcje domu nadal działają: name, decor, upgrade, chest, store, take, trophies.",
    ],
    "transport2": [
        "Transport 2.0: transport. Sieć obejmuje łodzie, wozy, windy i portale, z zachowaniem istniejących odblokowań świata.",
    ],
    "recaps": [
        "Death Recap: deathrecap / deathsummary. Pokazuje krótkie podsumowanie przyczyny ostatniej śmierci, jeśli dane są dostępne.",
        "Combat Recap: combatrecap / combatsummary. Pokazuje czas walki, obrażenia, leczenie, krytyki i użyte skille z ostatniej walki.",
    ],
    "loothistory2": [
        "Loot History 2.0: loothistory [filtr] lub drophistory [filtr]. Filtr może dopasować nazwę, rarity, źródło albo strefę.",
    ],
    "accessibility_presets": [
        "Presety NVDA: nvda <combat|social|system|all> <concise|normal|full>.",
        "Ustawienia są rozdzielone dla walki, komunikacji społecznej i komunikatów systemowych.",
    ],
    "social2": [
        "Social Suite 2.0: ignore/unignore, friends/friend, afk, who/whois, mail, board, lfg, gossip/newbie/trade, channels.",
        "Kanały można włączać i wyciszać przez gossip/newbie/trade on/off. channels pokazuje stan i historię.",
        "Mail obsługuje list/send/read/delete; board list/post/delete; LFG obsługuje crypt, boss, profession, list i off.",
    ],
})

# Current category summaries: append only current truth, without deleting useful old help.
for _topic, _line in {
    "profesje": "v0.30.55: nowe rzemiosła mają pełne komendy PL/EN: Tailoring, Leatherworking, Carpentry i Enchanting; Crafting Mastery oraz jakość craftu działają na gotowym EQ.",
    "rzemioslo": "v0.30.55: help krawiectwo/tailoring, garbarstwo/leatherworking, stolarstwo/carpentry, zaklinanie/enchanting oraz help craftmastery opisują aktualny Crafting 2.0.",
    "gracze": "v0.30.55: Social Suite obejmuje ignore, friends, AFK, WHO 2.0, whois, mail, board, LFG, kanały i mentoring.",
    "eq": "v0.30.55: crafted EQ może mieć jakość, krytyczny affix, upgrade +1..+10, runy/sockety oraz trwałe zaklęcie slotu.",
}.items():
    HELP_TOPICS.setdefault(_topic, [])
    if _line not in HELP_TOPICS[_topic]:
        HELP_TOPICS[_topic].append(_line)

# Keep `help komendy` current without rewriting the large historical list.
_old_help_commands_v03055 = Session.help_commands
def _help_commands_v03055(self):
    rows = list(_old_help_commands_v03055(self))
    extras = [
        "tailoring / krawiectwo; sew / szyj <recipe> - Krawiectwo 1-600",
        "leatherworking / garbarstwo; tan / garbuj <recipe> - Garbarstwo 1-600",
        "carpentry / stolarstwo; woodcraft / stolarka <recipe> - Stolarstwo 1-600",
        "enchanting / zaklinanie; enchantitem / zaklinaj <slot> <type>; enchants - Zaklinanie 1-600",
        "craftmastery / craftingmastery [filter] - mastery kategorii craftu 1-100",
        "collection2 [missing/braki]; completion - Collection/Completion 2.0",
        "leaderboards / leaderboard / rankings [professions|bosses|collection|records|guilds|mentor] - rankingi 2.0",
        "deathrecap / deathsummary; combatrecap / combatsummary - podsumowania śmierci i walki",
        "loothistory [filter] - Loot History 2.0",
        "nvda <combat|social|system|all> <concise|normal|full> - presety dostępności",
        "ignore/unignore, friends/friend, afk, whois, mail, board, lfg - systemy społeczne 2.0",
        "house rooms / room add / station / gallery - Housing 2.0; transport - system transportu",
    ]
    for row in extras:
        if row not in rows:
            rows.append(row)
    return rows
Session.help_commands = _help_commands_v03055


def full_game_audit_v03055(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: full_game_audit_v03055")
full_game_audit_v03055 = _sb410_bind(_sb410_mod_v410_release_audits.full_game_audit_v03055, globals())

FULL_GAME_AUDIT_V03055 = full_game_audit_v03055()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["audyt_v03055"] = [
    "v0.30.55 wykonuje finalny audyt świata, przejść, klas/skilli, itemów, mobów, questów, receptur, profesji, komend PL/EN i HELP.",
    "Błędy integralności zatrzymują start serwera zamiast pozwalać wdrożyć uszkodzony build.",
    "Raport wydania AUDYT_CALEJ_GRY_v0.30.55_PL.txt zawiera wyniki audytu oraz ostrzeżenia nieblokujące.",
]
HELP_TOPIC_ALIASES.update({"audyt gry":"audyt_v03055", "game audit":"audyt_v03055", "audit":"audyt_v03055"})

LATEST_CHANGES_TITLE = "Soulbound v0.30.55 - Full Game Audit + English Commands + HELP Refresh"
LATEST_CHANGES = [
    "Pełny audyt całej gry: świat/przejścia, klasy/skille, przedmioty, moby, questy, receptury, profesje, komendy i HELP.",
    "Dodano brakujące angielskie komendy dla nowych rzemiosł: tailoring/sew, leatherworking/tan, carpentry/woodcraft, enchanting/enchantitem.",
    "Zaklinanie akceptuje teraz również angielskie nazwy statystyk: strength, dexterity, constitution, intelligence, will, health i mana.",
    "HELP został odświeżony dla systemów v0.30.50-v0.30.54, w tym Social, Mentor, Housing, Collection/Completion, rankingi, recapy, NVDA i Crafting 2.0.",
    "help komendy zawiera aktualne komendy nowych systemów i ich polsko-angielskie odpowiedniki.",
]




# v0.31.2: nowe helpy rasy i klas technologicznych.
def _install_v0310_tech_help():
    HELP_TOPICS["cyborg"] = [
        "Cyborg: 14. rasa Soulbound. Bazowe statystyki: Siła 10, Zręczność 11, Kondycja 12, Inteligencja 10, Siła Woli 7.",
        "Pasyw: redukcja wszystkich otrzymywanych obrażeń. Polecane klasy: Mec, Inżynier, Strażnik, Łowca.",
        "Cyborg dostaje Moogle Board na starcie. To jeden slot Board; moduł może być używany również przez Inżyniera.",
    ]
    HELP_TOPICS["mec"] = [
        "Mec: technologiczna klasa fizyczna 1-400. Broń Duszy: Rdzeń Meca.",
        "Ma pełną siatkę 123 skilli: 3 na progu 1 i co 10 aż do 400. Wczesne umiejętności obejmują Fire Beam, Ice Beam, Bolt Beam, TekShield, Gravity Bomb, TekMissile, Heal Force i Overdrive.",
        "Styl: ciężki pancerz, bariery, salwy rdzenia i przeciążenia systemów.",
        "Moogle Board jest startowym Boardem Cyborga i może być używany także przy Inżynierze; bonus skaluje się zgodnie z istniejącą progresją Boarda.",
    ]
    HELP_TOPICS["inzynier"] = HELP_TOPICS["inżynier"] = [
        "Inżynier: technologiczna klasa fizyczna 1-400. Broń Duszy: Omni-Narzędzie.",
        "Wczesne umiejętności inspirowane Engineerem UOSSMUD obejmują Auto Crossbow, Mako Gun, Bio Blaster, Scanner, Flash, Debilitator, Drill, Napalm, Launcher, Noise Blaster, Chainsaw, Mega Bomb i Air Anchor.",
        "Styl: Zręczność, narzędzia, materiały wybuchowe, skanowanie i urządzenia taktyczne.",
    ]
    HELP_TOPIC_ALIASES["engineer"] = "inżynier"
    HELP_TOPIC_ALIASES["cyborg"] = "cyborg"
    HELP_TOPIC_ALIASES["mech"] = "mec"
_install_v0310_tech_help()

# ============================================================
# v0.35.3 - FULL GAME PRE-DEPLOY INTEGRITY + POLISH GATE
# Covers every registered runtime content domain and blocks startup on broken
# cross-references, technical IDs in player-facing item names, stale generated
# numeric item descriptions, invalid quest/item/NPC/shop links, skill-name
# regressions, mojibake, or missing help aliases.
# ============================================================
def full_game_predeploy_audit_v0336(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: full_game_predeploy_audit_v0336")
full_game_predeploy_audit_v0336 = _sb410_bind(_sb410_mod_v410_release_audits.full_game_predeploy_audit_v0336, globals())

# v0.34.4: the exhaustive audit must run only after *all* runtime modules are
# loaded. server.py executes it after the module loop when SOULBOUND_FULL_AUDIT=1.
# Keeping a placeholder here preserves compatibility for code that inspects the symbol.
FULL_GAME_PREDEPLOY_AUDIT_V0336={
    'version':'0.35.6','deferred_until_runtime_complete':True,'error_count':0,'warning_count':0,
    'errors':[],'warnings':[],
    'reason':'Final pre-deploy audit is executed by server.py after every runtime module has loaded.'
}


# ============================================================
# v0.35.3 - DEEP CODE INSPECTION + RARE PATH STABILITY
# ============================================================
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.3: Deep Code Inspection — naprawione rzadkie ścieżki Meca/admina, aktywowane nowsze Social/Salvage oraz zabezpieczone taski tła."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.3 - Deep Code Inspection + Rare Path Stability"
LATEST_CHANGES = [
    "Pełna statyczna inspekcja call-graphu Session/Database/World/MudServer/Character oraz test MRO mixinów.",
    "Naprawiono Mec Intercept System: kontratak używa spell_power zamiast nieistniejącego magic_power.",
    "Naprawiono admin goto po nazwie lokacji: używa istniejącego find_room zamiast nieistniejącego resolve_room_query.",
    "Nowsze Social Expansion jest aktywne dla who/tell/kanałów: ignore, AFK, historia kanałów, antyspam i rozszerzone WHO.",
    "Nowszy Salvage 3.0 jest aktywny i nadal deleguje klasyczne rozkładanie armor EQ do stabilnej warstwy bazowej.",
    "Odpoczynek, wędrówka mobów i event x2 EXP nie giną już bezpowrotnie po pojedynczym błędzie taska w tle.",
    "Dodano Code Integrity Gate, który blokuje release przy wywołaniu nieistniejącej metody lub ponownym zasłonięciu nowszego mixinu.",
]


# ============================================================
# v0.35.5 - PARTY TEMPLE TELEPORT + SHARED SOUL SHARDS
# ============================================================
def party_temple_shard_audit_v0355():
    errors = []
    metrics = {}
    try:
        _core_path = _ROOT / "player/session_mixins/session_runtime_state.py"
        _combat_path = _ROOT / "player/session_mixins/combat_rewards.py"
        _core = _core_path.read_text(encoding="utf-8")
        _combat = _combat_path.read_text(encoding="utf-8")
        if "_teleport_self_to_temple_v0354" not in _core:
            errors.append("brak helpera teleportu pojedynczego członka")
        if "same_room=origin_room" not in _core:
            errors.append("teleport świątyni nie ogranicza drużyny do wspólnej lokacji")
        # v0.35.9 rozszerzyło zasadę z samych Odłamków na wszystkie zwykłe dropy.
        # Historyczny gate v0.35.5 sprawdza więc, czy nadal istnieje aktywny
        # mechanizm wspólnych odbiorców, niezależnie od jego nowszej nazwy.
        if "drop_recipients = party_drop_recipients_v0359(item_id, recipients)" not in _combat:
            errors.append("wspólne dropy drużyny nie używają aktywnego helpera odbiorców")
        if "party_drop_recipients_v0359" not in globals():
            errors.append("brak aktywnego helpera wspólnych dropów po rozszerzeniu v0.35.9")
        metrics["teleport_helper"] = hasattr(Session, "_teleport_self_to_temple_v0354")
        metrics["teleport_command"] = hasattr(Session, "teleport_to_temple_command")
        if not metrics["teleport_helper"] or not metrics["teleport_command"]:
            errors.append("brak aktywnej metody teleportu v0.35.5")
    except Exception as exc:
        errors.append(f"audit exception: {exc!r}")
    return {"version":"0.35.5","error_count":len(errors),"errors":errors,"metrics":metrics}

PARTY_TEMPLE_SHARD_AUDIT_V0355 = party_temple_shard_audit_v0355()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("party", []).extend([
    "Teleport do Świątyni przez / albo Enter obejmuje tylko członków drużyny stojących razem w tej samej lokacji; członkowie drużyny gdzie indziej pozostają na miejscu.",
    "Odłamek Duszy jest wspólnym dropem drużynowym: gdy jego rzut się powiedzie, każdy obecny w tej samej lokacji członek drużyny dostaje własny Odłamek.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.5: teleport do Świątyni oraz wspólne Odłamki Duszy obejmują tylko członków drużyny stojących razem w tej samej lokacji."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.5 - Party Temple Teleport + Shared Soul Shards"
LATEST_CHANGES = [
    "Teleport do Świątyni przez / lub Enter obejmuje tylko członków aktualnej drużyny stojących razem w tej samej lokacji co osoba uruchamiająca teleport.",
    "Teleport zatrzymuje prowadzenie, odpoczynek, auto-rzemiosła i aktywną walkę tylko u członków faktycznie przenoszonych z tej samej lokacji.",
    "Odłamki Duszy z dropu przeciwników są teraz współdzielone: po udanym rzucie każdy członek drużyny obecny przy walce dostaje po 1 Odłamku.",
    "Od v0.35.9 ta sama lokalna zasada drużynowa została rozszerzona na wszystkie zwykłe dropy z mobów.",
]


# v0.35.6 - SALVAGE WSZYSTKO
def salvage_all_audit_v0356():
    errors=[]
    metrics={}
    try:
        import inspect
        source=inspect.getsource(SessionCraftingExpansionV03114Mixin.salvage_equipment_v0925)
        bulk=inspect.getsource(SessionCraftingExpansionV03114Mixin.salvage_all_v0356)
        metrics["has_bulk_command"] = '"wszystko"' in source and 'salvage_all_v0356' in source
        metrics["protects_equipped"] = (
            ('free_equipment_quantity' in bulk and 'equipped_quantity_of_item' in bulk)
            or ('inventory_qty_v0717' in bulk and 'equipped_qty_v0717' in bulk and 'free_qty = max(0, total - equipped)' in bulk)
        )
        metrics["protects_moogle"] = 'moogle_board' in bulk
        metrics["extended_salvage"] = 'SALVAGE3_V03114' in bulk
        metrics["aggregated_output"] = 'SALVAGE WSZYSTKO' in bulk
        for key,value in metrics.items():
            if not value: errors.append(f"salvage wszystko audit failed: {key}")
    except Exception as exc:
        errors.append(f"salvage wszystko audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.6","error_count":len(errors),"errors":errors,"metrics":metrics}

SALVAGE_ALL_AUDIT_V0356 = salvage_all_audit_v0356()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
LATEST_CHANGES_TITLE = "Soulbound v0.35.6 - Salvage Wszystko"
LATEST_CHANGES = [
    "v0.35.6: dodano salvage wszystko / rozloz wszystko — hurtowe rozkładanie wszystkich wolnych przedmiotów obsługiwanych przez Salvage.",
    "Założone EQ jest zawsze pomijane; startowy Moogle Board jest chroniony przed przypadkowym hurtowym rozłożeniem.",
    "Hurtowy Salvage agreguje raport odzyskanych materiałów, run i klejnotów, żeby nie spamować NVDA setkami komunikatów.",
]


# v0.35.7 - BULK SMELTING + INGOT-BASED SMITHING
def bulk_smelting_ingot_smithing_audit_v0357(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: bulk_smelting_ingot_smithing_audit_v0357")
bulk_smelting_ingot_smithing_audit_v0357 = _sb410_bind(_sb410_mod_v410_equipment_audits.bulk_smelting_ingot_smithing_audit_v0357, globals())

BULK_SMELTING_INGOT_SMITHING_AUDIT_V0357 = bulk_smelting_ingot_smithing_audit_v0357()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("kowalstwo", []).extend([
    "v0.35.7: metalowe EQ z normalnej linii Kowalstwa powstaje ze sztabek. Ruda jest najpierw przetapiana, a dopiero sztabki są zużywane do kucia EQ.",
    "przetop wszystko wykonuje cały dostępny przetop jako jedną akcję: rudy, Stalowe Płyty i zgodne materiały Salvage. XP Kowalstwa i Młota jest sumowane i przyznawane wspólnie raz.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.7: przetop wszystko jest jedną hurtową akcją ze wspólnym XP; standardowe kowalskie EQ wymaga sztabek zamiast surowej rudy."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.7 - Bulk Smelting + Ingot-Based Smithing"
LATEST_CHANGES = [
    "v0.35.7: przetop wszystko zużywa w jednej akcji wszystkie dostępne rudy, Stalowe Płyty oraz zgodne materiały Salvage, do których postać ma wymagany poziom Kowalstwa i Tier Młota.",
    "Cały hurtowy przetop ma jeden czas akcji i jeden wspólny grant XP Kowalstwa oraz Młota zamiast osobnego XP za każdą sztukę.",
    "Normalne kowalskie EQ nie może być już tworzone bezpośrednio z rudy: metal najpierw przetapia się na sztabki, a receptury EQ zużywają odpowiednie sztabki.",
    "Poprawiono starsze talizmany Kowalstwa 100-200 oraz linię progresji 220-400, które wcześniej omijały sztabki.",
]


# v0.35.8 - GLOBAL NO-PVP PLAYER SAFETY
def no_pvp_player_safety_audit_v0358():
    errors=[]
    metrics={}
    try:
        import inspect
        helper_source=inspect.getsource(SessionSkillsCombatMixin.reject_player_attack)
        target_source=inspect.getsource(SessionSkillsCombatMixin.protected_player_target)
        attack_source=inspect.getsource(SessionSkillsCombatMixin.attack)
        skill_target_source=inspect.getsource(SessionSkillsCombatMixin.skill_combat_target)
        skill_source=inspect.getsource(SessionSkillsCombatMixin.use_class_skill)
        metrics["explicit_player_guard"] = "PvP jest wyłączone" in helper_source
        metrics["same_room_player_lookup"] = "self.server.sessions" in target_source and "room_id" in target_source
        metrics["attack_guard_before_activity"] = attack_source.find("reject_player_attack") < attack_source.find("stop_auto_fishing")
        metrics["skill_target_guard"] = "reject_player_attack" in skill_target_source
        metrics["aoe_mobs_only"] = "self.server.world.room_mobs(self.character.room_id)" in skill_source
        metrics["no_player_damage_assignment"] = (
            "session.current_hp -=" not in skill_source
            and "target_session.current_hp -=" not in skill_source
        )
        for key,value in metrics.items():
            if not value:
                errors.append(f"no-PvP audit failed: {key}")
    except Exception as exc:
        errors.append(f"no-PvP audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.8","error_count":len(errors),"errors":errors,"metrics":metrics}

NO_PVP_PLAYER_SAFETY_AUDIT_V0358 = no_pvp_player_safety_audit_v0358()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("walka", []).extend([
    "v0.35.8: PvP jest całkowicie wyłączone. Gracze nie mogą atakować, ranić ani zabijać innych graczy ani własnej postaci.",
    "atakuj/k oraz ofensywne skille odrzucają nazwę gracza jako cel. AoE obejmuje wyłącznie żywe moby w lokacji.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.8: globalna blokada PvP chroni wszystkich graczy przed atakami, ofensywnymi skillami i friendly fire."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.8 - PvP Protection + Player Safety"
LATEST_CHANGES = [
    "v0.35.8: PvP jest globalnie wyłączone — gracze nie mogą atakować, ranić ani zabijać innych graczy ani własnej postaci.",
    "atakuj <gracz> / k <gracz> zatrzymuje się natychmiast i informuje, że PvP jest wyłączone; nie przerywa przy tym profesji automatycznych.",
    "Ofensywne skille nie mogą wybrać gracza jako celu, a AoE nadal działa wyłącznie na moby w bieżącej lokacji.",
    "Dodano stały audit no-PvP, aby przyszłe zmiany systemu walki nie przywróciły przypadkowego friendly fire.",
]

# v0.35.9 - ALL LOCAL PARTY MOB DROPS SHARED
def all_party_mob_drops_shared_audit_v0359():
    errors=[]
    metrics={}
    try:
        import inspect
        helper_source=inspect.getsource(party_drop_recipients_v0359)
        combat_source=inspect.getsource(SessionSkillsCombatMixin.mob_defeated)
        wrapped = getattr(SessionSkillsCombatMixin.mob_defeated, "__wrapped__", None)
        if wrapped is not None:
            combat_source += "\n" + inspect.getsource(wrapped)
        metrics["helper_returns_all"] = "return list(recipients or [])" in helper_source
        # v1.13.29: authored drop chance may be transformed by a rank/source
        # helper before the roll. The party contract is unchanged: exactly one
        # random roll happens before recipients are expanded, so all eligible
        # local party members share the same success/failure result.
        _drop_loop = 'for item_id, chance in template["drops"].items()'
        _effective_helper = "authored_drop_chance_v11329("
        _effective_roll = "if random.random() <= _effective_drop_chance_v11329:"
        _recipient_expand = "drop_recipients = party_drop_recipients_v0359(item_id, recipients)"
        _loop_pos = combat_source.find(_drop_loop)
        _helper_pos = combat_source.find(_effective_helper, _loop_pos)
        _roll_pos = combat_source.find(_effective_roll, _helper_pos)
        _recipients_pos = combat_source.find(_recipient_expand, _roll_pos)
        metrics["single_roll"] = (
            _loop_pos >= 0
            and _helper_pos > _loop_pos
            and _roll_pos > _helper_pos
            and _recipients_pos > _roll_pos
            and combat_source[_helper_pos:_recipients_pos].count("random.random()") == 1
        )
        metrics["all_drop_types_use_helper"] = "drop_recipients = party_drop_recipients_v0359(item_id, recipients)" in combat_source
        metrics["no_random_winner"] = "random.choice(recipients)" not in helper_source and "winner = drop_recipients[0]" not in combat_source
        metrics["shared_message"] = "każdy obecny członek otrzymuje" in combat_source
        metrics["same_room_reward_set"] = "self.server.party_sessions(" in combat_source and "same_room=self.character.room_id" in combat_source
        for key,value in metrics.items():
            if not value:
                errors.append(f"all-party drop audit failed: {key}")
    except Exception as exc:
        errors.append(f"all-party drop audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.9","error_count":len(errors),"errors":errors,"metrics":metrics}

ALL_PARTY_MOB_DROPS_SHARED_AUDIT_V0359 = all_party_mob_drops_shared_audit_v0359()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("party", []).extend([
    "v0.35.9: każdy zwykły drop z pokonanego moba jest kopiowany do wszystkich członków drużyny obecnych razem przy zabiciu.",
    "Szansa dropu jest losowana raz na moba. Jeśli przedmiot wypadnie, każdy obecny członek dostaje własną kopię — dotyczy eliksirów, mikstur, materiałów, run, klejnotów, komponentów i Odłamków Duszy.",
    "Członkowie drużyny w innych lokacjach nie otrzymują dropu z tego zabicia.",
])
HELP_TOPICS.setdefault("druzyna", []).extend([
    "v0.35.9: każdy zwykły drop z pokonanego moba jest kopiowany do wszystkich członków drużyny obecnych razem przy zabiciu.",
    "Szansa dropu jest losowana raz na moba. Jeśli przedmiot wypadnie, każdy obecny członek dostaje własną kopię — dotyczy eliksirów, mikstur, materiałów, run, klejnotów, komponentów i Odłamków Duszy.",
    "Członkowie drużyny w innych lokacjach nie otrzymują dropu z tego zabicia.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.9: wszystkie zwykłe dropy z mobów są współdzielone przez członków drużyny obecnych razem przy zabiciu."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.9 - All Local Party Mob Drops Shared"
LATEST_CHANGES = [
    "v0.35.9: każdy udany zwykły drop z moba trafia do każdego członka drużyny obecnego w tej samej lokacji przy zabiciu.",
    "Szansa dropu jest wykonywana tylko raz; wynik jest wspólny, a każda uprawniona postać dostaje własną kopię przedmiotu.",
    "Wspólna zasada obejmuje Eliksiry Duszy, mikstury, Odłamki Duszy, materiały, runy, klejnoty i komponenty technologiczne z tabeli drops.",
    "Gracze poza lokacją zabicia nie dostają dropu; liczniki questów nie są mnożone przez kopiowanie przedmiotów.",
]


# v0.35.10 - ALL LOCAL PARTY CORPSE LOOT SHARED
def all_party_corpse_loot_shared_audit_v03510():
    errors=[]
    metrics={}
    try:
        import inspect
        recipient_source=inspect.getsource(SessionWorldProgressionMixin._corpse_party_recipients_v03510)
        record_source=inspect.getsource(SessionWorldProgressionMixin._record_corpse_loot)
        all_source=inspect.getsource(SessionWorldProgressionMixin.loot_corpse)
        one_source=inspect.getsource(SessionWorldProgressionMixin.get_from_corpse)
        metrics["same_room_party"] = "party_sessions(\n                self.account_id, same_room=corpse.room_id\n            )" in recipient_source
        metrics["award_every_recipient"] = "for recipient in recipients" in record_source and "recipient.server.db.add_item(recipient.account_id, item_id, 1)" in record_source
        metrics["quest_collection_per_recipient"] = "await recipient.record_item_collection(" in record_source
        metrics["whole_corpse_cleared_before_award"] = "corpse.items.clear()" in all_source and "recipients = await self._record_corpse_loot(corpse, looted)" in all_source
        metrics["single_item_removed_before_award"] = one_source.find("corpse.items.remove(item_id)") < one_source.find("recipients = await self._record_corpse_loot(corpse, [item_id])")
        metrics["no_remote_party"] = "session.character.room_id == corpse.room_id" in recipient_source
        metrics["shared_nvda_message"] = "Loot z ciała drużyny" in all_source and "Loot z ciała drużyny" in one_source
        for key,value in metrics.items():
            if not value:
                errors.append(f"party corpse loot audit failed: {key}")
    except Exception as exc:
        errors.append(f"party corpse loot audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.10","error_count":len(errors),"errors":errors,"metrics":metrics}

ALL_PARTY_CORPSE_LOOT_SHARED_AUDIT_V03510 = all_party_corpse_loot_shared_audit_v03510()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("party", []).extend([
    "v0.35.10: loot leżący na ciele moba także jest współdzielony — gdy ktoś z drużyny przeszuka ciało lub zabierze z niego przedmiot, każdy członek drużyny stojący przy tym samym ciele w tej lokacji dostaje własną kopię.",
    "Ciało jest opróżniane tylko raz, więc współdzielonego EQ, materiału ani przedmiotu nie da się rozdawać ponownie przez wielokrotne przeszukiwanie.",
    "Członkowie drużyny poza lokacją ciała nie dostają jego lootu.",
])
HELP_TOPICS.setdefault("druzyna", []).extend(HELP_TOPICS.get("party", [])[-3:])
HELP_TOPICS.setdefault("zwloki", []).extend([
    "v0.35.10: przeszukanie ciała lub zabranie pojedynczego przedmiotu daje własną kopię każdemu członkowi drużyny stojącemu razem w lokacji ciała.",
    "Przedmiot znika z ciała przed rozdaniem kopii, więc jedno ciało nie może wypłacić tego samego lootu drugi raz.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.10: cały loot z ciał mobów jest współdzielony z lokalnymi członkami drużyny, tak jak zwykłe dropy z zabicia."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.10 - All Local Party Corpse Loot Shared"
LATEST_CHANGES = [
    "v0.35.10: EQ, materiały, klucze i inne przedmioty leżące na ciele moba są kopiowane do każdego członka drużyny obecnego w tej samej lokacji podczas przeszukania.",
    "Zasada działa zarówno dla przeszukaj/loot/get all, jak i dla zabrania pojedynczego przedmiotu get/wez z ciała.",
    "Przedmiot jest usuwany z ciała przed rozdaniem kopii, więc wielokrotne przeszukanie nie może zduplikować tego samego lootu.",
    "Materiały rzemieślnicze nadal trafiają do Szkatułki Rzemieślniczej, a każdy rzeczywisty odbiorca dostaje własny postęp kolekcji i aktywnego questa zbierackiego.",
    "Gracze poza lokacją ciała nie otrzymują lootu.",
]


# v0.35.11 - ALL LOCAL PARTY COMBAT BUFFS

def all_local_party_buffs_audit_v03511():
    errors=[]
    metrics={}
    try:
        import inspect
        combat_source=inspect.getsource(SessionSkillsCombatMixin.use_class_skill)
        helper_source=inspect.getsource(SessionSkillsCombatMixin.local_party_buff_recipients_v03511)
        passive_boost_source=inspect.getsource(SessionSkillsCombatMixin.passive_class_boost_multiplier_v11134)
        skill_buff_source=inspect.getsource(SessionSkillsCombatMixin.skill_buff_multiplier)
        offensive_multiplier_source=inspect.getsource(SessionSkillsCombatMixin.offensive_skill_damage_multiplier_v11186)
        vmax_support_source=inspect.getsource(SessionSkillsCombatMixin.party_vmax_support_active_v03511)
        metrics["same_room_party_helper"] = "party_sessions" in helper_source and "same_room=self.character.room_id" in helper_source
        metrics["living_local_only"] = "session.current_hp > 0" in helper_source and "session.character.room_id == self.character.room_id" in helper_source
        metrics["generic_boost_passive"] = "pasywnym wzmocnieniem Automatic" in combat_source and "apply_party_boost_v03511" not in combat_source
        metrics["typed_physical_magic_boosts"] = (
            "target_type" in passive_boost_source
            and "class_type_for_name(class_name)" in passive_boost_source
            and 'wanted_type in {"physical", "magic"}' in passive_boost_source
            and "target_type" in skill_buff_source
            and "skill_buff_multiplier(target_type=resolved_type)" in offensive_multiplier_source
        )
        metrics["guard_shared"] = "for session in recipients:" in combat_source and "session.skill_guard" in combat_source
        metrics["evade_shared"] = "for session in recipients:" in combat_source and "session.skill_evade = True" in combat_source
        metrics["vmax_self_only"] = "_vmax_statuses=" in combat_source and "self.active_skill_buffs" in combat_source and "v03511_party_vmax_until" not in combat_source
        metrics["vmax_support_self_only"] = "return self.mec_vmax_active_v0319()" in vmax_support_source and "v03511_party_vmax_until" not in vmax_support_source
        engineer_upgrade = next((x for x in CLASS_SKILLS.get("Inżynier",[]) if x.get("id")=="v0317_engineer_upgrade"), None)
        metrics["engineer_upgrade_not_fake_buff"] = bool(engineer_upgrade and engineer_upgrade.get("kind")=="utility")
        boost_skills=[(cls,sk.get("id")) for cls,rows in CLASS_SKILLS.items() for sk in rows if sk.get("kind")=="boost"]
        metrics["boost_skill_count"] = len(boost_skills)
        if not boost_skills:
            errors.append("brak skilli boost do weryfikacji")
        for key,value in metrics.items():
            if key=="boost_skill_count":
                continue
            if not value:
                errors.append(f"party buff audit failed: {key}")
    except Exception as exc:
        errors.append(f"party buff audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.11","error_count":len(errors),"errors":errors,"metrics":metrics}

ALL_LOCAL_PARTY_BUFFS_AUDIT_V03511 = all_local_party_buffs_audit_v03511()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("party", []).extend([
    "v0.35.11 po aktualizacji kontraktu: aktywne guardy i gwarantowane uniki działają na wszystkich żywych członków drużyny stojących w tej samej lokacji co rzucający.",
    "Zwykłe skille typu boost są pasywne Automatic po nauczeniu: fizyczne boosty wzmacniają tylko fizyczne skille, a magiczne tylko magiczne.",
    "V-MAX jest mechaniką Meca i nakłada swój korzystny pakiet wyłącznie na Meca; nie tworzy sztucznego drużynowego +30 procent.",
])
HELP_TOPICS.setdefault("druzyna", []).extend(HELP_TOPICS.get("party", [])[-3:])
HELP_TOPICS.setdefault("walka", []).extend([
    "v0.35.11: guard i evade są aktywnymi efektami drużynowymi w bieżącej lokacji; zwykłe boosty działają pasywnie Automatic.",
    "Inżynierski Upgrade jest trwałym narzędziem użytkowym, nie buffem bojowym; dlatego nie jest kopiowany na drużynę jako status czasowy.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.11: guard i evade pozostają lokalnie drużynowe; boosty są pasywne Automatic, a V-MAX pozostaje własnym efektem Meca."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.11 - All Local Party Combat Buffs"
LATEST_CHANGES = [
    "v0.35.11: zwykłe boosty są pasywne Automatic; fizyczne wzmacniają fizyczne skille, a magiczne magiczne.",
    "Guard daje każdemu obecnemu członkowi własną ochronę następnego trafienia, a evade daje każdemu własny gwarantowany unik następnego ataku.",
    "V-MAX Meca działa na Meca i jego źródłowy pakiet korzystnych statusów; nie daje sztucznego +30 procent całej drużynie.",
    "Upgrade Inżyniera został poprawnie sklasyfikowany jako utility, ponieważ jest trwałym ulepszeniem narzędzia, a nie czasowym buffem bojowym.",
    "Dodano stały audit wszystkich lokalnych buffów drużynowych.",
]

# ============================================================
# v0.36.0 - GLOBAL PROGRESSION 600 + LEADER DISBAND
# ============================================================
def progression_600_and_leader_disband_audit_v0360(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: progression_600_and_leader_disband_audit_v0360")
progression_600_and_leader_disband_audit_v0360 = _sb410_bind(_sb410_mod_v410_equipment_audits.progression_600_and_leader_disband_audit_v0360, globals())

PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360=progression_600_and_leader_disband_audit_v0360()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
# Final truth layer: old HELP aliases remain accepted, but describe current 600 progression.
HELP_TOPICS["progresja600"] = [
    "Główne osie progresji mają zakres 1-600: Level postaci, Biegłość klas, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia. Sześć statystyk bazowych pozostaje bez twardego limitu.",
    "Każda z 14 klas ma bazową siatkę minimum 183 skilli/spelli i dochodzi do Biegłości 600. Dwanaście standardowych klas ma minimum 3 skille na progach 1, 10, 20 i dalej co 10; źródłowe umiejętności mogą rozszerzać te progi. Mec i Inżynier zachowują swoje autorskie wczesne progi.",
    "Broń Duszy rozwija się do Soul Level 600 i Soul Tier 60. Tiery 41-60 kontynuują próby co 10 poziomów od 410 do 600.",
    "Wszystkie 14 profesji i 14 narzędzi rozwijają się do 600. Narzędzia mają 60 Tierów i nie mają trwałości; każde narzędzie kupuje się tylko raz na postać.",
    "Klasowe EQ ma progi 1, 10, 20, 30 i dalej co 10 aż do 600. Każdy kolejny próg ma wyższy rzeczywisty budżet podstawowych statów, więc niskie Tiery nie powtarzają tych samych wartości. Surowce i receptury mają dalszą zawartość 401-600.",
    "Wzniesienie klas i dostęp do World Tier 2+ zaczynają się po osiągnięciu Biegłości 600, bez resetowania wcześniejszej progresji.",
    "Auto kolejka skilli zaczyna z 10 slotami i rośnie o 1 co 10 Leveli postaci, do 70 slotów na Levelu 600.",
]
HELP_TOPICS["progresja400"] = list(HELP_TOPICS["progresja600"])
HELP_TOPIC_ALIASES.update({
    "600":"progresja600", "progresja 600":"progresja600", "progression600":"progresja600",
    "400":"progresja600", "progresja 400":"progresja600", "progression400":"progresja600",
})
HELP_TOPICS["podstawy"] = [
    "Soulbound v0.36.0 używa Generator Core jako źródła aktywnego balansu liczbowego.",
    "Level postaci, Biegłość, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia mają zakres 1-600; sześć statystyk bazowych rozwija się bez twardego limitu.",
    "Najważniejsze komendy: help, look/l/sp, exits/ex, hp, level/lvl, xp, score, staty, dusza, eq, quest, walk/prowadz oraz / do Świątyni.",
    "Wpisz help progresja600 po pełny opis obecnego zakresu progresji.",
]
HELP_TOPICS["profesje"] = [
    "Soulbound ma 14 profesji 1-600: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo, Zaklinanie, Archeologia i Kartografia.",
    "Każda profesja ma własny poziom do 600, a odpowiadające narzędzie ma niezależny poziom do 600 i 60 Tierów.",
    "Zakres 401-600 ma dalsze rangi, materiały i receptury; stare progi i zawartość 1-400 pozostają kompatybilne.",
    "Narzędzia nie mają trwałości ani zużycia.",
]
HELP_TOPICS["narzedzia200"] = [
    "Wszystkie 12 narzędzi profesji mają level 1-600 i 60 Tierów.",
    "Historyczne Tiery 1-40 do poziomu 400 pozostają w tych samych miejscach; Tiery 41-60 zaczynają się od 410 i kończą na 600.",
    "Narzędzia nie mają trwałości i nie wymagają naprawy.",
]
HELP_TOPICS["dusza"] = [
    "Broń Duszy ma Soul Level 1-600, Soul Weapon Mastery 1-600 i 60 Soul Tierów.",
    "Soul XP zatrzymuje się na progu następnego nieodblokowanego Tieru; dalszy rozwój wymaga odpowiedniej Próby Broni Duszy.",
    "Historyczne Tiery 1-40 pozostają zgodne ze starą progresją, a Tiery 41-60 prowadzą od Soul 410 do 600.",
    "Skille klasowe odblokuje Biegłość właściwej klasy, nie Soul Level.",
]
HELP_TOPICS["soul200"] = list(HELP_TOPICS["dusza"])
HELP_TOPICS["umiejetnosci"] = [
    "Każda z 14 klas ma 183 skille/spelle i progresję do Biegłości 600. Standardowe klasy mają po 3 na progach 1/10/20...600; Mec i Inżynier zachowują autorskie wczesne progi swoich zestawów technologicznych.",
    "Każdy nauczony skill/spell ma własny Skill Level 1-600 i własny XP.",
    "Odblokowanie zależy od Biegłości klasy; Skill Level rozwija konkretną poznaną umiejętność przez jej używanie.",
]
HELP_TOPICS["ekwipunek"] = [
    "Klasowe EQ ma progi 1, 10, 20, 30 i dalej co 10 aż do 600; każdy kolejny próg ma większy rzeczywisty budżet podstawowych statów, więc kolejne Tiery nie powtarzają tych samych wartości.",
    "Zwykłe i mityczne lochy oraz crafting zachowują starsze przedmioty, a progresja 401-600 dodaje dalsze EQ bez kasowania starego ekwipunku.",
    "Kowalskie metalowe EQ powstaje ze sztabek: ruda -> przetopienie -> sztabka -> kucie EQ.",
]
HELP_TOPICS["gildia"] = list(HELP_TOPICS.get("gildia", [])) + [
    "v0.36.0: poziom Gildii rozwija się do 600. Bonusy i koszty poziomów 1-400 zachowują balans v0.35.11, a 401-600 jest dalszą progresją.",
]
HELP_TOPICS["party"] = list(HELP_TOPICS.get("party", [])) + [
    "v0.36.0: gdy lider opuszcza drużynę, drużyna natychmiast się rozwiązuje; przywództwo nie jest przekazywane innej osobie.",
]
HELP_TOPICS["druzyna"] = list(HELP_TOPICS.get("druzyna", [])) + [
    "v0.36.0: wyjście lidera zawsze rozwiązuje całą drużynę zamiast wybierać nowego lidera.",
]
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.0: Global Progression 600 + Leader Disband — wszystkie główne osie dawnej progresji 1-400 rozwijają się do 600, a wyjście lidera rozwiązuje drużynę."
)

LATEST_CHANGES_TITLE = "Soulbound v0.36.0 - Global Progression 600 + Leader Disband"
LATEST_CHANGES = [
    "Wyjście lidera drużyny natychmiast rozwiązuje całą drużynę; nie ma automatycznego przekazania lidera.",
    "Level postaci, Biegłość klas, Skill Level, Soul Level, Soul Weapon Mastery, profesje, narzędzia i poziom Gildii mają cap 600.",
    "Każda z 14 klas ma 183 skille/spelle do Biegłości 600; Mec i Inżynier zachowują autorskie wczesne progi.",
    "Soul ma 60 Tierów; narzędzia mają 60 Tierów; profesje i crafting otrzymały zawartość 401-600.",
    "Klasowe EQ i receptury rozwijają się do 600; każdy Tier EQ 1/10/20/30/... ma realnie wyższy budżet statów. Wzniesienie i World Tier 2+ zaczynają się po Biegłości 600.",
    "Stare save'y nie wymagają wipe. Historyczna progresja 1-400 pozostaje kompatybilna.",
]

# ============================================================
# v0.36.1 - PARTY QUEST ACCEPT SYNC
# ============================================================
def party_quest_accept_sync_audit_v0361():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")
    try:
        import inspect
        src=inspect.getsource(SessionQuestsMixin.accept_quest_id)
        check("party_accept_internal_guard", "_party_shared" in src and "if not _party_shared" in src)
        check("leader_only_party_accept", "party_key" in src and "int(party_key) == int(self.account_id)" in src)
        check("same_room_party_accept", "same_room=self.character.room_id" in src)
        check("living_local_members_only", 'getattr(session, "current_hp"' in src and '> 0' in src)
        check("per_member_accept_call", "await member.accept_quest_id" in src and "_party_shared=True" in src)
        check("individual_requirements_preserved", "self.quest_lock_reasons(quest_id)" in src)
        check("individual_accept_items_preserved", 'quest.get("accept_items")' in src)
        check("party_summary_present", "Quest przyjęła razem z tobą drużyna" in src)
    except Exception as exc:
        errors.append(f"party quest source audit: {type(exc).__name__}: {exc}")
    return {"version":"0.36.1","error_count":len(errors),"errors":errors,"metrics":metrics}

PARTY_QUEST_ACCEPT_SYNC_AUDIT_V0361=party_quest_accept_sync_audit_v0361()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("questy", []).append(
    "v0.36.1: gdy lider przyjmuje zwykły quest, wszyscy żywi członkowie drużyny stojący z nim w tej samej lokacji automatycznie próbują przyjąć ten sam quest. Każdy zaczyna własny postęp od 0/x i musi spełniać własne wymagania."
)
HELP_TOPICS.setdefault("party", []).append(
    "v0.36.1: lider przyjmujący quest automatycznie dzieli jego przyjęcie z żywymi członkami drużyny stojącymi w tej samej lokacji. Członkowie poza pokojem nie dostają questa."
)
HELP_TOPICS.setdefault("druzyna", []).append(
    "v0.36.1: quest przyjęty przez lidera jest automatycznie przyjmowany osobno przez uprawnionych żywych członków drużyny obecnych przy liderze."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.1: Party Quest Accept Sync — lider przyjmuje zwykłe questy razem z lokalną drużyną, z osobnym postępem 0/x dla każdego gracza."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.1 - Party Quest Accept Sync"
LATEST_CHANGES = [
    "Lider przyjmujący zwykły quest automatycznie próbuje przyjąć go także dla wszystkich żywych członków drużyny stojących w tej samej lokacji.",
    "Każdy członek dostaje własny wpis 0/x, własne przedmioty questowe, własny postęp i własną nagrodę.",
    "Każdy gracz nadal musi spełniać własne wymagania questa; aktywne/ukończone zadanie, cooldown, brak wymagań albo walka powodują pominięcie tylko tej osoby.",
    "Członkowie poza pokojem i martwi członkowie nie dostają questa automatycznie; przyjęcie przez zwykłego członka drużyny pozostaje osobiste.",
    "Dodano stały audit v0.36.1 zapobiegający rekurencyjnemu rozsyłaniu questów.",
]

# ============================================================
# v0.36.2 - OPEN-WORLD TERRAIN THREAT REBALANCE
# ============================================================
def terrain_threat_rebalance_audit_v0362(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: terrain_threat_rebalance_audit_v0362")
terrain_threat_rebalance_audit_v0362 = _sb410_bind(_sb410_mod_v410_equipment_audits.terrain_threat_rebalance_audit_v0362, globals())

TERRAIN_THREAT_REBALANCE_AUDIT_V0362=terrain_threat_rebalance_audit_v0362()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("walka", []).append(
    "v0.36.2: zwykłe moby terenowe od etapu 50+ są wyraźnie mocniejsze. Teren około 100 ma około 2x bazowego HP moba i +10 procent obrażeń; wzrost trwa dalej na późnych terenach. Bossowie zachowują własne reguły rang i nie dostają dodatkowego mnożnika terenowego."
)
HELP_TOPICS.setdefault("generator", []).append(
    "v0.36.2: recommended_mastery jest dolną granicą NUMERYCZNEGO balansu pokoju. Nie blokuje wejścia, ale moby nie są już generowane jak dla znacznie słabszego terenu."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.2: Terrain Threat Rebalance — naprawiono zaniżone etapy statycznych i proceduralnych terenów oraz skalowanie współdzielonych mobów do aktualnej lokacji."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.2 - Terrain Threat Rebalance"
LATEST_CHANGES = [
    "Naprawiono zaniżony poziom mobów na terenach: recommended_mastery jest teraz dolną granicą numerycznego etapu lokacji bez tworzenia blokady wejścia.",
    "Współdzielony szablon moba jest na zwykłym terenie klonowany i balansowany pod aktualny etap pokoju zamiast pozostawać na poziomie najłatwiejszej strefy, w której występuje.",
    "Zwykłe/Elite/Rare moby terenowe od etapu 50 dostają dodatkowy wzrost wytrzymałości: około x2 HP na 100, x3 na 200 i x4 od 300; obrażenia rosną łagodniej, np. +10 procent na 100 i +20 procent na 200.",
    "Bossowie, World Bossowie i systemy lochowe zachowują własne reguły trudności; dodatkowy mnożnik terenowy nie jest na nie nakładany.",
    "Naprawiono także pokoje tworzone dopiero przy wejściu: ich recommended_mastery jest używane przy generowaniu etapu i mobów.",
    "Dodano stały audit v0.36.2 pilnujący balansu terenów i zachowania mnożników po runtime refreshu moba.",
]

# ============================================================
# v0.36.3 - OFFLINE PLAYER PROFILES + PRESENCE
# ============================================================
def offline_player_profiles_audit_v0363():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")
    try:
        import inspect
        dbsrc=(_ROOT/'storage/schema_migrate_social.py').read_text(encoding='utf-8')
        check("presence_table", "player_presence_v0363" in dbsrc and "last_login_ts" in dbsrc and "last_logout_ts" in dbsrc and "last_seen_ts" in dbsrc)
        check("profile_alias_pl", COMMAND_ALIASES.get("profil")=="whois")
        check("profile_alias_en", COMMAND_ALIASES.get("profile")=="whois")
        psrc=inspect.getsource(SessionSocialExpansionMixin.whois_v03051)
        check("offline_lookup", "SELECT * FROM characters WHERE account_id=?" in psrc)
        check("profile_character_level", "Level postaci" in psrc and "character_level" in psrc)
        check("profile_all_classes", "FROM class_progress" in psrc)
        check("profile_soul", "Soul Weapon Mastery" in psrc and "soul_tier" in psrc)
        check("profile_stats", "Statystyki:" in psrc and "charisma" in psrc)
        check("profile_professions_tools", "FROM professions" in psrc and "FROM tools" in psrc)
        check("profile_endgame", "world_tier_settings_v021" in psrc and "ascension_progress_v021" in psrc)
        check("profile_activity", "osiągnięcia" in psrc and "bestiary_stats" in psrc and "deaths" in psrc)
        check("profile_presence", "last_seen_ts" in psrc and "ostatnio widziany" in psrc)
        check("profile_eq_privacy", "inspect_enabled" in psrc and "inspectprivacy" in psrc)
        check("profile_no_account_secrets", "password_hash" not in psrc and "password_salt" not in psrc and "username" not in psrc)
        esrc=inspect.getsource(SessionIOAuthCharacterMixin.enter_world)
        csrc=inspect.getsource(SessionCommandLoopMixin.close)
        lsrc=inspect.getsource(SessionCommandLoopMixin.leave_current_character_for_selection)
        check("login_presence_hook", "mark_player_login_v0363" in esrc)
        check("logout_presence_close_hook", "mark_player_logout_v0363" in csrc)
        check("logout_presence_switch_hook", "mark_player_logout_v0363" in lsrc)
    except Exception as exc:
        errors.append(f"offline profile audit: {type(exc).__name__}: {exc}")
    return {"version":"0.36.3","error_count":len(errors),"errors":errors,"metrics":metrics}

OFFLINE_PLAYER_PROFILES_AUDIT_V0363=offline_player_profiles_audit_v0363()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS["profil"] = [
    "profil <nazwa gracza> działa dla postaci online i offline. Alias angielski: profile <nazwa>; starsze whois <nazwa> działa tak samo.",
    "Profil pokazuje publiczną progresję postaci: status i ostatnią obecność, Level, wszystkie klasy/Biegłości, Broń Duszy, statystyki, profesje, narzędzia, Gildię, World Tier/Wzniesienie, osiągnięcia, questy, Bestiariusz, zgony, rekordy i postęp lochów.",
    "EQ jest pokazane tylko wtedy, gdy pozwala na to inspectprivacy właściciela. Profil nigdy nie ujawnia loginu, hasła, poczty, banku ani innych prywatnych danych konta.",
]
HELP_TOPICS["profile"] = list(HELP_TOPICS["profil"])
HELP_TOPICS["whois"] = list(HELP_TOPICS["profil"])
HELP_TOPICS.setdefault("social", []).append(
    "v0.36.3: profil/profile/whois <gracz> pokazuje rozbudowany publiczny profil także wtedy, gdy postać jest offline, wraz z czasem ostatniej obecności."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.3: Offline Player Profiles — pełny profil postaci działa online i offline oraz zapisuje ostatnie logowanie/wylogowanie."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.3 - Offline Player Profiles"
LATEST_CHANGES = [
    "Dodano profil <gracz> oraz profile <player>; starsze whois korzysta z tego samego rozbudowanego profilu.",
    "Profil działa także dla postaci offline i pokazuje status, ostatnio widziany, ostatnie logowanie oraz ostatnie wylogowanie.",
    "Profil obejmuje Level postaci, wszystkie klasy/Biegłości, Broń Duszy, statystyki, profesje, narzędzia, Gildię, World Tier/Wzniesienie, osiągnięcia, questy, Bestiariusz, zgony, rekordy i postęp lochów.",
    "EQ respektuje inspectprivacy. Dane konta, login/hasło, poczta i bank nie są ujawniane.",
    "Dodano trwałą tabelę obecności i hooki logowania/wylogowania oraz stały audit v0.36.3.",
]


# ============================================================
# v0.36.4 - INDEPENDENT SKILL / SPELL COOLDOWNS
# ============================================================
def independent_skill_cooldowns_audit_v0364(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: independent_skill_cooldowns_audit_v0364")
independent_skill_cooldowns_audit_v0364 = _sb410_bind(_sb410_mod_v410_equipment_audits.independent_skill_cooldowns_audit_v0364, globals())

INDEPENDENT_SKILL_COOLDOWNS_AUDIT_V0364=independent_skill_cooldowns_audit_v0364()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("skills", []).append(
    "v0.36.4: każdy skill i spell ma własny niezależny cooldown. Użycie jednej umiejętności nie uruchamia, nie resetuje i nie przedłuża cooldownu żadnej innej umiejętności."
)
HELP_TOPICS.setdefault("spells", []).append(
    "v0.36.4: cooldown każdego zaklęcia jest liczony osobno po jego unikalnym ID; nie ma wspólnego cooldownu magicznego, fizycznego, klasowego ani globalnego."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.4: Independent Skill Cooldowns — wszystkie skille i zaklęcia mają niezależne timery cooldownu."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.4 - Independent Skill Cooldowns"
LATEST_CHANGES = [
    "Każdy skill i spell ma własny cooldown zapisany wyłącznie pod unikalnym ID danej umiejętności.",
    "Użycie skilla fizycznego nie blokuje innych skilli fizycznych ani zaklęć; użycie zaklęcia nie blokuje innych zaklęć ani skilli.",
    "Auto-kolejka oraz automatyczne leczenie Kapłana korzystają z tych samych niezależnych timerów co ręczne używanie umiejętności.",
    "Dodano stały audit v0.36.4 sprawdzający unikalność ID wszystkich skilli/spelli i test zachowania, że uruchomienie cooldownu A nie zmienia cooldownu B.",
]


# ============================================================
# v0.36.5 - SOUL TIER 7 CEMETERY TARGET DENSITY
# ============================================================
def soul_tier7_cemetery_spawn_audit_v0365():
    return _audit_rules_v406.soul_tier7_cemetery_spawn_audit_v0365(SOUL_TRIAL_QUEST_IDS=SOUL_TRIAL_QUEST_IDS, QUESTS=QUESTS, MOB_SPAWNS=MOB_SPAWNS, ROOMS=ROOMS)

SOUL_TIER7_CEMETERY_SPAWN_AUDIT_V0365 = soul_tier7_cemetery_spawn_audit_v0365()
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.5: Próba Broni Duszy Tier 7 ma sześć stałych Niespokojnych Zmarłych rozłożonych po Starym Cmentarzu przy wymaganiu 4 zabójstw."
)
HELP_TOPICS.setdefault("quests", []).append(
    "Próba Broni Duszy Tier 7: na Starym Cmentarzu dostępnych jest sześć stałych Niespokojnych Zmarłych, więc wykonanie celu 4/4 nie wymaga czekania na respawn."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.5 - Soul Tier 7 Cemetery Spawn Fix"
LATEST_CHANGES = [
    "Próba Broni Duszy Tier 7 nadal wymaga 4 Niespokojnych Zmarłych na Starym Cmentarzu.",
    "Zwiększono liczbę stałych celów questu z 2 naturalnych miejsc do 6 rozłożonych po całym Starym Cmentarzu.",
    "Niespokojni Zmarli są teraz w: Starym Cmentarzu, Alei Ossuariów, Ogrodzie Księżycowego Mchu, Zawalonej Kaplicy, Polu Kości i Wieży Martwego Dzwonu.",
    "Dodano audit v0.36.5 pilnujący celu 4/4 i co najmniej sześciu różnych miejsc spawnu.",
]


# ============================================================
# FINAL PUBLIC HELP TRUTH PASS v1.11.97
# admin/audits.py contains historical HELP writers. Re-apply the current
# audited HELP surface only after every legacy writer in this module ran.
# ============================================================
refresh_help_truth_v11197()
refresh_public_help_surface_v11197()

HELP_TRUTH_AUDIT_V11197 = help_truth_audit_v11197()
HELP_SURFACE_AUDIT_V11197 = help_surface_audit_v11197()
_FINAL_HELP_ERRORS_V11197 = list(HELP_TRUTH_AUDIT_V11197.get("errors", ()))
_FINAL_HELP_ERRORS_V11197.extend(HELP_SURFACE_AUDIT_V11197.get("errors", ()))
# v1.13.30: audit report is enforced by predeploy_full.py; runtime stays diagnostic.