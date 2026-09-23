# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: quests."""
from player.session_mixins.quest_progress import SessionQuestProgressMixin
from player.session_mixins.quest_offers import SessionQuestOffersMixin
from player.session_mixins.quest_turnin import SessionQuestTurninMixin
from player.session_mixins.quest_npc import SessionQuestNpcMixin
from player.session_mixins.quest_commands import SessionQuestCommandsMixin


class SessionQuestsMixin(
    SessionQuestProgressMixin,
    SessionQuestOffersMixin,
    SessionQuestTurninMixin,
    SessionQuestNpcMixin,
    SessionQuestCommandsMixin,
):
    """Compatibility aggregate; methods live in focused maintenance mixins."""
    pass
