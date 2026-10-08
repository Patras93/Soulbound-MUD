# -*- coding: utf-8 -*-
"""v1.15.1: finite, nonstacking monster spell effects.

Statuses live only on sessions, not in persistent character data. All effects
expire by monotonic clock; their tick budget also bounds their impact.
"""
import time

# Duration in seconds, maximum periodic ticks, and a separate reapplication gap.
MONSTER_MAGIC_EFFECTS = {
    "fire": ("burn", "Podpalenie", 9.0, 3, 0.008),
    "ice": ("chill", "Chłód", 8.0, 0, 0.0),
    "lightning": ("shock", "Porażenie", 6.0, 0, 0.0),
    "dark": ("curse", "Klątwa", 8.0, 0, 0.0),
    "shadow": ("curse", "Klątwa", 8.0, 0, 0.0),
    "void": ("mana_drain", "Wysysanie Many", 9.0, 3, 0.018),
    "poison": ("poison", "Trucizna", 12.0, 4, 0.006),
    "holy": ("blind", "Oślepienie", 6.0, 0, 0.0),
    "water": ("chill", "Mokry chłód", 8.0, 0, 0.0),
    "arcane": ("mana_drain", "Zakłócenie Many", 9.0, 3, 0.018),
}
SPELL_NAMES = {
    "fire": ("Ognista Kula", "Inferno"),
    "ice": ("Lodowa Włócznia", "Zamieć"),
    "lightning": ("Błyskawica", "Burza Gromów"),
    "dark": ("Mroczna Klątwa", "Nocny Promień"),
    "shadow": ("Szpony Cienia", "Widmowe Ostrze"),
    "void": ("Puls Pustki", "Rozdarcie Nicości"),
    "poison": ("Jadowita Chmura", "Toksyczna Fala"),
    "holy": ("Święty Promień", "Blask Sądu"),
    "water": ("Wodny Wir", "Lodowaty Przypływ"),
    "arcane": ("Pocisk Arkanów", "Magiczna Eksplozja"),
}


