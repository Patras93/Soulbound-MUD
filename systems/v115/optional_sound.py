# -*- coding: utf-8 -*-
"""Optional audio adapter. Gameplay must never depend on soundpack transport.

The old SOUND_EVENT protocol remains available without requiring client audio.
SOULBOUND_SOUND_EVENTS=0 disables optional audio entirely on this server.
The normal default remains enabled for backward compatibility with soundpacks.
"""
from __future__ import annotations
import os


def audio_enabled():
    return os.environ.get('SOULBOUND_SOUND_EVENTS', '1').strip().lower() not in {'0', 'off', 'false', 'no'}


def _audio():
    if not audio_enabled():
        return None
    try:
        from systems import sound_events_v1208
        return sound_events_v1208
    except ModuleNotFoundError as exc:
        if exc.name in {'systems.sound_events_v1208', 'sound_events_v1208'}:
            return None
        raise


def install_sound_hooks_v1208(session_class):
    module = _audio()
    if module is not None:
        module.install_sound_hooks_v1208(session_class)


def _event(event_name, **fields):
    module = _audio()
    return module._event(event_name, **fields) if module is not None else None


def record_paid_exp_event_v11329(db, account_id, paid, cap, *, kind='character'):
    module = _audio()
    if module is not None:
        return module.record_paid_exp_event_v11329(db, account_id, paid, cap, kind=kind)
    return None


def sound_reward_queue_checkpoint_v11329(db, account_id):
    module = _audio()
    return module.sound_reward_queue_checkpoint_v11329(db, account_id) if module is not None else None


def sound_reward_queue_rollback_v11329(db, account_id, checkpoint):
    module = _audio()
    if module is not None:
        module.sound_reward_queue_rollback_v11329(db, account_id, checkpoint)
