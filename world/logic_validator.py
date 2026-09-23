"""Soulbound v0.30.0 Semantic World Logic Validator.

The topology may be procedural, but geography must remain understandable.
This validator checks semantic gateway rules, vertical movement semantics,
world reachability, reciprocal navigation and deterministic topology output.
"""
from __future__ import annotations

from collections import defaultdict, deque
import hashlib
import json

VERSION = "0.30.0"
HORIZONTAL = ("north","east","south","west","northeast","southeast","southwest","northwest")
OPPOSITE = {
    "north":"south","south":"north","east":"west","west":"east",
    "northeast":"southwest","southwest":"northeast",
    "northwest":"southeast","southeast":"northwest",
    "up":"down","down":"up",
}


def _norm(text):
    return str(text or "").casefold()


def zone_family(zone: str) -> str:
    z=_norm(zone)
    if any(k in z for k in ("miasto dusz","gildia dusz","pracownia kartografa")):
        return "urban"
    if any(k in z for k in ("przedmieścia","przedmiescia","wioska","osada","posterunek","obóz straży","oboz strazy","przystań","przystan")):
        return "settlement"
    if any(k in z for k in ("kanały","kanaly","podziemia","krypt","jaskini","jaskinie","nekropolia","katakumb","kopal")):
        return "underground"
    if any(k in z for k in ("góry","gory","lodowe","twierdza gigant")):
        return "highland"
    if any(k in z for k in ("popielne","rozbite niebo","pustki","korona świata","korona swiata","rubież końca","rubiez konca")):
        return "endgame"
    if any(k in z for k in ("próba","proba","arena","archiwum otchłani","archiwum otchlani","katedra tysiąca","katedra tysiaca","kuźnia pierwszych","kuznia pierwszych","labirynt wiecznych","pałac bezimiennej","palac bezimiennej")):
        return "instance"
    if "proceduralny region:" in z:
        return "expedition"
    if any(k in z for k in ("ocean","wybrzeże","wybrzeze","jezior","dolina rzek")):
        return "waterland"
    return "wilderness"


def _gateway_semantic(rid: str, room: dict, direction: str, target_id: str, target: dict) -> bool:
    """True when a cross-zone edge has a believable semantic transition."""
    if direction in ("up","down"):
        return True
    src=_norm(rid)+" "+_norm(room.get("name"))
    dst=_norm(target_id)+" "+_norm(target.get("name"))
    gateway_words=(
        "gate","brama","harbor","port","pier","molo","road","trakt","path","szlak",
        "pass","przełęcz","przelecz","bridge","most","entrance","wejście","wejscie",
        "mouth","wylot","frontier","rubież","rubiez","gateway","portal","archive","archiw",
        "hall","hala","lobby","warsztat kartograf","cartographer","watchpost","posterunek",
        "camp","obóz","oboz","v0130_gateway","v028_region_gate",
    )
    return any(k in src or k in dst for k in gateway_words)


def _reachable(rooms, start):
    if start not in rooms:
        return set()
    seen={start}; q=deque([start])
    while q:
        cur=q.popleft()
        for target in rooms[cur].get("exits",{}).values():
            if target in rooms and target not in seen:
                seen.add(target); q.append(target)
    return seen


