# -*- coding: utf-8 -*-
"""Production HELP, NPC, quest and equipment finalization for Soulbound v111.

Pure historical audits stay in admin/audits.py, used only by PREDEPLOY.
The statements below retain their original order and source, preserving
all game-state changes without running release-only regressions on boot.
"""

from data import catalog_mutations as _catalog_mut

def main():
    import asyncio  # explicit current dependency
    from server.mud_server import MudServer  # explicit current dependency
    try:
        asyncio.run(MudServer().run())
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")

from data.current_help import get_help_catalogs as _current_help_catalogs
HELP_TOPICS = _current_help_catalogs()[0]
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

def refresh_help_v03021_full():
    """Finalna warstwa HELP. Nadpisuje historyczne teksty, które nie opisują już runtime."""
    from data.current_help import get_help_catalogs as _current_help_catalogs
    HELP_TOPICS = _current_help_catalogs()[0]
    HELP_TOPIC_ALIASES = _current_help_catalogs()[1]
    HELP_TOPIC_ALIASES.update({
        "waluta":"waluta", "pieniadze":"waluta", "pieniądze":"waluta", "money":"waluta",
        "eq sklep":"sklepy", "sklep eq":"sklepy", "sklepy eq":"sklepy",
        "sell all":"sprzedaj_wszystko", "sprzedaj wszystko":"sprzedaj_wszystko",
    })
    HELP_TOPICS["waluta"] = [
        "Cała ekonomia używa jednego wspólnego salda. Nominały służą tylko do czytelnego wyświetlania i wpisywania kwot.",
        "100 srebra = 1 złota. 1 000 000 złota = 1 mithril. 1 mithril = 100 000 000 srebra.",
        "Gra zawsze normalizuje kwotę do najwyższych nominałów: 100 srebra jest czytane jako 1 złota; 250 srebra jako 2 złota, 50 srebra.",
        "Przy późnym endgame duże kwoty przechodzą automatycznie w mithril. Ta sama zasada działa przy zarabianiu, zakupie, sprzedaży, banku i innych kosztach.",
    ]
    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę aktualnego sprzedawcy.",
        "shop info <numer> / sklep info <numer> pokazuje pełny opis, statystyki, wymagania, cenę po rabacie i porównanie z założonym EQ.",
        "kup <nazwa> albo kup <numer> kupuje przedmiot; np. kup 9 albo kup 9 3.",
        "Klasowe sklepy EQ pokazują najlepszy Tier odblokowany przez Level postaci dla aktywnej klasy i wszystkie 13 typów: hełm, pancerz, rękawice, nogawice, buty, talizman, pierścień, naszyjnik, naramienniki, pas, peleryna, karwasze, kolczyki i relikt.",
        "sprzedaj <nazwa> sprzedaje jedną wolną sztukę. Założone EQ i Character-Bound są chronione.",
        "sell all / sprzedaj wszystko sprzedaje wyłącznie niezałożone EQ. Nie sprzedaje mikstur, consumables, zwykłego lootu, materiałów, narzędzi ani quest itemów.",
        "Zasoby profesyjne sprzedaje się osobno u właściwych fachowców; hurtowo działają istniejące komendy wszystko siatka/sakwa/stos/torba.",
        "Każda kwota sklepu jest czytana ze wspólnego salda po normalizacji mithril, złoto, srebro.",
    ]
    HELP_TOPICS["eq"] = [
        "equipment / eq pokazuje założone wyposażenie oraz Broń Duszy; eq info pokazuje szczegóły, bonusy, sockety i aktywne sety.",
        "Klasowe EQ ma 13 logicznych typów: hełm, pancerz, rękawice, nogawice, buty, talizman, pierścień, naszyjnik, naramienniki, pas, peleryna, karwasze, kolczyki i relikt.",
        "Pierścienie i talizmany zakładają się automatycznie: załóż <nazwa>, zp <numer> albo zt <numer> używa wolnego slotu; przy dwóch zajętych zastępuje słabszy.",
        "Ręczny wybór pozostaje: zp1/zp2 dla pierścieni oraz zt1/zt2 dla talizmanów.",
        "Skróty: zh hełm, zz zbroja, zr rękawice, zn nogi, zb buty, zna naszyjnik, zkol kolczyki auto, zkol1/zkol2 ręcznie, znar naramienniki, zpas pas, zpel peleryna, zkar karwasze, zrel relikt.",
        "Level postaci odblokowuje EQ na progach 1, 10, 20...400. Biegłość klasy nadal odblokowuje skille/spelle, ale nie jest bramą założenia EQ.",
    ]
    HELP_TOPICS["sety_klasowe"] = [
        "Każda z 14 klas ma klasowe linie EQ obejmujące 13 typów wyposażenia.",
        "Bonusy zestawów nadal mają progi 2/4/6/8 części. Nowe sloty zwiększają wybór i nie dodają kolejnego automatycznego progu mocy.",
        "Sety i ich tożsamość są ręcznie projektowane; Generator Core może balansować wyłącznie liczbowe wartości istniejących bonusów.",
    ]
    HELP_TOPICS["skille100_200"] = [
        "Historyczna nazwa tematu została zachowana jako alias. Obecnie Biegłość każdej klasy ma zakres 1-400.",
        "Każda klasa ma 123 skille/spelle: dokładnie 3 na każdy próg Biegłości 1, 10, 20...400.",
        "Sloty auto kolejki zależą od Character Level, nie od Biegłości: Level 1 ma 10 slotów, potem +1 co 10 Leveli, do 50 na Levelu 400.",
    ]
    # quest / questy mogą być osobnymi aliasami w zależności od historycznej warstwy.
    quest_help = [
        "quest / questy pokazuje aktywne zadania; quest ukończone pokazuje historię; quest list <NPC> pokazuje numerowaną ofertę NPC.",
        "quest accept <numer> przyjmuje zadanie. Każdy quest zaczyna od 0/x i liczy wyłącznie zdarzenia wykonane po przyjęciu.",
        "Questy nie mają globalnej blokady Character Level. Obowiązują tylko rzeczywiste wymagania konkretnego zadania, np. Soul, profesja, narzędzie, wcześniejszy quest lub fabuła.",
        "quest info <numer> pokazuje opis, cel, postęp, wymagania i wszystkie nagrody; quest oddaj <numer> oddaje gotowe zadanie właściwemu NPC.",
        "Nagrody pieniężne questów trafiają do jednego portfela i są zawsze czytane w znormalizowanych nominałach: mithril, potem złoto, potem srebro.",
        "Od v0.30.21 zwykły quest daje co najmniej równowartość 1 złota oraz resztę w srebrze; mithril pojawia się dopiero w późnej progresji/endgame.",
    ]
    HELP_TOPICS["quest"] = list(quest_help)
    HELP_TOPICS["questy"] = list(quest_help)
    HELP_TOPICS["sprzedaj_wszystko"] = [
        "sell all / sprzedaj wszystko sprzedaje tylko niezałożone EQ typu armor.",
        "Mikstury, inne consumables, zwykły loot, materiały, narzędzia, quest itemy i założone wyposażenie nie są przez tę komendę sprzedawane.",
    ]
    HELP_TOPICS["generator"] = [
        "Generator Core działa w trybie Numeric-Only z Whitelist Guard.",
        "Może zmieniać wyłącznie dozwolone liczby balansu: HP, damage, XP, ceny, nagrody, cooldowny, koszty many oraz wartości istniejących efektów/statów.",
        "Nie może zmieniać nazw, ID, unlocków, klas, slotów EQ, list dropów, celów questów, wymagań, składników receptur, Soul Milestones ani topologii świata.",
        "v0.30.21 koryguje wyłącznie numeryczną ekonomię questów i narzędzi; zasady Whitelist Guard pozostają bez zmian.",
    ]


