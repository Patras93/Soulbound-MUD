# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound runtime bootstrap. Canonical release version lives in core/bootstrap_economy_professions.py."""
from systems.runtime_activation import enabled as _sb107_runtime_enabled
from pathlib import Path
import os
import socket
import sys

from core.native_runtime import load_native_runtime

_ROOT = Path(__file__).resolve().parent
# This entrypoint also owns the server namespace package. Register one module
# identity when executed as a script, so ordinary imports of server.mud_server
# never execute the bootstrap a second time.
__path__ = [str(_ROOT / 'server')]
if __name__ == '__main__':
    sys.modules.setdefault('server', sys.modules[__name__])

# This entrypoint belongs to the current release only. It never imports an
# earlier release's activation or staging implementation.
from systems.runtime_activation import authorized_mode
authorized_mode(os.getenv('SOULBOUND_DB', str(_ROOT / 'soulbound.db')))


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
from core.runtime_transport import register_boot_socket
register_boot_socket(_BOOT_SOCKET)
print(f"Soulbound bootstrap port open: {_BOOT_SOCKET.getsockname()}", flush=True)

# v0.49.0: runtime catalog writes are routed through controlled ownership while untouched
# historical modules remain behind a measured compatibility bridge.
# The manifest keeps load/override policy explicit and server.py never executes
# project source text into its own globals.
RUNTIME_ARCHITECTURE_STATE = load_native_runtime(_ROOT, globals())


# v39: Historical legacy modules still export older LATEST_CHANGES_TITLE and
# overwrite the first release title during compatibility assembly. Restore the
# canonical release identity *after* assembly, without re-executing catalogs or
# modifying gameplay. Keep prior NEWS entries accessible in this session.

# v40 Guardian 6.0 release identity. No catalog reload and no changes to quest XP engine.

# v41 Guardian 7.0: private source-rule arena and atomic quest repair DRAFT.
# No grant, real HP, real mob or live world-state changes from arena commands.

# v42 Guardian 8.0: pure-source rehearsal and atomic quest DRAFT batches.

# v43 Guardian 9.0: reversible isolated arena simulations and OLC review.

# v44 Guardian 10: per-arena RNG, reproducible snapshots and scenario comparisons.

# v45: isolated skill and test-equipment experiments. No live XP/combat changes.

# v46: next generation of the existing admin live workflow; never auto-deploy.

# v47: release readiness and unified, read-only admin live commands.

# v48 release identity; retains v47 release news for changelog history.

# v49: release identity for conservative quest and LAB integrity tools.

# v50: unified admin live with owner-confirmed DRAFT fixes and full dependency scan.

# v51: canonical multi-field quest DRAFT and isolated 22-class comparison.


# v54: one Admin Live inspection dashboard, without changes to real combat/EXP.

# v55: actual progressive crafting above 800 with persistent item-ID restore.

# v56: scale ordinary equipment from authored infinite mobs AFTER a normal roll.

# v53 owner-configurable gear requirements for truly deep-world EQ.
# v57: real infinite boss chest payout beyond the historical 800 plateau.

# v58: real high-floor boss chest bonus EQ and quest item-ID diagnostics.


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
# v2.10.0 additive side chambers over the final runtime dungeon registry.
from systems.titans_v2100 import install_titans_v2100
TITANS_V2100 = install_titans_v2100(ROOMS, ITEMS, _WorldV1500)

from systems.era_legends_v1600 import install_era_legends_v1600
ERA_LEGENDS_V1600 = install_era_legends_v1600(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)

# v1.70.0 — Sky Kingdoms, 14 profession guild trials and nine authored boss arenas.
from systems.sky_era_v1700 import install_sky_era_v1700
SKY_ERA_V1700 = install_sky_era_v1700(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)

# v1.80.0 — additive Chaos God arenas and class mastery catalogue.
from systems.era_chaos_v1800 import install_chaos_v1800
CHAOS_ERA_V1800 = install_chaos_v1800(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)

# v1.90.0 — authored Underground Kingdoms, Chaos dimensions and forge artifacts.
from systems.underground_kingdoms_v1900 import install_underground_kingdoms_v1900
from data.crafting_recipes import CRAFT_RECIPES
UNDERGROUND_V1900 = install_underground_kingdoms_v1900(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    SHOP_SELLERS, CRAFT_RECIPES)


# v2.00.0 - four linked worlds, islands and real PvE arenas; additive IDs only.
from systems.parallel_worlds_v2000 import install_parallel_worlds_v2000
PARALLEL_WORLDS_V2000 = install_parallel_worlds_v2000(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS)
from systems import ocean4_v1350 as _ocean5
# v2.20.0: four connected, authored deep-ocean routes and fleet encounters.
from systems.ocean_depths_v2200 import install as _install_ocean_depths_v2200
OCEAN_DEPTHS_V2200 = _install_ocean_depths_v2200(
    ROOMS, NPCS, SHOPS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS, SHOP_SELLERS, _ocean5)
from systems.mastery_crafting_v2201 import install as _install_mastery_craft_v2201
MASTERY_RECIPES_V2201 = _install_mastery_craft_v2201(ITEMS)
from systems.ocean_sagas_v2300 import install as _install_ocean_sagas_v2300
OCEAN_SAGAS_V2300 = _install_ocean_sagas_v2300(ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, _ocean5)

# v3.10.0: install the eight legendary realms AFTER all old authored roads.
# Never overwrite previous routes, NPCs, quests, data or player progress.
from world.legends_v3100 import install as _install_legends_v3100
V3100_LEGENDS_STATS = _install_legends_v3100(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES,
)
# v3.20.0: seven linked expansions across both old and new worlds.
from world.legends_v3200 import install as _install_legends_v3200
V3200_LEGENDS_STATS = _install_legends_v3200(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES,
)
# v3.31.3: expand action-backed low-level tasks for every profession and
# the sparse tailoring/leatherworking/carpentry/enchanting quest paths.
# Register BEFORE single-NPC isolation; no new NPCs or locations are needed.
from systems.profession_apprenticeship_v3313 import install as _install_professions_v3313
V3313_PROFESSION_STATS = _install_professions_v3313(QUESTS, NPCS)

# v4.00.0: five linked systems — old-world story, ocean fleets, ancient bosses,
# 14 existing professions and real craft recipes. No new tools or SQLite reset.
from world.imperium_v4000 import install as _install_imperium_v4000
V4000_IMPERIUM_STATS = _install_imperium_v4000(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES, _ocean5,
)

# v5.00.0: additive quest, boss, ocean, dungeon and profession expansion.
from world.war_of_gods_v5000 import install as _install_war_of_gods_v5000
V5000_WAR_OF_GODS = _install_war_of_gods_v5000(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES,
)

