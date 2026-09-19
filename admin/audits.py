

def main():
    try:
        asyncio.run(MudServer().run())
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")




# v0.30.18 — Generator Core Numeric-Only semantic guard.
def generator_numeric_only_audit_v03018():
    audit = GENERATOR_CORE_AUDIT or {}
    errors = []
    if not audit.get("numeric_only"):
        errors.append("Generator Core numeric_only flag missing")
    if not audit.get("semantic_preserved"):
        errors.append("Generator Core changed protected authored semantics")
    # Explicit regression guards for semantics previously overwritten by Generator Core.
    if tuple(SOUL_MILESTONE_TIERS) != (5, 10, 15, 20):
        errors.append(f"Soul Milestones changed: {SOUL_MILESTONE_TIERS}")
    skill_grid = {1, *range(10, 401, 10)}
    for cname, rows in CLASS_SKILLS.items():
        if cname in ("Inżynier","Mec"):
            if any(not 1 <= int(s.get("unlock", 0) or 0) <= 400 for s in rows):
                errors.append(f"skill unlock range changed: {cname}")
            continue
        if any(int(s.get("unlock", 0) or 0) not in skill_grid for s in rows):
            errors.append(f"skill unlock grid changed: {cname}")
    # Generator is forbidden to invent equipment mastery requirements.
    missing_currency = sum(1 for item in ITEMS.values() if item.get("currency") is None)
    return {
        "version": "0.30.18",
        "error_count": len(errors),
        "errors": errors,
        "semantic_preserved": bool(audit.get("semantic_preserved")),
        "semantic_fingerprint": audit.get("semantic_fingerprint_after"),
        "numeric_only": bool(audit.get("numeric_only")),
        "authored_soul_milestones": tuple(SOUL_MILESTONE_TIERS),
        "items_without_explicit_currency": missing_currency,
    }

GENERATOR_NUMERIC_ONLY_AUDIT_V03018 = generator_numeric_only_audit_v03018()
if GENERATOR_NUMERIC_ONLY_AUDIT_V03018.get("error_count"):
    raise RuntimeError(
        "Generator Numeric-Only Audit v0.30.18 failed: " +
        "; ".join(GENERATOR_NUMERIC_ONLY_AUDIT_V03018.get("errors", [])[:20])
    )

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
    audit = GENERATOR_CORE_AUDIT or {}
    whitelist = audit.get("whitelist_audit") or {}
    errors = []
    if GENERATOR_CORE_VERSION != "0.33.3":
        errors.append(f"Generator Core version={GENERATOR_CORE_VERSION}, expected 0.33.3")
    if not audit.get("numeric_only"):
        errors.append("numeric_only flag missing")
    if not audit.get("semantic_preserved"):
        errors.append("semantic fingerprint changed")
    if not audit.get("whitelist_enforced"):
        errors.append("whitelist_enforced flag missing")
    if not audit.get("whitelist_passed"):
        errors.extend(whitelist.get("errors") or ["numeric whitelist failed"])
    required_tables = {
        "ROOMS", "MOB_TEMPLATES", "ITEMS", "QUESTS", "CLASS_SKILLS",
        "CRAFT_RECIPES", "COOK_RECIPES", "ALCHEMY_RECIPES", "JEWELCRAFT_RECIPES",
    }
    actual_tables = set((whitelist.get("record_whitelist") or {}).keys())
    missing = sorted(required_tables - actual_tables)
    if missing:
        errors.append("whitelist missing tables: " + ", ".join(missing))
    return {
        "version": "0.30.19",
        "whitelist_enforced": bool(audit.get("whitelist_enforced")),
        "whitelist_passed": bool(audit.get("whitelist_passed")),
        "semantic_preserved": bool(audit.get("semantic_preserved")),
        "numeric_values_checked": int(whitelist.get("numeric_values_checked", 0) or 0),
        "record_tables": tuple(sorted(actual_tables)),
        "nested_value_tables": tuple(sorted((whitelist.get("nested_value_whitelist") or {}).keys())),
        "top_level_domains": tuple(whitelist.get("top_level_value_whitelist") or ()),
        "error_count": len(errors),
        "errors": errors,
    }


GENERATOR_WHITELIST_AUDIT_V03019 = generator_whitelist_audit_v03019()
if GENERATOR_WHITELIST_AUDIT_V03019.get("error_count"):
    raise RuntimeError(
        "Generator Whitelist Audit v0.30.19 failed: " +
        "; ".join(GENERATOR_WHITELIST_AUDIT_V03019.get("errors", [])[:30])
    )

