# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def rebalance_economy_v0861():
    """Ujednolica wszystkie cenniki pod wspólne saldo i nowe nominały."""
    # 1. Podstawowe sklepy i trwałe narzędzia profesji.
    for item_id, price_silver in V0861_BASE_SHOP_PRICES_SILVER.items():
        item = ITEMS.get(item_id)
        if not item:
            continue
        item["price"] = int(price_silver)
        item["currency"] = "silver"

    # 2. Pełne 21 progów klasowego EQ: ceny rosną aż do poziomu mithrilowego.
    for item_id in CLASS_EQUIPMENT_ITEM_IDS:
        item = ITEMS.get(item_id)
        if not item:
            continue
        mastery = max(1, int(item.get("required_mastery", 1) or 1))
        base = V0861_CLASS_TIER_BASE_SILVER.get(mastery)
        if base is None:
            nearest = min(V0861_CLASS_TIER_BASE_SILVER, key=lambda key: abs(key - mastery))
            base = V0861_CLASS_TIER_BASE_SILVER[nearest]
        factor = V0861_CLASS_SLOT_PRICE_FACTOR.get(item.get("slot"), 1.0)
        item["price"] = max(1, int(round(base * factor)))
        item["currency"] = "silver"

    # 3. Skup surowców. Zwykłe srebrne ceny pozostają czytelne,
    #    a drogie surowce w złocie rosną łagodnie. Stary sprzedawalny
    #    mithril nie może destabilizować skali nagród pojedynczego surowca.
    for item in ITEMS.values():
        old_mithril = int(item.get("sell_mithril", 0) or 0)
        old_gold = int(item.get("sell_gold", 0) or 0)
        if old_mithril > 0:
            # Sprzedawalny przedmiot za dawny 1 mithril daje 100 000 złota,
            # a nie pełny mithril wart 1 000 000 złota.
            item["sell_gold"] = old_gold + old_mithril * 100_000
            item["sell_mithril"] = 0
            continue
        if old_gold > 10:
            if old_gold <= 50:
                new_gold = old_gold * 2
            elif old_gold <= 100:
                new_gold = old_gold * 3
            elif old_gold <= 250:
                new_gold = old_gold * 4
            else:
                new_gold = old_gold * 5
            item["sell_gold"] = int(new_gold)

    # 4. Stare słabe moby nie mogą wypłacać pełnego mithrilu.
    #    Prawdziwy mithril pozostaje u endgame bossów z co najmniej 500k HP.
    for mob_id, mob in MOB_TEMPLATES.items():
        mithril = int(mob.get("mithril", 0) or 0)
        if mithril <= 0:
            continue
        hp = max(1, int(mob.get("max_hp", 1) or 1))
        if hp >= 500_000 or mob_id.startswith("end_") or mob_id.startswith("mythic_"):
            continue
        if hp < 5_000:
            gold_per_legacy_mithril = 250
        elif hp < 25_000:
            gold_per_legacy_mithril = 1_000
        elif hp < 100_000:
            gold_per_legacy_mithril = 5_000
        else:
            gold_per_legacy_mithril = 20_000
        mob["gold"] = int(mob.get("gold", 0) or 0) + mithril * gold_per_legacy_mithril
        mob["mithril"] = 0


def rebalance_quest_rewards_v0862():
    """Przelicza wszystkie 119 questów na płynną skalę wspólnego salda."""
    for quest_id, quest in QUESTS.items():
        reward = None

        if quest_id in V0862_FIXED_QUEST_REWARDS_SILVER:
            reward = V0862_FIXED_QUEST_REWARDS_SILVER[quest_id]

        soul_level = int(quest.get("required_soul_level", 0) or 0)
        if soul_level:
            reward = V0862_SOUL_TRIAL_REWARD_SILVER.get(
                soul_level,
                v0862_nearest_progression_reward(soul_level),
            )

        tool_level = int(quest.get("min_tool_level", 0) or 0)
        if tool_level:
            reward = v0862_nearest_progression_reward(tool_level)
            kind = quest.get("kind")
            needed = max(1, int(quest.get("needed", 1) or 1))

            # Trudniejsze formy zadania płacą trochę więcej, ale nie tworzą
            # skoków o całe nominały. Liczba wymaganych przedmiotów ma tylko
            # łagodny wpływ, aby powtarzalnych questów nie dało się nadużywać.
            if kind == "craft_set":
                reward = int(reward * 2.5)
            elif kind in ("collect_category", "collect_distinct_category"):
                reward = int(reward * 1.25)
            elif kind == "collect":
                reward = int(reward * 1.10)
            elif kind == "collect_resource":
                reward = int(reward * 1.00)
            elif kind == "kill":
                reward = int(reward * 1.20)

            if needed >= 10:
                reward = int(reward * 1.20)
            elif needed >= 5:
                reward = int(reward * 1.10)

        # Awaryjnie każdy quest, którego nie opisuje jedna z powyższych grup,
        # zachowuje dotychczasową wartość, ale zostaje znormalizowany do
        # jednego salda. W praktyce v0.8.62 obejmuje wprost wszystkie 119.
        if reward is None:
            reward = legacy_currency_to_coins(
                quest.get("reward_silver", 0),
                quest.get("reward_gold", 0),
                quest.get("reward_mithril", 0),
            )

        quest["reward_silver"] = max(0, int(reward))
        quest["reward_gold"] = 0
        quest["reward_mithril"] = 0


