# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def handle_party(self, args):
        parts = args.strip().split(maxsplit=1)
        if not parts:
            await self.show_party()
            return

        action = self.normalize_description_query(parts[0])
        value = parts[1] if len(parts) > 1 else ""

        if action in ("status", "lista", "list", "sklad"):
            await self.show_party()
        elif action in ("zaloz", "utworz", "stworz", "create"):
            await self.create_party()
        elif action in ("zapros", "invite"):
            if not value:
                await self.send("Użycie: druzyna zapros <gracz>.")
            else:
                await self.party_invite(value)
        elif action in ("dolacz", "accept"):
            await self.party_accept()
        elif action in ("odrzuc", "decline"):
            await self.party_decline()
        elif action in ("opusc", "leave"):
            await self.leave_party(announce=True)
        elif action in ("wyrzuc", "kick"):
            if not value:
                await self.send("Użycie: druzyna wyrzuc <gracz>.")
            else:
                await self.party_kick(value)
        elif action in ("rozwiaz", "disband"):
            await self.disband_party()
        elif action in ("lider", "leader", "przekaz"):
            await self.transfer_party_leader(value)
        elif action in ("zaslon", "oslon", "protect"):
            await self.protect_party(value)
        elif action in ("wspieraj", "assist", "pomagaj"):
            if not value:
                await self.send(
                    "Użycie: druzyna wspieraj <gracz>."
                )
            else:
                await self.assist_party_member(value)
        elif action in ("wskrzes", "wskrześ", "revive"):
            await self.revive_party_member_v0371(value)
        elif action in ("raport", "health", "zdrowie"):
            await self.party_report_v1193()
        elif action in ("zbiorka", "zbiórka", "zbierz", "gather"):
            await self.party_gather_v1193()
        elif action in ("trasa", "route"):
            await self.party_route_v1193(value)
        elif action in ("pomoc", "komendy", "help"):
            await self.send("Party 4.0: druzyna raport, druzyna zbiorka, druzyna trasa <cel>, "
                            "druzyna trasa krok, druzyna trasa off. "
                            "Ponadto: druzyna cel, gotowi, niegotowy, zapros, wspieraj.")
        elif action in ("cel", "goal", "objective"):
            await self.set_party_goal_v0610(value)
        elif action in ("gotowi", "ready", "readycheck"):
            await self.handle_party_ready_v0610(value)
        elif action in ("niegotowy", "notready", "unready"):
            await self.set_party_not_ready_v0610()
        elif action in ("limit", "capacity"):
            key = self.party_key()
            leader = self.server.session_by_account(key) if key else self
            leader = leader or self
            await self.send(
                f"Limit drużyny: {leader.character.party_capacity()} osób. "
                f"Startowo 8; +1 miejsce co 25 Charyzmy lidera."
            )
        else:
            await self.send(
                "Drużyna: zaloz, status, zapros <gracz>, dolacz, odrzuc, "
                "opusc, wyrzuc <gracz>, rozwiaz, lider <gracz>, "
                "cel <tekst>/off, gotowi [status/reset], niegotowy, "
                "raport, zbiorka, trasa <cel>/krok/off, "
                "zaslon [off], wspieraj <gracz>, wskrzes <gracz>, limit. Czat: pc <tekst>."
            )

