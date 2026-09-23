# -*- coding: utf-8 -*-
"""HP, level, XP, score, stats and Soul profile."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
from core.bootstrap_economy_professions import (
    SOUL_MILESTONE_GUARDIAN_REDUCTION,
    SOUL_MILESTONE_NAMES,
    SOUL_MILESTONE_SPECIALIZATION_BONUS,
    SOUL_MILESTONE_TIERS,
    SOUL_TRIAL_QUEST_IDS,
    currency_reading_text,
    soul_trial_difficulty_band,
    soul_weapon_trait_for_tier,
    soul_weapon_trait_totals,
    stat_quality_label,
)
from core.classes_skills import ROOMS
from core.progression_600 import (
    CHARACTER_MAX_LEVEL,
    CLASS_MASTERY_MAX_LEVEL,
    SOUL_MAX_LEVEL,
    SOUL_MAX_TIER,
    SOUL_TIER_THRESHOLDS,
    SOUL_WEAPON_MASTERY_MAX_LEVEL,
)
from core.progression_resources import character_xp_to_next
from systems.content_registry import QUESTS


class SessionCharacterProfileMixin:

    async def show_hp(self):
            """Krótki stan zasobów bez podwójnego nagłówka HP pod NVDA."""
            await self.send(f"HP: {self.current_hp} z {self.max_hp()}.")
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")

    async def show_character_level(self):
            """Krótki Poziom postaci 1-600, niezależny od Soul Levelu."""
            c = self.character
            if c.character_level >= CHARACTER_MAX_LEVEL:
                await self.send(f"Poziom postaci: {CHARACTER_MAX_LEVEL}/{CHARACTER_MAX_LEVEL}. Maksymalny poziom.")
                return
            needed = character_xp_to_next(c.character_level)
            missing = max(0, int(needed) - int(c.character_xp))
            await self.send(
                f"Poziom postaci: {c.character_level}/{CHARACTER_MAX_LEVEL}. "
                f"EXP {c.character_xp} z {needed}. Brakuje {missing} EXP do Levelu {c.character_level + 1}."
            )

    async def show_character_xp(self):
            """Stan EXP postaci z dokładną liczbą brakującą do następnego Levelu."""
            c = self.character
            if c.character_level >= CHARACTER_MAX_LEVEL:
                await self.send(f"EXP postaci: maksimum. Poziom {CHARACTER_MAX_LEVEL}/{CHARACTER_MAX_LEVEL}.")
                return
            needed = character_xp_to_next(c.character_level)
            missing = max(0, int(needed) - int(c.character_xp))
            await self.send(
                f"EXP postaci: {c.character_xp} z {needed}. "
                f"Brakuje {missing} EXP do Levelu {c.character_level + 1}."
            )

    async def show_score(self):
            """Czytelne podsumowanie wszystkich osi Generator Core."""
            c = self.character
            active_classes = self.active_class_names()
            room = ROOMS.get(c.room_id, {})

            await self.send("SCORE")
            await self.send(f"Postać: {c.name}.")
            await self.send(f"Rasa: {c.race}.")
            await self.send(f"Klasa główna: {c.class_name}.")
            await self.send(f"Poziom postaci: {c.character_level}/{CHARACTER_MAX_LEVEL}. EXP: {c.character_xp} z {character_xp_to_next(c.character_level) if c.character_level < CHARACTER_MAX_LEVEL else 0}.")
            for class_name in active_classes:
                await self.send(
                    f"Biegłość {class_name}: {self.class_mastery_level(class_name)}/{CLASS_MASTERY_MAX_LEVEL}."
                )
            await self.send(f"Broń Duszy: {c.soul_weapon}.")
            await self.send(f"Soul Level: {c.soul_level}/{SOUL_MAX_LEVEL}.")
            await self.send(f"Soul Tier: {c.soul_tier}/{SOUL_MAX_TIER}.")
            await self.send(f"Soul Weapon Mastery: {c.soul_weapon_mastery_level}/{SOUL_WEAPON_MASTERY_MAX_LEVEL}. XP: {c.soul_weapon_mastery_xp} z {c.soul_weapon_mastery_xp_to_next() if c.soul_weapon_mastery_level < SOUL_WEAPON_MASTERY_MAX_LEVEL else 0}.")
            await self.send(f"HP: {self.current_hp} z {self.max_hp()}.")
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
            await self.send(f"Siła: {self.effective_strength()}.")
            await self.send(f"Zręczność: {self.effective_dexterity()}.")
            await self.send(f"Kondycja: {self.effective_constitution()}.")
            await self.send(f"Inteligencja: {self.effective_intelligence()}.")
            await self.send(f"Siła Woli: {self.effective_willpower()}.")
            await self.send(f"Charyzma: {c.charisma}.")
            await self.send(
                "Portfel: "
                + currency_reading_text(
                    c.silver, c.gold, c.mithril,
                    full_names=True, include_zero=True,
                )
                + "."
            )
            await self.send(f"Lokacja: {room.get('name') or 'Nieznana lokacja'}.")
            await self.send(f"Strefa: {room.get('zone', 'brak')}.")
            area = self.exp_area_for_room(c.room_id)
            if area:
                label, target, power = self.exp_area_dynamic_threat(area, room_id=c.room_id)
                await self.send(f"Ocena terenu dla tej postaci: {label}.")
                await self.send(
                    f"Orientacyjna siła progresji: {power}/{CHARACTER_MAX_LEVEL}. Próg terenu: {target}/{CHARACTER_MAX_LEVEL}."
                )
            else:
                await self.send(
                    f"Orientacyjna siła progresji: {self.character_progression_power()}/{CHARACTER_MAX_LEVEL}."
                )
            await self.send("Wszystkie główne osie progresji 1-600 korzystają z Generator Core.")

    async def show_stats(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły",
                "details", "mechanika",
            )
            c = self.character
            bonuses = self.equipment_bonus_totals()
            active_classes = self.active_class_names()

            if not detailed:
                await self.send("STATY")
                await self.send(f"Postać: {c.name}.")
                await self.send(f"Rasa: {c.race}.")
                await self.send(f"Klasa główna: {c.class_name}.")
                await self.send(f"Aktywne klasy: {', '.join(active_classes)}.")
                stat_values = (
                    ("strength", "Siła", c.strength, self.effective_strength()),
                    ("dexterity", "Zręczność", c.dexterity, self.effective_dexterity()),
                    ("constitution", "Kondycja", c.constitution, self.effective_constitution()),
                    ("intelligence", "Inteligencja", c.intelligence, self.effective_intelligence()),
                    ("willpower", "Siła Woli", c.willpower, self.effective_willpower()),
                    ("charisma", "Charyzma", c.charisma, c.charisma),
                )
                for stat_key, label, base_value, effective_value in stat_values:
                    effective_text = (
                        f" Efektywna {effective_value}."
                        if effective_value != base_value else ""
                    )
                    await self.send(
                        f"{label}: {base_value} — {stat_quality_label(base_value)}."
                        f"{effective_text} EXP {c.stat_progress_for(stat_key)} z "
                        f"{c.stat_growth_threshold_for(stat_key)}."
                    )
                await self.send(f"HP: {self.current_hp} z {self.max_hp()}.")
                await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                await self.send(f"Obrona fizyczna: {self.defense()}.")
                await self.send(f"Obrona magiczna: {self.magic_defense()}.")
                await self.send(f"Atak fizyczny: {self.physical_power()}.")
                await self.send(f"Moc czarów: {self.spell_power() if self.max_mana() > 0 else 0}.")
                await self.send(f"Unik: {int(self.dodge_chance() * 100)} procent.")
                await self.send(f"Krytyk: {int(round(self.critical_chance() * 100))} procent.")
                await self.send("Każda statystyka ma własny, niezależny licznik EXP.")
                await self.send("Wpisz staty info po pełne szczegóły albo help staty po pomoc.")
                return

            await self.send("STATY INFO")
            await self.send("Soulbound nie ma levelu ani XP postaci. Każda statystyka rozwija się osobno.")
            stat_rows = (
                ("strength", "Siła", c.strength, self.effective_strength(), bonuses["strength"]),
                ("dexterity", "Zręczność", c.dexterity, self.effective_dexterity(), bonuses["dexterity"]),
                ("constitution", "Kondycja", c.constitution, self.effective_constitution(), bonuses["constitution"]),
                ("intelligence", "Inteligencja", c.intelligence, self.effective_intelligence(), bonuses["intelligence"]),
                ("willpower", "Siła Woli", c.willpower, self.effective_willpower(), bonuses["willpower"]),
                ("charisma", "Charyzma", c.charisma, c.charisma, 0),
            )
            for stat_key, label, base, effective, gear_bonus in stat_rows:
                await self.send(f"{label}: baza {base} — {stat_quality_label(base)}.")
                if stat_key != "charisma":
                    await self.send(f"{label}: efektywna {effective}. Bonus EQ i klejnotów +{gear_bonus}.")
                else:
                    await self.send(f"{label}: efektywna {effective}.")
                await self.send(
                    f"{label}: EXP {c.stat_progress_for(stat_key)} z "
                    f"{c.stat_growth_threshold_for(stat_key)} do następnego wzrostu."
                )
            await self.send(f"HP: {self.current_hp} z {self.max_hp()}. Bonus EQ +{bonuses['hp']}.")
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}. Bonus EQ +{bonuses['mana']}.")
            await self.send(f"Obrona fizyczna: {self.defense()}.")
            await self.send(f"Obrona magiczna: {self.magic_defense()}.")
            await self.send(f"Szybkość: {self.speed()}.")
            await self.send(f"Krytyk: {int(round(self.critical_chance() * 100))} procent.")
            await self.send(f"Mnożnik krytyka: {int(self.critical_multiplier() * 100)} procent.")
            await self.send(f"Unik: {int(self.dodge_chance() * 100)} procent.")
            await self.send("Kondycja zwiększa maksymalne HP każdej klasy.")
            await self.send("Inteligencja zwiększa maksymalną Manę każdej klasy.")
            await self.send("Zręczność zwiększa szybkość, unik i krytyki każdej klasy.")
            await self.send(
                "Siła zwiększa obrażenia fizyczne i daje 25 procent swojego wpływu "
                "jako wtórne skalowanie magicznych skilli i spelli."
            )
            await self.send(f"Pasyw rasy {c.race}: {c.racial_passive_text()}.")
            for class_name in active_classes:
                await self.send(f"Pasyw klasy {class_name}: {c.class_passive_text_for(class_name)}.")
            await self.send(f"Bonus Broni Duszy klasy głównej: {c.soul_weapon_class_bonus_text()}.")
            await self.send(self.crypt_set_bonus_text())
            await self.send(self.astral_set_bonus_text())
            for line in self.class_set_status_lines():
                await self.send(line)
            await self.send(f"Rabat sklepowy z Charyzmy: {c.shop_discount_percent()} procent.")
            await self.send(f"Limit drużyny jako lider: {c.party_capacity()}.")

    def soul_milestone_text(self, tier):
            tier = int(tier)
            if tier not in SOUL_MILESTONE_TIERS:
                return ""
            name = SOUL_MILESTONE_NAMES[tier]
            c = self.character
            if c.class_name == "Łotrzyk":
                damage = c.soul_weapon_rogue_damage_bonus_percent()
                dodge = int(round(c.soul_weapon_dodge_bonus() * 100))
                effect = (
                    f"specjalizacja Łotrzyka: obrażenia fizyczne Broni Duszy "
                    f"+{damage} procent, unik z Broni Duszy +{dodge} pp"
                )
            elif c.class_name == "Strażnik":
                amount = SOUL_MILESTONE_GUARDIAN_REDUCTION[tier]
                effect = f"dodatkowa redukcja obrażeń +{amount} procent"
            else:
                amount = SOUL_MILESTONE_SPECIALIZATION_BONUS[tier]
                effect = f"dodatkowa specjalizacja Broni Duszy +{amount} procent"
            return f"{name}: {effect}."

    def soul_next_goal_text(self):
            c = self.character
            if c.soul_level >= SOUL_MAX_LEVEL and c.soul_tier >= SOUL_MAX_TIER:
                return "Soul Level i Tier są maksymalne."

            if c.soul_tier >= SOUL_MAX_TIER:
                return f"Tier jest maksymalny. Rozwijaj Soul do {SOUL_MAX_LEVEL}."

            next_tier = c.soul_tier + 1
            needed = SOUL_TIER_THRESHOLDS[next_tier - 1]
            if c.soul_level < needed:
                return f"Następny cel: Soul {needed} dla Tieru {next_tier}."

            quest_id = SOUL_TRIAL_QUEST_IDS.get(next_tier)
            if quest_id:
                if self.soul_tier_quest_completed(next_tier):
                    return f"Próba Tieru {next_tier} ukończona. Wpisz unlock."
                band = soul_trial_difficulty_band(next_tier)
                return (
                    f"Soul wymagany osiągnięty. Tier {next_tier} wymaga "
                    f"Próby Broni Duszy u Kapłana Elora. Pasmo: {band}."
                )
            return f"Tier {next_tier} jest gotowy. Wpisz unlock."

    async def show_soul(self, mode=""):
            mode = self.normalize_description_query(mode)
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły",
                "details", "progi", "tiers", "tiery", "proby", "próby",
            )
            c = self.character

            if not detailed:
                await self.send("DUSZA")
                await self.send(f"Broń Duszy: {c.soul_weapon}.")
                await self.send(f"Soul Level: {c.soul_level}/{SOUL_MAX_LEVEL}.")
                await self.send(f"Soul Tier: {c.soul_tier}/{SOUL_MAX_TIER}.")
                await self.send(f"Soul Weapon Mastery: {c.soul_weapon_mastery_level}/{SOUL_WEAPON_MASTERY_MAX_LEVEL}.")
                if c.soul_weapon_mastery_level < SOUL_WEAPON_MASTERY_MAX_LEVEL:
                    await self.send(f"Mastery XP: {c.soul_weapon_mastery_xp} z {c.soul_weapon_mastery_xp_to_next()}.")
                else:
                    await self.send("Mastery XP: maksimum.")
                await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
                if c.soul_level < SOUL_MAX_LEVEL:
                    if c.soul_progress_is_tier_locked():
                        await self.send(
                            f"Soul XP: ZABLOKOWANY na Soul Poziom {c.soul_level}. "
                            f"Najpierw odblokuj Tier {min(SOUL_MAX_TIER, c.soul_tier + 1)}."
                        )
                    else:
                        await self.send(f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}.")
                        await self.send(f"Mnożnik wymaganego Soul XP: x{c.soul_xp_multiplier():.2f}.")
                else:
                    await self.send("Soul XP: maksimum.")
                await self.send(f"Bonus klasowy: {c.soul_weapon_class_bonus_text()}.")
                await self.send(self.soul_next_goal_text())
                await self.send("Wpisz dusza info po wszystkie progi, Próby i status następnego odblokowania.")
                return

            await self.send("DUSZA INFO")
            await self.send("Soul Level jest osobnym rozwojem Broni Duszy 1-600. Nie jest levelem postaci.")
            await self.send("Soul Level zatrzymuje się na progu następnego Tieru. Dalszy Soul XP rusza dopiero po ukończeniu Próby i użyciu unlock.")
            await self.send("Stare progi skilli do 200 odblokuje Biegłość właściwej klasy; sama Biegłość rozwija się do 600, nie Soul Level.")
            await self.send(f"Broń Duszy: {c.soul_weapon}.")
            await self.send(f"Soul Level: {c.soul_level}/{SOUL_MAX_LEVEL}.")
            await self.send(f"Soul Tier: {c.soul_tier}/{SOUL_MAX_TIER}.")
            await self.send(f"Soul Weapon Mastery: {c.soul_weapon_mastery_level}/{SOUL_WEAPON_MASTERY_MAX_LEVEL}.")
            if c.soul_weapon_mastery_level < SOUL_WEAPON_MASTERY_MAX_LEVEL:
                await self.send(f"Mastery XP: {c.soul_weapon_mastery_xp} z {c.soul_weapon_mastery_xp_to_next()}. XP wpada tylko za zwykłe trafienia Bronią Duszy.")
            else:
                await self.send("Mastery XP: maksimum. Soul Weapon Mastery 600.")
            _mastery = c.soul_weapon_mastery_bonus()
            await self.send(
                f"Premie Mastery: +{_mastery['damage_percent']:.1f}% obrażeń podstawowego ataku; "
                f"+{_mastery['crit_chance']*100:.1f} pp krytyka; +{_mastery['crit_damage_percent']:.1f}% obrażeń krytycznych; "
                f"+{_mastery['boss_damage_percent']:.1f}% przeciw bossom; "
                f"{_mastery['echo_chance']*100:.1f}% szansy na Echo zadające {_mastery['echo_damage_percent']:.0f}% obrażeń."
            )
            await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
            if c.soul_level < SOUL_MAX_LEVEL:
                if c.soul_progress_is_tier_locked():
                    await self.send(
                        f"Soul XP: ZABLOKOWANY na Soul Poziom {c.soul_level}. "
                        f"Najpierw odblokuj Tier {min(SOUL_MAX_TIER, c.soul_tier + 1)}."
                    )
                else:
                    await self.send(f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}.")
                    await self.send(f"Mnożnik wymaganego Soul XP: x{c.soul_xp_multiplier():.2f}.")
            else:
                await self.send("Soul XP: maksimum. Soul Level 600.")
            await self.send(f"Bonus klasowy Broni Duszy: {c.soul_weapon_class_bonus_text()}.")
            trait = soul_weapon_trait_for_tier(c.soul_tier, c.class_name)
            totals = soul_weapon_trait_totals(c.soul_tier, c.class_name)
            if trait:
                await self.send(f"Najnowsza właściwość T{c.soul_tier}: {trait['name']}. {trait['description']}.")
            await self.send(
                f"Łączne właściwości klasy {c.class_name}: +{totals['damage_percent']:.1f}% obrażeń podstawowego ataku; "
                f"+{totals['crit_chance']*100:.1f} pp krytyka; +{totals['crit_damage_percent']:.0f}% obrażeń krytycznych; "
                f"{totals['lifesteal_percent']:.1f}% wysysania życia; +{totals['execute_damage_percent']:.1f}% obrażeń przy celu do 35% HP; "
                f"+{totals['boss_damage_percent']:.1f}% obrażeń przeciw bossom; {totals['mana_restore_percent']:.1f}% obrażeń zwracane jako Mana."
            )
            await self.send(
                "Progi Tierów 1-10: T1 Soul 1; T2 10; T3 20; T4 25; T5 35; "
                "T6 45; T7 60; T8 70; T9 80; T10 90."
            )
            await self.send(
                "Progi Tierów 11-20: T11 Soul 100; T12 110; T13 120; T14 130; "
                "T15 140; T16 150; T17 160; T18 170; T19 180; T20 200."
            )
            await self.send("Każdy Tier od 2 do 40 wymaga własnej jednorazowej Próby Broni Duszy u Kapłana Elora.")
            await self.send("Po ukończeniu Próby wpisz unlock, aby odblokować przygotowany Tier.")

            for tier in range(2, SOUL_MAX_TIER + 1):
                quest_id = SOUL_TRIAL_QUEST_IDS.get(tier)
                quest = QUESTS.get(quest_id, {}) if quest_id else {}
                required_soul = SOUL_TIER_THRESHOLDS[tier - 1]
                row = self.server.db.quest(self.account_id, quest_id) if quest_id else None
                if c.soul_tier >= tier:
                    state = "Tier odblokowany"
                elif row and row["status"] == "completed":
                    state = "Próba ukończona; wpisz unlock"
                elif row and row["status"] == "active":
                    needed = int(quest.get("needed", 1))
                    progress = int(row["progress"])
                    state = f"Próba aktywna; postęp {progress} z {needed}"
                elif c.soul_level < required_soul:
                    state = f"zablokowana do Soul {required_soul}"
                elif c.soul_tier < tier - 1:
                    state = f"najpierw odblokuj Tier {tier - 1}"
                else:
                    state = "dostępna u Kapłana Elora"
                band = quest.get("trial_band", soul_trial_difficulty_band(tier))
                trait = soul_weapon_trait_for_tier(tier, c.class_name)
                trait_text = f" Właściwość: {trait['name']} - {trait['description']}." if trait else ""
                await self.send(f"Tier {tier}. Wymaga Soul {required_soul}. Próba: {band}. {state}." + trait_text)

            await self.send("KAMIENIE MILOWE BRONI DUSZY")
            for milestone_tier in SOUL_MILESTONE_TIERS:
                state = "aktywne" if c.soul_tier >= milestone_tier else "zablokowane"
                await self.send(f"T{milestone_tier}: {self.soul_milestone_text(milestone_tier)} Stan: {state}.")
            await self.send(self.soul_next_goal_text())
            await self.send(
                "Mityczna Krypta jest dostępna bez progu Soul Level; Mityczna Wieża Astralna nadal wymaga Soul 100. "
                "Nie wymagają ukończenia zwykłej Krypty ani zwykłej Wieży."
            )
            await self.send("Wysokopoziomowe elity i bossowie mogą dawać bardzo duże ilości Soul XP.")
