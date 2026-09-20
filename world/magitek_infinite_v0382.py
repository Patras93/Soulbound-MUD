# -*- coding: utf-8 -*-
"""Soulbound v0.38.2 - Infinite Unified Magitek Dungeon.

Merges the authored Magitek Complex + Magitek Dungeon 2.0 into one zone and
adds an infinite, large-floor continuation after WarMech Zero's archive.
"""
import re as _re_v0382

V0382_MAGITEK_VERSION = "0.38.2"
MAGITEK_INFINITY_ZONE = "Nieskończony Kompleks Magitek"
MAGITEK_INFINITY_START_LEVEL = 110
MAGITEK_BOSS_INTERVAL = 10


def magitek_floor_id(floor):
    return f"magitek_floor_{max(1, int(floor))}"


def magitek_floor_number(room_id):
    m = _re_v0382.fullmatch(r"magitek_floor_(\d+)(?:_r\d+)?", str(room_id or ""))
    if not m:
        return None
    floor = int(m.group(1))
    return floor if floor >= 1 else None


def is_magitek_boss_floor(floor):
    try:
        floor = int(floor)
    except (TypeError, ValueError):
        return False
    return floor >= MAGITEK_BOSS_INTERVAL and floor % MAGITEK_BOSS_INTERVAL == 0


def magitek_floor_stage(floor):
    # Authored sectors previously covered roughly 120..390. Infinite floors
    # continue that curve up to the global 600 progression cap, then keep
    # growing through an uncapped depth multiplier.
    floor = max(1, int(floor))
    return min(CLASS_MASTERY_MAX_LEVEL, MAGITEK_INFINITY_START_LEVEL + floor * 7)


