# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def boss_floor_chest_room_id(kind, floor):
    """Return the REAL room where the checkpoint boss is spawned.

    v0.10 expands dungeon floors into many _rXX rooms and moves the boss from
    the canonical landing room into the final guard room. Resolve from
    MOB_SPAWNS first so boss chests follow the boss instead of the old landing.
    """
    kind = str(kind or "")
    floor = int(floor)
    fallback = {
        "giant": f"giant_fortress_{floor}",
        "crypt": f"crypt_floor_{floor}",
        "astral": f"astral_floor_{floor}",
        "mythic_crypt": f"mythic_crypt_floor_{floor}",
        "mythic_astral": f"mythic_astral_floor_{floor}",
    }.get(kind, "")
    boss_meta = {
        "giant": ("giant_fortress_boss", "giant_fortress_floor"),
        "crypt": ("crypt_boss", "crypt_floor"),
        "astral": ("astral_boss", "astral_floor"),
        "mythic_crypt": ("mythic_crypt_boss", "mythic_crypt_floor"),
        "mythic_astral": ("mythic_astral_boss", "mythic_astral_floor"),
    }.get(kind)
    if not boss_meta:
        return fallback

    boss_flag, floor_key = boss_meta
    # v1.28.6: authoritative room marker from v0100_expand_instance_floor.
    # Dynamic floor spawns may be pruned/rehydrated independently of room map.
    canonical = ROOMS.get(fallback, {})
    marked_room = str(canonical.get('v1286_boss_chest_room', '') or '')
    if (marked_room in ROOMS and
            ROOMS[marked_room].get('v1286_boss_chest_parent') == fallback):
        return marked_room

    # Self-heal already-expanded floors without the new marker (e.g. loaded
    # from a historical runtime map). All subrooms carry numeric position.
    if canonical and f'{fallback}_r01' in ROOMS:
        best = ''
        for index in range(1, 100):
            candidate_id = f'{fallback}_r{index:02d}'
            candidate = ROOMS.get(candidate_id)
            if candidate is None:
                break
            if (candidate.get('v0100_instance_kind') == kind
                    and int(candidate.get('v0100_floor', 0) or 0) == floor
                    and int(candidate.get('v0100_floor_room', 0) or 0) > 1):
                best = candidate_id
        if best:
            # Backfill so subsequent 'look' calls stay O(1).
            canonical['v1286_boss_chest_room'] = best
            ROOMS[best]['v1286_boss_chest_parent'] = fallback
            return best

    for spawn_room, template_id in reversed(MOB_SPAWNS):
        template = MOB_TEMPLATES.get(template_id, {})
        if not template.get(boss_flag):
            continue
        try:
            template_floor = int(template.get(floor_key, 0) or 0)
        except (TypeError, ValueError, OverflowError):
            continue
        if template_floor == floor:
            return str(spawn_room)
    # Boss checkpoint chests are never at the landing after expansion.
    if any(f'{fallback}_r{n:02d}' in ROOMS for n in (1, 2)):
        return ''
    return fallback


def boss_chest_reward_roll(kind, floor, power):
    floor = int(floor)
    raw_power=max(1,int(power))
    power = raw_power if str(kind) in {"astral","mythic_astral"} else min(CHARACTER_MAX_LEVEL,raw_power)
    # v1.13.8: skrzynia bossa ma być nagrodą, nie kilkoma symbolicznymi Gold.
    kind_mult = {
        "giant": 0.90,
        "crypt": 1.00,
        "astral": 1.20,
        "mythic_crypt": 1.60,
        "mythic_astral": 1.75,
    }.get(kind, 1.0)
    base_gold = max(
        1,
        int(round(v1138_boss_chest_gold_anchor(power) * kind_mult)),
    )
    gold = random.randint(
        base_gold,
        max(base_gold, int(round(base_gold * 1.50))),
    )

    items = []
    # Fragmenty Duszy są użyteczne na każdym etapie. Endless Tower depth
    # increases quantity instead of freezing chest quality at progression 600.
    if "soul_shard" in ITEMS:
        depth_bonus=(max(0,power-600)//200) if str(kind) in {"astral","mythic_astral"} else 0
        items.extend(["soul_shard"] * random.randint(1+depth_bonus,3+depth_bonus))

    consumables = ["healing_potion", "mana_potion", "soul_elixir"]
    if power >= 60:
        consumables += ["greater_healing_potion", "greater_mana_potion", "vitality_elixir"]
    if power >= 120:
        consumables += ["supreme_healing_potion", "supreme_mana_potion", "soul_tonic"]
    if power >= 170:
        consumables += ["astral_restoration_elixir", "eternal_soul_elixir"]
    consumables = [item for item in consumables if item in ITEMS]
    if consumables:
        items.append(random.choice(consumables))

    # Szansa na surowy klejnot odblokowany na poziomie tej zawartości.
    available_gems = [
        f"raw_gem_{definition['key']}"
        for definition in GEM_DEFINITIONS
        if int(definition.get("mining_level", 1)) <= power
        and f"raw_gem_{definition['key']}" in ITEMS
    ]
    if available_gems and random.random() < min(0.55, 0.18 + power / 700.0):
        items.append(random.choice(available_gems))

    # Endgame ma małą szansę na drugi przydatny consumable.
    if power >= 100 and consumables and random.random() < 0.30:
        items.append(random.choice(consumables))

    # v1.13.63: every additional 200 effective Tower power above 600 grants
    # another useful loot roll, so boss chests keep improving without an end floor.
    if str(kind) in {"astral","mythic_astral"} and power>600 and consumables:
        for _ in range(min(8,max(0,(power-600)//200))):
            items.append(random.choice(consumables))

    return {"gold": gold, "items": items}


def _boss_floor_chest_spec(room_id):
    """Boss chest exists only in the exact room that actually contains the boss."""
    room_id = str(room_id or "")

    floor = giant_fortress_floor_number(room_id)
    if (
        is_giant_fortress_boss_floor(floor)
        and room_id == boss_floor_chest_room_id("giant", floor)
    ):
        return ("giant", floor, min(CHARACTER_MAX_LEVEL, max(20, floor * 2)))

    floor = crypt_floor_number(room_id)
    if (
        is_crypt_boss_floor(floor)
        and room_id == boss_floor_chest_room_id("crypt", floor)
    ):
        return ("crypt", floor, min(CHARACTER_MAX_LEVEL, floor))

    floor = astral_floor_number(room_id)
    if (
        is_astral_boss_floor(floor)
        and room_id == boss_floor_chest_room_id("astral", floor)
    ):
        return ("astral", floor, max(1, int(floor)))

    floor = mythic_crypt_floor_number(room_id)
    if (
        is_mythic_crypt_boss_floor(floor)
        and room_id == boss_floor_chest_room_id("mythic_crypt", floor)
    ):
        return (
            "mythic_crypt",
            floor,
            min(CHARACTER_MAX_LEVEL, 100 + floor // 2),
        )

    floor = mythic_astral_floor_number(room_id)
    if (
        is_mythic_astral_boss_floor(floor)
        and room_id == boss_floor_chest_room_id("mythic_astral", floor)
    ):
        return (
            "mythic_astral",
            floor,
            110 + floor // 2,
        )
    return None

