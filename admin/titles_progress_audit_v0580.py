# -*- coding: utf-8 -*-
"""Soulbound v0.58.0 - Titles 2.0 and unified progress audit."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _literal_assignment(path: Path, name: str, default=()):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            try:
                return ast.literal_eval(node.value)
            except Exception:
                return default
    return default


def titles_progress_audit_v0580():
    errors = []
    module_path = ROOT / "player/session_mixins/progress_titles.py"
    session_path = ROOT / "player/session.py"
    aliases_path = ROOT / "config/command_aliases.py"
    registry_path = ROOT / "player/session_mixins/command_registry.py"

    if not module_path.is_file():
        return {"version": "0.58.0", "error_count": 1, "errors": ["progress_titles.py missing"]}

    source = module_path.read_text(encoding="utf-8")
    exploration = _literal_assignment(module_path, "EXPLORATION_TITLES_V0580")
    bosses = _literal_assignment(module_path, "BOSS_TITLES_V0580")
    professions = _literal_assignment(module_path, "PROFESSIONS_V0580")
    profession_thresholds = _literal_assignment(module_path, "PROFESSION_TITLE_THRESHOLDS_V0580")

    if tuple(row[0] for row in exploration) != (10, 25, 50, 75, 100):
        errors.append("exploration title thresholds changed")
    if len(bosses) < 6 or not bosses or int(bosses[-1][0]) < 1000:
        errors.append("boss title progression is incomplete")
    if len(professions) != 12:
        errors.append(f"profession title coverage={len(professions)}, expected 12")
    if tuple(row[0] for row in profession_thresholds) != (200, 400, 600):
        errors.append("profession title thresholds changed")
    for token in ("def sync_titles_v0580", "async def show_unified_progress_v0580"):
        if token not in source:
            errors.append(f"missing Titles 2.0 implementation token: {token}")
    for token in ("boss_kills", "courier_guild_state_v0530", "guild_reputation", "clan_membership", "faction_reputations_v016"):
        if token not in source:
            errors.append(f"Titles 2.0 missing durable source: {token}")

    session_source = session_path.read_text(encoding="utf-8")
    if "SessionProgressTitlesV0580Mixin," not in session_source:
        errors.append("Session does not compose SessionProgressTitlesV0580Mixin")
    exploration_source = (ROOT / "player/session_mixins/exploration_progress.py").read_text(encoding="utf-8")
    if "await self.show_unified_progress_v0580()" not in exploration_source:
        errors.append("legacy progress command does not delegate to unified v0.58.0 summary")
    if "await self.sync_titles_v0580(announce=True)" not in exploration_source:
        errors.append("titles command does not synchronize Titles 2.0")

    aliases = aliases_path.read_text(encoding="utf-8")
    if "'postep': 'progress'" not in aliases or "'postęp': 'progress'" not in aliases:
        errors.append("postep/postęp aliases do not route to progress")
    registry = registry_path.read_text(encoding="utf-8")
    if "'progress': ('show_progress'" not in registry:
        errors.append("progress command is not routed to show_progress")

    io_source = (ROOT / "player/session_mixins/io_auth_character.py").read_text(encoding="utf-8")
    if "await self.sync_titles_v0580(announce=True)" not in io_source:
        errors.append("Titles 2.0 is not synchronized on world entry")

    return {
        "version": "0.58.0",
        "exploration_title_count": len(exploration),
        "boss_title_count": len(bosses),
        "profession_count": len(professions),
        "profession_threshold_count": len(profession_thresholds),
        "error_count": len(errors),
        "errors": errors,
    }


TITLES_PROGRESS_AUDIT_V0580 = titles_progress_audit_v0580()

__all__ = ["titles_progress_audit_v0580", "TITLES_PROGRESS_AUDIT_V0580"]
