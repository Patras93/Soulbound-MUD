from data import catalog_mutations as _catalog_mut

# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.

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
    "bounty porzuć / bounty porzuc - porzuć aktywny kontrakt; bieżący postęp przepada, licznik ukończonych i aktualne oferty pozostają bez zmian.",
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
    "Panel działa także przy 0/14 postaci: lista kont, postacie konta, wipe własnego lub wskazanego konta, usunięcie jednej postaci i wipe wszystkich postaci serwera.",
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
    "Biegłość każdej z 14 klas ma zakres 1-400; na każdym progu 1 oraz co 10 aż do 400 dostępne są 3 skille/spelle do nauczenia.",
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
    "Każda z 14 klas ma 3 różne linie EQ o równym budżecie mocy.",
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
    "Biegłość każdej z 14 klas ma zakres 1-400; skille zachowują stare progi 1-200 i dalsze odblokowania 220-400.",
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
        return ("giant", floor, min(CHARACTER_MAX_LEVEL, max(20, floor * 2)))
    floor = crypt_floor_number(room_id)
    if is_crypt_boss_floor(floor):
        return ("crypt", floor, min(CHARACTER_MAX_LEVEL, floor))
    floor = astral_floor_number(room_id)
    if is_astral_boss_floor(floor):
        return ("astral", floor, min(CHARACTER_MAX_LEVEL, floor))
    floor = mythic_crypt_floor_number(room_id)
    if is_mythic_crypt_boss_floor(floor):
        return ("mythic_crypt", floor, min(CHARACTER_MAX_LEVEL, 100 + floor // 2))
    floor = mythic_astral_floor_number(room_id)
    if is_mythic_astral_boss_floor(floor):
        return ("mythic_astral", floor, min(CHARACTER_MAX_LEVEL, 110 + floor // 2))
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
        _catalog_mut.catalog_assign({
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
        }, 'ITEMS', ITEMS, (key_id,))

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
    power = max(1, min(CHARACTER_MAX_LEVEL, int(power)))
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

    # v0.71.5: exact item lookups are O(1); partial searches reuse normalized
    # names/aliases instead of normalizing tens of thousands of strings again.
    # Cache lives on this already-existing function, so the architectural global
    # dependency budget does not grow.
    if mapping is ITEMS and name_field == "name":
        cache = getattr(find_by_name, "_v0715_cache", None)
        if not isinstance(cache, dict) or cache.get("size") != len(ITEMS):
            rows = []
            exact = {}
            for key, value in ITEMS.items():
                key_name = normalize_lookup_text(key)
                name = normalize_lookup_text(value.get("name", key))
                aliases = tuple(
                    normalize_lookup_text(alias)
                    for alias in (value.get("aliases") or ())
                    if str(alias or "").strip()
                )
                rows.append((key, value, key_name, name, aliases))
                for token in (key_name, name, *aliases):
                    if token and token not in exact:
                        exact[token] = (key, value)
            cache = {"size": len(ITEMS), "rows": tuple(rows), "exact": exact}
            find_by_name._v0715_cache = cache
        hit = cache["exact"].get(q)
        if hit is not None:
            return hit
        partial = []
        for key, value, key_name, name, aliases in cache["rows"]:
            if q in name or q in key_name or any(q in alias for alias in aliases):
                partial.append((key, value))
                if len(partial) > 1:
                    return None
        return partial[0] if partial else None

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
    _catalog_mut.catalog_assign({
        "name": _iname, "type": "craft_material", "price": None,
        "craftbox_category": "salvage",
        "desc": "Materiał odzyskany przez rozkładanie niepotrzebnego EQ u Haldora.",
    }, 'ITEMS', ITEMS, (_iid,))
# v0.31.13: materiały salvage mają także praktyczne zastosowanie w Kuźni.
if "salvage_iron_scrap" in ITEMS:
    _catalog_mut.catalog_assign("Odłamek żelaza odzyskany przez rozkładanie EQ u Haldora. "
        "Dwa odłamki można przetopić w Kuźni w 1 Żelazną sztabkę.", 'ITEMS', ITEMS, ("salvage_iron_scrap", "desc"))
_V03113_SALVAGE_SMELT_OUTPUTS = {
    "salvage_steel_scrap": "Sztabkę Stali",
    "salvage_cobalt_fragment": "Kobaltową sztabkę",
    "salvage_runic_fragment": "Runiczną sztabkę",
    "salvage_dragonsteel_fragment": "Sztabkę Smoczej Stali",
    "salvage_astral_fragment": "Astralną sztabkę",
    "salvage_void_fragment": "Sztabkę Pustki",
    "salvage_eternium_fragment": "Sztabkę Eternium",
}
for _sid, _out_name in _V03113_SALVAGE_SMELT_OUTPUTS.items():
    if _sid in ITEMS:
        _catalog_mut.catalog_assign(ITEMS[_sid].get("desc", "").rstrip(". ")
            + f". Dwa takie materiały można przetopić w Kuźni w 1 {_out_name}.", 'ITEMS', ITEMS, (_sid, "desc"))

_catalog_mut.catalog_assign({
    "name": "Esencja Przekucia", "type": "craft_material", "price": None,
    "craftbox_category": "salvage",
    "desc": "Esencja używana przez Haldora do zmiany jednego bonusu EQ.",
}, 'ITEMS', ITEMS, ("reforge_essence",))
_catalog_mut.catalog_assign({
    "name": "Pył Runiczny", "type": "craft_material", "price": None,
    "craftbox_category": "runes",
    "desc": "Pył odzyskiwany z wysokopoziomowego EQ; służy do tworzenia run.",
}, 'ITEMS', ITEMS, ("rune_dust",))
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
    _catalog_mut.catalog_assign({
        "name": _rname, "type": "craft_material", "price": None,
        "craftbox_category": "runes", "rune_key": _rkey,
        "rune_properties": _props, "rune_stats": _stats,
        "desc": "Runę można osadzić w gnieździe endgame EQ; nie zmienia wymogu Biegłości.",
    }, 'ITEMS', ITEMS, (_rid,))
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
V0925_MASTERY_MILESTONES = (1, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600)

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
    level = max(1, min(CHARACTER_MAX_LEVEL, int(
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
    return max(1, min(CHARACTER_MAX_LEVEL, int(
        item.get("required_character_level", item.get("required_mastery", 1)) or 1
    )))

def v03042_upgrade_required_smithing(item, target_upgrade):
    target_upgrade = max(1, min(V03042_EQ_UPGRADE_MAX, int(target_upgrade)))
    return min(PROFESSION_MAX_LEVEL, v03042_equipment_level(item) + (target_upgrade - 1) * 5)

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
    if mastery >= 500: return 4
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
    "technology": "Technologia",
    "other": "Pozostałe materiały",
}
V0925_CRAFTBOX_ALIASES = {
    "kowalstwo":"blacksmithing", "kowal":"blacksmithing", "blacksmithing":"blacksmithing",
    "jubilerstwo":"jewelcrafting", "jubilerskie":"jewelcrafting", "jewelry":"jewelcrafting",
    "alchemia":"alchemy", "alchemy":"alchemy",
    "runy":"runes", "runes":"runes",
    "salvage":"salvage", "odzysk":"salvage", "odzyskane":"salvage",
    "technologia":"technology", "tech":"technology", "technology":"technology",
    "inne":"other", "pozostale":"other", "pozostałe":"other",
}


# ============================================================
# v0.9.26 - GILDIA GRACZY: SKARBIEC / ROZWÓJ / RANGI
# ============================================================
V0926_GUILD_MAX_LEVEL = 600
V0926_GUILD_LEGACY_MAX_LEVEL = 100
V0926_GUILD_PREVIOUS_CAP = 400
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

def _v0926_legacy_guild_anchor_400():
    # v0.35.11 używało Generator Core MAX_LEVEL=400 jako kotwicy kosztu.
    # Wyliczamy tę samą wartość bez zależności od nowego globalnego capu 600.
    old_max = int(generator_core_v027.MAX_LEVEL)
    try:
        generator_core_v027.MAX_LEVEL = V0926_GUILD_PREVIOUS_CAP
        return generator_core_v027.system_cost(V0926_GUILD_PREVIOUS_CAP, "guild-level", 300.0)
    finally:
        generator_core_v027.MAX_LEVEL = old_max

def v0926_guild_upgrade_cost(current_level):
    """Koszt rozwoju Gildii 1-600; poziomy 1-400 zachowują balans v0.35.11."""
    level=max(1,min(V0926_GUILD_MAX_LEVEL,int(current_level or 1)))
    if level >= V0926_GUILD_MAX_LEVEL:
        return 0
    if level < V0926_GUILD_LEGACY_MAX_LEVEL:
        # To mapowanie było historycznie liczone w przestrzeni 1-400.
        old_max = int(generator_core_v027.MAX_LEVEL)
        try:
            generator_core_v027.MAX_LEVEL = V0926_GUILD_PREVIOUS_CAP
            stage=generator_core_v027.stage_from_index(level+1,V0926_GUILD_LEGACY_MAX_LEVEL)
            return generator_core_v027.system_cost(stage,"guild-level",300.0)
        finally:
            generator_core_v027.MAX_LEVEL = old_max
    anchor=_v0926_legacy_guild_anchor_400()
    if level <= V0926_GUILD_PREVIOUS_CAP:
        extension=(float(level)/float(V0926_GUILD_LEGACY_MAX_LEVEL))**2.0
        return min(9_000_000_000_000_000_000,max(1,int(round(anchor*extension))))
    # 401-600 kontynuuje krzywą od dokładnego kosztu poziomu 400.
    cost_400=min(9_000_000_000_000_000_000,max(1,int(round(anchor*(4.0**2.0)))))
    extension=(float(level)/float(V0926_GUILD_PREVIOUS_CAP))**2.0
    return min(9_000_000_000_000_000_000,max(1,int(round(cost_400*extension))))

def v0926_guild_bonus_percent(level):
    """Bonus Gildii 1-600; 1-400 identyczne z v0.35.11, potem dalszy wzrost."""
    level=max(1,min(V0926_GUILD_MAX_LEVEL,int(level or 1)))
    if level <= V0926_GUILD_LEGACY_MAX_LEVEL:
        return generator_core_v027.guild_bonus_percent(level,V0926_GUILD_LEGACY_MAX_LEVEL)
    if level <= V0926_GUILD_PREVIOUS_CAP:
        progress=(level-V0926_GUILD_LEGACY_MAX_LEVEL)/(V0926_GUILD_PREVIOUS_CAP-V0926_GUILD_LEGACY_MAX_LEVEL)
        return min(23,11+int(round(12*(progress**0.90))))
    # Po starym capie 400 bonus nadal rośnie, do 29% na poziomie 600.
    progress=(level-V0926_GUILD_PREVIOUS_CAP)/(V0926_GUILD_MAX_LEVEL-V0926_GUILD_PREVIOUS_CAP)
    return min(29,23+int(round(6*(progress**0.90))))


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
_catalog_mut.catalog_update_path('ITEMS', ITEMS, (), {
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

_catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
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
_catalog_mut.catalog_assign({
    "name": "Strażnik Starego Cmentarza",
    "room": "graveyard",
    "dialogue": (
        "Nieumarli znowu wychodzą z grobów. Jeśli oczyścisz teren, zapłacę za patrol. "
        "Zlecenie odnawia się co godzinę."
    ),
    "quest": "cemetery_undead_rising_v0929",
}, 'NPCS', NPCS, ("cemetery_watchman_v0929",))

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
        _catalog_mut.catalog_assign(tuple(_tags), 'MOB_TEMPLATES', MOB_TEMPLATES, (_mid, "quest_targets"))

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
    "Godzinne zlecenia odnawiają się niezależnie po 60 minutach od ukończenia. Każde zaczyna od 0/x i liczy wyłącznie zdarzenia wykonane po przyjęciu.",
    "Tablica Godzinnych Zleceń oferuje stale zadania bojowe i profesyjne, w tym Kły Wilków Cienia 0/5. Kły muszą zostać zdobyte po przyjęciu i są zabierane przy oddaniu.",
    "Haldor: Złamane ostrza i Pancerz do przetopu; Orin: Toksyczne gruczoły; pozostałe godzinne zadania obejmują ryby, rudy, drewno, zioła i walkę.",
]
HELP_TOPICS.setdefault("quest", []).append(
    "v0.9.29: help questy godzinne opisuje 8 nowych odnawialnych zadań profesyjnych i cmentarnych."
)
