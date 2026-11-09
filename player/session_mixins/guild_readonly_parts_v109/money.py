# -*- coding: utf-8 -*-
"""v109: bez zmian zachowania, wyodrebnione metody gildii.

Nie ma tutaj wyplat z konta, depozytow, ani operacji na ekwipunku.
"""

class GuildMoneyV109Mixin:

    def parse_guild_money_v0926(self, raw):
                parts=str(raw or "").strip().split()
                if not parts or not parts[0].isdigit():
                    return None
                amount=int(parts[0])
                if amount<=0:
                    return None
                currency=self.normalize_bank_currency(parts[1]) if len(parts)>1 else "silver"
                if not currency:
                    return None
                return self.bank_amount_to_silver(amount,currency)
