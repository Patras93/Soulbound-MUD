"""Fast deterministic regression tests for core progression, saves and UOSS helpers.

Tests use disposable state only; never touch SOULBOUND_DB or production volumes.
"""
from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace

from core.progression_resources import character_xp_to_next, class_mastery_xp_to_next, soul_xp_to_next
from storage.database import Database


def audit_release_stability_v1147():
    errors = []
    checks = 0

    def verify(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    # Current 100 is still the old milestone; the next requirements are heavier.
    for label, requirement in (
        ("character", character_xp_to_next),
        ("class", class_mastery_xp_to_next),
        ("soul", soul_xp_to_next),
    ):
        verify(requirement(101) > requirement(100) > 0, f"{label}: XP curve must rise immediately after 100")
        verify(requirement(200) > requirement(150), f"{label}: endgame XP requirement must keep rising")

    return {"version": "1.14.7", "checks": checks, "error_count": len(errors), "errors": errors}


def audit_release_stability_runtime_v1147(ns):
    """Exercise native-runtime Character and helper implementations in a disposable model."""
    errors = []
    checks = 0
    def verify(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)
    Character = ns["Character"]
    from world.uoss_superboss_runtime import (
        superboss_helper_action_v1146, superboss_helper_release_v1146,
    )
    # Legacy callers may still send single_level_cap=True; actual progression
    # must grant *all* purchased levels and preserve the unspent XP remainder.
    c = object.__new__(Character)
    c.character_level = 100
    c.character_xp = 0
    leftover = 137
    getattr(c, "add_character_xp")(character_xp_to_next(100) + character_xp_to_next(101) + leftover, single_level_cap=True)
    verify((c.character_level, c.character_xp) == (102, leftover), "character XP was lost / incorrectly capped")

    # Uncapped independent statistic; current gain must not stop after one point.
    for stat in Character.STAT_PROGRESS_FIELDS:
        _label, value_field, progress_field = Character.STAT_PROGRESS_FIELDS[stat]
        setattr(c, value_field, 100)
        setattr(c, progress_field, 0)
    c.stat_progress = 0
    c.race = "Człowiek"
    c.racial_stat_progress_multiplier = lambda: 1.0
    c._guild_bonus_percent = 0
    initial = c.strength
    getattr(c, "add_stat_progress")(
        c.stat_growth_threshold_for("strength") + c.stat_growth_threshold_for("strength") * 4,
        targets=["strength"], single_level_cap=True,
    )
    verify(c.strength >= initial + 2, "strength XP still limited to one stat increase")
    verify(c.stat_growth_threshold_for("strength") > 0, "stat XP to next not available")

    # Actual SQL persistence across two independent Database instances.
    with tempfile.TemporaryDirectory(prefix="soulbound-stability-v1147-") as directory:
        path = os.path.join(directory, "regression.db")
        db = Database(path)
        try:
            account = db.create_account("stability_test_1147", "disposable-test-only")
            db.ensure_class_progress(account, "Mec")
            db.conn.execute(
                "UPDATE class_progress SET level=100,xp=0 WHERE account_id=? AND class_name='Mec'",
                (account,),
            )
            db.conn.commit()
            gain = class_mastery_xp_to_next(100) + class_mastery_xp_to_next(101) + 223
            result = getattr(db, "add_class_mastery_xp")(account, "Mec", gain, single_level_cap=True)
            verify((result["level"], result["xp"]) == (102, 223), "class XP was lost / capped")
            verify(result["level_ups"] == 2, "class progress level_up counter incorrect")
            verify(db.conn.execute("PRAGMA foreign_key_check").fetchone() is None, "SQL FK integrity failed")
        finally:
            db.conn._connection.close()
        reopened = Database(path)
        try:
            saved = reopened.class_progress_row(account, "Mec")
            verify((int(saved["level"]), int(saved["xp"])) == (102, 223), "class progress not saved after restart")
            verify(reopened.conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "SQLite integrity check failed")
        finally:
            reopened.conn._connection.close()


    # Real helper decision path: one helper action per boss turn for whole group,
    # and hiring slot is released after completed encounter.
    class HelperServer:
        def __init__(self):
            self.world = SimpleNamespace(mobs={})
            self._uoss_helper_choice_1 = "Popoi"
            self._uoss_helper_used_1 = False
            self.members = []
        def party_sessions(self, account_id, same_room=None):
            return self.members

    server = HelperServer()
    session = SimpleNamespace(
        account_id=1, server=server, character=SimpleNamespace(room_id="boss_arena"),
        current_hp=1000, current_mana=50, closed=False, combat_mob_key=None,
        max_hp=lambda: 1000, max_mana=lambda: 1000,
        party_key=lambda: None,
    )
    server.members = [session]
    mob = SimpleNamespace(alive=True, hp=100_000, combat_turn=2, room_id="boss_arena")
    template = {"uoss_unique_superboss_key": "black_rabite"}
    action = superboss_helper_action_v1146(session, template, mob)
    verify(bool(action) and action["ability"] == "Faerie Walnut", "Popoi does not restore mana at low MP")
    verify(superboss_helper_action_v1146(session, template, mob) is None, "helper executes twice in one boss turn")
    mob.combat_turn = 3
    session.current_mana = 1000
    action2 = superboss_helper_action_v1146(session, template, mob)
    verify(bool(action2) and action2["ability"] != "Faerie Walnut", "helper does not switch to offense")
    verify(superboss_helper_release_v1146(session), "used helper could not be released")
    verify(not hasattr(server, "_uoss_helper_choice_1"), "paid helper slot still locked after fight")

    return {"version": "1.14.7", "checks": checks, "error_count": len(errors), "errors": errors}


if __name__ == "__main__":
    outcome = audit_release_stability_v1147()
    print(f"RELEASE STABILITY SMOKE: {outcome['checks']} checks, {outcome['error_count']} errors")
    for e in outcome["errors"]:
        print("ERROR:", e)
    raise SystemExit(1 if outcome["errors"] else 0)
