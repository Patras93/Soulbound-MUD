# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound runtime bootstrap. Canonical release version lives in core/bootstrap_economy_professions.py."""
from pathlib import Path
import os
import socket

from core.native_runtime import load_native_runtime

_ROOT = Path(__file__).resolve().parent


def _boot_port() -> int:
    # Keep exactly the same precedence as core/bootstrap_economy_professions.py.
    for key in ("RAILWAY_TCP_APPLICATION_PORT", "PORT", "SOULBOUND_PORT"):
        raw = os.getenv(key, "").strip()
        if raw:
            try:
                value = int(raw)
                if 1 <= value <= 65535:
                    return value
            except ValueError:  # AUDIT_INTENTIONAL_PASS: invalid port value falls through to the next source/default
                pass
    return 4000


# Railway/TCP health must see a listening socket immediately, before the large
# world registry and Generator Core finish loading. asyncio adopts this socket
# later; connections made during boot wait safely in the kernel backlog.
_BOOT_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_BOOT_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
_BOOT_SOCKET.bind((os.getenv("SOULBOUND_HOST", "0.0.0.0"), _boot_port()))
_BOOT_SOCKET.listen(128)
_BOOT_SOCKET.setblocking(False)
print(f"Soulbound bootstrap port open: {_BOOT_SOCKET.getsockname()}", flush=True)

# v0.49.0: runtime catalog writes are routed through controlled ownership while untouched
# historical modules remain behind a measured compatibility bridge.
# The manifest keeps load/override policy explicit and server.py never executes
# project source text into its own globals.
RUNTIME_ARCHITECTURE_STATE = load_native_runtime(_ROOT, globals())

# v1.28.12 authored city network: register AFTER all crypt floor modules,
# before late boot audits / live World() initialization.
from systems.underground_cities_v12812 import register_rewards_v12812, install_cities_v12812
from systems.equipment_crafting import SHOP_SELLERS
register_rewards_v12812(ITEMS)
install_cities_v12812(ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)
from systems.era_awakening_v1300 import install_awakening_v1300
install_awakening_v1300(ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)
from systems.six_eras_v1310 import install_six_eras_v1310
SIX_ERAS_V1310 = install_six_eras_v1310(ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)

# v1.14.3: final runtime mob names are normalized only after every world
# module/generator has registered its templates. This keeps NVDA output short
# and prevents procedural floor numbers / stacked rarity prefixes leaking into
# combat messages.
# v1.50.0 — explicit authored content, layered on top of the COMPLETE historical world.
from systems.forgotten_world_v1500 import install_forgotten_world_v1500
FORGOTTEN_WORLD_V1500 = install_forgotten_world_v1500(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)
from world.world_state import World as _WorldV1500
from systems.echo_dungeon_v1500 import install_echo_dungeon_v1500
ECHO_DUNGEON_V1500 = install_echo_dungeon_v1500(ROOMS, ITEMS, _WorldV1500)

from systems.era_legends_v1600 import install_era_legends_v1600
ERA_LEGENDS_V1600 = install_era_legends_v1600(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)

# v1.70.0 — Sky Kingdoms, 14 profession guild trials and nine authored boss arenas.
from systems.sky_era_v1700 import install_sky_era_v1700
SKY_ERA_V1700 = install_sky_era_v1700(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)

# v1.60.2: final public documentation after both content expansions and old HELP layers.
from systems.help_atlas_v1602 import install_help_atlas_v1602
HELP_ATLAS_V1602 = install_help_atlas_v1602(HELP_TOPICS, HELP_TOPIC_ALIASES)
HELP_TOPICS['niebo'] = [
    'Niebo 1.0: wejście z Kamiennego Mostu Traktatów w GÓRĘ; podniebna przystań i 3 krainy.',
    'niebo bossowie, niebo profesje. Dziewięć walk z bossami; trzy legendarne trony.',
    'Nowi Arcymistrzowie wszystkich 14 profesji dają zadania z realnych czynności.',
]
HELP_TOPICS['chowaniec'] = [
    'chowaniec lista; chowaniec przywolaj pajak / wojownik / mag / lifeoak / ancientoak / wilk / sowa / niedzwiedz.',
    'Nekromanta: zwykłe zęby dla szkieletów pająków; smocze zęby dla szkieletów wojowników i magów.',
    'Nekro wyrwij: poniżej 20% HP wroga można zdobyć Kamień Duszy o kolorze zależnym od siły wroga. Mana jest wymagana; z jednego przeciwnika tylko raz.',
    'chowaniec kamienie: dziewięć kolorów i zapasy. chowaniec ulepsz wojownik <kolor> / mag <kolor>: kolorowe Kamienie Duszy i mana. nekro scal <kolor>: 3 kamienie niższe w 1 wyższy.',
    'Druid: Life Oak, Ancient Oak i zwierzęta. Przywołanie zużywa manę, trzy aktywne stworzenia, automatyczna walka, trwały zapis.',
]
HELP_TOPICS.setdefault('nekro', list(HELP_TOPICS['chowaniec']))
HELP_TOPICS['druid'] = [
    'Druid: Life Oak 80 MP + 2 szyszki; Ancient Oak 180 MP + 5 szyszek. Wilk, Sowa, Niedźwiedź wymagają Pieczęci Chowańców oraz MP.',
    'druid zbierz — szyszki w lesie (odnowienie 90 sekund); druid szyszki — stan zapasów; druid wymien — wymiana starych nasion na szyszki.',
    'chowaniec przywolaj lifeoak / ancientoak / wilk / sowa / niedzwiedz; chowaniec lista — aktualne HP każdego pomocnika.',
    'Każdy pomocnik ma własne HP, otrzymuje obrażenia od wrogów i ginie przy 0 HP. Powrót wymaga ponownego kosztu many i materiałów.',
    'Trzy aktywne przywołania łącznie. Zwierzęta i drzewa walczą automatycznie, a dęby wspierają leczenie.',
]
HELP_TOPICS['fame'] = [
    'fame — tylko: You have no/some/most/all fame in this area. Każdy teren ma osobny wynik, w lochu liczą się wszystkie piętra.',
    'fame log — zaliczone i oczekujące cele terenu. fame log wszystko — historia świata.',
    'Fame przynosi po chwili jednorazowy EXP poziomu, Duszy, Biegłości klasowej i każdej statystyki. Profesje i narzędzia nie dostają EXP.',
    'fame regiony — lista postępów świata; fame none / some / most / all — filtr regionów o danym stopniu ukończenia.',
    'none = 0%, some = 1–49%, most = 50–99%, all = 100% unikalnych celów Fame w terenie.',
    'Pokonani ważni bossowie i oznaczeni przeciwnicy Fame zaliczają się tylko raz, także obecnym członkom drużyny.',
    'Wyniki są trwale zapisane w SQLite. Fame nie blokuje awansów i nie zmienia nagród EXP.',
]

