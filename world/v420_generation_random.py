# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def v0180_active_legendary_events(now=None):
    now=time.time() if now is None else float(now)
    slot=v0180_legendary_event_slot(now)
    keys=tuple(V018_LEGENDARY_EVENT_DEFS)
    picked=[]; used=set(); used_rooms=set()
    for n in range(2):
        etype=keys[_v0140_hash_int("v018-legend-event-type",slot,n)%len(keys)]
        # ensure distinct type when possible
        if etype in used:
            etype=keys[(keys.index(etype)+1)%len(keys)]
        used.add(etype)
        d=V018_LEGENDARY_EVENT_DEFS[etype]
        kinds=tuple(d["kinds"])
        kind=kinds[_v0140_hash_int("v018-legend-event-kind",slot,n)%len(kinds)]
        x=_v0140_hash_int("v018-legend-event-x",slot,n)%V013_FRONTIER_SIDE
        y=_v0140_hash_int("v018-legend-event-y",slot,n)%V013_FRONTIER_SIDE
        room_id=v0130_frontier_room_id(kind,x,y)
        # Two different legendary events can select the same tile. The
        # location-only resolver would then hide the second event (and its
        # profession action), depending on the server's random world seed.
        # Keep the historical placement unless there really is a collision.
        if room_id in used_rooms:
            size = V013_FRONTIER_SIDE * V013_FRONTIER_SIDE
            start = _v0140_hash_int("v018-legend-event-retry-index",slot,n) % size
            for offset in range(size):
                cell = (start + offset) % size
                other_x, other_y = cell % V013_FRONTIER_SIDE, cell // V013_FRONTIER_SIDE
                other_id = v0130_frontier_room_id(kind,other_x,other_y)
                if other_id not in used_rooms:
                    x,y,room_id = other_x,other_y,other_id
                    break
            else:
                raise RuntimeError("Brak dostepnego sektora legendarnego wydarzenia")
        used_rooms.add(room_id)
        picked.append({
            "type":etype,"title":d["title"],"desc":d["desc"],"kind":kind,"x":x,"y":y,"room_id":room_id,
            "tool":d.get("tool"),"xp_mult":float(d.get("xp_mult",1.0)),"quantity_bonus":int(d.get("quantity_bonus",0)),
            "slot":slot,"token":f"{slot}:{etype}:{kind}:{x}:{y}","expires_at":(slot+1)*V018_LEGENDARY_EVENT_SECONDS,
        })
    return tuple(picked)


def v11339_world_content_audit():
    errors = []
    if set(V11339_BIOME_NAMED_RARES) != set(V013_FRONTIER_SPECS):
        errors.append("named rare catalog does not cover every frontier biome")
    if set(V11339_ELEMENT_CHASE_ITEMS) != {
        "fire", "ice", "lightning", "dark", "poison", "holy", "water", "arcane"
    }:
        errors.append("chase item catalog does not cover all eight elements")
    names = []
    for kind in V013_FRONTIER_SPECS:
        tid = v11339_named_rare_template_for_kind(kind, "rare_hunt")
        template = MOB_TEMPLATES.get(tid, {})
        names.append(str(template.get("name") or ""))
        if not template.get("v11339_named_rare"):
            errors.append(f"{kind}: named rare marker missing")
        if not template.get("attack_elements_v11339"):
            errors.append(f"{kind}: named rare elemental affinity missing")
        if not any(
            item_id in (template.get("drops") or {})
            for item_id in V11339_ELEMENT_CHASE_ITEMS.values()
        ):
            errors.append(f"{kind}: named rare chase drop missing")
    if len(names) != len(set(names)):
        errors.append("named rare display names are not unique")
    for element, item_id in V11339_ELEMENT_CHASE_ITEMS.items():
        item = ITEMS.get(item_id, {})
        if float((item.get("element_wards") or {}).get(element, 0.0) or 0.0) < 0.20:
            errors.append(f"{element}: chase item ward missing")
        if float((item.get("element_damage_bonus_pct") or {}).get(element, 0.0) or 0.0) < 12.0:
            errors.append(f"{element}: chase item elemental damage bonus missing")
    return {
        "version": "1.13.39",
        "named_rare_count": len(V11339_BIOME_NAMED_RARES),
        "chase_item_count": len(V11339_ELEMENT_CHASE_ITEMS),
        "errors": errors,
        "error_count": len(errors),
    }