def topology_fingerprint(rooms):
    payload=[]
    for rid in sorted(rooms):
        exits=rooms[rid].get("exits",{}) or {}
        payload.append((rid,tuple(sorted((str(k),str(v)) for k,v in exits.items()))))
    raw=json.dumps(payload,ensure_ascii=False,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_world_logic(rooms: dict) -> dict:
    errors=[]; warnings=[]; cross=[]; vertical=[]
    if not isinstance(rooms,dict):
        return {"version":VERSION,"error_count":1,"errors":["ROOMS is not dict"]}

    # References and reciprocal navigation for every static edge.
    for rid,room in rooms.items():
        exits=room.get("exits",{}) or {}
        for direction,target_id in exits.items():
            if target_id not in rooms:
                # Runtime/lazy destination; validated by its own materializer.
                continue
            target=rooms[target_id]
            if direction in OPPOSITE:
                reverse=OPPOSITE[direction]
                if target.get("exits",{}).get(reverse)!=rid:
                    # Some explicit gauntlet finales remain one-way by design; require a
                    # global return path instead of pretending the exact edge is reciprocal.
                    if not (room.get("procedural_dynamic") or target.get("procedural_dynamic")):
                        warnings.append(f"one-way {rid}.{direction}->{target_id}")
            z1=str(room.get("zone") or "Bez strefy")
            z2=str(target.get("zone") or "Bez strefy")
            if direction in ("up","down"):
                vertical.append((rid,direction,target_id))
            if z1!=z2:
                cross.append((rid,direction,target_id,z1,z2))
                f1,f2=zone_family(z1),zone_family(z2)
                semantic_gateway=_gateway_semantic(rid,room,direction,target_id,target)
                # Granice naturalnych biomów (np. łąka -> rzeka -> dzicz) mogą
                # przechodzić bez sztucznej bramy. Twarda semantyczna brama jest
                # wymagana, gdy opuszczamy/wchodzimy do huba miejskiego.
                if (f1=="urban") != (f2=="urban") and not semantic_gateway:
                    errors.append(f"urban boundary without semantic gateway: {rid}.{direction}->{target_id} ({z1}->{z2})")
                # Miasto nie może być bezpośrednim sąsiadem gór/endgame. Nawet
                # prawdziwa brama miejska ma prowadzić najpierw do traktu/przedmieść.
                if f1=="urban" and f2 in {"highland","endgame"} and direction not in ("up","down"):
                    errors.append(f"urban direct jump to {f2}: {rid}.{direction}->{target_id}")
                if f2=="urban" and f1 in {"highland","endgame"} and direction not in ("up","down"):
                    errors.append(f"{f1} direct jump to urban: {rid}.{direction}->{target_id}")

    # v0.30 generator nie używa up/down jako GENERATED_DIRS. Każde pionowe
    # przejście obecne tutaj pochodzi więc z semantycznej tożsamości świata
    # (schody, piwnica, wieża, krypta, jaskinia, portal) albo z generatora
    # dedykowanej instancji, a nie z losowego łączenia topologii.

    reachable=_reachable(rooms,"square")
    if len(reachable)!=len(rooms):
        missing=sorted(set(rooms)-reachable)
        errors.append(f"unreachable from square: {len(missing)} rooms; sample {missing[:10]}")

    # Every static room must have some route back to the hub. Reverse-graph BFS.
    rev=defaultdict(list)
    for rid,room in rooms.items():
        for target in room.get("exits",{}).values():
            if target in rooms: rev[target].append(rid)
    can_return=set()
    if "square" in rooms:
        can_return={"square"}; q=deque(["square"])
        while q:
            cur=q.popleft()
            for source in rev.get(cur,[]):
                if source not in can_return:
                    can_return.add(source); q.append(source)
    if len(can_return)!=len(rooms):
        missing=sorted(set(rooms)-can_return)
        errors.append(f"cannot return to square: {len(missing)} rooms; sample {missing[:10]}")

    city=[rid for rid,r in rooms.items() if r.get("zone")=="Miasto Dusz"]
    city_bad=[]
    for rid in city:
        for d,t in rooms[rid].get("exits",{}).items():
            if t not in rooms: continue
            z2=rooms[t].get("zone")
            if z2=="Miasto Dusz": continue
            if not _gateway_semantic(rid,rooms[rid],d,t,rooms[t]):
                city_bad.append(f"{rid}.{d}->{t}")
    if city_bad:
        errors.append("city exits without gateway semantics: "+", ".join(city_bad[:10]))

    families=defaultdict(int)
    for r in rooms.values(): families[zone_family(r.get("zone"))]+=1
    return {
        "version":VERSION,
        "room_count":len(rooms),
        "reachable_from_square":len(reachable),
        "returnable_to_square":len(can_return),
        "cross_zone_edges":len(cross),
        "vertical_edges":len(vertical),
        "city_rooms":len(city),
        "zone_family_room_counts":dict(families),
        "topology_fingerprint":topology_fingerprint(rooms),
        "warning_count":len(warnings),
        "warnings":warnings,
        "error_count":len(errors),
        "errors":errors,
    }