refresh_help_v03021_full()

LATEST_CHANGES_TITLE = "Soulbound v0.30.21 - Full HELP + Unified Currency Economy"

LATEST_CHANGES = [
    "Pełny audit finalnego HELP: wszystkie tematy i aliasy są sprawdzane po nałożeniu wszystkich historycznych warstw pomocy.",
    "Klasowe sklepy EQ są audytowane dla wszystkich 14 klas i pełnych 13 typów wyposażenia.",
    "Jedno saldo waluty jest zawsze prezentowane po normalizacji: mithril, złoto, srebro; 100 srebra jest czytane jako 1 złota.",
    "Nagrody questów zostały podniesione i skalowane tak, aby od początku zawierały co najmniej równowartość złota, a mithril pojawiał się dopiero w późnym endgame.",
    "Ceny podstawowych narzędzi nie zależą już od przypadkowego generator_level przedmiotu; wszystkie starterowe narzędzia mają spójny przedział cenowy.",
]

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

from data.current_help import get_help_catalogs as _current_help_catalogs
HELP_TOPIC_ALIASES = _current_help_catalogs()[1]
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

V03025_PROFESSION_REWARD_REPAIRS = {}

from data.quests import QUESTS  # canonical current dependency
from core.bootstrap_economy_professions import profession_for_tool_type  # explicit current dependency
for _quest_id, _quest in QUESTS.items():
    _tool_type = _quest.get("reward_tool_type")
    _expected_profession = profession_for_tool_type(_tool_type)
    _has_profession_reward = int(_quest.get("reward_profession_xp", 0) or 0) > 0
    _has_tool_reward = int(_quest.get("reward_tool_xp", 0) or 0) > 0
    if _has_profession_reward and _has_tool_reward and _expected_profession:
        if not _quest.get("reward_profession"):
            _quest["reward_profession"] = _expected_profession
            V03025_PROFESSION_REWARD_REPAIRS[_quest_id] = _expected_profession

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

