# -*- coding: utf-8 -*-
"""Soulbound v1.13.28 - final public HELP truth sweep.

Loaded near the end of the runtime manifest, after historical HELP patches,
UOSS, dungeons and global difficulty. This module is intentionally the final
player-facing truth layer: old milestone text may remain in source history,
but public HELP must describe the current runtime.
"""
from __future__ import annotations

import re

from core.bootstrap_economy_professions import TOOL_PROFESSION_MAP, VERSION
from core.classes_skills import CLASSES, RACES
from core.command_catalog import COMMAND_CATALOG
from core.profession_timing import TOOL_ACTION_BASE_SECONDS, TOOL_ACTION_MIN_SECONDS
from systems.items_resources import CLASS_EQUIPMENT_SLOT_DEFS
from world.equipment_help import HELP_TOPICS, HELP_TOPIC_ALIASES

HELP_TRUTH_CURRENT_VERSION_V11328 = str(VERSION)


def _help_lines_v11328(value):
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(line) for line in (value or ()) if str(line).strip()]


def _historical_help_line_v11328(line):
    folded = str(line).casefold()
    return any(
        marker in folded
        for marker in (
            "historycz",
            "dawnego wydania",
            "stary opis",
            "starsza warstwa",
            "nazwa starszej",
        )
    )


def _normalize_help_line_v11328(line, slot_count, topic=""):
    text = str(line)
    if _historical_help_line_v11328(text):
        return text

    # Safe current-progression replacements for known 1-600 axes only.
    # Do not blindly rewrite every number 400: a local subsystem may have its
    # own legitimate cap unrelated to Character/Class/Soul/profession growth.
    always_replacements = (
        ("maksymalnie 50 na Levelu 400", "maksymalnie 80 na Levelu 600"),
        ("50 na Levelu 400", "80 na Levelu 600"),
        ("10 na Levelu 1", "20 na Levelu 1"),
    )
    for old, new in always_replacements:
        text = text.replace(old, new)

    topic_key = str(topic or "").casefold()
    progression_topics = {
        "podstawy", "score", "level", "xp", "statystyki", "dusza",
        "soul", "aoe", "umiejetnosci", "skille", "kolejka",
        "profesje", "tempo_profesji", "narzedzia", "narzedzia200",
        "wiecej_ryb", "generator", "progresja600", "hp_mobow",
        "soul_xp_bloki", "hp_bossow_lochow", "expowiska",
        "krawiectwo", "garbarstwo", "stolarstwo", "zaklinanie",
        "jubilerstwo2", "archeologia", "kartografia", "inzynier",
        "klasy", "rasy", "materialy_eq", "sety_klasowe",
        "gildia kurierow", "kurierzy",
    }
    axis_markers = (
        "level postaci", "character level", "biegłość", "soul level",
        "soul weapon mastery", "skill level", "profesj", "narzędzi",
        "wędkarstwo", "górnictwo", "drwalstwo", "zielarstwo",
        "gotowanie", "alchemia", "kowalstwo", "jubilerstwo",
        "krawiectwo", "garbarstwo", "stolarstwo", "zaklinanie",
        "archeologia", "kartografia", "reputacja kurier",
    )
    if topic_key in progression_topics or any(
        marker in text.casefold() for marker in axis_markers
    ):
        for old, new in (
            ("1-400", "1-600"),
            ("1–400", "1–600"),
            ("do levelu 400", "do levelu 600"),
            ("do Levelu 400", "do Levelu 600"),
            ("na Levelu 400", "na Levelu 600"),
        ):
            text = text.replace(old, new)

    for old_slots in (13, 14, 15, 16):
        text = re.sub(
            rf"\b{old_slots}\s+logicznych",
            f"{slot_count} logicznych",
            text,
            flags=re.IGNORECASE,
        )

    # These were Generator-era cooldown contracts and are false today.
    stale_cooldown_fragments = (
        "cooldown i bazowa moc pochodzą z Generator Core",
        "krzywej mocy/cooldownu",
        "Damage, heal, guard, drain, boost i cooldown są wyliczane",
        "współdzielą cooldown wyboru",
    )
    if any(fragment.casefold() in text.casefold() for fragment in stale_cooldown_fragments):
        return ""

    # Positive old start-board claims are no longer valid.
    folded = text.casefold()
    if (
        "moogle board" in folded
        and "na starcie" in folded
        and "nie " not in folded
        and "nie jest" not in folded
    ):
        return ""

    return text


