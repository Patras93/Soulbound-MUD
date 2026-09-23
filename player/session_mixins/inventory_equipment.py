# -*- coding: utf-8 -*-
"""Inventory, equipment, consumables, gems and player transfers."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import random
from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, currency_reading_text, currency_unit_multiplier
from core.mines_threat import EQUIPMENT_SLOT_ALIASES, EQUIPMENT_SLOT_NAMES, ITEMS, is_character_bound_item
from core.progression_600 import CLASS_MASTERY_MAX_LEVEL, SOUL_MAX_LEVEL, SOUL_MAX_TIER
from network.protocol_gameplay_utils import (
    V03042_EQ_UPGRADE_MAX,
    find_by_name,
    normalize_lookup_text,
    v03042_upgrade_defense_bonus,
    v03042_upgrade_primary_stat,
    v03042_upgrade_stat_bonus,
    v03042_upgraded_display_name,
)
from player.session_mixins.equipment_stats import moogle_board_stat_bonus_v0313
from systems.crafting_quality import ensure_crafting_quality_variant_v0332, player_item_display_name_v0335
from systems.dungeons_regions import CRYPT_AFFIXES
from systems.equipment_crafting import (
    CLASS_SET_STAT_NAMES,
    CUT_GEM_IDS,
    GEM_AFFIX_NAMES,
    GEM_DEFINITIONS,
    GEM_QUALITY_ORDER,
    GEODE_DEFINITIONS,
    GEODE_IDS,
    JEWELCRAFT_RECIPES,
    gem_quality_item_id,
    jewelry_socket_capacity,
)
from systems.items_resources import CLASS_EQUIPMENT_SETS
from world.generation_systems import V014_TREASURE_MAP_ITEM


class SessionInventoryEquipmentMixin:
    def equipped_quantity_of_item(self, item_id):
            return sum(
                1 for row in self.server.db.equipment(self.account_id)
                if row["item_id"] == item_id
            )

    def free_equipment_quantity(self, item_id):
            return max(
                0,
                self.server.db.item_qty(self.account_id, item_id)
                - self.equipped_quantity_of_item(item_id),
            )

    def resolve_transferable_equipment(self, query):
            transferable = {
                item_id: item
                for item_id, item in ITEMS.items()
                if (
                    item.get("type") == "armor"
                    and not is_character_bound_item(item_id)
                    and self.free_equipment_quantity(item_id) > 0
                )
            }
            return find_by_name(transferable, query)

    def free_transferable_quantity(self, item_id):
            total = self.server.db.item_qty(self.account_id, item_id)
            item = ITEMS.get(item_id, {})
            if item.get("type") == "armor":
                total -= self.equipped_quantity_of_item(item_id)
            return max(0, int(total))

    def resolve_transferable_inventory_item(self, query):
            transferable = {
                item_id: item
                for item_id, item in ITEMS.items()
                if (
                    self.free_transferable_quantity(item_id) > 0
                    and not is_character_bound_item(item_id)
                    and item.get("type") != "quest"
                )
            }
            return find_by_name(transferable, query)

    def parse_player_currency_transfer(self, payload):
            """Zwraca (amount_silver, opis) lub None, gdy payload nie jest walutą."""
            words = str(payload or "").strip().split()
            if len(words) < 2:
                return None
            amount = None
            unit = None
            if words[0].isdigit():
                amount = int(words[0])
                unit = " ".join(words[1:])
            elif words[-1].isdigit():
                amount = int(words[-1])
                unit = " ".join(words[:-1])
            else:
                return None
            multiplier = currency_unit_multiplier(unit)
            if multiplier is None:
                return None
            if amount <= 0:
                return (0, "")
            total = amount * int(multiplier)
            if total > CURRENCY_SQLITE_SAFE_TOTAL:
                return (CURRENCY_SQLITE_SAFE_TOTAL + 1, "")
            return total, currency_reading_text(total, 0, 0, full_names=True)

    async def give_player(self, raw):
            """Przekazuje walutę albo zwykły przedmiot graczowi stojącemu obok."""
            text = str(raw or "").strip()
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                await self.send(
                    "Użycie: daj <gracz> <przedmiot>; daj <gracz> <ilość> <przedmiot>; "
                    "daj <gracz> <ilość> złota."
                )
                return

            target_name, payload = parts[0].strip(), parts[1].strip()
            target = self.server.find_character_session(target_name)
            if target is None or target.closed or not target.character:
                await self.send(f"Gracz {target_name} nie jest teraz online.")
                return
            if target is self or target.account_id == self.account_id:
                await self.send("Nie możesz przekazać przedmiotu ani waluty samemu sobie.")
                return
            if target.character.room_id != self.character.room_id:
                await self.send(
                    f"{target.character.name} nie znajduje się w tej samej lokacji. "
                    "Przekazywanie działa tylko między graczami stojącymi obok."
                )
                return

            currency = self.parse_player_currency_transfer(payload)
            if currency is not None:
                amount_silver, description = currency
                if amount_silver <= 0:
                    await self.send("Kwota musi być większa od zera.")
                    return
                if amount_silver > CURRENCY_SQLITE_SAFE_TOTAL:
                    await self.send("Ta kwota jest zbyt duża.")
                    return
                sender_total = int(self.server.db.shared_wallet_for_character(self.account_id)[0])
                if sender_total < amount_silver:
                    await self.send(
                        "Nie masz wystarczającej ilości waluty. Masz: "
                        + currency_reading_text(sender_total, 0, 0, full_names=True)
                        + "."
                    )
                    return
                if not self.server.db.transfer_shared_currency(
                    self.account_id, target.account_id, amount_silver
                ):
                    await self.send("Nie udało się przekazać waluty. Nic nie zostało zmienione.")
                    return
                self.server.db.apply_shared_wallet_to_character(self.character)
                self.server.db.apply_shared_wallet_to_character(target.character)
                await self.send(
                    f"Przekazujesz graczowi {target.character.name}: {description}.",
                    history_category="system",
                )
                await target.send(
                    f"{self.character.name} przekazuje ci: {description}.",
                    history_category="system",
                )
                return

            qty = 1
            item_query = payload
            item_parts = payload.split(maxsplit=1)
            if item_parts and item_parts[0].isdigit():
                qty = int(item_parts[0])
                item_query = item_parts[1].strip() if len(item_parts) > 1 else ""
            if qty <= 0 or not item_query:
                await self.send("Ilość przedmiotów musi być dodatnia i trzeba podać nazwę przedmiotu.")
                return

            found = self.resolve_transferable_inventory_item(item_query)
            if not found:
                owned = {
                    item_id: item
                    for item_id, item in ITEMS.items()
                    if self.server.db.item_qty(self.account_id, item_id) > 0
                }
                owned_found = find_by_name(owned, item_query)
                if owned_found:
                    item_id, item = owned_found
                    if is_character_bound_item(item_id):
                        await self.send(
                            f"{item['name']} jest przypisany do postaci i nie może być przekazany."
                        )
                    elif item.get("type") == "quest":
                        await self.send(
                            f"{item['name']} jest przedmiotem questowym i nie może być przekazany."
                        )
                    elif self.free_transferable_quantity(item_id) <= 0:
                        await self.send(
                            f"{item['name']} jest założony. Najpierw zdejmij wolną sztukę z EQ."
                        )
                    else:
                        await self.send("Tego przedmiotu nie można teraz przekazać.")
                else:
                    await self.send(
                        "Nie rozpoznaję takiego przedmiotu w twoim inventory. "
                        "Podaj pełną nazwę; ilość wpisz przed nazwą, np. daj Arven 3 Mikstura Leczenia."
                    )
                return

            item_id, item = found
            free_qty = self.free_transferable_quantity(item_id)
            if free_qty < qty:
                await self.send(
                    f"Masz tylko {free_qty} wolnych sztuk: {item['name']}."
                )
                return

            if not self.server.db.transfer_inventory_item(
                self.account_id, target.account_id, item_id, qty
            ):
                await self.send("Nie udało się przekazać przedmiotu. Nic nie zostało zmienione.")
                return

            # Zachowaj istniejące dane reforgingu/run tylko wtedy, gdy ostatnia
            # sztuka konkretnego EQ opuszcza konto nadawcy.
            if (
                item.get("type") == "armor"
                and self.server.db.item_qty(self.account_id, item_id) <= 0
            ):
                self.server.db.transfer_equipment_crafting_v0925(
                    self.account_id, target.account_id, item_id
                )

            quantity_text = f"{qty} x " if qty != 1 else ""
            await self.send(
                f"Przekazujesz graczowi {target.character.name}: {quantity_text}{item['name']}.",
                history_category="system",
            )
            await target.send(
                f"{self.character.name} przekazuje ci: {quantity_text}{item['name']}.",
                history_category="system",
            )

    async def give_equipment(self, raw):
            # Zgodność wsteczna z dawną nazwą handlera v0.9.17.
            await self.give_player(raw)

    async def inventory(self):
            rows = self.server.db.inventory(self.account_id)
            # v0.33.16: inventory pokazuje tylko WOLNE sztuki.
            # Baza zachowuje łączną ilość przedmiotu, również gdy konkretna sztuka
            # jest aktualnie założona. Odejmujemy więc każdą sztukę obecną w EQ
            # wyłącznie na potrzeby prezentacji inventory. Dzięki temu dwa identyczne
            # pierścienie/talizmany/kolczyki są liczone poprawnie sztuka po sztuce.
            equipped_counts = {}
            for equipped in self.server.db.equipment(self.account_id):
                equipped_id = str(equipped["item_id"])
                equipped_counts[equipped_id] = equipped_counts.get(equipped_id, 0) + 1

            await self.send(
                "Waluta: "
                + currency_reading_text(
                    self.character.silver, self.character.gold, self.character.mithril,
                    full_names=True, include_zero=True,
                )
                + "."
            )
            await self.send(
                "Siatka na ryby, Sakwa górnicza, Stos drewna, Torba Zielarska "
                "i Szkatułka Rzemieślnicza są osobnymi magazynami; użyj siatka/net, "
                "sakwa/bag, drewno/stos, ziola/herbs oraz szkatułka/craftbox."
            )
            visible_rows = []
            for row in rows:
                item_id = str(row["item_id"])
                visible_quantity = max(
                    0,
                    int(row["quantity"]) - int(equipped_counts.get(item_id, 0)),
                )
                if visible_quantity > 0:
                    visible_rows.append((row, visible_quantity))

            if not visible_rows:
                await self.send("Ekwipunek jest pusty.")
                return
            await self.send("Ekwipunek:")
            for row, visible_quantity in visible_rows:
                item = ITEMS.get(row["item_id"]) or ensure_crafting_quality_variant_v0332(row["item_id"]) or {"name": player_item_display_name_v0335(row["item_id"]), "desc": ""}
                bound_text = (
                    " Przypisany do postaci; nie można oddać ani wyrzucić."
                    if is_character_bound_item(row["item_id"])
                    else ""
                )
                await self.send(
                    f"{item['name']} x{visible_quantity}. "
                    f"{item.get('desc','')}{bound_text}"
                )

    async def equipment(self, mode=""):
            mode = self.normalize_description_query(mode)
            if mode in ("auto", "automatycznie", "najlepsze", "best"):
                await self.auto_equip_best_v03040()
                return
            detailed = mode in (
                "info", "pelne", "pełne", "szczegoly", "szczegóły", "details"
            )
            rows = self.server.db.equipment(self.account_id)

            await self.send("EQ INFO" if detailed else "EQ")
            c = self.character
            soul_line = (
                f"Broń Duszy: {c.soul_weapon}. "
                f"Soul Poziom {c.soul_level}/{SOUL_MAX_LEVEL}. "
                f"Soul Tier {c.soul_tier}/{SOUL_MAX_TIER}. "
                f"Moc {c.soul_power()}."
            )
            if detailed:
                if c.soul_level < SOUL_MAX_LEVEL:
                    soul_line += f" Soul XP {c.soul_xp} z {c.soul_xp_to_next()}."
                else:
                    soul_line += " Soul XP maksimum."
                soul_line += f" Bonus klasowy: {c.soul_weapon_class_bonus_text()}."
            await self.send(soul_line)

            if not rows:
                await self.send("Nie masz założonego dodatkowego wyposażenia.")
        
            slot_names = {
                "head": "Głowa", "body": "Korpus", "hands": "Dłonie",
                "legs": "Nogi", "feet": "Stopy", "charm": "Talizman",
                "charm1": "Talizman 1", "charm2": "Talizman 2",
                "ring": "Pierścień", "ring1": "Pierścień 1",
                "ring2": "Pierścień 2", "necklace": "Naszyjnik",
                "earring1": "Kolczyk 1", "earring2": "Kolczyk 2",
                "shoulders": "Naramienniki", "belt": "Pas", "cloak": "Peleryna",
                "bracers": "Karwasze", "relic": "Relikt", "board": "Board",
            }
            for row in rows:
                item = ITEMS.get(row["item_id"]) or ensure_crafting_quality_variant_v0332(row["item_id"])
                upgrade_level = self.server.db.equipment_upgrade_level_v03042(
                    self.account_id, row["item_id"]
                ) if item else 0
                base_name = item["name"] if item else player_item_display_name_v0335(row["item_id"])
                name = v03042_upgraded_display_name(base_name, upgrade_level)
                defense = (
                    int(item.get("defense", 0) or 0)
                    + v03042_upgrade_defense_bonus(item, upgrade_level)
                    if item else 0
                )
                slot_name = slot_names.get(row["slot"], row["slot"])
                if not detailed:
                    socket_short = ""
                    if item and item.get("slot") in ("ring", "necklace"):
                        capacity = jewelry_socket_capacity(item)
                        occupied = len(self.socketed_gem_rows_for_item(row["slot"], row["item_id"]))
                        socket_short = f" Gniazda {occupied}/{capacity}."
                    await self.send(f"{slot_name}: {name}. Obrona +{defense}.{socket_short}")
                    continue

                extra = ""
                if item and upgrade_level > 0:
                    upgrade_stat = v03042_upgrade_primary_stat(
                        item,
                        str((self.server.db.equipment_reforge(self.account_id, row["item_id"]) or {}).get("affix") or item.get("affix") or ""),
                    )
                    upgrade_amount = v03042_upgrade_stat_bonus(upgrade_level)
                    stat_label = CLASS_SET_STAT_NAMES.get(upgrade_stat, upgrade_stat)
                    extra += (
                        f" Ulepszenie Kowalstwa +{upgrade_level}/{V03042_EQ_UPGRADE_MAX}: "
                        f"obrona po ulepszeniu +{defense}"
                        + (f", {stat_label} +{upgrade_amount}." if upgrade_amount > 0 else ".")
                    )
                if item and item.get("rarity_name"):
                    extra += f" Rzadkość: {item['rarity_name']}."
                if item and item.get("affix"):
                    affix_name = CRYPT_AFFIXES.get(item["affix"], item["affix"])
                    extra += f" Bonus: {affix_name} +{item.get('affix_amount', 0)}."
                if item and item.get("stats"):
                    fixed_stats = ", ".join(
                        f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                        for stat, amount in item.get("stats", {}).items()
                        if int(amount or 0) != 0
                    )
                    if fixed_stats:
                        extra += f" Statystyki bazowe: {fixed_stats}."
                if row["item_id"] == "moogle_board" and item and item.get("cyborg_board_scaling") == "mec_mastery":
                    _mb = moogle_board_stat_bonus_v0313(self.class_mastery_level("Mec"))
                    extra += f" Skalowanie Moogle Board: Biegłość Meca {self.class_mastery_level('Mec')}/{CLASS_MASTERY_MAX_LEVEL}, +{_mb} do Siły, Zręczności, Kondycji, Inteligencji i Siły Woli."
                if item and item.get("slot") in ("ring", "necklace"):
                    extra += " " + self.jewelry_socket_text(row["slot"], row["item_id"], item)
                await self.send(f"{slot_name}: {name}. Obrona +{defense}.{extra}")

            if not detailed:
                await self.send(
                    f"Łączna obrona fizyczna: {self.defense()}. Wpisz eq info po bonusy, sety i sockety."
                )
                return

            bonuses = self.equipment_bonus_totals()
            await self.send(
                f"Łączna obrona fizyczna: {self.defense()}. Obrona magiczna: {self.magic_defense()}."
            )
            await self.send(
                "Łączne bonusy EQ i socketów: "
                f"Siła +{bonuses['strength']}, Zręczność +{bonuses['dexterity']}, "
                f"Kondycja +{bonuses['constitution']}, Inteligencja +{bonuses['intelligence']}, "
                f"Siła Woli +{bonuses['willpower']}, HP +{bonuses['hp']}, Mana +{bonuses['mana']}."
            )
            await self.send(
                f"Efektywne staty: Siła {self.effective_strength()}, Zręczność {self.effective_dexterity()}, "
                f"Kondycja {self.effective_constitution()}, Inteligencja {self.effective_intelligence()}, "
                f"Siła Woli {self.effective_willpower()}."
            )
            await self.send(self.crypt_set_bonus_text())
            await self.send(self.astral_set_bonus_text())
            for line in self.class_set_status_lines():
                await self.send(line)
            for line in self.regional_set_status_lines():
                await self.send(line)
            await self.send("Regionalne sety mają progi 2/4/6. Komenda sety pokazuje progi 2/4/6/8 wszystkich zestawów klasowych.")
            await self.send("Komenda gniazda pokazuje dokładnie osadzone klejnoty w biżuterii.")

    async def show_class_sets(self, query=""):
            q = self.normalize_description_query(query)
            counts = self.class_set_counts()

            if q in ("", "aktywne", "active"):
                await self.send("SETY KLASOWE")
                any_set = False
                for class_name in self.active_class_names():
                    count = int(counts.get(class_name, 0))
                    if count <= 0:
                        continue
                    any_set = True
                    await self.send(
                        f"{class_name}: {count}/14 części. Bonusy kończą się na progu 8. "
                        f"{self.class_set_threshold_text(class_name)}."
                    )
                if not any_set:
                    await self.send("Nie masz założonej części aktywnego setu klasowego.")
                await self.send(
                    "Wpisz sety info po wszystkie 12 zestawów albo sety <klasa>."
                )
                return

            if q in ("info", "wszystkie", "all", "pelne", "pełne"):
                await self.send("SETY KLASOWE 2/4/6/8 - WSZYSTKIE KLASY")
                for class_name in CLASS_EQUIPMENT_SETS:
                    set_name = CLASS_EQUIPMENT_SETS[class_name]["set_name"]
                    await self.send(
                        f"{class_name}, Zestaw {set_name}. "
                        f"{self.class_set_threshold_text(class_name)}."
                    )
                return

            found = None
            for class_name in CLASS_EQUIPMENT_SETS:
                if q == self.normalize_description_query(class_name):
                    found = class_name
                    break
            if not found:
                await self.send(
                    "Nie rozpoznaję klasy. Wpisz sety info po listę wszystkich 12 zestawów."
                )
                return

            set_name = CLASS_EQUIPMENT_SETS[found]["set_name"]
            count = int(counts.get(found, 0))
            await self.send(
                f"SET {found}: Zestaw {set_name}. Masz założone {count}/14 części; bonusy aktywują się na 2/4/6/8."
            )
            await self.send(self.class_set_threshold_text(found) + ".")
            await self.send(
                "Czternaście logicznych części to: głowa, korpus, dłonie, nogi, stopy, talizman, "
                "pierścień, naszyjnik, kolczyki, naramienniki, pas, peleryna, karwasze i relikt. "
                "Drugi taki sam talizman, pierścień ani kolczyk nie zwiększa licznika setu."
            )

    def equipment_item_score(self, item):
            if not item:
                return (-1, -1, -1, "")
            rarity_order = {
                "common": 0,
                "crafted": 1,
                "rare": 2,
                "epic": 3,
                "legendary": 4,
                "mythic": 5,
                "unique": 6,
                "eternal": 7,
            }
            stat_power = int(item.get("affix_amount", 0) or 0) + sum(
                max(0, int(v or 0)) for v in (item.get("stats") or {}).values()
            )
            return (
                int(item.get("defense", 0) or 0),
                rarity_order.get(item.get("rarity"), 0),
                stat_power,
                normalize_lookup_text(item.get("name", "")),
            )

    def auto_equipment_score_v03040(self, item, item_id=None):
            """Porównanie indywidualnej mocy EQ dla opcjonalnego trybu auto.

            Nie zmienia balansu przedmiotów. Uwzględnia obronę, bazowe staty,
            właściwości procentowe, affix, rarity oraz pojemność gniazd biżuterii.
            """
            if not item or item.get("type") != "armor":
                return (-1, -1, -1, -1, -1, "")
            rarity_order = {
                "common": 0, "crafted": 1, "uncommon": 1, "rare": 2,
                "epic": 3, "legendary": 4, "mythic": 5, "unique": 6,
                "eternal": 7,
            }
            upgrade_level = (
                self.server.db.equipment_upgrade_level_v03042(self.account_id, item_id)
                if item_id else 0
            )
            defense = max(0, int(item.get("defense", 0) or 0)) + v03042_upgrade_defense_bonus(item, upgrade_level)
            stats = sum(max(0, int(v or 0)) for v in (item.get("stats") or {}).values())
            stats += v03042_upgrade_stat_bonus(upgrade_level)
            props = sum(max(0, int(v or 0)) for v in (item.get("properties") or {}).values())
            affix = max(0, int(item.get("affix_amount", 0) or 0))
            rarity = rarity_order.get(str(item.get("rarity") or "").lower(), 0)
            sockets = 0
            if item.get("slot") in ("ring", "earring", "necklace"):
                try:
                    sockets = max(0, int(jewelry_socket_capacity(item)))
                except Exception:
                    sockets = 0
            total = defense * 12 + stats * 8 + props * 10 + affix * 8 + rarity * 5 + sockets * 3
            return (
                total, defense, stats + affix, props, rarity,
                normalize_lookup_text(item.get("name", "")),
            )

    def auto_equipment_eligible_v03040(self, item):
            if not item or item.get("type") != "armor":
                return False
            required_class = item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                return False
            if not self.equipment_mastery_requirement_met(item):
                return False
            return True

    async def auto_equip_best_v03040(self):
            """Jednym poleceniem zakłada indywidualnie najmocniejsze dostępne EQ.

            Działa wyłącznie na posiadanych i aktualnie dozwolonych przedmiotach.
            Podwójne sloty respektują faktyczną liczbę posiadanych kopii.
            """
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz automatycznie zmieniać EQ podczas aktywnej walki. "
                    "Najpierw zakończ walkę albo użyj flee."
                )
                return

            active_classes = set(self.active_class_names())
            owned = {}
            for item_id, item in ITEMS.items():
                if item.get("type") != "armor":
                    continue
                qty = int(self.server.db.item_qty(self.account_id, item_id) or 0)
                if qty <= 0:
                    continue
                required_class = item.get("required_class")
                if required_class and required_class not in active_classes:
                    continue
                required_race = item.get("required_race")
                if required_race and str(self.character.race) != str(required_race):
                    continue
                if not self.equipment_mastery_requirement_met(item):
                    continue
                owned[item_id] = (item, qty)

            if not owned:
                await self.send("AUTO EQ: nie masz żadnego dostępnego EQ do założenia.")
                return

            changes = []
            returned_gems = []
            single_slots = (
                "head", "body", "hands", "legs", "feet", "necklace",
                "shoulders", "belt", "cloak", "bracers", "relic", "board",
            )

            for slot in single_slots:
                candidates = [
                    (self.auto_equipment_score_v03040(item, item_id), item_id, item)
                    for item_id, (item, qty) in owned.items()
                    if qty > 0 and item.get("slot") == slot
                ]
                if not candidates:
                    continue
                candidates.sort(key=lambda row: row[0], reverse=True)
                _score, best_id, best_item = candidates[0]
                old_id = self.server.db.equipped_item(self.account_id, slot)
                old_item = ITEMS.get(old_id) if old_id else None
                if old_id == best_id:
                    continue
                if old_item and self.auto_equipment_score_v03040(old_item, old_id) >= self.auto_equipment_score_v03040(best_item, best_id):
                    continue
                if slot == "necklace" and old_id:
                    returned_gems.extend(await self.return_socketed_gems(slot, old_id))
                self.server.db.equip(self.account_id, slot, best_id)
                changes.append((slot, old_item.get("name", old_id) if old_item else "pusty", best_item.get("name", best_id)))

            duals = {
                "ring": ("ring1", "ring2"),
                "charm": ("charm1", "charm2"),
                "earring": ("earring1", "earring2"),
            }
            for logical_slot, pair in duals.items():
                # v0.33.11: dual-slot auto-equip must compare the two currently
                # equipped pieces as well as owned inventory candidates. Older
                # saves may have equipped jewelry whose inventory quantity is 0,
                # and those pieces must still participate in the ranking.
                candidate_counts = {}
                candidate_items = {}
                for item_id, (item, qty) in owned.items():
                    item_slot = str(item.get("slot") or "")
                    if item_slot not in (logical_slot, pair[0], pair[1]):
                        continue
                    candidate_counts[item_id] = max(candidate_counts.get(item_id, 0), max(0, int(qty)))
                    candidate_items[item_id] = item

                current_by_slot = {}
                equipped_counts = {}
                for slot in pair:
                    cur = self.server.db.equipped_item(self.account_id, slot)
                    if not cur:
                        continue
                    current_by_slot[slot] = cur
                    cur_item = ITEMS.get(cur)
                    if not cur_item:
                        continue
                    cur_slot = str(cur_item.get("slot") or "")
                    if cur_slot not in (logical_slot, pair[0], pair[1]):
                        continue
                    candidate_items[cur] = cur_item
                    equipped_counts[cur] = equipped_counts.get(cur, 0) + 1

                for item_id, count in equipped_counts.items():
                    candidate_counts[item_id] = max(candidate_counts.get(item_id, 0), count)

                expanded = []
                for item_id, count in candidate_counts.items():
                    item = candidate_items.get(item_id)
                    if not item:
                        continue
                    for _ in range(min(2, max(0, int(count)))):
                        expanded.append((self.auto_equipment_score_v03040(item, item_id), item_id, item))
                if not expanded:
                    continue
                expanded.sort(key=lambda row: row[0], reverse=True)
                selected = expanded[:2]

                # Build the desired top-two multiset.
                wanted_counts = {}
                selected_score = {}
                for score, item_id, item in selected:
                    wanted_counts[item_id] = wanted_counts.get(item_id, 0) + 1
                    selected_score[item_id] = score

                desired = {}
                # Preserve an existing ring only when that exact copy belongs to
                # the final top-two set. This prevents needless slot shuffling.
                remaining = dict(wanted_counts)
                for slot in pair:
                    cur = current_by_slot.get(slot)
                    if cur and remaining.get(cur, 0) > 0:
                        desired[slot] = cur
                        remaining[cur] -= 1

                rest = []
                for score, item_id, item in selected:
                    if remaining.get(item_id, 0) > 0:
                        rest.append((score, item_id, item))
                        remaining[item_id] -= 1

                # Fill empty/non-top slots with the strongest remaining pieces.
                for slot in pair:
                    if slot not in desired and rest:
                        _score, item_id, _item = rest.pop(0)
                        desired[slot] = item_id

                for slot in pair:
                    target_id = desired.get(slot)
                    if not target_id:
                        continue
                    old_id = self.server.db.equipped_item(self.account_id, slot)
                    if old_id == target_id:
                        continue
                    target_item = ITEMS[target_id]
                    old_item = ITEMS.get(old_id) if old_id else None
                    if logical_slot in ("ring", "earring") and old_id:
                        returned_gems.extend(await self.return_socketed_gems(slot, old_id))
                    self.server.db.equip(self.account_id, slot, target_id)
                    changes.append((slot, old_item.get("name", old_id) if old_item else "pusty", target_item.get("name", target_id)))

            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())

            if not changes:
                await self.send("AUTO EQ: masz już najmocniejsze dostępne indywidualne części według statystyk EQ.")
                return

            await self.send(f"AUTO EQ: zmieniono {len(changes)} slotów.")
            for slot, old_name, new_name in changes:
                await self.send(
                    f"{EQUIPMENT_SLOT_NAMES.get(slot, slot)}: {old_name} -> {new_name}."
                )
            if returned_gems:
                await self.send(
                    f"Z wymienionej biżuterii zwrócono {len(returned_gems)} klejnotów do Szkatułki Rzemieślniczej."
                )
            await self.send(
                "Auto EQ porównuje indywidualną moc części: obronę, statystyki, właściwości, affix, rarity i gniazda. "
                "Nie zmienia przedmiotów niedostępnych przez Poziom postaci lub klasę."
            )

    def owned_armor_for_slot(self, slot):
            candidates = []
            if slot in ("ring1", "ring2"):
                logical_slot = "ring"
            elif slot in ("charm1", "charm2"):
                logical_slot = "charm"
            elif slot in ("earring1", "earring2"):
                logical_slot = "earring"
            else:
                logical_slot = slot
            for item_id, item in ITEMS.items():
                if item.get("type") != "armor":
                    continue
                if item.get("slot") != logical_slot:
                    continue
                # Lista wyboru pokazuje wszystkie posiadane części tego slotu,
                # również te jeszcze zablokowane Biegłością/klasą. Dzięki temu
                # komenda slotowa nigdy nie "wybiera za gracza" tylko dlatego,
                # że część posiadanych opcji jest chwilowo niedostępna. Walidacja
                # klasy i Biegłości następuje dopiero po podaniu konkretnej nazwy.
                quantity = self.server.db.item_qty(
                    self.account_id, item_id
                )
                if quantity <= 0:
                    continue

                score = self.equipment_item_score(item)
                candidates.append((score, item_id, item))

            candidates.sort(key=lambda entry: entry[0], reverse=True)
            return candidates

    def resolve_equipment_for_equip(self, query):
            """Resolve only an explicitly selected item.

            v0.9.16 deliberately does not pick the strongest item for the player.
            Slot-only commands are handled in equip_item so they can list choices.
            """
            owned_armor = {
                item_id: item
                for item_id, item in ITEMS.items()
                if (
                    item.get("type") == "armor"
                    and self.server.db.item_qty(self.account_id, item_id) > 0
                )
            }
            return find_by_name(owned_armor, query)

    def explicit_dual_slot_and_item_query(self, query):
            """Return (slot, remaining item query) for numbered ring/charm/earring syntax.

            Accepted examples:
            - załóż pierścień 1 <nazwa>
            - załóż <nazwa> pierścień 1
            - equip ring2 <name>
            - equip <name> charm1
            """
            raw = str(query or "").strip()
            normalized = self.normalize_description_query(raw)
            aliases = (
                ("pierścień 1", "ring1"), ("pierscien 1", "ring1"),
                ("ring 1", "ring1"), ("ring1", "ring1"),
                ("pierścień 2", "ring2"), ("pierscien 2", "ring2"),
                ("ring 2", "ring2"), ("ring2", "ring2"),
                ("talizman 1", "charm1"), ("charm 1", "charm1"), ("charm1", "charm1"),
                ("talizman 2", "charm2"), ("charm 2", "charm2"), ("charm2", "charm2"),
                ("kolczyk 1", "earring1"), ("earring 1", "earring1"), ("earring1", "earring1"),
                ("kolczyk 2", "earring2"), ("earring 2", "earring2"), ("earring2", "earring2"),
            )
            for alias, slot in aliases:
                alias_norm = self.normalize_description_query(alias)
                prefix = alias_norm + " "
                suffix = " " + alias_norm
                if normalized.startswith(prefix):
                    # Slice by words rather than normalized character count so Polish diacritics are safe.
                    alias_words = len(alias.split())
                    rest = " ".join(raw.split()[alias_words:]).strip()
                    return slot, rest
                if normalized.endswith(suffix):
                    alias_words = len(alias.split())
                    rest = " ".join(raw.split()[:-alias_words]).strip()
                    return slot, rest
            return None, raw

    def equipment_choices_text(self, candidates):
            names = []
            seen = set()
            for _score, _item_id, item in candidates:
                name = item.get("name", "")
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
            return ", ".join(names)

    def equipped_jewelry(self, slot):
            if slot in ("ring", "earring"):
                pair = ("ring1", "ring2") if slot == "ring" else ("earring1", "earring2")
                slot = pair[0] if self.server.db.equipped_item(self.account_id, pair[0]) else pair[1]
            valid = ("ring1", "ring2", "earring1", "earring2", "necklace")
            if slot not in valid:
                return None, None
            item_id = self.server.db.equipped_item(self.account_id, slot)
            item = ITEMS.get(item_id) if item_id else None
            if slot in ("ring1", "ring2"):
                logical = "ring"
            elif slot in ("earring1", "earring2"):
                logical = "earring"
            else:
                logical = slot
            if not item or item.get("slot") != logical:
                return None, None
            return item_id, item

    def socketed_gem_rows_for_item(self, slot, item_id):
            return list(
                self.server.db.socketed_gems(
                    self.account_id,
                    slot,
                    item_id,
                )
            )

    def jewelry_socket_text(self, slot, item_id, item):
            capacity = jewelry_socket_capacity(item)
            if capacity <= 0:
                return "Brak gniazd."

            rows = self.socketed_gem_rows_for_item(
                slot,
                item_id,
            )
            if not rows:
                return f"Gniazda: 0 z {capacity} zajętych."

            names = [
                ITEMS.get(row["gem_id"], {"name": row["gem_id"]})["name"]
                for row in rows
            ]
            return (
                f"Gniazda: {len(rows)} z {capacity} zajętych. "
                f"Klejnoty: {', '.join(names)}."
            )

    async def return_socketed_gems(self, slot, item_id=None):
            rows = list(
                self.server.db.socketed_gems(
                    self.account_id,
                    slot,
                    item_id,
                )
                if item_id
                else self.server.db.socketed_gems(
                    self.account_id,
                    slot,
                )
            )
            if not rows:
                return []

            self.server.db.clear_socketed_gems(
                self.account_id,
                slot,
            )
            returned = []
            for row in rows:
                gem_id = row["gem_id"]
                if gem_id in ITEMS:
                    self.server.db.add_item(
                        self.account_id,
                        gem_id,
                        1,
                    )
                    returned.append(gem_id)
            return returned

    async def show_geodes(self):
            await self.send("GEODY")
            rows = {row["item_id"]: int(row["quantity"]) for row in self.server.db.storage_rows(self.account_id, "bag")}
            total = 0
            for geode_id, cfg in GEODE_DEFINITIONS.items():
                qty = rows.get(geode_id, 0)
                total += qty
                await self.send(
                    f"{cfg['name']}: {qty}. Kilof {cfg['min_tool']}+, głębokość {cfg['min_floor']}+."
                )
            if total:
                await self.send("Otwieranie: open geode / otwórz geodę. Możesz też podać nazwę, np. otwórz geodę kryształową.")
            else:
                await self.send("Nie masz obecnie geod w Sakwie Górnika.")

    def _find_owned_geode(self, query=""):
            rows = {row["item_id"]: int(row["quantity"]) for row in self.server.db.storage_rows(self.account_id, "bag")}
            owned = {gid: ITEMS[gid] for gid in GEODE_IDS if rows.get(gid, 0) > 0}
            if not owned:
                return None
            q = self.normalize_description_query(str(query or "").strip())
            for token in ("geoda", "geode", "geodę", "geodee"):
                q = q.replace(token, " ").strip()
            if q:
                found = find_by_name(owned, q)
                if found:
                    return found[0]
            # Bez nazwy otwieramy najlepszą posiadaną geodę.
            priority = ("astral_geode", "crystal_geode", "stone_geode")
            return next((gid for gid in priority if gid in owned), None)

    async def open_geode(self, query=""):
            geode_id = self._find_owned_geode(query)
            if not geode_id:
                await self.send("Nie masz takiej geody w Sakwie Górnika. Wpisz geody / geodes.")
                return False
            if not self.server.db.remove_storage_item(self.account_id, "bag", geode_id, 1):
                await self.send("Nie udało się pobrać geody z Sakwy Górnika.")
                return False
            cfg = GEODE_DEFINITIONS[geode_id]
            eligible = [d for d in GEM_DEFINITIONS if int(d["level"]) <= int(cfg["max_gem_level"])]
            weights = list(range(len(eligible), 0, -1))
            low_qty, high_qty = cfg["gem_qty"]
            quantity = random.randint(int(low_qty), int(high_qty))
            rewards = []
            for _ in range(quantity):
                definition = random.choices(eligible, weights=weights, k=1)[0]
                quality = random.choices(GEM_QUALITY_ORDER, weights=cfg["quality_weights"], k=1)[0]
                gem_id = gem_quality_item_id("raw", definition["key"], quality)
                self.store_profession_resource(gem_id, 1)
                await self.record_item_collection(
                    gem_id, source=cfg["name"], announce=True, record_history=False
                )
                rewards.append(ITEMS[gem_id]["name"])
            gold_low, gold_high = cfg["gold"]
            gold = random.randint(int(gold_low), int(gold_high))
            if gold > 0:
                self.character.gold += gold
            shard = False
            if geode_id == "astral_geode" and random.random() < 0.08:
                self.server.db.add_item(self.account_id, "soul_shard", 1)
                shard = True
            self.server.db.save_character(self.character)
            await self.send(f"Otwierasz {cfg['name']}. Klejnoty: " + ", ".join(rewards) + ".")
            if gold > 0:
                await self.send("W geodzie znajdujesz także " + currency_reading_text(0, gold, 0) + ".")
            if shard:
                await self.send("Rzadkie znalezisko: Odłamek Duszy x1.")
            return True

    async def show_gems(self):
            await self.send("KAMIENIE SZLACHETNE")
            await self.send(
                "Surowe kamienie wypadają dodatkowo podczas Górnictwa i trafiają do Sakwy Górnika. "
                "Po oszlifowaniu stają się materiałem jubilerskim i automatycznie trafiają do Szkatułki Rzemieślniczej."
            )
            await self.send(
                "Jakości: Surowy, Czysty, Doskonały, Perfekcyjny. Lepszy Kilof i wyższe Górnictwo "
                "zwiększają szansę jakości; Perfekcyjny pozostaje rzadkim jackpotem. Geody dają dodatkową "
                "szansę na klejnoty: geody / geodes."
            )
            for definition in GEM_DEFINITIONS:
                await self.send(
                    f"{definition['raw_name']} -> "
                    f"{definition['cut_name']}. "
                    f"Wymaga Górnictwa {definition['mining_level']} "
                    f"i głębokości {definition['min_floor']}. "
                    f"Szlifowanie: Jubilerstwo {definition['level']}. "
                    f"Bonus: "
                    f"{GEM_AFFIX_NAMES.get(definition['affix'], definition['affix'])} "
                    f"+{definition['amount']}."
                )

    async def cut_gem(self, query):
            q = self.normalize_description_query(query)
            if not q:
                await self.send(
                    "Użycie: szlifuj <kamień>. "
                    "Przykład: szlifuj rubin."
                )
                return False

            candidates = {}
            for recipe_id, recipe in JEWELCRAFT_RECIPES.items():
                if not recipe.get("gem_cut_recipe"):
                    continue
                output = ITEMS[recipe["output"]]
                raw_id = next(iter(recipe["ingredients"]))
                raw = ITEMS[raw_id]
                candidates[recipe_id] = {
                    "name": output["name"],
                    "aliases": (
                        raw["name"],
                        output["name"],
                        recipe_id.replace("cut_", ""),
                    ),
                    "recipe": recipe,
                }

            found = find_by_name(candidates, query)
            if not found:
                await self.send(
                    "Nie rozpoznaję kamienia do szlifowania. "
                    "Wpisz kamienie."
                )
                return False

            _recipe_id, entry = found
            return await self.perform_recipe(
                entry["recipe"]["name"],
                JEWELCRAFT_RECIPES,
                "szlifowanie",
            )

    async def socket_gem(self, query):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz osadzać klejnotów podczas walki."
                )
                return False

            raw = str(query or "").strip()
            if not raw:
                await self.send(
                    "Użycie: osadz <klejnot> <pierścień/kolczyk/naszyjnik>. "
                    "Przykład: osadz rubin kolczyk 1."
                )
                return False

            normalized = self.normalize_description_query(raw)
            slot = None
            slot_tokens = (
                ("pierścień 1", "ring1"), ("pierscien 1", "ring1"),
                ("ring 1", "ring1"), ("ring1", "ring1"),
                ("pierścień 2", "ring2"), ("pierscien 2", "ring2"),
                ("ring 2", "ring2"), ("ring2", "ring2"),
                ("pierścień", "ring"), ("pierscien", "ring"),
                ("ring", "ring"),
                ("kolczyk 1", "earring1"), ("earring 1", "earring1"), ("earring1", "earring1"),
                ("kolczyk 2", "earring2"), ("earring 2", "earring2"), ("earring2", "earring2"),
                ("kolczyk", "earring"), ("kolczyki", "earring"), ("earring", "earring"),
                ("naszyjnik", "necklace"), ("necklace", "necklace"),
                ("głowa", "head"), ("glowa", "head"), ("head", "head"),
                ("ciało", "body"), ("cialo", "body"), ("body", "body"),
                ("ręce", "hands"), ("rece", "hands"), ("hands", "hands"),
                ("nogi", "legs"), ("legs", "legs"), ("stopy", "feet"), ("feet", "feet"),
                ("barki", "shoulders"), ("shoulders", "shoulders"), ("pas", "belt"), ("belt", "belt"),
                ("płaszcz", "cloak"), ("plaszcz", "cloak"), ("cloak", "cloak"),
                ("karwasze", "bracers"), ("bracers", "bracers"), ("relikt", "relic"), ("relic", "relic"),
                ("board", "board"),
            )
            gem_query = raw
            for token, resolved in slot_tokens:
                token_norm = self.normalize_description_query(token)
                if normalized.endswith(" " + token_norm):
                    slot = resolved
                    words = raw.split()
                    token_words = len(token.split())
                    gem_query = " ".join(words[:-token_words]).strip()
                    break
                if normalized == token_norm:
                    slot = resolved
                    gem_query = ""
                    break

            if not slot:
                await self.send(
                    "Na końcu podaj slot EQ, np. ring1, necklace, body, head, bracers albo board."
                )
                return False

            if slot in ("ring", "earring"):
                pair = ("ring1", "ring2") if slot == "ring" else ("earring1", "earring2")
                slot = pair[0] if self.server.db.equipped_item(self.account_id, pair[0]) else pair[1]

            item_id = self.server.db.equipped_item(self.account_id, slot)
            item = ITEMS.get(item_id) if item_id else None
            if not item:
                await self.send(f"Nie masz założonego przedmiotu w slocie {EQUIPMENT_SLOT_NAMES.get(slot, slot)}.")
                return False
            capacity = self.equipment_total_socket_capacity_v03114(item_id, item, "gem")
            if capacity <= 0:
                await self.send(f"{item['name']} nie ma gniazd na klejnoty.")
                return False
            rows = self.socketed_gem_rows_for_item(
                slot,
                item_id,
            )
            if len(rows) >= capacity:
                await self.send(
                    f"{item['name']} ma wszystkie gniazda zajęte: "
                    f"{len(rows)} z {capacity}."
                )
                return False

            owned_gems = {
                gem_id: ITEMS[gem_id]
                for gem_id in CUT_GEM_IDS
                if self.available_recipe_item(gem_id) > 0
            }
            found = find_by_name(owned_gems, gem_query)
            if not found:
                await self.send(
                    "Nie masz takiego oszlifowanego klejnotu."
                )
                return False

            gem_id, gem = found
            if not self.consume_recipe_item(gem_id, 1):
                await self.send("Nie masz tego klejnotu w Szkatułce Rzemieślniczej.")
                return False

            used = {
                int(row["socket_index"])
                for row in rows
            }
            socket_index = next(
                i for i in range(1, capacity + 1)
                if i not in used
            )
            self.server.db.add_socketed_gem(
                self.account_id,
                slot,
                item_id,
                socket_index,
                gem_id,
            )

            self.current_hp = min(
                self.current_hp,
                self.max_hp(),
            )
            self.current_mana = min(
                self.current_mana,
                self.max_mana(),
            )

            affix_name = CRYPT_AFFIXES.get(
                gem.get("affix"),
                gem.get("affix"),
            )
            await self.send(
                f"Osadzasz {gem['name']} w {item['name']}. "
                f"Gniazdo {socket_index} z {capacity}. "
                f"Bonus: {affix_name} "
                f"+{gem.get('affix_amount', 0)}."
            )
            return True

    async def show_socketed_gems(self):
            await self.send("GNIAZDA EQ")
            found_any = False
            for row in self.equipped_item_rows():
                slot=row["slot"]; item_id=row["item_id"]; item=ITEMS.get(item_id)
                if not item:
                    continue
                capacity=self.equipment_total_socket_capacity_v03114(item_id,item,"gem")
                rune_capacity=self.equipment_total_socket_capacity_v03114(item_id,item,"rune")
                if capacity<=0 and rune_capacity<=0:
                    continue
                found_any=True
                gems=self.socketed_gem_rows_for_item(slot,item_id) if capacity>0 else []
                runes=list(self.server.db.equipment_runes_v0925(self.account_id,item_id)) if rune_capacity>0 else []
                await self.send(f"{EQUIPMENT_SLOT_NAMES.get(slot,slot)}: {item['name']}. Klejnoty {len(gems)}/{capacity}. Runy {len(runes)}/{rune_capacity}.")
            if not found_any:
                await self.send("Nie masz założonego EQ z gniazdami.")

    def automatic_dual_slot_v03020(self, logical_slot):
            """Pick first free ring/charm/earring slot; when full, replace the weaker equipped piece."""
            pairs = {
                "ring": ("ring1", "ring2"),
                "charm": ("charm1", "charm2"),
                "earring": ("earring1", "earring2"),
            }
            paired = pairs[logical_slot]
            for slot in paired:
                if not self.server.db.equipped_item(self.account_id, slot):
                    return slot
            scored = []
            for order, slot in enumerate(paired):
                item_id = self.server.db.equipped_item(self.account_id, slot)
                item = ITEMS.get(item_id, {})
                scored.append((self.equipment_item_score(item), order, slot))
            scored.sort(key=lambda row: (row[0], row[1]))
            return scored[0][2]

    async def equip_shortcut_dual_v03020(self, logical_slot, query=""):
            pairs = {
                "ring": ("ring1", "ring2", "pierścienie", "zp"),
                "charm": ("charm1", "charm2", "talizmany", "zt"),
                "earring": ("earring1", "earring2", "kolczyki", "zkol"),
            }
            s1, s2, noun, shortcut = pairs[logical_slot]
            candidates = self.owned_armor_for_slot(s1)
            if not candidates:
                await self.send(f"Nie masz żadnego EQ w kategorii {noun}.")
                return
            raw = str(query or "").strip()
            if not raw:
                n1 = ITEMS.get(self.server.db.equipped_item(self.account_id, s1), {}).get("name", "pusty")
                n2 = ITEMS.get(self.server.db.equipped_item(self.account_id, s2), {}).get("name", "pusty")
                await self.send(f"{noun.capitalize()}. Slot 1: {n1}. Slot 2: {n2}. Wybierz numer przedmiotu:")
                for idx, (_score, item_id, item) in enumerate(candidates, 1):
                    await self.send(f"{idx}. {player_item_display_name_v0335(item_id)}. Poziom postaci {int(item.get('required_character_level', item.get('required_mastery',1)) or 1)}.")
                return
            if raw.isdigit():
                idx = int(raw)
                if not 1 <= idx <= len(candidates):
                    await self.send(f"Nie ma pozycji {idx}. Zakres: 1-{len(candidates)}.")
                    return
                _score, item_id, item = candidates[idx-1]
            else:
                pool = {item_id:item for _score,item_id,item in candidates}
                found = find_by_name(pool, raw)
                if not found:
                    await self.send(f"Nie rozpoznaję przedmiotu. Wpisz {shortcut}, aby dostać listę.")
                    return
                item_id, item = found
            await self.equip_item(player_item_display_name_v0335(item_id))

    async def equip_shortcut_slot_v03016(self, slot, query=""):
            """NVDA-friendly numbered slot picker.

            Sam skrót pokazuje numerowaną listę. Skrót + numer zakłada wybraną
            pozycję. Skrót + nazwa nadal działa, ale wyłącznie w obrębie tego slotu.
            """
            slot = str(slot or "")
            candidates = self.owned_armor_for_slot(slot)
            if not candidates:
                await self.send(
                    f"Nie masz żadnego EQ dla slotu {EQUIPMENT_SLOT_NAMES.get(slot, slot)}."
                )
                return
            raw = str(query or "").strip()
            if not raw:
                current_id = self.server.db.equipped_item(self.account_id, slot)
                current_name = ITEMS.get(current_id, {}).get("name") if current_id else None
                await self.send(
                    f"EQ {EQUIPMENT_SLOT_NAMES.get(slot, slot)}. "
                    f"Aktualnie: {current_name or 'pusty slot'}. Wybierz numer:"
                )
                for idx, (_score, item_id, item) in enumerate(candidates, 1):
                    mastery = int(item.get("required_mastery", 1) or 1)
                    marker = " [ZAŁOŻONE]" if item_id == current_id else ""
                    await self.send(
                        f"{idx}. {player_item_display_name_v0335(item_id)}. "
                        f"Poziom postaci {int(item.get('required_character_level', mastery) or mastery)}. "
                        f"{CLASS_SET_STAT_NAMES.get(item.get('affix'), item.get('affix'))} "
                        f"+{int(item.get('affix_amount', 0) or 0)}; "
                        + ", ".join(
                            f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{int(amount or 0)}"
                            for stat, amount in (item.get("stats") or {}).items()
                        )
                        + marker
                    )
                return

            found = None
            if raw.isdigit():
                index = int(raw)
                if 1 <= index <= len(candidates):
                    _score, item_id, item = candidates[index - 1]
                    found = (item_id, item)
                else:
                    await self.send(f"Nie ma pozycji {index}. Zakres: 1-{len(candidates)}.")
                    return
            else:
                pool = {item_id: item for _score, item_id, item in candidates}
                found = find_by_name(pool, raw)
                if not found:
                    await self.send(
                        f"Nie rozpoznaję EQ dla slotu {EQUIPMENT_SLOT_NAMES.get(slot, slot)}. "
                        "Wpisz sam skrót, aby dostać numerowaną listę."
                    )
                    return

            item_id, item = found
            if slot in ("ring1", "ring2", "charm1", "charm2", "earring1", "earring2"):
                await self.equip_item(f"{slot} {player_item_display_name_v0335(item_id)}")
            else:
                await self.equip_item(player_item_display_name_v0335(item_id))

    async def equip_item(self, query):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz zmieniać ekwipunku podczas aktywnej walki. "
                    "Najpierw użyj flee albo zakończ walkę."
                )
                return

            raw_query = str(query or "").strip()
            normalized = self.normalize_description_query(raw_query)
            if not normalized:
                await self.send(
                    "Użycie: załóż <pełna nazwa EQ>. Pierścienie, talizmany i kolczyki wybierają wolny slot automatycznie; "
                    "ręczny slot 1/2 nadal działa. Skróty: zp, zt i zkol. Całość automatycznie: załóż auto albo eq auto."
                )
                return
            if normalized in ("auto", "automatycznie", "najlepsze", "best"):
                await self.auto_equip_best_v03040()
                return

            # Slot-only commands never choose the best item automatically.
            requested_slot = EQUIPMENT_SLOT_ALIASES.get(normalized)
            if requested_slot:
                if requested_slot in ("ring", "charm", "earring"):
                    await self.equip_shortcut_dual_v03020(requested_slot)
                    return

                candidates = self.owned_armor_for_slot(requested_slot)
                if not candidates:
                    await self.send(
                        f"Nie masz żadnego pancerza w slocie {EQUIPMENT_SLOT_NAMES[requested_slot]}."
                    )
                    return

                current_id = self.server.db.equipped_item(self.account_id, requested_slot)
                choices = self.equipment_choices_text(candidates)
                if current_id:
                    current = ITEMS.get(current_id, {"name": current_id})
                    await self.send(
                        f"Slot {EQUIPMENT_SLOT_NAMES[requested_slot]} jest zajęty przez: {current['name']}. "
                        "Nic nie zostało zmienione. Podaj pełną nazwę przedmiotu, który chcesz założyć, "
                        "albo najpierw użyj zdejmij " + EQUIPMENT_SLOT_NAMES[requested_slot] + "."
                    )
                    if choices:
                        await self.send(f"Posiadane opcje dla tego slotu: {choices}.")
                    return

                if len(candidates) != 1:
                    await self.send(
                        f"Masz kilka przedmiotów dla slotu {EQUIPMENT_SLOT_NAMES[requested_slot]}. "
                        "Gra nie wybiera najlepszego automatycznie. Podaj pełną nazwę wybranego EQ."
                    )
                    if choices:
                        await self.send(f"Posiadane opcje: {choices}.")
                    return
                _score, item_id, item = candidates[0]
                found = (item_id, item)
                explicit_slot = requested_slot
            else:
                explicit_slot, item_query = self.explicit_dual_slot_and_item_query(raw_query)
                if explicit_slot and not item_query:
                    candidates = self.owned_armor_for_slot(explicit_slot)
                    choices = self.equipment_choices_text(candidates)
                    current_id = self.server.db.equipped_item(self.account_id, explicit_slot)
                    if current_id:
                        current = ITEMS.get(current_id, {"name": current_id})
                        await self.send(
                            f"Slot {EQUIPMENT_SLOT_NAMES[explicit_slot]} jest zajęty przez: {current['name']}. "
                            "Nic nie zostało zmienione. Podaj pełną nazwę wybranego przedmiotu."
                        )
                    elif len(candidates) == 1:
                        _score, item_id, item = candidates[0]
                        found = (item_id, item)
                    else:
                        await self.send(
                            f"Wybierz konkretny przedmiot dla slotu {EQUIPMENT_SLOT_NAMES[explicit_slot]}. "
                            "Gra nie wybiera najlepszego automatycznie."
                        )
                        if choices:
                            await self.send(f"Posiadane opcje: {choices}.")
                        return
                    if current_id:
                        if choices:
                            await self.send(f"Posiadane opcje: {choices}.")
                        return
                else:
                    found = self.resolve_equipment_for_equip(item_query)

            if not found:
                await self.send(
                    "Nie rozpoznaję posiadanego EQ. Podaj pełną nazwę przedmiotu. "
                    "Pierścienie, talizmany i kolczyki nie wymagają podawania slotu 1/2."
                )
                return

            item_id, item = found
            if item.get("type") != "armor":
                await self.send("Tego przedmiotu nie można założyć.")
                return

            required_class = item.get("required_class")
            if required_class and required_class not in self.active_class_names():
                await self.send(
                    f"{item['name']} wymaga aktywnej klasy {required_class}."
                )
                return

            required_race = item.get("required_race")
            if required_race and str(self.character.race) != str(required_race):
                await self.send(
                    f"{item['name']} może używać tylko rasa {required_race}."
                )
                return

            required_mastery = max(1, int(item.get("required_mastery", 1)))
            if not self.equipment_mastery_requirement_met(item):
                await self.send(
                    f"{item['name']}: {self.equipment_mastery_requirement_text(item)}"
                )
                return

            if self.server.db.item_qty(self.account_id, item_id) <= 0:
                await self.send("Nie masz tego przedmiotu.")
                return

            logical_slot = item["slot"]
            if logical_slot == "ring":
                actual_slot = explicit_slot if explicit_slot in ("ring1", "ring2") else self.automatic_dual_slot_v03020("ring")
            elif logical_slot == "charm":
                actual_slot = explicit_slot if explicit_slot in ("charm1", "charm2") else self.automatic_dual_slot_v03020("charm")
            elif logical_slot == "earring":
                actual_slot = explicit_slot if explicit_slot in ("earring1", "earring2") else self.automatic_dual_slot_v03020("earring")
            else:
                actual_slot = logical_slot
                if explicit_slot and explicit_slot != actual_slot:
                    await self.send(
                        f"{item['name']} nie pasuje do slotu {EQUIPMENT_SLOT_NAMES.get(explicit_slot, explicit_slot)}."
                    )
                    return

            if logical_slot in ("ring", "charm", "earring"):
                paired = {
                    "ring": ("ring1", "ring2"),
                    "charm": ("charm1", "charm2"),
                    "earring": ("earring1", "earring2"),
                }[logical_slot]
                already_equipped = sum(
                    1 for row in self.equipped_item_rows()
                    if row["slot"] in paired and row["item_id"] == item_id and row["slot"] != actual_slot
                )
                if self.server.db.item_qty(self.account_id, item_id) <= already_equipped:
                    await self.send(
                        "Do drugiego slotu potrzebujesz drugiej sztuki tego samego przedmiotu."
                    )
                    return

            old_item_id = self.server.db.equipped_item(self.account_id, actual_slot)
            if old_item_id == item_id:
                await self.send(f"{item['name']} jest już założony w tym slocie.")
                return

            returned_gems = []
            if actual_slot in ("ring1", "ring2", "earring1", "earring2", "necklace") and old_item_id:
                returned_gems = await self.return_socketed_gems(actual_slot, old_item_id)

            # Replacing is explicit by chosen item; v0.30.20 may auto-pick the free/weaker ring or charm slot.
            self.server.db.equip(self.account_id, actual_slot, item_id)
            replaced_item = ITEMS.get(old_item_id) if old_item_id else None
            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())

            if replaced_item:
                await self.send(
                    f"Na twoje polecenie zdejmujesz: {replaced_item['name']}. "
                    f"Zakładasz wybrany przedmiot w tym samym slocie."
                )

            rarity = f" Rzadkość: {item['rarity_name']}." if item.get("rarity_name") else ""
            affix = ""
            if item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(item["affix"], item["affix"])
                affix = f" Bonus: {affix_name} +{item.get('affix_amount', 0)}."
            fixed_stats = ""
            if item.get("stats"):
                fixed_text = ", ".join(
                    f"{CLASS_SET_STAT_NAMES.get(stat, stat)} +{amount}"
                    for stat, amount in item.get("stats", {}).items()
                    if int(amount or 0) != 0
                )
                if fixed_text:
                    fixed_stats = f" Statystyki bazowe: {fixed_text}."
            await self.send(
                f"Zakładasz: {item['name']}. "
                f"Slot: {EQUIPMENT_SLOT_NAMES.get(actual_slot, actual_slot)}. "
                f"Obrona przedmiotu +{item.get('defense', 0)}.{rarity}{affix}{fixed_stats}"
            )
            if returned_gems:
                await self.send(
                    "Z poprzedniej biżuterii wyjęto i zwrócono do Szkatułki Rzemieślniczej: "
                    + ", ".join(ITEMS[g]["name"] for g in returned_gems) + "."
                )
            await self.send(f"Obrona fizyczna wynosi teraz {self.defense()}.")
            await self.send(self.crypt_set_bonus_text())
            await self.send(self.astral_set_bonus_text())

    async def unequip_item(self, query):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz zmieniać ekwipunku podczas aktywnej walki. "
                    "Najpierw użyj flee albo zakończ walkę."
                )
                return

            normalized = self.normalize_description_query(str(query or "").strip())
            slot = EQUIPMENT_SLOT_ALIASES.get(normalized)
            if slot in ("ring", "charm", "earring"):
                noun = {"ring":"pierścień", "charm":"talizman", "earring":"kolczyk"}[slot]
                await self.send(f"Podaj konkretny slot: zdejmij {noun} 1 albo zdejmij {noun} 2.")
                return
            if slot not in EQUIPMENT_SLOT_NAMES:
                await self.send(
                    "Użycie: zdejmij <slot>, np. zdejmij hełm, zdejmij pierścień 1, "
                    "zdejmij kolczyk 2, zdejmij talizman 2 albo zdejmij naszyjnik."
                )
                return

            item_id = self.server.db.equipped_item(self.account_id, slot)
            if not item_id:
                await self.send(f"Slot {EQUIPMENT_SLOT_NAMES[slot]} jest już pusty.")
                return
            item = ITEMS.get(item_id) or ensure_crafting_quality_variant_v0332(item_id) or {"name": player_item_display_name_v0335(item_id)}
            returned_gems = []
            if slot in ("ring1", "ring2", "earring1", "earring2", "necklace"):
                returned_gems = await self.return_socketed_gems(slot, item_id)
            self.server.db.unequip(self.account_id, slot)
            self.current_hp = min(self.current_hp, self.max_hp())
            self.current_mana = min(self.current_mana, self.max_mana())
            await self.send(
                f"Zdejmujesz: {item['name']}. Slot {EQUIPMENT_SLOT_NAMES[slot]} jest teraz pusty."
            )
            if returned_gems:
                await self.send(
                    "Wyjęte klejnoty wracają do Szkatułki Rzemieślniczej: "
                    + ", ".join(ITEMS[g]["name"] for g in returned_gems) + "."
                )

    def find_consumable_for_use(self, query):
            q = self.normalize_description_query(query)
            if not q:
                return None, []

            # v0.24.3: prosty skrót `użyj mapy`. Jeśli aktywny quest Erena
            # ma własną mapę, używamy najpierw jej; zwykła Mapa Skarbu nadal działa poza questem.
            if q in {"mapa", "mapy", "mape", "mapę", "mapa skarbu", "mape skarbu", "mapę skarbu", "treasure map"}:
                quest_map_id = globals().get("V0243_EREN_SECRET_MAP_ITEM")
                if quest_map_id and self.server.db.item_qty(self.account_id, quest_map_id) > 0:
                    return (quest_map_id, ITEMS[quest_map_id]), []
                return (V014_TREASURE_MAP_ITEM, ITEMS[V014_TREASURE_MAP_ITEM]), []

            # Celowe krótkie aliasy wymagane dla szybkiej obsługi NVDA.
            direct_aliases = {
                "mikstura": "healing_potion",
                "miksture": "healing_potion",
                "miksturę": "healing_potion",
                "potion": "healing_potion",
                "eliksir": "soul_elixir",
                "elixir": "soul_elixir",
                "eliksir duszy": "soul_elixir",
                "soul elixir": "soul_elixir",
                "mana": "mana_potion",
                "mikstura many": "mana_potion",
                "mana potion": "mana_potion",
            }
            item_id = direct_aliases.get(q)
            if item_id:
                return (item_id, ITEMS[item_id]), []

            consumables = {
                item_id: item
                for item_id, item in ITEMS.items()
                if item.get("type") == "consumable"
            }

            exact = []
            partial = []
            for item_id, item in consumables.items():
                names = (
                    item_id,
                    item.get("name", ""),
                )
                normalized_names = [
                    self.normalize_description_query(name)
                    for name in names
                ]
                if q in normalized_names:
                    exact.append((item_id, item))
                elif any(q in name for name in normalized_names):
                    partial.append((item_id, item))

            if exact:
                return exact[0], []
            if len(partial) == 1:
                return partial[0], []
            if len(partial) > 1:
                return None, partial
            return None, []

    async def use_item(self, query):
            raw_query = str(query or "").strip()
            lowered = raw_query.lower()

            # Wygodna składnia dla umiejętności:
            # użyj umiejętność <nazwa> [cel]
            # use skill <name> [target]
            skill_prefixes = (
                "skill ",
                "umiejętność ",
                "umiejetnosc ",
                "zdolność ",
                "zdolnosc ",
                "czar ",
                "spell ",
            )
            for prefix in skill_prefixes:
                if lowered.startswith(prefix):
                    skill_query = raw_query[len(prefix):].strip()
                    if not skill_query:
                        await self.send(
                            "Użycie: użyj umiejętność <nazwa> [cel] "
                            "albo use skill <name> [target]."
                        )
                        return
                    await self.use_class_skill(skill_query)
                    return

            found, ambiguous = self.find_consumable_for_use(raw_query)

            if ambiguous:
                names = ", ".join(item["name"] for _, item in ambiguous)
                await self.send(
                    f"Nazwa pasuje do kilku przedmiotów: {names}. "
                    "Podaj dokładniejszą nazwę."
                )
                return

            if not found:
                skill, _target = self.find_skill_from_input(raw_query)
                if skill:
                    await self.use_class_skill(raw_query)
                    return

                await self.send(
                    "Nie rozpoznaję przedmiotu ani umiejętności. "
                    "Przykłady: użyj mikstura; użyj umiejętność <nazwa> [cel]; "
                    "use skill <name> [target]."
                )
                return

            item_id, item = found

            if item.get("treasure_map"):
                if self.combat_mob_key:
                    await self.send("Nie możesz odczytywać mapy skarbu podczas walki.")
                    return
                await self.use_v0140_treasure_map(item_id)
                return

            if self.server.db.item_qty(self.account_id, item_id) <= 0:
                await self.send(f"Nie masz przedmiotu: {item['name']}.")
                return

            if item.get("type") != "consumable":
                await self.send("Tego przedmiotu nie używa się w ten sposób.")
                return

            if "heal" in item or "mana" in item:
                max_hp = self.max_hp()
                max_mana = self.max_mana()

                missing_hp = max(0, max_hp - self.current_hp)
                missing_mana = max(0, max_mana - self.current_mana)

                can_restore_hp = (
                    item.get("heal", 0) > 0
                    and missing_hp > 0
                )
                can_restore_mana = (
                    item.get("mana", 0) > 0
                    and max_mana > 0
                    and missing_mana > 0
                )

                if not can_restore_hp and not can_restore_mana:
                    if max_mana > 0:
                        await self.send("Masz pełne HP i Manę.")
                    else:
                        await self.send("Masz pełne życie.")
                    return

                self.server.db.remove_item(
                    self.account_id, item_id, 1
                )

                healed = 0
                restored_mana = 0

                if can_restore_hp:
                    healed = min(
                        item.get("heal", 0), missing_hp
                    )
                    self.current_hp += healed

                if can_restore_mana:
                    restored_mana = min(
                        item.get("mana", 0), missing_mana
                    )
                    self.current_mana += restored_mana

                parts = []
                if healed:
                    parts.append(f"{healed} HP")
                if restored_mana:
                    parts.append(f"{restored_mana} Many")

                await self.send(
                    f"Używasz {item['name']}. Odzyskujesz "
                    + " i ".join(parts) + "."
                )
                await self.send(
                    f"HP {self.current_hp} z {max_hp}."
                )
                if max_mana > 0:
                    await self.send(
                        f"Mana {self.current_mana} z {max_mana}."
                    )

                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            if "soul_xp" in item:
                self.server.db.remove_item(
                    self.account_id, item_id, 1
                )
                await self.send(
                    f"Używasz {item['name']}."
                )
                await self.grant_soul_xp(
                    item["soul_xp"]
                )
                self.server.db.save_character(self.character)

                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            await self.send(
                "Ten przedmiot nie ma efektu do użycia."
            )
