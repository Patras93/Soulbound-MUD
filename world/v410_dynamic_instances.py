# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def v0100_instance_spec(room_id):
    """Zwraca opis kanonicznego pokoju piętra, bez jego nowych odnóg."""
    rid = str(room_id or "")
    floor = crypt_floor_number(rid)
    if floor is not None and rid == crypt_floor_id(floor):
        return {
            "kind": "crypt", "floor": floor, "next_dir": "down",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "crypt_boss",
        }
    floor = mythic_crypt_floor_number(rid)
    if floor is not None and rid == mythic_crypt_floor_id(floor):
        return {
            "kind": "mythic_crypt", "floor": floor, "next_dir": "down",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "mythic_crypt_boss",
        }
    floor = astral_floor_number(rid)
    if floor is not None and rid == astral_floor_id(floor):
        return {
            "kind": "astral", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "astral_boss",
        }
    floor = mythic_astral_floor_number(rid)
    if floor is not None and rid == mythic_astral_floor_id(floor):
        return {
            "kind": "mythic_astral", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "mythic_astral_boss",
        }
    floor = giant_fortress_floor_number(rid)
    if floor is not None and rid == giant_fortress_floor_id(floor):
        return {
            "kind": "giant", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "giant_fortress_boss",
        }
    floor = mine_floor_number(rid)
    if floor is not None and rid == mine_floor_id(floor):
        return {
            "kind": "mine", "floor": floor, "next_dir": "down",
            "rooms": V0100_PROF_FLOOR_ROOMS, "boss_flag": None,
        }
    dungeon, floor = profession_dungeon_floor(rid)
    if dungeon is not None and rid == profession_dungeon_room_id(dungeon, floor):
        next_dirs = {
            "crystal_mine": "down", "sunken_grotto": "down",
            "ancient_forest": "south", "alchemy_garden": "east",
        }
        return {
            "kind": "profession", "profession_dungeon": dungeon,
            "floor": floor, "next_dir": next_dirs[dungeon],
            "rooms": V0100_PROF_FLOOR_ROOMS, "boss_flag": None,
        }
    return None


