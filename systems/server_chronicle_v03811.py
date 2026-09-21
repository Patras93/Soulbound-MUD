# -*- coding: utf-8 -*-
"""Soulbound v0.38.11 — Procedural Legends & Persistent Server Chronicle.

The chronicle stores exceptional server-wide events in SQLite without changing
combat, loot, professions or progression balance.  Ordinary first kills are
remembered as low-importance history; the default `kronika` view focuses on
notable legends while category views can show the complete history.
"""

V03811_SERVER_CHRONICLE_VERSION = "0.38.11"


# ---------------------------------------------------------------------------
# Persistent storage
# ---------------------------------------------------------------------------
_V03811_DB_INIT_BEFORE = Database.__init__


def _v03811_db_init(self, path):
    _V03811_DB_INIT_BEFORE(self, path)
    self.conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS server_legend_keys_v03811 (
            legend_key TEXT PRIMARY KEY,
            claimed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS server_chronicle_v03811 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_key TEXT UNIQUE,
            account_id INTEGER NOT NULL DEFAULT 0,
            actor_name TEXT NOT NULL DEFAULT '',
            subject_id TEXT NOT NULL DEFAULT '',
            subject_name TEXT NOT NULL DEFAULT '',
            detail TEXT NOT NULL,
            importance INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_server_chronicle_v03811_created
            ON server_chronicle_v03811(id DESC);
        CREATE INDEX IF NOT EXISTS idx_server_chronicle_v03811_type
            ON server_chronicle_v03811(event_type, id DESC);
        CREATE INDEX IF NOT EXISTS idx_server_chronicle_v03811_importance
            ON server_chronicle_v03811(importance, id DESC);
        """
    )
    self.conn.execute(
        """
        INSERT OR IGNORE INTO server_chronicle_v03811(
            event_type,event_key,actor_name,detail,importance
        ) VALUES('system','system:v03811','Soulbound',?,2)
        """,
        (
            "Kronika serwera została uruchomiona w v0.38.11. "
            "Od tej chwili zapisuje proceduralne legendy i wyjątkowe wydarzenia; "
            "starsze zdarzenia nie są sztucznie odtwarzane.",
        ),
    )
    self.conn.commit()


Database.__init__ = _v03811_db_init


def _db_v03811_claim_legend_key(self, legend_key):
    key = str(legend_key or "").strip()
    if not key:
        return False
    cur = self.conn.execute(
        "INSERT OR IGNORE INTO server_legend_keys_v03811(legend_key) VALUES(?)",
        (key,),
    )
    self.conn.commit()
    return int(cur.rowcount or 0) > 0


Database.claim_server_legend_key_v03811 = _db_v03811_claim_legend_key


def _db_v03811_add_event(
    self, event_type, detail, *, account_id=0, actor_name="", subject_id="",
    subject_name="", importance=1, event_key=None,
):
    event_type = str(event_type or "system").strip()[:64]
    detail = " ".join(str(detail or "").split())[:1000]
    if not detail:
        return False
    event_key = str(event_key).strip()[:255] if event_key else None
    params = (
        event_type,
        event_key,
        int(account_id or 0),
        str(actor_name or "")[:120],
        str(subject_id or "")[:255],
        str(subject_name or "")[:255],
        detail,
        max(1, min(5, int(importance or 1))),
    )
    cur = self.conn.execute(
        """
        INSERT OR IGNORE INTO server_chronicle_v03811(
            event_type,event_key,account_id,actor_name,subject_id,subject_name,
            detail,importance
        ) VALUES(?,?,?,?,?,?,?,?)
        """,
        params,
    )
    self.conn.commit()
    return int(cur.rowcount or 0) > 0


Database.add_server_chronicle_event_v03811 = _db_v03811_add_event


def _db_v03811_rows(self, limit=25, event_types=None, min_importance=1):
    limit = max(1, min(100, int(limit or 25)))
    min_importance = max(1, min(5, int(min_importance or 1)))
    params = []
    where = ["importance>=?"]
    params.append(min_importance)
    types = [str(x) for x in (event_types or ()) if str(x)]
    if types:
        where.append("event_type IN (" + ",".join("?" for _ in types) + ")")
        params.extend(types)
    params.append(limit)
    return self.conn.execute(
        "SELECT * FROM server_chronicle_v03811 WHERE "
        + " AND ".join(where)
        + " ORDER BY id DESC LIMIT ?",
        tuple(params),
    ).fetchall()


Database.server_chronicle_rows_v03811 = _db_v03811_rows


def _v03811_world_boss(template):
    return bool(
        template.get("world_boss")
        or template.get("v016_world_boss")
        or template.get("v020_mythic_world_boss")
    )


def _v03811_kill_importance(template):
    if _v03811_world_boss(template) or template.get("uoss_superboss"):
        return 4
    if v0866_is_boss_template(template):
        return 3
    if (
        v0866_is_random_variant_template(template)
        or template.get("v016_legendary_rare")
        or template.get("elite")
        or str(template.get("rank") or "").casefold() in ("elite", "rare")
    ):
        return 2
    return 1


def _v03811_actor_phrase(actor_name, participants):
    names = [str(x).strip() for x in (participants or ()) if str(x).strip()]
    # Stable de-duplication, preserving party order supplied by combat.
    unique = []
    seen = set()
    for name in names:
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            unique.append(name)
    if len(unique) > 1:
        return "Drużyna [" + ", ".join(unique) + "]", True
    return str(actor_name or (unique[0] if unique else "Nieznany")), False


def _db_v03811_record_kill(self, account_id, actor_name, template_id, participants=()):
    template_id = str(template_id or "")
    template = MOB_TEMPLATES.get(template_id, {})
    canonical_id = canonical_bestiary_template_id(template_id)
    canonical = MOB_TEMPLATES.get(canonical_id, template)
    actual_name = str(template.get("name") or canonical.get("name") or template_id)
    actor_phrase, grouped = _v03811_actor_phrase(actor_name, participants)
    first = self.claim_server_legend_key_v03811("first_kill:" + str(canonical_id))
    importance = _v03811_kill_importance(template)

    if _v03811_world_boss(template):
        if first:
            detail = (
                f"{actor_phrase} {'jako pierwsza na serwerze pokonała' if grouped else 'jako pierwszy na serwerze pokonał'} "
                f"world bossa {actual_name}."
            )
        else:
            detail = f"{actor_phrase} {'pokonała' if grouped else 'pokonał'} world bossa {actual_name}."
        self.add_server_chronicle_event_v03811(
            "world_boss", detail,
            account_id=account_id, actor_name=actor_name,
            subject_id=canonical_id, subject_name=actual_name,
            importance=4,
        )
        return {"first": first, "world_boss": True, "recorded": True}

    if not first:
        return {"first": False, "world_boss": False, "recorded": False}

    detail = (
        f"{actor_phrase} {'jako pierwsza na serwerze pokonała' if grouped else 'jako pierwszy na serwerze pokonał'} "
        f"{actual_name}."
    )
    recorded = self.add_server_chronicle_event_v03811(
        "first_kill", detail,
        account_id=account_id, actor_name=actor_name,
        subject_id=canonical_id, subject_name=actual_name,
        importance=importance,
        event_key="chronicle:first_kill:" + str(canonical_id),
    )
    return {"first": True, "world_boss": False, "recorded": bool(recorded)}


Database.record_server_kill_v03811 = _db_v03811_record_kill


def _db_v03811_record_fish(
    self, account_id, holder_name, species_id, item_id, length_mm, weight_g,
    record_flags, had_global_record=True,
):
    flags = dict(record_flags or {})
    if not any((
        flags.get("new_global_length"),
        flags.get("new_global_weight"),
        flags.get("new_global_rarest"),
    )):
        return False
    species_id = base_fish_species_id(species_id)
    fish_name = player_item_display_name_v0335(species_id)
    parts = []
    if flags.get("new_global_length"):
        parts.append("długość " + format_fish_length(length_mm))
    if flags.get("new_global_weight"):
        parts.append("masa " + format_fish_weight(weight_g))
    if flags.get("new_global_rarest"):
        parts.append("najrzadszy okaz serwera")
    baseline = not bool(had_global_record) and not flags.get("new_global_rarest")
    importance = 1 if baseline else (3 if flags.get("new_global_rarest") else 2)
    detail = (
        f"{holder_name} ustanowił rekord połowu: {fish_name}; "
        + ", ".join(parts) + "."
    )
    return self.add_server_chronicle_event_v03811(
        "fish_record", detail,
        account_id=account_id, actor_name=holder_name,
        subject_id=species_id, subject_name=fish_name,
        importance=importance,
    )


Database.record_server_fish_record_v03811 = _db_v03811_record_fish


def _db_v03811_record_project(self, account_id, actor_name, project_id):
    project_id = str(project_id or "")
    spec = V022_WORLD_PROJECTS.get(project_id, {})
    project_name = str(spec.get("name") or project_id)
    return self.add_server_chronicle_event_v03811(
        "world_project",
        f"{actor_name} domknął wspólny projekt świata: {project_name}. Projekt został ukończony przez społeczność serwera.",
        account_id=account_id, actor_name=actor_name,
        subject_id=project_id, subject_name=project_name,
        importance=4,
        event_key="chronicle:world_project:" + project_id,
    )


Database.record_server_project_v03811 = _db_v03811_record_project


def _db_v03811_record_exceptional_drop(
    self, account_id, actor_name, item_id, item_name, rarity, source="", zone="",
):
    rank = loot_rarity_rank(item_id)
    if rank < 3:
        return False
    source_text = str(source or "").strip()
    zone_text = str(zone or "").strip()
    where = ""
    if source_text:
        where += f" z: {source_text}"
    if zone_text:
        where += f"; strefa: {zone_text}"
    detail = f"{actor_name} zdobył wyjątkowy drop: {item_name} ({rarity}){where}."
    return self.add_server_chronicle_event_v03811(
        "exceptional_drop", detail,
        account_id=account_id, actor_name=actor_name,
        subject_id=item_id, subject_name=item_name,
        importance=4 if rank >= 4 else 3,
    )


Database.record_server_exceptional_drop_v03811 = _db_v03811_record_exceptional_drop


# ---------------------------------------------------------------------------
# Player command: kronika / chronicle
# ---------------------------------------------------------------------------
V03811_CHRONICLE_FILTERS = {
    "zabicia": ("first_kill",),
    "zabicie": ("first_kill",),
    "kills": ("first_kill",),
    "firstkills": ("first_kill",),
    "bossy": ("world_boss",),
    "worldbossy": ("world_boss",),
    "worldbosses": ("world_boss",),
    "ryby": ("fish_record",),
    "fish": ("fish_record",),
    "rekordy": ("fish_record",),
    "projekty": ("world_project",),
    "projects": ("world_project",),
    "dropy": ("exceptional_drop",),
    "drops": ("exceptional_drop",),
    "legendy": ("first_kill", "world_boss", "fish_record", "world_project", "exceptional_drop"),
    "legends": ("first_kill", "world_boss", "fish_record", "world_project", "exceptional_drop"),
}

V03811_CHRONICLE_LABELS = {
    "first_kill": "PIERWSZE ZABICIE",
    "world_boss": "WORLD BOSS",
    "fish_record": "REKORD POŁOWU",
    "world_project": "PROJEKT ŚWIATA",
    "exceptional_drop": "WYJĄTKOWY DROP",
    "system": "SYSTEM",
}


async def _v03811_show_chronicle(self, args=""):
    raw = normalize_lookup_text(args)
    parts = raw.split() if raw else []
    limit = 25
    filter_types = None
    min_importance = 2  # default view = exceptional legends, not every ordinary first kill

    if parts and parts[-1].isdigit():
        limit = max(1, min(100, int(parts[-1])))
        parts = parts[:-1]
    category = " ".join(parts).strip()
    if category in ("all", "wszystko", "pelna", "pełna"):
        min_importance = 1
    elif category:
        filter_types = V03811_CHRONICLE_FILTERS.get(category)
        if not filter_types:
            await self.send(
                "Kronika: nieznana kategoria. Użyj: kronika, kronika zabicia, "
                "kronika bossy, kronika ryby, kronika projekty, kronika dropy, kronika wszystko."
            )
            return
        min_importance = 1

    rows = self.server.db.server_chronicle_rows_v03811(
        limit=limit, event_types=filter_types, min_importance=min_importance
    )
    await self.send("KRONIKA SERWERA — PROCEDURALNE LEGENDY")
    if not rows:
        await self.send("Brak zapisanych wydarzeń w tej kategorii.")
        return
    for index, row in enumerate(rows, 1):
        label = V03811_CHRONICLE_LABELS.get(str(row["event_type"]), str(row["event_type"]).upper())
        await self.send(
            f"{index}. {label}. {row['detail']} Data: {row['created_at']} UTC."
        )
    if filter_types is None and min_importance >= 2:
        await self.send(
            "Domyślnie pokazuję wyjątkowe wydarzenia. `kronika wszystko` pokazuje także zwykłe pierwsze zabicia."
        )


Session.show_server_chronicle_v03811 = _v03811_show_chronicle

COMMAND_ALIASES.update({
    "kronika": "chronicle",
    "chronicle": "chronicle",
    "kronikaserwera": "chronicle",
    "serverchronicle": "chronicle",
})

HELP_TOPICS["kronika"] = [
    "kronika / chronicle pokazuje trwałą Kronikę Serwera i Proceduralne Legendy zapisane w SQLite.",
    "Kronika pamięta pierwsze zabicia, każde pokonanie world bossa, globalne rekordy połowów, ukończenie Projektu Świata oraz wyjątkowe dropy Legendary/Unique/Mythic.",
    "Zwykłe pierwsze zabicia są zapisywane, ale nie zaśmiecają widoku domyślnego. `kronika wszystko` pokazuje pełną historię.",
    "Filtry: kronika zabicia, kronika bossy, kronika ryby, kronika projekty, kronika dropy. Na końcu można podać 1-100, np. `kronika bossy 50`.",
    "Kronika zaczyna pełny zapis zdarzeń od v0.38.11; nie zgaduje wydarzeń, których starsze wersje nie zapisały wiarygodnie.",
]
HELP_TOPIC_ALIASES.update({
    "chronicle": "kronika",
    "kronikaserwera": "kronika",
    "serverchronicle": "kronika",
    "proceduralnelegendy": "kronika",
})

_V03811_HELP_COMMANDS_BEFORE = SessionHelpCodexProfileMixin.help_commands


def _v03811_help_commands(self):
    lines = list(_V03811_HELP_COMMANDS_BEFORE(self))
    lines.append(
        "kronika / chronicle [zabicia|bossy|ryby|projekty|dropy|wszystko] [1-100] - trwałe Proceduralne Legendy i historia wyjątkowych zdarzeń całego serwera"
    )
    return lines


SessionHelpCodexProfileMixin.help_commands = _v03811_help_commands


# ---------------------------------------------------------------------------
# Release audit
# ---------------------------------------------------------------------------
def server_chronicle_audit_v03811():
    errors = []
    for method_name in (
        "claim_server_legend_key_v03811",
        "add_server_chronicle_event_v03811",
        "server_chronicle_rows_v03811",
        "record_server_kill_v03811",
        "record_server_fish_record_v03811",
        "record_server_project_v03811",
        "record_server_exceptional_drop_v03811",
    ):
        if not hasattr(Database, method_name):
            errors.append("Database missing " + method_name)
    if not hasattr(Session, "show_server_chronicle_v03811"):
        errors.append("Session missing chronicle command handler")
    if COMMAND_ALIASES.get("kronika") != "chronicle":
        errors.append("kronika alias missing")
    if "kronika" not in HELP_TOPICS:
        errors.append("HELP kronika missing")
    return {
        "version": V03811_SERVER_CHRONICLE_VERSION,
        "event_types": 6,
        "error_count": len(errors),
        "errors": errors,
    }


SERVER_CHRONICLE_AUDIT_V03811 = server_chronicle_audit_v03811()
if SERVER_CHRONICLE_AUDIT_V03811["error_count"]:
    raise RuntimeError(
        "Server Chronicle Audit v0.38.11 failed: "
        + "; ".join(SERVER_CHRONICLE_AUDIT_V03811["errors"][:100])
    )

LATEST_CHANGES_TITLE = "Soulbound v0.38.11 - Procedural Legends & Server Chronicle"
LATEST_CHANGES = [
    "Dodano trwałą Kronikę Serwera dostępną komendą kronika / chronicle.",
    "Proceduralne Legendy zapisują pierwsze zabicia, world bossy, rekordy połowów, ukończone Projekty Świata i wyjątkowe dropy.",
    "Zwykłe pierwsze zabicia są pamiętane, ale widok domyślny pokazuje tylko ważniejsze wydarzenia; kronika wszystko pokazuje pełny zapis.",
    "Dodano filtry kronika zabicia, bossy, ryby, projekty i dropy oraz limit 1-100 wpisów.",
    "Kronika jest trwała w SQLite i przeżywa restart/deploy bez zmiany mechaniki walki, lootu ani progresji.",
    "Zachowano v0.38.10 Canonical Smithing Materials oraz wszystkie wcześniejsze audytowane milestone'y.",
]
