# -*- coding: utf-8 -*-
"""Runtime helpers for unique UOSSMUD superboss encounters (v1.11.35).

This module deliberately uses the existing collection_entries persistence for
per-account clears/lockouts. No new SQLite migration is required.
"""
import random
from data.items import ITEMS
from datetime import datetime, timezone
import world.uoss_superboss_world as _uoss_superboss_world_v11136
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

SUPERBOSS_COLLECTION_V11135 = "uoss_superboss_clears_v11135"
SUPERBOSS_REWARD_COLLECTION_V11135 = "uoss_superboss_rewards_v11135"
SUPERBOSS_LOCKOUT_SECONDS_V11157 = 24 * 60 * 60

SUPERBOSS_TOKEN_ITEMS_V11135 = {
    "odin": ("uoss_odins_mantle", "Odin's Mantle"),
    "culex": ("quartz_chunk", "Quartz Chunk"),
    "ruby_weapon": ("uoss_desert_rose", "Desert Rose"),
    "emerald_weapon": ("uoss_earth_harp", "Earth Harp"),
    "black_rabite": ("uoss_moogle_steel", "Moogle Steel"),
    "serpentarius": ("uoss_serpentarius_emblem", "Serpentarius Emblem"),
    "yiazmat": ("uoss_godslayers_badge", "Godslayer's Badge"),
}

BLACK_RABITE_UNIQUE_DROPS_V11135 = tuple(f"uoss_black_rabite_unique_{i}" for i in range(1, 10)) + ("moogle_board",)
YIAZMAT_UNIQUE_DROPS_V11135 = tuple(f"uoss_yiazmat_unique_{i}" for i in range(1, 8))
ODIN_UNIQUE_DROPS_V11158 = tuple(f"uoss_odin_unique_{i}" for i in range(1, 9))


def superboss_key_from_template_v11135(template):
    if not isinstance(template, dict):
        return None
    key = str(template.get("uoss_unique_superboss_key") or "")
    return key if key in UOSS_SUPERBOSS_ENCOUNTERS_V11134 else None


def _superboss_clear_age_seconds_v11157(db, account_id, boss_key):
    raw = db.collection_entry_discovered_at(account_id, SUPERBOSS_COLLECTION_V11135, str(boss_key))
    if not raw:
        return None
    try:
        stamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds())
    except (TypeError, ValueError):
        # Legacy malformed timestamps must not create a permanent lockout.
        return None


def superboss_lockout_remaining_v11157(db, account_id, boss_key):
    age = _superboss_clear_age_seconds_v11157(db, account_id, boss_key)
    if age is None or age >= SUPERBOSS_LOCKOUT_SECONDS_V11157:
        return 0
    return max(1, int(SUPERBOSS_LOCKOUT_SECONDS_V11157 - age))


def superboss_cleared_v11135(db, account_id, boss_key):
    return superboss_lockout_remaining_v11157(db, account_id, boss_key) > 0


def mark_superboss_clear_v11135(db, account_id, boss_key):
    return db.touch_collection_entry(account_id, SUPERBOSS_COLLECTION_V11135, str(boss_key))


def superboss_personal_reward_v11135(db, account_id, boss_key):
    row = SUPERBOSS_TOKEN_ITEMS_V11135.get(str(boss_key))
    if not row:
        return None
    item_id, label = row
    # The encounter lockout already guarantees one legal reward per clear.
    # Do not permanently suppress the personal token after the first lifetime kill.
    marker = f"{boss_key}:token"
    db.touch_collection_entry(account_id, SUPERBOSS_REWARD_COLLECTION_V11135, marker)
    db.add_item(account_id, item_id, 1)
    return item_id, label


