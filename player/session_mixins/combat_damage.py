# -*- coding: utf-8 -*-
"""Damage and combat-consider calculations.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import math
import random

from core.progression_600 import CHARACTER_MAX_LEVEL
from core.player_math import (
    character_attribute_power,
    character_offensive_build_multiplier,
)
from systems.equipment_crafting import class_equipment_base_stat_pair
from systems.adaptive_combat import (
    adaptive_combat_rank_v11330,
    adaptive_reward_multiplier_v11330,
    adaptive_target_incoming_fraction_v11330,
    adaptive_target_max_hp_v11330,
)
from data.mobs import MOB_TEMPLATES

MEC_COMBAT_MASTERY_DAMAGE_MULTIPLIER_V1124 = 1.20

class SessionCombatDamageMixin:
    def adaptive_party_members_v11330(self, mob=None):
                room_id = (
                    getattr(mob, "room_id", None)
                    or (self.character.room_id if self.character else None)
                )
                members = self.server.party_sessions(
                    self.account_id, same_room=room_id
                )
                members = [
                    member for member in members
                    if member and not member.closed and member.character
                    and member.current_hp > 0
                ]
                return members or [self]

    def adaptive_member_dps_v11330(self, member):
                try:
                    per_action = max(1.0, float(member.consider_player_expected_hit()))
                    hits = max(1, int(member.basic_attack_hit_count_v11196()))
                    interval = max(0.35, float(member.player_action_interval_v11154()))
                    # consider() intentionally omits some late Soul Weapon/skill layers.
                    # A modest factor keeps the scaler ahead of auto-queue burst without
                    # turning normal mobs into pure HP walls.
                    return max(1.0, per_action * hits * 1.30 / interval)
                except Exception:
                    return 1.0

    def mob_effective_max_hp_v11330(self, mob, template=None):
                if mob is None:
                    return 1
                template = template or MOB_TEMPLATES.get(mob.template_id, {})
                return max(
                    1,
                    int(
                        getattr(mob, "adaptive_max_hp_v11330", 0)
                        or template.get("max_hp", 1)
                        or 1
                    ),
                )

    def apply_adaptive_mob_scale_v11330(self, mob):
                if not mob or not mob.alive or not self.character:
                    return None
                template = MOB_TEMPLATES.get(mob.template_id, {})
                if not isinstance(template, dict) or template.get("training_dummy"):
                    return None

                members = self.adaptive_party_members_v11330(mob)
                party_dps = sum(
                    self.adaptive_member_dps_v11330(member)
                    for member in members
                )
                base_max = max(1, int(template.get("max_hp", 1) or 1))
                target_max = adaptive_target_max_hp_v11330(
                    base_max, party_dps, template
                )
                old_max = max(
                    base_max,
                    int(getattr(mob, "adaptive_max_hp_v11330", 0) or base_max),
                )

                # Never shrink an active fight when a member leaves or loses buffs.
                if target_max > old_max:
                    damage_already_done = max(0, old_max - max(0, int(mob.hp)))
                    mob.hp = max(1, target_max - damage_already_done)
                    old_max = target_max

                mob.adaptive_max_hp_v11330 = old_max
                mob.adaptive_hp_multiplier_v11330 = round(
                    old_max / float(base_max), 6
                )
                mob.adaptive_party_size_v11330 = len(members)
                mob.adaptive_party_dps_v11330 = round(float(party_dps), 3)
                mob.adaptive_rank_v11330 = adaptive_combat_rank_v11330(template)
                mob.adaptive_reward_multiplier_v11330 = (
                    adaptive_reward_multiplier_v11330(base_max, old_max)
                )
                return {
                    "max_hp": old_max,
                    "base_max_hp": base_max,
                    "party_size": len(members),
                    "party_dps": party_dps,
                    "hp_multiplier": mob.adaptive_hp_multiplier_v11330,
                    "reward_multiplier": mob.adaptive_reward_multiplier_v11330,
                    "rank": mob.adaptive_rank_v11330,
                }

    def adaptive_enemy_damage_multiplier_v11330(self, mob, template=None):
                if not mob or not self.character:
                    return 1.0
                template = template or MOB_TEMPLATES.get(mob.template_id, {})
                if not isinstance(template, dict) or template.get("training_dummy"):
                    return 1.0

                party_size = max(
                    1, int(getattr(mob, "adaptive_party_size_v11330", 1) or 1)
                )
                desired = max(
                    1.0,
                    float(self.max_hp())
                    * adaptive_target_incoming_fraction_v11330(
                        template, party_size
                    ),
                )
                base_raw = max(1, int(template.get("damage", 1) or 1))
                base_expected = max(
                    1.0, float(self.consider_enemy_expected_hit(template))
                )
                if base_expected >= desired:
                    return 1.0

                # Defense is nonlinear because flat mitigation is capped relative
                # to raw damage. Search the raw hit that produces the intended
                # post-defense pressure for THIS target instead of guessing.
                low = float(base_raw)
                high = max(low * 2.0, 2.0)
                probe = dict(template)
                for _ in range(24):
                    probe["damage"] = max(1, int(round(high)))
                    if self.consider_enemy_expected_hit(probe) >= desired:
                        break
                    high *= 2.0
                for _ in range(18):
                    mid = (low + high) / 2.0
                    probe["damage"] = max(1, int(round(mid)))
                    if self.consider_enemy_expected_hit(probe) < desired:
                        low = mid
                    else:
                        high = mid
                return max(1.0, min(1_000_000_000.0, high / float(base_raw)))

    def mec_combat_mastery_active_v1124(self):
                """Selected Mec inherent adapted to Soulbound's one-Soul-Weapon model."""
                c = self.character
                if not c or c.class_name != "Mec":
                    return False
                # Source explicitly says Combat Mastery does not work unarmed.
                if not str(getattr(c, "soul_weapon", "") or "").strip():
                    return False
                return self.job_ability_selected(
                    "inherent", "v0319_mec_combat_mastery"
                )

    def basic_attack_inherent_multiplier_v1124(self):
                if self.mec_combat_mastery_active_v1124():
                    return MEC_COMBAT_MASTERY_DAMAGE_MULTIPLIER_V1124
                return 1.0

    def basic_attack_build_v11196(self):
                """Return (power, raw stat, channel) for the active class build."""
                c = self.character
                flat = self.equipment_flat_power_totals_v11187()
                if c.class_type == "physical":
                    # UOSS Combat Mastery only works with a purely STR melee weapon.
                    # Soulbound has one persistent Mec Soul Weapon instead of separate
                    # axe/claw/greatsword/etc. slots, so selecting Combat Mastery makes
                    # the ordinary Mec Soul Weapon attack use its melee/STR role.
                    if self.mec_combat_mastery_active_v1124():
                        raw_stat = max(1, int(self.effective_strength()))
                        power = self.physical_power()
                    else:
                        primary, _secondary = class_equipment_base_stat_pair(c.class_name)
                        if primary == "dexterity":
                            raw_stat = max(1, int(self.effective_dexterity()))
                            power = (
                                character_attribute_power(
                                    c.character_level, raw_stat
                                )
                                + int(flat["attack"])
                                + int(flat["weapon_power"])
                            )
                        else:
                            raw_stat = max(1, int(self.effective_strength()))
                            power = self.physical_power()
                    return max(1, int(power)), raw_stat, "physical"

                raw_stat = max(1, int(self.effective_intelligence()))
                return max(1, int(self.spell_power())), raw_stat, "magic"

    def player_damage(self):
                c = self.character

                if c.class_type == "physical":
                    build_power, build_stat, _channel = self.basic_attack_build_v11196()
                    base_damage = c.soul_power() + build_power + random.randint(-3, 4)
                    build_multiplier = character_offensive_build_multiplier(build_stat)
                    return max(
                        1,
                        int(
                            round(
                                base_damage
                                * build_multiplier
                                * c.class_physical_damage_multiplier()
                                * c.racial_physical_damage_multiplier()
                                * c.racial_all_damage_multiplier()
                                * self.total_set_damage_multiplier()
                                * self.equipment_damage_multiplier("physical")
                                * self.basic_attack_inherent_multiplier_v1124()
                            )
                        )
                    )

                # v0.30.17: magiczny autoatak Bronią Duszy skaluje się z Inteligencją,
                # nie z Siłą. Soul Power jest rdzeniem broni, spell_power wkładem INT.
                if self.current_mana >= 4:
                    self.current_mana -= 4
                    build_power, build_stat, _channel = self.basic_attack_build_v11196()
                    base_damage = (
                        c.soul_power()
                        + build_power
                        + random.randint(-3, 4)
                    )
                    build_multiplier = character_offensive_build_multiplier(build_stat)
                    return max(
                        1,
                        int(
                            round(
                                base_damage
                                * build_multiplier
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
                build_power, build_stat, _channel = self.basic_attack_build_v11196()
                base_damage = (
                    c.soul_power()
                    + build_power // 2
                    + random.randint(-2, 2)
                )
                build_multiplier = character_offensive_build_multiplier(build_stat)
                max_mana = self.max_mana()
                mana_focus = min(40, max(4, int(round(max_mana * 0.05))))
                self.current_mana = min(max_mana, self.current_mana + mana_focus)
                self._last_mana_focus_gain = mana_focus
                return max(
                        1,
                        int(
                            round(
                                base_damage
                                * build_multiplier
                                * c.class_magic_damage_multiplier()
                                * c.racial_magic_damage_multiplier()
                                * c.racial_all_damage_multiplier()
                                * self.total_set_damage_multiplier()
                            )
                        )
                    )

    def consider_player_expected_hit(self):
                c = self.character
                build_power, build_stat, _channel = self.basic_attack_build_v11196()
                build_multiplier = character_offensive_build_multiplier(build_stat)

                if c.class_type == "physical":
                    base_damage = (
                        c.soul_power()
                        + build_power
                        + 0.5
                    )
                    value = (
                        base_damage
                        * build_multiplier
                        * c.class_physical_damage_multiplier()
                        * c.racial_physical_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                        * self.equipment_damage_multiplier("physical")
                        * self.basic_attack_inherent_multiplier_v1124()
                    )
                elif self.current_mana >= 4:
                    base_damage = (
                        c.soul_power()
                        + build_power
                        + 0.5
                    )
                    value = (
                        base_damage
                        * build_multiplier
                        * c.class_magic_damage_multiplier()
                        * c.racial_magic_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                        * self.equipment_damage_multiplier("magic")
                    )
                else:
                    base_damage = (
                        c.soul_power()
                        + build_power / 2.0
                    )
                    value = (
                        base_damage
                        * build_multiplier
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

                # Match real combat: flat Defense can strongly reward equipment,
                # but cannot erase enemy attacks completely. Bosses retain the
                # stricter 60% cap; ordinary enemies can be reduced by up to 75%.
                is_boss = bool(
                    template.get("boss")
                    or template.get("world_boss")
                    or template.get("crypt_boss")
                    or template.get("mythic_crypt_boss")
                    or template.get("astral_boss")
                    or template.get("mythic_astral_boss")
                    or template.get("boss_mechanic")
                )
                defense_cap_ratio = 0.60 if is_boss else 0.75
                reduction = min(reduction, raw * defense_cap_ratio)
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

