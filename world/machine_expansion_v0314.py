# v0.31.4 - Machine Enemy Expansion
MACHINE_ZONE = "Kompleks Magitek"
MACHINE_BIO_IMMUNITIES = ("poison", "bleed", "sleep", "drain", "disease", "fear", "charm")

_MACHINE_ITEMS = {
    "machine_servo": ("Serwomechanizm", 18),
    "machine_plating": ("Płyta Pancerna", 24),
    "machine_circuit": ("Obwód Sterujący", 28),
    "machine_sensor": ("Sensor Optyczny", 32),
    "machine_power_cell": ("Ogniwo Zasilające", 38),
    "machine_targeting_chip": ("Chip Celowniczy", 45),
    "machine_actuator": ("Siłownik Magitek", 52),
    "machine_cooling_unit": ("Moduł Chłodzenia", 60),
    "machine_drone_core": ("Rdzeń Drona", 75),
    "machine_magitek_core": ("Rdzeń Magitek", 110),
    "machine_moogle_alloy": ("Stop Moogle", 140),
    "machine_warmech_core": ("Rdzeń WarMecha", 220),
}
for _iid, (_name, _sell) in _MACHINE_ITEMS.items():
    ITEMS[_iid] = {
        "name": _name, "type": "resource", "price": None, "sell_gold": _sell,
        "desc": "Technologiczny komponent odzyskany z przeciwników typu Machine.",
    }