def superboss_personal_unique_drops_v11158(db, recipients, boss_key):
    """Give every eligible participant their own independently rolled unique drop."""
    pool = {
        "black_rabite": BLACK_RABITE_UNIQUE_DROPS_V11135,
        "yiazmat": YIAZMAT_UNIQUE_DROPS_V11135,
        "odin": ODIN_UNIQUE_DROPS_V11158,
    }.get(str(boss_key))
    if not pool or not recipients:
        return []
    awards = []
    for session in recipients:
        owned = session.server.db.collection_entry_ids(session.account_id, "equipment")
        eligible = [item_id for item_id in pool if item_id not in owned]
        if str(boss_key)=="black_rabite" and str(getattr(session.character,"race",""))!="Cyborg":
            # Confirmed project rule: Moogle Board is Black Rabite's
            # Cyborg-only unique reward.
            eligible=[item_id for item_id in eligible if item_id!="moogle_board"]
            fallback=[item_id for item_id in pool if item_id!="moogle_board"]
        else:
            fallback=list(pool)
        item_id = random.choice(eligible or fallback)
        db.add_item(session.account_id, item_id, 1)
        awards.append((session, item_id))
    return awards


# Compatibility alias for older imports; semantics are personal since v1.11.58.
def superboss_shared_drop_v11135(db, recipients, boss_key):
    return superboss_personal_unique_drops_v11158(db, recipients, boss_key)


def superboss_local_party_v11137(session):
    members = session.server.party_sessions(session.account_id, same_room=session.character.room_id)
    return list(members) if members else [session]


def superboss_member_entry_error_v11331(session, boss_key):
    """Return why this specific player cannot enter a named UOSS Super Boss."""
    key = str(boss_key or "")
    spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(key)
    if not spec or not session or not getattr(session, "character", None):
        return "Nieprawidłowy Super Boss albo brak aktywnej postaci."

    level_req = int(spec.get("unlock_level", 0) or 0)
    if level_req and int(session.character.character_level) < level_req:
        return (
            f"{session.character.name} nie spełnia wymogu Level "
            f"{level_req} dla {spec['name']}."
        )

    if (
        spec.get("unlock") == "explore_deep_dungeon"
        or spec.get("party_members_must_unlock")
    ):
        unlock_entries = session.server.db.collection_entry_ids(
            session.account_id, "deep_dungeon_discovery"
        )
        unlocked = "floor_100" in unlock_entries
        if not unlocked:
            return (
                f"{session.character.name} nie dotarł jeszcze do piętra 100 "
                f"Deep Dungeon i nie odblokował {spec['name']}."
            )

    if spec.get("lockout_hours") and superboss_cleared_v11135(
        session.server.db, session.account_id, key
    ):
        remaining = superboss_lockout_remaining_v11157(
            session.server.db, session.account_id, key
        )
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return (
            f"{session.character.name} ma jeszcze blokadę {spec['name']}: "
            f"{hours} godz. {minutes} min."
        )
    return ""


def superboss_attack_gate_v11137(session, template):
    key = superboss_key_from_template_v11135(template)
    if not key:
        return True, ""
    spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
    party = superboss_local_party_v11137(session)
    mode = str(spec.get("mode", "solo"))
    if mode == "solo" and len(party) > 1:
        return False, f"{spec['name']} jest wyzwaniem solo. Opuść drużynę albo walcz sam."
    # UOSSMUD-compatible rule: bosses designed for party play may also be challenged solo.
    # Party minimums apply only when the player actually enters with a party.
    min_players=int(spec.get("min_players",0) or 0)
    max_players=int(spec.get("max_players",0) or 0)
    if min_players and len(party) > 1 and len(party)<min_players:
        return False, f"{spec['name']} wymaga co najmniej {min_players} graczy w tej samej lokacji, jeśli wchodzisz drużyną; solo jest dozwolone."
    if max_players and len(party)>max_players:
        return False, f"{spec['name']} dopuszcza maksymalnie {max_players} graczy."
    for member in party:
        entry_error = superboss_member_entry_error_v11331(member, key)
        if entry_error:
            return False, entry_error
    return True, ""


# v1.13.30: Soulbound helper balance layer. These are deliberately modest
# gameplay roles, not claimed source-exact UOSSMUD percentages. A helper must
# be noticeable, but never replace a player or turn a superboss into auto-win.
SUPERBOSS_HELPER_ROLES_V11330 = {
    "Popoi": {
        "role": "magiczny ofensywny",
        "damage_multiplier": 1.20,
        "damage_reduction": 0.03,
    },
    "Primm": {
        "role": "zbalansowany support",
        "damage_multiplier": 1.00,
        "damage_reduction": 0.08,
    },
    "Byblos": {
        "role": "ochronny support",
        "damage_multiplier": 0.95,
        "damage_reduction": 0.10,
    },
    "Montblanc": {
        "role": "taktyczny magiczny",
        "damage_multiplier": 1.10,
        "damage_reduction": 0.06,
    },
    "Seifer": {
        "role": "fizyczny ofensywny",
        "damage_multiplier": 1.20,
        "damage_reduction": 0.03,
    },
}


