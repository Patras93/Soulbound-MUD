# -*- coding: utf-8 -*-
import time

from systems.elemental_combat import (
    player_element_bonus_multiplier_v11339,
    skill_element_v11339,
)

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


# ============================================================
# v1.13.39 — SYNERGY 2.0: skill primers + party reactions.
# These are optional combo interactions. Solo damage remains unchanged.
# ============================================================
V11339_SYNERGY2_MARK_SECONDS = 12.0
V11339_SYNERGY2_MAX_REACTION_MULTIPLIER = 1.35

V11339_SYNERGY2_REACTIONS = (
    {
        "id": "frostbreak",
        "name": "Frostbreak",
        "classes": frozenset(("Mag", "Wojownik")),
        "primer_class": "Mag",
        "trigger_class": "Wojownik",
        "mark": "arcane_frost",
        "primer_element": "ice",
        "multiplier": 1.25,
        "prime_text": "ARCANE FROST: cel zostaje zamrożony energią Maga.",
        "trigger_text": "SHATTER: Wojownik rozbija Arcane Frost.",
    },
    {
        "id": "venom_harvest",
        "name": "Venom Harvest",
        "classes": frozenset(("Druid", "Nekromanta")),
        "primer_class": "Druid",
        "trigger_class": "Nekromanta",
        "mark": "venom_bloom",
        "primer_element": "poison",
        "multiplier": 1.25,
        "prime_text": "VENOM BLOOM: Druid zatruwa i przygotowuje cel.",
        "trigger_text": "BLIGHTBURST: Nekromanta detonuje Venom Bloom.",
    },
    {
        "id": "hellstorm_overload",
        "name": "Hellstorm Overload",
        "classes": frozenset(("Czarownik", "Inżynier")),
        "primer_class": "Czarownik",
        "trigger_class": "Inżynier",
        "mark": "hellfire_charge",
        "primer_element": "fire",
        "trigger_element": "lightning",
        "multiplier": 1.22,
        "prime_text": "HELLFIRE CHARGE: ogień Czarownika przegrzewa cel.",
        "trigger_text": "OVERLOAD: Electric Inżyniera detonuje Hellfire.",
    },
    {
        "id": "marked_ambush",
        "name": "Marked Ambush",
        "classes": frozenset(("Łowca", "Łotrzyk")),
        "primer_class": "Łowca",
        "trigger_class": "Łotrzyk",
        "mark": "hunted_opening",
        "multiplier": 1.20,
        "prime_text": "HUNTED: Łowca otwiera słaby punkt celu.",
        "trigger_text": "AMBUSH: Łotrzyk wykorzystuje oznaczony słaby punkt.",
    },
    {
        "id": "holy_circuit_burst",
        "name": "Holy Circuit Burst",
        "classes": frozenset(("Kapłan", "Mec")),
        "primer_class": "Kapłan",
        "trigger_class": "Mec",
        "mark": "holy_charge",
        "primer_element": "holy",
        "multiplier": 1.20,
        "prime_text": "HOLY CHARGE: Kapłan nasyca cel świetlistą energią.",
        "trigger_text": "HOLY CIRCUIT: Mec wyzwala zgromadzoną energię światła.",
    },
    {
        "id": "runic_fracture",
        "name": "Runic Fracture",
        "classes": frozenset(("Strażnik", "Mag")),
        "primer_class": "Strażnik",
        "trigger_class": "Mag",
        "mark": "runic_crack",
        "multiplier": 1.20,
        "prime_text": "RUNIC CRACK: Strażnik narusza strukturę obrony celu.",
        "trigger_text": "RUNIC FRACTURE: Mag rozrywa naruszoną obronę.",
    },
    {
        "id": "mind_resonance",
        "name": "Mind Resonance",
        "classes": frozenset(("Mnich", "Psionik")),
        "primer_class": "Mnich",
        "trigger_class": "Psionik",
        "mark": "resonance",
        "multiplier": 1.20,
        "prime_text": "RESONANCE: Mnich wprowadza cel w podatny rytm.",
        "trigger_text": "MIND BREAK: Psionik rozrywa rezonans celu.",
    },
    {
        "id": "bloodrend",
        "name": "Bloodrend",
        "classes": frozenset(("Berserker", "Wojownik")),
        "primer_class": "Berserker",
        "trigger_class": "Wojownik",
        "mark": "blood_opening",
        "multiplier": 1.20,
        "prime_text": "BLOOD OPENING: Berserker rozrywa gardę celu.",
        "trigger_text": "BLOODREND: Wojownik wykorzystuje otwartą gardę.",
    },
)


