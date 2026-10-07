# -*- coding: utf-8 -*-
"""Local party class synergies for Soulbound v1.13.38.

Synergies reward complementary class compositions without making any class or
pair mandatory. They activate only for living party members in the same room.
Adaptive Combat sees the same outgoing multiplier through consider/DPS paths.
"""

V11338_PARTY_SYNERGY_VERSION = "1.13.38"
V11338_PARTY_SYNERGY_DAMAGE_CAP_PCT = 20.0
V11338_PARTY_SYNERGY_HEALING_CAP_PCT = 25.0

V11338_PARTY_CLASS_SYNERGIES = (
    {
        "id": "holy_circuit",
        "name": "Święty Obwód",
        "classes": frozenset(("Kapłan", "Mec")),
        "all_damage_pct": 6.0,
        "healing_pct": 12.0,
        "description": "Kapłan stabilizuje V-MAX i wsparcie Meca.",
    },
    {
        "id": "runic_bastion",
        "name": "Runiczny Bastion",
        "classes": frozenset(("Strażnik", "Mag")),
        "all_damage_pct": 4.0,
        "magic_damage_pct": 8.0,
        "description": "Strażnik utrzymuje front, a Mag bezpiecznie wzmacnia napór.",
    },
    {
        "id": "blood_front",
        "name": "Krwawy Front",
        "classes": frozenset(("Wojownik", "Berserker")),
        "physical_damage_pct": 10.0,
        "description": "Dwie klasy natarcia podtrzymują fizyczną presję.",
    },
    {
        "id": "shadow_hunt",
        "name": "Polowanie z Cienia",
        "classes": frozenset(("Łotrzyk", "Łowca")),
        "physical_damage_pct": 10.0,
        "description": "Łowca prowadzi cel, a Łotrzyk wykorzystuje otwarcia.",
    },
    {
        "id": "mind_body",
        "name": "Jedność Ciała i Umysłu",
        "classes": frozenset(("Mnich", "Psionik")),
        "all_damage_pct": 8.0,
        "description": "Dyscyplina ciała i psionika pracują jako jeden rytm.",
    },
    {
        "id": "life_death_cycle",
        "name": "Cykl Życia i Śmierci",
        "classes": frozenset(("Nekromanta", "Druid")),
        "magic_damage_pct": 7.0,
        "healing_pct": 10.0,
        "description": "Natura i nekromancja wzmacniają magię oraz podtrzymanie drużyny.",
    },
    {
        "id": "aether_overclock",
        "name": "Przeciążenie Eteru",
        "classes": frozenset(("Czarownik", "Inżynier")),
        "all_damage_pct": 8.0,
        "magic_damage_pct": 4.0,
        "description": "Inżynier stabilizuje przeciążenie energii Czarownika.",
    },
)


def party_synergy_profile_from_classes_v11338(class_names):
    classes = frozenset(str(name or "").strip() for name in (class_names or ()) if str(name or "").strip())
    active = [
        synergy
        for synergy in V11338_PARTY_CLASS_SYNERGIES
        if synergy["classes"].issubset(classes)
    ]
    all_damage = sum(float(row.get("all_damage_pct", 0.0) or 0.0) for row in active)
    physical = all_damage + sum(
        float(row.get("physical_damage_pct", 0.0) or 0.0) for row in active
    )
    magic = all_damage + sum(
        float(row.get("magic_damage_pct", 0.0) or 0.0) for row in active
    )
    healing = sum(float(row.get("healing_pct", 0.0) or 0.0) for row in active)
    return {
        "classes": classes,
        "active": tuple(active),
        "physical_damage_pct": min(V11338_PARTY_SYNERGY_DAMAGE_CAP_PCT, physical),
        "magic_damage_pct": min(V11338_PARTY_SYNERGY_DAMAGE_CAP_PCT, magic),
        "all_damage_pct": min(V11338_PARTY_SYNERGY_DAMAGE_CAP_PCT, all_damage),
        "healing_pct": min(V11338_PARTY_SYNERGY_HEALING_CAP_PCT, healing),
    }


def party_synergy_profile_for_session_v11338(session):
    if not session or not getattr(session, "character", None):
        return party_synergy_profile_from_classes_v11338(())
    room_id = session.character.room_id
    members = session.server.party_sessions(
        session.account_id, same_room=room_id
    )
    classes = []
    for member in members or ():
        if (
            not member
            or getattr(member, "closed", False)
            or not getattr(member, "character", None)
            or getattr(member, "current_hp", 0) <= 0
        ):
            continue
        classes.append(member.character.class_name)
    return party_synergy_profile_from_classes_v11338(classes)