# v6.00.1: eight 120-stage action-backed paths and private reachable mentors.
# Register before NPC isolation and before final exploration map refresh.
from systems.profession_paths_v601 import install as _install_profession_paths_v601
V601_PROFESSION_PATHS = _install_profession_paths_v601(ROOMS, NPCS, QUESTS, ITEMS)
# v11.00.4: Kupczyni Selma sells Waga Kupiecka; bounty board lives in the Guild Hall.
from systems.merchant_guild_board_v1104 import install as _install_merchant_board_v1104
V1104_MERCHANT_BOARD = _install_merchant_board_v1104(
    ROOMS, NPCS, SHOPS, SHOP_SELLERS, ITEMS, HELP_TOPICS, HELP_TOPIC_ALIASES)

# v7.00.0: real world-connected story, industry and commerce, no old IDs reused.
from systems.living_empire_v7000 import install as _install_living_empire_v7000
V700_LIVING_EMPIRE = _install_living_empire_v7000(ROOMS, NPCS, QUESTS, ITEMS, HELP_TOPICS)

# v8.00.0: 14 full 120-stage class sagas, solo-class gates and private mentors.
from systems.class_legend_paths_v800 import install as _install_class_legend_paths_v800
V800_CLASS_LEGEND_PATHS = _install_class_legend_paths_v800(ROOMS, NPCS, QUESTS, ITEMS, HELP_TOPICS)

# v9.00.0: 8 new class legends and eight private class teachers.
from systems.class_legend_paths_v900 import install as _install_class_legend_paths_v900
V900_CLASS_LEGENDS = _install_class_legend_paths_v900(ROOMS, NPCS, QUESTS, ITEMS, HELP_TOPICS)

# v10.00.0: additional authored territories, per-room EP pools and real mapping.
from systems.forgotten_horizons_v1000 import install as _install_horizons_v1000
V1000_FORGOTTEN_HORIZONS = _install_horizons_v1000(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES)

# v11.00.0: new nonurban territories; catalog-only install, no resets.
from systems.eternal_glory.world import install as _install_eternal_glory_v1100
V1100_ETERNAL_GLORY = _install_eternal_glory_v1100(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES)

# v11 dungeon chapters and extra boss Fame objectives, no legacy floor changes.
from systems.eternal_glory.depths import install as _install_glory_depths_v1100
V1100_GLORY_DEPTHS = _install_glory_depths_v1100(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES)

from systems.eternal_glory.crafting import install as _install_glory_crafts_v1100
V1100_GLORY_CRAFTS = _install_glory_crafts_v1100(
    ITEMS, QUESTS, NPCS, CRAFT_RECIPES, HELP_TOPICS)

from systems.eternal_glory.class_guild import install as _install_class_guild_v1100
V1100_CLASS_GUILD = _install_class_guild_v1100(NPCS, QUESTS, HELP_TOPICS)

from systems.eternal_glory.story import install as _install_glory_story_v1100
V1100_STORY = _install_glory_story_v1100(NPCS, QUESTS, ITEMS, HELP_TOPICS, HELP_TOPIC_ALIASES)

# v11 truly endless floors and durable personal party checkpoint portals.
from systems.eternal_glory.infinite import install as _install_infinite_v1100
from player.session import Session as _SessionV1100
V1100_INFINITE = _install_infinite_v1100(
    ROOMS, MOB_TEMPLATES, MOB_SPAWNS, HELP_TOPICS, HELP_TOPIC_ALIASES,
    _WorldV1500, _SessionV1100)

# v11 Ocean: four actual new PvE targets in the established fleet battle engine.
for _key,_enemy_name,_health,_damage,_reward,_kind,_threat,_relic in (
    ('v1100_navy_reef','Flota Żelaznej Rafy',7100000,130000,1700000,'siege',800000,'v1100_eg_szept_relic'),
    ('v1100_navy_maelstrom','Lewiatan Wielkiego Wiru',9200000,165000,2300000,'monster',1150000,'v1100_eg_otchlan_relic'),
    ('v1100_navy_storm','Armada Wiecznego Gromu',11800000,210000,2950000,'siege',1450000,'v1100_eg_burza_relic'),
    ('v1100_navy_abyss','Król Bezgłośnej Otchłani',17000000,280000,4200000,'monster',1900000,'v1100_eg_mrok_relic'),
):
    if _key in _ocean5.ENEMIES or _relic not in ITEMS:
        raise RuntimeError('v11 Ocean: invalid fleet encounter or missing reward')
    _ocean5.ENEMIES[_key]=(_enemy_name,_health,_damage,_reward,_kind,_threat)
    _ocean5.MATERIALS[_key]=_relic
HELP_TOPICS['ocean11'] = [
    'Ocean 7.0: cztery dodatkowe starcia floty w istniejącym systemie Ocean4.',
    'ocean4 atak v1100_navy_reef / v1100_navy_maelstrom / v1100_navy_storm / v1100_navy_abyss.',
    'Wymagane prawdziwe statki, dostępne manewry i dotychczasowy zapis walk w SQLite.',
]

# Exploration's lookup was built earlier by the native runtime; refresh it once
# after the new rooms have been safely installed.
from world.generation_systems import v0130_refresh_exploration_catalog as _v3100_ep_refresh
_v3100_ep_refresh()


for _code,_name,_hp,_damage,_reward,_kind,_threat in (
    ('perlowaflota','Flota Perłowych Sztormów',2500000,50000,490000,'siege',240000),
    ('czarnaarmada','Czarna Armada Głębin',3900000,71000,750000,'siege',360000),
    ('sztormowcy','Władcy Błyskawicznych Mórz',5200000,94000,1050000,'monster',490000),
):
    if _code in _ocean5.ENEMIES:raise RuntimeError('Ocean 5.0 collision: '+_code)
    _ocean5.ENEMIES[_code]=(_name,_hp,_damage,_reward,_kind,_threat)
    _ocean5.MATERIALS[_code]='soul_shard'

# Keep the public class topic consistent with the actual 22 playable classes.
HELP_TOPICS['klasy'] = [
    'Soulbound ma 22 grywalne klasy. Każda ma osobną Biegłość 1–800, umiejętności i zadania gildyjne.',
    'Nowe klasy: Paladyn, Samuraj, Korsarz, Gladiator, Chronomanta, Iluzjonista, Bard i Szaman.',
    'classguild / guildquest — zadania gildyjne; Droga Legendy u Mistrza Drogi Legendy obejmuje 120 etapów dla każdej klasy.',
    'multiclass — odblokowane i aktywne klasy; help multiclass — zasady wielu klas.',
]

