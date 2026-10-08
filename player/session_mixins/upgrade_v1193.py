# -*- coding: utf-8 -*-
"""v1.19.1-1.19.3: NVDA-readable navigation, career and party planning.

All commands are opt-in. They reuse the real path graph and existing durable
statistics; they never auto-teleport, fabricate achievements or grant rewards.
"""
from __future__ import annotations

from core.classes_skills import ROOMS


# Milestones are PROGRESS HINTS, not reward grants or new unlock definitions.
CAREER_MILESTONES_V1192 = (
    ("Zwycięstwa", "kills_total", (10, 100, 1000, 10000, 100000)),
    ("Bossowie", "boss_kills", (1, 10, 50, 100, 500, 1000)),
    ("Zadania", "quests_completed", (10, 50, 100, 500, 1000)),
    ("Profesje", "profession_actions", (25, 100, 1000, 10000, 100000)),
    ("Odkryte lokacje", "rooms_discovered", (10, 50, 100, 500, 1000)),
)


def next_career_milestone_v1192(value, thresholds):
    """Next informational checkpoint, or None after the last threshold."""
    value = max(0, int(value or 0))
    for threshold in thresholds:
        if value < threshold:
            return threshold, threshold - value
    return None


class SessionUpgradeV1193Mixin:
    def _party_room_v1193(self, session):
        character = getattr(session, "character", None)
        if character is None:
            return None
        return ROOMS.get(character.room_id)

    async def navigation_v1191(self, args=""):
        """Compact route/nearby guidance; cannot move player or bypass gates."""
        if not self.character:
            await self.send("Nawigacja: najpierw wybierz postać.")
            return
        raw = str(args or "").strip()
        mode = self.normalize_room_query(raw)
        room_id = self.character.room_id
        room = ROOMS.get(room_id)
        if not room:
            await self.send("Nawigacja: lokacja nie jest obecnie dostępna na mapie.")
            return
        if mode in ("", "status", "stan"):
            await self.send(f"NAWIGACJA 2.0: {room['name']}. Strefa: {room.get('zone', 'nieznana')}.")
            task = getattr(self, "guide_task", None)
            await self.send("Automatyczne prowadzenie: " + ("aktywne." if task and not task.done() else "nieaktywne."))
            target = getattr(self, "route_target_room", None)
            if target in ROOMS:
                path = self.shortest_path(room_id, target)
                label = getattr(self, "route_target_label", "") or ROOMS[target]["name"]
                if path is None:
                    await self.send(f"Zapamiętany cel: {label}; brak połączenia na mapie.")
                elif not path:
                    await self.send(f"Zapamiętany cel: {label}; już jesteś na miejscu.")
                else:
                    direction, next_room = path[0]
                    await self.send(f"Cel: {label}. Pozostało {len(path)} przejść. Teraz: "
                                    f"{self.route_direction_name(direction)} do {ROOMS[next_room]['name']}.")
            else:
                await self.send("Brak zapamiętanego celu. Użyj: trasa <cel>.")
            await self.send("Skróty: nawigacja krok, nawigacja okolica, nawigacja cel <nazwa>.")
            return
        if mode in ("krok", "next", "dalej"):
            await self.show_route_next_step()
            return
        if mode in ("okolica", "otoczenie", "sasiedzi", "sąsiedzi"):
            await self.send(f"OKOLICA: {room['name']}. Wyjścia: {len(room.get('exits', {}))}.")
            for direction, neighbor in sorted(room.get("exits", {}).items()):
                target = ROOMS.get(neighbor)
                if target is not None:
                    await self.send(f"{self.route_direction_name(direction)}: {target['name']}; "
                                    f"strefa {target.get('zone', 'nieznana')}.")
            await self.send("Lista pokazuje mapę, a nie uprawnienie do przejścia przez zamknięte bramy.")
            return
        if mode in ("druzyna", "drużyna", "grupa", "party"):
            await self.party_route_v1193("")
            return
        if mode.startswith("cel "):
            await self.show_route(raw.split(maxsplit=1)[1])
            return
        await self.send("Nawigacja 2.0: nawigacja [status|krok|okolica|druzyna|cel <nazwa>]. "
                        "Trasa jest informacją, a przejścia nadal sprawdzają wszystkie blokady.")

    async def career_v1192(self, args=""):
        """Read-only compact per-account statistics; zero schema changes."""
        if self.account_id is None or not self.character:
            await self.send("Kariera: najpierw wybierz postać.")
            return
        mode = self.normalize_room_query(args)
        stats = self.server.db.lifetime_stats(self.account_id)
        def val(key):
            return max(0, int(stats.get(key, 0) or 0))
        if mode in ("", "status", "podsumowanie"):
            achievements = self.server.db.achievement_rows(self.account_id)
            await self.send(f"KARIERA 2.0: {self.character.name}. Trwałe zapisane dane postaci.")
            await self.send(f"Walka: zwycięstwa {val('kills_total')}; bossowie {val('boss_kills')}; "
                            f"rzadcy wrogowie {val('rare_kills')}; śmierci {max(val('deaths'),int(self.character.deaths or 0))}.")
            await self.send(f"Wyprawy: odkryte lokacje {max(val('rooms_discovered'), len(self.server.db.discovered_room_ids(self.account_id)))}; "
                            f"zadania {val('quests_completed')}; kontrakty {val('bounties_completed')}.")
            await self.send(f"Rzemiosło: czynności {val('profession_actions')}; "
                            f"craftingi {val('craft_actions')}; przedmioty {val('crafted_items')}.")
            await self.send(f"Odblokowane osiągnięcia: {len(achievements)}. "
                            "Szczegóły: osiagniecia; postęp: osiagniecia postep.")
            await self.send("Kategorie: kariera walka, kariera profesje, kariera rekordy, kariera postep.")
        elif mode in ("walka", "combat"):
            await self.send(f"WALKA: zwycięstwa {val('combat_victories')}; zabici wrogowie {val('kills_total')}; "
                            f"bossowie {val('boss_kills')}; rzadcy {val('rare_kills')}; "
                            f"śmierci {max(val('deaths'), int(self.character.deaths or 0))}.")
            await self.send("Historia ostatniej walki: combat ostatnie. Bossowie: bosskodex.")
        elif mode in ("profesje", "rzemioslo", "craft"):
            await self.send(f"PROFESJE: działania {val('profession_actions')}; crafting {val('craft_actions')}; "
                            f"przedmioty {val('crafted_items')}; połowy {val('fish_caught')}; "
                            f"ruda {val('ore_mined')}; drewno {val('wood_gathered')}; zioła {val('herbs_gathered')}.")
            await self.send("Starsze zapisy mogą nie zawierać dokładnych liczników sprzed v0.9.4.")
        elif mode in ("osiagniecia", "postep", "progress", "cele"):
            await self.send("NASTĘPNE PROGI KARIERY (orientacyjne, bez automatycznych nagród):")
            for label, key, thresholds in CAREER_MILESTONES_V1192:
                value = val(key)
                if key == "rooms_discovered":
                    value = max(value, len(self.server.db.discovered_room_ids(self.account_id)))
                next_step = next_career_milestone_v1192(value, thresholds)
                if next_step is None:
                    await self.send(f"{label}: {value}; wszystkie pokazane progi przekroczone.")
                else:
                    threshold, remaining = next_step
                    await self.send(f"{label}: {value} z {threshold}; brakuje {remaining}.")
            await self.send("Faktycznie odblokowane osiągnięcia: osiagniecia.")
        elif mode in ("rekordy", "records"):
            row = self.server.db.conn.execute(
                "SELECT COUNT(*) AS total, MAX(damage_dealt) AS max_damage, "
                "MAX(damage_taken) AS max_taken, MAX(healing) AS max_heal "
                "FROM combat_recaps_v03052 WHERE account_id=?", (self.account_id,)
            ).fetchone()
            await self.send(f"REKORDY Z ZAPISANYCH WALK: podsumowania {int(row['total'] or 0)}; "
                            f"maks. obrażenia zadane w walce {int(row['max_damage'] or 0)}; "
                            f"maks. obrażenia otrzymane {int(row['max_taken'] or 0)}; "
                            f"maks. leczenie {int(row['max_heal'] or 0)}.")
            await self.send("Rekordy dotyczą zachowanych raportów walk, nie wszystkich dawnych walk. "
                            "Rekordy bossów: bosskodex.")
        else:
            await self.send("Kariera: kariera [status|walka|profesje|rekordy|postep]. "
                            "Osiągnięcia: osiagniecia postep albo osiagniecia.")

    async def achievements_plus_v1192(self, args=""):
        mode = self.normalize_room_query(args)
        if mode in ("postep", "progress", "cele", "progi"):
            await self.career_v1192("postep")
        elif mode in ("", "lista", "list", "status"):
            await self.show_achievements()
        else:
            await self.send("Osiągnięcia: osiagniecia albo osiagniecia postep.")

    async def party_report_v1193(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        members = sorted(self.server.party_sessions(self.account_id),
                         key=lambda x: (x.account_id != key, x.character.name.casefold()))
        ready = self.server.party_ready_checks.get(key)
        leader = self.server.session_by_account(key)
        leader_room = leader.character.room_id if leader and leader.character else None
        here = self.character.room_id
        await self.send(f"PARTY 4.0: {len(members)} członków online. "
                        f"W twojej lokacji {sum(s.character.room_id == here for s in members)}.")
        if ready is not None:
            await self.send(f"Gotowych: {len(ready.intersection(set(self.server.parties.get(key, set()))))} "
                            f"z {len(self.server.parties.get(key, set()))} członków.")
        for session in members:
            c = session.character
            health = max(0, min(100, int(100 * max(0, session.current_hp) / max(1, session.max_hp()))))
            mana = max(0, min(100, int(100 * max(0, session.current_mana) / max(1, session.max_mana()))))
            flags = []
            if session.account_id == key:
                flags.append("lider")
            if session.is_downed_v0371():
                flags.append("powalony")
            if ready is not None:
                flags.append("gotowy" if session.account_id in ready else "niegotowy")
            place = "obok ciebie" if c.room_id == here else ROOMS.get(c.room_id, {}).get("name", "nieznana lokacja")
            await self.send(f"{c.name}, {c.class_name}, level {c.character_level}; "
                            f"HP {health}%, Mana {mana}%; {place}" +
                            ("; " + ", ".join(flags) if flags else "") + ".")
        if leader_room and leader_room != here:
            path = self.shortest_path(here, leader_room)
            if path is not None:
                await self.send(f"Do lidera po mapie: {len(path)} przejść. "
                                "Ruch nie omija żadnych blokad wejścia.")

    async def party_gather_v1193(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        leader = self.server.session_by_account(key)
        if leader is None or leader.character is None:
            await self.send("Lider jest offline. Zbiórka nie może określić jego lokacji.")
            return
        room_id = leader.character.room_id
        room = ROOMS.get(room_id)
        if room is None:
            await self.send("Lokacja lidera nie jest na aktualnej mapie.")
            return
        await self.send(f"ZBIÓRKA: lider {leader.character.name}, {room['name']}. "
                        "To wskazówka, nie teleport.")
        for member in sorted(self.server.party_sessions(self.account_id), key=lambda x:x.character.name.casefold()):
            if member is leader:
                continue
            path = self.shortest_path(member.character.room_id, room_id)
            if path is None:
                result = "brak połączenia na mapie"
            elif not path:
                result = "na miejscu"
            else:
                result = f"{len(path)} przejść; najpierw {self.route_direction_name(path[0][0])}"
            await self.send(f"{member.character.name}: {result}.")
        await self.send("Drużyna automatycznie podąża za liderem wyłącznie, gdy członkowie są razem; "
                        "osobne blokady wejścia nadal obowiązują.")

    async def party_route_v1193(self, args=""):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        raw = str(args or "").strip()
        mode = self.normalize_room_query(raw)
        if mode in ("off", "usun", "clear", "stop", "wylacz"):
            if key != self.account_id:
                await self.send("Tylko lider może usunąć wspólny cel trasy.")
                return
            self.server.party_routes_v1193.pop(key, None)
            await self.server.party_broadcast(key, "Wspólna trasa drużyny została wyłączona.")
            return
        if mode in ("", "status", "krok", "next", "dalej"):
            target = self.server.party_routes_v1193.get(key)
            if not target or target[0] not in ROOMS:
                await self.send("Brak wspólnej trasy. Lider: druzyna trasa <cel>.")
                return
            room_id, label = target
            path = self.shortest_path(self.character.room_id, room_id)
            if path is None:
                await self.send(f"TRASA DRUŻYNY: {label}; brak połączenia z twojej lokacji.")
            elif not path:
                await self.send(f"TRASA DRUŻYNY: {label}; jesteś na miejscu.")
            else:
                direction, next_room = path[0]
                await self.send(f"TRASA DRUŻYNY: {label}. {len(path)} przejść. "
                                f"Twój pierwszy krok: {self.route_direction_name(direction)} "
                                f"do {ROOMS[next_room]['name']}.")
            return
        if key != self.account_id:
            await self.send("Tylko lider może ustawić trasę. Wpisz druzyna trasa krok, by odczytać wskazówkę.")
            return
        # Do not choose an ambiguous target or create high dungeon floors on request.
        npc = self.find_guide_npc(raw)
        matches = [npc[1]['room']] if npc else self.find_room_matches(raw)
        matches = list(dict.fromkeys(self.guide_exploration_safe_target(rid) for rid in matches))
        if len(matches) != 1:
            await self.send("Nie rozpoznaję jednoznacznego celu drużyny. Podaj pełniejszą nazwę "
                            "lub sprawdź: prowadz lista.")
            return
        target = matches[0]
        path = self.shortest_path(self.character.room_id, target)
        if path is None:
            await self.send("Brak połączenia z celem na aktualnej mapie. Nie zapisano trasy.")
            return
        label = str(npc[1].get("name") or ROOMS[target]["name"]) if npc else ROOMS[target]["name"]
        self.server.party_routes_v1193[key] = (target, label)
        # Changing a coordination objective invalidates an old ready check.
        self.server.party_ready_checks.pop(key, None)
        await self.server.party_broadcast(key,
            f"Lider ustawia trasę: {label}; z jego lokacji {len(path)} przejść. "
            "Sprawdź własny krok: druzyna trasa krok. Gotowość wyzerowana.")