HELP_TOPICS.setdefault("generator", []).extend([
    "v0.30.19: Generator Core działa z jawną białą listą zapisu. Może zmienić wyłącznie konkretne pola liczbowego balansu.",
    "Mob: tylko generator_level/stage, HP, damage, EXP, waluta oraz prawdopodobieństwa istniejących dropów. Nie może zmienić rangi, nazw, quest-targetów ani listy dropów.",
    "Przedmiot/EQ: tylko liczby ceny, obrony i wartości istniejących stats/properties/runes. Nie może dodać nowego statystyku, właściwości, slotu, klasy ani wymagania.",
    "Skill/spell: tylko generator_level, cooldown, mana i wartości istniejącego rodzaju efektu. ID, nazwa, kind, scale i próg unlock są chronione.",
    "Quest/receptura: generator liczy wyłącznie dozwolone nagrody/XP i generator_level; cele, wymagania, składniki, produkty i ilości pozostają ręcznie projektowane.",
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
    errors = []
    required_slots = {"shoulders", "belt", "cloak", "bracers", "relic"}
    if not required_slots.issubset(CLASS_EQUIPMENT_SLOT_DEFS):
        errors.append("missing new class EQ slots: " + ", ".join(sorted(required_slots - set(CLASS_EQUIPMENT_SLOT_DEFS))))
    if not required_slots.issubset(EQUIPMENT_SLOT_NAMES):
        errors.append("missing new slot display names")
    expected_commands = {
        "zp":"equipringauto", "zt":"equipcharmauto", "znar":"equipshoulders",
        "zpas":"equipbelt", "zpel":"equipcloak", "zkar":"equipbracers", "zrel":"equiprelic",
    }
    for alias, command in expected_commands.items():
        if COMMAND_ALIASES.get(alias) != command:
            errors.append(f"shortcut {alias} -> {COMMAND_ALIASES.get(alias)!r}, expected {command!r}")
    # Every class/tier should now expose all 14 logical equipment pieces per style.
    logical_slots = set(CLASS_EQUIPMENT_SLOT_DEFS)
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for mastery in (1, 100, 200, 400):
            ids = tiers.get(mastery, ())
            present = {ITEMS[i].get("slot") for i in ids if i in ITEMS}
            if not logical_slots.issubset(present):
                errors.append(f"{class_name} mastery {mastery}: missing slots {sorted(logical_slots-present)}")
                break
    return {
        "version":"0.30.20",
        "logical_slot_count":len(logical_slots),
        "new_slots":tuple(sorted(required_slots)),
        "error_count":len(errors),
        "errors":errors,
    }

EQUIPMENT_EXPANSION_AUDIT_V03020 = equipment_expansion_audit_v03020()
if EQUIPMENT_EXPANSION_AUDIT_V03020.get("error_count"):
    raise RuntimeError("Equipment Expansion Audit v0.30.20 failed: " + "; ".join(EQUIPMENT_EXPANSION_AUDIT_V03020.get("errors", [])[:20]))

HELP_TOPICS.setdefault("eq", []).extend([
    "v0.30.20: dodano 5 nowych slotów EQ: naramienniki, pas, peleryna, karwasze, kolczyki i relikt. Klasowe EQ wszystkich 14 klas generuje te sloty na każdym istniejącym progu Biegłości.",
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
def refresh_help_v03021_full():
    """Finalna warstwa HELP. Nadpisuje historyczne teksty, które nie opisują już runtime."""
    HELP_TOPIC_ALIASES.update({
        "waluta":"waluta", "pieniadze":"waluta", "pieniądze":"waluta", "money":"waluta",
        "eq sklep":"sklepy", "sklep eq":"sklepy", "sklepy eq":"sklepy",
        "sell all":"sprzedaj_wszystko", "sprzedaj wszystko":"sprzedaj_wszystko",
    })
    HELP_TOPICS["waluta"] = [
        "Cała ekonomia używa jednego wspólnego salda. Nominały służą tylko do czytelnego wyświetlania i wpisywania kwot.",
        "100 srebra = 1 złota. 1000 złota = 1 mithril. 1 mithril = 100 000 srebra.",
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
if FULL_HELP_AUDIT_V03021["error_count"]:
    raise RuntimeError("Full HELP Audit v0.30.21 failed: "+"; ".join(FULL_HELP_AUDIT_V03021["errors"][:30]))


def eq_shop_audit_v03021():
    errors=[]
    slots=set(CLASS_EQUIPMENT_SLOT_DEFS)
    if len(slots)!=14:
        errors.append(f"logical EQ slots={len(slots)}, expected 14")
    for class_name,definition in CLASS_EQUIPMENT_SETS.items():
        room=definition.get("room")
        if room not in SHOPS:
            errors.append(f"brak sklepu: {class_name}/{room}")
        for mastery in (1,100,200,300,400):
            ids=CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name,{}).get(mastery,())
            present={ITEMS[i].get("slot") for i in ids if i in ITEMS}
            if not slots.issubset(present):
                errors.append(f"{class_name} {mastery}: brakuje {sorted(slots-present)}")
                break
    return {"version":"0.30.21","shops":len(CLASS_SHOP_ITEMS_BY_ROOM),"slot_count":len(slots),"error_count":len(errors),"errors":errors}

EQ_SHOP_AUDIT_V03021=eq_shop_audit_v03021()
if EQ_SHOP_AUDIT_V03021["error_count"]:
    raise RuntimeError("EQ Shop Audit v0.30.21 failed: "+"; ".join(EQ_SHOP_AUDIT_V03021["errors"][:30]))


def currency_economy_audit_v03021():
    errors=[]
    formatter_tests={
        SILVER_PER_GOLD-1:f"{SILVER_PER_GOLD-1} srebra",
        SILVER_PER_GOLD:"1 złota",
        2*SILVER_PER_GOLD+50:"2 złota, 50 srebra",
        SILVER_PER_MITHRIL:"1 mithril",
        SILVER_PER_MITHRIL+2*SILVER_PER_GOLD+45:"1 mithril, 2 złota, 45 srebra",
    }
    for total,expected in formatter_tests.items():
        got=currency_reading_text(total,0,0)
        if got!=expected: errors.append(f"format {total}: {got!r} != {expected!r}")
    quest_values=[]
    for qid,q in QUESTS.items():
        value=v0190_quest_currency_reward(q)
        quest_values.append(value)
        if value<SILVER_PER_GOLD: errors.append(f"quest <1 gold: {qid}={value}")
    tool_rows=[]
    for iid,item in ITEMS.items():
        if str(item.get("type","")).lower()=="tool" or item.get("tool_type"):
            price=int(item.get("price",0) or 0)
            tool_rows.append((iid,price))
            # Basic ungated tools must stay in a compact starter band.
            has_gate=any(int(item.get(k,0) or 0)>0 for k in ("required_tool_level","min_tool_level","min_profession_level","required_profession_level","required_mastery"))
            if not has_gate and not (1001 <= price <= 3500):
                errors.append(f"starter tool price {iid}={price}")
    return {
        "version":"0.30.21",
        "quests":len(quest_values),
        "quest_min":min(quest_values) if quest_values else 0,
        "quest_max":max(quest_values) if quest_values else 0,
        "tools":tuple(tool_rows),
        "error_count":len(errors),
        "errors":errors,
    }

CURRENCY_ECONOMY_AUDIT_V03021=currency_economy_audit_v03021()
if CURRENCY_ECONOMY_AUDIT_V03021["error_count"]:
    raise RuntimeError("Currency Economy Audit v0.30.21 failed: "+"; ".join(CURRENCY_ECONOMY_AUDIT_V03021["errors"][:30]))

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
def full_release_integrity_audit_v03022():
    errors=[]
    warnings=[]
    stats={}

    # Every previously active release gate must still be clean.
    audit_names=(
        "GENERATOR_CORE_AUDIT", "GENERATOR_WHITELIST_AUDIT_V03019",
        "WORLD_TOPOLOGY_AUDIT", "WORLD_LOGIC_AUDIT",
        "FULL_WORLD_TOPOLOGY_AUDIT_V03013", "FULL_GAME_AUDIT_V03014",
        "FULL_COMBAT_SCALING_AUDIT_V03015", "AGGRO_CLEANUP_AUDIT_V03015",
        "CLASS_EQ_AUDIT_V03015", "EQUIPMENT_NAME_AUDIT_V03016",
        "CLASS_EQ_IDENTITY_AUDIT_V03016", "PROGRESSION_COMBAT_AUDIT_V03017",
        "GENERATOR_NUMERIC_ONLY_AUDIT_V03018", "EQUIPMENT_EXPANSION_AUDIT_V03020",
        "FULL_HELP_AUDIT_V03021", "EQ_SHOP_AUDIT_V03021",
        "CURRENCY_ECONOMY_AUDIT_V03021",
    )
    for name in audit_names:
        audit=globals().get(name)
        if not isinstance(audit,dict):
            errors.append(f"missing audit {name}")
            continue
        if int(audit.get("error_count",0) or 0):
            errors.append(f"{name}: {audit.get('errors',[])[:3]}")
        if int(audit.get("warning_count",0) or 0):
            warnings.append(f"{name}: {audit.get('warnings',[])[:3]}")

    opposite={
        "north":"south", "south":"north", "east":"west", "west":"east",
        "northeast":"southwest", "southwest":"northeast",
        "northwest":"southeast", "southeast":"northwest",
        "up":"down", "down":"up",
    }
    static_edges=0
    lazy_edges=[]
    for rid,room in ROOMS.items():
        if not str(room.get("name","")).strip(): errors.append(f"room without name: {rid}")
        if not str(room.get("zone","")).strip(): errors.append(f"room without zone: {rid}")
        if not str(room.get("desc","")).strip(): errors.append(f"room without desc: {rid}")
        exits=room.get("exits",{})
        if not isinstance(exits,dict):
            errors.append(f"room exits not dict: {rid}")
            continue
        for direction,target in exits.items():
            if direction not in opposite: errors.append(f"invalid direction: {rid}.{direction}")
            if target==rid: errors.append(f"self exit: {rid}.{direction}")
            if target in ROOMS:
                static_edges += 1
                if ROOMS[target].get("exits",{}).get(opposite.get(direction)) != rid:
                    errors.append(f"nonreciprocal: {rid}.{direction}->{target}")
            else:
                lazy_edges.append((rid,direction,target))
                kind,floor=instance_room_identity(target)
                known=kind is not None or str(target).startswith((
                    "v0130_frontier_", "v018_endless_", "v020_mega_",
                    "v021_gauntlet_", "v0140_mini_", "v0140_secret_",
                    "v018_archipelago_", "v018_ruin_",
                ))
                if not known:
                    errors.append(f"unknown lazy exit: {rid}.{direction}->{target}")

    # Reachability and return-path invariants are mandatory release gates.
    logic=WORLD_LOGIC_AUDIT
    if int(logic.get("reachable_from_square",0)) != len(ROOMS):
        errors.append(f"reachable {logic.get('reachable_from_square')} != rooms {len(ROOMS)}")
    if int(logic.get("returnable_to_square",0)) != len(ROOMS):
        errors.append(f"returnable {logic.get('returnable_to_square')} != rooms {len(ROOMS)}")

    # Profession terrain references: every authored gathering location must still exist.
    room_collections={
        "RIVER_FISHING_ROOMS":RIVER_FISHING_ROOMS, "LAKE_FISHING_ROOMS":LAKE_FISHING_ROOMS,
        "SEA_FISHING_ROOMS":SEA_FISHING_ROOMS, "OCEAN_FISHING_ROOMS":OCEAN_FISHING_ROOMS,
        "FRESHWATER_FISHING_ROOMS":FRESHWATER_FISHING_ROOMS, "MARINE_FISHING_ROOMS":MARINE_FISHING_ROOMS,
        "FISHING_ROOMS":FISHING_ROOMS, "MINING_ROOMS":MINING_ROOMS,
        "UNIFIED_DEEP_MINE_STATIC_ROOMS":UNIFIED_DEEP_MINE_STATIC_ROOMS,
        "AUTO_FISHING_ROUTE":AUTO_FISHING_ROUTE, "AUTO_WOODCUTTING_ROUTE":AUTO_WOODCUTTING_ROUTE,
        "AUTO_HERBALISM_ROUTE":AUTO_HERBALISM_ROUTE, "WOODCUTTING_ROOMS":WOODCUTTING_ROOMS,
        "MEADOW_HERBALISM_ROOMS":MEADOW_HERBALISM_ROOMS, "HERBALISM_ROOMS":HERBALISM_ROOMS,
    }
    for name,values in room_collections.items():
        missing=[room for room in values if room not in ROOMS]
        if missing: errors.append(f"{name} missing rooms: {missing[:10]}")

    for tool_id,room_id in TOOL_SHOP_ROOMS.items():
        if tool_id not in ITEMS: errors.append(f"tool shop item missing: {tool_id}")
        if room_id not in ROOMS: errors.append(f"tool shop room missing: {tool_id}->{room_id}")
    for room_id,item_ids in SHOPS.items():
        if room_id not in ROOMS: errors.append(f"shop room missing: {room_id}")
        for item_id in item_ids:
            if item_id not in ITEMS: errors.append(f"shop item missing: {room_id}->{item_id}")
    for room_id in PROFESSION_GUIDE_PRIMARY_ROOMS.values():
        if room_id not in ROOMS: errors.append(f"profession guide room missing: {room_id}")

    resource_collections={
        "FISH_RESOURCE_IDS":FISH_RESOURCE_IDS, "ORE_RESOURCE_IDS":ORE_RESOURCE_IDS,
        "WOOD_RESOURCE_IDS":WOOD_RESOURCE_IDS, "HERB_RESOURCE_IDS":HERB_RESOURCE_IDS,
        "WORLD_FISH_IDS":WORLD_FISH_IDS, "WORLD_ORE_IDS":WORLD_ORE_IDS,
        "WORLD_WOOD_IDS":WORLD_WOOD_IDS, "WORLD_HERB_IDS":WORLD_HERB_IDS,
    }
    for name,values in resource_collections.items():
        missing=[item_id for item_id in values if item_id not in ITEMS]
        if missing: errors.append(f"{name} missing items: {missing[:10]}")

    # Static content references outside the terrain graph.
    for room_id,template_id in MOB_SPAWNS:
        if room_id not in ROOMS: errors.append(f"spawn room missing: {room_id}:{template_id}")
        if template_id not in MOB_TEMPLATES: errors.append(f"spawn mob missing: {room_id}:{template_id}")
    for npc_id,npc in NPCS.items():
        if npc.get("room") not in ROOMS: errors.append(f"NPC room missing: {npc_id}->{npc.get('room')}")
    for class_name,tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for mastery,item_ids in tiers.items():
            for item_id in item_ids:
                if item_id not in ITEMS: errors.append(f"class EQ missing: {class_name}/{mastery}/{item_id}")

    stats.update({
        "rooms":len(ROOMS), "static_directed_edges":static_edges, "lazy_runtime_exits":len(lazy_edges),
        "zones":len({str(r.get('zone') or '') for r in ROOMS.values()}),
        "mobs":len(MOB_TEMPLATES), "spawns":len(MOB_SPAWNS), "items":len(ITEMS),
        "quests":len(QUESTS), "npcs":len(NPCS), "skills":sum(len(v) for v in CLASS_SKILLS.values()),
        "help_topics":len(HELP_TOPICS), "help_aliases":len(HELP_TOPIC_ALIASES),
        "fishing_rooms":len(FISHING_ROOMS), "mining_rooms":len(MINING_ROOMS),
        "woodcutting_rooms":len(WOODCUTTING_ROOMS), "herbalism_rooms":len(HERBALISM_ROOMS),
        "active_audits_checked":len(audit_names),
    })
    return {
        "version":"0.30.22", "error_count":len(errors), "warning_count":len(warnings),
        "errors":errors, "warnings":warnings, **stats,
    }

FULL_RELEASE_INTEGRITY_AUDIT_V03022 = full_release_integrity_audit_v03022()
if FULL_RELEASE_INTEGRITY_AUDIT_V03022.get("error_count"):
    raise RuntimeError(
        "Full Release Integrity Audit v0.30.22 failed: " +
        "; ".join(FULL_RELEASE_INTEGRITY_AUDIT_V03022.get("errors",[])[:30])
    )

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
def quest_reward_hybrid_audit_v03024():
    errors = []
    manual_ids = set(V03024_MANUAL_QUEST_REWARDS_COINS)
    automatic_ids = set(QUESTS) - manual_ids

    if V03024_MANUAL_QUEST_REWARD_MARKING.get("missing"):
        errors.append("manual quest IDs missing: " + ", ".join(V03024_MANUAL_QUEST_REWARD_MARKING["missing"][:10]))

    for quest_id, quest in QUESTS.items():
        reward = int(quest.get("reward_silver", 0) or 0)
        if reward < 0:
            errors.append(f"negative quest reward: {quest_id}")
        if int(quest.get("reward_gold", 0) or 0) != 0 or int(quest.get("reward_mithril", 0) or 0) != 0:
            errors.append(f"quest has split wallet reward: {quest_id}")
        if quest_id in manual_ids:
            expected = int(V03024_MANUAL_QUEST_REWARDS_COINS[quest_id])
            if quest.get("currency_reward_mode") != "manual":
                errors.append(f"manual reward mode missing: {quest_id}")
            if int(quest.get("manual_currency_reward_coins", -1)) != expected:
                errors.append(f"manual reward marker changed: {quest_id}")
            if reward != expected:
                errors.append(f"manual reward overwritten: {quest_id}={reward}, expected={expected}")
        else:
            if quest.get("manual_currency_reward_coins") is not None:
                errors.append(f"unexpected manual marker: {quest_id}")
            if reward < 1001:
                errors.append(f"automatic reward below unified floor: {quest_id}={reward}")

    # Critical hand-authored anchors.
    anchors = {
        "soul_shards": 7_500,
        "fisher_30_fish": 2_500,
        "herbalist_30_herbs": 2_500,
        "lumberjack_30_wood": 2_500,
        "miner_30_ore": 2_500,
        "mountain_troll_hunt": 15_000,
        "troll_king_hunt": 75_000,
        "desert_patrol": 150_000,
    }
    for quest_id, expected in anchors.items():
        if int(QUESTS.get(quest_id, {}).get("reward_silver", -1)) != expected:
            errors.append(f"anchor reward mismatch: {quest_id}")

    # Presentation must be a lossless view of the one shared integer balance.
    sample_values = (
        0, 1, 999, 1000, 2500, 7_500, 150_000,
        SILVER_PER_MITHRIL, SILVER_PER_MITHRIL + 2 * SILVER_PER_GOLD + 345,
        max(int(q.get("reward_silver", 0) or 0) for q in QUESTS.values()),
    )
    for coins in sample_values:
        mithril, gold, silver = currency_denominations(coins)
        rebuilt = legacy_currency_to_coins(silver, gold, mithril)
        if rebuilt != coins:
            errors.append(f"currency roundtrip {coins}->{mithril}/{gold}/{silver}->{rebuilt}")

    rewards = [int(q.get("reward_silver", 0) or 0) for q in QUESTS.values()]
    return {
        "version": "0.30.24",
        "quests": len(QUESTS),
        "manual_quests": len(manual_ids),
        "automatic_quests": len(automatic_ids),
        "min_reward": min(rewards) if rewards else 0,
        "max_reward": max(rewards) if rewards else 0,
        "single_balance_storage": all(
            int(q.get("reward_gold", 0) or 0) == 0 and int(q.get("reward_mithril", 0) or 0) == 0
            for q in QUESTS.values()
        ),
        "error_count": len(errors),
        "errors": errors,
    }

QUEST_REWARD_HYBRID_AUDIT_V03024 = quest_reward_hybrid_audit_v03024()
if QUEST_REWARD_HYBRID_AUDIT_V03024.get("error_count"):
    raise RuntimeError(
        "Hybrid Quest Reward Audit v0.30.24 failed: " +
        "; ".join(QUEST_REWARD_HYBRID_AUDIT_V03024.get("errors", [])[:30])
    )

HELP_TOPICS.setdefault("quest", []).extend([
    "v0.30.24: ważne questy fabularne, próby profesji, wybrane duże zadania świata i Próby Broni Duszy mają ręcznie zbalansowaną, chronioną nagrodę walutową.",
    "Pozostałe questy nadal otrzymują walutę automatycznie z Generator Core. Wszystkie wypłaty trafiają do jednego wspólnego salda.",
    "quest list <NPC> pokazuje teraz również nagrodę walutową przed przyjęciem zadania; quest info <numer> pokazuje pełny zestaw nagród.",
])
HELP_TOPICS.setdefault("waluta", []).extend([
    "v0.30.24: nagrody questów używają systemu hybrydowego. Ręcznie oznaczone questy zachowują dokładną kwotę, a pozostałe są skalowane automatycznie.",
    "Generator Core nie może już nadpisać manual_currency_reward_coins. Złoto i mithril są nadal tylko sposobem prezentacji jednego salda w srebrze.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.24: Hybrid Quest Rewards. 64 ważne questy mają chronione ręczne nagrody walutowe; 243 pozostałe nadal skaluje Generator Core. Quest list pokazuje nagrodę przed przyjęciem."
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


def profession_tool_xp_audit_v03025():
    errors = []
    recipe_tables = (
        ("Kowalstwo", "crafting", CRAFT_RECIPES),
        ("Alchemia", "alchemy", ALCHEMY_RECIPES),
        ("Gotowanie", "cooking", COOK_RECIPES),
        ("Jubilerstwo", "jewelcrafting", JEWELCRAFT_RECIPES),
    )
    recipe_count = 0
    ingot_count = 0
    for profession, tool_type, recipes in recipe_tables:
        for recipe_id, recipe in recipes.items():
            recipe_count += 1
            profession_xp = int(recipe.get("profession_xp", 0) or 0)
            tool_xp = int(recipe.get("tool_xp", 0) or 0)
            if profession_xp <= 0:
                errors.append(f"{profession}/{recipe_id}: brak profession_xp")
            if tool_xp <= 0:
                errors.append(f"{profession}/{recipe_id}: brak tool_xp")
            output_id = str(recipe.get("output") or "")
            if tool_type == "crafting" and (output_id.endswith("_ingot") or output_id.startswith("ingot_")):
                ingot_count += 1
                if profession_xp <= 0 or tool_xp <= 0:
                    errors.append(f"przetop {recipe_id}: nie rozwija jednocześnie Kowalstwa i Młota")

    profession_quest_count = 0
    for quest_id, quest in QUESTS.items():
        profession_xp = int(quest.get("reward_profession_xp", 0) or 0)
        tool_xp = int(quest.get("reward_tool_xp", 0) or 0)
        profession = quest.get("reward_profession")
        tool_type = quest.get("reward_tool_type")
        if not (profession_xp or tool_xp or profession or tool_type):
            continue
        profession_quest_count += 1
        expected = profession_for_tool_type(tool_type)
        if profession_xp <= 0:
            errors.append(f"quest {quest_id}: brak reward_profession_xp")
        if tool_xp <= 0:
            errors.append(f"quest {quest_id}: brak reward_tool_xp")
        if not tool_type:
            errors.append(f"quest {quest_id}: brak reward_tool_type")
        if not profession:
            errors.append(f"quest {quest_id}: brak reward_profession")
        if expected and profession and profession != expected:
            errors.append(
                f"quest {quest_id}: {profession} nie pasuje do narzędzia {tool_type} ({expected})"
            )

    # Główne akcje zbierackie są celowo jawne: każda wywołuje
    # grant_profession_progress(profesja, xp, narzędzie, xp).
    gathering_pairs = {
        "fish": ("Wędkarstwo", "fishing"),
        "mine": ("Górnictwo", "mining"),
        "woodcut": ("Drwalstwo", "woodcutting"),
        "gather_herb": ("Zielarstwo", "herbalism"),
    }
    return {
        "version": "0.30.25",
        "recipes_checked": recipe_count,
        "ingot_recipes_checked": ingot_count,
        "profession_quests_checked": profession_quest_count,
        "quest_profession_repairs": len(V03025_PROFESSION_REWARD_REPAIRS),
        "gathering_actions_checked": len(gathering_pairs),
        "gathering_pairs": gathering_pairs,
        "error_count": len(errors),
        "errors": errors,
    }


PROFESSION_TOOL_XP_AUDIT_V03025 = profession_tool_xp_audit_v03025()
if PROFESSION_TOOL_XP_AUDIT_V03025.get("error_count"):
    raise RuntimeError(
        "Profession + Tool XP Audit v0.30.25 failed: "
        + "; ".join(PROFESSION_TOOL_XP_AUDIT_V03025.get("errors", [])[:30])
    )

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
    if GENERATOR_CORE_VERSION != "0.33.3":
        errors.append(f"GENERATOR_CORE_VERSION={GENERATOR_CORE_VERSION}")
    return {
        "version": "0.30.25",
        "base_release_gate": previous.get("version", "v0.30.22"),
        "profession_tool_xp": PROFESSION_TOOL_XP_AUDIT_V03025.get("error_count") == 0,
        "world_logic": WORLD_LOGIC_AUDIT.get("error_count") == 0,
        "world_warnings": WORLD_LOGIC_AUDIT.get("warning_count", 0),
        "error_count": len(errors),
        "errors": errors,
    }

FULL_RELEASE_INTEGRITY_AUDIT_V03025 = full_release_integrity_audit_v03025()
if FULL_RELEASE_INTEGRITY_AUDIT_V03025.get("error_count"):
    raise RuntimeError(
        "Full Release Integrity Audit v0.30.25 failed: "
        + "; ".join(FULL_RELEASE_INTEGRITY_AUDIT_V03025.get("errors", [])[:30])
    )

HELP_TOPICS.setdefault("kowalstwo", []).extend([
    "v0.30.25: każde przetopienie sztabki daje jednocześnie XP Kowalstwa i XP Młota Rzemieślniczego.",
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
COMMAND_ALIASES.update({"ex": "exits"})

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
    if _starter_ore not in SHOPS.setdefault("forge", []):
        SHOPS["forge"].append(_starter_ore)

# v0.30.26: Odłamki Duszy są materiałem questowym Krypty i nie mogą być
# spłaszczane przez ogólny rebalance dropów Generator Core. Ten późny pass
# przywraca celowe szanse po wykonaniu Generator Core. Dynamiczne piętra
# tworzone później mają własne wysokie wartości w generatorze runtime.
def apply_soul_shard_drop_fix_v03026():
    # Klasyczne moby wejściowej Krypty.
    if "skeleton" in MOB_TEMPLATES:
        MOB_TEMPLATES["skeleton"].setdefault("drops", {})["soul_shard"] = 0.55
    if "crypt_wraith" in MOB_TEMPLATES:
        MOB_TEMPLATES["crypt_wraith"].setdefault("drops", {})["soul_shard"] = 0.85

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
            # Zwykła Krypta: około 25% na początku, rośnie do 65%.
            _template.setdefault("drops", {})["soul_shard"] = min(0.65, 0.25 + _crypt_floor * 0.002)
            regular_fixed += 1
        elif _mythic_floor > 0:
            # Mityczna Krypta jest późnym źródłem — odłamek ma być częsty.
            _template.setdefault("drops", {})["soul_shard"] = 0.65
            mythic_fixed += 1
    return {
        "regular_crypt": regular_fixed,
        "mythic_crypt": mythic_fixed,
        "bosses": boss_fixed,
    }

SOUL_SHARD_DROP_FIX_V03026 = apply_soul_shard_drop_fix_v03026()

# HELP: Tier narzędzia jest teraz twardym progiem zawartości.
HELP_TOPICS.setdefault("quest", []).append(
    "v0.30.26: Odłamki Duszy w Krypcie wypadają znacznie częściej. Zwykłe piętra zaczynają od około 25 procent i rosną do 65 procent; bossowie Krypty gwarantują Odłamek."
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


def gameplay_flow_audit_v03026():
    errors = []
    if COMMAND_ALIASES.get("ex") != "exits":
        errors.append("ex nie mapuje się na exits")

    # Dostęp zasobów musi zmieniać się wyłącznie na progach Tieru.
    for _tool_type in ("fishing", "mining", "woodcutting", "herbalism"):
        previous_access = None
        previous_tier = None
        for _level in range(1, 401):
            _tier = tool_tier(_level)
            _access = tool_tier_access_level(_level)
            if _access != TOOL_TIER_THRESHOLDS[_tier - 1]:
                errors.append(f"{_tool_type}: zły access level {_level}->{_access}")
                break
            if previous_tier == _tier and previous_access != _access:
                errors.append(f"{_tool_type}: pula zmienia się wewnątrz Tieru {_tier}")
                break
            previous_access, previous_tier = _access, _tier

    recipe_count = 0
    for _recipes in (CRAFT_RECIPES, COOK_RECIPES, ALCHEMY_RECIPES, JEWELCRAFT_RECIPES):
        for _rid, _recipe in _recipes.items():
            recipe_count += 1
            _required = max(1, int(_recipe.get("min_profession_level", _recipe.get("min_tool_level", 1)) or 1))
            _required_tier = required_tool_tier_for_level(_required)
            if not 1 <= _required_tier <= TOOL_MAX_TIER:
                errors.append(f"recipe {_rid}: invalid tool tier {_required_tier}")
            if int(_recipe.get("profession_xp", 0) or 0) <= 0:
                errors.append(f"recipe {_rid}: brak profession_xp")
            if int(_recipe.get("tool_xp", 0) or 0) <= 0:
                errors.append(f"recipe {_rid}: brak tool_xp")

    for _rid in V03026_WOOD_RECIPES:
        _recipe = CRAFT_RECIPES[_rid]
        if _recipe.get("profession") != "Drwalstwo" or _recipe.get("tool_type") != "woodcutting":
            errors.append(f"wood recipe {_rid}: zła para profesja/narzędzie")

    smith_missing = [
        _rid for _rid, _recipe in CRAFT_RECIPES.items()
        if _rid not in V03026_WOOD_RECIPES
        and "crafting_workshop" not in tuple(_recipe.get("stations", ()))
    ]
    if smith_missing:
        errors.append(f"station crafting_workshop: brak w {smith_missing[:5]}")
    wood_missing = [
        _rid for _rid in V03026_WOOD_RECIPES
        if "forester_lodge" not in tuple(CRAFT_RECIPES[_rid].get("stations", ()))
    ]
    if wood_missing:
        errors.append(f"station forester_lodge: brak w {wood_missing[:5]}")
    required_stations = (
        (COOK_RECIPES, "blue_flame_kitchen"),
        (ALCHEMY_RECIPES, "alchemy_lab"),
        (JEWELCRAFT_RECIPES, "jeweler_workshop"),
    )
    for _recipes, _station in required_stations:
        missing = [_rid for _rid, _recipe in _recipes.items() if _station not in tuple(_recipe.get("stations", ()))]
        if missing:
            errors.append(f"station {_station}: brak w {missing[:5]}")

    if GENERATOR_CORE_VERSION != "0.33.3":
        errors.append(f"GENERATOR_CORE_VERSION={GENERATOR_CORE_VERSION}")

    return {
        "version": "0.30.26",
        "recipes_checked": recipe_count,
        "wood_recipes_fixed": len(V03026_WOOD_RECIPES),
        "tool_tiers": TOOL_MAX_TIER,
        "gathering_professions": 4,
        "error_count": len(errors),
        "errors": errors,
    }

GAMEPLAY_FLOW_AUDIT_V03026 = gameplay_flow_audit_v03026()
if GAMEPLAY_FLOW_AUDIT_V03026["error_count"]:
    raise RuntimeError(
        "Gameplay Flow Audit v0.30.26 failed: "
        + "; ".join(GAMEPLAY_FLOW_AUDIT_V03026["errors"][:30])
    )

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
    "Naprawiono zaniżanie szansy Odłamków Duszy przez ogólny rebalance: zwykła Krypta ma teraz około 25-65 procent, klasyczne moby Krypty 55-85 procent, a bossowie gwarantują Odłamek.",
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
    errors = []
    checked = 0
    for class_name, skills in CLASS_SKILLS.items():
        for skill in skills:
            if str(skill.get("kind") or "").lower() != "boost":
                continue
            checked += 1
            if int(skill.get("duration", 0) or 0) != GLOBAL_SKILL_BUFF_DURATION_SECONDS:
                errors.append(
                    f"{class_name}/{skill.get('name')}: duration={skill.get('duration')}"
                )
            desc = str(skill.get("desc") or "")
            if "30 sekund" not in desc:
                errors.append(f"{class_name}/{skill.get('name')}: opis bez 30 sekund")
    return {
        "version": "0.30.30",
        "checked": checked,
        "duration_seconds": GLOBAL_SKILL_BUFF_DURATION_SECONDS,
        "error_count": len(errors),
        "errors": errors,
    }

BUFF_DURATION_AUDIT_V03030 = buff_duration_audit_v03030()
if BUFF_DURATION_AUDIT_V03030["error_count"]:
    raise RuntimeError(
        "Buff Duration Audit v0.30.30 failed: "
        + "; ".join(BUFF_DURATION_AUDIT_V03030["errors"][:20])
    )

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
    errors = []
    if not hasattr(MudServer, "party_combat_broadcast"):
        errors.append("brak MudServer.party_combat_broadcast")
    return {
        "version": "0.30.31",
        "error_count": len(errors),
        "errors": errors,
    }

PARTY_COMBAT_FEED_AUDIT_V03031 = party_combat_feed_audit_v03031()
if PARTY_COMBAT_FEED_AUDIT_V03031.get("error_count"):
    raise RuntimeError(
        "Party Combat Feed Audit v0.30.31 failed: "
        + "; ".join(PARTY_COMBAT_FEED_AUDIT_V03031.get("errors", [])[:20])
    )

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
    errors = []
    for name in ("party_combat_target", "auto_priest_party_heal"):
        if not hasattr(MudServer, name):
            errors.append(f"brak MudServer.{name}")
    for name in ("auto_priest_heal_option", "perform_auto_priest_heal"):
        if not hasattr(Session, name):
            errors.append(f"brak Session.{name}")
    if PARTY_AUTO_HEAL_THRESHOLD != 0.85:
        errors.append(f"threshold={PARTY_AUTO_HEAL_THRESHOLD}")
    return {"version": "0.30.32", "error_count": len(errors), "errors": errors}

PARTY_ROLES_AUDIT_V03032 = party_roles_audit_v03032()
if PARTY_ROLES_AUDIT_V03032.get("error_count"):
    raise RuntimeError(
        "Party Roles Audit v0.30.32 failed: "
        + "; ".join(PARTY_ROLES_AUDIT_V03032.get("errors", [])[:20])
    )

# ============================================================
# v0.30.33 - UNIQUE TOOL TIER NAMES + RENEWABLE TAILOR QUEST
# ============================================================
def tool_tier_name_audit_v03033():
    errors = []
    checked = 0
    for tool_type, names in TOOL_TIER_NAMES.items():
        checked += len(names)
        if len(names) != TOOL_MAX_TIER:
            errors.append(f"{tool_type}: {len(names)} nazw, oczekiwano {TOOL_MAX_TIER}")
        normalized = [str(name).strip().casefold() for name in names]
        if len(set(normalized)) != len(normalized):
            seen = set()
            duplicates = []
            for name in normalized:
                if name in seen and name not in duplicates:
                    duplicates.append(name)
                seen.add(name)
            errors.append(f"{tool_type}: duplikaty {duplicates[:5]}")
    quest = QUESTS.get("city_tailor_guard_delivery", {})
    if not quest.get("repeatable"):
        errors.append("city_tailor_guard_delivery nie jest repeatable")
    if int(quest.get("repeat_cooldown", 0) or 0) != int(QUEST_REPEAT_COOLDOWN_SECONDS):
        errors.append("city_tailor_guard_delivery ma zły cooldown")
    return {
        "version": "0.30.33",
        "tool_names_checked": checked,
        "expected_tool_names": len(TOOL_TIER_NAMES) * TOOL_MAX_TIER,
        "tailor_quest_repeatable": bool(quest.get("repeatable")),
        "error_count": len(errors),
        "errors": errors,
    }

TOOL_TIER_NAME_AUDIT_V03033 = tool_tier_name_audit_v03033()
if TOOL_TIER_NAME_AUDIT_V03033.get("error_count"):
    raise RuntimeError(
        "Tool Tier Name Audit v0.30.33 failed: "
        + "; ".join(TOOL_TIER_NAME_AUDIT_V03033.get("errors", [])[:20])
    )

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
    errors = []
    q = QUESTS.get("haldor_steel_recycling", {})
    if q.get("target") != "salvaged_steel_plate" or int(q.get("needed", 0) or 0) != 4:
        errors.append("haldor_steel_recycling target/needed")
    sources = {
        "cemetery_steel_skeleton": 0.72,
        "cemetery_restless_dead": 0.28,
        "cemetery_bone_collector": 0.42,
    }
    for mid, expected in sources.items():
        t = MOB_TEMPLATES.get(mid, {})
        if "salvaged_steel_plate" in (t.get("drops") or {}):
            errors.append(f"{mid}: plate still in direct drops")
        actual = float((t.get("corpse_material_chances") or {}).get("salvaged_steel_plate", -1))
        if abs(actual - expected) > 1e-9:
            errors.append(f"{mid}: corpse chance={actual} expected={expected}")
    if ITEMS.get("salvaged_steel_plate", {}).get("type") != "craft_material":
        errors.append("plate is not craft_material")
    if "salvaged_steel_plate" not in CRAFT_MATERIAL_STORAGE_IDS:
        errors.append("plate missing from craftbox routing")
    return {"version":"0.30.34","sources":len(sources),"error_count":len(errors),"errors":errors}

HALDOR_STEEL_PLATE_CORPSE_AUDIT_V03034 = haldor_steel_plate_corpse_audit_v03034()
if HALDOR_STEEL_PLATE_CORPSE_AUDIT_V03034.get("error_count"):
    raise RuntimeError("Haldor Steel Plate Corpse Audit v0.30.34 failed: " + "; ".join(HALDOR_STEEL_PLATE_CORPSE_AUDIT_V03034["errors"]))

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
def v03035_broken_blades_and_death_audit():
    errors = []
    quest = QUESTS.get("haldor_broken_blades_v0929", {})
    if quest.get("target") != "damaged_weapon_v0929" or int(quest.get("needed", 0) or 0) != 6:
        errors.append("broken blades target/needed")
    if not quest.get("repeatable"):
        errors.append("broken blades not repeatable")
    for mob_id in V03035_BROKEN_BLADE_SOURCES:
        template = MOB_TEMPLATES.get(mob_id)
        if not template:
            errors.append(f"missing source mob: {mob_id}")
            continue
        if v0929_kill_drop_item("haldor_broken_blades_v0929", mob_id, template) != "damaged_weapon_v0929":
            errors.append(f"source not recognized: {mob_id}")
    import inspect as _inspect_v03035
    die_src = _inspect_v03035.getsource(Session.die)
    forbidden = (
        "self.character.silver -=",
        "self.character.gold -=",
        "self.character.mithril -=",
        "remove_item(",
        "remove_storage_item(",
        "clear_skill_buffs()",
    )
    for token in forbidden:
        if token in die_src:
            errors.append(f"death still removes state: {token}")
    return {
        "version": "0.30.35",
        "broken_blade_sources": len(V03035_BROKEN_BLADE_SOURCES),
        "error_count": len(errors),
        "errors": errors,
    }

V03035_AUDIT = v03035_broken_blades_and_death_audit()
if V03035_AUDIT.get("error_count"):
    raise RuntimeError(
        "Broken Blades + Lossless Death Audit v0.30.35 failed: "
        + "; ".join(V03035_AUDIT.get("errors", [])[:30])
    )

HELP_TOPICS["śmierć"] = (
    "Po śmierci postać odradza się w Świątyni Odrodzenia z pełnym HP i Maną. "
    "Nie traci waluty, przedmiotów, EQ, XP, Biegłości, Soul XP, profesji ani poziomów narzędzi. "
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


def v03035_related_quest_flow_audit():
    errors = []
    recipe_outputs = {
        str(recipe.get("output"))
        for table in (CRAFT_RECIPES, COOK_RECIPES, ALCHEMY_RECIPES, JEWELCRAFT_RECIPES)
        for recipe in table.values()
        if recipe.get("output")
    }
    category_targets = {"fish", "fish_river", "ore", "wood", "herb"}
    checked = 0
    for quest_id, quest in QUESTS.items():
        kind = quest.get("kind")
        if kind == "collect":
            checked += 1
            target = quest.get("target")
            if target not in ITEMS:
                errors.append(f"{quest_id}: missing collect target {target}")
            if quest.get("track_craft_progress") and target not in recipe_outputs:
                errors.append(f"{quest_id}: craft target has no recipe {target}")
        elif kind == "collect_category":
            checked += 1
            if quest.get("target") not in category_targets:
                errors.append(f"{quest_id}: unknown category {quest.get('target')}")
        elif kind == "collect_resource":
            checked += 1
            if quest.get("target") not in ITEMS:
                errors.append(f"{quest_id}: missing resource {quest.get('target')}")
        elif kind == "collect_resource_set":
            checked += 1
            requirements = dict(quest.get("resource_targets") or {})
            if not requirements:
                errors.append(f"{quest_id}: empty resource set")
            if sum(max(1, int(v)) for v in requirements.values()) != int(quest.get("needed", 0) or 0):
                errors.append(f"{quest_id}: resource-set needed mismatch")
            for target in requirements:
                if target not in ITEMS:
                    errors.append(f"{quest_id}: missing set resource {target}")
        elif kind == "craft_set":
            checked += 1
            for target in quest.get("targets") or ():
                if target not in recipe_outputs:
                    errors.append(f"{quest_id}: craft-set target has no recipe {target}")

    special_sources = {
        "haldor_broken_blades_v0929": "damaged_weapon_v0929",
        "haldor_armor_recycling_v0929": "heavy_armor_fragment_v0929",
        "orin_toxic_glands_v0929": "toxic_gland_v0929",
    }
    source_counts = {}
    for quest_id, expected_item in special_sources.items():
        matches = 0
        for mob_id, template in MOB_TEMPLATES.items():
            if v0929_kill_drop_item(quest_id, mob_id, template) == expected_item:
                matches += 1
        source_counts[quest_id] = matches
        if matches <= 0:
            errors.append(f"{quest_id}: no kill sources")

    ordinary_item_sources = {
        "soul_shards": "soul_shard",
        "stolen_mountain_ores": "stolen_mountain_ore",
    }
    for quest_id, item_id in ordinary_item_sources.items():
        if not any(item_id in (template.get("drops") or {}) for template in MOB_TEMPLATES.values()):
            errors.append(f"{quest_id}: no mob drop source for {item_id}")

    return {
        "version": "0.30.35",
        "quests_checked": checked,
        "special_source_counts": source_counts,
        "error_count": len(errors),
        "errors": errors,
    }

V03035_RELATED_QUEST_FLOW_AUDIT = v03035_related_quest_flow_audit()
if V03035_RELATED_QUEST_FLOW_AUDIT.get("error_count"):
    raise RuntimeError(
        "Related Quest Flow Audit v0.30.35 failed: "
        + "; ".join(V03035_RELATED_QUEST_FLOW_AUDIT.get("errors", [])[:40])
    )


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
if V03035_EQUIPMENT_LEVEL_AUDIT.get("error_count"):
    raise RuntimeError(
        "Equipment Character Level Audit v0.30.35 failed: "
        + "; ".join(V03035_EQUIPMENT_LEVEL_AUDIT.get("errors", [])[:40])
    )

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
    "Każdy z 10 materiałów obejmuje wszystkie 14 logicznych slotów: głowę, korpus, dłonie, nogi, stopy, talizman, pierścień, naszyjnik, kolczyk, naramienniki, pas, pelerynę, karwasze i relikt.",
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


def apply_separate_class_shops_v03036():
    # 1. Wspólne sale przestają być sklepami.
    for room_id in OLD_SHARED_CLASS_SHOP_ROOMS_V03036:
        SHOPS.pop(room_id, None)
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
        SHOPS[room_id] = list(tier_one)

        seller_id = "class_eq_shop_" + normalize_lookup_text(class_name).replace(" ", "_")
        seller_name = CLASS_SHOP_SELLER_NAMES_V03036[class_name]
        NPCS[seller_id] = {
            "name": seller_name,
            "room": room_id,
            "dialogue": (
                f"Prowadzę osobny sklep EQ klasy {class_name}. "
                "Wpisz shop albo list, aby usłyszeć aktualny Tier wyposażenia "
                "odblokowany przez Level postaci."
            ),
            "shopkeeper": True,
            "class_eq_shop": class_name,
        }
        SHOP_SELLERS[room_id] = seller_id
        if isinstance(globals().get("NPC_DESCRIPTIONS"), dict):
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


# v0.31.2: dwie nowe sale klas technologicznych.
ROOMS.setdefault("guild_mec_chamber", {
    "name": "Hangar Meca", "zone": "Gildia Dusz",
    "desc": "Wzmocniony hangar z rdzeniami energetycznymi i stanowiskami ciężkiego pancerza.",
    "exits": {"south": "guild_martial_hall"},
})
ROOMS.setdefault("guild_engineer_chamber", {
    "name": "Warsztat Inżyniera", "zone": "Gildia Dusz",
    "desc": "Warsztat pełen narzędzi, działek testowych, skanerów i mechanicznych konstrukcji.",
    "exits": {"east": "guild_shadow_gallery"},
})
ROOMS.setdefault("guild_martial_hall", {}).setdefault("exits", {})["east"] = "guild_mec_chamber"
ROOMS.setdefault("guild_shadow_gallery", {}).setdefault("exits", {})["west"] = "guild_engineer_chamber"
NPCS["teacher_mec"]["room"] = "guild_mec_chamber"
NPCS["teacher_engineer"]["room"] = "guild_engineer_chamber"

apply_separate_class_shops_v03036()


def class_shop_audit_v03036():
    errors = []
    checked = 0
    if len(CLASS_SHOP_CLASSES_BY_ROOM) != 14:
        errors.append(f"shop room count={len(CLASS_SHOP_CLASSES_BY_ROOM)} expected=14")
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
        for level in (1, 10, 100, 200, 300, 400):
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
if CLASS_SHOP_AUDIT_V03036.get("error_count"):
    raise RuntimeError(
        "Class Shop Audit v0.30.36 failed: "
        + "; ".join(CLASS_SHOP_AUDIT_V03036.get("errors", [])[:40])
    )

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
def refresh_material_stat_profiles_v03037():
    """Finalna warstwa po Generator Core: 24 różne profile statów per materiał/slot.

    Generator Core może numerycznie wyrównać wartości istniejących statów. Tutaj zachowujemy
    jego całkowity budżet możliwie blisko, ale rozkładamy go na 24 różne podzbiory statów.
    Dzięki temu żadna para wariantów tego samego materiału i slotu nie jest statystyczną kopią.
    """
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


def equipment_completeness_audit_v03037():
    errors = []
    logical_slots = set(CLASS_EQUIPMENT_SLOT_DEFS)
    expected_slots = {
        "head", "body", "hands", "legs", "feet", "charm", "ring", "necklace",
        "earring", "shoulders", "belt", "cloak", "bracers", "relic",
    }
    if logical_slots != expected_slots:
        errors.append(f"class logical slots={sorted(logical_slots)} expected={sorted(expected_slots)}")
    if set(CORPSE_MATERIAL_SLOT_DEFS) != expected_slots:
        errors.append("material corpse slots do not match full logical slot set")

    material_names = set()
    material_items = 0
    duplicate_profiles = []
    for tier in CORPSE_MATERIAL_TIERS:
        ids = CORPSE_MATERIAL_ITEM_IDS.get(tier["key"], ())
        expected_count = len(expected_slots) * CORPSE_RANDOM_VARIANTS_PER_SLOT
        if len(ids) != expected_count:
            errors.append(f"{tier['key']}: item count={len(ids)} expected={expected_count}")
        for slot in expected_slots:
            rows = [ITEMS[i] for i in ids if ITEMS.get(i, {}).get("slot") == slot]
            if len(rows) != CORPSE_RANDOM_VARIANTS_PER_SLOT:
                errors.append(f"{tier['key']} {slot}: variants={len(rows)} expected={CORPSE_RANDOM_VARIANTS_PER_SLOT}")
                continue
            sigs = [tuple(sorted((k, int(v)) for k, v in (row.get("stats") or {}).items())) for row in rows]
            if len(set(sigs)) != len(sigs):
                duplicate_profiles.append(f"{tier['key']}:{slot}")
            for row in rows:
                material_items += 1
                n = normalize_lookup_text(row.get("name", ""))
                if n in material_names:
                    errors.append(f"duplicate material EQ name: {row.get('name')}")
                material_names.add(n)
    if duplicate_profiles:
        errors.append("duplicate material stat profiles: " + ", ".join(duplicate_profiles[:20]))

    # Class EQ must expose earrings on representative levels for all 12 classes.
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for level in (1, 100, 200, 300, 400):
            ids = tiers.get(class_equipment_unlocked_tier(level), ())
            slots = {ITEMS[i].get("slot") for i in ids if i in ITEMS}
            if "earring" not in slots:
                errors.append(f"{class_name} level {level}: missing class earring")
                break

    # Jewelcrafting must offer earrings throughout its tier table.
    jewel_earrings = [i for i, item in ITEMS.items() if item.get("slot") == "earring" and item.get("jewelcraft_level")]
    if len(jewel_earrings) < len(JEWELCRAFTING_TIERS):
        errors.append(f"jewelcraft earrings={len(jewel_earrings)} tiers={len(JEWELCRAFTING_TIERS)}")

    for slot in ("earring", "earring1", "earring2"):
        if slot not in EQUIPMENT_SLOT_NAMES:
            errors.append(f"missing display slot {slot}")
    for alias in ("zkol", "zkol1", "zkol2"):
        if alias not in COMMAND_ALIASES:
            errors.append(f"missing earring shortcut {alias}")

    # Krypta i Wieża Astralna również muszą używać pełnych 14 slotów.
    for tier in (1, 20, 40):
        crypt_slots = {ITEMS.get(f"crypt_t{tier}_{slot}", {}).get("slot") for slot in expected_slots}
        if crypt_slots != expected_slots:
            errors.append(f"crypt tier {tier}: incomplete slots {sorted(expected_slots - crypt_slots)}")
    for tier in (1, 6, 11):
        astral_slots = {ITEMS.get(f"astral_t{tier}_{slot}", {}).get("slot") for slot in expected_slots}
        if astral_slots != expected_slots:
            errors.append(f"astral tier {tier}: incomplete slots {sorted(expected_slots - astral_slots)}")

    # Żadna nazwa pancerza/EQ w całej grze nie może się powtarzać.
    armor_names = {}
    duplicate_armor_names = []
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        key = normalize_lookup_text(item.get("name", ""))
        previous = armor_names.get(key)
        if previous is not None:
            duplicate_armor_names.append((previous, item_id, item.get("name", "")))
        else:
            armor_names[key] = item_id
    if duplicate_armor_names:
        errors.append("duplicate armor names: " + repr(duplicate_armor_names[:10]))

    # Reprezentatywny klasowy Tier: każdy slot musi mieć odmienny pełny profil
    # (obrona + staty + właściwości), więc nowe sloty nie są mechanicznymi kopiami.
    class_profiles_checked = 0
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        ids = list(tiers.get(class_equipment_unlocked_tier(200), ()))
        # Pierwsza linia stylistyczna: po jednej części z każdego slotu.
        first_style = {}
        for iid in ids:
            item = ITEMS.get(iid, {})
            if int(item.get("class_equipment_style", 1) or 1) == 1:
                first_style.setdefault(item.get("slot"), item)
        if set(first_style) != expected_slots:
            errors.append(f"{class_name}: incomplete representative class profile")
            continue
        signatures = []
        for slot in sorted(expected_slots):
            item = first_style[slot]
            signatures.append((
                int(item.get("defense", 0) or 0),
                item.get("affix"), int(item.get("affix_amount", 0) or 0),
                tuple(sorted((item.get("stats") or {}).items())),
                tuple(sorted((item.get("properties") or {}).items())),
            ))
        class_profiles_checked += len(signatures)
        if len(set(signatures)) != len(signatures):
            errors.append(f"{class_name}: duplicated slot profiles at Level 200")

    return {
        "version": "0.30.37",
        "logical_slot_count": len(expected_slots),
        "material_items_checked": material_items,
        "material_name_count": len(material_names),
        "global_armor_name_count": len(armor_names),
        "class_profiles_checked": class_profiles_checked,
        "materials": len(CORPSE_MATERIAL_TIERS),
        "variants_per_material_slot": CORPSE_RANDOM_VARIANTS_PER_SLOT,
        "error_count": len(errors),
        "errors": errors,
    }

V03037_EQUIPMENT_COMPLETENESS_AUDIT = equipment_completeness_audit_v03037()
if V03037_EQUIPMENT_COMPLETENESS_AUDIT.get("error_count"):
    raise RuntimeError(
        "Equipment Completeness Audit v0.30.37 failed: "
        + "; ".join(V03037_EQUIPMENT_COMPLETENESS_AUDIT.get("errors", [])[:50])
    )

HELP_TOPICS["kolczyki"] = [
    "Kolczyki są pełnoprawnym EQ. Możesz nosić dwa naraz: kolczyk 1 i kolczyk 2.",
    "zkol pokazuje posiadane kolczyki i automatycznie wybiera wolne/słabsze miejsce; zkol1 i zkol2 wymuszają konkretny slot.",
    "Kolczyki występują jako klasowe EQ, materiałowy drop z mobów oraz receptury Jubilerstwa. Mogą mieć gniazda na oszlifowane klejnoty.",
    "Materiałowe kolczyki istnieją dla Żelaza, Stali, Mithrilu, Adamantytu, Kobaltu, Runicznego metalu, Smoczej Stali, Astralu, Pustki i Eternium.",
]
HELP_TOPICS.setdefault("materialy_eq", []).append(
    "v0.30.37: materiałowe EQ obejmuje wszystkie 14 logicznych slotów, w tym naramienniki, pas, pelerynę, karwasze, relikt i nowe kolczyki. Każdy wariant ma niepowtarzalną nazwę i profil statów w obrębie materiału/slotu."
)
HELP_TOPICS.setdefault("jubilerstwo", []).append(
    "v0.30.37: Jubilerstwo tworzy też kolczyki. Jedna receptura daje jedną sztukę; do obu uszu potrzebujesz dwóch. Kolczyki obsługują gniazda klejnotów."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.30.37: pełny pass EQ: 14 logicznych slotów, dwa miejsca na kolczyki, pełne materiałowe dropy wszystkich slotów i audit braku powtórek nazw/profili statów."
)
LATEST_CHANGES_TITLE = "Soulbound v0.30.37 - Complete EQ Slots + Earrings + Unique Material Stats"
LATEST_CHANGES = [
    "v0.30.37: dodano kolczyki jako pełnoprawne dwa sloty użytkowe: kolczyk 1 i kolczyk 2, z automatycznym zkol oraz ręcznym zkol1/zkol2.",
    "v0.30.37: kolczyki są dostępne w klasowym EQ, materiale z mobów oraz Jubilerstwie i obsługują gniazda klejnotów.",
    "v0.30.37: materiałowe EQ z ciał obejmuje teraz wszystkie 14 logicznych slotów dla wszystkich 10 materiałów od Żelaza do Eternium.",
    "v0.30.37: 24 warianty każdego materiału/slotu mają niepowtarzalne profile statów; nazwy materiałowego EQ są globalnie unikalne.",
    "v0.30.37: sloty mają własne preferencje statów/właściwości, więc np. korpus, karwasze, peleryna i kolczyki nie są statystycznymi kopiami.",
    "v0.30.37: Krypta i Wieża Astralna zostały podniesione do pełnych 14 slotów; stare sześcioslotowe pule nie ograniczają już nowych dropów.",
    "v0.30.37: globalny audit wymaga unikalnej nazwy każdego EQ typu armor i rozróżnia pełne profile klasowych slotów.",
    "v0.30.37: po dodaniu kolczyków podstawowe sloty wearable są kompletne; Broń Duszy pozostaje osobnym systemem broni i nie jest dublowana zwykłym main-hand/off-hand.",
] + LATEST_CHANGES



# ============================================================
# v0.30.38 - BROKEN BLADES SPOKEN PROGRESS HOTFIX
# ============================================================
def broken_blades_spoken_progress_audit_v03038():
    errors = []
    import inspect as _inspect_v03038
    src = _inspect_v03038.getsource(Session.grant_hourly_quest_kill_drop_v0929)
    required = (
        "increment_item_collect_quest",
        "Postęp questa:",
        "quest_progress=False",
    )
    for token in required:
        if token not in src:
            errors.append(f"missing runtime token: {token}")
    quest = QUESTS.get("haldor_broken_blades_v0929", {})
    if quest.get("target") != "damaged_weapon_v0929" or int(quest.get("needed", 0) or 0) != 6:
        errors.append("broken blades target/needed changed")
    return {
        "version": "0.30.38",
        "error_count": len(errors),
        "errors": errors,
    }

BROKEN_BLADES_SPOKEN_PROGRESS_AUDIT_V03038 = broken_blades_spoken_progress_audit_v03038()
if BROKEN_BLADES_SPOKEN_PROGRESS_AUDIT_V03038.get("error_count"):
    raise RuntimeError(
        "Broken Blades Spoken Progress Audit v0.30.38 failed: "
        + "; ".join(BROKEN_BLADES_SPOKEN_PROGRESS_AUDIT_V03038["errors"])
    )

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


def profession_carryover_audit_v03039():
    errors = []
    pool_checks = 0
    positive_weights = 0
    thresholds = tuple(int(v) for v in TOOL_TIER_THRESHOLDS)

    groups = {
        "rzeka": tuple(RIVER_FISH_ATLAS),
        "jezioro": tuple(LAKE_FISH_ATLAS),
        "morze": tuple(SEA_FISH_ATLAS),
        "ocean": tuple(OCEAN_FISH_ATLAS),
        "rudy": tuple(ORE_RESOURCE_IDS),
        "drewno": tuple(WOOD_RESOURCE_IDS),
        "ziola": tuple(HERB_RESOURCE_IDS),
        "klejnoty": tuple(
            iid for iid, item in ITEMS.items()
            if item.get("type") == "gem_raw" and not item.get("gem_quality")
        ),
    }
    final_sizes = {}
    for label, ids in groups.items():
        previous = set()
        for level in thresholds:
            pool = tuple(generator_core_v027.resource_pool(ids, ITEMS, level, f"audit:{label}"))
            pool_checks += 1
            current = set(pool)
            if not previous.issubset(current):
                errors.append(f"{label}: zasób zniknął przy Tierze dla levelu {level}")
            weights = generator_core_v027.resource_weights(pool, ITEMS, level, f"audit:{label}")
            if len(weights) != len(pool):
                errors.append(f"{label}: niezgodna liczba wag na levelu {level}")
            for item_id, weight in zip(pool, weights):
                if float(weight) <= 0:
                    errors.append(f"{label}: zerowa waga {item_id} na levelu {level}")
                else:
                    positive_weights += 1
            previous = current
        final_sizes[label] = len(previous)

    # Specjalne łowisko nie może wycinać gatunków ze zwykłej kumulacyjnej puli.
    forest_pref = set(FISHING_ECOLOGY_PREFERRED_IDS.get("forest_stream") or ())
    river_low = set(generator_core_v027.resource_pool(tuple(RIVER_FISH_ATLAS), ITEMS, thresholds[0], "audit:forest"))
    river_high = set(generator_core_v027.resource_pool(tuple(RIVER_FISH_ATLAS), ITEMS, thresholds[-1], "audit:forest"))
    if not river_low.issubset(river_high):
        errors.append("forest_stream: wcześniejsze ryby nie są podzbiorem późniejszej puli")
    if forest_pref and not (forest_pref & river_high):
        errors.append("forest_stream: preferencje ekologiczne nie przecinają puli rzecznej")

    recipe_count = 0
    forbidden_max_keys = (
        "max_profession_level", "max_tool_level", "max_level",
        "maximum_profession_level", "maximum_tool_level",
    )
    for table_name, table in (
        ("craft", CRAFT_RECIPES), ("cook", COOK_RECIPES),
        ("alchemy", ALCHEMY_RECIPES), ("jewel", JEWELCRAFT_RECIPES),
    ):
        for recipe_id, recipe in table.items():
            recipe_count += 1
            for key in forbidden_max_keys:
                if recipe.get(key) not in (None, 0, ""):
                    errors.append(f"{table_name}:{recipe_id}: górny limit {key}")

    # Quest Marcela: pełna baza gatunków rzecznych + ich rzadkie warianty.
    recipe = COOK_RECIPES.get("grilled_river_fish", {})
    pool = set(recipe.get("pooled_ingredient_pool") or ())
    expected = {
        item_id for item_id in FISH_STORAGE_IDS
        if base_fish_species_id(item_id) in RIVER_FISH_ATLAS
    }
    missing = expected - pool
    if missing:
        errors.append("Pieczona ryba rzeczna: brakuje ryb: " + ", ".join(sorted(missing)[:20]))
    if int(recipe.get("pooled_ingredient_count", 0) or 0) != 2:
        errors.append("Pieczona ryba rzeczna: wymaganie nie wynosi 2 ryb")
    if recipe.get("distinct_ingredient_pool"):
        errors.append("Pieczona ryba rzeczna nadal wymaga różnych gatunków")

    race_topics = 0
    for race_name, *_rest in RACES:
        slug = "rasa_" + normalize_lookup_text(race_name).replace(" ", "_")
        if slug not in HELP_TOPICS:
            errors.append(f"brak help rasy: {race_name}")
        else:
            race_topics += 1

    return {
        "version": "0.30.39",
        "race_topics": race_topics,
        "pool_checks": pool_checks,
        "positive_weights_checked": positive_weights,
        "recipes_checked": recipe_count,
        "river_recipe_pool_size": len(pool),
        "river_base_species": len(RIVER_FISH_ATLAS),
        "final_pool_sizes": final_sizes,
        "error_count": len(errors),
        "errors": errors,
    }

PROFESSION_CARRYOVER_AUDIT_V03039 = profession_carryover_audit_v03039()
if PROFESSION_CARRYOVER_AUDIT_V03039.get("error_count"):
    raise RuntimeError(
        "Profession Carryover Audit v0.30.39 failed: "
        + "; ".join(PROFESSION_CARRYOVER_AUDIT_V03039.get("errors", [])[:50])
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

# ============================================================
# v0.30.40 - COMPLETE EQ SHORTCUTS + OPTIONAL AUTO EQUIP
# ============================================================
def eq_shortcuts_auto_audit_v03040():
    errors = []
    expected_aliases = {
        "zhel":"equiphead", "zpan":"equipbody", "zrek":"equiphands",
        "znog":"equiplegs", "zbut":"equipfeet", "ztal":"equipcharmauto",
        "zpier":"equipringauto", "znasz":"equipnecklace", "zkol":"equipearringauto",
        "znar":"equipshoulders", "zpas":"equipbelt", "zpel":"equipcloak",
        "zkar":"equipbracers", "zrel":"equiprelic",
        "autoeq":"autoequip", "eqauto":"autoequip", "zauto":"autoequip",
    }
    for alias, expected in expected_aliases.items():
        if COMMAND_ALIASES.get(alias) != expected:
            errors.append(f"{alias}: {COMMAND_ALIASES.get(alias)!r}, expected {expected!r}")
    import inspect as _inspect_v03040
    src = _inspect_v03040.getsource(Session.auto_equip_best_v03040)
    for token in (
        "required_class", "equipment_mastery_requirement_met",
        "ring1", "ring2", "charm1", "charm2", "earring1", "earring2",
        "return_socketed_gems", "AUTO EQ",
    ):
        if token not in src:
            errors.append(f"auto eq missing token: {token}")
    if len(CLASS_EQUIPMENT_SLOT_DEFS) != 14:
        errors.append(f"logical EQ slot count {len(CLASS_EQUIPMENT_SLOT_DEFS)}, expected 14")
    return {
        "version":"0.30.40",
        "shortcut_count":len(expected_aliases),
        "logical_slot_count":len(CLASS_EQUIPMENT_SLOT_DEFS),
        "error_count":len(errors),
        "errors":errors,
    }

EQ_SHORTCUTS_AUTO_AUDIT_V03040 = eq_shortcuts_auto_audit_v03040()
if EQ_SHORTCUTS_AUTO_AUDIT_V03040.get("error_count"):
    raise RuntimeError(
        "EQ Shortcuts/Auto Audit v0.30.40 failed: "
        + "; ".join(EQ_SHORTCUTS_AUTO_AUDIT_V03040.get("errors", [])[:30])
    )

HELP_TOPICS["skroty_eq"] = [
    "Pełne skróty zakładania EQ: zhel hełm, zpan pancerz, zrek rękawice, znog nogawice, zbut buty.",
    "Biżuteria: ztal talizmany auto, zpier pierścienie auto, znasz naszyjnik, zkol kolczyki auto. Ręcznie nadal działają zt1/zt2, zp1/zp2 i zkol1/zkol2.",
    "Pozostałe: znar naramienniki, zpas pas, zpel peleryna, zkar karwasze, zrel relikt.",
    "Stare skróty zh, zz, zr, zn, zb, zt, zp, zna itd. nadal działają.",
    "Samo wpisanie skrótu pokazuje numerowaną listę posiadanego EQ danego slotu; skrót + numer zakłada wybraną pozycję.",
    "eq auto, załóż auto, autoeq, eqauto albo zauto automatycznie wymienia dostępne części na indywidualnie najmocniejsze posiadane EQ.",
]
HELP_TOPIC_ALIASES.update({
    "skroty eq":"skroty_eq", "skróty eq":"skroty_eq", "eq skroty":"skroty_eq",
    "eq skróty":"skroty_eq", "auto eq":"skroty_eq", "autoeq":"skroty_eq",
})
HELP_TOPICS.setdefault("eq", []).extend([
    "v0.30.40: pełne czytelne skróty: zhel, zpan, zrek, znog, zbut, ztal, zpier, znasz, zkol, znar, zpas, zpel, zkar, zrel. Stare skróty nadal działają.",
    "v0.30.40: eq auto / załóż auto / autoeq / zauto jednym poleceniem wymienia posiadane, dostępne EQ na indywidualnie najmocniejsze części. Auto respektuje Level postaci, aktywną klasę i liczbę posiadanych kopii.",
    "Auto EQ nie klonuje podwójnej biżuterii; do dwóch identycznych pierścieni, talizmanów lub kolczyków potrzebujesz dwóch sztuk. Klejnoty z wymienianej biżuterii wracają do Szkatułki.",
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
    "v0.30.40: komunikaty setów zostały zsynchronizowane z 14 logicznymi typami EQ.",
]


# ============================================================
# v0.30.41 - UNIVERSAL EQUIPMENT SALVAGE
# ============================================================
def universal_salvage_audit_v03041():
    errors = []
    armor_ids = [item_id for item_id, item in ITEMS.items() if item.get("type") == "armor"]
    by_material = {key: 0 for key in V0925_SALVAGE_MATERIALS}
    for item_id in armor_ids:
        item = ITEMS[item_id]
        material = v03041_salvage_material_key(item)
        if material not in V0925_SALVAGE_MATERIALS:
            errors.append(f"{item_id}: invalid salvage material {material!r}")
            continue
        by_material[material] += 1
        level = max(1, min(400, int(item.get("required_character_level", item.get("required_mastery", 1)) or 1)))
        # Bez jawnego materiału późne EQ nie może wpadać z powrotem do Żelaza.
        explicit = str(item.get("corpse_material") or item.get("blacksmith_material") or "").strip()
        if not explicit and level >= 360 and material != "eternium" and not any(
            token in normalize_lookup_text(item.get("name", ""))
            for token in ("eternium", "pustk", "astral", "smocz", "runicz", "kobalt", "adamant", "mithril", "stal", "zelaz")
        ):
            errors.append(f"{item_id}: level {level} maps to {material}, expected eternium")
    import inspect as _inspect_v03041
    src = _inspect_v03041.getsource(Session.salvage_equipment_v0925)
    for token in (
        "free_equipment_quantity", "v03041_salvage_material_key",
        "equipment_runes_v0925", "clear_equipment_crafting_v0925",
        "ROZKŁADANIE EQ", "Wybierz numer",
    ):
        if token not in src:
            errors.append(f"salvage implementation missing token: {token}")
    if "is_character_bound_item" in src:
        errors.append("salvage still rejects bound armor")
    return {
        "version": "0.30.41",
        "armor_checked": len(armor_ids),
        "material_counts": by_material,
        "error_count": len(errors),
        "errors": errors,
    }

UNIVERSAL_SALVAGE_AUDIT_V03041 = universal_salvage_audit_v03041()
if UNIVERSAL_SALVAGE_AUDIT_V03041.get("error_count"):
    raise RuntimeError(
        "Universal Salvage Audit v0.30.41 failed: "
        + "; ".join(UNIVERSAL_SALVAGE_AUDIT_V03041.get("errors", [])[:50])
    )

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
    errors = []
    armor_ids = [iid for iid, item in ITEMS.items() if item.get("type") == "armor"]
    for item_id in armor_ids:
        item = ITEMS[item_id]
        previous_req = 0
        previous_cost = 0
        for target in range(1, V03042_EQ_UPGRADE_MAX + 1):
            req = v03042_upgrade_required_smithing(item, target)
            cost = v03042_upgrade_material_cost(item, target)
            if not 1 <= req <= 400:
                errors.append(f"{item_id}: bad smithing requirement +{target}={req}")
                break
            if req < previous_req:
                errors.append(f"{item_id}: smithing requirement decreases at +{target}")
                break
            if cost <= 0 or cost < previous_cost:
                errors.append(f"{item_id}: bad/nonmonotonic material cost +{target}={cost}")
                break
            previous_req, previous_cost = req, cost
        material = v03041_salvage_material_key(item)
        if material not in V0925_SALVAGE_MATERIALS:
            errors.append(f"{item_id}: invalid upgrade material {material}")
    expected_aliases = {
        "ulepsz": "equpgrade", "ulepszaj": "equpgrade", "upgrade": "equpgrade",
        "upgradeeq": "equpgrade", "ulepszeq": "equpgrade",
    }
    for alias, command in expected_aliases.items():
        if COMMAND_ALIASES.get(alias) != command:
            errors.append(f"shortcut {alias} -> {COMMAND_ALIASES.get(alias)!r}, expected {command!r}")
    import inspect as _inspect_v03042
    src = _inspect_v03042.getsource(Session.upgrade_equipment_v03042)
    for token in (
        "Kowalstwo", "crafting_hammer", "required_tool_tier_for_level",
        "v03042_upgrade_material_cost", "set_equipment_upgrade_level_v03042",
        "grant_profession_progress", "Nie ma ryzyka zniszczenia",
    ):
        if token not in src:
            errors.append(f"upgrade implementation missing token: {token}")
    return {
        "version": "0.30.42",
        "armor_checked": len(armor_ids),
        "max_upgrade": V03042_EQ_UPGRADE_MAX,
        "error_count": len(errors),
        "errors": errors,
    }

EQUIPMENT_UPGRADE_AUDIT_V03042 = equipment_upgrade_audit_v03042()
if EQUIPMENT_UPGRADE_AUDIT_V03042.get("error_count"):
    raise RuntimeError(
        "Equipment Upgrade Audit v0.30.42 failed: "
        + "; ".join(EQUIPMENT_UPGRADE_AUDIT_V03042.get("errors", [])[:50])
    )

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

COMMAND_ALIASES.update({
    # Extended crafting professions: Polish + English pairs.
    "tailoring": "krawiectwo", "tailor": "krawiectwo",
    "sew": "szyj", "sewing": "szyj",
    "leatherworking": "garbarstwo", "leatherwork": "garbarstwo",
    "tan": "garbuj", "tanning": "garbuj",
    "carpentry": "stolarstwo", "woodworking": "stolarstwo",
    "woodcraft": "stolarka", "carpenter": "stolarstwo",
    "enchanting": "zaklinanie", "enchantinginfo": "zaklinanie",
    "enchantitem": "zaklinaj", "enchant": "zaklinaj",
    # Current 2.0 systems.
    "craftingmastery": "craftmastery",
    "leaderboard": "leaderboards", "rankings": "leaderboards",
    "collections": "collection2", "completionpercent": "completion",
    "deathsummary": "deathrecap", "combatsummary": "combatrecap",
})

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
        "tailoring / krawiectwo; sew / szyj <recipe> - Krawiectwo 1-400",
        "leatherworking / garbarstwo; tan / garbuj <recipe> - Garbarstwo 1-400",
        "carpentry / stolarstwo; woodcraft / stolarka <recipe> - Stolarstwo 1-400",
        "enchanting / zaklinanie; enchantitem / zaklinaj <slot> <type>; enchants - Zaklinanie 1-400",
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


def full_game_audit_v03055():
    errors = []
    warnings = []

    # 1. World graph: every explicit exit must point to a real room.
    bad_exits = []
    dynamic_exits = []
    dynamic_prefixes = (
        "prof_", "mine_floor_", "crypt_floor_", "astral_floor_",
        "mythic_crypt_floor_", "mythic_astral_floor_", "giant_fortress_",
        "v0130_frontier_", "v018_endless_", "v020_mega_",
    )
    exit_count = 0
    for room_id, room in ROOMS.items():
        exits = room.get("exits", {}) or {}
        if isinstance(exits, dict):
            for direction, target in exits.items():
                exit_count += 1
                if target not in ROOMS:
                    if str(target).startswith(dynamic_prefixes):
                        dynamic_exits.append(f"{room_id}:{direction}->{target}")
                    else:
                        bad_exits.append(f"{room_id}:{direction}->{target}")
    if bad_exits:
        errors.append("invalid static room exits: " + ", ".join(bad_exits[:20]))
    if dynamic_exits:
        warnings.append(f"dynamic exit targets={len(dynamic_exits)} (validated by runtime generators)")

    # 2. Core catalogs.
    if len(CLASSES) != 14:
        errors.append(f"classes={len(CLASSES)}, expected 14")
    class_names = [row[0] for row in CLASSES]
    missing_skill_classes = [name for name in class_names if not CLASS_SKILLS.get(name)]
    if missing_skill_classes:
        errors.append("classes without skills: " + ", ".join(missing_skill_classes))
    if not ITEMS:
        errors.append("ITEMS is empty")
    if not MOB_TEMPLATES:
        errors.append("MOB_TEMPLATES is empty")
    if not QUESTS:
        errors.append("QUESTS is empty")

    # 3. Recipe integrity across all major recipe registries.
    recipe_sets = {
        "craft": CRAFT_RECIPES,
        "cook": COOK_RECIPES,
        "alchemy": ALCHEMY_RECIPES,
        "jewel": JEWELCRAFT_RECIPES,
        "extended": V03053_CRAFT_RECIPES,
    }
    recipe_count = 0
    for label, table in recipe_sets.items():
        for recipe_id, recipe in table.items():
            recipe_count += 1
            for item_id, qty in (recipe.get("ingredients", {}) or {}).items():
                if item_id not in ITEMS:
                    errors.append(f"{label}/{recipe_id}: missing ingredient {item_id}")
                if int(qty or 0) <= 0:
                    errors.append(f"{label}/{recipe_id}: invalid quantity {item_id}={qty}")
            output = recipe.get("output")
            if output and output not in ITEMS:
                errors.append(f"{label}/{recipe_id}: missing output {output}")

    # 4. Profession/tool mappings.
    expected_professions = {
        "fishing":"Wędkarstwo", "mining":"Górnictwo", "woodcutting":"Drwalstwo",
        "crafting":"Kowalstwo", "cooking":"Gotowanie", "herbalism":"Zielarstwo",
        "alchemy":"Alchemia", "jewelcrafting":"Jubilerstwo", "tailoring":"Krawiectwo",
        "leatherworking":"Garbarstwo", "carpentry":"Stolarstwo", "enchanting":"Zaklinanie",
    }
    for tool_type, profession in expected_professions.items():
        if TOOL_PROFESSION_MAP.get(tool_type) != profession:
            errors.append(f"tool/profession map {tool_type}->{TOOL_PROFESSION_MAP.get(tool_type)!r}, expected {profession}")
        if profession not in PROFESSION_RANK_NAMES:
            errors.append(f"missing rank names for {profession}")

    # 5. English command coverage for every newer Polish-only canonical command.
    english_aliases = {
        "tailoring":"krawiectwo", "sew":"szyj",
        "leatherworking":"garbarstwo", "tan":"garbuj",
        "carpentry":"stolarstwo", "woodcraft":"stolarka",
        "enchanting":"zaklinanie", "enchantitem":"zaklinaj",
        "craftingmastery":"craftmastery", "leaderboard":"leaderboards",
        "rankings":"leaderboards", "deathsummary":"deathrecap",
        "combatsummary":"combatrecap",
    }
    for alias, target in english_aliases.items():
        if COMMAND_ALIASES.get(alias) != target:
            errors.append(f"English command alias missing/wrong: {alias}->{COMMAND_ALIASES.get(alias)!r}, expected {target}")

    # 6. HELP integrity and current-system coverage.
    virtual_help = {"tematy", "komendy", "wszystko", "kategorie"}
    for alias, target in HELP_TOPIC_ALIASES.items():
        if target not in HELP_TOPICS and target not in virtual_help:
            errors.append(f"HELP alias without target: {alias}->{target}")
    required_help = {
        "krawiectwo", "garbarstwo", "stolarstwo", "zaklinanie",
        "jakosccraftu", "krytycznycraft", "craftmastery",
        "collection2", "completion2", "leaderboards2", "mentor2",
        "housing2", "transport2", "recaps", "loothistory2",
        "accessibility_presets", "social2",
    }
    for topic in sorted(required_help):
        rows = HELP_TOPICS.get(topic)
        if not rows:
            errors.append(f"missing current HELP topic: {topic}")

    # 7. Important data collisions worth reviewing, but not fatal.
    names = {}
    for item_id, item in ITEMS.items():
        name = normalize_lookup_text(item.get("name", ""))
        if name:
            names.setdefault(name, []).append(item_id)
    duplicate_names = {name: ids for name, ids in names.items() if len(ids) > 1}
    if duplicate_names:
        warnings.append(f"duplicate visible item names={len(duplicate_names)} (may be intentional variants)")

    return {
        "version": "0.30.55",
        "rooms": len(ROOMS),
        "exits": exit_count,
        "items": len(ITEMS),
        "mobs": len(MOB_TEMPLATES),
        "quests": len(QUESTS),
        "classes": len(CLASSES),
        "skills": sum(len(CLASS_SKILLS.get(name, ())) for name in class_names),
        "professions": len(PROFESSION_RANK_NAMES),
        "recipes": recipe_count,
        "help_topics": len(HELP_TOPICS),
        "help_aliases": len(HELP_TOPIC_ALIASES),
        "command_aliases": len(COMMAND_ALIASES),
        "warnings": warnings,
        "error_count": len(errors),
        "errors": errors,
    }

FULL_GAME_AUDIT_V03055 = full_game_audit_v03055()
if FULL_GAME_AUDIT_V03055["error_count"]:
    raise RuntimeError(
        "Full Game Audit v0.30.55 failed: " + "; ".join(FULL_GAME_AUDIT_V03055["errors"][:80])
    )

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
    ]
    HELP_TOPICS["mec"] = [
        "Mec: technologiczna klasa fizyczna 1-400. Broń Duszy: Rdzeń Meca.",
        "Ma pełną siatkę 123 skilli: 3 na progu 1 i co 10 aż do 400. Wczesne umiejętności obejmują Fire Beam, Ice Beam, Bolt Beam, TekShield, Gravity Bomb, TekMissile, Heal Force i Overdrive.",
        "Styl: ciężki pancerz, bariery, salwy rdzenia i przeciążenia systemów.",
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