def refresh_help_truth_current_v11328():
    class_count = len(CLASSES)
    race_count = len(RACES)
    profession_count = len(set(TOOL_PROFESSION_MAP.values()))
    slot_count = len(CLASS_EQUIPMENT_SLOT_DEFS)

    # First clean every existing public topic, including niche historical modules.
    for topic, value in list(HELP_TOPICS.items()):
        cleaned = []
        for line in _help_lines_v11328(value):
            normalized = _normalize_help_line_v11328(
                line, slot_count, topic=topic
            )
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)
        HELP_TOPICS[topic] = cleaned

    HELP_TOPICS["wersja"] = [
        f"Aktualna wersja gameplay HELP: Soulbound v{VERSION}.",
        "HELP opisuje bieżący runtime; pełną historię zmian pokazuje changes / zmiany / changelog.",
        "Dokładne liczby konkretnego moba, skilla, EQ, receptury lub źródła sprawdzaj komendą runtime zamiast historycznej tabeli.",
    ]

    HELP_TOPICS["podstawy"] = [
        f"Soulbound ma obecnie {class_count} klas, {race_count} ras i {profession_count} profesji.",
        "Główne osie progresji postaci rozwijają się 1-600; bazowe statystyki postaci nie mają twardego limitu.",
        "Najważniejsze komendy: help, look/l, exits, hp, score, staty, dusza, eq, quest, profesje, atlas, prowadz/walk, con i k/atakuj.",
        "Generator uzupełnia brakujące/proceduralne wartości; ręcznie authored treść ma pierwszeństwo i nie jest globalnie nadpisywana tylko dlatego, że istnieje Generator.",
        "Soulbound jest projektowany jako długoterminowy grind bez klasycznego końca po jednym zestawie EQ: sklep, crafting, dropy, lochy i bossowie mają różne role.",
    ]

    HELP_TOPICS["progresja600"] = [
        "Character Level, Biegłość klas, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia rozwijają się 1-600.",
        "Bazowe statystyki postaci są bez twardego limitu.",
        "Nieskończone instancje mogą skalować zagrożenie dalej niż główna oś 600.",
        "score, level/lvl, xp, staty info, dusza info i profesje info pokazują bieżący postęp z runtime.",
    ]

    HELP_TOPICS["generator"] = [
        "Generator Core nie ma prawa spłaszczać ręcznie zaprojektowanej zawartości: authored wins, Generator uzupełnia braki i proceduralne rekordy.",
        "HP, nagrody i progresja korzystają ze wspólnych krzywych tam, gdzie system tego wymaga, ale ręczne bossy, questy, sklepy i specjalne kontrakty zachowują swoje jawne zasady.",
        "Dokładne wartości runtime sprawdzaj przez con, score, staty info, skill info, eq info, shop info, atlas, gdzie zdobyc i do czego.",
    ]

    HELP_TOPICS["statystyki"] = [
        "Sześć statystyk to Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.",
        "Bazowe statystyki nie mają twardego limitu. EQ, runy, sety, relikty i efekty zwiększają wartości efektywne.",
        "Fizyczne buildy opierają obrażenia głównie o właściwe kanały fizyczne, magiczne o właściwe kanały magiczne; konkretny skill pokazuje własne skalowanie przez help skill <nazwa>.",
        "Każde leczenie korzysta z Inteligencji i Siły Woli; Magic Attack zwiększa obrażenia magiczne, ale nie healing.",
        "Końcowa Szybkość wpływa na liczbę trafień zwykłego autoataku Broni Duszy; Haste osobno zwiększa serię.",
        "staty info pokazuje bazę, wartości efektywne, EXP statystyk i bonusy wyposażenia.",
    ]

    HELP_TOPICS["walka"] = [
        "k <mob> / atakuj <mob> rozpoczyna walkę realtime; con <mob> ocenia przeciwnika bez rozpoczynania walki; uciekaj/flee wycofuje z walki.",
        "Zwykły autoatak Broni Duszy wykonuje się niezależnie od auto-kolejki. Gotowy skill z kolejki może wykonać się w tej samej rundzie.",
        "Zwykłe skille klasowe nie mają cooldownu ponownego użycia. Specjalny timer istnieje tylko tam, gdzie jest częścią mechaniki, np. V-MAX.",
        "Zwykłe moby nie są papierem: runtime dokłada presję obrażeń, a wyższe rangi Elite/Rare/miniboss/boss są coraz groźniejsze.",
        "Przeciwnicy tej samej ogólnej kategorii mogą mieć okazjonalne ataki charakterystyczne, np. Mocny Cios, Ciężkie Uderzenie, Szybki Atak lub Magiczny Zryw.",
        "combatlog concise/normal/full oraz bufor walka sterują szczegółowością komunikatów pod NVDA.",
    ]

    HELP_TOPICS["aoe"] = [
        "aoe on włącza ofensywne efekty wielocelowe; aoe off ogranicza je do jednego przeciwnika.",
        "Umiejętność zachowuje własne zasady targetowania: diminishing, non-diminishing, losowe trafienia albo tylko zaangażowane cele.",
        "Gdy członek drużyny rozpoczyna lokalną walkę/AoE, pozostali uprawnieni członkowie w tej samej lokacji dołączają zgodnie z aktualną logiką party.",
        "Moby walczące z drużyną mogą atakować jej członków, a nie wyłącznie osobę, która rozpoczęła starcie.",
        "Szczegóły konkretnego skilla: help skill <nazwa> / skill info <nazwa>.",
    ]

    HELP_TOPICS["umiejetnosci"] = [
        f"Każda z {class_count} klas ma własny katalog umiejętności, a nauczony skill ma osobny Skill Level 1-600.",
        "Zwykłe skille klasowe nie mają cooldownu ponownego użycia; wyjątki są jawnie opisanymi specjalnymi mechanikami.",
        "Pasywki po nauczeniu działają automatycznie i nie zajmują slotów auto-kolejki.",
        "help skill <nazwa> pokazuje klasę, wymaganie, Manę, target, skalowanie, właściwości, Skill Level oraz specjalny timer, jeśli naprawdę istnieje.",
        "skills / skills all / skillnames / kodeksklasowy <klasa> pokazują bieżący katalog runtime.",
    ]
    HELP_TOPICS["skille"] = list(HELP_TOPICS["umiejetnosci"])

    HELP_TOPICS["kolejka"] = [
        "Auto-kolejka rozdziela skille według realnej roli; pasywki nie zajmują slotów.",
        "Na Character Level 1 każda dostępna kolejka ma 20 aktywnych slotów; co 10 Leveli dochodzi +1, do 80 na Levelu 600.",
        "kolejka dodaj <skill>, kolejka lista [fizyczna|magiczna|feedback], kolejka usuń <nr>, kolejka wyczyść, kolejka góra/dół i kolejka on/off zarządzają rotacją.",
        "Skill z kolejki nie zastępuje zwykłego autoataku Broni Duszy.",
    ]

    HELP_TOPICS["dusza"] = [
        "Broń Duszy ma Soul Level 1-600 i osobną Soul Weapon Mastery 1-600.",
        "Soul Weapon Mastery rozwija zwykły autoatak; skille klasowe rozwijają własny Skill Level.",
        "Liczba trafień autoataku wynika z końcowej Szybkości, a Haste zwiększa serię dodatkowo.",
        "dusza info pokazuje Soul XP, Tier, Próby i następny cel.",
        "forma lista / forma wybierz / forma auto zarządza formą Broni Duszy; starsze relic/relikt pozostają zgodnymi aliasami.",
    ]

    HELP_TOPICS["profesje"] = [
        f"Soulbound ma {profession_count} profesji 1-600 i tyle samo przypisanych narzędzi; narzędzie kupuje się tylko raz na postać.",
        "Zbieractwo: Wędkarstwo, Górnictwo, Drwalstwo i Zielarstwo. Rzemiosła: Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo i Zaklinanie. Eksploracja: Archeologia i Kartografia.",
        "zamowienia / zamówienia obsługuje wszystkie profesje; zlecenia odnawiają się niezależnie zgodnie z ich godzinnym cooldownem.",
        "Czasy aktywności są authored, a nie losowane przez Generator. help tempo_profesji pokazuje bieżące czasy bazowe i minimalne.",
        "Cztery podstawowe zbieractwa mają rzadki wyjątkowo obfity zbiór: 4-8% zależnie od progresji, dodatkowy pełny urobek i x1.75 XP profesji/narzędzia.",
        "Rzadkie ryby, żyły, geody, drewno i zioła zachowują własne jackpoty; pierwsze odkrycia Archeologii/Kartografii mają własne premie.",
    ]

    timing_lines = [
        "Tempo profesji jest ręcznie zaprojektowane i skaluje się wraz z poziomem narzędzia/profesji do ustalonego minimum.",
    ]
    tool_labels = {
        "fishing": "Wędkarstwo",
        "mining": "Górnictwo",
        "woodcutting": "Drwalstwo",
        "crafting": "Kowalstwo",
        "cooking": "Gotowanie",
        "herbalism": "Zielarstwo",
        "alchemy": "Alchemia",
        "jewelcrafting": "Jubilerstwo",
        "tailoring": "Krawiectwo",
        "leatherworking": "Garbarstwo",
        "carpentry": "Stolarstwo",
        "enchanting": "Zaklinanie",
        "archaeology": "Archeologia",
        "cartography_profession": "Kartografia",
    }
    for tool_type, base in TOOL_ACTION_BASE_SECONDS.items():
        minimum = TOOL_ACTION_MIN_SECONDS[tool_type]
        timing_lines.append(
            f"{tool_labels.get(tool_type, tool_type)}: start {base} s, minimum {minimum} s."
        )
    HELP_TOPICS["tempo_profesji"] = timing_lines

    HELP_TOPICS["crafting"] = [
        "Crafting korzysta z realnych składników, poziomu profesji, narzędzia, stacji i bieżącej receptury.",
        "receptury <profesja>, receptury mozliwe, braki receptura <nazwa>, gdzie zdobyc <item> oraz do czego <item> służą do planowania bez zgadywania.",
        "Jakość craftu może zwiększać moc przedmiotu, a krytyczny craft może dodać affix zgodnie z bieżącym systemem jakości.",
        "Mistrzowska Inspiracja ma około 3-6% szansy zależnie od progresji i daje x2 Profession/Tool XP; nie tworzy darmowego duplikatu EQ.",
        "Kowalstwo Masterwork jest źródłem customizacji: właściwość materiałowa i rosnące sockety. Jubilerstwo skupia się na socketach i precyzyjnym affixie.",
    ]

    HELP_TOPICS["quest"] = [
        "quest pokazuje aktywne zadania; quest godzinne pokazuje odnawialne zlecenia; questy ukończone pokazuje historię.",
        "quest list <NPC>, accept quest <numer>, oddaj quest <numer>, quest info <numer> i quest porzuc <numer> obsługują dziennik.",
        "Godzinne questy odnawiają się niezależnie; postęp aktywności jest liczony od momentu/przyjętego celu zgodnie z kontraktem konkretnego zadania.",
        "Automatyczne niemanualne wypłaty questa mogą dostać rzadką premię wykonania: repeatable 2% (+25%), zwykłe 6% (+50%), większe legendary/world-boss/mini-dungeon 8% (+75%).",
        "Ręcznie chronione manualne wypłaty pozostają dokładne i nie dostają tej automatycznej premii.",
    ]
    HELP_TOPICS["questy"] = list(HELP_TOPICS["quest"])

    HELP_TOPICS["druzyny"] = [
        "Drużyna działa lokalnie: do wspólnej walki i większości wspólnych akcji liczą się członkowie stojący w tej samej lokacji.",
        "Nie ma kary drużynowej za wspólne zabicie: każdy uprawniony obecny członek dostaje własne pełne Character XP, Class XP, Soul XP, stat XP i bazową pulę waluty.",
        "Udane wspólne dropy korzystają z aktualnej logiki party; samo dołączenie do party nie obniża wartości nagrody.",
        "druzyna cel i druzyna gotowi obsługują wspólny cel/ready-check; Party Combo i wspólny Ultimate mają osobne tematy help combo / help ultimate.",
        "Lider może inicjować wybrane wspólne kontrakty, np. handel morski, dla obecnych członków zgodnie z zasadami danego systemu.",
    ]
    HELP_TOPICS["party"] = list(HELP_TOPICS["druzyny"])
    HELP_TOPICS["drużyna"] = list(HELP_TOPICS["druzyny"])

    HELP_TOPICS["loot"] = [
        "Każdy prawdziwy mob ma dodatkowy roll Trofeum z potyczki zależny od rangi: Normal 8%, Elite 18%, Rare 32%, miniboss 50%, boss 75%, World Boss 100%.",
        "Losowe klasowe EQ z ciała ma osobną hierarchię v1.13.29: Normal 7%, Elite 18%, Rare 28%, miniboss 40%, boss 55%, World Boss 70%. Rare generowany jako rare_mob jest poprawnie rozpoznawany jako Rare.",
        "Trofeum skaluje się z etapem i ma sensowną wartość sprzedaży; nie zastępuje authored dropów, Soul Shardów, EQ ani nagród bossowych.",
        "Stare zwykłe rodziny z pustym/potionowym lootem mogą mieć charakterystyczny materiał, np. szczur, goblin, bandyta lub ruiny.",
        "Named world-boss uniques są skalowane do progresji źródłowego bossa, a ich bezpośredni authored drop ma co najmniej 60% szansy dla World Bossa. Zwykłe materiały i mikstury zachowują własne authored chance.",
        "Krypta zachowuje własną drabinę rarity, losowych affixów, power/properties i socketów; od v1.13.29 głębsze źródło zwiększa również samą szansę na Epic/Legendary/Mythic.",
        "historiadropow / drophistory oraz loot rare+/epic+/legendary/all/off pomagają śledzić wartościowe dropy pod NVDA.",
    ]

    HELP_TOPICS["gamefeel"] = [
        "Globalny Game Feel nie polega na jednym blanket jackpocie. Każda aktywność ma własny rodzaj rzadkiej nagrody.",
        "Gathering: 4-8% na wyjątkowo obfity zbiór, dodatkowy pełny urobek i x1.75 XP profesji/narzędzia.",
        "Crafting: około 3-6% na Mistrzowską Inspirację i x2 Profession/Tool XP, bez darmowego kopiowania EQ.",
        "Questy: rzadkie premie do automatycznych niemanualnych wypłat; manualne kontrakty zachowują dokładną kwotę.",
        "Eksploracja: nowe miejsce ma 2.5% szansy na ukryte znalezisko; sekretne/ukryte miejsce 8% i wyższą wartość.",
        "Walka: zwykłe moby mają realną presję oraz okazjonalne ataki charakterystyczne; loot ma osobny rank/stage trophy roll.",
        "Nieskończone instancje po etapie 600 mogą dropić trwałe warianty Rezonans Głębi: głębsze źródło dalej zwiększa moc i wartość konkretnego egzemplarza.",
    ]

    HELP_TOPICS["ekwipunek"] = [
        f"Aktualna siatka ma {slot_count} logicznych typów EQ; podwójne są pierścienie, talizmany, kolczyki i akcesoria.",
        "eq info pokazuje statystyki, properties, sockety, sety i bieżące wymagania. porownaj <item> porównuje z aktualnie założonym sprzętem.",
        "Klasowe EQ klas fizycznych daje Siłę + Zręczność + Kondycję; magiczne daje Inteligencję + Siłę Woli + Kondycję.",
        "Sklep klasowy ma trzy realne style: ofensywny, pancerny i zbalansowany. Mieszanie stylów tej samej klasy nadal liczy się do progów setu 2/4/6/8.",
        "Źródła EQ mają osobną tożsamość: sklep = przewidywalny set, Kowalstwo = masterwork/customizacja, Krypta = rarity+losowy affix, boss = mocniejszy/unikalny drop, UOSS = specjalne efekty/wardy/status-proof.",
        "shop info i porownaj czytają linię Tożsamość EQ. Gdy przedmiot ma określony etap źródła, czytają też Etap źródła EQ.",
        "Bossowy set klasowy przy tym samym mastery ma mocniejszy pakiet properties niż sklepowy odpowiednik; named boss uniques mają floor mocy zależny od źródła.",
        "Rezonans Głębi działa ponad etapem źródła 600 w nieskończonych instancjach. Nie tworzy wymagania Biegłości 601+: wymaganie założenia pozostaje w normalnej progresji 1-600, a rośnie moc konkretnego dropu.",
        "EQ nie jest automatycznie bindowane tylko dlatego, że zostało zdobyte; konkretne wyjątki UOSS mogą mieć własne zasady pickup/bind.",
    ]
    HELP_TOPICS["eq"] = list(HELP_TOPICS["ekwipunek"])

    HELP_TOPICS["zrodla_eq"] = [
        "Sklep klasowy: przewidywalny build, trzy style i pewne wymagania.",
        "Kowalstwo: Masterwork, właściwość materiałowa i sockety — najlepsza ścieżka customizacji.",
        "Jubilerstwo: sockety i precyzyjny affix.",
        "Corpse drop: losowy materiał, wariant i profil; dobry roll może być atrakcyjny dla konkretnego buildu.",
        "Krypta: rarity + losowy affix + rosnące properties/sockety; boss Krypty daje unikalny relikt.",
        "Boss/world boss: named unique lub boss-set skalowany do źródła; trudniejsze źródło nie powinno przegrywać z wcześniejszą drabiną tylko przez historyczne wartości.",
        "Post-600: Krypta, Wieża i Magitek mogą nadać EQ Rezonans Głębi. Etap źródła może wtedy rosnąć ponad 600, ale required_mastery/poziom gracza nie rośnie ponad istniejący cap.",
        "UOSS Superboss: specjalne efekty, wardy, odporności/status-proof i relikty. shop info / eq info / porownaj pokazują realne dane.",
    ]

    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę; shop info <nr> pokazuje pełny opis, wymagania, Tożsamość EQ, Etap źródła i porównanie.",
        "Brakujące price=None/0 w prawdziwej ofercie NIE oznacza darmowego itemu: sklep stosuje bezpieczny progression price floor.",
        "Prawdziwe token-only jest jawne: zerowy koszt pieniężny + dodatni koszt tokenu. Wtedy HELP/lista pokazuje token, a nie mylące 0 srebra.",
        "Rabat Charyzmy obniża część pieniężną, nie koszt tokenów.",
        "shop, shop info i kup używają tej samej kanonicznej ścieżki ceny.",
        "sell/sprzedaj korzysta z aktualnych floorów wartości; stare sell_* lub stara cena katalogowa nie mogą automatycznie robić wartościowego loot/EQ śmieciowym.",
    ]

    HELP_TOPICS["sprzedaz"] = [
        "sell / sprzedaj sprzedaje dozwolone przedmioty; sell all / sprzedaj wszystko pomija założone i chronione przedmioty.",
        "Surowce i loot mają aktualne floor wartości zależne od ich progresji/rarity; jawna stara cena nie może zaniżać nowoczesnego loot/EQ.",
        "Rzadkie ryby, warianty zasobów, geody i trofea bojowe mają własne mnożniki/wycenę.",
        "Ręcznie chronione manualne wartości mogą pozostać dokładne tam, gdzie system jawnie tego wymaga.",
    ]

    HELP_TOPICS["materialy_eq"] = [
        f"Materiałowe corpse-drop EQ obejmuje aktualną siatkę {slot_count} logicznych typów i progresję wymaganej Biegłości 1-600.",
        "Każdy wariant ma source_progression_stage równy required_mastery i własną tożsamość dropu z moba.",
        "Materiał, losowy wariant, statystyki, properties, rarity i sockety tworzą osobny build; nie jest to kopia sklepu ani craftu.",
        "eq info / porownaj pokazują realny roll konkretnego przedmiotu.",
    ]

    HELP_TOPICS["sety_klasowe"] = [
        f"Każda z {class_count} klas ma klasowe EQ w aktualnej siatce {slot_count} logicznych typów.",
        "Bonusy setów pozostają na progach 2/4/6/8 części; mieszane style tej samej klasy liczą się wspólnie.",
        "Sklepowe style mają realnie różne properties, a bossowe sety przy tym samym mastery mają mocniejszy pakiet properties.",
        "sety / sety info / sety <klasa>, shop info, eq info i porownaj pokazują bieżące dane.",
    ]

    HELP_TOPICS["krypta"] = [
        "Zwykła i Mityczna Krypta rosną na każdym kolejnym piętrze; boss co 10 pięter jest dodatkowym skokiem.",
        "Trudność, EXP i nagrody korzystają z aktualnych warstw Crypt Overdrive + Global Difficulty; con pokazuje bieżącą ocenę konkretnego przeciwnika.",
        "Loot Krypty ma rarity i losowy affix; wyższa rarity zwiększa affix, obronę/power, properties i sockety. Głębsze źródło ma jawny Etap źródła EQ.",
        "Od v1.13.29 rarity chance rośnie z etapem źródła. Przy etapie 600 zwykły drop używa wag 30/30/20/13/7 dla Common/Rare/Epic/Legendary/Mythic, a boss 3/17/30/28/22.",
        "Bossowie Krypty mają unikalne relikty skalowane z piętrem. Po runie może pojawić się Dungeon Summary.",
        "Nieskończona część może skalować zagrożenie dalej niż główna progresja 600.",
        "Po etapie źródła 600 corpse-EQ Krypty dostaje Rezonans Głębi: kolejne głębokości dalej podnoszą staty/properties/sockety i wartość sprzedaży bez wymagania Biegłości ponad 600.",
    ]

    HELP_TOPICS["wieza"] = [
        "Wieża Astralna i Mityczna Wieża rosną poziom po poziomie; boss co 10 poziomów jest dodatkowym skokiem.",
        "Tower Overdrive i Global Difficulty działają razem; zagrożenie może rosnąć dalej niż główna progresja 600.",
        "Po etapie źródła 600 EQ z Wieży dostaje Rezonans Głębi, a waluta z nieskończonych poziomów dalej rośnie zamiast zatrzymywać się na ekonomii stage 600.",
        "UOSS Superbossowie są osobnymi encounterami świata, nie rotacją bossów Wieży.",
        "astralportal i mapa instancji pokazują bieżące checkpointy/progres.",
    ]

    HELP_TOPICS["ocean"] = [
        "Ocean 2.0 obejmuje statki graczy, szlaki morskie, mapy skarbów, handel morski, podwodne ruiny i głębinowe Wędkarstwo.",
        "statek pokazuje/rozwija Kadłub, Żagle, Ładownię i Nawigację; zegluj / sail obsługuje ruch po sektorach.",
        "handel morski pokazuje oferty; handel morski wez <nr>, handel morski oddaj, handel morski porzuc obsługują kontrakt. Zmiana wód/objazd nie zeruje aktywnego handlu, dopóki pozostajesz na morzu.",
        "Lider może przekazać przyjęty handel obecnym członkom drużyny zgodnie z aktualną logiką party.",
        "Połów głębinowy używa zwykłego Wędkarstwa/Wędki 1-600, nie jest osobną profesją.",
    ]

    HELP_TOPICS["superbossy"] = [
        "superbosses pokazuje unikalne wyzwania UOSS, wymagania i zaliczenia; superboss <nazwa> obsługuje wejście.",
        "Superbossowie mają własne mechaniki, lockouty, tokeny, named uniques i sklepy; nie są zwykłą rotacją bossów Krypty/Wieży.",
        "Black Rabite: osobisty Moogle Steel, pula unikalnych dropów i warunkowy Moogle Board dla Cyborga. Moogle Board nie jest startowym itemem.",
        "Każdy legalny clear UOSS zachowuje osobistą nagrodę tokenową; Black Rabite, Yiazmat i Odin zachowują też osobisty unique roll dla uprawnionych uczestników zgodnie z lockoutem.",
        "Odin/Yiazmat/Culex i inne UOSS źródła zachowują specjalne tokeny oraz własne efekty EQ. shop info / eq info pokazują realny koszt i właściwości.",
        "Token-only jest wyświetlany jako koszt tokenu bez fałszywego 0 srebra.",
    ]

    HELP_TOPICS["archeologia"] = [
        "Archeologia jest profesją 1-600. Pędzel Archeologa kupujesz tylko raz na postać.",
        "W odpowiednich ruinach/kryptach/świątyniach/archiwach użyj wykop; archeologia kolekcja pokazuje znaleziska.",
        "Pierwsze odkrycie konkretnego znaleziska ma premię XP i wysoką wartość kolekcjonerską.",
        "Archeologia ma odnawialne zlecenia i zamówienia; szczegóły pokazuje bieżący NPC/quest runtime.",
    ]

    HELP_TOPICS["kartografia"] = [
        "Kartografia jest profesją 1-600. Kompas Mierniczy kupujesz tylko raz na postać.",
        "mapuj mierzy odwiedzaną lokację; pierwszy pomiar dopisuje ją do Atlasu Kartografa i daje premię odkrywcy.",
        "Kartografia ma odnawialne zlecenia i zamówienia; atlas odkrycia pokazuje długoterminową eksplorację świata.",
    ]

    # Group canonical commands under the actual current HELP topics.
    command_help_groups = {
        "help": "podstawy",
        "attack": "walka",
        "consider": "walka",
        "wimpy": "walka",
        "skill": "umiejetnosci",
        "skills": "umiejetnosci",
        "spells": "umiejetnosci",
        "learn": "umiejetnosci",
        "skillqueue": "kolejka",
        "soul": "dusza",
        "professions": "profesje",
        "tools": "profesje",
        "fish": "profesje",
        "mine": "profesje",
        "woodcut": "profesje",
        "herb": "profesje",
        "craft": "crafting",
        "cook": "crafting",
        "alchemy": "crafting",
        "jewelcraft": "crafting",
        "recipes": "crafting",
        "craftorders": "profesje",
        "quests": "quest",
        "questaccept": "quest",
        "turnin": "quest",
        "equipment": "ekwipunek",
        "equip": "ekwipunek",
        "compareeq": "ekwipunek",
        "classsets": "sety_klasowe",
        "shop": "sklepy",
        "buy": "sklepy",
        "sell": "sprzedaz",
        "ship": "ocean",
        "sail": "ocean",
        "oceantreasure": "ocean",
        "oceantrade": "ocean",
        "superbosses": "superbossy",
        "superboss": "superbossy",
    }
    HELP_TOPIC_ALIASES.update(command_help_groups)
    HELP_TOPIC_ALIASES.update({
        "gra feel": "gamefeel",
        "game feel": "gamefeel",
        "gamefeel": "gamefeel",
        "o kurde": "gamefeel",
        "dropy": "loot",
        "drop": "loot",
        "loot": "loot",
        "zrodla eq": "zrodla_eq",
        "źródła eq": "zrodla_eq",
        "zrodla_eq": "zrodla_eq",
        "source progression": "zrodla_eq",
        "sprzedaz": "sprzedaz",
        "sprzedaż": "sprzedaz",
        "crafting": "crafting",
        "rzemioslo": "crafting",
        "rzemiosło": "crafting",
    })

    COMMAND_CATALOG.bind_help(HELP_TOPICS, HELP_TOPIC_ALIASES)

    return {
        "version": HELP_TRUTH_CURRENT_VERSION_V11328,
        "class_count": class_count,
        "race_count": race_count,
        "profession_count": profession_count,
        "slot_count": slot_count,
        "topic_count": len(HELP_TOPICS),
    }


