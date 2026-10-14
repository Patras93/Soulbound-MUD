# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def refresh_help_v03021_full():
    """Finalna warstwa HELP. Nadpisuje historyczne teksty, które nie opisują już runtime."""
    HELP_TOPIC_ALIASES.update({
        "waluta":"waluta", "pieniadze":"waluta", "pieniądze":"waluta", "money":"waluta",
        "eq sklep":"sklepy", "sklep eq":"sklepy", "sklepy eq":"sklepy",
        "sell all":"sprzedaj_wszystko", "sprzedaj wszystko":"sprzedaj_wszystko",
    })
    HELP_TOPICS["waluta"] = [
        "Cała ekonomia używa jednego wspólnego salda. Nominały służą tylko do czytelnego wyświetlania i wpisywania kwot.",
        "100 srebra = 1 złota. 1 000 000 złota = 1 mithril. 1 mithril = 100 000 000 srebra.",
        "Gra zawsze normalizuje kwotę do najwyższych nominałów: 100 srebra jest czytane jako 1 złota; 250 srebra jako 2 złota, 50 srebra.",
        "Przy późnym endgame duże kwoty przechodzą automatycznie w mithril. Ta sama zasada działa przy zarabianiu, zakupie, sprzedaży, banku i innych kosztach.",
    ]
    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę aktualnego sprzedawcy.",
        "shop info <numer> / sklep info <numer> pokazuje pełny opis, statystyki, wymagania, cenę po rabacie i porównanie z założonym EQ.",
        "kup <nazwa> albo kup <numer> kupuje przedmiot; np. kup 9 albo kup 9 3.",
        "Klasowe sklepy EQ pokazują najlepszy Tier odblokowany przez Level postaci dla aktywnej klasy i wszystkie 13 typów: hełm, pancerz, rękawice, nogawice, buty, talizman, pierścień, naszyjnik, naramienniki, pas, peleryna, karwasze, kolczyki i relikt.",
        "sprzedaj <nazwa> sprzedaje jedną wolną sztukę. Założone EQ i Character-Bound są chronione.",
        "sell all / sprzedaj wszystko sprzedaje wyłącznie niezałożone EQ. Nie sprzedaje mikstur, consumables, zwykłego lootu, materiałów, narzędzi ani quest itemów.",
        "Zasoby profesyjne sprzedaje się osobno u właściwych fachowców; hurtowo działają istniejące komendy wszystko siatka/sakwa/stos/torba.",
        "Każda kwota sklepu jest czytana ze wspólnego salda po normalizacji mithril, złoto, srebro.",
    ]
    HELP_TOPICS["eq"] = [
        "equipment / eq pokazuje założone wyposażenie oraz Broń Duszy; eq info pokazuje szczegóły, bonusy, sockety i aktywne sety.",
        "Klasowe EQ ma 13 logicznych typów: hełm, pancerz, rękawice, nogawice, buty, talizman, pierścień, naszyjnik, naramienniki, pas, peleryna, karwasze, kolczyki i relikt.",
        "Pierścienie i talizmany zakładają się automatycznie: załóż <nazwa>, zp <numer> albo zt <numer> używa wolnego slotu; przy dwóch zajętych zastępuje słabszy.",
        "Ręczny wybór pozostaje: zp1/zp2 dla pierścieni oraz zt1/zt2 dla talizmanów.",
        "Skróty: zh hełm, zz zbroja, zr rękawice, zn nogi, zb buty, zna naszyjnik, zkol kolczyki auto, zkol1/zkol2 ręcznie, znar naramienniki, zpas pas, zpel peleryna, zkar karwasze, zrel relikt.",
        "Level postaci odblokowuje EQ na progach 1, 10, 20...400. Biegłość klasy nadal odblokowuje skille/spelle, ale nie jest bramą założenia EQ.",
    ]
    HELP_TOPICS["sety_klasowe"] = [
        "Każda z 14 klas ma klasowe linie EQ obejmujące 13 typów wyposażenia.",
        "Bonusy zestawów nadal mają progi 2/4/6/8 części. Nowe sloty zwiększają wybór i nie dodają kolejnego automatycznego progu mocy.",
        "Sety i ich tożsamość są ręcznie projektowane; Generator Core może balansować wyłącznie liczbowe wartości istniejących bonusów.",
    ]
    HELP_TOPICS["skille100_200"] = [
        "Historyczna nazwa tematu została zachowana jako alias. Obecnie Biegłość każdej klasy ma zakres 1-400.",
        "Każda klasa ma 123 skille/spelle: dokładnie 3 na każdy próg Biegłości 1, 10, 20...400.",
        "Sloty auto kolejki zależą od Character Level, nie od Biegłości: Level 1 ma 10 slotów, potem +1 co 10 Leveli, do 50 na Levelu 400.",
    ]
    # quest / questy mogą być osobnymi aliasami w zależności od historycznej warstwy.
    quest_help = [
        "quest / questy pokazuje aktywne zadania; quest ukończone pokazuje historię; quest list <NPC> pokazuje numerowaną ofertę NPC.",
        "quest accept <numer> przyjmuje zadanie. Każdy quest zaczyna od 0/x i liczy wyłącznie zdarzenia wykonane po przyjęciu.",
        "Questy nie mają globalnej blokady Character Level. Obowiązują tylko rzeczywiste wymagania konkretnego zadania, np. Soul, profesja, narzędzie, wcześniejszy quest lub fabuła.",
        "quest info <numer> pokazuje opis, cel, postęp, wymagania i wszystkie nagrody; quest oddaj <numer> oddaje gotowe zadanie właściwemu NPC.",
        "Nagrody pieniężne questów trafiają do jednego portfela i są zawsze czytane w znormalizowanych nominałach: mithril, potem złoto, potem srebro.",
        "Od v0.30.21 zwykły quest daje co najmniej równowartość 1 złota oraz resztę w srebrze; mithril pojawia się dopiero w późnej progresji/endgame.",
    ]
    HELP_TOPICS["quest"] = list(quest_help)
    HELP_TOPICS["questy"] = list(quest_help)
    HELP_TOPICS["sprzedaj_wszystko"] = [
        "sell all / sprzedaj wszystko sprzedaje tylko niezałożone EQ typu armor.",
        "Mikstury, inne consumables, zwykły loot, materiały, narzędzia, quest itemy i założone wyposażenie nie są przez tę komendę sprzedawane.",
    ]
    HELP_TOPICS["generator"] = [
        "Generator Core działa w trybie Numeric-Only z Whitelist Guard.",
        "Może zmieniać wyłącznie dozwolone liczby balansu: HP, damage, XP, ceny, nagrody, cooldowny, koszty many oraz wartości istniejących efektów/statów.",
        "Nie może zmieniać nazw, ID, unlocków, klas, slotów EQ, list dropów, celów questów, wymagań, składników receptur, Soul Milestones ani topologii świata.",
        "v0.30.21 koryguje wyłącznie numeryczną ekonomię questów i narzędzi; zasady Whitelist Guard pozostają bez zmian.",
    ]


