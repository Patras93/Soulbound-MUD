COMMAND_ALIASES.update({
    "bosskodex": "bosscodex", "bosscodex": "bosscodex",
    "kodeksbossow": "bosscodex", "kodeksbossów": "bosscodex",
})

HELP_TOPIC_ALIASES.update({
    "bosskodex": "boss_codex", "bosscodex": "boss_codex",
    "kodeksbossow": "boss_codex", "kodeksbossów": "boss_codex",
    "exploration": "eksploracja", "postep": "eksploracja", "postęp": "eksploracja",
    "bestiary": "bestiariusz", "bestia": "bestiariusz",
    "achievements": "osiagniecia", "achievement": "osiagniecia",
    "osiągnięcia": "osiagniecia",
    "titles": "tytuly", "tytuły": "tytuly",
    "collection": "collection_codex", "kolekcja": "collection_codex",
    "collectioncodex": "collection_codex",
    "drophistory": "loot_accessibility", "lootfilter": "loot_accessibility",
    "filtrlootu": "loot_accessibility",
})

HELP_TOPICS["eksploracja"] = [
    "Eksploracja jest zapisywana osobno dla każdej postaci. Obejmuje bieżący świat oraz lokacje generowane dynamicznie; nie używa starego sztywnego licznika 1272.",
    "mapa / map - procent bieżącego regionu i tylko odkryte nazwy lokacji; nieodkryte miejsca pozostają ukryte.",
    "mapa all / map all - procent wszystkich regionów oraz status nagrody za 100 procent.",
    "eksploracja / exploration - procent bieżącej strefy i całego świata; exploration all - lista większych stref.",
    "progress - ogólny postęp; progress region - szczegóły bieżącego regionu.",
    "100 procent większej strefy daje Soul XP, walutę, unikalną Pamiątkę Odkrywcy, tytuł i osiągnięcie.",
]
HELP_TOPICS["osiagniecia"] = [
    "Achievementy mają progi Bronze, Silver, Gold i Platinum; nie dają bezpośredniej przewagi bojowej.",
    "osiagniecia / achievements - pokaż bieżący postęp i odblokowane osiągnięcia.",
    "Śledzone są gobliny, skrzynie, rare moby, bossowie, eksploracja świata, profesje 200, Bestiariusz, rzadkie ryby, klejnoty, multiclass, Soul Level oraz kontrakty.",
    "Metryki możliwe do odtworzenia są synchronizowane z trwałym stanem postaci; nowe połowy rzadkich ryb i nowe klejnoty są liczone na bieżąco.",
]
HELP_TOPICS["tytuly"] = [
    "tytuly / titles - lista odblokowanych tytułów.",
    "tytul <numer lub nazwa> / title <number or name> - ustaw aktywny tytuł.",
    "tytul off - wyłącz aktywny tytuł.",
    "Tytuły są wyłącznie prestiżowe: nie zwiększają statystyk, obrażeń, obrony, dropu, XP ani waluty.",
]
HELP_TOPICS["bounty_contracts"] = [
    "bounty / zlecenia / contracts - pokaż losowaną Tablicę Zleceń i bieżący kontrakt.",
    "bounty accept <1-3> / bounty <1-3> - przyjmij jeden kontrakt. Każdy zaczyna od 0/x.",
    "bounty aktywne - przeczytaj aktualny postęp bez cache.",
    "bounty odbierz / bounty claim - odbierz Soul XP i złoto po wykonaniu celu.",
    "bounty odśwież - ponownie losuje trzy oferty, ale tylko gdy nie masz aktywnego kontraktu.",
    "Postęp kontraktu jest zapisywany per postać i po każdym właściwym zabiciu, wydobyciu, połowie, ścięciu albo zbiorze NVDA od razu czyta n/x.",
    "Stare zlecenia Gildii są nadal dostępne: guildbounty / zleceniagildii.",
]
HELP_TOPIC_ALIASES.update({
    "bounty": "bounty_contracts", "contracts": "bounty_contracts",
    "kontrakty": "bounty_contracts", "zlecenia": "bounty_contracts",
    "zlecenie": "bounty_contracts", "tablicazlecen": "bounty_contracts",
})
HELP_TOPICS["boss_codex"] = [
    "v0.9.21: Boss Codex pokazuje także wersję piętrową bossa, najwyższy pokonany próg jego instancji oraz unikalne dropy zdobyte z tego bossa.",
    "bosskodex / bosscodex - podsumowanie odkrytych bossów.",
    "bosskodex lista - odkryte bossy stronicowane po 30 wpisów.",
    "bosskodex <nazwa> - liczba pokonań, pierwszy i ostatni kill, solo/grupa, rekord czasu i odkryte dropy.",
    "Dane pierwszego/ostatniego killa i rekordu są odzyskiwane z Bestiariusza. Rozdział solo/grupa oraz lista dropów są dokładne od v0.9.6; starszych danych gra nie zgaduje.",
]

HELP_TOPICS["collection_codex"] = [
    "v0.9.21 Collection Codex 2.0: procenty dla każdej klasy, konkretnego setu, legend, materiałowego EQ, regionu i instancji.",
    "kolekcja / collection - podsumowanie Collection Codex.",
    "kolekcja ryby|minerały|zioła|klejnoty|bossowie|rare|materiały|wyjątkowe - główne kategorie v0.9.6.",
    "Starsze widoki named|sety|skrzynie pozostają dostępne dla zgodności.",
    "Nieodkryte wpisy nie zdradzają nazw.",
]
HELP_TOPIC_ALIASES.update({
    "skrzynie_bossow": "boss_chests", "skrzynie bossow": "boss_chests",
    "bosschests": "boss_chests", "boss_chests": "boss_chests",
    "admin": "admin_owner", "administrator": "admin_owner",
})

HELP_TOPICS["boss_chests"] = [
    "Skrzynie Bossów stoją na piętrach bossów co 10 w Krypcie, Wieży Astralnej, Mitycznej Krypcie, Mitycznej Wieży i Twierdzy Gigantów.",
    "Właściwy Klucz Bossa jest gwarantowany w ciele pokonanego bossa danego piętra.",
    "Bez właściwego klucza skrzynia pozostaje zamknięta.",
    "unlock / odklucz / odblokuj - zużyj klucz i otwórz skrzynię.",
    "Skrzynia daje gwarantowane złoto oraz losowe użyteczne przedmioty zależne od poziomu zawartości.",
]
HELP_TOPICS["admin_owner"] = [
    "Komendy administracyjne są owner-only i wymagają nazwy konta na serwerowej whitelist SOULBOUND_ADMIN_ACCOUNTS.",
    "v0.30.1: w MENU POSTACI admin widzi ukrytą opcję 6 Administrator; zwykłe konta nie widzą tej pozycji wcale.",
    "Panel działa także przy 0/12 postaci: lista kont, postacie konta, wipe własnego lub wskazanego konta, usunięcie jednej postaci i wipe wszystkich postaci serwera.",
    "admin help / administrator pomoc - lista opcji właściciela podczas gry postacią.",
    "wipe moje postacie POTWIERDZAM - usuwa postacie Twojego konta, ale zachowuje konto i hasło.",
    "wipe wszystkie postacie POTWIERDZAM - serwerowy wipe postaci bez kasowania kont.",
]

HELP_TOPICS["loot_accessibility"] = [
    "historiadropow / drophistory - ostatnie wartościowe dropy.",
    "loot all - czytaj każdy loot.",
    "loot rare+ - czytaj Rare i lepszy; loot epic+ - Epic i lepszy.",
    "loot legendary - Legendary, Unique i Mythic; loot off - wycisz komunikaty przedmiotów.",
    "Filtr nie usuwa przedmiotów. Zmienia tylko komunikaty lootu pod NVDA.",
]

# v0.9.12: finalna warstwa HELP dla progresji 1-400. Historyczne tematy
# v0.8.x pozostają archiwalne, ale bieżące tematy muszą opisywać realny stan gry.
HELP_TOPICS["progresja400"] = [
    "Postać nadal NIE ma levelu postaci.",
    "Biegłość każdej z 12 klas ma zakres 1-400; na każdym progu 1 oraz co 10 aż do 400 dostępne są 3 skille/spelle do nauczenia.",
    "Każdy nauczony skill/spell ma własny Skill Level 1-400 i własny XP.",
    "Broń Duszy ma Soul Level 1-400. Soul Tiery mają zakres 1-40; Tiery 21-40 odblokowują się co 10 Soul Level od 210 do 400 przez kolejne Próby Krypty.",
    "Wszystkie 8 profesji i 8 narzędzi mają zakres 1-400. Narzędzia mają 40 Tierów i nie mają trwałości.",
    "Klasowe EQ ma progi Biegłości 1, 10, 20 i dalej co 10 aż do 400. Krypta ma zwykłe Tiery EQ 1-40, czyli progresję wyposażenia do 400.",
    "Po 200 profesje nie skracają czasu pracy poniżej dotychczasowego minimum; dalsze levele są kontynuacją progresji bez łamania timerów.",
    "Nieskończone Krypty rosną trudnością i Class/Soul XP co 10 pięter; moc EQ ma cap 400, więc piętra powyżej 400 nie tworzą nieskończonego power creepu.",
]
HELP_TOPIC_ALIASES.update({
    "400": "progresja400", "progression400": "progresja400", "progresja 400": "progresja400",
})
HELP_TOPICS["krypty_nieskonczone"] = [
    "Zwykła Krypta i Mityczna Krypta mają nieskończoną liczbę pięter; piętra powyżej 200 powstają na żądanie.",
    "Co 10 pięter jest boss oraz dodatkowy próg trudności. HP, obrażenia, Class XP, Soul XP i Postęp Rozwoju rosną razem z głębokością.",
    "Nie ma blokady wejścia typu wymagany Soul Level 100. Mityczna Krypta jest dostępna wcześniej, ale od pierwszego piętra jest dużo trudniejsza.",
    "EQ rozwija się do progresji 400 / Tieru 40; głębiej trudność i XP nadal rosną, ale moc EQ i ekonomia nie rosną bez końca.",
    "Portale/checkpointy odblokowują się po bossach co 10 pięter także powyżej 200.",
]
HELP_TOPIC_ALIASES.update({
    "nieskonczona krypta": "krypty_nieskonczone", "nieskończona krypta": "krypty_nieskonczone",
    "infinite crypt": "krypty_nieskonczone", "krypty infinite": "krypty_nieskonczone",
})
HELP_TOPICS["profesje"] = [
    "Soulbound ma 8 profesji 1-400: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo i Jubilerstwo.",
    "Każda profesja ma własny level 1-400. Odpowiadające narzędzie ma osobny level 1-400 i 40 Tierów.",
    "Stare wymagania receptur i zasobów 1-200 pozostają w tych samych miejscach; zakres 220-400 dodaje nowe zasoby, receptury i zlecenia co 20 leveli.",
    "Po levelu 200 czas pracy pozostaje na dotychczasowym minimum. Dalszy rozwój nie skraca akcji poniżej zbalansowanego limitu.",
    "Narzędzia nie mają trwałości ani zużycia.",
]
HELP_TOPICS["ekwipunek"] = [
    "Nowa postać nie dostaje startowego EQ klasowego. Klasowe wyposażenie zdobywa się w sklepach i jako losowy drop z mobów.",
    "Każda z 12 klas ma 3 różne linie EQ o równym budżecie mocy.",
    "Klasowe EQ ma progi Biegłości 1, 10, 20 i dalej co 10 aż do 400.",
    "Krypta daje zwykłe EQ Tier 1-40: Tiery 21-40 odpowiadają progresji po dawnym capie 200.",
    "Nieskończone piętra powyżej progresji 400 nie zwiększają dalej mocy EQ.",
    "shop <klasa> filtruje ofertę klasową, np. shop wojownik albo shop mag.",
]
HELP_TOPICS["dusza"] = [
    "Broń Duszy ma Soul Level 1-400 i Soul XP. Nie jest levelem postaci.",
    "Soul Tiery mają zakres 1-40. Historyczne Tiery 1-20 i ich progi do Soul 200 pozostają dokładnie bez zmian.",
    "Tiery 21-40 odblokowują się od Soul 210 do 400 co 10 leveli i wymagają kolejnych Prób Kapłana Elora w nieskończonej Krypcie.",
    "Soul Level 201-400 dalej zwiększa moc Broni Duszy łagodniej niż zakres 1-200.",
    "Skille klasowe odblokuje Biegłość właściwej klasy; stare progi 1-200 nie zostały przesunięte, a nowa linia działa 220-400.",
    "Zwykła i Mityczna Krypta nie mają limitu pięter ani wymogu Soul Level do wejścia. Mityczna Wieża Astralna nadal ma własne zasady.",
]
HELP_TOPICS["umiejetnosci"] = [
    "Każdy nauczony skill i spell ma własny Skill Level 1-400 oraz własny XP.",
    "Skill Level 1-200 zachowuje dawny balans. 201-400 daje malejący dalszy wzrost mocy i cooldownu.",
    "Przy Skill Level 200 mnożnik mocy pozostaje około 1,745; przy 400 około 1,995. Cooldown przy 400 ma maksymalnie około 35 procent redukcji.",
    "Progi nauczenia skilli nadal wynikają z Biegłości klasy i nie zostały przeliczone x2.",
]
HELP_TOPICS["narzedzia200"] = [
    "Wszystkie 8 narzędzi ma teraz level 1-400 i 40 Tierów.",
    "Stare Tiery 1-20 oraz ich progi do 200 pozostają dokładnie bez zmian.",
    "Tiery 21-40 zaczynają się na 210, 220 i dalej co 10 aż do 400.",
    "Narzędzia nie mają trwałości ani nie wymagają naprawy.",
]
HELP_TOPICS["soul200"] = [
    "Broń Duszy ma Soul Level 1-400.",
    "Historyczne Tiery 1-20 i ich Próby do Soul 200 pozostają bez zmian.",
    "Tiery 21-40 obejmują Soul 210-400 co 10 leveli i mają dalsze Próby w nieskończonej Krypcie.",
    "Nie ma levelu postaci.",
]


# v0.9.14: finalna warstwa HELP dla domknięcia lochów/wież i progresji questów walki.
HELP_TOPICS["lochy_wieze"] = [
    "Od v0.11.0 wszystkie piętrowe lochy i wieże są generowane na żądanie już od pierwszego poziomu.",
    "Wieża Astralna, Mityczna Wieża Astralna i Twierdza Gigantów mają cykliczne motywy pięter. Co 5. proceduralne piętro bez głównego bossa ma dodatkowego Czempiona Próby; co 10. piętro nadal ma właściwego bossa.",
    "Kopalnia Głębinowa i cztery lochy profesyjne również są dynamiczne od poziomu 1. Specjalne sektory rezonansowe, bogate i mistrzowskie nadal występują zgodnie z progresją i nie podnoszą capu mocy ponad 400.",
    "Nieskończona głębokość zwiększa wyzwanie i XP. Ekonomia, zasoby i moc EQ nadal respektują cap progresji 400.",
]
HELP_TOPIC_ALIASES.update({
    "lochy": "lochy_wieze", "wieze": "lochy_wieze", "wieże": "lochy_wieze",
    "dungeons": "lochy_wieze", "towers": "lochy_wieze", "lochy i wieze": "lochy_wieze",
    "lochy i wieże": "lochy_wieze",
})
HELP_TOPICS["questy_walka"] = [
    "Każdy quest walki typu kill daje dodatkowy EXP statystyk oraz Soul XP oprócz swoich dotychczasowych nagród.",
    "EXP statystyk jest przyznawany OSOBNO do każdej statystyki: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma. Nie istnieje level postaci.",
    "Każda statystyka ma własny licznik EXP i własny próg wzrostu. Obowiązuje dotychczasowe zabezpieczenie nagrody questa przed przeskakiwaniem wielu punktów statystyki jednym oddaniem.",
    "Soul XP z questa podlega tej samej bramce Soul Tier co każde inne źródło Soul XP.",
]
HELP_TOPIC_ALIASES.update({
    "questy walki": "questy_walka", "combat quests": "questy_walka",
    "xp statystyk": "questy_walka", "stat xp": "questy_walka",
})
# Nadpisanie bieżącego tematu Duszy: v0.9.14 wprowadza twardą bramkę Tieru.
HELP_TOPICS["dusza"] = [
    "Broń Duszy ma Soul Level 1-400 i Soul XP. Nie jest levelem postaci.",
    "Soul Tiery mają zakres 1-40. Historyczne Tiery 1-20 oraz progi do Soul 200 pozostają bez zmian; Tiery 21-40 prowadzą dalej do Soul 400.",
    "Soul Level może dojść tylko do progu następnego, jeszcze nieodblokowanego Tieru. Na tym progu dalszy Soul XP jest ZABLOKOWANY.",
    "Aby Soul XP znów ruszył, wykonaj właściwą Próbę Broni Duszy i odblokuj kolejny Tier komendą unlock. Nadmiar Soul XP ponad zablokowany próg nie jest bankowany.",
    "Bramka działa globalnie: na Soul XP z mobów, questów walki, przedmiotów i innych źródeł.",
    "Istniejące save'y nie są cofane, jeśli historycznie mają Soul Level ponad bieżącym Tierem; dalszy Soul XP pozostaje zablokowany do nadrobienia Tierów.",
]
HELP_TOPICS["progresja400"] = [
    "Postać nadal NIE ma levelu postaci.",
    "Biegłość każdej z 12 klas ma zakres 1-400; skille zachowują stare progi 1-200 i dalsze odblokowania 220-400.",
    "Każdy nauczony skill/spell ma własny Skill Level 1-400 i własny XP.",
    "Broń Duszy ma Soul Level 1-400 oraz Soul Tier 1-40. Soul XP zatrzymuje się na progu następnego nieodblokowanego Tieru.",
    "Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma rozwijają się niezależnym EXP statystyk; questy walki rozwijają wszystkie sześć.",
    "Wszystkie 8 profesji i 8 narzędzi mają zakres 1-400. Narzędzia mają 40 Tierów i nie mają trwałości.",
    "Klasowe EQ oraz EQ Krypty rozwijają się do progresji/Tieru 40 odpowiadającego 400. Powyżej 400 głębokość nie zwiększa mocy ekonomii/EQ bez końca.",
]

# v0.9.14: uzupełnienie istniejących głównych tematów HELP, nie tylko nowych aliasów.
HELP_TOPICS["questy"].append(
    "Każdy quest walki typu kill daje dodatkowo EXP osobno do Siły, Zręczności, Kondycji, Inteligencji, Siły Woli i Charyzmy oraz Soul XP. Soul XP podlega bramce aktualnego Tieru."
)
if "statystyki" in HELP_TOPICS:
    HELP_TOPICS["statystyki"].append(
        "Questy walki rozwijają wszystkie sześć statystyk niezależnym EXP; nie istnieje level postaci."
    )

IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240


TELNET_CHARSET = 42
TELNET_CHARSET_REQUEST = 1
TELNET_CHARSET_ACCEPTED = 2
TELNET_CHARSET_REJECTED = 3

DEFAULT_TEXT_ENCODING = "utf-8"
POLISH_LEGACY_ENCODING = "cp1250"
SUPPORTED_TEXT_ENCODINGS = (
    DEFAULT_TEXT_ENCODING,
    POLISH_LEGACY_ENCODING,
)


def telnet_charset_offer_bytes():
    # RFC 2066: TELNET CHARSET option 42.
    # UTF-8 jest preferowane, Windows-1250 jest fallbackiem.
    return (
        bytes((
            IAC, WILL, TELNET_CHARSET,
            IAC, SB, TELNET_CHARSET,
            TELNET_CHARSET_REQUEST,
            ord(";"),
        ))
        + b"UTF-8;WINDOWS-1250"
        + bytes((IAC, SE))
    )


def strip_telnet_commands(data: bytes) -> bytes:
    out = bytearray()
    i = 0

    while i < len(data):
        byte = data[i]

        if byte != IAC:
            out.append(byte)
            i += 1
            continue

        i += 1
        if i >= len(data):
            break

        command = data[i]
        i += 1

        if command in (DO, DONT, WILL, WONT):
            if i < len(data):
                i += 1
            continue

        if command == SB:
            while i < len(data):
                if (
                    data[i] == IAC
                    and i + 1 < len(data)
                    and data[i + 1] == SE
                ):
                    i += 2
                    break
                i += 1
            continue

        if command == IAC:
            out.append(IAC)

    return bytes(out)


def decode_polish_telnet_text(
    data: bytes,
    preferred_encoding=DEFAULT_TEXT_ENCODING,
) -> str:
    payload = strip_telnet_commands(data)

    preferred = str(
        preferred_encoding or DEFAULT_TEXT_ENCODING
    ).lower()

    attempts = []
    for encoding in (
        preferred,
        DEFAULT_TEXT_ENCODING,
        POLISH_LEGACY_ENCODING,
    ):
        if encoding not in attempts:
            attempts.append(encoding)

    for encoding in attempts:
        try:
            return payload.decode(
                encoding,
                errors="strict",
            )
        except UnicodeDecodeError:
            pass

    # Nie gubimy bajtów po cichu.
    return payload.decode(
        DEFAULT_TEXT_ENCODING,
        errors="replace",
    )


def clean_telnet(
    data: bytes,
    preferred_encoding=DEFAULT_TEXT_ENCODING,
) -> str:
    return decode_polish_telnet_text(
        data,
        preferred_encoding,
    )



def mob_respawn_seconds(template):
    if template.get("respawn_seconds") is not None:
        base_seconds = max(
            1,
            int(template["respawn_seconds"]),
        )
    elif (
        template.get("crypt_boss")
        or template.get("world_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("giant_fortress_boss")
    ):
        base_seconds = BOSS_RESPAWN_SECONDS
    elif template.get("training_dummy"):
        base_seconds = TRAINING_DUMMY_RESPAWN_SECONDS
    else:
        base_seconds = REGULAR_MOB_RESPAWN_SECONDS

    return max(
        1,
        int(round(
            base_seconds
            * GLOBAL_MOB_RESPAWN_MULTIPLIER
        )),
    )

def safe_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9_-]{3,20}", name))


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, hash_hex)


# ================================================================
# v0.8.72 — bossowe skrzynie piętrowe, klucze i losowy urobek
# ================================================================

def _boss_floor_chest_spec(room_id):
    """Zwraca opis skrzyni bossowej dla piętra co 10 lub None."""
    floor = giant_fortress_floor_number(room_id)
    if is_giant_fortress_boss_floor(floor):
        return ("giant", floor, min(400, max(20, floor * 2)))
    floor = crypt_floor_number(room_id)
    if is_crypt_boss_floor(floor):
        return ("crypt", floor, min(400, floor))
    floor = astral_floor_number(room_id)
    if is_astral_boss_floor(floor):
        return ("astral", floor, min(400, floor))
    floor = mythic_crypt_floor_number(room_id)
    if is_mythic_crypt_boss_floor(floor):
        return ("mythic_crypt", floor, min(400, 100 + floor // 2))
    floor = mythic_astral_floor_number(room_id)
    if is_mythic_astral_boss_floor(floor):
        return ("mythic_astral", floor, min(400, 110 + floor // 2))
    return None

BOSS_CHEST_KIND_NAMES = {
    "giant": "Twierdzy Gigantów",
    "crypt": "Krypty",
    "astral": "Wieży Astralnej",
    "mythic_crypt": "Mitycznej Krypty",
    "mythic_astral": "Mitycznej Wieży Astralnej",
}

def boss_floor_key_id(kind, floor):
    return f"boss_chest_key_{kind}_{int(floor)}"

def boss_floor_chest_name(kind, floor):
    return f"Skrzynia Bossa {BOSS_CHEST_KIND_NAMES[kind]}, piętro {int(floor)}"

def _register_boss_floor_keys():
    rows = []
    rows.extend(("giant", f) for f in GIANT_FORTRESS_BOSS_FLOORS)
    rows.extend(("crypt", f) for f in CRYPT_BOSS_FLOORS)
    rows.extend(("astral", f) for f in ASTRAL_BOSS_FLOORS)
    rows.extend(("mythic_crypt", f) for f in sorted(MYTHIC_BOSS_FLOORS))
    rows.extend(("mythic_astral", f) for f in sorted(MYTHIC_BOSS_FLOORS))
    for kind, floor in rows:
        key_id = boss_floor_key_id(kind, floor)
        ITEMS[key_id] = {
            "name": f"Klucz Bossa {BOSS_CHEST_KIND_NAMES[kind]} {floor}",
            "type": "quest",
            "price": None,
            "boss_chest_key": True,
            "boss_chest_kind": kind,
            "boss_chest_floor": int(floor),
            "desc": (
                f"Jednorazowy klucz z ciała bossa. Otwiera skrzynię na "
                f"piętrze {floor} w: {BOSS_CHEST_KIND_NAMES[kind]}."
            ),
        }

_register_boss_floor_keys()

def boss_key_for_template(template):
    if template.get("giant_fortress_boss"):
        floor = int(template.get("giant_fortress_floor", 0) or 0)
        return boss_floor_key_id("giant", floor) if is_giant_fortress_boss_floor(floor) else None
    if template.get("crypt_boss"):
        floor = int(template.get("crypt_floor", 0) or 0)
        return boss_floor_key_id("crypt", floor) if is_crypt_boss_floor(floor) else None
    if template.get("astral_boss"):
        floor = int(template.get("astral_floor", 0) or 0)
        return boss_floor_key_id("astral", floor) if is_astral_boss_floor(floor) else None
    if template.get("mythic_crypt_boss"):
        floor = int(template.get("mythic_crypt_floor", 0) or 0)
        return boss_floor_key_id("mythic_crypt", floor) if is_mythic_crypt_boss_floor(floor) else None
    if template.get("mythic_astral_boss"):
        floor = int(template.get("mythic_astral_floor", 0) or 0)
        return boss_floor_key_id("mythic_astral", floor) if is_mythic_astral_boss_floor(floor) else None
    return None

def roll_profession_gather_quantity(tool_level, profession_level, kind):
    return generator_core_v027.gather_quantity(
        str(kind), tool_level, profession_level, random.random()
    )

def roll_crafting_xp(base_value, variance=0.15):
    # variance is kept only for API compatibility; Generator Core owns the spread.
    return generator_core_v027.crafting_xp_roll(base_value, random.random())

def boss_chest_reward_roll(kind, floor, power):
    power = max(1, min(400, int(power)))
    floor = int(floor)
    # Gwarantowane złoto, ale kwota pozostaje umiarkowana względem bossa.
    base_gold = {
        "giant": max(1, floor // 10),
        "crypt": max(1, floor // 20 + 1),
        "astral": max(5, (floor - 80) // 15),
        "mythic_crypt": max(6, floor // 10 + 4),
        "mythic_astral": max(7, floor // 10 + 5),
    }.get(kind, 1)
    gold = random.randint(base_gold, max(base_gold, int(round(base_gold * 1.5))))

    items = []
    # Fragmenty Duszy są użyteczne na każdym etapie.
    if "soul_shard" in ITEMS:
        items.extend(["soul_shard"] * random.randint(1, 3))

    consumables = ["healing_potion", "mana_potion", "soul_elixir"]
    if power >= 60:
        consumables += ["greater_healing_potion", "greater_mana_potion", "vitality_elixir"]
    if power >= 120:
        consumables += ["supreme_healing_potion", "supreme_mana_potion", "soul_tonic"]
    if power >= 170:
        consumables += ["astral_restoration_elixir", "eternal_soul_elixir"]
    consumables = [item for item in consumables if item in ITEMS]
    if consumables:
        items.append(random.choice(consumables))

    # Szansa na surowy klejnot odblokowany na poziomie tej zawartości.
    available_gems = [
        f"raw_gem_{definition['key']}"
        for definition in GEM_DEFINITIONS
        if int(definition.get("mining_level", 1)) <= power
        and f"raw_gem_{definition['key']}" in ITEMS
    ]
    if available_gems and random.random() < min(0.55, 0.18 + power / 700.0):
        items.append(random.choice(available_gems))

    # Endgame ma małą szansę na drugi przydatny consumable.
    if power >= 100 and consumables and random.random() < 0.30:
        items.append(random.choice(consumables))

    return {"gold": gold, "items": items}

def normalize_lookup_text(value):
    text = str(value or "").strip().lower()
    text = text.replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(text.split())


# v0.30.8: screen-reader friendly navigation aliases for profession hubs and class EQ shops.
PROFESSION_GUIDE_PRIMARY_ROOMS = {
    "wedkarstwo": "fishing_school", "wędkarstwo": "fishing_school", "fishing": "fishing_school",
    "gornictwo": "miners_guild", "górnictwo": "miners_guild", "mining": "miners_guild",
    "drwalstwo": "forester_lodge", "woodcutting": "forester_lodge",
    "zielarstwo": "herbalism_garden", "herbalism": "herbalism_garden",
    "kowalstwo": "crafting_workshop", "rzemioslo": "crafting_workshop", "rzemiosło": "crafting_workshop", "crafting": "crafting_workshop",
    "gotowanie": "blue_flame_kitchen", "cooking": "blue_flame_kitchen",
    "alchemia": "alchemy_lab", "alchemy": "alchemy_lab",
    "jubilerstwo": "jeweler_workshop", "jewelcrafting": "jeweler_workshop",
}
for _profession_alias, _profession_room in PROFESSION_GUIDE_PRIMARY_ROOMS.items():
    GUIDE_DESTINATION_ALIASES[normalize_lookup_text(f"profesje {_profession_alias}")] = _profession_room
    GUIDE_DESTINATION_ALIASES[normalize_lookup_text(f"profesja {_profession_alias}")] = _profession_room

for _eq_room, _eq_classes in CLASS_SHOP_CLASSES_BY_ROOM.items():
    for _eq_class in _eq_classes:
        for _eq_prefix in ("eq", "sklep eq", "sklep z eq", "ekwipunek"):
            GUIDE_DESTINATION_ALIASES[normalize_lookup_text(f"{_eq_prefix} {_eq_class}")] = _eq_room


def find_by_name(mapping, query, name_field="name"):
    q = normalize_lookup_text(query)
    if not q:
        return None
    exact = []
    partial = []
    for key, value in mapping.items():
        key_name = normalize_lookup_text(key)
        name = normalize_lookup_text(value[name_field])
        aliases = [
            normalize_lookup_text(alias)
            for alias in (value.get("aliases") or ())
            if str(alias or "").strip()
        ]
        if q == key_name or q == name or q in aliases:
            exact.append((key, value))
        elif (
            q in name or q in key_name or
            any(q in alias for alias in aliases)
        ):
            partial.append((key, value))
    if exact:
        return exact[0]
    if len(partial) == 1:
        return partial[0]
    return None


def canonical_profession_resource_id(item_id):
    """v0.8.70: zwraca bazowy zasób profesji dla postępu questów.

    Rzadki wariant ryby/drewna/zioła nadal pochodzi z konkretnego bazowego
    zasobu, więc quest na ten zasób nie może gubić postępu tylko dlatego,
    że gracz trafił lepszą jakość. Zwykłe i terenowe zasoby zwracają siebie.
    """
    item = ITEMS.get(item_id, {})
    return str(item.get("base_resource_id") or item_id)



# ============================================================
# v0.9.25 - SALVAGE / REFORGE / RUNES / PLAYER GUILDS (internal player_clan schema)
# ============================================================
V0925_SALVAGE_MATERIALS = {
    "iron": ("salvage_iron_scrap", "Odłamek Żelaza"),
    "steel": ("salvage_steel_scrap", "Odłamek Stali"),
    "mithril": ("salvage_mithril_fragment", "Fragment Mithrilu"),
    "adamantite": ("salvage_adamantite_fragment", "Fragment Adamantytu"),
    "cobalt": ("salvage_cobalt_fragment", "Fragment Kobaltu"),
    "runic": ("salvage_runic_fragment", "Runiczny Fragment"),
    "dragonsteel": ("salvage_dragonsteel_fragment", "Fragment Smoczej Stali"),
    "astral": ("salvage_astral_fragment", "Astralny Fragment"),
    "void": ("salvage_void_fragment", "Fragment Pustki"),
    "eternium": ("salvage_eternium_fragment", "Fragment Eternium"),
}
for _mat_key, (_iid, _iname) in V0925_SALVAGE_MATERIALS.items():
    ITEMS[_iid] = {
        "name": _iname, "type": "craft_material", "price": None,
        "craftbox_category": "salvage",
        "desc": "Materiał odzyskany przez rozkładanie niepotrzebnego EQ u Haldora.",
    }
ITEMS["reforge_essence"] = {
    "name": "Esencja Przekucia", "type": "craft_material", "price": None,
    "craftbox_category": "salvage",
    "desc": "Esencja używana przez Haldora do zmiany jednego bonusu EQ.",
}
ITEMS["rune_dust"] = {
    "name": "Pył Runiczny", "type": "craft_material", "price": None,
    "craftbox_category": "runes",
    "desc": "Pył odzyskiwany z wysokopoziomowego EQ; służy do tworzenia run.",
}
V0925_RUNES = {
    "moc": ("rune_power", "Runa Mocy", {"all_damage_pct": 2}),
    "ochrona": ("rune_guard", "Runa Ochrony", {"physical_defense_pct": 2, "magic_defense_pct": 2}),
    "zycie": ("rune_vitality", "Runa Życia", {"max_hp_pct": 3}),
    "mana": ("rune_focus", "Runa Skupienia", {"max_mana_pct": 3}),
    "unik": ("rune_agility", "Runa Zwinności", {"dodge_pct": 1}),
    "hart": ("rune_fortitude", "Runa Hartu", {"constitution": 1, "willpower": 1}),
}
V0925_RUNE_BY_ID = {}
for _rkey, (_rid, _rname, _effects) in V0925_RUNES.items():
    _props = {k:v for k,v in _effects.items() if k.endswith("_pct")}
    _stats = {k:v for k,v in _effects.items() if not k.endswith("_pct")}
    ITEMS[_rid] = {
        "name": _rname, "type": "craft_material", "price": None,
        "craftbox_category": "runes", "rune_key": _rkey,
        "rune_properties": _props, "rune_stats": _stats,
        "desc": "Runę można osadzić w gnieździe endgame EQ; nie zmienia wymogu Biegłości.",
    }
    V0925_RUNE_BY_ID[_rid] = (_rkey, _effects)

CRAFT_MATERIAL_STORAGE_IDS = frozenset(
    set(CRAFT_MATERIAL_STORAGE_IDS)
    | {iid for iid,_name in V0925_SALVAGE_MATERIALS.values()}
    | {"reforge_essence", "rune_dust"}
    | {data[0] for data in V0925_RUNES.values()}
)

V0925_REFORGE_AFFIXES = ("strength", "dexterity", "constitution", "intelligence", "willpower", "hp", "mana")
V0925_AFFIX_PL = {
    "strength":"Siła", "dexterity":"Zręczność", "constitution":"Kondycja",
    "intelligence":"Inteligencja", "willpower":"Siła Woli", "hp":"HP", "mana":"Mana",
}
V0925_MASTERY_MILESTONES = (1, 50, 100, 150, 200, 250, 300, 350, 400)

def v0925_item_material_key(item):
    key = str(item.get("corpse_material") or item.get("blacksmith_material") or "").strip()
    if key in V0925_SALVAGE_MATERIALS:
        return key
    name = normalize_lookup_text(item.get("name", ""))
    tests = (
        ("eternium","eternium"),("pustk","void"),("astral","astral"),
        ("smocz","dragonsteel"),("runicz","runic"),("kobalt","cobalt"),
        ("adamant","adamantite"),("mithril","mithril"),("stal","steel"),("zelaz","iron"),
    )
    for text,key in tests:
        if text in name:
            return key
    return "iron"

def v03041_salvage_material_key(item):
    """v0.30.41: każde armor daje materiał adekwatny do realnego poziomu EQ.

    Jawny materiał (drop z ciała/Kowalstwo/nazwa) ma pierwszeństwo.
    Klasowe, bossowe, setowe, kryptowe, astralne i inne EQ bez jawnej
    nazwy materiału mapuje się po wymaganym Levelu postaci na tę samą
    drabinkę materiałów co późne dropy mobów.
    """
    explicit = str(item.get("corpse_material") or item.get("blacksmith_material") or "").strip()
    if explicit in V0925_SALVAGE_MATERIALS:
        return explicit
    name = normalize_lookup_text(item.get("name", ""))
    tests = (
        ("eternium","eternium"),("pustk","void"),("astral","astral"),
        ("smocz","dragonsteel"),("runicz","runic"),("kobalt","cobalt"),
        ("adamant","adamantite"),("mithril","mithril"),("stal","steel"),("zelaz","iron"),
    )
    for marker, key in tests:
        if marker in name:
            return key
    level = max(1, min(400, int(
        item.get("required_character_level", item.get("required_mastery", 1)) or 1
    )))
    if level >= 360: return "eternium"
    if level >= 320: return "void"
    if level >= 280: return "astral"
    if level >= 240: return "dragonsteel"
    if level >= 200: return "runic"
    if level >= 160: return "cobalt"
    if level >= 120: return "adamantite"
    if level >= 80: return "mithril"
    if level >= 40: return "steel"
    return "iron"

# ============================================================
# v0.30.42 - KOWALSTWO: ULEPSZANIE KAŻDEGO EQ +1..+10
# ============================================================
V03042_EQ_UPGRADE_MAX = 10
V03042_UPGRADE_STAT_STEP = 2
V03042_UPGRADE_SLOT_FALLBACK_STAT = {
    "head": "willpower", "body": "constitution", "hands": "strength",
    "legs": "constitution", "feet": "dexterity", "charm": "willpower",
    "ring": "dexterity", "necklace": "intelligence", "earring": "intelligence",
    "shoulders": "strength", "belt": "constitution", "cloak": "dexterity",
    "bracers": "strength", "relic": "willpower",
}
V03042_MAIN_STATS = ("strength", "dexterity", "constitution", "intelligence", "willpower")

def v03042_equipment_level(item):
    return max(1, min(400, int(
        item.get("required_character_level", item.get("required_mastery", 1)) or 1
    )))

def v03042_upgrade_required_smithing(item, target_upgrade):
    target_upgrade = max(1, min(V03042_EQ_UPGRADE_MAX, int(target_upgrade)))
    return min(400, v03042_equipment_level(item) + (target_upgrade - 1) * 5)

def v03042_upgrade_material_cost(item, target_upgrade):
    target_upgrade = max(1, min(V03042_EQ_UPGRADE_MAX, int(target_upgrade)))
    level = v03042_equipment_level(item)
    rarity_bonus = {
        "common": 0, "crafted": 0, "uncommon": 0, "rare": 1, "epic": 1,
        "legendary": 2, "mythic": 3, "unique": 3, "eternal": 4,
    }.get(str(item.get("rarity") or "common").lower(), 0)
    return max(1, 1 + target_upgrade + level // 100 + rarity_bonus)

def v03042_upgrade_defense_bonus(item, upgrade_level):
    upgrade_level = max(0, min(V03042_EQ_UPGRADE_MAX, int(upgrade_level)))
    if upgrade_level <= 0:
        return 0
    base = max(0, int(item.get("defense", 0) or 0))
    return max(1, int(math.ceil(base * 0.02 * upgrade_level)) + upgrade_level // 2)

def v03042_upgrade_primary_stat(item, effective_affix=None):
    if effective_affix in V03042_MAIN_STATS:
        return str(effective_affix)
    base_affix = str(item.get("affix") or "")
    if base_affix in V03042_MAIN_STATS:
        return base_affix
    stats = {
        str(k): int(v or 0) for k, v in (item.get("stats") or {}).items()
        if str(k) in V03042_MAIN_STATS and int(v or 0) > 0
    }
    if stats:
        return max(stats, key=lambda key: (stats[key], -V03042_MAIN_STATS.index(key)))
    return V03042_UPGRADE_SLOT_FALLBACK_STAT.get(str(item.get("slot") or ""), "constitution")

def v03042_upgrade_stat_bonus(upgrade_level):
    upgrade_level = max(0, min(V03042_EQ_UPGRADE_MAX, int(upgrade_level)))
    return upgrade_level // V03042_UPGRADE_STAT_STEP

def v03042_upgraded_display_name(item_name, upgrade_level):
    upgrade_level = max(0, min(V03042_EQ_UPGRADE_MAX, int(upgrade_level)))
    return f"{item_name} [+{upgrade_level}]" if upgrade_level > 0 else str(item_name)


def v0925_equipment_socket_count(item):
    mastery = int(item.get("required_mastery", 1) or 1)
    if mastery >= 400: return 3
    if mastery >= 300: return 2
    if mastery >= 200: return 1
    return 0

def v0925_craftbox_category(item_id):
    item = ITEMS.get(item_id, {})
    explicit = item.get("craftbox_category")
    if explicit:
        return explicit
    if item_id in CUT_GEM_IDS or item.get("jewelcraft_level"):
        return "jewelcrafting"
    text = normalize_lookup_text(item.get("name", ""))
    if item.get("blacksmith_material") or item.get("blacksmith_tier") or item_id.startswith("ingot_") or "sztabka" in text or "plyta" in text:
        return "blacksmithing"
    if any(x in text for x in ("esencja", "ekstrakt", "proszek alchem", "destylat")):
        return "alchemy"
    return "other"

V0925_CRAFTBOX_CATEGORIES = {
    "blacksmithing": "Kowalstwo",
    "jewelcrafting": "Jubilerstwo",
    "alchemy": "Alchemia",
    "runes": "Runy",
    "salvage": "Materiały z Salvage",
    "other": "Pozostałe materiały",
}
V0925_CRAFTBOX_ALIASES = {
    "kowalstwo":"blacksmithing", "kowal":"blacksmithing", "blacksmithing":"blacksmithing",
    "jubilerstwo":"jewelcrafting", "jubilerskie":"jewelcrafting", "jewelry":"jewelcrafting",
    "alchemia":"alchemy", "alchemy":"alchemy",
    "runy":"runes", "runes":"runes",
    "salvage":"salvage", "odzysk":"salvage", "odzyskane":"salvage",
    "inne":"other", "pozostale":"other", "pozostałe":"other",
}


# ============================================================
# v0.9.26 - GILDIA GRACZY: SKARBIEC / ROZWÓJ / RANGI
# ============================================================
V0926_GUILD_MAX_LEVEL = 100
V0926_GUILD_DEFAULT_ROLES = {
    "member": {
        "name": "Członek", "priority": 10,
        "withdraw_money": 0, "withdraw_items": 0,
        "invite": 0, "kick": 0,
    },
    "officer": {
        "name": "Oficer", "priority": 100,
        "withdraw_money": 0, "withdraw_items": 1,
        "invite": 1, "kick": 1,
    },
}
V0926_GUILD_PERMISSION_ALIASES = {
    "wyplata": "withdraw_money", "wyplaty": "withdraw_money", "wypłata": "withdraw_money", "wypłaty": "withdraw_money",
    "withdraw": "withdraw_money", "withdrawmoney": "withdraw_money", "money": "withdraw_money",
    "przedmioty": "withdraw_items", "itemy": "withdraw_items", "items": "withdraw_items", "bank": "withdraw_items",
    "zapraszanie": "invite", "zaproszenia": "invite", "invite": "invite",
    "wyrzucanie": "kick", "wyrzuc": "kick", "kick": "kick",
}
V0926_GUILD_PERMISSION_LABELS = {
    "withdraw_money": "wypłata pieniędzy",
    "withdraw_items": "wypłata przedmiotów",
    "invite": "zapraszanie",
    "kick": "wyrzucanie niższych rang",
}

def v0926_guild_upgrade_cost(current_level):
    """Generator Core: koszt rozwoju Gildii bez ręcznej tabeli per poziom."""
    level=max(1,min(V0926_GUILD_MAX_LEVEL,int(current_level or 1)))
    if level >= V0926_GUILD_MAX_LEVEL:
        return 0
    stage=generator_core_v027.stage_from_index(level+1,V0926_GUILD_MAX_LEVEL)
    return generator_core_v027.system_cost(stage,"guild-level",300.0)


def v0926_guild_bonus_percent(level):
    level=max(1,min(V0926_GUILD_MAX_LEVEL,int(level or 1)))
    return generator_core_v027.guild_bonus_percent(level,V0926_GUILD_MAX_LEVEL)


def v0926_bool_word(value):
    return "tak" if int(value or 0) else "nie"


# ============================================================
# v0.9.27 - SIEDZIBA GILDII / KONTRAKTY / BOSSOWIE / ELITY
# ============================================================
V0927_GUILD_HALL_MAX_LEVEL = 10
V0927_GUILD_BUILDINGS = {
    "forge": ("Kuźnia", "kowal", "forge"),
    "treasury": ("Skarbiec", "skarbiec", "treasury"),
    "library": ("Biblioteka", "biblioteka", "library"),
    "training": ("Sala Treningowa", "trening", "training"),
}
def v0927_guild_hall_upgrade_cost(current_level):
    level=max(1,min(V0927_GUILD_HALL_MAX_LEVEL,int(current_level or 1)))
    if level>=V0927_GUILD_HALL_MAX_LEVEL:
        return 0
    stage=generator_core_v027.stage_from_index(level+1,V0927_GUILD_HALL_MAX_LEVEL)
    return generator_core_v027.system_cost(stage,"guild-hall",500.0)

def v0927_guild_building_upgrade_cost(current_level):
    level=max(0,min(V0927_GUILD_HALL_MAX_LEVEL,int(current_level or 0)))
    if level>=V0927_GUILD_HALL_MAX_LEVEL:
        return 0
    stage=generator_core_v027.stage_from_index(level+1,V0927_GUILD_HALL_MAX_LEVEL)
    return generator_core_v027.system_cost(stage,"guild-building",150.0)

# Tożsamość kontraktów jest treścią; cele, nagrody i cooldown wylicza Generator Core.
V0927_GUILD_CONTRACTS = {
    "hunt100": {"name":"Wspólne Polowanie", "kind":"kills"},
    "boss5": {"name":"Piątka Bossów", "kind":"bosses"},
    "rune20": {"name":"Dostawa Pyłu Runicznego", "kind":"material", "item_id":"rune_dust"},
}
for _contract_id,_contract in V0927_GUILD_CONTRACTS.items():
    _kind=_contract["kind"]
    _stage=1+int(generator_core_v027.stable_unit("guild-contract:"+_contract_id)*399)
    _contract["generator_level"]=_stage
    if _kind=="kills":
        _contract["need"]=generator_core_v027.generated_count(_stage,_contract_id,40,120)
    elif _kind=="bosses":
        _contract["need"]=generator_core_v027.generated_count(_stage,_contract_id,3,10)
    else:
        _contract["need"]=generator_core_v027.generated_count(_stage,_contract_id,10,35)
    _contract["reward"]=generator_core_v027.system_reward(_stage,"guild-contract:"+_contract_id,max(4.0,_contract["need"]*.65))
    _contract["cooldown"]=generator_core_v027.generated_cooldown_seconds(_stage,"guild-contract:"+_contract_id,3600,21600)

def v0927_guild_contract_ready_text(ready_at):
    now=int(time.time()); ready=max(0,int(ready_at or 0)-now)
    if ready<=0: return "aktywny"
    return f"odnowi się za {max(1,(ready+59)//60)} min"

V0927_GUILD_BOSS_NAMES = (
    "Strażnik Żelaznej Pieczęci",
    "Koloss Runicznej Bramy",
    "Astralny Archont Gildii",
    "Pradawny Władca Siedziby",
)

def v0927_guild_boss_name(hall_level):
    level=max(1,min(V0927_GUILD_HALL_MAX_LEVEL,int(hall_level or 1)))
    idx=0 if len(V0927_GUILD_BOSS_NAMES)<=1 else int(round((level-1)*(len(V0927_GUILD_BOSS_NAMES)-1)/max(1,V0927_GUILD_HALL_MAX_LEVEL-1)))
    return V0927_GUILD_BOSS_NAMES[max(0,min(len(V0927_GUILD_BOSS_NAMES)-1,idx))]

# ---- v0.9.29: osiem godzinnych questów odnawialnych ----
V0929_HOURLY_QUEST_COOLDOWN = 60 * 60

# Przedmioty questowe wypadają wyłącznie podczas aktywnego zlecenia.
ITEMS.update({
    "damaged_weapon_v0929": {
        "name": "Uszkodzone Ostrze", "type": "quest", "price": None,
        "desc": "Pęknięta broń zabrana szkieletowi lub strażnikowi podczas zlecenia Haldora.",
    },
    "heavy_armor_fragment_v0929": {
        "name": "Fragment Ciężkiego Pancerza", "type": "quest", "price": None,
        "desc": "Ciężki fragment opancerzenia odzyskany z potężnego przeciwnika dla Haldora.",
    },
    "toxic_gland_v0929": {
        "name": "Toksyczny Gruczoł", "type": "quest", "price": None,
        "desc": "Gruczoł z jadowitej lub skażonej istoty potrzebny Orinowi do badań alchemicznych.",
    },
})

# Ryby rzeczne obejmują bazowe gatunki i ich rzadkie warianty.
V0929_RIVER_FISH_STORAGE_IDS = {
    item_id for item_id in FISH_STORAGE_IDS
    if base_fish_species_id(item_id) in RIVER_FISH_ATLAS
}

QUESTS.update({
    "haldor_broken_blades_v0929": {
        "name": "Złamane ostrza",
        "giver": "Mistrz Rzemiosła Haldor",
        "kind": "collect",
        "target": "damaged_weapon_v0929",
        "needed": 6,
        "progress_label": "Uszkodzone Ostrza",
        "description": (
            "Zdobądź po przyjęciu zlecenia 6 Uszkodzonych Ostrzy z uzbrojonych "
            "nieumarłych Starego Cmentarza, szkieletów, strażników lub rycerzy i przynieś je Haldorowi. "
            "Każdy kwalifikujący się kill daje 1 ostrze i od razu zwiększa postęp 0/6."
        ),
        "required_profession": "Kowalstwo",
        "min_profession_level": 1,
        "reward_profession": "Kowalstwo",
        "reward_profession_xp": 1100,
        "reward_tool_type": "crafting",
        "reward_tool_xp": 850,
        "reward_silver": 800, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
    "haldor_armor_recycling_v0929": {
        "name": "Pancerz do przetopu",
        "giver": "Mistrz Rzemiosła Haldor",
        "kind": "collect",
        "target": "heavy_armor_fragment_v0929",
        "needed": 6,
        "progress_label": "Fragmenty Ciężkiego Pancerza",
        "description": (
            "Zdobądź po przyjęciu zlecenia 6 Fragmentów Ciężkiego Pancerza z ciężkich "
            "fizycznych przeciwników i przynieś je Haldorowi do przetopu."
        ),
        "required_profession": "Kowalstwo",
        "min_profession_level": 1,
        "reward_profession": "Kowalstwo",
        "reward_profession_xp": 1300,
        "reward_tool_type": "crafting",
        "reward_tool_xp": 1000,
        "reward_silver": 1000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
    "orin_toxic_glands_v0929": {
        "name": "Toksyczne gruczoły",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "target": "toxic_gland_v0929",
        "needed": 10,
        "progress_label": "Toksyczne Gruczoły",
        "description": (
            "Zdobądź po przyjęciu zadania 10 Toksycznych Gruczołów z jadowitych, "
            "skażonych albo Toksycznych elit i przynieś je Orinowi."
        ),
        "required_profession": "Alchemia",
        "min_profession_level": 1,
        "reward_profession": "Alchemia",
        "reward_profession_xp": 1000,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 800,
        "reward_silver": 900, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
    "borys_daily_catch_v0929": {
        "name": "Dzisiejszy połów",
        "giver": "Rybak Borys",
        "kind": "collect_category",
        "target": "fish_river",
        "needed": 15,
        "description": (
            "Złów po przyjęciu zadania 15 ryb rzecznych i przynieś je Rybakowi Borysowi. "
            "Liczą się również rzadkie warianty gatunków rzecznych."
        ),
        "required_profession": "Wędkarstwo",
        "min_profession_level": 1,
        "reward_profession": "Wędkarstwo",
        "reward_profession_xp": 700,
        "reward_tool_type": "fishing",
        "reward_tool_xp": 600,
        "reward_silver": 400, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
    "toren_ore_samples_v0929": {
        "name": "Próbki rudy",
        "giver": "Górnik Toren",
        "kind": "collect_resource_set",
        "resource_targets": {"copper_ore": 5, "iron_ore": 5, "silver_ore": 5},
        "needed": 15,
        "description": (
            "Wydobądź po przyjęciu zadania po 5 sztuk trzech rud: Ruda miedzi 5, "
            "Ruda żelaza 5 i Ruda srebra 5. Każdy rodzaj ma własny licznik."
        ),
        "required_profession": "Górnictwo",
        "min_profession_level": 10,
        "reward_profession": "Górnictwo",
        "reward_profession_xp": 900,
        "reward_tool_type": "mining",
        "reward_tool_xp": 800,
        "reward_silver": 750, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
    "bran_repair_wood_v0929": {
        "name": "Drewno na naprawy",
        "giver": "Drwal Bran",
        "kind": "collect_category",
        "target": "wood",
        "needed": 25,
        "description": "Zetnij po przyjęciu zadania 25 sztuk dowolnego drewna i przynieś je Drwalowi Branowi na naprawy.",
        "required_profession": "Drwalstwo",
        "min_profession_level": 1,
        "reward_profession": "Drwalstwo",
        "reward_profession_xp": 800,
        "reward_tool_type": "woodcutting",
        "reward_tool_xp": 700,
        "reward_silver": 450, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
    "liora_healer_bundle_v0929": {
        "name": "Zestaw dla uzdrowiciela",
        "giver": "Zielarka Liora",
        "kind": "collect_category",
        "target": "herb",
        "needed": 20,
        "description": (
            "Zbierz po przyjęciu zadania 20 dowolnych ziół dla uzdrowiciela. "
            "Zioła mogą pochodzić z różnych regionów; liczy się nowy zbiór po przyjęciu."
        ),
        "required_profession": "Zielarstwo",
        "min_profession_level": 1,
        "reward_profession": "Zielarstwo",
        "reward_profession_xp": 750,
        "reward_tool_type": "herbalism",
        "reward_tool_xp": 650,
        "reward_silver": 450, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
    "cemetery_undead_rising_v0929": {
        "name": "Nieumarli znów wstali",
        "giver": "Strażnik Starego Cmentarza",
        "kind": "kill",
        "target": "cemetery_undead_v0929",
        "needed": 25,
        "description": (
            "Pokonaj po przyjęciu zadania 25 nieumarłych ze Starego Cmentarza: "
            "Niespokojnych Zmarłych, szkielety, Zbieraczy Kości lub Upiory Martwego Dzwonu."
        ),
        "reward_stat_progress": 180,
        "reward_soul_xp": 300,
        "reward_silver": 650, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True, "repeat_cooldown": V0929_HOURLY_QUEST_COOLDOWN,
    },
})

# Dodatkowy NPC stoi bezpośrednio przy wejściu na Stary Cmentarz.
NPCS["cemetery_watchman_v0929"] = {
    "name": "Strażnik Starego Cmentarza",
    "room": "graveyard",
    "dialogue": (
        "Nieumarli znowu wychodzą z grobów. Jeśli oczyścisz teren, zapłacę za patrol. "
        "Zlecenie odnawia się co godzinę."
    ),
    "quest": "cemetery_undead_rising_v0929",
}

# Haldor i Orin pokazują nowe zlecenia również w swoich jawnych listach specjalisty.
def _v0929_append_specialist_quests(npc_id, *quest_ids):
    npc = NPCS.get(npc_id)
    if not npc:
        return
    current = list(npc.get("specialist_quests") or ())
    for quest_id in quest_ids:
        if quest_id not in current:
            current.append(quest_id)
    npc["specialist_quests"] = tuple(current)

_v0929_append_specialist_quests(
    "specialist_crafting",
    "haldor_broken_blades_v0929",
    "haldor_armor_recycling_v0929",
)
_v0929_append_specialist_quests("specialist_alchemy", "orin_toxic_glands_v0929")

# Cmentarne typy zaliczają jeden wspólny kill-target.
for _mid in (
    "cemetery_restless_dead",
    "cemetery_bone_collector",
    "cemetery_bell_wraith",
    "cemetery_steel_skeleton",
):
    if _mid in MOB_TEMPLATES:
        _tags = list(MOB_TEMPLATES[_mid].get("quest_targets") or ())
        if "cemetery_undead_v0929" not in _tags:
            _tags.append("cemetery_undead_v0929")
        MOB_TEMPLATES[_mid]["quest_targets"] = tuple(_tags)

V03035_BROKEN_BLADE_SOURCES = frozenset({
    "cemetery_restless_dead",
    "cemetery_bone_collector",
    "cemetery_bell_wraith",
    "cemetery_steel_skeleton",
    "cemetery_crypt_reaper",
    "cemetery_mourning_knight",
    "cemetery_keeper",
})

def v0929_kill_drop_item(quest_id, mob_template_id, template):
    """Quest-only drop. Zwraca item_id albo None."""
    name = normalize_lookup_text(template.get("name", ""))
    if quest_id == "haldor_broken_blades_v0929":
        # v0.30.35: jawne źródła na Starym Cmentarzu + kompatybilny fallback
        # dla innych szkieletów/strażników. Nie zależymy już tylko od nazwy moba.
        base_id = str(template.get("base_template") or mob_template_id)
        if (
            str(mob_template_id) in V03035_BROKEN_BLADE_SOURCES
            or base_id in V03035_BROKEN_BLADE_SOURCES
            or "szkielet" in name
            or "straznik" in name
            or "rycerz" in name
        ):
            return "damaged_weapon_v0929"
    elif quest_id == "haldor_armor_recycling_v0929":
        heavy_keywords = ("opancerz", "rycerz", "golem", "troll wojenny", "zelaznoskory", "kolos")
        if (
            template.get("damage_type") == "physical"
            and (int(template.get("max_hp", 0) or 0) >= 650 or any(k in name for k in heavy_keywords))
        ):
            return "heavy_armor_fragment_v0929"
    elif quest_id == "orin_toxic_glands_v0929":
        toxic_keywords = ("zarazy", "szlam", "waz", "skorpion", "hydra", "bagien", "toksycz")
        if template.get("elite_affix") == "toxic" or any(k in name for k in toxic_keywords):
            return "toxic_gland_v0929"
    return None

HELP_TOPICS["questy godzinne"] = [
    "v0.9.29 dodaje 8 niezależnych zadań odnawianych co 60 minut. Każde zaczyna od 0/x i liczy wyłącznie zdarzenia po przyjęciu.",
    "Haldor: Złamane ostrza 0/6 oraz Pancerz do przetopu 0/6. Oba mogą być aktywne jednocześnie z innymi zleceniami Haldora.",
    "Orin: Toksyczne gruczoły 0/10 z jadowitych/skażonych mobów albo elit z affixem Toksyczny.",
    "Borys: Dzisiejszy połów 0/15 — tylko ryby rzeczne; Bran: Drewno na naprawy 0/25; Liora: Zestaw dla uzdrowiciela 0/20.",
    "Toren: Próbki rudy — osobno Ruda miedzi 0/5, Ruda żelaza 0/5 i Ruda srebra 0/5; wymagane Górnictwo 10.",
    "Strażnik Starego Cmentarza: Nieumarli znów wstali 0/25. Quest daje EXP każdej statystyki i Soul XP jak inne questy walki.",
]
HELP_TOPICS.setdefault("quest", []).append(
    "v0.9.29: help questy godzinne opisuje 8 nowych odnawialnych zadań profesyjnych i cmentarnych."
)


class Database:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_schema()
        self.migrate_schema()

    def create_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS account_characters (
                master_account_id INTEGER NOT NULL,
                character_account_id INTEGER NOT NULL UNIQUE,
                slot INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(master_account_id, slot),
                FOREIGN KEY(master_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                FOREIGN KEY(character_account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS account_wallet (
                master_account_id INTEGER PRIMARY KEY,
                silver INTEGER NOT NULL DEFAULT 0,
                gold INTEGER NOT NULL DEFAULT 0,
                mithril INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(master_account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS characters (
                account_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name_nom TEXT NOT NULL DEFAULT '',
                name_gen TEXT NOT NULL DEFAULT '',
                name_dat TEXT NOT NULL DEFAULT '',
                name_acc TEXT NOT NULL DEFAULT '',
                name_ins TEXT NOT NULL DEFAULT '',
                name_loc TEXT NOT NULL DEFAULT '',
                name_voc TEXT NOT NULL DEFAULT '',
                race TEXT NOT NULL,
                class_name TEXT NOT NULL,
                class_type TEXT NOT NULL,
                soul_weapon TEXT NOT NULL,
                weapon_base INTEGER NOT NULL,
                strength INTEGER NOT NULL,
                dexterity INTEGER NOT NULL,
                constitution INTEGER NOT NULL,
                intelligence INTEGER NOT NULL,
                willpower INTEGER NOT NULL,
                stat_progress INTEGER NOT NULL DEFAULT 0,
                strength_progress INTEGER NOT NULL DEFAULT 0,
                dexterity_progress INTEGER NOT NULL DEFAULT 0,
                constitution_progress INTEGER NOT NULL DEFAULT 0,
                intelligence_progress INTEGER NOT NULL DEFAULT 0,
                willpower_progress INTEGER NOT NULL DEFAULT 0,
                charisma_progress INTEGER NOT NULL DEFAULT 0,
                soul_level INTEGER NOT NULL DEFAULT 1,
                soul_xp INTEGER NOT NULL DEFAULT 0,
                soul_tier INTEGER NOT NULL DEFAULT 1,
                room_id TEXT NOT NULL DEFAULT 'square',
                silver INTEGER NOT NULL DEFAULT 250,
                gold INTEGER NOT NULL DEFAULT 2,
                mithril INTEGER NOT NULL DEFAULT 0,
                charisma INTEGER NOT NULL DEFAULT 10,
                character_level INTEGER NOT NULL DEFAULT 1,
                character_xp INTEGER NOT NULL DEFAULT 0,
                deaths INTEGER NOT NULL DEFAULT 0,
                crypt_checkpoint INTEGER NOT NULL DEFAULT 0,
                guild_reputation_json TEXT NOT NULL DEFAULT '{}',
                guild_exams_json TEXT NOT NULL DEFAULT '{}',
                guild_class_quests_json TEXT NOT NULL DEFAULT '{}',
                guild_bounty_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS inventory (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment (
                account_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                item_id TEXT NOT NULL,
                PRIMARY KEY(account_id, slot),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment_gems (
                account_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                socket_index INTEGER NOT NULL,
                jewelry_item_id TEXT NOT NULL,
                gem_id TEXT NOT NULL,
                PRIMARY KEY(account_id, slot, socket_index),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quests (
                account_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                progress INTEGER NOT NULL DEFAULT 0,
                completed_at INTEGER NOT NULL DEFAULT 0,
                completion_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, quest_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quest_resource_progress_v0929 (
                account_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, quest_id, target_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS professions (
                account_id INTEGER NOT NULL,
                profession TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                actions INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, profession),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tools (
                account_id INTEGER NOT NULL,
                tool_type TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                uses INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, tool_type),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS profession_storage (
                account_id INTEGER NOT NULL,
                container TEXT NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, container,item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bank_balances (
                account_id INTEGER PRIMARY KEY,
                silver INTEGER NOT NULL DEFAULT 0,
                gold INTEGER NOT NULL DEFAULT 0,
                mithril INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bank_items (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id,item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_friends_v0928 (
                account_id INTEGER NOT NULL,
                friend_account_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, friend_account_id),
                CHECK(account_id <> friend_account_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                FOREIGN KEY(friend_account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_friend_requests_v0928 (
                sender_account_id INTEGER NOT NULL,
                target_account_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(sender_account_id, target_account_id),
                CHECK(sender_account_id <> target_account_id),
                FOREIGN KEY(sender_account_id) REFERENCES accounts(id) ON DELETE CASCADE,
                FOREIGN KEY(target_account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS astral_progress (
                account_id INTEGER PRIMARY KEY,
                checkpoint INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS mine_progress (
                account_id INTEGER PRIMARY KEY,
                max_floor_unlocked INTEGER NOT NULL DEFAULT 1,
                wall_hits INTEGER NOT NULL DEFAULT 0,
                wall_required_hits INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS class_progress (
                account_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                active_slot INTEGER,
                PRIMARY KEY(account_id, class_name),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS learned_skills (
                account_id INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS skill_progress (
                account_id INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                uses INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS skill_queue (
                account_id INTEGER NOT NULL,
                queue_type TEXT NOT NULL,
                position INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                PRIMARY KEY(account_id, queue_type, position),
                UNIQUE(account_id, skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS skill_queue_settings (
                account_id INTEGER PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS combat_log_settings (
                account_id INTEGER PRIMARY KEY,
                mode TEXT NOT NULL DEFAULT 'normal',
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS wimpy_settings (
                account_id INTEGER PRIMARY KEY,
                percent INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exploration_rooms (
                account_id INTEGER NOT NULL,
                room_id TEXT NOT NULL,
                discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, room_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exploration_rewards (
                account_id INTEGER NOT NULL,
                zone TEXT NOT NULL,
                claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, zone),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS collection_codex (
                account_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                entry_id TEXT NOT NULL,
                discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, category, entry_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS nemesis_v029 (
                account_id INTEGER PRIMARY KEY,
                base_template_id TEXT NOT NULL,
                nemesis_name TEXT NOT NULL,
                rank INTEGER NOT NULL DEFAULT 1,
                level INTEGER NOT NULL DEFAULT 1,
                room_id TEXT NOT NULL,
                kills_player INTEGER NOT NULL DEFAULT 1,
                defeats INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bestiary_stats (
                account_id INTEGER NOT NULL,
                mob_template_id TEXT NOT NULL,
                kills INTEGER NOT NULL DEFAULT 0,
                fastest_kill_ms INTEGER,
                first_killed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_killed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, mob_template_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS boss_codex_stats (
                account_id INTEGER NOT NULL,
                boss_id TEXT NOT NULL,
                solo_kills INTEGER NOT NULL DEFAULT 0,
                group_kills INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, boss_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS boss_codex_drops (
                account_id INTEGER NOT NULL,
                boss_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, boss_id, item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS boss_floor_clears (
                account_id INTEGER NOT NULL,
                dungeon_kind TEXT NOT NULL,
                floor INTEGER NOT NULL,
                cleared_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, dungeon_kind, floor),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS achievement_progress (
                account_id INTEGER NOT NULL,
                metric TEXT NOT NULL,
                value INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, metric),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS achievements (
                account_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                name TEXT NOT NULL,
                tier TEXT NOT NULL,
                unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, achievement_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ascension_progress_v021 (
                account_id INTEGER NOT NULL,
                track TEXT NOT NULL,
                rank INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, track),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS world_tier_settings_v021 (
                account_id INTEGER PRIMARY KEY,
                tier INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS endless_gauntlet_progress_v021 (
                account_id INTEGER PRIMARY KEY,
                best_round INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS unlocked_titles (
                account_id INTEGER NOT NULL,
                title_id TEXT NOT NULL,
                title_name TEXT NOT NULL,
                unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, title_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bounty_boards (
                account_id INTEGER PRIMARY KEY,
                offers_json TEXT NOT NULL DEFAULT '[]',
                active_json TEXT NOT NULL DEFAULT '{}',
                completed_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS dynamic_world_quests_v015 (
                account_id INTEGER PRIMARY KEY,
                quest_key TEXT NOT NULL DEFAULT '',
                quest_type TEXT NOT NULL DEFAULT '',
                target TEXT NOT NULL DEFAULT 'any',
                label TEXT NOT NULL DEFAULT '',
                needed INTEGER NOT NULL DEFAULT 0,
                progress INTEGER NOT NULL DEFAULT 0,
                reward_soul_xp INTEGER NOT NULL DEFAULT 0,
                reward_gold INTEGER NOT NULL DEFAULT 0,
                accepted_slot INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS faction_reputation_v016 (
                account_id INTEGER NOT NULL,
                faction_id TEXT NOT NULL,
                reputation INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, faction_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment_reforges (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                affix TEXT NOT NULL,
                affix_amount INTEGER NOT NULL DEFAULT 0,
                rerolls INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id,item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment_upgrades_v03042 (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                upgrade_level INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id,item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment_runes_v0925 (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                socket_index INTEGER NOT NULL,
                rune_id TEXT NOT NULL,
                PRIMARY KEY(account_id,item_id,socket_index),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                owner_account_id INTEGER NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                treasury INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS player_clan_roles (
                clan_id INTEGER NOT NULL,
                role_key TEXT NOT NULL,
                name TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 20,
                withdraw_money INTEGER NOT NULL DEFAULT 0,
                withdraw_items INTEGER NOT NULL DEFAULT 0,
                invite INTEGER NOT NULL DEFAULT 0,
                kick INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(clan_id,role_key),
                UNIQUE(clan_id,name)
            );
            CREATE TABLE IF NOT EXISTS player_clan_members (
                clan_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL UNIQUE,
                rank TEXT NOT NULL DEFAULT 'member',
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(clan_id,account_id)
            );
            CREATE TABLE IF NOT EXISTS player_clan_invites (
                clan_id INTEGER NOT NULL,
                target_account_id INTEGER NOT NULL,
                inviter_account_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(clan_id,target_account_id)
            );
            CREATE TABLE IF NOT EXISTS player_clan_bank (
                clan_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(clan_id,item_id)
            );
            CREATE TABLE IF NOT EXISTS player_clan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER NOT NULL,
                actor_account_id INTEGER NOT NULL DEFAULT 0,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS player_clan_metrics (
                clan_id INTEGER NOT NULL,
                metric TEXT NOT NULL,
                value INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(clan_id,metric)
            );
            CREATE TABLE IF NOT EXISTS player_clan_achievements (
                clan_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                name TEXT NOT NULL,
                unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(clan_id,achievement_id)
            );
            CREATE TABLE IF NOT EXISTS player_guild_halls_v0927 (
                clan_id INTEGER PRIMARY KEY,
                hall_level INTEGER NOT NULL DEFAULT 1,
                forge_level INTEGER NOT NULL DEFAULT 0,
                treasury_level INTEGER NOT NULL DEFAULT 0,
                library_level INTEGER NOT NULL DEFAULT 0,
                training_level INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS player_guild_contracts_v0927 (
                clan_id INTEGER NOT NULL,
                contract_id TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                completed_count INTEGER NOT NULL DEFAULT 0,
                ready_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(clan_id,contract_id)
            );
            CREATE TABLE IF NOT EXISTS player_guild_boss_records_v0927 (
                clan_id INTEGER PRIMARY KEY,
                kills INTEGER NOT NULL DEFAULT 0,
                fastest_kill_ms INTEGER,
                last_boss_name TEXT NOT NULL DEFAULT '',
                last_killed_at TEXT,
                last_summoned_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS player_guild_trophies_v0927 (
                clan_id INTEGER NOT NULL,
                trophy_id TEXT NOT NULL,
                name TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(clan_id,trophy_id)
            );

            CREATE TABLE IF NOT EXISTS lifetime_statistics (
                account_id INTEGER NOT NULL,
                stat_key TEXT NOT NULL,
                value INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, stat_key),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS fish_journal (
                account_id INTEGER NOT NULL,
                fish_id TEXT NOT NULL,
                caught_count INTEGER NOT NULL DEFAULT 0,
                best_length_mm INTEGER NOT NULL DEFAULT 0,
                best_weight_g INTEGER NOT NULL DEFAULT 0,
                first_room_id TEXT NOT NULL DEFAULT '',
                last_room_id TEXT NOT NULL DEFAULT '',
                first_caught_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_caught_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, fish_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS fish_global_records_v022 (
                fish_id TEXT PRIMARY KEY,
                best_length_mm INTEGER NOT NULL DEFAULT 0,
                length_holder TEXT NOT NULL DEFAULT '',
                best_weight_g INTEGER NOT NULL DEFAULT 0,
                weight_holder TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS fish_rarest_record_v022 (
                record_key TEXT PRIMARY KEY,
                rarity_score INTEGER NOT NULL DEFAULT 0,
                fish_id TEXT NOT NULL DEFAULT '',
                item_id TEXT NOT NULL DEFAULT '',
                holder_name TEXT NOT NULL DEFAULT '',
                length_mm INTEGER NOT NULL DEFAULT 0,
                weight_g INTEGER NOT NULL DEFAULT 0,
                rarity_label TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS world_projects_v022 (
                project_id TEXT PRIMARY KEY,
                progress_json TEXT NOT NULL DEFAULT '{}',
                completed INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS world_project_contributions_v022 (
                project_id TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                points INTEGER NOT NULL DEFAULT 0,
                resources_json TEXT NOT NULL DEFAULT '{}',
                coins INTEGER NOT NULL DEFAULT 0,
                reward_claimed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(project_id,account_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS legendary_contracts_v022 (
                account_id INTEGER PRIMARY KEY,
                offers_json TEXT NOT NULL DEFAULT '[]',
                active_json TEXT NOT NULL DEFAULT '{}',
                completed_count INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS drop_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                zone TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS treasure_chest_cooldowns (
                account_id INTEGER NOT NULL,
                room_id TEXT NOT NULL,
                opened_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, room_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS instance_map_progress (
                account_id INTEGER NOT NULL,
                instance_kind TEXT NOT NULL,
                floor INTEGER NOT NULL,
                first_visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, instance_kind, floor),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS instance_map_secrets (
                account_id INTEGER NOT NULL,
                instance_kind TEXT NOT NULL,
                floor INTEGER NOT NULL,
                secret_name TEXT NOT NULL,
                discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, instance_kind, floor),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS instance_map_checkpoints (
                account_id INTEGER NOT NULL,
                instance_kind TEXT NOT NULL,
                floor INTEGER NOT NULL,
                unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, instance_kind, floor),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    def migrate_schema(self):
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(characters)")}
        _v027_character_level_new = "character_level" not in cols
        additions = {
            "silver": "INTEGER NOT NULL DEFAULT 30",
            "gold": "INTEGER NOT NULL DEFAULT 2",
            "mithril": "INTEGER NOT NULL DEFAULT 0",
            "charisma": "INTEGER NOT NULL DEFAULT 10",
            "character_level": "INTEGER NOT NULL DEFAULT 1",
            "character_xp": "INTEGER NOT NULL DEFAULT 0",
            "deaths": "INTEGER NOT NULL DEFAULT 0",
            "crypt_checkpoint": "INTEGER NOT NULL DEFAULT 0",
            "name_nom": "TEXT NOT NULL DEFAULT ''",
            "name_gen": "TEXT NOT NULL DEFAULT ''",
            "name_dat": "TEXT NOT NULL DEFAULT ''",
            "name_acc": "TEXT NOT NULL DEFAULT ''",
            "name_ins": "TEXT NOT NULL DEFAULT ''",
            "name_loc": "TEXT NOT NULL DEFAULT ''",
            "name_voc": "TEXT NOT NULL DEFAULT ''",
            "guild_reputation_json": "TEXT NOT NULL DEFAULT '{}'",
            "guild_exams_json": "TEXT NOT NULL DEFAULT '{}'",
            "guild_class_quests_json": "TEXT NOT NULL DEFAULT '{}'",
            "guild_bounty_json": "TEXT NOT NULL DEFAULT '{}'",
            "loot_filter": "TEXT NOT NULL DEFAULT 'all'",
            "active_title": "TEXT NOT NULL DEFAULT ''",
            "strength_progress": "INTEGER NOT NULL DEFAULT 0",
            "dexterity_progress": "INTEGER NOT NULL DEFAULT 0",
            "constitution_progress": "INTEGER NOT NULL DEFAULT 0",
            "intelligence_progress": "INTEGER NOT NULL DEFAULT 0",
            "willpower_progress": "INTEGER NOT NULL DEFAULT 0",
            "charisma_progress": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, decl in additions.items():
            if name not in cols:
                self.conn.execute(f"ALTER TABLE characters ADD COLUMN {name} {decl}")

        # v0.9.26: rozwój Gildii graczy jest niedestrukcyjnym rozszerzeniem
        # tabel v0.9.25. Wewnętrzne nazwy player_clan pozostają dla zgodności save'ów.
        _guild_cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(player_clans)")}
        if "level" not in _guild_cols:
            self.conn.execute("ALTER TABLE player_clans ADD COLUMN level INTEGER NOT NULL DEFAULT 1")
        if "treasury" not in _guild_cols:
            self.conn.execute("ALTER TABLE player_clans ADD COLUMN treasury INTEGER NOT NULL DEFAULT 0")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS player_clan_roles (
                clan_id INTEGER NOT NULL, role_key TEXT NOT NULL, name TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 20,
                withdraw_money INTEGER NOT NULL DEFAULT 0,
                withdraw_items INTEGER NOT NULL DEFAULT 0,
                invite INTEGER NOT NULL DEFAULT 0, kick INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(clan_id,role_key), UNIQUE(clan_id,name)
            )
        """)
        for _grow in self.conn.execute("SELECT id FROM player_clans").fetchall():
            _gid=int(_grow["id"])
            for _key,_data in V0926_GUILD_DEFAULT_ROLES.items():
                self.conn.execute(
                    "INSERT OR IGNORE INTO player_clan_roles(clan_id,role_key,name,priority,withdraw_money,withdraw_items,invite,kick) VALUES(?,?,?,?,?,?,?,?)",
                    (_gid,_key,_data["name"],_data["priority"],_data["withdraw_money"],_data["withdraw_items"],_data["invite"],_data["kick"]),
                )

        # v0.9.27: osobna Siedziba Gildii, budynki, kontrakty i bossy.
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS player_guild_halls_v0927 (
                clan_id INTEGER PRIMARY KEY, hall_level INTEGER NOT NULL DEFAULT 1,
                forge_level INTEGER NOT NULL DEFAULT 0, treasury_level INTEGER NOT NULL DEFAULT 0,
                library_level INTEGER NOT NULL DEFAULT 0, training_level INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS player_guild_contracts_v0927 (
                clan_id INTEGER NOT NULL, contract_id TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
                completed_count INTEGER NOT NULL DEFAULT 0, ready_at INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(clan_id,contract_id)
            );
            CREATE TABLE IF NOT EXISTS player_guild_boss_records_v0927 (
                clan_id INTEGER PRIMARY KEY, kills INTEGER NOT NULL DEFAULT 0, fastest_kill_ms INTEGER,
                last_boss_name TEXT NOT NULL DEFAULT '', last_killed_at TEXT, last_summoned_at INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS player_guild_trophies_v0927 (
                clan_id INTEGER NOT NULL, trophy_id TEXT NOT NULL, name TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(clan_id,trophy_id)
            );
        """)
        for _grow in self.conn.execute("SELECT id FROM player_clans").fetchall():
            _gid=int(_grow["id"])
            self.conn.execute("INSERT OR IGNORE INTO player_guild_halls_v0927(clan_id) VALUES(?)",(_gid,))
            for _cid in V0927_GUILD_CONTRACTS:
                self.conn.execute("INSERT OR IGNORE INTO player_guild_contracts_v0927(clan_id,contract_id) VALUES(?,?)",(_gid,_cid))

        # Zgodność ze starymi postaciami: jeśli nie mają jeszcze odmiany,
        # dotychczasowe imię staje się bezpieczną formą we wszystkich przypadkach.
        for column in (
            "name_nom", "name_gen", "name_dat", "name_acc",
            "name_ins", "name_loc", "name_voc",
        ):
            self.conn.execute(
                f"UPDATE characters SET {column}=name "
                f"WHERE {column} IS NULL OR TRIM({column})=''"
            )
        # v0.8.38: Charyzma jest szóstą normalną statystyką.
        # Stare postacie zachowują wypracowaną Charyzmę; wartości 0/brakujące
        # otrzymują bezpieczną wartość startową 10.
        self.conn.execute(
            "UPDATE characters SET charisma=10 "
            "WHERE charisma IS NULL OR charisma < 1"
        )

        # v0.8.6: dwa sloty pierścieni. Stary slot ring jest
        # bezpiecznie migrowany do ring1 bez kasowania przedmiotów.
        old_ring = self.conn.execute(
            "SELECT item_id FROM equipment WHERE slot='ring' LIMIT 1"
        ).fetchone()
        ring1 = self.conn.execute(
            "SELECT item_id FROM equipment WHERE slot='ring1' LIMIT 1"
        ).fetchone()
        if old_ring and not ring1:
            self.conn.execute(
                "UPDATE equipment SET slot='ring1' WHERE slot='ring'"
            )
            self.conn.execute(
                "UPDATE equipment_gems SET slot='ring1' WHERE slot='ring'"
            )
        elif old_ring and ring1:
            # Nie niszczymy nietypowych danych; pozostawiony stary wpis
            # zostanie zignorowany do ręcznej korekty zamiast nadpisania ring1.
            pass

        # v0.8.52: dwa sloty talizmanów. Stary slot charm zostaje
        # niedestrukcyjnie przeniesiony do charm1.
        self.conn.execute(
            "UPDATE equipment SET slot='charm1' "
            "WHERE slot='charm' AND NOT EXISTS ("
            "SELECT 1 FROM equipment e2 "
            "WHERE e2.account_id=equipment.account_id AND e2.slot='charm1'"
            ")"
        )

        quest_cols = {
            r["name"] for r in self.conn.execute("PRAGMA table_info(quests)")
        }
        quest_additions = {
            "completed_at": "INTEGER NOT NULL DEFAULT 0",
            "completion_count": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, decl in quest_additions.items():
            if name not in quest_cols:
                self.conn.execute(
                    f"ALTER TABLE quests ADD COLUMN {name} {decl}"
                )

        # v0.8.24: każda ściana Kopalni Głębinowej ma własny,
        # losowy i trwały próg uderzeń. Kolumna jest dodawana
        # niedestrukcyjnie do zapisów z wcześniejszych wersji.
        mine_cols = {
            r["name"] for r in self.conn.execute("PRAGMA table_info(mine_progress)")
        }
        if "wall_required_hits" not in mine_cols:
            self.conn.execute(
                "ALTER TABLE mine_progress ADD COLUMN "
                "wall_required_hits INTEGER NOT NULL DEFAULT 0"
            )

        # v0.8.5: jednorazowa, niedestrukcyjna migracja starego systemu
        # Soul Tier 1-5 do nowego 1-20. Zachowuje zdobyte Próby.
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS migration_flags("
            "flag TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )

        # v0.27.0: stare postacie nie startują nagle od Levelu 1. Przy pierwszym
        # dodaniu osi Character Level wyprowadzamy go z najwyższej istniejącej osi
        # progresji (Soul/Biegłość/profesja/narzędzie), bez kasowania żadnego postępu.
        if _v027_character_level_new:
            self.conn.execute("""
                UPDATE characters SET character_level = MIN(400, MAX(1,
                    soul_level,
                    COALESCE((SELECT MAX(level) FROM class_progress cp WHERE cp.account_id=characters.account_id),1),
                    COALESCE((SELECT MAX(level) FROM professions p WHERE p.account_id=characters.account_id),1),
                    COALESCE((SELECT MAX(level) FROM tools t WHERE t.account_id=characters.account_id),1)
                )), character_xp=0
            """)
            self.conn.execute("INSERT OR IGNORE INTO migration_flags(flag) VALUES(?)",("character_level_v0270",))

        # v0.8.66: sześć niezależnych liczników EXP statystyk.
        # Stary wspólny Postęp Rozwoju jest kopiowany 1:1 do każdej statystyki,
        # dzięki czemu żadna postać nie traci wypracowanego postępu.
        stat_xp_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("separate_stat_progress_v0866",),
        ).fetchone()
        if not stat_xp_migrated:
            self.conn.execute(
                "UPDATE characters SET "
                "strength_progress=stat_progress, dexterity_progress=stat_progress, "
                "constitution_progress=stat_progress, intelligence_progress=stat_progress, "
                "willpower_progress=stat_progress, charisma_progress=stat_progress"
            )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("separate_stat_progress_v0866",),
            )
        migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("soul_tier_20_v085",),
        ).fetchone()
        if not migrated:
            self.conn.execute(
                "UPDATE characters SET soul_tier = CASE soul_tier "
                "WHEN 1 THEN 1 WHEN 2 THEN 4 WHEN 3 THEN 7 "
                "WHEN 4 THEN 13 WHEN 5 THEN 19 ELSE soul_tier END "
                "WHERE soul_tier BETWEEN 1 AND 5"
            )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("soul_tier_20_v085",),
            )

        # v0.8.8: narzędzia profesji są Character-Bound.
        # Jeżeli stara wersja pozwoliła schować je do Banku Dusz albo
        # zgromadzić kilka kopii, zostaje dokładnie jedna sztuka przy postaci.
        bound_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("character_bound_tools_v088",),
        ).fetchone()
        if not bound_migrated:
            for item_id in CHARACTER_BOUND_TOOL_IDS:
                bank_rows = self.conn.execute(
                    "SELECT account_id,quantity FROM bank_items "
                    "WHERE item_id=? AND quantity>0",
                    (item_id,),
                ).fetchall()
                for bank_row in bank_rows:
                    account_id = int(bank_row["account_id"])
                    owned = self.conn.execute(
                        "SELECT quantity FROM inventory "
                        "WHERE account_id=? AND item_id=?",
                        (account_id, item_id),
                    ).fetchone()
                    if not owned or int(owned["quantity"]) <= 0:
                        self.conn.execute(
                            "INSERT INTO inventory(account_id,item_id,quantity) "
                            "VALUES(?,?,1) "
                            "ON CONFLICT(account_id,item_id) "
                            "DO UPDATE SET quantity=1",
                            (account_id, item_id),
                        )
                self.conn.execute(
                    "DELETE FROM bank_items WHERE item_id=?",
                    (item_id,),
                )
                self.conn.execute(
                    "UPDATE inventory SET quantity=1 "
                    "WHERE item_id=? AND quantity>1",
                    (item_id,),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("character_bound_tools_v088",),
            )

        # v0.8.20: stare konto z jedną postacią staje się kontem głównym
        # ze slotem 1. Dalsze postacie są przechowywane w osobnych, ukrytych
        # profilach danych, dzięki czemu wszystkie dotychczasowe tabele
        # pozostają w 100% odseparowane między postaciami.
        self.conn.execute(
            """
            INSERT OR IGNORE INTO account_characters(
                master_account_id, character_account_id, slot
            )
            SELECT c.account_id, c.account_id, 1
            FROM characters c
            WHERE NOT EXISTS(
                SELECT 1 FROM account_characters ac
                WHERE ac.character_account_id=c.account_id
            )
            """
        )

        # v0.8.32: jeden wspólny portfel dla wszystkich postaci na koncie.
        # Pierwsza migracja SUMUJE walutę wszystkich istniejących slotów,
        # dzięki czemu aktualizacja nie kasuje pieniędzy żadnej postaci.
        wallet_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("shared_account_wallet_v0832",),
        ).fetchone()
        if not wallet_migrated:
            masters = self.conn.execute(
                "SELECT DISTINCT master_account_id FROM account_characters "
                "ORDER BY master_account_id"
            ).fetchall()
            for master_row in masters:
                master_id = int(master_row["master_account_id"])
                sums = self.conn.execute(
                    """
                    SELECT COALESCE(SUM(c.silver),0) AS silver,
                           COALESCE(SUM(c.gold),0) AS gold,
                           COALESCE(SUM(c.mithril),0) AS mithril
                    FROM account_characters ac
                    JOIN characters c ON c.account_id=ac.character_account_id
                    WHERE ac.master_account_id=?
                    """,
                    (master_id,),
                ).fetchone()
                silver, gold, mithril = normalize_currency_values(
                    int(sums["silver"] or 0),
                    int(sums["gold"] or 0),
                    int(sums["mithril"] or 0),
                )
                self.conn.execute(
                    "INSERT OR REPLACE INTO account_wallet("
                    "master_account_id,silver,gold,mithril,updated_at"
                    ") VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
                    (master_id, silver, gold, mithril),
                )
                self.conn.execute(
                    """
                    UPDATE characters SET silver=?,gold=?,mithril=?
                    WHERE account_id IN (
                        SELECT character_account_id FROM account_characters
                        WHERE master_account_id=?
                    )
                    """,
                    (silver, gold, mithril, master_id),
                )

                # Waluta zdeponowana w Banku Dusz również jest wspólna.
                bank_sums = self.conn.execute(
                    """
                    SELECT COALESCE(SUM(b.silver),0) AS silver,
                           COALESCE(SUM(b.gold),0) AS gold,
                           COALESCE(SUM(b.mithril),0) AS mithril
                    FROM account_characters ac
                    LEFT JOIN bank_balances b ON b.account_id=ac.character_account_id
                    WHERE ac.master_account_id=?
                    """,
                    (master_id,),
                ).fetchone()
                bank_silver, bank_gold, bank_mithril = normalize_currency_values(
                    int(bank_sums["silver"] or 0),
                    int(bank_sums["gold"] or 0),
                    int(bank_sums["mithril"] or 0),
                )
                self.conn.execute(
                    "INSERT INTO bank_balances(account_id,silver,gold,mithril) "
                    "VALUES(?,?,?,?) "
                    "ON CONFLICT(account_id) DO UPDATE SET "
                    "silver=excluded.silver,gold=excluded.gold,mithril=excluded.mithril",
                    (master_id, bank_silver, bank_gold, bank_mithril),
                )
                self.conn.execute(
                    """
                    DELETE FROM bank_balances
                    WHERE account_id<>? AND account_id IN (
                        SELECT character_account_id FROM account_characters
                        WHERE master_account_id=?
                    )
                    """,
                    (master_id, master_id),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("shared_account_wallet_v0832",),
            )

        # v0.8.51: nadaj istniejącym postaciom taki sam bazowy profil klasy,
        # jaki od tej wersji dostają nowe postacie. Jednorazowa flaga zapobiega
        # ponownemu dodawaniu bonusów po restarcie/deployu.
        class_stats_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("class_starting_stats_v0851",),
        ).fetchone()
        if not class_stats_migrated:
            rows = self.conn.execute(
                "SELECT account_id,class_name FROM characters"
            ).fetchall()
            for row in rows:
                bonuses = V0876_CLASS_STARTING_STAT_BONUSES.get(row["class_name"], {})
                self.conn.execute(
                    "UPDATE characters SET strength=strength+?, dexterity=dexterity+?, "
                    "constitution=constitution+?, intelligence=intelligence+?, "
                    "willpower=willpower+?, charisma=charisma+? WHERE account_id=?",
                    (
                        int(bonuses.get("strength", 0)),
                        int(bonuses.get("dexterity", 0)),
                        int(bonuses.get("constitution", 0)),
                        int(bonuses.get("intelligence", 0)),
                        int(bonuses.get("willpower", 0)),
                        int(bonuses.get("charisma", 0)),
                        int(row["account_id"]),
                    ),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("class_starting_stats_v0851",),
            )

        # v0.9.0: pełny balans startu rasa + klasa + weapon_base.
        # Zachowujemy CAŁY zdobyty później rozwój: do aktualnej wartości
        # dodajemy wyłącznie różnicę między starym a nowym profilem startowym.
        # Flaga sprawia, że migracja jest idempotentna.
        character_balance_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("character_start_balance_v0900",),
        ).fetchone()
        if not character_balance_migrated:
            new_race_stats = {
                race[0]: {
                    "strength": int(race[2]),
                    "dexterity": int(race[3]),
                    "constitution": int(race[4]),
                    "intelligence": int(race[5]),
                    "willpower": int(race[6]),
                }
                for race in RACES
            }
            new_weapon_bases = {entry[0]: int(entry[3]) for entry in CLASSES}
            rows = self.conn.execute(
                "SELECT account_id,race,class_name FROM characters"
            ).fetchall()
            stat_names = (
                "strength", "dexterity", "constitution",
                "intelligence", "willpower", "charisma",
            )
            for row in rows:
                race_name = row["race"]
                class_name = row["class_name"]
                old_race = V0876_RACE_BASE_STATS.get(race_name, {})
                new_race = new_race_stats.get(race_name, old_race)
                old_class = V0876_CLASS_STARTING_STAT_BONUSES.get(class_name, {})
                new_class = CLASS_STARTING_STAT_BONUSES.get(class_name, old_class)
                deltas = {}
                for stat_name in stat_names:
                    race_delta = 0
                    if stat_name != "charisma":
                        race_delta = int(new_race.get(stat_name, 0)) - int(old_race.get(stat_name, 0))
                    class_delta = int(new_class.get(stat_name, 0)) - int(old_class.get(stat_name, 0))
                    deltas[stat_name] = race_delta + class_delta
                self.conn.execute(
                    "UPDATE characters SET "
                    "strength=MAX(1,strength+?), dexterity=MAX(1,dexterity+?), "
                    "constitution=MAX(1,constitution+?), intelligence=MAX(1,intelligence+?), "
                    "willpower=MAX(1,willpower+?), charisma=MAX(1,charisma+?), "
                    "weapon_base=? WHERE account_id=?",
                    (
                        deltas["strength"], deltas["dexterity"],
                        deltas["constitution"], deltas["intelligence"],
                        deltas["willpower"], deltas["charisma"],
                        int(new_weapon_bases.get(class_name, 7)),
                        int(row["account_id"]),
                    ),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("character_start_balance_v0900",),
            )

        # v0.8.60: jedno wspólne saldo, trzy nominały.
        # Konwersja jest wykonywana dokładnie raz i zachowuje pełną wartość:
        # silver 1:1, gold 1:1000, mithril 1:1_000_000_000 srebra.
        unified_currency_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("unified_currency_v0859",),
        ).fetchone()
        if not unified_currency_migrated:
            wallet_rows = self.conn.execute(
                "SELECT master_account_id,silver,gold,mithril FROM account_wallet"
            ).fetchall()
            for row in wallet_rows:
                coins = legacy_currency_to_coins(
                    row["silver"], row["gold"], row["mithril"]
                )
                master_id = int(row["master_account_id"])
                self.conn.execute(
                    "UPDATE account_wallet SET silver=?,gold=0,mithril=0,"
                    "updated_at=CURRENT_TIMESTAMP WHERE master_account_id=?",
                    (coins, master_id),
                )
                self.conn.execute(
                    "UPDATE characters SET silver=?,gold=0,mithril=0 "
                    "WHERE account_id IN (SELECT character_account_id "
                    "FROM account_characters WHERE master_account_id=?)",
                    (coins, master_id),
                )

            # Nietypowe stare save'y bez account_wallet też nie tracą środków.
            orphan_rows = self.conn.execute(
                "SELECT account_id,silver,gold,mithril FROM characters "
                "WHERE account_id NOT IN (SELECT character_account_id FROM account_characters)"
            ).fetchall()
            for row in orphan_rows:
                coins = legacy_currency_to_coins(
                    row["silver"], row["gold"], row["mithril"]
                )
                self.conn.execute(
                    "UPDATE characters SET silver=?,gold=0,mithril=0 WHERE account_id=?",
                    (coins, int(row["account_id"])),
                )

            bank_rows = self.conn.execute(
                "SELECT account_id,silver,gold,mithril FROM bank_balances"
            ).fetchall()
            for row in bank_rows:
                coins = legacy_currency_to_coins(
                    row["silver"], row["gold"], row["mithril"]
                )
                self.conn.execute(
                    "UPDATE bank_balances SET silver=?,gold=0,mithril=0 WHERE account_id=?",
                    (coins, int(row["account_id"])),
                )

            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("unified_currency_v0859",),
            )

        # v0.9.4: Historia postaci / Lifetime Statistics.
        # Odtwarzamy wyłącznie dane, które starsze wersje faktycznie zapisywały.
        # Dokładne ilości ryb/rud/drewna/ziół oraz crafted_items zaczynają się
        # od v0.9.4, ponieważ starsze save'y nie przechowywały pełnej historii sztuk.
        lifetime_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("lifetime_statistics_v094",),
        ).fetchone()
        if not lifetime_migrated:
            character_ids = [
                int(row["account_id"])
                for row in self.conn.execute("SELECT account_id FROM characters").fetchall()
            ]
            production_professions = {"Kowalstwo", "Gotowanie", "Alchemia", "Jubilerstwo"}
            for account_id in character_ids:
                def set_max(key, value):
                    value = max(0, int(value or 0))
                    self.conn.execute(
                        "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
                        "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
                        "value=MAX(lifetime_statistics.value,excluded.value), "
                        "updated_at=CURRENT_TIMESTAMP",
                        (account_id, key, value),
                    )

                bestiary_rows = self.conn.execute(
                    "SELECT mob_template_id,kills FROM bestiary_stats WHERE account_id=?",
                    (account_id,),
                ).fetchall()
                total_kills = sum(max(0, int(row["kills"] or 0)) for row in bestiary_rows)
                boss_kills = 0
                rare_kills = 0
                for row in bestiary_rows:
                    mob_id = str(row["mob_template_id"])
                    kills = max(0, int(row["kills"] or 0))
                    template = MOB_TEMPLATES.get(mob_id, {})
                    if mob_id in BOSS_COLLECTION_CATALOG:
                        boss_kills += kills
                    if template.get("rare_mob"):
                        rare_kills += kills

                metrics = {
                    str(row["metric"]): max(0, int(row["value"] or 0))
                    for row in self.conn.execute(
                        "SELECT metric,value FROM achievement_progress WHERE account_id=?",
                        (account_id,),
                    ).fetchall()
                }
                set_max("kills_total", total_kills)
                set_max("combat_victories", total_kills)
                set_max("boss_kills", max(boss_kills, metrics.get("boss_kills", 0)))
                set_max("rare_kills", max(rare_kills, metrics.get("rare_kills", 0)))
                set_max("rare_fish_caught", metrics.get("rare_fish_caught", 0))
                set_max("gems_found", metrics.get("gems_found", 0))

                char_row = self.conn.execute(
                    "SELECT deaths FROM characters WHERE account_id=?", (account_id,)
                ).fetchone()
                set_max("deaths", int(char_row["deaths"] or 0) if char_row else 0)

                quest_row = self.conn.execute(
                    "SELECT COALESCE(SUM(completion_count),0) AS total FROM quests WHERE account_id=?",
                    (account_id,),
                ).fetchone()
                set_max("quests_completed", int(quest_row["total"] or 0) if quest_row else 0)

                bounty_row = self.conn.execute(
                    "SELECT completed_count FROM bounty_boards WHERE account_id=?", (account_id,)
                ).fetchone()
                set_max("bounties_completed", int(bounty_row["completed_count"] or 0) if bounty_row else 0)

                profession_rows = self.conn.execute(
                    "SELECT profession,actions FROM professions WHERE account_id=?", (account_id,)
                ).fetchall()
                profession_actions = sum(max(0, int(row["actions"] or 0)) for row in profession_rows)
                craft_actions = sum(
                    max(0, int(row["actions"] or 0))
                    for row in profession_rows if str(row["profession"]) in production_professions
                )
                set_max("profession_actions", profession_actions)
                set_max("craft_actions", craft_actions)

                explored = self.conn.execute(
                    "SELECT COUNT(*) AS total FROM exploration_rooms WHERE account_id=?", (account_id,)
                ).fetchone()
                set_max("rooms_discovered", int(explored["total"] or 0) if explored else 0)
                unique_bestiary = len({str(row["mob_template_id"]) for row in bestiary_rows})
                set_max("bestiary_unique", unique_bestiary)

            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("lifetime_statistics_v094",),
            )

        # v0.9.5: Dziennik ryb. Starszy zapis potrafi pewnie potwierdzić tylko
        # gatunki nadal obecne w Siatce. Seedujemy je raz; rekordy rozmiaru i
        # pełny licznik połowów są dokładne od v0.9.5.
        fish_journal_migrated = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("fish_journal_v095",),
        ).fetchone()
        if not fish_journal_migrated:
            character_ids = [
                int(row["account_id"])
                for row in self.conn.execute("SELECT account_id FROM characters").fetchall()
            ]
            for account_id in character_ids:
                rows = self.conn.execute(
                    "SELECT item_id,quantity FROM profession_storage "
                    "WHERE account_id=? AND container='net' AND quantity>0",
                    (account_id,),
                ).fetchall()
                seeded_counts = {}
                for row in rows:
                    item_id = str(row["item_id"])
                    base_id = base_fish_species_id(item_id)
                    if base_id not in FISH_RESOURCE_IDS:
                        continue
                    qty = max(1, int(row["quantity"] or 0))
                    seeded_counts[base_id] = seeded_counts.get(base_id, 0) + qty
                for base_id, qty in seeded_counts.items():
                    self.conn.execute(
                        "INSERT OR IGNORE INTO fish_journal("
                        "account_id,fish_id,caught_count,best_length_mm,best_weight_g,first_room_id,last_room_id"
                        ") VALUES(?,?,?,0,0,'','')",
                        (account_id, base_id, qty),
                    )
                self.conn.execute(
                    "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
                    "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
                    "value=MAX(lifetime_statistics.value,excluded.value),updated_at=CURRENT_TIMESTAMP",
                    (account_id, "fish_species_discovered", len(seeded_counts)),
                )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("fish_journal_v095",),
            )

        # v0.9.6: rozszerzony Collection Codex. Seedujemy tylko dane, które
        # poprzednie wersje potrafią pewnie potwierdzić: Dziennik ryb,
        # bossów z Bestiariusza, istniejący Rare Codex oraz przedmioty nadal
        # posiadane w inventory/storage.
        collection_v096 = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("collections_v096",),
        ).fetchone()
        if not collection_v096:
            character_ids = [
                int(row["account_id"])
                for row in self.conn.execute("SELECT account_id FROM characters").fetchall()
            ]
            for account_id in character_ids:
                for row in self.conn.execute(
                    "SELECT fish_id FROM fish_journal WHERE account_id=?", (account_id,)
                ).fetchall():
                    fish_id = str(row["fish_id"])
                    if fish_id in FISH_COLLECTION_CATALOG:
                        self.conn.execute(
                            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
                            (account_id, "fish", fish_id),
                        )

                for row in self.conn.execute(
                    "SELECT mob_template_id FROM bestiary_stats WHERE account_id=? AND kills>0",
                    (account_id,),
                ).fetchall():
                    mob_id = canonical_bestiary_template_id(row["mob_template_id"])
                    if mob_id in BOSS_COLLECTION_CATALOG:
                        self.conn.execute(
                            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
                            (account_id, "bosses", mob_id),
                        )

                owned_ids = set()
                for row in self.conn.execute(
                    "SELECT item_id FROM inventory WHERE account_id=? AND quantity>0", (account_id,)
                ).fetchall():
                    owned_ids.add(str(row["item_id"]))
                for row in self.conn.execute(
                    "SELECT item_id FROM profession_storage WHERE account_id=? AND quantity>0", (account_id,)
                ).fetchall():
                    owned_ids.add(str(row["item_id"]))
                for item_id in owned_ids:
                    base_id = canonical_profession_resource_id(item_id)
                    categories = []
                    if base_id in MINERAL_COLLECTION_CATALOG: categories.append(("minerals", base_id))
                    if base_id in HERB_COLLECTION_CATALOG: categories.append(("herbs", base_id))
                    if base_id in MATERIAL_COLLECTION_CATALOG: categories.append(("materials", base_id))
                    if item_id in GEM_COLLECTION_CATALOG: categories.append(("gems", item_id))
                    if item_id in UNIQUE_ITEM_COLLECTION_CATALOG: categories.append(("unique", item_id))
                    for category, entry_id in categories:
                        self.conn.execute(
                            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
                            (account_id, category, entry_id),
                        )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("collections_v096",),
            )

        # v0.9.11: v0.9.10 przez krótki czas dawało darmowe klasowe EQ
        # przy tworzeniu postaci. Nowa zasada usuwa te wyłącznie startowe
        # przedmioty również ze starych zapisów, bez dotykania kupionego/zdobytego EQ.
        starter_eq_removed = self.conn.execute(
            "SELECT 1 FROM migration_flags WHERE flag=?",
            ("remove_class_starter_equipment_v0911",),
        ).fetchone()
        if not starter_eq_removed:
            self.conn.execute(
                "DELETE FROM equipment_gems WHERE EXISTS ("
                "SELECT 1 FROM equipment e "
                "WHERE e.account_id=equipment_gems.account_id "
                "AND e.slot=equipment_gems.slot "
                "AND e.item_id LIKE 'starter_%'"
                ")"
            )
            self.conn.execute(
                "DELETE FROM equipment WHERE item_id LIKE 'starter_%'"
            )
            self.conn.execute(
                "DELETE FROM inventory WHERE item_id LIKE 'starter_%'"
            )
            self.conn.execute(
                "INSERT INTO migration_flags(flag) VALUES(?)",
                ("remove_class_starter_equipment_v0911",),
            )

        self.conn.commit()

    def account_name(self, account_id):
        row = self.conn.execute(
            "SELECT username FROM accounts WHERE id=?", (int(account_id),)
        ).fetchone()
        return str(row["username"]) if row else ""

    def wipe_characters_for_master(self, master_account_id):
        """Usuń postacie/progres konta, ale zachowaj login i hasło konta."""
        master_account_id = int(master_account_id)
        rows = self.conn.execute(
            "SELECT character_account_id FROM account_characters WHERE master_account_id=? ORDER BY slot",
            (master_account_id,),
        ).fetchall()
        char_ids = [int(row["character_account_id"]) for row in rows]

        # Ukryte konta profili można bezpiecznie usunąć — FK CASCADE czyści ich dane.
        for char_id in char_ids:
            if char_id != master_account_id:
                self.conn.execute("DELETE FROM accounts WHERE id=?", (char_id,))

        # Pierwsza postać może używać ID konta głównego, więc kasujemy jej dane,
        # ale nigdy rekordu logowania w accounts.
        if master_account_id in char_ids:
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {"accounts", "account_characters", "account_wallet"}
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )

        self.conn.execute(
            "DELETE FROM account_characters WHERE master_account_id=?",
            (master_account_id,),
        )
        # Portfel jest częścią postępu gry, nie danych logowania. Nowa pierwsza
        # postać ponownie dostanie normalny pakiet startowy.
        self.conn.execute(
            "DELETE FROM account_wallet WHERE master_account_id=?",
            (master_account_id,),
        )
        self.conn.commit()
        return len(char_ids)

    def delete_character_for_master(self, master_account_id, character_account_id):
        """v0.9.1: usuń dokładnie jedną postać bez kasowania konta ani wspólnego portfela.

        Pierwsza postać może używać ID konta głównego, dlatego nie wolno wtedy
        usuwać rekordu z accounts. Dodatkowe postacie mają ukryte konta techniczne
        i ich usunięcie przez FK CASCADE czyści cały własny progres postaci.
        """
        master_account_id = int(master_account_id)
        character_account_id = int(character_account_id)
        row = self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.name
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=? AND ac.character_account_id=?
            """,
            (master_account_id, character_account_id),
        ).fetchone()
        if not row:
            return None

        slot = int(row["slot"])
        name = str(row["name"])

        if character_account_id != master_account_id:
            # Ukryty profil postaci. Usunięcie konta technicznego uruchamia
            # ON DELETE CASCADE dla całego progresu i samego powiązania slotu.
            self.conn.execute(
                "DELETE FROM accounts WHERE id=?", (character_account_id,)
            )
        else:
            # Slot oparty na koncie głównym: zachowujemy login, hasło i
            # account_wallet, a czyścimy wyłącznie dane tej postaci.
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
            protected = {"accounts", "account_characters", "account_wallet"}
            for table_row in tables:
                table = str(table_row["name"])
                if table in protected:
                    continue
                columns = {
                    str(col["name"])
                    for col in self.conn.execute(
                        f'PRAGMA table_info("{table}")'
                    ).fetchall()
                }
                if "account_id" in columns:
                    self.conn.execute(
                        f'DELETE FROM "{table}" WHERE account_id=?',
                        (master_account_id,),
                    )
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND character_account_id=?",
                (master_account_id, character_account_id),
            )

        self.conn.commit()
        return {"slot": slot, "name": name}

    def wipe_all_characters_preserve_accounts(self):
        masters = [
            int(row["id"])
            for row in self.conn.execute(
                "SELECT id FROM accounts WHERE id NOT IN ("
                "SELECT character_account_id FROM account_characters "
                "WHERE character_account_id<>master_account_id) ORDER BY id"
            ).fetchall()
        ]
        removed = 0
        for master_id in masters:
            removed += self.wipe_characters_for_master(master_id)
        return removed, masters

    def master_accounts(self):
        """v0.30.1: lista prawdziwych kont logowania, bez ukrytych profili postaci."""
        return self.conn.execute(
            """
            SELECT a.id,a.username,COUNT(ac.character_account_id) AS character_count
            FROM accounts a
            LEFT JOIN account_characters ac ON ac.master_account_id=a.id
            WHERE a.id NOT IN (
                SELECT character_account_id FROM account_characters
                WHERE character_account_id<>master_account_id
            )
            GROUP BY a.id,a.username
            ORDER BY a.username COLLATE NOCASE,a.id
            """
        ).fetchall()

    def master_account_by_name(self, username):
        """v0.30.1: znajdź tylko konto główne; profil techniczny postaci nie jest celem admina."""
        return self.conn.execute(
            """
            SELECT a.* FROM accounts a
            WHERE a.username=? COLLATE NOCASE
              AND a.id NOT IN (
                  SELECT character_account_id FROM account_characters
                  WHERE character_account_id<>master_account_id
              )
            """,
            (username,),
        ).fetchone()

    def account_by_name(self, username):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()

    def create_account(self, username, password):
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid

    def is_character_profile(self, account_id):
        row = self.conn.execute(
            "SELECT 1 FROM account_characters "
            "WHERE character_account_id=? AND master_account_id<>character_account_id",
            (account_id,),
        ).fetchone()
        return row is not None

    def master_account_for_character(self, character_account_id):
        row = self.conn.execute(
            "SELECT master_account_id FROM account_characters "
            "WHERE character_account_id=?",
            (character_account_id,),
        ).fetchone()
        if row:
            return int(row["master_account_id"])
        return int(character_account_id)

    def shared_wallet_for_master(self, master_account_id):
        master_account_id = int(master_account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM account_wallet "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        if row:
            silver, gold, mithril = normalize_currency_values(
                row["silver"], row["gold"], row["mithril"]
            )
            if gold or mithril or silver != int(row["silver"]):
                self.set_shared_wallet_for_master(
                    master_account_id, silver, gold, mithril
                )
            return (silver, gold, mithril)

        # Bezpieczny fallback dla świeżego konta albo nietypowego starego save'a.
        sums = self.conn.execute(
            """
            SELECT COALESCE(SUM(c.silver),0) AS silver,
                   COALESCE(SUM(c.gold),0) AS gold,
                   COALESCE(SUM(c.mithril),0) AS mithril
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            """,
            (master_account_id,),
        ).fetchone()
        silver, gold, mithril = normalize_currency_values(
            int(sums["silver"] or 0), int(sums["gold"] or 0), int(sums["mithril"] or 0)
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO account_wallet("
            "master_account_id,silver,gold,mithril,updated_at"
            ") VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
            (master_account_id, silver, gold, mithril),
        )
        self.conn.commit()
        return silver, gold, mithril

    def shared_wallet_for_character(self, character_account_id):
        return self.shared_wallet_for_master(
            self.master_account_for_character(character_account_id)
        )

    def set_shared_wallet_for_master(self, master_account_id, silver, gold, mithril, *, commit=True):
        master_account_id = int(master_account_id)
        silver, gold, mithril = normalize_currency_values(silver, gold, mithril)
        self.conn.execute(
            """
            INSERT INTO account_wallet(master_account_id,silver,gold,mithril,updated_at)
            VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(master_account_id) DO UPDATE SET
                silver=excluded.silver,
                gold=excluded.gold,
                mithril=excluded.mithril,
                updated_at=CURRENT_TIMESTAMP
            """,
            (master_account_id, silver, gold, mithril),
        )
        # Trzymamy kolumny legacy zsynchronizowane, żeby wszystkie starsze
        # fragmenty gry i narzędzia administracyjne widziały to samo saldo.
        self.conn.execute(
            """
            UPDATE characters SET silver=?,gold=?,mithril=?
            WHERE account_id IN (
                SELECT character_account_id FROM account_characters
                WHERE master_account_id=?
            )
            """,
            (silver, gold, mithril, master_account_id),
        )
        if commit:
            self.conn.commit()
        return silver, gold, mithril

    def set_shared_wallet_for_character(self, character_account_id, silver, gold, mithril, *, commit=True):
        return self.set_shared_wallet_for_master(
            self.master_account_for_character(character_account_id),
            silver, gold, mithril, commit=commit,
        )

    def apply_shared_wallet_to_character(self, character):
        silver, gold, mithril = self.shared_wallet_for_character(character.account_id)
        character.silver = silver
        character.gold = gold
        character.mithril = mithril
        return character

    def character_for_account(self, account_id):
        return self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()

    def characters_for_master(self, master_account_id):
        return self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, c.*
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?
            ORDER BY ac.slot
            """,
            (master_account_id,),
        ).fetchall()

    def character_count_for_master(self, master_account_id):
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM account_characters "
            "WHERE master_account_id=?",
            (master_account_id,),
        ).fetchone()
        return int(row["n"] or 0) if row else 0

    def _next_character_slot(self, master_account_id):
        used = {
            int(r["slot"]) for r in self.conn.execute(
                "SELECT slot FROM account_characters WHERE master_account_id=?",
                (master_account_id,),
            ).fetchall()
        }
        for slot in range(1, MAX_CHARACTERS_PER_ACCOUNT + 1):
            if slot not in used:
                return slot
        return None

    def _create_hidden_character_account(self, master_account_id, slot):
        # Profil jest wyłącznie technicznym kluczem danych postaci. Nie można
        # zalogować się do niego z ekranu logowania.
        while True:
            username = f"__char_{master_account_id}_{slot}_{secrets.token_hex(6)}"
            if not self.account_by_name(username):
                break
        salt, digest = hash_password(secrets.token_urlsafe(32))
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        return int(cur.lastrowid)

    def create_character_for_master(self, master_account_id, name, race, cls, name_cases):
        if self.character_count_for_master(master_account_id) >= MAX_CHARACTERS_PER_ACCOUNT:
            raise ValueError("character_limit")

        slot = self._next_character_slot(master_account_id)
        if slot is None:
            raise ValueError("character_limit")

        existing_master_character = self.character_for_account(master_account_id)
        master_link = self.conn.execute(
            "SELECT 1 FROM account_characters WHERE character_account_id=?",
            (master_account_id,),
        ).fetchone()

        if slot == 1 and not existing_master_character and not master_link:
            character_account_id = int(master_account_id)
        else:
            character_account_id = self._create_hidden_character_account(
                master_account_id, slot
            )

        self.conn.execute(
            "INSERT INTO account_characters(master_account_id,character_account_id,slot) "
            "VALUES(?,?,?)",
            (master_account_id, character_account_id, slot),
        )
        try:
            self.create_character(
                character_account_id, name, race, cls, name_cases
            )
            wallet_row = self.conn.execute(
                "SELECT silver,gold,mithril FROM account_wallet "
                "WHERE master_account_id=?",
                (master_account_id,),
            ).fetchone()
            if wallet_row is None:
                # Pierwsza postać zakłada wspólny portfel z pakietem startowym.
                created = self.character_for_account(character_account_id)
                self.set_shared_wallet_for_master(
                    master_account_id,
                    created["silver"], created["gold"], created["mithril"],
                )
            else:
                # Każda następna postać dostaje dokładnie saldo konta,
                # bez ponownego przyznawania startowych monet.
                self.set_shared_wallet_for_master(
                    master_account_id,
                    wallet_row["silver"], wallet_row["gold"], wallet_row["mithril"],
                )
        except Exception:
            self.conn.execute(
                "DELETE FROM account_characters WHERE master_account_id=? AND slot=?",
                (master_account_id, slot),
            )
            if character_account_id != master_account_id:
                self.conn.execute(
                    "DELETE FROM accounts WHERE id=?", (character_account_id,)
                )
            self.conn.commit()
            raise
        return character_account_id, slot

    def character_name_exists(self, name):
        return self.conn.execute(
            "SELECT 1 FROM characters WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone() is not None

    def character_account_id_by_name_v0928(self, name):
        row = self.conn.execute(
            "SELECT account_id FROM characters WHERE name=? COLLATE NOCASE",
            (str(name or "").strip(),),
        ).fetchone()
        return int(row["account_id"]) if row else None

    def character_name_by_account_v0928(self, account_id):
        row = self.conn.execute(
            "SELECT name FROM characters WHERE account_id=?",
            (int(account_id),),
        ).fetchone()
        return str(row["name"]) if row else None

    def are_friends_v0928(self, account_id, friend_account_id):
        return self.conn.execute(
            "SELECT 1 FROM player_friends_v0928 WHERE account_id=? AND friend_account_id=?",
            (int(account_id), int(friend_account_id)),
        ).fetchone() is not None

    def create_character(self, account_id, name, race, cls, name_cases):
        rname, _, _race_strength, _race_dexterity, _race_constitution, _race_intelligence, _race_willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        starting_stats = class_starting_stats_for(race, cls)
        strength = starting_stats["strength"]
        dexterity = starting_stats["dexterity"]
        constitution = starting_stats["constitution"]
        intelligence = starting_stats["intelligence"]
        willpower = starting_stats["willpower"]
        charisma = starting_stats["charisma"]
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,
                name_nom,name_gen,name_dat,name_acc,name_ins,name_loc,name_voc,
                race,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,charisma,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',?,?,?,0)
            """,
            (
                account_id, name,
                name_cases["nom"], name_cases["gen"], name_cases["dat"],
                name_cases["acc"], name_cases["ins"], name_cases["loc"],
                name_cases["voc"],
                rname, cname, ctype, soul_weapon, weapon_base,
                strength, dexterity, constitution, intelligence, willpower, charisma,
                STARTING_SILVER, STARTING_GOLD, STARTING_MITHRIL,
            ),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
            (account_id, "healing_potion", 2),
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,1)",
            (account_id, cname),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, cname),
        )
        self.conn.commit()

    def save_character(self, c):
        (
            c.silver,
            c.gold,
            c.mithril,
        ) = normalize_currency_values(
            c.silver,
            c.gold,
            c.mithril,
        )

        # v0.8.32: waluta należy do konta głównego, nie do slotu postaci.
        self.set_shared_wallet_for_character(
            c.account_id, c.silver, c.gold, c.mithril, commit=False
        )

        self.conn.execute(
            """
            UPDATE characters SET
                strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                stat_progress=?, strength_progress=?, dexterity_progress=?,
                constitution_progress=?, intelligence_progress=?, willpower_progress=?,
                charisma_progress=?, soul_level=?, soul_xp=?, soul_tier=?, room_id=?,
                silver=?, gold=?, mithril=?, charisma=?, character_level=?, character_xp=?, deaths=?,
                guild_reputation_json=?, guild_exams_json=?,
                guild_class_quests_json=?, guild_bounty_json=?,
                loot_filter=?, active_title=?
            WHERE account_id=?
            """,
            (
                c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                min(c.strength_progress, c.dexterity_progress, c.constitution_progress,
                    c.intelligence_progress, c.willpower_progress, c.charisma_progress),
                c.strength_progress, c.dexterity_progress, c.constitution_progress,
                c.intelligence_progress, c.willpower_progress, c.charisma_progress,
                c.soul_level, c.soul_xp, c.soul_tier, c.room_id,
                c.silver, c.gold, c.mithril, c.charisma, c.character_level, c.character_xp, c.deaths,
                c.guild_reputation_json, c.guild_exams_json,
                c.guild_class_quests_json, c.guild_bounty_json,
                c.loot_filter, c.active_title,
                c.account_id,
            ),
        )
        self.conn.commit()

    def crypt_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT crypt_checkpoint FROM characters WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["crypt_checkpoint"] or 0) if row else 0

    def unlock_crypt_checkpoint(self, account_id, floor):
        floor = int(floor)
        if not is_crypt_boss_floor(floor):
            return self.crypt_checkpoint(account_id)

        current = self.crypt_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                "UPDATE characters SET crypt_checkpoint=? "
                "WHERE account_id=?",
                (new_value, account_id),
            )
            self.conn.commit()
        return new_value

    def sync_legacy_crypt_checkpoint(self, account_id, room_id):
        floor = crypt_floor_number(room_id)
        if floor is None:
            return self.crypt_checkpoint(account_id)

        # Stara postać stojąca na piętrze N musiała wcześniej przejść
        # wszystkie bossy poniżej N. Nie zaliczamy bossa bieżącego piętra.
        safe_floor = ((max(1, floor) - 1) // 10) * 10
        if safe_floor >= 10:
            return self.unlock_crypt_checkpoint(account_id, safe_floor)
        return self.crypt_checkpoint(account_id)

    def crypt_portal(self, account_id):
        return self.crypt_checkpoint(account_id)

    def unlock_crypt_portal(self, account_id, floor):
        return self.unlock_crypt_checkpoint(account_id, floor)

    def astral_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT checkpoint FROM astral_progress WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["checkpoint"] or 0) if row else 0

    def unlock_astral_checkpoint(self, account_id, floor):
        floor = int(floor)
        if not is_astral_boss_floor(floor):
            return self.astral_checkpoint(account_id)

        current = self.astral_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                """
                INSERT INTO astral_progress(account_id,checkpoint)
                VALUES(?,?)
                ON CONFLICT(account_id)
                DO UPDATE SET checkpoint=excluded.checkpoint
                """,
                (account_id, new_value),
            )
            self.conn.commit()
        return new_value

    def astral_portal(self, account_id):
        return self.astral_checkpoint(account_id)

    def unlock_astral_portal(self, account_id, floor):
        return self.unlock_astral_checkpoint(account_id, floor)

    def boss_floor_cleared(self, account_id, dungeon_kind, floor):
        dungeon_kind = str(dungeon_kind or "").strip().lower()
        floor = max(1, int(floor))
        # Zgodność starych save'ów: checkpoint Krypty/Wieży oznacza, że wszystkie
        # wcześniejsze bossy co 10 zostały już kiedyś pokonane.
        if dungeon_kind == "crypt" and floor <= self.crypt_checkpoint(account_id):
            return True
        if dungeon_kind == "astral" and floor <= self.astral_checkpoint(account_id):
            return True
        row = self.conn.execute(
            "SELECT 1 FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=? AND floor=?",
            (account_id, dungeon_kind, floor),
        ).fetchone()
        return bool(row)

    def mark_boss_floor_cleared(self, account_id, dungeon_kind, floor):
        dungeon_kind = str(dungeon_kind or "").strip().lower()
        floor = max(1, int(floor))
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO boss_floor_clears(account_id,dungeon_kind,floor) VALUES(?,?,?)",
            (account_id, dungeon_kind, floor),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def ensure_mine_progress(self, account_id):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO mine_progress(
                account_id,max_floor_unlocked,wall_hits,wall_required_hits
            ) VALUES(?,1,0,0)
            """,
            (account_id,),
        )
        self.conn.commit()

    def mine_progress(self, account_id):
        self.ensure_mine_progress(account_id)
        row = self.conn.execute(
            """
            SELECT max_floor_unlocked,wall_hits,wall_required_hits
            FROM mine_progress
            WHERE account_id=?
            """,
            (account_id,),
        ).fetchone()
        highest = max(
            MINE_MIN_FLOOR,
            int(row["max_floor_unlocked"]),
        )
        hits = max(0, int(row["wall_hits"]))
        required_hits = max(0, int(row["wall_required_hits"]))

        # Stare zapisy nie miały losowego progu. Losujemy go raz
        # dla aktualnej ściany i zapisujemy, aby restart niczego nie zmieniał.
        if required_hits <= hits:
            required_hits = roll_mine_wall_hits_required(highest, hits)
            self.conn.execute(
                "UPDATE mine_progress SET wall_required_hits=? WHERE account_id=?",
                (required_hits, account_id),
            )
            self.conn.commit()

        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "wall_required_hits": required_hits,
        }

    def add_mine_wall_hit(self, account_id, floor):
        floor = int(floor)
        progress = self.mine_progress(account_id)
        highest = progress["max_floor_unlocked"]
        hits = progress["wall_hits"]
        required_hits = progress["wall_required_hits"]

        if floor != highest:
            return {
                "max_floor_unlocked": highest,
                "wall_hits": hits,
                "wall_required_hits": required_hits,
                "unlocked_floor": None,
            }

        hits += 1
        unlocked_floor = None
        if hits >= required_hits:
            highest = highest + 1
            hits = 0
            unlocked_floor = highest
            required_hits = roll_mine_wall_hits_required(highest, 0)

        self.conn.execute(
            """
            UPDATE mine_progress
            SET max_floor_unlocked=?, wall_hits=?, wall_required_hits=?
            WHERE account_id=?
            """,
            (highest, hits, required_hits, account_id),
        )
        self.conn.commit()
        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "wall_required_hits": required_hits,
            "unlocked_floor": unlocked_floor,
        }

    def reset_mine_for_server_start(self):
        """v0.30.35: reset Kopalni Głębinowej przy każdym starcie procesu/deployu.

        Reset dotyczy wyłącznie wspólnego stanu przejścia Kopalni: odblokowanej
        głębokości oraz postępu bieżącej ściany. Nie dotyka Górnictwa, Kilofa,
        surowców, EQ, questów ani żadnej progresji postaci. Postacie zapisane
        wewnątrz dynamicznych pięter są przenoszone do wejścia, żeby po resecie
        nie pozostawały poniżej ponownie zamkniętej ściany.
        """
        progress_rows = int(self.conn.execute(
            "SELECT COUNT(*) AS n FROM mine_progress"
        ).fetchone()["n"] or 0)
        moved_rows = int(self.conn.execute(
            "SELECT COUNT(*) AS n FROM characters WHERE room_id LIKE 'mine_floor_%'"
        ).fetchone()["n"] or 0)
        self.conn.execute(
            "UPDATE mine_progress SET max_floor_unlocked=?, wall_hits=0, wall_required_hits=0",
            (MINE_MIN_FLOOR,),
        )
        self.conn.execute(
            "UPDATE characters SET room_id='crystal_chamber' WHERE room_id LIKE 'mine_floor_%'"
        )
        self.conn.commit()
        return {
            "progress_rows_reset": progress_rows,
            "characters_moved_to_entrance": moved_rows,
            "max_floor_unlocked": MINE_MIN_FLOOR,
            "wall_hits": 0,
        }

    def ensure_bank(self, account_id):
        # v0.8.32: waluta Banku Dusz jest również wspólna dla całego konta.
        currency_account_id = self.master_account_for_character(account_id)
        self.conn.execute(
            "INSERT OR IGNORE INTO bank_balances("
            "account_id,silver,gold,mithril"
            ") VALUES(?,0,0,0)",
            (currency_account_id,),
        )
        self.conn.commit()
        return currency_account_id

    def bank_balance(self, account_id):
        currency_account_id = self.ensure_bank(account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM bank_balances "
            "WHERE account_id=?",
            (currency_account_id,),
        ).fetchone()

        silver, gold, mithril = normalize_currency_values(
            row["silver"],
            row["gold"],
            row["mithril"],
        )

        if (
            silver != int(row["silver"])
            or gold != int(row["gold"])
            or mithril != int(row["mithril"])
        ):
            self.conn.execute(
                "UPDATE bank_balances "
                "SET silver=?, gold=?, mithril=? "
                "WHERE account_id=?",
                (silver, gold, mithril, currency_account_id),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT silver,gold,mithril FROM bank_balances "
                "WHERE account_id=?",
                (currency_account_id,),
            ).fetchone()

        return row

    def change_bank_currency(self, account_id, currency, amount):
        if currency not in ("silver", "gold", "mithril"):
            raise ValueError("Nieznana waluta bankowa.")

        currency_account_id = self.master_account_for_character(account_id)
        row = self.bank_balance(account_id)
        values = {
            "silver": int(row["silver"]),
            "gold": int(row["gold"]),
            "mithril": int(row["mithril"]),
        }
        values[currency] += int(amount)

        if values[currency] < 0:
            return False

        silver, gold, mithril = normalize_currency_values(
            values["silver"],
            values["gold"],
            values["mithril"],
        )

        self.conn.execute(
            "UPDATE bank_balances "
            "SET silver=?, gold=?, mithril=? "
            "WHERE account_id=?",
            (silver, gold, mithril, currency_account_id),
        )
        self.conn.commit()
        return True

    def bank_items(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM bank_items "
            "WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def bank_item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM bank_items "
            "WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        self.conn.execute(
            """
            INSERT INTO bank_items(account_id,item_id,quantity)
            VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def remove_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        current = self.bank_item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM bank_items "
                "WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE bank_items SET quantity=? "
                "WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def inventory(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM inventory WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        # v0.9.15: materiały rzemieślnicze nigdy nie zapychają zwykłego
        # inventory. Każde źródło używające add_item automatycznie kieruje
        # je do Szkatułki Rzemieślniczej.
        if item_id in CRAFT_MATERIAL_STORAGE_IDS:
            self.add_storage_item(account_id, "craftbox", item_id, qty)
            return
        self.conn.execute(
            """
            INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def mark_room_discovered(self, account_id, room_id):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rooms(account_id,room_id) VALUES(?,?)",
            (account_id, room_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def discovered_room_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT room_id FROM exploration_rooms WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["room_id"]) for row in rows}

    def claim_exploration_reward(self, account_id, zone):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rewards(account_id,zone) VALUES(?,?)",
            (account_id, zone),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def exploration_reward_claimed(self, account_id, zone):
        row = self.conn.execute(
            "SELECT 1 FROM exploration_rewards WHERE account_id=? AND zone=?",
            (account_id, zone),
        ).fetchone()
        return bool(row)

    def record_bestiary_kill(self, account_id, mob_template_id, kill_ms=None):
        mob_template_id = canonical_bestiary_template_id(mob_template_id)
        previous = self.conn.execute(
            "SELECT kills,fastest_kill_ms FROM bestiary_stats "
            "WHERE account_id=? AND mob_template_id=?",
            (account_id, mob_template_id),
        ).fetchone()
        is_new = previous is None
        old_fastest = int(previous["fastest_kill_ms"]) if previous and previous["fastest_kill_ms"] is not None else None
        clean_ms = None
        if kill_ms is not None:
            try:
                clean_ms = max(1, int(kill_ms))
            except (TypeError, ValueError):
                clean_ms = None
        self.conn.execute(
            """
            INSERT INTO bestiary_stats(
                account_id,mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at
            ) VALUES(?,?,1,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id,mob_template_id) DO UPDATE SET
                kills=bestiary_stats.kills+1,
                fastest_kill_ms=CASE
                    WHEN excluded.fastest_kill_ms IS NULL THEN bestiary_stats.fastest_kill_ms
                    WHEN bestiary_stats.fastest_kill_ms IS NULL THEN excluded.fastest_kill_ms
                    WHEN excluded.fastest_kill_ms < bestiary_stats.fastest_kill_ms THEN excluded.fastest_kill_ms
                    ELSE bestiary_stats.fastest_kill_ms
                END,
                last_killed_at=CURRENT_TIMESTAMP
            """,
            (account_id, mob_template_id, clean_ms),
        )
        self.conn.commit()
        row = self.bestiary_entry(account_id, mob_template_id)
        new_fastest = row["fastest_kill_ms"] if row else None
        is_record = (
            clean_ms is not None
            and new_fastest == clean_ms
            and (old_fastest is None or clean_ms < old_fastest)
        )
        return row, is_new, is_record

    def bestiary_entry(self, account_id, mob_template_id):
        mob_template_id = canonical_bestiary_template_id(mob_template_id)
        return self.conn.execute(
            "SELECT mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at "
            "FROM bestiary_stats WHERE account_id=? AND mob_template_id=?",
            (account_id, mob_template_id),
        ).fetchone()

    def bestiary_rows(self, account_id):
        return self.conn.execute(
            "SELECT mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at "
            "FROM bestiary_stats WHERE account_id=? ORDER BY kills DESC,mob_template_id",
            (account_id,),
        ).fetchall()

    def record_boss_codex_kill(self, account_id, boss_id, grouped=False):
        boss_id = canonical_bestiary_template_id(boss_id)
        if boss_id not in BOSS_COLLECTION_CATALOG:
            return None
        solo_inc = 0 if grouped else 1
        group_inc = 1 if grouped else 0
        self.conn.execute(
            "INSERT INTO boss_codex_stats(account_id,boss_id,solo_kills,group_kills) VALUES(?,?,?,?) "
            "ON CONFLICT(account_id,boss_id) DO UPDATE SET "
            "solo_kills=boss_codex_stats.solo_kills+excluded.solo_kills, "
            "group_kills=boss_codex_stats.group_kills+excluded.group_kills",
            (account_id, boss_id, solo_inc, group_inc),
        )
        self.conn.commit()
        return self.boss_codex_stats(account_id, boss_id)

    def boss_codex_stats(self, account_id, boss_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        return self.conn.execute(
            "SELECT boss_id,solo_kills,group_kills FROM boss_codex_stats "
            "WHERE account_id=? AND boss_id=?",
            (account_id, boss_id),
        ).fetchone()

    def add_boss_codex_drop(self, account_id, boss_id, item_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        if boss_id not in BOSS_COLLECTION_CATALOG or item_id not in ITEMS:
            return False
        if not boss_codex_drop_is_unique(item_id):
            return False
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO boss_codex_drops(account_id,boss_id,item_id) VALUES(?,?,?)",
            (account_id, boss_id, item_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def boss_codex_drops(self, account_id, boss_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        rows = self.conn.execute(
            "SELECT item_id,discovered_at FROM boss_codex_drops "
            "WHERE account_id=? AND boss_id=? ORDER BY discovered_at,item_id",
            (account_id, boss_id),
        ).fetchall()
        return rows

    def add_collection_entry(self, account_id, category, entry_id):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
            (account_id, category, entry_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def collection_entry_ids(self, account_id, category):
        rows = self.conn.execute(
            "SELECT entry_id FROM collection_codex WHERE account_id=? AND category=?",
            (account_id, category),
        ).fetchall()
        return {str(row["entry_id"]) for row in rows}

    def remove_collection_entry(self, account_id, category, entry_id):
        cur = self.conn.execute(
            "DELETE FROM collection_codex WHERE account_id=? AND category=? AND entry_id=?",
            (account_id, category, entry_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # v0.29.0: jeden aktywny Nemesis na konto. Rekord jest trwały i
    # bezpiecznie przechodzi przez restarty serwera.
    def nemesis_row_v029(self, account_id):
        return self.conn.execute(
            "SELECT * FROM nemesis_v029 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()

    def promote_nemesis_v029(self, account_id, base_template_id, base_name, player_name, level, room_id):
        account_id = int(account_id)
        previous = self.nemesis_row_v029(account_id)
        same = bool(previous and int(previous["active"] or 0) and str(previous["base_template_id"]) == str(base_template_id))
        rank = min(10, (int(previous["rank"] or 1) + 1) if same else 1)
        kills = (int(previous["kills_player"] or 0) + 1) if same else 1
        defeats = int(previous["defeats"] or 0) if previous else 0
        stage = max(1, min(400, int(level or 1) + (rank - 1) * 8))
        name = dynamic_world_v029.nemesis_name(str(base_name), account_id, str(player_name), rank)
        self.conn.execute(
            "INSERT INTO nemesis_v029(account_id,base_template_id,nemesis_name,rank,level,room_id,kills_player,defeats,active,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,1,CURRENT_TIMESTAMP) "
            "ON CONFLICT(account_id) DO UPDATE SET base_template_id=excluded.base_template_id,nemesis_name=excluded.nemesis_name,"
            "rank=excluded.rank,level=excluded.level,room_id=excluded.room_id,kills_player=excluded.kills_player,defeats=excluded.defeats,"
            "active=1,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(base_template_id), name, rank, stage, str(room_id), kills, defeats),
        )
        self.conn.commit()
        return self.nemesis_row_v029(account_id)

    def defeat_nemesis_v029(self, account_id):
        row = self.nemesis_row_v029(account_id)
        if not row:
            return None
        self.conn.execute(
            "UPDATE nemesis_v029 SET active=0,defeats=defeats+1,updated_at=CURRENT_TIMESTAMP WHERE account_id=?",
            (int(account_id),),
        )
        self.conn.commit()
        return self.nemesis_row_v029(account_id)


    # v0.21.0: trwała progresja po capie 400, World Tier i Endless Gauntlet.
    def ascension_row_v021(self, account_id, track):
        track=str(track or "")
        self.conn.execute(
            "INSERT OR IGNORE INTO ascension_progress_v021(account_id,track,rank,xp) VALUES(?,?,0,0)",
            (account_id,track),
        )
        self.conn.commit()
        return self.conn.execute(
            "SELECT track,rank,xp FROM ascension_progress_v021 WHERE account_id=? AND track=?",
            (account_id,track),
        ).fetchone()

    def add_ascension_xp_v021(self, account_id, track, amount):
        row=self.ascension_row_v021(account_id,track)
        rank=max(0,int(row["rank"] or 0)); xp=max(0,int(row["xp"] or 0)); gain=max(0,int(amount or 0))
        xp=min(V019_SAFE_INT,xp+gain); ups=0
        while rank < V021_ASCENSION_MAX_RANK:
            needed=v0210_ascension_xp_to_next(rank)
            if needed<=0 or xp<needed: break
            xp-=needed; rank+=1; ups+=1
        if rank>=V021_ASCENSION_MAX_RANK:
            rank=V021_ASCENSION_MAX_RANK; xp=0
        self.conn.execute(
            "UPDATE ascension_progress_v021 SET rank=?,xp=? WHERE account_id=? AND track=?",
            (rank,xp,account_id,str(track)),
        ); self.conn.commit()
        return {"track":str(track),"rank":rank,"xp":xp,"rank_ups":ups,"gain":gain,"next_xp":v0210_ascension_xp_to_next(rank)}

    def ascension_rows_v021(self, account_id):
        return self.conn.execute(
            "SELECT track,rank,xp FROM ascension_progress_v021 WHERE account_id=? ORDER BY rank DESC,track",
            (account_id,),
        ).fetchall()

    def world_tier_v021(self, account_id):
        self.conn.execute("INSERT OR IGNORE INTO world_tier_settings_v021(account_id,tier) VALUES(?,1)",(account_id,))
        self.conn.commit()
        row=self.conn.execute("SELECT tier FROM world_tier_settings_v021 WHERE account_id=?",(account_id,)).fetchone()
        return max(1,min(V021_WORLD_TIER_MAX,int(row["tier"] if row else 1)))

    def set_world_tier_v021(self, account_id, tier):
        tier=max(1,min(V021_WORLD_TIER_MAX,int(tier)))
        self.conn.execute(
            "INSERT INTO world_tier_settings_v021(account_id,tier) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET tier=excluded.tier",
            (account_id,tier),
        ); self.conn.commit(); return tier

    def endless_gauntlet_best_v021(self, account_id):
        self.conn.execute("INSERT OR IGNORE INTO endless_gauntlet_progress_v021(account_id,best_round) VALUES(?,0)",(account_id,))
        self.conn.commit()
        row=self.conn.execute("SELECT best_round FROM endless_gauntlet_progress_v021 WHERE account_id=?",(account_id,)).fetchone()
        return max(0,int(row["best_round"] if row else 0))

    def mark_endless_gauntlet_round_v021(self, account_id, round_no):
        round_no=max(0,int(round_no))
        self.conn.execute(
            "INSERT INTO endless_gauntlet_progress_v021(account_id,best_round) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET best_round=MAX(best_round,excluded.best_round)",
            (account_id,round_no),
        ); self.conn.commit(); return self.endless_gauntlet_best_v021(account_id)

    # v0.9.21: trwała mapa instancji, sekrety i checkpointy.
    def mark_instance_floor_visited(self, account_id, instance_kind, floor):
        instance_kind = str(instance_kind or "")
        floor = max(1, int(floor))
        previous = self.conn.execute(
            "SELECT 1 FROM instance_map_progress WHERE account_id=? AND instance_kind=? AND floor=?",
            (account_id, instance_kind, floor),
        ).fetchone()
        self.conn.execute(
            "INSERT INTO instance_map_progress(account_id,instance_kind,floor) VALUES(?,?,?) "
            "ON CONFLICT(account_id,instance_kind,floor) DO UPDATE SET last_visited_at=CURRENT_TIMESTAMP",
            (account_id, instance_kind, floor),
        )
        self.conn.commit()
        return previous is None

    def instance_visited_floors(self, account_id, instance_kind):
        rows = self.conn.execute(
            "SELECT floor FROM instance_map_progress WHERE account_id=? AND instance_kind=? ORDER BY floor",
            (account_id, str(instance_kind or "")),
        ).fetchall()
        return {int(row["floor"]) for row in rows}

    def instance_highest_floor(self, account_id, instance_kind):
        row = self.conn.execute(
            "SELECT MAX(floor) AS floor FROM instance_map_progress WHERE account_id=? AND instance_kind=?",
            (account_id, str(instance_kind or "")),
        ).fetchone()
        return int(row["floor"] or 0) if row else 0

    def mark_instance_secret(self, account_id, instance_kind, floor, secret_name):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO instance_map_secrets(account_id,instance_kind,floor,secret_name) VALUES(?,?,?,?)",
            (account_id, str(instance_kind or ""), max(1, int(floor)), str(secret_name or "Sekret")),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def instance_secret_rows(self, account_id, instance_kind):
        return self.conn.execute(
            "SELECT floor,secret_name,discovered_at FROM instance_map_secrets "
            "WHERE account_id=? AND instance_kind=? ORDER BY floor",
            (account_id, str(instance_kind or "")),
        ).fetchall()

    def mark_instance_checkpoint(self, account_id, instance_kind, floor):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO instance_map_checkpoints(account_id,instance_kind,floor) VALUES(?,?,?)",
            (account_id, str(instance_kind or ""), max(1, int(floor))),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def instance_checkpoint_floors(self, account_id, instance_kind):
        kind = str(instance_kind or "")
        result = {
            int(row["floor"])
            for row in self.conn.execute(
                "SELECT floor FROM instance_map_checkpoints WHERE account_id=? AND instance_kind=?",
                (account_id, kind),
            ).fetchall()
        }
        # Jednorazowo zaliczone bramki bossów są również checkpointami mapy.
        result.update(
            int(row["floor"])
            for row in self.conn.execute(
                "SELECT floor FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=?",
                (account_id, kind),
            ).fetchall()
        )
        # Zgodność starych save'ów, które miały tylko najwyższy portal.
        if kind == "crypt":
            highest = self.crypt_checkpoint(account_id)
            result.update(range(10, highest + 1, 10))
        elif kind == "astral":
            highest = self.astral_checkpoint(account_id)
            start = int(ASTRAL_MIN_FLOOR)
            if highest >= start:
                result.update(range(start, highest + 1, 10))
        return result

    def highest_boss_floor_cleared(self, account_id, instance_kind):
        floors = self.instance_checkpoint_floors(account_id, instance_kind)
        return max(floors) if floors else 0

    def treasure_chest_opened_at(self, account_id, room_id):
        row = self.conn.execute(
            "SELECT opened_at FROM treasure_chest_cooldowns WHERE account_id=? AND room_id=?",
            (account_id, room_id),
        ).fetchone()
        return int(row["opened_at"]) if row else 0

    def mark_treasure_chest_opened(self, account_id, room_id, opened_at=None):
        stamp = int(time.time() if opened_at is None else opened_at)
        self.conn.execute(
            "INSERT INTO treasure_chest_cooldowns(account_id,room_id,opened_at) VALUES(?,?,?) "
            "ON CONFLICT(account_id,room_id) DO UPDATE SET opened_at=excluded.opened_at",
            (account_id, room_id, stamp),
        )
        self.conn.commit()
        return stamp

    def achievement_metric(self, account_id, metric):
        row = self.conn.execute(
            "SELECT value FROM achievement_progress WHERE account_id=? AND metric=?",
            (account_id, metric),
        ).fetchone()
        return int(row["value"]) if row else 0

    def add_achievement_metric(self, account_id, metric, amount=1):
        self.conn.execute(
            """
            INSERT INTO achievement_progress(account_id,metric,value) VALUES(?,?,?)
            ON CONFLICT(account_id,metric)
            DO UPDATE SET value=value+excluded.value
            """,
            (account_id, metric, int(amount)),
        )
        self.conn.commit()
        return self.achievement_metric(account_id, metric)

    def set_achievement_metric_max(self, account_id, metric, value):
        value = max(0, int(value))
        self.conn.execute(
            """
            INSERT INTO achievement_progress(account_id,metric,value) VALUES(?,?,?)
            ON CONFLICT(account_id,metric) DO UPDATE SET
                value=MAX(achievement_progress.value, excluded.value)
            """,
            (account_id, metric, value),
        )
        self.conn.commit()
        return self.achievement_metric(account_id, metric)

    def unlock_achievement(self, account_id, achievement_id, name, tier):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO achievements(account_id,achievement_id,name,tier) VALUES(?,?,?,?)",
            (account_id, achievement_id, name, tier),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def achievement_rows(self, account_id):
        return self.conn.execute(
            "SELECT achievement_id,name,tier,unlocked_at FROM achievements "
            "WHERE account_id=? ORDER BY unlocked_at, achievement_id",
            (account_id,),
        ).fetchall()

    def unlock_title(self, account_id, title_id, title_name):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO unlocked_titles(account_id,title_id,title_name) VALUES(?,?,?)",
            (account_id, title_id, title_name),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def title_rows(self, account_id):
        return self.conn.execute(
            "SELECT title_id,title_name,unlocked_at FROM unlocked_titles "
            "WHERE account_id=? ORDER BY title_name COLLATE NOCASE",
            (account_id,),
        ).fetchall()

    def bounty_board_state(self, account_id):
        row = self.conn.execute(
            "SELECT offers_json,active_json,completed_count FROM bounty_boards WHERE account_id=?",
            (account_id,),
        ).fetchone()
        if not row:
            return {"offers": [], "active": {}, "completed_count": 0}
        try:
            offers = json.loads(row["offers_json"] or "[]")
        except Exception:
            offers = []
        try:
            active = json.loads(row["active_json"] or "{}")
        except Exception:
            active = {}
        if not isinstance(offers, list):
            offers = []
        if not isinstance(active, dict):
            active = {}
        return {
            "offers": offers,
            "active": active,
            "completed_count": max(0, int(row["completed_count"] or 0)),
        }

    def save_bounty_board_state(self, account_id, offers=None, active=None, completed_count=None):
        current = self.bounty_board_state(account_id)
        if offers is None:
            offers = current["offers"]
        if active is None:
            active = current["active"]
        if completed_count is None:
            completed_count = current["completed_count"]
        self.conn.execute(
            """
            INSERT INTO bounty_boards(account_id,offers_json,active_json,completed_count,updated_at)
            VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                offers_json=excluded.offers_json,
                active_json=excluded.active_json,
                completed_count=excluded.completed_count,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                account_id,
                json.dumps(list(offers or []), ensure_ascii=False, separators=(",", ":")),
                json.dumps(dict(active or {}), ensure_ascii=False, separators=(",", ":")),
                max(0, int(completed_count or 0)),
            ),
        )
        self.conn.commit()

    def dynamic_world_quest_v015(self, account_id):
        row = self.conn.execute(
            "SELECT * FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,)
        ).fetchone()
        return row

    def save_dynamic_world_quest_v015(self, account_id, quest):
        quest = dict(quest or {})
        self.conn.execute(
            """
            INSERT INTO dynamic_world_quests_v015(
                account_id,quest_key,quest_type,target,label,needed,progress,
                reward_soul_xp,reward_gold,accepted_slot,completed,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                quest_key=excluded.quest_key, quest_type=excluded.quest_type,
                target=excluded.target, label=excluded.label, needed=excluded.needed,
                progress=excluded.progress, reward_soul_xp=excluded.reward_soul_xp,
                reward_gold=excluded.reward_gold, accepted_slot=excluded.accepted_slot,
                completed=excluded.completed, updated_at=CURRENT_TIMESTAMP
            """,
            (account_id, str(quest.get("quest_key", "")), str(quest.get("quest_type", "")),
             str(quest.get("target", "any")), str(quest.get("label", "")),
             max(0,int(quest.get("needed",0))), max(0,int(quest.get("progress",0))),
             max(0,int(quest.get("reward_soul_xp",0))), max(0,int(quest.get("reward_gold",0))),
             int(quest.get("accepted_slot",0)), 1 if quest.get("completed") else 0)
        )
        self.conn.commit()

    def clear_dynamic_world_quest_v015(self, account_id):
        self.conn.execute("DELETE FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,))
        self.conn.commit()

    def faction_reputation_v016(self, account_id, faction_id):
        row = self.conn.execute(
            "SELECT reputation FROM faction_reputation_v016 WHERE account_id=? AND faction_id=?",
            (account_id, str(faction_id)),
        ).fetchone()
        return max(0, int(row["reputation"] or 0)) if row else 0

    def faction_reputations_v016(self, account_id):
        rows = self.conn.execute(
            "SELECT faction_id,reputation FROM faction_reputation_v016 WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["faction_id"]): max(0,int(row["reputation"] or 0)) for row in rows}

    def add_faction_reputation_v016(self, account_id, faction_id, amount=1):
        amount = max(0, int(amount or 0))
        if amount <= 0:
            return self.faction_reputation_v016(account_id, faction_id)
        self.conn.execute(
            "INSERT INTO faction_reputation_v016(account_id,faction_id,reputation) VALUES(?,?,?) "
            "ON CONFLICT(account_id,faction_id) DO UPDATE SET "
            "reputation=faction_reputation_v016.reputation+excluded.reputation,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(faction_id), amount),
        )
        self.conn.commit()
        return self.faction_reputation_v016(account_id, faction_id)

    def lifetime_stat(self, account_id, stat_key):
        row = self.conn.execute(
            "SELECT value FROM lifetime_statistics WHERE account_id=? AND stat_key=?",
            (account_id, str(stat_key)),
        ).fetchone()
        return max(0, int(row["value"] or 0)) if row else 0

    def add_lifetime_stat(self, account_id, stat_key, amount=1):
        amount = int(amount or 0)
        if amount <= 0:
            return self.lifetime_stat(account_id, stat_key)
        self.conn.execute(
            "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
            "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
            "value=lifetime_statistics.value+excluded.value,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(stat_key), amount),
        )
        self.conn.commit()
        return self.lifetime_stat(account_id, stat_key)

    def set_lifetime_stat_max(self, account_id, stat_key, value):
        value = max(0, int(value or 0))
        self.conn.execute(
            "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
            "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
            "value=MAX(lifetime_statistics.value,excluded.value),updated_at=CURRENT_TIMESTAMP",
            (account_id, str(stat_key), value),
        )
        self.conn.commit()
        return self.lifetime_stat(account_id, stat_key)

    def lifetime_stats(self, account_id):
        rows = self.conn.execute(
            "SELECT stat_key,value FROM lifetime_statistics WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["stat_key"]): max(0, int(row["value"] or 0)) for row in rows}

    def fish_journal_entry(self, account_id, fish_id):
        return self.conn.execute(
            "SELECT * FROM fish_journal WHERE account_id=? AND fish_id=?",
            (account_id, base_fish_species_id(fish_id)),
        ).fetchone()

    def fish_journal_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM fish_journal WHERE account_id=? ORDER BY caught_count DESC, fish_id",
            (account_id,),
        ).fetchall()

    def fish_journal_ids(self, account_id):
        return {str(row["fish_id"]) for row in self.fish_journal_rows(account_id)}

    def record_fish_catch(self, account_id, fish_id, quantity, length_mm, weight_g, room_id):
        fish_id = base_fish_species_id(fish_id)
        quantity = max(1, int(quantity or 1))
        length_mm = max(0, int(length_mm or 0))
        weight_g = max(0, int(weight_g or 0))
        room_id = str(room_id or "")
        old = self.fish_journal_entry(account_id, fish_id)
        old_length = int(old["best_length_mm"] or 0) if old else 0
        old_weight = int(old["best_weight_g"] or 0) if old else 0
        result = {
            "new_species": old is None,
            "new_length_record": length_mm > old_length,
            "new_weight_record": weight_g > old_weight,
        }
        self.conn.execute(
            """
            INSERT INTO fish_journal(
                account_id,fish_id,caught_count,best_length_mm,best_weight_g,
                first_room_id,last_room_id,first_caught_at,last_caught_at
            ) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id,fish_id) DO UPDATE SET
                caught_count=fish_journal.caught_count+excluded.caught_count,
                best_length_mm=MAX(fish_journal.best_length_mm,excluded.best_length_mm),
                best_weight_g=MAX(fish_journal.best_weight_g,excluded.best_weight_g),
                last_room_id=excluded.last_room_id,
                last_caught_at=CURRENT_TIMESTAMP
            """,
            (account_id, fish_id, quantity, length_mm, weight_g, room_id, room_id),
        )
        self.conn.commit()
        row = self.fish_journal_entry(account_id, fish_id)
        result.update({
            "caught_count": int(row["caught_count"] or 0),
            "best_length_mm": int(row["best_length_mm"] or 0),
            "best_weight_g": int(row["best_weight_g"] or 0),
        })
        return result

    # ---------------- v0.22.0 persistent systems ----------------
    def record_fishing_global_v022(self, fish_id, item_id, holder_name, length_mm, weight_g, account_id=None):
        fish_id=base_fish_species_id(fish_id); item_id=str(item_id or fish_id); holder_name=str(holder_name or "Nieznany")
        length_mm=max(0,int(length_mm or 0)); weight_g=max(0,int(weight_g or 0))
        row=self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(fish_id,)).fetchone()
        old_l=int(row["best_length_mm"] or 0) if row else 0; old_w=int(row["best_weight_g"] or 0) if row else 0
        new_l=length_mm>old_l; new_w=weight_g>old_w
        best_l=max(old_l,length_mm); best_w=max(old_w,weight_g)
        lholder=holder_name if new_l else (str(row["length_holder"] or "") if row else "")
        wholder=holder_name if new_w else (str(row["weight_holder"] or "") if row else "")
        self.conn.execute("""INSERT INTO fish_global_records_v022(fish_id,best_length_mm,length_holder,best_weight_g,weight_holder,updated_at) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(fish_id) DO UPDATE SET best_length_mm=excluded.best_length_mm,length_holder=excluded.length_holder,best_weight_g=excluded.best_weight_g,weight_holder=excluded.weight_holder,updated_at=CURRENT_TIMESTAMP""",
            (fish_id,best_l,lholder,best_w,wholder))
        score=v022_fish_rarity_score(item_id); rare=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()
        old_score=int(rare["rarity_score"] or 0) if rare else 0; old_rare_weight=int(rare["weight_g"] or 0) if rare else 0
        new_rare=score>old_score or (score==old_score and weight_g>old_rare_weight)
        if new_rare:
            self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES('global',?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
                (score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
        new_personal_rare=False
        if account_id is not None:
            pkey=f"account:{int(account_id)}"; personal=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(pkey,)).fetchone()
            pscore=int(personal["rarity_score"] or 0) if personal else 0; pweight=int(personal["weight_g"] or 0) if personal else 0
            new_personal_rare=score>pscore or (score==pscore and weight_g>pweight)
            if new_personal_rare:
                self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                    ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
                    (pkey,score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
        self.conn.commit(); return {"new_global_length":new_l,"new_global_weight":new_w,"new_global_rarest":new_rare,"new_personal_rarest":new_personal_rare}

    def fish_global_record_v022(self, fish_id):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(base_fish_species_id(fish_id),)).fetchone()

    def fish_global_top_v022(self, limit=5):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 ORDER BY best_weight_g DESC,best_length_mm DESC LIMIT ?",(max(1,min(20,int(limit))),)).fetchall()

    def fish_rarest_global_v022(self):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()

    def fish_rarest_personal_v022(self, account_id):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(f"account:{int(account_id)}",)).fetchone()

    def world_project_state_v022(self, project_id):
        project_id=str(project_id); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        if not row:
            self.conn.execute("INSERT INTO world_projects_v022(project_id,progress_json,completed) VALUES(?,'{}',0)",(project_id,)); self.conn.commit(); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        try: progress=json.loads(row["progress_json"] or "{}")
        except Exception: progress={}
        return {"project_id":project_id,"progress":progress if isinstance(progress,dict) else {},"completed":bool(row["completed"]),"completed_at":row["completed_at"]}

    def world_project_contribution_v022(self, project_id, account_id):
        row=self.conn.execute("SELECT * FROM world_project_contributions_v022 WHERE project_id=? AND account_id=?",(project_id,account_id)).fetchone()
        if not row: return {"points":0,"coins":0,"resources":{},"reward_claimed":False}
        try: resources=json.loads(row["resources_json"] or "{}")
        except Exception: resources={}
        return {"points":int(row["points"] or 0),"coins":int(row["coins"] or 0),"resources":resources if isinstance(resources,dict) else {},"reward_claimed":bool(row["reward_claimed"])}

    def add_world_project_contribution_v022(self, project_id, account_id, category, amount, points):
        spec=V022_WORLD_PROJECTS[project_id]; state=self.world_project_state_v022(project_id); progress=dict(state["progress"]); category=str(category); amount=max(0,int(amount)); points=max(0,int(points))
        need=int(spec["requirements"].get(category,0)); old=int(progress.get(category,0) or 0); accepted=min(amount,max(0,need-old))
        if accepted<=0: return {"accepted":0,"completed":state["completed"],"newly_completed":False,"progress":progress}
        progress[category]=old+accepted
        completed=all(int(progress.get(k,0) or 0)>=int(v) for k,v in spec["requirements"].items())
        newly=completed and not state["completed"]
        self.conn.execute("UPDATE world_projects_v022 SET progress_json=?,completed=?,completed_at=CASE WHEN ?=1 AND completed=0 THEN CURRENT_TIMESTAMP ELSE completed_at END WHERE project_id=?",(json.dumps(progress,ensure_ascii=False,separators=(",",":")),1 if completed else 0,1 if completed else 0,project_id))
        cur=self.world_project_contribution_v022(project_id,account_id); resources=dict(cur["resources"]); coins=int(cur["coins"]);
        if category=="coins": coins+=accepted
        else: resources[category]=int(resources.get(category,0) or 0)+accepted
        self.conn.execute("""INSERT INTO world_project_contributions_v022(project_id,account_id,points,resources_json,coins,reward_claimed,updated_at) VALUES(?,?,?,?,?,0,CURRENT_TIMESTAMP)
            ON CONFLICT(project_id,account_id) DO UPDATE SET points=world_project_contributions_v022.points+excluded.points,resources_json=excluded.resources_json,coins=excluded.coins,updated_at=CURRENT_TIMESTAMP""",
            (project_id,account_id,points,json.dumps(resources,ensure_ascii=False,separators=(",",":")),coins))
        self.conn.commit(); return {"accepted":accepted,"completed":completed,"newly_completed":newly,"progress":progress}

    def mark_world_project_reward_claimed_v022(self, project_id, account_id):
        cur=self.conn.execute("UPDATE world_project_contributions_v022 SET reward_claimed=1,updated_at=CURRENT_TIMESTAMP WHERE project_id=? AND account_id=? AND reward_claimed=0",(project_id,account_id)); self.conn.commit(); return cur.rowcount>0

    def legendary_contract_state_v022(self, account_id):
        row=self.conn.execute("SELECT * FROM legendary_contracts_v022 WHERE account_id=?",(account_id,)).fetchone()
        if not row: return {"offers":[],"active":{},"completed_count":0}
        try: offers=json.loads(row["offers_json"] or "[]")
        except Exception: offers=[]
        try: active=json.loads(row["active_json"] or "{}")
        except Exception: active={}
        return {"offers":offers if isinstance(offers,list) else [],"active":active if isinstance(active,dict) else {},"completed_count":int(row["completed_count"] or 0)}

    def save_legendary_contract_state_v022(self, account_id, offers=None, active=None, completed_count=None):
        cur=self.legendary_contract_state_v022(account_id); offers=cur["offers"] if offers is None else offers; active=cur["active"] if active is None else active; completed_count=cur["completed_count"] if completed_count is None else completed_count
        self.conn.execute("""INSERT INTO legendary_contracts_v022(account_id,offers_json,active_json,completed_count,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET offers_json=excluded.offers_json,active_json=excluded.active_json,completed_count=excluded.completed_count,updated_at=CURRENT_TIMESTAMP""",
            (account_id,json.dumps(list(offers or []),ensure_ascii=False,separators=(",",":")),json.dumps(dict(active or {}),ensure_ascii=False,separators=(",",":")),max(0,int(completed_count or 0))))
        self.conn.commit()

    def add_drop_history(self, account_id, item_id, item_name, rarity, source, zone):
        self.conn.execute(
            "INSERT INTO drop_history(account_id,item_id,item_name,rarity,source,zone) "
            "VALUES(?,?,?,?,?,?)",
            (account_id, item_id, item_name, rarity, source, zone),
        )
        self.conn.execute(
            "DELETE FROM drop_history WHERE account_id=? AND id NOT IN ("
            "SELECT id FROM drop_history WHERE account_id=? ORDER BY id DESC LIMIT ?)",
            (account_id, account_id, DROP_HISTORY_LIMIT),
        )
        self.conn.commit()

    def drop_history_rows(self, account_id, limit=20):
        return self.conn.execute(
            "SELECT item_name,rarity,source,zone,created_at FROM drop_history "
            "WHERE account_id=? ORDER BY id DESC LIMIT ?",
            (account_id, max(1, min(DROP_HISTORY_LIMIT, int(limit)))),
        ).fetchall()

    def remove_item(self, account_id, item_id, qty=1):
        current = self.item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def transfer_inventory_item(self, from_account_id, to_account_id, item_id, qty=1):
        """Atomowo przenosi zwykły item inventory między dwiema postaciami."""
        qty = max(1, int(qty))
        if from_account_id == to_account_id:
            return False
        current = self.item_qty(from_account_id, item_id)
        if current < qty:
            return False
        try:
            self.conn.execute("BEGIN")
            new_qty = current - qty
            if new_qty <= 0:
                self.conn.execute(
                    "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                    (from_account_id, item_id),
                )
            else:
                self.conn.execute(
                    "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                    (new_qty, from_account_id, item_id),
                )
            self.conn.execute(
                """
                INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
                ON CONFLICT(account_id,item_id)
                DO UPDATE SET quantity=quantity+excluded.quantity
                """,
                (to_account_id, item_id, qty),
            )
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise

    def transfer_shared_currency(self, from_character_account_id, to_character_account_id, amount_silver):
        """Atomowy transfer wspólnego salda konta między dwoma różnymi kontami."""
        amount_silver = int(amount_silver or 0)
        if amount_silver <= 0:
            return False
        from_master = self.master_account_for_character(from_character_account_id)
        to_master = self.master_account_for_character(to_character_account_id)
        if from_master == to_master:
            return False
        from_total = int(self.shared_wallet_for_master(from_master)[0])
        to_total = int(self.shared_wallet_for_master(to_master)[0])
        if from_total < amount_silver:
            return False
        if to_total + amount_silver > CURRENCY_SQLITE_SAFE_TOTAL:
            return False
        try:
            self.conn.execute("BEGIN")
            self.set_shared_wallet_for_master(
                from_master, from_total - amount_silver, 0, 0, commit=False
            )
            self.set_shared_wallet_for_master(
                to_master, to_total + amount_silver, 0, 0, commit=False
            )
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            raise

    def ensure_class_progress(self, account_id, class_name):
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,NULL)",
            (account_id, class_name),
        )
        self.conn.commit()

    def ensure_primary_class(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND active_slot=1 AND class_name<>?",
            (account_id, class_name),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()

    def class_progress_row(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()

    def active_class_rows(self, account_id, primary_class):
        self.ensure_primary_class(account_id, primary_class)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND active_slot IS NOT NULL "
            "ORDER BY active_slot",
            (account_id,),
        ).fetchall()

    def active_class_names(self, account_id, primary_class):
        return [
            row["class_name"]
            for row in self.active_class_rows(account_id, primary_class)
        ]

    def activate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        rows = self.active_class_rows(account_id, primary_class)
        active_names = [row["class_name"] for row in rows]

        if class_name in active_names:
            return False, "Ta klasa jest już aktywna."
        if len(active_names) >= MULTICLASS_MAX_ACTIVE:
            return False, "Masz już maksymalnie 3 aktywne klasy."

        used_slots = {
            int(row["active_slot"])
            for row in rows
            if row["active_slot"] is not None
        }
        slot = next(
            number for number in range(2, MULTICLASS_MAX_ACTIVE + 1)
            if number not in used_slots
        )

        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=? "
            "WHERE account_id=? AND class_name=?",
            (slot, account_id, class_name),
        )
        self.conn.commit()
        return True, slot

    def deactivate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        if class_name == primary_class:
            return False, "Nie można wyłączyć klasy głównej."

        row = self.conn.execute(
            "SELECT active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()
        if not row or row["active_slot"] is None:
            return False, "Ta klasa nie jest aktywna."

        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()
        return True, None

    def add_class_mastery_xp(self, account_id, class_name, amount):
        self.ensure_class_progress(account_id, class_name)
        row = self.class_progress_row(account_id, class_name)
        level = int(row["level"])
        xp = int(row["xp"])
        gain = max(0, int(amount))
        xp += gain
        level_ups = 0

        while level < CLASS_MASTERY_MAX_LEVEL:
            needed = class_mastery_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        overflow_xp = 0
        if level >= CLASS_MASTERY_MAX_LEVEL:
            level = CLASS_MASTERY_MAX_LEVEL
            overflow_xp = max(0, int(xp))
            xp = 0

        self.conn.execute(
            "UPDATE class_progress SET level=?,xp=? "
            "WHERE account_id=? AND class_name=?",
            (level, xp, account_id, class_name),
        )
        self.conn.commit()
        return {
            "class_name": class_name,
            "level": level,
            "xp": xp,
            "level_ups": level_ups,
            "next_xp": class_mastery_xp_to_next(level),
            "gain": gain,
            "overflow_xp": overflow_xp,
        }

    def skill_queue_rows(self, account_id, queue_type=None):
        if queue_type is None:
            return self.conn.execute(
                "SELECT queue_type,position,skill_id FROM skill_queue "
                "WHERE account_id=? ORDER BY CASE queue_type WHEN 'physical' THEN 0 ELSE 1 END, position",
                (account_id,),
            ).fetchall()
        return self.conn.execute(
            "SELECT queue_type,position,skill_id FROM skill_queue "
            "WHERE account_id=? AND queue_type=? ORDER BY position",
            (account_id, queue_type),
        ).fetchall()

    def skill_queue_enabled(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_queue_settings(account_id,enabled) VALUES(?,0)",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT enabled FROM skill_queue_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return bool(row and int(row["enabled"]))

    def set_skill_queue_enabled(self, account_id, enabled):
        self.conn.execute(
            "INSERT INTO skill_queue_settings(account_id,enabled) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET enabled=excluded.enabled",
            (account_id, 1 if enabled else 0),
        )
        self.conn.commit()

    def combat_log_mode(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO combat_log_settings(account_id,mode) VALUES(?, 'normal')",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT mode FROM combat_log_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        mode = str(row["mode"] if row else "normal").lower()
        return mode if mode in ("concise", "normal", "full") else "normal"

    def set_combat_log_mode(self, account_id, mode):
        mode = str(mode or "normal").lower()
        if mode not in ("concise", "normal", "full"):
            mode = "normal"
        self.conn.execute(
            "INSERT INTO combat_log_settings(account_id,mode) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET mode=excluded.mode",
            (account_id, mode),
        )
        self.conn.commit()
        return mode

    def wimpy_percent(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO wimpy_settings(account_id,percent) VALUES(?,0)",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT percent FROM wimpy_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        value = int(row["percent"] if row else 0)
        return max(0, min(99, value))

    def set_wimpy_percent(self, account_id, percent):
        percent = max(0, min(99, int(percent or 0)))
        self.conn.execute(
            "INSERT INTO wimpy_settings(account_id,percent) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET percent=excluded.percent",
            (account_id, percent),
        )
        self.conn.commit()
        return percent

    def replace_skill_queue(self, account_id, queue_type, skill_ids):
        queue_type = str(queue_type)
        skill_ids = list(skill_ids)
        self.conn.execute(
            "DELETE FROM skill_queue WHERE account_id=? AND queue_type=?",
            (account_id, queue_type),
        )
        for index, skill_id in enumerate(skill_ids, 1):
            self.conn.execute(
                "INSERT INTO skill_queue(account_id,queue_type,position,skill_id) VALUES(?,?,?,?)",
                (account_id, queue_type, index, skill_id),
            )
        self.conn.commit()

    def add_skill_queue_entry(self, account_id, queue_type, skill_id):
        exists = self.conn.execute(
            "SELECT queue_type,position FROM skill_queue WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()
        if exists:
            return False, f"Umiejętność jest już w kolejce {exists['queue_type']} na pozycji {exists['position']}."
        row = self.conn.execute(
            "SELECT COALESCE(MAX(position),0) AS max_position FROM skill_queue "
            "WHERE account_id=? AND queue_type=?",
            (account_id, queue_type),
        ).fetchone()
        position = int(row["max_position"]) + 1
        self.conn.execute(
            "INSERT INTO skill_queue(account_id,queue_type,position,skill_id) VALUES(?,?,?,?)",
            (account_id, queue_type, position, skill_id),
        )
        self.conn.commit()
        return True, position

    def remove_skill_queue_entry(self, account_id, queue_type, position):
        rows = self.skill_queue_rows(account_id, queue_type)
        skill_ids = [row["skill_id"] for row in rows]
        index = int(position) - 1
        if index < 0 or index >= len(skill_ids):
            return None
        removed = skill_ids.pop(index)
        self.replace_skill_queue(account_id, queue_type, skill_ids)
        return removed

    def remove_skill_queue_skill(self, account_id, skill_id):
        row = self.conn.execute(
            "SELECT queue_type,position FROM skill_queue WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()
        if not row:
            return None
        return self.remove_skill_queue_entry(
            account_id, row["queue_type"], int(row["position"])
        )

    def clear_skill_queue(self, account_id, queue_type=None):
        if queue_type is None:
            self.conn.execute(
                "DELETE FROM skill_queue WHERE account_id=?",
                (account_id,),
            )
        else:
            self.conn.execute(
                "DELETE FROM skill_queue WHERE account_id=? AND queue_type=?",
                (account_id, queue_type),
            )
        self.conn.commit()

    def move_skill_queue_entry(self, account_id, queue_type, position, delta):
        rows = self.skill_queue_rows(account_id, queue_type)
        skill_ids = [row["skill_id"] for row in rows]
        index = int(position) - 1
        target = index + int(delta)
        if index < 0 or index >= len(skill_ids) or target < 0 or target >= len(skill_ids):
            return False
        skill_ids[index], skill_ids[target] = skill_ids[target], skill_ids[index]
        self.replace_skill_queue(account_id, queue_type, skill_ids)
        return True

    def learned_skill_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT skill_id FROM learned_skills WHERE account_id=? ORDER BY learned_at, skill_id",
            (account_id,),
        ).fetchall()
        return {row["skill_id"] for row in rows}

    def knows_skill(self, account_id, skill_id):
        return self.conn.execute(
            "SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone() is not None

    def learn_skill(self, account_id, skill_id):
        before = self.conn.total_changes
        self.conn.execute(
            "INSERT OR IGNORE INTO learned_skills(account_id,skill_id) VALUES(?,?)",
            (account_id, skill_id),
        )
        self.conn.commit()
        learned_now = self.conn.total_changes > before
        self.ensure_skill_progress(account_id, skill_id)
        return learned_now

    def ensure_skill_progress(self, account_id, skill_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_progress(account_id,skill_id,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, skill_id),
        )
        self.conn.commit()

    def skill_progress(self, account_id, skill_id):
        self.ensure_skill_progress(account_id, skill_id)
        return self.conn.execute(
            "SELECT level,xp,uses FROM skill_progress WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()

    def add_skill_xp(self, account_id, skill_id, amount):
        self.ensure_skill_progress(account_id, skill_id)
        row = self.skill_progress(account_id, skill_id)
        level = int(row["level"])
        xp = int(row["xp"]) + max(0, int(amount))
        uses = int(row["uses"]) + 1
        level_ups = 0

        while level < SKILL_MAX_LEVEL:
            needed = skill_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        if level >= SKILL_MAX_LEVEL:
            level = SKILL_MAX_LEVEL
            xp = 0

        self.conn.execute(
            "UPDATE skill_progress SET level=?,xp=?,uses=? WHERE account_id=? AND skill_id=?",
            (level, xp, uses, account_id, skill_id),
        )
        self.conn.commit()
        return {
            "level": level,
            "xp": xp,
            "uses": uses,
            "level_ups": level_ups,
            "next_xp": skill_xp_to_next(level),
        }

    def equipment(self, account_id):
        return self.conn.execute(
            "SELECT slot,item_id FROM equipment WHERE account_id=? ORDER BY slot",
            (account_id,),
        ).fetchall()

    def equipped_item(self, account_id, slot):
        row = self.conn.execute(
            "SELECT item_id FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        ).fetchone()
        return row["item_id"] if row else None

    def equip(self, account_id, slot, item_id):
        self.conn.execute(
            """
            INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)
            ON CONFLICT(account_id,slot) DO UPDATE SET item_id=excluded.item_id
            """,
            (account_id, slot, item_id),
        )
        self.conn.commit()

    def unequip(self, account_id, slot):
        self.conn.execute(
            "DELETE FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()

    def socketed_gems(self, account_id, slot, jewelry_item_id=None):
        if jewelry_item_id is None:
            return self.conn.execute(
                "SELECT socket_index,jewelry_item_id,gem_id "
                "FROM equipment_gems "
                "WHERE account_id=? AND slot=? "
                "ORDER BY socket_index",
                (account_id, slot),
            ).fetchall()
        return self.conn.execute(
            "SELECT socket_index,jewelry_item_id,gem_id "
            "FROM equipment_gems "
            "WHERE account_id=? AND slot=? AND jewelry_item_id=? "
            "ORDER BY socket_index",
            (account_id, slot, jewelry_item_id),
        ).fetchall()

    def add_socketed_gem(
        self, account_id, slot, jewelry_item_id,
        socket_index, gem_id,
    ):
        self.conn.execute(
            """
            INSERT INTO equipment_gems(
                account_id,slot,socket_index,jewelry_item_id,gem_id
            ) VALUES(?,?,?,?,?)
            ON CONFLICT(account_id,slot,socket_index)
            DO UPDATE SET
                jewelry_item_id=excluded.jewelry_item_id,
                gem_id=excluded.gem_id
            """,
            (
                account_id, slot, int(socket_index),
                jewelry_item_id, gem_id,
            ),
        )
        self.conn.commit()

    def clear_socketed_gems(self, account_id, slot):
        rows = self.socketed_gems(account_id, slot)
        self.conn.execute(
            "DELETE FROM equipment_gems "
            "WHERE account_id=? AND slot=?",
            (account_id, slot),
        )
        self.conn.commit()
        return rows

    def ensure_profession(self, account_id, profession):
        self.conn.execute(
            "INSERT OR IGNORE INTO professions(account_id,profession,level,xp,actions) VALUES(?,?,1,0,0)",
            (account_id, profession),
        )
        self.conn.commit()

    def profession(self, account_id, profession):
        self.ensure_profession(account_id, profession)
        return self.conn.execute(
            "SELECT * FROM professions WHERE account_id=? AND profession=?",
            (account_id, profession),
        ).fetchone()

    def save_profession(self, account_id, profession, level, xp, actions):
        self.conn.execute(
            "UPDATE professions SET level=?,xp=?,actions=? WHERE account_id=? AND profession=?",
            (level, xp, actions, account_id, profession),
        )
        self.conn.commit()

    def ensure_tool(self, account_id, tool_type):
        self.conn.execute(
            "INSERT OR IGNORE INTO tools(account_id,tool_type,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, tool_type),
        )
        self.conn.commit()

    def tool(self, account_id, tool_type):
        self.ensure_tool(account_id, tool_type)
        return self.conn.execute(
            "SELECT * FROM tools WHERE account_id=? AND tool_type=?",
            (account_id, tool_type),
        ).fetchone()

    def save_tool(self, account_id, tool_type, level, xp, uses):
        self.conn.execute(
            "UPDATE tools SET level=?,xp=?,uses=? WHERE account_id=? AND tool_type=?",
            (level, xp, uses, account_id, tool_type),
        )
        self.conn.commit()

    def storage_rows(self, account_id, container):
        return self.conn.execute(
            "SELECT item_id,quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND quantity>0 ORDER BY item_id",
            (account_id, container),
        ).fetchall()

    def storage_qty(self, account_id, container, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND item_id=?",
            (account_id, container, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_storage_item(self, account_id, container, item_id, qty=1):
        self.conn.execute(
            """
            INSERT INTO profession_storage(account_id,container,item_id,quantity)
            VALUES(?,?,?,?)
            ON CONFLICT(account_id,container,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, container, item_id, qty),
        )
        self.conn.commit()

    def remove_storage_item(self, account_id, container, item_id, qty=1):
        current = self.storage_qty(account_id, container, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM profession_storage "
                "WHERE account_id=? AND container=? AND item_id=?",
                (account_id, container, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE profession_storage SET quantity=? "
                "WHERE account_id=? AND container=? AND item_id=?",
                (new_qty, account_id, container, item_id),
            )
        self.conn.commit()
        return True

    def total_items_across_storage_and_inventory(self, account_id, item_ids, container=None):
        total = 0
        for item_id in item_ids:
            total += self.item_qty(account_id, item_id)
            if container:
                total += self.storage_qty(account_id, container, item_id)
        return total

    def consume_items_across_storage_and_inventory(self, account_id, item_ids, needed, container=None):
        remaining = needed

        if container:
            for item_id in sorted(item_ids):
                if remaining <= 0:
                    break
                qty = self.storage_qty(account_id, container, item_id)
                take = min(qty, remaining)
                if take > 0:
                    self.remove_storage_item(account_id, container, item_id, take)
                    remaining -= take

        for item_id in sorted(item_ids):
            if remaining <= 0:
                break
            qty = self.item_qty(account_id, item_id)
            take = min(qty, remaining)
            if take > 0:
                self.remove_item(account_id, item_id, take)
                remaining -= take

        return remaining == 0

    def quest(self, account_id, quest_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        ).fetchone()

    def start_quest(self, account_id, quest_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO quests("
            "account_id,quest_id,status,progress,completed_at,completion_count"
            ") VALUES(?,?, 'active',0,0,0)",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def restart_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='active',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def set_quest_progress(self, account_id, quest_id, progress):
        self.conn.execute(
            "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
            (max(0, int(progress)), account_id, quest_id),
        )
        self.conn.commit()

    def abandon_quest(self, account_id, quest_id):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "active":
            return False
        # Nie kasujemy completion_count ani completed_at: historia wcześniejszych
        # ukończeń ma pozostać. Porzucenie kasuje tylko bieżące podejście/postęp.
        self.conn.execute(
            "UPDATE quests SET status='abandoned',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()
        return True

    def repeat_quest_seconds_remaining(self, account_id, quest_id, cooldown):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "completed":
            return 0
        completed_at = int(row["completed_at"] or 0)
        if completed_at <= 0:
            return 0
        elapsed = max(0, int(time.time()) - completed_at)
        return max(0, int(cooldown) - elapsed)

    def quest_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? ORDER BY status,quest_id",
            (account_id,),
        ).fetchall()

    def increment_quest(self, account_id, target):
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            q = QUESTS.get(row["quest_id"])
            if not q or q["kind"] != "kill" or q["target"] != target:
                continue
            new_progress = min(q["needed"], row["progress"] + 1)
            # v0.30.7: gotowy quest nie ogłasza ponownie tego samego
            # stanu po każdym kolejnym zabiciu tego samego celu.
            if int(new_progress) == int(row["progress"]):
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress))
        self.conn.commit()
        return changed

    def increment_item_collect_quest(self, account_id, item_id, amount=1):
        """v0.8.66: zwykłe collect liczy wyłącznie nowe zdobycze po przyjęciu."""
        amount = max(0, int(amount))
        if amount <= 0:
            return []
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if (
                not quest
                or quest.get("kind") != "collect"
                or quest.get("track_craft_progress")
                or quest.get("target") != item_id
            ):
                continue
            needed = max(1, int(quest.get("needed", 1)))
            old_progress = max(0, int(row["progress"]))
            new_progress = min(needed, old_progress + amount)
            if new_progress == old_progress:
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress, needed))
        self.conn.commit()
        return changed

    def increment_craft_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if not quest or not quest.get(
                "track_craft_progress"
            ):
                continue

            if quest.get("kind") == "collect":
                if quest.get("target") != item_id:
                    continue
                needed = max(
                    1, int(quest.get("needed", 1))
                )
                old_progress = int(row["progress"])
                new_progress = min(
                    needed,
                    old_progress + amount,
                )
                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_progress,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        new_progress,
                        needed,
                    )
                )
                continue

            if quest.get("kind") == "craft_set":
                targets = tuple(
                    quest.get("targets") or ()
                )
                if item_id not in targets:
                    continue

                index = targets.index(item_id)
                old_mask = int(row["progress"])
                new_mask = old_mask | (1 << index)
                if new_mask == old_mask:
                    continue

                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_mask,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        int(new_mask).bit_count(),
                        len(targets),
                    )
                )

        self.conn.commit()
        return changed

    def increment_resource_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        progress_item_id = canonical_profession_resource_id(item_id)
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            quest_target = canonical_profession_resource_id(
                quest.get("target") if quest else ""
            )
            if (
                not quest
                or quest.get("kind") != "collect_resource"
                or not quest.get("track_resource_progress")
                or quest_target != progress_item_id
            ):
                continue

            needed = max(
                1, int(quest.get("needed", 1))
            )
            old_progress = int(row["progress"])
            new_progress = min(
                needed,
                old_progress + amount,
            )
            # v0.30.7: po osiągnięciu celu nie zwracamy sztucznej
            # "zmiany" 30->30. Dzięki temu komunikat o gotowości questa
            # nie powtarza się przy każdym następnym zbiorze.
            if new_progress == old_progress:
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? "
                "WHERE account_id=? AND quest_id=?",
                (
                    new_progress,
                    account_id,
                    row["quest_id"],
                ),
            )
            changed.append(
                (
                    row["quest_id"],
                    new_progress,
                    needed,
                )
            )

        self.conn.commit()
        return changed

    def resource_set_progress_v0929(self, account_id, quest_id, targets):
        result = {}
        for target_id in targets:
            row = self.conn.execute(
                "SELECT progress FROM quest_resource_progress_v0929 "
                "WHERE account_id=? AND quest_id=? AND target_id=?",
                (account_id, quest_id, canonical_profession_resource_id(target_id)),
            ).fetchone()
            result[target_id] = max(0, int(row["progress"])) if row else 0
        return result

    def distinct_category_items_v023(self, account_id, quest_id):
        rows = self.conn.execute(
            "SELECT target_id FROM quest_resource_progress_v0929 "
            "WHERE account_id=? AND quest_id=? AND progress>0 ORDER BY target_id",
            (account_id, quest_id),
        ).fetchall()
        return [str(row["target_id"]) for row in rows]

    def mark_distinct_category_item_v023(self, account_id, quest_id, item_id, needed):
        """Zapisz jeden NOWY gatunek/typ dla questa wymagającego różnych zasobów."""
        needed = max(1, int(needed))
        existing = self.distinct_category_items_v023(account_id, quest_id)
        if item_id in existing or len(existing) >= needed:
            return len(existing), False
        self.conn.execute(
            "INSERT INTO quest_resource_progress_v0929(account_id,quest_id,target_id,progress) "
            "VALUES(?,?,?,1) ON CONFLICT(account_id,quest_id,target_id) DO NOTHING",
            (account_id, quest_id, str(item_id)),
        )
        count = len(self.distinct_category_items_v023(account_id, quest_id))
        self.conn.execute(
            "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
            (min(needed, count), account_id, quest_id),
        )
        self.conn.commit()
        return min(needed, count), True

    def increment_resource_set_quest_v0929(self, account_id, item_id, amount=1):
        amount = max(0, int(amount))
        if amount <= 0:
            return []
        item_base = canonical_profession_resource_id(item_id)
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if not quest or quest.get("kind") != "collect_resource_set":
                continue
            requirements = dict(quest.get("resource_targets") or {})
            matched_target = None
            target_needed = 0
            for target_id, needed in requirements.items():
                if canonical_profession_resource_id(target_id) == item_base:
                    matched_target = target_id
                    target_needed = max(1, int(needed))
                    break
            if matched_target is None:
                continue
            current = self.resource_set_progress_v0929(
                account_id, row["quest_id"], requirements
            ).get(matched_target, 0)
            updated = min(target_needed, current + amount)
            # v0.30.7: brak ponownego komunikatu po osiągnięciu limitu.
            if updated == current:
                continue
            self.conn.execute(
                "INSERT INTO quest_resource_progress_v0929(account_id,quest_id,target_id,progress) "
                "VALUES(?,?,?,?) ON CONFLICT(account_id,quest_id,target_id) "
                "DO UPDATE SET progress=excluded.progress",
                (account_id, row["quest_id"], canonical_profession_resource_id(matched_target), updated),
            )
            counts = self.resource_set_progress_v0929(
                account_id, row["quest_id"], requirements
            )
            counts[matched_target] = updated
            total = sum(min(max(1, int(requirements[t])), int(counts.get(t, 0))) for t in requirements)
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (total, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], total, int(quest.get("needed", total)), matched_target, updated, target_needed))
        self.conn.commit()
        return changed

    def complete_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='completed',completed_at=?,"
            "completion_count=completion_count+1 "
            "WHERE account_id=? AND quest_id=?",
            (int(time.time()), account_id, quest_id),
        )
        self.conn.commit()


    # ---- v0.9.25 equipment crafting / clan persistence ----
    def equipment_reforge(self, account_id, item_id):
        return self.conn.execute(
            "SELECT affix,affix_amount,rerolls FROM equipment_reforges WHERE account_id=? AND item_id=?",
            (account_id,item_id),
        ).fetchone()

    def save_equipment_reforge(self, account_id, item_id, affix, amount):
        self.conn.execute(
            "INSERT INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,1) "
            "ON CONFLICT(account_id,item_id) DO UPDATE SET affix=excluded.affix,affix_amount=excluded.affix_amount,rerolls=equipment_reforges.rerolls+1",
            (account_id,item_id,affix,int(amount)),
        )
        self.conn.commit()

    def equipment_runes_v0925(self, account_id, item_id):
        return self.conn.execute(
            "SELECT socket_index,rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? ORDER BY socket_index",
            (account_id,item_id),
        ).fetchall()

    def add_equipment_rune_v0925(self, account_id, item_id, socket_index, rune_id):
        self.conn.execute(
            "INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",
            (account_id,item_id,int(socket_index),rune_id),
        )
        self.conn.commit()

    def remove_equipment_rune_v0925(self, account_id, item_id, socket_index):
        row=self.conn.execute(
            "SELECT rune_id FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? AND socket_index=?",
            (account_id,item_id,int(socket_index)),
        ).fetchone()
        if not row: return None
        self.conn.execute(
            "DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=? AND socket_index=?",
            (account_id,item_id,int(socket_index)),
        )
        self.conn.commit()
        return str(row["rune_id"])

    def equipment_upgrade_level_v03042(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT upgrade_level FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return max(0, int(row["upgrade_level"])) if row else 0

    def set_equipment_upgrade_level_v03042(self, account_id, item_id, level):
        level = max(0, min(V03042_EQ_UPGRADE_MAX, int(level)))
        if level <= 0:
            self.conn.execute(
                "DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "INSERT INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?) "
                "ON CONFLICT(account_id,item_id) DO UPDATE SET upgrade_level=excluded.upgrade_level",
                (account_id, item_id, level),
            )
        self.conn.commit()

    def clear_equipment_crafting_v0925(self, account_id, item_id):
        self.conn.execute("DELETE FROM equipment_reforges WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.execute("DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.execute("DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?", (account_id,item_id))
        self.conn.commit()

    def transfer_equipment_crafting_v0925(self, from_account_id, to_account_id, item_id):
        ref=self.equipment_reforge(from_account_id,item_id)
        runes=list(self.equipment_runes_v0925(from_account_id,item_id))
        upgrade=self.equipment_upgrade_level_v03042(from_account_id,item_id)
        if ref:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_reforges(account_id,item_id,affix,affix_amount,rerolls) VALUES(?,?,?,?,?)",
                (to_account_id,item_id,ref["affix"],int(ref["affix_amount"]),int(ref["rerolls"])),
            )
            self.conn.execute("DELETE FROM equipment_reforges WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        for rr in runes:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_runes_v0925(account_id,item_id,socket_index,rune_id) VALUES(?,?,?,?)",
                (to_account_id,item_id,int(rr["socket_index"]),rr["rune_id"]),
            )
        if runes:
            self.conn.execute("DELETE FROM equipment_runes_v0925 WHERE account_id=? AND item_id=?",(from_account_id,item_id))
        if upgrade > 0:
            self.conn.execute(
                "INSERT OR REPLACE INTO equipment_upgrades_v03042(account_id,item_id,upgrade_level) VALUES(?,?,?)",
                (to_account_id,item_id,int(upgrade)),
            )
            self.conn.execute(
                "DELETE FROM equipment_upgrades_v03042 WHERE account_id=? AND item_id=?",
                (from_account_id,item_id),
            )
        self.conn.commit()

    def clan_membership(self, account_id):
        # Wewnętrzna nazwa pozostaje dla zgodności z v0.9.25; UI mówi Gildia.
        return self.conn.execute(
            "SELECT c.id clan_id,c.name,c.level,c.treasury,m.rank,c.owner_account_id "
            "FROM player_clan_members m JOIN player_clans c ON c.id=m.clan_id WHERE m.account_id=?",
            (account_id,),
        ).fetchone()

    def guild_bonus_percent_v0926(self, account_id):
        row=self.clan_membership(account_id)
        return v0926_guild_bonus_percent(int(row["level"])) if row else 0

    def ensure_guild_default_roles_v0926(self, clan_id):
        clan_id=int(clan_id)
        for key,data in V0926_GUILD_DEFAULT_ROLES.items():
            self.conn.execute(
                "INSERT OR IGNORE INTO player_clan_roles(clan_id,role_key,name,priority,withdraw_money,withdraw_items,invite,kick) VALUES(?,?,?,?,?,?,?,?)",
                (clan_id,key,data["name"],data["priority"],data["withdraw_money"],data["withdraw_items"],data["invite"],data["kick"]),
            )
        self.conn.commit()

    def guild_role_v0926(self, clan_id, role_key):
        if str(role_key)=="leader":
            return {"role_key":"leader","name":"Lider","priority":1000,"withdraw_money":1,"withdraw_items":1,"invite":1,"kick":1}
        self.ensure_guild_default_roles_v0926(clan_id)
        return self.conn.execute(
            "SELECT role_key,name,priority,withdraw_money,withdraw_items,invite,kick FROM player_clan_roles WHERE clan_id=? AND role_key=?",
            (int(clan_id),str(role_key)),
        ).fetchone()

    def guild_role_by_name_v0926(self, clan_id, query):
        self.ensure_guild_default_roles_v0926(clan_id)
        norm=normalize_lookup_text(query)
        rows=self.conn.execute(
            "SELECT role_key,name,priority,withdraw_money,withdraw_items,invite,kick FROM player_clan_roles WHERE clan_id=?",
            (int(clan_id),),
        ).fetchall()
        exact=[r for r in rows if normalize_lookup_text(r["name"])==norm or normalize_lookup_text(r["role_key"])==norm]
        if exact: return exact[0]
        partial=[r for r in rows if norm and (norm in normalize_lookup_text(r["name"]) or norm in normalize_lookup_text(r["role_key"]))]
        return partial[0] if len(partial)==1 else None

    def clan_log(self, clan_id, actor_account_id, message):
        self.conn.execute("INSERT INTO player_clan_log(clan_id,actor_account_id,message) VALUES(?,?,?)", (clan_id,actor_account_id,str(message)))
        self.conn.commit()

    def clan_metric_add(self, clan_id, metric, amount=1):
        self.conn.execute(
            "INSERT INTO player_clan_metrics(clan_id,metric,value) VALUES(?,?,?) ON CONFLICT(clan_id,metric) DO UPDATE SET value=value+excluded.value",
            (clan_id,metric,int(amount)),
        )
        self.conn.commit()

    def guild_hall_v0927(self, clan_id):
        clan_id=int(clan_id)
        self.conn.execute("INSERT OR IGNORE INTO player_guild_halls_v0927(clan_id) VALUES(?)",(clan_id,))
        self.conn.commit()
        return self.conn.execute("SELECT * FROM player_guild_halls_v0927 WHERE clan_id=?",(clan_id,)).fetchone()

    def guild_contract_row_v0927(self, clan_id, contract_id):
        self.conn.execute("INSERT OR IGNORE INTO player_guild_contracts_v0927(clan_id,contract_id) VALUES(?,?)",(int(clan_id),str(contract_id)))
        self.conn.commit()
        return self.conn.execute("SELECT * FROM player_guild_contracts_v0927 WHERE clan_id=? AND contract_id=?",(int(clan_id),str(contract_id))).fetchone()

    def guild_contract_add_v0927(self, clan_id, kind, amount=1):
        clan_id=int(clan_id); now=int(time.time()); changed=[]
        for contract_id,definition in V0927_GUILD_CONTRACTS.items():
            if definition["kind"]!=kind: continue
            row=self.guild_contract_row_v0927(clan_id,contract_id)
            if int(row["ready_at"] or 0)>now: continue
            need=int(definition["need"]); new=min(need,int(row["progress"] or 0)+int(amount))
            self.conn.execute("UPDATE player_guild_contracts_v0927 SET progress=? WHERE clan_id=? AND contract_id=?",(new,clan_id,contract_id))
            changed.append((contract_id,new,need))
        self.conn.commit(); return changed

    def guild_contract_complete_v0927(self, clan_id, contract_id):
        clan_id=int(clan_id); definition=V0927_GUILD_CONTRACTS[str(contract_id)]
        row=self.guild_contract_row_v0927(clan_id,contract_id)
        if int(row["progress"] or 0)<int(definition["need"]): return False
        ready=int(time.time())+int(definition["cooldown"]); reward=int(definition["reward"])
        self.conn.execute("UPDATE player_guild_contracts_v0927 SET progress=0,completed_count=completed_count+1,ready_at=? WHERE clan_id=? AND contract_id=?",(ready,clan_id,contract_id))
        self.conn.execute("UPDATE player_clans SET treasury=treasury+? WHERE id=?",(reward,clan_id))
        self.conn.commit(); return True


@dataclass
class Character:
    account_id: int
    name: str
    name_nom: str
    name_gen: str
    name_dat: str
    name_acc: str
    name_ins: str
    name_loc: str
    name_voc: str
    race: str
    class_name: str
    class_type: str
    soul_weapon: str
    weapon_base: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    willpower: int
    stat_progress: int
    strength_progress: int
    dexterity_progress: int
    constitution_progress: int
    intelligence_progress: int
    willpower_progress: int
    charisma_progress: int
    soul_level: int
    soul_xp: int
    soul_tier: int
    room_id: str
    silver: int
    gold: int
    mithril: int
    charisma: int
    character_level: int
    character_xp: int
    deaths: int
    guild_reputation_json: str = "{}"
    guild_exams_json: str = "{}"
    guild_class_quests_json: str = "{}"
    guild_bounty_json: str = "{}"
    loot_filter: str = "all"
    active_title: str = ""

    @classmethod
    def from_row(cls, row):
        return cls(
            account_id=row["account_id"], name=row["name"],
            name_nom=row["name_nom"], name_gen=row["name_gen"],
            name_dat=row["name_dat"], name_acc=row["name_acc"],
            name_ins=row["name_ins"], name_loc=row["name_loc"],
            name_voc=row["name_voc"], race=row["race"],
            class_name=row["class_name"], class_type=row["class_type"],
            soul_weapon=row["soul_weapon"], weapon_base=row["weapon_base"],
            strength=row["strength"], dexterity=row["dexterity"],
            constitution=row["constitution"], intelligence=row["intelligence"],
            willpower=row["willpower"], stat_progress=row["stat_progress"],
            strength_progress=(row["strength_progress"] if "strength_progress" in row.keys() else row["stat_progress"]),
            dexterity_progress=(row["dexterity_progress"] if "dexterity_progress" in row.keys() else row["stat_progress"]),
            constitution_progress=(row["constitution_progress"] if "constitution_progress" in row.keys() else row["stat_progress"]),
            intelligence_progress=(row["intelligence_progress"] if "intelligence_progress" in row.keys() else row["stat_progress"]),
            willpower_progress=(row["willpower_progress"] if "willpower_progress" in row.keys() else row["stat_progress"]),
            charisma_progress=(row["charisma_progress"] if "charisma_progress" in row.keys() else row["stat_progress"]),
            soul_level=row["soul_level"], soul_xp=row["soul_xp"],
            soul_tier=row["soul_tier"], room_id=row["room_id"],
            silver=row["silver"], gold=row["gold"], mithril=row["mithril"],
            charisma=row["charisma"],
            character_level=(row["character_level"] if "character_level" in row.keys() else 1),
            character_xp=(row["character_xp"] if "character_xp" in row.keys() else 0),
            deaths=row["deaths"],
            guild_reputation_json=(row["guild_reputation_json"] if "guild_reputation_json" in row.keys() else "{}"),
            guild_exams_json=(row["guild_exams_json"] if "guild_exams_json" in row.keys() else "{}"),
            guild_class_quests_json=(row["guild_class_quests_json"] if "guild_class_quests_json" in row.keys() else "{}"),
            guild_bounty_json=(row["guild_bounty_json"] if "guild_bounty_json" in row.keys() else "{}"),
            loot_filter=(row["loot_filter"] if "loot_filter" in row.keys() else "all"),
            active_title=(row["active_title"] if "active_title" in row.keys() else ""),
        )

    def character_xp_to_next(self):
        return character_xp_to_next(self.character_level)

    def add_character_xp(self, amount):
        amount=max(0,int(amount or 0))
        if self.character_level >= CHARACTER_MAX_LEVEL:
            self.character_level=CHARACTER_MAX_LEVEL
            self.character_xp=0
            return []
        self.character_xp += amount
        messages=[]
        while self.character_level < CHARACTER_MAX_LEVEL:
            needed=character_xp_to_next(self.character_level)
            if self.character_xp < needed:
                break
            self.character_xp -= needed
            self.character_level += 1
            messages.append(f"Level postaci wzrasta do {self.character_level}.")
        if self.character_level >= CHARACTER_MAX_LEVEL:
            self.character_level=CHARACTER_MAX_LEVEL
            self.character_xp=0
        if amount:
            next_needed=character_xp_to_next(self.character_level) if self.character_level < CHARACTER_MAX_LEVEL else 0
            messages.insert(0, f"EXP postaci +{amount}. Postęp {self.character_xp} z {next_needed}." if next_needed else f"EXP postaci +{amount}. Osiągnięto maksymalny Level {CHARACTER_MAX_LEVEL}.")
        return messages

    def name_case(self, case):
        mapping = {
            "nom": self.name_nom, "mianownik": self.name_nom,
            "gen": self.name_gen, "dopelniacz": self.name_gen, "dopełniacz": self.name_gen,
            "dat": self.name_dat, "celownik": self.name_dat,
            "acc": self.name_acc, "biernik": self.name_acc,
            "ins": self.name_ins, "narzednik": self.name_ins, "narzędnik": self.name_ins,
            "loc": self.name_loc, "miejscownik": self.name_loc,
            "voc": self.name_voc, "wolacz": self.name_voc, "wołacz": self.name_voc,
        }
        return mapping.get(str(case).strip().lower(), self.name_nom or self.name)

    def max_hp(self):
        base = generator_core_v027.character_hp_base(self.character_level, self.constitution)
        return max(1, int(round(base * self.racial_max_hp_multiplier())))

    def physical_power(self):
        return generator_core_v027.character_attribute_power(self.character_level, self.strength)

    def speed(self):
        return generator_core_v027.speed_from_dexterity(self.dexterity)

    def dodge_chance(self):
        # v0.8.65: Zręczność daje malejący pasywny dodge zamiast liniowej
        # krzywej, która w endgame doprowadzała prawie każdą klasę do 45%.
        base = v0865_dodge_chance_from_dexterity(self.dexterity)
        return min(
            0.35,
            base + self.class_dodge_bonus() + self.racial_dodge_bonus()
        )

    def active_class_names(self):
        names = list(getattr(self, "_active_classes", []) or [])
        if self.class_name not in names:
            names.insert(0, self.class_name)
        result = []
        for name in names:
            if name not in result:
                result.append(name)
        return result[:MULTICLASS_MAX_ACTIVE]

    def has_active_class(self, class_name):
        return class_name in self.active_class_names()

    def max_mana(self):
        base = generator_core_v027.character_mana_base(self.character_level, self.intelligence, self.willpower)
        return max(0, int(round(base * self.racial_max_mana_multiplier())))

    def spell_power(self):
        return generator_core_v027.character_attribute_power(self.character_level, self.intelligence)

    def _generated_class_passive(self, class_name):
        return generator_core_v027.class_passive_profile(class_name)

    def _generated_race_passive(self):
        return generator_core_v027.race_passive_profile(self.race)

    def class_passive_text_for(self, class_name):
        return generator_core_v027.class_passive_text_pl(class_name)

    def class_passive_text(self):
        return self.class_passive_text_for(self.class_name)

    def class_physical_damage_multiplier(self):
        multiplier = 1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "physical_damage": multiplier *= 1.0 + p["value"]
        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        elif self.class_name == "Łotrzyk":
            multiplier *= 1.0 + self.soul_weapon_rogue_damage_bonus_percent() / 100.0
        return multiplier

    def class_magic_damage_multiplier(self):
        multiplier = 1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "magic_damage": multiplier *= 1.0 + p["value"]
        if self.class_name in ("Mag", "Czarownik"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_healing_multiplier(self):
        multiplier = 1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "healing": multiplier *= 1.0 + p["value"]
        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_drain_healing_multiplier(self):
        multiplier=1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "drain_healing": multiplier *= 1.0 + p["value"]
        if self.class_name == "Nekromanta":
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_dodge_bonus(self):
        bonus=sum(self._generated_class_passive(name)["value"] for name in self.active_class_names() if self._generated_class_passive(name)["kind"]=="dodge")
        if self.class_name == "Łotrzyk": bonus += self.soul_weapon_dodge_bonus()
        return bonus

    def class_damage_reduction_percent(self):
        percent=100.0*sum(self._generated_class_passive(name)["value"] for name in self.active_class_names() if self._generated_class_passive(name)["kind"]=="damage_reduction")
        if self.class_name == "Strażnik": percent += self.soul_weapon_guardian_reduction_percent()
        return int(round(percent))

    def class_magic_defense_multiplier(self):
        multiplier=1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"]=="magic_defense": multiplier *= 1.0+p["value"]
        if self.class_name == "Psionik": multiplier *= 1.0 + self.soul_weapon_bonus_percent()/100.0
        return multiplier

    def apply_class_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.class_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        return reduced, max(0, damage - reduced)

    def racial_passive_text(self):
        return generator_core_v027.race_passive_text_pl(self.race)

    def _race_bonus(self, kind):
        p=self._generated_race_passive()
        return p["value"] if p["kind"]==kind else 0.0

    def racial_stat_progress_multiplier(self):
        return 1.0 + self._race_bonus("stat_xp")

    def racial_physical_damage_multiplier(self):
        return 1.0 + self._race_bonus("physical_damage")

    def racial_dodge_bonus(self):
        return self._race_bonus("dodge")

    def racial_max_hp_multiplier(self):
        return 1.0 + self._race_bonus("max_hp")

    def racial_profession_bonus_chance(self):
        return self._race_bonus("profession_bonus")

    def racial_magic_damage_multiplier(self):
        return 1.0 + self._race_bonus("magic_damage")

    def racial_max_mana_multiplier(self):
        return 1.0 + self._race_bonus("max_mana")

    def racial_all_damage_multiplier(self):
        return 1.0 + self._race_bonus("all_damage")

    def racial_physical_damage_reduction_percent(self):
        return int(round(100.0*self._race_bonus("physical_reduction")))

    def racial_soul_xp_multiplier(self):
        return 1.0 + self._race_bonus("soul_xp")

    def racial_magic_defense_multiplier(self):
        return 1.0 + self._race_bonus("magic_defense")

    def racial_healing_multiplier(self):
        return 1.0 + self._race_bonus("healing")

    def racial_healing_bonus_percent(self):
        return int(round((self.racial_healing_multiplier() - 1.0) * 100))

    def racial_damage_reduction_percent(self):
        return int(round(100.0*self._race_bonus("damage_reduction")))

    def apply_racial_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.racial_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        prevented = max(0, damage - reduced)
        return reduced, prevented

    def magic_defense(self):
        # Siła Woli odpowiada wyłącznie za obronę magiczną.
        base = max(0, self.willpower // 2)
        return max(
            0,
            int(
                round(
                    base
                    * self.class_magic_defense_multiplier()
                    * self.racial_magic_defense_multiplier()
                )
            )
        )

    def shop_discount_percent(self):
        return min(
            CHARISMA_MAX_DISCOUNT,
            max(0, self.charisma // CHARISMA_DISCOUNT_STEP),
        )

    def party_capacity(self):
        # Startowo 8 osób łącznie z liderem.
        # Co 25 Charyzmy lider otrzymuje jedno kolejne miejsce.
        return PARTY_BASE_CAPACITY + max(0, self.charisma // PARTY_CHARISMA_STEP)

    def charisma_to_next_discount(self):
        if self.shop_discount_percent() >= CHARISMA_MAX_DISCOUNT:
            return 0
        next_value = (self.shop_discount_percent() + 1) * CHARISMA_DISCOUNT_STEP
        return max(0, next_value - self.charisma)

    def charisma_to_next_party_slot(self):
        next_value = (
            (max(0, self.charisma) // PARTY_CHARISMA_STEP) + 1
        ) * PARTY_CHARISMA_STEP
        return max(0, next_value - self.charisma)

    def soul_xp_multiplier(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0.0
        level = max(1, int(self.soul_level))
        if level <= 200:
            # Dokładnie stara krzywa 1-200.
            completed_ten_level_blocks = max(0, (level - 1) // 10)
            return 1.25 ** completed_ten_level_blocks
        # 201-400: nie kontynuujemy wykładniczego 1.25^blok, bo koszt
        # eksplodowałby do setek milionów na level. Kotwiczymy na koszcie
        # levelu 200 i zwiększamy go liniowo do około x3 na 399->400.
        anchor_base = 180 + (200 - 1) * 60
        anchor_cost = anchor_base * (1.25 ** 19)
        target_cost = anchor_cost * (1.0 + (level - 200) * 0.01)
        current_base = 180 + (level - 1) * 60
        return max(1.0, target_cost / current_base)

    def soul_xp_to_next(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0
        return v0190_requirement("soul", self.soul_level)

    def soul_milestone_specialization_bonus(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        active = [t for t in SOUL_MILESTONE_TIERS if tier >= t]
        return SOUL_MILESTONE_SPECIALIZATION_BONUS[max(active)] if active else 0

    def soul_milestone_dodge_bonus(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        active = [t for t in SOUL_MILESTONE_TIERS if tier >= t]
        return SOUL_MILESTONE_DODGE_BONUS[max(active)] if active else 0.0

    def soul_milestone_guardian_reduction(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        active = [t for t in SOUL_MILESTONE_TIERS if tier >= t]
        return SOUL_MILESTONE_GUARDIAN_REDUCTION[max(active)] if active else 0

    def soul_weapon_bonus_percent(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        return (
            SOUL_TIER_CLASS_BONUS_PERCENT[tier - 1]
            + self.soul_milestone_specialization_bonus()
        )

    def soul_weapon_rogue_damage_bonus_percent(self):
        # Łotrzyk zachowuje defensywną tożsamość, ale jego Broń Duszy nie
        # przepala już progresji po osiągnięciu globalnego capu dodge.
        return max(0, (self.soul_weapon_bonus_percent() + 1) // 2)

    def soul_weapon_dodge_bonus(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        return min(
            0.05,
            SOUL_TIER_DODGE_BONUS[tier - 1]
            + self.soul_milestone_dodge_bonus()
        )

    def soul_weapon_guardian_reduction_percent(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        return (
            SOUL_TIER_GUARDIAN_REDUCTION[tier - 1]
            + self.soul_milestone_guardian_reduction()
        )

    def soul_weapon_class_bonus_text(self):
        percent = self.soul_weapon_bonus_percent()
        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            return (
                f"+{percent} procent obrażeń fizycznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Łotrzyk":
            pp = int(round(self.soul_weapon_dodge_bonus() * 100))
            dmg = self.soul_weapon_rogue_damage_bonus_percent()
            return (
                f"+{dmg} procent obrażeń fizycznych i +{pp} punktów "
                "procentowych uniku z Broni Duszy Łotrzyka"
            )
        if self.class_name in ("Mag", "Czarownik"):
            return (
                f"+{percent} procent obrażeń magicznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            return (
                f"+{percent} procent mocy leczenia z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Nekromanta":
            return (
                f"+{percent} procent leczenia z wysysania życia "
                "z Broni Duszy Nekromanty"
            )
        if self.class_name == "Strażnik":
            return (
                f"+{self.soul_weapon_guardian_reduction_percent()} procent "
                "redukcji wszystkich obrażeń z Broni Duszy Strażnika"
            )
        if self.class_name == "Psionik":
            return (
                f"+{percent} procent obrony magicznej "
                "z Broni Duszy Psionika"
            )
        return f"+{percent} procent do specjalizacji klasy głównej"

    def soul_power(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        tier_bonus = SOUL_TIER_POWER_BONUSES[tier - 1]
        level = max(1, min(SOUL_MAX_LEVEL, int(self.soul_level)))
        # 1-200 zachowuje dawny +1 mocy/level. 201-400 daje +1 mocy
        # co 2 levele, więc cap 400 jest dalszym wzrostem, nie x2 power creepem.
        level_bonus = min(level, 200) - 1 + max(0, level - 200) // 2
        return self.weapon_base + level_bonus + tier_bonus

    def can_unlock(self):
        if self.soul_tier >= SOUL_MAX_TIER:
            return None
        next_tier = int(self.soul_tier) + 1
        needed_level = SOUL_TIER_THRESHOLDS[next_tier - 1]
        if self.soul_level >= needed_level:
            return next_tier
        return None

    STAT_PROGRESS_FIELDS = {
        "strength": ("Siła", "strength", "strength_progress"),
        "dexterity": ("Zręczność", "dexterity", "dexterity_progress"),
        "constitution": ("Kondycja", "constitution", "constitution_progress"),
        "intelligence": ("Inteligencja", "intelligence", "intelligence_progress"),
        "willpower": ("Siła Woli", "willpower", "willpower_progress"),
        "charisma": ("Charyzma", "charisma", "charisma_progress"),
    }

    def stat_growth_threshold_for(self, stat_name):
        """Próg EXP pojedynczej statystyki.

        Każda statystyka rozwija się niezależnie. Start to 100 EXP, a od
        wartości bazowej 26 próg rośnie o 10 za każdy punkt. Dzięki temu
        niska statystyka może nadrobić, a wysoka nie rośnie lawinowo.
        """
        _label, value_field, _progress_field = self.STAT_PROGRESS_FIELDS[stat_name]
        value = max(1, int(getattr(self, value_field)))
        return v0190_requirement("stat", value)

    def stat_growth_threshold(self):
        """Legacy: zwraca średni próg sześciu statystyk dla zgodności."""
        thresholds = [self.stat_growth_threshold_for(name) for name in self.STAT_PROGRESS_FIELDS]
        return int(round(sum(thresholds) / len(thresholds)))

    def stat_progress_for(self, stat_name):
        _label, _value_field, progress_field = self.STAT_PROGRESS_FIELDS[stat_name]
        return max(0, int(getattr(self, progress_field)))

    def stat_progress_snapshot(self):
        result = {}
        for stat_name, (label, value_field, progress_field) in self.STAT_PROGRESS_FIELDS.items():
            result[stat_name] = {
                "label": label,
                "value": int(getattr(self, value_field)),
                "progress": max(0, int(getattr(self, progress_field))),
                "threshold": self.stat_growth_threshold_for(stat_name),
            }
        return result

    def add_stat_progress(self, amount, targets=None):
        """Dodaje EXP osobno do wskazanych statystyk.

        Domyślnie źródła ogólnego rozwoju (moby/questy) przyznają tę samą
        ilość EXP każdej statystyce, ale każda ma własny licznik i próg.
        """
        base_amount = max(0, int(amount))
        racial_amount = max(
            0,
            int(round(base_amount * self.racial_stat_progress_multiplier()))
        )
        _guild_pct=max(0,int(getattr(self,"_guild_bonus_percent",0) or 0))
        amount=max(0,int(round(racial_amount*(1.0+_guild_pct/100.0))))
        if targets is None:
            target_names = list(self.STAT_PROGRESS_FIELDS)
        else:
            target_names = [name for name in targets if name in self.STAT_PROGRESS_FIELDS]
        messages = []
        bonus = max(0, racial_amount - base_amount)
        guild_bonus=max(0, amount - racial_amount)
        for stat_name in target_names:
            label, value_field, progress_field = self.STAT_PROGRESS_FIELDS[stat_name]
            current_value=max(1,int(getattr(self,value_field)))
            # v0.27.1: statystyki nie mają capu. Powyżej 400 Generator Core
            # ekstrapoluje zarówno wymagany EXP, jak i wartość nagrody ze
            # źródła. Dzięki temu endgame nie zatrzymuje progresji, ale niskie
            # levele mobów nadal pozostają słabym źródłem EXP dla wysokich statów.
            stat_amount = generator_core_v027.uncapped_stat_xp_gain(amount, current_value)
            progress = max(0, int(getattr(self, progress_field))) + stat_amount
            leveled = 0
            while True:
                threshold = self.stat_growth_threshold_for(stat_name)
                if progress < threshold:
                    break
                progress -= threshold
                setattr(self, value_field, int(getattr(self, value_field)) + 1)
                leveled += 1
            setattr(self, progress_field, progress)
            if leveled:
                new_value = int(getattr(self, value_field))
                if leveled == 1:
                    messages.append(
                        f"{label} wzrasta do {new_value} — {stat_quality_label(new_value)}."
                    )
                else:
                    messages.append(
                        f"{label} wzrasta o {leveled} do {new_value} — {stat_quality_label(new_value)}."
                    )
            threshold = self.stat_growth_threshold_for(stat_name)
            messages.append(
                f"{label}: EXP +{stat_amount}. Postęp {progress} z {threshold}."
            )
        if bonus:
            messages.append(
                f"Bonus rasy {self.race} został uwzględniony w EXP rozwijanych statystyk."
            )
        if guild_bonus:
            messages.append(
                f"Bonus Gildii +{_guild_pct}% został uwzględniony w EXP rozwijanych statystyk."
            )
        # Legacy pole zachowujemy jako najmniejszy bieżący postęp, ale nie
        # steruje już rozwojem.
        values = [self.stat_progress_for(name) for name in self.STAT_PROGRESS_FIELDS]
        self.stat_progress = min(values) if values else 0
        return messages

    def soul_level_cap_for_current_tier(self):
        """Najwyższy Soul Level dostępny przed odblokowaniem kolejnego Tieru.

        Tier 1 pozwala dojść do progu Tieru 2, Tier 2 do progu Tieru 3 itd.
        Tier 40 ma końcowy cap Soul Level 400. Istniejących save'ów nie cofamy:
        postać zapisana powyżej bieżącego capu po prostu nie dostaje dalszego
        Soul XP, dopóki nie odblokuje brakujących Tierów.
        """
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        if tier >= SOUL_MAX_TIER:
            return SOUL_MAX_LEVEL
        return int(SOUL_TIER_THRESHOLDS[tier])

    def soul_progress_is_tier_locked(self):
        return (
            int(self.soul_tier) < SOUL_MAX_TIER
            and int(self.soul_level) >= self.soul_level_cap_for_current_tier()
        )

    def add_soul_xp(self, amount):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return [f"Broń Duszy ma już Soul Level {SOUL_MAX_LEVEL}."]

        # v0.9.14: Soul Level nie może wyprzedzić odblokowanego Tieru.
        # Osiągnięcie progu następnego Tieru zatrzymuje cały dalszy Soul XP
        # do chwili wykonania Próby i użycia komendy unlock. Overflow nie jest
        # bankowany, dzięki czemu po unlock nie da się przeskoczyć kilku progów.
        cap_level = self.soul_level_cap_for_current_tier()
        if self.soul_progress_is_tier_locked():
            next_tier = min(SOUL_MAX_TIER, int(self.soul_tier) + 1)
            self.soul_xp = 0
            return [
                f"Soul XP zablokowany na Soul Level {cap_level}. "
                f"Najpierw odblokuj Soul Tier {next_tier}: wykonaj właściwą Próbę "
                "Broni Duszy i użyj unlock."
            ]

        base_amount = max(0, int(amount))
        racial_amount = max(
            0,
            int(round(base_amount * self.racial_soul_xp_multiplier()))
        )
        _guild_pct=max(0,int(getattr(self,"_guild_bonus_percent",0) or 0))
        amount=max(0,int(round(racial_amount*(1.0+_guild_pct/100.0))))
        messages = [f"Broń Duszy otrzymuje {amount} Soul XP."]
        if racial_amount > base_amount:
            messages.append(
                f"Bonus rasy {self.race}: +{racial_amount - base_amount} Soul XP."
            )
        if amount > racial_amount:
            messages.append(
                f"Bonus Gildii +{_guild_pct}%: +{amount-racial_amount} Soul XP."
            )
        self.soul_xp += amount
        while self.soul_level < SOUL_MAX_LEVEL:
            cap_level = self.soul_level_cap_for_current_tier()
            if self.soul_level >= cap_level:
                # Nie zachowujemy nadmiaru ponad bramką Tieru.
                self.soul_xp = 0
                next_tier = min(SOUL_MAX_TIER, int(self.soul_tier) + 1)
                messages.append(
                    f"Soul Level zatrzymuje się na {cap_level}. Dalszy Soul XP jest "
                    f"zablokowany do odblokowania Soul Tier {next_tier}."
                )
                break
            needed = self.soul_xp_to_next()
            if self.soul_xp < needed:
                break
            self.soul_xp -= needed
            self.soul_level += 1
            messages.append(f"Broń Duszy osiąga Soul Level {self.soul_level}.")
            if self.soul_level in SOUL_TIER_THRESHOLDS[1:]:
                tier = SOUL_TIER_THRESHOLDS.index(self.soul_level) + 1
                if tier in SOUL_TRIAL_QUEST_IDS:
                    messages.append(
                        f"Osiągnięto próg Tieru {tier}. "
                        "Idź do Kapłana Elora po Próbę Broni Duszy."
                    )
                else:
                    messages.append(
                        f"Osiągnięto próg Tieru {tier}. Wpisz unlock, "
                        "gdy poprzednie Tiery są odblokowane."
                    )
                if int(self.soul_tier) < tier:
                    self.soul_xp = 0
                    messages.append(
                        f"Dalszy Soul XP jest teraz zablokowany do odblokowania Tieru {tier}."
                    )
                    break
        if self.soul_level >= SOUL_MAX_LEVEL:
            self.soul_level = SOUL_MAX_LEVEL
            self.soul_xp = 0
            messages.append(f"Osiągnięto maksymalny Soul Level {SOUL_MAX_LEVEL}.")
        return messages


    def _guild_json(self, field_name):
        try:
            raw = getattr(self, field_name, "{}") or "{}"
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _set_guild_json(self, field_name, data):
        setattr(self, field_name, json.dumps(data, ensure_ascii=False, sort_keys=True))

    def guild_reputation(self, class_name):
        data = self._guild_json("guild_reputation_json")
        return int(data.get(class_name, 0) or 0)

    def add_guild_reputation(self, class_name, amount):
        data = self._guild_json("guild_reputation_json")
        current = int(data.get(class_name, 0) or 0)
        data[class_name] = max(0, min(GUILD_REPUTATION_MAX, current + int(amount)))
        self._set_guild_json("guild_reputation_json", data)
        return data[class_name]

    def guild_rep_rank(self, class_name):
        value = self.guild_reputation(class_name)
        current = GUILD_REPUTATION_RANKS[0]
        for row in GUILD_REPUTATION_RANKS:
            if value >= row[0]:
                current = row
        return current

    def guild_training_discount(self, class_name):
        return float(self.guild_rep_rank(class_name)[2])

    def guild_exam_done(self, class_name, threshold):
        data = self._guild_json("guild_exams_json")
        done = data.get(class_name, [])
        return int(threshold) in [int(x) for x in done]

    def mark_guild_exam_done(self, class_name, threshold):
        data = self._guild_json("guild_exams_json")
        done = set(int(x) for x in data.get(class_name, []))
        done.add(int(threshold))
        data[class_name] = sorted(done)
        self._set_guild_json("guild_exams_json", data)

    def guild_class_quest_done(self, class_name):
        data = self._guild_json("guild_class_quests_json")
        return bool(data.get(class_name, False))

    def mark_guild_class_quest_done(self, class_name):
        data = self._guild_json("guild_class_quests_json")
        data[class_name] = True
        self._set_guild_json("guild_class_quests_json", data)

    def guild_bounty_state(self):
        return self._guild_json("guild_bounty_json")

    def set_guild_bounty_state(self, data):
        self._set_guild_json("guild_bounty_json", data)


# ============================================================
# v0.12.0 - LIVING WATERS + MEADOW BIOMES + PASSIVE WORLD
# ============================================================
# Globalna zasada rozgrywki: żaden mob ani boss nie zaczyna walki sam.
# Moby mogą się poruszać i pojawiać obok gracza, ale combat uruchamia
# wyłącznie świadoma akcja gracza (atakuj/k/skill ofensywny użyty na celu).
GLOBAL_MOB_AUTO_AGGRO_ENABLED = False


def mob_can_auto_aggro(_template=None):
    """Jedno źródło prawdy dla globalnej polityki aggro.

    Funkcja celowo zawsze zwraca False. Zostawiamy ją jawnie w kodzie,
    aby przyszłe systemy biomów/roamingu nie wprowadziły auto-ataku bokiem.
    """
    return False


V012_NEW_FISHING_ROOMS = set()
V012_NEW_MEADOW_ROOMS = set()
V012_WATER_MEADOW_ROOMS = set()
V012_MEADOW_HERB_GROUP = {}
V012_HERB_ECOLOGY_POOLS = {}


def _v012_connect(a, direction_a, b, direction_b):
    ROOMS[a].setdefault("exits", {})[direction_a] = b
    ROOMS[b].setdefault("exits", {})[direction_b] = a


def _v012_add_room(room_id, zone, name, desc):
    ROOMS[room_id] = {
        "zone": zone,
        "name": name,
        "desc": desc,
        "exits": {},
    }


def build_v012_living_waters_and_meadows():
    # --------------------------------------------------------
    # WYBRZEŻE, MORZE I OCEAN
    # --------------------------------------------------------
    water_rooms = {
        "coastal_cove": ("Wybrzeże", "Spokojna Zatoka", "Osłonięta zatoka o łagodnym nurcie. Płytka woda sprzyja rybom przybrzeżnym."),
        "rocky_shore": ("Wybrzeże", "Skalisty Brzeg", "Poszarpane skały schodzą w słoną wodę. Między głazami tworzą się głębsze rynny łowiskowe."),
        "river_estuary": ("Wybrzeże", "Ujście Srebrnej Rzeki", "Słodka i słona woda mieszają się w szerokim ujściu. Łowisko ma charakter estuarium."),
        "salt_marsh": ("Wybrzeże", "Słone Mokradła", "Płytkie kanały pływowe przecinają kępy słonolubnych traw."),
        "tidal_flats": ("Wybrzeże", "Płycizny Pływowe", "Rozległe płycizny zmieniają się wraz z przypływem. Ryby podchodzą tu blisko brzegu."),
        "coastal_lagoon": ("Wybrzeże", "Laguna Przybrzeżna", "Ciepła laguna jest częściowo odcięta od morza pasem skał i piasku."),
        "kelp_bay": ("Wybrzeże", "Zatoka Wodorostów", "Gęste pasma wodorostów falują pod powierzchnią i kryją wiele morskich gatunków."),
        "outer_reef": ("Ocean", "Zewnętrzna Rafa", "Rafa leży już poza spokojnym pasem wybrzeża. Woda jest głęboka i przejrzysta."),
        "bluewater_channel": ("Ocean", "Błękitny Kanał", "Silny prąd oceaniczny tworzy naturalny szlak dużych ryb pelagicznych."),
        "ocean_shelf": ("Ocean", "Krawędź Szelfu", "Dno gwałtownie opada. To przejście między wodami przybrzeżnymi a otwartym oceanem."),
        "deep_ocean_buoy": ("Ocean", "Boja Głębokiego Oceanu", "Samotna boja wyznacza dalekie łowisko na bardzo głębokiej wodzie."),
        "trench_edge": ("Ocean", "Krawędź Rowu Oceanicznego", "Ciemna toń zaczyna się tuż za krawędzią podmorskiego urwiska."),
        "storm_current": ("Ocean", "Prąd Burzowy", "Niespokojny prąd niesie chłodniejszą wodę i przyciąga silne oceaniczne drapieżniki."),
    }
    for rid, (zone, name, desc) in water_rooms.items():
        _v012_add_room(rid, zone, name, desc)

    _v012_connect("sea_pier", "north", "coastal_cove", "south")
    _v012_connect("coastal_cove", "east", "rocky_shore", "west")
    _v012_connect("rocky_shore", "north", "river_estuary", "south")
    _v012_connect("river_estuary", "west", "salt_marsh", "east")
    _v012_connect("salt_marsh", "south", "coastal_cove", "north")
    _v012_connect("sea_pier", "south", "tidal_flats", "north")
    _v012_connect("tidal_flats", "east", "coastal_lagoon", "west")
    _v012_connect("coastal_lagoon", "north", "rocky_shore", "south")
    _v012_connect("tidal_flats", "south", "kelp_bay", "north")
    _v012_connect("kelp_bay", "east", "coastal_lagoon", "south")

    _v012_connect("ocean_platform", "north", "outer_reef", "south")
    _v012_connect("outer_reef", "east", "bluewater_channel", "west")
    _v012_connect("bluewater_channel", "south", "ocean_shelf", "north")
    _v012_connect("ocean_platform", "south", "ocean_shelf", "west")
    _v012_connect("bluewater_channel", "east", "deep_ocean_buoy", "west")
    _v012_connect("deep_ocean_buoy", "south", "trench_edge", "north")
    _v012_connect("trench_edge", "west", "storm_current", "east")
    _v012_connect("storm_current", "north", "ocean_shelf", "south")

    sea_ids = {
        "coastal_cove", "rocky_shore", "river_estuary", "salt_marsh",
        "tidal_flats", "coastal_lagoon", "kelp_bay",
    }
    ocean_ids = {
        "outer_reef", "bluewater_channel", "ocean_shelf",
        "deep_ocean_buoy", "trench_edge", "storm_current",
    }
    SEA_FISHING_ROOMS.update(sea_ids)
    OCEAN_FISHING_ROOMS.update(ocean_ids)
    MARINE_FISHING_ROOMS.update(sea_ids | ocean_ids)
    FISHING_ROOMS.update(sea_ids | ocean_ids)
    V012_NEW_FISHING_ROOMS.update(sea_ids | ocean_ids)

    # --------------------------------------------------------
    # RZEKA, JEZIORO, STARORZECZE I STAW ŁĄKOWY
    # --------------------------------------------------------
    fresh_rooms = {
        "willow_bend": ("Dolina Rzeki", "Wierzbowe Zakole", "Rzeka zwalnia pod starymi wierzbami i tworzy głębokie stanowiska przy brzegu."),
        "river_rapids": ("Dolina Rzeki", "Srebrne Bystrza", "Szybki nurt pieni się między kamieniami. Żyją tu gatunki lubiące natlenioną wodę."),
        "reed_bank": ("Dolina Rzeki", "Trzcinowy Brzeg", "Szeroki pas trzcin osłania spokojniejsze zatoczki rzecznego brzegu."),
        "river_ford": ("Dolina Rzeki", "Kamienny Bród", "Płytki bród przecina rzekę, a za głazami tworzą się naturalne kieszenie dla ryb."),
        "spring_creek": ("Dolina Rzeki", "Źródlany Potok", "Chłodny potok wpada do rzeki. Woda jest czysta i szybka."),
        "oxbow_pool": ("Dolina Rzeki", "Stare Starorzecze", "Odcięte zakole tworzy ciche, zarośnięte łowisko o niemal jeziorowym charakterze."),
        "reed_lake_bank": ("Srebrne Jezioro", "Trzcinowy Brzeg Jeziora", "Płytki brzeg jeziora porastają trzciny i lilie wodne."),
        "quiet_cove": ("Srebrne Jezioro", "Cicha Zatoka Jeziora", "Osłonięta zatoka ma spokojną wodę i głębszy środek."),
        "southern_lake_bank": ("Srebrne Jezioro", "Południowy Brzeg Jeziora", "Kamienisto-piaszczysty brzeg otwiera dostęp do szerokiej tafli Srebrnego Jeziora."),
        "pebble_lake_bank": ("Srebrne Jezioro", "Żwirowy Brzeg Jeziora", "Dno opada tu równomiernie, a żwir przyciąga inne gatunki niż trzcinowe zatoki."),
        "fisher_inlet": ("Srebrne Jezioro", "Zatoczka Rybaków", "Mała zatoczka z resztkami starego pomostu jest wygodnym miejscem do spokojnego łowienia."),
        "deepwater_pier": ("Srebrne Jezioro", "Pomost Głębokiej Toni", "Długi pomost sięga nad najgłębszą część jeziora dostępną z brzegu."),
        "meadow_pond": ("Łąki", "Staw pośród Łąk", "Niewielki staw otaczają miękkie trawy, mięta i owady. To spokojne łowisko jeziorno-stawowe."),
    }
    for rid, (zone, name, desc) in fresh_rooms.items():
        _v012_add_room(rid, zone, name, desc)

    _v012_connect("riverbank", "north", "willow_bend", "south")
    _v012_connect("willow_bend", "east", "river_rapids", "west")
    _v012_connect("river_rapids", "south", "stone_bridge", "north")
    _v012_connect("riverbank", "south", "reed_bank", "north")
    _v012_connect("reed_bank", "east", "river_ford", "west")
    _v012_connect("river_ford", "north", "stone_bridge", "south")
    _v012_connect("willow_bend", "west", "spring_creek", "east")
    _v012_connect("spring_creek", "south", "reed_bank", "west")
    _v012_connect("reed_bank", "south", "oxbow_pool", "north")

    _v012_connect("lake_shore", "east", "reed_lake_bank", "west")
    _v012_connect("reed_lake_bank", "south", "quiet_cove", "north")
    _v012_connect("quiet_cove", "west", "southern_lake_bank", "east")
    _v012_connect("southern_lake_bank", "north", "lake_shore", "south")
    _v012_connect("lake_shore", "west", "pebble_lake_bank", "east")
    _v012_connect("pebble_lake_bank", "south", "fisher_inlet", "north")
    _v012_connect("fisher_inlet", "east", "southern_lake_bank", "west")
    _v012_connect("quiet_cove", "east", "deepwater_pier", "west")
    _v012_connect("deepwater_pier", "north", "reed_lake_bank", "east")

    river_ids = {
        "willow_bend", "river_rapids", "reed_bank", "river_ford", "spring_creek",
    }
    lake_ids = {
        "oxbow_pool", "reed_lake_bank", "quiet_cove", "southern_lake_bank",
        "pebble_lake_bank", "fisher_inlet", "deepwater_pier", "meadow_pond",
    }
    RIVER_FISHING_ROOMS.update(river_ids)
    LAKE_FISHING_ROOMS.update(lake_ids)
    FRESHWATER_FISHING_ROOMS.update(river_ids | lake_ids)
    FISHING_ROOMS.update(river_ids | lake_ids)
    V012_NEW_FISHING_ROOMS.update(river_ids | lake_ids)

    # --------------------------------------------------------
    # ROZLEGŁE ŁĄKI - kilka typów siedlisk połączonych pętlami
    # --------------------------------------------------------
    meadow_rooms = {
        "wildflower_basin": ("Kotlina Dzikich Kwiatów", "Łagodna niecka pełna rumianku, lawendy, krwawnika i wysokich kwiatów."),
        "butterfly_field": ("Łąka Motyli", "Ciepła polana przyciąga chmary motyli i drobną zwierzynę. Rosną tu lekkie zioła łąkowe."),
        "heather_field": ("Wrzosowisko", "Purpurowe wrzosy pokrywają suchszy fragment łąk, gdzie roślinność jest rzadsza, ale bardziej aromatyczna."),
        "wind_meadow": ("Wietrzna Łąka", "Wysoka trawa ugina się pod stałym wiatrem. Między kępami rosną odporne zioła."),
        "clover_field": ("Pole Koniczyny", "Niskie, miękkie trawy i koniczyna tworzą spokojny teren dla drobnych zwierząt."),
        "tall_grass_field": ("Morze Wysokich Traw", "Trawa sięga niemal do pasa i tworzy naturalne ścieżki między pagórkami."),
        "wet_meadow": ("Mokra Łąka", "Grunt jest nasiąknięty wodą z rzeki. Mięta, melisa i rośliny wilgociolubne rosną bardzo gęsto."),
        "reed_meadow": ("Trzcinowa Łąka", "Łąka przechodzi w pas trzcin i niewielkich oczek wodnych."),
        "marshy_meadow": ("Podmokła Łąka", "Między trawami błyszczą małe rozlewiska. To przejście między łąką a mokradłem."),
        "creek_meadow": ("Łąka Nad Potokiem", "Wąski potok przecina zielony teren, tworząc wilgotne stanowiska zielarskie."),
        "herb_ridge": ("Zielarska Grań", "Nieznacznie wyniesiony teren jest suchszy i nasłoneczniony. Rosną tu szałwia i późniejsze zioła."),
        "sage_hollow": ("Niecka Szałwii", "Ciepła niecka pachnie szałwią i gorzkimi roślinami leczniczymi."),
        "valerian_lowland": ("Nizina Waleriany", "Chłodniejsza, wilgotna dolinka sprzyja walerianie i roślinom późniejszej progresji."),
        "ginseng_hill": ("Wzgórze Żeń-szenia", "Stoki wzgórza są zacienione przez pojedyncze drzewa. Wśród korzeni można znaleźć cenne zioła."),
        "moon_meadow": ("Księżycowa Łąka", "Jasne kwiaty pozostają otwarte nawet nocą. To jeden z bardziej wymagających terenów Zielarstwa."),
        "old_stone_meadow": ("Łąka Starych Kamieni", "Krąg omszałych głazów dzieli łąkę na kilka naturalnych polan i ścieżek."),
        "orchard_meadow": ("Łąka Przy Sadzie", "Trawiaste zbocze łączy dzikie łąki ze starymi sadami przedmieść."),
    }
    for rid, (name, desc) in meadow_rooms.items():
        _v012_add_room(rid, "Łąki", name, desc)
        HERBALISM_ROOMS.add(rid)
        MEADOW_HERBALISM_ROOMS.add(rid)
        V012_NEW_MEADOW_ROOMS.add(rid)

    _v012_connect("flower_meadow", "south", "wildflower_basin", "north")
    _v012_connect("wildflower_basin", "west", "butterfly_field", "east")
    _v012_connect("butterfly_field", "south", "old_stone_meadow", "north")
    _v012_connect("wildflower_basin", "east", "heather_field", "west")
    _v012_connect("heather_field", "east", "wind_meadow", "west")
    _v012_connect("wind_meadow", "south", "clover_field", "north")
    _v012_connect("clover_field", "south", "mint_meadow", "north")
    _v012_connect("heather_field", "north", "tall_grass_field", "south")
    _v012_connect("tall_grass_field", "east", "old_stone_meadow", "west")
    _v012_connect("old_stone_meadow", "south", "wind_meadow", "north")

    _v012_connect("mint_meadow", "south", "wet_meadow", "north")
    _v012_connect("wet_meadow", "east", "reed_meadow", "west")
    _v012_connect("reed_meadow", "south", "marshy_meadow", "north")
    _v012_connect("marshy_meadow", "west", "herb_ridge", "east")
    _v012_connect("lakeside_meadow", "west", "creek_meadow", "east")
    _v012_connect("creek_meadow", "south", "meadow_pond", "north")
    _v012_connect("marshy_meadow", "south", "valerian_lowland", "north")

    _v012_connect("creek_meadow", "north", "wet_meadow", "south")
    _v012_connect("herb_ridge", "south", "sage_hollow", "north")
    _v012_connect("sage_hollow", "east", "valerian_lowland", "west")
    _v012_connect("sage_hollow", "south", "ginseng_hill", "north")
    _v012_connect("ginseng_hill", "east", "moon_meadow", "west")
    _v012_connect("moon_meadow", "north", "valerian_lowland", "south")
    _v012_connect("tall_grass_field", "north", "orchard_meadow", "south")
    if "old_orchard" in ROOMS:
        _v012_connect("orchard_meadow", "north", "old_orchard", "south")

    HERBALISM_ROOMS.add("meadow_pond")
    MEADOW_HERBALISM_ROOMS.add("meadow_pond")
    V012_WATER_MEADOW_ROOMS.update({
        "wet_meadow", "reed_meadow", "marshy_meadow", "creek_meadow", "meadow_pond",
    })


build_v012_living_waters_and_meadows()

# Opisy typów wody używane przez komendę łowienia/atlas.
FISHING_WATER_TYPE_OVERRIDES.update({
    "coastal_cove": "Zatoka morska", "rocky_shore": "Skalisty brzeg morski",
    "river_estuary": "Estuarium", "salt_marsh": "Słone mokradła",
    "tidal_flats": "Płycizny pływowe", "coastal_lagoon": "Laguna",
    "kelp_bay": "Zatoka wodorostów", "outer_reef": "Rafa oceaniczna",
    "bluewater_channel": "Otwarty ocean", "ocean_shelf": "Krawędź szelfu",
    "deep_ocean_buoy": "Głęboki ocean", "trench_edge": "Rów oceaniczny",
    "storm_current": "Prąd oceaniczny", "willow_bend": "Zakole rzeki",
    "river_rapids": "Bystrza", "reed_bank": "Trzcinowy brzeg rzeki",
    "river_ford": "Bród rzeczny", "spring_creek": "Potok",
    "oxbow_pool": "Starorzecze", "reed_lake_bank": "Trzcinowy brzeg jeziora",
    "quiet_cove": "Zatoka jeziora", "southern_lake_bank": "Brzeg jeziora",
    "pebble_lake_bank": "Żwirowy brzeg jeziora", "fisher_inlet": "Zatoczka jeziora",
    "deepwater_pier": "Głęboka toń jeziora", "meadow_pond": "Staw łąkowy",
})

# Ekologia łowisk: preferencja zmienia charakter stanowiska, ale nigdy
# nie omija levelu Wędki. Gdy filtr byłby pusty, system wraca do normalnej puli.
FISHING_ECOLOGY_PREFERRED_IDS.update({
    "coastal_cove": {"sand_eel", "world_bonefish", "world_common_snook", "world_pompano", "world_yellowtail_snapper"},
    "rocky_shore": {"world_sheepshead", "world_red_grouper", "world_european_conger", "world_scorpionfish", "world_wolffish"},
    "river_estuary": {"world_atlantic_tarpon", "world_red_drum", "world_black_drum", "world_striped_bass", "world_atlantic_croaker"},
    "salt_marsh": {"world_bonefish", "world_common_snook", "world_red_drum", "world_mangrove_snapper", "world_lane_snapper"},
    "tidal_flats": {"sand_eel", "world_bonefish", "world_permit_fish", "world_pompano", "world_atlantic_croaker"},
    "coastal_lagoon": {"world_common_snook", "world_red_drum", "world_yellowtail_snapper", "world_mangrove_snapper", "world_queen_triggerfish"},
    "kelp_bay": {"world_atlantic_mackerel", "world_horse_mackerel", "world_john_dory", "world_wolffish", "world_atlantic_halibut_world"},
    "outer_reef": {"reef_shark", "world_manta_ray", "world_spotted_eagle_ray", "world_blue_marlin", "world_whale_shark"},
    "bluewater_channel": {"bluefin_tuna", "yellowfin_tuna", "world_skipjack_tuna", "world_blue_marlin", "world_white_marlin"},
    "ocean_shelf": {"world_escolar", "world_oilfish", "world_lancetfish", "world_blue_shark", "world_common_thresher"},
    "deep_ocean_buoy": {"world_oarfish", "world_greenland_shark", "world_goblin_shark", "world_orange_roughy", "world_coelacanth_world"},
    "trench_edge": {"world_goblin_shark", "world_megamouth_shark", "world_bluntnose_sixgill", "world_frilled_shark", "world_coelacanth_world"},
    "storm_current": {"mako_shark", "tiger_shark", "world_blue_shark", "world_oceanic_whitetip_shark", "world_common_thresher"},
    "willow_bend": {"dace", "chub", "river_carp", "barbel", "ide", "world_freshwater_drum"},
    "river_rapids": {"grayling", "salmon", "brown_trout", "river_taimen", "world_rainbow_trout", "world_chinook_salmon"},
    "reed_bank": {"river_perch", "river_carp", "burbot", "river_catfish", "world_channel_catfish", "world_wels_catfish"},
    "river_ford": {"dace", "common_nase", "barbel", "grayling", "world_mahseer", "world_golden_dorado"},
    "spring_creek": {"stone_loach", "brown_trout", "silver_trout", "golden_trout", "world_brook_trout", "world_cutthroat_trout"},
    "oxbow_pool": {"crucian_carp", "tench", "pike", "freshwater_eel", "world_largemouth_bass", "world_bluegill"},
    "reed_lake_bank": {"lake_roach", "rudd", "crucian_carp", "tench", "lake_perch", "world_bluegill"},
    "quiet_cove": {"bream", "tench", "pike", "zander", "freshwater_eel", "world_walleye"},
    "southern_lake_bank": {"lake_roach", "bream", "lake_perch", "vendace", "world_yellow_perch", "world_cisco"},
    "pebble_lake_bank": {"whitefish", "lake_char", "lake_trout", "world_round_whitefish", "world_marble_trout"},
    "fisher_inlet": {"rudd", "crucian_carp", "bream", "tench", "world_pumpkinseed", "world_black_crappie"},
    "deepwater_pier": {"pike", "zander", "lake_trout", "mirror_sturgeon", "world_lake_sturgeon", "world_taimen"},
    "meadow_pond": {"crucian_carp", "tench", "rudd", "lake_roach", "world_bluegill", "world_pumpkinseed"},
})

# Lokalne profile ziół. Mają 65% szansy wpłynąć na zbiór; pozostałe 35%
# korzysta z pełnej, levelowanej puli świata, więc progresja 1-400 nadal działa.
V012_HERB_ECOLOGY_POOLS.update({
    "wildflower_basin": ((1,"chamomile"),(1,"lavender"),(15,"yarrow"),(25,"lemon_balm"),(40,"sage")),
    "butterfly_field": ((1,"chamomile"),(1,"mint"),(10,"lavender"),(20,"yarrow"),(35,"lemon_balm")),
    "heather_field": ((15,"lavender"),(30,"sage"),(45,"valerian"),(70,"ginseng")),
    "wind_meadow": ((1,"nettle"),(1,"chamomile"),(15,"yarrow"),(30,"sage"),(50,"valerian")),
    "clover_field": ((1,"nettle"),(1,"mint"),(10,"chamomile"),(20,"lemon_balm"),(35,"yarrow")),
    "tall_grass_field": ((1,"nettle"),(15,"yarrow"),(25,"lemon_balm"),(40,"sage"),(60,"valerian")),
    "wet_meadow": ((1,"mint"),(10,"lemon_balm"),(30,"valerian"),(55,"ginseng"),(80,"moonflower")),
    "reed_meadow": ((1,"mint"),(15,"lemon_balm"),(35,"sage"),(60,"ginseng"),(90,"star_moss")),
    "marshy_meadow": ((10,"lemon_balm"),(30,"valerian"),(50,"ginseng"),(70,"nightshade"),(100,"moonflower")),
    "creek_meadow": ((1,"mint"),(10,"chamomile"),(25,"lemon_balm"),(45,"valerian"),(75,"ginseng")),
    "meadow_pond": ((1,"mint"),(20,"lemon_balm"),(40,"valerian"),(70,"ginseng"),(100,"star_moss")),
    "herb_ridge": ((20,"lavender"),(35,"sage"),(50,"valerian"),(70,"ginseng"),(90,"mandrake")),
    "sage_hollow": ((30,"sage"),(45,"valerian"),(65,"ginseng"),(85,"nightshade"),(110,"mandrake")),
    "valerian_lowland": ((40,"valerian"),(60,"ginseng"),(80,"nightshade"),(100,"moonflower"),(120,"soulroot")),
    "ginseng_hill": ((50,"ginseng"),(75,"nightshade"),(95,"mandrake"),(120,"soulroot"),(150,"phoenix_leaf")),
    "moon_meadow": ((70,"moonflower"),(100,"soulroot"),(130,"star_moss"),(160,"phoenix_leaf"),(190,"astral_lotus")),
    "old_stone_meadow": ((10,"yarrow"),(25,"lavender"),(45,"sage"),(70,"valerian"),(100,"ginseng")),
    "orchard_meadow": ((1,"chamomile"),(10,"mint"),(20,"yarrow"),(35,"lemon_balm"),(50,"sage")),
})
V012_MEADOW_HERB_GROUP.update({rid: ("water" if rid in V012_WATER_MEADOW_ROOMS else "meadow") for rid in V012_NEW_MEADOW_ROOMS})
V012_MEADOW_HERB_GROUP["meadow_pond"] = "water"

# Atlas surowców zna nowe łąki i pokazuje realne wymagania Sierpa.
for _rid, _rows in V012_HERB_ECOLOGY_POOLS.items():
    HERB_ATLAS_ROOM_MIN_LEVELS.setdefault(_rid, {})
    for _level, _herb_id in _rows:
        if _herb_id in ITEMS:
            previous = HERB_ATLAS_ROOM_MIN_LEVELS[_rid].get(_herb_id)
            HERB_ATLAS_ROOM_MIN_LEVELS[_rid][_herb_id] = int(_level if previous is None else min(previous, _level))

# Dodatkowa fauna łąkowa. To zabijalne moby, ale podlegają globalnej zasadzie
# PASSIVE WORLD i nigdy nie inicjują walki bez decyzji gracza.
MOB_TEMPLATES.update({
    "meadow_hare": {"name":"Zając Łąkowy","max_hp":32,"damage":4,"damage_type":"physical","silver":8,"gold":0,"mithril":0,"stat_reward":12,"soul_reward":55,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_fox": {"name":"Lis Polny","max_hp":48,"damage":5,"damage_type":"physical","silver":13,"gold":0,"mithril":0,"stat_reward":18,"soul_reward":82,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_deer": {"name":"Jeleń Łąkowy","max_hp":72,"damage":6,"damage_type":"physical","silver":20,"gold":0,"mithril":0,"stat_reward":24,"soul_reward":112,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_stag": {"name":"Stary Jeleń","max_hp":105,"damage":8,"damage_type":"physical","silver":31,"gold":0,"mithril":0,"stat_reward":34,"soul_reward":165,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_grass_wisp": {"name":"Błędny Ognik Traw","max_hp":88,"damage":8,"damage_type":"magic","silver":28,"gold":0,"mithril":0,"stat_reward":31,"soul_reward":155,"drops":{},"quest_target":None,"auto_aggro":False},
    "meadow_field_serpent": {"name":"Wąż Polny","max_hp":58,"damage":6,"damage_type":"physical","silver":16,"gold":0,"mithril":0,"stat_reward":21,"soul_reward":98,"drops":{},"quest_target":None,"auto_aggro":False},
})

MOB_SPAWNS.extend([
    ("wildflower_basin","meadow_hare"), ("wildflower_basin","meadow_deer"),
    ("butterfly_field","meadow_hare"), ("butterfly_field","meadow_fox"),
    ("heather_field","meadow_fox"), ("heather_field","meadow_field_serpent"),
    ("wind_meadow","meadow_deer"), ("wind_meadow","meadow_field_wolf"),
    ("clover_field","meadow_hare"), ("clover_field","meadow_deer"),
    ("tall_grass_field","meadow_field_serpent"), ("tall_grass_field","meadow_wild_boar"),
    ("wet_meadow","meadow_giant_wasp"), ("wet_meadow","meadow_hare"),
    ("reed_meadow","meadow_field_serpent"), ("reed_meadow","meadow_wild_boar"),
    ("marshy_meadow","meadow_field_serpent"), ("marshy_meadow","meadow_giant_wasp"),
    ("creek_meadow","meadow_deer"), ("creek_meadow","meadow_fox"),
    ("herb_ridge","meadow_stag"), ("herb_ridge","meadow_field_wolf"),
    ("sage_hollow","meadow_grass_wisp"), ("sage_hollow","meadow_wild_boar"),
    ("valerian_lowland","meadow_grass_wisp"), ("valerian_lowland","meadow_field_serpent"),
    ("ginseng_hill","meadow_stag"), ("ginseng_hill","meadow_field_wolf"),
    ("moon_meadow","meadow_grass_wisp"), ("moon_meadow","meadow_stag"),
    ("old_stone_meadow","meadow_deer"), ("old_stone_meadow","meadow_wild_boar"),
    ("orchard_meadow","meadow_hare"), ("orchard_meadow","meadow_fox"),
    ("meadow_pond","meadow_hare"),
])

# W istniejących definicjach również zapisujemy intencję. Mechanika walki i tak
# respektuje GLOBAL_MOB_AUTO_AGGRO_ENABLED=False, ale metadane ułatwiają audyt.
for _template in MOB_TEMPLATES.values():
    if isinstance(_template, dict):
        _template["auto_aggro"] = False

GUIDE_DESTINATION_ALIASES.update({
    "zatoka": "coastal_cove", "spokojna zatoka": "coastal_cove",
    "ujscie rzeki": "river_estuary", "estuarium": "river_estuary",
    "laguna": "coastal_lagoon", "zatoka wodorostow": "kelp_bay",
    "rafa": "outer_reef", "rafa oceaniczna": "outer_reef",
    "gleboki ocean": "deep_ocean_buoy", "row oceaniczny": "trench_edge",
    "starorzecze": "oxbow_pool", "staw": "meadow_pond", "staw lakowy": "meadow_pond",
    "wrzosowisko": "heather_field", "mokra laka": "wet_meadow",
    "trzcinowa laka": "reed_meadow", "ksiezycowa laka": "moon_meadow",
    "laka motyli": "butterfly_field", "dzikie kwiaty": "wildflower_basin",
})

HELP_TOPICS["pasywny_swiat"] = [
    "GLOBALNA ZASADA: żaden zwykły mob ani boss w Soulbound nie rozpoczyna walki automatycznie.",
    "Moby mogą chodzić między lokacjami i mogą wejść do pokoju gracza, ale samo spotkanie nigdy nie uruchamia combat loopa.",
    "Walkę rozpoczyna gracz komendą atakuj <mob> / k <mob> albo świadomą ofensywną akcją na wybranym celu.",
    "Po rozpoczęciu walki przeciwnik normalnie kontratakuje według timera realtime aż do śmierci, ucieczki lub zakończenia starcia.",
    "Zasada dotyczy całego świata: łąk, dziczy, ruin, jaskiń, krypt, wież, bossów, endgame i przyszłych biomów.",
]
HELP_TOPICS["akweny"] = [
    "v0.12.0 rozbudowuje Wędkarstwo przestrzennie: rzeki, potoki, starorzecze, jeziorne zatoki, staw, wybrzeże, estuarium, lagunę, morze, rafę, szelf i głęboki ocean.",
    "Różne stanowiska tego samego typu wody preferują inne gatunki, ale nigdy nie omijają wymaganego levelu Wędki.",
    "Nowe łowiska tworzą pętle i alternatywne trasy zamiast pojedynczego liniowego pomostu.",
    "Komenda atlas / dziennik ryb nadal pokazuje progresję gatunków, a opis łowiska podaje typ akwenu.",
]
HELP_TOPICS["rozlegle_laki"] = [
    "v0.12.0 rozbudowuje Łąki o suche, kwietne, wrzosowe, wysokotrawiaste, mokre i późniejsze zielarskie siedliska.",
    "Nowe łąki mają własne preferowane zestawy ziół, ale pełna progresja Zielarstwa 1-400 pozostaje zachowana.",
    "Na łąkach żyją i przemieszczają się moby, lecz zgodnie z zasadą PASSIVE WORLD nigdy nie atakują pierwsze.",
    "Staw pośród Łąk jest jednocześnie łowiskiem i terenem zielarskim.",
]
HELP_TOPIC_ALIASES.update({
    "pasywny swiat":"pasywny_swiat", "pasywny świat":"pasywny_swiat", "brak aggro":"pasywny_swiat", "aggro":"pasywny_swiat",
    "akweny":"akweny", "lowiska":"akweny", "łowiska":"akweny", "oceany":"akweny",
    "rozlegle laki":"rozlegle_laki", "rozległe łąki":"rozlegle_laki", "laki":"rozlegle_laki", "łąki":"rozlegle_laki",
})


# ============================================================
# v0.13.0 - HYBRID PROCEDURAL WORLD
# Stały rdzeń świata (miasta, drogi, quest huby i landmarki) pozostaje ręczny.
# Naturalne pogranicza i endgame dostają duże, deterministyczne mapy tworzone
# dopiero przy wejściu. Ten sam seed + biom + współrzędne zawsze daje ten sam pokój.
# ============================================================
V013_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0130-hybrid-world"
V013_FRONTIER_SIDE = 12
V013_FRONTIER_ROOMS_PER_BIOME = V013_FRONTIER_SIDE * V013_FRONTIER_SIDE

V013_FRONTIER_SPECS = {
    "meadow": {
        "zone": "Proceduralne Łąki", "anchor": "v0100_laki_001", "direction": "north",
        "base_mastery": 1, "step": 2,
        "titles": ("Polana Dzikich Kwiatów", "Łąka Wysokich Traw", "Wietrzne Pastwisko", "Koniczynowa Niecka", "Wrzosowa Polana"),
        "features": ("stary kamienny krąg", "małe oczko wodne", "pas dzikich kwiatów", "opuszczony szałas", "kępę pachnących ziół"),
        "mobs": ("meadow_hare", "meadow_fox", "meadow_deer", "meadow_field_serpent", "meadow_field_wolf", "meadow_wild_boar"),
        "resources": ("herb_meadow",),
    },
    "forest": {
        "zone": "Proceduralny Las", "anchor": "forest_wolf_trail", "direction": "east",
        "base_mastery": 20, "step": 3,
        "titles": ("Gęsty Bór", "Omszała Polana", "Dębowa Gęstwina", "Brzozowy Parów", "Ciemny Zagajnik"),
        "features": ("powalone pradawne drzewo", "kamień porośnięty mchem", "suchy strumień", "ukrytą leśną polanę", "ślady dawnego obozu"),
        "mobs": ("shadow_wolf", "shadow_wolf_stalker", "shadow_wolf_howler", "shadow_wolf_pack_leader"),
        "resources": ("wood", "herb_forest"),
    },
    "wild": {
        "zone": "Proceduralna Dzicz", "anchor": "stone_ravine", "direction": "east",
        "base_mastery": 30, "step": 3,
        "titles": ("Kamienista Dzicz", "Cierniste Pogranicze", "Dolina Starych Tropów", "Surowa Równina", "Parów Dziczy"),
        "features": ("zarośnięty drogowskaz", "porzucone ognisko", "głazy ze starymi runami", "zwierzęcy wodopój", "wąską ścieżkę między cierniami"),
        "mobs": ("shadow_wolf", "wild_ash_boar", "wild_thorn_wolf", "goblin_scout", "bandit_scout"),
        "resources": ("wood",),
    },
    "mountain": {
        "zone": "Proceduralne Góry", "anchor": "lava_fissure", "direction": "east",
        "base_mastery": 70, "step": 4,
        "titles": ("Skalna Grań", "Wysoka Przełęcz", "Kamienna Półka", "Wąwóz Szczytów", "Smagana Wiatrem Grań"),
        "features": ("odsłoniętą żyłę minerału", "stare osuwisko", "kamienny schron", "głęboką szczelinę", "ślady kozic na skale"),
        "mobs": ("mountain_ice_wolf", "mountain_stone_ram", "mountain_harpy", "mountain_troll"),
        "resources": ("mine",),
    },
    "swamp": {
        "zone": "Proceduralne Mokradła", "anchor": "fungal_bog", "direction": "north",
        "base_mastery": 90, "step": 4,
        "titles": ("Czarne Rozlewisko", "Trzcinowe Mokradło", "Gnijące Torfowisko", "Zatopiona Grobla", "Mglista Niecka"),
        "features": ("kępy świecących grzybów", "zatopiony kamień", "martwe drzewo", "gęsty pas trzcin", "małe błotne źródło"),
        "mobs": ("swamp_crawler", "swamp_serpent", "swamp_mire_witch"),
        "resources": ("herb_water",),
    },
    "desert": {
        "zone": "Proceduralna Pustynia", "anchor": "desert_oasis", "direction": "east",
        "base_mastery": 110, "step": 4,
        "titles": ("Morze Wydm", "Czerwony Kanion", "Szklana Równina", "Kamienista Niecka", "Szlak Gorącego Wiatru"),
        "features": ("fragment zasypanej ruiny", "ciemną skałę wystającą z piasku", "wyschniętą studnię", "ślady dawnej karawany", "pas szkliwionego piasku"),
        "mobs": ("desert_raider", "dune_scorpion", "sand_wraith"),
        "resources": ("mine",),
    },
    "coast": {
        "zone": "Proceduralne Wybrzeże", "anchor": "v0100_wybrzeze_001", "direction": "north",
        "base_mastery": 40, "step": 3,
        "titles": ("Skalisty Brzeg", "Piaszczysta Zatoka", "Klif Nad Morzem", "Płycizna Przypływu", "Wietrzne Molo"),
        "features": ("małą zatoczkę", "wyrzucone przez morze drewno", "basen pływowy", "pas muszli", "stare pale pomostu"),
        "mobs": ("coast_rock_crab", "coast_sea_raider"),
        "resources": ("fish_sea",),
    },
    "ocean": {
        "zone": "Proceduralny Ocean", "anchor": "outer_reef", "direction": "north",
        "base_mastery": 80, "step": 4,
        "titles": ("Otwarta Toń", "Głęboki Szelf", "Błękitny Prąd", "Rafa Dalekiego Morza", "Ciemna Głębia"),
        "features": ("wir chłodnej wody", "pas wodorostów", "wynurzoną skałę", "dryfującą boję", "ciemną krawędź głębi"),
        "mobs": ("coast_sea_raider", "coast_rock_crab"),
        "resources": ("fish_ocean",),
    },
    "river": {
        "zone": "Proceduralne Dorzecze", "anchor": "willow_bend", "direction": "north",
        "base_mastery": 20, "step": 2,
        "titles": ("Rzeczne Zakole", "Kamienny Bród", "Trzcinowy Brzeg", "Szybki Nurt", "Źródlana Odnoga"),
        "features": ("piaszczystą łachę", "zwalone drzewo nad wodą", "głęboki dołek nurtu", "kępę trzcin", "kamienny próg rzeczny"),
        "mobs": ("meadow_deer", "meadow_fox", "meadow_field_serpent", "bandit_scout"),
        "resources": ("fish_river", "herb_water"),
    },
    "lake": {
        "zone": "Proceduralne Pojezierze", "anchor": "deepwater_pier", "direction": "east",
        "base_mastery": 30, "step": 2,
        "titles": ("Cicha Zatoka", "Trzcinowy Brzeg", "Żwirowa Zatoczka", "Głęboka Toń", "Leśne Jezioro"),
        "features": ("stary pomost", "pas lilii wodnych", "głęboką zatokę", "małą wyspę", "zatopiony pień"),
        "mobs": ("meadow_hare", "meadow_deer", "meadow_field_wolf", "shadow_wolf"),
        "resources": ("fish_lake", "herb_water"),
    },
    "frozen": {
        "zone": "Proceduralne Lodowe Pustkowia", "anchor": "ice_cave_crystal_chamber", "direction": "north",
        "base_mastery": 140, "step": 5,
        "titles": ("Pole Niebieskiego Lodu", "Szczelina Szronu", "Kryształowa Grota", "Zamarznięta Galeria", "Lodowy Parów"),
        "features": ("żyłę lodowego kryształu", "zamarznięty wodospad", "pękniętą kolumnę lodu", "ciemną szczelinę", "warstwę pradawnego szronu"),
        "mobs": ("ice_crystal_golem", "ice_fang_wolf", "ice_wraith", "ice_glacier_guard"),
        "resources": ("mine",),
    },
    "ash": {
        "zone": "Proceduralne Popielne Rubieże", "anchor": "cinder_ravine", "direction": "east",
        "base_mastery": 220, "step": 6,
        "titles": ("Morze Popiołu", "Wąwóz Żaru", "Pole Czarnego Pyłu", "Spękana Równina", "Martwe Palenisko"),
        "features": ("dogasającą szczelinę", "stos zwęglonych kości", "czarną żyłę minerału", "ruinę pieca", "wir gorącego popiołu"),
        "mobs": ("cinder_wraith", "ash_revenant", "charred_colossus", "ash_seer"),
        "resources": ("mine",),
    },
    "sky": {
        "zone": "Proceduralne Rubieże Nieba", "anchor": "thunder_shelf", "direction": "east",
        "base_mastery": 260, "step": 6,
        "titles": ("Most Chmur", "Gromowa Półka", "Taras Nawałnicy", "Rozdarta Grań", "Podniebna Platforma"),
        "features": ("wir elektrycznych chmur", "pęknięty filar", "wiszącą skałę", "runiczny piorunochron", "szczelinę między chmurami"),
        "mobs": ("skybreaker", "storm_seraph", "thunder_harrier", "cloud_titan"),
        "resources": ("mine",),
    },
    "void": {
        "zone": "Proceduralne Wybrzeże Pustki", "anchor": "black_tide_flats", "direction": "east",
        "base_mastery": 300, "step": 7,
        "titles": ("Czarny Brzeg", "Bezgwiezdna Zatoka", "Molo Pustki", "Martwy Przypływ", "Zatopiony Taras"),
        "features": ("czarną sadzawkę", "wrak bez żagli", "milczący dzwon", "ciemną rafę", "zatopiony posąg"),
        "mobs": ("black_tide_oracle", "void_mariner", "starless_knight", "abyssal_manta"),
        "resources": ("fish_ocean",),
    },
    "crown": {
        "zone": "Proceduralne Rubieże Korony", "anchor": "absolute_gallery", "direction": "east",
        "base_mastery": 340, "step": 5,
        "titles": ("Grobla Absolutu", "Taras Milczących Gwiazd", "Galeria Wieczności", "Biała Platforma", "Ponadczasowa Grań"),
        "features": ("biały monolit", "pęknięty zegar runiczny", "kamień świecący bez cienia", "zamkniętą bramę", "krąg nieruchomego światła"),
        "mobs": ("timeless_magister", "crown_sentinel", "worldcrown_echo", "absolute_guardian"),
        "resources": ("mine",),
    },
}

V013_REVERSE_DIRECTION = {
    "north": "south", "south": "north", "east": "west", "west": "east",
    "up": "down", "down": "up",
}


def v0130_frontier_room_id(kind, x, y):
    return f"v0130_frontier_{kind}_{int(x):02d}_{int(y):02d}"


def v0130_frontier_room_identity(room_id):
    match = re.fullmatch(r"v0130_frontier_([a-z]+)_(\d{2})_(\d{2})", str(room_id or ""))
    if not match:
        return None
    kind, sx, sy = match.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x, y = int(sx), int(sy)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    return kind, x, y


def v0130_frontier_room_ids(kind):
    return tuple(
        v0130_frontier_room_id(kind, x, y)
        for y in range(V013_FRONTIER_SIDE)
        for x in range(V013_FRONTIER_SIDE)
    )


def v0130_gateway_id(kind):
    return f"v0130_gateway_{kind}"


def v0130_build_static_gateways():
    for kind, spec in V013_FRONTIER_SPECS.items():
        anchor = spec["anchor"]
        direction = spec["direction"]
        if anchor not in ROOMS:
            raise RuntimeError(f"Brak kotwicy proceduralnego biomu {kind}: {anchor}")
        if direction in ROOMS[anchor].setdefault("exits", {}):
            raise RuntimeError(f"Zajęty kierunek {direction} w kotwicy {anchor}")
        gateway = v0130_gateway_id(kind)
        reverse = V013_REVERSE_DIRECTION[direction]
        root = v0130_frontier_room_id(kind, 0, 0)
        anchor_zone = ROOMS[anchor].get("zone", "Dzicz")
        ROOMS[gateway] = {
            "zone": anchor_zone,
            "name": f"Granica: {spec['zone']}",
            "desc": (
                "Stały punkt orientacyjny na granicy ręcznie zaprojektowanego świata. "
                "Dalej zaczyna się rozległy teren proceduralny. Układ sektorów jest "
                "deterministyczny i nie zmienia się po restarcie serwera."
            ),
            "exits": {reverse: anchor, direction: root},
            "procedural_gateway": kind,
        }
        ROOMS[anchor]["exits"][direction] = gateway


def _v0130_apply_resources(room_id, spec):
    for resource in spec.get("resources", ()):
        if resource == "herb_meadow":
            HERBALISM_ROOMS.add(room_id)
            MEADOW_HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "meadow"
        elif resource == "herb_forest":
            HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "forest"
        elif resource == "herb_water":
            HERBALISM_ROOMS.add(room_id)
            V012_MEADOW_HERB_GROUP[room_id] = "water"
        elif resource == "wood":
            WOODCUTTING_ROOMS.add(room_id)
        elif resource == "mine":
            # v0.25.1: geologiczny motyw może wystąpić wizualnie, ale
            # wydobycie jest dostępne wyłącznie w Kopalni Głębinowej.
            pass
        elif resource == "fish_river":
            RIVER_FISHING_ROOMS.add(room_id)
            FRESHWATER_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralna rzeka"
        elif resource == "fish_lake":
            LAKE_FISHING_ROOMS.add(room_id)
            FRESHWATER_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralne jezioro"
        elif resource == "fish_sea":
            SEA_FISHING_ROOMS.add(room_id)
            MARINE_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralne morze"
        elif resource == "fish_ocean":
            OCEAN_FISHING_ROOMS.add(room_id)
            MARINE_FISHING_ROOMS.add(room_id)
            FISHING_ROOMS.add(room_id)
            FISHING_WATER_TYPE_OVERRIDES[room_id] = "Proceduralny ocean"


def v0130_create_frontier_room_definition(room_id):
    identity = v0130_frontier_room_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y = identity
    spec = V013_FRONTIER_SPECS[kind]
    seed_text = f"{V013_WORLD_SEED}:{kind}:{x}:{y}"
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    title = rng.choice(spec["titles"])
    feature = rng.choice(spec["features"])
    distance = x + y
    mastery = min(400, int(spec["base_mastery"]) + distance * int(spec["step"]))
    exits = {}
    if x > 0:
        exits["west"] = v0130_frontier_room_id(kind, x - 1, y)
    if x + 1 < V013_FRONTIER_SIDE:
        exits["east"] = v0130_frontier_room_id(kind, x + 1, y)
    if y > 0:
        exits["south"] = v0130_frontier_room_id(kind, x, y - 1)
    if y + 1 < V013_FRONTIER_SIDE:
        exits["north"] = v0130_frontier_room_id(kind, x, y + 1)
    if x == 0 and y == 0:
        direction = spec["direction"]
        exits[V013_REVERSE_DIRECTION[direction]] = v0130_gateway_id(kind)

    # v0.14.0: wejścia do mini-lochów są częścią trwałego seedu sektora.
    # Funkcja jest zdefiniowana niżej; nazwa rozwiązuje się dopiero przy
    # faktycznym generowaniu pokoju po zakończeniu importu modułu.
    if "v0140_has_mini_dungeon" in globals() and v0140_has_mini_dungeon(kind, x, y):
        exits["down"] = v0140_mini_room_id(kind, x, y, 1)
    if "v0180_has_great_ruin" in globals() and v0180_has_great_ruin(kind, x, y):
        exits["up"] = v0180_ruin_room_id(kind, x, y, 1)

    ROOMS[room_id] = {
        "zone": spec["zone"],
        "name": f"{title} — sektor {x + 1}-{y + 1}",
        "desc": (
            f"Rozległy sektor biomu {spec['zone']}. Wyróżnia się tu {feature}. "
            "Teren został wygenerowany z trwałego seedu świata, więc po ponownym "
            "uruchomieniu serwera zachowuje ten sam układ i charakter."
        ),
        "exits": exits,
        "recommended_mastery": mastery,
        "procedural_surface": True,
        "generated_on_demand": True,
        "procedural_biome": kind,
        "procedural_x": x,
        "procedural_y": y,
    }
    if "v0140_has_mini_dungeon" in globals() and v0140_has_mini_dungeon(kind, x, y):
        ROOMS[room_id]["desc"] += " W terenie ukrywa się zejście do proceduralnego mini-lochu."
        ROOMS[room_id]["v0140_mini_entrance"] = True
    if "v0180_has_great_ruin" in globals() and v0180_has_great_ruin(kind, x, y):
        ROOMS[room_id]["desc"] += " Nad sektorem wznoszą się rozległe ruiny; wejście prowadzi w górę."
        ROOMS[room_id]["v0180_great_ruin_entrance"] = True
    if "v0140_surface_secret_info" in globals():
        secret_info = v0140_surface_secret_info(room_id)
        if secret_info:
            ROOMS[room_id]["v0140_surface_secret"] = True
            ROOMS[room_id]["v0140_secret_name"] = secret_info["name"]
    _v0130_apply_resources(room_id, spec)

    mob_pool = tuple(t for t in spec.get("mobs", ()) if t in MOB_TEMPLATES)
    spawns = []
    if mob_pool:
        spawn_count = 1 + (1 if rng.random() < 0.38 else 0)
        for _ in range(spawn_count):
            spawns.append((room_id, rng.choice(mob_pool)))
    return room_id, tuple(spawns)


def v0130_refresh_exploration_catalog():
    global TRACKED_EXPLORATION_ZONES, ALL_EXPLORATION_ROOMS
    EXPLORATION_ZONE_ROOMS.clear()
    for room_id, room in ROOMS.items():
        EXPLORATION_ZONE_ROOMS.setdefault(room["zone"], []).append(room_id)
    for kind, spec in V013_FRONTIER_SPECS.items():
        EXPLORATION_ZONE_ROOMS.setdefault(spec["zone"], []).extend(v0130_frontier_room_ids(kind))
    for zone in EXPLORATION_ZONE_ROOMS:
        EXPLORATION_ZONE_ROOMS[zone] = sorted(set(EXPLORATION_ZONE_ROOMS[zone]))
    TRACKED_EXPLORATION_ZONES = {
        zone: tuple(room_ids)
        for zone, room_ids in EXPLORATION_ZONE_ROOMS.items()
        if len(room_ids) >= EXPLORATION_ZONE_MIN_ROOMS
    }
    ALL_EXPLORATION_ROOMS = tuple(sorted({rid for ids in EXPLORATION_ZONE_ROOMS.values() for rid in ids}))

    EXPLORATION_REWARD_ITEMS.clear()
    for zone, room_ids in TRACKED_EXPLORATION_ZONES.items():
        reward_item_id = f"exploration_relic_{_collection_slug(zone)}"
        EXPLORATION_REWARD_ITEMS[zone] = reward_item_id
        ITEMS.setdefault(reward_item_id, {
            "name": f"Pamiątka Odkrywcy: {zone}", "type": "collectible",
            "price": None, "rarity": "unique", "rarity_name": "Unikalny",
            "exploration_reward": True,
            "desc": f"Unikalna pamiątka za odkrycie 100 procent strefy {zone}.",
        })

    tiers = list(ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ()))
    if tiers:
        tiers = [(req, rank) for req, rank in tiers if rank != "Platinum"]
        tiers.append((len(ALL_EXPLORATION_ROOMS), "Platinum"))
        ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(tiers)


v0130_build_static_gateways()
V013_FIXED_CORE_ROOMS = len(ROOMS)
V013_FRONTIER_POTENTIAL_ROOMS = len(V013_FRONTIER_SPECS) * V013_FRONTIER_ROOMS_PER_BIOME
V013_PROCEDURAL_SURFACE_SHARE = V013_FRONTIER_POTENTIAL_ROOMS / float(V013_FIXED_CORE_ROOMS + V013_FRONTIER_POTENTIAL_ROOMS)
v0130_refresh_exploration_catalog()

GUIDE_DESTINATION_ALIASES.update({
    "proceduralne laki": v0130_gateway_id("meadow"), "dzikie laki": v0130_gateway_id("meadow"),
    "proceduralny las": v0130_gateway_id("forest"), "dziki las": v0130_gateway_id("forest"),
    "proceduralna dzicz": v0130_gateway_id("wild"),
    "proceduralne gory": v0130_gateway_id("mountain"),
    "proceduralne bagna": v0130_gateway_id("swamp"), "proceduralne mokradla": v0130_gateway_id("swamp"),
    "proceduralna pustynia": v0130_gateway_id("desert"),
    "proceduralne wybrzeze": v0130_gateway_id("coast"),
    "proceduralny ocean": v0130_gateway_id("ocean"),
    "proceduralna rzeka": v0130_gateway_id("river"), "proceduralne dorzecze": v0130_gateway_id("river"),
    "proceduralne jeziora": v0130_gateway_id("lake"), "proceduralne pojezierze": v0130_gateway_id("lake"),
    "proceduralny lod": v0130_gateway_id("frozen"),
    "proceduralny popiol": v0130_gateway_id("ash"),
    "proceduralne niebo": v0130_gateway_id("sky"),
    "proceduralna pustka": v0130_gateway_id("void"),
    "proceduralna korona": v0130_gateway_id("crown"),
})

HELP_TOPICS["hybrydowy_swiat"] = [
    "v0.13.0 wprowadza hybrydowy świat: miasta, główne drogi, quest huby, ważni NPC i landmarki pozostają stałe.",
    f"15 naturalnych i endgame'owych biomów ma po {V013_FRONTIER_ROOMS_PER_BIOME} proceduralnych sektorów, łącznie {V013_FRONTIER_POTENTIAL_ROOMS} możliwych lokacji powierzchniowych.",
    "Sektory są tworzone dopiero przy wejściu. Nie obciążają startu serwera tysiącami gotowych pokoi.",
    "Generator jest deterministyczny: ten sam biom i współrzędne zawsze tworzą tę samą nazwę, opis, wyjścia, zasoby i bazową obsadę mobów.",
    "Proceduralne są: łąki, las, dzicz, góry, mokradła, pustynia, wybrzeże, ocean, dorzecze, pojezierze, lód oraz cztery rubieże endgame.",
    "Profesje działają w proceduralnym świecie: odpowiednie sektory wspierają Wędkarstwo, Zielarstwo, Drwalstwo lub Górnictwo bez omijania levelu narzędzia 1-400.",
    "Moby proceduralne również podlegają PASSIVE WORLD i nigdy nie zaczynają walki same.",
    "Prowadzenie doprowadza do stałej granicy biomu; dalszą proceduralną mapę odkrywa się ręcznie.",
]
HELP_TOPIC_ALIASES.update({
    "hybrydowy swiat": "hybrydowy_swiat", "hybrydowy świat": "hybrydowy_swiat",
    "proceduralny swiat": "hybrydowy_swiat", "proceduralny świat": "hybrydowy_swiat",
    "generowany swiat": "hybrydowy_swiat", "generowany świat": "hybrydowy_swiat",
})


# ============================================================
# v0.14.0 - DYNAMIC WORLD EVENTS & SECRETS
# Opcjonalne wydarzenia, rare roaming, deterministyczne mini-lochy,
# sekrety powierzchniowe, mapy skarbów i questy eksploracyjne.
# ============================================================
V014_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0140-events-secrets"
V014_EVENT_ROTATION_SECONDS = 30 * 60
V014_TREASURE_MAP_ITEM = "treasure_map_frontier"
V014_MINI_DENOMINATOR = 18
V014_SECRET_DENOMINATOR = 17

ITEMS[V014_TREASURE_MAP_ITEM] = {
    "name": "Mapa Skarbu Rubieży",
    "type": "consumable",
    "price": None,
    "rarity": "rare",
    "rarity_name": "Rzadki",
    "treasure_map": True,
    "desc": (
        "Mapa prowadząca do jednego z deterministycznych sekretów proceduralnych rubieży. "
        "Użyj jej, aby zapisać trop; potem wpisz mapa skarbu."
    ),
}

V0243_EREN_SECRET_MAP_ITEM = "quest_map_eren_secret_marks"
ITEMS[V0243_EREN_SECRET_MAP_ITEM] = {
    "name": "Mapa Erena: Znak poza mapą",
    "type": "consumable",
    "price": None,
    "rarity": "quest",
    "rarity_name": "Questowy",
    "treasure_map": True,
    "quest_treasure_map_for": "city_cartographer_secret_marks",
    "desc": (
        "Questowa mapa Kartografa Erena. Wpisz użyj mapy, aby zapisać trop, "
        "a następnie prowadz skarb. Po porzuceniu questa mapa i jej aktywny trop znikają."
    ),
}

V014_EVENT_DEFS = {
    "rare_hunt": {
        "title": "Trop rzadkiego przeciwnika",
        "kinds": tuple(V013_FRONTIER_SPECS),
        "desc": "W sektorze pojawił się wędrujący rare. Walka pozostaje całkowicie dobrowolna.",
    },
    "fish_run": {
        "title": "Wielka ławica",
        "kinds": ("coast", "ocean", "river", "lake", "void"),
        "desc": "W tym łowisku trwa ławica: +2 do bazowego połowu i +25% XP Wędkarstwa/Wędki.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
    "herb_bloom": {
        "title": "Rozkwit rzadkich ziół",
        "kinds": ("meadow", "forest", "swamp", "river"),
        "desc": "Roślinność jest wyjątkowo obfita: +2 do bazowego zbioru i +25% XP Zielarstwa/Sierpa.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
    "rich_vein": {
        "title": "Bogata żyła",
        "kinds": ("mountain", "desert", "frozen", "ash", "sky", "crown"),
        "desc": "Odsłonięto wyjątkowo bogate złoże: +2 do bazowego urobku i +25% XP Górnictwa/Kilofa.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
    "forest_growth": {
        "title": "Rozrost starego boru",
        "kinds": ("forest", "wild", "meadow"),
        "desc": "Stare drzewa dają więcej drewna: +2 do bazowego pozyskania i +25% XP Drwalstwa/Piły.",
        "quantity_bonus": 2, "xp_mult": 1.25,
    },
}


def _v0140_hash_int(*parts):
    text = ":".join(str(part) for part in (V014_WORLD_SEED,) + parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def v0140_has_mini_dungeon(kind, x, y):
    if kind not in V013_FRONTIER_SPECS:
        return False
    return _v0140_hash_int("mini", kind, int(x), int(y)) % V014_MINI_DENOMINATOR == 0


def v0140_mini_size(kind, x, y):
    return 7 + (_v0140_hash_int("mini-size", kind, int(x), int(y)) % 6)


def v0140_mini_room_id(kind, x, y, index):
    return f"v0140_mini_{kind}_{int(x):02d}_{int(y):02d}_{int(index):02d}"


def v0140_mini_identity(room_id):
    match = re.fullmatch(r"v0140_mini_([a-z]+)_(\d{2})_(\d{2})_(\d{2})", str(room_id or ""))
    if not match:
        return None
    kind, sx, sy, si = match.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x, y, index = int(sx), int(sy), int(si)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    size = v0140_mini_size(kind, x, y)
    if not v0140_has_mini_dungeon(kind, x, y) or not (1 <= index <= size):
        return None
    return kind, x, y, index, size


def v0140_secret_room_id(kind, x, y):
    return f"v0140_secret_{kind}_{int(x):02d}_{int(y):02d}"


def v0140_secret_room_identity(room_id):
    match = re.fullmatch(r"v0140_secret_([a-z]+)_(\d{2})_(\d{2})", str(room_id or ""))
    if not match:
        return None
    kind, sx, sy = match.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x, y = int(sx), int(sy)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    parent = v0130_frontier_room_id(kind, x, y)
    if not v0140_surface_secret_info(parent):
        return None
    return kind, x, y


V014_SECRET_NAMES = (
    "Zapomniana Kapliczka", "Ukryta Grota", "Zarośnięty Skarbiec",
    "Kamienna Komnata", "Zatopiony Schowek", "Pradawny Krąg",
    "Szczelina Kartografów", "Ruina Bez Drogi",
)


def v0140_surface_secret_info(room_id):
    identity = v0130_frontier_room_identity(room_id)
    if identity is None:
        return None
    kind, x, y = identity
    value = _v0140_hash_int("secret", kind, x, y)
    if value % V014_SECRET_DENOMINATOR != 0:
        return None
    return {
        "kind": kind, "x": x, "y": y,
        "name": V014_SECRET_NAMES[(value // V014_SECRET_DENOMINATOR) % len(V014_SECRET_NAMES)],
        "room_id": room_id,
        "hidden_room": v0140_secret_room_id(kind, x, y),
    }


def v0140_surface_secret_room_ids(kind=None):
    kinds = (kind,) if kind else tuple(V013_FRONTIER_SPECS)
    result = []
    for current_kind in kinds:
        for y in range(V013_FRONTIER_SIDE):
            for x in range(V013_FRONTIER_SIDE):
                rid = v0130_frontier_room_id(current_kind, x, y)
                if v0140_surface_secret_info(rid):
                    result.append(rid)
    return tuple(result)


def v0140_event_slot(now=None):
    now = time.time() if now is None else float(now)
    return int(now // V014_EVENT_ROTATION_SECONDS)


def v0140_active_world_events(now=None):
    now = time.time() if now is None else float(now)
    slot = v0140_event_slot(now)
    result = []
    used_rooms = set()
    for event_type, definition in V014_EVENT_DEFS.items():
        rng = random.Random(_v0140_hash_int("event", slot, event_type))
        kinds = tuple(definition["kinds"])
        # Kilka prób, aby dwa typy eventu nie wylądowały w dokładnie tym samym sektorze.
        for _ in range(20):
            kind = rng.choice(kinds)
            x = rng.randrange(V013_FRONTIER_SIDE)
            y = rng.randrange(V013_FRONTIER_SIDE)
            room_id = v0130_frontier_room_id(kind, x, y)
            if room_id not in used_rooms:
                break
        used_rooms.add(room_id)
        result.append({
            "type": event_type,
            "title": definition["title"],
            "desc": definition["desc"],
            "kind": kind,
            "x": x,
            "y": y,
            "room_id": room_id,
            "slot": slot,
            "token": f"{slot}:{event_type}:{kind}:{x}:{y}",
            "expires_at": (slot + 1) * V014_EVENT_ROTATION_SECONDS,
            "quantity_bonus": int(definition.get("quantity_bonus", 0) or 0),
            "xp_mult": float(definition.get("xp_mult", 1.0) or 1.0),
        })
    return tuple(result)


def v0140_event_for_room(room_id, event_type=None, now=None):
    for event in v0140_active_world_events(now):
        if event["room_id"] == room_id and (event_type is None or event["type"] == event_type):
            return event
    return None


def v0140_gather_event_bonus(room_id, tool_type=None, now=None):
    event = v0140_event_for_room(room_id, now=now)
    expected = {
        "fish_run": "fishing",
        "herb_bloom": "herbalism",
        "rich_vein": "mining",
        "forest_growth": "woodcutting",
    }
    if not event or expected.get(event["type"]) != str(tool_type or ""):
        return {"label": "", "quantity_bonus": 0, "xp_mult": 1.0}
    return {
        "label": f"WYDARZENIE ŚWIATA — {event['title']}",
        "quantity_bonus": int(event.get("quantity_bonus", 0) or 0),
        "xp_mult": float(event.get("xp_mult", 1.0) or 1.0),
    }


def _v0140_clone_variant(base_id, *, rare=False, miniboss=False):
    base = MOB_TEMPLATES.get(base_id)
    if not base:
        return None
    suffix = "rare" if rare else "miniboss"
    variant_id = f"v0140_{suffix}_{base_id}"
    if variant_id in MOB_TEMPLATES:
        return variant_id
    data = dict(base)
    data["drops"] = dict(base.get("drops", {}))
    if rare:
        data["name"] = f"Wędrujący Rzadki {base['name']}"
        data["rare_mob"] = True
        data["rare_base_template"] = base_id
        hp_mult, dmg_mult, reward_mult = 1.75, 1.30, 2.20
    else:
        data["name"] = f"Strażnik Mini-Lochu: {base['name']}"
        data["mini_boss"] = True
        data["stationary_mob"] = True
        data["v0140_mini_boss"] = True
        hp_mult, dmg_mult, reward_mult = 2.80, 1.55, 3.20
    data["max_hp"] = max(1, int(round(int(base.get("max_hp", 1)) * hp_mult)))
    data["damage"] = max(1, int(round(int(base.get("damage", 1)) * dmg_mult)))
    data["stat_reward"] = max(1, int(round(int(base.get("stat_reward", 1)) * min(1.8, reward_mult))))
    data["soul_reward"] = max(1, int(round(int(base.get("soul_reward", 1)) * reward_mult)))
    data["class_xp_reward"] = max(50, int(round(int(base.get("class_xp_reward", max(50, int(base.get("stat_reward", 1))*10))) * reward_mult)))
    data["silver"] = max(1, int(round(int(base.get("silver", 1)) * reward_mult)))
    data["gold"] = 0
    data["mithril"] = 0
    data["auto_aggro"] = False
    data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.28 if rare else 0.45)
    data["drops"].setdefault("soul_shard", 0.45 if rare else 0.70)
    MOB_TEMPLATES[variant_id] = data
    return variant_id


for _kind, _spec in V013_FRONTIER_SPECS.items():
    for _base_id in tuple(_spec.get("mobs", ())):
        if _base_id in MOB_TEMPLATES:
            _v0140_clone_variant(_base_id, rare=True)
            _v0140_clone_variant(_base_id, miniboss=True)

# Katalogi Codexu powstały w starszej części modułu, więc dopisujemy nowe
# dynamiczne warianty do tych samych słowników referencyjnych.
for _mob_id, _data in MOB_TEMPLATES.items():
    if _mob_id.startswith("v0140_rare_"):
        RARE_MOB_COLLECTION_CATALOG[_mob_id] = _data["name"]
    if _mob_id.startswith("v0140_miniboss_"):
        BOSS_COLLECTION_CATALOG[_mob_id] = _data["name"]


def v0140_rare_template_for_kind(kind, salt="event"):
    pool = [base for base in V013_FRONTIER_SPECS[kind].get("mobs", ()) if base in MOB_TEMPLATES]
    if not pool:
        return None
    base = pool[_v0140_hash_int("rare-pick", kind, salt) % len(pool)]
    return _v0140_clone_variant(base, rare=True)


def v0140_miniboss_template_for_sector(kind, x, y):
    pool = [base for base in V013_FRONTIER_SPECS[kind].get("mobs", ()) if base in MOB_TEMPLATES]
    if not pool:
        return None
    base = pool[_v0140_hash_int("mini-boss-pick", kind, x, y) % len(pool)]
    return _v0140_clone_variant(base, miniboss=True)


def v0140_create_mini_room_definition(room_id):
    identity = v0140_mini_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y, index, size = identity
    spec = V013_FRONTIER_SPECS[kind]
    width = 3
    cx, cy = (index - 1) % width, (index - 1) // width
    exits = {}
    candidates = {
        "west": (cx - 1, cy), "east": (cx + 1, cy),
        "south": (cx, cy - 1), "north": (cx, cy + 1),
    }
    for direction, (nx, ny) in candidates.items():
        if nx < 0 or ny < 0 or nx >= width:
            continue
        neighbor = ny * width + nx + 1
        if 1 <= neighbor <= size:
            exits[direction] = v0140_mini_room_id(kind, x, y, neighbor)
    parent = v0130_frontier_room_id(kind, x, y)
    if index == 1:
        exits["up"] = parent
    final = index == size
    seed = _v0140_hash_int("mini-room", kind, x, y, index)
    rng = random.Random(seed)
    room_titles = (
        "Zawalone Przejście", "Kamienna Galeria", "Boczna Komora", "Stary Korytarz",
        "Podziemna Sala", "Szczelina Korzeni", "Zapomniany Tunel", "Komora Runiczna",
    )
    title = "Komnata Strażnika" if final else rng.choice(room_titles)
    ROOMS[room_id] = {
        "zone": f"Mini-loch: {spec['zone']}",
        "name": f"{title} — {index}/{size}",
        "desc": (
            f"Proceduralny mini-loch odkryty w sektorze {x+1}-{y+1} biomu {spec['zone']}. "
            "Układ tej podziemnej siatki jest trwały dla seedu świata."
            + (" To finałowa komnata ze strażnikiem i skrzynią." if final else "")
        ),
        "exits": exits,
        "recommended_mastery": min(400, int(spec["base_mastery"]) + (x+y)*int(spec["step"]) + index*3),
        "generated_on_demand": True,
        "v0140_mini_dungeon": True,
        "v0140_mini_kind": kind,
        "v0140_mini_index": index,
        "v0140_mini_size": size,
        "v0140_mini_final": final,
    }
    spawns = []
    mob_pool = tuple(base for base in spec.get("mobs", ()) if base in MOB_TEMPLATES)
    if final:
        boss = v0140_miniboss_template_for_sector(kind, x, y)
        if boss:
            spawns.append((room_id, boss))
        TREASURE_CHESTS.setdefault(room_id, {
            "name": f"Skrzynia Mini-Lochu: {spec['zone']}",
            "respawn": 3600,
            "base_pool": ("soul_shard", "soul_elixir", V014_TREASURE_MAP_ITEM),
            "set_pool": (),
        })
        CHEST_COLLECTION_CATALOG[room_id] = TREASURE_CHESTS[room_id]["name"]
    elif mob_pool:
        count = 1 + (1 if rng.random() < 0.45 else 0)
        for _ in range(count):
            spawns.append((room_id, rng.choice(mob_pool)))
    return room_id, tuple(spawns)


def v0140_create_secret_room_definition(room_id):
    identity = v0140_secret_room_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y = identity
    parent = v0130_frontier_room_id(kind, x, y)
    secret = v0140_surface_secret_info(parent)
    spec = V013_FRONTIER_SPECS[kind]
    ROOMS[room_id] = {
        "zone": f"Sekret: {spec['zone']}",
        "name": secret["name"],
        "desc": (
            f"Ukryta lokacja odnaleziona w sektorze {x+1}-{y+1}. "
            "Nie należy do zwykłej siatki dróg i pozostaje stała dla seedu świata."
        ),
        "exits": {"down": parent},
        "generated_on_demand": True,
        "v0140_secret_room": True,
        "v0140_secret_parent": parent,
        "recommended_mastery": min(400, int(spec["base_mastery"]) + (x+y)*int(spec["step"])),
    }
    TREASURE_CHESTS.setdefault(room_id, {
        "name": f"Ukryty Skarb: {secret['name']}",
        "respawn": 5400,
        "base_pool": ("soul_shard", V014_TREASURE_MAP_ITEM),
        "set_pool": ("soul_elixir",),
    })
    CHEST_COLLECTION_CATALOG[room_id] = TREASURE_CHESTS[room_id]["name"]
    return room_id, ()


# Kartografka i cztery jednorazowe questy eksploracyjne. Postęp jest zdarzeniowy,
# więc nic odkrytego przed przyjęciem nie daje darmowych punktów.
QUESTS.update({
    "v014_frontier_survey": {
        "name": "Mapa Żywych Rubieży", "giver": "Kartografka Lysa",
        "kind": "explore_frontier", "target": "any", "needed": 20,
        "description": "Odkryj 20 nowych sektorów proceduralnych rubieży po przyjęciu zadania.",
        "reward_silver": 3500, "reward_gold": 2, "reward_mithril": 0,
        "reward_items": {V014_TREASURE_MAP_ITEM: 1}, "repeatable": False,
    },
    "v014_secret_signs": {
        "name": "Znaki poza drogą", "giver": "Kartografka Lysa",
        "kind": "discover_secret", "target": "any", "needed": 3,
        "description": "Odkryj 3 nowe sekrety proceduralnego świata. W podejrzanym sektorze użyj sekret.",
        "requires_quest": "v014_frontier_survey",
        "reward_silver": 6000, "reward_gold": 4, "reward_mithril": 0,
        "reward_items": {V014_TREASURE_MAP_ITEM: 2}, "repeatable": False,
    },
    "v014_mini_depths": {
        "name": "Małe głębiny", "giver": "Kartografka Lysa",
        "kind": "mini_dungeon", "target": "any", "needed": 2,
        "description": "Dotrzyj do finałowej komnaty 2 nowych proceduralnych mini-lochów.",
        "requires_quest": "v014_secret_signs",
        "reward_silver": 9000, "reward_gold": 6, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 2}, "repeatable": False,
    },
    "v014_living_world": {
        "name": "Świat, który się porusza", "giver": "Kartografka Lysa",
        "kind": "world_event", "target": "any", "needed": 3,
        "description": "Odwiedź 3 nowe aktywne wydarzenia świata po przyjęciu zadania. Komenda wydarzenia pokazuje aktualne cele.",
        "requires_quest": "v014_mini_depths",
        "reward_silver": 12000, "reward_gold": 10, "reward_mithril": 0,
        "reward_items": {V014_TREASURE_MAP_ITEM: 2, "soul_elixir": 2}, "repeatable": False,
    },
})

NPCS["cartographer_lysa"] = {
    "name": "Kartografka Lysa", "room": "library",
    "dialogue": (
        "Stałe drogi znamy dobrze, ale rubieże żyją własnym rytmem. "
        "Zbieram mapy nowych sektorów, sekretów, mini-lochów i wydarzeń świata."
    ),
    "quest": "v014_frontier_survey",
    "quest_chain": (
        "v014_frontier_survey", "v014_secret_signs", "v014_mini_depths", "v014_living_world",
    ),
}

HELP_TOPICS["wydarzenia_swiata"] = [
    "Komenda wydarzenia / events pokazuje pięć aktualnych eventów proceduralnego świata. Zestaw zmienia się co 30 minut.",
    "Eventy nie teleportują i nie atakują gracza. Podają biom oraz sektor, do którego można dojść normalnie.",
    "Polowanie na rare tworzy pasywnego wędrującego rare; walkę nadal rozpoczyna wyłącznie gracz.",
    "Ławica, rozkwit ziół, bogata żyła i rozrost boru dają +2 do bazowego zbioru i +25 procent XP właściwej profesji/narzędzia w sektorze eventu.",
]
HELP_TOPICS["mini_lochy"] = [
    "Część proceduralnych sektorów ma trwałe zejście do mini-lochu generowanego na żądanie.",
    "Mini-loch ma 7-12 pokojów ułożonych w małą siatkę z pętlami; finał ma pasywnego mini-bossa i odnawialną skrzynię.",
    "Mini-lochy nie zastępują dużych Krypt i Wież. Są krótkimi odkryciami podczas eksploracji powierzchni.",
]
HELP_TOPICS["sekrety_swiata"] = [
    "W części proceduralnych sektorów istnieje deterministyczny sekret. Komenda sekret odkrywa go osobno dla postaci.",
    "Po odkryciu wpisz sekret ponownie w tym samym sektorze, aby wejść do ukrytej komnaty ze skrzynią.",
    "Mapa Skarbu Rubieży może wskazać jeden nieodkryty sekret. Wpisz mapa skarbu, aby sprawdzić zapisane tropy.",
]
HELP_TOPIC_ALIASES.update({
    "wydarzenia": "wydarzenia_swiata", "eventy": "wydarzenia_swiata", "events": "wydarzenia_swiata",
    "mini lochy": "mini_lochy", "minilochy": "mini_lochy", "mini-lochy": "mini_lochy",
    "sekrety swiata": "sekrety_swiata", "sekrety świata": "sekrety_swiata", "mapy skarbow": "kartografia", "mapy skarbów": "kartografia",
})

# ============================================================
# v0.15.0 - WORLD LIFE & PROGRESSION (NO TRAPS)
# ============================================================
V015_DAY_SECONDS = 7200
V015_WEATHER_SECONDS = 1800
V015_DYNAMIC_QUEST_SECONDS = 3600
V015_BIOME_MASTERY_THRESHOLDS = (25, 50, 75, 100)
V015_TIME_PHASES = (
    ("swit", "Świt"), ("dzien", "Dzień"), ("zmierzch", "Zmierzch"), ("noc", "Noc"),
)
V015_WEATHER_POOLS = {
    "meadow": ("bezchmurnie", "lekki_deszcz", "wiatr", "mgla"),
    "forest": ("bezchmurnie", "lekki_deszcz", "mgla", "ulewa"),
    "wild": ("bezchmurnie", "wiatr", "lekki_deszcz", "mgla"),
    "mountain": ("bezchmurnie", "silny_wiatr", "snieg", "burza"),
    "swamp": ("mgla", "lekki_deszcz", "ulewa", "bezchmurnie"),
    "desert": ("bezchmurnie", "upal", "wiatr", "burza_piaskowa"),
    "coast": ("bezchmurnie", "morska_mgla", "wiatr", "ulewa"),
    "ocean": ("bezchmurnie", "morska_mgla", "wiatr", "sztorm"),
    "river": ("bezchmurnie", "lekki_deszcz", "mgla", "ulewa"),
    "lake": ("bezchmurnie", "lekki_deszcz", "mgla", "wiatr"),
    "frozen": ("bezchmurnie", "snieg", "zamiec", "mgla"),
    "ash": ("popiol", "goracy_wiatr", "bezchmurnie", "burza_popiolowa"),
    "sky": ("wiatr", "burza", "bezchmurnie", "mgla"),
    "void": ("bezchmurnie", "czarna_mgla", "wiatr", "martwy_deszcz"),
    "crown": ("bezchmurnie", "biala_mgla", "wiatr", "cichy_deszcz"),
}
V015_WEATHER_LABELS = {
    "bezchmurnie":"Bezchmurnie", "lekki_deszcz":"Lekki deszcz", "wiatr":"Wiatr",
    "mgla":"Mgła", "ulewa":"Ulewa", "silny_wiatr":"Silny wiatr", "snieg":"Śnieg",
    "burza":"Burza", "upal":"Upał", "burza_piaskowa":"Burza piaskowa", "morska_mgla":"Morska mgła",
    "sztorm":"Sztorm", "zamiec":"Zamieć", "popiol":"Opad popiołu", "goracy_wiatr":"Gorący wiatr",
    "burza_popiolowa":"Burza popiołowa", "czarna_mgla":"Czarna mgła", "martwy_deszcz":"Martwy deszcz",
    "biala_mgla":"Biała mgła", "cichy_deszcz":"Cichy deszcz",
}
V015_BIOME_TITLE_BASE = {
    kind: spec["zone"] for kind, spec in V013_FRONTIER_SPECS.items()
}


def v0150_time_state(now=None):
    now = time.time() if now is None else float(now)
    pos = (now % V015_DAY_SECONDS) / V015_DAY_SECONDS
    idx = min(3, int(pos * 4))
    key, label = V015_TIME_PHASES[idx]
    return {"key": key, "label": label, "cycle_percent": int(pos * 100)}


def v0150_weather_state(room_id, now=None):
    identity = v0130_frontier_room_identity(room_id)
    if not identity:
        return {"kind":"", "weather":"bezchmurnie", "label":"Spokojna pogoda", "slot":0}
    kind, x, y = identity
    now = time.time() if now is None else float(now)
    slot = int(now // V015_WEATHER_SECONDS)
    pool = V015_WEATHER_POOLS.get(kind, ("bezchmurnie",))
    idx = _v0140_hash_int("v015-weather", kind, slot) % len(pool)
    weather = pool[idx]
    return {"kind":kind, "weather":weather, "label":V015_WEATHER_LABELS.get(weather, weather), "slot":slot}


def v0150_environment_bonus(room_id, tool_type=None, now=None):
    identity = v0130_frontier_room_identity(room_id)
    if not identity:
        return {"label":"", "quantity_bonus":0, "xp_mult":1.0}
    weather = v0150_weather_state(room_id, now)
    phase = v0150_time_state(now)
    tool = str(tool_type or "")
    mult = 1.0
    wet = {"lekki_deszcz","ulewa","morska_mgla","mgla","sztorm","cichy_deszcz"}
    wind = {"wiatr","silny_wiatr","burza","sztorm","burza_piaskowa","zamiec","burza_popiolowa"}
    if tool == "fishing" and weather["weather"] in wet:
        mult *= 1.08
    if tool == "herbalism" and weather["weather"] in wet:
        mult *= 1.08
    if tool == "mining" and weather["weather"] in wind:
        mult *= 1.05
    if tool == "woodcutting" and weather["weather"] in {"bezchmurnie","wiatr","lekki_deszcz"}:
        mult *= 1.05
    if phase["key"] in {"swit","zmierzch"} and tool in {"fishing","herbalism"}:
        mult *= 1.04
    return {
        "label": f"Warunki: {weather['label']}, {phase['label']}",
        "quantity_bonus": 0,
        "xp_mult": round(mult, 4),
    }


def v0150_biome_mastery_title(kind, threshold):
    zone = V013_FRONTIER_SPECS[kind]["zone"]
    prefix = {25:"Wędrowiec",50:"Znawca",75:"Strażnik",100:"Mistrz"}.get(int(threshold), "Odkrywca")
    return f"{prefix}: {zone}"


def v0150_dynamic_quest_slot(now=None):
    now = time.time() if now is None else float(now)
    return int(now // V015_DYNAMIC_QUEST_SECONDS)


def v0150_dynamic_world_offer(account_id, now=None):
    slot = v0150_dynamic_quest_slot(now)
    kinds = tuple(V013_FRONTIER_SPECS)
    qtypes = ("explore", "event", "secret", "mini", "fish", "herb", "mine", "wood")
    qtype = qtypes[_v0140_hash_int("v015-dq-type", account_id, slot) % len(qtypes)]
    kind = kinds[_v0140_hash_int("v015-dq-kind", account_id, slot) % len(kinds)]
    target = kind if qtype in {"explore"} else "any"
    needs = {"explore":12, "event":2, "secret":2, "mini":1, "fish":12, "herb":12, "mine":12, "wood":12}
    labels = {
        "explore":f"Zbadaj nowe sektory: {V013_FRONTIER_SPECS[kind]['zone']}",
        "event":"Odwiedź aktywne wydarzenia świata", "secret":"Odkryj sekrety rubieży",
        "mini":"Dotrzyj do finału proceduralnego mini-lochu", "fish":"Złów ryby",
        "herb":"Zbierz zioła", "mine":"Wydobądź surowce", "wood":"Pozyskaj drewno",
    }
    needed = needs[qtype]
    stage=max(1,min(400,int(V013_FRONTIER_SPECS[kind].get("base_mastery",1) or 1)))
    complexity=1.5 if qtype in {"event","secret","mini"} else 1.0
    reward_soul=max(1,int(round(v0190_log_curve(stage,V019_SOUL_KILL_NORMAL)*max(2.0,math.sqrt(needed))*complexity)))
    reward_coins=max(1,int(round(v0190_log_curve(stage,V019_QUEST_COIN)*complexity)))
    reward_gold=max(1,reward_coins//SILVER_PER_GOLD)
    return {
        "quest_key":f"v015:{slot}:{qtype}:{kind}", "quest_type":qtype, "target":target,
        "label":labels[qtype], "needed":needed, "progress":0, "reward_soul_xp":reward_soul,
        "reward_gold":reward_gold, "accepted_slot":slot, "completed":False,
    }

HELP_TOPICS["pogoda"] = [
    "pogoda / weather pokazuje aktualną pogodę, porę cyklu i ewentualny mały bonus profesyjny.",
    "Pogoda nigdy nie blokuje łowienia, zbierania, questów, ruchu ani walki. Nie ma kar za złą pogodę.",
    "Cykl świata ma Świt, Dzień, Zmierzch i Noc. Zmienia klimat oraz drobne bonusy, nie zamyka zawartości.",
]
HELP_TOPICS["biome_mastery"] = [
    "biom / mastery pokazuje postęp Biome Mastery proceduralnych rubieży.",
    "Progi 25, 50, 75 i 100 procent odkrycia odblokowują wpisy Codexu i tytuły.",
]
HELP_TOPICS["dynamiczne_questy"] = [
    "zadanie świata / worldquest pokazuje rotacyjną ofertę. worldquest accept przyjmuje ją od 0/x.",
    "Przyjęte zadanie nie znika po zmianie rotacji. worldquest aktywne pokazuje postęp, worldquest odbierz odbiera nagrodę.",
]
HELP_TOPIC_ALIASES.update({
    "pogoda":"pogoda", "weather":"pogoda", "pora dnia":"pogoda", "dzien noc":"pogoda",
    "biom":"biome_mastery", "mastery":"biome_mastery", "biome mastery":"biome_mastery",
    "zadanie swiata":"dynamiczne_questy", "zadanie świata":"dynamiczne_questy", "worldquest":"dynamiczne_questy",
})
COMMAND_ALIASES.update({
    "pogoda":"weather", "weather":"weather", "pora":"weather", "poradnia":"weather",
    "biom":"biomemastery", "biome":"biomemastery", "mastery":"biomemastery", "biomemastery":"biomemastery",
    "worldquest":"worldquest", "worldquests":"worldquest", "zadanieswiata":"worldquest", "zadanieświata":"worldquest",
    "zadanie_swiata":"worldquest", "dynamicquest":"worldquest",
})


# ============================================================
# v0.16.0 - FACTIONS, TRAVELERS & WORLD BOSSES (NO TRAPS)
# ============================================================
V016_WORLD_BOSS_ROTATION_SECONDS = 2 * 60 * 60
V016_LEGENDARY_ROTATION_SECONDS = 60 * 60
V016_TRAVELER_STEP_SECONDS = 15 * 60
V016_FACTION_THRESHOLDS = (25, 75, 150, 300)

V016_FACTIONS = {
    "cartographers": {
        "name": "Liga Kartografów", "zone": "Rubieże i eksploracja",
        "desc": "Badacze dróg, sekretów, mini-lochów i nieopisanych sektorów.",
    },
    "waters": {
        "name": "Bractwo Wód", "zone": "Rzeki, jeziora, morza i ocean",
        "desc": "Rybacy, przewodnicy i badacze wielkich akwenów.",
    },
    "miners": {
        "name": "Kamienny Związek", "zone": "Góry i kopalnie",
        "desc": "Górnicy i poszukiwacze żył, minerałów i klejnotów.",
    },
    "green_path": {
        "name": "Krąg Zielonego Szlaku", "zone": "Lasy, łąki i mokradła",
        "desc": "Zielarze i drwale dbający o dzikie tereny i ich zasoby.",
    },
    "frontier_watch": {
        "name": "Straż Rubieży", "zone": "Łowy i najdalszy endgame",
        "desc": "Łowcy rare, legendary rare i world bossów. Walka zawsze pozostaje dobrowolna.",
    },
}

V016_FACTION_RANKS = (
    (0, "Nieznajomy"), (25, "Sympatyk"), (75, "Zaufany"),
    (150, "Sojusznik"), (300, "Mistrz Frakcji"),
)

for _fid, _fdata in V016_FACTIONS.items():
    _badge = f"v016_badge_{_fid}"
    ITEMS.setdefault(_badge, {
        "name": f"Odznaka: {_fdata['name']}", "type": "collectible", "price": None,
        "rarity": "unique", "rarity_name": "Unikalny",
        "desc": f"Pamiątkowa odznaka za wysoką reputację: {_fdata['name']}.",
    })


def v0160_faction_rank(reputation):
    reputation = max(0, int(reputation or 0))
    result = V016_FACTION_RANKS[0][1]
    for threshold, label in V016_FACTION_RANKS:
        if reputation >= threshold:
            result = label
    return result


# Pięć małych stałych punktów orientacyjnych przy proceduralnych rubieżach.
# Same rubieże nadal pozostają generowane; osady są kotwicami, nie nowymi miastami.
V016_SETTLEMENTS = {
    "cartographers": {
        "kind": "meadow", "branch": "east", "back": "west",
        "zone": "Posterunek Kartografów", "name": "Posterunek Kartografów",
        "rooms": (
            ("v016_cartographers_square", "Plac Map", "Stoły z mapami i tablicami kierunków stoją pod lekkimi zadaszeniami."),
            ("v016_cartographers_archive", "Archiwum Rubieży", "Małe archiwum przechowuje opisy odkrytych sektorów, sekretów i szlaków."),
            ("v016_cartographers_camp", "Obóz Mierniczych", "Kartografowie odpoczywają tu przed kolejnymi wyprawami."),
        ),
    },
    "waters": {
        "kind": "coast", "branch": "east", "back": "west",
        "zone": "Przystań Bractwa Wód", "name": "Przystań Bractwa Wód",
        "rooms": (
            ("v016_waters_square", "Nabrzeże Bractwa", "Pomosty i magazyny łączą rybaków rzek, jezior, mórz i oceanu."),
            ("v016_waters_hall", "Dom Sieci", "Wędkarze wymieniają informacje o ławicach, rekordach i nietypowych połowach."),
            ("v016_waters_store", "Skład Wodny", "Niewielki skład przechowuje sprzęt wyprawowy i skrzynie z połowami."),
        ),
    },
    "miners": {
        "kind": "mountain", "branch": "north", "back": "south",
        "zone": "Posterunek Kamiennego Związku", "name": "Posterunek Kamiennego Związku",
        "rooms": (
            ("v016_miners_square", "Kamienny Dziedziniec", "Punkt zbiórki górników przed wyprawami w góry i głębokie kopalnie."),
            ("v016_miners_hall", "Sala Żył", "Na kamiennych tablicach zaznaczono odkryte złoża i stare tunele."),
            ("v016_miners_workshop", "Warsztat Geologów", "Młotki, sita i próbki skał wypełniają niewielki warsztat."),
        ),
    },
    "green_path": {
        "kind": "forest", "branch": "north", "back": "south",
        "zone": "Osada Zielonego Szlaku", "name": "Osada Zielonego Szlaku",
        "rooms": (
            ("v016_green_square", "Polana Zielonego Szlaku", "Spokojna polana łączy szlaki zielarzy i drwali."),
            ("v016_green_hall", "Dom Ziół i Drewna", "Suszą się tu zioła, a próbki drewna opisano według regionów."),
            ("v016_green_garden", "Ogród Wędrowców", "Mały ogród pokazuje rośliny spotykane na wielu biomach."),
        ),
    },
    "frontier_watch": {
        "kind": "wild", "branch": "north", "back": "south",
        "zone": "Obóz Straży Rubieży", "name": "Obóz Straży Rubieży",
        "rooms": (
            ("v016_watch_square", "Plac Wielkich Łowów", "Tablice opisują tropy rare, legendary rare i world bossów."),
            ("v016_watch_hall", "Sala Tropicieli", "Łowcy porównują ślady i raporty z najdalszych rubieży."),
            ("v016_watch_rest", "Ognisko Straży", "Bezpieczne miejsce odpoczynku. Żaden przeciwnik nie atakuje tu automatycznie."),
        ),
    },
}


def v0160_build_settlements():
    for faction_id, data in V016_SETTLEMENTS.items():
        gateway = v0130_gateway_id(data["kind"])
        first, second, third = [row[0] for row in data["rooms"]]
        if gateway not in ROOMS:
            continue
        if data["branch"] not in ROOMS[gateway]["exits"]:
            ROOMS[gateway]["exits"][data["branch"]] = first
        room_rows = data["rooms"]
        ROOMS[first] = {
            "zone": data["zone"], "name": room_rows[0][1], "desc": room_rows[0][2],
            "exits": {data["back"]: gateway, "north": second, "east": third},
            "safe_hub": True, "v016_settlement": faction_id,
        }
        ROOMS[second] = {
            "zone": data["zone"], "name": room_rows[1][1], "desc": room_rows[1][2],
            "exits": {"south": first}, "safe_hub": True, "v016_settlement": faction_id,
        }
        ROOMS[third] = {
            "zone": data["zone"], "name": room_rows[2][1], "desc": room_rows[2][2],
            "exits": {"west": first}, "safe_hub": True, "v016_settlement": faction_id,
        }
        GUIDE_DESTINATION_ALIASES[normalize_lookup_text(data["name"])] = first


v0160_build_settlements()
v0130_refresh_exploration_catalog()

# Stali wysłannicy frakcji w nowych małych osadach.
V016_FACTION_ENVOYS = {
    "cartographers": ("v016_envoy_cartographers", "Miernicza Alena", "v016_cartographers_archive"),
    "waters": ("v016_envoy_waters", "Rybak Orel", "v016_waters_hall"),
    "miners": ("v016_envoy_miners", "Geolog Daren", "v016_miners_hall"),
    "green_path": ("v016_envoy_green", "Zielarka Miva", "v016_green_hall"),
    "frontier_watch": ("v016_envoy_watch", "Herold Rubieży Iren", "v016_watch_hall"),
}
for _fid, (_nid, _name, _room) in V016_FACTION_ENVOYS.items():
    NPCS[_nid] = {
        "name": _name, "room": _room,
        "dialogue": f"Reprezentuję frakcję {V016_FACTIONS[_fid]['name']}. {V016_FACTIONS[_fid]['desc']} Użyj frakcje, aby sprawdzić reputację.",
        "v016_faction": _fid,
    }

# Długi, sześcioczęściowy łańcuch. Każdy etap liczy tylko zdarzenia po przyjęciu,
# bo korzysta z istniejącego trwałego licznika aktywnego questa.
QUESTS.update({
    "v016_frontier_oath_1": {
        "name":"Przysięga Rubieży I: Nowe Szlaki", "giver":"Herold Rubieży Iren",
        "kind":"explore_frontier", "target":"any", "needed":25,
        "description":"Odkryj 25 nowych proceduralnych sektorów po przyjęciu zadania.",
        "reward_silver":8000, "reward_gold":5, "reward_mithril":0,
        "reward_items":{V014_TREASURE_MAP_ITEM:1}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":15,
    },
    "v016_frontier_oath_2": {
        "name":"Przysięga Rubieży II: Żywy Świat", "giver":"Herold Rubieży Iren",
        "kind":"world_event", "target":"any", "needed":4, "requires_quest":"v016_frontier_oath_1",
        "description":"Odwiedź 4 nowe aktywne wydarzenia świata.",
        "reward_silver":11000, "reward_gold":7, "reward_mithril":0,
        "reward_items":{V014_TREASURE_MAP_ITEM:1}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":20,
    },
    "v016_frontier_oath_3": {
        "name":"Przysięga Rubieży III: Znaki Ukryte", "giver":"Herold Rubieży Iren",
        "kind":"discover_secret", "target":"any", "needed":4, "requires_quest":"v016_frontier_oath_2",
        "description":"Odkryj 4 nowe sekrety rubieży.",
        "reward_silver":14000, "reward_gold":9, "reward_mithril":0,
        "reward_items":{V014_TREASURE_MAP_ITEM:2}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":25,
    },
    "v016_frontier_oath_4": {
        "name":"Przysięga Rubieży IV: Małe Głębiny", "giver":"Herold Rubieży Iren",
        "kind":"mini_dungeon", "target":"any", "needed":3, "requires_quest":"v016_frontier_oath_3",
        "description":"Dotrzyj do finału 3 nowych proceduralnych mini-lochów.",
        "reward_silver":18000, "reward_gold":12, "reward_mithril":0,
        "reward_items":{"soul_elixir":2}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":30,
    },
    "v016_frontier_oath_5": {
        "name":"Przysięga Rubieży V: Legendarny Trop", "giver":"Herold Rubieży Iren",
        "kind":"legendary_rare", "target":"any", "needed":2, "requires_quest":"v016_frontier_oath_4",
        "description":"Pokonaj 2 legendary rare. Przeciwnicy są pasywni; gracz sam rozpoczyna walkę.",
        "reward_silver":24000, "reward_gold":16, "reward_mithril":0,
        "reward_items":{"soul_elixir":3}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":40,
    },
    "v016_frontier_oath_6": {
        "name":"Przysięga Rubieży VI: Wielki Łów", "giver":"Herold Rubieży Iren",
        "kind":"world_boss", "target":"any", "needed":1, "requires_quest":"v016_frontier_oath_5",
        "description":"Pokonaj jednego aktywnego world bossa. Boss nie atakuje pierwszy.",
        "reward_silver":35000, "reward_gold":25, "reward_mithril":1,
        "reward_items":{"soul_elixir":5, V014_TREASURE_MAP_ITEM:2}, "repeatable":False,
        "reward_faction_v016":"frontier_watch", "reward_faction_amount_v016":60,
    },
})
NPCS["v016_envoy_watch"]["quest"] = "v016_frontier_oath_1"
NPCS["v016_envoy_watch"]["quest_chain"] = tuple(f"v016_frontier_oath_{i}" for i in range(1,7))

# Wędrujący NPC. Ich trasa jest deterministyczna i zmienia punkt co 15 minut.
V016_TRAVELERS = {
    "v016_traveler_neria": {
        "name":"Kupczyni Neria", "faction":"waters",
        "dialogue":"Podróżuję między Rynkiem, portem i Przystanią Bractwa Wód. Zbieram wieści o połowach i eventach.",
        "route":("market","fish_market","harbor",v0130_gateway_id("coast"),"v016_waters_square"),
    },
    "v016_traveler_toren": {
        "name":"Kartograf Toren", "faction":"cartographers",
        "dialogue":"Porównuję stałe drogi z proceduralnymi rubieżami. Odkryte sektory nie zmieniają układu po restarcie.",
        "route":("library","square","north_gate",v0130_gateway_id("meadow"),"v016_cartographers_square"),
    },
    "v016_traveler_vela": {
        "name":"Wędrowna Zielarka Vela", "faction":"green_path",
        "dialogue":"Szukam roślin na łąkach, w lasach i mokradłach. Nie musisz walczyć z mobami, aby zbierać.",
        "route":("market","forest_edge",v0130_gateway_id("forest"),"v016_green_square",v0130_gateway_id("swamp")),
    },
    "v016_traveler_radan": {
        "name":"Górnik Radan", "faction":"miners",
        "dialogue":"Wędruję za nowymi żyłami. Kamienny Związek ceni regularną pracę, nie jednorazowy grind.",
        "route":("forge",v0130_gateway_id("mountain"),"v016_miners_square",v0130_gateway_id("frozen"),v0130_gateway_id("ash")),
    },
    "v016_traveler_arik": {
        "name":"Tropiciel Arik", "faction":"frontier_watch",
        "dialogue":"Śledzę legendary rare i world bossy. Każdy z nich jest pasywny, dopóki sam nie rozpoczniesz walki.",
        "route":("north_gate",v0130_gateway_id("wild"),"v016_watch_square",v0130_gateway_id("desert"),v0130_gateway_id("void")),
    },
}


def v0160_traveler_room(npc_id, now=None):
    data = V016_TRAVELERS.get(npc_id)
    if not data:
        return None
    now = time.time() if now is None else float(now)
    slot = int(now // V016_TRAVELER_STEP_SECONDS)
    route = tuple(r for r in data["route"] if r in ROOMS)
    if not route:
        return None
    offset = _v0140_hash_int("v016-traveler", npc_id) % len(route)
    return route[(slot + offset) % len(route)]


def v0160_npcs_in_room(room_id, now=None):
    result = {nid: npc for nid, npc in NPCS.items() if npc.get("room") == room_id}
    for npc_id, data in V016_TRAVELERS.items():
        if v0160_traveler_room(npc_id, now) == room_id:
            entry = dict(data)
            entry["room"] = room_id
            entry["v016_traveler"] = True
            result[npc_id] = entry
    return result


# --- Legendary rare i world bossy ---
def _v0160_clone_encounter_template(kind, encounter_type):
    spec = V013_FRONTIER_SPECS.get(kind, {})
    pool = [mid for mid in spec.get("mobs", ()) if mid in MOB_TEMPLATES]
    if not pool:
        return None
    base_id = pool[-1]
    base = MOB_TEMPLATES[base_id]
    if encounter_type == "world_boss":
        tid = f"v016_worldboss_{kind}"
        if tid in MOB_TEMPLATES:
            return tid
        mult_hp, mult_damage, mult_reward = 14.0, 2.25, 10.0
        prefix = f"Władca {spec['zone']}"
    else:
        tid = f"v016_legendary_{kind}"
        if tid in MOB_TEMPLATES:
            return tid
        mult_hp, mult_damage, mult_reward = 3.8, 1.60, 4.0
        prefix = f"Legendarny Trop {spec['zone']}"
    data = dict(base)
    data["drops"] = dict(base.get("drops", {}))
    data["name"] = f"{prefix}: {base['name']}"
    data["max_hp"] = max(1, int(round(int(base.get("max_hp", 1)) * mult_hp)))
    data["damage"] = max(1, int(round(int(base.get("damage", 1)) * mult_damage)))
    data["silver"] = max(1, int(round(int(base.get("silver", 1)) * mult_reward)))
    data["gold"] = max(1, int(base.get("gold", 0)) + (12 if encounter_type == "world_boss" else 4))
    data["mithril"] = int(base.get("mithril", 0)) + (1 if encounter_type == "world_boss" else 0)
    data["soul_reward"] = max(1, int(round(int(base.get("soul_reward", 1)) * mult_reward)))
    data["class_xp_reward"] = max(50, int(round(int(base.get("class_xp_reward", 50)) * mult_reward)))
    data["stat_reward"] = max(1, int(round(int(base.get("stat_reward", 1)) * min(2.5, mult_reward))))
    data["auto_aggro"] = False
    data["v016_biome"] = kind
    if encounter_type == "world_boss":
        data["world_boss"] = True
        data["v016_world_boss"] = True
        data["stationary_mob"] = True
        data["drops"].setdefault("soul_elixir", 0.65)
        data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.80)
        BOSS_COLLECTION_CATALOG[tid] = data["name"]
    else:
        data["rare_mob"] = True
        data["v016_legendary_rare"] = True
        data["rare_base_template"] = base_id
        data.pop("stationary_mob", None)
        data["drops"].setdefault("soul_elixir", 0.35)
        data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.55)
        RARE_MOB_COLLECTION_CATALOG[tid] = data["name"]
    MOB_TEMPLATES[tid] = data
    return tid


for _kind in tuple(V013_FRONTIER_SPECS):
    _v0160_clone_encounter_template(_kind, "legendary_rare")
    _v0160_clone_encounter_template(_kind, "world_boss")


def _v0160_active_encounters(encounter_type, now=None):
    now = time.time() if now is None else float(now)
    if encounter_type == "world_boss":
        seconds, count = V016_WORLD_BOSS_ROTATION_SECONDS, 3
    else:
        seconds, count = V016_LEGENDARY_ROTATION_SECONDS, 5
    slot = int(now // seconds)
    rng = random.Random(_v0140_hash_int("v016-encounter", encounter_type, slot))
    kinds = list(V013_FRONTIER_SPECS)
    rng.shuffle(kinds)
    result = []
    used = set()
    for index, kind in enumerate(kinds[:count]):
        for _ in range(30):
            x = rng.randrange(V013_FRONTIER_SIDE)
            y = rng.randrange(V013_FRONTIER_SIDE)
            room_id = v0130_frontier_room_id(kind, x, y)
            if room_id not in used:
                break
        used.add(room_id)
        tid = _v0160_clone_encounter_template(kind, encounter_type)
        result.append({
            "type": encounter_type, "kind": kind, "x": x, "y": y,
            "room_id": room_id, "template_id": tid, "slot": slot,
            "token": f"{slot}:{encounter_type}:{kind}:{x}:{y}",
            "expires_at": (slot + 1) * seconds,
        })
    return tuple(result)


def v0160_active_world_bosses(now=None):
    return _v0160_active_encounters("world_boss", now)


def v0160_active_legendary_rares(now=None):
    return _v0160_active_encounters("legendary_rare", now)


def v0160_encounters_for_room(room_id, now=None):
    return tuple(
        e for e in (v0160_active_world_bosses(now) + v0160_active_legendary_rares(now))
        if e["room_id"] == room_id
    )


HELP_TOPICS["frakcje_v016"] = [
    "frakcje / factions pokazuje reputację pięciu frakcji świata.",
    "Reputacja rośnie naturalnie przez eksplorację, profesje oraz wielkie łowy. Nie jest wymagana do głównej progresji.",
    "Progi 25/75/150/300 dają tytuły lub jednorazowe drobne nagrody kolekcjonerskie.",
]
HELP_TOPICS["wielkie_lowy_v016"] = [
    "worldbossy pokazuje trzy aktywne world bossy rotujące co 2 godziny.",
    "legendy pokazuje pięć aktywnych legendary rare rotujących co godzinę.",
    "Wszystkie są objęte PASSIVE WORLD: nie rozpoczynają walki automatycznie.",
]
HELP_TOPICS["podroznicy_v016"] = [
    "podroznicy pokazuje aktualne miejsca pięciu wędrujących NPC. Zmieniają punkt trasy co 15 minut.",
    "Wędrowcy poruszają się wyłącznie po bezpiecznej, stałej sieci hubów i granic biomów.",
]
HELP_TOPIC_ALIASES.update({
    "frakcje":"frakcje_v016", "factions":"frakcje_v016", "reputacja frakcji":"frakcje_v016",
    "world bossy":"wielkie_lowy_v016", "worldbossy":"wielkie_lowy_v016", "legendary rare":"wielkie_lowy_v016",
    "podroznicy":"podroznicy_v016", "podróżnicy":"podroznicy_v016", "travelers":"podroznicy_v016",
})
COMMAND_ALIASES.update({
    "frakcje":"factions", "factions":"factions", "fakcje":"factions", "reputacjefrakcji":"factions",
    "worldbossy":"worldbosses", "worldboss":"worldbosses", "worldbosses":"worldbosses",
    "legendy":"legendaryrares", "legendary":"legendaryrares", "legendaryrare":"legendaryrares", "legendaryrares":"legendaryrares",
    "podroznicy":"travelers", "podróżnicy":"travelers", "travelers":"travelers", "wedrowcy":"travelers", "wędrowcy":"travelers",
})


# ============================================================
# v0.17.0 - ARTIFACTS, BIOME SETS, BOSS MECHANICS & FACTION STORIES
# No traps. PASSIVE WORLD remains global.
# ============================================================
V017_ARTIFACTS = {
    "cartographers": {
        "item_id":"v017_artifact_compass", "name":"Kompas Pierwszej Rubieży",
        "effect":"Maksymalne HP/Mana +5%, obrona +3%.",
        "hp":1.05, "damage":1.00, "defense":1.03, "defense_flat":11,
    },
    "waters": {
        "item_id":"v017_artifact_tideheart", "name":"Serce Wiecznego Przypływu",
        "effect":"Maksymalne HP/Mana +7%.",
        "hp":1.07, "damage":1.00, "defense":1.00, "defense_flat":10,
    },
    "miners": {
        "item_id":"v017_artifact_worldstone", "name":"Odłamek Kamienia Świata",
        "effect":"Obrona +7%.",
        "hp":1.00, "damage":1.00, "defense":1.07, "defense_flat":15,
    },
    "green_path": {
        "item_id":"v017_artifact_verdant_seed", "name":"Nasienie Pradawnego Gaju",
        "effect":"Maksymalne HP/Mana +4%, obrona +4%.",
        "hp":1.04, "damage":1.00, "defense":1.04, "defense_flat":12,
    },
    "frontier_watch": {
        "item_id":"v017_artifact_hunter_mark", "name":"Znak Pierwszego Łowcy",
        "effect":"Obrażenia +7%.",
        "hp":1.00, "damage":1.07, "defense":1.00, "defense_flat":12,
    },
}

for _fid, _artifact in V017_ARTIFACTS.items():
    _iid = _artifact["item_id"]
    ITEMS[_iid] = {
        "name": _artifact["name"], "type":"armor", "slot":"charm",
        "defense": int(_artifact["defense_flat"]), "price":None,
        "rarity":"legendary", "rarity_name":"Artefakt", "sockets":3,
        "v017_artifact": _fid,
        "artifact_hp_multiplier": float(_artifact["hp"]),
        "artifact_damage_multiplier": float(_artifact["damage"]),
        "artifact_defense_multiplier": float(_artifact["defense"]),
        "desc": (
            f"Unikalny artefakt frakcji {V016_FACTIONS[_fid]['name']}. "
            f"{_artifact['effect']} Można mieć założony w slocie talizmanu."
        ),
    }
    UNIQUE_ITEM_COLLECTION_CATALOG[_iid] = _artifact["name"]
    EQUIPMENT_COLLECTION_CATALOG[_iid] = _artifact["name"]

# 15 biome-specific six-piece sets. They deliberately reuse the existing regional
# set engine, so all old EQ/set commands continue to work.
V017_BIOME_SET_NAMES = {
    "meadow":"Zestaw Kwitnących Łąk", "forest":"Zestaw Starego Boru",
    "wild":"Zestaw Nieujarzmionej Dziczy", "mountain":"Zestaw Kamiennej Grani",
    "swamp":"Zestaw Czarnego Rozlewiska", "desert":"Zestaw Szklanego Piasku",
    "coast":"Zestaw Sztormowego Wybrzeża", "ocean":"Zestaw Otwartej Toni",
    "river":"Zestaw Rzecznego Nurtu", "lake":"Zestaw Cichego Pojezierza",
    "frozen":"Zestaw Wiecznego Szronu", "ash":"Zestaw Popielnego Żaru",
    "sky":"Zestaw Rozdartego Nieba", "void":"Zestaw Bezgwiezdnej Pustki",
    "crown":"Zestaw Korony Absolutu",
}
V017_BIOME_SET_ITEMS = {}
_v017_slots = (("head","Hełm"),("body","Pancerz"),("hands","Rękawice"),("legs","Nogawice"),("feet","Buty"),("charm","Talizman"))
_v017_affixes = ("strength","dexterity","constitution","intelligence","willpower","charisma")
for _idx, (_kind, _spec) in enumerate(V013_FRONTIER_SPECS.items()):
    _sid = f"v017_{_kind}"
    _endgame = int(_spec.get("base_mastery", 1)) >= 200
    REGIONAL_SET_BONUSES[_sid] = {
        "name": V017_BIOME_SET_NAMES[_kind],
        "hp": 1.08 if _endgame else 1.06,
        "damage": 1.10 if _endgame else 1.08,
        "defense": 1.10 if _endgame else 1.08,
    }
    _ids = []
    _base_def = 7 + min(11, int(_spec.get("base_mastery", 1)) // 35)
    for _slot_index, (_slot, _slot_label) in enumerate(_v017_slots):
        _iid = f"v017_set_{_kind}_{_slot}"
        _affix = _v017_affixes[(_idx + _slot_index) % len(_v017_affixes)]
        _amount = 3 + min(7, int(_spec.get("base_mastery", 1)) // 55)
        ITEMS[_iid] = {
            "name": f"{_slot_label} — {V017_BIOME_SET_NAMES[_kind]}",
            "type":"armor", "slot":_slot,
            "defense": _base_def + _slot_index // 2,
            "price":None, "rarity":"epic", "rarity_name":"Epicki",
            "affix":_affix, "affix_amount":_amount,
            "regional_set":_sid, "v017_biome_set":_kind,
            "desc": (
                f"Część biomowego zestawu {V017_BIOME_SET_NAMES[_kind]}. "
                "Progi 2/4/6 wzmacniają HP/Mana, obrażenia i obronę. "
                "Zdobywana z legendary rare i world bossów odpowiedniego biomu."
            ),
        }
        EQUIPMENT_COLLECTION_CATALOG[_iid] = ITEMS[_iid]["name"]
        _ids.append(_iid)
    V017_BIOME_SET_ITEMS[_kind] = tuple(_ids)

# Existing combat already supports distinct mechanics + 75/50/25% boss phases.
# v0.17 assigns those mechanics to every biome world boss and legendary rare.
V017_BIOME_BOSS_MECHANICS = {
    "meadow":("blood_drain","Drenaż Życia: okresowo wysysa część zadanych obrażeń."),
    "forest":("spectral_shift","Leśna Zmiana: kontrataki przeplatają obrażenia fizyczne i magiczne."),
    "wild":("bone_crush","Miażdżenie: co trzeci kontratak jest znacznie silniejszy."),
    "mountain":("giant_crush","Miażdżenie Giganta: okresowy ciężki kontratak fizyczny."),
    "swamp":("necro_regen","Regeneracja Bagna: boss okresowo odzyskuje część HP."),
    "desert":("ash_curse","Klątwa Pyłu: okresowy magiczny kontratak częściowo ignoruje obronę."),
    "coast":("blood_drain","Drenaż Przypływu: specjalny kontratak leczy przeciwnika."),
    "ocean":("spectral_shift","Zmiana Głębi: typ obrażeń zmienia się między turami."),
    "river":("bone_rage","Furia Nurtu: poniżej połowy HP kontrataki stają się mocniejsze."),
    "lake":("necro_regen","Odnowa Głębin: przeciwnik okresowo regeneruje HP."),
    "frozen":("crystal_lord","Kryształowy Promień i bariera wzmacniają walkę fazową."),
    "ash":("black_flame","Czarny Płomień: silny magiczny kontratak częściowo ignorujący obronę."),
    "sky":("stellar_storm","Gwiezdna Burza: cykliczny silny magiczny kontratak."),
    "void":("astral_sovereign","Faza Suwerena: poniżej połowy HP rośnie siła, a specjalny atak ignoruje część obrony."),
    "crown":("two_hundred_lord","Załamanie Wieczności: wielofazowy endgame'owy profil kontrataków."),
}

for _kind, (_mechanic, _mechanic_text) in V017_BIOME_BOSS_MECHANICS.items():
    _pool = list(V017_BIOME_SET_ITEMS[_kind])
    for _prefix, _enc_type in (("v016_worldboss_","world_boss"),("v016_legendary_","legendary_rare")):
        _tid = _prefix + _kind
        _t = MOB_TEMPLATES.get(_tid)
        if not _t:
            continue
        _t["boss_mechanic"] = _mechanic
        _t["boss_mechanic_text"] = (
            _mechanic_text + " Dodatkowo walka ma fazy przy 75, 50 i 25 procent HP. "
            "PASSIVE WORLD: przeciwnik nie rozpoczyna walki sam."
        )
        _t["auto_aggro"] = False
        _t["v017_boss_phases"] = True
        _t["corpse_equipment_pool"] = _pool
        _t["corpse_equipment_guaranteed"] = max(
            int(_t.get("corpse_equipment_guaranteed", 0) or 0),
            2 if _enc_type == "world_boss" else 1,
        )

# New six-stage faction stories. The old Frontier Oath remains intact and the
# new Straż Rubieży story is appended after it.
V017_FACTION_STORIES = {
    "cartographers": {"biome":"meadow", "title":"Szlak Pierwszych Map"},
    "waters": {"biome":"ocean", "title":"Pieśń Wielkich Wód"},
    "miners": {"biome":"mountain", "title":"Głos Kamienia"},
    "green_path": {"biome":"forest", "title":"Korzenie Zielonego Szlaku"},
    "frontier_watch": {"biome":"wild", "title":"Legenda Straży Rubieży"},
}
V017_FACTION_STORY_QUESTS = {}
_v017_stage_specs = (
    ("I", "Rozpoznanie", "explore_frontier", 15, 12, 7000, 4),
    ("II", "Żywy Znak", "world_event", 2, 15, 9000, 6),
    ("III", "Ukryta Droga", "discover_secret", 2, 18, 12000, 8),
    ("IV", "Głębia Szlaku", "mini_dungeon", 2, 22, 16000, 10),
    ("V", "Legendarny Ślad", "legendary_rare", 1, 28, 22000, 14),
    ("VI", "Próba Mistrza", "world_boss", 1, 40, 32000, 20),
)
for _fid, _story in V017_FACTION_STORIES.items():
    _envoy = V016_FACTION_ENVOYS[_fid][0]
    _prev = None
    _chain = []
    for _stage_no, (_roman, _stage_name, _kind, _needed, _rep, _silver, _gold) in enumerate(_v017_stage_specs, 1):
        _qid = f"v017_{_fid}_{_stage_no}"
        _chain.append(_qid)
        _q = {
            "name":f"{_story['title']} {_roman}: {_stage_name}",
            "giver":V016_FACTION_ENVOYS[_fid][1],
            "kind":_kind, "target":_story["biome"], "needed":_needed,
            "description":(
                f"Etap historii frakcji {V016_FACTIONS[_fid]['name']}. "
                f"Cel dotyczy biomu {V013_FRONTIER_SPECS[_story['biome']]['zone']}. "
                "Postęp liczy wyłącznie zdarzenia po przyjęciu questa."
            ),
            "reward_silver":_silver, "reward_gold":_gold, "reward_mithril":0,
            "reward_items":{}, "repeatable":False,
            "reward_faction_v016":_fid, "reward_faction_amount_v016":_rep,
            "v017_faction_story":_fid,
        }
        if _prev:
            _q["requires_quest"] = _prev
        if _stage_no == 6:
            _q["reward_items"] = {V017_ARTIFACTS[_fid]["item_id"]:1, "soul_elixir":3}
            _q["reward_mithril"] = 1
        elif _stage_no in (3,5):
            _q["reward_items"] = {V014_TREASURE_MAP_ITEM:1}
        QUESTS[_qid] = _q
        _prev = _qid
    V017_FACTION_STORY_QUESTS[_fid] = tuple(_chain)
    _old_chain = tuple(NPCS[_envoy].get("quest_chain", ()))
    NPCS[_envoy]["quest_chain"] = _old_chain + tuple(_chain)
    if not NPCS[_envoy].get("quest"):
        NPCS[_envoy]["quest"] = _chain[0]
    NPCS[_envoy]["dialogue"] += f" Mam też dla ciebie historię: {_story['title']}."

# v0.24.1: finalny pass po WSZYSTKICH definicjach questów.
# Część zadań z późniejszych wersji była dopisywana już po historycznych
# normalizatorach v0.8.66, więc porządkujemy je ponownie globalnie.
normalize_profession_requirements_v0866()
normalize_quest_progress_tracking_v0866()
ensure_profession_quest_currency_v098()

HELP_TOPICS["artefakty_v017"] = [
    "artefakty / artifacts pokazuje 5 unikalnych artefaktów frakcyjnych i ich efekty.",
    "Artefakt otrzymujesz za finał nowej historii danej frakcji. Każdy zajmuje slot talizmanu, więc wybierasz aktywny efekt.",
]
HELP_TOPICS["sety_biomowe_v017"] = [
    "setybiomowe / biomesets pokazuje 15 zestawów biomowych po 6 części.",
    "Legendary rare daje co najmniej 1 część swojego biomu, a world boss co najmniej 2. Progi 2/4/6 wzmacniają HP/Mana, obrażenia i obronę.",
]
HELP_TOPICS["historie_frakcji_v017"] = [
    "historiefrakcji / factionstories pokazuje postęp nowych sześcioczęściowych historii wszystkich 5 frakcji.",
    "Każdy etap zaczyna od 0/x i liczy tylko zdarzenia wykonane po przyjęciu.",
]
HELP_TOPIC_ALIASES.update({
    "artefakty":"artefakty_v017", "artifacts":"artefakty_v017",
    "sety biomowe":"sety_biomowe_v017", "biomesets":"sety_biomowe_v017",
    "historie frakcji":"historie_frakcji_v017", "faction stories":"historie_frakcji_v017",
})
COMMAND_ALIASES.update({
    "artefakty":"artifacts", "artifacts":"artifacts", "artifact":"artifacts",
    "setybiomowe":"biomesets", "biomesets":"biomesets", "biomeset":"biomesets",
    "historiefrakcji":"factionstories", "factionstories":"factionstories", "historiefrakcyjne":"factionstories",
})


# ============================================================
# v0.18.0 - SEASONS, EXPEDITIONS & ENDGAME
# Seasons + archipelagos + transport + great ruins + legendary events
# + first endless endgame layer. NO TRAPS. PASSIVE WORLD remains global.
# ============================================================
V018_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0180-seasons-expeditions-endgame"
V018_SEASON_SECONDS = 6 * 60 * 60
V018_LEGENDARY_EVENT_SECONDS = 4 * 60 * 60
V018_GREAT_RUIN_DENOMINATOR = 48
V018_ENDLESS_POWER_CAP_BAND = 40

V018_SEASONS = (
    ("spring", "Wiosna", "Świat budzi się do życia; zioła i rzeki są szczególnie aktywne."),
    ("summer", "Lato", "Długie dni sprzyjają połowom morskim i pracy w otwartym terenie."),
    ("autumn", "Jesień", "Dojrzałe lasy i zioła dają stabilne warunki zbieractwa."),
    ("winter", "Zima", "Mróz wzmacnia górskie i lodowe wyprawy, ale niczego nie blokuje."),
)


def v0180_season_state(now=None):
    now = time.time() if now is None else float(now)
    slot = int(now // V018_SEASON_SECONDS)
    key, label, desc = V018_SEASONS[slot % len(V018_SEASONS)]
    return {
        "key": key, "label": label, "desc": desc, "slot": slot,
        "expires_at": (slot + 1) * V018_SEASON_SECONDS,
    }


def v0180_season_profession_multiplier(tool_type=None, now=None):
    tool = str(tool_type or "")
    season = v0180_season_state(now)["key"]
    table = {
        "spring": {"herbalism":1.08, "fishing":1.05},
        "summer": {"fishing":1.08, "woodcutting":1.04},
        "autumn": {"woodcutting":1.08, "herbalism":1.05},
        "winter": {"mining":1.08, "fishing":1.03},
    }
    return float(table.get(season, {}).get(tool, 1.0))


# Wrap the mature v0.15 environment system instead of replacing it.
_v0180_environment_bonus_base = v0150_environment_bonus
def v0150_environment_bonus(room_id, tool_type=None, now=None):
    base = dict(_v0180_environment_bonus_base(room_id, tool_type=tool_type, now=now))
    season = v0180_season_state(now)
    mult = v0180_season_profession_multiplier(tool_type, now)
    # Legendary world events may add a small, optional profession bonus.
    levent = v0180_legendary_event_for_room(room_id, now=now) if "v0180_legendary_event_for_room" in globals() else None
    if levent and levent.get("tool") == str(tool_type or ""):
        mult *= float(levent.get("xp_mult", 1.0) or 1.0)
        base["quantity_bonus"] = int(base.get("quantity_bonus", 0) or 0) + int(levent.get("quantity_bonus", 0) or 0)
    base["xp_mult"] = max(1.0, float(base.get("xp_mult", 1.0) or 1.0)) * max(1.0, mult)
    labels = [str(base.get("label", "") or ""), f"Sezon: {season['label']}"]
    if levent and levent.get("tool") == str(tool_type or ""):
        labels.append(f"LEGENDARNE WYDARZENIE — {levent['title']}")
    base["label"] = " + ".join(x for x in labels if x)
    return base


# ------------------------------------------------------------
# Ocean expeditions: five deterministic 4x4 archipelagos.
# ------------------------------------------------------------
V018_EXPEDITIONS = {
    "coral": {"name":"Archipelag Koralowy", "zone":"Archipelag Koralowy", "biome":"ocean", "mastery":120,
              "titles":("Koralowa Laguna","Wyspa Białych Muszli","Rafa Szmaragdowa","Ciepła Zatoka")},
    "storm": {"name":"Archipelag Burz", "zone":"Archipelag Burz", "biome":"coast", "mastery":190,
              "titles":("Wyspa Gromów","Sztormowy Klif","Zatoka Piorunów","Czarna Rafa")},
    "mist": {"name":"Mgliste Wyspy", "zone":"Mgliste Wyspy", "biome":"lake", "mastery":240,
              "titles":("Wyspa Mgieł","Cicha Laguna","Kamienny Przesmyk","Ukryta Zatoka")},
    "frost": {"name":"Archipelag Szronu", "zone":"Archipelag Szronu", "biome":"frozen", "mastery":320,
              "titles":("Lodowa Wyspa","Zamarznięty Brzeg","Błękitna Rafa","Zatoka Szronu")},
    "void": {"name":"Wyspy Czarnego Przypływu", "zone":"Wyspy Czarnego Przypływu", "biome":"void", "mastery":390,
              "titles":("Bezgwiezdna Wyspa","Czarna Laguna","Martwa Rafa","Molo Pustki")},
}
V018_EXPEDITION_SIDE = 4


def v0180_archipelago_room_id(expedition_id, x, y):
    return f"v018_arch_{expedition_id}_{int(x):02d}_{int(y):02d}"


def v0180_archipelago_identity(room_id):
    m = re.fullmatch(r"v018_arch_([a-z]+)_(\d{2})_(\d{2})", str(room_id or ""))
    if not m:
        return None
    eid, sx, sy = m.groups()
    if eid not in V018_EXPEDITIONS:
        return None
    x, y = int(sx), int(sy)
    if not (0 <= x < V018_EXPEDITION_SIDE and 0 <= y < V018_EXPEDITION_SIDE):
        return None
    return eid, x, y


def v0180_archipelago_room_ids(expedition_id):
    return tuple(v0180_archipelago_room_id(expedition_id, x, y)
                 for y in range(V018_EXPEDITION_SIDE) for x in range(V018_EXPEDITION_SIDE))


def v0180_create_archipelago_room_definition(room_id):
    ident = v0180_archipelago_identity(room_id)
    if not ident:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    eid, x, y = ident
    spec = V018_EXPEDITIONS[eid]
    seed = _v0140_hash_int("v018-arch", eid, x, y)
    rng = random.Random(seed)
    exits = {}
    if x > 0: exits["west"] = v0180_archipelago_room_id(eid, x-1, y)
    if x+1 < V018_EXPEDITION_SIDE: exits["east"] = v0180_archipelago_room_id(eid, x+1, y)
    if y > 0: exits["south"] = v0180_archipelago_room_id(eid, x, y-1)
    if y+1 < V018_EXPEDITION_SIDE: exits["north"] = v0180_archipelago_room_id(eid, x, y+1)
    if x == 0 and y == 0:
        exits["down"] = "harbor"
    title = rng.choice(spec["titles"])
    ROOMS[room_id] = {
        "zone":spec["zone"], "name":f"{title} — sektor {x+1}-{y+1}",
        "desc":(
            f"Sektor ekspedycji na {spec['name']}. Wyspy są generowane z trwałego seedu; "
            "po restarcie zachowują układ. Powrót do Portu Dusz prowadzi z pierwszego sektora w dół."
        ),
        "exits":exits, "recommended_mastery":int(spec["mastery"]),
        "generated_on_demand":True, "v018_archipelago":eid,
        "v018_arch_x":x, "v018_arch_y":y,
    }
    # Island gathering ecology: marine fishing everywhere; some later islands also support herbs/mining.
    FISHING_ROOMS.add(room_id); MARINE_FISHING_ROOMS.add(room_id); OCEAN_FISHING_ROOMS.add(room_id)
    FISHING_WATER_TYPE_OVERRIDES[room_id] = spec["name"]
    if eid in ("coral","mist") and (x+y)%2 == 0:
        HERBALISM_ROOMS.add(room_id)
    # v0.25.1: ekspedycje nie są już alternatywnymi kopalniami.
    base_kind = spec["biome"]
    pool = [t for t in V013_FRONTIER_SPECS[base_kind].get("mobs",()) if t in MOB_TEMPLATES]
    spawns = []
    if pool:
        for _ in range(1 + (1 if rng.random() < 0.45 else 0)):
            spawns.append((room_id, rng.choice(pool)))
    return room_id, tuple(spawns)


# ------------------------------------------------------------
# Great procedural ruins: rarer than mini-dungeons, 20-40 rooms.
# ------------------------------------------------------------
def v0180_has_great_ruin(kind, x, y):
    if kind not in V013_FRONTIER_SPECS:
        return False
    return _v0140_hash_int("v018-great-ruin", kind, int(x), int(y)) % V018_GREAT_RUIN_DENOMINATOR == 0


def v0180_ruin_size(kind, x, y):
    return 20 + (_v0140_hash_int("v018-ruin-size", kind, int(x), int(y)) % 21)


def v0180_ruin_room_id(kind, x, y, index):
    return f"v018_ruin_{kind}_{int(x):02d}_{int(y):02d}_{int(index):02d}"


def v0180_ruin_identity(room_id):
    m = re.fullmatch(r"v018_ruin_([a-z]+)_(\d{2})_(\d{2})_(\d{2})", str(room_id or ""))
    if not m:
        return None
    kind, sx, sy, si = m.groups()
    if kind not in V013_FRONTIER_SPECS:
        return None
    x,y,index = int(sx),int(sy),int(si)
    if not (0 <= x < V013_FRONTIER_SIDE and 0 <= y < V013_FRONTIER_SIDE):
        return None
    size = v0180_ruin_size(kind,x,y)
    if not v0180_has_great_ruin(kind,x,y) or not (1 <= index <= size):
        return None
    return kind,x,y,index,size


V018_RUIN_GUARDIANS = {}
for _kind, _spec in V013_FRONTIER_SPECS.items():
    _base = MOB_TEMPLATES.get(f"v016_legendary_{_kind}")
    if not _base:
        continue
    _tid = f"v018_ruin_guardian_{_kind}"
    _data = dict(_base)
    _data["drops"] = dict(_base.get("drops",{}))
    _data["name"] = f"Strażnik Wielkich Ruin: {_base['name']}"
    _data["max_hp"] = max(1, int(int(_base.get("max_hp",1))*1.45))
    _data["damage"] = max(1, int(int(_base.get("damage",1))*1.18))
    _data["soul_reward"] = max(1, int(int(_base.get("soul_reward",1))*1.35))
    _data["class_xp_reward"] = max(1, int(int(_base.get("class_xp_reward",1))*1.30))
    _data["world_boss"] = True; _data["mini_boss"] = True
    _data["stationary_mob"] = True; _data["auto_aggro"] = False
    _data["v018_great_ruin_guardian"] = True; _data["v018_biome"] = _kind
    MOB_TEMPLATES[_tid] = _data
    V018_RUIN_GUARDIANS[_kind] = _tid


def v0180_create_ruin_room_definition(room_id):
    ident = v0180_ruin_identity(room_id)
    if not ident:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind,x,y,index,size = ident
    seed = _v0140_hash_int("v018-ruin-room",kind,x,y,index)
    rng = random.Random(seed)
    exits = {}
    if index > 1: exits["west"] = v0180_ruin_room_id(kind,x,y,index-1)
    if index < size: exits["east"] = v0180_ruin_room_id(kind,x,y,index+1)
    # deterministic cross-links create loops and alternative paths, never traps.
    if index % 4 == 1 and index + 4 <= size:
        exits["north"] = v0180_ruin_room_id(kind,x,y,index+4)
    if index >= 5 and (index-4) % 4 == 1:
        exits["south"] = v0180_ruin_room_id(kind,x,y,index-4)
    if index == 1:
        exits["down"] = v0130_frontier_room_id(kind,x,y)
    final = index == size
    zone = f"Wielkie Ruiny — {V013_FRONTIER_SPECS[kind]['zone']}"
    names = ("Galeria Run","Zawalona Nawa","Sala Kolumn","Kamienny Dziedziniec","Archiwum Ruin","Korytarz Posągów")
    ROOMS[room_id] = {
        "zone":zone, "name":f"{rng.choice(names)} {index}/{size}",
        "desc":(
            "Rozległy fragment proceduralnych ruin. Układ jest deterministyczny, ma pętle i alternatywne przejścia. "
            + ("To finałowa komnata strażnika. " if final else "")
            + "Nie ma tu pułapek ani automatycznych obrażeń wejściowych."
        ),
        "exits":exits, "recommended_mastery":min(400, int(V013_FRONTIER_SPECS[kind].get("base_mastery",1))+40),
        "generated_on_demand":True, "v018_great_ruin":True, "v018_ruin_final":final,
        "v018_biome":kind, "v018_ruin_parent":v0130_frontier_room_id(kind,x,y),
    }
    spawns=[]
    pool=[t for t in V013_FRONTIER_SPECS[kind].get("mobs",()) if t in MOB_TEMPLATES]
    if final and kind in V018_RUIN_GUARDIANS:
        spawns.append((room_id,V018_RUIN_GUARDIANS[kind]))
    elif pool and rng.random() < 0.82:
        spawns.append((room_id,rng.choice(pool)))
        if rng.random() < 0.33: spawns.append((room_id,rng.choice(pool)))
    return room_id, tuple(spawns)


def v0180_all_great_ruins():
    result=[]
    for kind in V013_FRONTIER_SPECS:
        for y in range(V013_FRONTIER_SIDE):
            for x in range(V013_FRONTIER_SIDE):
                if v0180_has_great_ruin(kind,x,y):
                    result.append((kind,x,y,v0180_ruin_size(kind,x,y)))
    return tuple(result)


# ------------------------------------------------------------
# Legendary World Events: two major events every 4 hours.
# ------------------------------------------------------------
V018_LEGENDARY_EVENT_DEFS = {
    "titan_awakening":{"title":"Przebudzenie Tytana","kinds":tuple(V013_FRONTIER_SPECS),"tool":None,"desc":"W sektorze pojawił się potężny pasywny Tytan. Gracz sam decyduje o walce."},
    "great_bloom":{"title":"Wielki Rozkwit","kinds":("meadow","forest","swamp","river"),"tool":"herbalism","xp_mult":1.18,"quantity_bonus":1,"desc":"Rzadki rozkwit wzmacnia Zielarstwo w tym sektorze."},
    "ocean_convergence":{"title":"Zbieg Wielkich Prądów","kinds":("coast","ocean","river","lake","void"),"tool":"fishing","xp_mult":1.18,"quantity_bonus":1,"desc":"Wody zbiegają się w wyjątkową ławicę."},
    "deep_vein":{"title":"Przebudzenie Głębokiej Żyły","kinds":("mountain","desert","frozen","ash","sky","crown"),"tool":"mining","xp_mult":1.18,"quantity_bonus":1,"desc":"Głęboka żyła minerału odsłoniła się na krótki czas."},
    "ancient_growth":{"title":"Pradawny Rozrost","kinds":("forest","wild","meadow"),"tool":"woodcutting","xp_mult":1.18,"quantity_bonus":1,"desc":"Stare drzewa przechodzą niezwykły okres wzrostu."},
}


def v0180_legendary_event_slot(now=None):
    now=time.time() if now is None else float(now)
    return int(now//V018_LEGENDARY_EVENT_SECONDS)


def v0180_active_legendary_events(now=None):
    now=time.time() if now is None else float(now)
    slot=v0180_legendary_event_slot(now)
    keys=tuple(V018_LEGENDARY_EVENT_DEFS)
    picked=[]; used=set()
    for n in range(2):
        etype=keys[_v0140_hash_int("v018-legend-event-type",slot,n)%len(keys)]
        # ensure distinct type when possible
        if etype in used:
            etype=keys[(keys.index(etype)+1)%len(keys)]
        used.add(etype)
        d=V018_LEGENDARY_EVENT_DEFS[etype]
        kinds=tuple(d["kinds"])
        kind=kinds[_v0140_hash_int("v018-legend-event-kind",slot,n)%len(kinds)]
        x=_v0140_hash_int("v018-legend-event-x",slot,n)%V013_FRONTIER_SIDE
        y=_v0140_hash_int("v018-legend-event-y",slot,n)%V013_FRONTIER_SIDE
        room_id=v0130_frontier_room_id(kind,x,y)
        picked.append({
            "type":etype,"title":d["title"],"desc":d["desc"],"kind":kind,"x":x,"y":y,"room_id":room_id,
            "tool":d.get("tool"),"xp_mult":float(d.get("xp_mult",1.0)),"quantity_bonus":int(d.get("quantity_bonus",0)),
            "slot":slot,"token":f"{slot}:{etype}:{kind}:{x}:{y}","expires_at":(slot+1)*V018_LEGENDARY_EVENT_SECONDS,
        })
    return tuple(picked)


def v0180_legendary_event_for_room(room_id, now=None):
    return next((e for e in v0180_active_legendary_events(now) if e["room_id"]==room_id),None)


# Passive Titan templates reuse the proven v0.16/v0.17 world-boss profiles.
V018_TITAN_TEMPLATES={}
for _kind in V013_FRONTIER_SPECS:
    _base=MOB_TEMPLATES.get(f"v016_worldboss_{_kind}")
    if not _base: continue
    _tid=f"v018_titan_{_kind}"
    _data=dict(_base); _data["drops"]=dict(_base.get("drops",{}))
    _data["name"]=f"Przebudzony Tytan: {_base['name']}"
    _data["max_hp"]=max(1,int(int(_base.get("max_hp",1))*1.60))
    _data["damage"]=max(1,int(int(_base.get("damage",1))*1.22))
    _data["soul_reward"]=max(1,int(int(_base.get("soul_reward",1))*1.50))
    _data["auto_aggro"]=False; _data["stationary_mob"]=True; _data["world_boss"]=True
    _data["v018_legendary_event_boss"]=True; _data["v018_biome"]=_kind
    MOB_TEMPLATES[_tid]=_data; V018_TITAN_TEMPLATES[_kind]=_tid


# ------------------------------------------------------------
# Endless Frontier: infinite mapping with bounded combat scaling.
# ------------------------------------------------------------
V018_ENDLESS_GATE="v018_endless_gate"
V018_ENDLESS_ZONE="Rubież Końca"


def v0180_endless_room_id(depth):
    return f"v018_endless_{max(1,int(depth)):08d}"


def v0180_endless_identity(room_id):
    m=re.fullmatch(r"v018_endless_(\d{8})",str(room_id or ""))
    if not m: return None
    depth=int(m.group(1))
    return depth if depth>=1 else None


def v0180_endless_band(depth):
    return min(V018_ENDLESS_POWER_CAP_BAND, 1 + (max(1,int(depth))-1)//25)


def v0180_endless_template(depth):
    band=v0180_endless_band(depth)
    tid=f"v018_endless_echo_b{band:02d}"
    if tid in MOB_TEMPLATES: return tid
    base_pool=[t for t in V013_FRONTIER_SPECS["crown"].get("mobs",()) if t in MOB_TEMPLATES]
    base_id=base_pool[(band-1)%len(base_pool)] if base_pool else "crown_sentinel"
    base=MOB_TEMPLATES[base_id]
    data=dict(base); data["drops"]=dict(base.get("drops",{}))
    mult=1.0 + min(3.0,(band-1)*0.075)
    data["name"]=f"Echo Rubieży Końca {band}: {base['name']}"
    data["max_hp"]=max(1,int(int(base.get("max_hp",1))*mult))
    data["damage"]=max(1,int(int(base.get("damage",1))*(1.0+min(1.5,(band-1)*0.04))))
    data["soul_reward"]=max(1,int(int(base.get("soul_reward",1))*(1.0+min(2.0,(band-1)*0.06))))
    data["auto_aggro"]=False; data["v018_endless"]=True; data["v018_endless_band"]=band
    MOB_TEMPLATES[tid]=data
    return tid


def v0180_create_endless_room_definition(room_id):
    depth=v0180_endless_identity(room_id)
    if depth is None: return None,()
    if room_id in ROOMS: return room_id,()
    seed=_v0140_hash_int("v018-endless",depth)
    rng=random.Random(seed)
    names=("Galeria Końca","Pusty Horyzont","Kamienny Bezmiar","Taras Echa","Droga Poza Koroną","Milcząca Rubież")
    exits={"north":v0180_endless_room_id(depth+1)}
    exits["south"]=V018_ENDLESS_GATE if depth==1 else v0180_endless_room_id(depth-1)
    ROOMS[room_id]={
        "zone":V018_ENDLESS_ZONE,"name":f"{rng.choice(names)} — sektor {depth}",
        "desc":(
            "Pierwsza warstwa endless endgame. Mapa nie ma sztywnego końca i powstaje przy wejściu, "
            "ale siła przeciwników ma twardy bezpieczny cap, aby progresja 1-400 nie została unieważniona. "
            "Brak pułapek i automatycznego aggro."
        ),
        "exits":exits,"recommended_mastery":400,"generated_on_demand":True,
        "v018_endless":True,"v018_endless_depth":depth,"v018_endless_band":v0180_endless_band(depth),
    }
    # v0.25.1: Endless nie jest miejscem Górnictwa.
    spawns=[(room_id,v0180_endless_template(depth))]
    if rng.random()<0.35: spawns.append((room_id,v0180_endless_template(depth)))
    return room_id,tuple(spawns)


# Static gate branches from the Crown procedural gateway without replacing its old exits.
if v0130_gateway_id("crown") in ROOMS:
    _gw=v0130_gateway_id("crown")
    if "north" not in ROOMS[_gw].setdefault("exits",{}):
        ROOMS[_gw]["exits"]["north"]=V018_ENDLESS_GATE
    ROOMS[V018_ENDLESS_GATE]={
        "zone":V018_ENDLESS_ZONE,"name":"Brama Rubieży Końca",
        "desc":"Stała brama do pierwszej nieskończonej warstwy endgame. Dalej sektory są generowane na żądanie i nigdy nie auto-aggro.",
        "exits":{"south":_gw,"north":v0180_endless_room_id(1)},"safe_hub":True,
    }
    GUIDE_DESTINATION_ALIASES["rubiez konca"]=V018_ENDLESS_GATE
    GUIDE_DESTINATION_ALIASES["rubież końca"]=V018_ENDLESS_GATE

# The new fixed Endless gate is part of the static exploration catalog.
v0130_refresh_exploration_catalog()

# Transport network: only discovered destinations are usable.
V018_TRANSPORT_HUBS = {
    "miasto":"market", "port":"harbor", "swiatynia":"temple",
    "kartografowie":"v016_cartographers_square", "wody":"v016_waters_square",
    "gornicy":"v016_miners_square", "zielony":"v016_green_square", "straz":"v016_watch_square",
    "koniec":V018_ENDLESS_GATE,
}
V018_TRANSPORT_ORIGINS = frozenset(V018_TRANSPORT_HUBS.values())


HELP_TOPICS["sezony_v018"]=[
    "sezon / season pokazuje aktualny sezon. Pełny cykl ma Wiosnę, Lato, Jesień i Zimę; każdy sezon trwa 6 godzin.",
    "Sezony dają tylko małe bonusy ekologiczne. Nigdy nie blokują questów, profesji, ryb, ziół ani dostępu do regionów.",
]
HELP_TOPICS["ekspedycje_v018"]=[
    "ekspedycje / expeditions pokazuje 5 archipelagów. ekspedycja <nazwa> wypływa z Portu Dusz lub Przystani Bractwa Wód.",
    "Każdy archipelag ma 16 proceduralnych sektorów 4x4, własną trudność i zasoby. Powrót jest zawsze dostępny z pierwszego sektora.",
]
HELP_TOPICS["ruiny_v018"]=[
    "wielkieruiny / greatruins pokazuje liczbę wielkich proceduralnych ruin. Każda ma 20-40 pokoi, pętle, alternatywne przejścia i finałowego pasywnego strażnika.",
    "Wielkie ruiny nie mają pułapek ani automatycznych obrażeń wejściowych.",
]
HELP_TOPICS["legend_event_v018"]=[
    "legendarnewydarzenia / legendaryevents pokazuje 2 duże wydarzenia świata rotujące co 4 godziny.",
    "Wydarzenia profesyjne dają mały bonus tylko właściwej profesji; Przebudzenie Tytana dodaje pasywnego world bossa.",
]
HELP_TOPICS["endless_v018"]=[
    "rubiezkonca / endless pokazuje informacje o Rubieży Końca. Mapa generuje sektory bez sztywnego końca.",
    "Skalowanie przeciwników jest ograniczone twardym capem, więc system 1-400 pozostaje ważny. PASSIVE WORLD obowiązuje wszędzie.",
]
HELP_TOPIC_ALIASES.update({
    "sezony":"sezony_v018","sezon":"sezony_v018","seasons":"sezony_v018",
    "ekspedycje":"ekspedycje_v018","expeditions":"ekspedycje_v018",
    "wielkie ruiny":"ruiny_v018","great ruins":"ruiny_v018",
    "legendarne wydarzenia":"legend_event_v018","legendary events":"legend_event_v018",
    "rubiez konca":"endless_v018","rubież końca":"endless_v018","endless":"endless_v018",
})
COMMAND_ALIASES.update({
    "sezon":"season","season":"season","seasons":"season",
    "ekspedycje":"expeditions","expeditions":"expeditions",
    "ekspedycja":"expedition","expedition":"expedition",
    "transport":"transport","podroz":"transport","podróż":"transport","fasttravel":"transport",
    "wielkieruiny":"greatruins","greatruins":"greatruins",
    "legendarnewydarzenia":"legendaryevents","legendaryevents":"legendaryevents",
    "rubiezkonca":"endless","rubieżkońca":"endless","endless":"endless",
})

HELP_TOPICS["generator_v019"]=[
    "v0.19.0 używa jednego Global Progression & Reward Generator dla całej gry.",
    "Początek pozostaje w setkach EXP, a później nagrody rosną do tysięcy, milionów, miliardów i bilionów.",
    "Wymagany EXP rośnie mocniej co kolejne progi; duża nagroda nie jest ukrycie obcinana procentowym capem.",
    "Krypta około piętra 20 celuje w około 10000 Class XP za zwykłego moba i około 250000 za bossa, zanim zadziałają dodatnie bonusy.",
    "Generator obejmuje staty, Biegłość, Soul Level, Skill Level, profesje, narzędzia, nagrody mobów/questów, trudność HP/damage oraz główne koszty ekonomii.",
    "Nowa postać nadal zaczyna dokładnie z 2 złota i 30 srebra; wielkie wartości ekonomii pojawiają się dopiero wraz z postępem.",
]
HELP_TOPIC_ALIASES.update({"generator":"generator_v019","balans 019":"generator_v019","progression generator":"generator_v019"})


# ============================================================
# v0.20.0 - ENDGAME CHALLENGES & MEGADUNGEONS
# Megalochy 100-300 pokoi, boss gauntlets, mythic world bosses,
# trwały rozwój artefaktów i długoterminowe cele. NO TRAPS.
# Całość korzysta z Global Progression & Reward Generator v0.19.
# ============================================================
V020_WORLD_SEED = f"{V0250_WORLD_SEED}:soulbound-v0200-endgame-challenges-megadungeons"
V020_MYTHIC_WORLD_BOSS_SECONDS = 6 * 60 * 60
V020_MEGA_BOSS_STEP = 25

V020_MEGADUNGEONS = {
    "echo": {"name":"Katedra Tysiąca Ech", "faction":"cartographers", "biome":"crown", "size":120, "stage":220},
    "abyss": {"name":"Archiwum Otchłani", "faction":"waters", "biome":"ocean", "size":160, "stage":260},
    "forge": {"name":"Kuźnia Pierwszych Tytanów", "faction":"miners", "biome":"mountain", "size":200, "stage":300},
    "verdant": {"name":"Labirynt Wiecznych Korzeni", "faction":"green_path", "biome":"forest", "size":240, "stage":340},
    "null": {"name":"Pałac Bezimiennej Korony", "faction":"frontier_watch", "biome":"void", "size":280, "stage":380},
}

V020_MEGADUNGEON_HOST_ROOMS = {
    "echo":"v016_cartographers_archive",
    "abyss":"v016_waters_hall",
    "forge":"v016_miners_hall",
    "verdant":"v016_green_hall",
    "null":"v016_watch_hall",
}

V020_ENDGAME_MATERIALS = {
    "v020_ancient_core": ("Rdzeń Megalochu", "Skondensowany rdzeń zdobywany z bossów megalochów."),
    "v020_gauntlet_seal": ("Pieczęć Próby", "Pieczęć zdobywana za finałowe rundy boss gauntletów."),
    "v020_mythic_essence": ("Esencja Mitycznego Bossa", "Esencja pozostawiana przez mityczne world bossy."),
}
for _iid, (_name, _desc) in V020_ENDGAME_MATERIALS.items():
    ITEMS[_iid] = {"name":_name, "type":"material", "price":None, "rarity":"mythic", "rarity_name":"Mityczny", "desc":_desc}
    UNIQUE_ITEM_COLLECTION_CATALOG.setdefault(_iid, _name)


def v0200_mega_gate_id(key):
    return f"v020_mega_{key}_gate"


def v0200_mega_room_id(key, index):
    return f"v020_mega_{key}_{int(index)}"


def v0200_mega_identity(room_id):
    m = re.fullmatch(r"v020_mega_([a-z]+)_(\d+)", str(room_id or ""))
    if not m or m.group(1) not in V020_MEGADUNGEONS:
        return None
    index=int(m.group(2)); size=int(V020_MEGADUNGEONS[m.group(1)]["size"])
    if not 1 <= index <= size:
        return None
    return m.group(1), index


def v0200_mega_stage(key, index):
    spec=V020_MEGADUNGEONS[key]; size=max(2,int(spec["size"])); base=int(spec["stage"])
    # W obrębie jednego megalochu trudność powoli rośnie, ale zawsze pozostaje
    # w zakresie generatora 1-400.
    return max(1,min(400,int(round(base + (400-base)*((index-1)/(size-1))*0.72))))


def v0200_mega_is_boss_index(key, index):
    size=int(V020_MEGADUNGEONS[key]["size"])
    return index == size or (index % V020_MEGA_BOSS_STEP == 0)


def v0200_mega_neighbors(key, index):
    size=int(V020_MEGADUNGEONS[key]["size"]); exits={}
    if index == 1:
        exits["up"] = v0200_mega_gate_id(key)
    else:
        exits["south"] = v0200_mega_room_id(key,index-1)
    if index < size:
        exits["north"] = v0200_mega_room_id(key,index+1)
    # Deterministyczne skróty tworzą prawdziwe pętle, ale nie omijają boss gate'u
    # na końcu sekcji 25-pokojowej.
    if index % 13 == 1 and index+8 <= size and (index//25)==((index+8)//25):
        exits["east"] = v0200_mega_room_id(key,index+8)
    if index > 8 and (index-8) % 13 == 1 and ((index-8)//25)==(index//25):
        exits["west"] = v0200_mega_room_id(key,index-8)
    return exits


def v0200_mega_template(key, index, boss=False):
    stage=v0200_mega_stage(key,index); spec=V020_MEGADUNGEONS[key]; biome=spec["biome"]
    tid=f"v020_mega_{key}_{'boss' if boss else 'mob'}_{index if boss else stage}"
    if tid in MOB_TEMPLATES:
        return tid
    if boss:
        mechanic, mechanic_text = V017_BIOME_BOSS_MECHANICS.get(biome,("two_hundred_lord","Wielofazowy profil bossa."))
        pool=list((globals().get("V021_MYTHIC_SET_ITEMS",{}).get(key) or V017_BIOME_SET_ITEMS.get(biome,())))
        MOB_TEMPLATES[tid]={
            "name":f"Strażnik {spec['name']} — próg {index}",
            "max_hp":1,"damage":1,"damage_type":"magic" if biome in ("void","crown","ocean") else "physical",
            "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,
            "drops":{"v020_ancient_core":1.0,"v021_ascension_crystal":0.45,"soul_elixir":0.55},
            "auto_aggro":False,"stationary_mob":True,"boss_mechanic":mechanic,
            "boss_mechanic_text":mechanic_text+" Fazy 75/50/25%. PASSIVE WORLD.",
            "v017_boss_phases":True,"v020_megadungeon_boss":True,"v020_mega_key":key,"v020_mega_index":index,
            "v019_stage":stage,"corpse_equipment_pool":pool,"corpse_equipment_guaranteed":min(2 if index==int(spec["size"]) else 1,len(pool)),
            "respawn_seconds":6*60*60,
        }
        BOSS_COLLECTION_CATALOG[tid]=MOB_TEMPLATES[tid]["name"]
    else:
        names=("Strażnik Korytarza","Wędrowiec Głębi","Opiekun Pieczęci","Echo Dawnej Straży","Bestia Megalochu")
        rng=random.Random(_v0140_hash_int(V020_WORLD_SEED,key,stage))
        MOB_TEMPLATES[tid]={
            "name":f"{rng.choice(names)} — {spec['name']}","max_hp":1,"damage":1,
            "damage_type":"magic" if rng.random()<0.38 else "physical",
            "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,
            "drops":{"soul_shard":0.10},"auto_aggro":False,"v020_megadungeon":True,"v020_mega_key":key,"v019_stage":stage,
        }
    v0190_apply_combat_template(MOB_TEMPLATES[tid])
    return tid


def v0200_create_mega_room_definition(room_id):
    ident=v0200_mega_identity(room_id)
    if not ident: return None,()
    if room_id in ROOMS: return room_id,()
    key,index=ident; spec=V020_MEGADUNGEONS[key]; stage=v0200_mega_stage(key,index)
    rng=random.Random(_v0140_hash_int(V020_WORLD_SEED,key,index))
    labels=("Galeria","Komnata","Korytarz","Sanktuarium","Sala","Krużganek","Archiwum","Przejście")
    ROOMS[room_id]={
        "zone":spec["name"],"name":f"{rng.choice(labels)} — {index} z {spec['size']}",
        "desc":(
            f"Część megalochu {spec['name']}. Kompleks ma {spec['size']} pokoi i jest generowany na żądanie. "
            "Ma pętle i alternatywne drogi, ale boss progu blokuje wyłącznie przejście do następnej sekcji. "
            "Brak pułapek i auto-aggro."
        ),
        "exits":v0200_mega_neighbors(key,index),"recommended_mastery":stage,"generated_on_demand":True,
        "v020_megadungeon":key,"v020_mega_index":index,
    }
    spawns=[]
    if v0200_mega_is_boss_index(key,index):
        spawns.append((room_id,v0200_mega_template(key,index,boss=True)))
    else:
        count=1 + (1 if rng.random()<0.52 else 0) + (1 if stage>=330 and rng.random()<0.30 else 0)
        for _ in range(count): spawns.append((room_id,v0200_mega_template(key,index,boss=False)))
    return room_id,tuple(spawns)


# Stałe bramy megalochów. Same wnętrza są lazy-generated.
for _key,_spec in V020_MEGADUNGEONS.items():
    _host=V020_MEGADUNGEON_HOST_ROOMS[_key]; _gate=v0200_mega_gate_id(_key)
    ROOMS[_gate]={"zone":_spec["name"],"name":f"Brama: {_spec['name']}",
        "desc":f"Stałe wejście do megalochu {_spec['name']} ({_spec['size']} pokoi). Wnętrze generuje się dopiero przy wejściu.",
        "exits":{"up":_host,"down":v0200_mega_room_id(_key,1)},"safe_hub":True,"v020_mega_gate":_key}
    if _host in ROOMS and "down" not in ROOMS[_host].setdefault("exits",{}): ROOMS[_host]["exits"]["down"]=_gate
    GUIDE_DESTINATION_ALIASES[normalize_lookup_text(_spec["name"])]=_gate


# -------------------- BOSS GAUNTLETS --------------------
V020_GAUNTLETS={
    "stalowa":{"name":"Stalowa Próba","stages":(140,160,180,200,220)},
    "mityczna":{"name":"Mityczna Próba","stages":(240,260,280,300,320)},
    "astralna":{"name":"Astralna Próba","stages":(300,325,350,375,400)},
    "wieczna":{"name":"Wieczna Próba","stages":(360,370,380,390,400)},
}
V020_GAUNTLET_LOBBY="v020_gauntlet_lobby"
ROOMS[V020_GAUNTLET_LOBBY]={"zone":"Arena Prób","name":"Sala Boss Gauntletów","desc":"Bezpieczny hol czterech wieloetapowych prób bossów. Żaden boss nie atakuje pierwszy.","exits":{"west":"v016_watch_hall","north":"v020_gauntlet_stalowa_1","east":"v020_gauntlet_mityczna_1","up":"v020_gauntlet_astralna_1","down":"v020_gauntlet_wieczna_1"},"safe_hub":True}
if "v016_watch_hall" in ROOMS and "east" not in ROOMS["v016_watch_hall"].setdefault("exits",{}): ROOMS["v016_watch_hall"]["exits"]["east"]=V020_GAUNTLET_LOBBY

for _gkey,_gdata in V020_GAUNTLETS.items():
    for _round,_stage in enumerate(_gdata["stages"],1):
        _rid=f"v020_gauntlet_{_gkey}_{_round}"
        _prev=V020_GAUNTLET_LOBBY if _round==1 else f"v020_gauntlet_{_gkey}_{_round-1}"
        _next=V020_GAUNTLET_LOBBY if _round==5 else f"v020_gauntlet_{_gkey}_{_round+1}"
        ROOMS[_rid]={"zone":_gdata["name"],"name":f"{_gdata['name']} — runda {_round}/5",
            "desc":"Arena pojedynczego bossa. Wyjście naprzód otwiera się po pokonaniu aktywnego bossa. PASSIVE WORLD; brak pułapek.",
            "exits":{"south":_prev,"north":_next},"recommended_mastery":_stage,"v020_gauntlet":_gkey,"v020_gauntlet_round":_round}
        _tid=f"v020_gauntlet_boss_{_gkey}_{_round}"
        _mechanic=list(V017_BIOME_BOSS_MECHANICS.values())[(_round+list(V020_GAUNTLETS).index(_gkey)*3)%len(V017_BIOME_BOSS_MECHANICS)][0]
        MOB_TEMPLATES[_tid]={"name":f"{_gdata['name']} — Boss Rundy {_round}","max_hp":1,"damage":1,"damage_type":"physical" if _round%2 else "magic",
            "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,"drops":({"v020_gauntlet_seal":1.0} if _round==5 else {"soul_elixir":0.25}),
            "auto_aggro":False,"stationary_mob":True,"boss_mechanic":_mechanic,"v017_boss_phases":True,
            "v020_gauntlet":_gkey,"v020_gauntlet_round":_round,"v019_stage":_stage,"respawn_seconds":6*60*60}
        v0190_apply_combat_template(MOB_TEMPLATES[_tid]); BOSS_COLLECTION_CATALOG[_tid]=MOB_TEMPLATES[_tid]["name"]
        MOB_SPAWNS.append((_rid,_tid))


# -------------------- MYTHIC WORLD BOSSES --------------------
def v0200_mythic_template(kind):
    tid=f"v020_mythic_worldboss_{kind}"
    if tid in MOB_TEMPLATES: return tid
    spec=V013_FRONTIER_SPECS[kind]; biome=kind
    stage=max(250,min(400,int(spec.get("base_mastery",1))+140))
    mechanic, text=V017_BIOME_BOSS_MECHANICS.get(kind,("two_hundred_lord","Wielofazowa mechanika."))
    pool=list(V017_BIOME_SET_ITEMS.get(kind,()))
    MOB_TEMPLATES[tid]={"name":f"Mityczny Władca — {spec['zone']}","max_hp":1,"damage":1,"damage_type":"magic" if kind in ("void","sky","crown","ocean") else "physical",
        "silver":0,"gold":0,"mithril":0,"stat_reward":1,"soul_reward":1,"class_xp_reward":1,
        "drops":{"v020_mythic_essence":1.0,"v020_ancient_core":0.65,"soul_elixir":0.80},"world_boss":True,"v020_mythic_world_boss":True,"v020_biome":kind,
        "auto_aggro":False,"stationary_mob":True,"boss_mechanic":mechanic,"boss_mechanic_text":text+" Mityczny world boss; fazy 75/50/25%. PASSIVE WORLD.",
        "v017_boss_phases":True,"v019_stage":stage,"corpse_equipment_pool":pool,"corpse_equipment_guaranteed":min(4,len(pool))}
    v0190_apply_combat_template(MOB_TEMPLATES[tid]); BOSS_COLLECTION_CATALOG[tid]=MOB_TEMPLATES[tid]["name"]
    return tid

for _kind in tuple(V013_FRONTIER_SPECS): v0200_mythic_template(_kind)

def v0200_active_mythic_world_bosses(now=None):
    now=time.time() if now is None else float(now); slot=int(now//V020_MYTHIC_WORLD_BOSS_SECONDS)
    rng=random.Random(_v0140_hash_int(V020_WORLD_SEED,"mythic-world",slot)); kinds=list(V013_FRONTIER_SPECS); rng.shuffle(kinds)
    out=[]
    for kind in kinds[:2]:
        x=rng.randrange(V013_FRONTIER_SIDE); y=rng.randrange(V013_FRONTIER_SIDE)
        out.append({"kind":kind,"x":x,"y":y,"room_id":v0130_frontier_room_id(kind,x,y),"template_id":v0200_mythic_template(kind),
            "token":f"{slot}:v020mythic:{kind}:{x}:{y}","expires_at":(slot+1)*V020_MYTHIC_WORLD_BOSS_SECONDS})
    return tuple(out)

def v0200_mythic_encounters_for_room(room_id,now=None):
    return tuple(e for e in v0200_active_mythic_world_bosses(now) if e["room_id"]==room_id)


# -------------------- ARTIFACT PROGRESSION --------------------
V020_ARTIFACT_MAX_TIER=10
V020_ARTIFACT_UPGRADE_COSTS={
    2:{"v020_ancient_core":3,"coins":v0190_economy_sink(250,"equipment")},
    3:{"v020_gauntlet_seal":3,"v020_ancient_core":5,"coins":v0190_economy_sink(300,"equipment")},
    4:{"v020_mythic_essence":4,"v020_gauntlet_seal":5,"coins":v0190_economy_sink(350,"equipment")},
    5:{"v020_mythic_essence":10,"v020_ancient_core":12,"v020_gauntlet_seal":8,"coins":v0190_economy_sink(400,"equipment")},
    6:{"v020_mythic_essence":20,"v020_ancient_core":18,"v020_gauntlet_seal":12,"v021_ascension_crystal":5,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*2)},
    7:{"v020_mythic_essence":35,"v020_ancient_core":28,"v020_gauntlet_seal":20,"v021_ascension_crystal":10,"v021_world_tier_crest":3,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*4)},
    8:{"v020_mythic_essence":50,"v020_ancient_core":42,"v020_gauntlet_seal":30,"v021_ascension_crystal":20,"v021_world_tier_crest":8,"v021_eternal_sigil":2,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*8)},
    9:{"v020_mythic_essence":80,"v020_ancient_core":65,"v020_gauntlet_seal":45,"v021_ascension_crystal":35,"v021_world_tier_crest":15,"v021_eternal_sigil":5,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*16)},
    10:{"v020_mythic_essence":120,"v020_ancient_core":100,"v020_gauntlet_seal":70,"v021_ascension_crystal":60,"v021_world_tier_crest":30,"v021_eternal_sigil":10,"coins":min(V019_SAFE_INT,v0190_economy_sink(400,"equipment")*32)},
}
V020_ARTIFACT_VARIANTS={}
for _fid,_data in V017_ARTIFACTS.items():
    _base=_data["item_id"]; V020_ARTIFACT_VARIANTS[_fid]=[_base]
    _base_item=ITEMS[_base]
    for _tier in range(2,V020_ARTIFACT_MAX_TIER+1):
        _iid=f"{_base}_t{_tier}"; _scale=1.0+0.35*(_tier-1)
        _hp=1.0+(float(_data["hp"])-1.0)*_scale; _dmg=1.0+(float(_data["damage"])-1.0)*_scale; _def=1.0+(float(_data["defense"])-1.0)*_scale
        ITEMS[_iid]=dict(_base_item); ITEMS[_iid].update({"name":f"{_data['name']} +{_tier-1}","rarity":"mythic" if _tier>=4 else "legendary","rarity_name":"Artefakt Rozwinięty",
            "defense":int(round(int(_data["defense_flat"])*_scale)),"artifact_hp_multiplier":_hp,"artifact_damage_multiplier":_dmg,"artifact_defense_multiplier":_def,
            "v020_artifact_tier":_tier,"v020_artifact_base":_base,
            "desc":f"Rozwinięcie artefaktu {_data['name']}, poziom {_tier}/{V020_ARTIFACT_MAX_TIER}. Brak losowego faila."})
        UNIQUE_ITEM_COLLECTION_CATALOG[_iid]=ITEMS[_iid]["name"]; EQUIPMENT_COLLECTION_CATALOG[_iid]=ITEMS[_iid]["name"]
        V020_ARTIFACT_VARIANTS[_fid].append(_iid)


def v0200_artifact_owned_tier(db,account_id,faction_id):
    variants=V020_ARTIFACT_VARIANTS[faction_id]
    for tier in range(len(variants),0,-1):
        if db.item_qty(account_id,variants[tier-1])>0: return tier,variants[tier-1]
    return 0,None


# -------------------- LONG-TERM ENDGAME GOALS --------------------
V020_ENDGAME_GOALS=(
    ("mega_bosses",25,"Pokonaj 25 bossów megalochów"),
    ("gauntlet_finals",20,"Ukończ 20 finałów boss gauntletów"),
    ("mythic_world",15,"Pokonaj 15 mitycznych world bossów"),
    ("artifact_t5",5,"Zdobądź pięć artefaktów poziomu 5"),
)

v0130_refresh_exploration_catalog()

HELP_TOPICS["megalochy_v020"]=[
    "megalochy / megadungeons pokazuje pięć megalochów po 120, 160, 200, 240 i 280 pokoi.",
    "Wnętrza generują się na żądanie. Boss co 25 pokoi blokuje tylko przejście do następnej sekcji i tylko do pierwszego trwałego zaliczenia.",
    "Megalochy nie mają pułapek ani auto-aggro i używają generatora balansu v0.19.",
]
HELP_TOPICS["gauntlety_v020"]=[
    "gauntlety / gauntlets pokazuje cztery pięciorundowe próby bossów. gauntlet <nazwa> rozpoczyna próbę z Sali Boss Gauntletów.",
    "Każdy boss jest pasywny. Aktywny boss blokuje tylko wyjście do następnej rundy.",
]
HELP_TOPICS["mythicboss_v020"]=[
    "mitycznebossy / mythicbosses pokazuje dwa aktywne mityczne world bossy rotujące co 6 godzin.",
    "Są silniejsze od zwykłych world bossów, dają Esencję Mitycznego Bossa i nadal nie atakują pierwsi.",
]
HELP_TOPICS["artifactupgrade_v020"]=[
    "ulepszartefakt / artifactupgrade pokazuje lub wykonuje trwałe rozwinięcie artefaktu do poziomu 10.",
    "Poziomy 2-5 używają materiałów v0.20, a 6-10 także Kryształów Wzniesienia, Herbów World Tieru i Wiecznych Sigili. Nie ma szansy niepowodzenia ani niszczenia przedmiotu.",
]
HELP_TOPICS["endgamegoals_v020"]=["celekonca / endgamegoals pokazuje długoterminowe cele endgame i ich postęp."]
HELP_TOPIC_ALIASES.update({"megalochy":"megalochy_v020","megadungeons":"megalochy_v020","gauntlety":"gauntlety_v020","gauntlets":"gauntlety_v020",
    "mityczne bossy":"mythicboss_v020","mythic bosses":"mythicboss_v020","ulepsz artefakt":"artifactupgrade_v020","artifact upgrade":"artifactupgrade_v020",
    "cele konca":"endgamegoals_v020","endgame goals":"endgamegoals_v020"})
COMMAND_ALIASES.update({"megalochy":"megadungeons","megadungeons":"megadungeons","gauntlety":"gauntlets","gauntlets":"gauntlets","gauntlet":"gauntlet",
    "mitycznebossy":"mythicbosses","mythicbosses":"mythicbosses","mythicworldbosses":"mythicbosses",
    "ulepszartefakt":"artifactupgrade","artifactupgrade":"artifactupgrade","celekonca":"endgamegoals","endgamegoals":"endgamegoals"})


# ============================================================
# v0.21.0 - ASCENSION, WORLD TIERS & MYTHIC PROGRESSION
# Post-400 progression without resets, optional personal World Tiers 1-10,
# artifact Tier 6-10, five 8-piece mythic sets and an endless boss gauntlet.
# PASSIVE WORLD stays global. No traps, entry damage or auto damage.
# ============================================================
