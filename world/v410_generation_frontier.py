# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def v0130_create_frontier_room_definition(room_id):
    identity = v0130_frontier_room_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y = identity
    spec = V013_FRONTIER_SPECS[kind]
    seed_text = f"{V013_WORLD_SEED}:{kind}:{x}:{y}"
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    title = rng.choice(spec["titles"])
    feature = rng.choice(spec["features"])
    distance = x + y
    mastery = min(CHARACTER_MAX_LEVEL, int(spec["base_mastery"]) + distance * int(spec["step"]))
    exits = {}
    if x > 0:
        exits["west"] = v0130_frontier_room_id(kind, x - 1, y)
    if x + 1 < V013_FRONTIER_SIDE:
        exits["east"] = v0130_frontier_room_id(kind, x + 1, y)
    if y > 0:
        exits["south"] = v0130_frontier_room_id(kind, x, y - 1)
    if y + 1 < V013_FRONTIER_SIDE:
        exits["north"] = v0130_frontier_room_id(kind, x, y + 1)
    if x == 0 and y == 0:
        direction = spec["direction"]
        exits[V013_REVERSE_DIRECTION[direction]] = v0130_gateway_id(kind)

    # v0.14.0: wejścia do mini-lochów są częścią trwałego seedu sektora.
    # Funkcja jest zdefiniowana niżej; nazwa rozwiązuje się dopiero przy
    # faktycznym generowaniu pokoju po zakończeniu importu modułu.
    if "v0140_has_mini_dungeon" in globals() and v0140_has_mini_dungeon(kind, x, y):
        exits["down"] = v0140_mini_room_id(kind, x, y, 1)
    if "v0180_has_great_ruin" in globals() and v0180_has_great_ruin(kind, x, y):
        exits["up"] = v0180_ruin_room_id(kind, x, y, 1)

    _catalog_mut.catalog_assign({
        "zone": spec["zone"],
        "name": f"{title} — sektor {x + 1}-{y + 1}",
        "desc": (
            f"Rozległy sektor biomu {spec['zone']}. Wyróżnia się tu {feature}. "
            "Teren został wygenerowany z trwałego seedu świata, więc po ponownym "
            "uruchomieniu serwera zachowuje ten sam układ i charakter."
        ),
        "exits": exits,
        "recommended_mastery": mastery,
        "procedural_surface": True,
        "generated_on_demand": True,
        "procedural_biome": kind,
        "procedural_x": x,
        "procedural_y": y,
    }, 'ROOMS', ROOMS, (room_id,))
    if "v0140_has_mini_dungeon" in globals() and v0140_has_mini_dungeon(kind, x, y):
        _catalog_mut.catalog_aug_path('ROOMS', ROOMS, (room_id, "desc"), 'Add', " W terenie ukrywa się zejście do proceduralnego mini-lochu.")
        _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (room_id, "v0140_mini_entrance"))
    if "v0180_has_great_ruin" in globals() and v0180_has_great_ruin(kind, x, y):
        _catalog_mut.catalog_aug_path('ROOMS', ROOMS, (room_id, "desc"), 'Add', " Nad sektorem wznoszą się rozległe ruiny; wejście prowadzi w górę.")
        _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (room_id, "v0180_great_ruin_entrance"))
    if "v0140_surface_secret_info" in globals():
        secret_info = v0140_surface_secret_info(room_id)
        if secret_info:
            _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (room_id, "v0140_surface_secret"))
            _catalog_mut.catalog_assign(secret_info["name"], 'ROOMS', ROOMS, (room_id, "v0140_secret_name"))
    _v0130_apply_resources(room_id, spec)

    mob_pool = tuple(t for t in spec.get("mobs", ()) if t in MOB_TEMPLATES)
    spawns = []
    if mob_pool:
        spawn_count = 1 + (1 if rng.random() < 0.38 else 0)
        for _ in range(spawn_count):
            spawns.append((room_id, rng.choice(mob_pool)))
    return room_id, tuple(spawns)


def v0140_create_mini_room_definition(room_id):
    identity = v0140_mini_identity(room_id)
    if identity is None:
        return None, ()
    if room_id in ROOMS:
        return room_id, ()
    kind, x, y, index, size = identity
    spec = V013_FRONTIER_SPECS[kind]
    width = 3
    cx, cy = (index - 1) % width, (index - 1) // width
    exits = {}
    candidates = {
        "west": (cx - 1, cy), "east": (cx + 1, cy),
        "south": (cx, cy - 1), "north": (cx, cy + 1),
    }
    for direction, (nx, ny) in candidates.items():
        if nx < 0 or ny < 0 or nx >= width:
            continue
        neighbor = ny * width + nx + 1
        if 1 <= neighbor <= size:
            exits[direction] = v0140_mini_room_id(kind, x, y, neighbor)
    parent = v0130_frontier_room_id(kind, x, y)
    if index == 1:
        exits["up"] = parent
    final = index == size
    seed = _v0140_hash_int("mini-room", kind, x, y, index)
    rng = random.Random(seed)
    room_titles = (
        "Zawalone Przejście", "Kamienna Galeria", "Boczna Komora", "Stary Korytarz",
        "Podziemna Sala", "Szczelina Korzeni", "Zapomniany Tunel", "Komora Runiczna",
    )
    title = "Komnata Strażnika" if final else rng.choice(room_titles)
    _catalog_mut.catalog_assign({
        "zone": f"Mini-loch: {spec['zone']}",
        "name": f"{title} — {index}/{size}",
        "desc": (
            f"Proceduralny mini-loch odkryty w sektorze {x+1}-{y+1} biomu {spec['zone']}. "
            "Układ tej podziemnej siatki jest trwały dla seedu świata."
            + (" To finałowa komnata ze strażnikiem i skrzynią." if final else "")
        ),
        "exits": exits,
        "recommended_mastery": min(CHARACTER_MAX_LEVEL, int(spec["base_mastery"]) + (x+y)*int(spec["step"]) + index*3),
        "generated_on_demand": True,
        "v0140_mini_dungeon": True,
        "v0140_mini_kind": kind,
        "v0140_mini_index": index,
        "v0140_mini_size": size,
        "v0140_mini_final": final,
    }, 'ROOMS', ROOMS, (room_id,))
    spawns = []
    mob_pool = tuple(base for base in spec.get("mobs", ()) if base in MOB_TEMPLATES)
    if final:
        boss = v0140_miniboss_template_for_sector(kind, x, y)
        if boss:
            spawns.append((room_id, boss))
        TREASURE_CHESTS.setdefault(room_id, {
            "name": f"Skrzynia Mini-Lochu: {spec['zone']}",
            "respawn": 3600,
            "base_pool": ("soul_shard", "soul_elixir", V014_TREASURE_MAP_ITEM),
            "set_pool": (),
        })
        CHEST_COLLECTION_CATALOG[room_id] = TREASURE_CHESTS[room_id]["name"]
    elif mob_pool:
        count = 1 + (1 if rng.random() < 0.45 else 0)
        for _ in range(count):
            spawns.append((room_id, rng.choice(mob_pool)))
    return room_id, tuple(spawns)

