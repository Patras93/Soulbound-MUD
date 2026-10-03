# -*- coding: utf-8 -*-
"""Runtime helpers for unique UOSSMUD superboss encounters (v1.11.35).

This module deliberately uses the existing collection_entries persistence for
per-account clears/lockouts. No new SQLite migration is required.
"""
import random
import world.uoss_superboss_world as _uoss_superboss_world_v11136
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

SUPERBOSS_COLLECTION_V11135 = "uoss_superboss_clears_v11135"
SUPERBOSS_REWARD_COLLECTION_V11135 = "uoss_superboss_rewards_v11135"

SUPERBOSS_TOKEN_ITEMS_V11135 = {
    "ruby_weapon": ("uoss_desert_rose", "Desert Rose"),
    "emerald_weapon": ("uoss_earth_harp", "Earth Harp"),
    "black_rabite": ("uoss_moogle_steel", "Moogle Steel"),
    "serpentarius": ("uoss_serpentarius_emblem", "Serpentarius Emblem"),
    "yiazmat": ("uoss_godslayers_badge", "Godslayer's Badge"),
}

BLACK_RABITE_UNIQUE_DROPS_V11135 = tuple(f"uoss_black_rabite_unique_{i}" for i in range(1, 11))
YIAZMAT_UNIQUE_DROPS_V11135 = tuple(f"uoss_yiazmat_unique_{i}" for i in range(1, 8))


def superboss_key_from_template_v11135(template):
    if not isinstance(template, dict):
        return None
    key = str(template.get("uoss_unique_superboss_key") or "")
    return key if key in UOSS_SUPERBOSS_ENCOUNTERS_V11134 else None


def superboss_cleared_v11135(db, account_id, boss_key):
    return str(boss_key) in db.collection_entry_ids(account_id, SUPERBOSS_COLLECTION_V11135)


def mark_superboss_clear_v11135(db, account_id, boss_key):
    return db.add_collection_entry(account_id, SUPERBOSS_COLLECTION_V11135, str(boss_key))


def superboss_personal_reward_v11135(db, account_id, boss_key):
    row = SUPERBOSS_TOKEN_ITEMS_V11135.get(str(boss_key))
    if not row:
        return None
    item_id, label = row
    marker = f"{boss_key}:token"
    if not db.add_collection_entry(account_id, SUPERBOSS_REWARD_COLLECTION_V11135, marker):
        return None
    db.add_item(account_id, item_id, 1)
    return item_id, label


def superboss_shared_drop_v11135(db, recipients, boss_key):
    pool = {
        "black_rabite": BLACK_RABITE_UNIQUE_DROPS_V11135,
        "yiazmat": YIAZMAT_UNIQUE_DROPS_V11135,
    }.get(str(boss_key))
    if not pool or not recipients:
        return None
    eligible = []
    for item_id in pool:
        if any(item_id not in s.server.db.collection_entry_ids(s.account_id, "equipment") for s in recipients):
            eligible.append(item_id)
    item_id = random.choice(eligible or pool)
    # Shared boss drop: exactly one copy for the party. Give it deterministically
    # to the first local participant who does not have it; otherwise party leader/killer order.
    winner = next((s for s in recipients if item_id not in s.server.db.collection_entry_ids(s.account_id, "equipment")), recipients[0])
    db.add_item(winner.account_id, item_id, 1)
    return winner, item_id


def superboss_local_party_v11137(session):
    members = session.server.party_sessions(session.account_id, same_room=session.character.room_id)
    return list(members) if members else [session]


def superboss_attack_gate_v11137(session, template):
    key = superboss_key_from_template_v11135(template)
    if not key:
        return True, ""
    spec = UOSS_SUPERBOSS_ENCOUNTERS_V11134[key]
    party = superboss_local_party_v11137(session)
    mode = str(spec.get("mode", "solo"))
    if mode == "solo" and len(party) > 1:
        return False, f"{spec['name']} jest wyzwaniem solo. Opuść drużynę albo walcz sam."
    if mode == "party" and len(party) < 2:
        return False, f"{spec['name']} jest wyzwaniem drużynowym. Potrzebujesz co najmniej 2 graczy."
    min_players=int(spec.get("min_players",0) or 0)
    max_players=int(spec.get("max_players",0) or 0)
    if min_players and len(party)<min_players:
        return False, f"{spec['name']} wymaga co najmniej {min_players} graczy w tej samej lokacji."
    if max_players and len(party)>max_players:
        return False, f"{spec['name']} dopuszcza maksymalnie {max_players} graczy."
    level_req = int(spec.get("unlock_level", 0) or 0)
    for member in party:
        if level_req and int(member.character.character_level) < level_req:
            return False, f"{member.character.name} nie spełnia wymogu Level {level_req} dla {spec['name']}."
    if spec.get("party_members_must_unlock"):
        for member in party:
            unlocked = bool(member.server.db.collection_entry_ids(member.account_id, "deep_dungeon_discovery"))
            if not unlocked:
                return False, f"{member.character.name} nie odblokował jeszcze Serpentariusa przez eksplorację Deep Dungeon."
    if superboss_cleared_v11135(session.server.db, session.account_id, key) and spec.get("once_per_cycle"):
        return False, f"{spec['name']} jest już przez ciebie zaliczony w trwałym cyklu."
    return True, ""


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
        name=chosen if chosen in tuple(helpers) else tuple(helpers)[0]
    elif helper:
        name = str(helper)
    else:
        return None
    return {"name":name, "damage_multiplier":1.12, "damage_reduction":0.08}


