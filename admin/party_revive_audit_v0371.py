# -*- coding: utf-8 -*-
"""Soulbound v0.37.1 - Local Party Revive audit/help."""

PARTY_REVIVE_WINDOW_SECONDS_V0371 = 60
PARTY_REVIVE_RESTORE_FRACTION_V0371 = 0.35

HELP_TOPICS["wskrzeszenie"] = [
    "W drużynie śmierć przy żywym członku party stojącym w tej samej lokacji daje 60 sekund stanu POWALONY zamiast natychmiastowego teleportu.",
    "Każdy żywy członek tej samej drużyny w tym pokoju może użyć: wskrzes <gracz> / revive <player>.",
    "Wskrzeszony wraca w tym samym pokoju z 35 procent maksymalnego HP i 35 procent maksymalnej many. Nie wraca automatycznie do walki.",
    "Powalony może wpisać odrodz, aby natychmiast wrócić do Świątyni. Po 60 sekundach bez pomocy następuje automatyczne odrodzenie.",
    "Jeśli w chwili śmierci nie ma obok żywego członka drużyny, działa dawny natychmiastowy respawn w Świątyni.",
]
HELP_TOPICS["druzyny"].append(
    "Wskrzeszanie v0.37.1: wskrzes <gracz> działa na powalonego członka drużyny w tej samej lokacji; okno 60 s, powrót z 35% HP/many."
)
HELP_TOPIC_ALIASES.update({
    "wskrzes":"wskrzeszenie", "wskrzesz":"wskrzeszenie", "wskrześ":"wskrzeszenie",
    "revive":"wskrzeszenie", "odrodz":"wskrzeszenie", "odrodź":"wskrzeszenie",
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
        "is_downed_v0371", "party_revive_candidates_v0371", "begin_downed_v0371",
        "respawn_from_downed_v0371", "revive_party_member_v0371",
    ):
        if not hasattr(Session, method):
            errors.append(f"Session missing {method}")
    die_names=set(getattr(SessionSkillsCombatMixin.die, "__code__").co_names)
    for expected in ("party_revive_candidates_v0371", "begin_downed_v0371"):
        if expected not in die_names:
            errors.append(f"die() does not call {expected}")
    command_names=set(getattr(SessionCommandLoopMixin.command_loop, "__code__").co_names)
    if "is_downed_v0371" not in command_names:
        errors.append("command loop has no downed-state gate")
    if "wskrzeszenie" not in HELP_TOPICS:
        errors.append("missing help wskrzeszenie")
    return {
        "version":"0.37.1",
        "window_seconds":PARTY_REVIVE_WINDOW_SECONDS_V0371,
        "restore_fraction":PARTY_REVIVE_RESTORE_FRACTION_V0371,
        "error_count":len(errors), "errors":errors,
    }

PARTY_REVIVE_AUDIT_V0371=party_revive_audit_v0371()
if PARTY_REVIVE_AUDIT_V0371["error_count"]:
    raise RuntimeError("Party Revive Audit v0.37.1 failed: "+"; ".join(PARTY_REVIVE_AUDIT_V0371["errors"]))
