# -*- coding: utf-8 -*-
"""v109: bez zmian zachowania, wyodrebnione metody gildii.

Nie ma tutaj wyplat z konta, depozytow, ani operacji na ekwipunku.
"""

class GuildMembershipV109Mixin:

    def guild_row_v0926(self):
                return self.server.db.clan_membership(self.account_id)

    def clan_row_v0925(self):
                return self.guild_row_v0926()

    def clan_session_by_account_v0925(self, account_id):
                for sess in list(self.server.sessions):
                    if getattr(sess,"account_id",None)==account_id and not sess.closed:
                        return sess
                return None