def superboss_helper_balance_audit_v11330():
    errors = []
    for name, row in SUPERBOSS_HELPER_ROLES_V11330.items():
        damage = float(row.get("damage_multiplier", 0.0) or 0.0)
        reduction = float(row.get("damage_reduction", 0.0) or 0.0)
        if not 0.90 <= damage <= 1.20:
            errors.append(f"{name}: helper damage multiplier out of 0.90..1.20")
        if not 0.03 <= reduction <= 0.10:
            errors.append(f"{name}: helper reduction out of 0.03..0.10")
        # Runtime helper strike starts at 65% of the player's current build.
        # Even the most offensive helper must stay below 80% of that build.
        if 0.65 * damage > 0.80:
            errors.append(f"{name}: helper strike can exceed 80% player-build baseline")
    expected = {"Popoi", "Primm", "Byblos", "Montblanc", "Seifer"}
    if set(SUPERBOSS_HELPER_ROLES_V11330) != expected:
        errors.append("helper role roster mismatch")
    return {
        "version": "1.13.30",
        "helper_count": len(SUPERBOSS_HELPER_ROLES_V11330),
        "error_count": len(errors),
        "errors": errors,
    }


SUPERBOSS_HELPER_BALANCE_AUDIT_V11330 = superboss_helper_balance_audit_v11330()


def superboss_completion_audit_v11330():
    """Final UOSS reward/helper contract; diagnostic, never a startup raise."""
    errors = list(SUPERBOSS_HELPER_BALANCE_AUDIT_V11330.get("errors", ()))

    for boss_key, (_item_id, label) in SUPERBOSS_TOKEN_ITEMS_V11135.items():
        spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(boss_key)
        if not isinstance(spec, dict):
            errors.append(f"{boss_key}: personal token has no encounter")
            continue
        if str(spec.get("personal_token") or "") != str(label):
            errors.append(
                f"{boss_key}: encounter personal_token does not match reward mapping"
            )

    unique_contracts = {
        "black_rabite": (BLACK_RABITE_UNIQUE_DROPS_V11135, 10),
        "yiazmat": (YIAZMAT_UNIQUE_DROPS_V11135, 7),
        "odin": (ODIN_UNIQUE_DROPS_V11158, 8),
    }
    for boss_key, (pool, expected_count) in unique_contracts.items():
        spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(boss_key, {})
        if len(tuple(pool)) != expected_count:
            errors.append(
                f"{boss_key}: unique pool {len(tuple(pool))}!={expected_count}"
            )
        if int(spec.get("unique_drop_count", 0) or 0) != expected_count:
            errors.append(
                f"{boss_key}: encounter unique_drop_count mismatch"
            )
        if int(spec.get("lockout_hours", 0) or 0) != 24:
            errors.append(f"{boss_key}: personal reward lockout must remain 24h")
        if not bool(spec.get("shared_unique_drop")):
            errors.append(f"{boss_key}: personal unique reward contract missing")

    helper_names = set()
    for boss_key, spec in UOSS_SUPERBOSS_ENCOUNTERS_V11134.items():
        if spec.get("helpers"):
            helper_names.update(map(str, spec.get("helpers") or ()))
        if spec.get("helper"):
            helper_names.add(str(spec.get("helper")))
        if spec.get("helper") or spec.get("helpers"):
            if int(spec.get("helper_max_players", 0) or 0) <= 0:
                errors.append(f"{boss_key}: helper has no party-size limit")
            if int(spec.get("helper_cost_mithril", 0) or 0) != 1:
                errors.append(f"{boss_key}: helper cost must remain 1 mithril")

    missing_roles = sorted(
        helper_names - set(SUPERBOSS_HELPER_ROLES_V11330)
    )
    if missing_roles:
        errors.append("helpers without Soulbound combat role: " + ", ".join(missing_roles))

    return {
        "version": "1.13.30",
        "token_bosses": len(SUPERBOSS_TOKEN_ITEMS_V11135),
        "unique_bosses": len(unique_contracts),
        "helper_names": tuple(sorted(helper_names)),
        "error_count": len(errors),
        "errors": errors,
    }


