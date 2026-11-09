# -*- coding: utf-8 -*-
"""Oryginalne metody wydzielone w v109 bez zmiany algorytmow."""
# -*- coding: utf-8 -*-
"""Combat escape and player-death handling.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from events.contracts import PlayerDiedEvent
from systems.monster_magic import monster_magic_clear_v1151
from systems.combat_profile_records import (
    death_cause_text_v11341,
    record_combat_profile_v11341,
)


class CombatEscapeV109Mixin:
    async def flee(self):
                if self.combat_mob_key:
                    _mob=self.server.world.mobs.get(self.combat_mob_key)
                    _template=MOB_TEMPLATES.get(_mob.template_id,{}) if _mob else {}
                    if _template.get("uoss_unique_superboss_key")=="serpentarius":
                        await self.send("Serpentarius zamyka próbę. Nie możesz użyć flee po rozpoczęciu walki.")
                        return
                if not self.combat_mob_key:
                    await self.send("Nie jesteś w walce.")
                    return
                if self.server.party_protector_session(self.account_id) is self:
                    await self.stop_party_protection(announce=True)
                self.server.release_all_engagements_for_session(self)
                self.combat_mob_key = None
                await self.stop_realtime_combat()
                monster_magic_clear_v1151(self)
                self.skill_guard = 0
                self.skill_evade = False
                self.skill_evade_lockout_until = 0.0
                self.clear_skill_buffs()
                await self.send("Wycofujesz się z walki.")
                await self.server.party_combat_broadcast(
                    self, f"{self.character.name} wycofuje się z walki.", detail="normal"
                )