def v0100_expand_instance_floor(canonical_room, spawn_pairs=None, runtime=False):
    """Zmienia jedno liniowe piętro w dużą, zapętloną mapę.

    Kanoniczny pokój pozostaje lądowaniem/checkpointem. Wyjście na kolejne
    piętro zostaje przeniesione do ostatniej komnaty. Na piętrze bossa boss
    również trafia do tej komnaty, dzięki czemu naprawdę pilnuje dalszej drogi.
    """
    canonical_room = str(canonical_room or "")
    spec = v0100_instance_spec(canonical_room)
    if not spec or canonical_room not in ROOMS:
        return list(spawn_pairs or ())
    first_sub = v0100_subroom_id(canonical_room, 1)
    if first_sub in ROOMS:
        return list(spawn_pairs or ())

    base = ROOMS[canonical_room]
    exits = base.setdefault("exits", {})
    next_dir = spec["next_dir"]
    vertical_reverse = {"down":"up", "up":"down", "south":"north", "north":"south", "east":"west", "west":"east"}
    previous_dir = vertical_reverse[next_dir]
    # Jeżeli poprzednie piętro jest już rozbudowane, powrót prowadzi do jego
    # prawdziwej komnaty schodów, a nie teleportuje na początek piętra.
    previous_target = exits.get(previous_dir)
    previous_spec = v0100_instance_spec(previous_target) if previous_target else None
    if previous_spec:
        previous_final = v0100_subroom_id(previous_target, int(previous_spec["rooms"]) - 1)
        if previous_final in ROOMS:
            exits[previous_dir] = previous_final
    next_target = exits.pop(next_dir, None)
    total_rooms = max(3, int(spec["rooms"]))
    subrooms = [v0100_subroom_id(canonical_room, i) for i in range(1, total_rooms)]
    maze_rooms = subrooms[:-1]
    final_room = subrooms[-1]
    labels = V0100_INSTANCE_LABELS[spec["kind"]]
    floor = int(spec["floor"])
    zone = base.get("zone", "Loch")
    generated_profile_v025 = v0250_instance_floor_profile(spec["kind"], floor)

    for index, rid in enumerate(subrooms, 1):
        label_seed = int(hashlib.sha256(f"{spec['kind']}:{floor}".encode("utf-8")).hexdigest()[:8], 16)
        label = labels[(label_seed + index - 1) % len(labels)]
        if rid == final_room:
            if spec.get("boss_flag") and is_crypt_boss_floor(floor) and spec["kind"] in {"crypt", "mythic_crypt"}:
                label = "Komnata Strażnika Progu"
            elif spec.get("boss_flag") and spec["kind"] in {"astral", "mythic_astral"} and floor % 10 == 0:
                label = "Komnata Strażnika Kręgu"
            elif spec.get("boss_flag") and spec["kind"] == "giant" and floor % 10 == 0:
                label = "Sala Strażnika Bastionu"
        if spec["kind"] in {"crypt", "mythic_crypt"}:
            room_name = crypt_subroom_display_name(
                label, floor, index + 1, mythic=(spec["kind"] == "mythic_crypt")
            )
            room_desc = (
                "Rozległa część Krypty. Korytarze rozchodzą się w kilka stron, "
                "łączą w pętle i prowadzą przez boczne komnaty. To pełna sekcja lochu, "
                "a nie pojedynczy liniowy pokój. "
                f"Generator: {generated_profile_v025['layout']}; "
                f"motyw: {generated_profile_v025['motif']}."
            )
        else:
            room_name = f"{label} — {floor}"
            room_desc = (
                f"Rozległa część poziomu {floor}. Korytarze rozchodzą się w kilka stron, "
                "łączą w pętle i prowadzą przez boczne komnaty. To pełne piętro lochu, "
                "a nie pojedynczy liniowy pokój. "
                f"Generator piętra: {generated_profile_v025['layout']}; "
                f"motyw: {generated_profile_v025['motif']}."
            )
        _catalog_mut.catalog_assign({
            "zone": zone,
            "name": room_name,
            "desc": room_desc,
            "exits": {},
            "v0100_instance_kind": spec["kind"],
            "v0250_generator_profile": generated_profile_v025,
            "v0100_floor": floor,
            "v0100_floor_room": index + 1,
            "procedural_dynamic": True,
        }, 'ROOMS', ROOMS, (rid,))
        if "recommended_mastery" in base:
            _catalog_mut.catalog_assign(base["recommended_mastery"], 'ROOMS', ROOMS, (rid, "recommended_mastery"))
        dungeon = spec.get("profession_dungeon")
        if dungeon:
            _catalog_mut.catalog_assign(dungeon, 'ROOMS', ROOMS, (rid, "profession_dungeon"))
            _catalog_mut.catalog_assign(floor, 'ROOMS', ROOMS, (rid, "profession_dungeon_floor"))

    # v0.11.0: układ jest proceduralny, ale deterministyczny dla rodzaju i numeru
    # piętra. Restart serwera nie zmienia mapy w trakcie progresji gracza.
    seed_text = f"{V0250_WORLD_SEED}:soulbound-v0110:{spec['kind']}:{floor}:{spec.get('profession_dungeon','')}"
    floor_seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    floor_rng = random.Random(floor_seed)

    # Najpierw budujemy pełną siatkę labiryntu. Wejście z kanonicznego pokoju
    # podłączamy dopiero po utworzeniu połączeń wewnętrznych. Starszy układ
    # podpinał wejście do r01 przed siatką i mógł zająć jedyny kierunek, który
    # miał łączyć r01 z r02 (np. zwykła Krypta piętro 1), odcinając większość
    # piętra.
    reverse = {"east": "west", "west": "east", "north": "south", "south": "north"}

    # Różne piętra dostają siatkę o szerokości 3 albo 4. Każdy rząd pozostaje
    # spójny, a między kolejnymi rzędami zawsze istnieje co najmniej jedno
    # przejście; dodatkowe przejścia tworzą losowane, lecz stałe pętle.
    width = 3 + floor_rng.randrange(2)
    for idx, rid in enumerate(maze_rooms):
        row, col = divmod(idx, width)
        if col + 1 < width and idx + 1 < len(maze_rooms):
            other = maze_rooms[idx + 1]
            if "east" not in ROOMS[rid]["exits"] and "west" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "east", other, "west")

    rows = (len(maze_rooms) + width - 1) // width
    for row in range(rows - 1):
        current = list(range(row * width, min((row + 1) * width, len(maze_rooms))))
        below = list(range((row + 1) * width, min((row + 2) * width, len(maze_rooms))))
        possible = [c for c in range(min(len(current), len(below)))]
        if not possible:
            continue
        chosen = {floor_rng.choice(possible)}
        # Każde piętro ma co najmniej jedną prawdziwą pętlę, a część rzędów
        # dostaje dodatkowe alternatywne przejście.
        if len(possible) > 1 and (row == 0 or floor_rng.random() < 0.70):
            extras = [c for c in possible if c not in chosen]
            if extras:
                chosen.add(floor_rng.choice(extras))
        for c in sorted(chosen):
            a = maze_rooms[current[c]]
            b = maze_rooms[below[c]]
            if "south" not in ROOMS[a]["exits"] and "north" not in ROOMS[b]["exits"]:
                v0100_connect_pair(a, "south", b, "north")

    # Podepnij lądowanie do dowolnej komnaty brzegowej z wolnym kierunkiem.
    # Dzięki temu wejście nigdy nie rozrywa spójności siatki.
    free_attach = [d for d in ("east", "south", "west", "north") if d not in exits]
    attach_candidates = []
    for d in free_attach:
        rev = reverse[d]
        for rid in maze_rooms:
            if rev not in ROOMS[rid]["exits"]:
                attach_candidates.append((d, rid, rev))
    if not attach_candidates:
        raise RuntimeError(f"Brak wolnego połączenia wejściowego dla {canonical_room}")
    attach_dir, attach_room, attach_reverse = floor_rng.choice(attach_candidates)
    v0100_connect_pair(canonical_room, attach_dir, attach_room, attach_reverse)

    # Ostatnia komnata jest za labiryntem i zawiera drogę na kolejne piętro.
    tail = maze_rooms[-1]
    if "east" in ROOMS[tail]["exits"]:
        # Dla krótszej siatki użyj pierwszej wolnej pary.
        for d, rev in (("south", "north"), ("north", "south"), ("west", "east")):
            if d not in ROOMS[tail]["exits"] and rev not in ROOMS[final_room]["exits"]:
                v0100_connect_pair(tail, d, final_room, rev)
                break
    else:
        v0100_connect_pair(tail, "east", final_room, "west")
    if next_target:
        _catalog_mut.catalog_assign(next_target, 'ROOMS', ROOMS, (final_room, "exits", next_dir))
        # Gdy następne piętro istnieje już statycznie, jego droga powrotna
        # wskazuje na tę samą klatkę schodową. Dynamiczne piętro naprawi ten
        # link w chwili utworzenia.
        next_spec = v0100_instance_spec(next_target)
        if next_spec and next_target in ROOMS:
            _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (next_target,), "exits", {})[vertical_reverse[next_dir]] = final_room

    v0100_copy_resource_membership(canonical_room, subrooms)

    pairs = list(spawn_pairs or ())
    if not pairs and not runtime:
        pairs = [(r, t) for r, t in MOB_SPAWNS if r == canonical_room]
    boss_flag = spec.get("boss_flag")
    boss_ids = []
    regular_ids = []
    for r, tid in pairs:
        if r != canonical_room:
            continue
        template = MOB_TEMPLATES.get(tid, {})
        if boss_flag and template.get(boss_flag):
            boss_ids.append(tid)
        else:
            regular_ids.append(tid)

    # v1.28.6: Boss chest has a stable, O(1) authoritative room location.
    # In v0.11 lazy dungeons, pregenerated MOB_SPAWNS are removed and rebuilt
    # only when a player arrives. Chests must NEVER depend on whether the
    # historical spawn list happens to contain the current boss at query time.
    # The marker only exists on actual boss checkpoints, never on regular floors.
    if boss_ids:
        _catalog_mut.catalog_assign(final_room, 'ROOMS', ROOMS,
                                    (canonical_room, 'v1286_boss_chest_room'))
        _catalog_mut.catalog_assign(canonical_room, 'ROOMS', ROOMS,
                                    (final_room, 'v1286_boss_chest_parent'))

    # Przy statycznych piętrach przenieś bossów z lądowania do sali wyjściowej.
    if not runtime and boss_ids:
        moved = set(boss_ids)
        MOB_SPAWNS[:] = [
            (r, t) for r, t in MOB_SPAWNS
            if not (r == canonical_room and t in moved)
        ]
        for tid in boss_ids:
            MOB_SPAWNS.append((final_room, tid))
    elif runtime and boss_ids:
        pairs = [
            (final_room if (r == canonical_room and t in set(boss_ids)) else r, t)
            for r, t in pairs
        ]

    # Każda boczna komnata dostaje przeciwnika; część komnat ma dwa różne typy.
    extra_pairs = []
    if regular_ids:
        for index, rid in enumerate(subrooms):
            if rid == final_room and boss_ids:
                continue
            extra_pairs.append((rid, regular_ids[index % len(regular_ids)]))
            if index % 3 == 1 and len(regular_ids) > 1:
                extra_pairs.append((rid, regular_ids[(index + 1) % len(regular_ids)]))
    if runtime:
        pairs.extend(extra_pairs)
        return pairs
    MOB_SPAWNS.extend(extra_pairs)
    return pairs


