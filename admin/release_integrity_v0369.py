from pathlib import Path
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
    ("v0.52.2 City Courier & Combat Quest Mastery", "POSTAL_QUEST_REWARDS_AUDIT_V0522"),
    ("v0.53.0 Courier Guild & Package Classes", "COURIER_GUILD_AUDIT_V0530"),
    ("v0.54.0 Risk-Free Courier Achievements", "COURIER_ACHIEVEMENTS_AUDIT_V0540"),
    ("v0.55.0 Courier Prestige & Tavern Hourlies", "COURIER_PRESTIGE_TAVERN_AUDIT_V0550"),
    ("v0.56.0 Living NPCs & Activity Journal", "LIVING_NPCS_ACTIVITY_AUDIT_V0560"),
    ("v0.57.0 Courier & Schema Modularization", "MODULAR_REFACTOR_AUDIT_V0570"),
    ("v0.58.0 Titles 2.0 & Unified Progress", "TITLES_PROGRESS_AUDIT_V0580"),
    ("v0.58.1 Living NPC Late Finalize Hotfix", "LIVING_NPCS_LATE_FINALIZE_AUDIT_V0581"),
    ("v0.60.0 NPC Crafting Orders & EQ Compare", "CRAFTING_ORDERS_COMPARE_AUDIT_V0600"),
    ("v0.61.0 Item Sources & Party Coordination", "ITEM_SOURCES_PARTY_COORDINATION_AUDIT_V0610"),
    ("v0.61.1 Crafting Guidance", "ITEM_SOURCES_PARTY_COORDINATION_AUDIT_V0610"),
    ("v0.61.2 Memory Efficiency", "V0612_MEMORY_EFFICIENCY_AUDIT"),
    ("v0.61.3 Crafting Orders Hotfix", "CRAFTING_ORDERS_COMPARE_AUDIT_V0600"),
    ("v0.61.4 Crafting Logistics & Mail Escrow", "CRAFTING_LOGISTICS_AUDIT_V0614"),
    ("v0.61.5 Profession Level-Up Announcements", "CRAFTING_LOGISTICS_AUDIT_V0614"),
    ("v0.61.6 Memory Efficiency II", "V0616_MEMORY_EFFICIENCY_AUDIT"),
    ("v0.70.0 Courier & Profession Expansion", "COURIER_PROFESSION_EXPANSION_AUDIT_V0700"),
    ("v0.70.1 Beginner Profession Quests", "COURIER_PROFESSION_EXPANSION_AUDIT_V0700"),
    ("v0.71.0 Profession & City Expansion II", "COURIER_PROFESSION_EXPANSION_AUDIT_V0700"),
    ("v0.71.1 Crypt Soul Shard Hotfix", "SOUL_SHARD_CRYPT_FINAL_AUDIT_V0711"),
    ("v0.71.2 Hourly Quest Diversity & Rewards", "LIVING_NPCS_ACTIVITY_AUDIT_V0560"),
    ("v0.71.3 Orders for All Professions", "CRAFTING_ORDERS_COMPARE_AUDIT_V0600"),
    ("v0.71.4 Eren Treasure Map Hotfix", "COURIER_PROFESSION_EXPANSION_AUDIT_V0700"),
    ("v0.71.5 Performance Hotfix", "PERFORMANCE_HOTFIX_AUDIT_V0715"),
    ("v0.71.6 Startup Performance Hotfix", "STARTUP_PERFORMANCE_AUDIT_V0716"),
    ("v0.71.7 Runtime Performance II", "RUNTIME_PERFORMANCE_AUDIT_V0717"),
    ("v0.71.8 Runtime Performance III", "RUNTIME_PERFORMANCE_AUDIT_V0718"),
]

PERFORMANCE_HOTFIX_AUDIT_V0715 = {
    "version": "0.71.5",
    "error_count": 0,
    "errors": [],
}
try:
    _world_cls = globals().get("World")
    _refresh = getattr(_world_cls, "refresh", None)
    if getattr(_refresh, "__defaults__", None) != (False,):
        PERFORMANCE_HOTFIX_AUDIT_V0715["errors"].append("World.refresh force/coalescing API missing")
    _find = globals().get("find_by_name")
    _find_code = getattr(_find, "__code__", None)
    if "_v0715_cache" not in tuple(str(x) for x in getattr(_find_code, "co_names", ())):
        PERFORMANCE_HOTFIX_AUDIT_V0715["errors"].append("ITEMS lookup cache missing")
    _db_source = (Path(__file__).resolve().parents[1] / "storage" / "database.py").read_text(encoding="utf-8")
    if "PRAGMA synchronous=NORMAL" not in _db_source:
        PERFORMANCE_HOTFIX_AUDIT_V0715["errors"].append("SQLite WAL synchronous=NORMAL missing")