SUPERBOSS_COMPLETION_AUDIT_V11330 = superboss_completion_audit_v11330()


def superboss_helper_profile_v11137(session, template):
    key = superboss_key_from_template_v11135(template)
    if not key:
        return None
    spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
    party = superboss_local_party_v11137(session)
    if len(party) > int(spec.get("helper_max_players", 0) or 0):
        return None
    helpers = spec.get("helpers")
    helper = spec.get("helper")
    if helpers:
        party_key=session.party_key() if session.party_key() is not None else session.account_id
        chosen=getattr(session.server,f"_uoss_helper_choice_{party_key}",None)
        if chosen not in tuple(helpers):
            return None
        name=chosen
    elif helper:
        party_key=session.party_key() if session.party_key() is not None else session.account_id
        chosen=getattr(session.server,f"_uoss_helper_choice_{party_key}",None)
        if chosen != str(helper):
            return None
        name = str(helper)
    else:
        return None
    role = dict(SUPERBOSS_HELPER_ROLES_V11330.get(name) or {})
    if not role:
        return None
    return {
        "name": name,
        "role": role["role"],
        "damage_multiplier": float(role["damage_multiplier"]),
        "damage_reduction": float(role["damage_reduction"]),
    }


# Soulbound encounter phases (not claimed as source-exact UOSS turn tables).
# Only named UOSS encounters are affected; HP is measured against the current
# adaptive total rather than the unscaled template so party/solo work alike.
SUPERBOSS_PHASE_TEXT_V11138 = {
    1: "przeciwnik wzmacnia natarcie",
    2: "przeciwnik przechodzi do desperackiej ofensywy",
    3: "przeciwnik uwalnia ostatnią rezerwę sił",
}


def superboss_phase_v11137(template, mob):
    if not superboss_key_from_template_v11135(template) or not mob or not mob.alive:
        return None
    maximum = max(1, int(getattr(mob, "adaptive_max_hp_v11330", 0) or template.get("max_hp", 1) or 1))
    fraction = max(0.0, float(mob.hp) / maximum)
    if fraction <= 0.15:
        return 3
    if fraction <= 0.40:
        return 2
    if fraction <= 0.75:
        return 1
    return 0


def superboss_counterattack_multiplier_v11137(template, mob):
    stage = superboss_phase_v11137(template, mob)
    if not stage:
        return 1.0, ""
    return 1.0 + stage * 0.07, f"Faza {stage}: wzmożony napór."


def superboss_phase_event_v11138(session, template, mob):
    stage = superboss_phase_v11137(template, mob)
    if stage is None:
        return None
    previous = int(getattr(mob, "phase_stage", 0) or 0)
    if stage <= previous:
        return None
    mob.phase_stage = stage
    return stage, SUPERBOSS_PHASE_TEXT_V11138[stage]

def superboss_incoming_multiplier_v11138(session, template, mob):
    mult,note=superboss_counterattack_multiplier_v11137(template,mob)
    helper=superboss_helper_profile_v11137(session,template)
    if helper:
        mult *= max(0.1,1.0-float(helper.get("damage_reduction",0.0)))
    key=superboss_key_from_template_v11135(template)
    spec=UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(key,{})
    scale_from=int(spec.get("difficulty_scales_above_players",0) or 0)
    if scale_from:
        party_count=len(superboss_local_party_v11137(session))
        if party_count>scale_from:
            # Source establishes that Odin becomes harder above the designed
            # party size, but no numeric per-player multiplier is supplied.
            # Preserve the rule as metadata/text instead of inventing +20%.
            note=(note+" " if note else "")+f"Skalowanie drużyny aktywne: {party_count} graczy."
    if key=="spekkio":
        # Spekkio remains relevant regardless of level: his pressure tracks the
        # player's current defensive scale rather than a fixed authored tier.
        expected=max(1.0,float(session.consider_player_expected_hit()))
        authored=max(1.0,float(template.get("damage",1)))
        # Spekkio scales to the player, but the source contract does not define
        # a universal clamp/multiplier formula. Keep the encounter flag and
        # descriptive behavior without inventing 0.75x..3.0x combat math.
    return mult,note

