# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def audit_entire_world_topology_v03013(rooms):
    """Deep static topology audit including authored semantics, not just reachability."""
    from collections import defaultdict, deque
    errors = []
    warnings = []
    opposite = dict(_V03013_OPPOSITE, up="down", down="up")

    # 1. Static edges must be reciprocal. Lazy/runtime exits are counted separately.
    lazy = []
    static_edges = 0
    for rid, room in rooms.items():
        for direction, target in (room.get("exits", {}) or {}).items():
            if target not in rooms:
                lazy.append((rid, direction, target))
                continue
            static_edges += 1
            if direction in opposite:
                rev = opposite[direction]
                if rooms[target].get("exits", {}).get(rev) != rid:
                    errors.append(f"one-way static edge: {rid}.{direction}->{target}")

    # 2. Every static room reachable from square and able to return to square.
    def reachable(start, reverse=False):
        if start not in rooms:
            return set()
        graph = defaultdict(list)
        if reverse:
            for a, room in rooms.items():
                for b in (room.get("exits", {}) or {}).values():
                    if b in rooms:
                        graph[b].append(a)
        seen = {start}; q = deque([start])
        while q:
            cur = q.popleft()
            nxts = graph.get(cur, ()) if reverse else [x for x in rooms[cur].get("exits", {}).values() if x in rooms]
            for nxt in nxts:
                if nxt not in seen:
                    seen.add(nxt); q.append(nxt)
        return seen
    fwd = reachable("square")
    back = reachable("square", reverse=True)
    if len(fwd) != len(rooms):
        errors.append(f"unreachable from square: {len(rooms)-len(fwd)}")
    if len(back) != len(rooms):
        errors.append(f"cannot return to square: {len(rooms)-len(back)}")

    # 3. Every generated static zone must itself be connected internally.
    zones = defaultdict(list)
    for rid, room in rooms.items():
        if room.get("procedural_dynamic"):
            continue
        zones[str(room.get("zone") or "Bez strefy")].append(rid)
    disconnected_zones = []
    for zone, ids in zones.items():
        if len(ids) <= 1:
            continue
        allowed = set(ids); start = ids[0]; seen = {start}; q = deque([start])
        while q:
            cur = q.popleft()
            for target in rooms[cur].get("exits", {}).values():
                if target in allowed and target not in seen:
                    seen.add(target); q.append(target)
        if seen != allowed:
            disconnected_zones.append((zone, len(allowed-seen)))
    if disconnected_zones:
        errors.append("internally disconnected zones: " + repr(disconnected_zones[:10]))

    # 4. Every authored semantic adjacency captured before generation must survive.
    actual_pairs = set()
    for rid, room in rooms.items():
        for target in (room.get("exits", {}) or {}).values():
            if target in rooms and rooms[target].get("zone") == room.get("zone"):
                actual_pairs.add(tuple(sorted((rid, target))))
    missing_backbone = []
    for zone, pairs in SEMANTIC_BACKBONE_V03013.items():
        for a, b, _ in pairs:
            if tuple(sorted((a, b))) not in actual_pairs:
                missing_backbone.append((zone, a, b))
    if missing_backbone:
        errors.append(f"missing semantic backbone links: {len(missing_backbone)} sample={missing_backbone[:10]}")

    # 5. Ordered five-round trials must be exact chains without shortcuts.
    trial_errors = []
    trial_prefix = {
        "Stalowa Próba":"v020_gauntlet_stalowa_",
        "Mityczna Próba":"v020_gauntlet_mityczna_",
        "Astralna Próba":"v020_gauntlet_astralna_",
        "Wieczna Próba":"v020_gauntlet_wieczna_",
    }
    for zone, prefix in trial_prefix.items():
        ids = [f"{prefix}{i}" for i in range(1, 6)]
        expected = {tuple(sorted((ids[i], ids[i+1]))) for i in range(4)}
        got = set()
        for a in ids:
            if a not in rooms:
                trial_errors.append(f"{zone}: missing {a}"); continue
            for b in rooms[a].get("exits", {}).values():
                if b in ids:
                    got.add(tuple(sorted((a, b))))
        if got != expected:
            trial_errors.append(f"{zone}: expected chain {sorted(expected)}, got {sorted(got)}")
    if trial_errors:
        errors.extend(trial_errors)

    # 6. Explicit regression for the broken Stary Cmentarz story chain.
    cemetery_pairs = {
        tuple(sorted(("cemetery_ossuary_path", "cemetery_fallen_chapel"))),
        tuple(sorted(("cemetery_fallen_chapel", "cemetery_bell_tower"))),
        tuple(sorted(("cemetery_bone_field", "cemetery_bell_tower"))),
        tuple(sorted(("cemetery_bell_tower", "cemetery_keeper_tomb"))),
    }
    missing_cemetery = sorted(cemetery_pairs - actual_pairs)
    if missing_cemetery:
        errors.append(f"Stary Cmentarz semantic chain broken: {missing_cemetery}")

    return {
        "version":"0.30.13",
        "room_count":len(rooms),
        "static_directed_edges":static_edges,
        "lazy_runtime_exits":len(lazy),
        "zone_count":len(zones),
        "semantic_backbone_pairs":SEMANTIC_BACKBONE_PAIR_COUNT_V03013,
        "missing_semantic_backbone_pairs":len(missing_backbone),
        "disconnected_zones":len(disconnected_zones),
        "reachable_from_square":len(fwd),
        "returnable_to_square":len(back),
        "error_count":len(errors),
        "warning_count":len(warnings),
        "errors":errors,
        "warnings":warnings,
    }