def v03035_broken_blades_and_death_audit():
    errors = []
    quest = QUESTS.get("haldor_broken_blades_v0929", {})
    if quest.get("target") != "damaged_weapon_v0929" or int(quest.get("needed", 0) or 0) != 6:
        errors.append("broken blades target/needed")
    if not quest.get("repeatable"):
        errors.append("broken blades not repeatable")
    for mob_id in V03035_BROKEN_BLADE_SOURCES:
        template = MOB_TEMPLATES.get(mob_id)
        if not template:
            errors.append(f"missing source mob: {mob_id}")
            continue
        if v0929_kill_drop_item("haldor_broken_blades_v0929", mob_id, template) != "damaged_weapon_v0929":
            errors.append(f"source not recognized: {mob_id}")
    import inspect as _inspect_v03035
    die_src = _inspect_v03035.getsource(Session.die)
    forbidden = (
        "self.character.silver -=",
        "self.character.gold -=",
        "self.character.mithril -=",
        "remove_storage_item(",
        "clear_skill_buffs()",
    )
    for token in forbidden:
        if token in die_src:
            errors.append(f"death still removes state: {token}")
    # Phoenix Egg is not a death penalty: its source-authored Re-raise consumes
    # the egg only when it prevents the normal death/respawn flow. Any other
    # inventory removal from Session.die remains forbidden.
    for line in die_src.splitlines():
        if "remove_item(" not in line:
            continue
        if '"uoss_odin_unique_8"' in line or "'uoss_odin_unique_8'" in line:
            continue
        errors.append("death still removes state: remove_item(")
    return {
        "version": "0.30.35",
        "broken_blade_sources": len(V03035_BROKEN_BLADE_SOURCES),
        "error_count": len(errors),
        "errors": errors,
    }


def v03035_related_quest_flow_audit():
    errors = []
    recipe_outputs = {
        str(recipe.get("output"))
        for table in (CRAFT_RECIPES, COOK_RECIPES, ALCHEMY_RECIPES, JEWELCRAFT_RECIPES)
        for recipe in table.values()
        if recipe.get("output")
    }
    category_targets = {"fish", "fish_river", "fish_lake", "fish_sea", "fish_ocean", "ore", "wood", "herb"}
    checked = 0
    for quest_id, quest in QUESTS.items():
        kind = quest.get("kind")
        if kind == "collect":
            checked += 1
            target = quest.get("target")
            if target not in ITEMS:
                errors.append(f"{quest_id}: missing collect target {target}")
            if quest.get("track_craft_progress") and target not in recipe_outputs:
                errors.append(f"{quest_id}: craft target has no recipe {target}")
        elif kind == "collect_category":
            checked += 1
            if quest.get("target") not in category_targets:
                errors.append(f"{quest_id}: unknown category {quest.get('target')}")
        elif kind == "collect_resource":
            checked += 1
            if quest.get("target") not in ITEMS:
                errors.append(f"{quest_id}: missing resource {quest.get('target')}")
        elif kind == "collect_resource_set":
            checked += 1
            requirements = dict(quest.get("resource_targets") or {})
            if not requirements:
                errors.append(f"{quest_id}: empty resource set")
            if sum(max(1, int(v)) for v in requirements.values()) != int(quest.get("needed", 0) or 0):
                errors.append(f"{quest_id}: resource-set needed mismatch")
            for target in requirements:
                if target not in ITEMS:
                    errors.append(f"{quest_id}: missing set resource {target}")
        elif kind == "craft_set":
            checked += 1
            for target in quest.get("targets") or ():
                if target not in recipe_outputs:
                    errors.append(f"{quest_id}: craft-set target has no recipe {target}")

    special_sources = {
        "haldor_broken_blades_v0929": "damaged_weapon_v0929",
        "haldor_armor_recycling_v0929": "heavy_armor_fragment_v0929",
        "orin_toxic_glands_v0929": "toxic_gland_v0929",
    }
    source_counts = {}
    for quest_id, expected_item in special_sources.items():
        matches = 0
        for mob_id, template in MOB_TEMPLATES.items():
            if v0929_kill_drop_item(quest_id, mob_id, template) == expected_item:
                matches += 1
        source_counts[quest_id] = matches
        if matches <= 0:
            errors.append(f"{quest_id}: no kill sources")

    ordinary_item_sources = {
        "soul_shards": "soul_shard",
        "stolen_mountain_ores": "stolen_mountain_ore",
        "hourly_shadow_fangs": "wolf_fang",
    }
    for quest_id, item_id in ordinary_item_sources.items():
        if not any(item_id in (template.get("drops") or {}) for template in MOB_TEMPLATES.values()):
            errors.append(f"{quest_id}: no mob drop source for {item_id}")

    return {
        "version": "0.30.35",
        "quests_checked": checked,
        "special_source_counts": source_counts,
        "error_count": len(errors),
        "errors": errors,
    }