def superboss_series_progress_v11138(db, account_id, boss_key):
    spec=UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(str(boss_key),{})
    if not spec.get("series"):
        return None
    required=int(spec.get("required_wins",4 if boss_key=="four_fiends" else 1) or 1)
    collection=f"uoss_series_{boss_key}_v11138"
    current=len(db.collection_entry_ids(account_id,collection))
    return current,required,collection

def advance_superboss_series_v11138(db, account_id, boss_key):
    state=superboss_series_progress_v11138(db,account_id,boss_key)
    if not state:
        return None
    current,required,collection=state
    if current>=required:
        return current,required,True
    db.add_collection_entry(account_id,collection,f"stage_{current+1}")
    now=min(required,current+1)
    if boss_key=="elementals" and now>=8:
        db.add_collection_entry(account_id,"uoss_unlocks_v11138","elementals_final_foe")
    return now,required,now>=required


def weapon_pair_exchange_ready_v11141(db, account_id):
    """Both WEAPON spoils are required before the Kalm Traveler exchange."""
    inv=db.inventory(account_id)
    def qty(item_id):
        row=inv.get(item_id) if isinstance(inv,dict) else None
        if isinstance(row,dict): return int(row.get("quantity",row.get("qty",0)) or 0)
        try: return int(row or 0)
        except (TypeError,ValueError): return 0
    return qty("uoss_desert_rose")>0 and qty("uoss_earth_harp")>0

def superboss_source_round_event_v11160(session, template, mob):
    """Apply only exact numeric source mechanics; unspecified cadence/power stays descriptive."""
    key=superboss_key_from_template_v11135(template)
    if not key:
        return None
    # One source round per enemy action, not once per party target.
    marker=int(getattr(mob,"uoss_round_marker_v11176",0) or 0)
    current=int(getattr(mob,"combat_turn",0) or 0)
    if marker!=current:
        mob.uoss_round_marker_v11176=current
    turn=current
    if key=="serpentarius" and turn>100:
        return {
            "instant_death":True,
            "name":"Limit 100 rund",
            "text":"Serpentarius: minęło 100 rund. Próba kończy się śmiercią.",
        }
    if key=="odin":
        started=int(getattr(mob,"uoss_shin_zantetsuken_started_v11160",0) or 0)
        if started and turn-started>=10:
            return {
                "instant_death":True,
                "name":"Shin-Zantetsuken",
                "text":"Odin: Shin-Zantetsuken — upłynęło 10 rund.",
            }
    return None


def superboss_exact_ability_effect_v11160(session, template, mob, ability_name):
    """Resolve source abilities only when their numeric effect is explicitly known."""
    key=superboss_key_from_template_v11135(template)
    name=str(ability_name or "")
    if key=="serpentarius":
        if name=="Banish Ray" or name=="Light Pillar":
            return {"damage":9999}
        if name=="Resisted Gravija":
            return {"current_hp_fraction":0.10}
        if name=="Gravija":
            return {"current_hp_fraction":1.0/3.0}
    if key=="odin":
        if name=="Zantetsuken":
            return {"current_hp_fraction":2.0/3.0}
        if name=="Shin-Zantetsuken":
            mob.uoss_shin_zantetsuken_started_v11160=int(getattr(mob,"combat_turn",0) or 0)
            return {"countdown_rounds":10}
    if key=="yiazmat" and name=="Death Strike":
        gravityproof=bool(getattr(session,"gravityproof",False) or getattr(session.character,"gravityproof",False))
        return {"current_hp_fraction":0.50 if gravityproof else 0.80}
    return None


