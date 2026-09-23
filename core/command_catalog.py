# -*- coding: utf-8 -*-
"""Central command catalog for Soulbound v0.49.0.

The catalog is intentionally small and runtime-neutral.  It owns command
identity, alias provenance, handler metadata and state-safety flags while the
actual gameplay methods stay in their focused Session mixins.

Legacy modules may keep calling ``COMMAND_ALIASES.update(...)``.  The
``CommandAliasMap`` compatibility view records those writes in this central
catalog, so the parser and audits still have one authoritative resolved view.
New code should register aliases/handlers through the helpers in this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import inspect
from typing import Any, Iterable, Mapping


COMMAND_LOOP_BREAK = object()



def _normalize(value: object) -> str:
    return str(value or "").strip().lower()


def _caller_source() -> str:
    frame = inspect.currentframe()
    try:
        frame = frame.f_back if frame else None
        while frame is not None:
            filename = str(frame.f_code.co_filename or "").replace("\\", "/")
            if not filename.endswith("/core/command_catalog.py"):
                marker = "/Soulbound"
                if marker in filename:
                    return filename[filename.rfind(marker) + 1 :]
                parts = filename.split("/")
                for root in ("core", "systems", "world", "player", "network", "admin", "storage", "data", "server"):
                    if root in parts:
                        return "/".join(parts[parts.index(root):])
                return filename
            frame = frame.f_back
    finally:
        del frame
    return "<unknown>"


@dataclass
class CommandDefinition:
    canonical: str
    handler: str | None = None
    source: str = ""
    help_topic: str | None = None
    kind: str = "registered"
    downed_safe: bool = False
    rest_safe: bool = False
    guide_safe: bool = False
    aliases: set[str] = field(default_factory=set)

    def as_dict(self) -> dict[str, Any]:
        return {
            "canonical": self.canonical,
            "handler": self.handler,
            "source": self.source,
            "help_topic": self.help_topic,
            "kind": self.kind,
            "downed_safe": self.downed_safe,
            "rest_safe": self.rest_safe,
            "guide_safe": self.guide_safe,
            "aliases": tuple(sorted(self.aliases)),
        }


class CommandCatalog:
    def __init__(self) -> None:
        self._definitions: dict[str, CommandDefinition] = {}
        self._alias_to_canonical: dict[str, str] = {}
        self._alias_source: dict[str, str] = {}
        self._conflicts: list[dict[str, str]] = []

    def ensure(self, canonical: object) -> CommandDefinition:
        key = _normalize(canonical)
        if not key:
            raise ValueError("Command canonical name cannot be empty")
        definition = self._definitions.get(key)
        if definition is None:
            definition = CommandDefinition(canonical=key)
            self._definitions[key] = definition
        return definition

    def add_alias(self, alias: object, canonical: object, *, source: str | None = None) -> None:
        alias_key = _normalize(alias)
        canonical_key = _normalize(canonical)
        if not alias_key or not canonical_key:
            raise ValueError("Command alias and target must be non-empty")
        source = source or _caller_source()
        old = self._alias_to_canonical.get(alias_key)
        if old is not None and old != canonical_key:
            self._conflicts.append({
                "alias": alias_key,
                "old": old,
                "new": canonical_key,
                "old_source": self._alias_source.get(alias_key, ""),
                "new_source": source,
            })
            old_def = self._definitions.get(old)
            if old_def is not None:
                old_def.aliases.discard(alias_key)
        self._alias_to_canonical[alias_key] = canonical_key
        self._alias_source[alias_key] = source
        self.ensure(canonical_key).aliases.add(alias_key)

    def register_handler(
        self,
        canonical: object,
        handler: str,
        *,
        source: str | None = None,
        help_topic: str | None = None,
        kind: str = "registered",
    ) -> CommandDefinition:
        definition = self.ensure(canonical)
        definition.handler = str(handler)
        definition.source = source or _caller_source()
        definition.help_topic = _normalize(help_topic) if help_topic else definition.canonical
        definition.kind = str(kind or "registered")
        return definition

    def set_policy(
        self,
        canonical: object,
        *,
        downed_safe: bool | None = None,
        rest_safe: bool | None = None,
        guide_safe: bool | None = None,
    ) -> CommandDefinition:
        definition = self.ensure(canonical)
        if downed_safe is not None:
            definition.downed_safe = bool(downed_safe)
        if rest_safe is not None:
            definition.rest_safe = bool(rest_safe)
        if guide_safe is not None:
            definition.guide_safe = bool(guide_safe)
        return definition

    def resolve(self, token: object) -> str:
        key = _normalize(token)
        return self._alias_to_canonical.get(key, key)

    def definition(self, canonical_or_alias: object) -> CommandDefinition | None:
        canonical = self.resolve(canonical_or_alias)
        return self._definitions.get(canonical)

    def aliases(self) -> dict[str, str]:
        return dict(self._alias_to_canonical)

    def alias_source(self, alias: object) -> str | None:
        return self._alias_source.get(_normalize(alias))

    def definitions(self) -> dict[str, CommandDefinition]:
        return dict(self._definitions)

    def conflicts(self) -> tuple[dict[str, str], ...]:
        return tuple(self._conflicts)

    def bind_help(self, help_topics: Mapping[str, Any], help_aliases: Mapping[str, str]) -> int:
        """Resolve each command to a real HELP topic after all milestone patches load."""
        bound = 0
        for definition in self._definitions.values():
            candidates = [definition.canonical, *sorted(definition.aliases)]
            resolved = None
            for candidate in candidates:
                target = help_aliases.get(candidate, candidate)
                if target in help_topics:
                    resolved = target
                    break
            definition.help_topic = resolved
            if resolved is not None:
                bound += 1
        return bound

    def snapshot(self) -> dict[str, Any]:
        handler_count = sum(1 for d in self._definitions.values() if d.handler)
        return {
            "command_count": len(self._definitions),
            "handler_count": handler_count,
            "alias_count": len(self._alias_to_canonical),
            "alias_conflict_count": len(self._conflicts),
            "help_bound_count": sum(1 for d in self._definitions.values() if d.help_topic),
            "alias_sources": dict(self._alias_source),
            "commands": {k: v.as_dict() for k, v in sorted(self._definitions.items())},
        }


COMMAND_CATALOG = CommandCatalog()


class CommandAliasMap(dict):
    """dict-compatible alias table backed by ``COMMAND_CATALOG`` provenance."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        if args or kwargs:
            owner = _caller_source()
            data = dict(*args, **kwargs)
            self._update_with_owner(data, owner)

    def _set_with_owner(self, alias: object, canonical: object, owner: str) -> None:
        alias_key = _normalize(alias)
        canonical_key = _normalize(canonical)
        COMMAND_CATALOG.add_alias(alias_key, canonical_key, source=owner)
        super().__setitem__(alias_key, canonical_key)

    def _update_with_owner(self, values: Mapping | Iterable, owner: str) -> None:
        data = dict(values)
        for alias, canonical in data.items():
            self._set_with_owner(alias, canonical, owner)

    def __setitem__(self, alias: object, canonical: object) -> None:
        self._set_with_owner(alias, canonical, _caller_source())

    def update(self, *args: Any, **kwargs: Any) -> None:
        owner = _caller_source()
        data = dict(*args, **kwargs)
        self._update_with_owner(data, owner)

    def setdefault(self, alias: object, default: object = None):
        alias_key = _normalize(alias)
        if alias_key in self:
            return super().__getitem__(alias_key)
        self._set_with_owner(alias_key, default, _caller_source())
        return super().__getitem__(alias_key)


COMMAND_CATALOG_VERSION = "0.49.0"