except Exception as exc:
    PERFORMANCE_HOTFIX_AUDIT_V0715["errors"].append(f"performance audit exception: {type(exc).__name__}: {exc}")
PERFORMANCE_HOTFIX_AUDIT_V0715["error_count"] = len(PERFORMANCE_HOTFIX_AUDIT_V0715["errors"])

STARTUP_PERFORMANCE_AUDIT_V0716 = {"version":"0.71.6", "error_count":0, "errors":[]}
try:
    import core.native_runtime as _nr_v0716
    if len(getattr(_nr_v0716, "_RUNTIME_FULL_AUDIT_ONLY", ())) < 8:
        STARTUP_PERFORMANCE_AUDIT_V0716["errors"].append("runtime audit-only startup skip set missing")
    _gen_src = (Path(__file__).resolve().parents[1] / "core" / "generator_core.py").read_text(encoding="utf-8")
    if "ordinary class-shop EQ receives its stage" not in _gen_src or "not _plain_class_shop" not in _gen_src:
        STARTUP_PERFORMANCE_AUDIT_V0716["errors"].append("class-shop Generator fast path missing")
except Exception as exc:
    STARTUP_PERFORMANCE_AUDIT_V0716["errors"].append(f"startup performance audit exception: {type(exc).__name__}: {exc}")
STARTUP_PERFORMANCE_AUDIT_V0716["error_count"] = len(STARTUP_PERFORMANCE_AUDIT_V0716["errors"])

RUNTIME_PERFORMANCE_AUDIT_V0717 = {"version":"0.71.7", "error_count":0, "errors":[]}
try:
    _root_v0717 = Path(__file__).resolve().parents[1]
    _world_src_v0717 = (_root_v0717 / "world" / "world_state.py").read_text(encoding="utf-8")
    if "_last_live_by_room" not in _world_src_v0717 or "self._last_live_by_room.get(room_id, ())" not in _world_src_v0717:
        RUNTIME_PERFORMANCE_AUDIT_V0717["errors"].append("per-room live mob index missing")
    _inv_src_v0717 = (_root_v0717 / "player" / "session_mixins" / "inventory_equipment.py").read_text(encoding="utf-8")
    if "_owned_inventory_quantities_v0717" not in _inv_src_v0717 or "equip(self.account_id, slot, best_id, commit=False)" not in _inv_src_v0717:
        RUNTIME_PERFORMANCE_AUDIT_V0717["errors"].append("owned-inventory hot path or batched auto-equip missing")
    _gather_src_v0717 = (_root_v0717 / "player" / "session_mixins" / "gathering.py").read_text(encoding="utf-8")
    if "_base_gems_v0717" not in _gather_src_v0717:
        RUNTIME_PERFORMANCE_AUDIT_V0717["errors"].append("mining gem catalog cache missing")
    _db_inv_src_v0717 = (_root_v0717 / "storage" / "db_inventory.py").read_text(encoding="utf-8")
    if "def equip(self, account_id, slot, item_id, commit=True):" not in _db_inv_src_v0717:
        RUNTIME_PERFORMANCE_AUDIT_V0717["errors"].append("batched equipment commit API missing")
    _sources_src_v0717 = (_root_v0717 / "player" / "session_mixins" / "item_sources.py").read_text(encoding="utf-8")
    if "resolve_item_query_v0610._v0717_cache" not in _sources_src_v0717:
        RUNTIME_PERFORMANCE_AUDIT_V0717["errors"].append("item source lookup cache missing")
except Exception as exc:
    RUNTIME_PERFORMANCE_AUDIT_V0717["errors"].append(f"runtime performance audit exception: {type(exc).__name__}: {exc}")
RUNTIME_PERFORMANCE_AUDIT_V0717["error_count"] = len(RUNTIME_PERFORMANCE_AUDIT_V0717["errors"])