# Curated from source-authored ability lists. The source does not specify a
# turn-by-turn rotation, so Soulbound uses a stable, non-random 3-turn cadence.
# Fixed-HP strikes/statuses only fire through their existing vetted handlers.
SUPERBOSS_ROTATIONS_V1145 = {
    "culex": ("Crash Strike", "Dark Star", "Meteor Blast", "Flame Stone", "Dispel"),
    "emerald_weapon": ("Stamp", "Emerald Beam", "Aqua Beam", "Revenge Stamp", "Dissolving Ray"),
    "ruby_weapon": ("Big Swing", "Imp", "Mini", "Ruby Flame", "Shadow Flare", "Ultima"),
    "serpentarius": ("Resisted Gravija", "Necrotic Energy", "Gravija", "Nullify Healing", "Banish Ray", "Light Pillar", "Zodiac"),
    "odin": ("Zantetsuken", "Hall of Stone", "Hall of Lead", "Disease", "Einherjar", "Valknut", "Shin-Zantetsuken"),
    "yiazmat": ("Rake", "Ice Breath", "Death Strike", "Stone Breath", "Gust Front", "Cyclone"),
}


def superboss_source_ability_v11162(template, mob):
    """Choose at most one UOSS skill for each mob action, shared by party targets.

    A blocked summon is retried until successfully fired; other source-authored
    abilities do not displace it. Source lists stay authoritative for skill names.
    """
    turn=max(0,int(getattr(mob,"combat_turn",0) or 0))
    key=superboss_key_from_template_v11135(template)
    if turn<=0:
        return None
    if not getattr(mob,"uoss_summon_used_v1144",False):
        if key=="black_rabite" and turn>=2:
            return "Summon Greater Demon"
        if key=="emerald_weapon" and turn>=3:
            return "Open Eye"
        if key=="odin" and turn>=4:
            return "Gungnir"
    if str(getattr(mob,"template_id",""))=="uoss_add_emerald_red_eye_v11156":
        if not getattr(mob,"uoss_summon_used_v1144",False) and turn>=2:
            return "Emerald Torpedo"
        return None
    skills=SUPERBOSS_ROTATIONS_V1145.get(key,())
    if not skills or turn<6 or turn%3:
        return None
    index=(turn//3-2)%len(skills)
    chosen=skills[index]
    # Shin-Zantetsuken starts one countdown; do not keep rearming it.
    if chosen=="Shin-Zantetsuken" and getattr(mob,"uoss_shin_zantetsuken_started_v11160",0):
        return "Valknut"
    return chosen


def superboss_source_summons_v11162(session, template, mob, ability_name):
    """Return one action's summoned mobs only once, even against a full party."""
    key=superboss_key_from_template_v11135(template)
    name=str(ability_name or "")
    turn=int(getattr(mob,"combat_turn",0) or 0)
    if turn<=0 or int(getattr(mob,"uoss_last_summon_turn_v1144",-1) or -1)==turn:
        return ()
    summons=()
    if key=="black_rabite" and name=="Summon Greater Demon":
        summons=("uoss_add_greater_demon_v11156",)
    elif key=="emerald_weapon" and name=="Open Eye":
        summons=(f"uoss_add_{random.choice(('emerald_white_eye','emerald_blue_eye','emerald_red_eye'))}_v11156",)
    elif str(getattr(mob,"template_id",""))=="uoss_add_emerald_red_eye_v11156" and name=="Emerald Torpedo":
        summons=("uoss_add_emerald_torpedo_v11156",)
    elif key=="odin" and name=="Gungnir":
        summons=("uoss_add_odin_gungnir_v11156",)*3
    if summons:
        mob.uoss_last_summon_turn_v1144=turn
        mob.uoss_summon_used_v1144=True
    return summons

def superboss_source_attack_multiplier_v11162(template, ability_name):
    key=superboss_key_from_template_v11135(template)
    name=str(ability_name or "")
    if key=="odin" and name in ("Einherjar","Gungnir"):
        return 3.0
    return 1.0

def superboss_source_status_v11162(template, ability_name):
    key=superboss_key_from_template_v11135(template)
    name=str(ability_name or "")
    exact={
        ("odin","Hall of Stone"):"Petrify",
        ("odin","Hall of Lead"):"Slow",
        ("odin","Disease"):"Disease",
        ("yiazmat","Ice Breath"):"Immobilize",
        ("yiazmat","Stone Breath"):"Petrify",
        ("culex","Petal Blast"):"Don't Move",
        ("culex","Light Beam"):"Sleep",
        ("culex","Sand Storm"):"Curse",
        ("ruby_weapon","Big Swing"):"Noact",
        ("ruby_weapon","Imp"):"Imp",
        ("ruby_weapon","Mini"):"Mini",
    }
    return exact.get((key,name))

def superboss_apply_source_status_v11173(session, template, ability_name):
    """Apply a sourced status without inventing a duration.

    The status lasts until combat cleanup/cure because the supplied source data
    names the status but does not give a duration.
    """
    status=superboss_source_status_v11162(template, ability_name)
    if not status:
        return None
    normalized=str(status).lower().replace("'", "").replace(" ", "_")
    proofs=set()
    try:
        for row in session.equipped_item_rows():
            item=ITEMS.get(row["item_id"],{})
            proofs.update(str(x).lower().replace("'", "").replace(" ", "_") for x in item.get("status_proof",()))
    except Exception as exc:
        reporter = getattr(getattr(session, "server", None), "report_runtime_error", None)
        if callable(reporter):
            reporter(exc, handler="superboss_apply_source_status_v11173")
        # Fail safe: if equipment proofs cannot be verified, never apply a
        # harmful sourced status by pretending the player has no protection.
        return {"status":status,"blocked":True,"verification_failed":True}
    if normalized in proofs:
        return {"status":status,"blocked":True}
    active=getattr(session,"uoss_source_statuses_v11173",None)
    if not isinstance(active,set):
        active=set()
        session.uoss_source_statuses_v11173=active
    active.add(normalized)
    return {"status":status,"blocked":False}

def superboss_element_multiplier_v11173(template, element):
    """Resolve only explicit source weakness/resist/immune/absorb declarations."""
    key=superboss_key_from_template_v11135(template)
    spec=UOSS_SUPERBOSS_ENCOUNTERS_V11134.get(key,{})
    elem=str(element or "").strip().lower()
    if not elem:
        return 1.0,False
    def norm(values):
        if isinstance(values,str): values=(values,)
        return {str(v).strip().lower() for v in (values or ())}
    if elem in norm(spec.get("absorb")):
        return -1.0,True
    if elem in norm(spec.get("immune")):
        return 0.0,False
    # Source gives category identity but no universal numeric resistance/weakness
    # multiplier in the supplied contract. Keep it queryable without fabricating math.
    return 1.0,False



UOSS_HELPER_DEBUFF_TARGET_CONTRACTS_V11196 = {
    "Power Breakdown": {
        "source_effect": "attack_power_down",
        "soulbound_target_scope": "enemy_only",
        "numeric_source_defined": False,
    },
}


UOSS_HELPER_ABILITIES_V11174 = {
    "Popoi": ("Air Blast","Earth Slide","Acid Storm","Vine Hell","Luna Mini","Faerie Walnut"),
    "Primm": ("Lucent Beam","Cure Water","Bubble","Lumina","Dryad Preach"),
    "Byblos": ("Parasite","Pollute Soul","Cure","X-Ether"),
    "Montblanc": ("Firaga","Blizzaga","Thundaga","Darkra","Bioga","Flare","Drain","Syphon","Bubble"),
    "Seifer": ("Power Breakdown","No Mercy","Zantetsuken Reverse"),
}

def superboss_helper_ability_names_v11174(session, template):
    profile=superboss_helper_profile_v11137(session,template)
    if not profile:
        return ()
    return UOSS_HELPER_ABILITIES_V11174.get(str(profile.get("name")),())

def superboss_helper_passives_v11174(session, template, mob):
    """Exact helper mechanics that do not require inventing power/cadence."""
    profile=superboss_helper_profile_v11137(session,template)
    if not profile:
        return ()
    name=str(profile.get("name"))
    key=superboss_key_from_template_v11135(template)
    effects=[]
    if name=="Seifer" and key=="odin" and not getattr(mob,"uoss_seifer_breakdown_v11174",False):
        # Power Breakdown is a hostile debuff: it belongs to the enemy mob,
        # never to the player/party. Source does not provide a numeric reduction.
        mob.uoss_seifer_breakdown_v11174=True
        mob.uoss_power_breakdown_v11174=True
        mob.uoss_power_breakdown_target_scope_v11196="enemy_only"
        effects.append("Seifer: Power Breakdown aktywny na przeciwniku.")
    if name=="Byblos" and key=="serpentarius":
        mob.uoss_ignore_helper_target_v11174=True
    return tuple(effects)


def _helper_debuff_target_audit_v11196():
    errors=[]
    for name,row in UOSS_HELPER_DEBUFF_TARGET_CONTRACTS_V11196.items():
        if str(row.get("soulbound_target_scope",""))!="enemy_only":
            errors.append(f"{name}: helper debuff must be enemy_only")
    return {"version":"1.11.96","error_count":len(errors),"errors":errors}


HELPER_DEBUFF_TARGET_AUDIT_V11196=_helper_debuff_target_audit_v11196()
if HELPER_DEBUFF_TARGET_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "Helper Debuff Target Audit v1.11.96 failed: "
        + "; ".join(HELPER_DEBUFF_TARGET_AUDIT_V11196["errors"])
    )


