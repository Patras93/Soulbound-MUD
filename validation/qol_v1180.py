# -*- coding: utf-8 -*-
"""Non-destructive v1.18.0 command behavior checks for each predeploy lane."""
import ast
import asyncio
import sqlite3
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from player.session_mixins.quality_of_life_v1180 import (
    SessionQualityOfLifeV1180Mixin, _treasure_filter_v1180,
)


class _Task:
    def __init__(self, done=False):
        self._done = done
    def done(self):
        return self._done


class _Dummy(SessionQualityOfLifeV1180Mixin):
    def __init__(self, db, account_id=1):
        self.server = SimpleNamespace(db=db)
        self.account_id = account_id
        self.messages = []
        self.smelt_label_v1124 = "wszystko"
        self.smelt_task_v1124 = None
        self.auto_fishing = False
        self.auto_fishing_task = None
        self.auto_mining = False
        self.auto_mining_task = None
        self.auto_woodcutting = False
        self.auto_woodcutting_task = None
        self.auto_herbalism = False
        self.auto_herbalism_task = None
    async def send(self, text, **kw):
        self.messages.append(str(text))


class _Db:
    def __init__(self, conn):
        self.conn = conn
    def skill_queue_enabled(self, account_id):
        return True
    def skill_queue_rows(self, account_id):
        return [{"skill_id":"attack"}]


async def _check_commands(check):
    with tempfile.TemporaryDirectory(prefix="soulbound-qol-") as temp:
        conn = sqlite3.connect(str(Path(temp)/"history.db"))
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE drop_history (id INTEGER PRIMARY KEY, account_id INTEGER, item_name TEXT, rarity TEXT, source TEXT, zone TEXT)")
        rows = (
            (1, "Legendarny Miecz", "legendary", "Odin", "Wieża"),
            (1, "Rzadki Kryształ", "rare", "Krypta", "Podziemia"),
            (1, "Epicka Tarcza", "epic", "Boss", "Loch"),
            (2, "Cudzy Miecz", "legendary", "Boss", "Loch"),
        )
        conn.executemany("INSERT INTO drop_history(account_id,item_name,rarity,source,zone) VALUES(?,?,?,?,?)", rows)
        conn.commit()
        session = _Dummy(_Db(conn))
        await session.show_treasures_v1180("legendarne 30")
        check("Legendarny Miecz" in " ".join(session.messages), "legendary filter")
        check("Rzadki Kryształ" not in " ".join(session.messages), "legendary excludes rare")
        check("Cudzy Miecz" not in " ".join(session.messages), "history isolated by account")
        session.messages.clear()
        await session.show_treasures_v1180("szukaj kryształ")
        check("Rzadki Kryształ" in " ".join(session.messages), "Polish accent item search")
        session.messages.clear()
        await session.show_treasures_v1180("epickie")
        check("Epicka Tarcza" in " ".join(session.messages), "epic rarity filter")
        session.messages.clear()
        await session.show_treasures_v1180("rzadkie")
        check("Rzadki Kryształ" in " ".join(session.messages), "rare rarity filter")
        session.messages.clear()
        await session.show_treasures_v1180("pomoc")
        check("zdobycze szukaj" in " ".join(session.messages).lower(), "treasure command help")
        session.messages.clear()
        session.auto_fishing = True
        session.auto_fishing_task = _Task()
        session.smelt_task_v1124 = _Task()
        session.smelt_wait_until_v1180 = time.monotonic() + 30
        await session.show_tasks_v1180()
        output = " ".join(session.messages)
        check("Przetop: wszystko" in output, "ongoing smelt label")
        check("pozostało około" in output and "s" in output, "smelt ETA")
        check("Wędkarstwo: automatyczne" in output, "auto profession state")
        check("Kolejka skilli: włączona" in output, "persistent skill queue status")
        session.messages.clear()
        session.smelt_task_v1124 = None
        session.auto_fishing = False
        session.auto_fishing_task = None
        await session.show_tasks_v1180()
        check("Brak aktywnej automatycznej pracy" in " ".join(session.messages), "idle work status")
        # Read-only checks: a QoL query must neither add/drop history nor modify rows.
        check(conn.execute("SELECT COUNT(*) FROM drop_history").fetchone()[0] == 4, "query does not write drop history")
        conn.close()


