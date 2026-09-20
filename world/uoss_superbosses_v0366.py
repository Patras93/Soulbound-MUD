# -*- coding: utf-8 -*-
"""Soulbound v0.36.6 - corrected UOSSMUD named superboss rotation.

Only concrete boss names are used. UOSS wiki navigation groups such as
"Asterisks", "Lunar Trials", "Elementals" and "Four Fiends" are deliberately
NOT used as mob names.
"""

UOSS_SUPERBOSS_ROSTER_V0366 = (
    # Direct named UOSSMUD superbosses / superboss mission encounters.
    {"name": "Black Rabite", "mechanic": "comet_evade", "damage_type": "physical", "hp": 1.08, "damage": 1.10,
     "text": "Black Rabite porusza się nienaturalnie szybko; okresowo unika trafień i odpowiada gwałtowną serią ciosów."},
    {"name": "Culex", "mechanic": "astral_shift", "damage_type": "magic", "hp": 1.10, "damage": 1.12,
     "text": "Culex przełącza się między fazą fizyczną i magiczną, zmieniając charakter kontrataków."},
    {"name": "Dad", "mechanic": "iron_bones", "damage_type": "physical", "hp": 1.16, "damage": 1.08,
     "text": "Dad ma wyjątkowo twardą obronę; regularnie redukuje otrzymywane trafienia."},
    {"name": "Diabolos", "mechanic": "black_flame", "damage_type": "magic", "hp": 1.10, "damage": 1.15,
     "text": "Diabolos odpowiada Czarnym Płomieniem, który częściowo omija obronę magiczną."},
    {"name": "Emerald Weapon", "mechanic": "firmament_guard", "damage_type": "physical", "hp": 1.25, "damage": 1.08,
     "text": "Emerald Weapon wzmacnia pancerz w regularnych odstępach i wymaga długiej, stabilnej walki."},
    {"name": "Grahf", "mechanic": "bone_rage", "damage_type": "physical", "hp": 1.12, "damage": 1.18,
     "text": "Grahf wpada w coraz większą furię, gdy jego HP spada poniżej połowy."},
    {"name": "Hades", "mechanic": "abyss_queen", "damage_type": "magic", "hp": 1.14, "damage": 1.14,
     "text": "Hades używa mrocznego drenażu, który zadaje obrażenia i odnawia część jego HP."},
    {"name": "Odin", "mechanic": "giant_crush", "damage_type": "physical", "hp": 1.10, "damage": 1.20,
     "text": "Odin okresowo wykonuje wyjątkowo ciężki fizyczny kontratak."},
    {"name": "Ozma", "mechanic": "astral_sovereign", "damage_type": "magic", "hp": 1.22, "damage": 1.18,
     "text": "Ozma kumuluje astralną energię; kolejne fazy znacząco wzmacniają jego magiczne odpowiedzi."},
    {"name": "Ruby Weapon", "mechanic": "grave_shield", "damage_type": "physical", "hp": 1.20, "damage": 1.12,
     "text": "Ruby Weapon cyklicznie wzmacnia osłonę i redukuje część nadchodzących obrażeń."},
    {"name": "Sephiroth", "mechanic": "final_guardian", "damage_type": "physical", "hp": 1.15, "damage": 1.22,
     "text": "Sephiroth staje się znacznie groźniejszy w końcowej części walki."},
    {"name": "Serpentarius", "mechanic": "void_regen", "damage_type": "magic", "hp": 1.22, "damage": 1.12,
     "text": "Serpentarius okresowo regeneruje część maksymalnego HP."},
    {"name": "Yiazmat", "mechanic": "endless_echo", "damage_type": "physical", "hp": 1.30, "damage": 1.15,
     "text": "Yiazmat jest maratonem wytrzymałości; co kilka odpowiedzi wyzwala wyjątkowo silne Echo."},
    {"name": "Nova Dragon", "mechanic": "starfire", "damage_type": "magic", "hp": 1.15, "damage": 1.18,
     "text": "Nova Dragon cyklicznie wyzwala gwiezdny ogień o zwiększonej sile."},
    {"name": "Doomtrain", "mechanic": "ash_curse", "damage_type": "magic", "hp": 1.18, "damage": 1.14,
     "text": "Doomtrain nakłada wyniszczające przekleństwo w regularnych odstępach walki."},
    {"name": "Th'uban", "mechanic": "stellar_storm", "damage_type": "magic", "hp": 1.18, "damage": 1.18,
     "text": "Th'uban okresowo przywołuje Gwiezdną Burzę jako wzmocniony kontratak."},

    # Concrete bosses from the UOSSMUD Lunar Eidolons page.
    {"name": "Lunar Ifrit", "mechanic": "black_flame", "damage_type": "magic", "hp": 1.14, "damage": 1.18,
     "text": "Lunar Ifrit walczy ogniem i odpowiada silnym magicznym płomieniem."},
    {"name": "Lunar Shiva", "mechanic": "crystal_lord", "damage_type": "magic", "hp": 1.14, "damage": 1.16,
     "text": "Lunar Shiva tworzy lodową barierę, która okresowo ogranicza otrzymywane obrażenia."},
    {"name": "Lunar Ramuh", "mechanic": "starfire", "damage_type": "magic", "hp": 1.16, "damage": 1.18,
     "text": "Lunar Ramuh gromadzi energię błyskawic i okresowo wyzwala wzmocniony magiczny cios."},
    {"name": "Lunar Asura", "mechanic": "abyss_queen", "damage_type": "magic", "hp": 1.18, "damage": 1.12,
     "text": "Lunar Asura łączy presję magiczną z samoleczeniem w dłuższej walce."},
    {"name": "Lunar Leviathan", "mechanic": "nebula_drain", "damage_type": "magic", "hp": 1.18, "damage": 1.16,
     "text": "Lunar Leviathan uderza falami energii i okresowo odzyskuje część sił."},
    {"name": "Lunar Dragon", "mechanic": "ethereal_evade", "damage_type": "magic", "hp": 1.16, "damage": 1.15,
     "text": "Lunar Dragon otacza się mgłą, dzięki której może uniknąć części trafień."},
    {"name": "Lunar Titan", "mechanic": "iron_bones", "damage_type": "physical", "hp": 1.24, "damage": 1.15,
     "text": "Lunar Titan ma ogromną wytrzymałość i okresowo silnie redukuje nadchodzące trafienia."},
    {"name": "Lunar Odin", "mechanic": "giant_king", "damage_type": "physical", "hp": 1.18, "damage": 1.22,
     "text": "Lunar Odin przyspiesza w późniejszych fazach i odpowiada ciężkimi seriami fizycznymi."},
    {"name": "Lunar Bahamut", "mechanic": "astral_sovereign", "damage_type": "magic", "hp": 1.26, "damage": 1.22,
     "text": "Lunar Bahamut kumuluje potężną astralną energię; końcowe fazy są szczególnie niebezpieczne."},
)