def superboss_combat_start_effects_v11176(session, template, mob):
    """Exact always-on/start-of-fight effects only."""
    key=superboss_key_from_template_v11135(template)
    out=[]
    if key=="black_rabite":
        mob.uoss_permanent_protect_v11176=True
        mob.uoss_permanent_shell_v11176=True
        out.append("Black Rabite: permanent Protect i Shell.")
    out.extend(superboss_helper_passives_v11174(session,template,mob))
    return tuple(out)

def superboss_add_round_event_v11176(template, mob):
    """Exact add timing that does not require an invented damage value."""
    tid=str(getattr(mob,"template_id",""))
    if tid=="uoss_add_emerald_torpedo_v11156":
        turn=int(getattr(mob,"combat_turn",0) or 0)
        if turn>=3:
            mob.hp=0
            mob.alive=False
            mob.engaged_by=None
            # This is a transient add: do not leave a zero-HP active attacker.
            import time as _time
            mob.v016_expires_at=_time.time()-1
            return {"despawn":True,"text":"Emerald Torpedo eksploduje w trzeciej rundzie."}
    return None

def superboss_clear_source_statuses_v11176(session):
    active=getattr(session,"uoss_source_statuses_v11173",None)
    if isinstance(active,set):
        active.clear()
    session.uoss_nullify_healing_rounds_v11179=0
    session.uoss_necrotic_energy_rounds_v11179=0



