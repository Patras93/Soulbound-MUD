# -*- coding: utf-8 -*-
"""Persistent combat profile records and readable death causes for v1.13.41."""

V11341_COMBAT_PROFILE_VERSION = "1.13.41"


def mob_profile_xp_v11341(template):
    """Canonical public XP value used by Best Kill / Worst Defeat.

    Scanner-authored exact source XP wins. Other mobs use their authored
    class-XP reward so the record describes the opponent, not temporary party
    multipliers or Double XP.
    """
    template = template or {}
    source_xp = max(0, int(template.get("source_xp", 0) or 0))
    if bool(template.get("source_xp_exact")) and source_xp > 0:
        return source_xp
    return max(
        0,
        int(
            template.get(
                "class_xp_reward",
                template.get("stat_reward", 0),
            )
            or 0
        ),
    )


def record_combat_profile_v11341(db, account_id, record_key, template):
    if record_key not in ("best_kill", "worst_defeat"):
        raise ValueError("unsupported combat profile record")
    template = template or {}
    xp = mob_profile_xp_v11341(template)
    name = str(
        template.get("uoss_superboss_name")
        or template.get("name")
        or "Nieznany przeciwnik"
    )
    db.conn.execute(
        """
        INSERT INTO player_records_v03051(account_id,record_key,value,text_value)
        VALUES(?,?,?,?)
        ON CONFLICT(account_id,record_key) DO UPDATE SET
            value=CASE
                WHEN excluded.value>player_records_v03051.value
                THEN excluded.value ELSE player_records_v03051.value
            END,
            text_value=CASE
                WHEN excluded.value>player_records_v03051.value
                THEN excluded.text_value ELSE player_records_v03051.text_value
            END,
            updated_at=CASE
                WHEN excluded.value>player_records_v03051.value
                THEN CURRENT_TIMESTAMP ELSE player_records_v03051.updated_at
            END
        """,
        (int(account_id), str(record_key), int(xp), name),
    )
    db.conn.commit()
    return {"name": name, "xp": xp}


def backfill_combat_profile_records_v11341(db, account_id, mob_templates):
    """One-time best-effort migration from stored Bestiary/death history."""
    account_id = int(account_id)
    mob_templates = mob_templates or {}

    marker = db.conn.execute(
        "SELECT 1 FROM player_records_v03051 "
        "WHERE account_id=? AND record_key=?",
        (account_id, "combat_profile_backfill_v11341"),
    ).fetchone()
    if marker is not None:
        return

    best = combat_profile_row_v11341(db, account_id, "best_kill")
    if best is None:
        rows = db.conn.execute(
            "SELECT mob_template_id,kills FROM bestiary_stats "
            "WHERE account_id=? AND kills>0",
            (account_id,),
        ).fetchall()
        best_template = None
        best_xp = -1
        for row in rows:
            template = mob_templates.get(str(row["mob_template_id"]))
            if not template:
                continue
            xp = mob_profile_xp_v11341(template)
            if xp > best_xp:
                best_xp = xp
                best_template = template
        if best_template is not None:
            record_combat_profile_v11341(
                db, account_id, "best_kill", best_template
            )

    worst = combat_profile_row_v11341(db, account_id, "worst_defeat")
    if worst is None:
        rows = db.conn.execute(
            "SELECT killer FROM death_recaps_v03052 "
            "WHERE account_id=? ORDER BY id DESC LIMIT 500",
            (account_id,),
        ).fetchall()
        if rows:
            # Stare death recap'y przechowują tylko nazwę. Jeśli kilka
            # template'ów ma tę samą nazwę, nie zgadujemy najmocniejszego:
            # taki historyczny wpis jest z definicji niejednoznaczny.
            by_name = {}
            ambiguous_names = set()
            for template_id, template in mob_templates.items():
                name = str(
                    template.get("uoss_superboss_name")
                    or template.get("name")
                    or ""
                ).strip()
                if not name:
                    continue
                key = name.casefold()
                if key in by_name:
                    ambiguous_names.add(key)
                else:
                    by_name[key] = (str(template_id), template)
            for key in ambiguous_names:
                by_name.pop(key, None)

            worst_template = None
            worst_xp = -1
            for row in rows:
                killer = str(row["killer"] or "").strip().casefold()
                resolved = by_name.get(killer)
                if not resolved:
                    continue
                _template_id, template = resolved
                xp = mob_profile_xp_v11341(template)
                if xp > worst_xp:
                    worst_xp = xp
                    worst_template = template
            if worst_template is not None:
                record_combat_profile_v11341(
                    db, account_id, "worst_defeat", worst_template
                )

    db.conn.execute(
        """
        INSERT OR IGNORE INTO player_records_v03051(
            account_id,record_key,value,text_value
        ) VALUES(?,?,?,?)
        """,
        (account_id, "combat_profile_backfill_v11341", 1, "done"),
    )
    db.conn.commit()

def combat_profile_row_v11341(db, account_id, record_key):
    return db.conn.execute(
        """
        SELECT value,text_value
        FROM player_records_v03051
        WHERE account_id=? AND record_key=?
        """,
        (int(account_id), str(record_key)),
    ).fetchone()


def death_cause_text_v11341(killer, cause=None, room_name=""):
    cause = dict(cause or {})
    killer = str(killer or cause.get("killer") or "Nieznany przeciwnik")
    parts = [killer]
    ability = str(cause.get("ability") or "").strip()
    element = str(cause.get("element") or "").strip()
    damage_type = str(cause.get("damage_type") or "").strip().casefold()
    damage = max(0, int(cause.get("damage", 0) or 0))

    if ability:
        parts.append("atak: " + ability)
    if element:
        parts.append("żywioł: " + element)
    elif damage_type == "magic":
        parts.append("obrażenia magiczne")
    elif damage_type == "physical":
        parts.append("obrażenia fizyczne")
    if damage:
        parts.append(f"końcowe trafienie: {damage}")
    if room_name:
        parts.append("miejsce: " + str(room_name))
    return "; ".join(parts)


def combat_profile_records_audit_v11341():
    errors = []
    sample = {
        "name": "Black Rabite",
        "source_xp_exact": True,
        "source_xp": 18_900_000,
        "class_xp_reward": 1,
    }
    if mob_profile_xp_v11341(sample) != 18_900_000:
        errors.append("exact source XP does not win combat profile scoring")
    text = death_cause_text_v11341(
        "Odin",
        {
            "ability": "Giant Crush",
            "damage_type": "physical",
            "damage": 1234,
        },
        "Arena",
    )
    for needle in ("Odin", "Giant Crush", "1234", "Arena"):
        if needle not in text:
            errors.append("death cause text missing " + needle)
    return {
        "version": V11341_COMBAT_PROFILE_VERSION,
        "error_count": len(errors),
        "errors": errors,
    }


COMBAT_PROFILE_RECORDS_AUDIT_V11341 = combat_profile_records_audit_v11341()
