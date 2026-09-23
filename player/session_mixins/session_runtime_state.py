# -*- coding: utf-8 -*-
"""Session initialization, cooldowns, x2 EXP, wimpy and temple teleport."""

class SessionRuntimeStateMixin:

    def __init__(self, server, reader, writer):
            self.server = server
            self.reader = reader
            self.writer = writer
            self.input_encoding = DEFAULT_TEXT_ENCODING
            self.output_encoding = DEFAULT_TEXT_ENCODING
            self.master_account_id = None
            # account_id pozostaje identyfikatorem aktywnej postaci, aby wszystkie
            # istniejące systemy zapisu nadal działały bez mieszania slotów.
            self.account_id = None
            self.character = None
            self.closed = False
            self.current_hp = 0
            self.current_mana = 0
            self.combat_mob_key = None
            # v0.8.34: walka działa w czasie rzeczywistym. Jedno zadanie asyncio
            # prowadzi niezależne timery akcji gracza i przeciwnika.
            self.combat_task = None
            self.combat_player_interval = 1.35
            self.combat_enemy_interval = 1.85
            # v0.8.36: w trybie concise ostrzegamy tylko przy przekraczaniu
            # ważnych progów HP, zamiast czytać każde zwykłe trafienie.
            self.combat_hp_warn_level = 0
            self.last_profession_action = 0.0
            # v0.30.7: warunki zbierania (w tym pogoda/pora) są ogłaszane
            # tylko przy zmianie. Auto-zbieranie nie spamuje NVDA tym samym
            # komunikatem po każdym cyklu profesji.
            self.last_gather_feature_signature = None
            self.auto_fishing = False
            self.auto_fishing_task = None
            self.auto_mining = False
            self.auto_mining_task = None
            self.auto_woodcutting = False
            self.auto_woodcutting_task = None
            self.auto_herbalism = False
            self.auto_herbalism_task = None
            self.guiding = False
            self.guide_choice_state = None
            # v0.23.0: numerowany wybór przy niejednoznacznej sprzedaży pojedynczego EQ/przedmiotu.
            self.sell_choice_state = None
            # v0.8.57: prowadzenie jest osobnym zadaniem asyncio. Dzięki temu
            # gracz może odpytać status, zaplanować trasę lub przerwać marsz
            # bez czekania na zakończenie całej automatycznej podróży.
            self.guide_task = None
            self.guide_target_room = None
            self.guide_target_label = ""
            self.guide_target_is_npc = False
            self.guide_final_direction = None
            self.route_target_room = None
            self.route_target_label = ""
            self.route_target_is_npc = False
            # v0.8.56: normalny ruch ma zauważalny etap chodzenia.
            self.moving = False
            # v0.8.32: ostatnia numerowana lista questów: aktywne, ukończone lub NPC.
            # Dzięki temu quest info <numer> działa po każdej z tych list.
            self.quest_list_context = None
            self.skill_cooldowns = {}
            self.skill_guard = 0
            self.skill_evade = False
            # v0.8.64: wszystkie gwarantowane uniki dzielą krótki lockout po
            # zużyciu, żeby Łotrzyk/Łowca nie rotowali kilku evade w nietykalność.
            self.skill_evade_lockout_until = 0.0
            # v0.8.45: każdy skill typu boost jest czasowym, uniwersalnym buffem.
            # Aktywne buffy wzmacniają wszystkie skille i spelle o mierzalnej sile
            # (obrażenia, leczenie i guard), także przy multiclassie.
            self.active_skill_buffs = {}
            self._party_auto_heal_busy = False
            # v0.37.1: po śmierci w lokalnej drużynie postać może przez chwilę
            # pozostać powalona w pokoju i zostać wskrzeszona przez członka party.
            self.party_downed_until_v0371 = 0.0
            self.party_downed_task_v0371 = None
            self.party_downed_killer_v0371 = ""
            self.party_downed_room_v0371 = None
            # v0.8.26: automatyczna rotacja dwóch kolejek skilli.
            # Konfiguracja kolejki jest trwała w SQLite, a kursory rotacji są sesyjne.
            self.skill_queue_cursors = {"physical": 0, "magic": 0}
            self.skill_queue_next_type = "physical"
            self.auto_queue_casting = False
            self.resting = False
            self.rest_task = None
            # Ostatnia zwykła lokacja do komendy cofnij/back.
            self.previous_room_id = None
            # v0.9.28: ostatni nadawca prywatnej wiadomości dla reply/odpisz.
            self.last_private_sender_account_id = None
            self.last_private_sender_name = None
            # v0.30.11: sesyjne bufory historii przyjazne NVDA.
            self.history_sequence = 0
            self.history_buffers = {
                key: deque(maxlen=HISTORY_BUFFER_LIMIT)
                for key in ("xp", "loot", "quest", "system", "chat", "party", "tell", "combat")
            }
            self.history_replaying = False

    def skill_cooldown_ready_at_v0364(self, skill_or_id):
            skill_id = skill_or_id.get("id") if isinstance(skill_or_id, dict) else skill_or_id
            return float(self.skill_cooldowns.get(str(skill_id), 0.0) or 0.0)

    def skill_cooldown_remaining_v0364(self, skill_or_id, now=None):
            now = time.time() if now is None else float(now)
            return max(0.0, self.skill_cooldown_ready_at_v0364(skill_or_id) - now)

    def skill_cooldown_active_v0364(self, skill_or_id, now=None):
            return self.skill_cooldown_remaining_v0364(skill_or_id, now) > 0.0

    def start_skill_cooldown_v0364(self, skill_or_id, seconds, now=None):
            skill_id = skill_or_id.get("id") if isinstance(skill_or_id, dict) else skill_or_id
            skill_id = str(skill_id)
            now = time.time() if now is None else float(now)
            # Modyfikujemy tylko jeden wpis. Inne skille/spelle zachowują swoje
            # własne timery bez resetu, przedłużenia ani blokady kategorii.
            ready_at = now + max(0.0, float(seconds or 0.0))
            self.skill_cooldowns[skill_id] = ready_at
            return ready_at

    def double_xp_state(self, now=None):
            return double_xp_event_state(now)

    def apply_double_xp(self, amount, now=None):
            amount = max(0, int(amount or 0))
            state = self.double_xp_state(now)
            return min(V019_SAFE_INT, amount * int(state["multiplier"]))

    def add_character_xp_with_event(self, amount):
            actual = self.apply_double_xp(amount)
            self.session_summary_add("character_xp", actual)
            return self.character.add_character_xp(actual)

    async def show_double_xp_event(self):
            state = self.double_xp_state()
            if state["active"]:
                await self.send(
                    "EVENT x2 EXP AKTYWNY. Pozostało "
                    + self.format_duration_short(state["remaining_seconds"])
                    + ". Wszystkie główne rodzaje EXP są podwajane."
                )
            else:
                await self.send(
                    "EVENT x2 EXP: następny start za "
                    + self.format_duration_short(state["next_start_seconds"])
                    + ". Event trwa 15 minut i uruchamia się na początku każdej godziny."
                )

    async def handle_wimpy(self, raw=""):
            value = self.normalize_description_query(str(raw or "").strip())
            current = self.server.db.wimpy_percent(self.account_id)
            if not value or value in ("status", "show", "pokaz", "pokaż"):
                if current <= 0:
                    await self.send("WIMPY jest wyłączone. Użycie: wimpy set 50.")
                else:
                    await self.send(
                        f"WIMPY: {current} procent. Automatyczna ucieczka uruchamia się, "
                        f"gdy HP spadnie do {current} procent lub niżej."
                    )
                return
            for prefix in ("set ", "ustaw "):
                if value.startswith(prefix):
                    value = value[len(prefix):].strip()
                    break
            if value in ("off", "wylacz", "wyłącz", "disable", "0"):
                self.server.db.set_wimpy_percent(self.account_id, 0)
                await self.send("WIMPY wyłączone.")
                return
            try:
                percent = int(value)
            except (TypeError, ValueError):
                await self.send("Użycie: wimpy set <1-99>, wimpy off albo wimpy status.")
                return
            if percent < 1 or percent > 99:
                await self.send("WIMPY musi mieć wartość od 1 do 99 procent. 0 lub off wyłącza system.")
                return
            self.server.db.set_wimpy_percent(self.account_id, percent)
            await self.send(
                f"WIMPY ustawione na {percent} procent. Automatycznie uciekniesz, "
                f"gdy HP spadnie do {percent} procent lub niżej."
            )

    async def maybe_auto_wimpy(self):
            if not self.combat_mob_key or self.current_hp <= 0:
                return False
            percent = self.server.db.wimpy_percent(self.account_id)
            if percent <= 0:
                return False
            hp_percent = (max(0, self.current_hp) * 100.0) / max(1, self.max_hp())
            if hp_percent > percent:
                return False
            await self.send(
                f"WIMPY: HP spadło do {int(round(hp_percent))} procent. Automatyczna ucieczka."
            )
            await self.flee()
            return True

    async def _teleport_self_to_temple_v0354(self, party_trigger_name=None):
            """Teleport one online session to the temple without recursing through party logic."""
            if not self.character or self.closed:
                return False
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
            if self.resting or self.rest_task:
                await self.stop_rest(announce=False)
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
            if self.combat_mob_key:
                await self.flee()
            old_room = self.character.room_id
            if old_room == "temple":
                if party_trigger_name and party_trigger_name != self.character.name:
                    await self.send(
                        f"{party_trigger_name} uruchamia teleport drużyny. Już jesteś w Świątyni Odrodzenia."
                    )
                return False
            self.previous_room_id = old_room
            self.character.room_id = "temple"
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                old_room, f"{self.character.name} znika w świetle Świątyni.", exclude=self
            )
            await self.server.broadcast_room(
                "temple", f"{self.character.name} pojawia się w Świątyni Odrodzenia.", exclude=self
            )
            if party_trigger_name and party_trigger_name != self.character.name:
                await self.send(
                    f"{party_trigger_name} uruchamia teleport drużyny. Zostajesz przeniesiony do Świątyni Odrodzenia."
                )
            else:
                await self.send("Teleportujesz się do Świątyni Odrodzenia.")
            await self.look()
            return True

    async def teleport_to_temple_command(self):
            if not self.character:
                return
            origin_room = self.character.room_id
            party_members = self.server.party_sessions(
                self.account_id, same_room=origin_room
            )
            if not party_members:
                party_members = [self]
            party_members = sorted(
                [s for s in party_members if s.character and not s.closed],
                key=lambda s: s.character.name.casefold(),
            )
            if len(party_members) <= 1:
                moved = await self._teleport_self_to_temple_v0354()
                if not moved and self.character.room_id == "temple":
                    await self.send("Już jesteś w Świątyni Odrodzenia.")
                return

            trigger_name = self.character.name
            moved_count = 0
            for member in party_members:
                if await member._teleport_self_to_temple_v0354(
                    party_trigger_name=trigger_name
                ):
                    moved_count += 1
            await self.server.party_broadcast(
                self.account_id,
                f"Teleport do Świątyni zakończony dla członków drużyny stojących razem. Przeniesiono {moved_count} z {len(party_members)} obecnych w tej lokacji.",
            )
