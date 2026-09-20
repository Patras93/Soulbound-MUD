

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
    if not audit.get("runtime_fast_path") and not audit.get("semantic_preserved"):
        errors.append("Generator Core changed protected authored semantics")
    # Explicit regression guards for semantics previously overwritten by Generator Core.
    if tuple(SOUL_MILESTONE_TIERS) != (5, 10, 15, 20):
        errors.append(f"Soul Milestones changed: {SOUL_MILESTONE_TIERS}")
    skill_grid = {1, *range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10)}
    for cname, rows in CLASS_SKILLS.items():
        if cname in ("Inżynier","Mec"):
            if any(not 1 <= int(s.get("unlock", 0) or 0) <= CLASS_MASTERY_MAX_LEVEL for s in rows):
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
    if GENERATOR_CORE_VERSION != "0.36.11":
        errors.append(f"Generator Core version={GENERATOR_CORE_VERSION}, expected 0.36.11")
    if not audit.get("numeric_only"):
        errors.append("numeric_only flag missing")
    runtime_fast = bool(audit.get("runtime_fast_path"))
    if not runtime_fast:
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
    if not runtime_fast:
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
        for mastery in (1, 100, 200, 400, 600):
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
        for mastery in (1,100,200,300,400,600):
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
    if GENERATOR_CORE_VERSION != "0.36.11":
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

    if GENERATOR_CORE_VERSION != "0.36.11":
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
        "hourly_shadow_fangs": "wolf_fang",
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
        for level in (1, 100, 200, 300, 400, 600):
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
    # v0.35.3: the active method is the newer Salvage 3.0 wrapper, which
    # delegates classic armor salvage to SessionForgeGuildsMixin. Audit both
    # layers instead of forcing the old implementation to remain first in MRO.
    base_src = _inspect_v03041.getsource(SessionForgeGuildsMixin.salvage_equipment_v0925)
    active_src = _inspect_v03041.getsource(Session.salvage_equipment_v0925)
    for token in (
        "free_equipment_quantity", "v03041_salvage_material_key",
        "equipment_runes_v0925", "clear_equipment_crafting_v0925",
        "ROZKŁADANIE EQ", "Wybierz numer",
    ):
        if token not in base_src:
            errors.append(f"salvage base implementation missing token: {token}")
    if "is_character_bound_item" in base_src:
        errors.append("salvage still rejects bound armor")
    if "SessionForgeGuildsMixin.salvage_equipment_v0925" not in active_src:
        errors.append("Salvage 3.0 wrapper no longer delegates classic armor salvage")
    if "SALVAGE3_V03114" not in active_src:
        errors.append("Salvage 3.0 wrapper missing extended salvage registry")
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
            if not 1 <= req <= CHARACTER_MAX_LEVEL:
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
def full_game_predeploy_audit_v0336():
    errors=[]; warnings=[]; metrics={}
    def err(kind,*parts): errors.append((kind,*parts))

    # 1) Core registries and basic identity.
    registries={
        'rooms':ROOMS,'items':ITEMS,'mobs':MOB_TEMPLATES,'quests':QUESTS,
        'npcs':NPCS,'shops':SHOPS,'classes':CLASSES,'skills':CLASS_SKILLS,
        'help_topics':HELP_TOPICS,'help_aliases':HELP_TOPIC_ALIASES,
        'command_aliases':COMMAND_ALIASES,
    }
    for name,table in registries.items():
        metrics[name]=len(table)
        if not table: err('empty_registry',name)

    # 2) UTF-8/mojibake guard for runtime-visible text.
    bad_text_tokens=('\ufffd','Ã','Â','â€','â€™','ï¿½')
    def bad_text(value):
        s=str(value or '')
        return any(tok in s for tok in bad_text_tokens)
    for iid,it in ITEMS.items():
        for field in ('name','desc','rarity_name'):
            if bad_text(it.get(field,'')): err('mojibake_item',iid,field,it.get(field))
    for mid,mob in MOB_TEMPLATES.items():
        for field in ('name','desc'):
            if bad_text(mob.get(field,'')): err('mojibake_mob',mid,field,mob.get(field))
    for qid,q in QUESTS.items():
        for field in ('name','desc','description'):
            if bad_text(q.get(field,'')): err('mojibake_quest',qid,field,q.get(field))
    for rid,room in ROOMS.items():
        for field in ('name','desc'):
            if bad_text(room.get(field,'')): err('mojibake_room',rid,field,room.get(field))
    for topic,lines in HELP_TOPICS.items():
        if bad_text(topic): err('mojibake_help_topic',topic)
        if isinstance(lines,(list,tuple)):
            for line in lines:
                if bad_text(line): err('mojibake_help',topic,line)

    # 2b) Player-facing names that identify content must be globally unique
    # inside their own registry. This is especially important for NVDA navigation.
    for registry_name,table in (
        ('items',ITEMS),('mobs',MOB_TEMPLATES),('quests',QUESTS),('npcs',NPCS),('rooms',ROOMS)
    ):
        names={}
        for object_id,obj in table.items():
            name=str(obj.get('name') or '').strip()
            if not name:
                continue
            key=name.casefold()
            names.setdefault(key,[]).append(object_id)
        for key,object_ids in names.items():
            if len(object_ids)>1:
                err('duplicate_display_name',registry_name,key,tuple(object_ids))

    # 3) Rooms and exits.
    dynamic_prefixes=(
        'prof_','mine_floor_','crypt_floor_','astral_floor_','mythic_crypt_floor_',
        'mythic_astral_floor_','giant_fortress_','v0130_frontier_','v018_endless_',
        'v020_mega_'
    )
    for rid,room in ROOMS.items():
        if not str(room.get('name') or '').strip(): err('room_missing_name',rid)
        for direction,target in (room.get('exits') or {}).items():
            if target not in ROOMS and not str(target).startswith(dynamic_prefixes):
                err('broken_exit',rid,direction,target)

    # 4) NPCs and shops.
    for nid,npc in NPCS.items():
        if not str(npc.get('name') or '').strip(): err('npc_missing_name',nid)
        room=npc.get('room')
        if room and room not in ROOMS: err('npc_missing_room',nid,room)
        for key in ('quest','specialist_quest'):
            qid=npc.get(key)
            if qid and qid not in QUESTS: err('npc_missing_quest',nid,key,qid)
        for qid in tuple(npc.get('quest_chain') or ()) + tuple(npc.get('specialist_quests') or ()):
            if qid not in QUESTS: err('npc_missing_quest',nid,'chain',qid)
    for shop_id,offers in SHOPS.items():
        for iid in offers or ():
            if iid not in ITEMS: err('shop_missing_item',shop_id,iid)
    for room_id,offers in CLASS_SHOP_ITEMS_BY_ROOM.items():
        if room_id not in ROOMS: err('class_shop_missing_room',room_id)
        for iid in offers or ():
            if iid not in ITEMS: err('class_shop_missing_item',room_id,iid)

    # 5) Item identity and player-facing names.
    technical_name_prefixes=('craftq_','item_','eq_','loot_')
    for iid,it in ITEMS.items():
        name=str(it.get('name') or '').strip()
        if not name: err('item_missing_name',iid)
        if name==str(iid) or name.lower().startswith(technical_name_prefixes):
            err('technical_item_name',iid,name)
        if 'price' in it:
            try:
                if int(it.get('price') or 0) < 0: err('negative_price',iid,it.get('price'))
            except Exception: err('invalid_price',iid,it.get('price'))

    # 6) Numeric item descriptions must equal post-generator runtime values.
    numeric_claims=0
    stat_patterns={
        'strength':r'Siła','dexterity':r'Zręczność','constitution':r'Kondycja',
        'intelligence':r'Inteligencja','willpower':r'Siła Woli','charisma':r'Charyzma'
    }
    for iid,it in ITEMS.items():
        desc=str(it.get('desc') or '')
        m=re.search(r'(?i)Obrona\s*\+\s*(-?\d+(?:[.,]\d+)?)',desc)
        if m:
            numeric_claims+=1
            stated=float(m.group(1).replace(',','.')); actual=float(it.get('defense',0) or 0)
            if abs(stated-actual)>1e-6: err('stale_item_defense_desc',iid,stated,actual)
        stats=dict(it.get('stats') or {}); affix=str(it.get('affix') or ''); affix_amount=it.get('affix_amount')
        for key,label in stat_patterns.items():
            for m in re.finditer(rf'(?i){label}\s*\+\s*(-?\d+(?:[.,]\d+)?)',desc):
                actual=stats.get(key)
                if actual is None and affix==key: actual=affix_amount
                if actual is None: continue
                numeric_claims+=1
                stated=float(m.group(1).replace(',','.'))
                if abs(stated-float(actual))>1e-6: err('stale_item_stat_desc',iid,key,stated,actual)
    metrics['numeric_item_claims_checked']=numeric_claims

    # 7) Mob drops.
    for mid,mob in MOB_TEMPLATES.items():
        if not str(mob.get('name') or '').strip(): err('mob_missing_name',mid)
        drops=mob.get('drops') or mob.get('loot') or {}
        if isinstance(drops,dict): iterable=drops.keys()
        else: iterable=drops
        for entry in iterable:
            iid=(entry.get('item') or entry.get('id')) if isinstance(entry,dict) else entry
            if iid and iid not in ITEMS: err('mob_missing_drop_item',mid,iid)

    # 8) Recipes across every recipe registry.
    recipe_tables={
        'craft':CRAFT_RECIPES,'cook':COOK_RECIPES,'alchemy':ALCHEMY_RECIPES,
        'jewelcraft':JEWELCRAFT_RECIPES,'profession':V03053_CRAFT_RECIPES,
    }
    if 'TECH_CRAFT_RECIPES' in globals(): recipe_tables['tech']=TECH_CRAFT_RECIPES
    for table_name,table in recipe_tables.items():
        for rid,recipe in table.items():
            for iid,qty in (recipe.get('ingredients') or {}).items():
                if iid not in ITEMS: err('recipe_missing_ingredient',table_name,rid,iid)
                try:
                    if int(qty)<=0: err('recipe_bad_quantity',table_name,rid,iid,qty)
                except Exception: err('recipe_bad_quantity',table_name,rid,iid,qty)
            output=recipe.get('output')
            if output and output not in ITEMS: err('recipe_missing_output',table_name,rid,output)
    metrics['recipes_total']=sum(len(x) for x in recipe_tables.values())

    # 9) Quests: definitions, items, rewards and supported kinds.
    supported_kinds={
        'collect','collect_category','collect_distinct_category','collect_resource',
        'collect_resource_set','kill','deliver_npc','talk_class_teacher','craft_set',
        'explore_frontier','discover_secret','mini_dungeon','world_event',
        'legendary_rare','world_boss'
    }
    quest_kinds=set()
    for qid,q in QUESTS.items():
        if not str(q.get('name') or '').strip(): err('quest_missing_name',qid)
        kind=q.get('kind'); quest_kinds.add(kind)
        if kind not in supported_kinds: err('unsupported_quest_kind',qid,kind)
        try:
            if int(q.get('needed',1) or 0) < 0: err('quest_bad_needed',qid,q.get('needed'))
        except Exception: err('quest_bad_needed',qid,q.get('needed'))
        for field in ('item','item_id','required_item'):
            iid=q.get(field)
            if iid and isinstance(iid,str) and iid not in ITEMS: err('quest_missing_item',qid,field,iid)
        for field in ('accept_items','reward_items','required_items'):
            values=q.get(field) or {}
            if isinstance(values,dict):
                for iid,qty in values.items():
                    if iid not in ITEMS: err('quest_missing_item',qid,field,iid)
                    try:
                        if int(qty)<=0: err('quest_bad_item_qty',qid,field,iid,qty)
                    except Exception: err('quest_bad_item_qty',qid,field,iid,qty)
        if kind=='craft_set':
            req=q.get('craft_requirements') or q.get('requirements') or {}
            for iid,qty in req.items():
                if iid not in ITEMS: err('craft_set_missing_item',qid,iid)
                try:
                    if int(qty)<=0: err('craft_set_bad_qty',qid,iid,qty)
                except Exception: err('craft_set_bad_qty',qid,iid,qty)
    metrics['quest_kinds']=tuple(sorted(str(x) for x in quest_kinds))

    # 9b) Collections, museum, sets, boss codex and achievements.
    if 'COLLECTION_V2_SET_GROUPS' in globals():
        for group_id,item_ids in COLLECTION_V2_SET_GROUPS.items():
            for iid in item_ids:
                if iid not in ITEMS: err('collection_set_missing_item',group_id,iid)
    if 'V0260_SET_PIECE_GROUPS' in globals():
        for group_id,slots in V0260_SET_PIECE_GROUPS.items():
            for slot,item_ids in slots.items():
                for iid in item_ids:
                    if iid not in ITEMS: err('museum_set_missing_item',group_id,slot,iid)
    if 'LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER' in globals():
        for cname,tiers in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER.items():
            if cname not in CLASS_SKILLS: err('legendary_set_missing_class',cname)
            for tier,item_ids in tiers.items():
                for iid in item_ids:
                    if iid not in ITEMS: err('legendary_set_missing_item',cname,tier,iid)
    for table_name in ('V017_BIOME_SET_ITEMS','V021_MYTHIC_SET_ITEMS'):
        table=globals().get(table_name,{})
        for group_id,item_ids in table.items():
            for iid in item_ids:
                if iid not in ITEMS: err('set_missing_item',table_name,group_id,iid)
    if 'NAMED_LOOT_CATALOG' in globals():
        for iid in NAMED_LOOT_CATALOG:
            if iid not in ITEMS: err('named_loot_missing_item',iid)
    if 'WORLD_BOSS_UNIQUES' in globals():
        for iid in WORLD_BOSS_UNIQUES:
            if iid not in ITEMS: err('world_unique_missing_item',iid)
    if 'BOSS_COLLECTION_CATALOG' in globals():
        for mid in BOSS_COLLECTION_CATALOG:
            if mid not in MOB_TEMPLATES: err('boss_catalog_missing_mob',mid)
    if 'REGION_COLLECTION_ENTRIES' in globals():
        for region,entry in REGION_COLLECTION_ENTRIES.items():
            for mid in entry.get('bosses',()):
                if mid not in MOB_TEMPLATES: err('region_collection_missing_boss',region,mid)
    if 'CLASS_EQUIPMENT_SETS' in globals():
        for cname,spec in CLASS_EQUIPMENT_SETS.items():
            if cname not in CLASS_SKILLS: err('class_set_unknown_class',cname)
            room=spec.get('room')
            if room and room not in ROOMS: err('class_set_missing_room',cname,room)
    if 'ACHIEVEMENT_TITLE_REWARDS' in globals() and 'ACHIEVEMENT_TRACKS' in globals():
        for (track,tier),title in ACHIEVEMENT_TITLE_REWARDS.items():
            if track not in ACHIEVEMENT_TRACKS:
                err('achievement_title_missing_track',track,tier,title); continue
            valid_tiers={x[1] for x in ACHIEVEMENT_TRACKS[track].get('tiers',())}
            if tier not in valid_tiers: err('achievement_title_missing_tier',track,tier,title)

    # 9c) Professions, tools and progression tables.
    if len(PROFESSION_RANK_NAMES)!=12: err('profession_count',len(PROFESSION_RANK_NAMES))
    if len(TOOL_TIER_THRESHOLDS)!=TOOL_MAX_TIER or TOOL_MAX_TIER!=60: err('tool_tier_count',len(TOOL_TIER_THRESHOLDS))

    # 9d) Deep quest target/dependency validation for every quest.
    valid_kill_targets=set(MOB_TEMPLATES)
    for _mid,_mob in MOB_TEMPLATES.items():
        for _field in ('quest_target','quest_targets'):
            _value=_mob.get(_field)
            if isinstance(_value,str): valid_kill_targets.add(_value)
            elif isinstance(_value,(list,tuple,set)): valid_kill_targets.update(map(str,_value))
    valid_collect_categories={'fish','fish_river','ore','wood','herb'}
    npc_display_names={str(_npc.get('name') or '').casefold() for _npc in NPCS.values()}
    for qid,q in QUESTS.items():
        kind=q.get('kind'); target=q.get('target')
        if kind in ('collect','collect_resource') and target not in ITEMS:
            err('quest_bad_target_item',qid,target)
        if kind in ('collect_category','collect_distinct_category') and target not in valid_collect_categories:
            err('quest_bad_category',qid,target)
        if kind=='kill' and target not in valid_kill_targets:
            dynamic_ok=False
            if isinstance(target,str) and target.startswith('crypt_boss_'):
                try:
                    floor=int(target.rsplit('_',1)[1])
                    dynamic_ok=210<=floor<=SOUL_MAX_LEVEL and floor%10==0
                except Exception:
                    dynamic_ok=False
            if not dynamic_ok: err('quest_bad_kill_target',qid,target)
        if kind=='deliver_npc' and q.get('target_npc') not in NPCS:
            err('quest_bad_target_npc',qid,q.get('target_npc'))
        if q.get('quest_item') and q.get('quest_item') not in ITEMS:
            err('quest_bad_quest_item',qid,q.get('quest_item'))
        if q.get('requires_quest') and q.get('requires_quest') not in QUESTS:
            err('quest_bad_prerequisite',qid,q.get('requires_quest'))
        if q.get('required_profession') and q.get('required_profession') not in PROFESSION_RANK_NAMES:
            err('quest_bad_required_profession',qid,q.get('required_profession'))
        if q.get('reward_profession') and q.get('reward_profession') not in PROFESSION_RANK_NAMES:
            err('quest_bad_reward_profession',qid,q.get('reward_profession'))
        if q.get('reward_faction_v016') and q.get('reward_faction_v016') not in V016_FACTIONS:
            err('quest_bad_faction',qid,q.get('reward_faction_v016'))
        if q.get('repeatable') and int(q.get('repeat_cooldown',0) or 0)<=0:
            err('quest_bad_repeat_cooldown',qid,q.get('repeat_cooldown'))
        if kind=='collect_resource_set':
            req=dict(q.get('resource_targets') or {})
            if sum(int(v) for v in req.values()) != int(q.get('needed',0) or 0):
                err('quest_resource_set_needed_mismatch',qid,q.get('needed'),req)
            for iid,qty in req.items():
                if iid not in ITEMS: err('quest_resource_set_missing_item',qid,iid)
                if int(qty)<=0: err('quest_resource_set_bad_qty',qid,iid,qty)
        if kind=='craft_set':
            targets=tuple(q.get('targets') or ())
            if len(targets) != int(q.get('needed',0) or 0):
                err('quest_craft_set_needed_mismatch',qid,q.get('needed'),len(targets))
            for iid in targets:
                if iid not in ITEMS: err('quest_craft_set_missing_item',qid,iid)
        giver=str(q.get('giver') or '').strip()
        if giver and giver.casefold() not in npc_display_names and giver!='Tablica Godzinnych Zleceń':
            err('quest_unknown_giver',qid,giver)

    # Prerequisite graph must be acyclic.
    _visited=set(); _stack=set()
    def _visit_quest_dep_v0336(qid):
        if qid in _stack:
            err('quest_prerequisite_cycle',qid); return
        if qid in _visited: return
        _visited.add(qid); _stack.add(qid)
        dep=QUESTS[qid].get('requires_quest')
        if dep in QUESTS: _visit_quest_dep_v0336(dep)
        _stack.remove(qid)
    for _qid in QUESTS: _visit_quest_dep_v0336(_qid)

    # 9e) v0.34.1 Blacksmithing NPC resale must not multiply raw ore value.
    _smith_rows_checked=0
    try:
        _smith_dummy=object.__new__(Session)
        for _tier in BLACKSMITH_TIERS:
            _ore=ITEMS.get(str(_tier.get('ore')), {})
            _ore_value=legacy_currency_to_coins(
                _ore.get('sell_silver',0), _ore.get('sell_gold',0), _ore.get('sell_mithril',0)
            )
            if _ore_value<=0:
                err('blacksmith_ore_without_sale_value',_tier.get('key'),_tier.get('ore')); continue
            for _slot,_slot_row in BLACKSMITH_SLOT_DEFS.items():
                _iid=f"smith_{_tier['key']}_{_slot}"
                _item=ITEMS.get(_iid)
                if not _item:
                    err('blacksmith_missing_crafted_item',_iid); continue
                _cost=max(1,int(_slot_row[2] or 1))
                _material_value=_ore_value*_cost
                _sale=Session.generic_item_sale_value(_smith_dummy,_iid,_item)
                _sale_value=legacy_currency_to_coins(_sale.get('silver',0),_sale.get('gold',0),_sale.get('mithril',0))
                _max_normal=int(_material_value*0.90)
                if _sale_value>_max_normal:
                    err('blacksmith_normal_resale_too_high',_iid,_sale_value,_max_normal,_material_value)
                _smith_rows_checked+=1
    except Exception as _exc:
        err('blacksmith_economy_audit_exception',repr(_exc))
    metrics['blacksmith_resale_rows_checked']=_smith_rows_checked

    # 9f) v0.34.4 Currency economy + Mithril mining gate.
    # One wallet uses silver as the canonical unit; gold/mithril are display denominations.
    if int(SILVER_PER_GOLD) != 100:
        err('currency_ratio_silver_gold',SILVER_PER_GOLD,100)
    if int(GOLD_PER_MITHRIL) != 1000:
        err('currency_ratio_gold_mithril',GOLD_PER_MITHRIL,1000)
    if int(SILVER_PER_MITHRIL) != 100000:
        err('currency_ratio_silver_mithril',SILVER_PER_MITHRIL,100000)

    _mob_split=0; _quest_split=0
    _max_mob_currency=0; _max_quest_currency=0; _repeatable_count=0; _max_repeatable=0
    for _mid,_mob in MOB_TEMPLATES.items():
        _silver=int(_mob.get('silver',0) or 0)
        _max_mob_currency=max(_max_mob_currency,_silver)
        if int(_mob.get('gold',0) or 0) or int(_mob.get('mithril',0) or 0):
            _mob_split+=1; err('mob_split_currency_not_normalized',_mid,_mob.get('gold'),_mob.get('mithril'))
    for _qid,_q in QUESTS.items():
        _coins=int(_q.get('reward_silver',0) or 0)
        _max_quest_currency=max(_max_quest_currency,_coins)
        if bool(_q.get('repeatable')) or int(_q.get('cooldown_seconds',0) or 0)>0:
            _repeatable_count+=1; _max_repeatable=max(_max_repeatable,_coins)
        if int(_q.get('reward_gold',0) or 0) or int(_q.get('reward_mithril',0) or 0):
            _quest_split+=1; err('quest_split_currency_not_normalized',_qid,_q.get('reward_gold'),_q.get('reward_mithril'))
    metrics['currency_mob_split_count']=_mob_split
    metrics['currency_quest_split_count']=_quest_split
    metrics['currency_max_mob_reward']=_max_mob_currency
    metrics['currency_max_quest_reward']=_max_quest_currency
    metrics['currency_repeatable_quests']=_repeatable_count
    metrics['currency_max_repeatable_quest_reward']=_max_repeatable

    # Real shop offers only, with the maximum Charisma cashback applied: no buy -> sell profit loop.
    _shop_ids=set()
    for _offers in SHOPS.values():
        _shop_ids.update(_offers or ())
    for _offers in CLASS_SHOP_ITEMS_BY_ROOM.values():
        _shop_ids.update(_offers or ())
    _shop_arbitrage=[]
    try:
        _economy_dummy=object.__new__(Session)
        _max_discount=max(0,min(100,int(CHARISMA_MAX_DISCOUNT or 0)))
        for _iid in sorted(_shop_ids):
            _item=ITEMS.get(_iid)
            if not _item:
                continue
            _buy=int(Session.shop_item_base_value_silver(_economy_dummy,_item) or 0)
            if _buy<=0:
                continue
            _effective_buy=max(0,_buy-((_buy*_max_discount)//100))
            _sale=Session.generic_item_sale_value(_economy_dummy,_iid,_item)
            _sell=legacy_currency_to_coins(
                _sale.get('silver',0),_sale.get('gold',0),_sale.get('mithril',0)
            )
            if _sell>_effective_buy:
                _shop_arbitrage.append((_iid,_effective_buy,_sell))
                err('shop_buy_sell_arbitrage',_iid,_effective_buy,_sell,_max_discount)
    except Exception as _exc:
        err('currency_shop_audit_exception',repr(_exc))
    metrics['currency_shop_items_checked']=len(_shop_ids)
    metrics['currency_shop_arbitrage_count']=len(_shop_arbitrage)
    metrics['currency_max_charisma_discount']=int(CHARISMA_MAX_DISCOUNT or 0)

    _max_explicit_sell=0
    for _iid,_item in ITEMS.items():
        _value=legacy_currency_to_coins(
            _item.get('sell_silver',0),_item.get('sell_gold',0),_item.get('sell_mithril',0)
        )
        _max_explicit_sell=max(_max_explicit_sell,int(_value or 0))
    metrics['currency_max_explicit_item_sell']=_max_explicit_sell

    # v0.34.4: Mithril is a currency bonus from mining, never an ore resource.
    if 'mithril_ore' in ORE_RESOURCE_IDS:
        err('mithril_ore_must_not_be_active_resource')
    if 'mithril_ore' in ORE_ATLAS_ALL:
        err('mithril_ore_must_not_be_in_atlas')
    if 'mithril_ore' in ORE_ATLAS_LEVELS or 'mithril_ore' in ORE_MINE_FLOOR_MINIMUMS:
        err('mithril_ore_must_not_have_unlock_threshold')
    _mithril_chance_79=mining_mithril_currency_chance(79,79,79)
    _mithril_chance_80=mining_mithril_currency_chance(80,80,80)
    _mithril_chance_400=mining_mithril_currency_chance(400,400,400)
    _mithril_chance_600=mining_mithril_currency_chance(600,600,600)
    if _mithril_chance_79 != 0:
        err('mithril_currency_unlock_too_early',_mithril_chance_79)
    if not (0.0049 <= _mithril_chance_80 <= 0.0051):
        err('mithril_currency_level80_chance',_mithril_chance_80)
    if not (0.0199 <= _mithril_chance_600 <= 0.0201):
        err('mithril_currency_level600_chance',_mithril_chance_600)
    metrics['mithril_currency_chance_level80']=_mithril_chance_80
    metrics['mithril_currency_chance_level400']=_mithril_chance_400
    metrics['mithril_currency_chance_level600']=_mithril_chance_600

    # Audit authored ore weighting: newly unlocked core ores must be meaningfully
    # visible, while older ores remain possible.
    _ore_drop_checks=(
        (50,'gold_ore'),(100,'cobalt_ore'),(120,'runestone_ore'),
        (140,'dragonsteel_ore'),(160,'astral_ore'),(180,'void_ore'),
        (200,'eternium_ore'),(220,'ore_400_220'),(400,'ore_400_400'),
    )
    _ore_drop_metrics={}
    for _level,_ore_id in _ore_drop_checks:
        _pool=[]
        for _iid in ORE_RESOURCE_IDS:
            if _iid not in ITEMS:
                continue
            if int(ORE_ATLAS_LEVELS.get(_iid,1) or 1) <= _level and int(ORE_MINE_FLOOR_MINIMUMS.get(_iid,1) or 1) <= _level:
                _pool.append(_iid)
        _weights=mining_ore_weights(_pool,_level,f'audit:mine_floor_{_level}')
        _total=sum(_weights) or 1.0
        _prob=0.0
        if _ore_id in _pool:
            _prob=float(_weights[_pool.index(_ore_id)])/_total
        _ore_drop_metrics[_ore_id]=round(_prob,6)
        if _prob < 0.08:
            err('current_tier_ore_too_rare',_level,_ore_id,_prob)
    metrics['mining_current_ore_probabilities']=_ore_drop_metrics
    try:
        metrics['currency_guild_upgrade_1_400']=sum(int(v0926_guild_upgrade_cost(_lvl) or 0) for _lvl in range(1,V0926_GUILD_MAX_LEVEL))
    except Exception as _exc:
        warnings.append(('guild_currency_sink_metric_unavailable',repr(_exc)))

    # 10) Skills/spells: no duplicate display names, no numeric disambiguators.
    seen_skill_names={}; skill_count=0
    for cname,rows in CLASS_SKILLS.items():
        for skill in rows:
            skill_count+=1
            name=str(skill.get('name') or '').strip()
            if not name: err('skill_missing_name',cname,skill.get('id'))
            key=normalize_lookup_text(name)
            seen_skill_names.setdefault(key,[]).append((cname,skill.get('id'),name))
            if re.search(r'\d',name): err('skill_numeric_name',cname,skill.get('id'),name)
            try:
                unlock=int(skill.get('unlock',0) or 0)
                if not 1<=unlock<=CLASS_MASTERY_MAX_LEVEL: err('skill_bad_unlock',cname,skill.get('id'),unlock)
            except Exception: err('skill_bad_unlock',cname,skill.get('id'),skill.get('unlock'))
    for key,rows in seen_skill_names.items():
        if len(rows)>1: err('duplicate_skill_name',key,rows)
    metrics['skills_total']=skill_count

    # v0.35.3: Hunter/combat regression gate. Offensive Hunter skills must keep
    # their authored Dexterity scaling, and Soul Weapon trait_totals must never
    # leak into use_class_skill (traits belong only to the basic weapon attack).
    _hunter_rows=list(CLASS_SKILLS.get('Łowca') or [])
    _hunter_supported={'damage','drain','execute','aoe_damage','heal','group_heal','guard','evade','boost','passive'}
    _hunter_aliases={}
    _hunter_alias_collisions=[]
    for _skill in _hunter_rows:
        _sid=str(_skill.get('id') or '')
        _kind=str(_skill.get('kind') or '')
        if _kind not in _hunter_supported:
            err('hunter_unsupported_kind',_sid,_kind)
        if _kind in {'damage','drain','execute','aoe_damage'}:
            if _skill.get('scale') != 'dexterity':
                err('hunter_bad_scale',_sid,_skill.get('scale'))
            for _field in ('scale','mult'):
                if _field not in _skill:
                    err('hunter_missing_field',_sid,_field)
        if _kind == 'execute' and 'execute_mult' not in _skill:
            err('hunter_missing_field',_sid,'execute_mult')
        if _kind == 'boost' and 'boost' not in _skill:
            err('hunter_missing_field',_sid,'boost')
        for _form in [str(_skill.get('name') or '')] + list(_skill.get('aliases') or []):
            _norm=normalize_lookup_text(_form)
            if not _norm:
                continue
            _prev=_hunter_aliases.get(_norm)
            if _prev and _prev != _sid:
                _hunter_alias_collisions.append((_form,_prev,_sid))
            else:
                _hunter_aliases[_norm]=_sid
    for _row in _hunter_alias_collisions:
        err('hunter_alias_collision',*_row)
    metrics['hunter_skills_checked']=len(_hunter_rows)
    metrics['hunter_alias_collisions']=len(_hunter_alias_collisions)
    try:
        _combat_source=(_ROOT/'player/session_mixins/skills_combat.py').read_text(encoding='utf-8')
        _use_start=_combat_source.index('    async def use_class_skill(')
        _use_end=_combat_source.index('    async def stop_realtime_combat(',_use_start)
        _use_body=_combat_source[_use_start:_use_end]
        if 'trait_totals' in _use_body:
            err('soul_weapon_trait_leak_into_skills')
    except Exception as _exc:
        err('combat_skill_source_audit_failed',repr(_exc))

    # 10b) v0.35.3 Soul Weapon Mastery + Main Menu Exit gate.
    try:
        if int(SOUL_WEAPON_MASTERY_MAX_LEVEL) != 600:
            err('soul_weapon_mastery_bad_cap',SOUL_WEAPON_MASTERY_MAX_LEVEL)
        _m1=soul_weapon_mastery_bonuses(1)
        _m200=soul_weapon_mastery_bonuses(200)
        _m400=soul_weapon_mastery_bonuses(400)
        _m600=soul_weapon_mastery_bonuses(600)
        if any(float(_m1.get(k,0) or 0) != 0.0 for k in ('damage_percent','crit_chance','crit_damage_percent','boss_damage_percent','echo_chance')):
            err('soul_weapon_mastery_level1_not_neutral',_m1)
        if not (0.0099 <= float(_m200.get('echo_chance',0) or 0) <= 0.0101):
            err('soul_weapon_mastery_echo_200',_m200.get('echo_chance'))
        if abs(float(_m600.get('damage_percent',0))-8.0)>0.0001:
            err('soul_weapon_mastery_damage_600',_m600.get('damage_percent'))
        if abs(float(_m600.get('crit_chance',0))-0.02)>0.000001:
            err('soul_weapon_mastery_crit_600',_m600.get('crit_chance'))
        if abs(float(_m600.get('crit_damage_percent',0))-12.0)>0.0001:
            err('soul_weapon_mastery_crit_damage_600',_m600.get('crit_damage_percent'))
        if abs(float(_m600.get('boss_damage_percent',0))-5.0)>0.0001:
            err('soul_weapon_mastery_boss_600',_m600.get('boss_damage_percent'))
        if abs(float(_m600.get('echo_chance',0))-0.05)>0.000001:
            err('soul_weapon_mastery_echo_600',_m600.get('echo_chance'))
        _combat_source=(_ROOT/'player/session_mixins/skills_combat.py').read_text(encoding='utf-8')
        _basic_start=_combat_source.index('    async def realtime_player_action(')
        _loop_start=_combat_source.index('    async def realtime_combat_loop(',_basic_start)
        _basic_body=_combat_source[_basic_start:_loop_start]
        if 'grant_soul_weapon_mastery_hit_xp' not in _basic_body:
            err('soul_weapon_mastery_missing_basic_attack_xp')
        _use_start=_combat_source.index('    async def use_class_skill(')
        _use_end=_combat_source.index('    async def stop_realtime_combat(',_use_start)
        _use_body=_combat_source[_use_start:_use_end]
        if 'grant_soul_weapon_mastery_hit_xp' in _use_body or 'soul_weapon_mastery_bonuses' in _use_body:
            err('soul_weapon_mastery_leaked_into_skills')
        _auth_source=(_ROOT/'player/session_mixins/io_auth_character.py').read_text(encoding='utf-8')
        if 'await self.close_from_main_menu()' not in _auth_source or 'self.writer.close()' not in _auth_source:
            err('main_menu_exit_not_explicit_close')
        _db_source=(_ROOT/'storage/database.py').read_text(encoding='utf-8')
        for _column in ('soul_weapon_mastery_level','soul_weapon_mastery_xp'):
            if _column not in _db_source:
                err('soul_weapon_mastery_db_column_missing',_column)
        metrics['soul_weapon_mastery_cap']=int(SOUL_WEAPON_MASTERY_MAX_LEVEL)
        metrics['soul_weapon_mastery_bonus_400']=dict(_m400)
    except Exception as _exc:
        err('soul_weapon_mastery_audit_exception',repr(_exc))

    # 10c) v0.35.3 profession automation / identifier regression gate.
    # The v0.35.0 Polish Pass accidentally changed some Python identifiers
    # from ``level`` to ``poziom`` while leaving references to the other name.
    # That produced NameError inside gathering XP and silently killed auto tasks.
    try:
        import ast as _ast
        _identifier_mismatches=[]
        _functions_checked=0
        for _path in sorted(_ROOT.rglob('*.py')):
            # Ignore generated bytecode/cache trees if a local developer has them.
            if '__pycache__' in _path.parts:
                continue
            try:
                _tree=_ast.parse(_path.read_text(encoding='utf-8'), filename=str(_path))
            except Exception as _exc:
                err('python_source_parse_failed',str(_path.relative_to(_ROOT)),repr(_exc))
                continue
            for _node in _ast.walk(_tree):
                if not isinstance(_node,(_ast.FunctionDef,_ast.AsyncFunctionDef)):
                    continue
                _functions_checked += 1
                _params={_a.arg for _a in list(_node.args.args)+list(_node.args.kwonlyargs)}
                _stores=set(_params)
                _loads=set()
                for _child in _ast.walk(_node):
                    if isinstance(_child,_ast.Name):
                        if isinstance(_child.ctx,(_ast.Store,_ast.Param)):
                            _stores.add(_child.id)
                        elif isinstance(_child.ctx,_ast.Load):
                            _loads.add(_child.id)
                if 'level' in _stores and 'poziom' in _loads and 'poziom' not in _stores:
                    _identifier_mismatches.append((str(_path.relative_to(_ROOT)),_node.name,'local_level_load_poziom'))
                if 'poziom' in _stores and 'level' in _loads and 'level' not in _stores:
                    _identifier_mismatches.append((str(_path.relative_to(_ROOT)),_node.name,'local_poziom_load_level'))
        for _row in _identifier_mismatches:
            err('level_poziom_identifier_mismatch',*_row)
        metrics['python_functions_identifier_checked']=_functions_checked
        metrics['level_poziom_identifier_mismatches']=len(_identifier_mismatches)

        _prof_source=(_ROOT/'player/session_mixins/professions_storage_guide.py').read_text(encoding='utf-8')
        _auto_specs=(
            ('auto_fishing_loop','set_auto_fishing','AUTO_FISHING_ERROR'),
            ('auto_mining_loop','set_auto_mining','AUTO_MINING_ERROR'),
            ('auto_woodcutting_loop','set_auto_woodcutting','AUTO_WOODCUTTING_ERROR'),
            ('auto_herbalism_loop','set_auto_herbalism','AUTO_HERBALISM_ERROR'),
        )
        for _fn,_next_fn,_tag in _auto_specs:
            _start=_prof_source.find(f'    async def {_fn}(')
            _end=_prof_source.find(f'    async def {_next_fn}(',_start+1)
            if _start < 0 or _end < 0:
                err('auto_profession_loop_missing',_fn)
                continue
            _body=_prof_source[_start:_end]
            if 'except Exception as exc:' not in _body or _tag not in _body:
                err('auto_profession_loop_silent_failure_guard_missing',_fn)
        metrics['auto_profession_loops_guarded']=len(_auto_specs)
    except Exception as _exc:
        err('profession_automation_regression_audit_exception',repr(_exc))

    # 11) HELP aliases and nonempty topics.
    virtual={'tematy','komendy','wszystko','kategorie'}
    for alias,target in HELP_TOPIC_ALIASES.items():
        if target not in HELP_TOPICS and target not in virtual: err('help_alias_missing_target',alias,target)
    for topic,lines in HELP_TOPICS.items():
        if not lines: err('empty_help_topic',topic)

    # 11b) v0.35.3 polish regression gate: keep internal release labels and
    # stale caps out of normal player-facing runtime text.
    try:
        _polish_files=(
            'player/session_mixins/quests.py',
            'player/session_mixins/progression_accessibility_v03052.py',
            'player/session_mixins/milestone_v0320.py',
            'player/session_mixins/crafting_inventory_equipment.py',
            'player/session_mixins/crafting_expansion_v03114.py',
            'player/session_mixins/tech_crafting_v03111.py',
            'player/session_mixins/world_progression.py',
            'player/session_mixins/social_expansion.py',
            'player/session_mixins/admin_gathering_sales.py',
            'player/session_mixins/forge_guilds.py',
            'systems/content_registry.py',
        )
        _polish_source='\n'.join((_ROOT/_rel).read_text(encoding='utf-8') for _rel in _polish_files)
        _forbidden_ui=(
            'QUEST LIST:', 'QUEST INFO:', 'AKTYWNE QUESTY:', 'UKOŃCZONE QUESTY:',
            'COLLECTION CODEX 2.0', 'LOOT HISTORY 2.0', 'DEATH RECAP:',
            'COMBAT RECAP:', 'PARTY QUEST PROGRESS 2.0', 'SALVAGE 3.0:',
            'REFINING 2.0', 'MACHINE SALVAGE 2.0', 'FISHING RECORDS 2.0',
            'DYNAMICZNE EVENTY v0.29', 'MITYCZNA PROGRESJA v0.21',
            'COLLECTION CODEX — ŚWIAT v0.15',
            'poziomy Gildii 1-100', 'maksymalnie +11% do Biegłości',
        )
        for _token in _forbidden_ui:
            if _token in _polish_source:
                err('stale_player_ui_token',_token)
        metrics['polish_ui_tokens_checked']=len(_forbidden_ui)
    except Exception as _exc:
        err('polish_source_audit_failed',repr(_exc))

    # 12) Static code-integrity gate for assembled runtime.
    # Check method references across every Session mixin, plus the main runtime
    # collaborators used through self.server/db/world/character. This catches
    # rare-path typos that normal startup cannot execute (e.g. a single Mec proc
    # or an admin-only command).
    try:
        import ast as _ast_code
        _session_called=set()
        _db_called=set()
        _world_called=set()
        _server_called=set()
        _character_called=set()
        _session_files=list((_ROOT/'player/session_mixins').glob('*.py'))+[(_ROOT/'player/session.py')]
        for _path in _session_files:
            _tree=_ast_code.parse(_path.read_text(encoding='utf-8'), filename=str(_path))
            for _node in _ast_code.walk(_tree):
                if not isinstance(_node,_ast_code.Call) or not isinstance(_node.func,_ast_code.Attribute):
                    continue
                _attr=_node.func.attr
                _value=_node.func.value
                if isinstance(_value,_ast_code.Name) and _value.id=='self':
                    _session_called.add(_attr)
                    continue
                # self.character.foo(...)
                if (isinstance(_value,_ast_code.Attribute) and _value.attr=='character'
                        and isinstance(_value.value,_ast_code.Name) and _value.value.id=='self'):
                    _character_called.add(_attr); continue
                # self.server.foo(...)
                if (isinstance(_value,_ast_code.Attribute) and _value.attr=='server'
                        and isinstance(_value.value,_ast_code.Name) and _value.value.id=='self'):
                    _server_called.add(_attr); continue
                # self.server.db.foo(...) / self.server.world.foo(...)
                if isinstance(_value,_ast_code.Attribute) and _value.attr in ('db','world'):
                    _base=_value.value
                    if (isinstance(_base,_ast_code.Attribute) and _base.attr=='server'
                            and isinstance(_base.value,_ast_code.Name) and _base.value.id=='self'):
                        (_db_called if _value.attr=='db' else _world_called).add(_attr)
        for _name in sorted(_session_called):
            if not hasattr(Session,_name): err('missing_session_method_reference',_name)
        for _name in sorted(_db_called):
            if not hasattr(Database,_name): err('missing_database_method_reference',_name)
        for _name in sorted(_world_called):
            if not hasattr(World,_name): err('missing_world_method_reference',_name)
        for _name in sorted(_server_called):
            if not hasattr(MudServer,_name): err('missing_server_method_reference',_name)
        for _name in sorted(_character_called):
            if not hasattr(Character,_name): err('missing_character_method_reference',_name)
        metrics['session_methods_called_checked']=len(_session_called)
        metrics['database_methods_called_checked']=len(_db_called)
        metrics['world_methods_called_checked']=len(_world_called)
        metrics['server_methods_called_checked']=len(_server_called)
        metrics['character_methods_called_checked']=len(_character_called)

        # MRO regression gate: newer extensions must remain the active methods,
        # while they can explicitly delegate to their older compatibility layer.
        _expected_owners={
            'salvage_equipment_v0925':SessionCraftingExpansionV03114Mixin,
            'tell':SessionSocialExpansionMixin,
            'who':SessionSocialExpansionMixin,
            'channel_broadcast_v03050':SessionSocialExpansionMixin,
            'show_channels_v03050':SessionSocialExpansionMixin,
        }
        for _name,_owner in _expected_owners.items():
            _resolved=getattr(Session,_name,None)
            _expected=getattr(_owner,_name,None)
            if _resolved is not _expected:
                err('session_mro_shadowing_regression',_name,getattr(_resolved,'__qualname__',None),getattr(_expected,'__qualname__',None))
        metrics['mro_resolution_checks']=len(_expected_owners)

        # Long-lived background loops must survive an unexpected iteration error.
        _server_source=(_ROOT/'server/mud_server.py').read_text(encoding='utf-8')
        for _fn,_tag in (('double_xp_event_loop','DOUBLE XP LOOP ERROR'),('mob_wander_loop','MOB WANDER LOOP ERROR')):
            _start=_server_source.find(f'    async def {_fn}(')
            _next=_server_source.find('    async def ',_start+1)
            _body=_server_source[_start:(_next if _next>_start else len(_server_source))]
            if 'except Exception as exc:' not in _body or _tag not in _body:
                err('background_loop_guard_missing',_fn)
        _core_source=(_ROOT/'player/session_mixins/core_progression.py').read_text(encoding='utf-8')
        _start=_core_source.find('    async def rest_loop(')
        _next=_core_source.find('    async def ',_start+1)
        _body=_core_source[_start:(_next if _next>_start else len(_core_source))]
        if 'except Exception as exc:' not in _body or 'REST_LOOP_ERROR' not in _body:
            err('background_loop_guard_missing','rest_loop')
        metrics['background_loop_guards_checked']=3
    except Exception as _exc:
        err('code_integrity_gate_exception',repr(_exc))

    return {
        'version':'0.35.6','error_count':len(errors),'warning_count':len(warnings),
        'errors':errors,'warnings':warnings,'metrics':metrics,
        'description_sync':dict(ITEM_DESCRIPTION_SYNC_V0336),
    }

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
        _core_path = _ROOT / "player/session_mixins/core_progression.py"
        _combat_path = _ROOT / "player/session_mixins/skills_combat.py"
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
if PARTY_TEMPLE_SHARD_AUDIT_V0355.get("error_count"):
    raise RuntimeError(
        "Party Temple/Shard Audit v0.35.5 failed: "
        + "; ".join(PARTY_TEMPLE_SHARD_AUDIT_V0355.get("errors", [])[:20])
    )

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
        metrics["protects_equipped"] = 'free_equipment_quantity' in bulk and 'equipped_quantity_of_item' in bulk
        metrics["protects_moogle"] = 'moogle_board' in bulk
        metrics["extended_salvage"] = 'SALVAGE3_V03114' in bulk
        metrics["aggregated_output"] = 'SALVAGE WSZYSTKO' in bulk
        for key,value in metrics.items():
            if not value: errors.append(f"salvage wszystko audit failed: {key}")
    except Exception as exc:
        errors.append(f"salvage wszystko audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.6","error_count":len(errors),"errors":errors,"metrics":metrics}

SALVAGE_ALL_AUDIT_V0356 = salvage_all_audit_v0356()
if SALVAGE_ALL_AUDIT_V0356["error_count"]:
    raise RuntimeError("Salvage Wszystko Audit v0.35.6 failed: " + "; ".join(SALVAGE_ALL_AUDIT_V0356["errors"]))

LATEST_CHANGES_TITLE = "Soulbound v0.35.6 - Salvage Wszystko"
LATEST_CHANGES = [
    "v0.35.6: dodano salvage wszystko / rozloz wszystko — hurtowe rozkładanie wszystkich wolnych przedmiotów obsługiwanych przez Salvage.",
    "Założone EQ jest zawsze pomijane; startowy Moogle Board jest chroniony przed przypadkowym hurtowym rozłożeniem.",
    "Hurtowy Salvage agreguje raport odzyskanych materiałów, run i klejnotów, żeby nie spamować NVDA setkami komunikatów.",
]


# v0.35.7 - BULK SMELTING + INGOT-BASED SMITHING
def bulk_smelting_ingot_smithing_audit_v0357():
    errors=[]
    metrics={}
    try:
        import inspect
        source=inspect.getsource(SessionCraftingExpansionV03114Mixin.smelt_item_v03114)
        metrics["bulk_single_action"] = "przetopów w jednej akcji" in source and "await asyncio.sleep(action_seconds)" in source
        metrics["pooled_xp"] = "pooled_profession_xp" in source and "pooled_tool_xp" in source
        metrics["includes_direct_ore"] = 'recipe_ids = [tier["ingot"] for tier in BLACKSMITH_TIERS]' in source
        metrics["includes_steel_plates"] = 'recipe_ids.append("recycled_steel_ingot")' in source
        metrics["includes_salvage"] = "SALVAGE_SMELT_FALLBACK_V03113.values()" in source
        for key,value in metrics.items():
            if not value:
                errors.append(f"bulk smelting audit failed: {key}")

        ingot_ids={str(tier.get("ingot")) for tier in BLACKSMITH_TIERS}
        ingot_ids.add("steel_ingot")
        checked=0
        for recipe_id,recipe in CRAFT_RECIPES.items():
            output=ITEMS.get(recipe.get("output"),{})
            if output.get("type") != "armor":
                continue
            category=str(recipe.get("category") or "")
            # Tech equipment has its own component/alloy economy. This gate covers
            # the normal blacksmith equipment line and the historical forge charms.
            if category in ("technology","tech_set"):
                continue
            if "forge" not in tuple(recipe.get("stations") or ()):
                continue
            profession=str(recipe.get("profession") or "Kowalstwo")
            tool_type=str(recipe.get("tool_type") or "crafting")
            if profession != "Kowalstwo" or tool_type != "crafting":
                continue
            checked+=1
            ingredients=set((recipe.get("ingredients") or {}).keys())
            raw_ores=[iid for iid in ingredients if str(iid).endswith("_ore") or str(iid).startswith("ore_")]
            if raw_ores:
                errors.append(f"kowalskie EQ używa surowej rudy {recipe_id}: {raw_ores}")
            if not (ingredients & ingot_ids):
                errors.append(f"kowalskie EQ bez sztabki {recipe_id}: {sorted(ingredients)}")
        metrics["smith_equipment_recipes_checked"] = checked
        if checked < 10:
            errors.append(f"za mało receptur kowalskiego EQ w audicie: {checked}")
    except Exception as exc:
        errors.append(f"bulk smelting/ingot smithing audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.7","error_count":len(errors),"errors":errors,"metrics":metrics}

BULK_SMELTING_INGOT_SMITHING_AUDIT_V0357 = bulk_smelting_ingot_smithing_audit_v0357()
if BULK_SMELTING_INGOT_SMITHING_AUDIT_V0357["error_count"]:
    raise RuntimeError(
        "Bulk Smelting/Ingot Smithing Audit v0.35.7 failed: "
        + "; ".join(BULK_SMELTING_INGOT_SMITHING_AUDIT_V0357["errors"][:30])
    )

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
if NO_PVP_PLAYER_SAFETY_AUDIT_V0358["error_count"]:
    raise RuntimeError(
        "No-PvP Player Safety Audit v0.35.8 failed: "
        + "; ".join(NO_PVP_PLAYER_SAFETY_AUDIT_V0358["errors"][:20])
    )

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
        metrics["helper_returns_all"] = "return list(recipients or [])" in helper_source
        metrics["single_roll"] = "for item_id, chance in template[\"drops\"].items()" in combat_source and "if random.random() <= chance" in combat_source
        metrics["all_drop_types_use_helper"] = "drop_recipients = party_drop_recipients_v0359(item_id, recipients)" in combat_source
        metrics["no_random_winner"] = "random.choice(recipients)" not in helper_source and "winner = drop_recipients[0]" not in combat_source
        metrics["shared_message"] = "każdy obecny członek otrzymuje" in combat_source
        metrics["same_room_reward_set"] = "party_sessions(\n                self.account_id, same_room=self.character.room_id\n            )" in combat_source
        for key,value in metrics.items():
            if not value:
                errors.append(f"all-party drop audit failed: {key}")
    except Exception as exc:
        errors.append(f"all-party drop audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.9","error_count":len(errors),"errors":errors,"metrics":metrics}

ALL_PARTY_MOB_DROPS_SHARED_AUDIT_V0359 = all_party_mob_drops_shared_audit_v0359()
if ALL_PARTY_MOB_DROPS_SHARED_AUDIT_V0359["error_count"]:
    raise RuntimeError(
        "All Party Mob Drops Shared Audit v0.35.9 failed: "
        + "; ".join(ALL_PARTY_MOB_DROPS_SHARED_AUDIT_V0359["errors"][:20])
    )

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
if ALL_PARTY_CORPSE_LOOT_SHARED_AUDIT_V03510["error_count"]:
    raise RuntimeError(
        "All Party Corpse Loot Shared Audit v0.35.10 failed: "
        + "; ".join(ALL_PARTY_CORPSE_LOOT_SHARED_AUDIT_V03510["errors"][:20])
    )

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
        boost_source=inspect.getsource(SessionSkillsCombatMixin.apply_party_boost_v03511)
        vmax_support_source=inspect.getsource(SessionSkillsCombatMixin.party_vmax_support_active_v03511)
        metrics["same_room_party_helper"] = "party_sessions" in helper_source and "same_room=self.character.room_id" in helper_source
        metrics["living_local_only"] = "session.current_hp > 0" in helper_source and "session.character.room_id == self.character.room_id" in helper_source
        metrics["generic_boost_shared"] = "apply_party_boost_v03511" in combat_source and "session.active_skill_buffs" in boost_source
        metrics["guard_shared"] = "for session in recipients:\n                    session.skill_guard" in combat_source
        metrics["evade_shared"] = "for session in recipients:\n                    session.skill_evade = True" in combat_source
        metrics["vmax_shared"] = '"V-MAX", 1.30' in combat_source and "v03511_party_vmax_until" in combat_source
        metrics["vmax_defense_party_support"] = "mec_vmax_active_v0319" in vmax_support_source and "v03511_party_vmax_until" in vmax_support_source
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
if ALL_LOCAL_PARTY_BUFFS_AUDIT_V03511["error_count"]:
    raise RuntimeError(
        "All Local Party Buffs Audit v0.35.11 failed: "
        + "; ".join(ALL_LOCAL_PARTY_BUFFS_AUDIT_V03511["errors"][:30])
    )

HELP_TOPICS.setdefault("party", []).extend([
    "v0.35.11: wszystkie bojowe buffy klasowe działają na wszystkich żywych członków drużyny stojących w tej samej lokacji co rzucający.",
    "Boosty, guardy i gwarantowane uniki są nakładane osobno na każdego obecnego członka drużyny. Osoby w innych lokacjach nie dostają efektu.",
    "V-MAX daje lokalnej drużynie +30 procent do skilli/spelli oraz Protect, Shell i Regen. Specjalne zmiany konkretnych skilli Meca pozostają mechaniką Meca uruchamiającego V-MAX.",
])
HELP_TOPICS.setdefault("druzyna", []).extend(HELP_TOPICS.get("party", [])[-3:])
HELP_TOPICS.setdefault("walka", []).extend([
    "v0.35.11: guard i evade są efektami drużynowymi w bieżącej lokacji, tak samo jak zwykłe boosty.",
    "Inżynierski Upgrade jest trwałym narzędziem użytkowym, nie buffem bojowym; dlatego nie jest kopiowany na drużynę jako status czasowy.",
])
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.35.11: wszystkie prawdziwe buffy bojowe są lokalnie drużynowe; obejmuje to boost, guard, evade oraz drużynową warstwę V-MAX."
)
LATEST_CHANGES_TITLE = "Soulbound v0.35.11 - All Local Party Combat Buffs"
LATEST_CHANGES = [
    "v0.35.11: każdy prawdziwy boost bojowy trafia do wszystkich żywych członków drużyny stojących razem w tej samej lokacji.",
    "Guard daje każdemu obecnemu członkowi własną ochronę następnego trafienia, a evade daje każdemu własny gwarantowany unik następnego ataku.",
    "V-MAX Meca daje lokalnej drużynie +30 procent do skilli/spelli oraz Protect/Shell/Regen; Mec uruchamiający V-MAX zachowuje dodatkowo swoje specjalne transformacje skilli.",
    "Upgrade Inżyniera został poprawnie sklasyfikowany jako utility, ponieważ jest trwałym ulepszeniem narzędzia, a nie czasowym buffem bojowym.",
    "Dodano stały audit wszystkich lokalnych buffów drużynowych.",
]

# ============================================================
# v0.36.0 - GLOBAL PROGRESSION 600 + LEADER DISBAND
# ============================================================
def progression_600_and_leader_disband_audit_v0360():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")

    caps={
        "generator": int(getattr(generator_core_v027,"MAX_LEVEL",0) or 0),
        "character": int(CHARACTER_MAX_LEVEL),
        "class_mastery": int(CLASS_MASTERY_MAX_LEVEL),
        "skill": int(SKILL_MAX_LEVEL),
        "soul": int(SOUL_MAX_LEVEL),
        "soul_weapon_mastery": int(SOUL_WEAPON_MASTERY_MAX_LEVEL),
        "profession": int(PROFESSION_MAX_LEVEL),
        "tool": int(TOOL_MAX_LEVEL),
        "guild": int(V0926_GUILD_MAX_LEVEL),
    }
    metrics["caps"]=caps
    check("all_main_caps_600", all(v==600 for v in caps.values()), caps)
    check("soul_tiers_60", int(SOUL_MAX_TIER)==60 and len(SOUL_TIER_THRESHOLDS)==60 and int(SOUL_TIER_THRESHOLDS[-1])==600)
    check("tool_tiers_60", int(TOOL_MAX_TIER)==60 and len(TOOL_TIER_THRESHOLDS)==60 and int(TOOL_TIER_THRESHOLDS[-1])==600)
    check("profession_rank_cap_600", int(PROFESSION_RANK_THRESHOLDS[-1])==600)
    check("profession_count_12", len(PROFESSION_RANK_NAMES)>=12, len(PROFESSION_RANK_NAMES))
    check("all_tool_name_tables_60", all(len(tuple(v))>=60 for v in TOOL_TIER_NAMES.values()), {k:len(tuple(v)) for k,v in TOOL_TIER_NAMES.items()})

    grid=(1,*range(10,601,10))
    skill_errors=[]
    for class_name,rows in CLASS_SKILLS.items():
        unlocks=[int(row.get("unlock",0) or 0) for row in rows]
        counts={level:unlocks.count(level) for level in grid}
        if len(rows)!=183 or min(unlocks or [0])!=1 or max(unlocks or [0])!=600:
            skill_errors.append(f"{class_name}:{len(rows)}:{min(unlocks or [0])}-{max(unlocks or [0])}")
        if class_name not in ("Mec","Inżynier") and any(counts[level]!=3 for level in grid):
            skill_errors.append(f"{class_name}:grid")
    check("skill_grid_183_per_class", not skill_errors, skill_errors[:10])
    metrics["classes"]=len(CLASS_SKILLS)
    metrics["skills_total"]=sum(len(v) for v in CLASS_SKILLS.values())

    check("class_equipment_to_600", int(CLASS_EQUIPMENT_MASTERY_LEVELS[-1])==600)

    # v0.36.0: każdy kolejny Tier klasowego EQ ma realnie inny, rosnący
    # budżet podstawowych statów. Chroni szczególnie niskie progi
    # 1/10/20/30, które wcześniej mogły powtarzać te same wartości.
    eq_stat_progression_errors=[]
    for class_name, per_tier in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        previous={}
        for required_level in CLASS_EQUIPMENT_MASTERY_LEVELS:
            for item_id in per_tier.get(required_level, ()):
                item=ITEMS.get(item_id,{})
                key=(int(item.get("class_equipment_style",1) or 1), str(item.get("slot") or ""))
                budget=int(item.get("affix_amount",0) or 0) + sum(
                    int(v or 0) for v in (item.get("stats") or {}).values()
                )
                if key in previous and budget <= previous[key][1]:
                    eq_stat_progression_errors.append(
                        f"{class_name}:{key[0]}:{key[1]}:{previous[key][0]}={previous[key][1]} -> {required_level}={budget}"
                    )
                previous[key]=(int(required_level),budget)
    check("class_equipment_stats_rise_every_tier", not eq_stat_progression_errors, eq_stat_progression_errors[:20])

    low_tier_budgets={}
    for class_name, per_tier in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        row=[]
        for required_level in (1,10,20,30):
            ids=tuple(per_tier.get(required_level,()))
            if not ids:
                row.append(None); continue
            item=ITEMS[ids[0]]
            row.append(int(item.get("affix_amount",0) or 0) + sum(int(v or 0) for v in (item.get("stats") or {}).values()))
        low_tier_budgets[class_name]=row
    check("class_equipment_low_tiers_1_10_20_30_distinct",
          all(None not in row and row==sorted(set(row)) and len(row)==4 for row in low_tier_budgets.values()),
          low_tier_budgets)

    check("endgame_resources_to_600",
          any(int(level)==600 for level,_ in ENDGAME_ORE_UNLOCKS)
          and any(int(level)==600 for level,_ in ENDGAME_WOOD_UNLOCKS)
          and any(int(level)==600 for level,_ in ENDGAME_HERB_UNLOCKS))
    check("soul_trials_41_60", all(tier in SOUL_TRIAL_QUEST_IDS for tier in range(41,61)))
    check("guild_bonus_legacy_preserved",
          v0926_guild_bonus_percent(100)==11 and v0926_guild_bonus_percent(200)==15
          and v0926_guild_bonus_percent(300)==19 and v0926_guild_bonus_percent(400)==23
          and v0926_guild_bonus_percent(600)==29,
          [v0926_guild_bonus_percent(x) for x in (100,200,300,400,600)])
    check("guild_cost_monotonic_extension",
          v0926_guild_upgrade_cost(399)>0 and v0926_guild_upgrade_cost(400)>=v0926_guild_upgrade_cost(399)
          and v0926_guild_upgrade_cost(500)>=v0926_guild_upgrade_cost(400))

    try:
        import inspect
        src=inspect.getsource(SessionMovementPartySocialMixin.leave_party)
        check("leader_leave_disbands", "self.server.parties.pop(key, None)" in src and "Drużyna została rozwiązana" in src)
        check("leader_leave_no_transfer", "new_leader" not in src and "min(members)" not in src and "next(iter(members" not in src)
    except Exception as exc:
        errors.append(f"leader source audit: {type(exc).__name__}: {exc}")

    return {"version":"0.36.0","error_count":len(errors),"errors":errors,"metrics":metrics}

PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360=progression_600_and_leader_disband_audit_v0360()
if PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360["error_count"]:
    raise RuntimeError(
        "Progression 600 + Leader Disband Audit v0.36.0 failed: "
        + "; ".join(PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360["errors"][:50])
    )

# Final truth layer: old HELP aliases remain accepted, but describe current 600 progression.
HELP_TOPICS["progresja600"] = [
    "Główne osie progresji mają zakres 1-600: Level postaci, Biegłość klas, Soul Level, Soul Weapon Mastery, Skill Level, profesje i narzędzia. Sześć statystyk bazowych pozostaje bez twardego limitu.",
    "Każda z 14 klas ma 183 skille/spelle i dochodzi do Biegłości 600. Dwanaście standardowych klas ma dokładnie 3 skille na progach 1, 10, 20 i dalej co 10; Mec i Inżynier zachowują swoje autorskie wczesne progi.",
    "Broń Duszy rozwija się do Soul Level 600 i Soul Tier 60. Tiery 41-60 kontynuują próby co 10 poziomów od 410 do 600.",
    "Wszystkie 12 profesji i 12 narzędzi rozwijają się do 600. Narzędzia mają 60 Tierów i nie mają trwałości.",
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
    "Soulbound ma 12 profesji 1-600: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo, Jubilerstwo, Krawiectwo, Garbarstwo, Stolarstwo i Zaklinanie.",
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
if PARTY_QUEST_ACCEPT_SYNC_AUDIT_V0361["error_count"]:
    raise RuntimeError(
        "Party Quest Accept Sync Audit v0.36.1 failed: "
        + "; ".join(PARTY_QUEST_ACCEPT_SYNC_AUDIT_V0361["errors"][:50])
    )

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
def terrain_threat_rebalance_audit_v0362():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")
    try:
        import inspect
        # Every currently materialized authored recommendation must be honored
        # by the numeric room stage used by combat generation.
        bad=[]
        checked=0
        for rid, room in ROOMS.items():
            try:
                rec=int(room.get("recommended_mastery",0) or 0)
                stage=int(room.get("generator_level",0) or 0)
            except Exception:
                continue
            if rec>0:
                checked+=1
                if stage < rec:
                    bad.append((rid,rec,stage))
        metrics["recommended_rooms_checked"]=checked
        check("recommended_mastery_is_balance_floor", not bad, str(bad[:10]))

        gsrc=inspect.getsource(generator_core_v027.runtime_room_level)
        check("runtime_room_recommended_floor", "_v0362_recommended_room_floor" in gsrc and "_v0362" in generator_core_v027.runtime_room_level.__name__)

        wsrc=inspect.getsource(World._terrain_scaled_template_v0362)
        check("room_stage_runtime_clone", "stage > base_stage" in wsrc and "runtime_mob_balance" in wsrc)
        check("terrain_hp_growth", "1.0 + runtime_stage / 100.0" in wsrc and "min(4.0" in wsrc)
        check("terrain_damage_growth", "runtime_stage / 1000.0" in wsrc and "min(0.50" in wsrc)
        check("bosses_not_extra_terrain_scaled", 'rank in ("normal", "elite", "rare")' in wsrc)

        csrc=inspect.getsource(v0190_apply_combat_template)
        check("terrain_multiplier_survives_runtime_refresh", "terrain_runtime_clone_v0362" in csrc and "terrain_hp_multiplier_v0362" in csrc)

        # Concrete curve anchors used by the terrain layer.
        def hp_mult(stage): return min(4.0, 1.0 + stage / 100.0)
        def dmg_mult(stage): return 1.0 + min(0.50, stage / 1000.0)
        check("terrain_100_hp_x2", abs(hp_mult(100)-2.0)<1e-9)
        check("terrain_100_damage_x1_10", abs(dmg_mult(100)-1.10)<1e-9)
        check("terrain_300_hp_cap_x4", abs(hp_mult(300)-4.0)<1e-9)
    except Exception as exc:
        errors.append(f"terrain threat source audit: {type(exc).__name__}: {exc}")
    return {"version":"0.36.2","error_count":len(errors),"errors":errors,"metrics":metrics}

TERRAIN_THREAT_REBALANCE_AUDIT_V0362=terrain_threat_rebalance_audit_v0362()
if TERRAIN_THREAT_REBALANCE_AUDIT_V0362["error_count"]:
    raise RuntimeError(
        "Terrain Threat Rebalance Audit v0.36.2 failed: "
        + "; ".join(TERRAIN_THREAT_REBALANCE_AUDIT_V0362["errors"][:50])
    )

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
        dbsrc=inspect.getsource(Database.migrate_schema)
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
if OFFLINE_PLAYER_PROFILES_AUDIT_V0363["error_count"]:
    raise RuntimeError(
        "Offline Player Profiles Audit v0.36.3 failed: "
        + "; ".join(OFFLINE_PLAYER_PROFILES_AUDIT_V0363["errors"][:50])
    )

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
def independent_skill_cooldowns_audit_v0364():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")
    try:
        import inspect
        all_rows=[]
        seen={}
        duplicates=[]
        for class_name, rows in (CLASS_SKILLS or {}).items():
            for skill in rows:
                sid=str(skill.get("id") or "")
                all_rows.append((class_name, sid, skill.get("name")))
                if not sid:
                    errors.append(f"skill without id: {class_name}/{skill.get('name')}")
                    continue
                if sid in seen:
                    duplicates.append((sid, seen[sid], (class_name, skill.get("name"))))
                else:
                    seen[sid]=(class_name, skill.get("name"))
        check("all_skill_ids_unique", not duplicates, duplicates[:5])
        metrics["skill_count"] = len(all_rows)
        metrics["unique_skill_ids"] = len(seen)

        csrc=inspect.getsource(SessionCoreProgressionMixin.start_skill_cooldown_v0364)
        check("single_id_write", 'self.skill_cooldowns[skill_id] = ready_at' in csrc)
        check("no_category_cooldown_keys", all(
            token not in csrc for token in ('physical_cooldown','magic_cooldown','class_cooldown','global_cooldown')
        ))

        usrc=inspect.getsource(SessionSkillsCombatMixin.use_class_skill)
        check("manual_skill_reads_own_cd", 'skill_cooldown_ready_at_v0364(skill)' in usrc)
        check("manual_skill_starts_own_cd", 'start_skill_cooldown_v0364(skill, effective_cooldown, now)' in usrc)
        qsrc=inspect.getsource(SessionSkillsCombatMixin.auto_queue_skill_usable)
        check("queue_reads_own_cd", 'skill_cooldown_ready_at_v0364(skill)' in qsrc)
        hsrc=inspect.getsource(SessionMovementPartySocialMixin.auto_priest_heal_option)
        check("auto_heal_reads_own_cd", 'skill_cooldown_ready_at_v0364(skill)' in hsrc)
        h2src=inspect.getsource(SessionMovementPartySocialMixin.perform_auto_priest_heal)
        check("auto_heal_starts_own_cd", 'start_skill_cooldown_v0364(skill, effective_cooldown, now)' in h2src)

        # Behavior test: starting B must not alter A, and restarting A must not alter B.
        class Dummy:
            skill_cooldowns={}
            skill_cooldown_ready_at_v0364=SessionCoreProgressionMixin.skill_cooldown_ready_at_v0364
            skill_cooldown_remaining_v0364=SessionCoreProgressionMixin.skill_cooldown_remaining_v0364
            skill_cooldown_active_v0364=SessionCoreProgressionMixin.skill_cooldown_active_v0364
            start_skill_cooldown_v0364=SessionCoreProgressionMixin.start_skill_cooldown_v0364
        d=Dummy(); d.skill_cooldowns={}
        d.start_skill_cooldown_v0364('audit_skill_a', 10, 100.0)
        a1=d.skill_cooldown_ready_at_v0364('audit_skill_a')
        d.start_skill_cooldown_v0364('audit_skill_b', 20, 100.0)
        a2=d.skill_cooldown_ready_at_v0364('audit_skill_a')
        b1=d.skill_cooldown_ready_at_v0364('audit_skill_b')
        d.start_skill_cooldown_v0364('audit_skill_a', 5, 101.0)
        b2=d.skill_cooldown_ready_at_v0364('audit_skill_b')
        check("behavior_independent_a_after_b", a1 == a2 == 110.0)
        check("behavior_independent_b_after_a", b1 == b2 == 120.0)
        check("behavior_only_two_keys", set(d.skill_cooldowns)=={'audit_skill_a','audit_skill_b'})
    except Exception as exc:
        errors.append(f"independent cooldown audit: {type(exc).__name__}: {exc}")
    return {"version":"0.36.4","error_count":len(errors),"errors":errors,"metrics":metrics}

INDEPENDENT_SKILL_COOLDOWNS_AUDIT_V0364=independent_skill_cooldowns_audit_v0364()
if INDEPENDENT_SKILL_COOLDOWNS_AUDIT_V0364["error_count"]:
    raise RuntimeError(
        "Independent Skill Cooldowns Audit v0.36.4 failed: "
        + "; ".join(INDEPENDENT_SKILL_COOLDOWNS_AUDIT_V0364["errors"][:50])
    )

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
    errors=[]
    quest_id = SOUL_TRIAL_QUEST_IDS.get(7)
    quest = QUESTS.get(quest_id, {}) if quest_id else {}
    target = str(quest.get("target") or "")
    needed = int(quest.get("needed", 0) or 0)
    if target != "cemetery_restless_dead":
        errors.append(f"Tier 7 target={target!r}, expected cemetery_restless_dead")
    if needed != 4:
        errors.append(f"Tier 7 needed={needed}, expected 4")
    target_rooms = [
        room_id for room_id, mob_id in MOB_SPAWNS
        if mob_id == "cemetery_restless_dead"
        and ROOMS.get(room_id, {}).get("zone") == "Stary Cmentarz"
    ]
    distinct_rooms = sorted(set(target_rooms))
    expected_rooms = {
        "graveyard", "cemetery_ossuary_path", "cemetery_moon_garden",
        "cemetery_fallen_chapel", "cemetery_bone_field", "cemetery_bell_tower",
    }
    missing = sorted(expected_rooms - set(distinct_rooms))
    if missing:
        errors.append("missing Tier 7 cemetery spawn rooms: " + ", ".join(missing))
    if len(distinct_rooms) < 6:
        errors.append(f"Tier 7 has only {len(distinct_rooms)} distinct cemetery target rooms, expected >=6")
    return {
        "version":"0.36.5", "quest_id":quest_id, "target":target, "needed":needed,
        "distinct_spawn_rooms":len(distinct_rooms), "spawn_rooms":distinct_rooms,
        "error_count":len(errors), "errors":errors,
    }

SOUL_TIER7_CEMETERY_SPAWN_AUDIT_V0365 = soul_tier7_cemetery_spawn_audit_v0365()
if SOUL_TIER7_CEMETERY_SPAWN_AUDIT_V0365["error_count"]:
    raise RuntimeError(
        "Soul Tier 7 Cemetery Spawn Audit v0.36.5 failed: "
        + "; ".join(SOUL_TIER7_CEMETERY_SPAWN_AUDIT_V0365["errors"][:50])
    )

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