HELP_TOPICS['chowaniec'].extend([
    'Nowość: każda istota ma własne HP, może zostać zniszczona przez atak potwora i nie wskrzesza się po ponownym zalogowaniu.',
    'chowaniec aktywuj <typ>: ponowne wezwanie kosztuje MP; po śmierci także pierwotne materiały. Żywiołaki Maga potrzebują wyłącznie MP.',
    'Mag: mag lista, mag przywolaj <ogien|blyskawice|lod|krysztal> [mniejszy|zwykly|potezny]. Żywiołaki zużywają manę za przywołanie i atak.',
])
HELP_TOPICS['nekro'] = list(HELP_TOPICS['chowaniec'])

HELP_TOPICS['miasto'] = ['miasto zaloz <nazwa> — własna osada; miasto buduj mury / targ / warsztat / lazaret; miasto status.',
    'Mury: osłona; lazaret: leczenie; warsztat: obrażenia przywołań; targ: dochód co 2 godziny przez miasto zbierz. Wejście z przystani niebios.']
HELP_TOPICS['przebudzenie'] = ['Klasy 4.0: przebudzenie ofensywa / obrona / wsparcie.',
    'Jednorazowa ścieżka rozwoju na główną klasę. Bonusy do ataku, osłony albo leczenia w realnej walce.']

from systems.mob_name_cleanup import normalize_runtime_mob_names_v1142, audit_runtime_mob_names_v1142
MOB_NAME_CLEANUP_V1142 = normalize_runtime_mob_names_v1142(MOB_TEMPLATES)
MOB_NAME_AUDIT_V1142 = audit_runtime_mob_names_v1142(MOB_TEMPLATES)
if MOB_NAME_AUDIT_V1142["error_count"]:
    raise RuntimeError("Mob name cleanup audit failed: " + "; ".join(MOB_NAME_AUDIT_V1142["errors"][:100]))

from systems.combat_xp_repair_v11346 import COMBAT_XP_ZERO_AUDIT_V11346
if COMBAT_XP_ZERO_AUDIT_V11346["error_count"]:
    raise RuntimeError("Combat XP zero audit failed: " + "; ".join(COMBAT_XP_ZERO_AUDIT_V11346["errors"]))

# Run the exhaustive gate against the FINAL assembled runtime, after all
# compatibility layers and cumulative milestone guards have finished.
if os.environ.get("SOULBOUND_FULL_AUDIT", "").strip().lower() in ("1", "true", "yes", "on"):
    # Historical v0.33.6 audit is retained as a diagnostic snapshot. It still
    # encodes legacy assumptions (globally unique display names, old split-
    # currency normalization) that are not release-blocking in current Soulbound.
    FULL_GAME_PREDEPLOY_AUDIT_V0336 = full_game_predeploy_audit_v0336()
else:
    FULL_GAME_PREDEPLOY_AUDIT_V0336 = {
        "version": "0.70.0", "skipped_at_runtime": True,
        "error_count": 0, "warning_count": 0, "errors": [], "warnings": [],
        "reason": "Run before deploy with SOULBOUND_FULL_AUDIT=1; skipped during normal server startup.",
    }

# v0.71.5: compact only after the complete runtime and optional full audit are valid.
# predeploy_full can defer this once so it audits the authoring structure first.
if os.environ.get("SOULBOUND_DEFER_MEMORY_COMPACTION", "").strip().lower() in ("1", "true", "yes", "on"):
    RUNTIME_MEMORY_COMPACTION_V0616 = {"version": "0.70.0", "deferred": True}
else:
    RUNTIME_MEMORY_COMPACTION_V0616 = compact_runtime_memory_v0616()
    _memory_post = memory_efficiency_ii_audit_v0616(require_compacted=True)
    if _memory_post["error_count"]:
        raise RuntimeError(
            "Memory Efficiency II post-compaction audit failed: "
            + "; ".join(_memory_post["errors"][:100])
        )
    RUNTIME_MEMORY_COMPACTION_V0616["post_audit"] = _memory_post

if __name__ == "__main__":
    main()
