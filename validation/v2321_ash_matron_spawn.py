# -*- coding: utf-8 -*-
"""Regression of the missing Matka Popiolu in her named lair (v2.32.1)."""
from __future__ import annotations
import time
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_regression(runtime=None):
    from data.catalogs import ROOMS, MOB_TEMPLATES
    from systems.content_registry import MOB_SPAWNS
    from world.dragon_world import DRAGON_WORLD_SPAWNS
    from world.dynamic_content import mob_template_can_wander
    from world.world_state import World

    expected_room = "dragon_ashen_08"
    matron = "dragon_ash_matron"
    checks = 0
    assert ROOMS[expected_room]["name"] == "Legowisko Matki Popiołu"
    checks += 1
    assert [rid for rid, mid in DRAGON_WORLD_SPAWNS if mid == matron] == [expected_room]
    checks += 1
    assert [rid for rid, mid in MOB_SPAWNS if mid == matron] == [expected_room]
    checks += 1
    assert (expected_room, matron) in MOB_SPAWNS
    checks += 1
    assert ("dragon_ashen_07", matron) not in MOB_SPAWNS
    checks += 1
    template = MOB_TEMPLATES[matron]
    assert template.get("mini_boss") and template.get("boss")
    checks += 1
    assert int(template.get("respawn_seconds", 0)) == 12 * 60
    checks += 1
    assert not mob_template_can_wander(template)
    checks += 1
    assert ("dragon_canyon_07", "dragon_canyon_champion") in MOB_SPAWNS
    checks += 1
    # Isolate the genuine constructor to the boss spawn. Building all ~20k
    # unrelated world mobs here would make FAST/FULL unnecessarily slow.
    from unittest.mock import patch
    with patch("world.world_state.MOB_SPAWNS", [(expected_room, matron)]):
        world = World()  # Genuine MobState spawn loop, no live network or SQLite.
    found = [mob for mob in world.mobs.values()
             if mob.home_room_id == expected_room and (
                 mob.template_id == matron or
                 MOB_TEMPLATES.get(mob.template_id, {}).get("base_template") == matron
             )]
    assert len(found) == 1, f"Expected live Matka Popiolu in {expected_room}, got {len(found)}"
    checks += 1
    boss = found[0]
    assert boss.alive and boss.room_id == expected_room and boss.hp > 0
    checks += 1
    boss.alive = False
    boss.hp = 0
    boss.respawn_at = time.time() - 1
    world.refresh(force=True)
    assert boss.alive and boss.room_id == expected_room and boss.hp > 0
    checks += 1
    assert not [mob for mob in world.mobs.values()
                if mob.home_room_id == "dragon_ashen_07" and (
                     mob.template_id == matron or
                     MOB_TEMPLATES.get(mob.template_id, {}).get("base_template") == matron
                 )]
    checks += 1
    return checks


def run_static_source_regression():
    """Execute authored zone loop against a tiny stand-in spawn registrar.

    Does not load the server, does not connect to any database, and cannot
    falsely claim that a live game client saw the boss.
    """
    import ast
    from pathlib import Path
    tree = ast.parse((ROOT / "world" / "dragon_world.py").read_text(encoding="utf-8"))
    zone_def = next(n for n in tree.body
                    if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "ZONE_SPECS" for t in n.targets))
    zone_loop = next(n for n in tree.body
                     if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple)
                     and isinstance(n.target.elts[0], ast.Name)
                     and n.target.elts[0].id == "key")
    rows = []
    def grid(key, zone, stage, names, desc):
        return tuple(f"dragon_{key}_{i:02d}" for i in range(1, len(names)+1))
    def spawn(room_id, mob_id, count=1):
        rows.extend([(room_id, mob_id)]*count)
    scope = {"_grid": grid, "_dragon_link": lambda *a, **kw: None,
             "_dragon_mob": lambda mob_id, *a, **kw: mob_id,
             "_dragon_spawn": spawn,
             "_first_free_direction": lambda *a, **kw: "up",
             "observatory": "observatory", "previous_exit": "observatory", "zone_mob_sets": {}, "zone_lords": {},
             "min": min, "MAT_SCALE": "dragon_world_scale",
             "MAT_ASH": "dragon_world_ashen_core",
             "MAT_CRYSTAL": "dragon_world_crystal_shard",
             "MAT_INFERNO": "dragon_world_inferno_heart",
             "MAT_STORM": "dragon_world_storm_heart",
             "MAT_BONE": "dragon_world_ancient_bone"}
    exec(compile(ast.Module(body=[zone_def, zone_loop], type_ignores=[]),
                 str(ROOT / "world" / "dragon_world.py"), "exec"), scope)
    actual = [r for r, m in rows if m == "dragon_ash_matron"]
    assert actual == ["dragon_ashen_08"], actual
    assert not [r for r, m in rows if m == "dragon_ash_matron" and r == "dragon_ashen_07"]
    assert ("dragon_canyon_07", "dragon_canyon_champion") in rows
    return 3


if __name__ == "__main__":
    print(f"MATKA POPIOLU v2.32.1: {run_static_source_regression()} source-execution checks PASS")
    print("Real World() spawn and respawn are checked separately inside FAST and FULL.")
