# -*- coding: utf-8 -*-
"""v109: bez zmian zachowania, wyodrebnione metody gildii.

Nie ma tutaj wyplat z konta, depozytow, ani operacji na ekwipunku.
"""

class GuildBonusesV109Mixin:

    def refresh_guild_bonus_v0926(self):
                pct=self.server.db.guild_bonus_percent_v0926(self.account_id) if getattr(self,"account_id",None) else 0
                from systems.live_olc28_expansion import guild_extra_bonus
                membership = self.guild_row_v0926()
                pct = int(pct) + guild_extra_bonus(bool(membership))
                if membership:
                    from systems.live_olc29_creation import guild_level_bonus
                    # Guild growth level is stored in player_clans, not in a character.
                    row = self.server.db.conn.execute(
                        'SELECT level FROM player_clans WHERE id=?',
                        (int(membership['clan_id']),)).fetchone()
                    _guild_level = int(row['level']) if row else 1
                    pct += guild_level_bonus(_guild_level)
                    from systems.live_olc32_finale import guild_milestone_bonus
                    pct += guild_milestone_bonus(_guild_level)
                    from systems.live_olc35_finale import city_bonus
                    pct += city_bonus(self.server.db.conn,int(membership['clan_id']))
                if getattr(self,"character",None):
                    self.character._guild_bonus_percent=int(pct)
                return int(pct)

    def guild_bonus_percent_v0926(self):
                return self.refresh_guild_bonus_v0926()
