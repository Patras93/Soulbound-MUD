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

# v39: Historical legacy modules still export older LATEST_CHANGES_TITLE and
# overwrite the first release title during compatibility assembly. Restore the
# canonical release identity *after* assembly, without re-executing catalogs or
# modifying gameplay. Keep prior NEWS entries accessible in this session.
if VERSION in ("39.00.0", "39.00.1", "39.00.2", "39.00.3"):
    import sys as _guardian39_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v39.00.3 - Admin Guardian 5.0: questy i EXP statystyk (PREDEPLOY)"
    )
    _v39_first_news = (
        "v39.00.3: poprawka Dockerfile COPY seed; admin guardian5 pomoc; szesc osobnych nagrod EXP statystyk "
        "questow, wspolny reward_stat_xp zachowany, katalog i diagnostyka, "
        "podglad faz UOSS bez symulowania prawdziwej walki."
    )
    LATEST_CHANGES = [_v39_first_news] + [
        row for row in LATEST_CHANGES if not str(row).startswith(('v39.00.0:', 'v39.00.1:', 'v39.00.2:', 'v39.00.3:'))
    ]
    for _v39_module in ('systems.content_registry', 'player.session_mixins.help_system'):
        _v39_loaded = _guardian39_sys.modules.get(_v39_module)
        if _v39_loaded is not None:
            _v39_loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v39_loaded.LATEST_CHANGES = LATEST_CHANGES

# v40 Guardian 6.0 release identity. No catalog reload and no changes to quest XP engine.
if VERSION == "40.00.0":
    import sys as _guardian40_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v40.00.0 - Admin Guardian 6.0: audyt questow i DRAFT nagrod (PREDEPLOY)"
    )
    _v40_first_news = (
        "v40.00.0: admin guardian6 pomoc; zbiorcze przygotowywanie wspolnego i szesciu "
        "osobnych EXP statystyk w DRAFT, katalog nagrod, audyt i zaleznosci questow, "
        "korekty potrzebnych ilosci, kontrola przejsc krain, OLC preflight i statyczna analiza bossow. "
        "Prawdziwa arena UOSS wciaz nie jest dostepna."
    )
    LATEST_CHANGES = [_v40_first_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith(('v40.00.0:',))]
    for _v40_module in ('systems.content_registry', 'player.session_mixins.help_system'):
        _v40_loaded = _guardian40_sys.modules.get(_v40_module)
        if _v40_loaded is not None:
            _v40_loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v40_loaded.LATEST_CHANGES = LATEST_CHANGES

# v41 Guardian 7.0: private source-rule arena and atomic quest repair DRAFT.
# No grant, real HP, real mob or live world-state changes from arena commands.
if VERSION == "41.00.0":
    import sys as _guardian41_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v41.00.0 - Admin Guardian 7.0: arena UOSS LAB i naprawa questow (PREDEPLOY)"
    )
    _v41_first_news = (
        "v41.00.0: admin guardian7 pomoc 1/2/3; prywatna arena bossow z bezpiecznym "
        "modelem zdolnosci i faz UOSS, testowe miniony, statusy i raport; "
        "wielopolowe zmiany questow w DRAFT, plan, cofanie oraz przeglad i audyt. "
        "Arena nie jest pelna produkcyjna walka PvE/AI, brak prawdziwych nagrod."
    )
    LATEST_CHANGES = [_v41_first_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith(('v41.00.0:',))]
    for _v41_module in ('systems.content_registry', 'player.session_mixins.help_system'):
        _v41_loaded = _guardian41_sys.modules.get(_v41_module)
        if _v41_loaded is not None:
            _v41_loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v41_loaded.LATEST_CHANGES = LATEST_CHANGES