# v11.00.3: every playable profession and caravan needs a direct HELP
# entry. Names and actions come from the actual runtime mechanics.
from systems.new_professions import PROFESSIONS as _HELP_V1103_PROFESSIONS, BASE_ACTIONS as _HELP_V1103_ACTIONS
from storage.db_shared import normalize_lookup_text as _v1103_help_normalize
for _help_profession, (_help_tool_type, _help_tool_id, _help_tool_name) in _HELP_V1103_PROFESSIONS.items():
    _help_key = _v1103_help_normalize(_help_profession).replace(" ", "_")
    _help_rows = [
        f"{_help_profession} — profesja i {_help_tool_name}, poziomy 1–800.",
        f"Krótko: profesja status {_help_profession}; profesja kup {_help_profession}; pracuj {_help_profession} <czynność>.",
        f"profesja kup {_help_profession} — narzędzie za 1200 srebra, tylko raz na postać. Kupno u mistrza profesji, na targu, w porcie lub kuźni.",
        f"profesja status {_help_profession}; profesja czynnosci {_help_profession} — poziom i lista rzeczywistych czynności.",
    ]
    for _help_action in _HELP_V1103_ACTIONS:
        if _help_action.prof == _help_profession:
            _help_rows.append(
                f"profesja praca {_help_profession} {_help_action.code} [próg] — {_help_action.title}. "
                f"Teren: {_help_action.region}; poziom od {_help_action.min_level}."
            )
    _help_rows.append(f"profesja zamowienie {_help_profession}; profesja oddaj {_help_profession} — zamówienia.")
    _help_rows.append("Progi rozwoju: 1, 25, 75, 150, 300, 500, 700. Zadania: Droga Mistrza u odpowiedniego mistrza profesji.")
    HELP_TOPICS[_help_key] = _help_rows
    HELP_TOPIC_ALIASES[_help_key.replace("_", "")] = _help_key
    HELP_TOPIC_ALIASES[_help_tool_type] = _help_key
HELP_TOPIC_ALIASES.update({
    "hodowla": "hodowla_zwierzat", "zwierzeta": "hodowla_zwierzat",
    "handel": "kupiectwo", "kupiec": "kupiectwo", "kupcy": "kupiectwo",
    "lowiectwo": "lowiectwo", "lowy": "lowiectwo",
    "okrety": "okretownictwo", "inzynier": "inzynieria",
    "karawany": "karawana", "karavan": "karawana",
})
HELP_TOPICS['karawana'] = [
    'Kupiectwo i karawany Imperium 7.0: rozpoczęcie na rynku, dostawa i odbiór nagród.',
    'Krótko: karawana lista; karawana start rynek; karawana odbierz.',
    'imperium7 karawana lista — dostępne trasy, wymagania Kupiectwa i rzeczywiste zapasy.',
    'imperium7 karawana start <rynek|port|kuźnia|targ> — wyrusz karawaną z rynku.',
    'imperium7 karawana odbierz — odbierz ukończony transport; wcześniej nie rozpoczniesz następnego.',
    'Wymagane posiadana Waga Kupiecka, poziom Kupiectwa i materiały na wybraną trasę.',
    'To inny mechanizm niż profesja praca Kupiectwo wyslij/dostarcz.',
]
HELP_TOPIC_ALIASES['handlowanie'] = 'kupiectwo'