def apply_separate_class_shops_v03036():
    # 1. Wspólne sale przestają być sklepami.
    for room_id in OLD_SHARED_CLASS_SHOP_ROOMS_V03036:
        _catalog_mut.catalog_pop_path('SHOPS', SHOPS, (), room_id, None)
        SHOP_SELLERS.pop(room_id, None)
        room = ROOMS.get(room_id)
        if room:
            room["desc"] = str(room.get("desc") or "").replace(
                " W tej sali działa także klasowy sklep z pełnym 14-elementowym wyposażeniem.",
                " Sklepy EQ znajdują się w osobnych salach poszczególnych klas."
            )
    for npc_id in OLD_SHARED_CLASS_SHOP_SELLERS_V03036:
        npc = NPCS.get(npc_id)
        if npc:
            npc["shopkeeper"] = False
            npc["dialogue"] = (
                "Każda klasa ma teraz osobny sklep EQ w swojej własnej sali. "
                "Wpisz walk eq <klasa>, aby dojść bezpośrednio do właściwego sklepu."
            )

    # 2. Przebudowa mapowania: jeden pokój = dokładnie jedna klasa.
    CLASS_SHOP_CLASSES_BY_ROOM.clear()
    CLASS_SHOP_ITEMS_BY_ROOM.clear()

    for class_name, room_id in CLASS_SHOP_ROOM_BY_CLASS_V03036.items():
        if room_id not in ROOMS:
            raise RuntimeError(f"v0.30.36: brak sali sklepu klasy {class_name}: {room_id}")
        if class_name not in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER:
            raise RuntimeError(f"v0.30.36: brak EQ klasy {class_name}")

        CLASS_EQUIPMENT_SETS[class_name]["room"] = room_id
        CLASS_SHOP_CLASSES_BY_ROOM[room_id] = [class_name]
        tier_one = list(CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER[class_name].get(1, ()))
        CLASS_SHOP_ITEMS_BY_ROOM[room_id] = tier_one
        _catalog_mut.catalog_assign(list(tier_one), 'SHOPS', SHOPS, (room_id,))

        seller_id = "class_eq_shop_" + normalize_lookup_text(class_name).replace(" ", "_")
        seller_name = CLASS_SHOP_SELLER_NAMES_V03036[class_name]
        _catalog_mut.catalog_assign({
            "name": seller_name,
            "room": room_id,
            "dialogue": (
                f"Prowadzę osobny sklep EQ klasy {class_name}. "
                "Wpisz shop albo list, aby usłyszeć aktualny Tier wyposażenia "
                "odblokowany przez Level postaci."
            ),
            "shopkeeper": True,
            "class_eq_shop": class_name,
        }, 'NPCS', NPCS, (seller_id,))
        SHOP_SELLERS[room_id] = seller_id
        if isinstance(globals().get("NPC_DESCRIPTIONS"), dict):
            NPC_DESCRIPTIONS[seller_id] = (
                f"Sprzedawca wyposażenia wyłącznie dla klasy {class_name}. "
                "Oferta skaluje się z Levelem postaci, a zakup nadal wymaga aktywnej właściwej klasy."
            )

        room = ROOMS[room_id]
        shop_sentence = (
            f" Działa tu osobny sklep EQ klasy {class_name}; "
            "wpisz shop, aby usłyszeć ofertę."
        )
        if shop_sentence.strip() not in str(room.get("desc") or ""):
            room["desc"] = str(room.get("desc") or "") + shop_sentence

        # 3. Prowadzenie i stare skróty zawsze trafiają do nowego, osobnego sklepu.
        for prefix in ("eq", "sklep eq", "sklep z eq", "ekwipunek", "sklep"):
            GUIDE_DESTINATION_ALIASES[
                normalize_lookup_text(f"{prefix} {class_name}")
            ] = room_id

    # v1.20.2: The shared arcane *class EQ* shop was retired, but Selene is
    # also the Zaklinanie profession specialist. Restore her independent
    # single-tool shop after creating the separate Mag/Psionik EQ shops.
    # Without this, the v0.30.36 cleanup silently removes the Runic Focus
    # added by systems.professions and `list` says there is no shop.
    enchanting_room = "guild_arcane_chamber"
    enchanting_seller_id = "guild_quartermaster_arcane"
    _catalog_mut.catalog_assign(["runic_focus"], 'SHOPS', SHOPS, (enchanting_room,))
    SHOP_SELLERS[enchanting_room] = enchanting_seller_id
    enchanting_seller = NPCS[enchanting_seller_id]
    enchanting_seller["shopkeeper"] = True
    enchanting_seller["dialogue"] = (
        "Prowadzę Zaklinanie i sprzedaję Fokus Runiczny. "
        "Wpisz list albo shop, potem kup 1 lub kup fokus runiczny. "
        "Wyposażenie klasowe Maga i Psionika jest w osobnych salach."
    )
    enchanting_description = " U Selene kupisz Fokus Runiczny: list, kup 1."
    if enchanting_description.strip() not in str(ROOMS[enchanting_room].get("desc") or ""):
        ROOMS[enchanting_room]["desc"] = (
            str(ROOMS[enchanting_room].get("desc") or "") + enchanting_description
        )

    HELP_TOPICS["sklepy klasowe"] = [
        "Każda z 14 klas ma własny, osobny sklep EQ w swojej sali klasowej w Gildii Dusz.",
        "Wojownik, Berserker, Łotrzyk, Łowca, Mnich, Strażnik, Mag, Nekromanta, Kapłan, Czarownik, Druid i Psionik nie współdzielą już punktów sprzedaży.",
        "Najprościej użyć: walk eq <klasa>, na przykład walk eq wojownik albo walk eq kapłan.",
        "W sklepie wpisz shop. Oferta pokazuje najlepszy Tier EQ odblokowany przez Level postaci; zakup nadal wymaga aktywnej odpowiedniej klasy.",
    ]
    HELP_TOPICS.setdefault("eq", []).append(
        "v0.30.36: każda klasa ma osobny sklep EQ w swojej sali klasowej. Użyj walk eq <klasa>."
    )
    HELP_TOPICS.setdefault("sklepy", []).append(
        "v0.30.36: help sklepy klasowe opisuje 14 osobnych sklepów wyposażenia klasowego."
    )
    HELP_TOPICS.setdefault("wersja", []).append(
        "v0.30.36: rozdzielono klasowe sklepy EQ na 14 osobnych punktów, po jednym dla każdej klasy."
    )


