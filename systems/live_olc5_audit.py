# -*- coding: utf-8 -*-
"""Read-only NVDA-oriented status of a staged OLC revision."""
from systems.live_content_v1204 import blank

def live_audit_summary(service):
    active, draft = service.active, service.draft
    modified = [key for key in blank() if active[key] != draft[key]]
    try:
        summary = service.validate(draft)
        verdict = 'Walidacja PASS'
    except (ValueError, TypeError, OverflowError) as exc:
        verdict = 'Walidacja ODRZUCONA'
        summary = str(exc)[:240]
    names = ', '.join(modified) if modified else 'brak'
    return (f'OLC AUDYT: rewizja {service.revision}; {len(modified)} zmienionych sekcji: {names}. '
            f'{verdict}. {summary}. Bez zapisu SQLite i bez NEWS.')