RUNTIME_PERFORMANCE_AUDIT_V0718 = {"version":"0.71.8", "error_count":0, "errors":[]}
try:
    _root_v0718 = Path(__file__).resolve().parents[1]
    _predeploy_src_v0718 = (_root_v0718 / "predeploy_full.py").read_text(encoding="utf-8")
    if 'full = ns["FULL_GAME_PREDEPLOY_AUDIT_V0336"]' not in _predeploy_src_v0718:
        RUNTIME_PERFORMANCE_AUDIT_V0718["errors"].append("FULL predeploy still repeats Full Game Audit")
    _db_inv_src_v0718 = (_root_v0718 / "storage" / "db_inventory.py").read_text(encoding="utf-8")
    if "def add_item(self, account_id, item_id, qty=1, commit=True):" not in _db_inv_src_v0718:
        RUNTIME_PERFORMANCE_AUDIT_V0718["errors"].append("batched inventory commit API missing")
    if "COALESCE(SUM(quantity),0)" not in _db_inv_src_v0718:
        RUNTIME_PERFORMANCE_AUDIT_V0718["errors"].append("aggregate inventory/storage quantity query missing")
    _prof_src_v0718 = (_root_v0718 / "player" / "session_mixins" / "profession_storage.py").read_text(encoding="utf-8")
    if "commit=False" not in _prof_src_v0718 or "if moved:\n                self.server.db.conn.commit()" not in _prof_src_v0718:
        RUNTIME_PERFORMANCE_AUDIT_V0718["errors"].append("bulk profession storage commit batching missing")
    _cmd_src_v0718 = (_root_v0718 / "player" / "session_mixins" / "command_loop.py").read_text(encoding="utf-8")
    if "[PERF SLOW COMMAND]" not in _cmd_src_v0718:
        RUNTIME_PERFORMANCE_AUDIT_V0718["errors"].append("slow command diagnostics missing")
    _server_src_v0718 = (_root_v0718 / "server" / "mud_server.py").read_text(encoding="utf-8")
    if "[PERF SLOW WORLD TICK]" not in _server_src_v0718:
        RUNTIME_PERFORMANCE_AUDIT_V0718["errors"].append("slow world tick diagnostics missing")
except Exception as exc:
    RUNTIME_PERFORMANCE_AUDIT_V0718["errors"].append(f"runtime performance III audit exception: {type(exc).__name__}: {exc}")
RUNTIME_PERFORMANCE_AUDIT_V0718["error_count"] = len(RUNTIME_PERFORMANCE_AUDIT_V0718["errors"])

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
    if str(globals().get("VERSION","")) != "0.71.8":
        errors.append(f"VERSION={globals().get('VERSION')!r}, expected 0.71.8")
    if str(globals().get("GENERATOR_CORE_VERSION","")) != "0.61.0":
        errors.append(f"Generator Core={globals().get('GENERATOR_CORE_VERSION')!r}, expected 0.61.0")

    return {
        "version":"0.71.8",
        "checked":len(_RELEASE_AUDITS_V0369),
        "preserved":preserved,
        "preserved_count":len(preserved),
        "error_count":len(errors),
        "errors":errors,
    }

CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369=cumulative_release_integrity_audit_v0369()
if CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369["error_count"]:
    raise RuntimeError(
        "Cumulative Release Integrity Audit v0.71.8 failed: "
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

HELP_TOPICS.setdefault("wersja", []).append("v0.59.0: braki / gaps / missing pokazuje konkretne wartości brakujące do Levelu, Soul Tieru, profesji, Gildii, kolekcji i aktywnych celów.")
HELP_TOPICS.setdefault("wersja", []).append("v0.60.0: rotujące Zamówienia Rzemieślnicze NPC co godzinę oraz porownaj <przedmiot> do pełnego porównania posiadanego EQ poza sklepem. Crafting Odłamków Duszy z v0.59.2 pozostaje bez zmian.")
HELP_TOPICS.setdefault("wersja", []).append("v0.60.1: Full Audit Compatibility Hotfix — pełny audit rozpoznaje talk_npc z Living NPCs; gameplay bez zmian.")
HELP_TOPICS.setdefault("wersja", []).append("v0.61.0: gdzie zdobyc <przedmiot> przeszukuje realne źródła przedmiotów; drużyna dostała trwały cel sesyjny i kontrolę gotowości.")
HELP_TOPICS.setdefault("wersja", []).append("v0.61.1: do czego <przedmiot>, braki receptura <przedmiot>, gdzie zdobyc <przedmiot> pelne i receptury mozliwe / craft mozliwe rozbudowują nawigację po craftingu.")
HELP_TOPICS.setdefault("wersja", []).append("v0.61.2: Memory Efficiency zmniejsza RAM przez generowanie opisów masowego EQ dopiero przy wyświetleniu; gameplay i zawartość bez zmian.")
HELP_TOPICS.setdefault("wersja", []).append("v0.61.3: Crafting Orders Hotfix przywraca oferty Haldora, naprawia oddawanie zamówień i chroni produkty przed ponownym pobraniem po starym crashu.")
HELP_TOPICS.setdefault("wersja", []).append("v0.61.5: Profession Level-Up Announcements — każdy awans poziomu profesji jest wyraźnie czytany jako AWANS PROFESJI: <profesja> osiąga poziom <N>; bez informacji o brakującym XP.")
HELP_TOPICS.setdefault("wersja", []).append("v0.61.6: Memory Efficiency II współdzieli identyczne pule łupu mobów i usuwa startup-only metadata z masowego klasowego EQ dopiero po audycie; gameplay bez zmian.")
HELP_TOPICS.setdefault("wersja", []).append("v0.61.4: Crafting Logistics dodaje craft <ilość>/wszystko, historię zamówień, bezpieczne załączniki mailowe, wielopoziomową drogę receptury oraz przywrócone mithrilowe EQ z Fragmentów Mithrilu.")

HELP_TOPICS.setdefault("wersja", []).append("v0.71.2: godzinne questy NPC mają różne cele (rozmowa, dostawa, zbieranie, patrol), nie skupiają się na jednym NPC i żaden powtarzalny quest nie daje już tylko 1 EXP postaci.")
HELP_TOPICS.setdefault("wersja", []).append("v0.71.3: rotujące zamówienia działają dla wszystkich 12 profesji; Wędkarstwo, Górnictwo, Drwalstwo i Zielarstwo mają dostawy świeżo zebranych zasobów, a Zaklinanie liczy udane zaklęcia.")
HELP_TOPICS.setdefault("wersja", []).append("v0.71.4: naprawiono `użyj mapy` dla questu Kartografa Erena; aktywny quest potrafi też bezpiecznie odtworzyć brakującą mapę, jeśli trop nie został jeszcze zapisany.")
HELP_TOPICS.setdefault("wersja", []).append("v0.71.7: Runtime Performance II ogranicza skany globalnych katalogów podczas gry, indeksuje żywe moby per pokój i grupuje zapisy Auto EQ; gameplay i balans bez zmian.")
HELP_TOPICS.setdefault("wersja", []).append("v0.71.8: Runtime Performance III usuwa podwójne wykonanie Full Game Audit, grupuje zapisy przy przenoszeniu surowców i dodaje lekką diagnostykę wolnych komend/ticków; gameplay bez zmian.")
LATEST_CHANGES_TITLE = "Soulbound v0.71.8 - Runtime Performance III"
LATEST_CHANGES = [
    "v0.71.8: Full PREDEPLOY nie uruchamia już drugi raz Full Game Audit; bulk storage używa jednego commita, a wieloelementowe liczenie zasobów używa agregacji SQL; log wskazuje komendy >=0.25 s i ticki świata >=0.10 s.",
    "v0.71.7: gorące komendy pracują na faktycznie posiadanych przedmiotach zamiast skanować 30k+ ITEMS; świat używa indeksu żywych mobów per pokój; Górnictwo i źródła przedmiotów mają trwałe cache katalogów.",
    "v0.71.6: ciężkie audyty architektury działają w FULL PREDEPLOY, nie przy zwykłym starcie; Generator Core pomija zbędne obliczenia masowego klasowego EQ.",
    "v0.71.5: zoptymalizowano gorące ścieżki świata, cache wyszukiwania ITEMS i SQLite WAL bez zmiany balansu ani zawartości.",
    "v0.71.4: `użyj mapy` poprawnie wybiera questową Mapę Erena i zapisuje trop do zadania Znak poza mapą.",
    "v0.71.3: rotujące zamówienia obejmują wszystkie 12 profesji, nie tylko profesje wytwórcze.",
    "Wędkarstwo, Górnictwo, Drwalstwo i Zielarstwo mają trzy godzinne dostawy, które liczą wyłącznie świeżo zebrane surowce po przyjęciu zamówienia.",
    "Zaklinanie ma trzy serie zamówień liczące faktyczne udane akcje Zaklinania; przy oddaniu nie pobiera się produktu drugi raz.",
    "Każda z trzech ofert nadal może zostać ukończona raz w cyklu, a ukończenie jednej nie blokuje pozostałych.",
    "Naprawa v0.71.2 różnicująca godzinne questy NPC pozostaje aktywna.",
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

HELP_TOPICS.setdefault("wersja", []).append("v0.52.2: City Courier & Combat Quest Mastery — poczta kurierska między 9 miastami, lista paczek co 15 minut, miasta w walk/prowadz, EXP Biegłości z questów walki i brak Soul XP z questów profesyjnych/rzemieślniczych.")
HELP_TOPICS.setdefault("wersja", []).append("v0.53.0: Courier Guild & Package Classes — reputacja Kurierów 1-400, osiem rang i tytułów, sześć rodzajów paczek z różną nagrodą/ryzykiem oraz trwałe statystyki kuriera.")
HELP_TOPICS.setdefault("wersja", []).append("v0.54.0: Risk-Free Courier Achievements — usunięto losowe ryzyko z paczek i dodano osiągnięcia za 10/100/1000/10 000 dostaw, wszystkie miasta i wszystkie typy paczek.")
HELP_TOPICS.setdefault("wersja", []).append("v0.55.0: Courier Prestige & Tavern Hourlies — prestiżowe paczki od reputacji 360, osiągnięcia po 100 dostaw per miasto/per typ oraz trzy godzinne zlecenia Karczmarki Elii.")



HELP_TOPICS.setdefault("dziennik", []).extend([
    "Dziennik aktywności zapisuje od v0.56.0 ostatnie bossy, ukończone questy, ważne dropy, dostawy, osiągnięcia i awanse.",
    "Komendy: dziennik; dziennik bossy; dziennik questy; dziennik dropy; dziennik dostawy; dziennik osiągnięcia; dziennik awansy.",
])
HELP_TOPICS.setdefault("co robic", []).extend([
    "co robic — podaje dokładnie pięć aktualnych propozycji: questy do oddania/wykonania, lokalne zadania, pocztę, expowisko, profesje lub eksplorację.",
    "Lista jest krótka i przeznaczona do wygodnego czytania przez NVDA.",
])
HELP_TOPICS.setdefault("wersja", []).append("v0.56.0: Living NPCs & Activity Journal — sieć karczm z godzinymi questami, automatyczne questy dla NPC bez zadań, trwały dziennik aktywności i komenda co robic.")

HELP_TOPICS.setdefault("wersja", []).append("v0.57.0: Courier & Schema Modularization — Courier ma osobny moduł, a db_schema.py jest małym koordynatorem dziesięciu modułów schematu/migracji; gameplay i save'y pozostają zgodne.")

HELP_TOPICS.setdefault("wersja", []).append("v0.57.1: Fast Railway Predeploy — szybki gate działa podczas Docker build, a pełny historyczny audyt pozostaje osobno w predeploy_full.py; bez zmian gameplayu i save'ów.")
HELP_TOPICS.setdefault("wersja", []).append("v0.58.0: Titles 2.0 & Unified Progress — retroaktywne tytuły za eksplorację, bossy, profesje, Kurierów, gildie i frakcje oraz pełna komenda postep w jednym widoku NVDA.")
HELP_TOPICS.setdefault("wersja", []).append("v0.58.1: Living NPC Late Finalize Hotfix — późno tworzeni NPC, w tym klasowi sprzedawcy EQ, dostają godzinne questy przed audytem; naprawiono restart loop na Railway bez wyłączania walidacji.")
HELP_TOPICS.setdefault("wersja", []).append("v0.58.2: Runtime Symbol Collision Hotfix — usunięto kolizję `_has_quest` między audytami i dodano wykrywanie nieoczekiwanych override’ów symboli do Fast Railway Predeploy.")
HELP_TOPICS.setdefault("wersja", []).append("v0.58.4: Essential Quest Progress Notifications — postęp questów nie znika w zwięzłym logu walki; kill-quest pokazuje zaliczony cel, X/Y i gotowość do oddania.")

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.70.0: Courier & Profession Expansion — 12 nowych osad, 21 miast kurierskich łącznie, 48 nowych kontraktów profesyjnych oraz niezależne ukończenia wszystkich 3 rotujących zamówień rzemieślniczych w każdym cyklu."
)
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.70.1: Beginner Profession Quests — wszystkie 12 profesji ma teraz co najmniej jeden quest dostępny na poziomie profesji 1-10; dodano brakujące starty dla Krawiectwa, Garbarstwa, Stolarstwa i Zaklinania."
)

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.71.0: Profession & City Expansion II — 120 nowych etapów Drogi Mistrza profesji, 63 lokalne questy dla 21 miast oraz osobna reputacja miast 1-400 z bonusem kurierskim."
)
HELP_TOPICS.setdefault("reputacja miast", []).extend([
    "reputacjamiast — pokazuje reputację wszystkich 21 miast i osad w skali 1-400.",
    "reputacjamiast <miasto> — pokazuje rangę miasta i bonus do wypłat kurierskich kierowanych do tego miasta.",
    "Reputację miasta zwiększają lokalne questy zarządcy oraz dostawy paczek do danego miasta."
])