def class_shop_audit_v03036():
    errors = []
    checked = 0
    if len(CLASS_SHOP_CLASSES_BY_ROOM) != 14:
        errors.append(f"shop room count={len(CLASS_SHOP_CLASSES_BY_ROOM)} expected=14")
    if set(CLASS_SHOP_ROOM_BY_CLASS_V03036) != set(CLASS_EQUIPMENT_SETS):
        missing = sorted(set(CLASS_EQUIPMENT_SETS) - set(CLASS_SHOP_ROOM_BY_CLASS_V03036))
        extra = sorted(set(CLASS_SHOP_ROOM_BY_CLASS_V03036) - set(CLASS_EQUIPMENT_SETS))
        errors.append(f"class mapping mismatch missing={missing} extra={extra}")

    for class_name, room_id in CLASS_SHOP_ROOM_BY_CLASS_V03036.items():
        checked += 1
        classes = list(CLASS_SHOP_CLASSES_BY_ROOM.get(room_id, ()))
        if classes != [class_name]:
            errors.append(f"{class_name}: room mapping={classes}")
        if CLASS_EQUIPMENT_SETS.get(class_name, {}).get("room") != room_id:
            errors.append(f"{class_name}: equipment set room mismatch")
        seller_id = SHOP_SELLERS.get(room_id)
        seller = NPCS.get(seller_id, {}) if seller_id else {}
        if not seller_id or seller.get("room") != room_id or not seller.get("shopkeeper"):
            errors.append(f"{class_name}: missing active seller")
        for level in (1, 10, 100, 200, 300, 400, 600):
            tier = class_equipment_unlocked_tier(level)
            offers = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.get(class_name, {}).get(tier, ())
            if not offers:
                errors.append(f"{class_name}: no offers at level {level}")
                continue
            wrong = [iid for iid in offers if ITEMS.get(iid, {}).get("required_class") != class_name]
            if wrong:
                errors.append(f"{class_name}: foreign items at level {level}: {wrong[:3]}")
        for prefix in ("eq", "sklep eq", "sklep z eq", "ekwipunek", "sklep"):
            key = normalize_lookup_text(f"{prefix} {class_name}")
            if GUIDE_DESTINATION_ALIASES.get(key) != room_id:
                errors.append(f"{class_name}: guide alias {key!r} points elsewhere")

    for room_id in OLD_SHARED_CLASS_SHOP_ROOMS_V03036:
        if room_id in CLASS_SHOP_CLASSES_BY_ROOM:
            errors.append(f"old shared room still class shop: {room_id}")
        if room_id == "guild_arcane_chamber":
            # Zaklinanie has a real profession-tool vendor here; it must not
            # bring back the old mixed Mag/Psionik class EQ catalogue.
            if SHOPS.get(room_id) != ["runic_focus"]:
                errors.append("arcane profession shop must sell only runic_focus")
            seller = NPCS.get("guild_quartermaster_arcane", {})
            if (SHOP_SELLERS.get(room_id) != "guild_quartermaster_arcane"
                    or seller.get("room") != room_id or not seller.get("shopkeeper")):
                errors.append("arcane profession shop has no active Selene")
            continue
        if SHOPS.get(room_id):
            errors.append(f"old shared room still sells items: {room_id}")
        if SHOP_SELLERS.get(room_id):
            errors.append(f"old shared room still has seller mapping: {room_id}")

    return {
        "version": "0.30.36",
        "class_shops_checked": checked,
        "shop_room_count": len(CLASS_SHOP_CLASSES_BY_ROOM),
        "error_count": len(errors),
        "errors": errors,
    }


def refresh_material_stat_profiles_v03037():
    """Finalna warstwa po Generator Core: 24 różne profile statów per materiał/slot.

    Generator Core może numerycznie wyrównać wartości istniejących statów. Tutaj zachowujemy
    jego całkowity budżet możliwie blisko, ale rozkładamy go na 24 różne podzbiory statów.
    Dzięki temu żadna para wariantów tego samego materiału i slotu nie jest statystyczną kopią.
    """
    from itertools import combinations
    for tier in CORPSE_MATERIAL_TIERS:
        ids = CORPSE_MATERIAL_ITEM_IDS.get(tier["key"], ())
        for slot in CORPSE_MATERIAL_SLOT_DEFS:
            rows = [
                (item_id, ITEMS[item_id]) for item_id in ids
                if ITEMS.get(item_id, {}).get("slot") == slot
            ]
            rows.sort(key=lambda row: int(row[1].get("corpse_random_variant", 0) or 0))
            order = tuple(MATERIAL_SLOT_STAT_PREFERENCES.get(slot, MATERIAL_RANDOM_STAT_POOL))
            patterns = []
            # 5 singletonów + 10 par + pierwsze 9 trójek = dokładnie 24 unikalne układy kluczy.
            for size in (1, 2, 3):
                for combo in combinations(order, size):
                    patterns.append(combo)
                    if len(patterns) == CORPSE_RANDOM_VARIANTS_PER_SLOT:
                        break
                if len(patterns) == CORPSE_RANDOM_VARIANTS_PER_SLOT:
                    break
            if len(patterns) != CORPSE_RANDOM_VARIANTS_PER_SLOT:
                raise RuntimeError(f"v0.30.37: za mało wzorców statów dla {slot}")

            for index, (item_id, item) in enumerate(rows):
                combo = patterns[index]
                old_total = sum(max(0, int(v or 0)) for v in (item.get("stats") or {}).values())
                # Nie osłabiamy przedmiotu; bardzo niski budżet może wzrosnąć maksymalnie do 3,
                # żeby unikalny układ statów był możliwy także na Żelazie/Stali.
                budget = max(len(combo), old_total)
                values = {stat: 1 for stat in combo}
                remaining = budget - len(combo)
                pos = index % len(combo)
                while remaining > 0:
                    stat = combo[pos % len(combo)]
                    values[stat] += 1
                    pos += 1
                    remaining -= 1
                item["stats"] = values
                variant = int(item.get("corpse_random_variant", index + 1) or index + 1)
                req = int(item.get("required_character_level", item.get("required_mastery", 1)) or 1)
                item["name"] = _material_variant_title(tier, slot, values, variant, req)
                stat_text = ", ".join(
                    f"{MATERIAL_STAT_NAMES.get(stat, stat)} +{amount}" for stat, amount in values.items()
                )
                prop_text = ", ".join(
                    f"{MATERIAL_PROPERTY_NAMES.get(prop, prop)} +{amount}%"
                    for prop, amount in (item.get("properties") or {}).items()
                )
                item["desc"] = (
                    f"Materiałowe EQ z ciała przeciwnika. Wymaga Levelu postaci {req}. "
                    f"Slot ma własny profil, a wariant nie powtarza statów innego wariantu tego samego materiału/slotu. "
                    f"Obrona +{int(item.get('defense', 0) or 0)}. Statystyki: {stat_text}. "
                    f"Właściwości: {prop_text or 'brak dodatkowych'} ."
                )


