# -*- coding: utf-8 -*-
from core.runtime_diagnostics import build_runtime_error_report, log_runtime_error
from events.bootstrap import build_default_event_bus
import time
import sqlite3
import asyncio
import os
import sys
from pathlib import Path  # canonical current dependency
from core.bootstrap_economy_professions import (
    DB_PATH, HOST, MAX_CLIENTS, PARTY_AUTO_HEAL_THRESHOLD, PORT, PORT_SOURCE,
    VERSION, double_xp_event_state,
)
from core.runtime_transport import take_boot_socket
from data.items import ITEMS  # canonical current dependency
from data.mobs import MOB_TEMPLATES  # canonical current dependency
from data.rooms import ROOMS  # canonical current dependency
from network.protocol_gameplay_utils import DEFAULT_TEXT_ENCODING, telnet_charset_offer_bytes
from player.session import Session
from storage.database import Database
from systems.crafting_quality import ensure_crafting_quality_variant_v0332
from world.world_state import World
from systems.infinite_equipment import ensure_infinite_equipment_variant
from systems.mob_recovery_v1405 import (
    preserve_hp_when_encounter_ends_v1405,
    restore_idle_hp_tick_v1405,
)

from core.performance_v2002 import measure_async

from server_parts_v109 import (MudSessionsV109Mixin, MudPartyMembersV109Mixin, MudEngagementV109Mixin)