def superboss_phase_v11137(template, mob):
    key = superboss_key_from_template_v11135(template)
    if not key:
        return None
    max_hp = max(1, int(template.get("max_hp", 1)))
    pct = max(0.0, min(1.0, float(mob.hp) / max_hp))
    if pct <= 0.25:
        return 3
    if pct <= 0.60:
        return 2
    return 1


def superboss_counterattack_multiplier_v11137(template, mob):
    phase = superboss_phase_v11137(template, mob)
    if phase is None:
        return 1.0, ""
    key = superboss_key_from_template_v11135(template)
    if key == "spekkio":
        return 1.0, "Spekkio dopasowuje siłę do przeciwnika."
    if phase == 3:
        return 1.55, "Faza 3: desperacki atak Super Bossa."
    if phase == 2:
        return 1.25, "Faza 2: Super Boss zwiększa napór."
    return 1.0, "Faza 1."


SUPERBOSS_PHASE_TEXT_V11138 = {
 "asterisks":("Job Shift","Limit Break","Heroes' Finale"),
 "dad":("MAGI Guard","Guardian Pulse","Final Safeguard"),
 "diabolos":("Dream Veil","Nightmare Gravity","Dark Dream"),
 "harle":("Jester Step","Dimensional Trick","Frozen Flame"),
 "culex":("Crystal Guard","Elemental Crystal","Final Dimension"),
 "ruby_weapon":("Desert Armor","Tentacle Assault","Ruby Rage"),
 "emerald_weapon":("Abyss Pressure","Emerald Beam","Ocean Doom"),
 "ozma":("Sphere Shift","Curse Cycle","Meteor Storm"),
 "four_fiends":("Fiend Cycle","Elemental Reversal","Fourfold Finale"),
 "grahf":("Fist of Contact","Power of Id","Alpha Weltall"),
 "hades":("Forge of Hades","Underworld Craft","Masterwork Doom"),
 "lunar_trial":("Lunar Eidolon","Moon Trial","Lunar Judgment"),
 "elementals":("Mana Spirit","Element Shift","Mana Convergence"),
 "gilgamesh":("Weapon Draw","Legendary Arsenal","Big Bridge Finale"),
 "war_machines":("Twin Systems","Crossfire","Overdrive"),
 "black_rabite":("Corrupted Mana","Dark Pounce","Rabite Frenzy"),
 "serpentarius":("Zodiac Seal","Thirteenth Sign","Deep Dungeon Judgment"),
 "odin":("Sleipnir Charge","Gungnir","Zantetsuken"),
 "yiazmat":("Holy Dragon","Godslayer Trial","Cyclone"),
 "sephiroth":("Masamune","One-Winged Angel","Supernova"),
 "spekkio":("Mirror Strength","Master of War","Perfect Mirror"),
}

def superboss_phase_event_v11138(session, template, mob):
    key=superboss_key_from_template_v11135(template)
    if not key:
        return None
    phase=superboss_phase_v11137(template,mob) or 1
    seen=getattr(mob,"uoss_announced_phase_v11138",0)
    if phase <= seen:
        return None
    mob.uoss_announced_phase_v11138=phase
    label=SUPERBOSS_PHASE_TEXT_V11138.get(key,("Faza 1","Faza 2","Faza 3"))[phase-1]
    return phase,label

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
            # Odin/UOSS rule: additional players above the designed minimum
            # make the encounter harder instead of trivializing it.
            mult *= 1.0 + 0.20 * (party_count-scale_from)
            note=(note+" " if note else "")+f"Skalowanie drużyny: {party_count} graczy."
    if key=="spekkio":
        # Spekkio remains relevant regardless of level: his pressure tracks the
        # player's current defensive scale rather than a fixed authored tier.
        expected=max(1.0,float(session.consider_player_expected_hit()))
        authored=max(1.0,float(template.get("damage",1)))
        mult *= max(0.75,min(3.0,expected/authored))
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