def equipment_completeness_audit_v03037():
    errors = []
    logical_slots = set(CLASS_EQUIPMENT_SLOT_DEFS)
    expected_slots = {
        "head", "body", "shield", "hands", "legs", "feet", "charm", "ring", "necklace",
        "earring", "shoulders", "belt", "cloak", "bracers", "bracelet", "accessory", "relic",
    }
    if logical_slots != expected_slots:
        errors.append(f"class logical slots={sorted(logical_slots)} expected={sorted(expected_slots)}")
    if set(CORPSE_MATERIAL_SLOT_DEFS) != expected_slots:
        errors.append("material corpse slots do not match full logical slot set")

    material_names = set()
    material_items = 0
    duplicate_profiles = []
    for tier in CORPSE_MATERIAL_TIERS:
        ids = CORPSE_MATERIAL_ITEM_IDS.get(tier["key"], ())
        expected_count = len(expected_slots) * CORPSE_RANDOM_VARIANTS_PER_SLOT
        if len(ids) != expected_count:
            errors.append(f"{tier['key']}: item count={len(ids)} expected={expected_count}")
        for slot in expected_slots:
            rows = [ITEMS[i] for i in ids if ITEMS.get(i, {}).get("slot") == slot]
            if len(rows) != CORPSE_RANDOM_VARIANTS_PER_SLOT:
                errors.append(f"{tier['key']} {slot}: variants={len(rows)} expected={CORPSE_RANDOM_VARIANTS_PER_SLOT}")
                continue
            sigs = [tuple(sorted((k, int(v)) for k, v in (row.get("stats") or {}).items())) for row in rows]
            if len(set(sigs)) != len(sigs):
                duplicate_profiles.append(f"{tier['key']}:{slot}")
            for row in rows:
                material_items += 1
                n = normalize_lookup_text(row.get("name", ""))
                if n in material_names:
                    errors.append(f"duplicate material EQ name: {row.get('name')}")
                material_names.add(n)
    if duplicate_profiles:
        errors.append("duplicate material stat profiles: " + ", ".join(duplicate_profiles[:20]))

    # Class EQ must expose earrings on representative levels for all 14 classes.
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        for level in (1, 100, 200, 300, 400, 600):
            ids = tiers.get(class_equipment_unlocked_tier(level), ())
            slots = {ITEMS[i].get("slot") for i in ids if i in ITEMS}
            if "earring" not in slots:
                errors.append(f"{class_name} level {level}: missing class earring")
                break

    # Jewelcrafting must offer earrings throughout its tier table.
    jewel_earrings = [i for i, item in ITEMS.items() if item.get("slot") == "earring" and item.get("jewelcraft_level")]
    if len(jewel_earrings) < len(JEWELCRAFTING_TIERS):
        errors.append(f"jewelcraft earrings={len(jewel_earrings)} tiers={len(JEWELCRAFTING_TIERS)}")

    for slot in ("earring", "earring1", "earring2"):
        if slot not in EQUIPMENT_SLOT_NAMES:
            errors.append(f"missing display slot {slot}")
    for alias in ("zkol", "zkol1", "zkol2"):
        if alias not in COMMAND_ALIASES:
            errors.append(f"missing earring shortcut {alias}")

    # Krypta i Wieża Astralna również muszą używać pełnych 17 slotów.
    for tier in (1, 20, 40):
        crypt_slots = {ITEMS.get(f"crypt_t{tier}_{slot}", {}).get("slot") for slot in expected_slots}
        if crypt_slots != expected_slots:
            errors.append(f"crypt tier {tier}: incomplete slots {sorted(expected_slots - crypt_slots)}")
    for tier in (1, 6, 11):
        astral_slots = {ITEMS.get(f"astral_t{tier}_{slot}", {}).get("slot") for slot in expected_slots}
        if astral_slots != expected_slots:
            errors.append(f"astral tier {tier}: incomplete slots {sorted(expected_slots - astral_slots)}")

    # Żadna nazwa pancerza/EQ w całej grze nie może się powtarzać.
    armor_names = {}
    duplicate_armor_names = []
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        key = normalize_lookup_text(item.get("name", ""))
        previous = armor_names.get(key)
        if previous is not None:
            duplicate_armor_names.append((previous, item_id, item.get("name", "")))
        else:
            armor_names[key] = item_id
    if duplicate_armor_names:
        errors.append("duplicate armor names: " + repr(duplicate_armor_names[:10]))

    # Reprezentatywny klasowy Tier: każdy slot musi mieć odmienny pełny profil
    # (obrona + Attack/Magic Attack + staty + właściwości), więc nowe sloty nie
    # są mechanicznymi kopiami. Od v1.13.8 płaska moc jest częścią realnej
    # tożsamości slotu i musi być uwzględniana przez ten audit.
    class_profiles_checked = 0
    for class_name, tiers in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        ids = list(tiers.get(class_equipment_unlocked_tier(200), ()))
        # Pierwsza linia stylistyczna: po jednej części z każdego slotu.
        first_style = {}
        for iid in ids:
            item = ITEMS.get(iid, {})
            if int(item.get("class_equipment_style", 1) or 1) == 1:
                first_style.setdefault(item.get("slot"), item)
        if set(first_style) != expected_slots:
            errors.append(f"{class_name}: incomplete representative class profile")
            continue
        signatures = []
        for slot in sorted(expected_slots):
            item = first_style[slot]
            signatures.append((
                int(item.get("defense", 0) or 0),
                int(item.get("attack", 0) or 0),
                int(item.get("magic_attack", 0) or 0),
                item.get("affix"), int(item.get("affix_amount", 0) or 0),
                tuple(sorted((item.get("stats") or {}).items())),
                tuple(sorted((item.get("properties") or {}).items())),
            ))
        class_profiles_checked += len(signatures)
        if len(set(signatures)) != len(signatures):
            slots_sorted = sorted(expected_slots)
            grouped = {}
            for slot, signature in zip(slots_sorted, signatures):
                grouped.setdefault(signature, []).append(slot)
            duplicates = [group for group in grouped.values() if len(group) > 1]
            errors.append(
                f"{class_name}: duplicated slot profiles at Level 200: {duplicates}"
            )

    return {
        "version": "0.30.37",
        "logical_slot_count": len(expected_slots),
        "material_items_checked": material_items,
        "material_name_count": len(material_names),
        "global_armor_name_count": len(armor_names),
        "class_profiles_checked": class_profiles_checked,
        "materials": len(CORPSE_MATERIAL_TIERS),
        "variants_per_material_slot": CORPSE_RANDOM_VARIANTS_PER_SLOT,
        "error_count": len(errors),
        "errors": errors,
    }


