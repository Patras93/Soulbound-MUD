# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def _v028_build_regions():
    if "cartographer_house" not in ROOMS:
        return
    # Deterministic biome permutation; no region carries a hand-authored level.
    biome_order = sorted(V028_BIOMES, key=lambda key: balance_math.stable_unit(f"{V028_WORLD_SEED}:biome:{key}"))
    gate_ids=[]
    for index in range(1, V028_REGION_COUNT + 1):
        stage = balance_math.stage_from_index(index, V028_REGION_COUNT)
        biome_key = biome_order[(index - 1) % len(biome_order)]
        theme = V028_BIOMES[biome_key]
        gate_id=f"v028_region_gate_{index:02d}"; gate_ids.append(gate_id)
        width=4 + int(balance_math.stable_unit(f"{V028_WORLD_SEED}:{index}:w") > .52)
        height=4 + int(balance_math.stable_unit(f"{V028_WORLD_SEED}:{index}:h") > .52)
        max_distance=max(1,(width-1)+(height-1))
        zone=f"Proceduralny Region: {theme['label']}"
        _catalog_mut.catalog_assign({
            "zone":"Pracownia Kartografa", "name":f"Brama Ekspedycji {index}: {theme['label']}",
            "desc":f"Stabilna brama do wygenerowanego regionu {theme['label']}. Docelowy etap Generator Core: {stage}.",
            "exits":{}, "safe_hub":True, "procedural_region_stage":stage, "v028_region_gate":index,
        }, 'ROOMS', ROOMS, (gate_id,))
        # Create grid rooms first.
        room_ids=[]
        for y in range(height):
            for x in range(width):
                rid=_v028_region_room_id(index,x,y); room_ids.append(rid)
                dist=x+y
                span=max(6,min(28,400-stage))
                room_stage=min(CHARACTER_MAX_LEVEL,stage+int(round((dist/max_distance)*span)))
                title=_v028_pick(theme["titles"],f"r{index}:{x}:{y}:title")
                feature=_v028_pick(theme["features"],f"r{index}:{x}:{y}:feature")
                _catalog_mut.catalog_assign({
                    "zone":zone,"name":f"{title} — sektor {x+1}-{y+1}",
                    "desc":f"Wygenerowany sektor biomu {theme['label']}. Wyróżnia się tu {feature}. Układ, przeciwnicy i zasoby wynikają z trwałego seedu świata.",
                    "exits":{},"procedural_region_v028":index,"procedural_biome_v028":biome_key,
                    "procedural_region_stage":room_stage,"procedural_x":x,"procedural_y":y,
                }, 'ROOMS', ROOMS, (rid,))
        # Spanning comb guarantees connectivity; seeded extra edges create loops.
        for y in range(height):
            for x in range(width):
                rid=_v028_region_room_id(index,x,y)
                if x>0:
                    left=_v028_region_room_id(index,x-1,y)
                    _v028_connect(left,"east",rid,"west")
                if y>0:
                    below=_v028_region_room_id(index,x,y-1)
                    must_connect=(x==0)
                    extra=balance_math.stable_unit(f"{V028_WORLD_SEED}:edge:{index}:{x}:{y}")>.47
                    if must_connect or extra:
                        _v028_connect(below,"north",rid,"south")
        entry=_v028_region_room_id(index,0,0)
        boss_room=_v028_region_room_id(index,width-1,height-1)
        _catalog_mut.catalog_assign(entry, 'ROOMS', ROOMS, (gate_id, "exits", "down")); _catalog_mut.catalog_assign(gate_id, 'ROOMS', ROOMS, (entry, "exits", "up"))

        # Secrets are side rooms chosen by seed, never the entry or boss room.
        secret_candidates=[rid for rid in room_ids if rid not in (entry,boss_room)]
        secret_candidates.sort(key=lambda rid: balance_math.stable_unit(f"{V028_WORLD_SEED}:secret:{rid}"), reverse=True)
        secret_ids=[]
        for sn,base in enumerate(secret_candidates[:2],1):
            sid=f"v028_region_{index:02d}_secret_{sn:02d}"; secret_ids.append(sid)
            sstage=ROOMS[base]["procedural_region_stage"]
            _catalog_mut.catalog_assign({"zone":zone,"name":f"Sekret {theme['label']} {sn}",
                "desc":f"Ukryta odnoga regionu {theme['label']}. Generator oznaczył to miejsce jako sekret ekspedycji.",
                "exits":{"up":base},"procedural_region_v028":index,"procedural_secret":True,
                "procedural_region_stage":sstage}, 'ROOMS', ROOMS, (sid,))
            _catalog_mut.catalog_assign(sid, 'ROOMS', ROOMS, (base, "exits", "down"))

        # Real gathering locations are generated from biome semantics.
        resource_rooms=[]
        for rid in room_ids:
            if balance_math.stable_unit(f"{V028_WORLD_SEED}:resource:{rid}")>.66:
                _v0130_apply_resources(rid,{"resources":theme["resources"]}); resource_rooms.append(rid)
        if not resource_rooms:
            _v0130_apply_resources(entry,{"resources":theme["resources"]}); resource_rooms=[entry]

        # Region-specific relic; Generator Core owns its value/price/drop rate.
        relic_id=f"v028_region_{index:02d}_relic"
        _catalog_mut.catalog_assign({"name":f"Relikt: {theme['label']}","type":"material","price":1,"currency":"silver",
            "desc":f"Relikt znaleziony w proceduralnym regionie {theme['label']}.","procedural_region_stage":stage,
            "resource_category":"procedural_relic"}, 'ITEMS', ITEMS, (relic_id,))

        normal_ids=[]
        for mi in range(4):
            mid=f"v028_region_{index:02d}_mob_{mi+1}"
            word=theme["mob_words"][mi % len(theme["mob_words"])]
            _catalog_mut.catalog_assign({"name":f"{word} {theme['label']}","damage_type":theme["damage_type"],
                "drops":{relic_id:.05},"procedural_region_stage":stage,"quest_targets":(f"v028_region_{index:02d}_threat",),
                "elite_eligible":True,"rare_eligible":True}, 'MOB_TEMPLATES', MOB_TEMPLATES, (mid,))
            normal_ids.append(mid)
        elite_id=f"v028_region_{index:02d}_elite"
        _catalog_mut.catalog_assign({"name":"Elitarny Strażnik","damage_type":theme["damage_type"],
            "drops":{relic_id:.18},"procedural_region_stage":min(CHARACTER_MAX_LEVEL,stage+6),"elite_affix":"procedural",
            "quest_targets":(f"v028_region_{index:02d}_threat",f"v028_region_{index:02d}_elite_target")}, 'MOB_TEMPLATES', MOB_TEMPLATES, (elite_id,))
        rare_id=f"v028_region_{index:02d}_rare"
        _catalog_mut.catalog_assign({"name":"Rzadki Wędrowiec","damage_type":theme["damage_type"],
            "drops":{relic_id:.30},"procedural_region_stage":min(CHARACTER_MAX_LEVEL,stage+10),"rare_mob":True,
            "quest_targets":(f"v028_region_{index:02d}_threat",f"v028_region_{index:02d}_rare_target")}, 'MOB_TEMPLATES', MOB_TEMPLATES, (rare_id,))
        boss_id=f"v028_region_{index:02d}_boss"
        _catalog_mut.catalog_assign({"name":"Władca Regionu","damage_type":theme["damage_type"],
            "drops":{relic_id:1.0},"procedural_region_stage":min(CHARACTER_MAX_LEVEL,stage+18),"boss_mechanic":"procedural_region",
            "boss_mechanic_text":"Generator regionu wybiera fazę presji na podstawie etapu i biomu.",
            "quest_targets":(f"v028_region_{index:02d}_boss_target",),"leave_corpse":True}, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))

        # Seeded spawn layout: normal population everywhere, one Elite, one Rare and final boss.
        non_boss=[rid for rid in room_ids if rid!=boss_room]
        for rid in non_boss:
            pick=int(balance_math.stable_unit(f"{V028_WORLD_SEED}:spawn:{rid}")*len(normal_ids))%len(normal_ids)
            MOB_SPAWNS.append((rid,normal_ids[pick]))
            if balance_math.stable_unit(f"{V028_WORLD_SEED}:spawn2:{rid}")>.74:
                MOB_SPAWNS.append((rid,normal_ids[(pick+1)%len(normal_ids)]))
        elite_room=sorted(non_boss,key=lambda rid:balance_math.stable_unit(f"{V028_WORLD_SEED}:elite:{rid}"),reverse=True)[0]
        rare_room=sorted([rid for rid in non_boss if rid!=elite_room],key=lambda rid:balance_math.stable_unit(f"{V028_WORLD_SEED}:rare:{rid}"),reverse=True)[0]
        MOB_SPAWNS.extend(((elite_room,elite_id),(rare_room,rare_id),(boss_room,boss_id)))

        # Three generated quests per region. Their levels/rewards are recalculated by the final Core pass.
        guide_id=f"v028_region_{index:02d}_guide"; guide_name=f"Przewodnik {theme['label']}"
        q1=f"v028_region_{index:02d}_hunt"; q2=f"v028_region_{index:02d}_elite_quest"; q3=f"v028_region_{index:02d}_boss_quest"
        _catalog_mut.catalog_assign({"name":f"Ekspedycja {theme['label']}: Czystka","giver":guide_name,"kind":"kill",
            "target":f"v028_region_{index:02d}_threat","needed":balance_math.generated_count(stage,f"v028:{index}:hunt",8,18),
            "description":f"Pokonaj zagrożenia wygenerowanego regionu {theme['label']}.","reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS}, 'QUESTS', QUESTS, (q1,))
        _catalog_mut.catalog_assign({"name":f"Ekspedycja {theme['label']}: Elita","giver":guide_name,"kind":"kill",
            "target":f"v028_region_{index:02d}_elite_target","needed":1,"requires_quest":q1,
            "description":f"Pokonaj elitarnego strażnika regionu {theme['label']}.","reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS}, 'QUESTS', QUESTS, (q2,))
        _catalog_mut.catalog_assign({"name":f"Ekspedycja {theme['label']}: Władca","giver":guide_name,"kind":"kill",
            "target":boss_id,"needed":1,"requires_quest":q2,
            "description":f"Pokonaj bossa proceduralnego regionu {theme['label']}.","reward_items":{relic_id:1},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS}, 'QUESTS', QUESTS, (q3,))
        _catalog_mut.catalog_assign({"name":guide_name,"room":gate_id,
            "dialogue":f"Prowadzę wyprawy do regionu {theme['label']}. Generator Core dobiera trudność do etapu tej ekspedycji.",
            "quest":q1,"quest_chain":(q1,q2,q3)}, 'NPCS', NPCS, (guide_id,))
        V028_PROCEDURAL_REGIONS[index]={"index":index,"stage":stage,"biome":biome_key,"name":theme["label"],"gate":gate_id,
            "entry":entry,"boss_room":boss_room,"boss":boss_id,"elite":elite_id,"rare":rare_id,"rooms":tuple(room_ids),
            "secrets":tuple(secret_ids),"resource_rooms":tuple(resource_rooms),"quests":(q1,q2,q3),"relic":relic_id}

    # Safe corridor of expedition gates, attached to the Cartographer workshop.
    for i,gate in enumerate(gate_ids):
        if i>0: _v028_connect(gate_ids[i-1],"east",gate,"west")
    if "east" not in _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, ("cartographer_house",), "exits",{}):
        _catalog_mut.catalog_assign(gate_ids[0], 'ROOMS', ROOMS, ("cartographer_house", "exits", "east"))
        _catalog_mut.catalog_assign("cartographer_house", 'ROOMS', ROOMS, (gate_ids[0], "exits", "west"))


def _generate_zone_semantic_v03013(rooms, zone, ids):
    """Generator strefy zachowujący ręcznie zaprojektowany semantic backbone."""
    mod = world_topology_generator_v0281
    ids = list(ids)
    if len(ids) <= 1:
        for rid in ids:
            rooms[rid]["topology_generated_v0281"] = True
            rooms[rid]["topology_generated_v030"] = True
            rooms[rid]["topology_semantic_backbone_v03013"] = True
            rooms[rid]["world_role"] = mod._room_role(rid, rooms[rid])
        return {"rooms":len(ids), "links":0, "loops":0, "semantic_backbone_links":0, "root":ids[0] if ids else None}

    seed = f"{mod.WORLD_TOPOLOGY_SEED}:{zone}"
    # Zachowujemy tylko pion, lazy/runtime i granice stref. Poziome krawędzie
    # wewnętrzne odbudujemy: najpierw semantic backbone, potem filler.
    for rid in ids:
        old = dict(rooms[rid].get("exits", {})); new = {}
        for d, target in old.items():
            if d in ("up", "down"):
                new[d] = target
            elif target not in rooms:
                new[d] = target
            elif str(rooms[target].get("zone") or "Bez strefy") != zone:
                new[d] = target
        rooms[rid]["exits"] = new

    # Normalize vertical semantic links exactly as the v0.30 generator does.
    for rid in sorted(ids):
        for d, target in list(rooms[rid].get("exits", {}).items()):
            if d not in ("up", "down") or target not in rooms:
                continue
            if str(rooms[target].get("zone") or "Bez strefy") != zone:
                continue
            rev = mod.OPPOSITE[d]
            rooms[target].setdefault("exits", {})
            back = rooms[target]["exits"].get(rev)
            if back == rid:
                continue
            if back is None:
                rooms[target]["exits"][rev] = rid
            else:
                del rooms[rid]["exits"][d]

    # Rebuild every authored semantic adjacency before procedural filler links.
    backbone_links = 0
    zone_ids = set(ids)
    for a, b, preferred in SEMANTIC_BACKBONE_V03013.get(zone, ()): 
        if a not in zone_ids or b not in zone_ids:
            continue
        if b in rooms[a].get("exits", {}).values() or a in rooms[b].get("exits", {}).values():
            backbone_links += 1
            continue
        choices = [preferred] + [d for d in mod.GENERATED_DIRS if d != preferred]
        # Stable ordering after the authored direction keeps the result deterministic.
        tail = choices[1:]
        tail.sort(key=lambda d: mod._unit(f"{seed}:backbone:{a}:{b}:{d}"), reverse=True)
        choices = choices[:1] + tail
        connected = False
        for da in choices:
            db = mod.OPPOSITE[da]
            if mod._free(rooms[a], da) and mod._free(rooms[b], db):
                if mod._connect(rooms, a, da, b, db):
                    connected = True
                    backbone_links += 1
                    break
        if not connected:
            raise RuntimeError(f"semantic backbone has no free direction in zone {zone!r}: {a}<->{b}")

    root = mod._choose_root(zone, ids, rooms)
    comps = mod._components(rooms, ids, zone)
    comps.sort(key=lambda c: (0 if root in c else 1, mod._unit(f"{seed}:component:{'|'.join(c)}")))
    connected = list(comps[0])
    links = 0
    for comp in comps[1:]:
        cand = mod._candidate_links(rooms, connected, comp, seed)
        if not cand:
            raise RuntimeError(f"Topology generator has no free slots in zone {zone!r} for component {comp[:3]}")
        _, a, da, b, db = cand[0]
        if not mod._connect(rooms, a, da, b, db):
            raise RuntimeError(f"Topology generator failed to connect {a} and {b}")
        links += 1
        connected.extend(comp)

    # Ordered five-round trials must stay a chain. A generated loop can let the
    # player skip rounds, so those zones deliberately get no procedural shortcut.
    loop_target = 0 if zone in _V03013_ORDERED_TRIAL_ZONES else (max(1, len(ids)//6) if len(ids) >= 5 else 0)
    loops = 0
    pair_candidates = []
    ordered = sorted(ids)
    for i, a in enumerate(ordered):
        for b in ordered[i+1:]:
            if b in rooms[a].get("exits", {}).values():
                continue
            for da in mod.GENERATED_DIRS:
                db = mod.OPPOSITE[da]
                if mod._free(rooms[a], da) and mod._free(rooms[b], db):
                    compat = mod._role_compat(mod._room_role(a, rooms[a]), mod._room_role(b, rooms[b]))
                    pair_candidates.append((compat*10.0 + mod._unit(f"{seed}:loop:{a}:{da}:{b}"), a, da, b, db))
    pair_candidates.sort(reverse=True)
    for _, a, da, b, db in pair_candidates:
        if loops >= loop_target:
            break
        if mod._connect(rooms, a, da, b, db):
            loops += 1

    depth = {root:0}; q = __import__('collections').deque([root])
    while q:
        cur = q.popleft()
        for nxt in mod._internal_neighbors(rooms, cur, zone):
            if nxt not in depth:
                depth[nxt] = depth[cur] + 1; q.append(nxt)
    if len(depth) != len(ids):
        missing = sorted(set(ids)-set(depth))[:10]
        raise RuntimeError(f"Generated zone {zone!r} disconnected: {missing}")
    for rid in ids:
        rooms[rid]["topology_generated_v0281"] = True
        rooms[rid]["topology_generated_v030"] = True
        rooms[rid]["topology_semantic_backbone_v03013"] = True
        rooms[rid]["world_role"] = mod._room_role(rid, rooms[rid])
        rooms[rid]["topology_zone_depth"] = depth[rid]
        rooms[rid]["topology_seed"] = seed
    return {
        "rooms":len(ids), "links":links, "loops":loops,
        "semantic_backbone_links":backbone_links,
        "root":root, "max_depth":max(depth.values(), default=0),
    }

