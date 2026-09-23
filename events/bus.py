# -*- coding: utf-8 -*-
"""Small deterministic async event bus used by gameplay subsystems."""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True, frozen=True)
class Subscription:
    event_type: type
    handler: Callable[[Any], Any]
    name: str
    critical: bool = True


class EventBus:
    """Sequential event dispatcher with explicit error policy.

    Sequential order is deliberate: migrating old direct calls into listeners
    must not silently reorder gameplay side effects.
    """

    def __init__(self, error_reporter=None):
        self._subscriptions: dict[type, list[Subscription]] = {}
        self._error_reporter = error_reporter

    def subscribe(self, event_type, handler, *, name=None, critical=True):
        subscription = Subscription(
            event_type=event_type,
            handler=handler,
            name=str(name or getattr(handler, "__qualname__", getattr(handler, "__name__", "listener"))),
            critical=bool(critical),
        )
        rows = self._subscriptions.setdefault(event_type, [])
        if any(row.name == subscription.name for row in rows):
            raise ValueError(f"Duplicate event listener: {event_type.__name__}:{subscription.name}")
        rows.append(subscription)
        return subscription

    def listeners_for(self, event_or_type):
        event_type = event_or_type if isinstance(event_or_type, type) else type(event_or_type)
        return tuple(self._subscriptions.get(event_type, ()))

    async def publish(self, event):
        delivered = []
        errors = []
        for subscription in self.listeners_for(event):
            try:
                result = subscription.handler(event)
                if inspect.isawaitable(result):
                    await result
                delivered.append(subscription.name)
            except Exception as exc:
                errors.append((subscription.name, exc))
                if self._error_reporter is not None:
                    try:
                        self._error_reporter(
                            exc,
                            command=f"event:{type(event).__name__}",
                            handler=subscription.name,
                        )
                    except Exception:
                        pass
                if subscription.critical:
                    raise
        return {"event": type(event).__name__, "delivered": tuple(delivered), "errors": tuple(errors)}

    def describe(self):
        return {
            event_type.__name__: tuple(
                {"name": row.name, "critical": row.critical} for row in rows
            )
            for event_type, rows in sorted(
                self._subscriptions.items(), key=lambda pair: pair[0].__name__
            )
        }