def profession_carryover_audit_v03039():
    errors = []
    pool_checks = 0
    positive_weights = 0
    thresholds = tuple(int(v) for v in TOOL_TIER_THRESHOLDS)

    groups = {
        "rzeka": tuple(RIVER_FISH_ATLAS),
        "jezioro": tuple(LAKE_FISH_ATLAS),
        "morze": tuple(SEA_FISH_ATLAS),
        "ocean": tuple(OCEAN_FISH_ATLAS),
        "rudy": tuple(ORE_RESOURCE_IDS),
        "drewno": tuple(WOOD_RESOURCE_IDS),
        "ziola": tuple(HERB_RESOURCE_IDS),
        "klejnoty": tuple(
            iid for iid, item in ITEMS.items()
            if item.get("type") == "gem_raw" and not item.get("gem_quality")
        ),
    }
    final_sizes = {}
    for label, ids in groups.items():
        previous = set()
        for level in thresholds:
            pool = tuple(balance_math.resource_pool(ids, ITEMS, level, f"audit:{label}"))
            pool_checks += 1
            current = set(pool)
            if not previous.issubset(current):
                errors.append(f"{label}: zasób zniknął przy Tierze dla levelu {level}")
            weights = balance_math.resource_weights(pool, ITEMS, level, f"audit:{label}")
            if len(weights) != len(pool):
                errors.append(f"{label}: niezgodna liczba wag na levelu {level}")
            for item_id, weight in zip(pool, weights):
                if float(weight) <= 0:
                    errors.append(f"{label}: zerowa waga {item_id} na levelu {level}")
                else:
                    positive_weights += 1
            previous = current
        final_sizes[label] = len(previous)

    # Specjalne łowisko nie może wycinać gatunków ze zwykłej kumulacyjnej puli.
    forest_pref = set(FISHING_ECOLOGY_PREFERRED_IDS.get("forest_stream") or ())
    river_low = set(balance_math.resource_pool(tuple(RIVER_FISH_ATLAS), ITEMS, thresholds[0], "audit:forest"))
    river_high = set(balance_math.resource_pool(tuple(RIVER_FISH_ATLAS), ITEMS, thresholds[-1], "audit:forest"))
    if not river_low.issubset(river_high):
        errors.append("forest_stream: wcześniejsze ryby nie są podzbiorem późniejszej puli")
    if forest_pref and not (forest_pref & river_high):
        errors.append("forest_stream: preferencje ekologiczne nie przecinają puli rzecznej")

    recipe_count = 0
    forbidden_max_keys = (
        "max_profession_level", "max_tool_level", "max_level",
        "maximum_profession_level", "maximum_tool_level",
    )
    for table_name, table in (
        ("craft", CRAFT_RECIPES), ("cook", COOK_RECIPES),
        ("alchemy", ALCHEMY_RECIPES), ("jewel", JEWELCRAFT_RECIPES),
    ):
        for recipe_id, recipe in table.items():
            recipe_count += 1
            for key in forbidden_max_keys:
                if recipe.get(key) not in (None, 0, ""):
                    errors.append(f"{table_name}:{recipe_id}: górny limit {key}")

    # Quest Marcela: pełna baza gatunków rzecznych + ich rzadkie warianty.
    recipe = COOK_RECIPES.get("grilled_river_fish", {})
    pool = set(recipe.get("pooled_ingredient_pool") or ())
    expected = {
        item_id for item_id in FISH_STORAGE_IDS
        if base_fish_species_id(item_id) in RIVER_FISH_ATLAS
    }
    missing = expected - pool
    if missing:
        errors.append("Pieczona ryba rzeczna: brakuje ryb: " + ", ".join(sorted(missing)[:20]))
    if int(recipe.get("pooled_ingredient_count", 0) or 0) != 2:
        errors.append("Pieczona ryba rzeczna: wymaganie nie wynosi 2 ryb")
    if recipe.get("distinct_ingredient_pool"):
        errors.append("Pieczona ryba rzeczna nadal wymaga różnych gatunków")

    race_topics = 0
    for race_name, *_rest in RACES:
        slug = "rasa_" + normalize_lookup_text(race_name).replace(" ", "_")
        if slug not in HELP_TOPICS:
            errors.append(f"brak help rasy: {race_name}")
        else:
            race_topics += 1

    return {
        "version": "0.30.39",
        "race_topics": race_topics,
        "pool_checks": pool_checks,
        "positive_weights_checked": positive_weights,
        "recipes_checked": recipe_count,
        "river_recipe_pool_size": len(pool),
        "river_base_species": len(RIVER_FISH_ATLAS),
        "final_pool_sizes": final_sizes,
        "error_count": len(errors),
        "errors": errors,
    }


def bulk_smelting_ingot_smithing_audit_v0357():
    errors=[]
    metrics={}
    try:
        import inspect
        source=inspect.getsource(SessionCraftingExpansionV03114Mixin.smelt_item_v03114)
        executor=inspect.getsource(SessionCraftingExpansionV03114Mixin._smelt_execute_v1124)
        combined=source + "\n" + executor
        # v1.12.4: public handler manages status/stop and delegates the actual
        # bulk contract to a task executor. Keep the historical v0.35.7 guarantees,
        # but accept the interruptible wait that replaces a raw asyncio.sleep.
        metrics["bulk_single_action"] = (
            "przetopów w jednej akcji" in combined
            and (
                "await asyncio.sleep(action_seconds)" in combined
                or "await self.smelt_wait_v1124(action_seconds)" in combined
            )
        )
        metrics["pooled_xp"] = "pooled_profession_xp" in combined and "pooled_tool_xp" in combined
        metrics["includes_direct_ore"] = 'recipe_ids = [tier["ingot"] for tier in BLACKSMITH_TIERS]' in combined
        metrics["includes_steel_plates"] = 'recipe_ids.append("recycled_steel_ingot")' in combined
        metrics["includes_salvage"] = "SALVAGE_SMELT_FALLBACK_V03113.values()" in combined
        for key,value in metrics.items():
            if not value:
                errors.append(f"bulk smelting audit failed: {key}")

        ingot_ids={str(tier.get("ingot")) for tier in BLACKSMITH_TIERS}
        ingot_ids.add("steel_ingot")
        checked=0
        for recipe_id,recipe in CRAFT_RECIPES.items():
            output=ITEMS.get(recipe.get("output"),{})
            if output.get("type") != "armor":
                continue
            category=str(recipe.get("category") or "")
            # Tech equipment has its own component/alloy economy. This gate covers
            # the normal blacksmith equipment line and the historical forge charms.
            if category in ("technology","tech_set","salvage_forging"):
                continue
            if "forge" not in tuple(recipe.get("stations") or ()):
                continue
            profession=str(recipe.get("profession") or "Kowalstwo")
            tool_type=str(recipe.get("tool_type") or "crafting")
            if profession != "Kowalstwo" or tool_type != "crafting":
                continue
            checked+=1
            ingredients=set((recipe.get("ingredients") or {}).keys())
            raw_ores=[iid for iid in ingredients if str(iid).endswith("_ore") or str(iid).startswith("ore_")]
            if raw_ores:
                errors.append(f"kowalskie EQ używa surowej rudy {recipe_id}: {raw_ores}")
            if not (ingredients & ingot_ids):
                errors.append(f"kowalskie EQ bez sztabki {recipe_id}: {sorted(ingredients)}")
        metrics["smith_equipment_recipes_checked"] = checked
        if checked < 10:
            errors.append(f"za mało receptur kowalskiego EQ w audicie: {checked}")
    except Exception as exc:
        errors.append(f"bulk smelting/ingot smithing audit exception: {type(exc).__name__}: {exc}")
    return {"version":"0.35.7","error_count":len(errors),"errors":errors,"metrics":metrics}


