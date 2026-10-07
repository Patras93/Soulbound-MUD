# -*- coding: utf-8 -*-
"""Combat escape and player-death handling.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from events.contracts import PlayerDiedEvent
from systems.combat_profile_records import (
    death_cause_text_v11341,
    record_combat_profile_v11341,
)

class SessionCombatSurvivalMixin:
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
                self.skill_guard = 0
                self.skill_evade = False
                self.skill_evade_lockout_until = 0.0
                self.clear_skill_buffs()
                await self.send("Wycofujesz się z walki.")
                await self.server.party_combat_broadcast(
                    self, f"{self.character.name} wycofuje się z walki.", detail="normal"
                )

    async def die(self, killer):
                key = self.party_key()
                if key is not None and self.server.party_protectors.get(key) == self.account_id:
                    self.server.party_protectors.pop(key, None)
                    await self.server.party_nearby_broadcast(
                        self,
                        f"{self.character.name} pada; osłona drużyny zostaje wyłączona.",
                        exclude=[self],
                        detail="essential",
                        history_category="combat",
                    )
                if self.resting or self.rest_task:
                    await self.stop_rest(announce=False)
                _death_cause_v11341 = dict(
                    getattr(self, "_last_death_cause_v11341", {}) or {}
                )
                if (
                    _death_cause_v11341.get("killer")
                    and str(_death_cause_v11341.get("killer")).strip().casefold()
                    != str(killer or "").strip().casefold()
                ):
                    _death_cause_v11341 = {}

                # Prefer the exact mob that delivered the lethal action. In AoE/
                # multi-mob fights combat_mob_key can point at a different target.
                _cause_mob_key_v11341 = str(
                    _death_cause_v11341.get("mob_key") or ""
                ).strip()
                _killer_mob = (
                    self.server.world.mobs.get(_cause_mob_key_v11341)
                    if _cause_mob_key_v11341
                    else None
                )
                if _killer_mob is None and self.combat_mob_key:
                    _killer_mob = self.server.world.mobs.get(self.combat_mob_key)

                _killer_template_v11341 = None
                _cause_template_id_v11341 = str(
                    _death_cause_v11341.get("template_id") or ""
                ).strip()
                if _cause_template_id_v11341 in MOB_TEMPLATES:
                    _candidate_v11341 = MOB_TEMPLATES[_cause_template_id_v11341]
                    _candidate_name_v11341 = str(
                        _candidate_v11341.get("name") or _cause_template_id_v11341
                    )
                    if (
                        _candidate_name_v11341.casefold()
                        == str(killer or "").strip().casefold()
                    ):
                        _killer_template_v11341 = _candidate_v11341

                if (
                    _killer_template_v11341 is None
                    and _killer_mob
                    and _killer_mob.template_id in MOB_TEMPLATES
                ):
                    _candidate_v11341 = MOB_TEMPLATES[_killer_mob.template_id]
                    _candidate_name_v11341 = str(
                        _candidate_v11341.get("name") or _killer_mob.template_id
                    )
                    if (
                        _candidate_name_v11341.casefold()
                        == str(killer or "").strip().casefold()
                    ):
                        _killer_template_v11341 = _candidate_v11341

                if _killer_template_v11341 is not None:
                    record_combat_profile_v11341(
                        self.server.db,
                        self.account_id,
                        "worst_defeat",
                        _killer_template_v11341,
                    )
                self.server.release_all_engagements_for_session(self)
                if _killer_mob and _killer_mob.template_id in MOB_TEMPLATES:
                    _kt = MOB_TEMPLATES[_killer_mob.template_id]
                    _base = str(_kt.get("base_template") or _killer_mob.template_id)
                    _base_t = MOB_TEMPLATES.get(_base, _kt)
                    _stage = int(ROOMS.get(old_room if 'old_room' in locals() else self.character.room_id, {}).get("generator_level", _kt.get("generator_level", 1)) or 1)
                    _row = self.server.db.promote_nemesis_v029(
                        self.account_id, _base, _base_t.get("name", _kt.get("name", _base)), self.character.name, _stage, self.character.room_id
                    )
                    self.server.world.remove_v029_nemesis(self.account_id)
                    await self.send(f"NEMESIS POWSTAJE: {_row['nemesis_name']}. Ranga {int(_row['rank'])}. Wpisz nemesis po odrodzeniu.")
                self.combat_mob_key = None
                await self.stop_realtime_combat()
                self.skill_guard = 0
                self.skill_evade = False
                self.skill_evade_lockout_until = 0.0
                # v0.30.35: śmierć jest bezstratna. Nie kasuje waluty, przedmiotów,
                # EQ, progresji ani aktywnych 30-sekundowych buffów.
                self.character.deaths += 1
                self.server.db.add_lifetime_stat(self.account_id, "deaths", 1)
                old_room = self.character.room_id
                _death_room_name_v11341 = str(
                    ROOMS.get(old_room, {}).get("name") or old_room
                )
                _death_cause_text_v11341 = death_cause_text_v11341(
                    killer,
                    _death_cause_v11341,
                    _death_room_name_v11341,
                )
                self._last_death_cause_v11341 = {}
                self._incoming_attack_context_v11341 = {}
                self.current_hp = 0
                self.current_mana = 0
                self.server.db.save_character(self.character)
                await self.server.events.publish(
                    PlayerDiedEvent(session=self, killer=str(killer), room_id=str(old_room))
                )
                await self.server.broadcast_room(
                    old_room, f"{self.character.name} pada w walce.", exclude=self
                )
                try:
                    _dur=int(max(0.0,__import__("time").time()-float(getattr(self,"_recap52_start",__import__("time").time())))*1000)
                    self.server.db.conn.execute("INSERT INTO death_recaps_v03052(account_id,killer,room_id,damage_taken,duration_ms) VALUES(?,?,?,?,?)",(self.account_id,str(killer),str(old_room),int(getattr(self,"_recap52_taken",0)),_dur))
                    self.server.db.conn.execute("INSERT INTO combat_recaps_v03052(account_id,opponent,duration_ms,damage_dealt,damage_taken,healing,crits,skills_used,result) VALUES(?,?,?,?,?,?,?,?,?)",(self.account_id,str(killer),_dur,int(getattr(self,"_recap52_dealt",0)),int(getattr(self,"_recap52_taken",0)),int(getattr(self,"_recap52_heal",0)),int(getattr(self,"_recap52_crits",0)),int(getattr(self,"_recap52_skills",0)),"death"))
                    self.server.db.set_recap_summary_v0320(
                        self.account_id,
                        str(killer),
                        "Śmierć: " + _death_cause_text_v11341,
                        int(getattr(self,"_recap32_guard_saved",0)),
                        int(getattr(self,"_recap52_heal",0)),
                        "death",
                    )
                    self.server.db.add_combat_event_v0320(
                        self.account_id,
                        f"{killer} zadaje finalny cios. {_death_cause_text_v11341}. "
                        f"{self.character.name} ginie.",
                        "final",
                    )
                    self.server.db.conn.commit(); self._recap52_start=0
                except Exception as exc:
                    print(f"DEATH_RECAP_SAVE_ERROR: {type(exc).__name__}: {exc}", flush=True)
                await self.send(f"Pokonuje cię {killer}.")
                await self.send("Przyczyna śmierci: " + _death_cause_text_v11341 + ".")
                # Phoenix Egg: source grants Re-raise once and then disappears.
                # Soulbound reuses its existing full local revival state instead of
                # inventing a separate HP percentage.
                try:
                    if self.server.db.item_qty(self.account_id, "uoss_odin_unique_8") > 0:
                        self.server.db.remove_item(self.account_id, "uoss_odin_unique_8", 1)
                        self.current_hp = self.max_hp()
                        self.current_mana = self.max_mana()
                        self.server.db.save_character(self.character)
                        await self.send("Phoenix Egg pęka. Re-raise przywraca cię do walki; jajko znika.")
                        return
                except Exception as exc:
                    print(f"PHOENIX_EGG_RERAISE_ERROR: {type(exc).__name__}: {exc}", flush=True)
                await self.send(
                    "Śmierć nie powoduje utraty waluty, przedmiotów, EQ ani progresji. "
                    "Aktywne buffy zachowują pozostały czas działania."
                )

                # v1.13.43: każdy realny zgon bez Re-raise zostawia ciało
                # na 180 sekund. Globalny alarm podaje miejsce i dokładną
                # przyczynę, aby dowolny żywy gracz mógł dotrzeć i użyć
                # wskrzes <gracz> albo resp <gracz>.
                await self.begin_downed_v0371(killer, seconds=180)
                await self.server.broadcast_all(
                    f"ŚWIAT: {self.character.name} zginął. "
                    f"Miejsce: {_death_room_name_v11341}. "
                    f"Zabił lub przyczyna: {killer}. "
                    f"Szczegóły: {_death_cause_text_v11341}. "
                    f"Ratunek przez 180 sekund: wskrzes {self.character.name} "
                    f"albo resp {self.character.name}.",
                    history_category="system",
                )
                return

