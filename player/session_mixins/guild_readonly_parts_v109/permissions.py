# -*- coding: utf-8 -*-
"""v109: bez zmian zachowania, wyodrebnione metody gildii.

Nie ma tutaj wyplat z konta, depozytow, ani operacji na ekwipunku.
"""

class GuildPermissionsV109Mixin:

    def guild_role_v0926(self, membership=None):
                row=membership or self.guild_row_v0926()
                if not row:
                    return None
                return self.server.db.guild_role_v0926(int(row["clan_id"]),str(row["rank"]))

    def guild_has_permission_v0926(self, permission, membership=None):
                row=membership or self.guild_row_v0926()
                if not row:
                    return False
                if str(row["rank"])=="leader":
                    return True
                role=self.guild_role_v0926(row)
                return bool(role and int(role[permission] or 0))

    def guild_rank_name_v0926(self, membership=None):
                row=membership or self.guild_row_v0926()
                if not row:
                    return "Brak"
                role=self.guild_role_v0926(row)
                return str(role["name"]) if role else str(row["rank"])

    def guild_rank_priority_v0926(self, membership=None):
                row=membership or self.guild_row_v0926()
                if not row:
                    return 0
                role=self.guild_role_v0926(row)
                return int(role["priority"]) if role else 0
