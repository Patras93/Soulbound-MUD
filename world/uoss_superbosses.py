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
    return str(profile["name"])


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


# v1.11.33: UOSS superbosses are no longer injected into Mythic Crypt/Astral
# milestone bosses. They are unique world encounters with their own unlock,
# helper and per-cycle reward rules. Mythic dungeons keep their native scalable
# bosses instead of borrowing UOSS identities every ten floors.
UOSS_SUPERBOSS_ENCOUNTERS_V11134 = {
    "spekkio": {"name":"Spekkio","mode":"solo","scales_to_player":True,"unlock_level":1},
    "asterisks": {"name":"Asterisks","mode":"solo","unlock_level":80,"series":True},
    "dad": {"name":"Dad","mode":"solo","unlock_level":80},
    "diabolos": {"name":"Diabolos","mode":"solo","unlock_level":80},
    "harle": {"name":"Harle","mode":"solo_or_party","unlock_level":85},
    "culex": {"name":"Culex","mode":"party","unlock_level":100},
    "ruby_weapon": {
        "name":"Ruby WEAPON","mode":"party","area":"Corel Prison","unlock_level":100,"recommended_level":100,
        "personal_token":"Desert Rose","weapon_pair":"emerald_weapon",
        "pair_shop":"Traveler w Kalm","lockout_hours":24,
    },
    "emerald_weapon": {
        "name":"Emerald WEAPON","mode":"party","area":"On the Sea Floor","access_via":"Submarine on Junon Overland outside Lower Junon","unlock_level":100,"recommended_level":100,
        "personal_token":"Earth Harp","weapon_pair":"ruby_weapon",
        "pair_shop":"Traveler w Kalm","lockout_hours":24,
    },
    "ozma": {"name":"Ozma","mode":"solo","unlock_level":110},
    "four_fiends": {"name":"Four Fiends","mode":"solo","unlock_level":110,"series":True},
    "grahf": {"name":"Grahf","mode":"solo","unlock_level":110},
    "hades": {"name":"Hades","mode":"solo","unlock_level":110,"crafting_master":True},
    "lunar_trial": {"name":"Lunar Trial","mode":"solo","unlock_level":115,"series":True},
    "elementals": {"name":"Elementals","mode":"solo","unlock_level":120,"series":True,"required_wins":8,"unlocks_final_foe":True},
    "gilgamesh": {"name":"Gilgamesh","mode":"solo","unlock_level":120},
    "war_machines": {"name":"War Machines","mode":"solo_or_party","unlock_level":125},
    "black_rabite": {
        "name":"Black Rabite","mode":"party","area":"Rabite Field","unlock_level":100,
        "recommended_level":125,"helpers":("Primm","Popoi"),"helper_choice_limit":1,"helper_max_players":3,"helper_cost_mithril":1,
        "helper_join_phrases":{"Popoi":"Join me, Popoi","Primm":"Join me, Primm"},
        "personal_token":"Moogle Steel","shared_unique_drop":True,"unique_drop_count":10,
        "cyborg_conditional_drop":True,"pickup_binds":True,"lockout_hours":24,
    },
    "serpentarius": {
        "name":"Serpentarius","mode":"party","area":"Deep Dungeon","unlock":"explore_deep_dungeon","round_limit":100,"no_exit_after_start":True,"helper_cost_mithril":1,"helper_join_phrase":"Join me, Byblos",
        "arena":"Deep Dungeon — piętro 0","recommended_level":125,"helper":"Byblos","helper_max_players":3,
        "personal_token":"Serpentarius Emblem","party_members_must_unlock":True,"lockout_hours":24,
    },
    "odin": {
        "name":"Odin","mode":"party","area":"A Clearing in a Misty Forest","unlock_level":100,"recommended_level":125,
        "min_players":3,"max_players":5,"difficulty_scales_above_players":3,
        "helper":"Seifer","helper_max_players":3,"helper_cost_mithril":1,"helper_join_phrase":"Join me, Seifer.",
        "personal_token":"Odin's Mantle","shared_unique_drop":True,"unique_drop_count":8,
        "pickup_binds":True,"shop":"Fur Trader w Elsendor — Odin tier","lockout_hours":24,
    },
    "yiazmat": {
        "name":"Yiazmat","mode":"party","area":"Ridorana Cataract Colosseum","access_via":"Lighthouse near Tasnica","unlock_level":100,
        "recommended_level":125,"helper":"Montblanc","helper_max_players":3,"helper_cost_mithril":1,
        "personal_token":"Godslayer's Badge","shared_unique_drop":True,"unique_drop_count":7,
        "pickup_binds":True,"shop":"Fur shop w Elsendor — Yiazmat tier","lockout_hours":24,
    },
    "sephiroth": {"name":"Sephiroth","mode":"solo","unlock_level":130},
}
# Compatibility alias for code introduced in v1.11.33.
UOSS_SUPERBOSS_ENCOUNTERS_V11133 = UOSS_SUPERBOSS_ENCOUNTERS_V11134

