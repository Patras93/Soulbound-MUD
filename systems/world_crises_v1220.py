# -*- coding: utf-8 -*-
"""Multi-stage daily regional crises using existing traversable world and enemies.

All phases take place in existing regions: mobs are real combat opponents,
not simulated 'click to kill' counters. Daily state is per character and
kills credited through the game's existing same-room party recipients.
"""
import time

CRISES = {
    "aurora": {"name": "Inwazja na Ogrody Zorzy", "story": "Odeprzyj najeźdźców i uratuj mieszkańców ogrodów."},
    "thunder": {"name": "Oblężenie Burzowych Stepów", "story": "Obroń obozowisko przed napierającymi oddziałami."},
    "coral": {"name": "Ratunek na Koralowych Urwiskach", "story": "Uwolnij rozbitków i odzyskaj opanowane przez wrogów przejścia."},
    "clock": {"name": "Kryzys Mechanicznej Doliny", "story": "Zatrzymaj zbuntowane automaty i napraw szlak zaopatrzenia."},
}
STAGES = {0: "Nieprzyjęte", 1: "Odeprzyj zwiadowców kryzysu", 2: "Pokonaj najeźdźców i uratuj cywilów", 3: "Pokonaj przywódcę", 4: "Odbierz nagrodę", 5: "Ukończone"}


def crisis_day(now=None):
    return int((time.time() if now is None else now) // 86400)


def crisis_progress_message(stage, kills):
    if stage == 1:
        return f"Etap 1/3: zwiadowcy kryzysu {kills}/3. Szukaj na szlaku od obozu."
    if stage == 2:
        return f"Etap 2/3: najeźdźcy kryzysu {kills}/4. Potem wróć do obozu i użyj 'kryzys ratuj'."
    if stage == 3:
        return "Etap 3/3: pokonaj regionalnego bossa w jego arenie."
    if stage == 4:
        return "Sukces: wróć do obozu po nagrodę — kryzys odbierz."
    return STAGES.get(stage, STAGES[0])


def crisis_reward(stage):
    """Silver and rare essence amounts scale with regional difficulty."""
    stage = max(1, int(stage))
    return 20000 + stage * 280, max(3, stage // 45)
