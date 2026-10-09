# -*- coding: utf-8 -*-
"""Soulbound v1.14.0 — Pustkowia Eteru expansion.

Large late-game dimension with 76 authored locations, three endless dungeons,
eight unique superboss encounters, and real Void/Holy/Shadow elemental content.
Loaded through the compatibility runtime after dungeon entry commands so it can
extend World/Session behavior without duplicating core systems.
"""
import re
from systems.elemental_combat import canonical_element_v11339

ETHEREAL_WASTES_VERSION_V1140 = "1.14.0"
ETHEREAL_HUB_V1140 = "ethereal_crossroads_v1140"
ETHEREAL_ZONE_V1140 = "Pustkowia Eteru"

# ---------------------------------------------------------------------------
# Static dimension: 76 locations total (hub + 4x16 regional rooms + 3 gates +
# 8 superboss arenas). The layouts are grids so guide/walk remains useful.
# ---------------------------------------------------------------------------
_REGIONS_V1140 = (
    ("void", "Morze Pustki", "czarne szkło, bezgwiezdne szczeliny i pulsująca pustka", "void"),
    ("holy", "Bastion Światła", "białe monolity, dzwony i świetliste pieczęcie", "holy"),
    ("shadow", "Królestwo Cienia", "długie cienie, popękane lustra i żywa ciemność", "shadow"),
    ("twilight", "Pogranicze Zmierzchu", "mieszające się światło i mrok nad eterycznymi ruinami", "arcane"),
)

ROOMS.setdefault(ETHEREAL_HUB_V1140, {
    "zone": ETHEREAL_ZONE_V1140,
    "name": "Rozdroże Eteru",
    "desc": (
        "Ogromne rozdroże poza zwykłym światem. Cztery drogi prowadzą ku Pustce, "
        "Światłu, Cieniowi i Zmierzchowi. Trzy pieczęcie w podłożu prowadzą do "
        "nieskończonych lochów tego wymiaru."
    ),
    "exits": {}, "recommended_level": 101, "generator_level": 150,
})
ROOMS.setdefault("square", {}).setdefault("exits", {}).setdefault("northeast", ETHEREAL_HUB_V1140)
ROOMS[ETHEREAL_HUB_V1140]["exits"].setdefault("southwest", "square")

ETHEREAL_REGION_ROOMS_V1140 = {}
for region_index, (key, zone_name, flavor, element) in enumerate(_REGIONS_V1140):
    ids=[]
    base_level=140 + region_index * 35
    for row in range(4):
        for col in range(4):
            idx=row*4+col+1
            rid=f"ethereal_{key}_{idx:02d}_v1140"
            ids.append(rid)
            exits={}
            if row>0: exits["north"]=f"ethereal_{key}_{(row-1)*4+col+1:02d}_v1140"
            if row<3: exits["south"]=f"ethereal_{key}_{(row+1)*4+col+1:02d}_v1140"
            if col>0: exits["west"]=f"ethereal_{key}_{row*4+col:02d}_v1140"
            if col<3: exits["east"]=f"ethereal_{key}_{row*4+col+2:02d}_v1140"
            ROOMS.setdefault(rid, {
                "zone": f"{ETHEREAL_ZONE_V1140} — {zone_name}",
                "name": f"{zone_name} — sektor {idx}",
                "desc": f"Sektor {idx}. Wokół rozciągają się {flavor}. Energia {element.upper()} przenika teren.",
                "exits": exits,
                "recommended_level": base_level + idx*3,
                "generator_level": base_level + idx*3,
                "ethereal_dimension_v1140": True,
                "ethereal_element_v1140": element,
            })
    ETHEREAL_REGION_ROOMS_V1140[key]=tuple(ids)

# Hub <-> four regional grids.
_links=(
    ("north", "void", "south"),
    ("east", "holy", "west"),
    ("west", "shadow", "east"),
    ("south", "twilight", "north"),
)
for direction,key,back in _links:
    first=ETHEREAL_REGION_ROOMS_V1140[key][0]
    ROOMS[ETHEREAL_HUB_V1140]["exits"][direction]=first
    ROOMS[first]["exits"][back]=ETHEREAL_HUB_V1140