def v0100_expand_surface_zone(zone, target):
    existing = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
    need = max(0, int(target) - len(existing))
    if not need:
        return
    anchor = v0100_find_surface_anchor(zone)
    if not anchor:
        return
    pool = v0100_zone_regular_pool(zone)
    safe = _collection_slug(zone)
    new_ids = [f"v0100_{safe}_{i+1:03d}" for i in range(need)]
    words = V0100_SURFACE_WORDS.get(zone, ("Szlak", "Sektor", "Przejście", "Odnoga", "Rejon"))
    for i, rid in enumerate(new_ids):
        word = words[i % len(words)]
        _catalog_mut.catalog_assign({
            "zone": zone,
            "name": f"{word} {zone} {i+1}",
            "desc": (
                f"Rozległa część regionu {zone}. Teren rozchodzi się na boczne drogi, "
                "pętle i alternatywne przejścia, dzięki czemu obszar nie jest małym expowiskiem."
            ),
            "exits": {},
            "procedural_surface_v0100": True,
        }, 'ROOMS', ROOMS, (rid,))
        endgame_recommended = dict(V0923_ENDGAME_REGIONS).get(zone)
        if endgame_recommended is not None:
            _catalog_mut.catalog_assign(int(endgame_recommended), 'ROOMS', ROOMS, (rid, "recommended_mastery"))

    reverse = {"east":"west", "west":"east", "north":"south", "south":"north"}
    anchor_exits = _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (anchor,), "exits", {})
    attach = next((d for d in ("east", "south", "west", "north") if d not in anchor_exits), None)
    if attach is None:
        return
    v0100_connect_pair(anchor, attach, new_ids[0], reverse[attach])

    width = 5
    for idx, rid in enumerate(new_ids):
        row, col = divmod(idx, width)
        if col + 1 < width and idx + 1 < len(new_ids):
            other = new_ids[idx + 1]
            if "east" not in ROOMS[rid]["exits"] and "west" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "east", other, "west")
        down_idx = idx + width
        if down_idx < len(new_ids) and (col in (0, width - 1) or (row + col) % 2 == 0):
            other = new_ids[down_idx]
            if "south" not in ROOMS[rid]["exits"] and "north" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "south", other, "north")

    # Skopiuj charakter profesyjny regionu, jeśli stara część już go miała.
    for set_name in V0100_RESOURCE_ROOM_SETS:
        room_set = globals().get(set_name)
        if isinstance(room_set, set) and any(r in room_set for r in existing):
            room_set.update(new_ids)

    if pool:
        for i, rid in enumerate(new_ids):
            MOB_SPAWNS.append((rid, pool[i % len(pool)]))
            if i % 3 == 0 and len(pool) > 1:
                MOB_SPAWNS.append((rid, pool[(i + 1) % len(pool)]))

