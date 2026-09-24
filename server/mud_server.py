# -*- coding: utf-8 -*-
from core.runtime_diagnostics import build_runtime_error_report, log_runtime_error
from events.bootstrap import build_default_event_bus

class MudServer:
    def __init__(self):
        self.db = Database(DB_PATH)
        # v0.42.0: one central event bus decouples combat/gathering producers
        # from quest, bounty, chronicle and progression consumers.
        self.events = build_default_event_bus(self)
        self.crafting_quality_restored_v0332 = 0
        for _item_id in self.db.persisted_crafting_quality_item_ids_v0332():
            if ensure_crafting_quality_variant_v0332(_item_id):
                self.crafting_quality_restored_v0332 += 1
        self.mine_startup_reset = self.db.reset_mine_for_server_start()
        self.world = World()
        self.sessions = set()
        self.parties = {}
        self.party_invites = {}
        # leader_account_id -> protector_account_id. Stan sesyjny; bez migracji DB.
        self.party_protectors = {}
        # v0.61.0: koordynacja drużyny jest stanem sesyjnym tak samo jak sama
        # drużyna. Cel trwa do zmiany/wyczyszczenia i przechodzi na nowego
        # lidera; ready-check przechowuje konta, które potwierdziły gotowość.
        self.party_goals = {}
        self.party_ready_checks = {}

    def report_runtime_error(self, exc, *, command=None, handler=None):
        report = build_runtime_error_report(
            exc, root=globals().get("_ROOT"), command=command, handler=handler
        )
        log_runtime_error(report)
        return report

    def account_online(self, account_id):
        return self.session_by_master_account(account_id) is not None

    def session_by_master_account(self, account_id, exclude=None):
        for session in list(self.sessions):
            if session is exclude or session.closed:
                continue
            if getattr(session, "master_account_id", None) == int(account_id):
                return session
        return None

    def find_character_session(self, name):
        for s in self.sessions:
            if s.closed or not s.character:
                continue
            if s.character.name.lower() == str(name or "").lower():
                return s
        return None

    def session_by_account(self, account_id):
        for session in self.sessions:
            if session.account_id == account_id and session.character:
                return session
        return None

    def party_key_for_account(self, account_id):
        for leader_id, members in self.parties.items():
            if account_id in members:
                return leader_id
        return None

    def same_party(self, account_a, account_b):
        key_a = self.party_key_for_account(account_a)
        key_b = self.party_key_for_account(account_b)
        return key_a is not None and key_a == key_b

    def clear_party_protector_for_account(self, account_id):
        removed = False
        for leader_id, protector_id in list(self.party_protectors.items()):
            if protector_id == account_id:
                self.party_protectors.pop(leader_id, None)
                removed = True
        return removed

    def party_protector_session(self, account_id, same_room=None):
        key = self.party_key_for_account(account_id)
        if key is None:
            return None
        protector_id = self.party_protectors.get(key)
        if protector_id is None:
            return None
        if protector_id not in self.parties.get(key, set()):
            self.party_protectors.pop(key, None)
            return None
        protector = self.session_by_account(protector_id)
        if (
            not protector
            or not protector.character
            or protector.closed
            or protector.current_hp <= 0
            or not protector.character.has_active_class("Strażnik")
        ):
            self.party_protectors.pop(key, None)
            return None
        if (
            same_room is not None
            and protector.character.room_id != same_room
        ):
            return None
        return protector

    async def apply_party_protection(self, attacker, mob):
        """Przekieruj jeden wspólny cel drużyny na aktywnego tanka Strażnika."""
        if not attacker or not attacker.character or not mob or not mob.alive:
            return None
        protector = self.party_protector_session(
            attacker.account_id, same_room=mob.room_id
        )
        if protector is None:
            return None

        # Jedna sesja Strażnika może prowadzić jeden pełny realtime target naraz.
        if protector.combat_mob_key and protector.combat_mob_key != mob.key:
            current = self.world.mobs.get(protector.combat_mob_key)
            if current and current.alive and current.room_id == protector.character.room_id:
                return None
            protector.combat_mob_key = None

        if not self.engagement_allowed(protector, mob):
            return None

        joined = protector.combat_mob_key != mob.key
        old_aggro = mob.engaged_by
        protector.combat_mob_key = mob.key
        if mob.engaged_at <= 0:
            mob.engaged_at = time.monotonic()
        mob.engaged_by = protector.character.name
        if joined:
            protector.combat_hp_warn_level = 0
            await protector.send(
                f"Zasłaniasz drużynę przed {MOB_TEMPLATES[mob.template_id]['name']} i przejmujesz aggro."
            )
        if old_aggro != protector.character.name:
            await self.party_broadcast(
                attacker.account_id,
                f"{protector.character.name} przejmuje aggro {MOB_TEMPLATES[mob.template_id]['name']} i osłania drużynę.",
                exclude=protector,
            )
        await protector.ensure_realtime_combat()
        return protector

    def party_sessions(self, account_id, same_room=None):
        key = self.party_key_for_account(account_id)
        if key is None:
            session = self.session_by_account(account_id)
            if (
                session
                and (
                    same_room is None
                    or session.character.room_id == same_room
                )
            ):
                return [session]
            return []

        result = []
        for member_id in self.parties.get(key, set()):
            session = self.session_by_account(member_id)
            if not session:
                continue
            if (
                same_room is not None
                and session.character.room_id != same_room
            ):
                continue
            result.append(session)
        return result

    def party_combat_target(self, owner_session, mob):
        if not owner_session or not mob or not mob.alive:
            return owner_session
        protector = self.party_protector_session(
            owner_session.account_id, same_room=mob.room_id
        )
        if protector and protector.current_hp > 0:
            return protector
        candidates = [
            session for session in self.party_sessions(
                owner_session.account_id, same_room=mob.room_id
            )
            if session.character and not session.closed and session.current_hp > 0
            and session.combat_mob_key == mob.key
        ]
        if not candidates:
            return owner_session
        candidates.sort(key=lambda session: session.character.name.lower())
        return candidates[int(getattr(mob, "combat_turn", 0) or 0) % len(candidates)]

    async def auto_priest_party_heal(self, damaged_session):
        if (
            not damaged_session or damaged_session.closed or not damaged_session.character
            or damaged_session.current_hp <= 0
            or self.party_key_for_account(damaged_session.account_id) is None
        ):
            return False
        room_id = damaged_session.character.room_id
        members = [
            session for session in self.party_sessions(
                damaged_session.account_id, same_room=room_id
            )
            if session.character and not session.closed and session.current_hp > 0
        ]
        injured = [
            session for session in members
            if session.current_hp / max(1, session.max_hp()) < PARTY_AUTO_HEAL_THRESHOLD
        ]
        if not injured:
            return False
        options = []
        for healer in members:
            option = healer.auto_priest_heal_option(injured)
            if option:
                options.append((int(option.get("score", 0)), healer.character.name.lower(), healer, option))
        if not options:
            return False
        options.sort(key=lambda row: (-row[0], row[1]))
        _score, _name, healer, option = options[0]
        return await healer.perform_auto_priest_heal(option, injured)

    async def party_broadcast(self, account_id, message, exclude=None, history_category=None):
        for session in self.party_sessions(account_id):
            if session is not exclude:
                await session.send(message, history_category=history_category)

    async def party_nearby_broadcast(self, actor, message, exclude=None, detail=None, history_category=None):
        """Send a party gameplay event only to online party members in actor's room.

        Administrative party state messages continue to use party_broadcast.
        This helper is for nearby gameplay feed: combat, healing, loot and other
        events that should never travel across the map.
        """
        if (
            actor is None
            or actor.closed
            or not actor.character
            or actor.account_id is None
            or self.party_key_for_account(actor.account_id) is None
        ):
            return 0
        excluded = set(exclude or [])
        sent = 0
        room_id = actor.character.room_id
        for session in self.party_sessions(actor.account_id, same_room=room_id):
            if session in excluded or session.closed or not session.character:
                continue
            kwargs = {}
            if detail is not None:
                kwargs["combat_detail"] = detail
            if history_category is not None:
                kwargs["history_category"] = history_category
            await session.send(str(message), **kwargs)
            sent += 1
        return sent

    async def party_combat_broadcast(self, actor, message, detail="normal"):
        """NVDA-friendly combat feed for other party members in the same room."""
        return await self.party_nearby_broadcast(
            actor, message, exclude=[actor], detail=detail, history_category="combat"
        )

    async def auto_assist_party_combat(self, initiator, mob):
        """Automatycznie dołącza wolnych członków drużyny z tej samej lokacji."""
        if not initiator or not initiator.character or not mob or not mob.alive:
            return []
        key = self.party_key_for_account(initiator.account_id)
        if key is None:
            return []

        joined = []
        for session in self.party_sessions(
            initiator.account_id, same_room=mob.room_id
        ):
            if session is initiator or not session.character or session.closed:
                continue
            if session.current_hp <= 0:
                continue

            # Nie przełączaj osoby, która świadomie walczy już z innym żywym celem.
            if session.combat_mob_key and session.combat_mob_key != mob.key:
                current = self.world.mobs.get(session.combat_mob_key)
                if current and current.alive and current.room_id == mob.room_id:
                    continue
                session.combat_mob_key = None

            if session.combat_mob_key == mob.key:
                continue
            if not self.engagement_allowed(session, mob):
                continue

            # Walka drużyny ma pierwszeństwo przed automatyczną pracą profesji.
            if session.auto_fishing or session.auto_fishing_task:
                await session.stop_auto_fishing(announce=False)
            if session.auto_mining or session.auto_mining_task:
                await session.stop_auto_mining(announce=False)
            if session.auto_woodcutting or session.auto_woodcutting_task:
                await session.stop_auto_woodcutting(announce=False)
            if session.auto_herbalism or session.auto_herbalism_task:
                await session.stop_auto_herbalism(announce=False)

            session.combat_mob_key = mob.key
            session.combat_hp_warn_level = 0
            joined.append(session)
            await session.send(
                f"Automatycznie wspierasz drużynę przeciw "
                f"{MOB_TEMPLATES[mob.template_id]['name']}."
            )
            await session.ensure_realtime_combat()
        return joined

    def sanitize_mob_engagement(self, mob):
        """Usuń zombie-aggro, jeśli deklarowany właściciel już realnie nie walczy."""
        if not mob or not mob.alive or not mob.engaged_by:
            return None

        owner = self.find_character_session(mob.engaged_by)
        if (
            owner
            and owner.character
            and owner.current_hp > 0
            and owner.character.room_id == mob.room_id
            and owner.combat_mob_key == mob.key
        ):
            return owner

        # Jeśli stary właściciel zniknął, ale ktoś naprawdę nadal walczy z tym
        # mobem w tym samym pokoju, przekaż aggro aktywnemu uczestnikowi.
        candidates = [
            s for s in self.sessions
            if (
                not s.closed
                and s.character
                and s.current_hp > 0
                and s.character.room_id == mob.room_id
                and s.combat_mob_key == mob.key
            )
        ]
        if candidates:
            replacement = sorted(
                candidates, key=lambda s: s.character.name.lower()
            )[0]
            mob.engaged_by = replacement.character.name
            return replacement

        # Nikt realnie nie walczy: stan aggro był osierocony.
        mob.engaged_by = None
        mob.engaged_at = 0.0
        mob.combat_turn = 0
        mob.player_hits = 0
        return None

    def release_all_engagements_for_session(self, leaving_session):
        """Zwolnij wszystkie moby trzymane przez postać, nie tylko combat_mob_key."""
        if not leaving_session or not leaving_session.character:
            return 0
        released = 0
        name = leaving_session.character.name
        for mob in self.world.mobs.values():
            if not mob.alive or mob.engaged_by != name:
                continue
            self.reassign_mob_engagement(mob, leaving_session)
            if mob.engaged_by == name:
                mob.engaged_by = None
                mob.engaged_at = 0.0
                mob.combat_turn = 0
                mob.player_hits = 0
            released += 1
        return released

    def engagement_allowed(self, session, mob):
        if not mob or not mob.alive:
            return False
        self.sanitize_mob_engagement(mob)
        if not mob.engaged_by or mob.engaged_by == session.character.name:
            return True
        owner = self.find_character_session(mob.engaged_by)
        return bool(
            owner
            and self.same_party(session.account_id, owner.account_id)
        )

    def reassign_mob_engagement(self, mob, leaving_session):
        if not mob or not mob.alive:
            return
        if mob.engaged_by != leaving_session.character.name:
            return
        candidates = [
            session
            for session in self.party_sessions(
                leaving_session.account_id, same_room=mob.room_id
            )
            if (
                session is not leaving_session
                and session.combat_mob_key == mob.key
            )
        ]
        mob.engaged_by = (
            candidates[0].character.name if candidates else None
        )

    async def broadcast_room(self, room_id, text, exclude=None, history_category=None):
        for s in list(self.sessions):
            if s is not exclude and s.character and s.character.room_id == room_id:
                await s.send(text, history_category=history_category)

    async def broadcast_all(self, text, history_category=None):
        for session in list(self.sessions):
            if session.character and not session.closed:
                await session.send(text, history_category=history_category)

    async def double_xp_event_loop(self):
        last_active = double_xp_event_state()["active"]
        while True:
            await asyncio.sleep(5.0)
            try:
                state = double_xp_event_state()
                active = bool(state["active"])
                if active == last_active:
                    continue
                last_active = active
                if active:
                    await self.broadcast_all(
                        "EVENT x2 EXP START. Przez 15 minut wszystkie główne rodzaje EXP są podwajane.",
                        history_category="system",
                    )
                else:
                    await self.broadcast_all(
                        "EVENT x2 EXP ZAKOŃCZONY. Następny start na początku kolejnej godziny.",
                        history_category="system",
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(
                    f"[DOUBLE XP LOOP ERROR] {type(exc).__name__}: {exc}",
                    file=sys.stderr, flush=True,
                )

    async def mob_wander_loop(self):
        while True:
            await asyncio.sleep(5.0)
            try:
                for mob, old_room, new_room in self.world.wander_step():
                    name = MOB_TEMPLATES.get(mob.template_id, {}).get(
                        "name", "Wróg"
                    )
                    await self.broadcast_room(
                        old_room, f"{name} odchodzi do sąsiedniej lokacji."
                    )
                    await self.broadcast_room(
                        new_room, f"{name} nadchodzi z sąsiedniej lokacji."
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(
                    f"[MOB WANDER LOOP ERROR] {type(exc).__name__}: {exc}",
                    file=sys.stderr, flush=True,
                )

    async def handle_client(self, reader, writer):
        if len(self.sessions) >= MAX_CLIENTS:
            writer.write(
                telnet_charset_offer_bytes()
                + "Serwer jest pełny.\r\n".encode(
                    DEFAULT_TEXT_ENCODING
                )
            )
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        session = Session(self, reader, writer)
        self.sessions.add(session)
        try:
            if await session.login_flow():
                await session.enter_world()
                while not session.closed:
                    try:
                        await session.command_loop()
                        break
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        report = self.report_runtime_error(
                            exc,
                            command=getattr(session, "_last_command_for_diagnostics", ""),
                            handler="command_loop",
                        )
                        try:
                            await session.send(
                                f"Wystąpił błąd komendy [{report['error_id']}]. "
                                "Możesz dalej grać; identyfikator błędu zapisano w logu serwera."
                            )
                        except Exception:
                            break
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            report = self.report_runtime_error(exc, handler="session/login")
            try:
                await session.send(
                    f"Wystąpił błąd sesji [{report['error_id']}]. Połączenie zostanie zamknięte."
                )
            except Exception:
                pass
        finally:
            await session.close()
            self.sessions.discard(session)

    async def run(self):
        boot_socket = globals().get("_BOOT_SOCKET")
        if boot_socket is not None:
            server = await asyncio.start_server(self.handle_client, sock=boot_socket)
            globals()["_BOOT_SOCKET"] = None
        else:
            server = await asyncio.start_server(self.handle_client, HOST, PORT)
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        print(f"Soulbound v{VERSION} World Core nasłuchuje: {addresses}", flush=True)
        print(f"HOST={HOST}", flush=True)
        print(f"PORT={PORT} (source={PORT_SOURCE})", flush=True)
        print(
            "Railway TCP application port="
            + (os.getenv("RAILWAY_TCP_APPLICATION_PORT") or "brak"),
            flush=True,
        )
        print(f"Baza danych: {DB_PATH}", flush=True)
        print(f"Lokacje: {len(ROOMS)}", flush=True)
        print(f"Limit klientów: {MAX_CLIENTS}", flush=True)
        wander_task = asyncio.create_task(self.mob_wander_loop())
        xp_event_task = asyncio.create_task(self.double_xp_event_loop())
        try:
            async with server:
                await server.serve_forever()
        finally:
            for task in (wander_task, xp_event_task):
                task.cancel()
            for task in (wander_task, xp_event_task):
                try:
                    await task
                except asyncio.CancelledError:
                    pass
