

@dataclass
class Character:
    account_id: int
    name: str
    name_nom: str
    name_gen: str
    name_dat: str
    name_acc: str
    name_ins: str
    name_loc: str
    name_voc: str
    race: str
    class_name: str
    class_type: str
    soul_weapon: str
    weapon_base: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    willpower: int
    stat_progress: int
    strength_progress: int
    dexterity_progress: int
    constitution_progress: int
    intelligence_progress: int
    willpower_progress: int
    charisma_progress: int
    soul_level: int
    soul_xp: int
    soul_tier: int
    soul_weapon_mastery_level: int
    soul_weapon_mastery_xp: int
    room_id: str
    silver: int
    gold: int
    mithril: int
    charisma: int
    character_level: int
    character_xp: int
    deaths: int
    guild_reputation_json: str = "{}"
    guild_exams_json: str = "{}"
    guild_class_quests_json: str = "{}"
    guild_bounty_json: str = "{}"
    loot_filter: str = "all"
    active_title: str = ""

    @classmethod
    def from_row(cls, row):
        return cls(
            account_id=row["account_id"], name=row["name"],
            name_nom=row["name_nom"], name_gen=row["name_gen"],
            name_dat=row["name_dat"], name_acc=row["name_acc"],
            name_ins=row["name_ins"], name_loc=row["name_loc"],
            name_voc=row["name_voc"], race=row["race"],
            class_name=row["class_name"], class_type=row["class_type"],
            soul_weapon=row["soul_weapon"], weapon_base=row["weapon_base"],
            strength=row["strength"], dexterity=row["dexterity"],
            constitution=row["constitution"], intelligence=row["intelligence"],
            willpower=row["willpower"], stat_progress=row["stat_progress"],
            strength_progress=(row["strength_progress"] if "strength_progress" in row.keys() else row["stat_progress"]),
            dexterity_progress=(row["dexterity_progress"] if "dexterity_progress" in row.keys() else row["stat_progress"]),
            constitution_progress=(row["constitution_progress"] if "constitution_progress" in row.keys() else row["stat_progress"]),
            intelligence_progress=(row["intelligence_progress"] if "intelligence_progress" in row.keys() else row["stat_progress"]),
            willpower_progress=(row["willpower_progress"] if "willpower_progress" in row.keys() else row["stat_progress"]),
            charisma_progress=(row["charisma_progress"] if "charisma_progress" in row.keys() else row["stat_progress"]),
            soul_level=row["soul_level"], soul_xp=row["soul_xp"],
            soul_tier=row["soul_tier"],
            soul_weapon_mastery_level=(row["soul_weapon_mastery_level"] if "soul_weapon_mastery_level" in row.keys() else 1),
            soul_weapon_mastery_xp=(row["soul_weapon_mastery_xp"] if "soul_weapon_mastery_xp" in row.keys() else 0),
            room_id=row["room_id"],
            silver=row["silver"], gold=row["gold"], mithril=row["mithril"],
            charisma=row["charisma"],
            character_level=(row["character_level"] if "character_level" in row.keys() else 1),
            character_xp=(row["character_xp"] if "character_xp" in row.keys() else 0),
            deaths=row["deaths"],
            guild_reputation_json=(row["guild_reputation_json"] if "guild_reputation_json" in row.keys() else "{}"),
            guild_exams_json=(row["guild_exams_json"] if "guild_exams_json" in row.keys() else "{}"),
            guild_class_quests_json=(row["guild_class_quests_json"] if "guild_class_quests_json" in row.keys() else "{}"),
            guild_bounty_json=(row["guild_bounty_json"] if "guild_bounty_json" in row.keys() else "{}"),
            loot_filter=(row["loot_filter"] if "loot_filter" in row.keys() else "all"),
            active_title=(row["active_title"] if "active_title" in row.keys() else ""),
        )

    def soul_weapon_mastery_xp_to_next(self):
        return soul_weapon_mastery_xp_to_next(self.soul_weapon_mastery_level)

    def soul_weapon_mastery_bonus(self):
        return soul_weapon_mastery_bonuses(self.soul_weapon_mastery_level)

    def add_soul_weapon_mastery_xp(self, amount):
        amount = max(0, int(amount or 0))
        if self.soul_weapon_mastery_level >= SOUL_WEAPON_MASTERY_MAX_LEVEL:
            self.soul_weapon_mastery_level = SOUL_WEAPON_MASTERY_MAX_LEVEL
            self.soul_weapon_mastery_xp = 0
            return {"level_ups": 0, "level": self.soul_weapon_mastery_level, "xp": 0, "next_xp": 0}
        self.soul_weapon_mastery_xp += amount
        level_ups = 0
        while self.soul_weapon_mastery_level < SOUL_WEAPON_MASTERY_MAX_LEVEL:
            needed = soul_weapon_mastery_xp_to_next(self.soul_weapon_mastery_level)
            if needed <= 0 or self.soul_weapon_mastery_xp < needed:
                break
            self.soul_weapon_mastery_xp -= needed
            self.soul_weapon_mastery_level += 1
            level_ups += 1
        if self.soul_weapon_mastery_level >= SOUL_WEAPON_MASTERY_MAX_LEVEL:
            self.soul_weapon_mastery_level = SOUL_WEAPON_MASTERY_MAX_LEVEL
            self.soul_weapon_mastery_xp = 0
        return {
            "level_ups": level_ups,
            "level": self.soul_weapon_mastery_level,
            "xp": self.soul_weapon_mastery_xp,
            "next_xp": soul_weapon_mastery_xp_to_next(self.soul_weapon_mastery_level),
        }

    def character_xp_to_next(self):
        return character_xp_to_next(self.character_level)

    def add_character_xp(self, amount):
        amount=max(0,int(amount or 0))
        if self.character_level >= CHARACTER_MAX_LEVEL:
            self.character_level=CHARACTER_MAX_LEVEL
            self.character_xp=0
            return []
        self.character_xp += amount
        messages=[]
        while self.character_level < CHARACTER_MAX_LEVEL:
            needed=character_xp_to_next(self.character_level)
            if self.character_xp < needed:
                break
            self.character_xp -= needed
            self.character_level += 1
            messages.append(f"Level postaci wzrasta do {self.character_level}.")
        if self.character_level >= CHARACTER_MAX_LEVEL:
            self.character_level=CHARACTER_MAX_LEVEL
            self.character_xp=0
        if amount:
            next_needed=character_xp_to_next(self.character_level) if self.character_level < CHARACTER_MAX_LEVEL else 0
            messages.insert(0, f"EXP postaci +{amount}. Postęp {self.character_xp} z {next_needed}." if next_needed else f"EXP postaci +{amount}. Osiągnięto maksymalny Level {CHARACTER_MAX_LEVEL}.")
        return messages

    def name_case(self, case):
        mapping = {
            "nom": self.name_nom, "mianownik": self.name_nom,
            "gen": self.name_gen, "dopelniacz": self.name_gen, "dopełniacz": self.name_gen,
            "dat": self.name_dat, "celownik": self.name_dat,
            "acc": self.name_acc, "biernik": self.name_acc,
            "ins": self.name_ins, "narzednik": self.name_ins, "narzędnik": self.name_ins,
            "loc": self.name_loc, "miejscownik": self.name_loc,
            "voc": self.name_voc, "wolacz": self.name_voc, "wołacz": self.name_voc,
        }
        return mapping.get(str(case).strip().lower(), self.name_nom or self.name)

    def max_hp(self):
        base = generator_core_v027.character_hp_base(self.character_level, self.constitution)
        return max(1, int(round(base * self.racial_max_hp_multiplier())))

    def physical_power(self):
        return generator_core_v027.character_attribute_power(self.character_level, self.strength)

    def speed(self):
        return generator_core_v027.speed_from_dexterity(self.dexterity)

    def dodge_chance(self):
        # v0.8.65: Zręczność daje malejący pasywny dodge zamiast liniowej
        # krzywej, która w endgame doprowadzała prawie każdą klasę do 45%.
        base = v0865_dodge_chance_from_dexterity(self.dexterity)
        return min(
            0.35,
            base + self.class_dodge_bonus() + self.racial_dodge_bonus()
        )

    def active_class_names(self):
        names = list(getattr(self, "_active_classes", []) or [])
        if self.class_name not in names:
            names.insert(0, self.class_name)
        result = []
        for name in names:
            if name not in result:
                result.append(name)
        return result[:MULTICLASS_MAX_ACTIVE]

    def has_active_class(self, class_name):
        return class_name in self.active_class_names()

    def max_mana(self):
        base = generator_core_v027.character_mana_base(self.character_level, self.intelligence, self.willpower)
        return max(0, int(round(base * self.racial_max_mana_multiplier())))

    def spell_power(self):
        return generator_core_v027.character_attribute_power(self.character_level, self.intelligence)

    def _generated_class_passive(self, class_name):
        return generator_core_v027.class_passive_profile(class_name)

    def _generated_race_passive(self):
        return generator_core_v027.race_passive_profile(self.race)

    def class_passive_text_for(self, class_name):
        return generator_core_v027.class_passive_text_pl(class_name)

    def class_passive_text(self):
        return self.class_passive_text_for(self.class_name)

    def class_physical_damage_multiplier(self):
        multiplier = 1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "physical_damage": multiplier *= 1.0 + p["value"]
        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        elif self.class_name == "Łotrzyk":
            multiplier *= 1.0 + self.soul_weapon_rogue_damage_bonus_percent() / 100.0
        return multiplier

    def class_magic_damage_multiplier(self):
        multiplier = 1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "magic_damage": multiplier *= 1.0 + p["value"]
        if self.class_name in ("Mag", "Czarownik"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_healing_multiplier(self):
        multiplier = 1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "healing": multiplier *= 1.0 + p["value"]
        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_drain_healing_multiplier(self):
        multiplier=1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"] == "drain_healing": multiplier *= 1.0 + p["value"]
        if self.class_name == "Nekromanta":
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_dodge_bonus(self):
        bonus=sum(self._generated_class_passive(name)["value"] for name in self.active_class_names() if self._generated_class_passive(name)["kind"]=="dodge")
        if self.class_name == "Łotrzyk": bonus += self.soul_weapon_dodge_bonus()
        return bonus

    def class_damage_reduction_percent(self):
        percent=100.0*sum(self._generated_class_passive(name)["value"] for name in self.active_class_names() if self._generated_class_passive(name)["kind"]=="damage_reduction")
        if self.class_name == "Strażnik": percent += self.soul_weapon_guardian_reduction_percent()
        return int(round(percent))

    def class_magic_defense_multiplier(self):
        multiplier=1.0
        for name in self.active_class_names():
            p=self._generated_class_passive(name)
            if p["kind"]=="magic_defense": multiplier *= 1.0+p["value"]
        if self.class_name == "Psionik": multiplier *= 1.0 + self.soul_weapon_bonus_percent()/100.0
        return multiplier

    def apply_class_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.class_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        return reduced, max(0, damage - reduced)

    def racial_passive_text(self):
        return generator_core_v027.race_passive_text_pl(self.race)

    def _race_bonus(self, kind):
        p=self._generated_race_passive()
        return p["value"] if p["kind"]==kind else 0.0

    def racial_stat_progress_multiplier(self):
        return 1.0 + self._race_bonus("stat_xp")

    def racial_physical_damage_multiplier(self):
        return 1.0 + self._race_bonus("physical_damage")

    def racial_dodge_bonus(self):
        return self._race_bonus("dodge")

    def racial_max_hp_multiplier(self):
        return 1.0 + self._race_bonus("max_hp")

    def racial_profession_bonus_chance(self):
        return self._race_bonus("profession_bonus")

    def racial_magic_damage_multiplier(self):
        return 1.0 + self._race_bonus("magic_damage")

    def racial_max_mana_multiplier(self):
        return 1.0 + self._race_bonus("max_mana")

    def racial_all_damage_multiplier(self):
        return 1.0 + self._race_bonus("all_damage")

    def racial_physical_damage_reduction_percent(self):
        return int(round(100.0*self._race_bonus("physical_reduction")))

    def racial_soul_xp_multiplier(self):
        return 1.0 + self._race_bonus("soul_xp")

    def racial_magic_defense_multiplier(self):
        return 1.0 + self._race_bonus("magic_defense")

    def racial_healing_multiplier(self):
        return 1.0 + self._race_bonus("healing")

    def racial_healing_bonus_percent(self):
        return int(round((self.racial_healing_multiplier() - 1.0) * 100))

    def racial_damage_reduction_percent(self):
        return int(round(100.0*self._race_bonus("damage_reduction")))

    def apply_racial_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.racial_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        prevented = max(0, damage - reduced)
        return reduced, prevented

    def magic_defense(self):
        # Siła Woli odpowiada wyłącznie za obronę magiczną.
        base = max(0, self.willpower // 2)
        return max(
            0,
            int(
                round(
                    base
                    * self.class_magic_defense_multiplier()
                    * self.racial_magic_defense_multiplier()
                )
            )
        )

    def shop_discount_percent(self):
        return min(
            CHARISMA_MAX_DISCOUNT,
            max(0, self.charisma // CHARISMA_DISCOUNT_STEP),
        )

    def party_capacity(self):
        # Startowo 8 osób łącznie z liderem.
        # Co 25 Charyzmy lider otrzymuje jedno kolejne miejsce.
        return PARTY_BASE_CAPACITY + max(0, self.charisma // PARTY_CHARISMA_STEP)

    def charisma_to_next_discount(self):
        if self.shop_discount_percent() >= CHARISMA_MAX_DISCOUNT:
            return 0
        next_value = (self.shop_discount_percent() + 1) * CHARISMA_DISCOUNT_STEP
        return max(0, next_value - self.charisma)

    def charisma_to_next_party_slot(self):
        next_value = (
            (max(0, self.charisma) // PARTY_CHARISMA_STEP) + 1
        ) * PARTY_CHARISMA_STEP
        return max(0, next_value - self.charisma)

    def soul_xp_multiplier(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0.0
        level = max(1, int(self.soul_level))
        if level <= 200:
            # Dokładnie stara krzywa 1-200.
            completed_ten_level_blocks = max(0, (level - 1) // 10)
            return 1.25 ** completed_ten_level_blocks
        # 201-600: nie kontynuujemy wykładniczego 1.25^blok, bo koszt
        # eksplodowałby do setek milionów na level. Kotwiczymy na koszcie
        # levelu 200 i zwiększamy go liniowo do około x3 na 599->600.
        anchor_base = 180 + (200 - 1) * 60
        anchor_cost = anchor_base * (1.25 ** 19)
        target_cost = anchor_cost * (1.0 + (level - 200) * 0.01)
        current_base = 180 + (level - 1) * 60
        return max(1.0, target_cost / current_base)

    def soul_xp_to_next(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0
        return v0190_requirement("soul", self.soul_level)

    def soul_milestone_specialization_bonus(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        active = [t for t in SOUL_MILESTONE_TIERS if tier >= t]
        return SOUL_MILESTONE_SPECIALIZATION_BONUS[max(active)] if active else 0

    def soul_milestone_dodge_bonus(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        active = [t for t in SOUL_MILESTONE_TIERS if tier >= t]
        return SOUL_MILESTONE_DODGE_BONUS[max(active)] if active else 0.0

    def soul_milestone_guardian_reduction(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        active = [t for t in SOUL_MILESTONE_TIERS if tier >= t]
        return SOUL_MILESTONE_GUARDIAN_REDUCTION[max(active)] if active else 0

    def soul_weapon_bonus_percent(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        return (
            SOUL_TIER_CLASS_BONUS_PERCENT[tier - 1]
            + self.soul_milestone_specialization_bonus()
        )

    def soul_weapon_rogue_damage_bonus_percent(self):
        # Łotrzyk zachowuje defensywną tożsamość, ale jego Broń Duszy nie
        # przepala już progresji po osiągnięciu globalnego capu dodge.
        return max(0, (self.soul_weapon_bonus_percent() + 1) // 2)

    def soul_weapon_dodge_bonus(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        return min(
            0.05,
            SOUL_TIER_DODGE_BONUS[tier - 1]
            + self.soul_milestone_dodge_bonus()
        )

    def soul_weapon_guardian_reduction_percent(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        return (
            SOUL_TIER_GUARDIAN_REDUCTION[tier - 1]
            + self.soul_milestone_guardian_reduction()
        )

    def soul_weapon_class_bonus_text(self):
        percent = self.soul_weapon_bonus_percent()
        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            return (
                f"+{percent} procent obrażeń fizycznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Łotrzyk":
            pp = int(round(self.soul_weapon_dodge_bonus() * 100))
            dmg = self.soul_weapon_rogue_damage_bonus_percent()
            return (
                f"+{dmg} procent obrażeń fizycznych i +{pp} punktów "
                "procentowych uniku z Broni Duszy Łotrzyka"
            )
        if self.class_name in ("Mag", "Czarownik"):
            return (
                f"+{percent} procent obrażeń magicznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            return (
                f"+{percent} procent mocy leczenia z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Nekromanta":
            return (
                f"+{percent} procent leczenia z wysysania życia "
                "z Broni Duszy Nekromanty"
            )
        if self.class_name == "Strażnik":
            return (
                f"+{self.soul_weapon_guardian_reduction_percent()} procent "
                "redukcji wszystkich obrażeń z Broni Duszy Strażnika"
            )
        if self.class_name == "Psionik":
            return (
                f"+{percent} procent obrony magicznej "
                "z Broni Duszy Psionika"
            )
        return f"+{percent} procent do specjalizacji klasy głównej"

    def soul_power(self):
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        tier_bonus = SOUL_TIER_POWER_BONUSES[tier - 1]
        level = max(1, min(SOUL_MAX_LEVEL, int(self.soul_level)))
        # 1-200 zachowuje dawny +1 mocy/level. 201-600 daje +1 mocy
        # co 2 levele, więc cap 600 jest dalszym wzrostem, nie x2 power creepem.
        level_bonus = min(level, 200) - 1 + max(0, level - 200) // 2
        return self.weapon_base + level_bonus + tier_bonus

    def can_unlock(self):
        if self.soul_tier >= SOUL_MAX_TIER:
            return None
        next_tier = int(self.soul_tier) + 1
        needed_level = SOUL_TIER_THRESHOLDS[next_tier - 1]
        if self.soul_level >= needed_level:
            return next_tier
        return None

    STAT_PROGRESS_FIELDS = {
        "strength": ("Siła", "strength", "strength_progress"),
        "dexterity": ("Zręczność", "dexterity", "dexterity_progress"),
        "constitution": ("Kondycja", "constitution", "constitution_progress"),
        "intelligence": ("Inteligencja", "intelligence", "intelligence_progress"),
        "willpower": ("Siła Woli", "willpower", "willpower_progress"),
        "charisma": ("Charyzma", "charisma", "charisma_progress"),
    }

    def stat_growth_threshold_for(self, stat_name):
        """Próg EXP pojedynczej statystyki.

        Każda statystyka rozwija się niezależnie. Start to 100 EXP, a od
        wartości bazowej 26 próg rośnie o 10 za każdy punkt. Dzięki temu
        niska statystyka może nadrobić, a wysoka nie rośnie lawinowo.
        """
        _label, value_field, _progress_field = self.STAT_PROGRESS_FIELDS[stat_name]
        value = max(1, int(getattr(self, value_field)))
        return v0190_requirement("stat", value)

    def stat_growth_threshold(self):
        """Legacy: zwraca średni próg sześciu statystyk dla zgodności."""
        thresholds = [self.stat_growth_threshold_for(name) for name in self.STAT_PROGRESS_FIELDS]
        return int(round(sum(thresholds) / len(thresholds)))

    def stat_progress_for(self, stat_name):
        _label, _value_field, progress_field = self.STAT_PROGRESS_FIELDS[stat_name]
        return max(0, int(getattr(self, progress_field)))

    def stat_progress_snapshot(self):
        result = {}
        for stat_name, (label, value_field, progress_field) in self.STAT_PROGRESS_FIELDS.items():
            result[stat_name] = {
                "label": label,
                "value": int(getattr(self, value_field)),
                "progress": max(0, int(getattr(self, progress_field))),
                "threshold": self.stat_growth_threshold_for(stat_name),
            }
        return result

    def add_stat_progress(self, amount, targets=None):
        """Dodaje EXP osobno do wskazanych statystyk.

        Domyślnie źródła ogólnego rozwoju (moby/questy) przyznają tę samą
        ilość EXP każdej statystyce, ale każda ma własny licznik i próg.
        """
        base_amount = max(0, int(amount))
        racial_amount = max(
            0,
            int(round(base_amount * self.racial_stat_progress_multiplier()))
        )
        _guild_pct=max(0,int(getattr(self,"_guild_bonus_percent",0) or 0))
        amount=max(0,int(round(racial_amount*(1.0+_guild_pct/100.0))))
        if targets is None:
            target_names = list(self.STAT_PROGRESS_FIELDS)
        else:
            target_names = [name for name in targets if name in self.STAT_PROGRESS_FIELDS]
        messages = []
        bonus = max(0, racial_amount - base_amount)
        guild_bonus=max(0, amount - racial_amount)
        for stat_name in target_names:
            label, value_field, progress_field = self.STAT_PROGRESS_FIELDS[stat_name]
            current_value=max(1,int(getattr(self,value_field)))
            # v0.27.1: statystyki nie mają capu. Powyżej 400 Generator Core
            # ekstrapoluje zarówno wymagany EXP, jak i wartość nagrody ze
            # źródła. Dzięki temu endgame nie zatrzymuje progresji, ale niskie
            # levele mobów nadal pozostają słabym źródłem EXP dla wysokich statów.
            stat_amount = generator_core_v027.uncapped_stat_xp_gain(amount, current_value)
            progress = max(0, int(getattr(self, progress_field))) + stat_amount
            leveled = 0
            while True:
                threshold = self.stat_growth_threshold_for(stat_name)
                if progress < threshold:
                    break
                progress -= threshold
                setattr(self, value_field, int(getattr(self, value_field)) + 1)
                leveled += 1
            setattr(self, progress_field, progress)
            if leveled:
                new_value = int(getattr(self, value_field))
                if leveled == 1:
                    messages.append(
                        f"{label} wzrasta do {new_value} — {stat_quality_label(new_value)}."
                    )
                else:
                    messages.append(
                        f"{label} wzrasta o {leveled} do {new_value} — {stat_quality_label(new_value)}."
                    )
            threshold = self.stat_growth_threshold_for(stat_name)
            messages.append(
                f"{label}: EXP +{stat_amount}. Postęp {progress} z {threshold}."
            )
        if bonus:
            messages.append(
                f"Bonus rasy {self.race} został uwzględniony w EXP rozwijanych statystyk."
            )
        if guild_bonus:
            messages.append(
                f"Bonus Gildii +{_guild_pct}% został uwzględniony w EXP rozwijanych statystyk."
            )
        # Legacy pole zachowujemy jako najmniejszy bieżący postęp, ale nie
        # steruje już rozwojem.
        values = [self.stat_progress_for(name) for name in self.STAT_PROGRESS_FIELDS]
        self.stat_progress = min(values) if values else 0
        return messages

    def soul_level_cap_for_current_tier(self):
        """Najwyższy Soul Level dostępny przed odblokowaniem kolejnego Tieru.

        Tier 1 pozwala dojść do progu Tieru 2, Tier 2 do progu Tieru 3 itd.
        Tier 60 ma końcowy cap Soul Level 600. Istniejących save'ów nie cofamy:
        postać zapisana powyżej bieżącego capu po prostu nie dostaje dalszego
        Soul XP, dopóki nie odblokuje brakujących Tierów.
        """
        tier = max(1, min(SOUL_MAX_TIER, int(self.soul_tier)))
        if tier >= SOUL_MAX_TIER:
            return SOUL_MAX_LEVEL
        return int(SOUL_TIER_THRESHOLDS[tier])

    def soul_progress_is_tier_locked(self):
        return (
            int(self.soul_tier) < SOUL_MAX_TIER
            and int(self.soul_level) >= self.soul_level_cap_for_current_tier()
        )

    def add_soul_xp(self, amount):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return [f"Broń Duszy ma już Soul Level {SOUL_MAX_LEVEL}."]

        # v0.9.14: Soul Level nie może wyprzedzić odblokowanego Tieru.
        # Osiągnięcie progu następnego Tieru zatrzymuje cały dalszy Soul XP
        # do chwili wykonania Próby i użycia komendy unlock. Overflow nie jest
        # bankowany, dzięki czemu po unlock nie da się przeskoczyć kilku progów.
        cap_level = self.soul_level_cap_for_current_tier()
        if self.soul_progress_is_tier_locked():
            next_tier = min(SOUL_MAX_TIER, int(self.soul_tier) + 1)
            self.soul_xp = 0
            return [
                f"Soul XP zablokowany na Soul Level {cap_level}. "
                f"Najpierw odblokuj Soul Tier {next_tier}: wykonaj właściwą Próbę "
                "Broni Duszy i użyj unlock."
            ]

        base_amount = max(0, int(amount))
        racial_amount = max(
            0,
            int(round(base_amount * self.racial_soul_xp_multiplier()))
        )
        _guild_pct=max(0,int(getattr(self,"_guild_bonus_percent",0) or 0))
        amount=max(0,int(round(racial_amount*(1.0+_guild_pct/100.0))))
        messages = [f"Broń Duszy otrzymuje {amount} Soul XP."]
        if racial_amount > base_amount:
            messages.append(
                f"Bonus rasy {self.race}: +{racial_amount - base_amount} Soul XP."
            )
        if amount > racial_amount:
            messages.append(
                f"Bonus Gildii +{_guild_pct}%: +{amount-racial_amount} Soul XP."
            )
        self.soul_xp += amount
        while self.soul_level < SOUL_MAX_LEVEL:
            cap_level = self.soul_level_cap_for_current_tier()
            if self.soul_level >= cap_level:
                # Nie zachowujemy nadmiaru ponad bramką Tieru.
                self.soul_xp = 0
                next_tier = min(SOUL_MAX_TIER, int(self.soul_tier) + 1)
                messages.append(
                    f"Soul Level zatrzymuje się na {cap_level}. Dalszy Soul XP jest "
                    f"zablokowany do odblokowania Soul Tier {next_tier}."
                )
                break
            needed = self.soul_xp_to_next()
            if self.soul_xp < needed:
                break
            self.soul_xp -= needed
            self.soul_level += 1
            messages.append(f"Broń Duszy osiąga Soul Level {self.soul_level}.")
            if self.soul_level in SOUL_TIER_THRESHOLDS[1:]:
                tier = SOUL_TIER_THRESHOLDS.index(self.soul_level) + 1
                if tier in SOUL_TRIAL_QUEST_IDS:
                    messages.append(
                        f"Osiągnięto próg Tieru {tier}. "
                        "Idź do Kapłana Elora po Próbę Broni Duszy."
                    )
                else:
                    messages.append(
                        f"Osiągnięto próg Tieru {tier}. Wpisz unlock, "
                        "gdy poprzednie Tiery są odblokowane."
                    )
                if int(self.soul_tier) < tier:
                    self.soul_xp = 0
                    messages.append(
                        f"Dalszy Soul XP jest teraz zablokowany do odblokowania Tieru {tier}."
                    )
                    break
        if self.soul_level >= SOUL_MAX_LEVEL:
            self.soul_level = SOUL_MAX_LEVEL
            self.soul_xp = 0
            messages.append(f"Osiągnięto maksymalny Soul Level {SOUL_MAX_LEVEL}.")
        return messages


    def _guild_json(self, field_name):
        try:
            raw = getattr(self, field_name, "{}") or "{}"
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _set_guild_json(self, field_name, data):
        setattr(self, field_name, json.dumps(data, ensure_ascii=False, sort_keys=True))

    def guild_reputation(self, class_name):
        data = self._guild_json("guild_reputation_json")
        return int(data.get(class_name, 0) or 0)

    def add_guild_reputation(self, class_name, amount):
        data = self._guild_json("guild_reputation_json")
        current = int(data.get(class_name, 0) or 0)
        data[class_name] = max(0, min(GUILD_REPUTATION_MAX, current + int(amount)))
        self._set_guild_json("guild_reputation_json", data)
        return data[class_name]

    def guild_rep_rank(self, class_name):
        value = self.guild_reputation(class_name)
        current = GUILD_REPUTATION_RANKS[0]
        for row in GUILD_REPUTATION_RANKS:
            if value >= row[0]:
                current = row
        return current

    def guild_training_discount(self, class_name):
        return float(self.guild_rep_rank(class_name)[2])

    def guild_exam_done(self, class_name, threshold):
        data = self._guild_json("guild_exams_json")
        done = data.get(class_name, [])
        return int(threshold) in [int(x) for x in done]

    def mark_guild_exam_done(self, class_name, threshold):
        data = self._guild_json("guild_exams_json")
        done = set(int(x) for x in data.get(class_name, []))
        done.add(int(threshold))
        data[class_name] = sorted(done)
        self._set_guild_json("guild_exams_json", data)

    def guild_class_quest_done(self, class_name):
        data = self._guild_json("guild_class_quests_json")
        return bool(data.get(class_name, False))

    def mark_guild_class_quest_done(self, class_name):
        data = self._guild_json("guild_class_quests_json")
        data[class_name] = True
        self._set_guild_json("guild_class_quests_json", data)

    def guild_bounty_state(self):
        return self._guild_json("guild_bounty_json")

    def set_guild_bounty_state(self, data):
        self._set_guild_json("guild_bounty_json", data)


# ============================================================
# v0.12.0 - LIVING WATERS + MEADOW BIOMES + PASSIVE WORLD
# ============================================================
# Globalna zasada rozgrywki: żaden mob ani boss nie zaczyna walki sam.
# Moby mogą się poruszać i pojawiać obok gracza, ale combat uruchamia
# wyłącznie świadoma akcja gracza (atakuj/k/skill ofensywny użyty na celu).
GLOBAL_MOB_AUTO_AGGRO_ENABLED = False
