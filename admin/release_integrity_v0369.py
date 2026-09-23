# -*- coding: utf-8 -*-
"""Soulbound v0.36.9 - cumulative release integrity guard.

This file intentionally changes no gameplay. It verifies that recent milestone
features are still present after assembling the final runtime.
"""

_RELEASE_AUDITS_V0369 = [
    ("v0.35.5 party temple/shards", "PARTY_TEMPLE_SHARD_AUDIT_V0355"),
    ("v0.35.6 salvage all", "SALVAGE_ALL_AUDIT_V0356"),
    ("v0.35.7 bulk smelting/ingot smithing", "BULK_SMELTING_INGOT_SMITHING_AUDIT_V0357"),
    ("v0.35.8 no PvP", "NO_PVP_PLAYER_SAFETY_AUDIT_V0358"),
    ("v0.35.9 shared mob drops", "ALL_PARTY_MOB_DROPS_SHARED_AUDIT_V0359"),
    ("v0.35.10 shared corpse loot", "ALL_PARTY_CORPSE_LOOT_SHARED_AUDIT_V03510"),
    ("v0.35.11 local party combat buffs", "ALL_LOCAL_PARTY_BUFFS_AUDIT_V03511"),
    ("v0.36.0 progression 600/leader disband", "PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360"),
    ("v0.36.1 party quest accept", "PARTY_QUEST_ACCEPT_SYNC_AUDIT_V0361"),
    ("v0.36.2 terrain threat", "TERRAIN_THREAT_REBALANCE_AUDIT_V0362"),
    ("v0.36.3 offline profiles", "OFFLINE_PLAYER_PROFILES_AUDIT_V0363"),
    ("v0.36.4 independent cooldowns", "INDEPENDENT_SKILL_COOLDOWNS_AUDIT_V0364"),
    ("v0.36.5 Soul Tier 7 cemetery density", "SOUL_TIER7_CEMETERY_SPAWN_AUDIT_V0365"),
    ("v0.36.6 named UOSSMUD superbosses", "UOSS_SUPERBOSS_AUDIT_V0366"),
    ("v0.36.8 crypt/EXP/same-room exit/local Soul Tier", "CRYPT_PARTY_REBALANCE_AUDIT_V0368"),
    ("v0.36.10 every crypt floor harder", "CRYPT_EVERY_FLOOR_PROGRESSION_AUDIT_V03610"),
    ("v0.37.0 Crypt Overdrive", "CRYPT_OVERDRIVE_AUDIT_V0370"),
    ("v0.36.11 troll shaman density", "TROLL_SHAMAN_DENSITY_AUDIT_V03611"),
    ("v0.37.0 public records/hall/key salvage", "PUBLIC_RECORDS_AUDIT_V0370"),
    ("v0.37.1 local party revive", "PARTY_REVIVE_AUDIT_V0371"),
    ("v0.38.0 party combo/ultimate/dungeon summary", "PARTY_SYSTEMS_AUDIT_V0380"),
    ("v0.38.1 Tower Overdrive", "TOWER_OVERDRIVE_AUDIT_V0381"),
    ("v0.38.2 Infinite Unified Magitek", "MAGITEK_INFINITE_AUDIT_V0382"),
    ("v0.38.3 hourly Magitek contracts", "MAGITEK_HOURLY_QUESTS_AUDIT_V0383"),
    ("v0.38.4 global world threat", "WORLD_THREAT_OVERDRIVE_AUDIT_V0384"),
    ("v0.38.5 currency ratio", "CURRENCY_RATIO_AUDIT_V0385"),
    ("v0.38.6 global difficulty overdrive II", "GLOBAL_DIFFICULTY_OVERDRIVE_AUDIT_V0386"),
    ("v0.38.7 canonical bounty targets", "BOUNTY_CANONICAL_TARGET_AUDIT_V0387"),
    ("v0.38.8 easier Soul Tier 8 trial", "SOUL_TIER8_TRIAL_AUDIT_V0388"),
    ("v0.38.9 canonical kill quest credit", "QUEST_KILL_CANONICALIZATION_AUDIT_V0389"),
    ("v0.38.10 canonical smithing materials", "SMITHING_MATERIALS_AUDIT_V03810"),
    ("v0.38.11 procedural legends/server chronicle", "SERVER_CHRONICLE_AUDIT_V03811"),
    ("v0.38.12 named dungeon entry/return", "DUNGEON_NAMED_ENTRY_AUDIT_V03812"),
    ("v0.38.13 underground route isolation", "UNDERGROUND_ROUTE_ISOLATION_AUDIT_V03813"),
    ("v0.38.14 bounty abandon aliases", "BOUNTY_ABANDON_AUDIT_V03814"),
    ("v0.39.0 architecture stabilization", "ARCHITECTURE_STABILIZATION_AUDIT_V0390"),
    ("v0.40.0 maintenance architecture", "MAINTENANCE_ARCHITECTURE_AUDIT_V0400"),
    ("v0.41.0 native module architecture", "NATIVE_MODULE_ARCHITECTURE_AUDIT_V0410"),
    ("v0.42.0 modular services/data/events", "MODULAR_SERVICES_AUDIT_V0420"),
    ("v0.43.0 explicit dependencies architecture", "EXPLICIT_DEPENDENCIES_AUDIT_V0430"),
    ("v0.44.0 explicit gameplay dependencies", "EXPLICIT_GAMEPLAY_DEPENDENCIES_AUDIT_V0440"),
    ("v0.45.0 conservative explicit dependencies", "EXPLICIT_STABLE_DEPENDENCIES_AUDIT_V0450"),
    ("v0.46.0 explicit persistence/override cleanup", "EXPLICIT_PERSISTENCE_AUDIT_V0460"),
    ("v0.47.0 focused explicit combat architecture", "COMBAT_ARCHITECTURE_AUDIT_V0470"),
    ("v0.48.0 controlled world/data ownership", "CATALOG_OWNERSHIP_AUDIT_V0480"),
    ("v0.49.0 authoritative commands registry", "COMMAND_REGISTRY_AUDIT_V0490"),
    ("v0.50.0 maintainable core baseline", "MAINTAINABLE_CORE_AUDIT_V0500"),
    ("v0.50.1 progression pace rebalance", "PROGRESSION_PACE_AUDIT_V0501"),
    ("v0.50.2 long-term stat/progression balance", "LONG_TERM_BALANCE_AUDIT_V0502"),
    ("v0.50.3 world/dungeon difficulty pressure", "DIFFICULTY_PRESSURE_AUDIT_V0503"),
    ("v0.51.0 World Expansion I", "WORLD_EXPANSION_I_AUDIT_V0510"),
    ("v0.52.0 World Expansion II", "WORLD_EXPANSION_II_AUDIT_V0520"),
    ("v0.52.1 Railway packaging hotfix", "RAILWAY_PACKAGING_AUDIT_V0521"),
]