V03026_WOOD_RECIPES = []

from systems.equipment_crafting import CRAFT_RECIPES  # explicit current dependency
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

from systems.equipment_crafting import COOK_RECIPES  # explicit current dependency
for _recipe in COOK_RECIPES.values():
    _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("blue_flame_kitchen",)))

from systems.equipment_crafting import ALCHEMY_RECIPES  # explicit current dependency
for _recipe in ALCHEMY_RECIPES.values():
    _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("alchemy_lab",)))

from systems.equipment_crafting import JEWELCRAFT_RECIPES  # explicit current dependency
for _recipe in JEWELCRAFT_RECIPES.values():
    _recipe["stations"] = tuple(dict.fromkeys(tuple(_recipe.get("stations", ())) + ("jeweler_workshop",)))

from systems.equipment_crafting import SHOPS  # explicit current dependency
for _starter_ore in ("iron_ore", "silver_ore", "gold_ore"):
    if _starter_ore not in _catalog_mut.catalog_setdefault_path('SHOPS', SHOPS, (), "forge", []):
        SHOPS["forge"].append(_starter_ore)

def apply_soul_shard_drop_fix_v03026():
    # Klasyczne moby wejściowej Krypty.
    from data.mobs import MOB_TEMPLATES  # canonical current dependency
    import data.catalog_mutations as _catalog_mut  # explicit current dependency
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

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.26: gameplay flow pass. Naprawiono ex->exits, Tier-gating zasobów i receptur, stanowiska specjalistów oraz deski Drwalstwo+Piła."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.26 - Gameplay Flow + Tool Tier Gating"

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

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.29: naprawiono blokadę startu DEPLOY/Railway powodowaną przez historyczne audyty przypięte do starych numerów VERSION."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.29 - Deploy Startup Hotfix"

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

from core.progression_600 import CHARACTER_MAX_LEVEL  # canonical current dependency
from data.items import ITEMS  # canonical current dependency
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

from systems.new_heroes_v900 import EQUIPMENT as _V900_SHOP_DEFS, NEW_CLASSES as _V900_SHOP_CLASSES

for _name, *_entry in _V900_SHOP_CLASSES:
    _room = 'guild_v900_shop_'+_V900_SHOP_DEFS[_name]['prefix'].removeprefix('v900_')
    CLASS_SHOP_ROOM_BY_CLASS_V03036[_name] = _room
    CLASS_SHOP_SELLER_NAMES_V03036[_name] = 'Kwatermistrz '+_name

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

