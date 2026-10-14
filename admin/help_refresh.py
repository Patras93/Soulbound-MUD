from core.legacy_function_binding_v410 import bind_legacy_function_v410 as _sb410_bind

import admin.v410_help_refresh as _sb410_mod_v410_help_refresh
import admin.v410_help_audits as _sb410_mod_v410_help_audits

# v6.00.0: insert all historically aliased HELP targets before the earliest
# old HELP/alias audits run. Keep the v4 catalog factory byte-for-byte intact.
_V600_EARLY_HELP_TARGETS = {
        'alchemia': ['Alchemia: korzystaj z moździerza, ziół i poznanych receptur.'],
        'atlas': ['Atlas: lista poznanych zasobów, ryb, rud oraz odkryć świata.'],
        'charyzma': ['Charyzma: cecha postaci wpływająca na interakcje społeczne.'],
        'druzyny': ['Drużyny: zapraszaj graczy, korzystaj z pomocy w walce i wspólnych zadań.'],
        'drwalstwo': ['Drwalstwo: ścinaj drzewa piłą i przerabiaj drewno w istniejącym rzemiośle.'],
        'dusza': ['Dusza: rozwój duszy postaci i Broni Duszy.'],
        'ekwipunek': ['Ekwipunek: sprawdzaj, zakładaj i zdejmuj przedmioty.'],
        'gornictwo': ['Górnictwo: wydobywaj różne rudy kilofem, rozwijając profesję i narzędzie.'],
        'gracze': ['Gracze: komunikacja, drużyny, lista online i wspólne wyprawy.'],
        'klasy': ['Klasy: postacie wieloklasowe i umiejętności dostępne u nauczycieli.'],
        'nauczyciele': ['Nauczyciele: wpisz learn w ich pokoju, aby sprawdzić dostępne umiejętności.'],
        'nazwy_skilli': ['Nazwy umiejętności sprawdzisz w kodeksie klasowym i u nauczyciela.'],
        'odmiana_imienia': ['Odmiana imienia służy poprawnym komunikatom postaci w języku polskim.'],
        'pieniadze': ['Waluta świata: sto srebra to jedno złoto; milion złota to jeden mithril.'],
        'podstawy': ['Podstawy: help, look, exits, status, ekwipunek, profesje i questy.'],
        'pojemniki': ['Pojemniki: służą do przechowywania materiałów i przedmiotów postaci.'],
        'profesje': ['Profesje: rozwijaj czynności i własne narzędzia; nowe zawody: profesje6 lista.'],
        'rasy': ['Rasy: pochodzenie postaci i jego cechy, dostępne podczas tworzenia postaci.'],
        'receptury': ['Receptury: wykorzystuj materiały, aby tworzyć przedmioty.'],
        'rzemioslo': ['Rzemiosło: przerabiaj surowce na użyteczne wyposażenie i materiały.'],
        'sklepy': ['Sklepy: sprawdzaj ofertę sprzedawców i kupuj tylko potrzebne przedmioty.'],
        'smierc': ['Śmierć: postać odradza się w Świątyni Odrodzenia; postęp zostaje zachowany.'],
        'statystyki': ['Statystyki: Siła, Zręczność, Kondycja, Inteligencja i Wola.'],
        'umiejetnosci': ['Umiejętności: learn u nauczyciela; pełna lista w kodeksie klasowym.'],
        'wedkarstwo': ['Wędkarstwo: łów ryby w odpowiednich wodach, używając wędki.'],
        'zielarstwo': ['Zielarstwo: zbieraj zioła i wykorzystuj je w gotowaniu oraz alchemii.'],
        'zwloki': ['Zwłoki: po walce sprawdź ciało przeciwnika, aby odzyskać łupy i klucze.'],

}
for _topic_v600, _lines_v600 in _V600_EARLY_HELP_TARGETS.items():
    HELP_TOPICS.setdefault(_topic_v600, list(_lines_v600))