def cumulative_release_integrity_audit_v0369():
    errors=[]
    preserved=[]
    for label, varname in _RELEASE_AUDITS_V0369:
        value=globals().get(varname)
        if not isinstance(value, dict):
            errors.append(f"missing audit: {label} ({varname})")
            continue
        count=int(value.get("error_count",0) or 0)
        if count:
            errors.append(f"regression in {label}: {count} errors")
            continue
        preserved.append(label)

    # Direct release-line checks for the exact milestones the user flagged.
    if str(globals().get("VERSION","")) != "0.52.1":
        errors.append(f"VERSION={globals().get('VERSION')!r}, expected 0.52.1")
    if str(globals().get("GENERATOR_CORE_VERSION","")) != "0.52.1":
        errors.append(f"Generator Core={globals().get('GENERATOR_CORE_VERSION')!r}, expected 0.52.1")

    return {
        "version":"0.52.1",
        "checked":len(_RELEASE_AUDITS_V0369),
        "preserved":preserved,
        "preserved_count":len(preserved),
        "error_count":len(errors),
        "errors":errors,
    }

CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369=cumulative_release_integrity_audit_v0369()
if CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369["error_count"]:
    raise RuntimeError(
        "Cumulative Release Integrity Audit v0.52.1 failed: "
        + "; ".join(CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.11: Proceduralne Legendy zapisują trwałą Kronikę Serwera: pierwsze zabicia, world bossy, rekordy połowów, projekty świata i wyjątkowe dropy."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.12: przy progu Krypty, Wieży lub lochu wpisuje się nazwę miejsca; wyjście wraca do tego samego bezpiecznego progu."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.13: Piwnica Świątyni, Kopalnia Głębinowa i Krypta są osobnymi strefami nawigacji; `prowadz` nie używa już piwnicy jako skrótu do niezwiązanych obszarów."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.14: bounty porzuć / bounty porzuc anuluje aktywny kontrakt bez zmiany licznika ukończonych i bez darmowego losowania nowych ofert."
)

LATEST_CHANGES_TITLE = "Soulbound v0.52.1 - Railway Packaging Hotfix"
LATEST_CHANGES = [
    "v0.52.1: Railway Packaging Hotfix — obraz kontenera zawiera config/, data/, events/ i validation/ wymagane przez modułowy runtime.",
    "v0.52.0: World Expansion II — dodano zamorski ląd Ardelii ze stolicą Srebrna Korona i trzema osadami.",
    "Dodano dziesięć nowych expowisk od Brzegów Szeptów po Rubieże Nocy, każde z własnymi mobami i bossem.",
    "Nowy ląd ma pętle dróg i trzy trasy między osadami, więc podróż nie wymaga ciągłego wracania do stolicy.",
    "Dodano 20 odnawialnych lokalnych zleceń; stare regiony, progresja i World Expansion I pozostają bez zmian.",
    "v0.50.1-v0.50.3 nadal obowiązuje: wolniejsza długoterminowa progresja i podniesiona trudność świata/lochów.",
]



HELP_TOPICS.setdefault("wersja", []).append(
    "v0.39.0: uporządkowano architekturę bez zmiany gameplayu: jawny manifest runtime, kontrolowane nadpisania, osobne moduły generatorów i deklaratywny router prostych komend."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.40.0: Maintenance Architecture — baza i największe mixiny zostały rozbite według odpowiedzialności; diagnostyka błędów wskazuje subsystem, plik i linię bez zmiany gameplayu."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.41.0: Native Module Architecture — cały runtime jest ładowany jako prawdziwe moduły Pythona; usunięto aktywne sklejanie źródeł przez exec, zachowując gameplay v0.40.0."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.42.0: Modular Services Architecture — dane i balans są oddzielone od logiki, a kill/gather progression korzysta z centralnego event busa; naprawy prowadzą do data/, config/, events/ lub konkretnego subsystemu."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.43.0: Explicit Dependencies Architecture — nowe i zmigrowane moduły używają jawnych importów/eksportów, a compatibility bridge jest mierzalny i nie może się ponownie rozrastać."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.44.0: Explicit Gameplay Dependencies — kolejna fala modułów gameplayowych działa bez compatibility injection; ukryte zależności legacy spadły z 2312 do 1553."
)

HELP_TOPICS.setdefault("wersja", []).append("v0.45.0: Conservative Explicit Dependencies — 20 stabilnych modułów działa bez compatibility injection; dług legacy spadł z 1553 do 1182.")

HELP_TOPICS.setdefault("wersja", []).append("v0.46.0: Explicit Persistence & Override Cleanup — persistence działa przez jawne importy, a historyczne monkey-patche Database zostały zastąpione normalnym mixinem.")

HELP_TOPICS.setdefault("wersja", []).append("v0.47.0: Focused Explicit Combat Architecture — walka jest podzielona na osobne moduły skilli, obrażeń, realtime, nagród i przeżycia; combat.py jest tylko agregatem kompatybilności.")

HELP_TOPICS.setdefault("wersja", []).append("v0.48.0: Controlled World/Data Ownership — runtime nie zapisuje już bezpośrednio do wspólnych katalogów; każda kontrolowana zmiana ma ślad pochodzenia i właściciela.")

HELP_TOPICS.setdefault("wersja", []).append("v0.49.0: Authoritative Commands Registry — aliasy, handlery, HELP i zasady bezpieczeństwa komend są śledzone centralnie; parser nie zawiera już ręcznej drabiny komend.")

HELP_TOPICS.setdefault("wersja", []).append("v0.50.0: Maintainable Core Baseline — aktywne moduły mają nazwy funkcjonalne, historyczne pochodzenie jest centralnie opisane, a legacy compatibility działa wyłącznie z jawnej allowlisty.")

HELP_TOPICS.setdefault("wersja", []).append("v0.50.1: Progression Pace Rebalance — Character Level, Górnictwo i Kilof rozwijają się około 2x wolniej; pozostałe profesje i narzędzia zachowują dotychczasowe tempo.")

HELP_TOPICS.setdefault("wersja", []).append("v0.50.2: Long-Term Stat & Progression Balance — każda bazowa statystyka rośnie około co 120 równorzędnych akcji; statystyki pozostają bez limitu, a pozostałe długie osie progresji są audytowane pod kątem czasu dojścia do 600.")

HELP_TOPICS.setdefault("wersja", []).append("v0.50.3: Harder World & Dungeons — zwiększono HP i obrażenia całego świata oraz jeszcze mocniej instancji/Krypt; nagrody rosną znacznie słabiej niż trudność.")

HELP_TOPICS.setdefault("wersja", []).append("v0.51.0: World Expansion I — cztery nowe osady, osiem nowych expowisk, nowe drogi, moby, bossowie, NPC i 16 lokalnych zleceń.")

HELP_TOPICS.setdefault("wersja", []).append("v0.52.0: World Expansion II — Ardelia, stolica Srebrna Korona, trzy osady, dziesięć nowych expowisk, 40 nowych mobów i 20 lokalnych zleceń.")

HELP_TOPICS.setdefault("wersja", []).append("v0.52.1: Railway Packaging Hotfix — Dockerfile kopiuje wszystkie pakiety modułowego runtime: config, data, events i validation; brak tych katalogów nie może już przejść audytu wydania.")
