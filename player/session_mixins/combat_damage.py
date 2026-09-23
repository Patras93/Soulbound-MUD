# -*- coding: utf-8 -*-
"""Damage and combat-consider calculations.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import math
import random

from core.progression_600 import CHARACTER_MAX_LEVEL
from data.mobs import MOB_TEMPLATES

class SessionCombatDamageMixin:
    def player_damage(self):
                c = self.character

                if c.class_type == "physical":
                    # Siła odpowiada za atak fizyczny.
                    base_damage = c.soul_power() + self.physical_power() + random.randint(-3, 4)
                    return max(
                        1,
                        int(
                            round(
                                base_damage
                                * c.class_physical_damage_multiplier()
                                * c.racial_physical_damage_multiplier()
                                * c.racial_all_damage_multiplier()
                                * self.total_set_damage_multiplier()
                                * self.equipment_damage_multiplier("physical")
                            )
                        )
                    )

                # v0.30.17: magiczny autoatak Bronią Duszy skaluje się z Inteligencją,
                # nie z Siłą. Soul Power jest rdzeniem broni, spell_power wkładem INT.
                if self.current_mana >= 4:
                    self.current_mana -= 4
                    base_damage = (
                        c.soul_power()
                        + self.spell_power()
                        + random.randint(-3, 4)
                    )
                    return max(
                        1,
                        int(
                            round(
                                base_damage
                                * c.class_magic_damage_multiplier()
                                * c.racial_magic_damage_multiplier()
                                * c.racial_all_damage_multiplier()
                                * self.total_set_damage_multiplier()
                                * self.equipment_damage_multiplier("magic")
                            )
                        )
                    )

                # Bez Many klasa magiczna nadal może uderzyć Bronią Duszy.
                # v0.8.65: taki słabszy atak uruchamia Skupienie Broni Duszy i
                # odzyskuje niewielką część Many. Zapobiega to wielominutowemu
                # utknięciu magicznych klas na słabym autoataku w długich walkach,
                # ale nie daje darmowej regeneracji dopóki Mana nie jest wyczerpana.
                base_damage = (
                    c.soul_power()
                    + self.spell_power() // 2
                    + random.randint(-2, 2)
                )
                max_mana = self.max_mana()
                mana_focus = min(40, max(4, int(round(max_mana * 0.05))))
                self.current_mana = min(max_mana, self.current_mana + mana_focus)
                self._last_mana_focus_gain = mana_focus
                return max(
                        1,
                        int(
                            round(
                                base_damage
                                * c.class_magic_damage_multiplier()
                                * c.racial_magic_damage_multiplier()
                                * c.racial_all_damage_multiplier()
                                * self.total_set_damage_multiplier()
                            )
                        )
                    )

    def consider_player_expected_hit(self):
                c = self.character

                if c.class_type == "physical":
                    base_damage = (
                        c.soul_power()
                        + self.physical_power()
                        + 0.5
                    )
                    value = (
                        base_damage
                        * c.class_physical_damage_multiplier()
                        * c.racial_physical_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                        * self.equipment_damage_multiplier("physical")
                    )
                elif self.current_mana >= 4:
                    base_damage = (
                        c.soul_power()
                        + self.spell_power()
                        + 0.5
                    )
                    value = (
                        base_damage
                        * c.class_magic_damage_multiplier()
                        * c.racial_magic_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                        * self.equipment_damage_multiplier("magic")
                    )
                else:
                    base_damage = (
                        c.soul_power()
                        + self.spell_power() / 2.0
                    )
                    value = (
                        base_damage
                        * c.class_magic_damage_multiplier()
                        * c.racial_magic_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                        * self.equipment_damage_multiplier("magic")
                    )

                # Średnia wartość uwzględnia prawdopodobieństwo krytyka,
                # ale nie zużywa many i nie wykonuje żadnego rzutu RNG.
                crit_factor = (
                    1.0
                    + self.critical_chance()
                    * (self.critical_multiplier() - 1.0)
                )
                return max(1.0, float(value) * crit_factor)

    def consider_enemy_expected_hit(self, template):
                damage_type = template.get("damage_type", "physical")
                raw = max(1.0, float(template.get("damage", 1)))

                if damage_type == "magic":
                    reduction = float(self.magic_defense())
                else:
                    reduction = float(self.defense())

                incoming = max(1.0, raw - reduction)

                if damage_type == "physical":
                    physical_race_percent = (
                        self.character.racial_physical_damage_reduction_percent()
                    )
                    incoming *= max(
                        0.0,
                        1.0 - physical_race_percent / 100.0,
                    )

                racial_percent = (
                    self.character.racial_damage_reduction_percent()
                )
                incoming *= max(
                    0.0,
                    1.0 - racial_percent / 100.0,
                )

                class_percent = (
                    self.character.class_damage_reduction_percent()
                )
                incoming *= max(
                    0.0,
                    1.0 - class_percent / 100.0,
                )

                # Unik obniża średnie obrażenia w dłuższej walce.
                incoming *= max(
                    0.0,
                    1.0 - self.dodge_chance(),
                )

                return max(1.0, incoming)

    def consider_rating(self, mob, template):
                player_hit = self.consider_player_expected_hit() / max(1.0,self.v0210_world_tier_multipliers()["effective_hp"])
                enemy_hit = self.consider_enemy_expected_hit(template) * self.v0210_enemy_damage_multiplier()

                mob_hp = max(1, int(mob.hp))
                player_hp = max(1, int(self.current_hp))

                turns_to_kill = mob_hp / player_hit
                turns_to_die = player_hp / enemy_hit
                ratio = turns_to_die / max(0.01, turns_to_kill)

                # Boss mechanics are deliberately treated as extra danger.
                if template.get("boss_mechanic"):
                    ratio *= 0.82
                if (
                    template.get("crypt_boss")
                    or template.get("astral_boss")
                    or template.get("mythic_crypt_boss")
                    or template.get("mythic_astral_boss")
                ):
                    ratio *= 0.90
                if template.get("world_boss"):
                    ratio *= 0.90

                if ratio >= 3.0:
                    label = "bardzo słaby"
                    advice = "Powinien być dla ciebie łatwy."
                elif ratio >= 1.9:
                    label = "słaby"
                    advice = "Masz wyraźną przewagę."
                elif ratio >= 1.25:
                    label = "korzystny"
                    advice = "Masz przewagę, ale przeciwnik może zranić."
                elif ratio >= 0.80:
                    label = "porównywalny"
                    advice = "Walka może być wyrównana."
                elif ratio >= 0.50:
                    label = "niebezpieczny"
                    advice = "Przeciwnik ma przewagę. Przygotuj leczenie lub skille."
                elif ratio >= 0.28:
                    label = "bardzo niebezpieczny"
                    advice = "Ryzyko śmierci jest wysokie."
                else:
                    label = "śmiertelnie groźny"
                    advice = "Bez mocnego przygotowania lepiej go teraz nie atakować."

                return {
                    "label": label,
                    "advice": advice,
                    "player_hit": max(1, int(round(player_hit))),
                    "enemy_hit": max(1, int(round(enemy_hit))),
                    "turns_to_kill": max(1, int(math.ceil(turns_to_kill))),
                    "turns_to_die": max(1, int(math.ceil(turns_to_die))),
                }

    async def consider_mob(self, query):
                self.server.world.refresh()
                mobs = self.server.world.room_mobs(
                    self.character.room_id
                )

                if not mobs:
                    await self.send(
                        "Nie ma tutaj przeciwnika do oceny."
                    )
                    return

                raw = str(query or "").strip()
                if not raw:
                    if len(mobs) == 1:
                        mob = mobs[0]
                    else:
                        await self.send(
                            "Użycie: consider <mob>. "
                            "Przeciwnicy tutaj: "
                            + ", ".join(
                                MOB_TEMPLATES[m.template_id]["name"]
                                for m in mobs
                            )
                            + "."
                        )
                        return
                else:
                    # v0.8.44: CON używa dokładnie tego samego uniwersalnego
                    # resolvera żywych/zabijalnych mobów co k <mob>. Dzięki temu
                    # działają fragmenty nazw, brak polskich znaków i numer wystąpienia.
                    mob = self.server.world.find_mob(
                        self.character.room_id,
                        raw,
                    )
                    if not mob:
                        npc = self.protected_friendly_npc(raw)
                        if npc:
                            await self.send(
                                f"{npc['name']} jest pokojowym i chronionym NPC-em. "
                                "Komenda con działa tylko na przeciwników, których da się zabić."
                            )
                        else:
                            await self.send(
                                "Nie widzę tutaj takiego żywego przeciwnika do oceny. "
                                "Użyj con <mob>, np. con goblin albo con 2 goblin."
                            )
                        return

                template = MOB_TEMPLATES[mob.template_id]
                rating = self.consider_rating(mob, template)
                damage_type = (
                    "magiczne"
                    if template.get("damage_type") == "magic"
                    else "fizyczne"
                )

                await self.send(
                    f"CONSIDER: {template['name']}."
                )
                await self.send(
                    f"Ocena zagrożenia: {rating['label']}."
                )
                await self.send(
                    f"Przeciwnik ma {max(0, mob.hp)} z "
                    f"{template['max_hp']} HP. "
                    f"Bazowy atak: {template['damage']}. "
                    f"Typ obrażeń: {damage_type}."
                )
                await self.send(
                    f"Szacowany twój normalny cios: około "
                    f"{rating['player_hit']}. "
                    f"Szacowane otrzymane obrażenia na odpowiedź: około "
                    f"{rating['enemy_hit']}."
                )
                await self.send(
                    f"Orientacyjnie: około {rating['turns_to_kill']} twoich "
                    f"normalnych trafień do pokonania przeciwnika i około "
                    f"{rating['turns_to_die']} jego skutecznych odpowiedzi "
                    f"do pokonania ciebie przy obecnym HP."
                )

                elite_text = template.get(
                    "elite_affix_text"
                )
                if elite_text:
                    await self.send(
                        f"Elitarny affix: {elite_text}"
                    )

                if template.get("rare_troll"):
                    await self.send(
                        "Rzadki wariant trolla."
                    )

                mechanic = template.get("boss_mechanic_text")
                if mechanic:
                    await self.send(
                        f"Mechanika bossa: {mechanic}"
                    )
                elif template.get("boss_mechanic"):
                    await self.send(
                        "To boss ze specjalną mechaniką. "
                        "Ocena consider jest orientacyjna."
                    )

                xp_profile = self.dynamic_kill_xp_profile(template, room_id=self.character.room_id)
                await self.send(
                    f"EXP przy obecnej sile postaci: {xp_profile['label']}, "
                    f"mnożnik x{xp_profile['multiplier']:.2f} dla EXP statów, Soul XP i Class XP. "
                    f"Siła postaci {xp_profile['power']}/{CHARACTER_MAX_LEVEL}, siła przeciwnika około {xp_profile['target']}/{CHARACTER_MAX_LEVEL}."
                )
                await self.send(rating["advice"])
                await self.send(
                    "Consider jest tylko oceną: nie rozpoczyna walki "
                    "i nie uruchamia automatycznej pętli walki."
                )