# ---------------------------------------------------------------------------
# Regional mobs. Authored rewards rise by region/sector; generator may still
# apply global difficulty scaling at runtime.
# ---------------------------------------------------------------------------
_ETHEREAL_MOB_ARCHETYPES_V1140 = {
    "void": ("Pożeracz Pustki", "void"),
    "holy": ("Serafin Strażniczy", "holy"),
    "shadow": ("Łowca Cienia", "shadow"),
    "twilight": ("Eteryczny Rozszczepieniec", "arcane"),
}
for region_index,(key,_zone,_flavor,_element) in enumerate(_REGIONS_V1140):
    base_name, element = _ETHEREAL_MOB_ARCHETYPES_V1140[key]
    for variant in range(1,4):
        tid=f"ethereal_{key}_mob_{variant}_v1140"
        lvl=150 + region_index*50 + variant*20
        MOB_TEMPLATES.setdefault(tid, {
            "name": f"{base_name} {variant}",
            "max_hp": 140000 + lvl*2200,
            "damage": 900 + lvl*18,
            "damage_type": "magic",
            "attack_elements_v11339": (element,),
            "silver": lvl*950,
            "stat_reward": lvl*5200,
            "class_xp_reward": lvl*38000,
            "soul_reward": lvl*13500,
            "generator_level": lvl,
            "ethereal_mob_v1140": True,
            "drops": {"soul_shard": min(0.45, 0.10 + variant*0.05)},
        })
        if callable(globals().get("v0190_apply_combat_template")):
            v0190_apply_combat_template(MOB_TEMPLATES[tid])
    rooms=ETHEREAL_REGION_ROOMS_V1140[key]
    for i,rid in enumerate(rooms):
        MOB_SPAWNS.append((rid, f"ethereal_{key}_mob_{(i%3)+1}_v1140"))
        if i in (5,10,15):
            MOB_SPAWNS.append((rid, f"ethereal_{key}_mob_{((i+1)%3)+1}_v1140"))

# ---------------------------------------------------------------------------
# Three endless dungeons.
# ---------------------------------------------------------------------------
ETHEREAL_DUNGEONS_V1140 = {
    "void": {"name":"Otchłań Pustki", "prefix":"eth_void_floor_", "element":"void", "gate":"eth_void_gate_v1140"},
    "holy": {"name":"Nieskończone Sanktuarium", "prefix":"eth_holy_floor_", "element":"holy", "gate":"eth_holy_gate_v1140"},
    "shadow": {"name":"Labirynt Cienia", "prefix":"eth_shadow_floor_", "element":"shadow", "gate":"eth_shadow_gate_v1140"},
}
for key,spec in ETHEREAL_DUNGEONS_V1140.items():
    gate=spec["gate"]
    ROOMS.setdefault(gate, {
        "zone": ETHEREAL_ZONE_V1140,
        "name": f"Brama — {spec['name']}",
        "desc": f"Próg nieskończonego lochu: {spec['name']}. Każde kolejne piętro jest mocniejsze.",
        "exits": {"up": ETHEREAL_HUB_V1140, "down": f"{spec['prefix']}1_v1140"},
        "recommended_level": 180, "generator_level": 200,
    })
ROOMS[ETHEREAL_HUB_V1140]["exits"].update({
    "down": ETHEREAL_DUNGEONS_V1140["void"]["gate"],
    "southeast": ETHEREAL_DUNGEONS_V1140["holy"]["gate"],
    "northwest": ETHEREAL_DUNGEONS_V1140["shadow"]["gate"],
})
# back links for named routes
ROOMS[ETHEREAL_DUNGEONS_V1140["void"]["gate"]]["exits"]["up"] = ETHEREAL_HUB_V1140
ROOMS[ETHEREAL_DUNGEONS_V1140["holy"]["gate"]]["exits"]["northwest"] = ETHEREAL_HUB_V1140
ROOMS[ETHEREAL_DUNGEONS_V1140["shadow"]["gate"]]["exits"]["southeast"] = ETHEREAL_HUB_V1140

_ETH_FLOOR_RE = re.compile(r"^eth_(void|holy|shadow)_floor_(\d+)_v1140$")
def ethereal_floor_identity_v1140(room_id):
    m=_ETH_FLOOR_RE.fullmatch(str(room_id or ""))
    if not m: return None
    return m.group(1), max(1,int(m.group(2)))

def ethereal_floor_id_v1140(kind, floor):
    spec=ETHEREAL_DUNGEONS_V1140[str(kind)]
    return f"{spec['prefix']}{max(1,int(floor))}_v1140"

