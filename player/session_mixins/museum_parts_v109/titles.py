# -*- coding: utf-8 -*-
"""v109: muzeum, osiągnięcia i zlecenia — titles. Historyczne metody bez zmian."""
from .dependencies import *

class MuseumTitlesV109Mixin:
    def v0260_title_bonus_rule(self):
            if not self.character:
                return None
            return V0260_TITLE_BONUSES.get(str(self.character.active_title or ""))

    def v0260_profession_xp_bonus_percent(self, profession, tool_type):
            rule = self.v0260_title_bonus_rule()
            if not rule:
                return 0
            wanted = str(rule.get("tool", ""))
            if wanted == "all" or wanted == str(tool_type):
                return max(0, int(rule.get("percent", 0) or 0))
            return 0

    def v0260_title_bonus_text(self, title_name=None):
            name = str(title_name if title_name is not None else (self.character.active_title if self.character else "") or "")
            rule = V0260_TITLE_BONUSES.get(name)
            return str(rule.get("text", "")) if rule else ""