def ensure_profession_quest_currency_v098():
    """v0.9.8: każdy quest profesyjny/rzemieślniczy ma pieniężną wypłatę.

    Istniejące wartości z pełnego rebalance v0.8.62 są autorytatywne i nie są
    zwiększane. Fallback uruchamia się wyłącznie dla definicji z zerową walutą,
    również dla przyszłych questów dopisanych po tej wersji.
    """
    changed = 0
    for quest in QUESTS.values():
        if not quest_is_profession_or_crafting_v098(quest):
            continue
        existing = legacy_currency_to_coins(
            quest.get("reward_silver", 0),
            quest.get("reward_gold", 0),
            quest.get("reward_mithril", 0),
        )
        if existing > 0:
            continue

        level = max(1, int(quest.get("min_profession_level", 1) or 1))
        needed = max(1, int(quest.get("needed", 1) or 1))
        reward = int(v0862_nearest_progression_reward(level))
        kind = quest.get("kind")
        if kind == "craft_set":
            reward = int(reward * 2.5)
        elif kind in ("collect_category", "collect_distinct_category"):
            reward = int(reward * 1.25)
        elif kind == "collect":
            reward = int(reward * 1.10)
        elif kind == "kill":
            reward = int(reward * 1.20)
        if needed >= 10:
            reward = int(reward * 1.20)
        elif needed >= 5:
            reward = int(reward * 1.10)

        quest["reward_silver"] = max(50, reward)
        quest["reward_gold"] = 0
        quest["reward_mithril"] = 0
        changed += 1
    return changed


def rebalance_paper_mobs_v0874():
    changed = []
    class_xp_fixed = 0
    for mob_id, template in MOB_TEMPLATES.items():
        if template.get("training_dummy"):
            continue
        # Bossowie piętrowi mają własne precyzyjne reguły HP i długie walki.
        if (
            template.get("crypt_boss") or template.get("astral_boss")
            or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss")
            or template.get("giant_fortress_boss")
        ):
            continue

        old_hp = max(1, int(template.get("max_hp", 1) or 1))
        damage = max(1, int(template.get("damage", 1) or 1))
        ratio = v0874_min_hp_damage_ratio(template)
        target_hp = int(math.ceil((damage * ratio) / 10.0) * 10)
        # Nigdy nie osłabiamy przeciwnika; ten pass ma tylko naprawiać
        # za krótkie walki. Dodatkowo pojedyncza korekta nie przekracza x3.
        new_hp = min(max(old_hp, target_hp), old_hp * 3)
        # Pomijamy kosmetyczne różnice poniżej 5 procent, żeby pass dotykał
        # wyłącznie przeciwników, których walka faktycznie była za krótka.
        if new_hp < int(math.ceil(old_hp * 1.05)):
            new_hp = old_hp

        old_class_xp = int(template.get("class_xp_reward", 0) or 0)
        baseline_class_xp = max(50, int(template.get("stat_reward", 0) or 0) * 10)
        if old_class_xp <= 0:
            template["class_xp_reward"] = baseline_class_xp
            old_class_xp = baseline_class_xp
            class_xp_fixed += 1

        if new_hp <= old_hp:
            continue

        hp_mult = new_hp / float(old_hp)
        # EXP rośnie wolniej niż samo HP, bo mob zachowuje ten sam damage,
        # drop i Postęp Rozwoju statystyk. Maksymalny wzrost x2.25.
        reward_mult = min(2.25, max(1.0, hp_mult ** 0.75))
        old_soul_xp = max(0, int(template.get("soul_reward", 0) or 0))
        template["max_hp"] = int(new_hp)
        template["class_xp_reward"] = max(
            old_class_xp, int(round(old_class_xp * reward_mult))
        )
        if old_soul_xp > 0:
            template["soul_reward"] = max(
                old_soul_xp, int(round(old_soul_xp * reward_mult))
            )
        template["v0874_durability_balanced"] = True
        template["v0874_hp_before"] = old_hp
        template["v0874_reward_multiplier"] = round(reward_mult, 4)
        changed.append(mob_id)
    return tuple(changed), class_xp_fixed

