# -*- coding: utf-8 -*-
"""v3.00.6: validate both HELP writers without importing compatibility scripts directly.

admin/help_refresh.py is an injected script in the runtime manifest, not a
standalone importable module. Inspect its actual AST in the fast gate and
inspect the final assembled runtime namespace in the full gate.
"""
import ast
from pathlib import Path

from validation.v4100_virtual_source import read_factored_legacy_source_v410 as _v410_virtual_read
ROOT = Path(__file__).resolve().parents[1]


def _queue_topic_in_function(path, function_name):
    tree = ast.parse(_v410_virtual_read(ROOT / path))
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name == function_name)
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.List):
            continue
        if not node.targets or not isinstance(node.targets[0], ast.Subscript):
            continue
        target = node.targets[0]
        if isinstance(target.value, ast.Name) and target.value.id == "HELP_TOPICS" \
                and isinstance(target.slice, ast.Constant) and target.slice.value == "kolejka":
            return ast.literal_eval(node.value)
    raise AssertionError(f"Missing HELP kolejka in {path} / {function_name}")


def run_regression(runtime=None):
    checks = 0
    def check(value, message):
        nonlocal checks
        if not value:
            raise AssertionError("QUEUE HELP v3.00.6: " + message)
        checks += 1

    def check_queue(name, topic):
        text = " ".join(topic if isinstance(topic, (list, tuple)) else [topic]).casefold()
        check("bez limitu" in text or "nie mają limitu" in text,
              f"{name}: missing unlimited-queue description")
        for phrase in ("automatycznie", "kolejka", "nauczyciel"):
            check(phrase in text, f"{name}: missing {phrase}")
        for stale in ("20 aktywnych slotów", "80 na levelu 600", "120 na levelu 800",
                      "co 10 leveli dochodzi", "40 na levelu 1"):
            check(stale not in text, f"{name}: stale {stale}")
        check("off" in text, f"{name}: manual off missing")
        check("25" in text, f"{name}: NVDA pagination missing")

    check_queue("historical override", _queue_topic_in_function(
        "admin/help_refresh.py", "refresh_help_truth_v11197"))
    check_queue("current layer", _queue_topic_in_function(
        "admin/help_truth_current.py", "refresh_help_truth_current_v11328"))

    # Ensure the legacy audit no longer demands obsolete 600 in queue help,
    # while it still explicitly blocks an absent unlimited-queue description.
    source = _v410_virtual_read(ROOT / "admin/help_refresh.py")
    tree = ast.parse(source)
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name == "help_truth_audit_v11197")
    canonical = next(node for node in ast.walk(fn)
                     if isinstance(node, ast.Assign) and any(
                         isinstance(x, ast.Name) and x.id == "canonical_600" for x in node.targets))
    check("kolejka" not in ast.literal_eval(canonical.value),
          "legacy 600 requirement still includes queue")
    check("missing unlimited rotation semantics" in ast.get_source_segment(source, fn),
          "historical audit lost its unlimited queue guard")
    check("obsolete level-based slot limits" in ast.get_source_segment(source, fn),
          "historical audit missing obsolete limits guard")
    # Exercise the genuine historical HELP audit functions in isolation using
    # their original code; no server/socket/database is required.
    refresh_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                      and node.name == "refresh_help_truth_v11197")
    isolated = {"HELP_TOPICS": {}, "HELP_TOPIC_ALIASES": {}}
    exec(compile(ast.Module(body=[refresh_fn, fn], type_ignores=[]),
                 "admin/help_refresh.py", "exec"), isolated)
    isolated["refresh_help_truth_v11197"]()
    report = isolated["help_truth_audit_v11197"]()
    check(not report["errors"], f"executed historical audit errors: {report['errors']}")

    if runtime is not None:
        check_queue("running server", runtime["HELP_TOPICS"]["kolejka"])
        report = runtime["HELP_TRUTH_AUDIT_V11197"]
        check(not report["errors"], f"historical audit errors: {report['errors']}")
    return checks


if __name__ == "__main__":
    print(f"QUEUE HELP v3.00.6: {run_regression()} checks PASS")