class MudServer(MudSessionsV109Mixin, MudPartyMembersV109Mixin, MudEngagementV109Mixin):
    def __init__(self):
        # The current release owns startup authorization. Historical releases
        # and their markers/flags are never consulted by this server.
        from core.bootstrap_economy_professions import DB_PATH  # explicit current dependency
        from data.items import ITEMS  # canonical current dependency
        import time  # canonical current dependency
        from storage.database import Database  # explicit current dependency
        from systems.crafting_quality import ensure_crafting_quality_variant_v0332  # explicit current dependency
        from systems.infinite_equipment import ensure_infinite_equipment_variant  # explicit current dependency
        from world.world_state import World  # explicit current dependency
        from systems.runtime_activation import authorized_mode
        _runtime_mode = authorized_mode(DB_PATH)
        self.start_time_v1224 = time.time()
        self.db = Database(DB_PATH)
        # v116.00.64: set before any session, scheduled reward or login gift.
        self.db._uncapped_awards_v11664 = True
        self.db._rebalanced_awards_v11664 = True
        self.db._manual_bank_only_v11325 = True
        self.db._retired_mercenaries_v11664 = True
        self.db._retired_player_minions_v11665 = True
        self.db._class_schools_v11664 = True
        # Clock-driven live events remain disabled in isolated staging.
        if _runtime_mode == 'production':
            self.db._v108_live_event_caps = True
        # v71: restore conservative character-creator profiles in place.
        from systems.published_heritage_v7100 import restore as _restore_heritage_v7100
        _restore_heritage_v7100()
        from systems.published_races_v7600 import restore as _restore_custom_races
        _restore_custom_races()
        from systems.published_classes_v7700 import restore as _restore_custom_classes
        _restore_custom_classes()
        # v0.42.0: one central event bus decouples combat/gathering producers
        # from quest, bounty, chronicle and progression consumers.
        self.events = build_default_event_bus(self)
        self.crafting_quality_restored_v0332 = 0
        for _item_id in self.db.persisted_crafting_quality_item_ids_v0332():
            if ensure_crafting_quality_variant_v0332(_item_id):
                self.crafting_quality_restored_v0332 += 1
        self.infinite_equipment_restored_v11330 = 0
        for _item_id in self.db.persisted_infinite_equipment_item_ids_v11330():
            if ensure_infinite_equipment_variant(_item_id):
                self.infinite_equipment_restored_v11330 += 1
        # v107 EQ: load/verify physical instances only AFTER all persisted
        # dynamic equipment templates have been restored. Always before any
        # TCP client or World() can read or change a player's equipment.
        if _runtime_mode == 'production':
            # Existing player databases must already have a validated physical
            # ledger. Removing historical release authorization must not turn
            # startup into an implicit conversion of player equipment.
            existing = self.db.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' "
                "AND name='v107_eq_production_cutover'").fetchone()
            if not existing:
                raise PermissionError('EQ: brak zatwierdzonego rejestru fizycznych kopii; wymagana jawna inicjalizacja')
            from systems.v10700_live_equipment import activate_production_ledger
            activate_production_ledger(self.db, ITEMS)
        # v1.25.0: deploy/restart must NOT collapse the mine or teleport miners.
        self.mine_startup_state = self.db.mine_startup_status()
        # v12.00.4: restore additive live rooms/mobs/exits BEFORE World() spawns.
        from systems.published_world_content import PublishedWorldContent
        self.published_world_content = PublishedWorldContent(self.db)
        self.world = World()
        self.sessions = set()
        # v116.00.45: notification, not a periodic polling task. Only a real
        # player who has entered the world wakes autonomous monster movement.
        self._players_present_v11645 = asyncio.Event()
        self.parties = {}
        self.party_invites = {}
        # leader_account_id -> protector_account_id. Stan sesyjny; bez migracji DB.
        self.party_protectors = {}
        # v0.61.0: koordynacja drużyny jest stanem sesyjnym tak samo jak sama
        # drużyna. Cel trwa do zmiany/wyczyszczenia i przechodzi na nowego
        # lidera; ready-check przechowuje konta, które potwierdziły gotowość.
        self.party_goals = {}
        self.party_ready_checks = {}
        # v1.19.3: route goals are session-only and never grant travel permissions.
        self.party_routes_v1193 = {}

    def report_runtime_error(self, exc, *, command=None, handler=None):
        import sqlite3  # canonical current dependency
        report = build_runtime_error_report(
            exc, root=Path(__file__).resolve().parents[1], command=command, handler=handler
        )
        log_runtime_error(report)
        try:
            self.db.record_admin_error_v1224(report)
        except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
            print(f"[ADMIN DIAGNOSTICS] Cannot store error id: {type(exc).__name__}", flush=True)
        return report









    async def apply_party_protection(self, attacker, mob):
        """Przekieruj jeden wspólny cel drużyny na aktywnego tanka Strażnika."""
        from data.mobs import MOB_TEMPLATES  # canonical current dependency
        import time  # canonical current dependency
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





    async def auto_priest_party_heal(self, damaged_session):
        from core.bootstrap_economy_professions import PARTY_AUTO_HEAL_THRESHOLD  # explicit current dependency
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
        import asyncio  # canonical current dependency
        if (
            actor is None
            or actor.closed
            or not actor.character
            or actor.account_id is None
            or self.party_key_for_account(actor.account_id) is None
        ):
            return 0
        excluded = set(exclude or [])
        room_id = actor.character.room_id
        recipients = [session for session in self.party_sessions(actor.account_id, same_room=room_id)
                      if session not in excluded and not session.closed and session.character]
        if not recipients:
            return 0
        kwargs = {}
        if detail is not None:
            kwargs["combat_detail"] = detail
        if history_category is not None:
            kwargs["history_category"] = history_category
        # Each recipient keeps their complete NVDA message/history. A slow
        # client's writer.drain must not block everyone else's outgoing text.
        await asyncio.gather(*(session.send(str(message), **kwargs) for session in recipients))
        return len(recipients)

    @measure_async("party.combat_broadcast", report_every=100)
    async def party_combat_broadcast(self, actor, message, detail="normal"):
        """NVDA-friendly combat feed for other party members in the same room.

        The original, hash-protected combat engine signals Jammer expiration
        on the mob's final skipped action. Promote *that one transition* into
        an essential notice for the fighting player and nearby party members.
        Regular skipped turns keep their existing combat-log verbosity.
        """
        jammer_end_suffix = (
            " jest zatrzymany przez Jammer i pomija akcję. Stop się kończy."
        )
        if isinstance(message, str) and message.endswith(jammer_end_suffix):
            mob_name = message[:-len(jammer_end_suffix)]
            if mob_name and actor is not None and not actor.closed and actor.character:
                notice = f"Jammer na {mob_name} zakończył działanie."
                # The regular party broadcast deliberately excludes the actor;
                # an expiration must be audible to the actor even when solo.
                await actor.send_combat(notice, "essential")
                return await self.party_nearby_broadcast(
                    actor, notice, exclude=[actor], detail="essential",
                    history_category="combat",
                )
        return await self.party_nearby_broadcast(
            actor, message, exclude=[actor], detail=detail, history_category="combat"
        )

    async def auto_assist_party_combat(self, initiator, mob):
        """Automatycznie dołącza całą żywą drużynę z tej samej lokacji."""
        from data.mobs import MOB_TEMPLATES  # canonical current dependency
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

            # v1.11.10: wspólna walka party ma pierwszeństwo przed indywidualnym
            # targetem. Każdy żywy członek w pokoju przechodzi na cel, który właśnie
            # rozpoczął wspólną walkę — także jeśli wcześniej bił innego moba.
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

    def reset_adaptive_mob_encounter_v11330(self, mob):
        """Restore template-local stats when an encounter fully ends without a kill."""
        from data.mobs import MOB_TEMPLATES  # canonical current dependency
        if not mob:
            return
        template = MOB_TEMPLATES.get(mob.template_id, {})
        if mob.alive and isinstance(template, dict):
            # Flee/disconnect must not instantly refill a wounded boss. Convert
            # its adaptive HP proportion back to the template maximum instead.
            _base_hp_v1405 = max(1, int(template.get("max_hp", 1) or 1))
            _old_hp_v1405 = max(
                _base_hp_v1405,
                int(getattr(mob, "adaptive_max_hp_v11330", 0) or 0),
            )
            mob.hp = preserve_hp_when_encounter_ends_v1405(
                mob.hp, _old_hp_v1405, _base_hp_v1405,
            )
        mob.adaptive_max_hp_v11330 = 0
        mob.adaptive_hp_multiplier_v11330 = 1.0
        mob.adaptive_reward_multiplier_v11330 = 1.0
        mob.adaptive_party_size_v11330 = 1
        mob.adaptive_party_dps_v11330 = 0.0
        mob.adaptive_rank_v11330 = ""






    async def broadcast_room(self, room_id, text, exclude=None, history_category=None):
        import asyncio  # canonical current dependency
        targets = [s for s in tuple(self.sessions)
                   if s is not exclude and not s.closed and s.character
                   and s.character.room_id == room_id]
        if targets:
            await asyncio.gather(*(s.send(text, history_category=history_category) for s in targets))

    async def broadcast_all(self, text, history_category=None, *, exclude=None):
        # Pozwala pominąć nadawcę ogłoszenia (np. postać podczas wylogowania).
        import asyncio  # canonical current dependency
        targets = [s for s in tuple(self.sessions)
                   if s is not exclude and s.character and not s.closed]
        if targets:
            await asyncio.gather(*(s.send(text, history_category=history_category) for s in targets))

    async def double_xp_event_loop(self):
        from core.bootstrap_economy_professions import double_xp_event_state
        import asyncio  # canonical current dependency
        import time  # canonical current dependency
        from systems.v10800_seasonal_events import overcap_event_state
        last_active_overcap_v108 = overcap_event_state()['active']
        last_active = double_xp_event_state()["active"]
        last_world_slot_v12812 = None
        while True:
            await asyncio.sleep(5.0)
            try:
                state = double_xp_event_state()
                # Every 3 hours announce new actual rotating world encounters.
                # No rerolls, NPC spawning or EXP changes in this notifier.
                current_slot_v12812 = int(time.time() // (3 * 3600))
                if current_slot_v12812 != last_world_slot_v12812:
                    last_world_slot_v12812 = current_slot_v12812
                    from world.world_state import v0290_active_world_events
                    from data.rooms import ROOMS as _rooms_v12812  # canonical current dependency
                    from systems.world_events_v12812 import active_city_event_v12812
                    city_event = active_city_event_v12812()
                    self.world.ensure_runtime_room(city_event['room_id'])
                    await self.broadcast_all(
                        f"WYDARZENIE ŚWIATA: {city_event['name']}! Boss: {city_event['boss_name']}. "
                        f"Miejsce: {_rooms_v12812[city_event['room_id']]['name']}. "
                        'Czas wydarzenia: 3 godziny. Prawdziwy boss, wspólny EXP i łupy.',
                        history_category='system')
                    active_events = list(v0290_active_world_events())
                    for event in active_events[:3]:
                        room = _rooms_v12812.get(event.get('room_id'), {})
                        label = str(event.get('title') or event.get('name') or event.get('kind') or 'Starcie')
                        await self.broadcast_all(
                            f'WYDARZENIE ŚWIATA: {label}. Miejsce: {room.get("name",event.get("room_id","nieznane"))}. '
                            'Wydarzenie jest prawdziwą walką; solo i drużyny mogą wziąć udział.',
                            history_category='system')
                # Independent Over Cap schedule, even while double EXP state is stable.
                overcap_now = bool(overcap_event_state()['active'])
                if overcap_now != last_active_overcap_v108:
                    last_active_overcap_v108 = overcap_now
                    await self.broadcast_all(
                        'EVENT OVER CAP START. Przez 15 minut limit nagrody EXP x2; '
                        'sam EXP nie jest podwajany.' if overcap_now else
                        'EVENT OVER CAP ZAKOŃCZONY. Limity EXP wróciły do normy.',
                        history_category='system')
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

    def regenerate_idle_mobs_v1405(self, *, ticks=1):
        """One lightweight HP tick; only mobs without a living opponent heal.

        Reuses the existing 15-second world loop; no task per mob, no DB writes.
        A player in the room still fighting prevents healing, even if aggro is
        temporarily transferred between party members or AoE targets.
        """
        from data.mobs import MOB_TEMPLATES  # canonical current dependency
        active_keys = {
            s.combat_mob_key for s in self.sessions
            if (not s.closed and s.character and s.current_hp > 0
                and getattr(s, "combat_mob_key", None)
                and self.world.mobs.get(s.combat_mob_key) is not None
                and s.character.room_id == self.world.mobs[s.combat_mob_key].room_id)
        }
        restored = 0
        for mob in tuple(self.world.mobs.values()):
            if not mob.alive or int(mob.hp) <= 0:
                continue
            if mob.engaged_by:
                self.sanitize_mob_engagement(mob)
            if mob.engaged_by or getattr(mob, "aoe_engaged_by", None) or mob.key in active_keys:
                continue
            # Recover leftover scaling only after the last fighter disappears.
            if int(getattr(mob, "adaptive_max_hp_v11330", 0) or 0) > 0:
                self.reset_adaptive_mob_encounter_v11330(mob)
            template = MOB_TEMPLATES.get(mob.template_id, {})
            if restore_idle_hp_tick_v1405(mob, template, ticks=ticks):
                restored += 1
        return restored

    def _players_in_world_v11645(self):
        """Only logged-in characters count, not TCP probes or login screens."""
        return any(
            not getattr(session, "closed", False)
            and getattr(session, "character", None) is not None
            for session in self.sessions
        )

    async def mob_wander_loop(self, *, tick_seconds=15.0):
        import asyncio  # canonical current dependency
        from data.mobs import MOB_TEMPLATES  # canonical current dependency
        import time  # canonical current dependency
        while True:
            # v116.00.45: an empty server has no observers of roaming mobs.
            # Wait on a real login signal: no 22k-mob scans, no timed polling,
            # and no changes to other background event/Fame/backup tasks.
            if not self._players_in_world_v11645():
                self._players_present_v11645.clear()
                idle_since = time.monotonic()
                print('[WORLD IDLE] Brak graczy: ruch i AI spacerujacych mobow uspione.', flush=True)
                await self._players_present_v11645.wait()
                if not self._players_in_world_v11645():
                    continue
                # Respawns, loot and corpse expirations use real wall-clock
                # deadlines. Refresh once on wake instead of replaying ticks.
                try:
                    self.world.refresh(force=True)
                    # Healing would otherwise freeze during long empty periods.
                    # Catch up in ONE mob scan (at most ten 10% ticks), without
                    # respawning or fully healing a mob during live combat.
                    missed = min(10, int((time.monotonic() - idle_since) // 15.0))
                    if missed:
                        self.regenerate_idle_mobs_v1405(ticks=missed)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    print(f'[WORLD IDLE WAKE ERROR] {type(exc).__name__}: {exc}',
                          file=sys.stderr, flush=True)
                print('[WORLD ACTIVE] Gracz wszedl do swiata: ruch potworow wznowiony.', flush=True)
            # v1.11.22: ordinary roaming remains on the original 15-second
            # schedule while at least one character is in the world.
            await asyncio.sleep(tick_seconds)
            if not self._players_in_world_v11645():
                continue
            try:
                _tick_started_v0718 = time.perf_counter()
                # v1.40.5: healed idle mobs only; 10% HP each 15-second tick.
                self.regenerate_idle_mobs_v1405()
                _after_regen_v11655 = time.perf_counter()
                _moves_v0718 = self.world.wander_step()
                _after_wander_v11655 = time.perf_counter()
                _tick_elapsed_v0718 = _after_wander_v11655 - _tick_started_v0718
                if _tick_elapsed_v0718 >= 0.45:
                    # Separate the two CPU-heavy phases for the next real log;
                    # no usernames, IPs, movements or session data are stored.
                    print(
                        f"[PERF WORLD PHASE v11655] regen={_after_regen_v11655-_tick_started_v0718:.3f}s; "
                        f"wander={_after_wander_v11655-_after_regen_v11655:.3f}s; "
                        f"mobs={len(self.world.mobs)}", flush=True,
                    )
                if _tick_elapsed_v0718 >= 0.10:
                    print(
                        f"[PERF SLOW WORLD TICK] {_tick_elapsed_v0718:.3f}s; moves={len(_moves_v0718)}; mobs={len(self.world.mobs)}",
                        flush=True,
                    )
                # v116.00.47: a large active world may move thousands of
                # monsters per tick. The old loop awaited two no-op broadcasts
                # for EVERY move, including unoccupied regions. No player can
                # hear those events. Preserve all movement, AI, respawns and
                # observable messages; only skip sends to empty rooms.
                _occupied_rooms_v11647 = {
                    getattr(session.character, 'room_id', None)
                    for session in tuple(self.sessions)
                    if not session.closed and session.character is not None
                }
                for mob, old_room, new_room in _moves_v0718:
                    _has_departure_v11647 = old_room in _occupied_rooms_v11647
                    _has_arrival_v11647 = new_room in _occupied_rooms_v11647
                    if not (_has_departure_v11647 or _has_arrival_v11647):
                        continue
                    name = MOB_TEMPLATES.get(mob.template_id, {}).get('name', 'Wróg')
                    if _has_departure_v11647:
                        await self.broadcast_room(
                            old_room, f"{name} odchodzi do sąsiedniej lokacji."
                        )
                    if _has_arrival_v11647:
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
        from core.bootstrap_economy_professions import MAX_CLIENTS
        import asyncio  # canonical current dependency
        from network.protocol_gameplay_utils import DEFAULT_TEXT_ENCODING, telnet_charset_offer_bytes  # explicit current dependency
        from player.session import Session  # explicit current dependency
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
        # v116.00.64: enable uncapped direct XP for login/enter_world as well.
        # These same methods use the flag in authenticated command_loop.
        self.db._manual_bank_only_v11325 = True
        self.db._uncapped_awards_v11664 = True
        self.db._retired_mercenaries_v11664 = True
        self.db._retired_player_minions_v11665 = True
        self.sessions.add(session)
        try:
            if await session.login_flow():
                await session.enter_world()
                # Wake world movement as soon as the first real character enters.
                self._players_present_v11645.set()
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
            except Exception:  # AUDIT_INTENTIONAL_PASS: broken client connection may prevent final error message
                pass
        finally:
            await session.close()
            self.sessions.discard(session)

    async def performance_watchdog_v11320(self):
        """Observe event-loop starvation without touching gameplay or DB."""
        loop = asyncio.get_running_loop()
        interval = 0.5
        expected = loop.time() + interval
        last_report = -1e12
        while True:
            await asyncio.sleep(interval)
            now = loop.time()
            lag = max(0.0, now - expected)
            expected = now + interval
            if lag >= 0.25 and now - last_report >= 10.0:
                print(f'[PERF LOOP LAG] blokada petli={lag:.3f}s (bez danych graczy)', flush=True)
                last_report = now

    async def run(self):
        from core.bootstrap_economy_professions import DB_PATH, HOST, MAX_CLIENTS, PORT, PORT_SOURCE, VERSION
        import asyncio  # canonical current dependency
        # Windows Proactor cleanup can raise a benign peer-reset callback
        # after a client has already disconnected. Other errors retain the
        # native asyncio traceback; no TCP session or save is suppressed.
        from network.peer_reset_handler_v11668 import install_peer_reset_handler
        install_peer_reset_handler(asyncio.get_running_loop())
        from data.rooms import ROOMS  # canonical current dependency
        boot_socket = take_boot_socket()
        if boot_socket is not None:
            server = await asyncio.start_server(self.handle_client, sock=boot_socket)
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
        # On Windows, our BAT launcher supplies a per-launch secret for a
        # localhost-only stop channel. Linux/Railway uses the previous path.
        from systems.windows_control_v1603 import start_control_v1603
        stop_event = asyncio.Event()
        control = await start_control_v1603(stop_event)
        latency_task = asyncio.create_task(self.performance_watchdog_v11320())
        wander_task = asyncio.create_task(self.mob_wander_loop())
        xp_event_task = asyncio.create_task(self.double_xp_event_loop())
        # v115: only persisted and due Fame rewards, completely audio-optional.
        from systems.v115.fame_online_scheduler import fame_online_scheduler_v115
        fame_v115_task = asyncio.create_task(fame_online_scheduler_v115(self))
        try:
            async with server:
                if control is None:
                    await server.serve_forever()
                else:
                    serve_task = asyncio.create_task(server.serve_forever())
                    stop_task = asyncio.create_task(stop_event.wait())
                    try:
                        completed, _ = await asyncio.wait(
                            (serve_task, stop_task), return_when=asyncio.FIRST_COMPLETED
                        )
                        if serve_task in completed:
                            await serve_task  # Do not hide unexpected server failure.
                        else:
                            print('Soulbound: zamykanie serwera na zlecenie STOP_Soulbound.bat.', flush=True)
                            serve_task.cancel()
                            try:
                                await serve_task
                            except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal shutdown
                                pass
                            for session in tuple(self.sessions):
                                try:
                                    await asyncio.wait_for(session.close(), timeout=10)
                                except Exception as exc:
                                    print('Soulbound: nieudany zapis lub zamkniecie sesji: '
                                          + repr(exc), flush=True)
                            self.db.conn.commit()
                            print('Soulbound: zakonczenie sesji i zapis SQLite zakonczone.', flush=True)
                    finally:
                        for task in (serve_task, stop_task):
                            if not task.done():
                                task.cancel()
                        await asyncio.gather(serve_task, stop_task, return_exceptions=True)
        finally:
            if control is not None:
                await control.close()
            for task in (wander_task, xp_event_task, latency_task, fame_v115_task):
                task.cancel()
            for task in (wander_task, xp_event_task, latency_task, fame_v115_task):
                try:
                    await task
                except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal server shutdown task cancellation
                    pass