def apply_separate_class_shops_v03036():
    # 1. Wspólne sale przestają być sklepami.
    import systems.content_registry as _current_content_registry  # explicit optional dependency
    from data.npcs import NPCS  # canonical current dependency
    from data.rooms import ROOMS  # canonical current dependency
    import data.catalog_mutations as _catalog_mut  # explicit current dependency
    from storage.db_shared import normalize_lookup_text  # canonical current dependency
    from core.mines_threat import GUIDE_DESTINATION_ALIASES  # explicit current dependency
    from data.current_help import get_help_catalogs as _current_help_catalogs
    HELP_TOPICS = _current_help_catalogs()[0]
    from systems.content_registry import NPC_DESCRIPTIONS  # explicit current dependency
    from systems.equipment_crafting import SHOPS, SHOP_SELLERS  # explicit current dependency
    from systems.items_resources import CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER, CLASS_EQUIPMENT_SETS, CLASS_SHOP_CLASSES_BY_ROOM, CLASS_SHOP_ITEMS_BY_ROOM  # explicit current dependency
    for room_id in OLD_SHARED_CLASS_SHOP_ROOMS_V03036:
        _catalog_mut.catalog_pop_path('SHOPS', SHOPS, (), room_id, None)
        SHOP_SELLERS.pop(room_id, None)
        room = ROOMS.get(room_id)
        if room:
            room["desc"] = str(room.get("desc") or "").replace(
                " W tej sali działa także klasowy sklep z pełnym 14-elementowym wyposażeniem.",
                " Sklepy EQ znajdują się w osobnych salach poszczególnych klas."
            )
    for npc_id in OLD_SHARED_CLASS_SHOP_SELLERS_V03036:
        npc = NPCS.get(npc_id)
        if npc:
            npc["shopkeeper"] = False
            npc["dialogue"] = (
                "Każda klasa ma teraz osobny sklep EQ w swojej własnej sali. "
                "Wpisz walk eq <klasa>, aby dojść bezpośrednio do właściwego sklepu."
            )

    # 2. Przebudowa mapowania: jeden pokój = dokładnie jedna klasa.
    CLASS_SHOP_CLASSES_BY_ROOM.clear()
    CLASS_SHOP_ITEMS_BY_ROOM.clear()

    for class_name, room_id in CLASS_SHOP_ROOM_BY_CLASS_V03036.items():
        if room_id not in ROOMS:
            raise RuntimeError(f"v0.30.36: brak sali sklepu klasy {class_name}: {room_id}")
        if class_name not in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER:
            raise RuntimeError(f"v0.30.36: brak EQ klasy {class_name}")

        CLASS_EQUIPMENT_SETS[class_name]["room"] = room_id
        CLASS_SHOP_CLASSES_BY_ROOM[room_id] = [class_name]
        tier_one = list(CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER[class_name].get(1, ()))
        CLASS_SHOP_ITEMS_BY_ROOM[room_id] = tier_one
        _catalog_mut.catalog_assign(list(tier_one), 'SHOPS', SHOPS, (room_id,))

        seller_id = "class_eq_shop_" + normalize_lookup_text(class_name).replace(" ", "_")
        seller_name = CLASS_SHOP_SELLER_NAMES_V03036[class_name]
        _catalog_mut.catalog_assign({
            "name": seller_name,
            "room": room_id,
            "dialogue": (
                f"Prowadzę osobny sklep EQ klasy {class_name}. "
                "Wpisz shop albo list, aby usłyszeć aktualny Tier wyposażenia "
                "odblokowany przez Level postaci."
            ),
            "shopkeeper": True,
            "class_eq_shop": class_name,
        }, 'NPCS', NPCS, (seller_id,))
        SHOP_SELLERS[room_id] = seller_id
        if isinstance(getattr(_current_content_registry, 'NPC_DESCRIPTIONS', None), dict):
            NPC_DESCRIPTIONS[seller_id] = (
                f"Sprzedawca wyposażenia wyłącznie dla klasy {class_name}. "
                "Oferta skaluje się z Levelem postaci, a zakup nadal wymaga aktywnej właściwej klasy."
            )

        room = ROOMS[room_id]
        shop_sentence = (
            f" Działa tu osobny sklep EQ klasy {class_name}; "
            "wpisz shop, aby usłyszeć ofertę."
        )
        if shop_sentence.strip() not in str(room.get("desc") or ""):
            room["desc"] = str(room.get("desc") or "") + shop_sentence

        # 3. Prowadzenie i stare skróty zawsze trafiają do nowego, osobnego sklepu.
        for prefix in ("eq", "sklep eq", "sklep z eq", "ekwipunek", "sklep"):
            GUIDE_DESTINATION_ALIASES[
                normalize_lookup_text(f"{prefix} {class_name}")
            ] = room_id

    # v1.20.2: The shared arcane *class EQ* shop was retired, but Selene is
    # also the Zaklinanie profession specialist. Restore her independent
    # single-tool shop after creating the separate Mag/Psionik EQ shops.
    # Without this, the v0.30.36 cleanup silently removes the Runic Focus
    # added by systems.professions and `list` says there is no shop.
    enchanting_room = "guild_arcane_chamber"
    enchanting_seller_id = "guild_quartermaster_arcane"
    _catalog_mut.catalog_assign(["runic_focus"], 'SHOPS', SHOPS, (enchanting_room,))
    SHOP_SELLERS[enchanting_room] = enchanting_seller_id
    enchanting_seller = NPCS[enchanting_seller_id]
    enchanting_seller["shopkeeper"] = True
    enchanting_seller["dialogue"] = (
        "Prowadzę Zaklinanie i sprzedaję Fokus Runiczny. "
        "Wpisz list albo shop, potem kup 1 lub kup fokus runiczny. "
        "Wyposażenie klasowe Maga i Psionika jest w osobnych salach."
    )
    enchanting_description = " U Selene kupisz Fokus Runiczny: list, kup 1."
    if enchanting_description.strip() not in str(ROOMS[enchanting_room].get("desc") or ""):
        ROOMS[enchanting_room]["desc"] = (
            str(ROOMS[enchanting_room].get("desc") or "") + enchanting_description
        )

    HELP_TOPICS["sklepy klasowe"] = [
        "Każda z 14 klas ma własny, osobny sklep EQ w swojej sali klasowej w Gildii Dusz.",
        "Wojownik, Berserker, Łotrzyk, Łowca, Mnich, Strażnik, Mag, Nekromanta, Kapłan, Czarownik, Druid i Psionik nie współdzielą już punktów sprzedaży.",
        "Najprościej użyć: walk eq <klasa>, na przykład walk eq wojownik albo walk eq kapłan.",
        "W sklepie wpisz shop. Oferta pokazuje najlepszy Tier EQ odblokowany przez Level postaci; zakup nadal wymaga aktywnej odpowiedniej klasy.",
    ]
    HELP_TOPICS.setdefault("eq", []).append(
        "v0.30.36: każda klasa ma osobny sklep EQ w swojej sali klasowej. Użyj walk eq <klasa>."
    )
    HELP_TOPICS.setdefault("sklepy", []).append(
        "v0.30.36: help sklepy klasowe opisuje 14 osobnych sklepów wyposażenia klasowego."
    )
    HELP_TOPICS.setdefault("wersja", []).append(
        "v0.30.36: rozdzielono klasowe sklepy EQ na 14 osobnych punktów, po jednym dla każdej klasy."
    )