def _machine_template(name, hp, dmg, level, drops=None, boss=False, magic=False, weaknesses=("lightning", "emp")):
    return {
        "name": name, "max_hp": int(hp), "damage": int(dmg),
        "damage_type": "magic" if magic else "physical",
        "silver": int(30 + level * 2.1), "gold": int(level // 25), "mithril": 0,
        "stat_reward": int(30 + level * 1.3),
        "class_xp_reward": int(250 + level * 32),
        "soul_reward": int(180 + level * 22),
        "drops": dict(drops or {}), "quest_target": None,
        "creature_type": "machine", "machine": True,
        "resistances": {"physical": 0.10, "magic": 0.10},
        "immunities": MACHINE_BIO_IMMUNITIES,
        "weaknesses": tuple(weaknesses),
        "auto_aggro": False,
        **({"world_boss": True, "machine_boss": True} if boss else {}),
    }

_MACHINE_MOBS = {
    "machine_scout": _machine_template("Zwiadowca Mechaniczny",260,22,35,{"machine_servo":.32,"machine_circuit":.14}),
    "machine_pipsqueak": _machine_template("Pipsqueak Mk-I",310,26,42,{"machine_servo":.38,"machine_power_cell":.10}),
    "machine_debug_unit": _machine_template("Debug Unit",390,31,50,{"machine_circuit":.35,"machine_sensor":.16}, magic=True),
    "machine_chaser": _machine_template("Chaser Patrolowy",470,35,58,{"machine_servo":.28,"machine_sensor":.22}),
    "machine_sentry": _machine_template("Magitek Sentry",560,40,66,{"machine_plating":.34,"machine_circuit":.20}),
    "machine_repair_drone": _machine_template("Dron Naprawczy",520,36,72,{"machine_circuit":.25,"machine_power_cell":.20}, magic=True),
    "machine_assault_drone": _machine_template("Dron Szturmowy",650,46,80,{"machine_targeting_chip":.22,"machine_servo":.30}),
    "machine_shock_drone": _machine_template("Dron Porażeniowy",690,49,86,{"machine_power_cell":.28,"machine_sensor":.18}, magic=True, weaknesses=("emp",)),
    "machine_carry_frame": _machine_template("Carry Frame",900,58,95,{"machine_plating":.40,"machine_actuator":.22}),
    "machine_loader": _machine_template("Automat Przeładunkowy",1040,62,105,{"machine_actuator":.32,"machine_plating":.30}),
    "machine_bio_sprayer": _machine_template("Opryskiwacz Bio-Magitek",920,64,112,{"machine_circuit":.24,"machine_power_cell":.20}, magic=True),
    "machine_rail_guard": _machine_template("Strażnik Szynowy",1180,70,120,{"machine_targeting_chip":.28,"machine_actuator":.24}),
    "machine_siege_automaton": _machine_template("Automat Oblężniczy",1450,78,132,{"machine_plating":.45,"machine_cooling_unit":.20}),
    "machine_arc_cannon": _machine_template("Działo Łukowe",1320,82,140,{"machine_power_cell":.36,"machine_targeting_chip":.24}, magic=True),
    "machine_hunter_killer": _machine_template("Hunter-Killer",1580,88,150,{"machine_sensor":.34,"machine_targeting_chip":.28}),
    "machine_core_defender": _machine_template("Obrońca Rdzenia",1850,96,162,{"machine_magitek_core":.10,"machine_plating":.42}),
    "machine_warden": _machine_template("Magitek Warden",2100,104,175,{"machine_magitek_core":.12,"machine_cooling_unit":.30}, magic=True),
    "machine_vulcan_unit": _machine_template("Vulcan Unit",2350,112,188,{"machine_warmech_core":.05,"machine_targeting_chip":.35}),
    "machine_torpedo_frame": _machine_template("Torpedo Frame",2500,118,200,{"machine_magitek_core":.14,"machine_actuator":.35}),
    "machine_runic_engine": _machine_template("Runiczny Silnik Bojowy",2700,126,215,{"machine_magitek_core":.18,"machine_moogle_alloy":.08}, magic=True),
    "machine_overclocked_guard": _machine_template("Przetaktowany Strażnik",2950,134,230,{"machine_cooling_unit":.36,"machine_moogle_alloy":.10}),
    "machine_nuclear_platform": _machine_template("Platforma Nuklearna",3300,145,245,{"machine_warmech_core":.10,"machine_power_cell":.45}, magic=True),
    "machine_proto_warmech": _machine_template("Prototyp WarMecha",6200,175,260,{"machine_warmech_core":.65,"machine_moogle_alloy":.20}, boss=True),
    "machine_carry_armor_prime": _machine_template("Carry Armor Prime",7600,190,285,{"machine_warmech_core":.70,"machine_actuator":.55,"machine_plating":.80}, boss=True),
    "machine_core_guardian": _machine_template("Strażnik Rdzenia Magitek",9200,210,320,{"machine_magitek_core":.85,"machine_moogle_alloy":.35}, boss=True, magic=True),
    "machine_magitek_weapon": _machine_template("Magitek Weapon Omega",12500,238,360,{"machine_warmech_core":1.0,"machine_magitek_core":1.0,"machine_moogle_alloy":.60}, boss=True, magic=True),
}
MOB_TEMPLATES.update(_MACHINE_MOBS)

# Entry from the artisan district.
ROOMS.setdefault("artisan_lane", {}).setdefault("exits", {})["northeast"] = "magitek_gate"
_machine_rooms = {
    "magitek_gate": ("Brama Kompleksu Magitek", "Stalowa brama prowadzi do opuszczonego kompleksu automatyki.", {"southwest":"artisan_lane","north":"magitek_yard"}),
    "magitek_yard": ("Dziedziniec Fabryczny", "Rdzawe szyny i nieruchome ramiona montażowe przecinają plac.", {"south":"magitek_gate","north":"magitek_assembly","east":"magitek_scrap"}),
    "magitek_scrap": ("Złomowisko Magitek", "Stosy pancerzy, serw i kabli tworzą metaliczny labirynt.", {"west":"magitek_yard","north":"magitek_power"}),
    "magitek_assembly": ("Hala Montażowa", "Taśmy transportowe nadal poruszają się bez obsługi.", {"south":"magitek_yard","north":"magitek_conveyor","east":"magitek_drone_bay"}),
    "magitek_drone_bay": ("Hangar Dronów", "Dziesiątki gniazd ładowania migają czerwonym światłem.", {"west":"magitek_assembly","north":"magitek_repair"}),
    "magitek_power": ("Rozdzielnia Zasilania", "Łuki energii przeskakują między odsłoniętymi przewodami.", {"south":"magitek_scrap","east":"magitek_repair","north":"magitek_reactor"}),
    "magitek_repair": ("Stacja Naprawcza", "Automatyczne ramiona nadal próbują naprawiać wszystko, co się porusza.", {"south":"magitek_drone_bay","west":"magitek_power","north":"magitek_security"}),
    "magitek_conveyor": ("Wielki Przenośnik", "Ciężkie platformy suną w stronę głębszych hal.", {"south":"magitek_assembly","north":"magitek_security"}),
    "magitek_security": ("Węzeł Bezpieczeństwa", "Wieżyczki śledzą każdy ruch, a stalowe drzwi prowadzą dalej.", {"south":"magitek_conveyor","east":"magitek_repair","north":"magitek_foundry"}),
    "magitek_reactor": ("Komora Reaktora", "Rdzeń energetyczny wypełnia halę niskim, pulsującym pomrukiem.", {"south":"magitek_power","east":"magitek_foundry"}),
    "magitek_foundry": ("Odlewnia Ram", "Formy ciężkich automatów stoją w płynnym świetle pieców.", {"south":"magitek_security","west":"magitek_reactor","north":"magitek_missile"}),
    "magitek_missile": ("Magazyn Rakiet", "Puste wyrzutnie i zamknięte głowice otaczają wąski pomost.", {"south":"magitek_foundry","north":"magitek_lab"}),
    "magitek_lab": ("Laboratorium Sterowania", "Rozbite terminale nadal przesyłają rozkazy do maszyn.", {"south":"magitek_missile","north":"magitek_core_approach"}),
    "magitek_core_approach": ("Podejście do Rdzenia", "Gruby pancerz i pola energetyczne chronią centrum kompleksu.", {"south":"magitek_lab","north":"magitek_core"}),
    "magitek_core": ("Rdzeń Kompleksu", "Gigantyczny rdzeń Magitek zasila ostatnie aktywne platformy bojowe.", {"south":"magitek_core_approach","north":"magitek_omega_chamber"}),
    "magitek_omega_chamber": ("Komora Omega", "Najgłębsza hala mieści broń, której system nigdy nie zdołał wyłączyć.", {"south":"magitek_core"}),
}
for _rid, (_name, _desc, _exits) in _machine_rooms.items():
    ROOMS[_rid] = {"zone": MACHINE_ZONE, "name": _name, "desc": _desc, "exits": dict(_exits), "generator_level": 120}

_MACHINE_SPAWNS = [
    ("magitek_gate","machine_scout"),("magitek_yard","machine_pipsqueak"),("magitek_yard","machine_chaser"),
    ("magitek_scrap","machine_debug_unit"),("magitek_scrap","machine_loader"),
    ("magitek_assembly","machine_sentry"),("magitek_assembly","machine_carry_frame"),
    ("magitek_drone_bay","machine_repair_drone"),("magitek_drone_bay","machine_assault_drone"),("magitek_drone_bay","machine_shock_drone"),
    ("magitek_power","machine_arc_cannon"),("magitek_power","machine_bio_sprayer"),
    ("magitek_repair","machine_repair_drone"),("magitek_repair","machine_rail_guard"),
    ("magitek_conveyor","machine_loader"),("magitek_conveyor","machine_siege_automaton"),
    ("magitek_security","machine_hunter_killer"),("magitek_security","machine_proto_warmech"),
    ("magitek_reactor","machine_runic_engine"),("magitek_reactor","machine_core_defender"),
    ("magitek_foundry","machine_vulcan_unit"),("magitek_foundry","machine_carry_armor_prime"),
    ("magitek_missile","machine_torpedo_frame"),("magitek_missile","machine_nuclear_platform"),
    ("magitek_lab","machine_overclocked_guard"),("magitek_lab","machine_warden"),
    ("magitek_core_approach","machine_core_defender"),("magitek_core","machine_core_guardian"),
    ("magitek_omega_chamber","machine_magitek_weapon"),
]
MOB_SPAWNS.extend(_MACHINE_SPAWNS)


def v0314_machine_attack_element(skill_name="", damage_kind=""):
    text = f"{skill_name} {damage_kind}".casefold()
    if any(x in text for x in ("bolt", "lightning", "piorun", "błyskaw", "shock", "emp", "poraż")):
        return "lightning"
    if any(x in text for x in ("bio", "poison", "truc", "bleed", "krwaw", "drain", "wysys")):
        return "biological"
    return "magic" if str(damage_kind).casefold() == "magic" else "physical"


def v0314_adjust_damage_vs_template(template, damage, damage_kind="physical", skill_name=""):
    """Actual combat modifier for Machine and future typed enemies."""
    amount = max(1, int(damage))
    if not isinstance(template, dict):
        return amount, ""
    element = v0314_machine_attack_element(skill_name, damage_kind)
    if template.get("machine") or str(template.get("creature_type","")).casefold() == "machine":
        if element == "lightning":
            return max(1, int(round(amount * 1.35))), " Słabość Machine: Lightning/EMP +35%."
        if element == "biological":
            return max(1, int(round(amount * 0.25))), " Odporność Machine: atak biologiczny -75%."
        reduction = float((template.get("resistances") or {}).get(element, 0.0) or 0.0)
        if reduction:
            return max(1, int(round(amount * (1.0 - reduction)))), f" Odporność Machine: {int(round(reduction*100))}%."
    return amount, ""

HELP_TOPICS["machine"] = [
    "Machine to mechaniczny typ przeciwnika. Maszyny są odporne na efekty biologiczne i mają podstawową odporność na zwykłe obrażenia.",
    "Lightning i EMP zadają maszynom zwiększone obrażenia. Ataki Bio/Poison/Drain są przeciw nim mocno osłabione.",
    "Kompleks Magitek zaczyna się na północny wschód od Ulicy Rzemieślników. Dropią tam serwa, obwody, sensory, ogniwa, rdzenie i inne komponenty technologiczne.",
]
HELP_TOPIC_ALIASES.update({"maszyny":"machine","machine":"machine","magitek":"machine","kompleks magitek":"machine"})
