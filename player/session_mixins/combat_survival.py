# -*- coding: utf-8 -*-
"""Combat escape and player-death handling.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from events.contracts import PlayerDiedEvent

class SessionCombatSurvivalMixin:
    async def flee(self):
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
                _killer_mob = self.server.world.mobs.get(self.combat_mob_key) if self.combat_mob_key else None
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
                    self.server.db.set_recap_summary_v0320(self.account_id,str(killer),f"Śmierć od: {killer}",int(getattr(self,"_recap32_guard_saved",0)),int(getattr(self,"_recap52_heal",0)),"death")
                    self.server.db.add_combat_event_v0320(self.account_id,f"{killer} zadaje finalny cios. {self.character.name} ginie.","final")
                    self.server.db.conn.commit(); self._recap52_start=0
                except Exception:
                    pass
                await self.send(f"Pokonuje cię {killer}.")
                await self.send(
                    "Śmierć nie powoduje utraty waluty, przedmiotów, EQ ani progresji. "
                    "Aktywne buffy zachowują pozostały czas działania."
                )

                # v0.37.1: jeśli w tym samym pokoju stoi żywy członek drużyny,
                # nie teleportuj natychmiast. Daj 60 sekund na lokalne wskrzeszenie.
                revivers = self.party_revive_candidates_v0371()
                if revivers:
                    await self.begin_downed_v0371(killer, seconds=60)
                    await self.server.party_nearby_broadcast(
                        self,
                        f"{self.character.name} jest powalony. Użyj: wskrzes {self.character.name}. Czas: 60 sekund.",
                        exclude=[self],
                        detail="essential",
                        history_category="combat",
                    )
                    return

                # Bez żywego członka drużyny obok zachowujemy dawny natychmiastowy respawn.
                self.character.room_id = "temple"
                self.current_hp = self.max_hp()
                self.current_mana = self.max_mana()
                self.server.db.save_character(self.character)
                await self.server.broadcast_room(
                    "temple", f"{self.character.name} odradza się w Świątyni Odrodzenia.", exclude=self
                )
                await self.send("Twoja dusza odradza się w Świątyni Odrodzenia.")
                await self.look()