def progression_600_and_leader_disband_audit_v0360():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")

    caps={
        "generator": int(getattr(balance_math,"MAX_LEVEL",0) or 0),
        "character": int(CHARACTER_MAX_LEVEL),
        "class_mastery": int(CLASS_MASTERY_MAX_LEVEL),
        "skill": int(SKILL_MAX_LEVEL),
        "soul": int(SOUL_MAX_LEVEL),
        "soul_weapon_mastery": int(SOUL_WEAPON_MASTERY_MAX_LEVEL),
        "profession": int(PROFESSION_MAX_LEVEL),
        "tool": int(TOOL_MAX_LEVEL),
        "guild": int(V0926_GUILD_MAX_LEVEL),
    }
    metrics["caps"]=caps
    check("all_main_caps_800", all(v==800 for v in caps.values()), caps)
    check("soul_tiers_80", int(SOUL_MAX_TIER)==80 and len(SOUL_TIER_THRESHOLDS)==80 and int(SOUL_TIER_THRESHOLDS[-1])==800)
    check("tool_tiers_80", int(TOOL_MAX_TIER)==80 and len(TOOL_TIER_THRESHOLDS)==80 and int(TOOL_TIER_THRESHOLDS[-1])==800)
    check("profession_rank_cap_800", int(PROFESSION_RANK_THRESHOLDS[-1])==800)
    check("profession_count_14", len(PROFESSION_RANK_NAMES)>=14, len(PROFESSION_RANK_NAMES))
    check("all_tool_name_tables_80", all(len(tuple(v))>=80 for v in TOOL_TIER_NAMES.values()), {k:len(tuple(v)) for k,v in TOOL_TIER_NAMES.items()})

    grid=(1,*range(10,801,10))
    skill_errors=[]
    for class_name,rows in CLASS_SKILLS.items():
        unlocks=[int(row.get("unlock",0) or 0) for row in rows]
        counts={level:unlocks.count(level) for level in grid}
        # Generator Core guarantees the 183-skill base grid through 600.
        # Source-authored abilities may legally extend that catalogue, so the
        # release contract is a minimum rather than an exact total.
        if len(rows)<243 or min(unlocks or [0])!=1 or max(unlocks or [0])!=800:
            skill_errors.append(f"{class_name}:{len(rows)}:{min(unlocks or [0])}-{max(unlocks or [0])}")
        if class_name not in ("Mec","Inżynier") and any(counts[level]<3 for level in grid):
            skill_errors.append(f"{class_name}:grid")
    check("skill_grid_243_per_class", not skill_errors, skill_errors[:10])
    metrics["classes"]=len(CLASS_SKILLS)
    metrics["skills_total"]=sum(len(v) for v in CLASS_SKILLS.values())

    check("class_equipment_to_800", int(CLASS_EQUIPMENT_MASTERY_LEVELS[-1])==800)

    # v0.36.0: każdy kolejny Tier klasowego EQ ma realnie inny, rosnący
    # budżet podstawowych statów. Chroni szczególnie niskie progi
    # 1/10/20/30, które wcześniej mogły powtarzać te same wartości.
    eq_stat_progression_errors=[]
    for class_name, per_tier in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        previous={}
        for required_level in CLASS_EQUIPMENT_MASTERY_LEVELS:
            for item_id in per_tier.get(required_level, ()):
                item=ITEMS.get(item_id,{})
                key=(int(item.get("class_equipment_style",1) or 1), str(item.get("slot") or ""))
                budget=int(item.get("affix_amount",0) or 0) + sum(
                    int(v or 0) for v in (item.get("stats") or {}).values()
                )
                if key in previous and budget <= previous[key][1]:
                    eq_stat_progression_errors.append(
                        f"{class_name}:{key[0]}:{key[1]}:{previous[key][0]}={previous[key][1]} -> {required_level}={budget}"
                    )
                previous[key]=(int(required_level),budget)
    check("class_equipment_stats_rise_every_tier", not eq_stat_progression_errors, eq_stat_progression_errors[:20])

    low_tier_budgets={}
    for class_name, per_tier in CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.items():
        row=[]
        for required_level in (1,10,20,30):
            ids=tuple(per_tier.get(required_level,()))
            if not ids:
                row.append(None); continue
            item=ITEMS[ids[0]]
            row.append(int(item.get("affix_amount",0) or 0) + sum(int(v or 0) for v in (item.get("stats") or {}).values()))
        low_tier_budgets[class_name]=row
    check("class_equipment_low_tiers_1_10_20_30_distinct",
          all(None not in row and row==sorted(set(row)) and len(row)==4 for row in low_tier_budgets.values()),
          low_tier_budgets)

    check("endgame_resources_to_800",
          any(int(level)==800 for level,_ in ENDGAME_ORE_UNLOCKS)
          and any(int(level)==800 for level,_ in ENDGAME_WOOD_UNLOCKS)
          and any(int(level)==800 for level,_ in ENDGAME_HERB_UNLOCKS))
    check("soul_trials_41_80", all(tier in SOUL_TRIAL_QUEST_IDS for tier in range(41,81)))
    check("guild_bonus_legacy_preserved",
          v0926_guild_bonus_percent(100)==11 and v0926_guild_bonus_percent(200)==15
          and v0926_guild_bonus_percent(300)==19 and v0926_guild_bonus_percent(400)==23
          and v0926_guild_bonus_percent(600)==29 and v0926_guild_bonus_percent(800)==35,
          [v0926_guild_bonus_percent(x) for x in (100,200,300,400,600,800)])
    check("guild_cost_monotonic_extension",
          v0926_guild_upgrade_cost(399)>0 and v0926_guild_upgrade_cost(400)>=v0926_guild_upgrade_cost(399)
          and v0926_guild_upgrade_cost(500)>=v0926_guild_upgrade_cost(400)
          and v0926_guild_upgrade_cost(799)>=v0926_guild_upgrade_cost(600)
          and v0926_guild_upgrade_cost(800)==0)

    try:
        import inspect
        src=inspect.getsource(SessionMovementPartySocialMixin.leave_party)
        check("leader_leave_disbands", "self.server.parties.pop(key, None)" in src and "Drużyna została rozwiązana" in src)
        check("leader_leave_no_transfer", "new_leader" not in src and "min(members)" not in src and "next(iter(members" not in src)
    except Exception as exc:
        errors.append(f"leader source audit: {type(exc).__name__}: {exc}")

    return {"version":"0.36.0","error_count":len(errors),"errors":errors,"metrics":metrics}


