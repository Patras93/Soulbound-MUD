# -*- coding: utf-8 -*-
"""Durable equipment lock, per account and item ID."""
from core.mines_threat import ITEMS
from network.protocol_gameplay_utils import normalize_lookup_text

class SessionItemProtectionV1280Mixin:
    def item_is_protected_v1280(self, item_id):
        return self.server.db.inventory_is_protected_v1280(self.account_id, item_id)

    async def protect_item_v1280(self, query=""):
        raw = str(query or "").strip()
        pieces = raw.split(maxsplit=1)
        cmd = normalize_lookup_text(pieces[0]) if pieces else "lista"
        if cmd in ("lista", "list", "status", "info"):
            protected=[]
            for row in self.server.db.inventory(self.account_id):
                iid=str(row["item_id"])
                if self.item_is_protected_v1280(iid):
                    protected.append(f"{ITEMS.get(iid, {}).get('name', iid)} x{row['quantity']}")
            await self.send("Chronione EQ: " + (", ".join(protected) if protected else "brak") + ".")
            await self.send("Komendy: chron <nazwa EQ>, odchron <nazwa EQ>, chron lista. Ochrona obejmuje wszystkie identyczne egzemplarze.")
            return
        # Unknown action is treated as an item name (e.g. 'chron żelazny miecz').
        await self._set_item_protection_v1280(raw, True)

    async def unprotect_item_v1280(self, query=""):
        await self._set_item_protection_v1280(query, False)

    async def _set_item_protection_v1280(self, query, state):
        needle=normalize_lookup_text(query)
        if not needle:
            await self.send("Podaj nazwę EQ albo wpisz: chron lista.")
            return
        matches=[]
        for row in self.server.db.inventory(self.account_id):
            iid=str(row["item_id"])
            item=ITEMS.get(iid,{})
            if item.get("type") != "armor":
                continue
            name=normalize_lookup_text(item.get("name", ""))
            if needle == normalize_lookup_text(iid) or needle in name:
                matches.append((iid,item))
        if len(matches)!=1:
            await self.send("Nie znaleziono jednoznacznego EQ. Podaj pełną nazwę. Pasujących: " + str(len(matches)) + ".")
            return
        iid,item=matches[0]
        self.server.db.inventory_set_protected_v1280(self.account_id,iid,state)
        await self.send(("Chronisz " if state else "Odblokowujesz ") + item['name'] + ". " + (
            "Sprzedaż i rozkładanie tego EQ są zablokowane." if state else "Można je ponownie sprzedać lub rozłożyć."
        ))
