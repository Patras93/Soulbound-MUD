# -*- coding: utf-8 -*-
"""Soulbound v1.13.43 - World Death Rescue audit/help."""

PARTY_REVIVE_WINDOW_SECONDS_V0371 = 180
PARTY_REVIVE_RESTORE_FRACTION_V0371 = 0.35

HELP_TOPICS["wskrzeszenie"] = [
    "Po śmierci bez Phoenix Egg gracz zostaje POWALONY przez 180 sekund zamiast natychmiastowego teleportu.",
    "Świat dostaje komunikat z nazwą gracza, lokacją, zabójcą/przyczyną oraz dokładnym death recapem.",
    "Każdy żywy gracz, nie tylko członek party, może dotrzeć do tej samej lokacji i użyć: wskrzes <gracz> / revive <player>.",
    "Wskrzeszony wraca w tym samym pokoju z 35 procent maksymalnego HP i 35 procent maksymalnej many. Nie wraca automatycznie do walki.",
    "Ratownik stojący przy ciele może też użyć: resp <gracz>, aby odesłać duszę do Świątyni Odrodzenia z pełnym HP i maną.",
    "Powalony może wpisać odrodz, aby natychmiast samemu wrócić do Świątyni. Po 180 sekundach bez pomocy następuje automatyczne odrodzenie.",
]
HELP_TOPICS["druzyny"].append(
    "Wskrzeszanie v1.13.43 jest światowe: każdy żywy gracz w tej samej lokacji może użyć wskrzes <gracz>; okno ratunku 180 s."
)
HELP_TOPIC_ALIASES.update({
    "wskrzes":"wskrzeszenie", "wskrzesz":"wskrzeszenie", "wskrześ":"wskrzeszenie",
    "revive":"wskrzeszenie", "odrodz":"wskrzeszenie", "odrodź":"wskrzeszenie",
    "resp":"wskrzeszenie", "respi":"wskrzeszenie", "respawn":"wskrzeszenie",
})

def party_revive_audit_v0371():
    errors=[]
    required_aliases={
        "wskrzes":"partyrevive", "wskrzesz":"partyrevive", "revive":"partyrevive",
        "odrodz":"selfrespawn",
    }
    for alias,target in required_aliases.items():
        if COMMAND_ALIASES.get(alias) != target:
            errors.append(f"alias {alias!r} -> {COMMAND_ALIASES.get(alias)!r}, expected {target!r}")
    for method in (
        "is_downed_v0371", "begin_downed_v0371",
        "respawn_from_downed_v0371", "revive_party_member_v0371",
        "respawn_downed_player_v11343",
    ):
        if not hasattr(Session, method):
            errors.append(f"Session missing {method}")
    die_names=set(getattr(SessionSkillsCombatMixin.die, "__code__").co_names)
    for expected in ("begin_downed_v0371", "broadcast_all"):
        if expected not in die_names:
            errors.append(f"die() does not call {expected}")
    command_names=set(getattr(SessionCommandLoopMixin.command_loop, "__code__").co_names)
    if "is_downed_v0371" not in command_names:
        errors.append("command loop has no downed-state gate")
    if "wskrzeszenie" not in HELP_TOPICS:
        errors.append("missing help wskrzeszenie")
    return {
        "version":"1.13.43",
        "window_seconds":PARTY_REVIVE_WINDOW_SECONDS_V0371,
        "restore_fraction":PARTY_REVIVE_RESTORE_FRACTION_V0371,
        "world_rescue":True,
        "error_count":len(errors), "errors":errors,
    }

PARTY_REVIVE_AUDIT_V0371=party_revive_audit_v0371()
if PARTY_REVIVE_AUDIT_V0371["error_count"]:
    raise RuntimeError("Party Revive Audit v1.13.43 failed: "+"; ".join(PARTY_REVIVE_AUDIT_V0371["errors"]))