def create_ethereal_floor_v1140(kind, floor):
    kind=str(kind); floor=max(1,int(floor)); spec=ETHEREAL_DUNGEONS_V1140[kind]
    rid=ethereal_floor_id_v1140(kind,floor)
    prev=spec["gate"] if floor==1 else ethereal_floor_id_v1140(kind,floor-1)
    nxt=ethereal_floor_id_v1140(kind,floor+1)
    stage=min(800, 180 + floor*6)
    depth=1.0 + floor*0.045 + (floor//10)*0.15
    boss=(floor%10==0)
    ROOMS.setdefault(rid, {
        "zone": f"{ETHEREAL_ZONE_V1140} — {spec['name']}",
        "name": f"{spec['name']} — piętro {floor}",
        "desc": f"Nieskończone piętro {floor}. Energia {spec['element'].upper()} gęstnieje wraz z głębokością.",
        "exits": {"up":prev,"down":nxt},
        "recommended_level": stage,
        "generator_level": stage,
        "procedural_infinite": True,
        "ethereal_infinite_v1140": kind,
        "ethereal_floor_v1140": floor,
    })
    hp=int((220000 + stage*4200 + floor*18000)*depth)
    dmg=int((1600 + stage*25 + floor*90)*(depth**0.72))
    cxp=int((240000 + stage*8500 + floor*45000)*depth)
    spawns=[]
    for variant in (1,2):
        tid=f"eth_{kind}_floor_{floor}_mob_{variant}_v1140"
        mult=1.0 + (variant-1)*0.18
        MOB_TEMPLATES.setdefault(tid, {
            "name": f"{spec['name']} — strażnik {floor}.{variant}",
            "max_hp": max(1,int(hp*mult)), "damage":max(1,int(dmg*mult)),
            "damage_type":"magic", "attack_elements_v11339":(spec["element"],),
            "silver":max(1,int((stage*1400+floor*8000)*depth)),
            "class_xp_reward":max(1,int(cxp*mult)),
            "soul_reward":max(1,int(cxp*0.38*mult)),
            "stat_reward":max(1,int(cxp*0.11*mult)),
            "generator_level":stage, "ethereal_infinite_v1140":kind,
            "ethereal_floor_v1140":floor,
            "drops":{"soul_shard":min(0.65,0.18+floor/2000.0)},
        })
        if callable(globals().get("v0190_apply_combat_template")):
            v0190_apply_combat_template(MOB_TEMPLATES[tid])
        spawns.append((rid,tid))
    if boss:
        tid=f"eth_{kind}_floor_{floor}_boss_v1140"
        MOB_TEMPLATES.setdefault(tid, {
            "name": f"Władca {spec['name']} — piętro {floor}",
            "max_hp":max(1,int(hp*(14.0+min(16.0,floor/80.0)))),
            "damage":max(1,int(dmg*(2.0+min(1.5,floor/500.0)))),
            "damage_type":"magic", "attack_elements_v11339":(spec["element"],),
            "silver":max(1,int((stage*9000+floor*55000)*depth)),
            "class_xp_reward":max(1,int(cxp*14.0)),
            "soul_reward":max(1,int(cxp*5.5)),
            "stat_reward":max(1,int(cxp*1.6)),
            "generator_level":stage, "world_boss":True,
            "ethereal_infinite_v1140":kind, "ethereal_floor_v1140":floor,
            "boss_mechanic":f"ethereal_{kind}_overdrive",
            "boss_mechanic_text":f"Boss piętra {floor}: rosnący bez limitu Overdrive {spec['element'].upper()}.",
            "drops":{"soul_shard":1.0,"soul_elixir":min(1.0,0.45+floor/1000.0)},
        })
        if callable(globals().get("v0190_apply_combat_template")):
            v0190_apply_combat_template(MOB_TEMPLATES[tid])
        spawns.append((rid,tid))
    return rid, spawns

# Seed floor 1 of every endless dungeon so static topology audits and navigation
# never see a dangling gate. Deeper floors remain generated on demand.
for _seed_kind in ETHEREAL_DUNGEONS_V1140:
    _seed_room, _seed_spawns = create_ethereal_floor_v1140(_seed_kind, 1)
    for _seed_spawn in _seed_spawns:
        if _seed_spawn not in MOB_SPAWNS:
            MOB_SPAWNS.append(_seed_spawn)

# Patch dynamic world generation without replacing other infinite dungeons.
_ensure_inf_before_v1140 = World.ensure_infinite_dungeon_floor
def _ensure_infinite_dungeon_floor_v1140(self, room_id):
    identity=ethereal_floor_identity_v1140(room_id)
    if identity:
        kind,floor=identity
        created,spawns=create_ethereal_floor_v1140(kind,floor)
        self._generatorize_runtime_room(created)
        for spawn_room,template_id in spawns:
            self._register_runtime_spawn(spawn_room,template_id)
        return True
    return _ensure_inf_before_v1140(self, room_id)
World.ensure_infinite_dungeon_floor = _ensure_infinite_dungeon_floor_v1140

# Dungeon exit routing.
_dungeon_exit_before_v1140 = Session.dungeon_exit_destination
def _dungeon_exit_destination_v1140(self, room_id=None):
    rid=str(room_id or (self.character.room_id if self.character else ""))
    identity=ethereal_floor_identity_v1140(rid)
    if identity:
        kind,_floor=identity; spec=ETHEREAL_DUNGEONS_V1140[kind]
        return spec["gate"], spec["name"]
    return _dungeon_exit_before_v1140(self, rid)
Session.dungeon_exit_destination = _dungeon_exit_destination_v1140

# Named dungeon entry commands at each gate.
if "DUNGEON_ENTRY_SPECS_V03812" in globals() and callable(globals().get("_v03812_spec")):
    for key,spec in ETHEREAL_DUNGEONS_V1140.items():
        DUNGEON_ENTRY_SPECS_V03812.append(_v03812_spec(
            spec["name"], spec["gate"], ethereal_floor_id_v1140(key,1),
            (spec["name"], key, f"loch {key}"), spec["name"],
        ))

GUIDE_DESTINATION_ALIASES.update({
    "pustkowia eteru": ETHEREAL_HUB_V1140,
    "eter": ETHEREAL_HUB_V1140,
    "otchlan pustki": ETHEREAL_DUNGEONS_V1140["void"]["gate"],
    "otchłań pustki": ETHEREAL_DUNGEONS_V1140["void"]["gate"],
    "nieskonczone sanktuarium": ETHEREAL_DUNGEONS_V1140["holy"]["gate"],
    "nieskończone sanktuarium": ETHEREAL_DUNGEONS_V1140["holy"]["gate"],
    "labirynt cienia": ETHEREAL_DUNGEONS_V1140["shadow"]["gate"],
})

# ---------------------------------------------------------------------------
# Eight unique dimension superbosses. Register them with the mature UOSS
# lockout/gating framework: 24h per boss, solo or party allowed.
# ---------------------------------------------------------------------------
_ETHEREAL_SUPERBOSSES_V1140 = (
    ("nihil_archon", "Nihil, Archont Pustki", "void", 220, 7800000, 82000),
    ("seraph_prime", "Serafin Prime", "holy", 240, 9200000, 88000),
    ("umbra_regent", "Regent Umbry", "shadow", 260, 10800000, 96000),
    ("eclipse_twins", "Bliźnięta Zaćmienia", "shadow", 280, 13200000, 108000),
    ("void_leviathan", "Lewiatan Pustki", "void", 320, 16800000, 124000),
    ("saint_zero", "Święty Zero", "holy", 360, 20500000, 142000),
    ("shadow_emperor", "Cesarz Cienia", "shadow", 420, 28000000, 168000),
    ("aetherion", "Aetherion, Koniec Światła", "void", 500, 42000000, 210000),
)
# Arena anchors: last two rooms of each regional grid, then twilight extras.
_arena_hosts = (
    ETHEREAL_REGION_ROOMS_V1140["void"][14], ETHEREAL_REGION_ROOMS_V1140["holy"][14],
    ETHEREAL_REGION_ROOMS_V1140["shadow"][14], ETHEREAL_REGION_ROOMS_V1140["twilight"][12],
    ETHEREAL_REGION_ROOMS_V1140["void"][15], ETHEREAL_REGION_ROOMS_V1140["holy"][15],
    ETHEREAL_REGION_ROOMS_V1140["shadow"][15], ETHEREAL_REGION_ROOMS_V1140["twilight"][15],
)
for i,(key,name,element,lvl,hp,dmg) in enumerate(_ETHEREAL_SUPERBOSSES_V1140):
    arena=f"ethereal_superboss_{key}_arena_v1140"; mid=f"ethereal_superboss_{key}_v1140"
    host=_arena_hosts[i]
    ROOMS.setdefault(arena, {
        "zone":f"{ETHEREAL_ZONE_V1140} — Superbossy",
        "name":f"Arena — {name}",
        "desc":f"Arena unikalnego superbossa {name}. Po zwycięstwie obowiązuje 24-godzinna blokada tego encounteru.",
        "exits":{"down":host}, "recommended_level":lvl, "generator_level":lvl,
    })
    ROOMS[host].setdefault("exits", {}).setdefault("up", arena)
    UOSS_SUPERBOSS_ENCOUNTERS_V11134.setdefault(key, {
        "name":name, "mode":"party", "unlock_level":max(101,lvl-80),
        "recommended_level":lvl, "lockout_hours":24,
    })
    MOB_TEMPLATES.setdefault(mid, {
        "name":name, "max_hp":hp, "damage":dmg, "damage_type":"magic",
        "attack_elements_v11339":(element,), "ethereal_superboss_v1140":True,
        "silver":lvl*250000, "class_xp_reward":lvl*500000,
        "soul_reward":lvl*180000, "stat_reward":lvl*55000,
        "generator_level":lvl, "world_boss":True, "stationary_mob":True,
        "auto_aggro":False, "uoss_unique_superboss_key":key,
        "uoss_superboss_mode":"party", "boss_mechanic":f"ethereal_{key}",
        "boss_mechanic_text":f"Unikalny Super Boss Pustkowi Eteru. Główny żywioł: {element.upper()}.",
        "drops":{"soul_shard":1.0,"soul_elixir":1.0},
    })
    if callable(globals().get("v0190_apply_combat_template")):
        v0190_apply_combat_template(MOB_TEMPLATES[mid])
    MOB_SPAWNS.append((arena,mid))

# Help / discoverability.
HELP_TOPICS["pustkowia_eteru_v1140"] = [
    "v1.14.0: Pustkowia Eteru to nowy wymiar late-game połączony z Placem Dusz przez północny-wschód.",
    "Rozszerzenie ma 76 nowych lokacji statycznych oraz trzy nieskończone lochy: Otchłań Pustki, Nieskończone Sanktuarium i Labirynt Cienia.",
    "Każdy nowy loch skaluje HP, obrażenia i EXP bez końcowego piętra; boss pojawia się co 10 pięter.",
    "Nowe encountery używają realnych obrażeń Void, Holy i Shadow. Void i Shadow nie są aliasem Dark.",
    "W wymiarze znajduje się 8 nowych superbossów; mogą być atakowani solo albo w party, a po pokonaniu konkretnego bossa obowiązuje 24h lockout.",
]
HELP_TOPIC_ALIASES.update({
    "pustkowia eteru":"pustkowia_eteru_v1140", "eter":"pustkowia_eteru_v1140",
    "ethereal wastes":"pustkowia_eteru_v1140", "void":"pustkowia_eteru_v1140",
})


def ethereal_wastes_audit_v1140():
    errors=[]
    authored=[rid for rid,row in ROOMS.items() if isinstance(row,dict) and (row.get("ethereal_dimension_v1140") or rid==ETHEREAL_HUB_V1140 or rid.startswith("ethereal_superboss_") or rid.endswith("_gate_v1140"))]
    if len(set(authored)) < 76:
        errors.append(f"expected >=76 authored ethereal rooms, got {len(set(authored))}")
    for kind,spec in ETHEREAL_DUNGEONS_V1140.items():
        rid,spawns=create_ethereal_floor_v1140(kind,777)
        if rid not in ROOMS or len(spawns)<2: errors.append(f"{kind} endless floor contract failed")
        if ethereal_floor_identity_v1140(rid)!=(kind,777): errors.append(f"{kind} floor identity failed")
    for key,name,_element,_lvl,_hp,_dmg in _ETHEREAL_SUPERBOSSES_V1140:
        spec=UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(key,{})
        if spec.get("lockout_hours") != 24: errors.append(f"{name}: missing 24h lockout")
    for element in ("void","holy","shadow"):
        if canonical_element_v11339(element) != element: errors.append(f"element {element} is not canonical")
    return {"version":ETHEREAL_WASTES_VERSION_V1140,"errors":errors,"ok":not errors,"authored_rooms":len(set(authored)),"superbosses":len(_ETHEREAL_SUPERBOSSES_V1140),"endless_dungeons":3}