# Player-facing help. Category/group page labels are explicitly documented as
# not being boss names so the mistake cannot silently return later.
HELP_TOPICS["superbossy"] = [
    "Superbossy UOSSMUD są unikalnymi wyzwaniami świata, a nie rotacją bossów Mitycznej Krypty/Wierzy.",
    "Dostępne są wyzwania solo, solo/party i party. Minimalny próg nie oznacza zalecanego poziomu.",
    "Black Rabite: każdy uczestnik dostaje własny losowy drop z 10 przedmiotów + Moogle Steel; przy maks. 3 graczach można za 1 mithril zatrudnić Primm albo Popoi.",
    "Serpentarius: wymaga osobistego odblokowania Deep Dungeon; każdy uczestnik dostaje Serpentarius Emblem; przy maks. 3 graczach pomaga Byblos.",
    "Odin: Level 100+, drużyna 3-5; 8 unikalnych dropów + Odin's Mantle dla każdego uczestnika; przy 4-5 graczach trudność rośnie.",
    "Yiazmat: 7 unikalnych dropów + Godslayer's Badge dla każdego uczestnika; przy maks. 3 graczach pomaga Montblanc.",
    "Każdy źródłowy Super Boss ma 24-godzinny lockout liczony od pokonania; restart ani deploy Railway nie resetuje czasu.",
]
HELP_TOPIC_ALIASES.update({
    "superboss": "superbossy", "superbosses": "superbossy", "uossbosses": "superbossy",
    "uoss boss": "superbossy", "uoss bosses": "superbossy",
})


def uoss_superboss_audit_v11134():
    errors = []
    encounters = UOSS_SUPERBOSS_ENCOUNTERS_V11134
    required = {
        "spekkio","asterisks","dad","diabolos","harle","culex","ruby_weapon",
        "emerald_weapon","ozma","four_fiends","grahf","hades","lunar_trial",
        "elementals","gilgamesh","war_machines","black_rabite","serpentarius",
        "odin","yiazmat","sephiroth",
    }
    missing = sorted(required - set(encounters))
    if missing:
        errors.append("missing unique encounters: " + ", ".join(missing))
    for key in ("ruby_weapon","emerald_weapon","black_rabite","serpentarius","odin","yiazmat"):
        row = encounters.get(key, {})
        if not row.get("lockout_hours"):
            errors.append(f"{key}: missing 24-hour lockout")
        if not row.get("personal_token"):
            errors.append(f"{key}: missing personal participation reward")
    if encounters.get("black_rabite", {}).get("unique_drop_count") != 10:
        errors.append("black_rabite: expected 10 unique drops")
    if encounters.get("yiazmat", {}).get("unique_drop_count") != 7:
        errors.append("yiazmat: expected 7 unique drops")
    return {"version":"1.11.34","encounter_count":len(encounters),"error_count":len(errors),"errors":errors}


UOSS_SUPERBOSS_AUDIT_V11134 = uoss_superboss_audit_v11134()
UOSS_SUPERBOSS_AUDIT_V0366 = UOSS_SUPERBOSS_AUDIT_V11134
if UOSS_SUPERBOSS_AUDIT_V11134["error_count"]:
    raise RuntimeError(
        "UOSSMUD Superboss Audit v1.11.34 failed: "
        + "; ".join(UOSS_SUPERBOSS_AUDIT_V11134["errors"][:50])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v1.11.34: Superbossy UOSSMUD są unikalnymi wyzwaniami świata; dodano pełny katalog trybów oraz reguły Black Rabite, Serpentariusa i Yiazmata."
)
LATEST_CHANGES_TITLE = "Soulbound v0.36.6 - Correct UOSSMUD Named Superbosses"
LATEST_CHANGES = [
    "Dodano prawidłową rotację konkretnych nazwanych Superbossów UOSSMUD do Mitycznej Krypty i Mitycznej Wieży Astralnej.",
    "Asterisks, Lunar Trials, Elementals i Four Fiends są traktowane jako strony/grupy/serie, a nie jako nazwy pojedynczych bossów.",
    "Lunar Trials rozbito na konkretnych bossów: Lunar Ifrit, Shiva, Ramuh, Asura, Leviathan, Dragon, Titan, Odin i Bahamut.",
    "Superbossy występują co 10 poziomów również powyżej ręcznie przygotowanej części lochów, zachowując bramki, fazy, Boss Codex i drużynowy loot.",
    "Dodano audit v0.36.6, który blokuje powrót zbiorczych nazw jako pojedynczych mobów.",
]
