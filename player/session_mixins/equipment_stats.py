# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: equipment_stats."""


def moogle_board_stat_bonus_v0313(mec_mastery):
    """Bonus Moogle Board do każdego głównego statu, skalowany Biegłością Meca."""
    level = max(1, min(400, int(mec_mastery or 1)))
    if level >= 400:
        return 18
    return 2 + 2 * (level // 50)

class SessionEquipmentStatsMixin:
    def equipped_item_rows(self):
            return list(self.server.db.equipment(self.account_id))

    def equipment_bonus_totals(self):
            totals = {
                "strength": 0,
                "dexterity": 0,
                "constitution": 0,
                "intelligence": 0,
                "willpower": 0,
                "hp": 0,
                "mana": 0,
            }
            for row in self.equipped_item_rows():
                item = ITEMS.get(row["item_id"])
                if not item:
                    continue
                _reforge = self.server.db.equipment_reforge(self.account_id, row["item_id"])
                affix = str(_reforge["affix"]) if _reforge else item.get("affix")
                affix_amount = int(_reforge["affix_amount"]) if _reforge else int(item.get("affix_amount", 0))
                if affix in totals:
                    totals[affix] += affix_amount
                for _rrow in self.server.db.equipment_runes_v0925(self.account_id, row["item_id"]):
                    _rune = ITEMS.get(str(_rrow["rune_id"]), {})
                    for _stat,_amount in (_rune.get("rune_stats") or {}).items():
                        if _stat in totals:
                            totals[_stat] += int(_amount)

                for stat, amount in item.get("stats", {}).items():
                    if stat in totals:
                        totals[stat] += int(amount)

                # v0.31.3: Moogle Board skaluje wszystkie główne staty z Biegłością Meca.
                if row["item_id"] == "moogle_board" and item.get("cyborg_board_scaling") == "mec_mastery":
                    board_bonus = moogle_board_stat_bonus_v0313(self.class_mastery_level("Mec"))
                    for stat in ("strength", "dexterity", "constitution", "intelligence", "willpower"):
                        totals[stat] += board_bonus

                upgrade_level = self.server.db.equipment_upgrade_level_v03042(
                    self.account_id, row["item_id"]
                )
                if upgrade_level > 0:
                    upgrade_stat = v03042_upgrade_primary_stat(item, affix)
                    upgrade_amount = v03042_upgrade_stat_bonus(upgrade_level)
                    if upgrade_stat in totals and upgrade_amount > 0:
                        totals[upgrade_stat] += upgrade_amount

                if globals().get("equipment_gem_socket_capacity_v03111", lambda _i: jewelry_socket_capacity(_i))(item) > 0:
                    socket_slot = row["slot"]
                    for gem_row in self.server.db.socketed_gems(self.account_id, socket_slot, row["item_id"]):
                        gem = ITEMS.get(gem_row["gem_id"])
                        if not gem:
                            continue
                        gem_affix = gem.get("affix")
                        if gem_affix in totals:
                            totals[gem_affix] += int(gem.get("affix_amount", 0))
            for _erow in self.server.db.equipment_enchants_v03053(self.account_id):
                _stat=str(_erow["stat"]); _amount=int(_erow["amount"])
                if _stat in totals:
                    totals[_stat] += _amount
            class_stats = self.class_set_stat_bonus_totals()
            for stat, amount in class_stats.items():
                totals[stat] += int(amount)
            return totals

    def equipment_property_totals(self):
            totals = {
                "physical_damage_pct": 0,
                "magic_damage_pct": 0,
                "all_damage_pct": 0,
                "physical_defense_pct": 0,
                "magic_defense_pct": 0,
                "dodge_pct": 0,
                "max_hp_pct": 0,
                "max_mana_pct": 0,
            }
            for row in self.equipped_item_rows():
                item = ITEMS.get(row["item_id"])
                if not item:
                    continue
                for prop, amount in item.get("properties", {}).items():
                    if prop in totals:
                        totals[prop] += float(amount)
                for _rrow in self.server.db.equipment_runes_v0925(self.account_id, row["item_id"]):
                    _rune = ITEMS.get(str(_rrow["rune_id"]), {})
                    for _prop,_amount in (_rune.get("rune_properties") or {}).items():
                        if _prop in totals:
                            totals[_prop] += float(_amount)
            return totals

    def equipment_damage_multiplier(self, damage_type):
            props = self.equipment_property_totals()
            bonus = float(props.get("all_damage_pct", 0.0))
            if damage_type == "magic":
                bonus += float(props.get("magic_damage_pct", 0.0))
            else:
                bonus += float(props.get("physical_damage_pct", 0.0))
            return max(0.0, 1.0 + bonus / 100.0)

    def class_set_counts(self):
            active = set(self.active_class_names())
            logical_slots = {}
            for row in self.equipped_item_rows():
                item = ITEMS.get(row["item_id"])
                if not item or not item.get("class_shop_item"):
                    continue
                class_name = item.get("required_class")
                if class_name not in active:
                    continue
                # ring1/ring2 i charm1/charm2 są dwiema pozycjami użytkowymi,
                # ale dla progu setu nadal liczą się jako jedna logiczna część.
                logical_slots.setdefault(class_name, set()).add(item.get("slot"))
            return {
                class_name: len(slots)
                for class_name, slots in logical_slots.items()
            }

    def class_set_stat_bonus_totals(self):
            totals = {
                "strength": 0, "dexterity": 0, "constitution": 0,
                "intelligence": 0, "willpower": 0,
            }
            for class_name, count in self.class_set_counts().items():
                if count < 2:
                    continue
                config = CLASS_SET_BONUSES.get(class_name, {})
                for stat, amount in config.get("stats", {}).items():
                    if stat in totals:
                        totals[stat] += int(amount)
            return totals

    def class_set_damage_multiplier(self):
            multiplier = 1.0
            for class_name, count in self.class_set_counts().items():
                if count >= 4:
                    multiplier *= float(
                        CLASS_SET_BONUSES.get(class_name, {}).get(
                            "damage", 1.0
                        )
                    )
            return multiplier

    def class_set_defense_multiplier(self):
            multiplier = 1.0
            for class_name, count in self.class_set_counts().items():
                if count >= 6:
                    multiplier *= float(
                        CLASS_SET_BONUSES.get(class_name, {}).get(
                            "defense", 1.0
                        )
                    )
            return multiplier

    def class_set_vitality_multiplier(self):
            multiplier = 1.0
            for class_name, count in self.class_set_counts().items():
                if count >= 8:
                    multiplier *= float(
                        CLASS_SET_BONUSES.get(class_name, {}).get(
                            "vitality", 1.0
                        )
                    )
            return multiplier

    def class_set_threshold_text(self, class_name):
            config = CLASS_SET_BONUSES[class_name]
            stat_text = ", ".join(
                f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                for stat, amount in config["stats"].items()
            )
            damage = int(round((config["damage"] - 1.0) * 100))
            defense = int(round((config["defense"] - 1.0) * 100))
            vitality = int(round((config["vitality"] - 1.0) * 100))
            resource = (
                "maksymalnego HP i Many"
                if class_type_for_name(class_name) == "magic"
                else "maksymalnego HP"
            )
            return (
                f"2 części: {stat_text}; "
                f"4 części: +{damage} procent wszystkich obrażeń; "
                f"6 części: +{defense} procent obrony fizycznej i magicznej; "
                f"8 części: +{vitality} procent {resource}"
            )

    def class_set_status_lines(self):
            counts = self.class_set_counts()
            lines = []
            for class_name in self.active_class_names():
                count = int(counts.get(class_name, 0))
                if count <= 0:
                    continue
                set_name = CLASS_EQUIPMENT_SETS[class_name]["set_name"]
                active = []
                if count >= 2:
                    stats = CLASS_SET_BONUSES[class_name]["stats"]
                    active.append(
                        "2/8 " + ", ".join(
                            f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                            for stat, amount in stats.items()
                        )
                    )
                if count >= 4:
                    active.append(
                        f"4/8 obrażenia +{int(round((CLASS_SET_BONUSES[class_name]['damage'] - 1.0) * 100))}%"
                    )
                if count >= 6:
                    active.append(
                        f"6/8 obrona +{int(round((CLASS_SET_BONUSES[class_name]['defense'] - 1.0) * 100))}%"
                    )
                if count >= 8:
                    active.append(
                        f"8/8 HP/zasób +{int(round((CLASS_SET_BONUSES[class_name]['vitality'] - 1.0) * 100))}%"
                    )
                state = "; ".join(active) if active else "brak aktywnego progu"
                lines.append(
                    f"Set klasowy {class_name}, Zestaw {set_name}: "
                    f"{count}/13 części. {state}."
                )
            if not lines:
                lines.append("Brak założonych części aktywnego zestawu klasowego.")
            return lines

    def regional_set_counts(self):
            seen = {}
            for row in self.equipped_item_rows():
                item = ITEMS.get(row["item_id"])
                if not item or not item.get("regional_set"):
                    continue
                set_id = item["regional_set"]
                seen.setdefault(set_id, set()).add(item.get("slot"))
            return {set_id: len(slots) for set_id, slots in seen.items()}

    def regional_set_hp_mana_multiplier(self):
            mult=1.0
            for set_id,count in self.regional_set_counts().items():
                if count >= 2:
                    mult *= float(REGIONAL_SET_BONUSES.get(set_id,{}).get("hp",1.0))
            return mult

    def regional_set_damage_multiplier(self):
            mult=1.0
            for set_id,count in self.regional_set_counts().items():
                if count >= 4:
                    mult *= float(REGIONAL_SET_BONUSES.get(set_id,{}).get("damage",1.0))
            return mult

    def regional_set_defense_multiplier(self):
            mult=1.0
            for set_id,count in self.regional_set_counts().items():
                if count >= 6:
                    mult *= float(REGIONAL_SET_BONUSES.get(set_id,{}).get("defense",1.0))
            return mult

    def regional_set_status_lines(self):
            counts=self.regional_set_counts()
            lines=[]
            for set_id,config in REGIONAL_SET_BONUSES.items():
                count=int(counts.get(set_id,0))
                if count <= 0:
                    continue
                active=[]
                if count >= 2: active.append(f"2/6 HP i Mana +{int(round((config['hp']-1)*100))}%")
                if count >= 4: active.append(f"4/6 obrażenia +{int(round((config['damage']-1)*100))}%")
                if count >= 6: active.append(f"6/6 obrona +{int(round((config['defense']-1)*100))}%")
                lines.append(f"{config['name']}: {count}/6 części. " + ("; ".join(active) if active else "brak aktywnego progu" ) + ".")
            return lines or ["Brak aktywnego regionalnego zestawu."]

    def dominant_crypt_set(self):
            slots_by_tier = {}
            for row in self.equipped_item_rows():
                item = ITEMS.get(row["item_id"])
                if not item:
                    continue
                tier = item.get("crypt_set_tier")
                if tier:
                    tier = int(tier)
                    slots_by_tier.setdefault(tier, set()).add(item.get("slot"))

            counts = {tier: len(slots) for tier, slots in slots_by_tier.items()}
            if not counts:
                return 0, 0

            tier, count = sorted(
                counts.items(),
                key=lambda entry: (entry[1], entry[0]),
                reverse=True,
            )[0]
            return tier, count

    def crypt_set_hp_mana_multiplier(self):
            _tier, count = self.dominant_crypt_set()
            return 1.10 if count >= 2 else 1.0

    def crypt_set_damage_multiplier(self):
            _tier, count = self.dominant_crypt_set()
            return 1.10 if count >= 4 else 1.0

    def crypt_set_defense_multiplier(self):
            _tier, count = self.dominant_crypt_set()
            return 1.15 if count >= 6 else 1.0

    def crypt_set_bonus_text(self):
            tier, count = self.dominant_crypt_set()
            if not tier:
                return "Brak aktywnego zestawu Krypty."

            active = []
            if count >= 2:
                active.append("2 części: +10 procent maksymalnego HP i Many")
            if count >= 4:
                active.append("4 części: +10 procent wszystkich obrażeń")
            if count >= 6:
                active.append("6 części: +15 procent obrony fizycznej i magicznej")

            if not active:
                active_text = "brak aktywnego progu; potrzeba 2 części"
            else:
                active_text = "; ".join(active)

            return (
                f"Zestaw Krypty Tier {tier}: {count} z 6 części. "
                f"{active_text}."
            )

    def dominant_astral_set(self):
            slots_by_tier = {}
            for row in self.equipped_item_rows():
                item = ITEMS.get(row["item_id"])
                if not item:
                    continue
                tier = item.get("astral_set_tier")
                if tier:
                    tier = int(tier)
                    slots_by_tier.setdefault(tier, set()).add(item.get("slot"))

            counts = {tier: len(slots) for tier, slots in slots_by_tier.items()}
            if not counts:
                return 0, 0

            tier, count = sorted(
                counts.items(),
                key=lambda entry: (entry[1], entry[0]),
                reverse=True,
            )[0]
            return tier, count

    def astral_set_hp_mana_multiplier(self):
            _tier, count = self.dominant_astral_set()
            return 1.12 if count >= 2 else 1.0

    def astral_set_damage_multiplier(self):
            _tier, count = self.dominant_astral_set()
            return 1.15 if count >= 4 else 1.0

    def astral_set_defense_multiplier(self):
            _tier, count = self.dominant_astral_set()
            return 1.20 if count >= 6 else 1.0

    def artifact_multipliers_v017(self):
            hp = damage = defense = 1.0
            for row in self.equipped_item_rows():
                item = ITEMS.get(row["item_id"], {})
                if not item.get("v017_artifact"):
                    continue
                hp *= float(item.get("artifact_hp_multiplier", 1.0))
                damage *= float(item.get("artifact_damage_multiplier", 1.0))
                defense *= float(item.get("artifact_defense_multiplier", 1.0))
            return hp, damage, defense

    def v0210_mythic_set_counts(self):
            seen={}
            for row in self.equipped_item_rows():
                item=ITEMS.get(row["item_id"],{})
                sid=item.get("v021_mythic_set")
                if sid: seen.setdefault(str(sid),set()).add(str(item.get("slot") or row["slot"]))
            return {sid:len(slots) for sid,slots in seen.items()}

    def v0210_mythic_set_multiplier(self, kind):
            mult=1.0
            for _sid,count in self.v0210_mythic_set_counts().items():
                if kind=="hp" and count>=2: mult*=V021_MYTHIC_SET_BONUS["hp"]
                if kind=="damage" and count>=4: mult*=V021_MYTHIC_SET_BONUS["damage"]
                if kind=="defense" and count>=6: mult*=V021_MYTHIC_SET_BONUS["defense"]
                if count>=8: mult*=V021_MYTHIC_SET_BONUS["complete"]
            return mult

    def v0210_world_tier(self):
            return self.server.db.world_tier_v021(self.account_id)

    def v0210_world_tier_multipliers(self):
            return v0210_world_tier_multipliers(self.v0210_world_tier())

    def v0210_adjust_player_damage(self, damage):
            mult=self.v0210_world_tier_multipliers()["effective_hp"]
            return max(1,int(round(max(1,int(damage))/max(1.0,mult))))

    def v0210_enemy_damage_multiplier(self):
            return float(self.v0210_world_tier_multipliers()["enemy_damage"])

    def v0210_reward_multiplier(self):
            return float(self.v0210_world_tier_multipliers()["reward"])

    def total_set_hp_mana_multiplier(self):
            artifact_hp, _artifact_damage, _artifact_defense = self.artifact_multipliers_v017()
            return (
                self.crypt_set_hp_mana_multiplier()
                * self.astral_set_hp_mana_multiplier()
                * self.class_set_vitality_multiplier()
                * self.regional_set_hp_mana_multiplier()
                * self.v0210_mythic_set_multiplier("hp")
                * artifact_hp
            )

    def total_set_damage_multiplier(self):
            _artifact_hp, artifact_damage, _artifact_defense = self.artifact_multipliers_v017()
            return (
                self.crypt_set_damage_multiplier()
                * self.astral_set_damage_multiplier()
                * self.class_set_damage_multiplier()
                * self.regional_set_damage_multiplier()
                * self.v0210_mythic_set_multiplier("damage")
                * artifact_damage
            )

    def total_set_defense_multiplier(self):
            _artifact_hp, _artifact_damage, artifact_defense = self.artifact_multipliers_v017()
            return (
                self.crypt_set_defense_multiplier()
                * self.astral_set_defense_multiplier()
                * self.class_set_defense_multiplier()
                * self.regional_set_defense_multiplier()
                * self.v0210_mythic_set_multiplier("defense")
                * artifact_defense
            )

    def astral_set_bonus_text(self):
            tier, count = self.dominant_astral_set()
            if not tier:
                return "Brak aktywnego Zestawu Astralnego."

            active = []
            if count >= 2:
                active.append(
                    "2 części: +12 procent maksymalnego HP i Many"
                )
            if count >= 4:
                active.append(
                    "4 części: +15 procent wszystkich obrażeń"
                )
            if count >= 6:
                active.append(
                    "6 części: +20 procent obrony fizycznej i magicznej"
                )

            if not active:
                active_text = "brak aktywnego progu; potrzeba 2 części"
            else:
                active_text = "; ".join(active)

            return (
                f"Zestaw Astralny Krąg {tier}: {count} z 6 części. "
                f"{active_text}."
            )

    def effective_strength(self):
            return (
                self.character.strength
                + self.equipment_bonus_totals()["strength"]
            )

    def effective_dexterity(self):
            return (
                self.character.dexterity
                + self.equipment_bonus_totals()["dexterity"]
            )

    def critical_chance(self):
            return generator_core_v027.critical_chance_from_dexterity(self.effective_dexterity())

    def critical_multiplier(self):
            return generator_core_v027.critical_multiplier(self.character.character_level)

    def roll_critical_hit(self, damage):
            damage = max(0, int(damage))
            if damage <= 0:
                return damage, False
            if random.random() < self.critical_chance():
                return (
                    max(
                        1,
                        int(round(
                            damage * self.critical_multiplier()
                        )),
                    ),
                    True,
                )
            return damage, False

    def effective_constitution(self):
            return (
                self.character.constitution
                + self.equipment_bonus_totals()["constitution"]
            )

    def effective_intelligence(self):
            return (
                self.character.intelligence
                + self.equipment_bonus_totals()["intelligence"]
            )

    def effective_willpower(self):
            return (
                self.character.willpower
                + self.equipment_bonus_totals()["willpower"]
            )

    def max_hp(self):
            bonuses = self.equipment_bonus_totals()
            base = generator_core_v027.character_hp_base(
                self.character.character_level, self.effective_constitution()
            )
            value = int(round(
                (base + bonuses["hp"])
                * self.character.racial_max_hp_multiplier()
                * self.total_set_hp_mana_multiplier()
                * (1.0 + self.equipment_property_totals()["max_hp_pct"] / 100.0)
            ))
            return max(1, value)

    def max_mana(self):
            bonuses = self.equipment_bonus_totals()
            base = generator_core_v027.character_mana_base(
                self.character.character_level, self.effective_intelligence(), self.effective_willpower()
            )
            value = int(round(
                (base + bonuses["mana"])
                * self.character.racial_max_mana_multiplier()
                * self.total_set_hp_mana_multiplier()
                * (1.0 + self.equipment_property_totals()["max_mana_pct"] / 100.0)
            ))
            return max(0, value)

    def physical_power(self):
            return generator_core_v027.character_attribute_power(
                self.character.character_level, self.effective_strength()
            )

    def speed(self):
            return generator_core_v027.speed_from_dexterity(self.effective_dexterity())

    def dodge_chance(self):
            base = v0865_dodge_chance_from_dexterity(
                self.effective_dexterity()
            )
            return min(
                0.35,
                base
                + self.character.class_dodge_bonus()
                + self.character.racial_dodge_bonus()
                + self.equipment_property_totals()["dodge_pct"] / 100.0,
            )

    def spell_power(self):
            return generator_core_v027.character_attribute_power(
                self.character.character_level, self.effective_intelligence()
            )

    def magic_defense(self):
            base = generator_core_v027.magic_defense_base(
                self.character.character_level, self.effective_willpower()
            )
            value = int(
                round(
                    base
                    * self.character.class_magic_defense_multiplier()
                    * self.character.racial_magic_defense_multiplier()
                    * self.total_set_defense_multiplier()
                    * (1.0 + self.equipment_property_totals()["magic_defense_pct"] / 100.0)
                )
            )
            return max(0, value)

    def defense(self):
            total = 0
            for row in self.server.db.equipment(self.account_id):
                item = ITEMS.get(row["item_id"])
                if item:
                    upgrade_level = self.server.db.equipment_upgrade_level_v03042(
                        self.account_id, row["item_id"]
                    )
                    total += int(item.get("defense", 0)) + v03042_upgrade_defense_bonus(
                        item, upgrade_level
                    )
            return max(
                0,
                int(round(
                    total
                    * self.total_set_defense_multiplier()
                    * (1.0 + self.equipment_property_totals()["physical_defense_pct"] / 100.0)
                ))
            )
