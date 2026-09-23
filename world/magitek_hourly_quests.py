# -*- coding: utf-8 -*-
"""Soulbound v0.38.3 - Hourly Magitek Contracts.

Adds a permanent set of Magitek hourly quests to the existing hourly quest board.
Every contract starts at 0/x, has its own 60 minute cooldown after turn-in and
reuses the normal party quest-accept synchronization.
"""
from data import catalog_mutations as _catalog_mut

V0383_MAGITEK_HOURLY_VERSION = "0.38.3"
V0383_MAGITEK_HOURLY_COOLDOWN = 60 * 60

V0383_MAGITEK_HOURLY_IDS = (
    "hourly_magitek_patrol",
    "hourly_magitek_deep_patrol",
    "hourly_magitek_elites",
    "hourly_magitek_bosses",
    "hourly_magitek_core",
    "hourly_magitek_warmech_core",
    "hourly_magitek_salvage_set",
)

# All quests use the existing hourly board. The `level` field is a reward-stage
# hint only; it is NOT an acceptance gate.
_catalog_mut.catalog_update_path('QUESTS', QUESTS, (), {
    "hourly_magitek_patrol": {
        "name": "Godzinne Magitek: Czyszczenie kompleksu",
        "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "machine", "needed": 30, "level": 180,
        "description": "Pokonaj 30 dowolnych przeciwników typu Machine w Kompleksie Magitek. Liczą się wyłącznie zabójstwa po przyjęciu zadania.",
        "reward_silver": 0, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 2},
        "repeatable": True, "repeat_cooldown": V0383_MAGITEK_HOURLY_COOLDOWN,
        "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_magitek_deep_patrol": {
        "name": "Godzinne Magitek: Patrol głębinowy",
        "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "magitek_infinite", "needed": 20, "level": 240,
        "description": "Pokonaj 20 Machine na nieskończonych piętrach Kompleksu Magitek. Każdy nowy odbiór zaczyna od 0/20.",
        "reward_silver": 0, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
        "repeatable": True, "repeat_cooldown": V0383_MAGITEK_HOURLY_COOLDOWN,
        "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_magitek_elites": {
        "name": "Godzinne Magitek: Polowanie na prototypy",
        "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "magitek_elite", "needed": 3, "level": 270,
        "description": "Pokonaj 3 elitarne prototypy Magitek na nieskończonych piętrach. Elity pojawiają się m.in. co 5 pięter poza progami bossów.",
        "reward_silver": 0, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
        "repeatable": True, "repeat_cooldown": V0383_MAGITEK_HOURLY_COOLDOWN,
        "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_magitek_bosses": {
        "name": "Godzinne Magitek: Łowca WarMechów",
        "giver": "Tablica Godzinnych Zleceń",
        "kind": "kill", "target": "magitek_boss", "needed": 2, "level": 320,
        "description": "Pokonaj 2 bossów Machine/Magitek po przyjęciu zlecenia. Bossy nieskończonego Kompleksu pojawiają się co 10 pięter.",
        "reward_silver": 0, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_shard": 1, "soul_elixir": 1},
        "repeatable": True, "repeat_cooldown": V0383_MAGITEK_HOURLY_COOLDOWN,
        "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_magitek_core": {
        "name": "Godzinne Magitek: Rdzenie Magitek",
        "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect", "target": "machine_magitek_core", "needed": 5, "level": 250,
        "description": "Zdobądź 5 nowych Rdzeni Magitek po przyjęciu zlecenia. Stare zapasy nie nabijają postępu; przy oddaniu wymagane rdzenie są zużywane.",
        "progress_label": "Rdzeni Magitek",
        "reward_silver": 0, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
        "repeatable": True, "repeat_cooldown": V0383_MAGITEK_HOURLY_COOLDOWN,
        "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_magitek_warmech_core": {
        "name": "Godzinne Magitek: Rdzenie WarMecha",
        "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect", "target": "machine_warmech_core", "needed": 2, "level": 340,
        "description": "Zdobądź 2 nowe Rdzenie WarMecha po przyjęciu zlecenia. Przy oddaniu oba rdzenie są zużywane.",
        "progress_label": "Rdzeni WarMecha",
        "reward_silver": 0, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_shard": 1},
        "repeatable": True, "repeat_cooldown": V0383_MAGITEK_HOURLY_COOLDOWN,
        "hourly_rotation": False, "remote_turnin": True,
    },
    "hourly_magitek_salvage_set": {
        "name": "Godzinne Magitek: Zestaw odzysku",
        "giver": "Tablica Godzinnych Zleceń",
        "kind": "collect_resource_set", "target": "magitek_salvage", "needed": 13, "level": 210,
        "resource_targets": {
            "machine_servo": 4,
            "machine_circuit": 4,
            "machine_power_cell": 3,
            "machine_targeting_chip": 2,
        },
        "description": "Zdobądź po przyjęciu: 4 Serwomechanizmy, 4 Obwody Sterujące, 3 Ogniwa Zasilające i 2 Chipy Celownicze. Materiały są zużywane przy oddaniu.",
        "reward_silver": 0, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
        "repeatable": True, "repeat_cooldown": V0383_MAGITEK_HOURLY_COOLDOWN,
        "hourly_rotation": False, "remote_turnin": True,
    },
})

# Append to the permanent hourly board without disturbing the existing offer order.
HOURLY_QUEST_IDS = tuple(dict.fromkeys(tuple(HOURLY_QUEST_IDS) + V0383_MAGITEK_HOURLY_IDS))


def _v0383_add_target(template, target):
    values = []
    primary = template.get("quest_target")
    if primary:
        values.append(str(primary))
    raw = template.get("quest_targets") or ()
    if isinstance(raw, str):
        values.append(raw)
    else:
        values.extend(map(str, raw))
    values.append(str(target))
    template["quest_targets"] = tuple(dict.fromkeys(v for v in values if v))


def v0383_tag_magitek_template(template):
    if not isinstance(template, dict):
        return template
    is_machine = bool(template.get("machine")) or str(template.get("creature_type", "")).casefold() == "machine"
    if not is_machine:
        return template
    _v0383_add_target(template, "machine")
    if template.get("magitek_infinite"):
        _v0383_add_target(template, "magitek_infinite")
    if template.get("elite") or str(template.get("rank", "")).casefold() == "elite":
        _v0383_add_target(template, "magitek_elite")
    if template.get("magitek_boss") or template.get("machine_boss") or template.get("boss"):
        _v0383_add_target(template, "magitek_boss")
    return template


# Tag all authored and already-materialized Machine templates.
for _v0383_mid, _v0383_template in list(MOB_TEMPLATES.items()):
    v0383_tag_magitek_template(_v0383_template)

# Future lazy-generated Magitek floors must receive the same aliases.
_create_infinite_magitek_floor_definition_before_v0383 = create_infinite_magitek_floor_definition

def create_infinite_magitek_floor_definition(floor):
    room_id, spawns = _create_infinite_magitek_floor_definition_before_v0383(floor)
    for _room_id, template_id in spawns:
        v0383_tag_magitek_template(MOB_TEMPLATES.get(template_id))
    return room_id, spawns


HELP_TOPICS["godzinne magitek"] = [
    "v0.38.3: Tablica Godzinnych Zleceń ma 7 stałych zleceń Magitek.",
    "Każde zlecenie odnawia się niezależnie po 60 minutach od oddania i każdy nowy odbiór zaczyna od 0/x.",
    "Cele obejmują dowolne Machine, nieskończone piętra, elitarne prototypy, bossów, Rdzenie Magitek, Rdzenie WarMecha i zestaw komponentów.",
    "Komenda: questy godzinne. Przyjęcie przez lidera nadal korzysta z synchronizacji questów dla członków drużyny stojących razem.",
]
HELP_TOPIC_ALIASES.update({
    "magitek questy": "godzinne magitek",
    "questy magitek": "godzinne magitek",
    "magitek hourly": "godzinne magitek",
    "hourly magitek": "godzinne magitek",
})


def magitek_hourly_quests_audit_v0383():
    errors = []
    for quest_id in V0383_MAGITEK_HOURLY_IDS:
        q = QUESTS.get(quest_id)
        if not isinstance(q, dict):
            errors.append(f"missing quest {quest_id}")
            continue
        if quest_id not in HOURLY_QUEST_IDS:
            errors.append(f"not on hourly board: {quest_id}")
        if not q.get("repeatable") or int(q.get("repeat_cooldown", 0) or 0) != 3600:
            errors.append(f"bad cooldown: {quest_id}")
        if not q.get("remote_turnin"):
            errors.append(f"remote turn-in disabled: {quest_id}")
        if int(q.get("needed", 0) or 0) <= 0:
            errors.append(f"bad needed: {quest_id}")

    if len(V0383_MAGITEK_HOURLY_IDS) != 7:
        errors.append("expected 7 Magitek hourly quests")

    machine_count = 0
    boss_count = 0
    for template in MOB_TEMPLATES.values():
        if not isinstance(template, dict):
            continue
        if template.get("machine") or str(template.get("creature_type", "")).casefold() == "machine":
            machine_count += 1
            targets = set(template.get("quest_targets") or ())
            if "machine" not in targets:
                errors.append(f"machine without generic quest target: {template.get('name')}")
            if template.get("magitek_boss") or template.get("machine_boss") or template.get("boss"):
                boss_count += 1
                if "magitek_boss" not in targets:
                    errors.append(f"Magitek boss without boss quest target: {template.get('name')}")

    # Verify lazy generation without leaving the test floor in the static release.
    probe_floor = 770
    probe_room = magitek_floor_id(probe_floor)
    before_templates = set(MOB_TEMPLATES)
    before_room = ROOMS.get(probe_room)
    try:
        _room, spawns = create_infinite_magitek_floor_definition(probe_floor)
        probe_templates = [MOB_TEMPLATES.get(tid, {}) for _rid, tid in spawns]
        if not any("magitek_infinite" in set(t.get("quest_targets") or ()) for t in probe_templates):
            errors.append("lazy Magitek mobs missing magitek_infinite target")
        boss_templates = [t for t in probe_templates if t.get("magitek_boss") or t.get("machine_boss") or t.get("boss")]
        if not boss_templates or not all("magitek_boss" in set(t.get("quest_targets") or ()) for t in boss_templates):
            errors.append("lazy Magitek boss missing magitek_boss target")
    finally:
        for tid in set(MOB_TEMPLATES) - before_templates:
            _catalog_mut.catalog_pop_path('MOB_TEMPLATES', MOB_TEMPLATES, (), tid, None)
        if before_room is None:
            _catalog_mut.catalog_pop_path('ROOMS', ROOMS, (), probe_room, None)
        else:
            _catalog_mut.catalog_assign(before_room, 'ROOMS', ROOMS, (probe_room,))

    return {
        "version": V0383_MAGITEK_HOURLY_VERSION,
        "quest_count": len(V0383_MAGITEK_HOURLY_IDS),
        "machine_templates_checked": machine_count,
        "boss_templates_checked": boss_count,
        "error_count": len(errors),
        "errors": errors,
    }


MAGITEK_HOURLY_QUESTS_AUDIT_V0383 = magitek_hourly_quests_audit_v0383()
if MAGITEK_HOURLY_QUESTS_AUDIT_V0383["error_count"]:
    raise RuntimeError(
        "Hourly Magitek Quests Audit v0.38.3 failed: "
        + "; ".join(MAGITEK_HOURLY_QUESTS_AUDIT_V0383["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.3: 7 godzinnych zleceń Magitek; każde odnawia się osobno po 60 minutach i zaczyna ponownie od 0/x."
)
LATEST_CHANGES_TITLE = "Soulbound v0.38.3 - Hourly Magitek Contracts"
LATEST_CHANGES = [
    "Dodano 7 stałych, odnawialnych co 60 minut zleceń Magitek na istniejącej Tablicy Godzinnych Zleceń.",
    "Questy obejmują Machine, głębokie piętra, elitarne prototypy, bossów oraz technologiczne komponenty.",
    "Każdy quest ma własny cooldown liczony od oddania i każdy kolejny odbiór startuje od 0/x.",
    "Zachowano synchronizację przyjmowania questów przez lidera drużyny i wszystkie wcześniejsze milestone'y.",
]