from data.rooms import ROOMS  # canonical current dependency
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

from data.npcs import NPCS  # canonical current dependency
_catalog_mut.catalog_assign("guild_mec_chamber", 'NPCS', NPCS, ("teacher_mec", "room"))

_catalog_mut.catalog_assign("guild_engineer_chamber", 'NPCS', NPCS, ("teacher_engineer", "room"))

from systems.new_heroes_v900 import EQUIPMENT as _V900_ROOM_DEFS, NEW_CLASSES as _V900_ROOM_CLASSES

_V900_SHOP_ANCHOR = 'guild_mec_chamber'

_V900_SHOP_DIRECTIONS = (('north','south'),('south','north'),('east','west'),
                         ('west','east'),('northeast','southwest'),('northwest','southeast'),
                         ('southeast','northwest'),('southwest','northeast'),('up','down'),('down','up'))

for _v900_name, *_v900_entry in _V900_ROOM_CLASSES:
    _new_shop_room = 'guild_v900_shop_'+_V900_ROOM_DEFS[_v900_name]['prefix'].removeprefix('v900_')
    if _new_shop_room in ROOMS:
        raise RuntimeError('v9 duplicate class shop '+_new_shop_room)
    _catalog_mut.catalog_assign({'name':'Sklep EQ '+_v900_name,
         'zone':'Gildia Dusz','desc':'Osobny sklep ekwipunku klasy '+_v900_name+'.',
         'exits':{}}, 'ROOMS', ROOMS, (_new_shop_room,))
    for _forward,_reverse in _V900_SHOP_DIRECTIONS:
        if _forward not in ROOMS[_V900_SHOP_ANCHOR].setdefault('exits',{}) and _reverse not in ROOMS[_new_shop_room]['exits']:
            _catalog_mut.catalog_assign(_new_shop_room,'ROOMS',ROOMS,(_V900_SHOP_ANCHOR,'exits',_forward))
            _catalog_mut.catalog_assign(_V900_SHOP_ANCHOR,'ROOMS',ROOMS,(_new_shop_room,'exits',_reverse))
            break
    else:
        raise RuntimeError('v9 no exit for class shop '+_new_shop_room)
    _V900_SHOP_ANCHOR = _new_shop_room

