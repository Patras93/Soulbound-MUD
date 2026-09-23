# -*- coding: utf-8 -*-
"""Skill queues, buffs and class support helpers."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import asyncio
import re
import time
from player.session_mixins.equipment_stats import class_type_for_name
from player.session_mixins.shops_teachers import CHARACTER_MAX_LEVEL
from player.session_mixins.skill_learning import CLASS_SKILLS, SKILL_MAX_LEVEL


class SessionSkillQueueBuffsMixin:
    def skill_by_id(self, skill_id):
            for class_name, skills in CLASS_SKILLS.items():
                for skill in skills:
                    if skill["id"] == skill_id:
                        return skill
            return None

    def skill_queue_type(self, skill):
            class_name = self.skill_class_name(skill)
            return "magic" if class_type_for_name(class_name) == "magic" else "physical"

    def skill_queue_type_label(self, queue_type):
            return "magiczna" if queue_type == "magic" else "fizyczna"

    def skill_queue_active_mastery(self, queue_type):
            levels = []
            for row in self.server.db.active_class_rows(
                self.account_id, self.character.class_name
            ):
                wanted_type = class_type_for_name(row["class_name"])
                if wanted_type == queue_type:
                    levels.append(int(row["level"]))
            return max(levels) if levels else 0

    def skill_queue_capacity(self, queue_type):
            # v0.30.18: startowa pojemność kolejki to 10 slotów.
            # Sloty nadal rosną wyłącznie z Character Level, nie z Biegłości klasy:
            # Level 1=10, 10=11, 100=20, 200=30, 400=50, 600=70.
            if self.skill_queue_active_mastery(queue_type) <= 0:
                return 0
            character_level = max(1, min(CHARACTER_MAX_LEVEL, int(self.character.character_level)))
            return min(10 + CHARACTER_MAX_LEVEL // 10, 10 + character_level // 10)

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

            # v0.8.36: publiczna składnia używa zwykłych numerów slotów,
            # np. `fizyczna 1`, `magiczna 2`, `slot 1 fizyczna`.
            # Dawne F1/M1 pozostają akceptowane wyłącznie dla kompatybilności.
            short = normalized.replace(" ", "")
            match = re.fullmatch(r"([fm])(\d+)", short)
            if match:
                queue_type = "physical" if match.group(1) == "f" else "magic"
                return queue_type, int(match.group(2)), None

            type_map = {
                "f": "physical", "fiz": "physical", "fizyczna": "physical",
                "fizyczne": "physical", "physical": "physical",
                "m": "magic", "mag": "magic", "magiczna": "magic",
                "magiczne": "magic", "magic": "magic",
            }

            tokens = raw.split()
            norm_tokens = [self.normalize_description_query(token) for token in tokens]

            # fizyczna 1 / magiczna 2
            if len(tokens) >= 2 and norm_tokens[0] in type_map and tokens[1].isdigit():
                return type_map[norm_tokens[0]], int(tokens[1]), None

            # slot 1 fizyczna / slot 2 magiczna
            if len(tokens) >= 3 and norm_tokens[0] in ("slot", "miejsce") and tokens[1].isdigit():
                if norm_tokens[2] in type_map:
                    return type_map[norm_tokens[2]], int(tokens[1]), None

            # fizyczna slot 1 / magiczna slot 2
            if len(tokens) >= 3 and norm_tokens[0] in type_map and norm_tokens[1] in ("slot", "miejsce") and tokens[2].isdigit():
                return type_map[norm_tokens[0]], int(tokens[2]), None

            # Nazwa skilla: szukamy także w nieaktywnych wpisach, aby można było
            # usunąć skill z kolejki po wyłączeniu klasy multiclass.
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
            enabled = self.server.db.skill_queue_enabled(self.account_id)
            await self.send(
                "AUTO KOLEJKA SKILLI: " + ("WŁĄCZONA." if enabled else "WYŁĄCZONA.")
            )
            types = [queue_type] if queue_type in ("physical", "magic") else ["physical", "magic"]
            for current_type in types:
                mastery = self.skill_queue_active_mastery(current_type)
                capacity = self.skill_queue_capacity(current_type)
                rows = self.skill_queue_entries(current_type)
                label = self.skill_queue_type_label(current_type).capitalize()
                if mastery <= 0:
                    await self.send(
                        f"Kolejka {label}: 0 aktywnych slotów. "
                        "Nie masz aktywnej klasy tego typu."
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
                "Komendy: kolejka lista [fizyczna|magiczna], kolejka dodaj <skill>, "
                "kolejka usuń fizyczna <slot> / kolejka usuń magiczna <slot>, "
                "kolejka wyczyść [fizyczna|magiczna], kolejka góra fizyczna <slot>, "
                "kolejka dół magiczna <slot>, kolejka on, kolejka off. Dodanie skilla automatycznie włącza kolejkę."
            )

    async def handle_skill_queue(self, raw):
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
                else:
                    await self.show_skill_queue()
                return
            if action in ("fizyczna", "fizyczne", "physical"):
                await self.show_skill_queue("physical")
                return
            if action in ("magiczna", "magiczne", "magic"):
                await self.show_skill_queue("magic")
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
                # v0.8.34: kolejka ma działać natychmiast po dodaniu skilla/spella.
                # Użytkownik nie musi już wykonywać osobnego `kolejka on`.
                self.server.db.set_skill_queue_enabled(self.account_id, True)
                await self.send(
                    f"Dodano do kolejki {self.skill_queue_type_label(queue_type)}: "
                    f"{skill['name']}. Slot {result} z {capacity}. "
                    "Auto kolejka została włączona. Jeśli walka już trwa, wpis może zostać użyty od najbliższej automatycznej akcji."
                )
                return

            if action in ("usun", "usuń", "remove", "delete", "-"):
                queue_type, position, skill = self.skill_queue_find_position(value)
                if not queue_type or not position:
                    await self.send(
                        "Nie znajduję takiego wpisu. Użyj np. kolejka usuń fizyczna 1, "
                        "kolejka usuń magiczna 2 albo kolejka usuń <nazwa skilla>."
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
                else:
                    self.server.db.clear_skill_queue(self.account_id)
                    self.skill_queue_cursors = {"physical": 0, "magic": 0}
                    await self.send("Wyczyszczono obie kolejki skilli.")
                return

            if action in ("gora", "góra", "up", "dol", "dół", "down"):
                queue_type, position, _skill = self.skill_queue_find_position(value)
                if not queue_type or not position:
                    await self.send("Użycie: kolejka góra fizyczna 2 albo kolejka dół magiczna 1.")
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
                "Użycie: kolejka, kolejka lista [fizyczna|magiczna], kolejka dodaj <skill>, "
                "kolejka usuń fizyczna <slot> / kolejka usuń magiczna <slot>, "
                "kolejka wyczyść, kolejka fizyczna, kolejka magiczna, kolejka on/off."
            )

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
                except RuntimeError:
                    # Poza działającą pętlą asyncio (np. statyczny audit) nie ma klienta,
                    # któremu można wysłać komunikat.
                    pass

    def skill_buff_active(self, skill_id):
            self.cleanup_skill_buffs()
            return skill_id in getattr(self, "active_skill_buffs", {})

    def skill_buff_multiplier(self, exclude_skill_id=None):
            """Łączny mnożnik wszystkich aktywnych buffów.

            Bonusy sumują się addytywnie (+35% i +55% = +90%), więc różne buffy
            nadal mogą działać razem i uniwersalnie wzmacniają wszystkie skille/spelle.
            v0.8.64 ogranicza łączny bonus do +125% (x2.25). Buffy nie wzmacniają
            siły kolejnego buffa - zapobiega to pętli multiclass buff->buff.
            """
            self.cleanup_skill_buffs()
            total_bonus = 0.0
            for skill_id, data in getattr(self, "active_skill_buffs", {}).items():
                if exclude_skill_id and skill_id == exclude_skill_id:
                    continue
                total_bonus += max(0.0, float(data.get("boost", 1.0) or 1.0) - 1.0)
            return min(2.25, 1.0 + total_bonus)

    def clear_skill_buffs(self):
            getattr(self, "active_skill_buffs", {}).clear()

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

    def apply_party_boost_v03511(self, skill_id, name, boost, until, source=None):
            """Apply one combat boost to every living local party member."""
            recipients = self.local_party_buff_recipients_v03511()
            data = {
                "name": str(name),
                "boost": max(1.0, float(boost or 1.0)),
                "until": float(until),
                "source": str(source or self.character.name),
            }
            for session in recipients:
                session.active_skill_buffs[str(skill_id)] = dict(data)
            return recipients

    def party_vmax_support_active_v03511(self):
            """V-MAX party support grants Protect/Shell/Regen without granting Mec-only skill rewrites."""
            return (
                self.mec_vmax_active_v0319()
                or time.time() < float(getattr(self, "v03511_party_vmax_until", 0.0) or 0.0)
            )

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
            return time.time() < float(getattr(self, "v0319_overheat_until", 0.0) or 0.0)

    async def mec_refresh_vmax_v0319(self):
            now=time.time()
            until=float(getattr(self,"v0319_vmax_until",0.0) or 0.0)
            if until and now >= until:
                self.v0319_vmax_until=0.0
                # UOSS source confirms Overheat after V-MAX; exact duration is not supplied,
                # so Soulbound uses a short 20-second recovery window.
                _vd,_vc=self.server.db.vmax_upgrades_v03114(self.account_id)
                _overheat=max(4,20-8*_vc)
                self.v0319_overheat_until=max(float(getattr(self,"v0319_overheat_until",0.0) or 0.0),now+_overheat)
                self.active_skill_buffs.pop("v0319_mec_vmax",None)
                await self.send(f"V-MAX wygasa. OVERHEAT: wszystkie statystyki bojowe są osłabione przez {_overheat} sekund i V-MAX nie może być ponownie użyty.")

    def mec_branch_multiplier_v0319(self, branch):
            mult=1.0
            checks={
              "melee":("v0319_mec_combat_mastery","v0319_mec_strength_protocol"),
              "ranged":("v0319_mec_shooting_mastery","v0319_mec_ranged_protocol"),
              "feedback":(None,"v0319_mec_feedback_protocol"),
              "magic":("v0319_mec_maxwell_program","v0319_mec_magic_protocol"),
            }
            for sid in checks.get(branch,()):
                if sid and self.mec_skill_known_v0319(sid):
                    row=self.server.db.skill_progress(self.account_id,sid)
                    level=int(row["level"]); progress=(max(1,min(SKILL_MAX_LEVEL,level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                    mult*=1.04 + 0.21*(progress**0.82)
            if self.mec_overheat_active_v0319(): mult*=0.75
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
            if self.skill_cooldown_ready_at_v0364(skill) > time.time():
                return False
            if int(skill.get("mana", 0)) > self.current_mana:
                return False

            kind = skill.get("kind")
            if kind in ("passive", "utility"):
                return False
            if kind in ("damage", "drain", "execute", "aoe_damage"):
                if not mob or not mob.alive or mob.room_id != self.character.room_id:
                    return False
            elif kind == "heal":
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

            preferred = self.skill_queue_next_type
            order = [preferred, "magic" if preferred == "physical" else "physical"]
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
                    self.skill_queue_next_type = (
                        "magic" if queue_type == "physical" else "physical"
                    )
                    # combat_mob_key jest już ustawiony przez attack(), więc skille
                    # ofensywne automatycznie trafiają bieżący cel.
                    self.auto_queue_casting = True
                    try:
                        await self.use_class_skill(skill["name"])
                    finally:
                        self.auto_queue_casting = False
                    return True
            return False
