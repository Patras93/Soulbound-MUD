# -*- coding: utf-8 -*-
"""Skill queues, buffs and class support helpers."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import asyncio
import re
import time
from player.session_mixins.equipment_stats import class_type_for_name
from core.classes_skills import effective_skill_mana_cost, MEC_PROTOCOL_SKILLS_V11155
from player.session_mixins.shops_teachers import CHARACTER_MAX_LEVEL
from player.session_mixins.skill_learning import CLASS_SKILLS, SKILL_MAX_LEVEL


class SessionSkillQueueBuffsMixin:
    def skill_by_id(self, skill_id):
            for class_name, skills in CLASS_SKILLS.items():
                for skill in skills:
                    if skill["id"] == skill_id:
                        return skill
            return None

    def is_mec_protocol_v10013(self, skill):
            return bool(
                skill
                and skill.get("mec_authored")
                and skill.get("mec_special") in {
                    "strength_protocol",
                    "ranged_protocol",
                    "feedback_protocol",
                    "magic_protocol",
                }
            )

    def cleanup_mec_protocols_from_queue_v10013(self):
            """Pasywki działają stale i nigdy nie zajmują slotów auto-kolejki."""
            removed = 0
            for queue_type in ("physical", "magic", "feedback"):
                removed_here = 0
                rows = list(self.server.db.skill_queue_rows(self.account_id, queue_type))
                for row in sorted(rows, key=lambda item: int(item["position"]), reverse=True):
                    skill = self.skill_by_id(row["skill_id"])
                    if not skill:
                        continue
                    passive_kind = str(skill.get("kind", "")).lower() == "passive"
                    automatic_boost = (
                        str(skill.get("kind", "")).lower() == "boost"
                        and not skill.get("active_special")
                        and str(skill.get("mec_special", "")) != "vmax"
                    )
                    if not (passive_kind or automatic_boost):
                        continue
                    if self.server.db.remove_skill_queue_entry(
                        self.account_id, queue_type, int(row["position"])
                    ):
                        removed += 1
                        removed_here += 1
                if removed_here:
                    self.skill_queue_cursors[queue_type] = 0
            return removed

    def skill_queue_type(self, skill):
            """Queue by the concrete skill role, not only by the owning class."""
            if skill and skill.get("mec_authored"):
                branch = str(skill.get("mec_branch", "") or "").strip().lower()
                if branch in {"magic", "support"}:
                    return "magic"
                if branch == "feedback":
                    return "feedback"
                if branch in {"melee", "ranged"}:
                    return "physical"
            class_name = self.skill_class_name(skill)
            return "magic" if class_type_for_name(class_name) == "magic" else "physical"

    def normalize_skill_queue_types_v1125(self):
            """Move legacy Mec queue entries to their role-specific queue.

            Older builds classified the whole Mec class as physical, so magic and
            Feedback skills could remain stored in the wrong queue. Normalize them
            lazily without wiping the user's configured rotation.
            """
            moved = 0
            for row in list(self.server.db.skill_queue_rows(self.account_id)):
                skill = self.skill_by_id(row["skill_id"])
                if not skill:
                    continue
                desired = self.skill_queue_type(skill)
                current = str(row["queue_type"])
                if desired == current:
                    continue
                removed = self.server.db.remove_skill_queue_skill(
                    self.account_id, row["skill_id"]
                )
                if not removed:
                    continue
                ok, _position = self.server.db.add_skill_queue_entry(
                    self.account_id, desired, row["skill_id"]
                )
                if ok:
                    moved += 1
            if moved:
                self.skill_queue_cursors = {"physical": 0, "magic": 0, "feedback": 0}
                if self.skill_queue_next_type not in self.skill_queue_cursors:
                    self.skill_queue_next_type = "physical"
            return moved

    def skill_queue_type_label(self, queue_type):
            if queue_type == "magic":
                return "magiczna"
            if queue_type == "feedback":
                return "feedback"
            return "fizyczna"

    def skill_queue_active_mastery(self, queue_type):
            levels = []
            for row in self.server.db.active_class_rows(
                self.account_id, self.character.class_name
            ):
                class_name = str(row["class_name"])
                # Mec owns all three offensive/support channels.
                if class_name == "Mec" and queue_type in {"physical", "magic", "feedback"}:
                    levels.append(int(row["level"]))
                    continue
                wanted_type = class_type_for_name(class_name)
                if wanted_type == queue_type:
                    levels.append(int(row["level"]))
            return max(levels) if levels else 0

    def skill_queue_capacity(self, queue_type):
            # Sloty rosną wyłącznie z Character Level, nie z Biegłości klasy:
            # Level 1=40, 10=41, 100=50, 200=60, 400=80, 600=100.
            if self.skill_queue_active_mastery(queue_type) <= 0:
                return 0
            character_level = max(1, min(CHARACTER_MAX_LEVEL, int(self.character.character_level)))
            return min(40 + CHARACTER_MAX_LEVEL // 10, 40 + character_level // 10)

    def skill_queue_entries(self, queue_type, active_only=False):
            rows = list(self.server.db.skill_queue_rows(self.account_id, queue_type))
            if active_only:
                rows = rows[: self.skill_queue_capacity(queue_type)]
            return rows

    def skill_queue_find_position(self, query):
            raw = str(query or "").strip()
            normalized = self.normalize_description_query(raw)
            if not raw:
                return None, None, None

            # Dawne F1/M1 pozostają akceptowane; B/FB oznacza Feedback.
            short = normalized.replace(" ", "")
            match = re.fullmatch(r"(fb|[fmb])(\d+)", short)
            if match:
                prefix = match.group(1)
                queue_type = (
                    "physical" if prefix == "f"
                    else "magic" if prefix == "m"
                    else "feedback"
                )
                return queue_type, int(match.group(2)), None

            type_map = {
                "f": "physical", "fiz": "physical", "fizyczna": "physical",
                "fizyczne": "physical", "physical": "physical",
                "m": "magic", "mag": "magic", "magiczna": "magic",
                "magiczne": "magic", "magic": "magic",
                "b": "feedback", "fb": "feedback", "feedback": "feedback",
                "feetback": "feedback", "sprzezenie": "feedback",
            }

            tokens = raw.split()
            norm_tokens = [self.normalize_description_query(token) for token in tokens]

            if len(tokens) >= 2 and norm_tokens[0] in type_map and tokens[1].isdigit():
                return type_map[norm_tokens[0]], int(tokens[1]), None

            if len(tokens) >= 3 and norm_tokens[0] in ("slot", "miejsce") and tokens[1].isdigit():
                if norm_tokens[2] in type_map:
                    return type_map[norm_tokens[2]], int(tokens[1]), None

            if len(tokens) >= 3 and norm_tokens[0] in type_map and norm_tokens[1] in ("slot", "miejsce") and tokens[2].isdigit():
                return type_map[norm_tokens[0]], int(tokens[2]), None

            for row in self.server.db.skill_queue_rows(self.account_id):
                skill = self.skill_by_id(row["skill_id"])
                if not skill:
                    continue
                names = [skill["name"], skill["id"]] + skill.get("aliases", [])
                if any(
                    normalized == self.normalize_description_query(name)
                    for name in names
                ):
                    return row["queue_type"], int(row["position"]), skill
            return None, None, None

    async def show_skill_queue(self, queue_type=None):
            removed_protocols = self.cleanup_mec_protocols_from_queue_v10013()
            moved = self.normalize_skill_queue_types_v1125()
            if removed_protocols:
                await self.send(
                    f"Usunięto z kolejki {removed_protocols} pasywne umiejętności. "
                    "Po nauczeniu działają stale i nie zajmują slotów."
                )
            if moved:
                await self.send(
                    f"Uporządkowano {moved} wpisów Meca według typu skilla: "
                    "fizyczne, magiczne i Feedback."
                )
            enabled = self.server.db.skill_queue_enabled(self.account_id)
            await self.send(
                "AUTO KOLEJKA SKILLI: " + ("WŁĄCZONA." if enabled else "WYŁĄCZONA.")
            )
            types = (
                [queue_type]
                if queue_type in ("physical", "magic", "feedback")
                else ["physical", "magic", "feedback"]
            )
            for current_type in types:
                mastery = self.skill_queue_active_mastery(current_type)
                capacity = self.skill_queue_capacity(current_type)
                rows = self.skill_queue_entries(current_type)
                label = self.skill_queue_type_label(current_type).capitalize()
                if mastery <= 0:
                    await self.send(
                        f"Kolejka {label}: 0 aktywnych slotów. "
                        "Nie masz aktywnej klasy lub gałęzi tego typu."
                    )
                else:
                    await self.send(
                        f"Kolejka {label}: {len(rows)} zapisanych, {capacity} aktywnych slotów. "
                        f"Level postaci: {self.character.character_level}."
                    )
                if not rows:
                    await self.send(f"Kolejka {label}: pusta.")
                    continue
                for row in rows:
                    skill = self.skill_by_id(row["skill_id"])
                    name = skill["name"] if skill else row["skill_id"]
                    position = int(row["position"])
                    class_name = self.skill_class_name(skill) if skill else "nieznana klasa"
                    if class_name not in self.active_class_names():
                        active_text = "uśpiony: klasa nieaktywna"
                    elif position <= capacity:
                        active_text = "aktywny"
                    else:
                        active_text = "uśpiony ponad limitem"
                    await self.send(
                        f"Slot {position}. {name}. Typ {label.lower()}. Klasa {class_name}. {active_text}."
                    )
            await self.send(
                "Komendy: kolejka lista [fizyczna|magiczna|feedback], kolejka dodaj <skill>, "
                "kolejka usuń <numer>, kolejka usuń fizyczna <slot> / magiczna <slot> / feedback <slot>, "
                "kolejka wyczyść [fizyczna|magiczna|feedback], kolejka góra <typ> <slot>, "
                "kolejka dół <typ> <slot>, kolejka on, kolejka off. Dodanie skilla automatycznie włącza kolejkę."
            )

    async def handle_skill_queue(self, raw):
            self.normalize_skill_queue_types_v1125()
            text = str(raw or "").strip()
            if not text:
                await self.show_skill_queue()
                return

            parts = text.split(maxsplit=1)
            action = self.normalize_description_query(parts[0])
            value = parts[1].strip() if len(parts) > 1 else ""

            if action in ("on", "wlacz", "włącz", "start", "1"):
                self.server.db.set_skill_queue_enabled(self.account_id, True)
                await self.send(
                    "Auto kolejka skilli włączona. Podczas komendy atakuj system "
                    "spróbuje użyć następnego gotowego skilla z kolejki; jeśli żaden "
                    "nie jest gotowy, wykona zwykły atak."
                )
                return
            if action in ("off", "wylacz", "wyłącz", "stop", "0"):
                self.server.db.set_skill_queue_enabled(self.account_id, False)
                await self.send("Auto kolejka skilli wyłączona.")
                return
            if action in ("status", "lista", "list", "show"):
                list_type = self.normalize_description_query(value)
                if list_type in ("f", "fiz", "fizyczna", "fizyczne", "physical"):
                    await self.show_skill_queue("physical")
                elif list_type in ("m", "mag", "magiczna", "magiczne", "magic"):
                    await self.show_skill_queue("magic")
                elif list_type in ("b", "fb", "feedback", "feetback", "sprzezenie"):
                    await self.show_skill_queue("feedback")
                else:
                    await self.show_skill_queue()
                return
            if action in ("fizyczna", "fizyczne", "physical"):
                await self.show_skill_queue("physical")
                return
            if action in ("magiczna", "magiczne", "magic"):
                await self.show_skill_queue("magic")
                return
            if action in ("feedback", "feetback", "fb", "sprzezenie"):
                await self.show_skill_queue("feedback")
                return

            if action in ("dodaj", "add", "+"):
                if not value:
                    await self.send("Użycie: kolejka dodaj <nazwa skilla>.")
                    return
                skill, _target = self.find_skill_from_input(value)
                if not skill:
                    await self.send(
                        "Nie rozpoznaję skilla aktywnej klasy. Użyj pełnej nazwy z komendy skills."
                    )
                    return
                if not self.server.db.knows_skill(self.account_id, skill["id"]):
                    await self.send(f"Najpierw musisz nauczyć się umiejętności {skill['name']}.")
                    return
                if str(skill.get("kind", "")).lower() == "passive":
                    await self.send(
                        f"{skill['name']} jest umiejętnością pasywną. "
                        "Po nauczeniu działa automatycznie cały czas i nie dodaje się jej do kolejki."
                    )
                    return
                skill_class = self.skill_class_name(skill)
                mastery = self.class_mastery_level(skill_class)
                if mastery < int(skill["unlock"]):
                    await self.send(
                        f"{skill['name']} wymaga Biegłości klasy {skill['unlock']}. "
                        f"Aktualna Biegłość {skill_class}: {mastery}."
                    )
                    return
                queue_type = self.skill_queue_type(skill)
                capacity = self.skill_queue_capacity(queue_type)
                if capacity <= 0:
                    await self.send(
                        f"Nie masz aktywnych slotów kolejki {self.skill_queue_type_label(queue_type)}."
                    )
                    return
                current = self.skill_queue_entries(queue_type)
                if len(current) >= capacity:
                    await self.send(
                        f"Kolejka {self.skill_queue_type_label(queue_type)} jest pełna: "
                        f"{len(current)} z {capacity} slotów. Level postaci {self.character.character_level}. "
                        "Rozwijaj Level postaci, aby odblokować więcej slotów."
                    )
                    return
                ok, result = self.server.db.add_skill_queue_entry(
                    self.account_id, queue_type, skill["id"]
                )
                if not ok:
                    await self.send(str(result))
                    return
                self.server.db.set_skill_queue_enabled(self.account_id, True)
                await self.send(
                    f"Dodano do kolejki {self.skill_queue_type_label(queue_type)}: "
                    f"{skill['name']}. Slot {result} z {capacity}. "
                    "Auto kolejka została włączona. Jeśli walka już trwa, wpis może zostać użyty od najbliższej automatycznej akcji."
                )
                return

            if action in ("usun", "usuń", "remove", "delete", "-"):
                if value.isdigit():
                    global_position = int(value)
                    all_rows = list(self.server.db.skill_queue_rows(self.account_id))
                    if global_position < 1 or global_position > len(all_rows):
                        await self.send(
                            f"Nie ma wpisu numer {global_position}. Wpisz kolejka, aby zobaczyć aktualną listę."
                        )
                        return
                    selected = all_rows[global_position - 1]
                    queue_type = selected["queue_type"]
                    position = int(selected["position"])
                    skill = self.skill_by_id(selected["skill_id"])
                else:
                    queue_type, position, skill = self.skill_queue_find_position(value)
                if not queue_type or not position:
                    await self.send(
                        "Nie znajduję takiego wpisu. Użyj np. kolejka usuń 1, "
                        "kolejka usuń fizyczna 1, magiczna 1, feedback 1 albo nazwę skilla."
                    )
                    return
                if skill is None:
                    rows = self.skill_queue_entries(queue_type)
                    skill = next(
                        (self.skill_by_id(row["skill_id"]) for row in rows if int(row["position"]) == position),
                        None,
                    )
                removed = self.server.db.remove_skill_queue_entry(
                    self.account_id, queue_type, position
                )
                if not removed:
                    await self.send("Nie ma takiego slotu w kolejce.")
                    return
                removed_skill = skill or self.skill_by_id(removed)
                name = removed_skill["name"] if removed_skill else removed
                self.skill_queue_cursors[queue_type] = 0
                await self.send(f"Usunięto z kolejki: {name}.")
                return

            if action in ("wyczysc", "wyczyść", "clear"):
                normalized_value = self.normalize_description_query(value)
                if normalized_value in ("f", "fiz", "fizyczna", "fizyczne", "physical"):
                    self.server.db.clear_skill_queue(self.account_id, "physical")
                    self.skill_queue_cursors["physical"] = 0
                    await self.send("Wyczyszczono kolejkę fizyczną.")
                elif normalized_value in ("m", "mag", "magiczna", "magiczne", "magic"):
                    self.server.db.clear_skill_queue(self.account_id, "magic")
                    self.skill_queue_cursors["magic"] = 0
                    await self.send("Wyczyszczono kolejkę magiczną.")
                elif normalized_value in ("b", "fb", "feedback", "feetback", "sprzezenie"):
                    self.server.db.clear_skill_queue(self.account_id, "feedback")
                    self.skill_queue_cursors["feedback"] = 0
                    await self.send("Wyczyszczono kolejkę Feedback.")
                else:
                    self.server.db.clear_skill_queue(self.account_id)
                    self.skill_queue_cursors = {"physical": 0, "magic": 0, "feedback": 0}
                    await self.send("Wyczyszczono wszystkie trzy kolejki skilli.")
                return

            if action in ("gora", "góra", "up", "dol", "dół", "down"):
                queue_type, position, _skill = self.skill_queue_find_position(value)
                if not queue_type or not position:
                    await self.send(
                        "Użycie: kolejka góra fizyczna 2, kolejka dół magiczna 1 "
                        "albo kolejka góra feedback 2."
                    )
                    return
                delta = -1 if action in ("gora", "góra", "up") else 1
                if not self.server.db.move_skill_queue_entry(
                    self.account_id, queue_type, position, delta
                ):
                    await self.send("Nie można przesunąć tego slotu w wybranym kierunku.")
                    return
                self.skill_queue_cursors[queue_type] = 0
                await self.send("Kolejność skilli została zmieniona.")
                return

            await self.send(
                "Użycie: kolejka, kolejka lista [fizyczna|magiczna|feedback], "
                "kolejka dodaj <skill>, kolejka usuń <typ> <slot>, kolejka wyczyść [typ], "
                "kolejka fizyczna, kolejka magiczna, kolejka feedback, kolejka on/off."
            )

    async def mec_self_repair_round_v11154(self):
            """Advance Self-Repair by one Mec combat round.
            Feedback damage is restored in full after exactly three owner action rounds.
            Source also grants Auto-Regen, but its numeric amount is not supplied;
            this runtime therefore implements only the exact 3-round Feedback repair.
            """
            if not self.character or self.character.class_name!="Mec" or not self.job_ability_selected("inherent","v0319_mec_self_repair"):
                return
            round_no=int(getattr(self,"v0319_mec_round",0) or 0)+1
            self.v0319_mec_round=round_no
            queue=list(getattr(self,"v0319_feedback_repair_queue",[]) or [])
            due=[x for x in queue if int(x[0])<=round_no]
            self.v0319_feedback_repair_queue=[x for x in queue if int(x[0])>round_no]
            repaired=sum(max(0,int(x[1])) for x in due)
            if repaired and self.current_hp>0:
                before=self.current_hp
                self.current_hp=min(self.max_hp(),self.current_hp+repaired)
                actual=self.current_hp-before
                if actual: await self.send(f"Self-Repair: naprawiono {actual} HP obrażeń Feedback po 3 rundach.")

    def queue_mec_feedback_repair_v11154(self, amount):
            if not self.character or self.character.class_name!="Mec" or not self.job_ability_selected("inherent","v0319_mec_self_repair"):
                return
            round_no=int(getattr(self,"v0319_mec_round",0) or 0)
            queue=list(getattr(self,"v0319_feedback_repair_queue",[]) or [])
            queue.append((round_no+3,max(0,int(amount))))
            self.v0319_feedback_repair_queue=queue

    def skill_effect_duration_v11153(self, skill, skill_level, base_seconds=None):
            """Return only authored/source-backed duration values.
            Skill Level/Will may influence duration qualitatively, but without an
            authored numeric curve this helper must not invent seconds.
            """
            for key in ("duration","duration_seconds","duration_base"):
                value=skill.get(key)
                if value is not None:
                    try:
                        return max(1,int(value))
                    except (TypeError,ValueError):
                        pass
            if base_seconds is not None and skill.get("duration_source_defined"):
                return max(1,int(base_seconds))
            return None

    def cleanup_skill_buffs(self):
            """Usuń wygasłe czasowe buffy i ogłoś naturalne wygaśnięcie dokładnie raz."""
            now = time.time()
            buffs = getattr(self, "active_skill_buffs", {})
            expired_names = []
            for skill_id, data in list(buffs.items()):
                if now >= float(data.get("until", 0.0) or 0.0):
                    removed = buffs.pop(skill_id, None)
                    if removed:
                        expired_names.append(str(removed.get("name") or skill_id))
            for name in expired_names:
                try:
                    asyncio.get_running_loop().create_task(
                        self.send(f"Buff wygasł: {name}.")
                    )
                except RuntimeError:  # AUDIT_INTENTIONAL_PASS: static audit/no running event loop
                    # Poza działającą pętlą asyncio (np. statyczny audit) nie ma klienta,
                    # któremu można wysłać komunikat.
                    pass

    def skill_buff_active(self, skill_id):
            self.cleanup_skill_buffs()
            return skill_id in getattr(self, "active_skill_buffs", {})

    def passive_class_boost_multiplier_v11134(self, exclude_skill_id=None, target_type=None):
            """Stały bonus z nauczonych zwykłych klasowych boostów.

            Fizyczne boosty wzmacniają wyłącznie fizyczne skille, a magiczne
            wyłącznie magiczne. Mec Feedback jest osobnym kanałem i nie dziedziczy
            zwykłych boostów physical/magic. Bez target_type zachowujemy neutralny
            odczyt używany poza konkretną akcją bojową.
            """
            wanted_type = str(target_type or "").strip().lower()
            if wanted_type == "feedback":
                return 1.0
            total_bonus = 0.0
            for class_name in self.active_class_names():
                boost_type = class_type_for_name(class_name)
                if wanted_type in {"physical", "magic"} and boost_type != wanted_type:
                    continue
                for skill in CLASS_SKILLS.get(class_name, []):
                    if str(skill.get("kind", "")) != "boost":
                        continue
                    if skill.get("active_special") or str(skill.get("mec_special", "")) == "vmax":
                        continue
                    if exclude_skill_id and skill.get("id") == exclude_skill_id:
                        continue
                    if not self.server.db.knows_skill(self.account_id, skill["id"]):
                        continue
                    if not self.skill_mastery_unlocked(skill):
                        continue
                    progress = self.server.db.skill_progress(self.account_id, skill["id"])
                    level = max(1, int(progress["level"]))
                    authored = max(1.0, float(skill.get("boost", 1.0) or 1.0))
                    base_bonus = max(0.0, authored - 1.0)
                    scaled_bonus = base_bonus * (1.0 + min(1.0, level / float(SKILL_MAX_LEVEL)))
                    total_bonus += min(0.90, scaled_bonus)
            return 1.0 + total_bonus

    def skill_buff_multiplier(self, exclude_skill_id=None, target_type=None):
            """Mnożnik boostów właściwy dla bieżącego typu akcji.

            Pasywne boosty zachowują tożsamość fizyczną/magiczną. Specjalny
            aktywny buff może opcjonalnie ustawić buff_type; brak typu oznacza
            efekt ogólny zgodnie z jego własną mechaniką.
            """
            self.cleanup_skill_buffs()
            wanted_type = str(target_type or "").strip().lower()
            total_bonus = max(
                0.0,
                self.passive_class_boost_multiplier_v11134(
                    exclude_skill_id, target_type=wanted_type or None
                ) - 1.0,
            )
            for skill_id, data in getattr(self, "active_skill_buffs", {}).items():
                if exclude_skill_id and skill_id == exclude_skill_id:
                    continue
                buff_type = str(data.get("buff_type", "") or "").strip().lower()
                if wanted_type in {"physical", "magic", "feedback"} and buff_type in {"physical", "magic"}:
                    if wanted_type == "feedback" or buff_type != wanted_type:
                        continue
                total_bonus += max(0.0, float(data.get("boost", 1.0) or 1.0) - 1.0)
            return min(2.25, 1.0 + total_bonus)

    def permanence_active_v11154(self):
            """Canonical Permanence: enemy dispels cannot remove beneficial effects."""
            self.cleanup_skill_buffs()
            buffs=getattr(self,"active_skill_buffs",{})
            for skill_id,data in buffs.items():
                if str(skill_id).endswith("_permanence") and time.time()<float(data.get("until",0.0) or 0.0):
                    return True
            # Soulbound currently keeps Permanence as a buff/V-MAX mechanic.
            # No external Job/Trainer progression is installed.
            return False

    def vmax_permanence_active_v11152(self):
            """Compatibility alias for the canonical Permanence query."""
            return self.permanence_active_v11154()

    def clear_skill_buffs(self, hostile=False):
            buffs=getattr(self,"active_skill_buffs",{})
            # Permanence contract: while Permanence is active, enemy dispels
            # cannot remove beneficial effects. V-MAX grants Permanence,
            # so hostile clearing preserves the complete beneficial buff set,
            # not only the V-MAX marker itself.
            if hostile and self.permanence_active_v11154():
                return
            buffs.clear()

    def local_party_buff_recipients_v03511(self):
            """All living party members standing with the caster, including solo self."""
            recipients = self.server.party_sessions(
                self.account_id, same_room=self.character.room_id
            ) or [self]
            valid = [
                session for session in recipients
                if not session.closed and session.character and session.current_hp > 0
                and session.character.room_id == self.character.room_id
            ]
            if self not in valid and self.character and not self.closed and self.current_hp > 0:
                valid.append(self)
            return sorted(valid, key=lambda session: session.character.name.casefold())

    def beneficial_status_active_v11154(self, status):
            key="v0319_vmax_"+str(status or "").strip().casefold()
            buff=getattr(self,"active_skill_buffs",{}).get(key)
            if not buff:
                return False
            return time.time() < float(buff.get("until",0.0) or 0.0)

    def player_action_interval_v11154(self):
            """Return the normal realtime action cadence.

            UOSS combat logs supplied for Mec show V-MAX Haste as a larger
            ordinary-attack hit string (5 -> 10 at AGI 547). Soulbound models
            that in the DEX/AGI multi-hit calculation, so Haste must not also
            shorten the realtime interval and double-dip total throughput.
            """
            return float(getattr(self,"combat_player_interval",1.0) or 1.0)

    def party_vmax_support_active_v03511(self):
            """Compatibility query: V-MAX is self-only; old party V-MAX state is ignored."""
            return self.mec_vmax_active_v0319()

    def engineer_skill_known_v0317(self, skill_id):
            try:
                return bool(self.server.db.knows_skill(self.account_id, skill_id))
            except Exception:
                return False

    def engineer_upgrade_slots_v0317(self):
            slots = 1
            if self.engineer_skill_known_v0317("v0317_engineer_silver_gear"):
                slots += 1
            if self.engineer_skill_known_v0317("v0317_engineer_gold_battery"):
                slots += 1
            return slots

    def engineer_upgraded_tools_v0317(self):
            try:
                rows = self.server.db.conn.execute(
                    "SELECT skill_id FROM engineer_tool_upgrades_v0317 WHERE account_id=? ORDER BY upgraded_at, skill_id",
                    (int(self.account_id),),
                ).fetchall()
                return {str(row["skill_id"]) for row in rows}
            except Exception:
                return set()

    def engineer_tool_is_upgraded_v0317(self, skill):
            return str(skill.get("id", "")) in self.engineer_upgraded_tools_v0317()

    def engineer_passive_multiplier_v0317(self, skill):
            category = str(skill.get("engineer_category", ""))
            mult = 1.0
            pairs = []
            if category == "single": pairs.append("v0317_engineer_hypercharge")
            if category == "area": pairs.append("v0317_engineer_lindblum")
            for sid in pairs:
                if not self.engineer_skill_known_v0317(sid):
                    continue
                row = self.server.db.skill_progress(self.account_id, sid)
                level = int(row["level"])
                progress = (max(1, min(SKILL_MAX_LEVEL, level)) - 1) / float(max(1, SKILL_MAX_LEVEL - 1))
                mult *= 1.05 + 0.25 * (progress ** 0.82)
            return mult

    def mec_skill_known_v0319(self, skill_id):
            try:
                return bool(self.server.db.knows_skill(self.account_id, skill_id))
            except Exception:
                return False

    def mec_vmax_active_v0319(self):
            return time.time() < float(getattr(self, "v0319_vmax_until", 0.0) or 0.0)

    def mec_overheat_active_v0319(self):
            # UOSS specifies a brief Overheat after V-MAX but gives no duration.
            # Represent it as a recovery action instead of inventing seconds.
            return bool(getattr(self, "v0319_overheat_recovery_pending", False))

    def mec_finish_overheat_recovery_v0319(self):
            if bool(getattr(self, "v0319_overheat_recovery_pending", False)):
                self.v0319_overheat_recovery_pending=False
                return True
            return False

    async def mec_refresh_vmax_v0319(self):
            now=time.time()
            until=float(getattr(self,"v0319_vmax_until",0.0) or 0.0)
            if until and now < until and not self.mec_support_effect_v11149():
                self.v0319_vmax_support_maintained=False
            if until and now >= until:
                self.v0319_vmax_until=0.0
                # UOSS confirms a brief Overheat but supplies no numeric
                # duration. Model it as one recovery action, not a fabricated
                # seconds-based timer.
                if not bool(getattr(self,"v0319_vmax_support_maintained",False)):
                    self.v0319_overheat_recovery_pending=True
                self.v0319_vmax_support_maintained=False
                self.active_skill_buffs.pop("v0319_mec_vmax",None)
                for _status in ("protect","shell","haste","regen","preach","praise","permanence"):
                    self.active_skill_buffs.pop("v0319_vmax_"+_status,None)
                if self.mec_overheat_active_v0319():
                    await self.send("V-MAX wygasa. OVERHEAT: wszystkie statystyki bojowe są osłabione do zakończenia następnej akcji regeneracyjnej i V-MAX nie może być ponownie użyty.")
                else:
                    await self.send("V-MAX wygasa. Support Effect utrzymany do końca: brak OVERHEAT.")

    def mec_support_effect_v11149(self):
            """Soulbound adaptation of the UOSS Cyborg support weapon.

            Soulbound has one persistent Soul Weapon instead of separate Mec weapon
            categories. The Mec's Soul Weapon therefore *is* the support weapon for
            source mechanics that require one. Do not infer support mode from WILL
            dominance: V-MAX itself is Will-influenced, but weapon identity is separate.
            """
            if not self.character or self.character.class_name != "Mec":
                return False
            return bool(str(getattr(self.character, "soul_weapon", "") or "").strip())

    def mec_protocol_multiplier_v11196(self, skill_id):
            """Automatic Mec Protocol potency from its own Skill Level.

            UOSS confirms that Protocol level increases the mapped branch's damage
            but does not expose a numeric curve. Soulbound uses an explicit balance
            curve from +5% at Skill Level 1 to +75% at Skill Level 600.
            """
            sid=str(skill_id or "")
            if not sid or not self.mec_skill_known_v0319(sid):
                return 1.0
            progress_row=self.server.db.skill_progress(self.account_id,sid)
            level=max(1,min(SKILL_MAX_LEVEL,int(progress_row["level"])))
            progress=(level-1)/float(max(1,SKILL_MAX_LEVEL-1))
            return 1.05 + 0.70*(progress ** 0.82)

    def mec_branch_multiplier_v0319(self, branch, special=None):
            mult=1.0
            # Protocols are Automatic passives, but source contracts map them to
            # explicit skill lists rather than blindly to every skill in a branch.
            protocols={
              "melee":"v0319_mec_strength_protocol",
              "ranged":"v0319_mec_ranged_protocol",
              "feedback":"v0319_mec_feedback_protocol",
              "magic":"v0319_mec_magic_protocol",
            }
            sid=protocols.get(branch)
            mapped=tuple(MEC_PROTOCOL_SKILLS_V11155.get(sid,())) if sid else ()
            if sid and special and str(special) in mapped:
                mult*=self.mec_protocol_multiplier_v11196(sid)
            # Legacy callers without a special keep branch behavior only where the
            # source map is not needed for correctness. Combat callers pass special.
            elif sid and special is None and branch!="feedback":
                mult*=self.mec_protocol_multiplier_v11196(sid)
            # Overheat lowers all combat stats, but its numeric penalty is not
            # specified by source; do not fabricate a 25% reduction.
            return mult

    def engineer_upgrade_effect_text_v0319(self, special, upgraded):
            if not upgraded: return "bazowe"
            return {
              "auto_crossbow":"więcej obrażeń", "mako_gun":"więcej obrażeń + dobór najlepszego elementu",
              "bio_blaster":"więcej obrażeń + mocniejszy Poison", "flash":"więcej obrażeń + Blind/Guard Break",
              "debilitator":"3 podatności żywiołowe", "drill":"więcej obrażeń + dispel pozytywnych efektów + pęknięcie pancerza",
              "napalm":"więcej obrażeń + łatwopalny olej", "launcher":"do 6 pocisków",
              "noise_blaster":"obrażenia obszarowe + dłuższe Silence + Slow", "chainsaw":"Demi -> Quarter + HP Leak",
              "mega_bomb":"zwiększone obrażenia wszystkim celom", "air_anchor":"większy proc damage",
            }.get(special,"ulepszony efekt")

    def auto_queue_skill_usable(self, skill, mob):
            if not skill:
                return False
            skill_class = self.skill_class_name(skill)
            if skill_class not in self.active_class_names():
                return False
            if not self.server.db.knows_skill(self.account_id, skill["id"]):
                return False
            if not self.skill_mastery_unlocked(skill):
                return False
            # v1.11.40: ordinary skills of every class are cooldown-free.
            # Auto-queue respects only explicit special-mechanic timers.
            kind = str(skill.get("kind", ""))
            if skill.get("mechanic_cooldown"):
                if self.skill_cooldown_ready_at_v0364(skill) > time.time():
                    return False
            skill_class = self.skill_class_name(skill)
            if effective_skill_mana_cost(skill, skill_class) > self.current_mana:
                return False

            kind = skill.get("kind")
            if kind in ("passive", "utility"):
                return False
            if kind == "boost" and not skill.get("active_special") and str(skill.get("mec_special", "")) != "vmax":
                return False
            if kind in ("damage", "drain", "execute", "aoe_damage"):
                if not mob or not mob.alive or mob.room_id != self.character.room_id:
                    return False
            elif kind in ("heal", "regen"):
                recipients = self.server.party_sessions(
                    self.account_id, same_room=self.character.room_id
                ) or [self]
                if not any(
                    session.current_hp < session.max_hp()
                    for session in recipients
                    if not session.closed and session.character and session.current_hp > 0
                ):
                    return False
            elif kind == "group_heal":
                recipients = self.server.party_sessions(
                    self.account_id, same_room=self.character.room_id
                ) or [self]
                if not any(session.current_hp < session.max_hp() for session in recipients):
                    return False
            elif kind == "guard" and self.skill_guard > 0:
                return False
            elif kind == "evade":
                if self.skill_evade:
                    return False
            elif kind == "boost":
                # Nie ponawiaj tego samego buffa, dopóki jeszcze działa. Inne buffy
                # mogą być aktywowane równocześnie i składają się addytywnie.
                if self.skill_buff_active(skill.get("id")):
                    return False
            return True

    async def try_auto_skill_queue(self, mob):
            if not self.server.db.skill_queue_enabled(self.account_id):
                return False

            # Existing pre-v1.12.5 Mec entries are corrected lazily before use.
            self.normalize_skill_queue_types_v1125()
            queue_types = ("physical", "magic", "feedback")
            preferred = self.skill_queue_next_type
            if preferred not in queue_types:
                preferred = "physical"
            preferred_index = queue_types.index(preferred)
            order = list(queue_types[preferred_index:]) + list(queue_types[:preferred_index])
            for queue_type in order:
                rows = self.skill_queue_entries(queue_type, active_only=True)
                if not rows:
                    continue
                count = len(rows)
                start = self.skill_queue_cursors.get(queue_type, 0) % count
                for offset in range(count):
                    index = (start + offset) % count
                    row = rows[index]
                    skill = self.skill_by_id(row["skill_id"])
                    if not self.auto_queue_skill_usable(skill, mob):
                        continue
                    self.skill_queue_cursors[queue_type] = (index + 1) % count
                    used_index = queue_types.index(queue_type)
                    self.skill_queue_next_type = queue_types[
                        (used_index + 1) % len(queue_types)
                    ]
                    # combat_mob_key jest już ustawiony przez attack(), więc skille
                    # ofensywne automatycznie trafiają bieżący cel.
                    self.auto_queue_casting = True
                    try:
                        await self.use_class_skill(skill["name"])
                    finally:
                        self.auto_queue_casting = False
                    return True
            return False