def party_synergy2_local_classes_v11339(session):
    return set(party_synergy_profile_for_session_v11338(session)["classes"])


def _synergy2_mark_attr_v11339(mark):
    return "v11339_synergy2_" + str(mark) + "_until"


def party_synergy2_apply_hit_v11339(
    session,
    target,
    class_name,
    skill_name,
    damage,
    explicit_element="",
):
    """Apply elemental chase-gear bonus and at most one party reaction."""
    damage = max(0, int(damage or 0))
    if damage <= 0 or not session or not target:
        return damage, "", ""

    classes = party_synergy2_local_classes_v11339(session)
    element = skill_element_v11339(
        class_name, skill_name, explicit_element
    )
    if element:
        damage = max(
            1,
            int(round(
                damage
                * player_element_bonus_multiplier_v11339(session, element)
            )),
        )

    now = time.monotonic()

    # Trigger before primer so a hit cannot create and consume its own mark.
    for reaction in V11339_SYNERGY2_REACTIONS:
        if not reaction["classes"].issubset(classes):
            continue
        if str(class_name or "") != reaction["trigger_class"]:
            continue
        required_element = str(reaction.get("trigger_element") or "")
        if required_element and element != required_element:
            continue
        attr = _synergy2_mark_attr_v11339(reaction["mark"])
        until = float(getattr(target, attr, 0.0) or 0.0)
        if until <= now:
            continue
        setattr(target, attr, 0.0)
        multiplier = min(
            V11339_SYNERGY2_MAX_REACTION_MULTIPLIER,
            max(1.0, float(reaction["multiplier"])),
        )
        damage = max(1, int(round(damage * multiplier)))
        return (
            damage,
            " " + str(reaction["trigger_text"]),
            element,
        )

    for reaction in V11339_SYNERGY2_REACTIONS:
        if not reaction["classes"].issubset(classes):
            continue
        if str(class_name or "") != reaction["primer_class"]:
            continue
        required_element = str(reaction.get("primer_element") or "")
        if required_element and element != required_element:
            continue
        attr = _synergy2_mark_attr_v11339(reaction["mark"])
        setattr(target, attr, now + V11339_SYNERGY2_MARK_SECONDS)
        return (
            damage,
            " " + str(reaction["prime_text"]),
            element,
        )

    return damage, "", element


def party_synergy2_summary_v11339(session):
    classes = party_synergy2_local_classes_v11339(session)
    names = [
        row["name"]
        for row in V11339_SYNERGY2_REACTIONS
        if row["classes"].issubset(classes)
    ]
    return ", ".join(names) if names else "brak"


def party_synergy2_audit_v11339():
    errors = []
    ids = [row["id"] for row in V11339_SYNERGY2_REACTIONS]
    if len(ids) != 8 or len(set(ids)) != 8:
        errors.append("expected eight unique Synergy 2.0 reactions")
    if any(
        float(row.get("multiplier", 1.0))
        > V11339_SYNERGY2_MAX_REACTION_MULTIPLIER
        for row in V11339_SYNERGY2_REACTIONS
    ):
        errors.append("Synergy 2.0 reaction exceeds reviewed multiplier cap")
    frost = next(
        (row for row in V11339_SYNERGY2_REACTIONS if row["id"] == "frostbreak"),
        None,
    )
    if not frost or frost["primer_class"] != "Mag" or frost["trigger_class"] != "Wojownik":
        errors.append("Mag -> Wojownik Frostbreak contract missing")
    venom = next(
        (row for row in V11339_SYNERGY2_REACTIONS if row["id"] == "venom_harvest"),
        None,
    )
    if not venom or venom["primer_class"] != "Druid" or venom["trigger_class"] != "Nekromanta":
        errors.append("Druid -> Nekromanta Venom Harvest contract missing")
    overload = next(
        (row for row in V11339_SYNERGY2_REACTIONS if row["id"] == "hellstorm_overload"),
        None,
    )
    if (
        not overload
        or overload.get("primer_element") != "fire"
        or overload.get("trigger_element") != "lightning"
    ):
        errors.append("Fire -> Electric Hellstorm Overload contract missing")
    return {
        "version": "1.13.39",
        "reaction_count": len(V11339_SYNERGY2_REACTIONS),
        "errors": errors,
        "error_count": len(errors),
    }


PARTY_SYNERGY2_AUDIT_V11339 = party_synergy2_audit_v11339()
