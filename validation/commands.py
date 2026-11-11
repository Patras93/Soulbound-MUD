# -*- coding: utf-8 -*-
"""Static command-routing validation for Soulbound v0.49.0."""
from __future__ import annotations

import ast
from pathlib import Path


def validate_command_loop_architecture(root: Path) -> dict:
    root = Path(root)
    path = root / "player/session_mixins/command_loop.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    errors = []

    if "COMMAND_ALIASES" in source:
        errors.append("command_loop accesses legacy COMMAND_ALIASES directly")
    if "resolve_session_command" not in source:
        errors.append("command_loop does not use central resolve_session_command")
    if "dispatch_registered_command" not in source:
        errors.append("command_loop does not dispatch through command registry")

    # Manual command-name branching belongs in focused handlers/registry now.
    manual_command_branches = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        names = set()
        if isinstance(left, ast.Name):
            names.add(left.id)
        for comparator in node.comparators:
            if isinstance(comparator, ast.Name):
                names.add(comparator.id)
        if "command" in names:
            manual_command_branches.append(getattr(node, "lineno", 0))
    if manual_command_branches:
        errors.append(
            "manual command-name branches remain in command_loop.py at lines "
            + ", ".join(map(str, manual_command_branches[:20]))
        )

    return {
        "error_count": len(errors),
        "errors": errors,
        "manual_command_branch_count": len(manual_command_branches),
        "command_loop_lines": len(source.splitlines()),
    }



def validate_command_alias_ownership(root: Path, runtime_modules) -> dict:
    """Reject runtime alias mutations outside the authoritative alias definitions."""
    root = Path(root)
    violations = []
    for rel in runtime_modules:
        path = root / rel
        source = path.read_text(encoding="utf-8")
        if "COMMAND_ALIASES" not in source:
            continue
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                call = node.value
                if (
                    isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == "COMMAND_ALIASES"
                    and call.func.attr in {"update", "setdefault"}
                ):
                    violations.append(f"{rel}:{node.lineno}: COMMAND_ALIASES.{call.func.attr}")
            if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if (
                        isinstance(target, ast.Subscript)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "COMMAND_ALIASES"
                    ):
                        violations.append(f"{rel}:{node.lineno}: COMMAND_ALIASES[...] write")
    return {
        "error_count": len(violations),
        "errors": violations,
        "alias_mutation_count": len(violations),
    }