# v1.60.2: final public documentation after both content expansions and old HELP layers.
from systems.help_atlas_v1602 import install_help_atlas_v1602
HELP_ATLAS_V1602 = install_help_atlas_v1602(HELP_TOPICS, HELP_TOPIC_ALIASES, TOOL_PROFESSION_MAP)
HELP_TOPICS['mistrzprof'] = [
    'Mistrzowie Świata 6.0: mistrzprof lista/status <profesja>/wybierz <profesja> <1..3>. Specjalizacje na poziomach 100, 250, 450.',
    'mistrzprof zamowienie / odbierz / porzuc <profesja>; mistrzprof receptury / wykonaj <profesja>. Wyrób wymaga surowców Oceanu 5.0 i pierwszej specjalizacji.',
    'Nagroda to wysokie srebro (przeliczane na złoto). Specjalizacje zwiększają wypłatę kontraktu; EXP profesji i narzędzi oraz obecne zamówienia bez zmian.',
]
HELP_TOPICS['legendy5'] = ['Ocean 5.1: Skarbiec Milczących Wód z Rowu Lewiatana; Nawa Potępionych Żagli z Archipelagu Wiecznych Burz.', 'W Porcie Nieznanych Mórz przejdź północny wschód do Głębin. W nowych regionach są bossowie, kontrakty i bitwy: ocean4 atak legenda_cisza / legenda_nawa.']
HELP_TOPICS['glebiny5'] = [
    'Ocean 5.0 Głębie Lewiatana: z Portu Nieznanych Mórz północny wschód, potem cztery drogi do osobnych krain.',
    'Rów Lewiatana, Zatopiona Stolica, Rafy Szeptów i Archipelag Wiecznych Burz mają NPC, zadania i bossów.',
    'Ocean4 cele / ocean4 atak glebiny_row, glebiny_stolica, glebiny_rafy, glebiny_burze; pełny zapis bitew w istniejącym SQLite.',
]
HELP_TOPICS["tytani"] = ["tytani lista/info/status/obrona — 8 Tytanow na glebokosci 50, 100, 150 i dalej co 50 pieter. Zawsze opcjonalne.","Tytani maja cztery fazy i zapowiadane potezne ataki; tytani obrona zmniejsza zapowiedziany cios. Powrot: poludnie lub wyjscie.","Pierwsza wygrana daje legendarny artefakt. Premia Esencji powtarza sie po 24 h. Nagrody postaci/druzyny z EXP Banku zachowane."]
HELP_TOPICS["lochy7"] = ["lochy7 — dodatkowe odnogi co 25 pieter bez pulapek. Co 50 legowisko Tytana, na pozostalych progach 25 sekretna komnata.","W sekretnej komnacie wpisz lochy7 sekret. Nagroda osobista jednokrotna, zapis w SQLite. Wyjscie: poludnie lub wyjscie."]
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
    'Odwołanie zwierząt: call odwolaj <nazwa|wszystkie> lub chowaniec odwolaj <nazwa|wszystkie>. Nie usuwa poziomów i ulepszeń.',
]
HELP_TOPICS.setdefault('nekro', list(HELP_TOPICS['chowaniec']))
HELP_TOPICS['druid'] = [
    'call list — zwierzęta bieżącego terenu, w tym rzadkie (od poziomu 100) i legendarne (od 300); call <nazwa> przywołuje za manę bez Pieczęci Chowańców.',
    'call squirrel / call wiewiorka — tylko lasy i łąki; wiewiórka rzuca 2–4 szyszki i ucieka; 20 MP, odnowienie 90 s.',
    'Life Oak: 2 szyszki i 80 MP. Ancient Oak: 5 szyszek i 180 MP. Wpisz chowaniec przywolaj lifeoak/ancientoak.',
    'order <zwierze|all> atakuj|bron|wspieraj|czekaj — kierowanie zachowaniem żywych zwierząt w walce.',
    'druid szyszki — stan materiałów; druid wymien — wymiana starych nasion; druid zbierz wskazuje wiewiórkę.',
    'Każdy przywołany pomocnik ma HP, może zginąć i wymaga ponownego przywołania po zalogowaniu; limit trzech aktywnych.',
]
HELP_TOPICS['call'] = list(HELP_TOPICS['druid'])
HELP_TOPICS['order'] = list(HELP_TOPICS['druid'])
HELP_TOPICS['fame'] = [
    'fame — liczba zdobytych punktów Fame na całym świecie i stan celów z aktualnego katalogu.',
    'where fame / gdzie fame — status Fame bieżącego terenu: You have no/some/most/all fame in this area.',
    'none 0%, some 1–49%, most 50–99%, all 100%. Loch sumuje wszystkie piętra.',
    'fame log — zapis zabitych celów terenu; fame log wszystko — cały świat.',
    'fame cele / fame braki — cele obecnego terenu i to, co jeszcze pozostało.',
    'fame regiony — wszystkie tereny; fame none/some/most/all — filtr według stanu ukończenia.',
    'Fame jest zaliczana od razu do SQLite po pierwszym zabiciu; jedynie premia EXP może nadejść później.',
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

HELP_TOPICS['bogowie'] = [
 'Bogowie Chaosu: 4 krainy i 12 bossów; droga z Targu Osad Założycieli na zachód.',
 'Na HP 75%, 50%, 25% nowa faza walki zwiększa odporność bossa na ataki przywołań.',
 'Kronikarze mają prawdziwe odnawialne polowania. Komenda: bogowie.'
]
HELP_TOPICS['taktyka'] = [
 'Przywołania 5.0: taktyka szturm / bastion / harmonia. Formacja jest zapisana w SQLite.',
 'Szturm podnosi atak chowańców o 8%, bastion daje osłonę i obniża atak o 6%, harmonia wspiera odzyskiwanie HP.',
 'Ustalenie formacji nie usuwa starych rozkazów order ani poziomów pomocników.'
]
HELP_TOPICS['mistrzostwo'] = [
 'Klasy 5.0: mistrzostwo — nazwa umiejętności obecnej klasy. mistrzostwo uzyj — wykonanie.',
 'Od poziomu postaci 150, odnowienie 45 sekund, klasy magiczne koszt 110 MP.',
 'Wojownicy ofensywni atakują wskazany cel; Strażnik, Mec i Inżynier dają osłonę; Kapłan i Druid leczą.',
 'Wybrana wcześniej ścieżka przebudzenia pozostaje bez zmian.'
]
HELP_TOPICS['reakcje'] = [
 'Magia Żywiołów 3.0: kolejne różne żywioły przywołań trafiające ten sam cel mogą wywołać reakcję.',
 'Ogień + lód, lód + błyskawice, ogień + błyskawice, mrok + światło i inne pary.',
 'Reakcje mają niewielkie dodatkowe obrażenia (do 10% trafienia), odnowienie 8 s i nie nadpisują dawnych szkół magii.'
]


HELP_TOPICS['wymiary'] = [
 'wymiary — 4 krainy: Sny, Smoki, Duchy, Pustka. Z Wymiarów Chaosu w GÓRĘ.',
 'wymiary droga — najbliższy kierunek do Węzła Światów. Nie ma blokady poziomu ani pułapek.',
 'Każda kraina ma 18 pomieszczeń, cel Fame, 3 polowania, bossa i dwukierunkowe wyjścia.'
]
HELP_TOPICS['ocean5'] = [
 'ocean5 — trzy nowe archipelagi i dostęp do Portu Nieznanych Mórz z Węzła Światów w GÓRĘ.',
 'ocean4 cele / ocean4 atak <kod> — nowe i dotychczasowe bitwy flot. Istniejące statki pozostają.'
]
HELP_TOPICS['frakcje'] = [
 'frakcje lista/status; frakcje kontrakt <kod>; frakcje odbierz <kod>.',
 'Reputacja osobna dla siedmiu pokojowych frakcji. Kontrakt trwa do prawdziwego zabicia celu, solo lub w drużynie. Odnowienie 1 h.'
]
HELP_TOPICS['arena'] = [
 'arena lista; arena podejmij <kod>; arena status; arena odbierz <kod>.',
 'Hala Areny Legend z Portu Nieznanych Mórz w GÓRĘ. Cztery prawdziwe walki PvE, bez obowiązkowego PvP. Odnowienie 90 min.'
]

HELP_TOPICS['podziemia'] = [
    'Podziemne Królestwa: z Rozdroża Bogów Chaosu zejdź w DÓŁ do Bramy.',
    'PÓŁNOC: Królestwo Miedzianych Ech. WSCHÓD: Dwór Zarodnikowych Królów. POŁUDNIE: Obsydianowe Imperium.',
    'ZACHÓD: Wymiary Chaosu; trzy wyraźnie opisane ścieżki i walki z bossami.',
    'podziemia — przewodnik po krainach. Nie ma losowych pułapek ani nowej blokady poziomu.',
]
HELP_TOPICS['taktyka'].append(
    'Przywołania 6.0: taktyka auto — bez własnego EXP; AI dobiera szturm, bastion albo harmonię '
    'na podstawie HP właściciela i klasy wroga.')
HELP_TOPICS['fame'].append(
    'Fame 3.0: fame bestiariusz [strona] — odkryte gatunki i ukryte cele bieżącego terenu. '
    'Stare punkty pozostają w SQLite; katalog starszych krain rozszerzono do maksymalnie 30 naturalnych celów.')
HELP_TOPICS['reakcje'].append(
    'Magia Żywiołów 4.0: także woda + błyskawice, woda + lód, trucizna + lód i inne reakcje '
    'z ograniczeniem czasu, bez nieskończonego blokowania bossów.')

# v3.10.1: give each NPC a private, bidirectionally connected room AFTER all
# historical/new content is registered. No existing route is overwritten.
from systems.npc_single_room_v3101 import install as _install_single_npc_v3101
SINGLE_NPC_ROOMS_V3101 = _install_single_npc_v3101(ROOMS, NPCS, SHOP_SELLERS)
# All added annexes must also be visible to Exploration Points.
_v3100_ep_refresh()

# v12.00.1: 2 separate, first-kill-only champion encounters in each
# existing combat region; ordinary mobs still never yield Fame.
from systems.world_fame_v1201 import install as _install_world_fame_v1201
V1201_WORLD_FAME = _install_world_fame_v1201(ROOMS, MOB_TEMPLATES, MOB_SPAWNS, HELP_TOPICS)

from systems.mob_name_cleanup import normalize_runtime_mob_names_v1142, audit_runtime_mob_names_v1142
MOB_NAME_CLEANUP_V1142 = normalize_runtime_mob_names_v1142(MOB_TEMPLATES)
MOB_NAME_AUDIT_V1142 = audit_runtime_mob_names_v1142(MOB_TEMPLATES)
if MOB_NAME_AUDIT_V1142["error_count"]:
    raise RuntimeError("Mob name cleanup audit failed: " + "; ".join(MOB_NAME_AUDIT_V1142["errors"][:100]))

# v6.00: additive use for farm/hunting goods in established professions.
from systems.new_professions import install_legacy_profession_recipes as _v600_install_recipes
from systems.equipment_crafting import COOK_RECIPES as _v600_cook_recipes
V600_OLD_PROFESSION_INTEGRATION = _v600_install_recipes(ITEMS, _v600_cook_recipes, CRAFT_RECIPES)
# v11.00.6: short, natural commands shown first; older aliases still work.
# v11.00.7: global, human-readable help for legacy numbered command handlers.
_VERSIONLESS_HELP_V1107 = {
    'sekretylochu': ('lochy7', 'Sekretne odnogi i nagrody co 25 pięter. Wpisz sekretylochu lub sekretylochu sekret w sekretnej komnacie.'),
    'zapomnianelochy': ('lochy50', 'Zapomniane lochy kontynentu. Wpisz zapomnianelochy, aby zobaczyć dostępne opcje.'),
    'era': ('era60', 'Wielka Saga i wydarzenia Ery Legend. Wpisz era, aby sprawdzić opcje.'),
    'morza': ('ocean5', 'Nowe oceany i wyprawy. Wpisz morza, aby sprawdzić rejsy i regiony.'),
    'flota': ('ocean4', 'Floty i bitwy na morzu. Wpisz flota, aby sprawdzić dostępne polecenia.'),
    'handelimperium': ('handel4', 'Handel i gospodarka. Wpisz handelimperium, aby sprawdzić zlecenia i transakcje.'),
    'kodekskolekcji': ('collection2', 'Kodeks kolekcji i nagród. Wpisz kodekskolekcji, aby zobaczyć postęp.'),
    'nawigacja': ('navigation2', 'Nawigacja głosowa i wskazówki drogi. Wpisz nawigacja status, nawigacja cel <nazwa>.'),
    'kariera': ('career2', 'Kariera bohatera: kariera status, kariera walka, kariera profesje.'),
    'cenyrynkowe': ('marketquotes1260', 'Notowania rynkowe: cenyrynkowe — aktualne zestawienie.'),
    'wielkawyprawa': ('grandex1260', 'Wielka ekspedycja: wielkawyprawa — dostępne cele i nagrody.'),
    'legendarnewyprawy': ('legendaryexpeditions1210', 'Legendarne ekspedycje: legendarnewyprawy — lista i postęp.'),
    'mistrzowieprofesji': ('mistrzprof', 'Mistrzowie profesji: mistrzowieprofesji — wskazówki rozwoju i zadania.'),
    'łowcy': ('hunters1225', 'Tablica łowców: łowcy — oferty i status.'),
    'zawody': ('profesje6', 'Profesje: zawody lista; zawody kup Kupiectwo; pracuj Kupiectwo pakuj.'),
    'żyweimperium': ('imperium7', 'Żywe Imperium: karawana lista, łowy lista, wyprawa lista, rozbudowa status.'),
    'mistrzostworzemiosla': ('craftmastery', 'Mistrzostwo rzemiosła: mistrzostworzemiosla — poziomy i bonusy.'),
    'zadaniaklasowe': ('guildquest', 'Zadania klasowe: zadaniaklasowe — cele i postęp danej klasy.'),
    'egzaminklasowy': ('guildexam', 'Egzaminy klasowe: egzaminklasowy — wymagania i status.'),
    'zleceniagildii': ('guildbounty', 'Gildyjne zlecenia: zleceniagildii — lista, postęp i nagrody.'),
    'gildiaklasowa': ('classguild', 'Gildia klasowa: gildiaklasowa — postęp, próby i oferty.'),
}
for _shortcut_v1107, (_old_v1107, _description_v1107) in _VERSIONLESS_HELP_V1107.items():
    HELP_TOPICS[_shortcut_v1107] = [_description_v1107, 'Stara komenda ' + _old_v1107 + ' nadal działa.']
    HELP_TOPIC_ALIASES[_old_v1107] = _shortcut_v1107
    HELP_TOPIC_ALIASES[_shortcut_v1107.replace('ł','l').replace('ż','z')] = _shortcut_v1107
HELP_TOPICS['globalne komendy'] = [
    'Lochy: sekretylochu, zapomnianelochy; oceany: morza, flota; przygody: era, wielkawyprawa, legendarnewyprawy.',
    'Rzemiosło: profesja, pracuj <profesja> <czynność>, kupiectwo; handel: handelimperium, cenyrynkowe, karawana.',
    'Postać: kariera, nawigacja, kodekskolekcji, gildiaklasowa, zadaniaklasowe, egzaminklasowy, zleceniagildii.',
    'Mistrzowie: mistrzowieprofesji; łowcy: lowcy. Wszystkie starsze polecenia z numerami pozostają zgodne.',
    'help / pomoc: lista tematów. help <temat>: opis. help skill <nazwa>: opis umiejętności, bez jej wykonania.'
]
HELP_TOPIC_ALIASES['komendykrotkie'] = 'globalne komendy'

# v11.00.8: sawmill recipes belong to forestry, not forging.
HELP_TOPICS['obrabiaj'] = [
    'Deski obrabiasz w Obozie Drwala, korzystając z Piły. Praca rozwija Drwalstwo oraz Piłę, NIE Kowalstwo.',
    'Komendy: obrabiaj lista; obrabiaj deska dębowa; obrabiaj max deska dębowa; receptury drwalstwo.',
    'Gotowe deski trafiają do Szkatułki Rzemieślniczej i nadal służą do budowy oraz Stolarstwa.',
]
HELP_TOPIC_ALIASES['deski'] = 'obrabiaj'
HELP_TOPIC_ALIASES['drwalnictwo'] = 'drwalstwo'
HELP_TOPICS['drwalstwo'] = list(HELP_TOPICS.get('drwalstwo', [])) + HELP_TOPICS['obrabiaj']

HELP_TOPICS["proste komendy"] = [
    "Nowe profesje: profesje lista; profesja kup Kupiectwo; profesja czynnosci Kupiectwo; pracuj Kupiectwo pakuj.",
    "Wszystkie systemy: help globalne komendy; główna pomoc: help; opis skilla: help skill <nazwa>.",
    "Jeszcze krócej: kupiectwo kup, kupiectwo czynnosci, kupiectwo pakuj, kupiectwo zamowienie, kupiectwo oddaj.",
    "Karawany: karawana lista, karawana start rynek, karawana odbierz. Imperium: rozbudowa status, rozbudowa koszt pole.",
    "Łowy: lowy lista/start/odbierz. Wyprawy: wyprawa lista/start/odbierz. Stare komendy z cyframi nadal działają.",
]
HELP_TOPIC_ALIASES["komendyprofesji"] = "proste komendy"
HELP_TOPICS["profesje6"] = ["Nowe profesje: Łowiectwo, Rolnictwo, Hodowla zwierząt, Okrętownictwo, Murarstwo, Inżynieria, Kupiectwo, Żeglarstwo.", "Wpisz zawody lista; profesja kup <nazwa>; profesja czynnosci <nazwa>; pracuj <nazwa> <czynność> [próg]; profesja zamowienie <nazwa>; profesja oddaj <nazwa>.", "Siedem progów: 1, 25, 75, 150, 300, 500, 700. Każde narzędzie można kupić tylko raz na postać; poziomy 1–800."]
HELP_TOPICS["profesje6"].append("Droga Mistrza 6.00.1: 120 questów na każdą z ośmiu nowych profesji, po kolei od 1 do 800; u nowych mistrzów wpisz quest list, przyjmij 1, oddaj quest 1. Liczą się tylko wskazane czynności i progi pracy.")
HELP_TOPICS["profesje"] = ["Soulbound ma 22 profesje i 22 narzędzia, wszystkie z poziomami 1–800.", "Osiem nowych profesji: Łowiectwo, Rolnictwo, Hodowla zwierząt, Okrętownictwo, Murarstwo, Inżynieria, Kupiectwo, Żeglarstwo.", "Komendy nowych: profesje lista, profesja czynnosci <nazwa>, pracuj <nazwa> <czynność> [próg].", "Stare 14 profesji, ich materiały, zadania i narzędzia działają nadal."] + [line for line in HELP_TOPICS.get("profesje",[]) if "1-600" not in line and "8 profesji" not in line]

from systems.combat_xp_repair_v11346 import COMBAT_XP_ZERO_AUDIT_V11346
if COMBAT_XP_ZERO_AUDIT_V11346["error_count"]:
    raise RuntimeError("Combat XP zero audit failed: " + "; ".join(COMBAT_XP_ZERO_AUDIT_V11346["errors"]))


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

# v102.00.12: reapply persisted Admin Live caps at each startup for all
# releases from v52 onwards. A hand-maintained VERSION allowlist ended at
# v97.00.0, inadvertently restoring default 800 for later builds.
# Keep this AFTER native imports and authoring audits (baseline 800 required).
# File LIVE_CONTENT/admin_level_caps.json is protected by the ZIP updater.
if tuple(int(piece) for piece in VERSION.split('.')) >= (52, 0, 0):
    try:
        from core.live_level_caps_v5200 import load as _load_caps_v5200
        _load_caps_v5200()
    except (ValueError, OSError) as _caps_load_error_v5200:
        print('UWAGA admin live limity: odczyt ustawien nie powiodl sie: '
              + str(_caps_load_error_v5200), flush=True)

# v59 release title after legacy runtime assembly, no content reload.

# v60 canonical title; no re-import of runtime catalogues or game state.

# v61: canonical release title. Legacy command dispatch stays unchanged.

# v62 canonical release title. Older dispatchers remain as aliases.

# v63 release title; all earlier Admin Live commands preserved.

# v64 release title: all earlier Admin Live commands remain intact.

# v65: pass real UOSS status/equipment rules to detached Admin Live LAB only.

# v66: source helper choice inspection, never live combat.

# v67: helper support in source balance, detached arena, never live combat.

# v68: production UOSS helper party target selection, isolated laboratory.

# v69: Admin Live centrum komend NVDA; no live combat or EXP mutation.

# v70: Admin Live odbior wydania i bramki PREDEPLOY; no live combat or EXP mutation.

# v70.00.2: Admin Live test tools and deterministic DRAFT corrections.

# v70.00.3: cap-adaptive editor, owner-opt-in scalable shop offers and diagnostics.

# v72: this release is a strictly administrative extension, no combat rewards.

# v73: atomic OLC drafts only; UOSS catalog report is read-only.





# v74: correct the runtime release identity and expose new Admin Live help.


# v75: native UOSS mechanics and legacy prerequisite removal.


# v76: persistent, playable new races with authored inherited passives.


# v77: playable additional class archetypes, independent class skill IDs,
# compatible trainers, passive stats, and Soul Weapon trait inheritance.

# v78: detached actor uses actual production player_damage for basic attacks.

# v82: production and detached LAB now select the same auto-queue skill.
# This release does NOT enable side-effecting skill casts within the LAB.


# v83: safe, limited actual direct-skill cast, never world-side use_class_skill.

# v84: actual game runtime isolation (separate process, private DB, loopback-only).
# Deliberately NOT an in-session complete Guardian combat engine.

# v85: native engine TCP E2E and strict isolation safety release.

# v86: native full-engine arena lifecycle exposed within the existing admin live.

# v87: atomic quest + scripted UOSS multi-entity OLC and fresh native arena.

# v88: one atomic, cross-domain plan in the existing Admin Live panel.

# v89: read-only production publication gate and NVDA-readable global diff.

# v90: real durable revision recovery and conflict-safe publication.

# v91: complete tested archetype inheritance and atomic stale prerequisite repair.


# v92: one atomic multi-domain quest repair release.

# v93: combined quest repair and safe two-effect authored attack skills.

# v94: one substantive update spanning final-state quest fixes, deterministic
# counter repair and batch real combat status effects.


# v95: in-engine custom passive values for newly created classes/races;
# transactional, offline, explicit recovery of intrinsic level/XP pairs.

# v96: offline correction of already unlocked class and learned skill progression.


# v96.00.1: audited Windows predeploy historical regressions; no gameplay changes.


# v96.00.2: restore both pre-v70 and current Admin Live command grammars.



# v96.00.3: finish cumulative predeploy gates without dropping any test case.

# v96.00.4: keep static content_registry release and runtime /changes aligned.

# v97: active registry displays cumulative update without altering old version snapshots.


# v98: three owner-only Admin Live capabilities in one cumulative package.

# v99: five real Admin Live extensions, preserving earlier releases.

# v100: source-backed, explicitly bounded Admin Live additions.

# v102: native full-engine isolated tunnel, declarative mechanic conditions, audited Admin Live.

# v101: three bounded expansions. No code execution or unsafe direct in-session full combat.

# v107: register the 23rd class only after historical authored-world installs.
# These installs intentionally validate the unchanged old 22-class catalogue.
# This is experimental staging and NOT a deployable production configuration.
import os as _sb_v107_server_env
if _sb107_runtime_enabled():
    if tuple(map(int,VERSION.split('.'))) >= (110,0,0):
        # Native loader can replace sys.modules after a pre-bootstrap import.
        from core.archetypes.runtime_catalogue import canonical_classes_skills
        _sb_v107_catalogue = canonical_classes_skills()
    else:
        import core.classes_skills as _sb_v107_catalogue
    from core.magitek.catalogue import install as _sb_v107_install_magitek
    _sb_v107_catalogue.V107_MAGITEK_ADDED = _sb_v107_install_magitek(
        vars(_sb_v107_catalogue))
    V107_MAGITEK_ADDED = _sb_v107_catalogue.V107_MAGITEK_ADDED
    from core.archetypes.chaos import install as _sb_v107_install_new_archetypes
    V107_ARCHETYPES_BUILD = _sb_v107_install_new_archetypes(vars(_sb_v107_catalogue))
    if tuple(map(int,VERSION.split('.'))) >= (110,0,0):
        from core.archetypes.expansion import install as _sb110_install_archetypes
        V110_ARCHETYPES_BUILD = _sb110_install_archetypes(vars(_sb_v107_catalogue))
    from systems.equipment_crafting import install_magitek_guild_v107 as _sb_v107_guild
    V107_MAGITEK_GUILD_QUESTS = _sb_v107_guild()
    if tuple(map(int,VERSION.split('.'))) >= (110,0,0):
        from systems.equipment_crafting import install_successor_guild_v110
        V110_GUILD_QUEST_CLASS_COUNT = install_successor_guild_v110()

        # v110: all new classes have authored Tier EQ and one teacher each,
        # but the old shop map was frozen at 22 entries during native bootstrap.
        # Reuse the teacher's EXISTING room and NPC as an actual vendor rather
        # than introducing 16 redundant rooms, NPCs, Python modules or BATs.
        from core.archetypes.chaos import CLASS_SPECS as _v110_previous_classes
        from core.archetypes.expansion import CLASS_SPECS as _v110_current_classes
        from network.protocol_gameplay_utils import normalize_lookup_text as _v110_norm
        _v110_class_names = ('Magitek',) + tuple(
            row[0] for row in (*_v110_previous_classes, *_v110_current_classes))
        if len(_v110_class_names) != 16 or len(set(_v110_class_names)) != 16:
            raise RuntimeError('v110: brak 16 jednoznacznych klas sklepowych')
        _v110_used_shop_rooms = set(CLASS_SHOP_ROOM_BY_CLASS_V03036.values())
        for _v110_class in _v110_class_names:
            _v110_teachers = [(key, npc) for key, npc in NPCS.items()
                             if npc.get('teacher_class') == _v110_class]
            if len(_v110_teachers) != 1 or _v110_class not in CLASS_EQUIPMENT_SETS:
                raise RuntimeError(f'v110: brak pojedynczego nauczyciela/EQ: {_v110_class}')
            _v110_teacher_id, _v110_teacher = _v110_teachers[0]
            _v110_room = _v110_teacher.get('room')
            if (_v110_room not in ROOMS or _v110_room in _v110_used_shop_rooms
                    or _v110_room in SHOP_SELLERS or SHOPS.get(_v110_room)
                    or _v110_class in CLASS_SHOP_ROOM_BY_CLASS_V03036):
                raise RuntimeError(f'v110: konflikt sali sklepu EQ: {_v110_class}')
            _v110_tier_one = list(CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER[_v110_class][1])
            if not _v110_tier_one or any(
                    ITEMS.get(iid, {}).get('required_class') != _v110_class
                    for iid in _v110_tier_one):
                raise RuntimeError(f'v110: niewlasciwy Tier 1 EQ klasy {_v110_class}')
            _v110_used_shop_rooms.add(_v110_room)
            CLASS_SHOP_ROOM_BY_CLASS_V03036[_v110_class] = _v110_room
            CLASS_SHOP_SELLER_NAMES_V03036[_v110_class] = _v110_teacher['name']
            CLASS_SHOP_CLASSES_BY_ROOM[_v110_room] = [_v110_class]
            CLASS_SHOP_ITEMS_BY_ROOM[_v110_room] = _v110_tier_one
            CLASS_EQUIPMENT_SETS[_v110_class]['room'] = _v110_room
            SHOPS[_v110_room] = list(_v110_tier_one)
            SHOP_SELLERS[_v110_room] = _v110_teacher_id
            _v110_teacher['shopkeeper'] = True
            _v110_teacher['class_eq_shop'] = _v110_class
            _v110_teacher['dialogue'] = (
                str(_v110_teacher.get('dialogue') or '')
                + f' Sprzedaję również wyposażenie klasy {_v110_class}: shop, list, kup 1.')
            ROOMS[_v110_room]['desc'] = (
                str(ROOMS[_v110_room].get('desc') or '')
                + f' Tutaj kupisz klasowe EQ: {_v110_class}; wpisz shop.')
            for _v110_prefix in ('eq', 'sklep eq', 'sklep z eq', 'ekwipunek', 'sklep'):
                GUIDE_DESTINATION_ALIASES[_v110_norm(
                    f'{_v110_prefix} {_v110_class}')] = _v110_room
        CLASS_SHOP_AUDIT_V03036 = class_shop_audit_v03036()
        if CLASS_SHOP_AUDIT_V03036['error_count'] or CLASS_SHOP_AUDIT_V03036['class_shops_checked'] != 38:
            raise RuntimeError('v110: audyt nowych sklepów klasowych: '
                               + repr(CLASS_SHOP_AUDIT_V03036))
        HELP_TOPICS['sklepy klasowe'] = [
            'Wszystkie 38 klas ma własny sklep EQ; u nowszych klas sprzedaje nauczyciel.',
            'Wpisz prowadz eq albo walk eq <klasa>; na miejscu shop, list i kup 1.',
            'Każdy zakup wymaga właściwej klasy, a Tier zależy od Levelu postaci.',
        ]

    # v107 ETAP 6: only the EXISTING Kraina Owadów gets more wildlife.
    # Register after historical world audits and before World() is created.
    from world.v10700_insects_expansion import install as _sb_v107_insects_install
    V107_INSECTS_BUILD = _sb_v107_insects_install(
        ROOMS, MOB_TEMPLATES, MOB_SPAWNS, NPCS, QUESTS, ITEMS,
        HELP_TOPICS, HELP_TOPIC_ALIASES)

    # v107 ETAP 7: follow-up wildlife habitats, never duplicate phase 6 IDs.
    from world.v10700_insects_wildlife_plus import install as _sb_v107_insects_plus_install
    V107_INSECTS_PLUS_BUILD = _sb_v107_insects_plus_install(
        ROOMS, MOB_TEMPLATES, MOB_SPAWNS, NPCS, QUESTS, ITEMS,
        HELP_TOPICS, HELP_TOPIC_ALIASES)

    # v107 WIELKA PACZKA: komplet 30 krain, pomoc NVDA bez zbędnych ozdobników.
    if 'krainy107' in HELP_TOPICS or any(
            a in HELP_TOPIC_ALIASES for a in ('chaos107','nowekrainy107','rozdzialy107')):
        raise RuntimeError('v107: konflikt identyfikatorów pomocy nowych krain')
    from world.v10700_region_index import CHAPTER_ONE as _sb_v107_first_chapter
    from world.v10700_region_index_chapters_2_6 import CHAPTERS as _sb_v107_all_chapters
    _sb_v107_chapters=(_sb_v107_first_chapter,)+_sb_v107_all_chapters
    HELP_TOPICS['krainy107'] = [
        'v107 Era Wiecznego Chaosu. 30 nowych krain w sześciu rozdziałach. Bez rajdów.',
        'Początek: na wschód od Serca Astralnego Przebudzenia w krainie v106.',
        'Łącznie 600 lokacji, 360 typów potworów, 1200 regionalnych zadań.',
        'Każda kraina: 20 pokoi, 10 zwykłych potworów, 2 bossów i 4 NPC.',
        'Zadania fabularne, polowania, surowce i profesje. Każda droga ma powrót.',
        'Wszystkie bossy solo lub z drużyną do sześciu prawdziwych graczy.',
        'Poziomy zalecane od 60001 do 90000, bez sztywnej blokady wejścia.',
        'Dodatkowo w Krainie Owadów jest 40 zadań, 50 rodzajów nowych owadów.',
        'Saga v107: 2000 nowych zadań (1200 regionalnych, 40 owadów, 760 dodatkowych).',
    ]
    for _sb_v107_chapter_index,_sb_v107_rows in enumerate(_sb_v107_chapters,1):
        _sb_v107_names=', '.join(row[1] for row in _sb_v107_rows)
        HELP_TOPICS['krainy107'].append(
            f'Rozdział {_sb_v107_chapter_index}: {_sb_v107_names}.')
    HELP_TOPIC_ALIASES['chaos107'] = 'krainy107'
    HELP_TOPIC_ALIASES['nowekrainy107'] = 'krainy107'
    HELP_TOPIC_ALIASES['rozdzialy107'] = 'krainy107'


# v107: migrate only untouched legacy 800 defaults after all historical
# bootstrap/catalogue audits. Custom saved Admin Live caps remain unchanged.
# This is production-authorized only; no migration runs in staging mode.
if _sb107_runtime_enabled():
    from core.live_level_caps_v5200 import activate_v107_uncapped_defaults as _v107_uncap
    _v107_uncap()


# v108: documented, actually routed player commands; no overwritten old topic.
for _v108_help_key, _v108_help_line in (
    ('rasy', 'W kreatorze po wyborze rasy, na ekranie klas wpisz 0, wroc, wróć lub rasy, aby ponownie odczytać wszystkie opisy ras i zmienić wybór. Imię i płeć zostaną.'),
    ('klasy', 'W kreatorze numer klasy wybiera klasę. Wpisz 0, wroc, wróć lub rasy, by wrócić do opisu ras. Driada: tylko kobieta.'),
    ('portale', 'Twierdza Gigantów: portal lista, portal 10 / portal 20 / gigantportal 10. W zaliczonym checkpointcie: portal wyjdz. Każdy członek drużyny musi sam zaliczyć bossa.'),
    ('kopalnia', 'W Kopalni Głębinowej: kop off zatrzymuje automat, cofnij wraca do sąsiedniego odwiedzonego chodnika, wyjscie wyprowadza i wyłącza auto-kopanie.'),
    ('questy', 'Oddaj quest NUMER lub turnin NUMER. Zwykłą, nieulepszoną kopię EQ można oddać; założone, runiczne i rozwijane EQ pozostaje chronione.'),
    ('ekwipunek', 'Przy oddawaniu zadań nie zużywasz założonego, ulepszonego ani runicznego wyposażenia. Zwykły crafting nadal blokuje fizyczne EQ.'),
):
    HELP_TOPICS.setdefault(_v108_help_key, []).append(_v108_help_line)
HELP_TOPICS['twierdzaportal'] = [
    'Twierdza Gigantów: portal lista, portal 10, portal 20, gigantportal 10 i portal wyjdz.',
    'Checkpointy co 10 pięter, po osobistym zaliczeniu bossa; członek drużyny bez zaliczenia nie teleportuje się.',
]
HELP_TOPIC_ALIASES['gigantportal'] = 'twierdzaportal'
HELP_TOPIC_ALIASES['portalfortress'] = 'twierdzaportal'

if tuple(map(int,VERSION.split('.'))) >= (110,0,0):
    HELP_TOPICS['krainy110'] = [
        'v110: 12 nowych krain, 360 lokacji, 40 bossów, 700 questów.',
        'Nowa kraina zaczyna się na wschód od ostatniego regionu Horyzontów v109.',
        'Osiem nowych klas i ras oraz osiem profesji: komenda profesja110 lista.',
        'Wydarzenia globalne: komenda wydarzenie110. Rotacja co sześć godzin.',
        'Brak rajdów i blokad poziomu. Drużyna do sześciu prawdziwych graczy.',
    ]
    HELP_TOPIC_ALIASES['nowekrainy110'] = 'krainy110'
    LATEST_CHANGES_TITLE = f'Soulbound v{VERSION} — Aktualna wersja gry'
    LATEST_CHANGES = ['v110: osobne moduły 12 krain, 700 questów, 40 bossów, 8 klas, 8 ras i 8 profesji.',
                      'v110: wydarzenia globalne 3.0, nowy bezpieczny kontrakt uruchamiania.']+LATEST_CHANGES

# The server performs additional authored content registration below native
# composition. Evaluate public teacher HELP and the complete audit only AFTER
# that registration; otherwise those checks see incomplete catalogs.
from systems.current_teacher_help import publish_teacher_help as _publish_teacher_help
TEACHER_HELP_COUNT = _publish_teacher_help(globals())
assert TEACHER_HELP_COUNT == 8

# Run the exhaustive gate against the FINAL assembled runtime, after all
# compatibility layers and cumulative milestone guards have finished.
if os.environ.get("SOULBOUND_FULL_AUDIT", "").strip().lower() in ("1", "true", "yes", "on"):
    # Use the fully assembled CURRENT runtime. The legacy admin/audits.py
    # is deliberately absent from the production composition; importing its
    # version-specific implementation would both break boot and inspect
    # obsolete class/job assumptions rather than the real current catalogs.
    from systems.current_full_runtime_audit import audit_loaded_world
    FULL_GAME_PREDEPLOY_AUDIT_V0336 = audit_loaded_world(globals())
    if FULL_GAME_PREDEPLOY_AUDIT_V0336['error_count']:
        raise RuntimeError('Current full world audit failed: '+repr(
            FULL_GAME_PREDEPLOY_AUDIT_V0336['errors'][:25]))
else:
    FULL_GAME_PREDEPLOY_AUDIT_V0336 = {
        "version": "0.70.0", "skipped_at_runtime": True,
        "error_count": 0, "warning_count": 0, "errors": [], "warnings": [],
        "reason": "Run before deploy with SOULBOUND_FULL_AUDIT=1; skipped during normal server startup.",
    }


if __name__ == '__main__':
    main()

