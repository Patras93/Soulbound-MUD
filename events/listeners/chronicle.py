# -*- coding: utf-8 -*-
"""Server chronicle listeners."""
from events.contracts import MobDefeatedEvent


def record_server_kill(event: MobDefeatedEvent):
    session = event.killer_session
    session.server.db.record_server_kill_v03811(
        session.account_id,
        session.character.name,
        event.template_id,
        [member.character.name for member in event.recipients],
    )