apply_separate_class_shops_v03036()

# This check is a live safety contract, not a historical reporting audit:
# server.py revalidates all 38 class shops after registering v107/v110 classes.
def class_shop_audit_v03036():
    from data.items import ITEMS  # canonical current dependency
    from data.npcs import NPCS  # canonical current dependency
    from storage.db_shared import normalize_lookup_text  # canonical current dependency
    from core.mines_threat import GUIDE_DESTINATION_ALIASES  # explicit current dependency
    from systems.equipment_crafting import SHOPS, SHOP_SELLERS, class_equipment_unlocked_tier  # explicit current dependency
    from systems.items_resources import CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER, CLASS_EQUIPMENT_SETS, CLASS_SHOP_CLASSES_BY_ROOM  # explicit current dependency
    errors = []
    checked = 0
    if len(CLASS_SHOP_CLASSES_BY_ROOM) != len(CLASS_EQUIPMENT_SETS):
        errors.append(f"shop room count={len(CLASS_SHOP_CLASSES_BY_ROOM)} expected={len(CLASS_EQUIPMENT_SETS)}")
    if set(CLASS_SHOP_ROOM_BY_CLASS_V03036) != set(CLASS_EQUIPMENT_SETS):
        missing = sorted(set(CLASS_EQUIPMENT_SETS) - set(CLASS_SHOP_ROOM_BY_CLASS_V03036))
        extra = sorted(set(CLASS_SHOP_ROOM_BY_CLASS_V03036) - set(CLASS_EQUIPMENT_SETS))
        errors.append(f"class mapping mismatch missing={missing} extra={extra}")

    for class_name, room_id in CLASS_SHOP_ROOM_BY_CLASS_V03036.items():
        checked += 1
        classes = list(CLASS_SHOP_CLASSES_BY_ROOM.get(room_id, ()))
        if classes != [class_name]:
            errors.append(f"{class_name}: room mapping={classes}")
        if CLASS_EQUIPMENT_SETS.get(class_name, {}).get("room") != room_id:
            errors.append(f"{class_name}: equipment set room mismatch")
        seller_id = SHOP_SELLERS.get(room_id)
        seller = NPCS.get(seller_id, {}) if seller_id else {}
        if not seller_id or seller.get("room") != room_id or not seller.get("shopkeeper"):
            errors.append(f"{class_name}: missing active seller")
        for level in (1, 10, 100, 200, 300, 400, 600):
            tier = class_equipment_unlocked_tier(level)
            offers = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name, {}).get(tier, ())
            if not offers:
                errors.append(f"{class_name}: no offers at level {level}")
                continue
            wrong = [iid for iid in offers if ITEMS.get(iid, {}).get("required_class") != class_name]
            if wrong:
                errors.append(f"{class_name}: foreign items at level {level}: {wrong[:3]}")
        for prefix in ("eq", "sklep eq", "sklep z eq", "ekwipunek", "sklep"):
            key = normalize_lookup_text(f"{prefix} {class_name}")
            if GUIDE_DESTINATION_ALIASES.get(key) != room_id:
                errors.append(f"{class_name}: guide alias {key!r} points elsewhere")

    for room_id in OLD_SHARED_CLASS_SHOP_ROOMS_V03036:
        if room_id in CLASS_SHOP_CLASSES_BY_ROOM:
            errors.append(f"old shared room still class shop: {room_id}")
        if room_id == "guild_arcane_chamber":
            # Zaklinanie has a real profession-tool vendor here; it must not
            # bring back the old mixed Mag/Psionik class EQ catalogue.
            if SHOPS.get(room_id) != ["runic_focus"]:
                errors.append("arcane profession shop must sell only runic_focus")
            seller = NPCS.get("guild_quartermaster_arcane", {})
            if (SHOP_SELLERS.get(room_id) != "guild_quartermaster_arcane"
                    or seller.get("room") != room_id or not seller.get("shopkeeper")):
                errors.append("arcane profession shop has no active Selene")
            continue
        if SHOPS.get(room_id):
            errors.append(f"old shared room still sells items: {room_id}")
        if SHOP_SELLERS.get(room_id):
            errors.append(f"old shared room still has seller mapping: {room_id}")

    return {
        "version": "0.30.36",
        "class_shops_checked": checked,
        "shop_room_count": len(CLASS_SHOP_CLASSES_BY_ROOM),
        "error_count": len(errors),
        "errors": errors,
    }

