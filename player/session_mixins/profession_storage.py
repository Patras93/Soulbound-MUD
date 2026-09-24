# -*- coding: utf-8 -*-
"""Profession XP, tools and profession storage."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
from config.balance import (
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
)
from core.bootstrap_economy_professions import (
    PROFESSION_XP_GAIN_MULTIPLIER,
    currency_reading_text,
    generator_core_v027,
    profession_max_level,
    profession_max_rank,
    profession_rank,
    profession_rank_name,
    tool_max_level,
    tool_tier,
    tool_tier_bonus_chance,
    tool_tier_name,
)
from core.mines_threat import ITEMS
from core.progression_600 import CHARACTER_MAX_LEVEL, PROFESSION_MAX_LEVEL, TOOL_MAX_TIER
from core.progression_resources import (
    FISH_RESOURCE_IDS,
    HERB_RESOURCE_IDS,
    ORE_RESOURCE_IDS,
    WOOD_RESOURCE_IDS,
    v0190_requirement,
    v0190_resource_sale_coins,
    v0190_scaled_gain,
)
from network.protocol_gameplay_utils import (
    V0925_CRAFTBOX_ALIASES,
    V0925_CRAFTBOX_CATEGORIES,
    find_by_name,
    normalize_lookup_text,
    v0925_craftbox_category,
)
from systems.crafting_expansion import CRAFT_MATERIAL_STORAGE_IDS
from systems.crafting_quality import player_item_display_name_v0335
from systems.equipment_crafting import MINING_STORAGE_IDS, RAW_GEM_IDS
from systems.items_resources import FISH_STORAGE_IDS, HERB_STORAGE_IDS, ORE_STORAGE_IDS, WOOD_STORAGE_IDS


class SessionProfessionStorageMixin:

    def profession_xp_to_next(self, level, profession=None):
            max_level = (
                profession_max_level(profession)
                if profession is not None
                else PROFESSION_MAX_LEVEL
            )
            if level >= max_level:
                return 0
            base = v0190_requirement("profession", level)
            multiplier = float(PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get(str(profession), 1.0))
            return max(1, int(round(base * multiplier)))

    def tool_xp_to_next(self, level, tool_type=None):
            max_level = tool_max_level(tool_type)
            if level >= max_level:
                return 0

            base = v0190_requirement("tool", level)
            multiplier = float(TOOL_XP_REQUIREMENT_MULTIPLIERS.get(str(tool_type), 1.0))
            return max(1, int(round(base * multiplier)))

    def valid_tool_type(self, tool_type):
            return tool_type in (
                "fishing",
                "mining",
                "woodcutting",
                "crafting",
                "cooking",
                "herbalism",
                "alchemy",
                "jewelcrafting",
                "tailoring",
                "leatherworking",
                "carpentry",
                "enchanting",
            )

    def tool_progress_state(self):
            result = {}
            for tool_type in (
                "fishing",
                "mining",
                "woodcutting",
                "crafting",
                "cooking",
                "herbalism",
                "alchemy",
                "jewelcrafting",
                "tailoring",
                "leatherworking",
                "carpentry",
                "enchanting",
            ):
                row = self.server.db.tool(self.account_id, tool_type)
                result[tool_type] = (
                    int(row["level"]),
                    int(row["xp"]),
                    int(row["uses"]),
                )
            return result

    def grant_profession_progress(self, profession, prof_xp, tool_type, tool_xp, tool_progress=True):
            if not self.valid_tool_type(tool_type):
                raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

            _guild_pct=self.guild_bonus_percent_v0926()
            prow = self.server.db.profession(
                self.account_id, profession
            )
            profession_cap = profession_max_level(profession)
            plevel = int(prow["level"])
            trow_preview = self.server.db.tool(self.account_id, tool_type)
            tlevel_preview = int(trow_preview["level"])
            legacy_prof_xp = max(0, int(prof_xp)) * PROFESSION_XP_GAIN_MULTIPLIER
            actual_prof_xp = v0190_scaled_gain(legacy_prof_xp, plevel, "profession", 40)
            tool_xp = v0190_scaled_gain(tool_xp, tlevel_preview, "tool", 12)
            actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_guild_pct/100.0))))
            tool_xp=max(0,int(round(tool_xp*(1.0+_guild_pct/100.0))))
            _title_pct = self.v0260_profession_xp_bonus_percent(profession, tool_type)
            if _title_pct:
                actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_title_pct/100.0))))
                tool_xp=max(0,int(round(tool_xp*(1.0+_title_pct/100.0))))
            _mentor_pct = self.mentor_bonus_percent_v03050()
            if _mentor_pct:
                actual_prof_xp=max(0,int(round(actual_prof_xp*(1.0+_mentor_pct/100.0))))
                tool_xp=max(0,int(round(tool_xp*(1.0+_mentor_pct/100.0))))
                self.mentor_record_activity_v03051()
            actual_prof_xp = self.apply_double_xp(actual_prof_xp)
            tool_xp = self.apply_double_xp(tool_xp)
            self.session_summary_add("profession_xp", actual_prof_xp, profession)
            if tool_progress:
                self.session_summary_add("tool_xp", tool_xp, tool_type)
            old_profession_rank = profession_rank(
                plevel, profession
            )
            pxp = int(prow["xp"]) + actual_prof_xp
            actions = int(prow["actions"]) + 1
            messages = [f"{profession}: +{actual_prof_xp} XP."]

            while plevel < profession_cap:
                needed = self.profession_xp_to_next(
                    plevel, profession
                )
                if pxp < needed:
                    break
                pxp -= needed
                plevel += 1
                messages.append(f"AWANS PROFESJI: {profession} osiąga poziom {plevel}.")
            if plevel >= profession_cap:
                plevel = profession_cap
                pxp = 0
            self.server.db.save_profession(
                self.account_id, profession, plevel, pxp, actions
            )
            # v0.70.0: mastery contracts count only real profession actions.
            # Reward XP uses grant_profession_reward_xp(), so it cannot recurse.
            for quest_id, quest_progress, quest_needed in self.server.db.increment_profession_action_quests_v0700(
                self.account_id, profession, tool_type, 1
            ):
                if int(quest_progress) >= int(quest_needed):
                    messages.append(
                        f"QUEST PROFESJI GOTOWY: {quest_id}. Postęp {quest_progress} z {quest_needed}. Wróć do mistrza profesji."
                    )

            new_profession_rank = profession_rank(
                plevel, profession
            )
            max_profession_rank = profession_max_rank(
                profession
            )
            if new_profession_rank > old_profession_rank:
                messages.append(
                    f"{profession}: awansujesz na Rangę {new_profession_rank} "
                    f"z {max_profession_rank}: "
                    f"{profession_rank_name(profession, plevel)}."
                )

            trow = self.server.db.tool(self.account_id, tool_type)
            tlevel = int(trow["level"])
            if tool_progress:
                old_tool_tier = tool_tier(tlevel)
                txp = int(trow["xp"]) + tool_xp
                uses = int(trow["uses"]) + 1
                tool_name = {
                    "fishing": "Wędka",
                    "mining": "Kilof",
                    "woodcutting": "Piła",
                    "crafting": "Młot Rzemieślniczy",
                    "cooking": "Nóż Kucharski",
                    "herbalism": "Sierp Zielarski",
                    "alchemy": "Moździerz Alchemiczny",
                    "jewelcrafting": "Szczypce Jubilerskie",
                }.get(tool_type, tool_type)
                messages.append(f"{tool_name}: +{tool_xp} XP narzędzia.")

                tool_level_cap = tool_max_level(tool_type)
                while tlevel < tool_level_cap:
                    needed = self.tool_xp_to_next(tlevel, tool_type)
                    if txp < needed:
                        break
                    txp -= needed
                    tlevel += 1
                    messages.append(f"{tool_name} osiąga poziom {tlevel}.")
                if tlevel >= tool_level_cap:
                    tlevel = tool_level_cap
                    txp = 0
                self.server.db.save_tool(
                    self.account_id, tool_type, tlevel, txp, uses
                )

                new_tool_tier = tool_tier(tlevel)
                if new_tool_tier > old_tool_tier:
                    messages.append(
                        f"{tool_name} awansuje na Tier {new_tool_tier} z {TOOL_MAX_TIER}: "
                        f"{tool_tier_name(tool_type, tlevel)}. "
                        f"Szansa na dodatkowy urobek: "
                        f"{int(tool_tier_bonus_chance(tlevel) * 100)} procent."
                    )

            _char_stage=max(1,min(CHARACTER_MAX_LEVEL,max(plevel,tlevel)))
            _char_gain=generator_core_v027.axis_gain("character",_char_stage,0.35)
            messages.extend(self.add_character_xp_with_event(_char_gain))
            self.server.db.save_character(self.character)
            return messages, plevel, tlevel

    def grant_tool_progress(self, tool_type, tool_xp):
            if not self.valid_tool_type(tool_type):
                raise ValueError(f"Nieznany typ narzędzia: {tool_type}")
            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            old_tier = tool_tier(level)
            tool_xp = v0190_scaled_gain(tool_xp, level, "tool", 12)
            tool_xp = self.apply_double_xp(tool_xp)
            self.session_summary_add("tool_xp", tool_xp, tool_type)
            xp = int(row["xp"]) + max(0, int(tool_xp))
            uses = int(row["uses"]) + 1

            tool_name = {
                "fishing": "Wędka",
                "mining": "Kilof",
                "woodcutting": "Piła",
                "crafting": "Młot Rzemieślniczy",
                "cooking": "Nóż Kucharski",
                "herbalism": "Sierp Zielarski",
                "alchemy": "Moździerz Alchemiczny",
                "jewelcrafting": "Szczypce Jubilerskie",
            }.get(tool_type, tool_type)

            messages = [f"{tool_name}: +{tool_xp} XP narzędzia."]

            tool_level_cap = tool_max_level(tool_type)
            while level < tool_level_cap:
                needed = self.tool_xp_to_next(level, tool_type)
                if xp < needed:
                    break
                xp -= needed
                level += 1
                messages.append(f"{tool_name} osiąga poziom {level}.")

            if level >= tool_level_cap:
                level = tool_level_cap
                xp = 0

            self.server.db.save_tool(
                self.account_id, tool_type, level, xp, uses
            )

            new_tier = tool_tier(level)
            if new_tier > old_tier:
                if tool_type == "cooking":
                    bonus_name = "dodatkową potrawę"
                elif tool_type == "crafting":
                    bonus_name = "dodatkowy produkt receptury"
                else:
                    bonus_name = "dodatkowy urobek"
                messages.append(
                    f"{tool_name} awansuje na Tier {new_tier} z {TOOL_MAX_TIER}: "
                    f"{tool_tier_name(tool_type, level)}. "
                    f"Szansa na {bonus_name}: "
                    f"{int(tool_tier_bonus_chance(level) * 100)} procent."
                )

            _char_gain=generator_core_v027.axis_gain("character",max(1,min(CHARACTER_MAX_LEVEL,level)),0.25)
            messages.extend(self.add_character_xp_with_event(_char_gain))
            self.server.db.save_character(self.character)
            return messages, level

    def store_profession_resource(self, item_id, quantity=1):
            quantity = max(1, int(quantity))
            if item_id in FISH_STORAGE_IDS:
                self.server.db.add_storage_item(
                    self.account_id, "net", item_id, quantity
                )
                return "net"
            if item_id in MINING_STORAGE_IDS:
                self.server.db.add_storage_item(
                    self.account_id, "bag", item_id, quantity
                )
                return "bag"
            if item_id in WOOD_STORAGE_IDS:
                self.server.db.add_storage_item(
                    self.account_id, "woodpile", item_id, quantity
                )
                return "woodpile"
            if item_id in HERB_STORAGE_IDS:
                self.server.db.add_storage_item(
                    self.account_id, "herbbag", item_id, quantity
                )
                return "herbbag"
            raise ValueError(
                f"Przedmiot {item_id} nie jest surowcem obsługiwanej profesji."
            )

    def migrate_raw_mining_gems_to_bag_v0867(self):
            moved = 0
            for item_id in RAW_GEM_IDS:
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty <= 0:
                    continue
                if self.server.db.remove_item(self.account_id, item_id, qty):
                    self.server.db.add_storage_item(
                        self.account_id, "bag", item_id, qty
                    )
                    moved += qty
            return moved

    def migrate_craft_materials_to_casket_v0915(self):
            moved = 0
            for item_id in CRAFT_MATERIAL_STORAGE_IDS:
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty <= 0:
                    continue
                if self.server.db.remove_item(self.account_id, item_id, qty):
                    self.server.db.add_storage_item(
                        self.account_id, "craftbox", item_id, qty
                    )
                    moved += qty
            return moved

    def container_label(self, container):
            return {
                "net": "Siatka na ryby",
                "bag": "Sakwa górnicza",
                "woodpile": "Stos drewna",
                "herbbag": "Torba Zielarska",
                "craftbox": "Szkatułka Rzemieślnicza",
            }.get(container, container)

    def normalize_container(self, token):
            t = token.strip().lower()
            if t in ("net", "siatka", "siatkę", "siatke"):
                return "net"
            if t in ("bag", "sakwa", "sakwe", "sakwę", "worek"):
                return "bag"
            if t in ("woodpile", "stos", "drewno", "sterta"):
                return "woodpile"
            if t in ("herbbag", "ziola", "zioła", "herbs", "torba"):
                return "herbbag"
            if t in ("craftbox", "szkatulka", "szkatułka", "materialy", "materiały"):
                return "craftbox"
            return None

    def category_ids(self, query, container=None):
            q = query.strip().lower()
            if q in ("fish", "ryba", "ryby"):
                return set(FISH_STORAGE_IDS)
            if q in ("ore", "ruda", "rudy"):
                return set(ORE_STORAGE_IDS)
            if q in ("wood", "drewno", "pnie", "pień", "pien"):
                return set(WOOD_STORAGE_IDS)
            if q in ("herb", "herbs", "ziolo", "zioło", "ziola", "zioła"):
                return set(HERB_STORAGE_IDS)
            if container == "net":
                allowed = FISH_STORAGE_IDS
            elif container == "bag":
                allowed = MINING_STORAGE_IDS
            elif container == "woodpile":
                allowed = WOOD_STORAGE_IDS
            elif container == "herbbag":
                allowed = HERB_STORAGE_IDS
            elif container == "craftbox":
                allowed = CRAFT_MATERIAL_STORAGE_IDS
            else:
                allowed = (
                    FISH_STORAGE_IDS | ORE_RESOURCE_IDS | WOOD_RESOURCE_IDS | HERB_RESOURCE_IDS
                    | set(CRAFT_MATERIAL_STORAGE_IDS)
                )

            found = find_by_name(
                {item_id: ITEMS[item_id] for item_id in allowed},
                query
            )
            return {found[0]} if found else set()

    def profession_storage_definition(self, container):
            definitions = {
                "net": {
                    "ids": FISH_STORAGE_IDS,
                    "count_label": "ryb",
                    "type_label": "gatunków",
                    "value_label": "całej siatki",
                },
                "bag": {
                    "ids": MINING_STORAGE_IDS,
                    "count_label": "urobku",
                    "type_label": "rodzajów",
                    "value_label": "całej Sakwy Górnika",
                },
                "woodpile": {
                    "ids": WOOD_STORAGE_IDS,
                    "count_label": "sztuk drewna",
                    "type_label": "rodzajów",
                    "value_label": "całego stosu drewna",
                },
                "herbbag": {
                    "ids": HERB_STORAGE_IDS,
                    "count_label": "ziół",
                    "type_label": "rodzajów",
                    "value_label": "całej torby zielarskiej",
                    "show_value": True,
                },
                "craftbox": {
                    "ids": CRAFT_MATERIAL_STORAGE_IDS,
                    "count_label": "materiałów rzemieślniczych",
                    "type_label": "rodzajów",
                    "value_label": "Szkatułki Rzemieślniczej",
                    "show_value": False,
                },
            }
            return definitions.get(container)

    def profession_storage_summary(self, container, rows=None):
            definition = self.profession_storage_definition(container)
            if not definition:
                return {
                    "count": 0,
                    "types": 0,
                    "silver": 0,
                    "gold": 0,
                    "mithril": 0,
                }

            if rows is None:
                rows = self.server.db.storage_rows(
                    self.account_id, container
                )

            total_count = 0
            total_silver = 0
            total_gold = 0
            total_mithril = 0
            type_count = 0

            allowed_ids = definition["ids"]

            for row in rows:
                item_id = row["item_id"]
                if item_id not in allowed_ids:
                    continue

                quantity = max(0, int(row["quantity"]))
                if quantity <= 0:
                    continue

                type_count += 1
                total_count += quantity

                item = ITEMS.get(item_id, {})
                # v0.19: wartość torby korzysta z tego samego generatora co realna sprzedaż.
                total_silver += v0190_resource_sale_coins(item_id, item) * quantity

            return {
                "count": total_count,
                "types": type_count,
                "silver": total_silver,
                "gold": total_gold,
                "mithril": total_mithril,
            }

    def fish_net_summary(self, rows=None):
            generic = self.profession_storage_summary(
                "net", rows
            )
            return {
                "fish": generic["count"],
                "species": generic["types"],
                "silver": generic["silver"],
                "gold": generic["gold"],
                "mithril": generic["mithril"],
            }

    def profession_storage_value_text(self, summary):
            return currency_reading_text(
                summary["silver"], summary["gold"], summary["mithril"]
            )

    def fish_net_value_text(self, summary):
            return self.profession_storage_value_text(summary)

    async def show_craftbox_v0925(self, args=""):
            rows = list(self.server.db.storage_rows(self.account_id, "craftbox"))
            norm = normalize_lookup_text(args)
            if not norm or norm in ("info", "lista", "list", "kategorie", "categories"):
                counts = {key:0 for key in V0925_CRAFTBOX_CATEGORIES}
                types = {key:set() for key in V0925_CRAFTBOX_CATEGORIES}
                for row in rows:
                    cat=v0925_craftbox_category(str(row["item_id"]))
                    counts[cat]=counts.get(cat,0)+int(row["quantity"])
                    types.setdefault(cat,set()).add(str(row["item_id"]))
                await self.send("SZKATUŁKA RZEMIEŚLNICZA — KATEGORIE")
                for key,label in V0925_CRAFTBOX_CATEGORIES.items():
                    await self.send(f"{label}: {counts.get(key,0)} sztuk, {len(types.get(key,set()))} rodzajów.")
                await self.send("Użyj: szkatułka kowalstwo / jubilerstwo / alchemia / runy / salvage / inne.")
                return
            cat=V0925_CRAFTBOX_ALIASES.get(norm)
            if cat is None:
                await self.send("Nie znam takiej kategorii Szkatułki. Dostępne: kowalstwo, jubilerstwo, alchemia, runy, salvage, inne.")
                return
            filtered=[row for row in rows if v0925_craftbox_category(str(row["item_id"]))==cat]
            await self.send(f"SZKATUŁKA — {V0925_CRAFTBOX_CATEGORIES[cat]}:")
            if not filtered:
                await self.send("Pusto.")
                return
            total=0
            for row in filtered:
                item=ITEMS.get(str(row["item_id"]), {"name":player_item_display_name_v0335(str(row["item_id"]))})
                qty=int(row["quantity"]); total+=qty
                await self.send(f"{item['name']} x{qty}.")
            await self.send(f"Łącznie w tej kategorii: {total} sztuk, {len(filtered)} rodzajów.")

    async def show_container(self, container):
            label = self.container_label(container)
            rows = self.server.db.storage_rows(
                self.account_id, container
            )
            await self.send(label + ":")

            definition = self.profession_storage_definition(container)

            if not rows:
                await self.send("Pusto.")
                if definition:
                    await self.send(
                        f"Łącznie {definition['count_label']}: 0. "
                        f"{definition['type_label'].capitalize()}: 0."
                    )
                    if definition.get("show_value", True):
                        await self.send(
                            "Szacowany zarobek ze sprzedaży "
                            f"{definition['value_label']}: 0 srebra."
                        )
                return

            for row in rows:
                item = ITEMS.get(
                    row["item_id"],
                    {"name": row["item_id"]},
                )
                await self.send(
                    f"{item['name']} x{row['quantity']}."
                )

            if definition:
                summary = self.profession_storage_summary(
                    container, rows
                )
                await self.send(
                    f"Łącznie {definition['count_label']}: "
                    f"{summary['count']}. "
                    f"{definition['type_label'].capitalize()}: "
                    f"{summary['types']}."
                )
                if definition.get("show_value", True):
                    await self.send(
                        "Szacowany zarobek ze sprzedaży "
                        f"{definition['value_label']}: "
                        f"{self.profession_storage_value_text(summary)}."
                    )
                else:
                    await self.send(
                        "Materiały i oszlifowane klejnoty w Szkatułce są chronione przed sell/sell all "
                        "i są pobierane automatycznie przez receptury."
                    )

    async def put_in_container(self, args):
            # Przykłady:
            # wloz ryba siatka
            # put fish net
            # wloz ruda sakwa
            parts = args.split()
            if len(parts) < 2:
                await self.send(
                    "Użycie: wloz ryba siatka / put fish net / "
                    "wloz ruda sakwa / put ore bag."
                )
                return

            container = self.normalize_container(parts[-1])
            if not container:
                await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
                return
            if container == "craftbox":
                await self.send(
                    "Szkatułka Rzemieślnicza działa automatycznie. Materiały rzemieślnicze i oszlifowane klejnoty jubilerskie "
                    "trafiają do niej przy zdobyciu, a receptury pobierają je bez wyjmowania."
                )
                return

            query = " ".join(parts[:-1])
            ids = self.category_ids(query, container)
            if not ids:
                await self.send("Nie rozpoznaję takiego surowca.")
                return

            expected = {
                "net": FISH_RESOURCE_IDS,
                "bag": ORE_RESOURCE_IDS,
                "woodpile": WOOD_RESOURCE_IDS,
                "herbbag": HERB_RESOURCE_IDS,
            }[container]
            ids &= expected
            if not ids:
                await self.send(
                    "Do Siatki wkłada się ryby, do Sakwy rudy, na Stos drewno, a do Torby Zielarskiej zioła."
                )
                return

            moved = []
            for item_id in sorted(ids):
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty <= 0:
                    continue
                self.server.db.remove_item(self.account_id, item_id, qty)
                self.server.db.add_storage_item(
                    self.account_id, container, item_id, qty
                )
                moved.append((item_id, qty))

            if not moved:
                await self.send("Nie masz takich surowców w zwykłym ekwipunku.")
                return

            for item_id, qty in moved:
                await self.send(
                    f"Wkładasz {ITEMS[item_id]['name']} x{qty} do "
                    f"{self.container_label(container)}."
                )

    async def take_from_container(self, args):
            parts = args.split()
            if len(parts) < 2:
                await self.send(
                    "Użycie: wyjmij przedmiot siatka/sakwa/stos albo take item net/bag/woodpile."
                )
                return

            container = self.normalize_container(parts[-1])
            if not container:
                await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
                return
            if container == "craftbox":
                await self.send(
                    "Materiałów nie trzeba wyjmować ze Szkatułki Rzemieślniczej. "
                    "Receptury pobierają je z niej automatycznie."
                )
                return

            query = " ".join(parts[:-1])
            ids = self.category_ids(query, container)
            if not ids:
                await self.send("Nie rozpoznaję takiego surowca.")
                return

            moved = []
            for item_id in sorted(ids):
                qty = self.server.db.storage_qty(
                    self.account_id, container, item_id
                )
                if qty <= 0:
                    continue
                self.server.db.remove_storage_item(
                    self.account_id, container, item_id, qty
                )
                self.server.db.add_item(self.account_id, item_id, qty)
                moved.append((item_id, qty))

            if not moved:
                await self.send("Nie ma tego surowca w tym pojemniku.")
                return

            for item_id, qty in moved:
                await self.send(
                    f"Wyjmujesz {ITEMS[item_id]['name']} x{qty} z "
                    f"{self.container_label(container)}."
                )

    async def grant_tool_reward_xp(self, tool_type, tool_xp):
            if not self.valid_tool_type(tool_type):
                raise ValueError(
                    f"Nieznany typ narzędzia: {tool_type}"
                )

            row = self.server.db.tool(
                self.account_id, tool_type
            )
            level = int(row["level"])
            tool_xp = v0190_scaled_gain(tool_xp, level, "tool", 12)
            tool_xp = self.apply_double_xp(tool_xp)
            self.session_summary_add("tool_xp", tool_xp, tool_type)
            xp = int(row["xp"]) + tool_xp
            uses = int(row["uses"])

            tool_name = {
                "fishing": "Wędka",
                "mining": "Kilof",
                "woodcutting": "Piła",
                "crafting": "Młot Rzemieślniczy",
                "cooking": "Nóż Kucharski",
                "herbalism": "Sierp Zielarski",
                "alchemy": "Moździerz Alchemiczny",
                "jewelcrafting": "Szczypce Jubilerskie",
                "tailoring": "Zestaw Krawiecki",
                "leatherworking": "Nóż Garbarski",
                "carpentry": "Narzędzia Ciesielskie",
                "enchanting": "Fokus Runiczny",
            }[tool_type]

            await self.send(
                f"{tool_name}: nagroda +{tool_xp} XP."
            )

            cap = tool_max_level(tool_type)
            while level < cap:
                needed = self.tool_xp_to_next(
                    level, tool_type
                )
                if xp < needed:
                    break
                xp -= needed
                level += 1
                await self.send(
                    f"{tool_name} osiąga poziom {level}."
                )

            if level >= cap:
                level = cap
                xp = 0

            self.server.db.save_tool(
                self.account_id,
                tool_type,
                level,
                xp,
                uses,
            )

    async def grant_profession_reward_xp(self, profession, profession_xp, tool_type, tool_xp):
            if not self.valid_tool_type(tool_type):
                raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

            _guild_pct=self.guild_bonus_percent_v0926()
            prow = self.server.db.profession(
                self.account_id, profession
            )
            profession_cap = profession_max_level(profession)
            plevel = int(prow["level"])
            trow_preview = self.server.db.tool(self.account_id, tool_type)
            tlevel_preview = int(trow_preview["level"])
            legacy_profession_xp = max(0, int(profession_xp)) * PROFESSION_XP_GAIN_MULTIPLIER
            actual_profession_xp = v0190_scaled_gain(legacy_profession_xp, plevel, "profession", 40)
            tool_xp = v0190_scaled_gain(tool_xp, tlevel_preview, "tool", 12)
            actual_profession_xp=max(0,int(round(actual_profession_xp*(1.0+_guild_pct/100.0))))
            tool_xp=max(0,int(round(tool_xp*(1.0+_guild_pct/100.0))))
            _title_pct = self.v0260_profession_xp_bonus_percent(profession, tool_type)
            if _title_pct:
                actual_profession_xp=max(0,int(round(actual_profession_xp*(1.0+_title_pct/100.0))))
                tool_xp=max(0,int(round(tool_xp*(1.0+_title_pct/100.0))))
            actual_profession_xp = self.apply_double_xp(actual_profession_xp)
            tool_xp = self.apply_double_xp(tool_xp)
            self.session_summary_add("profession_xp", actual_profession_xp, profession)
            self.session_summary_add("tool_xp", tool_xp, tool_type)
            pxp = int(prow["xp"]) + actual_profession_xp
            actions = int(prow["actions"])

            await self.send(
                f"{profession}: nagroda +{actual_profession_xp} XP."
            )

            while plevel < profession_cap:
                needed = self.profession_xp_to_next(
                    plevel, profession
                )
                if pxp < needed:
                    break
                pxp -= needed
                plevel += 1
                await self.send(f"AWANS PROFESJI: {profession} osiąga poziom {plevel}.")

            if plevel >= profession_cap:
                plevel = profession_cap
                pxp = 0

            self.server.db.save_profession(
                self.account_id, profession, plevel, pxp, actions
            )

            trow = self.server.db.tool(self.account_id, tool_type)
            tlevel = int(trow["level"])
            txp = int(trow["xp"]) + tool_xp
            uses = int(trow["uses"])
            tool_name = {
                "fishing": "Wędka",
                "mining": "Kilof",
                "woodcutting": "Piła",
                "crafting": "Młot Rzemieślniczy",
                "cooking": "Nóż Kucharski",
                "herbalism": "Sierp Zielarski",
                "alchemy": "Moździerz Alchemiczny",
                "jewelcrafting": "Szczypce Jubilerskie",
                "tailoring": "Zestaw Krawiecki",
                "leatherworking": "Nóż Garbarski",
                "carpentry": "Narzędzia Ciesielskie",
                "enchanting": "Fokus Runiczny",
            }[tool_type]

            await self.send(f"{tool_name}: nagroda +{tool_xp} XP.")

            tool_level_cap = tool_max_level(tool_type)
            while tlevel < tool_level_cap:
                needed = self.tool_xp_to_next(tlevel, tool_type)
                if txp < needed:
                    break
                txp -= needed
                tlevel += 1
                await self.send(f"{tool_name} osiąga poziom {tlevel}.")

            if tlevel >= tool_level_cap:
                tlevel = tool_level_cap
                txp = 0

            self.server.db.save_tool(
                self.account_id, tool_type, tlevel, txp, uses
            )
