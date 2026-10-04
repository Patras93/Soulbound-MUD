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

BLACK_RABITE_UNIQUE_DROPS_V11135 = tuple(f"uoss_black_rabite_unique_{i}" for i in range(1, 11))
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
        # The supplied source confirms one Cyborg-conditional Black Rabite
        # reward but does not identify which of the ten drops it is. Do not guess
        # that Moogle Board is that item; keep all ten eligible until identified.
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
    if spec.get("lockout_hours") and superboss_cleared_v11135(session.server.db, session.account_id, key):
        remaining=superboss_lockout_remaining_v11157(session.server.db, session.account_id, key)
        hours=remaining//3600
        minutes=(remaining%3600)//60
        return False, f"{spec['name']} możesz ponownie pokonać za {hours} godz. {minutes} min."
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
    # Source establishes the helper's presence/identity but does not provide
    # a numeric damage bonus or damage-reduction percentage. Keep the helper
    # mechanically present without fabricating combat multipliers.
    return {"name":name, "damage_multiplier":1.0, "damage_reduction":0.0}


def superboss_phase_v11137(template, mob):
    return None

def superboss_counterattack_multiplier_v11137(template, mob):
    return 1.0, ""

SUPERBOSS_PHASE_TEXT_V11138 = {}

def superboss_phase_event_v11138(session, template, mob):
    return None

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
        return {"instant_death":True,"text":"Serpentarius: minęło 100 rund. Próba kończy się śmiercią."}
    if key=="odin":
        started=int(getattr(mob,"uoss_shin_zantetsuken_started_v11160",0) or 0)
        if started and turn-started>=10:
            return {"instant_death":True,"text":"Odin: Shin-Zantetsuken — upłynęło 10 rund."}
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


def superboss_source_ability_v11162(template, mob):
    """No fabricated ability cadence.

    Source pages list available abilities but do not define a turn order or
    probability. Runtime must not invent a deterministic rotation.
    """
    return None

def superboss_source_summons_v11162(session, template, mob, ability_name):
    """Summons only when a source-backed ability trigger is explicitly supplied."""
    key=superboss_key_from_template_v11135(template)
    name=str(ability_name or "")
    if key=="emerald_weapon" and name=="Open Eye":
        # Source says random Eye; selection is intentionally random rather than
        # a fabricated fixed cycle.
        return (f"uoss_add_{random.choice(('emerald_white_eye','emerald_blue_eye','emerald_red_eye'))}_v11156",)
    if key=="odin" and name=="Gungnir":
        return ("uoss_add_odin_gungnir_v11156",)*3
    return ()

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
    except Exception:
        pass
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
        mob.uoss_seifer_breakdown_v11174=True
        mob.uoss_power_breakdown_v11174=True
        effects.append("Seifer: Power Breakdown aktywny na początku walki.")
    if name=="Byblos" and key=="serpentarius":
        mob.uoss_ignore_helper_target_v11174=True
    return tuple(effects)


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
            return {"despawn":True,"text":"Emerald Torpedo eksploduje w trzeciej rundzie."}
    return None

def superboss_clear_source_statuses_v11176(session):
    active=getattr(session,"uoss_source_statuses_v11173",None)
    if isinstance(active,set):
        active.clear()


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