def magitek_floor_room_count(floor):
    # Large from floor 1 and grows further with depth: 12 rooms at the start,
    # up to 20 rooms from floor 201 onward.
    floor = max(1, int(floor))
    return 12 + min(8, (floor - 1) // 25)


def magitek_depth_multiplier(floor):
    floor = max(1, int(floor))
    return 1.0 + (floor - 1) * 0.018 + ((floor - 1) // 10) * 0.06


_MAGITEK_THEMES = (
    ("Sektor Alfa", "linie montażowe, skanery i szybkie automaty bojowe"),
    ("Sektor Beta", "chłodzenie kriogeniczne, zbrojownie i ciężkie platformy"),
    ("Sektor Gamma", "runiczne laboratoria i reaktory łączące magię z maszynami"),
    ("Rdzeń Zero", "przeciążone rdzenie, strażnicy Omega i prototypy WarMech"),
    ("Odlewnia Magitek", "piece ram, płynne stopy i automaty kuźnicze"),
    ("Sieć Dronów", "hangary, węzły naprawcze i roje autonomicznych dronów"),
    ("Archiwum Runiczne", "magitekowe pieczęcie, sensory i stare protokoły bojowe"),
    ("Reaktor Omega", "niestabilne ogniwa, działa łukowe i pola energetyczne"),
)

_MAGITEK_REGULAR_NAMES = (
    "Zwiadowca Nieskończonego Magitek",
    "Dron Szturmowy Nieskończonego Magitek",
    "Strażnik Szynowy Nieskończonego Magitek",
    "Runiczny Silnik Nieskończonego Magitek",
    "Przetaktowany Strażnik Nieskończonego Magitek",
    "Platforma Oblężnicza Nieskończonego Magitek",
    "Obrońca Rdzenia Nieskończonego Magitek",
    "Hunter-Killer Nieskończonego Magitek",
)

_MAGITEK_BOSS_NAMES = (
    "Prototyp WarMecha",
    "Carry Armor Prime",
    "Strażnik Rdzenia Magitek",
    "Magitek Weapon Omega",
    "Nadzorca Alfa",
    "Władca Oblężniczy Beta",
    "Runiczny Archont Gamma",
    "WarMech Zero",
)

_MAGITEK_BOSS_MECHANICS = (
    ("target_lock", "Blokada celu: boss okresowo wzmacnia następny precyzyjny atak."),
    ("siege_cycle", "Cykl oblężniczy: naprzemiennie wzmacnia pancerz i siłę ostrzału."),
    ("runic_overload", "Runiczne przeciążenie: fazy magiczne stają się groźniejsze wraz ze spadkiem HP."),
    ("warmech_zero", "WarMech Zero: wielofazowy protokół Omega; Lightning/EMP pozostaje główną słabością."),
)

_MAGITEK_COMPONENTS = (
    "machine_servo", "machine_plating", "machine_circuit", "machine_sensor",
    "machine_power_cell", "machine_targeting_chip", "machine_actuator",
    "machine_cooling_unit", "machine_drone_core", "machine_magitek_core",
    "machine_moogle_alloy", "machine_warmech_core",
)


def _v0382_magitek_gear_pool():
    pool = []
    for iid, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        low = str(iid).lower()
        name = str(item.get("name", "")).lower()
        if "magitek" in low or "magitek" in name or low.startswith("tech_"):
            pool.append(iid)
    return tuple(pool)


def _v0382_magitek_drop_table(floor, boss=False):
    floor = max(1, int(floor))
    unlocked = min(len(_MAGITEK_COMPONENTS), 4 + floor // 8)
    rows = list(_MAGITEK_COMPONENTS[:max(4, unlocked)])
    drops = {}
    for index, iid in enumerate(rows):
        # Deeper components become rarer; early salvage remains common.
        chance = max(0.07, 0.38 - index * 0.025 + min(0.18, floor / 1000.0))
        drops[iid] = min(1.0, round(chance * (1.65 if boss else 1.0), 4))
    if boss:
        drops["machine_magitek_core"] = 1.0
        drops["machine_warmech_core"] = max(0.55, drops.get("machine_warmech_core", 0.0))
        drops["soul_shard"] = 1.0
        drops["soul_elixir"] = 0.80
    return drops


def create_infinite_magitek_floor_definition(floor):
    floor = max(1, int(floor))
    stage = magitek_floor_stage(floor)
    depth = magitek_depth_multiplier(floor)
    theme_name, theme_desc = _MAGITEK_THEMES[(floor - 1) % len(_MAGITEK_THEMES)]
    room_id = magitek_floor_id(floor)
    exits = {
        "up": "magitek_zero_final" if floor == 1 else magitek_floor_id(floor - 1),
        "down": magitek_floor_id(floor + 1),
    }
    boss_note = (
        " Na końcu piętra działa boss-protokół blokujący dalszy zjazd przy pierwszym pokonaniu."
        if is_magitek_boss_floor(floor) else ""
    )
    ROOMS[room_id] = {
        "zone": MAGITEK_INFINITY_ZONE,
        "name": f"Nieskończony Kompleks Magitek, piętro {floor} — {theme_name}",
        "desc": (
            f"Piętro {floor}. Motyw: {theme_name}; {theme_desc}. "
            f"Zalecany etap około {stage}. To rozległe piętro z pętlami, bocznymi komorami "
            f"i wieloma patrolami Machine.{boss_note}"
        ),
        "exits": exits,
        "recommended_mastery": stage,
        "procedural_infinite": True,
        "magitek_floor": floor,
    }

    base_hp = int(round((18000 + stage * 120 + floor * 550) * depth))
    base_dmg = int(round((170 + stage * 1.30 + floor * 5.0) * (depth ** 0.65)))
    base_class_xp = int(round((45000 + stage * 700 + floor * 1800) * depth))
    base_soul_xp = max(1, int(round(base_class_xp * 0.34)))
    base_stat_xp = max(1, int(round(base_class_xp * 0.075)))
    gear_pool = list(_v0382_magitek_gear_pool())

    spawns = []
    for variant in range(2):
        tid = f"magitek_floor_mob_{floor}_{variant+1}"
        name = _MAGITEK_REGULAR_NAMES[(floor * 2 + variant - 2) % len(_MAGITEK_REGULAR_NAMES)]
        variant_mult = 1.0 + variant * 0.12
        template = _machine_template(
            f"{name}, piętro {floor}",
            max(1, int(round(base_hp * variant_mult))),
            max(1, int(round(base_dmg * (1.0 + variant * 0.08)))),
            stage,
            _v0382_magitek_drop_table(floor, boss=False),
            boss=False,
            magic=((floor + variant) % 3 == 0),
            weaknesses=("lightning", "emp"),
        )
        template.update({
            "template_id": tid,
            "silver": max(1, int(round((stage * 24 + floor * 120) * depth))),
            "gold": 0,
            "mithril": 0,
            "stat_reward": max(1, int(round(base_stat_xp * variant_mult))),
            "class_xp_reward": max(1, int(round(base_class_xp * variant_mult))),
            "soul_reward": max(1, int(round(base_soul_xp * variant_mult))),
            "magitek_floor": floor,
            "magitek_infinite": True,
            "rank": "normal",
            "corpse_equipment_pool": gear_pool,
            "corpse_equipment_guaranteed": 1 if gear_pool else 0,
        })
        MOB_TEMPLATES[tid] = template
        if globals().get("_configure_dynamic_corpse_material"):
            _configure_dynamic_corpse_material(template)
        spawns.append((room_id, tid))

    # Every fifth non-boss floor gets an overclocked elite in addition to the
    # expanded regular patrols.
    if floor % 5 == 0 and not is_magitek_boss_floor(floor):
        elite_id = f"magitek_floor_elite_{floor}"
        elite = _machine_template(
            f"Przetaktowany Elitarny Prototyp, piętro {floor}",
            int(round(base_hp * 4.2)),
            int(round(base_dmg * 1.55)),
            stage,
            _v0382_magitek_drop_table(floor, boss=True),
            boss=False,
            magic=(floor % 2 == 0),
            weaknesses=("lightning", "emp"),
        )
        elite.update({
            "template_id": elite_id,
            "silver": max(1, int(round((stage * 75 + floor * 420) * depth))),
            "gold": 0,
            "mithril": 0,
            "stat_reward": max(1, int(round(base_stat_xp * 4.0))),
            "class_xp_reward": max(1, int(round(base_class_xp * 4.0))),
            "soul_reward": max(1, int(round(base_soul_xp * 4.0))),
            "magitek_floor": floor,
            "magitek_infinite": True,
            "elite": True,
            "rank": "elite",
            "corpse_equipment_pool": gear_pool,
            "corpse_equipment_guaranteed": 2 if gear_pool else 0,
        })
        MOB_TEMPLATES[elite_id] = elite
        spawns.append((room_id, elite_id))

    if is_magitek_boss_floor(floor):
        boss_id = f"magitek_floor_boss_{floor}"
        cycle_index = (floor // 10 - 1) % len(_MAGITEK_BOSS_NAMES)
        boss_name = _MAGITEK_BOSS_NAMES[cycle_index]
        mech_id, mech_text = _MAGITEK_BOSS_MECHANICS[cycle_index % len(_MAGITEK_BOSS_MECHANICS)]
        cycle = max(1, (floor - 1) // (len(_MAGITEK_BOSS_NAMES) * 10) + 1)
        display = f"{boss_name} — piętro {floor}, cykl {cycle}"
        boss = _machine_template(
            display,
            int(round(base_hp * (18.0 + min(10.0, floor / 80.0)))),
            int(round(base_dmg * (2.15 + min(0.85, floor / 700.0)))),
            stage,
            _v0382_magitek_drop_table(floor, boss=True),
            boss=False,
            magic=(cycle_index % 2 == 1),
            weaknesses=("lightning", "emp"),
        )
        boss.update({
            "template_id": boss_id,
            "silver": max(1, int(round((stage * 300 + floor * 1800) * depth))),
            "gold": 0,
            "mithril": 0,
            "stat_reward": max(1, int(round(base_stat_xp * 9.0))),
            "class_xp_reward": max(1, int(round(base_class_xp * 9.0))),
            "soul_reward": max(1, int(round(base_soul_xp * 9.0))),
            "magitek_floor": floor,
            "magitek_infinite": True,
            "magitek_boss": True,
            "machine_boss": True,
            "boss": True,
            "rank": "boss",
            "boss_mechanic": f"magitek_infinite_{mech_id}",
            "boss_mechanic_text": mech_text,
            "corpse_equipment_pool": gear_pool,
            "corpse_equipment_guaranteed": min(5, len(gear_pool)) if gear_pool else 0,
        })
        MOB_TEMPLATES[boss_id] = boss
        if globals().get("_configure_dynamic_corpse_material"):
            _configure_dynamic_corpse_material(boss)
        spawns.append((room_id, boss_id))

    return room_id, spawns


# -------- Merge both authored Magitek layers into one public dungeon identity.
for _v0382_rid, _v0382_room in list(ROOMS.items()):
    if str(_v0382_rid).startswith("magitek_"):
        _v0382_room["zone"] = MAGITEK_INFINITY_ZONE
        _v0382_room["magitek_authored_prologue"] = True

ROOMS.setdefault("magitek_zero_final", {}).setdefault("exits", {})["down"] = magitek_floor_id(1)

# Expanded procedural labels.
V0100_INSTANCE_LABELS["magitek"] = (
    "Hala Montażowa", "Galeria Serw", "Węzeł Sensorów", "Magazyn Ogniw",
    "Korytarz Dronów", "Stacja Naprawcza", "Odlewnia Ram", "Komora Chłodzenia",
    "Laboratorium Runiczne", "Zbrojownia Magitek", "Reaktor Boczny", "Most Przesyłowy",
    "Archiwum Protokołów", "Szyb Omega", "Węzeł WarMecha", "Platforma Oblężnicza",
)

_v0100_instance_spec_before_v0382 = v0100_instance_spec

def v0100_instance_spec(room_id):
    rid = str(room_id or "")
    floor = magitek_floor_number(rid)
    if floor is not None and rid == magitek_floor_id(floor):
        return {
            "kind": "magitek", "floor": floor, "next_dir": "down",
            "rooms": magitek_floor_room_count(floor), "boss_flag": "magitek_boss",
        }
    return _v0100_instance_spec_before_v0382(room_id)


# -------- Infinite room materialization.
_ensure_infinite_dungeon_floor_before_v0382 = World.ensure_infinite_dungeon_floor

def _ensure_infinite_dungeon_floor_v0382(self, room_id):
    room_id = str(room_id or "")
    floor = magitek_floor_number(room_id)
    if floor is None:
        return _ensure_infinite_dungeon_floor_before_v0382(self, room_id)

    canonical = magitek_floor_id(floor)
    if canonical not in ROOMS:
        created_room, spawns = create_infinite_magitek_floor_definition(floor)
        ROOMS[created_room]["procedural_dynamic"] = True
        ROOMS[created_room]["generated_on_demand"] = True
        self._generatorize_runtime_room(created_room)
        spawns = v0100_expand_instance_floor(created_room, spawns, runtime=True)

        # Retag the generated subrooms with Magitek-specific metadata/description.
        spec = v0100_instance_spec(created_room)
        total_rooms = int(spec.get("rooms", 12))
        theme_name, theme_desc = _MAGITEK_THEMES[(floor - 1) % len(_MAGITEK_THEMES)]
        for index in range(1, total_rooms):
            rid = v0100_subroom_id(created_room, index)
            room = ROOMS.get(rid)
            if not room:
                continue
            room["zone"] = MAGITEK_INFINITY_ZONE
            room["magitek_floor"] = floor
            room["recommended_mastery"] = magitek_floor_stage(floor)
            room["desc"] = (
                f"Rozbudowana część piętra {floor}: {theme_name}. {theme_desc}. "
                "Korytarze tworzą pętle, boczne odnogi i alternatywne drogi przez aktywne systemy Magitek."
            )
        if is_magitek_boss_floor(floor):
            final_room = v0100_subroom_id(created_room, total_rooms - 1)
            if final_room in ROOMS:
                ROOMS[final_room]["name"] = f"Komora Bossa Magitek — piętro {floor}"
                ROOMS[final_room]["desc"] += " To sala końcowego protokołu bossa tego piętra."

        for spawn_room, template_id in spawns:
            self._generatorize_runtime_room(spawn_room)
            self._register_runtime_spawn(spawn_room, template_id)
        try:
            _ROOM_THREAT_CACHE.pop(created_room, None)
            _ZONE_THREAT_CACHE.clear()
        except Exception:
            pass
    elif v0100_subroom_id(canonical, 1) not in ROOMS:
        # Static/pre-created canonical room without its expanded layout.
        spawns = [(r, t) for r, t in MOB_SPAWNS if r == canonical]
        spawns = v0100_expand_instance_floor(canonical, spawns, runtime=True)
        for spawn_room, template_id in spawns:
            self._generatorize_runtime_room(spawn_room)
            self._register_runtime_spawn(spawn_room, template_id)

    if room_id in ROOMS:
        self._generatorize_runtime_room(room_id)
        return True
    return canonical in ROOMS

World.ensure_infinite_dungeon_floor = _ensure_infinite_dungeon_floor_v0382


def _v0382_live_magitek_boss(self, room_id):
    self.refresh()
    for mob in self.mobs.values():
        if not mob.alive or mob.room_id != room_id:
            continue
        template = MOB_TEMPLATES.get(mob.template_id, {})
        if template.get("magitek_boss"):
            return mob
    return None


def _v0382_magitek_descent_blocked(self, room_id, direction="down"):
    if direction != "down":
        return False
    floor = magitek_floor_number(room_id)
    if floor is None or not is_magitek_boss_floor(floor):
        return False
    target = ROOMS.get(room_id, {}).get("exits", {}).get(direction)
    target_floor = magitek_floor_number(target)
    if target_floor is None or target_floor <= floor:
        return False
    return self.live_magitek_boss(room_id) is not None

World.live_magitek_boss = _v0382_live_magitek_boss
World.magitek_descent_blocked = _v0382_magitek_descent_blocked


# -------- First-clear identity/checkpoint integration.
_boss_floor_identity_before_v0382 = boss_floor_identity

def boss_floor_identity(template):
    if template.get("magitek_boss"):
        floor = int(template.get("magitek_floor", 0) or 0)
        if is_magitek_boss_floor(floor):
            return "magitek", floor
    return _boss_floor_identity_before_v0382(template)

INSTANCE_MAP_DEFS["magitek"] = {"label": "Nieskończony Kompleks Magitek", "min_floor": 1}
BOSS_CHEST_KIND_NAMES["magitek"] = "Nieskończonego Kompleksu Magitek"


def _v0382_ensure_magitek_key(floor):
    floor = int(floor)
    key_id = boss_floor_key_id("magitek", floor)
    if key_id not in ITEMS:
        ITEMS[key_id] = {
            "name": f"Klucz Bossa Nieskończonego Kompleksu Magitek {floor}",
            "type": "key", "price": None,
            "desc": f"Jednorazowy klucz do skrzyni bossa Magitek na piętrze {floor}.",
        }
    return key_id

_boss_key_for_template_before_v0382 = boss_key_for_template

def boss_key_for_template(template):
    if template.get("magitek_boss"):
        floor = int(template.get("magitek_floor", 0) or 0)
        if is_magitek_boss_floor(floor):
            return _v0382_ensure_magitek_key(floor)
    return _boss_key_for_template_before_v0382(template)

_boss_floor_chest_spec_before_v0382 = _boss_floor_chest_spec

def _boss_floor_chest_spec(room_id):
    floor = magitek_floor_number(room_id)
    if is_magitek_boss_floor(floor):
        return ("magitek", floor, magitek_floor_stage(floor))
    return _boss_floor_chest_spec_before_v0382(room_id)


# -------- Session movement: first clear blocks only the true down-exit room.
def _v0382_magitek_descent_blocked_for_player(self, room_id, direction="down"):
    floor = magitek_floor_number(room_id)
    if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "magitek", floor):
        return False
    return self.server.world.magitek_descent_blocked(room_id, direction)

Session.magitek_descent_blocked_for_player = _v0382_magitek_descent_blocked_for_player

_move_before_v0382 = Session.move
async def _move_v0382(self, direction):
    if self.character and self.magitek_descent_blocked_for_player(self.character.room_id, direction):
        boss = self.server.world.live_magitek_boss(self.character.room_id)
        boss_name = MOB_TEMPLATES.get(getattr(boss, "template_id", ""), {}).get("name", "boss Magitek")
        await self.send(
            f"Nie możesz zejść na następne piętro. Drogę blokuje {boss_name}. "
            "Pokonaj go pierwszy raz, aby odblokować dalszy zjazd na stałe."
        )
        return
    return await _move_before_v0382(self, direction)

_move_v0382._magitek_infinite_v0382 = True
Session.move = _move_v0382


# -------- Emergency dungeon exit also recognises authored + infinite Magitek.
_dungeon_exit_destination_before_v0382 = Session.dungeon_exit_destination

def _dungeon_exit_destination_v0382(self, room_id=None):
    rid = str(room_id or (self.character.room_id if self.character else ""))
    if magitek_floor_number(rid) is not None:
        return "magitek_gate", MAGITEK_INFINITY_ZONE
    room = ROOMS.get(rid, {})
    if room.get("zone") == MAGITEK_INFINITY_ZONE and rid != "magitek_gate":
        return "magitek_gate", MAGITEK_INFINITY_ZONE
    return _dungeon_exit_destination_before_v0382(self, rid)

Session.dungeon_exit_destination = _dungeon_exit_destination_v0382


# -------- Help / version notes.
HELP_TOPICS["magitek dungeon"] = [
    "Nieskończony Kompleks Magitek jest teraz jednym dungeonem. Dawny Kompleks Magitek i Magitek Dungeon 2.0 tworzą wspólną autorską część wejściową.",
    "Po Archiwum WarMecha można zejść na piętro 1 nieskończonej części. Każde piętro ma dużą, zapętloną mapę z bocznymi komorami; od około 12 pomieszczeń na początku do 20 na dużej głębokości.",
    "Każde kolejne piętro jest mocniejsze i bardziej nagradzające. Co 5 pięter występuje elitarny prototyp, a co 10 pięter nazwany boss Machine, który przy pierwszym clearze blokuje dalszy zjazd.",
    "Machine zachowują biologiczne odporności i główne słabości Lightning/EMP. Piętra są generowane na żądanie bez końca, również ponad progresję 600.",
    "Wyjście awaryjne z dowolnej części Magitek wraca do Bramy Kompleksu Magitek; drużynowe wycofanie lidera nadal obejmuje tylko osoby stojące z nim w tej samej lokacji.",
]
HELP_TOPIC_ALIASES.update({
    "magitek dungeon":"magitek dungeon", "magitek 2":"magitek dungeon",
    "dungeon magitek":"magitek dungeon", "nieskonczony magitek":"magitek dungeon",
    "infinite magitek":"magitek dungeon",
})
HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.2: oba dotychczasowe Magitek dungeony zostały scalone w Nieskończony Kompleks Magitek z dużymi proceduralnymi piętrami i bossem co 10."
)


# -------- Audit.
def magitek_infinite_audit_v0382():
    errors = []
    _rooms_before = set(ROOMS)
    _mobs_before = set(MOB_TEMPLATES)
    authored = [rid for rid in ROOMS if str(rid).startswith("magitek_") and magitek_floor_number(rid) is None]
    if len(authored) < 30:
        errors.append(f"authored Magitek rooms={len(authored)}, expected >=30")
    for rid in authored:
        if ROOMS.get(rid, {}).get("zone") != MAGITEK_INFINITY_ZONE:
            errors.append(f"{rid}: not merged into unified zone")
            break
    if ROOMS.get("magitek_zero_final", {}).get("exits", {}).get("down") != magitek_floor_id(1):
        errors.append("WarMech archive does not lead to infinite floor 1")

    # Structural helpers must scale floor size and difficulty.
    if magitek_floor_room_count(1) < 12:
        errors.append("floor 1 has fewer than 12 rooms")
    if magitek_floor_room_count(201) <= magitek_floor_room_count(1):
        errors.append("deep floors do not expand room count")

    samples = (1, 2, 5, 10, 11, 99, 100, 201, 600, 601)
    prev = None
    for floor in samples:
        rid, spawns = create_infinite_magitek_floor_definition(floor)
        regs = [MOB_TEMPLATES[t] for r, t in spawns if r == rid and not MOB_TEMPLATES[t].get("magitek_boss") and not MOB_TEMPLATES[t].get("elite")]
        if len(regs) < 2:
            errors.append(f"floor {floor}: missing regular machine variants")
            continue
        current = (int(regs[0].get("max_hp", 0)), int(regs[0].get("damage", 0)), int(regs[0].get("class_xp_reward", 0)))
        if prev is not None and floor != 5 and any(a <= b for a, b in zip(current, prev)):
            # Samples are increasing floor numbers; every selected later floor must be stronger.
            errors.append(f"floor {floor}: non-growing HP/dmg/XP {current} after {prev}")
        prev = current
        if is_magitek_boss_floor(floor):
            bosses = [MOB_TEMPLATES[t] for r, t in spawns if MOB_TEMPLATES[t].get("magitek_boss")]
            if len(bosses) != 1:
                errors.append(f"floor {floor}: expected exactly one boss, got {len(bosses)}")
            elif int(bosses[0].get("max_hp", 0)) <= current[0] * 10:
                errors.append(f"floor {floor}: boss not sufficiently stronger")

    # Expand one early and one deep floor exactly as runtime will.
    for floor in (1, 10, 201):
        rid, spawns = create_infinite_magitek_floor_definition(floor)
        expanded = v0100_expand_instance_floor(rid, spawns, runtime=True)
        expected = magitek_floor_room_count(floor)
        present = 1 + sum(1 for i in range(1, expected) if v0100_subroom_id(rid, i) in ROOMS)
        if present < expected:
            errors.append(f"floor {floor}: expanded rooms {present}/{expected}")
        if floor == 10:
            final_room = v0100_subroom_id(rid, expected - 1)
            if not any(r == final_room and MOB_TEMPLATES[t].get("magitek_boss") for r, t in expanded):
                errors.append("floor 10 boss is not in final room")

    if not getattr(Session.move, "_magitek_infinite_v0382", False):
        errors.append("Session.move Magitek boss gate wrapper missing")
    if boss_floor_identity(MOB_TEMPLATES.get("magitek_floor_boss_10", {})) != ("magitek", 10):
        errors.append("Magitek boss first-clear identity missing")
    if _boss_floor_chest_spec("magitek_floor_10")[:2] != ("magitek", 10):
        errors.append("Magitek boss chest spec missing")

    result = {
        "version": V0382_MAGITEK_VERSION,
        "authored_rooms_merged": len(authored),
        "floor1_rooms": magitek_floor_room_count(1),
        "floor201_rooms": magitek_floor_room_count(201),
        "boss_interval": MAGITEK_BOSS_INTERVAL,
        "error_count": len(errors),
        "errors": errors,
    }
    # The release audit must not permanently materialize lazy infinite floors.
    for _rid in list(ROOMS):
        if _rid not in _rooms_before:
            ROOMS.pop(_rid, None)
    for _tid in list(MOB_TEMPLATES):
        if _tid not in _mobs_before:
            MOB_TEMPLATES.pop(_tid, None)
    return result

MAGITEK_INFINITE_AUDIT_V0382 = magitek_infinite_audit_v0382()
if MAGITEK_INFINITE_AUDIT_V0382["error_count"]:
    raise RuntimeError(
        "Infinite Magitek Audit v0.38.2 failed: "
        + "; ".join(MAGITEK_INFINITE_AUDIT_V0382["errors"][:100])
    )

LATEST_CHANGES_TITLE = "Soulbound v0.38.2 - Infinite Unified Magitek Dungeon"
LATEST_CHANGES = [
    "Kompleks Magitek i Magitek Dungeon 2.0 mają jedną wspólną strefę i jedną ciągłą trasę.",
    "Archiwum WarMecha prowadzi do nieskończonych pięter Magitek generowanych na żądanie.",
    "Każde piętro ma 12-20 pomieszczeń, pętle, boczne odnogi i wiele patroli Machine.",
    "Co 5 pięter pojawia się elitarny prototyp, co 10 pięter boss z trwałym first-clear/checkpointem i skrzynią bossową.",
    "Trudność, damage oraz Class/Soul/stat EXP rosną na każdym piętrze także ponad 600.",
]
