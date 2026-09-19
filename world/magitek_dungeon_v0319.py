# v0.31.9 - Magitek Dungeon 2.0
MAGITEK_DUNGEON_ZONE = "Kompleks Magitek 2.0"

# Extend the existing complex with four deeper sectors, elevators and boss checkpoints.
ROOMS.setdefault("magitek_omega_chamber", {}).setdefault("exits", {})["down"] = "magitek_sector1_lift"

_v0319_rooms = {
    "magitek_sector1_lift": ("Winda Sektora Alfa", "Ciężka winda schodzi pod fabrykę. Terminal wskazuje sektory Alfa, Beta, Gamma i Rdzeń Zero.", {"up":"magitek_omega_chamber","east":"magitek_alpha_entry"}, 180),
    "magitek_alpha_entry": ("Sektor Alfa — Kontrola", "Pierwsza podziemna linia produkcyjna pełna patroli i skanerów.", {"west":"magitek_sector1_lift","east":"magitek_alpha_lines"}, 185),
    "magitek_alpha_lines": ("Sektor Alfa — Linie Montażowe", "Automatyczne ramiona składają nowe jednostki bojowe.", {"west":"magitek_alpha_entry","east":"magitek_alpha_boss"}, 195),
    "magitek_alpha_boss": ("Sektor Alfa — Komora Strażnika", "Pole blokujące zamyka drogę do windy Beta.", {"west":"magitek_alpha_lines","down":"magitek_beta_lift"}, 205),
    "magitek_beta_lift": ("Winda Sektora Beta", "Winda wibruje od przeciążenia chłodzenia.", {"up":"magitek_alpha_boss","east":"magitek_beta_cooling"}, 220),
    "magitek_beta_cooling": ("Sektor Beta — Chłodzenie", "Kriogeniczne przewody otaczają korytarz.", {"west":"magitek_beta_lift","east":"magitek_beta_armory"}, 230),
    "magitek_beta_armory": ("Sektor Beta — Zbrojownia", "Wyrzutnie i zapasowe pancerze czekają na aktywację.", {"west":"magitek_beta_cooling","east":"magitek_beta_boss"}, 240),
    "magitek_beta_boss": ("Sektor Beta — Platforma Oblężnicza", "Ciężka platforma blokuje dalszy zjazd.", {"west":"magitek_beta_armory","down":"magitek_gamma_lift"}, 250),
    "magitek_gamma_lift": ("Winda Sektora Gamma", "Ściany windy pokrywają runiczne przewody Magitek.", {"up":"magitek_beta_boss","east":"magitek_gamma_lab"}, 270),
    "magitek_gamma_lab": ("Sektor Gamma — Laboratorium", "Terminale testują połączenie magii i maszyn.", {"west":"magitek_gamma_lift","east":"magitek_gamma_reactor"}, 285),
    "magitek_gamma_reactor": ("Sektor Gamma — Reaktor Runiczny", "Runiczne rdzenie pulsują niestabilną energią.", {"west":"magitek_gamma_lab","east":"magitek_gamma_boss"}, 300),
    "magitek_gamma_boss": ("Sektor Gamma — Węzeł Dowodzenia", "Centralny Warden steruje niższymi poziomami.", {"west":"magitek_gamma_reactor","down":"magitek_zero_lift"}, 320),
    "magitek_zero_lift": ("Winda Rdzenia Zero", "Ostatnia winda schodzi pod główny reaktor.", {"up":"magitek_gamma_boss","east":"magitek_zero_corridor"}, 340),
    "magitek_zero_corridor": ("Rdzeń Zero — Korytarz Omega", "Ściany reagują na każdy ruch i zamykają się za intruzem.", {"west":"magitek_zero_lift","east":"magitek_zero_core"}, 355),
    "magitek_zero_core": ("Rdzeń Zero", "Pierwotny rdzeń kompleksu podtrzymuje tysiące uśpionych maszyn.", {"west":"magitek_zero_corridor","east":"magitek_zero_final"}, 370),
    "magitek_zero_final": ("Archiwum WarMecha", "Najgłębsza komora przechowuje finalny prototyp systemu WarMech.", {"west":"magitek_zero_core"}, 390),
}
for _rid,(_name,_desc,_exits,_lvl) in _v0319_rooms.items():
    ROOMS[_rid]={"zone":MAGITEK_DUNGEON_ZONE,"name":_name,"desc":_desc,"exits":dict(_exits),"generator_level":_lvl}

# New authored bosses / variants for the deeper dungeon.
_v0319_mobs={
    "machine_alpha_overseer": _machine_template("Nadzorca Alfa", 9800,205,205,{"machine_targeting_chip":.75,"machine_magitek_core":.45},boss=True),
    "machine_beta_siege_lord": _machine_template("Władca Oblężniczy Beta", 12800,235,250,{"machine_plating":1.0,"machine_warmech_core":.55},boss=True),
    "machine_gamma_archon": _machine_template("Runiczny Archont Gamma", 16800,265,320,{"machine_magitek_core":1.0,"machine_moogle_alloy":.55},boss=True,magic=True),
    "machine_zero_warmech": _machine_template("WarMech Zero", 24000,315,390,{"machine_warmech_core":1.0,"machine_magitek_core":1.0,"machine_moogle_alloy":.90},boss=True,magic=True),
}
for _tid,_data in _v0319_mobs.items():
    _data["boss_mechanic"]="magitek_v0319"
    _data["boss_mechanic_text"]="Magitek Dungeon 2.0: wielofazowy boss Machine; Lightning/EMP pozostaje jego główną słabością."
MOB_TEMPLATES.update(_v0319_mobs)

_v0319_spawns=[
 ("magitek_alpha_entry","machine_hunter_killer"),("magitek_alpha_lines","machine_siege_automaton"),("magitek_alpha_lines","machine_assault_drone"),("magitek_alpha_boss","machine_alpha_overseer"),
 ("magitek_beta_cooling","machine_shock_drone"),("magitek_beta_armory","machine_vulcan_unit"),("magitek_beta_armory","machine_torpedo_frame"),("magitek_beta_boss","machine_beta_siege_lord"),
 ("magitek_gamma_lab","machine_warden"),("magitek_gamma_reactor","machine_runic_engine"),("magitek_gamma_reactor","machine_core_defender"),("magitek_gamma_boss","machine_gamma_archon"),
 ("magitek_zero_corridor","machine_overclocked_guard"),("magitek_zero_core","machine_nuclear_platform"),("magitek_zero_core","machine_core_guardian"),("magitek_zero_final","machine_zero_warmech"),
]
MOB_SPAWNS.extend(_v0319_spawns)

HELP_TOPICS["magitek dungeon"]=[
 "Magitek Dungeon 2.0 zaczyna się zejściem z Komory Omega w Kompleksie Magitek.",
 "Cztery sektory: Alfa, Beta, Gamma i Rdzeń Zero. Każdy kończy się bossem i windą do kolejnego poziomu.",
 "Poziom trudności rośnie mniej więcej od 180 do 390 Biegłości/progresji generatora. Machine są słabe na Lightning/EMP.",
]
HELP_TOPIC_ALIASES.update({"magitek dungeon":"magitek dungeon","magitek 2":"magitek dungeon","dungeon magitek":"magitek dungeon"})