def terrain_threat_rebalance_audit_v0362():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")
    try:
        import inspect
        # Every currently materialized authored recommendation must be honored
        # by the numeric room stage used by combat generation.
        bad=[]
        checked=0
        for rid, room in ROOMS.items():
            try:
                rec=int(room.get("recommended_mastery",0) or 0)
                stage=int(room.get("generator_level",0) or 0)
            except Exception:
                continue
            if rec>0:
                checked+=1
                if stage < rec:
                    bad.append((rid,rec,stage))
        metrics["recommended_rooms_checked"]=checked
        check("recommended_mastery_is_balance_floor", not bad, str(bad[:10]))

        # v1.13.22: validate behavior, not the historical wrapper/function name.
        # The recommended mastery floor is now native to Generator Core's
        # runtime_room_level(), so old _v0362 marker/name checks are obsolete.
        _probe_room={"recommended_mastery":137}
        _probe_stage=balance_math.runtime_room_level(
            "__audit_v0362_recommended_floor__", _probe_room, {}
        )
        check(
            "runtime_room_recommended_floor",
            int(_probe_stage) >= 137 and int(_probe_room.get("generator_level",0) or 0) >= 137,
            f"stage={_probe_stage}, stored={_probe_room.get('generator_level')}",
        )

        wsrc=inspect.getsource(World._terrain_scaled_template_v0362)
        check("room_stage_runtime_clone", "stage > base_stage" in wsrc and "runtime_mob_balance" in wsrc)
        check("terrain_hp_growth", "1.0 + runtime_stage / 100.0" in wsrc and "min(4.0" in wsrc)
        check("terrain_damage_growth", "runtime_stage / 1000.0" in wsrc and "min(0.50" in wsrc)
        check("bosses_not_extra_terrain_scaled", 'rank in ("normal", "elite", "rare")' in wsrc)

        csrc=inspect.getsource(v0190_apply_combat_template)
        check("terrain_multiplier_survives_runtime_refresh", "terrain_runtime_clone_v0362" in csrc and "terrain_hp_multiplier_v0362" in csrc)

        # Concrete curve anchors used by the terrain layer.
        def hp_mult(stage): return min(4.0, 1.0 + stage / 100.0)
        def dmg_mult(stage): return 1.0 + min(0.50, stage / 1000.0)
        check("terrain_100_hp_x2", abs(hp_mult(100)-2.0)<1e-9)
        check("terrain_100_damage_x1_10", abs(dmg_mult(100)-1.10)<1e-9)
        check("terrain_300_hp_cap_x4", abs(hp_mult(300)-4.0)<1e-9)
    except Exception as exc:
        errors.append(f"terrain threat source audit: {type(exc).__name__}: {exc}")
    return {"version":"0.36.2","error_count":len(errors),"errors":errors,"metrics":metrics}


def independent_skill_cooldowns_audit_v0364():
    errors=[]
    metrics={}
    def check(name, condition, detail=None):
        metrics[name]=bool(condition)
        if not condition:
            errors.append(f"{name}: {detail or 'FAIL'}")
    try:
        import inspect
        all_rows=[]
        seen={}
        duplicates=[]
        for class_name, rows in (CLASS_SKILLS or {}).items():
            for skill in rows:
                sid=str(skill.get("id") or "")
                all_rows.append((class_name, sid, skill.get("name")))
                if not sid:
                    errors.append(f"skill without id: {class_name}/{skill.get('name')}")
                    continue
                if sid in seen:
                    duplicates.append((sid, seen[sid], (class_name, skill.get("name"))))
                else:
                    seen[sid]=(class_name, skill.get("name"))
        check("all_skill_ids_unique", not duplicates, duplicates[:5])
        metrics["skill_count"] = len(all_rows)
        metrics["unique_skill_ids"] = len(seen)

        csrc=inspect.getsource(SessionCoreProgressionMixin.start_skill_cooldown_v0364)
        check("single_id_write", 'self.skill_cooldowns[skill_id] = ready_at' in csrc)
        check("no_category_cooldown_keys", all(
            token not in csrc for token in ('physical_cooldown','magic_cooldown','class_cooldown','global_cooldown')
        ))

        usrc=inspect.getsource(SessionSkillsCombatMixin.use_class_skill)
        check("manual_skill_reads_own_cd", 'skill_cooldown_ready_at_v0364(skill)' in usrc)
        check("manual_skill_starts_own_cd", 'start_skill_cooldown_v0364(skill, effective_cooldown, now)' in usrc)
        qsrc=inspect.getsource(SessionSkillsCombatMixin.auto_queue_skill_usable)
        check("queue_reads_own_cd", 'skill_cooldown_ready_at_v0364(skill)' in qsrc)
        hsrc=inspect.getsource(SessionMovementPartySocialMixin.auto_priest_heal_option)
        check("auto_heal_reads_own_cd", 'skill_cooldown_ready_at_v0364(skill)' in hsrc)
        h2src=inspect.getsource(SessionMovementPartySocialMixin.perform_auto_priest_heal)
        check("auto_heal_starts_own_cd", 'start_skill_cooldown_v0364(skill, effective_cooldown, now)' in h2src)

        # Behavior test: starting B must not alter A, and restarting A must not alter B.
        class Dummy:
            skill_cooldowns={}
            skill_cooldown_ready_at_v0364=SessionCoreProgressionMixin.skill_cooldown_ready_at_v0364
            skill_cooldown_remaining_v0364=SessionCoreProgressionMixin.skill_cooldown_remaining_v0364
            skill_cooldown_active_v0364=SessionCoreProgressionMixin.skill_cooldown_active_v0364
            start_skill_cooldown_v0364=SessionCoreProgressionMixin.start_skill_cooldown_v0364
        d=Dummy(); d.skill_cooldowns={}
        d.start_skill_cooldown_v0364('audit_skill_a', 10, 100.0)
        a1=d.skill_cooldown_ready_at_v0364('audit_skill_a')
        d.start_skill_cooldown_v0364('audit_skill_b', 20, 100.0)
        a2=d.skill_cooldown_ready_at_v0364('audit_skill_a')
        b1=d.skill_cooldown_ready_at_v0364('audit_skill_b')
        d.start_skill_cooldown_v0364('audit_skill_a', 5, 101.0)
        b2=d.skill_cooldown_ready_at_v0364('audit_skill_b')
        check("behavior_independent_a_after_b", a1 == a2 == 110.0)
        check("behavior_independent_b_after_a", b1 == b2 == 120.0)
        check("behavior_only_two_keys", set(d.skill_cooldowns)=={'audit_skill_a','audit_skill_b'})
    except Exception as exc:
        errors.append(f"independent cooldown audit: {type(exc).__name__}: {exc}")
    return {"version":"0.36.4","error_count":len(errors),"errors":errors,"metrics":metrics}