CLASS_SHOP_AUDIT_V03036 = class_shop_audit_v03036()

LATEST_CHANGES_TITLE = "Soulbound v0.30.36 - Separate Class EQ Shops"

LATEST_CHANGES = [
    "v0.30.36: każda z 14 klas ma własny, osobny sklep EQ w swojej sali klasowej.",
    "v0.30.36: sześć dawnych wspólnych punktów sprzedaży jest teraz wyłącznie hubami; nie sprzedają już mieszanego EQ dwóch klas.",
    "v0.30.36: walk eq <klasa>, sklep eq <klasa> i sklep <klasa> prowadzą do właściwego osobnego sklepu.",
    "v0.30.36: oferta nadal zależy od Levelu postaci, a zakup wymaga aktywnej właściwej klasy. Brak wipe.",
] + LATEST_CHANGES

def refresh_material_stat_profiles_v03037():
    """Finalna warstwa po Generator Core: 24 różne profile statów per materiał/slot.

    Generator Core może numerycznie wyrównać wartości istniejących statów. Tutaj zachowujemy
    jego całkowity budżet możliwie blisko, ale rozkładamy go na 24 różne podzbiory statów.
    Dzięki temu żadna para wariantów tego samego materiału i slotu nie jest statystyczną kopią.
    """
    from data.items import ITEMS  # canonical current dependency
    from systems.items_resources import CORPSE_MATERIAL_ITEM_IDS, CORPSE_MATERIAL_SLOT_DEFS, CORPSE_MATERIAL_TIERS, CORPSE_RANDOM_VARIANTS_PER_SLOT, MATERIAL_PROPERTY_NAMES, MATERIAL_RANDOM_STAT_POOL, MATERIAL_SLOT_STAT_PREFERENCES, MATERIAL_STAT_NAMES, _material_variant_title  # explicit current dependency
    from itertools import combinations
    for tier in CORPSE_MATERIAL_TIERS:
        ids = CORPSE_MATERIAL_ITEM_IDS.get(tier["key"], ())
        for slot in CORPSE_MATERIAL_SLOT_DEFS:
            rows = [
                (item_id, ITEMS[item_id]) for item_id in ids
                if ITEMS.get(item_id, {}).get("slot") == slot
            ]
            rows.sort(key=lambda row: int(row[1].get("corpse_random_variant", 0) or 0))
            order = tuple(MATERIAL_SLOT_STAT_PREFERENCES.get(slot, MATERIAL_RANDOM_STAT_POOL))
            patterns = []
            # 5 singletonów + 10 par + pierwsze 9 trójek = dokładnie 24 unikalne układy kluczy.
            for size in (1, 2, 3):
                for combo in combinations(order, size):
                    patterns.append(combo)
                    if len(patterns) == CORPSE_RANDOM_VARIANTS_PER_SLOT:
                        break
                if len(patterns) == CORPSE_RANDOM_VARIANTS_PER_SLOT:
                    break
            if len(patterns) != CORPSE_RANDOM_VARIANTS_PER_SLOT:
                raise RuntimeError(f"v0.30.37: za mało wzorców statów dla {slot}")

            for index, (item_id, item) in enumerate(rows):
                combo = patterns[index]
                old_total = sum(max(0, int(v or 0)) for v in (item.get("stats") or {}).values())
                # Nie osłabiamy przedmiotu; bardzo niski budżet może wzrosnąć maksymalnie do 3,
                # żeby unikalny układ statów był możliwy także na Żelazie/Stali.
                budget = max(len(combo), old_total)
                values = {stat: 1 for stat in combo}
                remaining = budget - len(combo)
                pos = index % len(combo)
                while remaining > 0:
                    stat = combo[pos % len(combo)]
                    values[stat] += 1
                    pos += 1
                    remaining -= 1
                item["stats"] = values
                variant = int(item.get("corpse_random_variant", index + 1) or index + 1)
                req = int(item.get("required_character_level", item.get("required_mastery", 1)) or 1)
                item["name"] = _material_variant_title(tier, slot, values, variant, req)
                stat_text = ", ".join(
                    f"{MATERIAL_STAT_NAMES.get(stat, stat)} +{amount}" for stat, amount in values.items()
                )
                prop_text = ", ".join(
                    f"{MATERIAL_PROPERTY_NAMES.get(prop, prop)} +{amount}%"
                    for prop, amount in (item.get("properties") or {}).items()
                )
                item["desc"] = (
                    f"Materiałowe EQ z ciała przeciwnika. Wymaga Levelu postaci {req}. "
                    f"Slot ma własny profil, a wariant nie powtarza statów innego wariantu tego samego materiału/slotu. "
                    f"Obrona +{int(item.get('defense', 0) or 0)}. Statystyki: {stat_text}. "
                    f"Właściwości: {prop_text or 'brak dodatkowych'} ."
                )


