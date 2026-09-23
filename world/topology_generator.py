"""Soulbound v0.30.0 Semantic Universal World Topology Generator.

All non-runtime/static zone topology is generated deterministically from a seed.
Content records keep semantic identity (room id/name/role), while adjacency is not
trusted from hand-authored horizontal exits. Existing procedural systems keep their
own generated topology. Cross-zone gateways and vertical semantic links are kept as
anchors so saves, quests and runtime portals remain compatible.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib

GENERATOR_VERSION = "0.30.0"
WORLD_TOPOLOGY_SEED = "soulbound:v0.30.0:semantic-world-topology"
CARDINAL = ("north", "east", "south", "west")
DIAGONAL = ("northeast", "southeast", "southwest", "northwest")
HORIZONTAL = CARDINAL + DIAGONAL
GENERATED_DIRS = HORIZONTAL
OPPOSITE = {"north":"south", "south":"north", "east":"west", "west":"east", "northeast":"southwest", "southwest":"northeast", "northwest":"southeast", "southeast":"northwest", "up":"down", "down":"up"}

# v0.30.0: generator ma tworzyć logiczny świat, nie losową sieć.
# Tożsamość lokacji pozostaje treścią świata, ale generator przypisuje jej
# rolę semantyczną i preferuje zgodne sąsiedztwa. Pion jest zarezerwowany
# wyłącznie dla zachowanych semantycznych schodów/piwnic/wież/portali.
def _room_role(rid: str, room: dict) -> str:
    text=(str(rid)+" "+str(room.get("name") or "")).lower()
    if any(k in text for k in ("gate", "brama", "street", "ulica", "lane", "alley", "zauł", "road", "trakt", "path", "szlak", "square", "plac")):
        return "transit"
    if any(k in text for k in ("temple", "świąty", "swiaty", "shrine", "kaplic", "cathedral", "katedr")):
        return "sacred"
    if any(k in text for k in ("guard", "straż", "straz", "barrack", "koszar", "armory", "zbroj", "watch", "patrol", "training", "arena")):
        return "guard"
    if any(k in text for k in ("harbor", "port", "dock", "stoczn", "ship", "pier", "nabrze", "warehouse", "magazyn", "ropewalk", "powroź")):
        return "harbor"
    if any(k in text for k in ("market", "targ", "inn", "karcz", "bakery", "piek", "pharmacy", "apte", "healer", "uzdrow", "kitchen", "kuchn")):
        return "commerce"
    if any(k in text for k in ("forge", "kuź", "kuz", "workshop", "warsztat", "jeweler", "jubiler", "tailor", "krawiec", "carpenter", "ciesiel", "leather", "kalet", "mason", "kamien", "potter", "garncar")):
        return "craft"
    if any(k in text for k in ("library", "bibliot", "archive", "archiw", "school", "szko", "courier", "kurier", "cartograph", "kartograf", "office", "biuro")):
        return "civic"
    if any(k in text for k in ("guild", "gild")):
        return "guild"
    if any(k in text for k in ("house", "dom", "residential", "miesz", "well", "studn")):
        return "residential"
    if any(k in text for k in ("cave", "jask", "crypt", "krypt", "sewer", "kanał", "kanal", "basement", "piwn", "dungeon", "loch", "mine", "kopal")):
        return "underground"
    if any(k in text for k in ("mountain", "gór", "gor", "summit", "szczyt", "ice", "lodow")):
        return "highland"
    if any(k in text for k in ("forest", "las", "grove", "gaj", "meadow", "łąk", "lak", "river", "rzek", "lake", "jezior", "swamp", "bag", "desert", "pust")):
        return "wilderness"
    return "general"

_ROLE_COMPAT = {
    "transit": {"transit":10,"civic":9,"commerce":9,"guard":9,"residential":9,"craft":8,"harbor":8,"sacred":8,"guild":8,"general":8,"wilderness":6,"underground":3,"highland":3},
    "sacred": {"sacred":10,"transit":9,"civic":8,"residential":6,"guard":6,"guild":5,"commerce":4,"craft":3,"harbor":3,"general":6,"underground":6,"wilderness":5,"highland":3},
    "guard": {"guard":10,"transit":9,"civic":8,"guild":7,"residential":6,"commerce":6,"craft":6,"harbor":7,"general":7,"sacred":6,"wilderness":6,"underground":6,"highland":6},
    "harbor": {"harbor":10,"transit":9,"craft":9,"commerce":8,"guard":7,"civic":6,"residential":5,"general":7,"wilderness":6,"sacred":3,"guild":5,"underground":4,"highland":2},
    "commerce": {"commerce":10,"transit":9,"craft":9,"residential":8,"civic":7,"harbor":8,"guard":6,"guild":6,"general":7,"sacred":4,"wilderness":4,"underground":3,"highland":2},
    "craft": {"craft":10,"transit":8,"commerce":9,"harbor":9,"residential":6,"guard":6,"civic":6,"guild":6,"general":7,"sacred":3,"wilderness":5,"underground":5,"highland":5},
    "civic": {"civic":10,"transit":9,"sacred":8,"guard":8,"commerce":7,"guild":8,"residential":7,"craft":6,"harbor":6,"general":7,"wilderness":4,"underground":4,"highland":3},
    "guild": {"guild":10,"transit":9,"civic":8,"guard":8,"commerce":7,"craft":7,"residential":5,"harbor":5,"sacred":5,"general":7,"wilderness":5,"underground":5,"highland":5},
    "residential": {"residential":10,"transit":9,"commerce":8,"civic":7,"craft":6,"guard":6,"sacred":6,"guild":5,"harbor":5,"general":7,"wilderness":4,"underground":3,"highland":2},
    "underground": {"underground":10,"transit":5,"guard":6,"sacred":6,"craft":5,"general":6,"wilderness":6,"highland":7},
    "highland": {"highland":10,"wilderness":8,"transit":5,"guard":6,"craft":5,"underground":7,"general":6},
    "wilderness": {"wilderness":10,"highland":8,"underground":7,"transit":6,"guard":6,"craft":5,"general":7},
    "general": {"general":8,"transit":8,"civic":7,"commerce":7,"guard":7,"craft":7,"harbor":7,"sacred":6,"guild":7,"residential":7,"wilderness":7,"underground":6,"highland":6},
}

def _role_compat(a_role: str, b_role: str) -> int:
    return int(_ROLE_COMPAT.get(a_role, {}).get(b_role, _ROLE_COMPAT.get(b_role, {}).get(a_role, 5)))


def _unit(text: str) -> float:
    raw = hashlib.sha256(str(text).encode("utf-8")).digest()
    return int.from_bytes(raw[:8], "big") / float((1 << 64) - 1)


def _is_native_procedural(room: dict) -> bool:
    # v0.28 regions already own their complete topology. Other runtime/infinite
    # dungeons are materialized outside the static ROOMS registry.
    return bool(room.get("procedural_region_v028") or room.get("procedural_dynamic"))


def _normalize_cross_zone_edges(rooms):
    """Make every static cross-zone edge geometrically reciprocal.

    The semantic zone relationship is preserved, but direction slots are chosen
    deterministically. This removes legacy cases such as south one way / west back.
    """
    pairs={}
    for a,room in rooms.items():
        za=str(room.get("zone") or "Bez strefy")
        for d,b in list((room.get("exits") or {}).items()):
            if b not in rooms: continue
            zb=str(rooms[b].get("zone") or "Bez strefy")
            if za==zb: continue
            key=tuple(sorted((a,b)))
            pairs.setdefault(key,[]).append((a,d,b))
    for (x,y),records in sorted(pairs.items()):
        # Remove only direct x<->y links; unrelated exits keep their slots.
        old_xy=[]; old_yx=[]
        for d,t in list(rooms[x].setdefault("exits",{}).items()):
            if t==y: old_xy.append(d); del rooms[x]["exits"][d]
        for d,t in list(rooms[y].setdefault("exits",{}).items()):
            if t==x: old_yx.append(d); del rooms[y]["exits"][d]
        # Preserve true vertical semantics whenever possible.
        preferred=[]
        for d in old_xy:
            preferred.append(d)
        for d in old_yx:
            if d in OPPOSITE: preferred.append(OPPOSITE[d])
        ordered=[]
        for d in preferred + list(HORIZONTAL) + ["up","down"]:
            if d in OPPOSITE and d not in ordered: ordered.append(d)
        chosen=None
        for d in ordered:
            rev=OPPOSITE[d]
            if _free(rooms[x],d) and _free(rooms[y],rev):
                chosen=(d,rev); break
        if not chosen:
            raise RuntimeError(f"No reciprocal direction slots for cross-zone edge {x}<->{y}")
        rooms[x]["exits"][chosen[0]]=y
        rooms[y]["exits"][chosen[1]]=x


def _zone_groups(rooms):
    groups = defaultdict(list)
    for rid, room in rooms.items():
        if _is_native_procedural(room):
            continue
        groups[str(room.get("zone") or "Bez strefy")].append(rid)
    return groups


def _free(room, direction):
    return direction not in room.setdefault("exits", {})


def _connect(rooms, a, da, b, db):
    if not _free(rooms[a], da) or not _free(rooms[b], db):
        return False
    rooms[a]["exits"][da] = b
    rooms[b]["exits"][db] = a
    return True


def _internal_neighbors(rooms, rid, zone):
    out=[]
    for target in rooms[rid].get("exits", {}).values():
        if target in rooms and str(rooms[target].get("zone") or "Bez strefy") == zone:
            out.append(target)
    return out


def _components(rooms, ids, zone):
    # Only reciprocal preserved links form a pre-connected component. One-way
    # historical links do not count, because the generated world must be fully
    # navigable in both directions.
    ids=set(ids); seen=set(); comps=[]
    for start in sorted(ids):
        if start in seen: continue
        q=[start]; seen.add(start); comp=[]
        while q:
            cur=q.pop(); comp.append(cur)
            for d,nxt in rooms[cur].get("exits",{}).items():
                if nxt not in ids or nxt not in rooms: continue
                if str(rooms[nxt].get("zone") or "Bez strefy") != zone: continue
                rev=OPPOSITE.get(d)
                if not rev or rooms[nxt].get("exits",{}).get(rev)!=cur: continue
                if nxt not in seen:
                    seen.add(nxt); q.append(nxt)
        comps.append(sorted(comp))
    return comps


def _component_slots(rooms, comp):
    slots=[]
    for rid in comp:
        for d in GENERATED_DIRS:
            if _free(rooms[rid], d): slots.append((rid,d))
    return slots


def _candidate_links(rooms, left, right, seed):
    candidates=[]
    right_set=set(right)
    for a, da in _component_slots(rooms,left):
        db=OPPOSITE[da]
        for b in right_set:
            if _free(rooms[b],db):
                role_score=_role_compat(_room_role(a,rooms[a]), _room_role(b,rooms[b]))
                score=role_score*10.0 + _unit(f"{seed}:link:{a}:{da}:{b}")
                candidates.append((score,a,da,b,db))
    candidates.sort(reverse=True)
    return candidates


def _choose_root(zone, ids, rooms):
    preferred={
        "Miasto Dusz":"square", "Gildia Dusz":"guild_hall", "Wioska Górska":"mountain_village",
        "Podziemia":"temple_basement", "Kanały Pod Miastem":"sewer_entrance",
    }.get(zone)
    if preferred in ids: return preferred
    # Prefer a room with external anchors, then deterministic hash.
    ranked=[]
    for rid in ids:
        ext=sum(1 for t in rooms[rid].get("exits",{}).values() if t in rooms and rooms[t].get("zone")!=zone)
        ranked.append((-ext, _unit(f"{WORLD_TOPOLOGY_SEED}:root:{zone}:{rid}"), rid))
    ranked.sort()
    return ranked[0][2]


def _generate_zone(rooms, zone, ids):
    ids=list(ids)
    if len(ids) <= 1:
        for rid in ids:
            rooms[rid]["topology_generated_v0281"] = True
            rooms[rid]["topology_generated_v030"] = True
            rooms[rid]["world_role"] = _room_role(rid, rooms[rid])
        return {"rooms":len(ids),"links":0,"loops":0,"root":ids[0] if ids else None}

    seed=f"{WORLD_TOPOLOGY_SEED}:{zone}"
    # Keep cross-zone gateways and all vertical semantic links. Horizontal links
    # inside this zone are deliberately discarded and rebuilt from the seed.
    for rid in ids:
        old=dict(rooms[rid].get("exits",{})); new={}
        for d,target in old.items():
            if d in ("up","down"):
                new[d]=target
            elif target not in rooms:
                new[d]=target
            elif str(rooms[target].get("zone") or "Bez strefy") != zone:
                new[d]=target
        rooms[rid]["exits"]=new

    # Normalize preserved internal vertical links. A vertical pair must be exact
    # up<->down. Conflicting legacy one-way links are dropped and the affected
    # rooms are reconnected horizontally by the generated topology.
    for rid in sorted(ids):
        for d,target in list(rooms[rid].get("exits",{}).items()):
            if d not in ("up","down") or target not in rooms: continue
            if str(rooms[target].get("zone") or "Bez strefy") != zone: continue
            rev=OPPOSITE[d]
            rooms[target].setdefault("exits",{})
            back=rooms[target]["exits"].get(rev)
            if back==rid:
                continue
            if back is None:
                rooms[target]["exits"][rev]=rid
            else:
                # Another semantic vertical pair owns this shaft/stair slot.
                del rooms[rid]["exits"][d]

    root=_choose_root(zone,ids,rooms)
    comps=_components(rooms,ids,zone)
    # Put root component first, remaining components in deterministic order.
    comps.sort(key=lambda c:(0 if root in c else 1, _unit(f"{seed}:component:{'|'.join(c)}")))
    connected=list(comps[0])
    links=0
    for comp in comps[1:]:
        # Find a generated cardinal link from any already-connected node into this component.
        left=connected
        cand=_candidate_links(rooms,left,comp,seed)
        if not cand:
            raise RuntimeError(f"Topology generator has no free cardinal slots in zone {zone!r} for component {comp[:3]}")
        _,a,da,b,db=cand[0]
        if not _connect(rooms,a,da,b,db):
            raise RuntimeError(f"Topology generator failed to connect {a} and {b}")
        links+=1; connected.extend(comp)

    # Add deterministic loops, aiming at roughly one extra link per 6 rooms.
    loop_target=max(1,len(ids)//6) if len(ids)>=5 else 0
    loops=0
    pair_candidates=[]
    ordered=sorted(ids)
    for i,a in enumerate(ordered):
        for b in ordered[i+1:]:
            if b in rooms[a].get("exits",{}).values(): continue
            for da in GENERATED_DIRS:
                db=OPPOSITE[da]
                if _free(rooms[a],da) and _free(rooms[b],db):
                    compat=_role_compat(_room_role(a,rooms[a]), _room_role(b,rooms[b]))
                    pair_candidates.append((compat*10.0+_unit(f"{seed}:loop:{a}:{da}:{b}"),a,da,b,db))
    pair_candidates.sort(reverse=True)
    for _,a,da,b,db in pair_candidates:
        if loops>=loop_target: break
        if _connect(rooms,a,da,b,db): loops+=1

    # Annotate generated layout metadata.
    # BFS depth is useful for accessible map/debug output and future content generation.
    depth={root:0}; q=deque([root])
    while q:
        cur=q.popleft()
        for nxt in _internal_neighbors(rooms,cur,zone):
            if nxt not in depth:
                depth[nxt]=depth[cur]+1; q.append(nxt)
    if len(depth)!=len(ids):
        missing=sorted(set(ids)-set(depth))[:10]
        raise RuntimeError(f"Generated zone {zone!r} disconnected: {missing}")
    for rid in ids:
        rooms[rid]["topology_generated_v0281"]=True
        rooms[rid]["topology_generated_v030"]=True
        rooms[rid]["world_role"]=_room_role(rid,rooms[rid])
        rooms[rid]["topology_zone_depth"]=depth[rid]
        rooms[rid]["topology_seed"]=seed
    return {"rooms":len(ids),"links":links,"loops":loops,"root":root,"max_depth":max(depth.values(),default=0)}


def apply_world_topology(rooms: dict) -> dict:
    if not isinstance(rooms,dict): raise TypeError("rooms must be a dict")
    _normalize_cross_zone_edges(rooms)
    groups=_zone_groups(rooms)
    zones={}; errors=[]
    for zone,ids in sorted(groups.items()):
        try: zones[zone]=_generate_zone(rooms,zone,ids)
        except Exception as exc: errors.append(f"{zone}: {exc}")
    # Validate all references and reciprocal generated internal cardinal edges.
    for rid,room in rooms.items():
        zone=str(room.get("zone") or "Bez strefy")
        for d,target in room.get("exits",{}).items():
            if target not in rooms:
                # Runtime/infinite/profession dungeon entrances intentionally point
                # at rooms materialized on demand. Keep the semantic portal.
                continue
            if room.get("topology_generated_v0281") and rooms[target].get("topology_generated_v0281") and rooms[target].get("zone")==zone and d in HORIZONTAL:
                rev=OPPOSITE[d]
                if rooms[target].get("exits",{}).get(rev)!=rid:
                    errors.append(f"non-reciprocal {rid}.{d}->{target}")
    # Global reachability from default spawn; preserves the original cross-zone graph.
    if "square" in rooms:
        seen={"square"}; q=deque(["square"])
        while q:
            cur=q.popleft()
            for target in rooms[cur].get("exits",{}).values():
                if target in rooms and target not in seen:
                    seen.add(target); q.append(target)
        missing=set(rooms)-seen
    else:
        seen=set(); missing=set(rooms)
    city=[rid for rid,r in rooms.items() if r.get("zone")=="Miasto Dusz"]
    city_links=sum(1 for rid in city for t in rooms[rid].get("exits",{}).values() if t in city)//2
    return {
        "version":GENERATOR_VERSION,"seed":WORLD_TOPOLOGY_SEED,"zone_count":len(zones),
        "generated_room_count":sum(v.get("rooms",0) for v in zones.values()),
        "city_room_count":len(city),"city_internal_links":city_links,
        "static_reachable_from_square":len(seen),"static_unreachable_without_runtime":len(missing),
        "zones":zones,"error_count":len(errors),"errors":errors,
    }