def audit_qol_v1180():
    checks, errors = 0, []
    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(label)
    for spec, expected in (("", (None, 10, "")), ("legendarne 999", ("legendary", 30, "")),
                           ("rzadkie 0", ("rare", 1, "")), ("szukaj kryształ", (None, 10, "kryształ")),
                           ("epickie 5", ("epic", 5, ""))):
        check(_treasure_filter_v1180(spec) == expected, f"parser {spec}")
    from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
    registry_tree = ast.parse((Path(__file__).resolve().parents[1] / "player/session_mixins/command_registry.py").read_text(encoding="utf-8"))
    command_keys = set()
    policy = {}
    for node in registry_tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "COMMAND_REGISTRY" for t in node.targets):
            if isinstance(node.value, ast.Dict):
                command_keys.update(key.value for key in node.value.keys if isinstance(key, ast.Constant))
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("REST_SAFE_COMMANDS", "GUIDE_SAFE_COMMANDS") for t in node.targets):
            if isinstance(node.value, ast.Set):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        policy[target.id] = {elt.value for elt in node.value.elts if isinstance(elt, ast.Constant)}
    for alias, command in (("gdzie", "where"), ("zdobycze", "treasures"), ("prace", "tasks")):
        check(COMMAND_ALIAS_DEFINITIONS.get(alias) == command, f"alias {alias}")
        check(command in command_keys, f"registered {command}")
    check("tasks" in policy.get("GUIDE_SAFE_COMMANDS", set()), "work status during walk")
    check("tasks" in policy.get("REST_SAFE_COMMANDS", set()), "work status during rest")
    root = Path(__file__).resolve().parents[1]
    assembled = (root / "player/session.py").read_text(encoding="utf-8")
    check("SessionQualityOfLifeV1180Mixin," in assembled, "session composition")
    modules = (("player/session_mixins/help_system.py", "gdzie cele"),
               ("player/session_mixins/io_auth_character.py", "combat ostatnie"),
               ("player/session_mixins/crafting_expansion.py", "smelt_wait_until_v1180"),
               ("world/equipment_help.py", 'HELP_TOPICS["zdobycze"]'))
    for filename, snippet in modules:
        text = (root / filename).read_text(encoding="utf-8")
        check(snippet in text, f"implementation {filename}")
        ast.parse(text, filename=filename)
    # Execute the actual command implementations, not just their help strings.
    help_source = ast.parse((root / "player/session_mixins/help_system.py").read_text(encoding="utf-8"))
    help_class = next(n for n in help_source.body if isinstance(n, ast.ClassDef) and n.name == "SessionHelpSystemMixin")
    where_method = next(n for n in help_class.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "show_where")
    where_class = ast.ClassDef(name="WhereUnderTest", bases=[], keywords=[], body=[where_method], decorator_list=[])
    where_module = ast.fix_missing_locations(ast.Module(body=[where_class], type_ignores=[]))
    where_vars = {"ROOMS":{"test_room":{"name":"Rynek", "zone":"Miasto", "exits":{"north":"shop"}}},
                  "normalize_lookup_text":lambda value: str(value).lower().strip()}
    exec(compile(where_module, "where-v1180", "exec"), where_vars)
    class WhereProbe(where_vars["WhereUnderTest"]):
        def __init__(self):
            self.character = SimpleNamespace(room_id="test_room")
            self.messages = []
        async def send(self, value):
            self.messages.append(str(value))
        async def show_exits(self):
            self.messages.append("Wyjścia: północ")
        async def show_current_city_walk_destinations(self):
            self.messages.append("Cele lokalne")
    async def _where_checks():
        probe = WhereProbe()
        await probe.show_where()
        check(any("Rynek" in line for line in probe.messages), "where reports actual location")
        check(any("północ" in line for line in probe.messages), "where shows real exits")
        probe.messages.clear()
        await probe.show_where("cele")
        check("Cele lokalne" in probe.messages, "where delegates city destinations")
        probe.messages.clear()
        await probe.show_where("pomoc")
        check(any("trasa" in line for line in probe.messages), "where help")
    asyncio.run(_where_checks())

    combat_source = ast.parse((root / "player/session_mixins/io_auth_character.py").read_text(encoding="utf-8"))
    combat_class = next(n for n in combat_source.body if isinstance(n, ast.ClassDef) and n.name == "SessionIOAuthCharacterMixin")
    combat_method = next(n for n in combat_class.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "set_combat_log")
    combat_probe = ast.ClassDef(name="CombatUnderTest", bases=[], keywords=[], body=[combat_method], decorator_list=[])
    combat_module = ast.fix_missing_locations(ast.Module(body=[combat_probe], type_ignores=[]))
    combat_vars = {"time":time}
    exec(compile(combat_module, "combat-v1180", "exec"), combat_vars)
    class CombatProbe(combat_vars["CombatUnderTest"]):
        def __init__(self):
            self.account_id = 1
            self.messages = []
            self.last_history = None
            self.server = SimpleNamespace(db=SimpleNamespace(set_combat_log_mode=self._set_mode))
            self.saved_mode = None
        def _set_mode(self, aid, mode):
            self.saved_mode = mode
        def normalize_description_query(self, text):
            return str(text).lower().strip()
        async def send(self, text):
            self.messages.append(str(text))
        async def show_history_buffer(self, args):
            self.last_history = args
    async def _combat_checks():
        probe = CombatProbe()
        await probe.set_combat_log("ostatnie 7")
        check(probe.last_history == "combat 7", "combat history routes to session buffer")
        check(probe.saved_mode is None, "combat history does not change mode")
        await probe.set_combat_log("concise")
        check(probe.saved_mode == "concise", "existing combat mode change preserved")
        await probe.set_combat_log("ostatnie 999")
        check(probe.last_history == "combat 100", "combat history bound")
    asyncio.run(_combat_checks())
    loop_source = (root / "player/session_mixins/command_loop.py").read_text(encoding="utf-8")
    check('if _busy_command == "tasks":' in loop_source, "task status allowed during smelt")
    asyncio.run(_check_commands(check))
    return {"checks":checks, "error_count":len(errors), "errors":errors}


if __name__ == "__main__":
    report = audit_qol_v1180()
    print(report)
    if report["error_count"]:
        raise SystemExit(1)