# ============================================================
# v0.27.1 - FINAL HELP/ATLAS TRUTH LAYER
# Pomoce nie przechowują kopii liczb balansu. Opisują dawny Generator Core, a komendy
# szczegółowe (skill info, atlas, con, score) czytają aktualne wygenerowane dane.
# ============================================================
def refresh_generator_help_v0271(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: refresh_generator_help_v0271")
refresh_generator_help_v0271 = _sb410_bind(_sb410_mod_v410_help_refresh.refresh_generator_help_v0271, globals())

refresh_generator_help_v0271()

# ============================================================
# v0.30.10 - FINAL HELP AUDIT
# Najnowsza warstwa nadpisuje historyczne teksty, które kłóciły się z realnym
# gameplayem. `help` pozostaje kategoriowym indeksem i prowadzi do tych tematów.
# ============================================================
def refresh_help_v03010(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: refresh_help_v03010")
refresh_help_v03010 = _sb410_bind(_sb410_mod_v410_help_refresh.refresh_help_v03010, globals())

refresh_help_v03010()

# ============================================================
# v0.30.11 - PARTY FOLLOW + HISTORY BUFFERS + PLAYER TRADING HELP AUDIT
# ============================================================
def refresh_help_v03011(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: refresh_help_v03011")
refresh_help_v03011 = _sb410_bind(_sb410_mod_v410_help_refresh.refresh_help_v03011, globals())

refresh_help_v03011()

# v0.30.12 - aktualizacja HELP po zmianie świata i progresji terenów.
HELP_TOPICS.setdefault("podstawy", []).append(
    "v0.30.12: rekomendacje i zakresy terenów korzystają z Levelu postaci, a nie z Biegłości klasy."
)
HELP_TOPICS.setdefault("poruszanie", []).append(
    "Stali NPC nie dzielą już jednego pokoju: gdy dawniej kilku NPC stało razem, otrzymali osobne pomieszczenia; prowadz <NPC> prowadzi bezpośrednio do jego pokoju."
)
HELP_TOPICS.setdefault("expowiska", []).append(
    "Dobór expowisk i zwykłych regionów świata opiera się na Levelu postaci 1-400. Biegłość klasy nadal rozwija klasę i odblokowuje skille/EQ, ale nie określa terenu."
)
HELP_TOPICS.setdefault("poruszanie", []).append(
    "v0.30.13: generator topologii zachowuje ręcznie zaprojektowany semantic backbone ważnych lokacji; proceduralne rozszerzenia są dołączane bez zrywania fabularnych przejść."
)
HELP_TOPICS.setdefault("generator", []).append(
    "Full World Topology Audit v0.30.13 sprawdza cały statyczny świat: osiągalność, powrót, spójność stref, wzajemność przejść, semantic backbone i kolejność prób."
)

# v0.30.14 - FULL RECIPE TEXT CONSISTENCY PASS
# dawny Generator Core przelicza progi i ilości składników. Starsze opisy były
# ręcznie wpisane i mogły po generacji podawać inny level/ilość niż realna
# receptura. Od tej wersji liczby widoczne dla gracza są synchronizowane z
# aktywną definicją runtime.
def refresh_recipe_descriptions_v03014():
    changed_levels = 0
    changed_quantities = 0
    for table_name in ("CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES"):
        table = globals().get(table_name, {}) or {}
        for recipe in table.values():
            desc = str(recipe.get("desc", "") or "")
            if not desc:
                continue
            level = max(1, int(recipe.get("min_profession_level", recipe.get("generator_level", 1)) or 1))
            # Każde wystąpienie "level N" w opisie receptury jest progiem
            # tej receptury; inne poziomy są przechowywane w osobnych polach.
            new_desc, count = re.subn(r"(?i)\blevel\s+\d+\b", f"level {level}", desc)
            if count and new_desc != desc:
                changed_levels += 1
                desc = new_desc

            ingredients = recipe.get("ingredients") or {}
            if len(ingredients) == 1:
                actual_qty = max(1, int(next(iter(ingredients.values())) or 1))
                # Synchronizuj pierwszy tekstowy licznik "X sztuk(i)" odnoszący
                # się do pojedynczego składnika. Nie dotykamy liczby produktu.
                m = re.search(r"(?i)\b\d+\s+sztuk(?:a|i|ę)?\b", desc)
                if m:
                    old = m.group(0)
                    suffix = old[old.find(' '):]
                    replacement = f"{actual_qty}{suffix}"
                    if replacement != old:
                        desc = desc[:m.start()] + replacement + desc[m.end():]
                        changed_quantities += 1
            recipe["desc"] = desc
    return {"level_descriptions_fixed": changed_levels, "ingredient_descriptions_fixed": changed_quantities}

V03014_RECIPE_TEXT_AUDIT = refresh_recipe_descriptions_v03014()

# ============================================================
# v0.30.16 - FULL EQUIPMENT NAME AUDIT / UNIQUE PROGRESSION NAMES
# ============================================================
# W v0.30.16 klasowe EQ było formalnie unikalne, ale kolejne progi różniły
# się niemal wyłącznie sufiksem +10, +20, ... +400. Dla czytnika ekranu
# brzmiało to jak ten sam przedmiot z inną cyfrą. Od v0.30.16 Biegłość
# pozostaje wymaganiem/opisem, natomiast sama nazwa dostaje unikalny epitet.
# ID, statystyki, ceny, sety, dropy i wymagania pozostają bez zmian.
V03016_EQ_MASTERY_EPITHETS = {
    1: "Początku",
    10: "Próby",
    20: "Hartu",
    30: "Szlaku",
    40: "Przebudzenia",
    50: "Żaru",
    60: "Przełomu",
    70: "Triumfu",
    80: "Chwały",
    90: "Weterana",
    100: "Mistrzostwa",
    110: "Niezłomności",
    120: "Dominacji",
    130: "Dziedzictwa",
    140: "Szczytu",
    150: "Potęgi",
    160: "Przeznaczenia",
    170: "Arcymistrza",
    180: "Wiecznego Marszu",
    190: "Nieugiętości",
    200: "Wieczności",
    210: "Pradawnego Echa",
    220: "Korony",
    230: "Gwiezdnego Progu",
    240: "Transcendencji",
    250: "Bezkresu",
    260: "Nieśmiertelności",
    270: "Nieskończonego Szlaku",
    280: "Astralnego Wzniesienia",
    290: "Wielkiego Przełomu",
    300: "Pradawnej Potęgi",
    310: "Odwiecznej Chwały",
    320: "Pierwotnego Dziedzictwa",
    330: "Nieugaszonego Żaru",
    340: "Bezgwiezdnego Horyzontu",
    350: "Mitycznej Korony",
    360: "Absolutnego Mistrzostwa",
    370: "Władzy nad Losem",
    380: "Końca Świata",
    390: "Ostatniej Granicy",
    400: "Transcendentnego Dziedzictwa",
    410: "Przekroczenia",
    420: "Gwiezdnego Tronu",
    430: "Wiecznego Echa",
    440: "Serca Otchłani",
    450: "Korony Gwiazd",
    460: "Sądu Horyzontu",
    470: "Nieskończonego Pulsu",
    480: "Kosmicznej Pieczęci",
    490: "Pradawnego Rezonansu",
    500: "Świtu Absolutu",
    510: "Drogi Przeznaczenia",
    520: "Oka Wszechświata",
    530: "Wiecznej Iskry",
    540: "Transcendentnego Znaku",
    550: "Głosu Nieskończoności",
    560: "Ostatecznego Horyzontu",
    570: "Duszy Kosmosu",
    580: "Korony Wieczności",
    590: "Apogeum",
    600: "Absolutu Duszy",
}

# v1.28.3: final authored names for every milestone 610-800.
# Keep the historical 1-600 names, and legacy item aliases, unchanged.
from systems.equipment_crafting import _class_equipment_tier_label as _class_tier_epithet_v1283
_historical_epithets_v1283 = set(V03016_EQ_MASTERY_EPITHETS.values())
for _level_v1283 in range(610, 801, 10):
    _epithet_v1283 = _class_tier_epithet_v1283(_level_v1283)
    if _epithet_v1283 in _historical_epithets_v1283:
        _epithet_v1283 = f"Nowej Ery {_epithet_v1283}"
    V03016_EQ_MASTERY_EPITHETS[_level_v1283] = _epithet_v1283

V03016_ARTIFACT_EPITHETS = {
    2: "Przebudzenia",
    3: "Rezonansu",
    4: "Harmonii",
    5: "Rozkwitu",
    6: "Ascendencji",
    7: "Pradawnej Mocy",
    8: "Wieczności",
    9: "Nieskończoności",
    10: "Transcendencji",
}


def _v03016_add_legacy_item_alias(item, old_name):
    old_name = str(old_name or "").strip()
    if not old_name:
        return
    aliases = list(item.get("aliases") or ())
    if old_name != item.get("name") and old_name not in aliases:
        aliases.append(old_name)
    if aliases:
        item["aliases"] = aliases
    # v0.61.2: stara nazwa pozostaje w aliases; osobna kopia stringa nie jest potrzebna w runtime.


def _v03016_slot_label(item):
    slot = str(item.get("slot") or "")
    spec = CLASS_EQUIPMENT_SLOT_DEFS.get(slot)
    if spec:
        return str(spec[0])
    return {
        "ring": "Pierścień", "charm": "Talizman", "necklace": "Naszyjnik",
        "head": "Hełm", "body": "Pancerz", "hands": "Rękawice",
        "legs": "Nogawice", "feet": "Buty",
    }.get(slot, "Wyposażenie")


def _v03016_class_eq_name(item_id, item):
    class_name = str(item.get("required_class") or "").strip()
    mastery = max(1, int(item.get("required_mastery", 1) or 1))
    epithet = V03016_EQ_MASTERY_EPITHETS.get(mastery, f"Biegłości {mastery}")

    if item.get("legendary_class_relic"):
        base_set = str(CLASS_EQUIPMENT_SETS.get(class_name, {}).get("set_name") or class_name)
        return f"Relikwiarz {base_set} {epithet}"

    slot_label = _v03016_slot_label(item)
    set_name = str(item.get("class_set_name") or CLASS_EQUIPMENT_SETS.get(class_name, {}).get("set_name") or class_name)
    return f"{slot_label} {set_name} {epithet}"


def apply_equipment_name_pass_v03016(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: apply_equipment_name_pass_v03016")
apply_equipment_name_pass_v03016 = _sb410_bind(_sb410_mod_v410_help_audits.apply_equipment_name_pass_v03016, globals())


V03016_EQUIPMENT_NAME_PASS = apply_equipment_name_pass_v03016()


def equipment_name_audit_v03016(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: equipment_name_audit_v03016")
equipment_name_audit_v03016 = _sb410_bind(_sb410_mod_v410_help_audits.equipment_name_audit_v03016, globals())


EQUIPMENT_NAME_AUDIT_V03016 = equipment_name_audit_v03016()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
HELP_TOPICS.setdefault("eq", []).append(
    "v0.30.16: klasowe EQ wszystkich 14 klas ma unikalne nazwy progresji. Nazwa nie jest już tym samym przedmiotem z +10/+20/+30; Biegłość pozostaje w wymaganiu i opisie."
)
HELP_TOPICS.setdefault("eq", []).append(
    "Stare numerowane nazwy EQ pozostają aliasami wyszukiwania, więc wcześniejsze komendy nadal mogą rozpoznać stary przedmiot."
)

HELP_TOPICS.setdefault("eq", []).append(
    "v0.30.16: klasy nie mają już identycznych wartości bazowych. Berserker kieruje budżet w Siłę, Strażnik w Kondycję, Mag w Inteligencję, Kapłan w Siłę Woli, a każda z 14 klas ma własne proporcje i właściwości EQ."
)
HELP_TOPICS.setdefault("eq", []).append(
    "Różnią się też sloty: rękawice i pierścienie są bardziej ofensywne, pancerz i nogawice bardziej przeżywalnościowe. Łączny budżet danego Tieru pozostaje kontrolowany."
)
HELP_TOPICS.setdefault("eq", []).append(
    "Skróty zakładania: zh, zz, zr, zn, zb, zp, zt, zp1/zp2, zt1/zt2, zna, znar, zpas, zpel, zkar, zrel. zp/zt automatycznie wybierają właściwy podwójny slot."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.16 - Unique Class Equipment Identity"
LATEST_CHANGES = [
    "Pełny audyt nazw EQ: 23 238 pancerzy ma unikalne nazwy; 0 nazw progresji kończy się +liczba.",
    "14 klas ma własne proporcje dwóch bazowych statystyk EQ oraz własne właściwości procentowe; klasy nie są już statystycznymi kopiami.",
    "Fizyczne klasy nadal używają Siły + Kondycji, magiczne Inteligencji + Siły Woli, ale rozkład zależy od klasy i slotu.",
    "Skróty NVDA do zakładania EQ: zh, zz, zr, zn, zb, zp, zt, zp1/zp2, zt1/zt2, zna, znar, zpas, zpel, zkar, zrel; skrót bez argumentu pokazuje numerowaną listę.",
    "Stare numerowane nazwy EQ pozostają aliasami wyszukiwania; brak wipe i brak zmiany ID przedmiotów.",
]

# v0.30.14 - FULL GAME CROSS-SYSTEM AUDIT
# Ten audyt celowo działa po dawny Generator Core i po wszystkich późnych patchach.
# Sprawdza nie tylko pojedyncze rekordy, ale też relacje pomiędzy systemami.
def full_game_audit_v03014(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: full_game_audit_v03014")
full_game_audit_v03014 = _sb410_bind(_sb410_mod_v410_help_audits.full_game_audit_v03014, globals())

FULL_GAME_AUDIT_V03014 = full_game_audit_v03014()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# v0.30.14: końcowy audyt po przejściu dawny Generator Core.
V03014_SKILL_NAME_AUDIT = _v03014_skill_name_audit()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
HELP_TOPICS.setdefault("skille", []).append(
    "v0.30.14: pełny audyt nazw 14 klas usunął numerowane serie skilli/spelli; każda umiejętność ma unikalną nazwę, a dawne nazwy pozostają aliasami kompatybilności."
)
HELP_TOPICS.setdefault("biegłość", []).append(
    "Nazwy alternatywnych umiejętności progów Biegłości są unikalne; stare formy typu 'Furia Berserkera 80' nadal działają jako aliasy."
)

# v0.30.16 - STAT-BASED DAMAGE / MANA + ROOM-WIDE AOE AUDIT
def full_combat_scaling_audit_v03015(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: full_combat_scaling_audit_v03015")
full_combat_scaling_audit_v03015 = _sb410_bind(_sb410_mod_v410_help_audits.full_combat_scaling_audit_v03015, globals())

FULL_COMBAT_SCALING_AUDIT_V03015 = full_combat_scaling_audit_v03015()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
def aggro_cleanup_audit_v03015(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: aggro_cleanup_audit_v03015")
aggro_cleanup_audit_v03015 = _sb410_bind(_sb410_mod_v410_help_audits.aggro_cleanup_audit_v03015, globals())

AGGRO_CLEANUP_AUDIT_V03015 = aggro_cleanup_audit_v03015()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# v0.30.16 - STAT-BASED DAMAGE / MANA + ROOM-WIDE AOE
HELP_TOPICS.setdefault("statystyki", []).extend([
    "v0.30.16: Siła bezpośrednio zwiększa moc wszystkich fizycznych skilli ofensywnych.",
    "v0.30.16: Inteligencja bezpośrednio zwiększa moc wszystkich magicznych skilli i spelli ofensywnych.",
    "Maksymalna Mana rośnie równomiernie z Inteligencją i Siłą Woli; oba staty mają taki sam udział w bazowej puli Many.",
    "Kondycja zwiększa maksymalne HP; Zręczność odpowiada m.in. za krytyk, unik i szybkość.",
])
HELP_TOPICS.setdefault("aoe", []).extend([
    "v0.30.16: ofensywne AoE trafia wszystkie żywe moby w całym pokoju, również te walczące już z innym graczem.",
    "AoE nie przejmuje aggro cudzego moba. Jeśli obszarówka dobije takiego przeciwnika, nagrody pozostają przy dotychczasowym właścicielu aggro i jego drużynie.",
    "Bez aktywnej drużyny zwykła blokada celu mówi 'walczy już z innym graczem'; tekst 'spoza twojej drużyny' jest używany dopiero, gdy naprawdę jesteś w drużynie.",
    "Osierocone aggro jest czyszczone automatycznie: mob nie pozostaje zajęty przez gracza, którego nie ma już w pokoju albo który nie walczy już z tym mobem.",
])


# ============================================================
# v0.30.17 - SKILL GRID / CHARACTER-LEVEL QUEUE / SOUL WEAPON COMBAT AUDIT
# ============================================================
def progression_combat_audit_v03017(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: progression_combat_audit_v03017")
progression_combat_audit_v03017 = _sb410_bind(_sb410_mod_v410_help_audits.progression_combat_audit_v03017, globals())


PROGRESSION_COMBAT_AUDIT_V03017 = progression_combat_audit_v03017()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
HELP_TOPICS.setdefault("skille", []).extend([
    "Większość klas zachowuje siatkę 1, 10, 20...400 z minimum 3 skillami na próg; źródłowe umiejętności mogą dodawać kolejne. Inżynier i Mec mają autorskie progi wynikające z ich projektów klasowych.",
    "dawny Generator Core nie rozciąga już 123 skilli po przypadkowych poziomach 1-400; zachowuje zaprojektowane progi Biegłości.",
])
HELP_TOPICS.setdefault("walka", []).extend([
    "v0.30.17: zwykły autoatak jest jawnym atakiem twoją Bronią Duszy; komunikat podaje nazwę broni i klasową technikę.",
    "Ofensywne skille i spelle także korzystają z Mocy Broni Duszy. Fizyczne skaluje Siła, magiczne Inteligencja.",
])
HELP_TOPICS.setdefault("kolejka", []).append(
    "v0.30.18: sloty auto kolejki rosną z Levelem postaci: 10 na Levelu 1, +1 co 10 Leveli, maksymalnie 50 na Levelu 400. Biegłość odblokowuje skille, nie sloty."
)

LATEST_CHANGES_TITLE = "Soulbound v0.30.17 - Soul Weapon Combat + Skill Grid + Character-Level Queue"
LATEST_CHANGES = [
    "Broń Duszy jest jawną aktywną bronią autoataku; każda z 14 klas ma własną technikę ataku, a Soul Power pozostaje rdzeniem obrażeń.",
    "Broń Duszy wykonuje wyłącznie zwykły atak bronią. Skille i spelle są uruchamiane jako osobne zdolności i nie są opisywane jako ataki wykonywane przez broń. Ich dotychczasowe skalowanie obrażeń pozostaje bez zmian.",
    "Naprawiono dawny Generator Core: 123 skille na klasę nie są już rozciągane po losowych progach. Każda klasa ma dokładnie 3 skille na 1, 10, 20...400.",
    "Sloty auto kolejki zależą od Character Level: 10 na Levelu 1, 11 na 10, 20 na 100, 30 na 200, 50 na 400.",
    "Brak wipe; ID skilli, nauczone umiejętności i zapisane kolejki pozostają kompatybilne.",
]


# v0.30.53 help additions
try:
    HELP_TOPICS.update({
      "krawiectwo":"Krawiectwo 1-400. Krawcowa Lysa, Pracownia Krawiecka. Komendy: krawiectwo, szyj <receptura>, szyj lista. Tworzy tkaniny, szaty i płaszcze.",
      "garbarstwo":"Garbarstwo 1-400. Kaletnik Soren. Komendy: garbarstwo, garbuj <receptura>, garbuj lista. Skóry bestii -> garbowana skóra -> pasy, karwasze i naramienniki.",
      "stolarstwo":"Stolarstwo 1-400. Cieśla Edric. Komendy: stolarstwo, stolarka <receptura>, stolarka lista. Obrabia drewno i tworzy totemy oraz komponenty housingu.",
      "zaklinanie":"Zaklinanie 1-600. Komnata Arkanów. Fokus Runiczny kupisz u Selene (list, kup 1). Receptury: receptury zaklinanie, receptury zaklinanie sila. Wykonaj: zaklinaj <slot> <typ> [poziom]; enchants pokazuje efekty. Jedno zaklęcie na slot.",
      "jubilerstwo2":"Jubilerstwo 2.0 dodaje nowe kolczyki, pierścienie i naszyjniki w progresji do levelu 400. Użyj receptury jubilerstwo i jub <nazwa>.",
    })
except Exception as exc:
    print(f"HELP_REFRESH_PROFESSIONS_ERROR: {type(exc).__name__}: {exc}", flush=True)


# v0.30.54 Crafting 2.0 help
try:
    HELP_TOPICS.update({
      "jakosccraftu":"Jakość craftu v0.30.54: gotowe EQ może wyjść jako Zwykłe, Dobre, Doskonałe, Mistrzowskie lub Legendarne. Wyższa jakość realnie zwiększa bazową moc/statystyki przedmiotu.",
      "krytycznycraft":"Krytyczny craft v0.30.54: mała szansa na dodatkowy affix statystyki. Szansa rośnie z levelem profesji oraz Crafting Mastery i ma bezpieczny limit.",
      "craftmastery":"Crafting Mastery v0.30.54 jest osobne od levelu profesji i narzędzia. Rośnie od liczby udanych craftów w konkretnej kategorii. Komenda: craftmastery [filtr]. Maksymalnie 100.",
    })
except Exception as exc:
    print(f"HELP_REFRESH_CRAFTING2_ERROR: {type(exc).__name__}: {exc}", flush=True)


# v0.31.7 Engineer Toolkit + profession tool audit.
HELP_TOPICS.setdefault("inzynier", []).extend([
    "v0.31.7: Inżynier ma autorski zestaw narzędzi: Auto Crossbow, Mako Gun, Bio Blaster, Scanner, Flash, Debilitator, Drill, Napalm, Launcher, Upgrade, Noise Blaster, Chainsaw, Mega Bomb i Air Anchor.",
    "Soulbound nie używa AP. Wartości źródłowej mocy są tylko wewnętrzną mocą bazową umiejętności.",
    "Upgrade <nazwa narzędzia> zapisuje trwałe ulepszenie. Bazowo dostępny jest 1 slot; Silver Gear daje drugi, Gold Battery trzeci. Upgrade reset czyści sloty.",
    "Hypercharge pasywnie wzmacnia single-target, Lindblum Assembly obszarowe narzędzia, a Improved Kinematics wydłuża efekty statusowe.",
])
HELP_TOPICS.setdefault("narzedzia", []).append(
    "v1.10.0: wszystkie 14 profesji ma dokładnie jedno kupowalne, przypisane do postaci narzędzie. Ponowny zakup tej samej postaci jest blokowany."
)
HELP_TOPICS["archeologia"] = [
    "Archeologia jest pełną profesją 1-600. Pędzel Archeologa kupujesz tylko raz na postać u Archeolożki Elary w Bibliotece.",
    "W ruinach, kryptach, na cmentarzach, w świątyniach, archiwach, Magiteku i innych pradawnych miejscach użyj wykop.",
    "archeologia kolekcja pokazuje 21 unikalnych znalezisk od poziomu 1 do 600.",
    "v1.11.0: Elara ma gęstą ścieżkę odnawialnych zleceń praktycznie co 25 poziomów profesji; nowe zlecenia odnawiają się co godzinę.",
    "v1.11.2: Elara ma dodatkowo 10 stałych Zamówień Archeologicznych na progach 25-600; każde odnawia się po 60 minutach.",
]
HELP_TOPICS["kartografia"] = [
    "Kartografia jest pełną profesją 1-600. Kompas Mierniczy kupujesz tylko raz na postać u Mistrzyni Kartografii Aleny w Archiwum Rubieży.",
    "Użyj mapuj w dowolnej odwiedzanej lokacji. Pierwszy pomiar lokacji dopisuje ją do Atlasu Kartografa.",
    "kartografia pokazuje profesję i postęp; kartografia świat otwiera starszy system map świata.",
    "v1.11.0: Alena ma gęstą ścieżkę odnawialnych zleceń praktycznie co 25 poziomów profesji; nowe zlecenia odnawiają się co godzinę.",
    "v1.11.2: Alena ma dodatkowo 10 stałych Zamówień Kartograficznych na progach 25-600; każde odnawia się po 60 minutach.",
]
HELP_TOPIC_ALIASES.update({
    "archeologia": "archeologia", "archaeology": "archeologia",
    "kartografia": "kartografia", "cartography": "kartografia",
})

# v0.31.8: Mec support semantics + tool migration clarification.
try:
    _mec_help = HELP_TOPICS.get("mec", "")
    if isinstance(_mec_help, str) and "Support Effect" not in _mec_help:
        HELP_TOPICS["mec"] = _mec_help + (
            "\nSupport Effect to dodatkowy tryb/efekt konkretnej umiejętności Meca. "
            "Nie jest osobną bronią. Rdzeń Meca pozostaje jego jedyną Bronią Duszy."
        )
except Exception as exc:
    print(f"HELP_REFRESH_MEC_ERROR: {type(exc).__name__}: {exc}", flush=True)

# ============================================================
# v0.61.0 - ITEM SOURCES + PARTY COORDINATION
# ============================================================
HELP_TOPICS["itemsource"] = [
    "gdzie zdobyc <przedmiot> wyszukuje podaną nazwę w aktualnym katalogu gry.",
    "Wynik pokazuje jawne źródła z realnych danych runtime: sklepy i sprzedawców, receptury i stacje, questy, zwykłe dropy, bossy oraz zasoby profesji.",
    "Dla jakościowych wariantów craftu i rzadkich wariantów zasobów komenda wskazuje źródło bazowego przedmiotu zamiast zgadywać osobny drop.",
    "Przykłady: gdzie zdobyc Mikstura leczenia; gdzie zdobyc Ruda żelaza. Przy niejednoznacznej nazwie gra podaje pasujące przedmioty.",
    "v0.61.1: gdzie zdobyc <przedmiot> pelne rozwija recepturę o składniki i pokazuje realne źródła każdego bezpośredniego składnika.",
]
HELP_TOPIC_ALIASES.update({
    "gdziezdobyc": "itemsource",
    "gdziezdobyć": "itemsource",
    "gdzie zdobyc": "itemsource",
    "gdzie zdobyć": "itemsource",
    "itemsource": "itemsource",
    "whereget": "itemsource",
})
HELP_TOPICS["itemuses"] = [
    "do czego <przedmiot> pokazuje, gdzie dany przedmiot jest rzeczywiście zużywany.",
    "Wynik obejmuje receptury, fizyczne oddawanie przedmiotów do questów oraz specjalne systemy: ulepszanie EQ, reforge, runy, sockety, klejnoty, Tech Set Upgrade, V-MAX i zaklinanie.",
    "Przykład: do czego Odłamek Duszy.",
]
HELP_TOPICS["recipegaps"] = [
    "braki receptura <przedmiot lub receptura> pokazuje składniki masz/potrzeba/brakuje.",
    "Komenda sprawdza też realny poziom profesji, posiadanie i Tier narzędzia oraz bieżącą stację craftingu.",
]
HELP_TOPICS["availablerecipes"] = [
    "receptury mozliwe / craft mozliwe pokazuje wyłącznie receptury możliwe do wykonania w tej chwili.",
    "Sprawdzane są składniki, poziom profesji, narzędzie, Tier narzędzia, aktualna stacja oraz blokada craftingu podczas walki.",
]
HELP_TOPIC_ALIASES.update({
    "do czego": "itemuses",
    "doczego": "itemuses",
    "itemuses": "itemuses",
    "braki receptura": "recipegaps",
    "brakireceptura": "recipegaps",
    "recipegaps": "recipegaps",
    "receptury mozliwe": "availablerecipes",
    "receptury możliwe": "availablerecipes",
    "craft mozliwe": "availablerecipes",
    "craft możliwe": "availablerecipes",
    "availablerecipes": "availablerecipes",
})
HELP_TOPICS.setdefault("druzyny", []).extend([
    "v0.61.0: druzyna cel <tekst> ustawia wspólny cel drużyny. Samo druzyna cel pokazuje go, a druzyna cel off usuwa. Cel trwa do zmiany lub rozwiązania drużyny i przechodzi przy ręcznym przekazaniu lidera.",
    "v0.61.0: lider uruchamia kontrolę komendą druzyna gotowi. Każdy członek potwierdza tą samą komendą; druzyna gotowi status pokazuje wszystkich, druzyna niegotowy cofa własne potwierdzenie, a druzyna gotowi reset zaczyna od nowa.",
    "Zmiana albo usunięcie celu zeruje kontrolę gotowości. Cel i ready-check są stanem sesyjnej drużyny, więc nie przechodzą przez restart serwera po rozwiązaniu samej drużyny.",
])
HELP_TOPICS.setdefault("podstawy", []).append(
    "v0.61.0: gdzie zdobyc <przedmiot> pokazuje realne źródła itemu; drużyna ma wspólny cel i kontrolę gotowości."
)
HELP_TOPICS.setdefault("podstawy", []).append(
    "v0.61.1: do czego <przedmiot>, braki receptura <przedmiot>, gdzie zdobyc <przedmiot> pelne oraz receptury mozliwe pomagają planować crafting bez ręcznego przeszukiwania HELP."
)


# ============================================================
# v1.11.97 - FINAL HELP TRUTH LAYER
# This block intentionally runs after all historical HELP patches.
# It makes the public help describe the current 1-600 runtime instead of
# preserving obsolete 1-400 / old-cooldown wording from older milestones.
# ============================================================
def refresh_help_truth_v11197(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: refresh_help_truth_v11197")
refresh_help_truth_v11197 = _sb410_bind(_sb410_mod_v410_help_refresh.refresh_help_truth_v11197, globals())


refresh_help_truth_v11197()


def help_truth_audit_v11197(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: help_truth_audit_v11197")
help_truth_audit_v11197 = _sb410_bind(_sb410_mod_v410_help_audits.help_truth_audit_v11197, globals())


HELP_TRUTH_AUDIT_V11197 = help_truth_audit_v11197()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# ============================================================
# v1.11.97 - PUBLIC HELP SURFACE CLEANUP
# Covers older, still-addressable topic names that survived previous milestones.
# Historical changelog entries are not rewritten; live HELP topics are.
# ============================================================
def refresh_public_help_surface_v11197(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: refresh_public_help_surface_v11197")
refresh_public_help_surface_v11197 = _sb410_bind(_sb410_mod_v410_help_refresh.refresh_public_help_surface_v11197, globals())


refresh_public_help_surface_v11197()


def help_surface_audit_v11197(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: help_surface_audit_v11197")
help_surface_audit_v11197 = _sb410_bind(_sb410_mod_v410_help_audits.help_surface_audit_v11197, globals())


HELP_SURFACE_AUDIT_V11197 = help_surface_audit_v11197()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# v1.28.3: replace obsolete user-facing Generator help with current ownership.
HELP_TOPICS["generator"] = [
    "Od Soulbound v1.28.4 Generator Core jest całkowicie usunięty z kodu gry.",
    "Nie tworzy ani nie nadpisuje EQ, skilli, potworów, questów, receptur, klas i poziomów.",
    "Obliczenia poziomów i balansu są w core/balance_math.py, a katalogi mają jawne, autorskie dane.",
    "Wcześniejsze stałe uzupełnienia liczbowe: data/catalogue_numeric_defaults_v1283.jsonl.gz (strumieniowy, skompresowany).",
    "Statystyki nadal rosną bez limitu; poziomy rozwoju do 800. Nieskończone lochy i kopalnia pozostają proceduralne.",
    "Katalog jest walidowany bez zapisu przez core/catalog_validation.py; pełny predeploy sprawdza integralność gry.",
]