UOSS_SUPERBOSS_FORBIDDEN_CATEGORY_NAMES_V0366 = (
    "Asterisks", "Lunar Trials", "Elementals", "Four Fiends",
)


def uoss_superboss_profile_v0366(kind, floor):
    floor = max(10, int(floor))
    step = max(0, floor // 10 - 1)
    # Offset keeps the two Mythic dungeons from showing the same boss on the
    # same threshold while preserving one endless deterministic rotation.
    offset = 0 if str(kind) == "mythic_crypt" else 9
    return UOSS_SUPERBOSS_ROSTER_V0366[(step + offset) % len(UOSS_SUPERBOSS_ROSTER_V0366)]


def uoss_superboss_display_name_v0366(kind, floor):
    profile = uoss_superboss_profile_v0366(kind, floor)
    if str(kind) == "mythic_crypt":
        return f"{profile['name']} — Mityczna Krypta, piętro {int(floor)}"
    return f"{profile['name']} — Mityczna Wieża Astralna, poziom {int(floor)}"


def _apply_uoss_superboss_v0366(template, kind, floor, scale_stats=True):
    if not isinstance(template, dict):
        return template
    profile = uoss_superboss_profile_v0366(kind, floor)
    template["name"] = uoss_superboss_display_name_v0366(kind, floor)
    template["boss_mechanic"] = profile["mechanic"]
    template["boss_mechanic_text"] = profile["text"]
    template["damage_type"] = profile["damage_type"]
    template["uoss_superboss"] = True
    template["uoss_superboss_name"] = profile["name"]
    template["uoss_superboss_floor"] = int(floor)
    template["uoss_superboss_kind"] = str(kind)
    # Superbosses are meant to sit clearly above an ordinary Mythic floor boss.
    # The marker prevents double scaling when lazy floor helpers are called more
    # than once for the same floor.
    if scale_stats and not template.get("uoss_superboss_scaled_v0366"):
        hp_mult = 2.20 * float(profile["hp"])
        dmg_mult = 1.28 * float(profile["damage"])
        for field in ("max_hp", "base_max_hp"):
            if int(template.get(field, 0) or 0) > 0:
                template[field] = max(1, int(round(int(template[field]) * hp_mult)))
        if int(template.get("damage", 0) or 0) > 0:
            template["damage"] = max(1, int(round(int(template["damage"]) * dmg_mult)))
        for field in ("class_xp_reward", "soul_reward", "stat_reward"):
            if int(template.get(field, 0) or 0) > 0:
                template[field] = max(1, int(round(int(template[field]) * 1.75)))
        template["corpse_equipment_guaranteed"] = max(
            5, int(template.get("corpse_equipment_guaranteed", 0) or 0)
        )
        drops = dict(template.get("drops") or {})
        drops["soul_shard"] = 1.0
        drops["soul_elixir"] = max(0.85, float(drops.get("soul_elixir", 0.0) or 0.0))
        template["drops"] = drops
        template["uoss_superboss_scaled_v0366"] = True
    # Keep the v0.34.4+ canonical one-wallet economy invariant: runtime mobs
    # store rewards only in silver; gold/mithril are display denominations.
    if int(template.get("gold", 0) or 0) or int(template.get("mithril", 0) or 0):
        _silver, _gold, _mithril = normalize_currency_values(
            template.get("silver", 0), template.get("gold", 0), template.get("mithril", 0)
        )
        template["silver"], template["gold"], template["mithril"] = _silver, _gold, _mithril
    return template


# Patch all already-built Mythic boss thresholds (normally 10..200).
for _floor in range(10, int(MYTHIC_MAX_FLOOR) + 1, 10):
    _crypt = MOB_TEMPLATES.get(f"mythic_crypt_boss_{_floor}")
    if _crypt:
        _apply_uoss_superboss_v0366(_crypt, "mythic_crypt", _floor, True)
    _astral = MOB_TEMPLATES.get(f"mythic_astral_boss_{_floor}")
    if _astral:
        _apply_uoss_superboss_v0366(_astral, "mythic_astral", _floor, True)


# Preserve the concrete UOSS boss identity on lazy-generated milestone floors.
_milestone_boss_name_before_v0366 = milestone_boss_name

def milestone_boss_name(kind, floor, default_name):
    if str(kind) in ("mythic_crypt", "mythic_astral") and is_crypt_boss_floor(floor):
        return uoss_superboss_display_name_v0366(kind, floor)
    return _milestone_boss_name_before_v0366(kind, floor, default_name)


def _infinite_mythic_boss_profile(floor):
    profile = uoss_superboss_profile_v0366("mythic_crypt", floor)
    return (
        uoss_superboss_display_name_v0366("mythic_crypt", floor),
        profile["mechanic"],
        profile["text"],
    )


def _dynamic_mythic_astral_boss_profile(floor):
    profile = uoss_superboss_profile_v0366("mythic_astral", floor)
    return (
        uoss_superboss_display_name_v0366("mythic_astral", floor),
        profile["mechanic"],
        profile["text"],
    )


_create_infinite_crypt_floor_definition_before_v0366 = create_infinite_crypt_floor_definition

def create_infinite_crypt_floor_definition(floor, mythic=False):
    result = _create_infinite_crypt_floor_definition_before_v0366(floor, mythic=mythic)
    if mythic and is_mythic_crypt_boss_floor(floor):
        template = MOB_TEMPLATES.get(f"mythic_crypt_boss_{int(floor)}")
        if template:
            _apply_uoss_superboss_v0366(template, "mythic_crypt", int(floor), True)
    return result


_create_infinite_astral_floor_definition_before_v0366 = create_infinite_astral_floor_definition

def create_infinite_astral_floor_definition(floor, mythic=False):
    result = _create_infinite_astral_floor_definition_before_v0366(floor, mythic=mythic)
    if mythic and is_mythic_astral_boss_floor(floor):
        template = MOB_TEMPLATES.get(f"mythic_astral_boss_{int(floor)}")
        if template:
            _apply_uoss_superboss_v0366(template, "mythic_astral", int(floor), True)
    return result


# Player-facing help. Category/group page labels are explicitly documented as
# not being boss names so the mistake cannot silently return later.
HELP_TOPICS["superbossy"] = [
    "Superbossy UOSSMUD występują na progach co 10 w Mitycznej Krypcie i Mitycznej Wieży Astralnej.",
    "Używane są wyłącznie konkretne nazwy bossów. Asterisks, Lunar Trials, Elementals i Four Fiends nie są pojedynczymi nazwami mobów i nie występują jako bossowie Soulbound.",
    "Roster: " + ", ".join(entry["name"] for entry in UOSS_SUPERBOSS_ROSTER_V0366) + ".",
    "Każdy Superboss zachowuje bramkę pierwszego pokonania, fazy 75/50/25 procent, Boss Codex i drużynowe współdzielenie dropów.",
]
HELP_TOPIC_ALIASES.update({
    "superboss": "superbossy", "superbosses": "superbossy", "uossbosses": "superbossy",
    "uoss boss": "superbossy", "uoss bosses": "superbossy",
})


def uoss_superboss_audit_v0366():
    errors = []
    names = [entry["name"] for entry in UOSS_SUPERBOSS_ROSTER_V0366]
    if len(names) != len(set(name.casefold() for name in names)):
        errors.append("duplicate concrete boss name in UOSS roster")
    for forbidden in UOSS_SUPERBOSS_FORBIDDEN_CATEGORY_NAMES_V0366:
        if forbidden.casefold() in {name.casefold() for name in names}:
            errors.append(f"category/group label used as boss: {forbidden}")
    for floor in range(10, int(MYTHIC_MAX_FLOOR) + 1, 10):
        for kind, prefix in (
            ("mythic_crypt", "mythic_crypt_boss_"),
            ("mythic_astral", "mythic_astral_boss_"),
        ):
            template = MOB_TEMPLATES.get(prefix + str(floor))
            if not template:
                errors.append(f"missing {kind} boss floor {floor}")
                continue
            expected = uoss_superboss_profile_v0366(kind, floor)["name"]
            actual = str(template.get("uoss_superboss_name") or "")
            if actual != expected:
                errors.append(f"{kind} floor {floor}: {actual!r}, expected {expected!r}")
            if not template.get("uoss_superboss"):
                errors.append(f"{kind} floor {floor}: missing uoss_superboss flag")
            display = str(template.get("name") or "")
            for forbidden in UOSS_SUPERBOSS_FORBIDDEN_CATEGORY_NAMES_V0366:
                if display.casefold().startswith(forbidden.casefold()):
                    errors.append(f"{kind} floor {floor}: forbidden category name {display!r}")
    return {
        "version": "0.36.6",
        "roster_count": len(names),
        "roster": tuple(names),
        "error_count": len(errors),
        "errors": errors,
    }


UOSS_SUPERBOSS_AUDIT_V0366 = uoss_superboss_audit_v0366()
if UOSS_SUPERBOSS_AUDIT_V0366["error_count"]:
    raise RuntimeError(
        "UOSSMUD Superboss Audit v0.36.6 failed: "
        + "; ".join(UOSS_SUPERBOSS_AUDIT_V0366["errors"][:50])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.36.6: poprawiono UOSSMUD Superbosses. Asterisks/Lunar Trials/Elementals/Four Fiends nie są używane jako pojedyncze bossy; Mityczne Lochy rotują konkretne nazwane starcia."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.6 - Correct UOSSMUD Named Superbosses"
LATEST_CHANGES = [
    "Dodano prawidłową rotację konkretnych nazwanych Superbossów UOSSMUD do Mitycznej Krypty i Mitycznej Wieży Astralnej.",
    "Asterisks, Lunar Trials, Elementals i Four Fiends są traktowane jako strony/grupy/serie, a nie jako nazwy pojedynczych bossów.",
    "Lunar Trials rozbito na konkretnych bossów: Lunar Ifrit, Shiva, Ramuh, Asura, Leviathan, Dragon, Titan, Odin i Bahamut.",
    "Superbossy występują co 10 poziomów również powyżej ręcznie przygotowanej części lochów, zachowując bramki, fazy, Boss Codex i drużynowy loot.",
    "Dodano audit v0.36.6, który blokuje powrót zbiorczych nazw jako pojedynczych mobów.",
]