refresh_material_stat_profiles_v03037()

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

def _install_race_help_v03039():
    from storage.db_shared import normalize_lookup_text  # canonical current dependency
    from core.classes_skills import RACES, RACE_CLASS_RECOMMENDATIONS  # explicit current dependency
    from data.current_help import get_help_catalogs as _current_help_catalogs
    HELP_TOPICS = _current_help_catalogs()[0]
    HELP_TOPIC_ALIASES = _current_help_catalogs()[1]
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

for _topic, _line in {
    "profesje": "v0.30.55: nowe rzemiosła mają pełne komendy PL/EN: Tailoring, Leatherworking, Carpentry i Enchanting; Crafting Mastery oraz jakość craftu działają na gotowym EQ.",
    "rzemioslo": "v0.30.55: help krawiectwo/tailoring, garbarstwo/leatherworking, stolarstwo/carpentry, zaklinanie/enchanting oraz help craftmastery opisują aktualny Crafting 2.0.",
    "gracze": "v0.30.55: Social Suite obejmuje ignore, friends, AFK, WHO 2.0, whois, mail, board, LFG, kanały i mentoring.",
    "eq": "v0.30.55: crafted EQ może mieć jakość, krytyczny affix, upgrade +1..+10, runy/sockety oraz trwałe zaklęcie slotu.",
}.items():
    HELP_TOPICS.setdefault(_topic, [])
    if _line not in HELP_TOPICS[_topic]:
        HELP_TOPICS[_topic].append(_line)

from player.session import Session  # explicit current dependency
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

def _install_v0310_tech_help():
    from data.current_help import get_help_catalogs as _current_help_catalogs
    HELP_TOPICS = _current_help_catalogs()[0]
    HELP_TOPIC_ALIASES = _current_help_catalogs()[1]
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

LATEST_CHANGES_TITLE = "Soulbound v0.35.6 - Salvage Wszystko"

LATEST_CHANGES = [
    "v0.35.6: dodano salvage wszystko / rozloz wszystko — hurtowe rozkładanie wszystkich wolnych przedmiotów obsługiwanych przez Salvage.",
    "Założone EQ jest zawsze pomijane; startowy Moogle Board jest chroniony przed przypadkowym hurtowym rozłożeniem.",
    "Hurtowy Salvage agreguje raport odzyskanych materiałów, run i klejnotów, żeby nie spamować NVDA setkami komunikatów.",
]

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

from admin.help_refresh import refresh_help_truth_v11197  # explicit current dependency
refresh_help_truth_v11197()

from admin.help_refresh import refresh_public_help_surface_v11197  # explicit current dependency
refresh_public_help_surface_v11197()
