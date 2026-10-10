# -*- coding: utf-8 -*-
"""Lightweight helpers shared by persistence modules.

This module intentionally depends only on Python stdlib, static data catalogs,
and Generator Core. Database imports must not pull the gameplay protocol, HELP,
or world runtime into module import time.
"""

import hashlib
import re
import secrets
import unicodedata

from core import balance_math
from data.items import ITEMS


PBKDF2_ROUNDS = 210_000
V03042_EQ_UPGRADE_MAX = 10
DROP_HISTORY_LIMIT = 50

V0926_GUILD_MAX_LEVEL = 800
V0926_GUILD_OLD_CAP = 600
V0926_GUILD_LEGACY_MAX_LEVEL = 100
V0926_GUILD_PREVIOUS_CAP = 400

V0926_GUILD_DEFAULT_ROLES = {
    "member": {
        "name": "Członek", "priority": 10,
        "withdraw_money": 0, "withdraw_items": 0,
        "invite": 0, "kick": 0,
    },
    "officer": {
        "name": "Oficer", "priority": 100,
        "withdraw_money": 0, "withdraw_items": 1,
        "invite": 1, "kick": 1,
    },
}


def normalize_lookup_text(value):
    text = str(value or "").strip().lower().replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(text.split())


def hash_password(password: str, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS
    )
    return salt.hex(), digest.hex()


def canonical_profession_resource_id(item_id):
    item = ITEMS.get(item_id, {})
    return str(item.get("base_resource_id") or item_id)


def base_fish_species_id(item_id):
    return canonical_profession_resource_id(item_id)


def is_craft_material_storage_item(item_id):
    item = ITEMS.get(str(item_id), {})
    if item.get("type") == "craft_material":
        return True
    # Cut gems are built by runtime catalog expansion. Import the canonical
    # set only when inventory routing actually needs it, never during DB import.
    try:
        from systems.content_registry import CUT_GEM_IDS
        return str(item_id) in CUT_GEM_IDS
    except Exception:
        return False


def v0926_guild_bonus_percent(level):
    """Persistence copy of guild bonuses; legacy values through 600 preserved."""
    level = max(1, min(V0926_GUILD_MAX_LEVEL, int(level or 1)))
    if level <= V0926_GUILD_LEGACY_MAX_LEVEL:
        return balance_math.guild_bonus_percent(level, V0926_GUILD_LEGACY_MAX_LEVEL)
    if level <= V0926_GUILD_PREVIOUS_CAP:
        progress = ((level - V0926_GUILD_LEGACY_MAX_LEVEL)
                    / (V0926_GUILD_PREVIOUS_CAP - V0926_GUILD_LEGACY_MAX_LEVEL))
        return min(23, 11 + int(round(12 * (progress ** 0.90))))
    if level <= V0926_GUILD_OLD_CAP:
        progress = ((level - V0926_GUILD_PREVIOUS_CAP)
                    / (V0926_GUILD_OLD_CAP - V0926_GUILD_PREVIOUS_CAP))
        return min(29, 23 + int(round(6 * (progress ** 0.90))))
    progress = ((level - V0926_GUILD_OLD_CAP)
                / (V0926_GUILD_MAX_LEVEL - V0926_GUILD_OLD_CAP))
    return min(35, 29 + int(round(6 * (progress ** 0.90))))


V0927_GUILD_CONTRACTS = {
    "hunt100": {"name": "Wspólne Polowanie", "kind": "kills"},
    "boss5": {"name": "Piątka Bossów", "kind": "bosses"},
    "rune20": {
        "name": "Dostawa Pyłu Runicznego",
        "kind": "material",
        "item_id": "rune_dust",
    },
}
for _contract_id, _contract in V0927_GUILD_CONTRACTS.items():
    _kind = _contract["kind"]
    _stage = 1 + int(
        balance_math.stable_unit("guild-contract:" + _contract_id) * 399
    )
    _contract["generator_level"] = _stage
    if _kind == "kills":
        _contract["need"] = balance_math.generated_count(
            _stage, _contract_id, 40, 120
        )
    elif _kind == "bosses":
        _contract["need"] = balance_math.generated_count(
            _stage, _contract_id, 3, 10
        )
    else:
        _contract["need"] = balance_math.generated_count(
            _stage, _contract_id, 10, 35
        )
    _contract["reward"] = balance_math.system_reward(
        _stage,
        "guild-contract:" + _contract_id,
        max(4.0, _contract["need"] * 0.65),
    )
    _contract["cooldown"] = balance_math.generated_cooldown_seconds(
        _stage, "guild-contract:" + _contract_id, 3600, 21600
    )