def monster_spell_name_v1151(element, combat_turn):
    names = SPELL_NAMES.get(str(element or ""), ())
    return names[(max(1, int(combat_turn or 1)) - 1) // 3 % len(names)] if names else ""


def monster_magic_active_v1151(session, key, now=None):
    now = time.monotonic() if now is None else float(now)
    active = getattr(session, "monster_magic_effects_v1151", {}) or {}
    return float(active.get(key, {}).get("expires", 0.0)) > now


def monster_magic_apply_v1151(session, element, roll, ward=0.0, now=None):
    """Return display text only on successful, nonrefreshing status application."""
    spec = MONSTER_MAGIC_EFFECTS.get(str(element or ""))
    if not spec or session is None:
        return ""
    now = time.monotonic() if now is None else float(now)
    kind, label, duration, ticks, strength = spec
    active = getattr(session, "monster_magic_effects_v1151", None)
    if not isinstance(active, dict):
        active = {}
        session.monster_magic_effects_v1151 = active
    # Keep only living effects. Reapplication cooldown stays separate.
    for old in tuple(active):
        if float(active[old].get("expires", 0)) <= now:
            del active[old]
    cooldown = getattr(session, "monster_magic_cooldown_v1151", None)
    if not isinstance(cooldown, dict):
        cooldown = {}
        session.monster_magic_cooldown_v1151 = cooldown
    if kind in active or len(active) >= 2 or now < float(cooldown.get(kind, 0)):
        return ""
    if now < float(getattr(session, "monster_magic_global_cooldown_v1151", 0)):
        return ""
    ward = max(0.0, min(.80, float(ward or 0.0)))
    if float(roll) >= 0.28 * (1.0 - ward):
        return ""
    active[kind] = {
        "name": label, "expires": now + duration, "next_tick": now + 3.0,
        "ticks_left": ticks, "strength": strength, "skip_left": 1,
    }
    # The same debuff cannot be refreshed for at least twelve seconds after it ends.
    cooldown[kind] = now + duration + 12.0
    session.monster_magic_global_cooldown_v1151 = now + 6.0
    return f"{label}: {int(duration)} sekund. Efekt nie kumuluje się ani nie odnawia przed wygaśnięciem."


def monster_magic_tick_v1151(session, now=None):
    """Run only in active combat on the owner's action; never finish a player with DOT."""
    now = time.monotonic() if now is None else float(now)
    active = getattr(session, "monster_magic_effects_v1151", None)
    if not isinstance(active, dict) or not active:
        return []
    messages = []
    for kind, effect in tuple(active.items()):
        if now >= float(effect.get("expires", 0)):
            del active[kind]
            messages.append(f"{effect.get('name', kind)} wygasa.")
            continue
        ticks = int(effect.get("ticks_left", 0))
        if ticks <= 0 or now < float(effect.get("next_tick", 0)):
            continue
        effect["next_tick"] = now + 3.0  # one tick per owner action, no catch-up bursts
        effect["ticks_left"] = ticks - 1
        amount = 0
        if kind in {"burn", "poison"}:
            amount = min(max(0, int(session.current_hp) - 1), max(1, int(session.max_hp() * float(effect["strength"]))))
            session.current_hp -= amount
            if amount:
                session._recap52_taken = int(getattr(session, "_recap52_taken", 0) or 0) + amount
            messages.append(f"{effect['name']}: {amount} obrażeń okresowych; pozostało {ticks - 1} impulsów.")
        elif kind == "mana_drain":
            amount = min(max(0, int(session.current_mana)), max(1, int(session.max_mana() * float(effect["strength"]))))
            session.current_mana -= amount
            messages.append(f"{effect['name']}: tracisz {amount} Many; pozostało {ticks - 1} impulsów.")
    return messages


def monster_magic_player_action_v1151(session, now=None):
    """At most one skipped *automatic* attack per status application."""
    now = time.monotonic() if now is None else float(now)
    active = getattr(session, "monster_magic_effects_v1151", {}) or {}
    for kind in ("shock", "blind"):
        effect = active.get(kind)
        if effect and float(effect.get("expires", 0)) > now and int(effect.get("skip_left", 0)) > 0:
            effect["skip_left"] = 0
            return effect.get("name", kind)
    return ""


def monster_magic_action_interval_v1151(session, interval, now=None):
    return float(interval) * (1.2 if monster_magic_active_v1151(session, "chill", now) else 1.0)


def monster_magic_incoming_multiplier_v1151(session, now=None):
    return 1.10 if monster_magic_active_v1151(session, "curse", now) else 1.0


def monster_magic_clear_v1151(session):
    session.monster_magic_effects_v1151 = {}
    session.monster_magic_cooldown_v1151 = {}
    session.monster_magic_global_cooldown_v1151 = 0.0


def monster_magic_audit_v1151():
    class Session:
        current_hp = 1000
        current_mana = 500
        def max_hp(self): return 1000
        def max_mana(self): return 500
    s = Session()
    errors = []
    if len(SPELL_NAMES) != 10 or len(MONSTER_MAGIC_EFFECTS) != 10:
        errors.append("incomplete elemental spell coverage")
    for element in MONSTER_MAGIC_EFFECTS:
        if not monster_spell_name_v1151(element, 99):
            errors.append(f"missing spell for {element}")
    if not monster_magic_apply_v1151(s, "fire", 0, now=100):
        errors.append("burn not applied")
    if monster_magic_apply_v1151(s, "fire", 0, now=101):
        errors.append("burn incorrectly refreshed")
    monster_magic_tick_v1151(s, now=103)
    if s.current_hp >= 1000:
        errors.append("burn does not tick")
    monster_magic_tick_v1151(s, now=109)
    if monster_magic_active_v1151(s, "burn", 109):
        errors.append("burn duration not capped")
    if monster_magic_apply_v1151(s, "fire", 0, now=110):
        errors.append("burn bypassed cooldown")
    if not monster_magic_apply_v1151(s, "lightning", 0, now=122):
        errors.append("shock not applied")
    if not monster_magic_player_action_v1151(s, now=123) or monster_magic_player_action_v1151(s, now=124):
        errors.append("shock skip not limited to one action")
    monster_magic_clear_v1151(s)
    if getattr(s, "monster_magic_effects_v1151", None):
        errors.append("cleanup failed")
    return {"checks": 18, "errors": errors, "error_count": len(errors)}
