# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _v0160_clone_encounter_template(kind, encounter_type):
    spec = V013_FRONTIER_SPECS.get(kind, {})
    pool = [mid for mid in spec.get("mobs", ()) if mid in MOB_TEMPLATES]
    if not pool:
        return None
    base_id = pool[-1]
    base = MOB_TEMPLATES[base_id]
    if encounter_type == "world_boss":
        tid = f"v016_worldboss_{kind}"
        if tid in MOB_TEMPLATES:
            return tid
        mult_hp, mult_damage, mult_reward = 14.0, 2.25, 10.0
        prefix = f"Władca {spec['zone']}"
    else:
        tid = f"v016_legendary_{kind}"
        if tid in MOB_TEMPLATES:
            return tid
        mult_hp, mult_damage, mult_reward = 3.8, 1.60, 4.0
        prefix = f"Legendarny Trop {spec['zone']}"
    data = dict(base)
    data["drops"] = dict(base.get("drops", {}))
    data["name"] = f"{prefix}: {base['name']}"
    data["max_hp"] = max(1, int(round(int(base.get("max_hp", 1)) * mult_hp)))
    data["damage"] = max(1, int(round(int(base.get("damage", 1)) * mult_damage)))
    data["silver"] = max(1, int(round(int(base.get("silver", 1)) * mult_reward)))
    data["gold"] = max(1, int(base.get("gold", 0)) + (12 if encounter_type == "world_boss" else 4))
    data["mithril"] = int(base.get("mithril", 0)) + (1 if encounter_type == "world_boss" else 0)
    data["soul_reward"] = max(1, int(round(int(base.get("soul_reward", 1)) * mult_reward)))
    data["class_xp_reward"] = max(50, int(round(int(base.get("class_xp_reward", 50)) * mult_reward)))
    data["stat_reward"] = max(1, int(round(int(base.get("stat_reward", 1)) * min(2.5, mult_reward))))
    data["auto_aggro"] = False
    data["v016_biome"] = kind
    if encounter_type == "world_boss":
        data["world_boss"] = True
        data["v016_world_boss"] = True
        data["stationary_mob"] = True
        data["drops"].setdefault("soul_elixir", 0.65)
        data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.80)
        BOSS_COLLECTION_CATALOG[tid] = data["name"]
    else:
        data["rare_mob"] = True
        data["v016_legendary_rare"] = True
        data["rare_base_template"] = base_id
        data.pop("stationary_mob", None)
        data["drops"].setdefault("soul_elixir", 0.35)
        data["drops"].setdefault(V014_TREASURE_MAP_ITEM, 0.55)
        RARE_MOB_COLLECTION_CATALOG[tid] = data["name"]
    _catalog_mut.catalog_assign(data, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
    return tid


def v0180_create_archipelago_room_definition(room_id):
    ident = v0180_archipelago_identity(room_id)
    if not ident:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    eid, x, y = ident
    spec = V018_EXPEDITIONS[eid]
    seed = _v0140_hash_int("v018-arch", eid, x, y)
    rng = random.Random(seed)
    exits = {}
    if x > 0: exits["west"] = v0180_archipelago_room_id(eid, x-1, y)
    if x+1 < V018_EXPEDITION_SIDE: exits["east"] = v0180_archipelago_room_id(eid, x+1, y)
    if y > 0: exits["south"] = v0180_archipelago_room_id(eid, x, y-1)
    if y+1 < V018_EXPEDITION_SIDE: exits["north"] = v0180_archipelago_room_id(eid, x, y+1)
    if x == 0 and y == 0:
        exits["down"] = "harbor"
    title = rng.choice(spec["titles"])
    _catalog_mut.catalog_assign({
        "zone":spec["zone"], "name":f"{title} — sektor {x+1}-{y+1}",
        "desc":(
            f"Sektor ekspedycji na {spec['name']}. Wyspy są generowane z trwałego seedu; "
            "po restarcie zachowują układ. Powrót do Portu Dusz prowadzi z pierwszego sektora w dół."
        ),
        "exits":exits, "recommended_mastery":int(spec["mastery"]),
        "generated_on_demand":True, "v018_archipelago":eid,
        "v018_arch_x":x, "v018_arch_y":y,
    }, 'ROOMS', ROOMS, (room_id,))
    # Island gathering ecology: marine fishing everywhere; some later islands also support herbs/mining.
    FISHING_ROOMS.add(room_id); MARINE_FISHING_ROOMS.add(room_id); OCEAN_FISHING_ROOMS.add(room_id)
    FISHING_WATER_TYPE_OVERRIDES[room_id] = spec["name"]
    if eid in ("coral","mist") and (x+y)%2 == 0:
        HERBALISM_ROOMS.add(room_id)
    # v0.25.1: ekspedycje nie są już alternatywnymi kopalniami.
    base_kind = spec["biome"]
    pool = [t for t in V013_FRONTIER_SPECS[base_kind].get("mobs",()) if t in MOB_TEMPLATES]
    spawns = []
    if pool:
        for _ in range(1 + (1 if rng.random() < 0.45 else 0)):
            spawns.append((room_id, rng.choice(pool)))
    return room_id, tuple(spawns)


def v0180_create_ruin_room_definition(room_id):
    ident = v0180_ruin_identity(room_id)
    if not ident:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind,x,y,index,size = ident
    seed = _v0140_hash_int("v018-ruin-room",kind,x,y,index)
    rng = random.Random(seed)
    exits = {}
    if index > 1: exits["west"] = v0180_ruin_room_id(kind,x,y,index-1)
    if index < size: exits["east"] = v0180_ruin_room_id(kind,x,y,index+1)
    # deterministic cross-links create loops and alternative paths, never traps.
    if index % 4 == 1 and index + 4 <= size:
        exits["north"] = v0180_ruin_room_id(kind,x,y,index+4)
    if index >= 5 and (index-4) % 4 == 1:
        exits["south"] = v0180_ruin_room_id(kind,x,y,index-4)
    if index == 1:
        exits["down"] = v0130_frontier_room_id(kind,x,y)
    final = index == size
    zone = f"Wielkie Ruiny — {V013_FRONTIER_SPECS[kind]['zone']}"
    names = ("Galeria Run","Zawalona Nawa","Sala Kolumn","Kamienny Dziedziniec","Archiwum Ruin","Korytarz Posągów")
    _catalog_mut.catalog_assign({
        "zone":zone, "name":f"{rng.choice(names)} {index}/{size}",
        "desc":(
            "Rozległy fragment proceduralnych ruin. Układ jest deterministyczny, ma pętle i alternatywne przejścia. "
            + ("To finałowa komnata strażnika. " if final else "")
            + "Nie ma tu pułapek ani automatycznych obrażeń wejściowych."
        ),
        "exits":exits, "recommended_mastery":min(CHARACTER_MAX_LEVEL, int(V013_FRONTIER_SPECS[kind].get("base_mastery",1))+40),
        "generated_on_demand":True, "v018_great_ruin":True, "v018_ruin_final":final,
        "v018_biome":kind, "v018_ruin_parent":v0130_frontier_room_id(kind,x,y),
    }, 'ROOMS', ROOMS, (room_id,))
    spawns=[]
    pool=[t for t in V013_FRONTIER_SPECS[kind].get("mobs",()) if t in MOB_TEMPLATES]
    if final and kind in V018_RUIN_GUARDIANS:
        spawns.append((room_id,V018_RUIN_GUARDIANS[kind]))
    elif pool and rng.random() < 0.82:
        spawns.append((room_id,rng.choice(pool)))
        if rng.random() < 0.33: spawns.append((room_id,rng.choice(pool)))
    return room_id, tuple(spawns)


def v11339_named_rare_template_for_kind(kind, event_type="rare_hunt"):
    kind = str(kind or "")
    event_type = str(event_type or "rare_hunt")
    if kind not in V013_FRONTIER_SPECS:
        return None
    pool = [
        base for base in V013_FRONTIER_SPECS[kind].get("mobs", ())
        if base in MOB_TEMPLATES
    ]
    if not pool:
        return None
    base_id = pool[_v0140_hash_int("v11339-named-base", kind) % len(pool)]
    suffix = {
        "rare_hunt": "hunt",
        "elemental_rift": "rift",
        "shadow_invasion": "shadow",
    }.get(event_type, "hunt")
    template_id = f"v11339_named_{suffix}_{kind}"
    if template_id in MOB_TEMPLATES:
        return template_id

    base = MOB_TEMPLATES[base_id]
    data = dict(base)
    data["drops"] = dict(base.get("drops", {}))
    base_name = V11339_BIOME_NAMED_RARES[kind]
    if event_type == "elemental_rift":
        data["name"] = "Rozszczepiony " + base_name
    elif event_type == "shadow_invasion":
        data["name"] = "Cienisty " + base_name
    else:
        data["name"] = base_name

    element = (
        "dark"
        if event_type == "shadow_invasion"
        else V11339_BIOME_ELEMENTS[kind]
    )
    data["rare_mob"] = True
    data["rank"] = "rare"
    data["v11339_named_rare"] = True
    data["v11339_world_event_type"] = event_type
    data["rare_base_template"] = base_id
    data["attack_elements_v11339"] = (element,)
    data["auto_aggro"] = False
    data["max_hp"] = max(1, int(round(int(base.get("max_hp", 1)) * 2.20)))
    data["damage"] = max(1, int(round(int(base.get("damage", 1)) * 1.35)))
    data["stat_reward"] = max(1, int(round(int(base.get("stat_reward", 1)) * 2.00)))
    data["soul_reward"] = max(1, int(round(int(base.get("soul_reward", 1)) * 2.50)))
    data["class_xp_reward"] = max(
        50,
        int(round(
            int(base.get("class_xp_reward", max(50, int(base.get("stat_reward", 1)) * 10)))
            * 2.50
        )),
    )
    data["silver"] = max(1, int(round(int(base.get("silver", 1)) * 2.50)))
    data["gold"] = 0
    data["mithril"] = 0
    chase = V11339_ELEMENT_CHASE_ITEMS[element]
    data["drops"][chase] = max(float(data["drops"].get(chase, 0.0) or 0.0), 0.12)
    data["drops"].setdefault("soul_shard", 0.70)
    _catalog_mut.catalog_assign(data, 'MOB_TEMPLATES', MOB_TEMPLATES, (template_id,))
    return template_id