# v42 Guardian 8.0: pure-source rehearsal and atomic quest DRAFT batches.
if VERSION == "42.00.0":
    import sys as _guardian42_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v42.00.0 - Admin Guardian 8.0: arena UOSS i questy (PREDEPLOY)"
    )
    _v42_first_news = (
        "v42.00.0: admin guardian8 pomoc 1/2/3; izolowane zasady UOSS, "
        "efekty czasowe, statusy i testowe AI minionow; serie napraw questow "
        "walidowane atomowo w DRAFT, z mozliwoscia cofania. "
        "Nie jest to pelna produkcyjna walka ani prawdziwe nagrody."
    )
    LATEST_CHANGES = [_v42_first_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v42.00.0:')]
    for _v42_module in ('systems.content_registry', 'player.session_mixins.help_system'):
        _v42_loaded = _guardian42_sys.modules.get(_v42_module)
        if _v42_loaded is not None:
            _v42_loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v42_loaded.LATEST_CHANGES = LATEST_CHANGES

# v43 Guardian 9.0: reversible isolated arena simulations and OLC review.
if VERSION == "43.00.0":
    import sys as _guardian43_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v43.00.0 - Admin Guardian 9.0: migawki areny UOSS i audyt DRAFT (PREDEPLOY)"
    )
    _v43_first_news = (
        "v43.00.0: admin guardian9 pomoc 1/2/3; arena prognoza i seria do 20 tur, "
        "migawki i przywracanie prywatnej areny, poprawiona zgodnosc HP aktora testowego; "
        "questy seria roznice / draft / zaleznosci tylko odczyt. Bez pelnej produkcyjnej walki, "
        "bez nagrod i bez publikacji DRAFT."
    )
    LATEST_CHANGES = [_v43_first_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v43.00.0:')]
    for _v43_module in ('systems.content_registry', 'player.session_mixins.help_system'):
        _v43_loaded = _guardian43_sys.modules.get(_v43_module)
        if _v43_loaded is not None:
            _v43_loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v43_loaded.LATEST_CHANGES = LATEST_CHANGES

# v44 Guardian 10: per-arena RNG, reproducible snapshots and scenario comparisons.
if VERSION == "44.00.0":
    import sys as _guardian44_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v44.00.0 - Admin Guardian 10: prywatna losowosc i scenariusze areny UOSS (PREDEPLOY)"
    )
    _guardian44_news = (
        "v44.00.0: admin guardian10 pomoc 1/2/3; arena z wlasnym RNG, migawka i replay, "
        "porownaj trzy warianty atak/obrona/lecz, odczyt nagrod i diagnostyki questow. "
        "Bez produkcyjnej petli walki, pelnego AI i realnego ekwipunku, bez wyplat i publikacji."
    )
    LATEST_CHANGES = [_guardian44_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v44.00.0:')]
    for _v44_mod in ('systems.content_registry', 'player.session_mixins.help_system'):
        _v44_loaded = _guardian44_sys.modules.get(_v44_mod)
        if _v44_loaded is not None:
            _v44_loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v44_loaded.LATEST_CHANGES = LATEST_CHANGES

# v45: isolated skill and test-equipment experiments. No live XP/combat changes.
if VERSION == "45.00.0":
    import sys as _guardian45_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v45.00.0 - Admin Live: skille i taktyki w UOSS LAB (PREDEPLOY)"
    )
    _guardian45_news = (
        "v45.00.0: admin live arena pomoc 1/2/3; testowe klasy, katalog skilli, "
        "mana z definicji umiejetnosci, podglad przedmiotow i sekwencje walki. "
        "Bez prawdziwej petli produkcyjnej, rzeczywistego EQ, EXP ani zmian bazy."
    )
    LATEST_CHANGES = [_guardian45_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v45.00.0:')]
    for _v45_mod in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded = _guardian45_sys.modules.get(_v45_mod)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v46: next generation of the existing admin live workflow; never auto-deploy.
if VERSION == "46.00.0":
    import sys as _adminlive46_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v46.00.0 - Admin Live Ultimate: druzyny LAB i kontrola questow (PREDEPLOY)"
    )
    _adminlive46_news = (
        "v46.00.0: admin live pomoc 1/2/3; arena druzyna (do 4 fikcyjnych postaci), "
        "katalog skilli i bezpieczne prognozy; questy karta/szukaj/napraw plan, "
        "zatwierdz i cofnij w DRAFT. Brak prawdziwych nagrod, zmian SQLite, "
        "pelnego AI 1:1 i automatycznej publikacji. Wymagany Windows PREDEPLOY 60/60 PLUS."
    )
    LATEST_CHANGES = [_adminlive46_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v46.00.0:')]
    for _adminlive46_mod in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded46 = _adminlive46_sys.modules.get(_adminlive46_mod)
        if _loaded46 is not None:
            _loaded46.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded46.LATEST_CHANGES = LATEST_CHANGES

# v47: release readiness and unified, read-only admin live commands.
if VERSION == "47.00.0":
    import sys as _adminlive47_sys
    LATEST_CHANGES_TITLE = (
        "Soulbound v47.00.0 - Admin Live Ultimate: audyt questow i zabezpieczenia wdrozenia (PREDEPLOY)"
    )
    _adminlive47_news = (
        "v47.00.0: admin live pomoc 4; questy exp ID (aktywny i DRAFT); "
        "questy global [strona] (pelny statyczny audyt); questy preflight; "
        "arena zgodnosc [ID]; gotowosc. Bez zmian nagrod i postepu graczy, "
        "bez zmian produkcyjnej walki. Arena pozostaje modelem, nie UOSS 1:1. "
        "Wymagany Windows PREDEPLOY 60/60 PLUS przed wdrozeniem."
    )
    LATEST_CHANGES = [_adminlive47_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v47.00.0:')]
    for _adminlive47_mod in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded47 = _adminlive47_sys.modules.get(_adminlive47_mod)
        if _loaded47 is not None:
            _loaded47.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded47.LATEST_CHANGES = LATEST_CHANGES

# v48 release identity; retains v47 release news for changelog history.
if VERSION == "48.00.0":
    import sys as _v48_sys
    LATEST_CHANGES_TITLE = "Soulbound v48.00.0 - Admin Live: questy 18 typow i LAB druzyny (PREDEPLOY)"
    _v48_news = ("v48.00.0: admin live pomoc 5; questy typy, typ NAZWA, diagnoza ID; "
        "arena druzyna klasy, gotowy KLASA i porownaj TURY. Bez zmian w produkcyjnej "
        "walce, EXP, bazie, postepie. Wymagany PREDEPLOY 60/60 PLUS.")
    LATEST_CHANGES = [_v48_news] + [row for row in LATEST_CHANGES if not str(row).startswith('v48.00.0:')]
    for _v48_name in ('systems.content_registry','player.session_mixins.help_system'):
        _v48_mod = _v48_sys.modules.get(_v48_name)
        if _v48_mod is not None:
            _v48_mod.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v48_mod.LATEST_CHANGES = LATEST_CHANGES

# v49: release identity for conservative quest and LAB integrity tools.
if VERSION == "49.00.0":
    import sys as _v49_sys
    LATEST_CHANGES_TITLE = "Soulbound v49.00.0 - Admin Live: audyt questow i przebieg LAB (PREDEPLOY)"
    _v49_news = ("v49.00.0: admin live pomoc 6; questy bledy / bledytyp / sprawdz / lancuch; "
        "arena druzyna raport / przebieg TURY. Wyłącznie odczyt i prywatny LAB; "
        "bez zmian EXP, aktywnych questow i postepow. Wymagany PREDEPLOY 60/60 PLUS.")
    LATEST_CHANGES = [_v49_news] + [row for row in LATEST_CHANGES if not str(row).startswith('v49.00.0:')]
    for _v49_name in ('systems.content_registry','player.session_mixins.help_system'):
        _v49_mod = _v49_sys.modules.get(_v49_name)
        if _v49_mod is not None:
            _v49_mod.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v49_mod.LATEST_CHANGES = LATEST_CHANGES

# v50: unified admin live with owner-confirmed DRAFT fixes and full dependency scan.
if VERSION == "50.00.0":
    import sys as _v50_sys
    LATEST_CHANGES_TITLE = "Soulbound v50.00.0 - Admin Live: korekty questow i scenariusze LAB (PREDEPLOY)"
    _v50_news = ("v50.00.0: admin live pomoc 7; questy korekta lista/plan/zastosuj/cofnij/anuluj; "
        "questy cykle/pokrycie; arena scenariusze. Zmiany tylko DRAFT, bez automatycznej "
        "publikacji, SQLite i nagrod. Arena LAB wciaz nie stanowi produkcyjnego UOSS 1:1. "
        "Wymagany Windows PREDEPLOY 60/60 PLUS i testy NVDA.")
    LATEST_CHANGES = [_v50_news] + [row for row in LATEST_CHANGES if not str(row).startswith('v50.00.0:')]
    for _v50_name in ('systems.content_registry','player.session_mixins.help_system'):
        _v50_mod = _v50_sys.modules.get(_v50_name)
        if _v50_mod is not None:
            _v50_mod.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v50_mod.LATEST_CHANGES = LATEST_CHANGES

# v51: canonical multi-field quest DRAFT and isolated 22-class comparison.
if VERSION == "51.00.0":
    import sys as _v51_sys
    LATEST_CHANGES_TITLE = "Soulbound v51.00.0 - Admin Live: edycja questow i LAB klas (PREDEPLOY)"
    _v51_news = ("v51.00.0: admin live pomoc 8; questy edycja plan/zatwierdz/cofnij/status/anuluj; "
        "arena klasy test 1-3 [strona], arena bossy test 1-3 [strona]. Kanoniczna walidacja DRAFT, ochrona przed "
        "kolizjami zmian, izolowane eksperymenty 22 klas. Brak publikacji automatycznej, "
        "realnego EQ, SQL i nagrod. Nie jest to walka UOSS 1:1; "
        "wymagane testy NVDA i Windows PREDEPLOY 60/60 PLUS.")
    LATEST_CHANGES = [_v51_news] + [row for row in LATEST_CHANGES if not str(row).startswith('v51.00.0:')]
    for _v51_name in ('systems.content_registry','player.session_mixins.help_system'):
        _v51_mod = _v51_sys.modules.get(_v51_name)
        if _v51_mod is not None:
            _v51_mod.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _v51_mod.LATEST_CHANGES = LATEST_CHANGES

if VERSION == '52.00.0':
    import sys as _v52_sys
    LATEST_CHANGES_TITLE = 'Soulbound v52.00.0 - Admin Live: limity poziomow (PREDEPLOY)'
    _v52_news = ('v52.00.0: admin live limity / limity ustaw DZIEDZINA LICZBA lub bezlimitu POTWIERDZAM; '
        'limity reset, wszystkie, wczytaj. Trwaly zapis poza SQLite, ochrona przed downlevelingiem; '
        'Soul Tier i budynki gildii nadal maja wlasne progi. Wymagany Windows PREDEPLOY 60/60 PLUS.')
    LATEST_CHANGES = [_v52_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v52.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _module = _v52_sys.modules.get(_name)
        if _module is not None:
            _module.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _module.LATEST_CHANGES = LATEST_CHANGES

# v54: one Admin Live inspection dashboard, without changes to real combat/EXP.
if VERSION == '54.00.0':
    import sys as _v54_sys
    LATEST_CHANGES_TITLE = 'Soulbound v54.00.0 - Admin Live: audyt koncowy i kontrola wdrozenia (PREDEPLOY)'
    _v54_news = ('v54.00.0: admin live pomoc 9; questy przeglad/napraw; arena przeglad; '
        'eq pokrycie; limity kontrola; gotowosc finalna. Raporty tylko do odczytu; '
        'DRAFT i publikacja pozostaja pod osobnymi zatwierdzeniami. '
        'Arena NIE jest produkcyjnym UOSS 1:1; wymagane Windows PREDEPLOY 60/60 PLUS i NVDA.')
    LATEST_CHANGES = [_v54_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v54.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _module = _v54_sys.modules.get(_name)
        if _module is not None:
            _module.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _module.LATEST_CHANGES = LATEST_CHANGES

# v55: actual progressive crafting above 800 with persistent item-ID restore.
if VERSION == '55.00.0':
    import sys as _v55_sys
    LATEST_CHANGES_TITLE = 'Soulbound v55.00.0 - Admin Live: rzemioslo i EQ ponad 800 (PREDEPLOY)'
    _v55_news = ('v55.00.0: autentyczny craft EQ po poziomie 800 profesji i narzedzia, '
        'Rezonans Rzemiosla i trwale odtwarzanie wyrobionych wariantow po restarcie. '
        'admin live eq craft 1000 930; pomoc 10. '
        'Materialy, stara jakosc i progi zakladania bez zmian. '
        'Wymagane Windows PREDEPLOY 60/60 PLUS oraz NVDA.')
    LATEST_CHANGES = [_v55_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v55.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _module = _v55_sys.modules.get(_name)
        if _module is not None:
            _module.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _module.LATEST_CHANGES = LATEST_CHANGES

# v56: scale ordinary equipment from authored infinite mobs AFTER a normal roll.
if VERSION == '56.00.0':
    import sys as _v56_sys
    LATEST_CHANGES_TITLE = 'Soulbound v56.00.0 - Admin Live: zwykly loot EQ z glebin (PREDEPLOY)'
    _v56_news = ('v56.00.0: zwykle EQ z mobow nieskonczonych lochow zyskuje '
        'Rezonans Glebi po realnym dropie; identyczne szanse i nagrody calej '
        'druzyny, bez zmiany unikatow UOSS, materialow i odkryc Boss Codex. '
        'admin live eq drop krypta 901 leather_vest; pomoc 11. '
        'Wymagane Windows PREDEPLOY 60/60 PLUS oraz NVDA.')
    LATEST_CHANGES = [_v56_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v56.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _module = _v56_sys.modules.get(_name)
        if _module is not None:
            _module.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _module.LATEST_CHANGES = LATEST_CHANGES

# v53 owner-configurable gear requirements for truly deep-world EQ.
# v57: real infinite boss chest payout beyond the historical 800 plateau.
if VERSION == '57.00.0':
    import sys as _v57_sys
    LATEST_CHANGES_TITLE = 'Soulbound v57.00.0 - Admin Live: skrzynie bossow ponad 800 (PREDEPLOY)'
    _v57_news = ('v57.00.0: złoto ze skrzyn bossow Krypt, Mitycznej Krypty i Magitek '
        'dalej rosnie ponad 800; bonus nakladany po dotychczasowym losowaniu, '
        'bez zmian przedmiotow, kluczy i nagrod druzyny. '
        'admin live skrzynie krypta 901 1000; pomoc 12. '
        'Wymagane Windows PREDEPLOY 60/60 PLUS i test NVDA.')
    LATEST_CHANGES = [_v57_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v57.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _module = _v57_sys.modules.get(_name)
        if _module is not None:
            _module.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _module.LATEST_CHANGES = LATEST_CHANGES

# v58: real high-floor boss chest bonus EQ and quest item-ID diagnostics.
if VERSION == '58.00.0':
    import sys as _v58_sys
    LATEST_CHANGES_TITLE = 'Soulbound v58.00.0 - Admin Live: bonusowe EQ skrzyn i kontrola nagrod questow (PREDEPLOY)'
    _v58_news = ('v58.00.0: wysokie skrzynie Krypt, Mitycznej Krypty, Wiezy Astralnej i '
        'Mitycznej Wiezy daja dodatkowa 25% szanse na EQ Rezonansu Glebi na osobe, '
        'bez naruszania bazowych nagrod. admin live skrzynie eq krypta 901; '
        'questy itemy; pomoc 13. Wymagane PREDEPLOY 60/60 PLUS.')
    LATEST_CHANGES = [_v58_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v58.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _module = _v58_sys.modules.get(_name)
        if _module is not None:
            _module.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _module.LATEST_CHANGES = LATEST_CHANGES

if VERSION == '53.00.0':
    import sys as _v53_sys
    LATEST_CHANGES_TITLE = 'Soulbound v53.00.0 - Admin Live: rozwoj EQ i audyt EXP (PREDEPLOY)'
    _v53_news = ('v53.00.0: admin live limity audyt; limity progi 801; '
        'limity eq prognoza krypta 901. Warianty EQ z glebi rosna z limitem EQ '
        'i biegłości; domyslne 800 zachowuje wymaganie 600. '
        'Wymagany Windows PREDEPLOY 60/60 PLUS.')
    LATEST_CHANGES = [_v53_news] + [row for row in LATEST_CHANGES
        if not str(row).startswith('v53.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _module = _v53_sys.modules.get(_name)
        if _module is not None:
            _module.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _module.LATEST_CHANGES = LATEST_CHANGES

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
from systems.eternal_glory_world_v1100 import install as _install_eternal_glory_v1100
V1100_ETERNAL_GLORY = _install_eternal_glory_v1100(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES)

# v11 dungeon chapters and extra boss Fame objectives, no legacy floor changes.
from systems.eternal_glory_depths_v1100 import install as _install_glory_depths_v1100
V1100_GLORY_DEPTHS = _install_glory_depths_v1100(
    ROOMS, NPCS, MOB_TEMPLATES, MOB_SPAWNS, QUESTS, ITEMS,
    HELP_TOPICS, HELP_TOPIC_ALIASES)

from systems.eternal_glory_crafting_v1100 import install as _install_glory_crafts_v1100
V1100_GLORY_CRAFTS = _install_glory_crafts_v1100(
    ITEMS, QUESTS, NPCS, CRAFT_RECIPES, HELP_TOPICS)

from systems.eternal_glory_class_guild_v1100 import install as _install_class_guild_v1100
V1100_CLASS_GUILD = _install_class_guild_v1100(NPCS, QUESTS, HELP_TOPICS)

from systems.eternal_glory_story_v1100 import install as _install_glory_story_v1100
V1100_STORY = _install_glory_story_v1100(NPCS, QUESTS, ITEMS, HELP_TOPICS, HELP_TOPIC_ALIASES)

# v11 truly endless floors and durable personal party checkpoint portals.
from systems.eternal_glory_infinite_v1100 import install as _install_infinite_v1100
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

# Run the exhaustive gate against the FINAL assembled runtime, after all
# compatibility layers and cumulative milestone guards have finished.
if os.environ.get("SOULBOUND_FULL_AUDIT", "").strip().lower() in ("1", "true", "yes", "on"):
    # Historical v0.33.6 audit is retained as a diagnostic snapshot. It still
    # encodes legacy assumptions (globally unique display names, old split-
    # currency normalization) that are not release-blocking in current Soulbound.
    FULL_GAME_PREDEPLOY_AUDIT_V0336 = full_game_predeploy_audit_v0336()
    # The original v0.33.6 audit had an exact 14-job catalog assertion.
    # In v6, validate the full 22-job extension explicitly instead of
    # weakening/rewriting its hash-locked legacy function. All other
    # original failures still remain release-blocking.
    if str(VERSION).startswith(('6.', '7.', '8.', '9.', '10.', '11.')):
        from systems.new_professions import PROFESSIONS as _v600_professions
        _v600_legacy_names = {
            'Wędkarstwo', 'Górnictwo', 'Drwalstwo', 'Zielarstwo',
            'Gotowanie', 'Alchemia', 'Kowalstwo', 'Jubilerstwo',
            'Krawiectwo', 'Garbarstwo', 'Stolarstwo', 'Zaklinanie',
            'Archeologia', 'Kartografia',
        }
        assert set(PROFESSION_RANK_NAMES) == _v600_legacy_names | set(_v600_professions), (
            'Legacy or new profession catalog changed unexpectedly',
            sorted(set(PROFESSION_RANK_NAMES) ^ (_v600_legacy_names | set(_v600_professions))))
        _v600_legacy_ext = [e for e in FULL_GAME_PREDEPLOY_AUDIT_V0336['errors']
                            if e[0] == 'profession_catalog_mismatch'
                            and set(e[1]) == _v600_legacy_names | set(_v600_professions)
                            and set(e[2]) == _v600_legacy_names]
        if len(_v600_legacy_ext) == 1:
            FULL_GAME_PREDEPLOY_AUDIT_V0336['catalog_extension_v600'] = '14 old + 8 new verified'
            FULL_GAME_PREDEPLOY_AUDIT_V0336['errors'] = [
                e for e in FULL_GAME_PREDEPLOY_AUDIT_V0336['errors']
                if e not in _v600_legacy_ext]
            FULL_GAME_PREDEPLOY_AUDIT_V0336['error_count'] = len(FULL_GAME_PREDEPLOY_AUDIT_V0336['errors'])
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
if VERSION == "59.00.0":
    import sys as _v59_sys
    LATEST_CHANGES_TITLE = "Soulbound v59.00.0 - Admin Live: EQ swiata ponad 800 i zaleznosci questow (PREDEPLOY)"
    _v59_first = ("v59.00.0: skalowanie zwyklych dropow EQ z mobow swiata ponad poziomem 800; "
                  "admin live eq swiat, questy zamien plan/zatwierdz/cofnij. "
                  "UOSS unikatow nie konwertujemy; questy tylko DRAFT; PREDEPLOY wymagany.")
    LATEST_CHANGES = [_v59_first] + [x for x in LATEST_CHANGES if not str(x).startswith('v59.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v59_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v60 canonical title; no re-import of runtime catalogues or game state.
if VERSION == "60.00.0":
    import sys as _v60_sys
    LATEST_CHANGES_TITLE = "Soulbound v60.00.0 - Admin Live: bezpieczna zamiana ID nagrod i celow questow (PREDEPLOY)"
    _v60_first = ("v60.00.0: questy id karta/znajdz/plan/zatwierdz/cofnij; walidowana zamiana "
                  "ID przedmiotow w nagrodach oraz celu kill/collect w DRAFT, maks. 8 questow. "
                  "Wymagane jawne ID, brak automatycznej publikacji i zapisu SQLite. PREDEPLOY wymagany.")
    LATEST_CHANGES = [_v60_first] + [x for x in LATEST_CHANGES if not str(x).startswith('v60.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v60_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v61: canonical release title. Legacy command dispatch stays unchanged.
if VERSION == "61.00.0":
    import sys as _v61_sys
    LATEST_CHANGES_TITLE = "Soulbound v61.00.0 - Admin Live: naprawy NPC, surowcow i celow questow (PREDEPLOY)"
    _v61_first = ("v61.00.0: admin live questy ref karta/znajdz/plan/zatwierdz/cofnij; "
                  "seryjna zamiana zleceniodawcow NPC, surowcow i celow wielocelowych "
                  "kill/collect/talk. Walidacja OLC, do 8 questow, tylko DRAFT. "
                  "Brak publikacji i zmian w SQLite. PREDEPLOY wymagany.")
    LATEST_CHANGES = [_v61_first] + [x for x in LATEST_CHANGES if not str(x).startswith('v61.00.0:')]
    for _module_name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v61_sys.modules.get(_module_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v62 canonical release title. Older dispatchers remain as aliases.
if VERSION == "62.00.0":
    import sys as _v62_sys
    LATEST_CHANGES_TITLE = "Soulbound v62.00.0 - Admin Live: questy, nagrody EQ, klasy (PREDEPLOY)"
    _v62_first = ("v62.00.0: pakiet wielorodzajowych zmian questow tylko DRAFT, "
                  "Rezonans Glebi wysokopoziomowych questow, skille 22 klas ponad 800. "
                  "Przed wdrozeniem wymagane PREDEPLOY 60/60 PLUS i test NVDA.")
    LATEST_CHANGES = [_v62_first] + [x for x in LATEST_CHANGES if not str(x).startswith('v62.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v62_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v63 release title; all earlier Admin Live commands preserved.
if VERSION in ("63.00.0", "64.00.0"):
    import sys as _v63_sys
    LATEST_CHANGES_TITLE = "Soulbound v63.00.0 - Admin Live: pakiet pol questow, bieglosc areny (PREDEPLOY)"
    _v63_change = ("v63.00.0: questy pakiet plan pole QUEST_ID POLE WARTOSC laczone z innymi naprawami; "
                  "arena klasy porownaj TURY STRONA BIEGLOSC; prywatni pomocnicy powyzej 800. "
                  "DRAFT tylko za potwierdzeniem. Wymagany Windows PREDEPLOY 60/60 PLUS.")
    LATEST_CHANGES = [_v63_change] + [x for x in LATEST_CHANGES if not str(x).startswith('v63.00.0:')]
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v63_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v64 release title: all earlier Admin Live commands remain intact.
if VERSION == "64.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v64.00.0 - Admin Live: atomowe naprawy celow questow (PREDEPLOY)"
    LATEST_CHANGES = ["v64.00.0: pakiet pole objectives/resource_targets JSON ; dopasuj QUEST_ID - kanoniczna walidacja calosci, bez publikowania i nagrod."] + [x for x in LATEST_CHANGES if not str(x).startswith('v64.00.0:')]
    import sys as _v64_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v64_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v65: pass real UOSS status/equipment rules to detached Admin Live LAB only.
if VERSION == "65.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v65.00.0 - Admin Live: odpornosci EQ i pasywy UOSS (PREDEPLOY)"
    LATEST_CHANGES = ["v65.00.0: arena uoss ekwipunek/status/pasywy: produkcyjne funkcje UOSS na kopii, bez SQLite i nagrod."] + [x for x in LATEST_CHANGES if not str(x).startswith('v65.00.0:')]
    import sys as _v65_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v65_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v66: source helper choice inspection, never live combat.
if VERSION == "66.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v66.00.0 - Admin Live: prawdziwy wybor akcji pomocnikow UOSS (PREDEPLOY)"
    LATEST_CHANGES = ["v66.00.0: arena uoss pomocnik [tura/seria/prognoza] - izolowane decyzje pomocnikow z kodu UOSS."] + [x for x in LATEST_CHANGES if not str(x).startswith('v66.00.0:')]
    import sys as _v66_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v66_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v67: helper support in source balance, detached arena, never live combat.
if VERSION == "67.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v67.00.0 - Admin Live: pomocnicy UOSS, skutki wsparcia (PREDEPLOY)"
    LATEST_CHANGES = ["v67.00.0: arena uoss pomocnik skutki - leczenie, mana, Bubble, debuff na prywatnych kopiach."] + [x for x in LATEST_CHANGES if not str(x).startswith('v67.00.0:')]
    import sys as _v67_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v67_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v68: production UOSS helper party target selection, isolated laboratory.
if VERSION == "68.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v68.00.0 - Admin Live: UOSS wsparcie calej druzyny (PREDEPLOY)"
    LATEST_CHANGES = ["v68.00.0: arena uoss druzyna wsparcie - 1-3 graczy na odizolowanych kopiach."] + [x for x in LATEST_CHANGES if not str(x).startswith('v68.00.0:')]
    import sys as _v68_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _v68_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v69: Admin Live centrum komend NVDA; no live combat or EXP mutation.
if VERSION == "69.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v69.00.0 - Admin Live: centrum komend NVDA (PREDEPLOY)"
    LATEST_CHANGES = ["v69.00.0: admin live centrum - centrum komend NVDA."] + [x for x in LATEST_CHANGES if not str(x).startswith('v69.00.0:')]
    import sys as _release_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _release_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v70: Admin Live odbior wydania i bramki PREDEPLOY; no live combat or EXP mutation.
if VERSION in ("70.00.0", "70.00.1"):
    LATEST_CHANGES_TITLE = "Soulbound v70.00.1 - Admin Live: poprawki PREDEPLOY (PREDEPLOY)"
    LATEST_CHANGES = ["v70.00.1: poprawki bramek PREDEPLOY, bez zmian rozgrywki."] + [x for x in LATEST_CHANGES if not str(x).startswith('v70.00.0:')]
    import sys as _release_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _release_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v70.00.2: Admin Live test tools and deterministic DRAFT corrections.
if VERSION == "70.00.2":
    LATEST_CHANGES_TITLE = "Soulbound v70.00.2 - Admin Live: UOSS, EQ, questy (PREDEPLOY)"
    LATEST_CHANGES = ["v70.00.2: uoss reguly, eq pokrycie, questy automaty z DRAFT/undo."] + [x for x in LATEST_CHANGES if not str(x).startswith('v70.00.2:')]
    import sys as _release_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _release_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v70.00.3: cap-adaptive editor, owner-opt-in scalable shop offers and diagnostics.
if VERSION == "70.00.3":
    LATEST_CHANGES_TITLE = "Soulbound v70.00.3 - Admin Live: Sklepy, poziomy, skille, questy (PREDEPLOY)"
    LATEST_CHANGES = ["v70.00.3: edycja ponad 800 wg limitow, zwykle skille mechanic_cooldown, wlaczane przez admina EQ w sklepach, diagnostyka questow/bossow/skilli."] + [x for x in LATEST_CHANGES if not str(x).startswith('v70.00.3:')]
    import sys as _release_sys
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _release_sys.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v72: this release is a strictly administrative extension, no combat rewards.
if VERSION == "72.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v72.00.0 - Admin Live: questy, fazy bossow, postacie (PREDEPLOY)"
    LATEST_CHANGES = [
        "v72.00.0: admin live pomoc 32; questy zaleznosci plan/undo DRAFT, "
        "boss fazy ustaw/zestaw DRAFT, postacie pakiet OFFLINE z atomowym audytem. "
        "Brak UOSS 1:1 i nowych grywalnych klas oraz ras. Wymagany Windows PREDEPLOY 60/60 PLUS."
    ] + [x for x in LATEST_CHANGES if not str(x).startswith('v72.00.0:')]
    import sys as _release_sys_v7200
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _release_sys_v7200.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v73: atomic OLC drafts only; UOSS catalog report is read-only.
if VERSION == "73.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v73.00.0 - Admin Live: pakiety questow i bossow (PREDEPLOY)"
    LATEST_CHANGES = [
        "v73.00.0: admin live pomoc 33; pakietowe zaleznosci questow i fazy zwyklych bossow "
        "w DRAFT (z cofnieciem); raport faz i ochrona skryptowanych UOSS. "
        "Nie jest to UOSS 1:1. Wymagany Windows PREDEPLOY 60/60 PLUS."
    ] + [x for x in LATEST_CHANGES if not str(x).startswith('v73.00.0:')]
    import sys as _release_sys_v7300
    for _name in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded = _release_sys_v7300.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES





# v74: correct the runtime release identity and expose new Admin Live help.
if VERSION == "74.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v74.00.0 - Admin Live: lancuchy questow i katalog UOSS (PREDEPLOY)"
    LATEST_CHANGES = [
        "v74.00.0: admin live pomoc 34; bezpieczna podmiana legacy requires_quest "
        "w DRAFT, raport wplywu i poprzednikow questow, lista i karta 21 skryptowanych "
        "spotkan UOSS. UOSS nadal nie jest walka 1:1. Windows 60/60 PLUS wymagany."
    ] + [x for x in LATEST_CHANGES if not str(x).startswith('v74.00.0:')]
    import sys as _release_sys_v7400
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _release_sys_v7400.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES


# v75: native UOSS mechanics and legacy prerequisite removal.
if VERSION == "75.00.0":
    LATEST_CHANGES_TITLE = "Soulbound v75.00.0 - rzeczywiste mechaniki UOSS i stabilizacja Admin Live (PREDEPLOY)"
    LATEST_CHANGES = [
        "v75.00.0: admin live pomoc 35, atomowa edycja skryptowanych faz, leczenia, furii i skali "
        "superbossow przez wykonywane mechaniki OLC24/32/33/34. Bez pelnej areny 1:1.",
        "v75.00.0: admin live questy zaleznosci stare usun plan ID; poprawnosc usuniecia "
        "starego requires_quest takze po publikacji i restarcie.",
        "v75.00.0: naprawa cofania rodowodu; zakaz publikacji leczenia/furii UOSS w trakcie walki. "
        "Obowiazkowy osobny PREDEPLOY 60/60 PLUS na Windows."
    ] + [x for x in LATEST_CHANGES if not str(x).startswith('v75.00.0:')]
    import sys as _release_sys_v7500
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _release_sys_v7500.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES


# v76: persistent, playable new races with authored inherited passives.
if VERSION == '76.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v76.00.0 - grywalne nowe rasy w Admin Live (PREDEPLOY)'
    LATEST_CHANGES = [
        'v76.00.0: admin live pomoc 36; rodowod nowa rasa plan / zatwierdz / cofnij.',
        'v76.00.0: prawdziwy kreator postaci, dzialajace pasywy rasowe i SQLite; max 32 nowe rasy.',
        'v76.00.0: bezpieczne wspoldzialanie z edycja starych ras, zachowanie przy aktualizacji.',
        'v76.00.0: brak kreatora nowych klas i pelnej areny UOSS 1:1; Windows 60/60 PLUS obowiazkowy.'
    ] + [x for x in LATEST_CHANGES if not str(x).startswith('v76.00.0:')]
    import sys as _release_sys_v7600
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_release_sys_v7600.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES


# v77: playable additional class archetypes, independent class skill IDs,
# compatible trainers, passive stats, and Soul Weapon trait inheritance.
if VERSION == '77.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v77.00.0 - grywalne klasy oparte na archetypach (PREDEPLOY)'
    LATEST_CHANGES = [
        'v77.00.0: admin live pomoc 37; rodowod nowa klasa plan/zatwierdz/cofnij.',
        'v77.00.0: 8 nowych klas na bazie Wojownik, Mag, Kaplan; wlasne ID skilli, pasyw, biegosc, bron.',
        'v77.00.0: nauka u istniejącego nauczyciela klasy bazowej i zapis w SQLite.',
        'v77.00.0: nie dodaje nowych typow AI ani nowych skryptow specjalnych; Windows 60/60 PLUS wymagane.',
    ] + [x for x in LATEST_CHANGES if not str(x).startswith('v77.00.0:')]
    import sys as _release_sys_v7700
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_release_sys_v7700.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v78: detached actor uses actual production player_damage for basic attacks.
if VERSION == '78.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v78.00.0 - UOSS surowy autoatak z produkcyjnej metody (PREDEPLOY)'
    LATEST_CHANGES = [
        'v81.00.0: admin live pomoc 41; bron UOSS - Echo, leczenie i odzysk MP.',
        'v80.00.0: admin live pomoc 40; arena uoss bron - wspolny krytyk i hit series.',
        'v78.00.0: admin live pomoc 38; arena uoss gracz prognoza/atak/stan.',
        'v78.00.0: player_damage liczone na klonie prawdziwej postaci; lokalne RNG i mana.',
        'v78.00.0: dotychczasowa reszta tury UOSS jest modelem, nie pelna walka 1:1.',
        'v78.00.0: bez zmian prawdziwych postaci i nagrod; Windows 60/60 PLUS wymagane.',
    ] + [x for x in LATEST_CHANGES if not str(x).startswith('v78.00.0:')]
    import sys as _release_sys_v7800
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_release_sys_v7800.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v82: production and detached LAB now select the same auto-queue skill.
# This release does NOT enable side-effecting skill casts within the LAB.
if VERSION == '82.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v82.00.0 - bezpieczny wybor skilla z auto-kolejki UOSS (PREDEPLOY)'
    LATEST_CHANGES = [
        'v82.00.0: admin live pomoc 42; arena uoss kolejka nastepny.',
        'v82.00.0: wspolny selektor skilli dla prawdziwej walki i prywatnego podgladu.',
        'v82.00.0: brak wykonania skilli/AI 1:1 w LAB; odczyt DB bez zapisow i izolacja kopii.',
        'v82.00.0: naprawiono wczytywanie zapisanych limitow admin live dla v79-v82.',
    ] + [row for row in LATEST_CHANGES if not str(row).startswith('v82.00.0:')]
    import sys as _sys82
    for _name in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded = _sys82.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES


# v83: safe, limited actual direct-skill cast, never world-side use_class_skill.
if VERSION == '83.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v83.00.0 - pierwsze bezpieczne rzucanie zwyklych skilli w LAB (PREDEPLOY)'
    LATEST_CHANGES = [
        'v83.00.0: admin live pomoc 43; arena uoss kolejka prosty prognoza/rzuc POTWIERDZAM.',
        'v83.00.0: wspolna z normalna walka formula bazowego ataku bezposrednim skillem.',
        'v83.00.0: koszt many i obrona bossa liczone na kopiach; prywatna rotacja i rollback.',
        'v83.00.0: AoE, Mec, reakcje zywiolowe, efekty specjalne i AI 1:1 NADAL zablokowane.',
    ] + [row for row in LATEST_CHANGES if not str(row).startswith('v83.00.0:')]
    import sys as _sys83
    for _name in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded = _sys83.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v84: actual game runtime isolation (separate process, private DB, loopback-only).
# Deliberately NOT an in-session complete Guardian combat engine.
if VERSION == '84.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v84.00.0 - pelny silnik walki w izolowanej kopii serwera (PREDEPLOY)'
    LATEST_CHANGES = [
        'v84.00.0: ARENA_UOSS_REAL_1_DO_1.bat - oddzielna pelna instancja gry na 127.0.0.1:4900.',
        'v84.00.0: migawka SQLite na prywatnej kopii, oddzielny zapis i seed swiata.',
        'v84.00.0: na kopii dziala rzeczywisty silnik walki (skille, AI, przywolania, dropy).',
        'v84.00.0: po zakonczeniu kasowana jest kopia, nagrody i zmiany nie trafiaja na serwer 4000.',
        'v84.00.0: administracyjna arena wewnatrz serwera nadal jest modelem i NIE jest 1:1.',
    ] + [row for row in LATEST_CHANGES if not str(row).startswith('v84.00.0:')]
    import sys as _sys84
    for _name in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded = _sys84.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v85: native engine TCP E2E and strict isolation safety release.
if VERSION == '85.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v85.00.0 - prawdziwy test TCP walki UOSS i twarda izolacja (PREDEPLOY)'
    LATEST_CHANGES = [
        'v85.00.0: pelny test TCP - logowanie, NPC, quest, Szczur i trwaly zapis kill 1/10 tylko na kopii.',
        'v85.00.0: --fresh nigdy nie czyta/kopiuje istniejącej bazy, blokada rekursywnego kopiowania.',
        'v85.00.0: izolacja kluczy srodowiska, zamykanie SQLite i obsluga Ctrl+Break na Windows.',
        'v85.00.0: prawdziwa walka 1:1 tylko na osobnym serwerze 127.0.0.1:4900, nie w srodku admin live.',
    ] + [row for row in LATEST_CHANGES if not str(row).startswith('v85.00.0:')]
    import sys as _sys85
    for _name in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded = _sys85.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v86: native full-engine arena lifecycle exposed within the existing admin live.
if VERSION == '86.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v86.00.0 - pelna izolowana arena UOSS zarzadzana z admin live (PREDEPLOY)'
    LATEST_CHANGES = [
        'v86.00.0: admin live pomoc 44; arena real start/status/stop z POTWIERDZAM.',
        'v86.00.0: jeden prawdziwy silnik walki na 127.0.0.1:4900, migawka SQLite, bez produkcyjnych nagrod.',
        'v86.00.0: sygnal zatrzymania i automatyczne zamkniecie po smierci serwera wlasciciela.',
        'v86.00.0: wbudowane laboratorium w tej samej sesji nadal jest symulatorem, nie walka 1:1.',
    ] + [row for row in LATEST_CHANGES if not str(row).startswith('v86.00.0:')]
    import sys as _sys86
    for _name in ('systems.content_registry', 'player.session_mixins.help_system'):
        _loaded = _sys86.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE = LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES = LATEST_CHANGES

# v87: atomic quest + scripted UOSS multi-entity OLC and fresh native arena.
if VERSION == '87.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v87.00.0 - duzy Admin Live: questy, UOSS, bezpieczna arena (PREDEPLOY)'
    LATEST_CHANGES = [
        'v87.00.0: pomoc 45; questy caly pakiet - stare i nowe zaleznosci 8 questow jednym planem.',
        'v87.00.0: boss uoss zbiorczy - do 8 superbossow, 16 rzeczywistych zasad walki.',
        'v87.00.0: arena real start pusta POTWIERDZAM - pelny silnik na pustej bazie bez kont graczy.',
        'v87.00.0: plany tylko DRAFT, zatwierdzenie i cofanie z kontrola konfliktow; publikacja osobno.',
        'v87.00.0: Windows PREDEPLOY 60/60 PLUS wymagane przed produkcyjnym wdrozeniem.',
    ] + [line for line in LATEST_CHANGES if not str(line).startswith('v87.00.0:')]
    import sys as _sys87
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _sys87.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v88: one atomic, cross-domain plan in the existing Admin Live panel.
if VERSION == '88.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v88.00.0 - Admin Live: aktualizacja calosciowa 8 dziedzin (PREDEPLOY)'
    LATEST_CHANGES = [
        'v88.00.0: pomoc 46; aktualizacja plan - do 24 zmian w 8 dziedzinach jednoczesnie.',
        'v88.00.0: questy, skille, moby, przedmioty, receptury, sklepy, NPC i skryptowane superbossy UOSS.',
        'v88.00.0: aktualizacja karta TYP ID POLE - prawdziwe wartosci ACTIVE i DRAFT dla NVDA.',
        'v88.00.0: calosciowa walidacja i kontrola konfliktow; zatwierdzanie i cofanie TYLKO DRAFT.',
        'v88.00.0: publikacja osobno; brak automatycznych zmian w SQLite i bazie postaci.',
        'v88.00.0: Windows PREDEPLOY 60/60 PLUS wymagane przed wdrozeniem.',
    ] + [line for line in LATEST_CHANGES if not str(line).startswith('v88.00.0:')]
    import sys as _sys88
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _sys88.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v89: read-only production publication gate and NVDA-readable global diff.
if VERSION == '89.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v89.00.0 - Admin Live: bezpieczna publikacja i pelne porownanie DRAFT (PREDEPLOY)'
    LATEST_CHANGES = [
        'v89.00.0: pomoc 47; aktualizacja porownaj [STRONA] - realne zmiany osmiu dziedzin.',
        'v89.00.0: aktualizacja publikacja sprawdz - prawdziwe kontrole przed aktywacja bez zapisow.',
        'v89.00.0: ochrona aktywnych questow, walk UOSS, spawnow i integralnosci katalogow.',
        'v89.00.0: dodatkowa kontrola braku zapisow SQLite; aktywacja nadal osobno.',
        'v89.00.0: Windows PREDEPLOY 60/60 PLUS wymagane przed wdrozeniem.',
    ] + [line for line in LATEST_CHANGES if not str(line).startswith('v89.00.0:')]
    import sys as _sys89
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _sys89.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v90: real durable revision recovery and conflict-safe publication.
if VERSION == '90.00.0':
    LATEST_CHANGES_TITLE = 'Soulbound v90.00.0 - Admin Live: historia rewizji, bezpieczne przywracanie i ochrona publikacji'
    LATEST_CHANGES = [
        'v90.00.0: pomoc 48; rewizje lista [STRONA], karta NUMER i audyt zapisu SQLite.',
        'v90.00.0: rewizje przywroc plan NUMER; zatwierdz i cofnij tylko w DRAFT.',
        'v90.00.0: wykrywanie przestarzalych rewizji; odmowa nadpisania cudzej publikacji.',
        'v90.00.0: historia nigdy nie jest nadpisywana; publikacja ciagle odrebna i zabezpieczona.',
        'v90.00.0: wymaga Windows PREDEPLOY 60/60 PLUS przed wdrozeniem.',
    ] + [line for line in LATEST_CHANGES if not str(line).startswith('v90.00.0:')]
    import sys as _sys90
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _sys90.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v91: complete tested archetype inheritance and atomic stale prerequisite repair.
if VERSION in ('91.00.0','92.00.0','93.00.0','94.00.0','95.00.0','95.00.0','96.00.0','96.00.1','96.00.2','96.00.3','96.00.4','97.00.0'):
    LATEST_CHANGES_TITLE = 'Soulbound v91.00.0 - Admin Live: 22 archetypy, migracja ID questow, bezpieczna publikacja'
    LATEST_CHANGES = [
        'v91.00.0: pomoc 49; do 32 nowych grywalnych klas opartych na wszystkich 22 archetypach.',
        'v91.00.0: nowa klasa mieszana - osobna baza, zestaw skilli, pasyw oraz Bron Duszy.',
        'v91.00.0: questy zaleznosci migracja - zastepowanie nieistniejacych ID w calym grafie questow.',
        'v91.00.0: aktywne questy chronione przed zmiana poprzednikow takze przy publikacji.',
        'v91.00.0: plan i cofanie bez ingerencji w SQLite; publikacja wymaga PREDEPLOY 60/60 PLUS.',
    ] + [line for line in LATEST_CHANGES if not str(line).startswith('v91.00.0:')]
    import sys as _sys91
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _sys91.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES


# v92: one atomic multi-domain quest repair release.
if VERSION in ('92.00.0','93.00.0','94.00.0','95.00.0','95.00.0','96.00.0','96.00.1','96.00.2','96.00.3','96.00.4','97.00.0'):
    LATEST_CHANGES_TITLE = 'Soulbound v92.00.0 - Admin Live: zbiorcza naprawa celow questow'
    LATEST_CHANGES = [
        'v92.00.0: pomoc 50; questy cele znajdz TRYB STARE_ID - pokaz odwolania.',
        'v92.00.0: questy cele plan - do 16 jawnych migracji kill, collect, talk, surowiec, reward i npc.',
        'v92.00.0: walidacja calego DRAFT; blokada kolizji i aktywnych questow, cofanie atomowe.',
        'v92.00.0: zadne EXP, zloto ani postep postaci nie sa modyfikowane przez plan i zatwierdz.',
    ] + [line for line in LATEST_CHANGES if not str(line).startswith('v92.00.0:')]
    import sys as _sys92
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded = _sys92.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v93: combined quest repair and safe two-effect authored attack skills.
if VERSION == '93.00.0':
    LATEST_CHANGES_TITLE='Soulbound v93.00.0 - Admin Live: kompleksowe naprawy i kombinacje efektow'
    LATEST_CHANGES=[
        'v93.00.0: pomoc 51; kompleksowy atomowy plan naprawy poprzednikow i celow questow.',
        'v93.00.0: skille damage i aoe_damage - olc_statuses dla dwoch bezpiecznych efektow trafienia.',
        'v93.00.0: walidacja DRAFT, blokada questow przyjetych, cofanie i publikacja osobno.',
    ] + [line for line in LATEST_CHANGES if not str(line).startswith('v93.00.0:')]
    import sys as _sys93
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys93.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v94: one substantive update spanning final-state quest fixes, deterministic
# counter repair and batch real combat status effects.
if VERSION == '94.00.0':
    LATEST_CHANGES_TITLE='Soulbound v94.00.0 - Admin Live: kompleksowe questy i skille'
    LATEST_CHANGES=[
        'v94.00.0: pomoc 52 - questy pakiet plan, do 32 pol w 16 questach na raz.',
        'v94.00.0: liczniki skan i plan - tylko matematycznie jednoznaczne needed.',
        'v94.00.0: skill efekty pakiet - do 16 skilli, atomowa migracja statusow.',
        'v94.00.0: ochrona aktywnych questow, cofanie DRAFT; publikacja osobna.',
    ]+[line for line in LATEST_CHANGES if not str(line).startswith('v94.00.0:')]
    import sys as _sys94
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys94.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES


# v95: in-engine custom passive values for newly created classes/races;
# transactional, offline, explicit recovery of intrinsic level/XP pairs.
if VERSION == '95.00.0':
    LATEST_CHANGES_TITLE='Soulbound v95.00.0 - Admin Live: rozwoj postaci i autorskie pasywy'
    LATEST_CHANGES=[
        'v95.00.0: pomoc 53; offline plan poziom+EXP postaci, Duszy i Broni Duszy, CAS i audyt.',
        'v95.00.0: nowe grywalne klasy i rasy: bezpieczne autorskie rodzaje/moc pasywow.',
        'v95.00.0: testy rollback SQLite, limitow, praw dostepu i odtwarzania po restarcie.',
        'v95.00.0: brak zmiany banku EXP, klasy/bieglosci, waluty i nagrod.',
    ]+[line for line in LATEST_CHANGES if not str(line).startswith('v95.00.0:')]
    import sys as _sys95
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys95.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v96: offline correction of already unlocked class and learned skill progression.
if VERSION in ('96.00.0','96.00.1','96.00.2','96.00.3','96.00.4','97.00.0'):
    LATEST_CHANGES_TITLE='Soulbound v96.00.0 - Admin Live: bieglosci klas i wyuczonych skilli'
    LATEST_CHANGES=[
        'v96.00.0: pomoc 54; plan i korekta do 16 istniejacych klas i skilli offline.',
        'v96.00.0: atomowa transakcja SQLite, kontrola zmian, audyt i bezpieczne cofniecie.',
        'v96.00.0: bank EXP: stronicowany raport tylko do odczytu, bez wyplat i zmiany salda.',
        'v96.00.0: brak uczenia skilli, dodawania klas, zmiany uzyc i nagrod; PREDEPLOY 60/60 PLUS przed wdrozeniem.',
    ]+[line for line in LATEST_CHANGES if not str(line).startswith('v96.00.0:')]
    import sys as _sys96
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys96.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES


# v96.00.1: audited Windows predeploy historical regressions; no gameplay changes.
if VERSION == '96.00.1':
    LATEST_CHANGES_TITLE='Soulbound v96.00.1 - korekta walidatorow PREDEPLOY 60/60 PLUS'
    LATEST_CHANGES=[
        'v96.00.1: testy historyczne rozpoznaja nowe wersje bez list zamknietych na v76.',
        'v96.00.1: bezwarunkowo pilnuje 6793 questow dla wspolczesnego katalogu.',
        'v96.00.1: mechanika gry i dane graczy pozostaja bez zmian.',
    ]+LATEST_CHANGES
    import sys as _sys9601
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys9601.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES


# v96.00.2: restore both pre-v70 and current Admin Live command grammars.
if VERSION == '96.00.2':
    LATEST_CHANGES_TITLE='Soulbound v96.00.2 - zgodnosc dawnych komend Admin Live'
    LATEST_CHANGES=[
        'v96.00.2: eq pokrycie bez argumentow oraz eq pokrycie ID [ETAP] dzialaja osobno.',
        'v96.00.2: przywrocono zgodnosc questy pakiet v62/v64 i v94, w tym cofanie i liczniki.',
        'v96.00.2: bez zmian mechaniki, baz postaci i wynagrodzen; PREDEPLOY wymagany.',
    ]+LATEST_CHANGES
    import sys as _sys9602
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys9602.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES



# v96.00.3: finish cumulative predeploy gates without dropping any test case.
if VERSION == '96.00.3':
    LATEST_CHANGES_TITLE='Soulbound v96.00.3 - pelna zgodnosc testow Windows PREDEPLOY'
    LATEST_CHANGES=[
        'v96.00.3: poprawiona weryfikacja wersji w historycznej regresji Admin Live v87.',
        'v96.00.3: czas na pelny audyt dostosowany do duzej liczby testow; wszystkie 60 etapow pozostaje obowiazkowe.',
        'v96.00.3: brak zmian EXP, walki, skilli, questow i bazy produkcyjnej.',
    ]+LATEST_CHANGES
    import sys as _sys9603
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys9603.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v96.00.4: keep static content_registry release and runtime /changes aligned.
if VERSION == '96.00.4':
    LATEST_CHANGES_TITLE='Soulbound v96.00.4 - naprawa testu TCP i zgodnosci wersji'
    LATEST_CHANGES=[
        'v96.00.4: poprawione odbieranie bannera w izolowanej arenie UOSS (Telnet negocjuje kodowanie przed banerem).',
        'v96.00.4: zgodnosc numeru wydania w rejestrze, silniku i CHANGELOG.',
        'v96.00.4: testy obowiazkowe; bez zmian EXP, walki i baz postaci.',
    ]+LATEST_CHANGES
    import sys as _sys9604
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys9604.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v97: active registry displays cumulative update without altering old version snapshots.
if VERSION == '97.00.0':
    LATEST_CHANGES_TITLE='Soulbound v97.00.0 - Admin Live: wielki pakiet postacie, plecak i UOSS'
    LATEST_CHANGES=[
        'v97.00.0: admin live pomoc 55 - korekta statystyk do 8 postaci offline (do 24 pol), jedna transakcja CAS z cofaniem.',
        'v97.00.0: admin live pomoc 55 - kontrola i korekta ilosci do 16 istniejacych stosow w plecaku; zakupione, chronione i wyposazone bez zmian.',
        'v97.00.0: admin live pomoc 56 - kopiowanie czterech prawdziwych mechanik UOSS z DRAFT lub ACTIVE do DRAFT wielu superbossow.',
        'v97.00.0: 120 kontroli nowych funkcji; brak zmian automatycznych w bazach graczy i zasadach walki.',
    ]+LATEST_CHANGES
    import sys as _sys9700
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys9700.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES


# v98: three owner-only Admin Live capabilities in one cumulative package.
if VERSION == '98.00.0':
    LATEST_CHANGES_TITLE='Soulbound v98.00.0 - Superbossowie 2.0, Quest Doctor, Postepy offline'
    LATEST_CHANGES=[
        'v98.00.0: pomoc 57 - nowe taktyki atakow, fazy HP i celowanie UOSS, tylko DRAFT do aktywacji.',
        'v98.00.0: pomoc 58 - Quest Doctor, bezpieczna diagnoza i deterministyczna korekta licznikow.',
        'v98.00.0: pomoc 59 - offline korekty istniejacych profesji, narzedzi i banku EXP.',
        'v98.00.0: wymagany Windows PREDEPLOY 60/60 PLUS; bez zmian danych postaci w ZIP.',
    ]+LATEST_CHANGES
    import sys as _sys9800
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys9800.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v99: five real Admin Live extensions, preserving earlier releases.
if VERSION == '99.00.0':
    LATEST_CHANGES_TITLE='Soulbound v99.00.0 - Piec rozszerzen Admin Live'
    LATEST_CHANGES=[
        'v99.00.0: pomoc 60/61 - nowe deklaratywne skille i kontrolowane naprawy questow w DRAFT.',
        'v99.00.0: pomoc 62 - osobny silnik areny na prywatnej migawce SQLite.',
        'v99.00.0: pomoc 63 - korekta HP/many online poza walka, audyt i cofanie.',
        'v99.00.0: pomoc 64 - fazowa regeneracja UOSS w prawdziwej petli walki.',
        'v99.00.0: przed wdrozeniem wykonaj Windows PREDEPLOY 60/60 PLUS.',
    ]+LATEST_CHANGES
    import sys as _sys9900
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys9900.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v100: source-backed, explicitly bounded Admin Live additions.
if VERSION == '100.00.0':
    LATEST_CHANGES_TITLE='Soulbound v100.00.0 - Admin Live Ultimate: 5 bezpiecznych rozszerzen'
    LATEST_CHANGES=[
        'v100.00.0: pomoc 65 - kopiowanie skilli z katalogu jako walidowany nowy DRAFT.',
        'v100.00.0: pomoc 66 - audyt questow NPC, zaleznosci, cykle i aktywne postepy.',
        'v100.00.0: pomoc 67 - CAS edycja podstawowych statystyk postaci ONLINE poza walka i raport rozwoju.',
        'v100.00.0: pomoc 68 - w-sesji arena LAB; osobny pelny serwer nadal dostepny przez arena real.',
        'v100.00.0: pomoc 69 - nowe fazowe AI UOSS: celowanie i oslabianie many w prawdziwej walce.',
        'v100.00.0: wymagany Windows PREDEPLOY 60/60 PLUS; bez dowolnych skryptow Python.',
    ]+LATEST_CHANGES
    import sys as _sys10000
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys10000.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v102: native full-engine isolated tunnel, declarative mechanic conditions, audited Admin Live.
if VERSION in ('102.00.0', '102.00.1', '102.00.2', '102.00.3', '102.00.4', '102.00.5'):
    LATEST_CHANGES_TITLE=f'Soulbound v{VERSION} - Admin Live: pelny silnik przez tunel, efekty, audyt'
    LATEST_CHANGES=[
        'v102.00.5: automatyczne usuwanie osmiu starych README z bezpieczna kopia poza folderem gry.',
        'v102.00.4: jeden plik README zamiast 8; bez zmian gry i bez omijania testow.',
        'v102.00.3: poprawka licznika 52 testow Admin Live v102 w PREDEPLOY, bez zmian gry.',
        'v102.00.2: czytelna obsluga rozlaczen tunelu i zgodnosc komendy admin live audyt z OLC5.',
        'v102.00.1: naprawa identyfikatora wydania i odcisku kontrolnego modularizacji (bez zmian walki).',
        'v102.00.0: pomoc 74 - arena real tunel POTWIERDZAM w tym samym kliencie, silnik 1:1 nadal na izolowanej kopii.',
        'v102.00.0: pomoc 75 - nowe conditions oraz restore_health w kompozytorze mechanik, OLC DRAFT i publikacja.',
        'v102.00.0: pomoc 76 - audyt raport/komendy/olc/arena, tylko odczyt; raport nie jest certyfikatem.',
        'v102.00.0: brak obcego Pythona; produkcyjna baza i nagrody pozostaja poza arena.',
        'v102.00.0: pelny PREDEPLOY Windows 60/60 PLUS wymagany.',
    ]+LATEST_CHANGES
    import sys as _sys10200
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys10200.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

# v101: three bounded expansions. No code execution or unsafe direct in-session full combat.
if VERSION == '101.00.0':
    LATEST_CHANGES_TITLE='Soulbound v101.00.0 - Admin Live: mechaniki, rozwoj online, arena LAB'
    LATEST_CHANGES=[
        'v101.00.0: pomoc 70 - kompozytor fazowych mechanik bossow przez JSON, plan DRAFT, publikacja OLC bez restartu.',
        'v101.00.0: pomoc 71 - postacie online rozwoj: level/EXP postaci, duszy, broni, SQLite+sesja CAS.',
        'v101.00.0: pomoc 73 - online wpisy: istniejace klasy, skille, profesje, narzedzia, EXP bank i niechronione stosy.',
        'v101.00.0: pomoc 72 - arena sesja seria i porownaj, izolowane testy LAB bez nagrod.',
        'v101.00.0: pelny silnik 1:1 nadal izolowany, wymaga osobnego klienta na porcie 4900.',
        'v101.00.0: wymagany PREDEPLOY 60/60 PLUS na Windows i backup SQLite/WAL przed wdrozeniem.',
    ]+LATEST_CHANGES
    import sys as _sys10100
    for _name in ('systems.content_registry','player.session_mixins.help_system'):
        _loaded=_sys10100.modules.get(_name)
        if _loaded is not None:
            _loaded.LATEST_CHANGES_TITLE=LATEST_CHANGES_TITLE
            _loaded.LATEST_CHANGES=LATEST_CHANGES

if __name__ == '__main__':
    main()