HELP_TRUTH_REFRESH_V11328 = refresh_help_truth_current_v11328()


def help_freshness_audit_v11328():
    errors = []
    slot_count = int(HELP_TRUTH_REFRESH_V11328["slot_count"])

    def topic_text(name):
        return " ".join(_help_lines_v11328(HELP_TOPICS.get(name, [])))

    # Scan every public topic, not only a hand-picked shortlist.
    forbidden = (
        "50 na Levelu 400",
        "50 na Levelu 600",
        "10 na Levelu 1",
        "cooldown i bazowa moc pochodzą z Generator Core",
        "krzywej mocy/cooldownu",
        "współdzielą cooldown wyboru",
    )
    stale_rows = []
    for topic, value in HELP_TOPICS.items():
        for line in _help_lines_v11328(value):
            if _historical_help_line_v11328(line):
                continue
            folded = line.casefold()
            bad = next(
                (needle for needle in forbidden if needle.casefold() in folded),
                None,
            )
            if bad:
                stale_rows.append(f"{topic}:{bad}")
            if (
                ("1-400" in line or "1–400" in line)
                and "progresja400" not in str(topic).casefold()
                and any(
                    marker in folded
                    for marker in (
                        "level postaci", "character level", "biegłość",
                        "soul level", "soul weapon mastery", "skill level",
                        "profesj", "narzędzi", "wędkarstwo", "górnictwo",
                        "drwalstwo", "zielarstwo", "gotowanie", "alchemia",
                        "kowalstwo", "jubilerstwo", "krawiectwo",
                        "garbarstwo", "stolarstwo", "zaklinanie",
                        "archeologia", "kartografia", "reputacja kurier",
                    )
                )
            ):
                stale_rows.append(f"{topic}:stale main-axis 1-400")
            for old_slots in (13, 14, 15, 16):
                if re.search(rf"\b{old_slots}\s+logicznych", line, re.IGNORECASE):
                    stale_rows.append(f"{topic}:stale {old_slots} slot grid")
    if stale_rows:
        errors.append("stale public HELP rows: " + ", ".join(stale_rows[:40]))

    expected = {
        "podstawy": ("authored", "1-600"),
        "walka": ("nie mają cooldownu", "charakterystyczne"),
        "aoe": ("aoe on", "drużyn"),
        "profesje": ("4-8%", "x1.75"),
        "tempo_profesji": ("Górnictwo: start 40 s", "Wędkarstwo: start 16 s"),
        "crafting": ("3-6%", "x2"),
        "quest": ("2%", "6%", "8%", "manual"),
        "druzyny": ("Nie ma kary drużynowej", "pełne"),
        "loot": ("Normal 8%", "World Boss 100%", "Rare 28%", "World Boss 70%", "60%"),
        "gamefeel": ("2.5%", "8%", "x1.75"),
        "ekwipunek": (str(slot_count), "Tożsamość EQ", "Etap źródła EQ"),
        "zrodla_eq": ("Kowalstwo", "Krypta", "UOSS"),
        "sklepy": ("NIE oznacza darmowego", "token-only", "kanonicznej"),
        "krypta": ("rarity", "Etap źródła EQ", "30/30/20/13/7", "3/17/30/28/22"),
        "ocean": ("handel morski porzuc", "nie zeruje"),
        "superbossy": ("Moogle Board nie jest startowym", "Token-only", "osobistą nagrodę tokenową"),
    }
    for topic, needles in expected.items():
        text = topic_text(topic)
        if not text:
            errors.append(f"HELP {topic}: empty")
            continue
        for needle in needles:
            if needle.casefold() not in text.casefold():
                errors.append(f"HELP {topic}: missing current contract {needle}")

    # Important command families must resolve to a real topic after final binding.
    critical_commands = (
        "help", "attack", "consider", "skill", "skillqueue", "soul",
        "professions", "tools", "craft", "recipes", "quests", "equipment",
        "compareeq", "shop", "buy", "sell", "ship", "sail", "oceantrade",
        "superbosses", "superboss",
    )
    snapshot = COMMAND_CATALOG.snapshot()
    definitions = snapshot["commands"]
    for command in critical_commands:
        row = definitions.get(command)
        if not row or not row.get("help_topic"):
            errors.append(f"command HELP binding missing: {command}")

    return {
        "version": HELP_TRUTH_CURRENT_VERSION_V11328,
        "topics_scanned": len(HELP_TOPICS),
        "critical_commands_checked": len(critical_commands),
        "help_bound_count": snapshot["help_bound_count"],
        "error_count": len(errors),
        "errors": errors,
    }


HELP_FRESHNESS_AUDIT_V11328 = help_freshness_audit_v11328()
if HELP_FRESHNESS_AUDIT_V11328["error_count"]:
    raise RuntimeError(
        "HELP Freshness Audit v1.13.28 failed: "
        + "; ".join(HELP_FRESHNESS_AUDIT_V11328["errors"][:80])
    )