def class_equipment_identity_audit_v03016():
    errors = []
    signatures = {}
    # Biegłość 600 daje wystarczający budżet liczb, by sprawdzić realny rozkład.
    for class_name in CLASS_EQUIPMENT_SETS:
        ids = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name, {}).get(400, ())
        sample = None
        for item_id in ids:
            item = ITEMS.get(item_id, {})
            if item.get("slot") == "body":
                sample = item
                break
        if not sample and ids:
            sample = ITEMS.get(ids[0], {})
        if not sample:
            errors.append(f"brak próbki EQ 400 dla {class_name}")
            continue
        signature = (
            sample.get("affix"), int(sample.get("affix_amount", 0) or 0),
            tuple(sorted((stat, int(value or 0)) for stat, value in (sample.get("stats") or {}).items())),
            tuple(sorted((prop, round(float(value or 0), 2)) for prop, value in (sample.get("properties") or {}).items())),
        )
        if signature in signatures:
            errors.append(f"identyczny profil EQ: {class_name} == {signatures[signature]}")
        signatures[signature] = class_name

    # Sloty jednej klasy również nie powinny wszystkie mieć identycznego rozkładu.
    for class_name in CLASS_EQUIPMENT_SETS:
        ids = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name, {}).get(400, ())
        split_signatures = set()
        for item_id in ids:
            item = ITEMS.get(item_id, {})
            split_signatures.add((
                int(item.get("affix_amount", 0) or 0),
                tuple(sorted(int(v or 0) for v in (item.get("stats") or {}).values())),
            ))
        if len(split_signatures) < 2:
            errors.append(f"brak różnic slotów EQ dla {class_name}")

    # v1.13.8: trzy linie sklepu tego samego Tieru muszą być realnie różne.
    # Sprawdzamy ten sam slot (hands), aby nazwa/styl nie mogły maskować kopii.
    for class_name in CLASS_EQUIPMENT_SETS:
        ids = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name, {}).get(100, ())
        style_signatures = {}
        for item_id in ids:
            item = ITEMS.get(item_id, {})
            if item.get("slot") != "hands":
                continue
            style = int(item.get("class_equipment_style", 1) or 1)
            style_signatures[style] = (
                int(item.get("defense", 0) or 0),
                int(item.get("attack", 0) or 0),
                int(item.get("magic_attack", 0) or 0),
                int(item.get("affix_amount", 0) or 0),
                tuple(sorted(
                    (stat, int(value or 0))
                    for stat, value in (item.get("stats") or {}).items()
                )),
            )
        if len(style_signatures) != 3 or len(set(style_signatures.values())) != 3:
            errors.append(f"linie stylu nadal identyczne dla {class_name}")
        if class_name == "Mec":
            for style, signature in style_signatures.items():
                if signature[1] <= 0 or signature[2] <= 0:
                    errors.append(
                        f"Mec styl {style} nie ma obu kanałów Attack/Magic Attack"
                    )

    return {
        "version": "0.30.16",
        "class_count": len(signatures),
        "unique_profile_signatures": len(signatures),
        "error_count": len(errors),
        "errors": errors,
    }