def superboss_helper_exact_utility_v11183(session, template, ability_name):
    """Exact helper utility values only; caller supplies an explicit ability trigger."""
    profile=superboss_helper_profile_v11137(session,template)
    if not profile:
        return None
    helper=str(profile.get("name"))
    name=str(ability_name or "")
    if helper=="Popoi" and name=="Faerie Walnut":
        amount=max(0,int(round(session.max_mana()*0.20)))
        before=session.current_mana
        session.current_mana=min(session.max_mana(),session.current_mana+amount)
        return {"mana_restored":session.current_mana-before}
    if helper=="Primm" and name=="Bubble":
        # Source gives +50% Max HP but no duration. Keep the exact magnitude as
        # an active marker; no fabricated expiry.
        session.uoss_primm_bubble_max_hp_multiplier_v11183=1.50
        return {"max_hp_multiplier":1.50}
    return None

def superboss_source_timed_effect_v11179(session, template, ability_name):
    """Exact duration-only effects; no invented damage/cadence."""
    key=superboss_key_from_template_v11135(template)
    name=str(ability_name or "")
    if key=="serpentarius" and name=="Nullify Healing":
        session.uoss_nullify_healing_rounds_v11179=3
        return {"effect":"nullify_healing","rounds":3}
    if key=="serpentarius" and name=="Necrotic Energy":
        # Source says a specified attribute is reduced for eight rounds but the
        # supplied data does not identify a universal amount/attribute choice.
        session.uoss_necrotic_energy_rounds_v11179=8
        return {"effect":"necrotic_energy","rounds":8}
    return None

def superboss_advance_timed_effects_v11179(session):
    ended=[]
    for attr,label in (("uoss_nullify_healing_rounds_v11179","Nullify Healing"),("uoss_necrotic_energy_rounds_v11179","Necrotic Energy")):
        left=int(getattr(session,attr,0) or 0)
        if left>0:
            left-=1
            setattr(session,attr,left)
            if left==0: ended.append(label)
    return tuple(ended)

def superboss_healing_blocked_v11179(session):
    return int(getattr(session,"uoss_nullify_healing_rounds_v11179",0) or 0)>0