def party_synergy_damage_multiplier_v11338(session, channel):
    profile = party_synergy_profile_for_session_v11338(session)
    channel = str(channel or "").strip().casefold()
    if channel == "magic":
        pct = float(profile["magic_damage_pct"])
    elif channel == "physical":
        pct = float(profile["physical_damage_pct"])
    else:
        pct = float(profile["all_damage_pct"])
    return 1.0 + max(0.0, pct) / 100.0


def party_synergy_healing_multiplier_v11338(session):
    profile = party_synergy_profile_for_session_v11338(session)
    return 1.0 + max(0.0, float(profile["healing_pct"])) / 100.0


def party_synergy_summary_v11338(session):
    profile = party_synergy_profile_for_session_v11338(session)
    active = profile["active"]
    if not active:
        return "brak"
    parts = []
    for row in active:
        bonuses = []
        if float(row.get("all_damage_pct", 0.0) or 0.0):
            bonuses.append(f"+{float(row['all_damage_pct']):g}% obrażeń")
        if float(row.get("physical_damage_pct", 0.0) or 0.0):
            bonuses.append(f"+{float(row['physical_damage_pct']):g}% fizycznych")
        if float(row.get("magic_damage_pct", 0.0) or 0.0):
            bonuses.append(f"+{float(row['magic_damage_pct']):g}% magicznych")
        if float(row.get("healing_pct", 0.0) or 0.0):
            bonuses.append(f"+{float(row['healing_pct']):g}% leczenia")
        parts.append(f"{row['name']} ({', '.join(bonuses)})")
    return "; ".join(parts)


def party_synergy_audit_v11338():
    errors = []
    ids = [row["id"] for row in V11338_PARTY_CLASS_SYNERGIES]
    names = [row["name"] for row in V11338_PARTY_CLASS_SYNERGIES]
    if len(ids) != 7 or len(set(ids)) != len(ids):
        errors.append("expected seven unique party synergy ids")
    if len(set(names)) != len(names):
        errors.append("party synergy names are not unique")

    expected_classes = {
        "Wojownik", "Berserker", "Łotrzyk", "Łowca", "Mnich", "Strażnik",
        "Mag", "Nekromanta", "Kapłan", "Czarownik", "Druid", "Psionik",
        "Mec", "Inżynier",
    }
    covered = set()
    for row in V11338_PARTY_CLASS_SYNERGIES:
        pair = set(row.get("classes") or ())
        if len(pair) != 2:
            errors.append(f"{row.get('id')}: synergy must require exactly two classes")
        covered.update(pair)
    if covered != expected_classes:
        errors.append(
            "party synergy class coverage mismatch: "
            + str(sorted(expected_classes - covered))
        )

    holy = party_synergy_profile_from_classes_v11338(("Kapłan", "Mec"))
    if not holy["active"] or holy["healing_pct"] < 12.0 or holy["physical_damage_pct"] < 6.0:
        errors.append("Kapłan + Mec Holy Circuit contract failed")
    bastion = party_synergy_profile_from_classes_v11338(("Strażnik", "Mag"))
    if not bastion["active"] or bastion["magic_damage_pct"] < 12.0:
        errors.append("Strażnik + Mag Runic Bastion contract failed")
    solo = party_synergy_profile_from_classes_v11338(("Kapłan",))
    if solo["active"] or solo["physical_damage_pct"] or solo["magic_damage_pct"] or solo["healing_pct"]:
        errors.append("solo class incorrectly activates party synergy")

    all_classes = party_synergy_profile_from_classes_v11338(expected_classes)
    if all_classes["physical_damage_pct"] > V11338_PARTY_SYNERGY_DAMAGE_CAP_PCT:
        errors.append("physical synergy cap exceeded")
    if all_classes["magic_damage_pct"] > V11338_PARTY_SYNERGY_DAMAGE_CAP_PCT:
        errors.append("magic synergy cap exceeded")
    if all_classes["healing_pct"] > V11338_PARTY_SYNERGY_HEALING_CAP_PCT:
        errors.append("healing synergy cap exceeded")

    return {
        "version": V11338_PARTY_SYNERGY_VERSION,
        "synergy_count": len(V11338_PARTY_CLASS_SYNERGIES),
        "covered_classes": len(covered),
        "errors": errors,
        "error_count": len(errors),
    }


PARTY_SYNERGY_AUDIT_V11338 = party_synergy_audit_v11338()
