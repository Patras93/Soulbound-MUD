# -*- coding: utf-8 -*-
"""v109: oryginalne metody administratora, niezmieniona logika i uprawnienia."""
from __future__ import annotations

class AdminGuardianControlsV109Mixin:
    async def admin_god_mode_v35005(self, args=""):
        """Session-only owner immortality; ordinary play stays unchanged."""
        if not self.is_admin():
            await self.send("Nieznana komenda. Wpisz help.")
            return
        choice = self.normalize_description_query(str(args or "").strip())
        if choice in ("", "status"):
            state = "WLACZONA" if getattr(self, "admin_god_v35005", False) else "WYLACZONA"
            await self.send(f"ADMIN GOD: {state}. Uzyj admin god on/off.")
            return
        if choice not in ("on", "off"):
            await self.send("Uzycie: admin god on / admin god off / admin god status.")
            return
        enabled = choice == "on"
        self.admin_god_v35005 = enabled
        if enabled:
            self.current_hp = self.max_hp()
        self.server.db.record_admin_action_v1224(
            self.server.db.account_name(self.master_account_id),
            "god_on" if enabled else "god_off", self.character.name,
        )
        await self.send(
            "ADMIN GOD WLACZONY: nie mozesz zginac; koledzy nadal graja normalnie. "
            "Wylacz przez admin god off. Tryb nie zapisuje sie po wylogowaniu."
            if enabled else "ADMIN GOD WYLACZONY: wracasz do normalnej walki."
        )

    async def admin_unique_strike_v35005(self, args=""):
        """Owner-only rescue strike; uses canonical victory and party credit."""
        if not self.is_admin():
            await self.send("Nieznana komenda. Wpisz help.")
            return
        from data.mobs import MOB_TEMPLATES as _mob_catalog
        from world.uoss_superboss_runtime import superboss_attack_gate_v11137
        words = str(args or "").strip().split(maxsplit=1)
        if not words or self.normalize_description_query(words[0]) not in ("grom", "nawalnica", "wyrok"):
            await self.send("Uzycie: admin cios grom/nawalnica/wyrok [cel]. Grom 15%, nawalnica 35%, wyrok 100% HP celu.")
            return
        technique = self.normalize_description_query(words[0])
        query = words[1].strip() if len(words)>1 else ""
        mob = None
        if query:
            mob = self.server.world.find_mob(self.character.room_id, query)
        elif self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
        if not mob or not mob.alive or mob.room_id != self.character.room_id:
            await self.send("ADMIN CIOS: najpierw rozpocznij walke lub podaj zywego potwora z pokoju.")
            return
        template = _mob_catalog[mob.template_id]
        # No direct bypass of source boss prerequisites, party ownership or combat gates.
        allowed, reason = superboss_attack_gate_v11137(self, template)
        if not allowed:
            await self.send(reason)
            return
        if self.combat_mob_key != mob.key:
            await self.attack(query or template["name"])
            if self.combat_mob_key != mob.key or not mob.alive:
                return
        if not self.server.engagement_allowed(self, mob):
            await self.send(self.engagement_block_message(mob))
            return
        percent = {"grom": 15, "nawalnica": 35, "wyrok": 100}[technique]
        effective_hp = max(1, int(self.mob_effective_max_hp_v11330(mob, template)))
        damage = min(max(0, int(mob.hp)), max(1, effective_hp * percent // 100))
        mob.hp -= damage
        self._recap52_dealt = int(getattr(self, "_recap52_dealt", 0) or 0) + damage
        self.server.db.record_admin_action_v1224(
            self.server.db.account_name(self.master_account_id),
            "admin_cios_" + technique, mob.template_id,
        )
        await self.server.party_combat_broadcast(
            self,
            f"ADMIN {self.character.name}: {technique.upper()}! {damage} obrazen w "
            f"{template['name']}. Pozostalo HP {max(0, mob.hp)}.", detail="essential",
        )
        await self.send(
            f"ADMIN CIOS {technique.upper()}: {damage} obrazen. "
            f"{template['name']}: {max(0, mob.hp)} HP."
        )
        if mob.hp <= 0:
            await self.mob_defeated(mob)

