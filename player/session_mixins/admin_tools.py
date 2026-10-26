# -*- coding: utf-8 -*-
"""Admin commands, wipe and unlock helpers."""

from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES
import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from data.npcs import NPCS
from data.mobs import MOB_TEMPLATES

from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from network.protocol_gameplay_utils import (
    BOSS_CHEST_OPENED_CATEGORY_V11332,
    _boss_floor_chest_spec,
    boss_chest_reward_roll,
    boss_floor_chest_name,
    boss_floor_chest_state_id,
    boss_floor_key_id,
)

def boss_chest_should_restore_v1288(opened_at, world_started, respawn_at, boss_alive):
    """A spent chest returns only when the checkpoint boss has returned.

    `opened_at` comes from the EXISTING collection_codex.discovered_at UTC
    column. No database migration or extra per-player state is needed.
    """
    if not boss_alive:
        return False
    try:
        opened_at = float(opened_at)
        cycle_start = max(float(world_started or 0), float(respawn_at or 0))
    except (TypeError, ValueError, OverflowError):
        return False
    # SQLite timestamps have one-second precision. Avoid false new cycles if
    # someone opens the chest immediately after boss resurrection.
    return opened_at + 1.5 < cycle_start


class SessionAdminToolsMixin:

    def is_admin(self):
            if self.master_account_id is None:
                return False
            username = self.server.db.account_name(self.master_account_id).casefold()
            return bool(username and username in ADMIN_ACCOUNT_NAMES)

    async def admin_command(self, args=""):
            raw = str(args or "").strip()
            first_guardian = raw.split(maxsplit=1)[0].casefold() if raw else ""
            guardian_direct = {"test", "moc", "ratunek", "wsparcie", "spawn", "event",
                               "kraina", "balans", "panel", "questdiag", "questnapraw", "role"}
            history_guardian = raw.casefold().startswith(("historia olc", "historia szczegoly", "historia quest", "historia cofnij"))
            if first_guardian == "guardian11":
                from systems.admin_guardian11_v4500 import handle_guardian11
                await handle_guardian11(self, raw)
                return
            if first_guardian == "guardian10":
                from systems.admin_guardian10_v4400 import handle_guardian10
                await handle_guardian10(self, raw)
                return
            if first_guardian == "guardian9":
                from systems.admin_guardian9_v4300 import handle_guardian9
                await handle_guardian9(self, raw)
                return
            if first_guardian == "guardian8":
                from systems.admin_guardian8_v4200 import handle_guardian8
                await handle_guardian8(self, raw)
                return
            if first_guardian == "guardian7":
                from systems.admin_guardian7_v4100 import handle_guardian7
                await handle_guardian7(self, raw)
                return
            if first_guardian == "guardian6":
                from systems.admin_guardian6_v4000 import handle_guardian6
                await handle_guardian6(self, raw)
                return
            if first_guardian == "guardian5":
                from systems.admin_guardian5_v3900 import handle_guardian5
                await handle_guardian5(self, raw)
                return
            if first_guardian == "guardian4":
                from systems.admin_guardian4_v3800 import handle_guardian4
                await handle_guardian4(self, raw)
                return
            if first_guardian == "guardian3":
                from systems.admin_guardian3_v3700 import handle_guardian3
                await handle_guardian3(self, raw)
                return
            if first_guardian == "guardian" or first_guardian in guardian_direct or history_guardian:
                from systems.admin_guardian2_v3600 import handle_guardian
                await handle_guardian(self, raw if first_guardian == "guardian" else "guardian " + raw)
                return
            if not self.is_admin():
                await self.send("Nieznana komenda. Wpisz help.")
                return
            norm = self.normalize_description_query(raw)
            # v1.40.5: convenient admin form must never be mistaken for a wipe.
            if norm.startswith(("wyczysc naprawione", "wyczyść naprawione")):
                await self.admin_error_cleanup_shortcut_v1405(norm)
                return
            if norm == "god" or norm.startswith("god "):
                await self.admin_god_mode_v35005(raw[3:].strip())
                return
            if norm == "cios" or norm.startswith("cios "):
                await self.admin_unique_strike_v35005(raw[4:].strip())
                return
            if not norm or norm in ("help", "pomoc"):
                await self.send("ADMIN OWNER-ONLY")
                await self.send("admin status / administrator status — status uprawnień.")
                await self.send("admin heal / administrator ulecz — pełne HP i Mana.")
                await self.send("admin god on/off/status — nieśmiertelność awaryjna tylko dla administratora.")
                await self.send("admin cios grom/nawalnica/wyrok [cel] — specjalne ataki admina podczas walki.")
                await self.send("admin pomoc gracze — ulecz/wskrzes/przywolaj kolegów.")
                await self.send("admin goto <room_id> / administrator teleport <room_id> — teleport testowy.")
                await self.send("admin give <item_id> [ilość] / administrator daj <item_id> [ilość].")
                await self.send("admin haslo reset <login> - jednorazowy kod do prywatnego przekazania właścicielowi konta.")
                await self.send("admin pomoc gracze / serwer / swiat / postacie - Admin Tools 2.0.")
                await self.send("admin live - nowe lokacje, przejscia, potwory i balans bez restartu.")
                await self.send("admin live arena pomoc — testowa walka, skille i sprzet, bez nowych numerow guardian.")
                await self.send("admin guardian pomoc — narzedzia Wladcy Swiata 2.0, arena, ratunek, role i kreator krain.")
                await self.send("admin guardian3 pomoc — rozszerzenia v37: arena, kraina do 20 pokoi, questy, balans, eventy, role i historia.")
                await self.send("admin guardian4 pomoc — v38: prognozy areny, laczenie pokoi DRAFT, skan questow.")
                await self.send("admin guardian5 pomoc — v39: EXP 6 statystyk, katalog i diagnostyka questow, arenowe metadane bossow, raport OLC.")
                await self.send("admin guardian6 pomoc — v40: nagrody grupowe DRAFT, audyt questow, zaleznosci i OLC preflight.")
                await self.send("admin guardian7 pomoc 1 — v41: prywatna arena zasad UOSS, naprawy questow i cofanie DRAFT.")
                await self.send("admin guardian8 pomoc 1 — v42: wzmocniona arena UOSS, efekty czasowe i seryjne naprawy questow DRAFT.")
                await self.send("admin guardian9 pomoc 1 — v43: prognozy i migawki areny UOSS, kontrola DRAFT questow.")
                await self.send("admin guardian10 pomoc 1 — v44: odizolowane RNG LAB, porownania wariantow i migawki.")
                await self.send("admin guardian11 pomoc 1 — v45: skille i testowy ekwipunek w arenie UOSS LAB, sekwencje tur.")
                await self.send("admin live pomoc 1/2/3 — v46: jedna pomoc, arena druzyna i bezpieczne naprawy questow.")
                await self.send("admin blad lista 20; admin blad diagnoza NUMER; admin blad questy NICK; admin blad napraw NUMER NICK QUEST_ID POTWIERDZAM.")
                await self.send("Wyczysc naprawione POTWIERDZAM - usuwa wyłącznie oznaczone jako naprawione błędy SB, nie postacie.")
                await self.send("wipe moje postacie POTWIERDZAM / wipe my characters CONFIRM.")
                await self.send("wipe wszystkie postacie POTWIERDZAM / wipe all characters CONFIRM.")
                await self.send("Wipe usuwa postacie i ich progres, ale NIE usuwa kont/loginów/haseł.")
                return
            if norm == "live" or norm.startswith("live "):
                await self.admin_live_v1204(raw[4:].strip())
                return
            if await self.admin_tools_v1224(raw):
                return
            if norm in ("status",):
                await self.send(
                    f"Administrator: TAK. Konto: {self.server.db.account_name(self.master_account_id)}. GOD: {'WLACZONY' if getattr(self, 'admin_god_v35005', False) else 'WYLACZONY'}."
                )
                return
            if norm in ("heal", "ulecz", "wylecz"):
                self.current_hp = self.max_hp()
                self.current_mana = self.max_mana()
                self.server.db.record_admin_action_v1224(self.server.db.account_name(self.master_account_id), "heal_self")
                await self.send(f"ADMIN: HP {self.current_hp}/{self.max_hp()}, Mana {self.current_mana}/{self.max_mana()}.")
                return
            parts = raw.split()
            first = self.normalize_description_query(parts[0]) if parts else ""
            if first in ("haslo", "hasło", "password"):
                if len(parts) != 3 or self.normalize_description_query(parts[1]) not in ("reset", "kod"):
                    await self.send("Użycie: admin haslo reset <login>.")
                    return
                target = self.server.db.master_account_by_name(parts[2])
                if not target:
                    await self.send("Nie można wygenerować kodu resetowania dla tego konta.")
                    return
                code = self.server.db.issue_password_recovery_v1222(target["id"], "admin")
                if code is None:
                    await self.send("Odczekaj co najmniej minutę przed ponownym wygenerowaniem kodu.")
                    return
                self.server.db.record_admin_action_v1224(self.server.db.account_name(self.master_account_id), "haslo_reset", target["username"])
                await self.send(
                    f"Kod jednorazowy dla konta {target['username']}: {code}. "
                    "Ważny 15 minut. Przekaż go prywatnie zweryfikowanemu właścicielowi. "
                    "Nie wysłano go automatycznie; starego hasła nie można odczytać.",
                    history_store=False,
                )
                return
            if first in ("goto", "teleport", "idz", "idź"):
                target = " ".join(parts[1:]).strip()
                room_id = target if target in ROOMS else self.find_room(target)
                if not room_id or room_id not in ROOMS:
                    await self.send("ADMIN: nie znaleziono lokacji.")
                    return
                self.character.room_id = room_id
                self.server.db.save_character(self.character)
                self.server.db.record_admin_action_v1224(self.server.db.account_name(self.master_account_id), "goto", room_id)
                await self.send(f"ADMIN: teleport do {ROOMS[room_id]['name']}.")
                await self.look()
                return
            if first in ("give", "daj"):
                if len(parts) < 2:
                    await self.send("Użycie: admin give <item_id> [ilość].")
                    return
                item_id = parts[1]
                try:
                    qty = max(1, min(9999, int(parts[2]) if len(parts) >= 3 else 1))
                except ValueError:
                    qty = 1
                if item_id not in ITEMS:
                    await self.send("ADMIN: nieznany item_id.")
                    return
                self.server.db.add_item(self.account_id, item_id, qty)
                self.server.db.record_admin_action_v1224(self.server.db.account_name(self.master_account_id), "give", f"{item_id} x{qty}")
                await self.send(f"ADMIN: dodano {ITEMS[item_id]['name']} x{qty}.")
                return
            await self.send("Nieznana opcja admin. Wpisz admin help.")

    async def admin_god_mode_v35005(self, args=""):
        """Session-only owner immortality; ordinary play stays unchanged."""
        if not self.is_admin():
            await self.send("Nieznana komenda. Wpisz help.")
            return
        choice = self.normalize_description_query(str(args or "").strip())
        if choice in ("", "status"):
            state = "WLACZONA" if getattr(self, "admin_god_v35005", False) else "WYLACZONA"
            await self.send(f"ADMIN GOD: {state}. Uzyj admin god on/off.")
            return
        if choice not in ("on", "off"):
            await self.send("Uzycie: admin god on / admin god off / admin god status.")
            return
        enabled = choice == "on"
        self.admin_god_v35005 = enabled
        if enabled:
            self.current_hp = self.max_hp()
        self.server.db.record_admin_action_v1224(
            self.server.db.account_name(self.master_account_id),
            "god_on" if enabled else "god_off", self.character.name,
        )
        await self.send(
            "ADMIN GOD WLACZONY: nie mozesz zginac; koledzy nadal graja normalnie. "
            "Wylacz przez admin god off. Tryb nie zapisuje sie po wylogowaniu."
            if enabled else "ADMIN GOD WYLACZONY: wracasz do normalnej walki."
        )

    async def admin_unique_strike_v35005(self, args=""):
        """Owner-only rescue strike; uses canonical victory and party credit."""
        if not self.is_admin():
            await self.send("Nieznana komenda. Wpisz help.")
            return
        from data.mobs import MOB_TEMPLATES as _mob_catalog
        from world.uoss_superboss_runtime import superboss_attack_gate_v11137
        words = str(args or "").strip().split(maxsplit=1)
        if not words or self.normalize_description_query(words[0]) not in ("grom", "nawalnica", "wyrok"):
            await self.send("Uzycie: admin cios grom/nawalnica/wyrok [cel]. Grom 15%, nawalnica 35%, wyrok 100% HP celu.")
            return
        technique = self.normalize_description_query(words[0])
        query = words[1].strip() if len(words)>1 else ""
        mob = None
        if query:
            mob = self.server.world.find_mob(self.character.room_id, query)
        elif self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
        if not mob or not mob.alive or mob.room_id != self.character.room_id:
            await self.send("ADMIN CIOS: najpierw rozpocznij walke lub podaj zywego potwora z pokoju.")
            return
        template = _mob_catalog[mob.template_id]
        # No direct bypass of source boss prerequisites, party ownership or combat gates.
        allowed, reason = superboss_attack_gate_v11137(self, template)
        if not allowed:
            await self.send(reason)
            return
        if self.combat_mob_key != mob.key:
            await self.attack(query or template["name"])
            if self.combat_mob_key != mob.key or not mob.alive:
                return
        if not self.server.engagement_allowed(self, mob):
            await self.send(self.engagement_block_message(mob))
            return
        percent = {"grom": 15, "nawalnica": 35, "wyrok": 100}[technique]
        effective_hp = max(1, int(self.mob_effective_max_hp_v11330(mob, template)))
        damage = min(max(0, int(mob.hp)), max(1, effective_hp * percent // 100))
        mob.hp -= damage
        self._recap52_dealt = int(getattr(self, "_recap52_dealt", 0) or 0) + damage
        self.server.db.record_admin_action_v1224(
            self.server.db.account_name(self.master_account_id),
            "admin_cios_" + technique, mob.template_id,
        )
        await self.server.party_combat_broadcast(
            self,
            f"ADMIN {self.character.name}: {technique.upper()}! {damage} obrazen w "
            f"{template['name']}. Pozostalo HP {max(0, mob.hp)}.", detail="essential",
        )
        await self.send(
            f"ADMIN CIOS {technique.upper()}: {damage} obrazen. "
            f"{template['name']}: {max(0, mob.hp)} HP."
        )
        if mob.hp <= 0:
            await self.mob_defeated(mob)

    async def admin_live_v1204(self, args=''):
        """Validated in-game OLC: no Python execution and no server restart."""
        if not self.is_admin():
            await self.send("Nieznana komenda. Wpisz help.")
            return
        service = self.server.live_content_v1204
        raw = str(args or '').strip()
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower() if parts else ''
        tail = parts[1].strip() if len(parts) > 1 else ''
        # v102.00.11: owner-only, bounded error triage; no source-code hotpatch.
        if cmd in ('bledy', 'błędy', 'napraw'):
            from systems.admin_live_repair_center_v1020011 import handle_repair_center
            if await handle_repair_center(self, cmd, tail):
                return
        # v102.00.6: global adaptive combat switch; not an OLC DRAFT change.
        if cmd == 'skalowanie':
            from systems.adaptive_switch_v102006 import command as adaptive_switch_command
            await adaptive_switch_command(self, tail)
            return
        # v102: local native engine tunnel, guarded mechanic vocabulary and audit.
        if cmd in ('pomoc','arena','audyt'):
            from systems.admin_live_final_v10200 import dispatch_v10200
            if await dispatch_v10200(self,cmd,tail):return
        # v101: declarative mechanics, live CAS progression and arena series.
        if cmd in ('pomoc','mechaniki','postacie','arena'):
            from systems.admin_live_v10100 import dispatch_v10100
            if await dispatch_v10100(self,cmd,tail):return
        # v100: five bounded additions. Register before legacy fallback.
        if cmd in ('pomoc','skill','questy','zadania','postacie','arena','boss'):
            from systems.admin_live_ultimate_v10000 import dispatch_v10000
            if await dispatch_v10000(self,cmd,tail):return
        # v99: five guarded extensions. Legacy admin live commands remain intact.
        if cmd in ('pomoc','skill','questy','zadania','arena','postacie','boss'):
            from systems.admin_live_five_v9900 import dispatch_v9900
            if await dispatch_v9900(self,cmd,tail):return
        # v98: three new owner-only tools, keeping all older aliases intact.
        if cmd in ('pomoc','boss'):
            from systems.admin_live_uoss_v9800 import dispatch_v9800_uoss
            if await dispatch_v9800_uoss(self,cmd,tail):return
        if cmd in ('pomoc','questy','zadania'):
            from systems.admin_live_quest_doctor_v9800 import dispatch_v9800_doctor
            if await dispatch_v9800_doctor(self,cmd,tail):return
        if cmd in ('pomoc','postacie'):
            from systems.admin_live_advancement_v9800 import dispatch_v9800_advancement
            if await dispatch_v9800_advancement(self,cmd,tail):return
        # v97: 8-character atomic offline stat edits and safe existing inventory stack corrections.
        if cmd in ('pomoc','postacie'):
            from systems.admin_live_offline_v9700 import dispatch_v9700_offline
            if await dispatch_v9700_offline(self,cmd,tail):return
        # v97: clone existing *executable* scripted UOSS profiles in a validated DRAFT bundle.
        if cmd in ('pomoc','boss'):
            from systems.admin_live_uoss_profiles_v9700 import dispatch_v9700_uoss
            if await dispatch_v9700_uoss(self,cmd,tail):return
        # v96: unlocked class + learned-skill progress (not new unlocks), EXP bank inspection.
        if cmd in ('pomoc','postacie'):
            from systems.admin_live_mastery_v9600 import dispatch_v9600
            if await dispatch_v9600(self,cmd,tail):return
        # v95: offline progression recovery with SQLite CAS, audit and undo.
        if cmd in ('pomoc','postacie'):
            from systems.admin_live_progress_v9500 import dispatch_v9500
            if await dispatch_v9500(self,cmd,tail):return
        # v94: multi-quest final-state patches, exact counter fixes, skill effect bundles.
        if cmd in ('pomoc','questy','zadania','skill'):
            from systems.admin_live_v9400 import dispatch_v9400
            if await dispatch_v9400(self,cmd,tail):return
        # v93: one atomic package for quest prerequisites AND multiple target kinds.
        if cmd in ('pomoc','questy','zadania'):
            from systems.admin_live_v9300 import dispatch_v9300
            if await dispatch_v9300(self,cmd,tail):return
        # v92: atomically repair real quest targets, rewards and NPC giver links.
        if cmd in ('pomoc','questy','zadania'):
            from systems.admin_live_v9200 import dispatch_v9200
            if await dispatch_v9200(self,cmd,tail):return
        # v91: full-graph migration of stale quest dependency IDs; DRAFT-only.
        if cmd in ('pomoc','questy','zadania'):
            from systems.admin_live_v9100 import dispatch_v9100
            if await dispatch_v9100(self,cmd,tail):return
        # v90: OLC revision history and safe DRAFT-only restore.
        if cmd in ('pomoc','rewizje'):
            from systems.admin_live_v9000 import dispatch_v9000
            if await dispatch_v9000(self,cmd,tail):return
        # v89: publication safety gate and full screen-reader diff.
        if cmd in ('pomoc','aktualizacja'):
            from systems.admin_live_v8900 import dispatch_v8900
            if await dispatch_v8900(self,cmd,tail):return
        # v88: validated cross-domain atomic Admin Live changeset, DRAFT-only.
        if cmd in ('pomoc','aktualizacja'):
            from systems.admin_live_v8800 import dispatch_v8800
            if await dispatch_v8800(self,cmd,tail):return
        # v87: atomic cross-quest & multi-superboss editing, DRAFT-only.
        if cmd in ('pomoc','questy','zadania','boss'):
            from systems.admin_live_v8700 import dispatch_v8700
            if await dispatch_v8700(self,cmd,tail):return
        # v86: native full-engine arena lifecycle inside existing admin live.
        if cmd in ('pomoc','arena'):
            from systems.admin_live_native_arena_v8600 import dispatch_v8600
            if await dispatch_v8600(self,cmd,tail):return
        # v78: source player basic attack on a detached test Session only.
        if cmd in ('pomoc','arena'):
            from systems.admin_live_arena_damage_v7800 import dispatch_v7800
            if await dispatch_v7800(self,cmd,tail):return
        # v77: additive playable archetype classes; first route before inherited panels.
        if cmd in ('pomoc','rodowod'):
            from systems.admin_live_classes_v7700 import dispatch_v7700
            if await dispatch_v7700(self,cmd,tail):return
        # v76: truly selectable new races, persisted and protected against deletion if used.
        if cmd in ('pomoc','rodowod'):
            from systems.admin_live_races_v7600 import dispatch_v7600
            if await dispatch_v7600(self,cmd,tail):return
        # v75: native atomic UOSS mechanics editor using real OLC24/32/33/34.
        if cmd in ('pomoc','boss'):
            from systems.admin_live_v7500 import dispatch_v7500
            if await dispatch_v7500(self,cmd,tail):return
        # v74: safe legacy quest parent repair, dependency impact, UOSS encounter data.
        if cmd in ('pomoc','questy','zadania','boss'):
            from systems.admin_live_v7400 import dispatch_v7400
            if await dispatch_v7400(self,cmd,tail):return
        # v73: multi-object final-state OLC validation and safe scripted boss audit.
        if cmd in ('pomoc','questy','zadania','boss'):
            from systems.admin_live_v7300 import dispatch_v7300
            if await dispatch_v7300(self,cmd,tail):return
        # v72: targeted extensions before older commands consume their subtrees.
        if cmd in ('pomoc','questy','zadania','boss','postacie'):
            from systems.admin_live_v7200 import dispatch_v7200
            if await dispatch_v7200(self,cmd,tail):return
        # v71: owner-only, validated, NVDA-friendly eight-area maintenance routes.
        if cmd in ('pomoc','arena','questy','zadania','skill','boss','limity'):
            from systems.admin_live_v7100 import dispatch_v7100
            if await dispatch_v7100(self,cmd,tail):return
        if cmd in ('pomoc','postacie'):
            from systems.admin_live_characters_v7100 import dispatch_v7100_characters
            if await dispatch_v7100_characters(self,cmd,tail):return
        if cmd in ('pomoc','rodowod'):
            from systems.admin_live_heritage_v7100 import dispatch_v7100_heritage
            if await dispatch_v7100_heritage(self,cmd,tail):return
        # v70.00.3: targeted, read-only quest / skill / boss diagnosis.
        if cmd in ('pomoc','questy','zadania','boss','skill','centrum'):
            from systems.admin_live_diagnostics_v7003 import dispatch_v7003_diagnostics
            if await dispatch_v7003_diagnostics(self,cmd,tail):return
        # v70.00.3: opt-in vendor progression and live cap-adaptive authoring.
        if cmd in ('pomoc','sklep','sklepy'):
            from systems.admin_live_shop_progression_v7003 import dispatch_v7003_shop
            if await dispatch_v7003_shop(self,cmd,tail):return
        # v70.00.2: sourced UOSS trace, EQ coverage and atomic deterministic quest repairs.
        if cmd in ('pomoc','arena','eq','questy','zadania'):
            from systems.admin_live_v7002 import dispatch_v7002
            if await dispatch_v7002(self,cmd,tail):return
        # v69: one navigable index instead of scattered Guardian commands.
        if cmd in ('pomoc','centrum'):
            from systems.admin_live_v6900 import dispatch_v69
            if await dispatch_v69(self,cmd,tail):return
        # v70: read-only release acceptance gate, never claims predeploy PASS.
        if cmd in ('pomoc','odbior'):
            from systems.admin_live_v7000 import dispatch_v70
            if await dispatch_v70(self,cmd,tail):return
        # v68: production helper targeting + party support on detached LAB clones.
        if cmd in ('pomoc','arena'):
            from systems.admin_live_v6800 import dispatch_v68
            if await dispatch_v68(self,cmd,tail):return
        # v67: deterministic helper support results on detached LAB clones.
        if cmd in ('pomoc','arena'):
            from systems.admin_live_v6700 import dispatch_v67
            if await dispatch_v67(self,cmd,tail):return
        # v66: exact UOSS helper action choice/utility on detached clones.
        if cmd in ('pomoc','arena'):
            from systems.admin_live_v6600 import dispatch_v66
            if await dispatch_v66(self,cmd,tail):return
        # v65: source UOSS status immunity and helper passives, isolated LAB gear.
        if cmd in ('pomoc','arena'):
            from systems.admin_live_v6500 import dispatch_v65
            if await dispatch_v65(self,cmd,tail):return
        # v64: read-only counts and NVDA help for atomic linked quest repairs.
        if cmd in ('pomoc','questy','zadania'):
            from systems.admin_live_v6400 import dispatch_v64
            if await dispatch_v64(self,cmd,tail):return
        # v63: unified cap-aware class comparisons and scalar fields in bundled OLC.
        if cmd in ('pomoc','arena'):
            from systems.admin_live_v6300 import dispatch_v63
            if await dispatch_v63(self,cmd,tail):return
        # v62: multi-type quest transaction, high-level quest gear and class audit.
        if cmd in ('pomoc','questy','zadania','eq','arena'):
            from systems.admin_live_bundle_v6200 import dispatch_v62
            if await dispatch_v62(self,cmd,tail):return
        # v61: owner-confirmed NPC / resource / multi-objective references, DRAFT only.
        if cmd in ('pomoc','questy','zadania'):
            from systems.admin_live_quest_refs_v6100 import dispatch_v61
            if await dispatch_v61(self,cmd,tail):return
        # v60: owner-confirmed item/target ID corrections; only DRAFT.
        if cmd in ('pomoc','questy','zadania'):
            from systems.admin_live_quest_id_v6000 import dispatch_v60
            if await dispatch_v60(self,cmd,tail):return
        # v59: world loot preview and explicit quest dependency corrections.
        if cmd in ('pomoc','eq','questy','zadania'):
            from systems.admin_live_v5900 import dispatch_v59
            if await dispatch_v59(self,cmd,tail):return
        # v58: owner-only post-800 chest EQ and quest reward ID audit.
        if cmd in ('pomoc','skrzynie'):
            from systems.admin_live_equipment_v5800 import dispatch_v58
            if await dispatch_v58(self,cmd,tail):return
        if cmd in ('questy','zadania'):
            from systems.admin_live_quest_items_v5800 import dispatch_quest_items_v5800
            if await dispatch_quest_items_v5800(self,cmd,tail):return
        # v57: real boss chest post-800 gold preview, owner only.
        if cmd in ('pomoc','skrzynie'):
            from systems.admin_live_chests_v5700 import dispatch_v57
            if await dispatch_v57(self,cmd,tail):
                return
        # v56: read-only normal mob equipment drop forecast.
        if cmd in ('pomoc','eq'):
            from systems.admin_live_loot_v5600 import dispatch_v56
            if await dispatch_v56(self,cmd,tail):
                return
        # v55: real post-800 crafting forecast; short owner-only NVDA commands.
        if cmd in ('pomoc','eq'):
            from systems.admin_live_endless_v5500 import dispatch_v55
            if await dispatch_v55(self,cmd,tail):
                return
        # v54: final diagnostics; all public commands remain under admin live.
        if cmd in ('pomoc','questy','zadania','arena','eq','limity','limit','capy','gotowosc'):
            from systems.admin_live_finish_v5400 import dispatch_v54
            if await dispatch_v54(self,cmd,tail):
                return
        # v52: caps, persisted atomically, take effect without restarting.
        if cmd in ('limity', 'limit', 'capy'):
            from systems.admin_live_level_caps_v5200 import dispatch_v52_caps
            await dispatch_v52_caps(self, tail)
            return
        # v51: canonical OLC multi-field transactions and 22-class detached LAB.
        if cmd in ('pomoc','questy','zadania','arena'):
            from systems.admin_live_complete_v5100 import dispatch_v51
            if await dispatch_v51(self,cmd,tail):
                return
        # v50: bounded quest corrections and whole-graph audit, strictly DRAFT.
        if cmd in ('pomoc','questy','zadania','arena'):
            from systems.admin_live_final_v5000 import dispatch_v50
            if await dispatch_v50(self,cmd,tail):
                return
        # v49: bounded read-only quest integrity scan and isolated LAB trace.
        if cmd in ('pomoc','questy','zadania','arena'):
            from systems.admin_live_integrity_v4900 import dispatch_v49
            if await dispatch_v49(self,cmd,tail):
                return
        # v48: targeted quest-type diagnostics and fully isolated party comparisons.
        if cmd in ('pomoc','questy','zadania','arena'):
            from systems.admin_live_expansion_v4800 import dispatch_v48
            if await dispatch_v48(self,cmd,tail):
                return
        # v47: read-only diagnostics from the same familiar `admin live` menu.
        if cmd in ('pomoc','gotowosc','questy','zadania','arena'):
            from systems.admin_live_release_v4700 import dispatch_release
            if await dispatch_release(self,cmd,tail):
                return
        # v46: a single `admin live` entry point; only intercept new subcommands.
        # Existing OLC, Guardian aliases and publication flow remain untouched.
        if (cmd == 'pomoc' and tail) or cmd in ('arena','questy','zadania'):
            from systems.admin_live_ultimate_v4600 import dispatch_live_ultimate
            if await dispatch_live_ultimate(self, cmd, tail):
                return
        # v45: one consistent owner workflow. Keep guardianN as legacy aliases,
        # but expose all new LAB operations in the existing `admin live` menu.
        # This is a dispatch-only bridge: no publication, world writes or SQL.
        if cmd == 'arena':
            from systems.admin_live_guardian_bridge_v4500 import dispatch_live_arena
            await dispatch_live_arena(self, tail)
            return
        if cmd == 'nagrody':
            from systems.admin_guardian6_v4000 import handle_guardian6
            await handle_guardian6(self, 'guardian6 nagrody '+tail)
            return
        if cmd in ('questy', 'zadania') and tail:
            from systems.admin_live_guardian_bridge_v4500 import dispatch_live_quest
            if await dispatch_live_quest(self, tail):
                return
        if cmd == 'olc' and tail.casefold() == 'kontrola':
            from systems.admin_guardian7_v4100 import handle_guardian7
            await handle_guardian7(self, 'guardian7 olc kontrola')
            return
        help_text = (
            "ADMIN LIVE: arena pomoc [1/2/3]; arena start BOSS HP ATAK; "
            "arena klasa KLASA BIEGLOSC MANA POTWIERDZAM; arena skille; "
            "arena skill ID; arena przedmiot ID; arena sekwencja plan AKCJE; "
            "arena migawka; arena prognoza LICZBA; questy skan; "
            "questy audyt FRAZA; nagrody katalog FRAZA. "
            "EXPPROGI: expprogi podglad POLE PROG; expprogi ustaw POLE PROG NOWY_EXP. "
            "Zwykle komendy OLC ponizej: "
            "ADMIN LIVE OLC23: status skilla: edytuj skill ID olc_status (JSON: kind poison/burn/freeze/shock, chance 0.01-1.0; dla poison/burn opcjonalne power_percent 1-200, ticks 1-5); auto cofa status. cele QUEST; celezmien QUEST | JSON_CELOW; nowywielocelowy live_ID | NAZWA | NPC | {\"kill\":{\"bandit\":5},\"collect\":{\"iron_ore\":2},\"talk\":[\"npc_id\"]} | SREBRO | OPIS; zaleznosci QUEST; grupapodglad quest/surowiec/skill/mob/receptura/przedmiot PREFIKS POLE; grupazmien KATEGORIA PREFIKS POLE | WARTOSC; quest requires_quests | [\"id1\",\"id2\"]; status; pokoj ID | poziom | nazwa | opis | region; "
            "polacz OD KIERUNEK DO; potwor ID | poziom | nazwa | HP | obrazenia | EXP; "
            "spawn POKOJ MOB; balans MOB POLE LICZBA; nowyskill live_ID | KLASA | NAZWA | damage/aoe_damage/heal/group_heal/guard/drain/regen/evade/boost | BIEGLOSC | MANA | MULT | SKALA | OPIS [| EFFECT]; quest ID; questy PROFESJA [STRONA]; edytuj skill ID POLE [| WARTOSC/auto]; katalog KATEGORIA [FRAZA] [STRONA]; pola KATEGORIA ID; wczytaj; sprawdz; aktywuj POTWIERDZAM; "
            "edytuj KATEGORIA ID POLE (pokaż obecną wartość i gotową komendę); "
            "edytuj KATEGORIA ID POLE | NOWA_WARTOSC (przygotuj zmianę); "
            "quest: reward_xp, xp_profesji, xp_narzedzia, reward_class_xp, reward_soul_xp, reward_stat_xp (liczba lub auto), needed, target, kind, reward_items, repeatable, repeat_cooldown, requires_quests, min_profession_level, min_tool_level; "
            "surowiec ID; surowiec: prof_fixed, tool_fixed, prof_scale, tool_scale, prof_mode, tool_mode=auto/manual/percent; wyczysc surowiec ID; "
            "OLC4: mob live_ID boss | true (nowy boss); mob ID olc_boss_phases (JSON 3–5 faz), olc_boss_tactic_element, olc_boss_tactic_interval lub auto; sklep ID inventory (lista JSON); receptura: stations, output, quantity; NPC: room, quest, shopkeeper; potwór: silver, gold, mithril, damage_type; "
            "nowyquest live_ID | NAZWA | NPC | kill/collect | CEL | LICZBA | SREBRO | OPIS; lancuch QUEST POPRZEDNI; kopiujrecepture live_ID | ID_RECEPTURY | NAZWA; nowabizuteria live_ID | NAZWA | ring | strength | 50 | 40 | 2500 | OPIS; audyt; nowyprzedmiot live_ID | armor/consumable/craft_material | NAZWA | OPIS | SLOT/heal/- | MOC | CENA; porownaj [limit]; wczytaj [plik.json]; eksport [plik.json]; "
            "nowyquestzestaw live_ID | NAZWA | NPC | {\"iron_ore\":3,\"copper_ore\":2} | SREBRO | OPIS; "
            "nowyekwipunek live_ID | NAZWA | SLOT | OBRONA | ATAK | JSON_STATYSTYK | POZIOM | CENA | OPIS; "
            "balansgrupa PREFIKS_ID max_hp/damage/EXP KWOTA (1–100 mobów); "
            "bonusprofesje 80/auto; bonusnarzedzia 80/auto; mozliwosci; "
            "OLC8: questmaterialy QUEST | JSON; nowamagiaeq ID | NAZWA | SLOT | DEF | ATK | MAGIC_ATK | MAGIC_DEF | WEAPON_POWER | JSON_STATYSTYK | LVL | CENA | OPIS; "
            "respawngrupa PREFIKS SEKUNDY; recepturyprof PROFESJA [STRONA]; panel KATEGORIA ID; "
            "OLC18/v21: strategie fazowe bossa JSON faz 0-5: olc_boss_phase_tactic_intervals, olc_boss_phase_guardian_intervals, olc_boss_phase_guard_thresholds, olc_boss_phase_support_intervals, olc_boss_phase_support_durations, olc_boss_phase_support_priorities (weakest/strongest), olc_boss_phase_rally_hp_thresholds, olc_boss_phase_rally_intervals, olc_boss_phase_rally_durations; auto cofa. OLC17: mob olc_boss_guardian_hp_threshold 1-100, olc_boss_rally_hp_threshold 5-95; mob olc_boss_guardian_phase_roles i olc_boss_phase_element_cycles jako JSON faz 0-5; auto przywraca domyslne. "
            "OLC10: nowyskill boost z EFFECT 1.01-1.90 to pasywna premia po nauczeniu (mana=0, cooldown=0); mob olc_boss_support_priority weakest/strongest. "
            "OLC9: nowyskill ... | EFFECT/- | ELEMENT/- | COOLDOWN (0-3600); edytuj skill live_ID cooldown | 120; boss olc_boss_element_cycle | [\"fire\",\"ice\"]; nowareceptura live_ID | NAZWA | PROFESJA | NARZEDZIE | PRODUKT | JSON_MATERIALOW | STACJA | POZIOM | ILOSC | OPIS; "
            "npc ID olc_dialogue_after_quest | {\"quest_id\":\"ID\",\"text\":\"Tekst\"}; npc olc_dialogue_after_quests | {\"quests\":[\"id1\",\"id2\"],\"text\":\"Tekst\"}; nowyskill ... | EFFECT/- | ZYWIOŁ. "
            "OLC22: edytuj mob ID olc_ancient_phases | [{hp_percent,name,attack_percent,element,duration_seconds} x3] dla v500; "
            "edytuj przywolanie Druid role/ability/bonus_percent | WARTOSC; "
            "edytuj swiat global combat_xp_bonus_percent/event_cycle_minutes/event_order | WARTOSC; "
            "world_bonus obejmuje zwykłe nagrody, nie UOSS source_xp_exact; auto cofa. "
            "OLC23: olc23, kalendarz 8, edytuj swiat global multi_cap_bonus_percent, multi_cap_category_bonus, multi_cap_all_owned_classes, event_offset_minutes; edytuj przywolanie Mag tactic_interval, guard_threshold_percent i execute_threshold_percent. "
            "cofnij POTWIERDZAM; anuluj. Nowe identyfikatory zaczynaja sie od live_. "
            "Zmiany widoczne po aktywacji, trwale w SQLite i bez restartu. "
            "Nie przeladowuje kodu Python ani migracji bazy."
        )
        if cmd in ('olc35','olc100','olc103','final35'):
            from systems.live_olc35_finale import help_text
            await self.send(help_text())
            return
        if cmd in ('pakiet35','pakietfinalny'):
            from systems.live_olc35_finale import package
            await self.send(package(service,tail.split('|',1)[-1].strip()))
            return
        if cmd in ('olc34','olc92','olc99','integracja34'):
            from systems.live_olc34_integration import help_text
            await self.send(help_text())
            return
        if cmd in ('pakiet34','pakietintegracji'):
            from systems.live_olc34_integration import package
            await self.send(package(service,tail.split('|',1)[-1].strip()))
            return
        if cmd in ('olc33','olc84','olc91','silnik33'):
            from systems.live_olc33_mechanics import help_text
            await self.send(help_text())
            return
        if cmd in ('pakiet33','pakietmechanik'):
            from systems.live_olc33_mechanics import package
            await self.send(package(service,tail.split('|',1)[-1].strip()))
            return
        if cmd in ('olc32','olc76','olc83','imperium32'):
            from systems.live_olc32_finale import help_text
            await self.send(help_text())
            return
        if cmd in ('pakiet32','pakietfinale'):
            from systems.live_olc32_finale import package
            source=tail.split('|',1)[-1].strip()
            await self.send(package(service,source))
            return
        if cmd in ('olc30','expowiska30','krainy30'):
            await self.send(
                'OLC v30: cztery otwarte regiony Level 401-800 od Korony Swiata: '
                'Szkarłatne Pogranicze 401-500, Kryształowe Bezmiary 501-600, '
                'Otchłań Nieskończoności 601-700, Tron Wieczności 701-800. '
                'Gracz: expowiska polecane, prowadz szkarłatne pogranicze. '
                'Boss UOSS (fazy): admin live edytuj boss29 black_rabite definicja | '
                '{"cycle":3,"extra_damage_percent":180,"phase_threshold_percent":25,"phase_damage_percent":160}. '
                'Nowy przywolany: admin live edytuj summon29 live_wilk_burzy definicja | '
                '{"name":"Wilk Burzy","class":"Druid","mana":120,"kind":"magic",'
                '"power":100,"materials":{},"hp_percent":150,"attack_percent":120}. '
                'Nowe profesje/receptury: admin live pakietfach; nowe skille: pakietskilli; '
                'questy i zakonczenia fabuly: fabula29 ID definicja | '
                '{"text":"Wybor","ending":"Zakonczenie historii"}; '
                'gildia/miasto: gildia29 i swiat29. '
                'Opublikuj: sprawdz, porownaj, aktywuj POTWIERDZAM. '
                'Auto: wycofanie wybranego pola. Tylko obslugiwane przez silnik funkcje; '
                'nowe rodzaje kodu i migracje wymagaja restartu.'
            )
            return
        if cmd in ('olc29','olc68','olc75','imperium29'):
            from systems.live_olc29_creation import help_text
            await self.send(help_text())
            return
        if cmd in ('olc28','olc60','olc67','imperium28'):
            from systems.live_olc28_expansion import help_text
            await self.send(help_text())
            return
        if cmd in ('olc27','olc52','olc59','imperium27'):
            from systems.live_olc27_master import help_text
            await self.send(help_text())
            return
        if cmd in ('olc26','olc44','olc51','imperium26'):
            from systems.live_olc26_world import help_text
            await self.send(help_text())
            return
        if cmd in ('olc25','olc36','olc43','imperium25'):
            from systems.live_olc25_workflows import summary
            await self.send(summary(service))
            return
        if cmd in ('olc24','rewolucja24'):
            await self.send('OLC24: nowafach live_ID | NAZWA | live_TOOL | tool_type | NAZWA_TOOL | POKOJ | CENA | OPIS; edytuj fach live_ID definicja | JSON; '
                'uoss black_rabite lockout_hours/max_hp_percent/damage_percent; '
                'przywolany pajak hp_percent/damage_percent/mana_percent; '
                'capkroki global step_extra_exp | [0,0,500,...]; '
                'event basalt title/boss_name; kontrola global respawn_percent; '
                'fachreceptura live_RECEPTURA | NAZWA | live_PROFESJA | PRODUKT | MATERIALY_JSON | POZIOM | ILOSC | OPIS; '
                'fabula | JSON z quests i npcs; komboskill SKILL | ELEMENT | STATUS_JSON. '
                'Każde pole ma podgląd obecnej wartości oraz auto, sprawdz i aktywuj POTWIERDZAM.')
            return
        if cmd in ('olc23','rozwoj23'):
            await self.send('OLC23: Multi Cap — swiat global multi_cap_bonus_percent 100-1000, '
                            'multi_cap_category_bonus jako JSON kategorii, '
                            'multi_cap_all_owned_classes true/false (archiwalne klasy); '
                            'przywolania — guard_threshold_percent, execute_threshold_percent, tactic_interval; '
                            'nawigacja wydarzeń — swiat global event_offset_minutes 0-719 i admin live kalendarz 8. '
                            'Wpisz admin live edytuj swiat global POLE bez kreski, aby usłyszeć aktualną wartość.')
            return
        if cmd in ('kalendarz','harmonogram'):
            from systems.live_olc23_calendar import event_calendar_lines
            limit = int(tail) if tail else 8
            for line in event_calendar_lines(limit):
                await self.send(line)
            return
        if cmd in ('megaupdate','mega','olc22'):
            # The detailed OLC24 guide is available at admin live olc24.
            await self.send(
                'SOULBOUND v22 OLC19-26: 1 superbossy v500: edytuj mob ID olc_ancient_phases; '
                '2 przywołania 22 klas: edytuj przywolanie Druid role/ability/bonus_percent; '
                '3 profesje, narzędzia i nowe receptury: stare edytory; '
                '4 skille: efekty poison/burn/freeze/shock, AoE, koszt, cooldown; '
                '5 bonus EXP zwykłych potworów: edytuj swiat global combat_xp_bonus_percent; '
                '6 inwazje: edytuj swiat global event_cycle_minutes/event_order; '
                '7 NPC i fabuła: questy wielocelowe, zależności i dialog po questach; '
                '8 świat: pokoje, bezkolizyjne portale/przejścia, sklepy, NPC i respawn. '
                'Każde pole: podgląd obecnej wartości, edytuj ... | WARTOSC, auto, sprawdz, aktywuj POTWIERDZAM; '
                'nie dotyka skryptów UOSS i danych postaci.')
            return
        if cmd == 'mozliwosci':
            await self.send(
                'OLC22: wpisz admin live megaupdate po osiem domen i przykłady. OLC18: 9 fazowych ustawien zwyklych bossow: taktyka, fale pomocnikow, oslona i kontra. Edytuj mob ID olc_boss_phase_tactic_intervals | JSON faz 0-5; auto usuwa. '
                'OLC15: admin live cele QUEST (podgląd), questy wielocelowe kill/collect/talk; do 12 celów, osobny postęp SQLite, nagroda po wszystkich celach. OLC14: do 8 warunków ukończonych questów na zadanie, walidacja cykli; grupowe receptury i przedmioty. '
                'OLC 7.0: skille atak/obszar/leczenie/ochrona/wysysanie/regeneracja/unik/egzekucja; '
                'bossowie zwykli: fazy HP, taktyka żywiołu, odstępy i czas osłony/rally; '
                'questy: kill/collect, zestaw 2–8 surowców, zależności, EXP, odnowienia; '
                'wyposażenie: pancerze i akcesoria z 1–6 statystykami; '
                'profesje: kopiowanie/edycja receptur, surowce i EXP; '
                'balans: pojedyncze i grupowe zmiany mobów; katalog, pola, porownaj, audyt, NEWS, cofnij. '
                'OLC8: żywioły nowych ataków, próg osłony bossów, zestawy surowców questów, magiczny sprzęt, ' 'recepturyprof, respawngrupa, warunkowy dialog NPC, panel. '
                ' OLC9: opcjonalne cooldowny nowych skilli, edycja elementu live skilla, cykl żywiołów zwykłych bossów, nowareceptura. ' 'Dowolne nowe klasy i wykonywalne skrypty superbossów nadal wymagają zmian silnika; nowe profesje i receptury obsługuje nowafach/fachreceptura/pakietfach.'
            )
            return
        if cmd in ('cele', 'wielocele'):
            from systems.live_olc18_multi_objective import describe_goals
            from data.quests import QUESTS
            await self.send(describe_goals(service, tail, QUESTS))
            return
        if cmd in ('', 'help', 'pomoc'):
            await self.send(help_text)
            return
        read_only_preview = False
        try:
            if cmd == 'pakiet29':
                from systems.live_olc29_creation import package
                await self.send(package(service,tail.partition('|')[2].strip() if '|' in tail else tail))
                return
            if cmd == 'pakietskilli':
                from systems.live_olc25_workflows import bundle_new_skills
                await self.send(bundle_new_skills(service,tail.partition('|')[2].strip() if '|' in tail else tail))
                return
            if cmd == 'pakietfach':
                from systems.live_olc25_workflows import profession_package
                await self.send(profession_package(service,tail))
                return
            if cmd == 'pakietzmian':
                from systems.live_olc25_workflows import batch
                category,sep,changes = tail.partition('|')
                if not sep: raise ValueError('pakietzmian SKILLE | JSON')
                await self.send(batch(service, category.strip().casefold(),changes.strip()))
                return
            if cmd == 'nowafach':
                parts=[x.strip() for x in tail.split('|')]
                if len(parts)!=8:
                    raise ValueError('Użycie: admin live nowafach live_ID | NAZWA_PROFESJI | live_ID_NARZEDZIA | TOOL_TYPE | NAZWA_NARZEDZIA | ID_POKOJU | CENA_SREBRO | OPIS')
                await self.send(service.stage_new_profession_and_tool_v2400(*parts))
                return
            if cmd == 'fachreceptura':
                parts=[x.strip() for x in tail.split('|',7)]
                if len(parts)!=8:
                    raise ValueError('Użycie: admin live fachreceptura live_ID | NAZWA | live_ID_PROFESJI | ID_PRODUKTU | JSON_MATERIAŁY | POZIOM | ILOŚĆ | OPIS')
                await self.send(service.stage_new_profession_recipe_v2400(*parts))
                return
            if cmd == 'fabula':
                read_only_preview=False
                from systems.live_olc24_revolution import stage_story_arc
                await self.send(stage_story_arc(service,tail))
                return
            if cmd == 'komboskill':
                read_only_preview=False
                from systems.live_olc24_revolution import stage_skill_combo
                parts=[x.strip() for x in tail.split('|',2)]
                if len(parts)!=3: raise ValueError('Użycie: admin live komboskill SKILL_ID | fire | {"status":"burn",...}')
                skill_id,element,status=parts
                await self.send(stage_skill_combo(service,skill_id,element,status))
                return
            if cmd in ('porownaj', 'diff', 'zmiany'):
                read_only_preview = True
                from systems.live_olc4_diff import describe_diff
                limit = int(tail) if tail else 15
                await self.send(describe_diff(service.active, service.draft, limit=limit))
                return
            if cmd in ('zaleznosci', 'wymaganiaquest'):
                read_only_preview = True
                from data.quests import QUESTS
                from systems.live_olc17_quest_dependencies import describe_quest_dependencies
                if not tail or len(tail.split()) != 1:
                    raise ValueError('Użycie: admin live zaleznosci bandit_patrol')
                await self.send(describe_quest_dependencies(service, tail, QUESTS))
                return
            if cmd in ('panel', 'szczegoly'):
                read_only_preview = True
                from systems.live_olc8_dashboard import describe_object
                bits = tail.split(maxsplit=1)
                if len(bits) != 2:
                    raise ValueError('Użycie: admin live panel quest bandit_patrol')
                await self.send(describe_object(service, bits[0], bits[1]))
                return
            if cmd == 'recepturyprof':
                read_only_preview = True
                from systems.live_olc8_dashboard import profession_recipes
                await self.send(profession_recipes(service, tail))
                return
            if cmd in ('pola','fields') and tail.strip() and tail.split(maxsplit=1)[0] in ('boss32','uoss32','fach32','profesja32','summon32','przywolanie32','skill32','magia32','event32','wydarzenie32','fabula32','quest32','gildia32','frakcja32','swiat32','warsztat32'):
                from systems.live_olc32_finale import help_text
                await self.send(help_text())
                return
            if cmd in ('pola','fields') and tail.strip() and tail.split(maxsplit=1)[0] in ('boss29','uoss29','fach29','praca29','summon29','przywolany29','skill29','magia29','event29','wydarzenie29','fabula29','wybor29','gildia29','frakcja29','swiat29','ekonomia29'):
                from systems.live_olc29_creation import help_text
                await self.send(help_text())
                return
            if cmd in ('pola','fields') and tail.strip() and tail.split(maxsplit=1)[0] in ('uoss28','boss28','fach28','rzemioslo28','summon28','przywolany28','skill28','magia28','event28','wydarzenie28','fabula28','quest28','gildia28','frakcja28','ekonomia28','swiat28'):
                from systems.live_olc28_expansion import help_text
                await self.send(help_text())
                return
            if cmd in ('pola','fields') and tail.strip() and tail.split(maxsplit=1)[0] in ('uoss27','boss27','fach27','prof27','summon27','przywolany27','magia27','skill27','event27','wydarzenie27','fabula27','quest27','frakcja27','sklep27'):
                from systems.live_olc27_master import help_text
                await self.send(help_text())
                return
            if cmd in ('pola','fields') and tail.strip() and tail.split(maxsplit=1)[0] in ('uoss26','boss26','fach26','summon26','przywolany26','event26','wybor26','frakcja26','ekonomia26'):
                from systems.live_olc26_world import help_text
                await self.send(help_text())
                return
            if cmd in ('pola','fields') and tail.strip() and tail.split(maxsplit=1)[0] in ('fach','nowaprofesja','uoss','superboss','przywolany','summontyp','capkroki','event','wydarzenie','kontrola','swiat24'):
                domain=tail.split(maxsplit=1)[0]
                from systems.live_olc24_revolution import UOSS_FIELDS, SUMMON_FIELDS as SUMMON24_FIELDS, EVENT_FIELDS, WORLD_FIELDS as WORLD24_FIELDS
                field_sets={'fach':'definicja','nowaprofesja':'definicja',
                    'uoss':', '.join(sorted(UOSS_FIELDS)), 'superboss':', '.join(sorted(UOSS_FIELDS)),
                    'przywolany':', '.join(sorted(SUMMON24_FIELDS)), 'summontyp':', '.join(sorted(SUMMON24_FIELDS)),
                    'capkroki':'step_extra_exp (1–80 przedziałów)', 'event':', '.join(sorted(EVENT_FIELDS)),
                    'wydarzenie':', '.join(sorted(EVENT_FIELDS)),
                    'kontrola':', '.join(sorted(WORLD24_FIELDS)), 'swiat24':', '.join(sorted(WORLD24_FIELDS))}
                await self.send('OLC24 pola '+domain+': '+field_sets[domain]+'.')
                return
            if cmd in ('pola', 'fields') and tail.strip() and tail.split(maxsplit=1)[0] in ('przywolanie','summon','swiat','world'):
                bits=tail.split()
                if len(bits)!=2: raise ValueError('Użycie: admin live pola przywolanie Druid / swiat global')
                from systems.summon_ai_v1200 import CLASS_AI
                from systems.live_olc22_empire import SUMMON_FIELDS, WORLD_FIELDS
                if bits[0] in ('przywolanie','summon'):
                    if bits[1] not in CLASS_AI: raise ValueError('Nieznana klasa.')
                    keys=SUMMON_FIELDS
                else:
                    if bits[1]!='global': raise ValueError('Wpisz swiat global.')
                    keys=WORLD_FIELDS
                await self.send('OLC23 dostępne pola: '+', '.join(sorted(keys))+'. Podgląd: admin live edytuj '+tail+' POLE')
                return
            if cmd in ('katalog', 'catalog') and tail.strip() in ('przywolanie','summon','swiat','world'):
                from systems.summon_ai_v1200 import CLASS_AI
                await self.send('OLC22: '+(', '.join(sorted(CLASS_AI)) if tail.strip() in ('przywolanie','summon') else 'global'))
                return
            if cmd in ('pola', 'fields'):
                from systems.live_olc4_browse import fields_for
                words = tail.split()
                if len(words) != 2:
                    raise ValueError('Użycie: admin live pola quest bandit_patrol')
                await self.send(fields_for(service, *words))
                return
            if cmd in ('katalog', 'catalog'):
                from systems.live_olc4_browse import find_catalog
                words = tail.split()
                if not words:
                    raise ValueError('Użycie: admin live katalog mob bandit [strona]')
                category = words.pop(0)
                page = int(words.pop()) if words and words[-1].isdigit() else 1
                await self.send(find_catalog(service, category, ' '.join(words), page))
                return
            if cmd in ('questy', 'zadania'):
                from data.quests import QUESTS
                from systems.live_quest_olc_v1209 import profession_quest_ids
                bits = tail.split()
                page = 1
                if bits and bits[-1].isdigit():
                    page = int(bits.pop())
                if page < 1 or page > 100000:
                    raise ValueError('Strona listy musi być dodatnia.')
                profession = ' '.join(bits).strip()
                if not profession:
                    raise ValueError('Użycie: admin live questy Wedkarstwo [strona].')
                found = profession_quest_ids(QUESTS, profession)
                page_size = 12
                pages = max(1, (len(found) + page_size - 1) // page_size)
                if page > pages:
                    raise ValueError(f'Nie ma strony {page}. Dostępnych stron: {pages}.')
                show = found[(page - 1) * page_size: page * page_size]
                await self.send(f'OLC questy {profession}: {len(found)} zadań, strona {page}/{pages}. '
                                + ('; '.join(f'{qid} ({str(QUESTS[qid].get("name", qid))[:55]})' for qid in show)
                                   if show else 'Brak zadań.'))
                return
            if cmd in ('quest', 'zadanie'):
                from data.quests import QUESTS
                definition = QUESTS.get(tail)
                if not definition:
                    raise ValueError('Nieznany quest. Podaj dokładne ID, np. bandit_patrol.')
                active = service.active['quest_edits'].get(tail, {})
                draft = service.draft['quest_edits'].get(tail, {})
                from core.progression_resources import (v0270_quest_character_reward,
                     v0522_combat_quest_class_reward, v0522_is_profession_quest, v0190_quest_soul_reward)
                from core.progression_resources import v0190_quest_stat_reward
                auto_char = v0270_quest_character_reward(definition)
                auto_stat = v0190_quest_stat_reward(definition)
                from systems.quest_combat_salvage_v102007 import class_xp_at_turnin, soul_xp_at_turnin, is_combat_salvage_quest
                auto_class = class_xp_at_turnin(definition, v0522_combat_quest_class_reward(definition), tail)
                auto_soul = soul_xp_at_turnin(definition, v0190_quest_soul_reward(definition), tail)
                def xp_view(field, generated):
                    if field in active:
                        return f'{active[field]} (ręczny)'
                    return f'{generated} (automatyczny)'
                await self.send(
                    f'OLC QUEST {tail}: {definition.get("name", tail)}. '
                    f'Typ: {definition.get("kind", "?")}; cel: {definition.get("target", "?")}; '
                    f'wymagane: {definition.get("needed", "?")}. '
                    f'EXP postaci: {xp_view("olc_reward_xp", auto_char)}; '
                    f'EXP biegłości: {xp_view("olc_reward_class_xp", auto_class)}; '
                    f'EXP statystyk: {xp_view("olc_reward_stat_xp", auto_stat)}; '
                    f'EXP Duszy: {xp_view("olc_reward_soul_xp", auto_soul) if not v0522_is_profession_quest(definition) or is_combat_salvage_quest(definition, tail) else "0 (quest profesyjny)"}; '
                    f'EXP profesji bazowe: {definition.get("reward_profession_xp", 0)}; '
                    f'EXP narzędzia bazowe: {definition.get("reward_tool_xp", 0)}; '
                    f'Odnowienie: {definition.get("repeat_cooldown", "domyślne")} s; '
                    f'Powtarzalny: {definition.get("repeatable", False)}. '
                    f'Poziom profesji (informacyjny): {definition.get("min_profession_level", "brak")}; '
                    f'Poziom narzędzia (informacyjny): {definition.get("min_tool_level", "brak")}; '
                    f'aktywne nadpisania: {active or "brak"}; robocze: {draft or "brak"}. '
                    'Wartości bazowe przed premiami, skalowaniem i EXP Bank.')
                return
            if cmd == 'surowiec':
                from data.items import ITEMS
                item = ITEMS.get(tail)
                if not item or item.get('type') not in (
                        'resource', 'material', 'craft_material', 'gem_raw', 'archaeology_find'):
                    raise ValueError('Podaj istniejący identyfikator surowca, np. iron_ore.')
                active = service.active['resource_edits'].get(tail, {})
                draft = service.draft['resource_edits'].get(tail, {})
                await self.send(f'HOT RELOAD SUROWIEC {tail}: {item["name"]}. '
                                f'Aktywne: {active or "automatyczny EXP"}; '
                                f'przygotowane: {draft or "automatyczny EXP"}. '
                                'prof_fixed/tool_fixed = ręczne EXP bazowe (także 0); '
                                'prof_scale/tool_scale = 0–1000% bazowego EXP; '
                                'prof_mode/tool_mode = auto/manual/percent. '
                                'Stare prof_xp/tool_xp nadal są minimami. '
                                'Ostateczne EXP zależy od poziomu i premii.')
                return
            if cmd == 'wyczysc':
                what = tail.split()
                if len(what) != 2 or what[0] not in ('surowiec', 'resource'):
                    raise ValueError('Użycie: admin live wyczysc surowiec iron_ore')
                service.stage_clear_resource(what[1])
                await self.send('HOT RELOAD: usunięto ustawienie z wersji roboczej. '
                                'Aby opublikować: admin live aktywuj POTWIERDZAM.')
                return
            if cmd in ('wczytaj', 'import'):
                from pathlib import Path
                import re
                filename = tail or 'nowe_lokacje.json'
                if not re.fullmatch(r'[a-zA-Z0-9_-]{1,70}\.json', filename):
                    raise ValueError('Nazwa pliku: litery, cyfry, _, - oraz .json; bez katalogów.')
                incoming = Path(__file__).resolve().parents[2] / 'LIVE_CONTENT' / filename
                result = service.stage_file(incoming)
                await self.send('HOT RELOAD: wczytano pakiet JSON: '+result+'. ' 
                                'Sprawdź admin live sprawdz, następnie aktywuj POTWIERDZAM.')
                return
            if cmd == 'eksport':
                from pathlib import Path
                import re
                filename = tail or 'pakiet_olc.json'
                if not re.fullmatch(r'[a-zA-Z0-9_-]{1,70}\.json', filename):
                    raise ValueError('Nazwa pliku JSON bez katalogów i znaków specjalnych.')
                dest = Path(__file__).resolve().parents[2] / 'LIVE_CONTENT' / filename
                service.export(dest, draft=True)
                await self.send(f'HOT RELOAD: wyeksportowano roboczy pakiet do LIVE_CONTENT/{filename}.')
                return
            if cmd == 'audyt':
                read_only_preview = True
                from systems.live_olc5_audit import live_audit_summary
                await self.send(live_audit_summary(service))
                return
            if cmd in ('status', 'sprawdz'):
                await self.send(f"HOT RELOAD: aktywna rewizja {service.revision}: {service.validate(service.active)}. "
                                f"Przygotowane: {service.validate(service.draft)}.")
                return
            if cmd in ('anuluj', 'cancel'):
                service.reset_draft()
                await self.send("HOT RELOAD: anulowano niezatwierdzone zmiany.")
                return
            if cmd == 'expprogi':
                # Bulk action validates a copy of DRAFT before swapping it in.
                # A rejected parameter must NOT delete the admin's older edits.
                read_only_preview = True  # Keep pre-existing DRAFT on errors.
                from systems.admin_live_quest_xp_threshold_v1 import preview as xp_preview, stage as xp_stage
                bits = tail.split()
                if len(bits) == 3 and bits[0] == 'podglad':
                    await self.send(xp_preview(service, bits[1], bits[2]))
                elif len(bits) == 4 and bits[0] == 'ustaw':
                    await self.send(xp_stage(service, bits[1], bits[2], bits[3]))
                else:
                    await self.send('EXPPROGI: admin live expprogi podglad xp_statystyk 1000; '
                                    'admin live expprogi ustaw xp_statystyk 1000 25000; '
                                    'pola: xp_postaci, xp_bieglosci, xp_duszy, xp_statystyk, '
                                    'xp_profesji, xp_narzedzia, xp_sila, xp_zrecznosc, '
                                    'xp_kondycja, xp_inteligencja, xp_wola, xp_charyzma, wszystkie. '
                                    'Zero pomijane, zmiany trafiaja do DRAFT.')
                return
            if cmd in ('grupapodglad', 'grupazmien'):
                from systems.live_olc13_batch import preview as batch_preview, stage as batch_stage
                if cmd == 'grupapodglad':
                    bits = tail.split()
                    if len(bits) != 3:
                        raise ValueError('Użycie: admin live grupapodglad quest bandit_ reward_xp')
                    read_only_preview = True
                    await self.send(batch_preview(service, *bits))
                else:
                    head, separator, value = tail.partition('|')
                    bits = head.strip().split()
                    if not separator or len(bits) != 3:
                        raise ValueError('Użycie: admin live grupazmien quest bandit_ reward_xp | 50000')
                    await self.send(batch_stage(service, *bits, value.strip()))
                return
            if cmd in ('edytuj', 'edit'):
                args2 = tail.split(maxsplit=3)
                if len(args2) == 3:
                    read_only_preview = True
                    from systems.live_olc35_finale import preview as preview35
                    result35=preview35(service,*args2)
                    if result35 is not None:
                        await self.send(result35)
                        return
                    from systems.live_olc34_integration import preview as preview34
                    result34=preview34(service,*args2)
                    if result34 is not None:
                        await self.send(result34)
                        return
                    from systems.live_olc33_mechanics import preview as preview33
                    result33=preview33(service,*args2)
                    if result33 is not None:
                        await self.send(result33)
                        return
                    from systems.live_olc32_finale import preview as preview32
                    result32=preview32(service,*args2)
                    if result32 is not None:
                        await self.send(result32)
                    else:
                        from systems.live_olc29_creation import preview as preview29
                        result29=preview29(service,*args2)
                        if result29 is not None:
                            await self.send(result29)
                        else:
                            from systems.live_olc_preview_v12010 import describe_current_edit
                            await self.send(describe_current_edit(service,*args2))
                    return  # Tylko odczyt: bez zmiany wersji roboczej i bez NEWS.
                if len(args2) != 4:
                    raise ValueError('Użycie: admin live edytuj quest bandit_patrol reward_gold | 100 (lub reward_gold 100).')
                section, key, field, value = args2
                if '|' in value:
                    raw_value = value.split('|', 1)[1].strip()
                elif (section.casefold() in ('quest', 'zadanie')
                      and field.casefold() in ('reward_silver', 'reward_gold', 'reward_mithril')
                      and value.strip().isdecimal()):
                    # Accessible short form: admin live edytuj quest ID reward_gold 100.
                    # Keep explicit | delimiter mandatory for free-form text/JSON.
                    raw_value = value.strip()
                else:
                    raise ValueError('Użycie: admin live edytuj quest bandit_patrol reward_gold | 100 (lub reward_gold 100).')
                service.stage_edit(section.lower(), key, field.lower(), raw_value)
            elif cmd in ('nowyskill', 'nowaumiejetnosc'):
                parts = [x.strip() for x in tail.split('|')]
                if len(parts) not in (9, 10, 11, 12):
                    raise ValueError('Użycie: admin live nowyskill live_id | Wojownik | Nazwa | damage | 40 | 20 | 1.0 | strength | Opis | EFFECT/- | fire')
                sid, class_name, name, kind, unlock, mana, mult, scale, description = parts[:9]
                effect = parts[9] if len(parts) >= 10 and parts[9] not in ('-', '') else None
                element = parts[10] if len(parts) >= 11 and parts[10] not in ('-', '') else None
                cooldown = parts[11] if len(parts) == 12 else 0
                service.stage_new_skill(sid, class_name, name, kind, unlock, mana,
                                        mult, scale, description, effect, element, cooldown)
            elif cmd in ('nowareceptura', 'nowyprzepis'):
                args = [v.strip() for v in tail.split('|')]
                if len(args) != 10:
                    raise ValueError('Użycie: admin live nowareceptura live_ID | Nazwa | Profesja | ID_NARZEDZIA | ID_PRODUKTU | JSON_MATERIALOW | ID_STACJI | POZIOM | ILOSC | Opis')
                service.stage_new_recipe(*args)
            elif cmd == 'questmaterialy':
                bits = [v.strip() for v in tail.split('|', 1)]
                if len(bits) != 2:
                    raise ValueError('Użycie: admin live questmaterialy QUEST_ID | {"iron_ore":2,"copper_ore":3}')
                service.stage_quest_materials(*bits)
            elif cmd == 'nowamagiaeq':
                bits = [v.strip() for v in tail.split('|')]
                if len(bits) != 12:
                    raise ValueError('Użycie: admin live nowamagiaeq live_ID | Nazwa | slot | obrona | atak | magic_attack | magic_defense | weapon_power | JSON_STATS | level | cena | opis')
                service.stage_magic_equipment(*bits)
            elif cmd == 'respawngrupa':
                bits = tail.split()
                if len(bits) != 2:
                    raise ValueError('Użycie: admin live respawngrupa PREFIKS SEKUNDY')
                service.stage_respawn_group(*bits)
            elif cmd in ('nowyekwipunek', 'nowazbroja'):
                bits = [v.strip() for v in tail.split('|')]
                if len(bits) != 9:
                    raise ValueError('Użycie: admin live nowyekwipunek live_ID | NAZWA | SLOT | OBRONA | ATAK | JSON_STATYSTYK | POZIOM | CENA | OPIS')
                service.stage_new_equipment(*bits)
            elif cmd in ('celezmien', 'zmiencele'):
                bits = [v.strip() for v in tail.split('|', 1)]
                if len(bits) != 2 or not all(bits):
                    raise ValueError('Użycie: admin live celezmien ID_QUESTA | JSON_CELOW')
                service.stage_change_multi_objectives_v1800(*bits)
            elif cmd in ('nowywielocelowy', 'questwielecelow'):
                bits = [v.strip() for v in tail.split('|')]
                if len(bits) != 6:
                    raise ValueError('Użycie: admin live nowywielocelowy live_ID | NAZWA | NPC | JSON_CELOW | SREBRO | OPIS')
                service.stage_new_multi_objective_quest_v1800(*bits)
            elif cmd in ('nowyquestzestaw', 'questzestaw'):
                bits = [v.strip() for v in tail.split('|')]
                if len(bits) != 6:
                    raise ValueError('Użycie: admin live nowyquestzestaw live_ID | NAZWA | NPC | JSON_SUROWCÓW | SREBRO | OPIS')
                service.stage_new_resource_set_quest(*bits)
            elif cmd in ('nowyprzedmiot', 'nowyitem'):
                parts = [x.strip() for x in tail.split('|')]
                if len(parts) != 7:
                    raise ValueError('Użycie: admin live nowyprzedmiot live_id | armor | Nazwa | Opis | body | 100 | 500')
                service.stage_new_item(*parts)
            elif cmd in ('nowyquest', 'nowezadanie'):
                parts = [x.strip() for x in tail.split('|')]
                if len(parts) != 8:
                    raise ValueError('Użycie: admin live nowyquest live_id | Nazwa | NPC | kill | mob_id | 10 | 500 | Opis')
                qid, name, giver, kind, target, needed, silver, description = parts
                service.stage_new_quest(qid, name, giver, kind, target, needed, silver, description)
            elif cmd == 'nowabizuteria':
                bits = [v.strip() for v in tail.split('|')]
                if len(bits) != 8:
                    raise ValueError('Użycie: admin live nowabizuteria live_ID | Nazwa | ring | strength | 50 | 40 | 2500 | Opis')
                service.stage_new_jewelry(*bits)
            elif cmd in ('lancuch', 'łańcuch'):
                bits = tail.split()
                if len(bits) != 2:
                    raise ValueError('Użycie: admin live lancuch ID_QUESTA ID_POPRZEDNIEGO_QUESTA')
                service.stage_quest_chain(*bits)
            elif cmd == 'kopiujrecepture':
                bits = [v.strip() for v in tail.split('|')]
                if len(bits) != 3:
                    raise ValueError('Użycie: admin live kopiujrecepture live_id | istniejaca_receptura | Nowa nazwa')
                service.stage_copy_recipe(*bits)
            elif cmd == 'pokoj':
                fields = [x.strip() for x in tail.split('|')]
                if len(fields) != 5:
                    raise ValueError("Uzycie: admin live pokoj live_id | 80 | Nazwa | Opis | Region")
                rid, level, name, desc, zone = fields
                level = int(level)
                service.stage_room(rid, level, name, desc, zone)
            elif cmd in ('polacz', 'przejscie'):
                fields = tail.split()
                if len(fields) != 3:
                    raise ValueError('Uzycie: admin live polacz OD KIERUNEK DO')
                service.stage_link(*fields)
            elif cmd == 'potwor':
                fields = [x.strip() for x in tail.split('|')]
                if len(fields) != 6:
                    raise ValueError('Uzycie: admin live potwor live_id | 80 | Nazwa | 50000 | 500 | 10000')
                mid, level, name, hp, damage, exp = fields
                service.stage_mob(mid, name, int(level), int(hp), int(damage), int(exp))
            elif cmd == 'spawn':
                fields = tail.split()
                if len(fields) != 2:
                    raise ValueError('Uzycie: admin live spawn POKOJ MOB')
                service.stage_spawn(*fields)
            elif cmd in ('bonusprofesje', 'bonusnarzedzia'):
                if not tail:
                    raise ValueError('Użycie: admin live bonusprofesje 80 (lub auto).')
                service.stage_progression_group('profesje' if cmd == 'bonusprofesje' else 'narzedzia', tail)
            elif cmd == 'balansgrupa':
                bits = tail.split()
                if len(bits) != 3:
                    raise ValueError('Użycie: admin live balansgrupa PREFIKS_ID max_hp|damage|class_xp_reward LICZBA')
                service.stage_balance_group(bits[0], bits[1], bits[2])
            elif cmd == 'balans':
                fields = tail.split()
                if len(fields) != 3:
                    raise ValueError('Uzycie: admin live balans MOB max_hp|damage|class_xp_reward|soul_reward|stat_reward LICZBA')
                service.stage_balance(fields[0], fields[1], int(fields[2]))
            elif cmd in ('aktywuj', 'zastosuj'):
                if tail != 'POTWIERDZAM':
                    raise ValueError('Potwierdzenie: admin live aktywuj POTWIERDZAM')
                login = self.server.db.account_name(self.master_account_id)
                previous = service.active
                outcome = service.apply(self.server, login)
                self.server.db.record_admin_action_v1224(login, 'live_activate_v1204', str(service.revision))
                await self.send('HOT RELOAD: '+outcome)
                if outcome != 'Nie ma nowych zmian.':
                    await self.news_channel_v1204(service.describe_news(previous))
                return
            elif cmd == 'cofnij':
                if tail != 'POTWIERDZAM':
                    raise ValueError('Potwierdzenie: admin live cofnij POTWIERDZAM')
                login = self.server.db.account_name(self.master_account_id)
                previous = service.active
                outcome = service.apply(self.server, login, rollback=True)
                self.server.db.record_admin_action_v1224(login, 'live_rollback_v1204', str(service.revision))
                await self.send('HOT RELOAD: '+outcome)
                if outcome != 'Nie ma nowych zmian.':
                    await self.news_channel_v1204(service.describe_news(previous, rollback=True))
                return
            else:
                await self.send(help_text)
                return
            await self.send('HOT RELOAD: przygotowano zmianę; '+service.validate(service.draft)+'. ' 
                            'Uzyj admin live sprawdz, potem admin live aktywuj POTWIERDZAM.')
        except (ValueError, TypeError, OverflowError) as exc:
            if not read_only_preview:
                service.reset_draft()
            ending = 'Wersja robocza bez zmian.' if read_only_preview else 'Zmiany robocze anulowano.'
            await self.send(f'HOT RELOAD: odrzucono zmianę: {exc}. {ending}')

    async def prepare_character_wipe(self):
            """Wyczyść stan sesyjny bez zapisywania usuwanej postaci."""
            if self.guide_task_active():
                await self.cancel_guide(announce=False)
            for task_name in ("rest_task", "auto_fishing_task", "auto_mining_task", "auto_woodcutting_task", "auto_herbalism_task", "combat_task"):
                task = getattr(self, task_name, None)
                if task and not task.done():
                    task.cancel()
                setattr(self, task_name, None)
            self.resting = False
            self.auto_fishing = self.auto_mining = self.auto_woodcutting = self.auto_herbalism = False
            if self.character:
                await self.leave_party(announce=False)
            self.combat_mob_key = None
            self.account_id = None
            self.character = None
            self.current_hp = 0
            self.current_mana = 0

    async def admin_error_cleanup_shortcut_v1405(self, args=""):
            """Short form: wyczysc naprawione POTWIERDZAM, never character wipe."""
            norm = self.normalize_description_query(args)
            if norm not in (
                "naprawione potwierdzam", "naprawione confirm",
                "wyczysc naprawione potwierdzam", "wyczysc naprawione confirm",
                "wyczyść naprawione potwierdzam", "wyczyść naprawione confirm",
            ):
                await self.send(
                    "Czyszczenie zgłoszeń: wyczysc naprawione POTWIERDZAM "
                    "albo admin log wyczysc naprawione POTWIERDZAM. "
                    "Usuwane są tylko błędy oznaczone jako naprawione."
                )
                return
            # Shared audited implementation; keeps active SB errors and all characters.
            await self.admin_tools_v1224("log wyczysc naprawione POTWIERDZAM")

    async def wipe_command(self, args=""):
            if not self.is_admin():
                await self.send("Nieznana komenda. Wpisz help.")
                return
            norm = self.normalize_description_query(args)
            if norm.startswith("naprawione"):
                await self.admin_error_cleanup_shortcut_v1405(norm)
                return
            own_tokens = ("moje postacie", "my characters")
            all_tokens = ("wszystkie postacie", "all characters")
            confirmed_pl = norm.endswith(" potwierdzam")
            confirmed_en = norm.endswith(" confirm")
            if not (confirmed_pl or confirmed_en):
                await self.send(
                    "WIPE wymaga potwierdzenia. Konta NIE zostaną usunięte. "
                    "Użyj: wipe moje postacie POTWIERDZAM albo wipe wszystkie postacie POTWIERDZAM."
                )
                return
            scope = norm.rsplit(" ", 1)[0]
            if scope not in own_tokens + all_tokens:
                await self.send("Nieprawidłowy zakres wipe.")
                return

            if scope in own_tokens:
                target_masters = {int(self.master_account_id)}
            else:
                target_masters = {
                    int(row["id"])
                    for row in self.server.db.conn.execute(
                        "SELECT id FROM accounts WHERE id NOT IN ("
                        "SELECT character_account_id FROM account_characters "
                        "WHERE character_account_id<>master_account_id)"
                    ).fetchall()
                }

            # Inne aktywne sesje z wipe zostają rozłączone bez zapisu usuwanej postaci.
            for session in list(self.server.sessions):
                if session is self or session.master_account_id not in target_masters:
                    continue
                try:
                    await session.send("ADMIN WIPE: postacie zostały wyczyszczone. Konto pozostaje. Połącz się ponownie.")
                    await session.prepare_character_wipe()
                    session.closed = True
                    session.writer.close()
                except Exception:  # AUDIT_INTENTIONAL_PASS: target session may already be disconnected during wipe
                    pass

            await self.prepare_character_wipe()
            if scope in own_tokens:
                removed = self.server.db.wipe_characters_for_master(self.master_account_id)
            else:
                removed, _masters = self.server.db.wipe_all_characters_preserve_accounts()
            # Wipe składu drużyn to tylko stan sesyjny.
            self.server.parties.clear()
            self.server.party_invites.clear()
            self.server.party_protectors.clear()
            self.server.party_goals.clear()
            self.server.party_routes_v1193.clear()
            self.server.party_ready_checks.clear()
            await self.send(f"WIPE POSTACI zakończony. Usunięto postaci: {removed}. Konta i hasła zachowane.")
            selected = await self.character_selection_flow()
            if selected is True:
                await self.enter_world()

    def boss_floor_chest_here(self):
            if not self.character:
                return None
            spec = _boss_floor_chest_spec(self.character.room_id)
            if not spec:
                return None
            kind, floor, _power = spec
            state_id = boss_floor_chest_state_id(kind, floor)
            opened = state_id in self.server.db.collection_entry_ids(
                self.account_id, BOSS_CHEST_OPENED_CATEGORY_V11332
            )
            if opened:
                # v1.28.8: Previously opened chest markers lived forever if a
                # player came back AFTER the boss had respawned. The chest
                # should already stand beside the living boss; the new key
                # still drops only from that boss's corpse on death.
                from world.magitek_infinite import boss_floor_identity
                boss = next(
                    (mob for mob in self.server.world.room_mobs(self.character.room_id)
                     if boss_floor_identity(MOB_TEMPLATES.get(mob.template_id, {})) == (kind, floor)),
                    None,
                )
                if boss is not None:
                    marked_at = self.server.db.collection_entry_discovered_at(
                        self.account_id, BOSS_CHEST_OPENED_CATEGORY_V11332, state_id
                    )
                    try:
                        opened_at = datetime.fromisoformat(str(marked_at).replace(' ', 'T')).replace(
                            tzinfo=timezone.utc
                        ).timestamp() if marked_at else 0
                    except (TypeError, ValueError, OverflowError):
                        opened_at = 0
                    if boss_chest_should_restore_v1288(
                        opened_at,
                        getattr(self.server.world, 'boss_chest_world_started_v1288', 0),
                        getattr(boss, 'respawn_at', 0),
                        getattr(boss, 'alive', False),
                    ):
                        self.server.db.remove_collection_entry(
                            self.account_id, BOSS_CHEST_OPENED_CATEGORY_V11332, state_id
                        )
                        opened = False
                if opened:
                    return None

            # Skrzynia fizycznie stoi w dokładnym pokoju bossa od razu.
            # Klucz nadal wypada dopiero z ciała bossa i unlock bez klucza
            # pozostaje niemożliwy. Po otwarciu marker ukrywa skrzynię aż
            # do kolejnego prawidłowego zabicia tego bossa.
            return spec

    async def unlock_boss_floor_chest(self):
            spec = self.boss_floor_chest_here()
            if not spec:
                return False
            kind, floor, power = spec
            key_id = boss_floor_key_id(kind, floor)
            chest_name = boss_floor_chest_name(kind, floor)

            party_key = self.party_key()
            if party_key is not None and party_key != self.account_id:
                leader = self.server.session_by_account(party_key)
                leader_name = (
                    leader.character.name
                    if leader and getattr(leader, "character", None)
                    else "lider drużyny"
                )
                await self.send(
                    f"W drużynie tę skrzynię otwiera lider: {leader_name}. "
                    "Stań przy skrzyni razem z liderem, aby dostać nagrodę z jednego wspólnego otwarcia."
                )
                return True

            if self.server.db.item_qty(self.account_id, key_id) <= 0:
                await self.send(
                    f"{chest_name} jest zamknięta. "
                    f"Nie masz właściwego klucza. Klucz znajduje się w ciele bossa tego piętra."
                )
                return True
            if not self.server.db.remove_item(self.account_id, key_id, 1):
                await self.send("Nie udało się zużyć klucza.")
                return True

            recipients = [self]
            if party_key is not None:
                recipients = [
                    member
                    for member in self.server.party_sessions(
                        self.account_id, same_room=self.character.room_id
                    )
                    if getattr(member, "character", None) is not None
                    and member.account_id is not None
                ]
                if self not in recipients:
                    recipients.append(self)

            # Jedno fizyczne otwarcie skrzyni daje osobny loot roll każdemu
            # obecnemu członkowi drużyny. Jeżeli członek ma własny klucz z tego
            # samego bossa, zużywamy jedną sztukę, żeby nie zostawić podwójnego
            # odbioru tej samej party-run skrzyni.
            unique_recipients = {}
            for member in recipients:
                unique_recipients[int(member.account_id)] = member
            recipients = [
                unique_recipients[account_id]
                for account_id in sorted(unique_recipients)
            ]

            leader_name = self.character.name
            rewarded = []
            for member in recipients:
                consumed_member_key = False
                if member is not self and self.server.db.item_qty(member.account_id, key_id) > 0:
                    consumed_member_key = bool(
                        self.server.db.remove_item(member.account_id, key_id, 1)
                    )

                reward = boss_chest_reward_roll(kind, floor, power)
                # v57: deterministic continuation after the ORIGINAL reward roll.
                # Never changes the individual player rolls, keys, items or chest state.
                from systems.endless_chests_v5700 import extend_boss_chest_reward_v5700
                reward = extend_boss_chest_reward_v5700(kind, floor, reward)
                # v58: ONE additional equipment chance for each eligible
                # high-floor chest recipient. Previous authored reward roll
                # (and v57 gold) stays intact; never touches UOSS uniques.
                from systems.endless_chest_equipment_v5800 import enhance_boss_chest_equipment_v5800
                reward = enhance_boss_chest_equipment_v5800(kind, floor, reward)
                member.character.gold += int(reward["gold"])
                for item_id in reward["items"]:
                    self.server.db.add_item(member.account_id, item_id, 1)
                    await member.record_item_collection(
                        item_id, source=chest_name, announce=True
                    )
                self.server.db.save_character(member.character)
                self.server.db.add_collection_entry(
                    member.account_id,
                    BOSS_CHEST_OPENED_CATEGORY_V11332,
                    boss_floor_chest_state_id(kind, floor),
                )
                rewarded.append(member.character.name)

                if member is self:
                    await member.send(
                        f"Odkluczasz i otwierasz: {chest_name}. "
                        f"Klucz zostaje zużyty. Złoto: +{reward['gold']}. "
                        "Po otwarciu skrzynia znika."
                    )
                else:
                    key_text = (
                        " Twój odpowiadający Klucz Bossa również zostaje zużyty."
                        if consumed_member_key
                        else ""
                    )
                    await member.send(
                        f"{leader_name} odklucza i otwiera: {chest_name}. "
                        f"Otrzymujesz Złoto: +{reward['gold']}.{key_text} "
                        "Po wspólnym otwarciu skrzynia znika."
                    )
                if reward["items"]:
                    await member.send(
                        "Nagrody: "
                        + ", ".join(ITEMS[i]["name"] for i in reward["items"])
                        + "."
                    )

            if len(rewarded) > 1:
                await self.send(
                    f"Wspólne otwarcie drużyny: nagrody otrzymało {len(rewarded)} osób "
                    "stojących przy skrzyni: " + ", ".join(rewarded) + "."
                )
            return True

    async def unlock_context(self, args=""):
            q = self.normalize_description_query(args)
            if q in ("soul", "dusza", "bron duszy", "broń duszy"):
                await self.unlock()
                return
            if self.boss_floor_chest_here() is not None:
                await self.unlock_boss_floor_chest()
                return
            await self.unlock()

    async def admin_tools_v1224(self, raw):
        """NVDA-first owner controls. Returns False for older admin commands."""
        parts = str(raw or "").strip().split()
        if not parts:
            return False
        action = parts[0].casefold()
        if action not in {
            "pomoc", "online", "gracz", "przywolaj", "ulecz", "wskrzes", "odbuguj",
            "wyrzuc", "serwer", "blad", "log", "komendy", "backup", "baza",
            "oglos", "historia", "lokacja", "moby", "boss", "npc", "profesje",
            "zamowienia", "prace", "najemnicy", "questy", "eq", "napraw", "goto"
        }:
            return False
        if action == "goto" and (len(parts) < 2 or parts[1].casefold() != "gracz"):
            return False
        db = self.server.db
        login = db.account_name(self.master_account_id)
        conn = db.conn
        def audit(cmd, target=""):
            db.record_admin_action_v1224(login, cmd, target)
        def target_row(nick):
            return conn.execute("SELECT account_id,name,room_id,character_level,race,class_name "
                                "FROM characters WHERE name=? COLLATE NOCASE", (nick,)).fetchone()
        def session_for(nick):
            return self.server.find_character_session(nick)
        def check_confirm():
            return len(parts) >= 2 and parts[-1].casefold() == "potwierdzam"
        def room_name(rid):
            return ROOMS.get(rid, {}).get("name", str(rid))
        if action == "pomoc":
            category = parts[1].casefold() if len(parts)>1 else ""
            menus = {
                "gracze": "admin god on/off/status; admin cios grom/nawalnica/wyrok [cel]; admin online; gracz NICK; goto gracz NICK; przywolaj NICK POTWIERDZAM; ulecz NICK POTWIERDZAM; wskrzes NICK POTWIERDZAM; odbuguj NICK POTWIERDZAM; wyrzuc NICK POTWIERDZAM",
                "serwer": "admin serwer; admin blad lista 20; admin blad diagnoza NUMER; admin blad questy NICK; admin blad napraw NUMER NICK QUEST_ID POTWIERDZAM; admin blad SB-XXXXXXXX; admin blad naprawiony SB-XXXXXXXX; admin blad otworz SB-XXXXXXXX; admin log ostatnie 20; admin log aktywne; admin log naprawione; admin log podglad; admin log wyczysc naprawione POTWIERDZAM; wyczysc naprawione POTWIERDZAM; komendy wolne; backup; baza sprawdz; oglos TEKST; historia 20",
                "swiat": "admin lokacja ID; npc NAZWA; moby ID; boss NAZWA",
                "postacie": "admin profesje NICK; zamowienia NICK; prace NICK; najemnicy NICK; questy NICK; eq NICK; napraw postac NICK (diagnoza) / ... POTWIERDZAM (tylko błędna lokacja)",
            }
            if category in menus:
                await self.send("ADMIN " + category.upper() + ": " + menus[category] + ".")
            else:
                await self.send("ADMIN TOOLS 2.0: admin pomoc gracze / serwer / swiat / postacie. Stare polecenia: admin help.")
            return True
        if action == "online":
            clients = sorted((s for s in self.server.sessions if not s.closed and s.character),
                             key=lambda s:s.character.name.casefold())
            await self.send(f"ONLINE: {len(clients)} postaci, {len(self.server.sessions)} połączeń.")
            for s in clients[:100]:
                await self.send(f"{s.character.name}: poziom {s.character.character_level}, {room_name(s.character.room_id)}.")
            return True
        if action == "serwer":
            online = sum(bool(s.character) for s in self.server.sessions if not s.closed)
            mobs = len(self.server.world.mobs)
            size = os.path.getsize(db.path) if os.path.isfile(db.path) else 0
            uptime = int(time.time() - getattr(self.server,"start_time_v1224",time.time()))
            ram_kib = 0
            status_file = Path("/proc/self/status")
            if status_file.exists():
                for line in status_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith("VmRSS:"):
                        ram_kib = int(line.split()[1])
                        break
            ram_text = f"{ram_kib // 1024} MiB" if ram_kib else "niedostępne"
            await self.send(f"SERWER: online {online}; połączeń {len(self.server.sessions)}; lokacji {len(ROOMS)}; mobów {mobs}; czas działania {uptime}s; baza {size//1024} KiB; RAM {ram_text}; CPU procesu {time.process_time():.1f}s.")
            return True
        if action == "blad":
            from systems.admin_error_quest_v36001 import handle_error_quest_command
            if await handle_error_quest_command(self, parts):
                return True
            import re
            error_id = parts[-1].upper() if len(parts) >= 2 else ""
            if len(parts) not in (2, 3) or not re.fullmatch(r"SB-[0-9A-F]{8}", error_id):
                await self.send("Użycie: admin blad SB-XXXXXXXX / admin blad naprawiony SB-XXXXXXXX / admin blad otworz SB-XXXXXXXX.")
                return True
            if len(parts) == 3:
                status_action = parts[1].casefold()
                if status_action not in ("naprawiony", "otworz", "otwórz"):
                    await self.send("Użycie: admin blad naprawiony SB-XXXXXXXX / admin blad otworz SB-XXXXXXXX.")
                    return True
                resolved = status_action == "naprawiony"
                if db.set_admin_error_resolved_v1371(error_id, login, resolved):
                    await self.send(f"ADMIN: {error_id} — {'oznaczony jako naprawiony' if resolved else 'ponownie otwarty'}. Wpis pozostaje w rejestrze do ręcznego czyszczenia.")
                else:
                    await self.send("Nie znaleziono podanego identyfikatora błędu.")
                return True
            row = conn.execute("SELECT * FROM admin_errors_v1224 WHERE id=?", (error_id,)).fetchone()
            if row is None:
                await self.send("Nie znaleziono w wewnętrznym rejestrze. Starsze błędy sprzed v1.22.4 są tylko w logach Railway.")
            else:
                status = ("naprawiony przez " + row['resolved_by'] + " dnia " + row['resolved_at']) if row['resolved_at'] else "aktywny / nieoznaczony"
                await self.send(f"{row['id']}: {row['created_at']}; {row['exception']}; {row['file']}:{row['line']}; moduł {row['subsystem']}; obsługa {row['handler']}; status {status}. Szczegóły traceback w logach serwera.")
            return True
        if action == "log":
            sub = parts[1].casefold() if len(parts) >= 2 else ""
            if sub in ("wyczysc", "wyczyść", "czysc", "czyść"):
                if len(parts) != 4 or parts[2].casefold() != "naprawione" or parts[3].casefold() != "potwierdzam":
                    await self.send("Użycie: admin log wyczysc naprawione POTWIERDZAM. Usuwa WYŁĄCZNIE ręcznie oznaczone błędy z wewnętrznej bazy. Zalecane: admin backup.")
                    return True
                removed = db.purge_resolved_admin_errors_v1371(login)
                await self.send(f"ADMIN: wyczyszczono {removed} naprawionych zgłoszeń SB. Aktywne błędy pozostają. Operację zapisano w admin historia. Logi Railway nie są zmieniane.")
                return True
            if sub in ("podglad", "podgląd"):
                active = conn.execute("SELECT COUNT(*) FROM admin_errors_v1224 WHERE resolved_at = ''").fetchone()[0]
                fixed = conn.execute("SELECT COUNT(*) FROM admin_errors_v1224 WHERE resolved_at != ''").fetchone()[0]
                await self.send(f"REJESTR BŁĘDÓW: aktywne lub nieoznaczone {active}; ręcznie naprawione {fixed}. Do wyczyszczenia: {fixed}. Niczego nie usunięto.")
                return True
            if sub not in ("ostatnie", "last", "aktywne", "naprawione"):
                await self.send("Użycie: admin log ostatnie 20 / aktywne 20 / naprawione 20 / podglad / wyczysc naprawione POTWIERDZAM.")
                return True
            if len(parts) > 3 or (len(parts) == 3 and not parts[2].isdigit()):
                await self.send("Podaj liczbę wpisów od 1 do 50, np. admin log aktywne 20.")
                return True
            limit = min(50, max(1, int(parts[2]) if len(parts) == 3 else 20))
            condition = {"aktywne": "WHERE resolved_at = ''", "naprawione": "WHERE resolved_at != ''"}.get(sub, "")
            rows = conn.execute(f"SELECT * FROM admin_errors_v1224 {condition} ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)).fetchall()
            await self.send(f"BŁĘDY {sub.upper()}: {len(rows)} wpisów.")
            for row in rows:
                status = "NAPRAWIONY" if row['resolved_at'] else "AKTYWNY"
                await self.send(f"{row['id']}: {row['exception']}, {row['file']}:{row['line']}; {status}.")
            return True
        if action == "komendy":
            if len(parts)<2 or parts[1].casefold() not in ("wolne","slow"):
                await self.send("Użycie: admin komendy wolne.")
                return True
            rows = conn.execute("SELECT command,COUNT(*) n,MAX(duration_ms) max_ms FROM admin_slow_commands_v1224 GROUP BY command ORDER BY max_ms DESC LIMIT 20").fetchall()
            await self.send(f"WOLNE KOMENDY: {len(rows)} typów (ostatnie 100 wolnych pomiarów, także z poprzednich wersji; od v102.00.9 bez celowego oczekiwania craft/menu quit).")
            for row in rows:
                await self.send(f"{row['command']}: {row['n']} razy; najwolniej {row['max_ms']} ms.")
            return True
        if action == "baza":
            if len(parts)<2 or parts[1].casefold() != "sprawdz":
                await self.send("Użycie: admin baza sprawdz.")
                return True
            row = conn.execute("PRAGMA quick_check").fetchone()
            await self.send(f"Baza danych: {'OK' if row[0]=='ok' else 'WYKRYTO PROBLEM: ' + str(row[0])[:150]}.")
            audit("baza_sprawdz")
            return True
        if action == "backup":
            folder = Path(db.path).resolve().parent / "backups"
            folder.mkdir(parents=True,exist_ok=True,mode=0o700)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
            destination = folder / ("soulbound_backup_" + stamp + ".db")
            with sqlite3.connect(str(destination)) as backup_db:
                # Consistent SQLite online backup; works with WAL mode.
                db.conn.backup(backup_db)
                result = backup_db.execute("PRAGMA quick_check").fetchone()[0]
            if result != "ok":
                destination.unlink(missing_ok=True)
                await self.send("Kopia nie przeszła kontroli integralności.")
                return True
            os.chmod(destination,0o600)
            old_backups = sorted(folder.glob("soulbound_backup_*.db"), reverse=True)
            for stale in old_backups[10:]:
                stale.unlink(missing_ok=True)
            audit("backup",destination.name)
            await self.send(f"BACKUP OK: {destination.name}. Folder: {folder}. Skopiuj go również poza serwer.")
            return True
        if action == "historia":
            limit = min(50,max(1,int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 20))
            rows = conn.execute("SELECT created_at,admin_login,action,target FROM admin_actions_v1224 ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
            await self.send(f"HISTORIA ADMIN: {len(rows)} wpisów.")
            for row in rows:
                await self.send(f"{row['created_at']}: {row['admin_login']} {row['action']} {row['target']}.")
            return True
        if action == "oglos":
            announcement = " ".join(ch for ch in str(raw).partition(" ")[2].strip() if ch.isprintable())
            if not 1<=len(announcement)<=240:
                await self.send("Użycie: admin oglos TEKST (1-240 znaków).")
                return True
            audit("oglos", f"{len(announcement)} znaków")
            await self.server.broadcast_all(f"OGŁOSZENIE ADMINISTRATORA: {announcement}")
            return True
        if action == "npc":
            needle = " ".join(parts[1:]).casefold()
            matches=[(k,v) for k,v in NPCS.items() if needle and (needle in str(v.get('name','')).casefold() or needle==str(k).casefold())]
            await self.send(f"NPC: znaleziono {len(matches)}. Podaj nazwę lub identyfikator.")
            for key,npc in matches[:20]:
                await self.send(f"{npc.get('name',key)} ({key}): {room_name(npc.get('room','?'))}; pokój {npc.get('room','?')}.")
            return True
        if action == "lokacja":
            rid = " ".join(parts[1:]) or self.character.room_id
            if rid not in ROOMS:
                await self.send("Nie znaleziono lokacji (użyj ID pokoju).")
                return True
            room = ROOMS[rid]
            await self.send(f"LOKACJA: {room_name(rid)}; ID {rid}; strefa {room.get('zone','?')}; wyjścia {', '.join(sorted(room.get('exits',{}))) or 'brak'}. NPC {sum(n.get('room')==rid for n in NPCS.values())}; żywe moby {sum(m.room_id==rid and m.alive for m in self.server.world.mobs.values())}.")
            return True
        if action == "moby":
            rid = " ".join(parts[1:]) or self.character.room_id
            if rid not in ROOMS:
                await self.send("Nie znaleziono lokacji.")
                return True
            mobs=[m for m in self.server.world.mobs.values() if m.room_id==rid]
            await self.send(f"MOBY: {room_name(rid)}, {len(mobs)} wpisów.")
            for mob in mobs[:30]:
                await self.send(f"{MOB_TEMPLATES.get(mob.template_id,{}).get('name',mob.template_id)}: HP {mob.hp}; {'żywy' if mob.alive else 'pokonany'}; klucz {mob.key}.")
            return True
        if action == "boss":
            q = " ".join(parts[1:]).casefold()
            if not q:
                await self.send("Użycie: admin boss NAZWA.")
                return True
            matches=[m for m in self.server.world.mobs.values() if q in str(MOB_TEMPLATES.get(m.template_id,{}).get('name',m.template_id)).casefold()]
            await self.send(f"BOSS / POTWÓR: znaleziono {len(matches)} aktywnych instancji pasujących do nazwy.")
            for m in matches[:20]:
                await self.send(f"{MOB_TEMPLATES.get(m.template_id,{}).get('name',m.template_id)}: {room_name(m.room_id)}, HP {m.hp}, {'żywy' if m.alive else 'pokonany'}, respawn {max(0,int(m.respawn_at-time.time()))}s.")
            return True
        if action == "goto":
            if len(parts)<3:
                await self.send("Użycie: admin goto gracz NICK.")
                return True
            target = session_for(" ".join(parts[2:]))
            if not target:
                await self.send("Gracz nie jest online.")
                return True
            self.character.room_id=target.character.room_id
            db.save_character(self.character)
            audit("goto_gracz",target.character.name)
            await self.send(f"Przeniesiono do {room_name(self.character.room_id)}.")
            await self.look()
            return True
        if action == "gracz":
            row=target_row(" ".join(parts[1:]))
            if not row:
                await self.send("Nie znaleziono postaci o tej nazwie.")
                return True
            online = session_for(row['name'])
            await self.send(f"GRACZ: {row['name']}; poziom {row['character_level']}; {row['race']} / {row['class_name']}; {room_name(row['room_id'])}; {'online' if online else 'offline'}." +
                            (f" HP {online.current_hp}/{online.max_hp()}." if online else ""))
            return True
        if action in ("przywolaj","ulecz","wskrzes","odbuguj","wyrzuc"):
            nick = " ".join(parts[1:-1] if check_confirm() else parts[1:])
            target = session_for(nick)
            if not target:
                await self.send("Ta postać musi być online i mieć dokładną nazwę.")
                return True
            if not check_confirm():
                await self.send(f"Potwierdź: admin {action} {target.character.name} POTWIERDZAM.")
                return True
            if target is self and action in ("wyrzuc","przywolaj"):
                await self.send("Nie możesz wykonać tej operacji na sobie.")
                return True
            if target.is_admin() and target is not self:
                await self.send("Operacje na innym administratorze są zablokowane.")
                return True
            if action in ("przywolaj","odbuguj"):
                if (target.combat_mob_key or target.is_downed_v0371()
                        or any(bool(getattr(target, flag, False)) for flag in
                        ("auto_mining", "auto_fishing", "auto_woodcutting", "auto_herbalism", "resting"))
                        or target.guide_task_active() or target.smelt_task_active_v1124()):
                    await self.send("Gracz walczy albo ma aktywną pracę. Najpierw zakończ walkę, prowadzenie lub pracę.")
                    return True
                dest = self.character.room_id if action=="przywolaj" else "temple"
                if dest not in ROOMS:
                    await self.send("Brak bezpiecznej lokacji docelowej.")
                    return True
                target.character.room_id=dest
                db.save_character(target.character)
                await target.send(f"ADMIN: przeniesiono cię do {room_name(dest)}.")
            elif action in ("ulecz","wskrzes"):
                if action=="wskrzes" and target.current_hp>0 and not target.is_downed_v0371():
                    await self.send("Gracz nie potrzebuje wskrzeszenia.")
                    return True
                if action=="wskrzes":
                    target.clear_downed_v0371(cancel_task=True)
                    target.server.release_all_engagements_for_session(target)
                    target.combat_mob_key=None
                    await target.stop_realtime_combat()
                    target.skill_guard=0
                    target.skill_evade=False
                    target.skill_evade_lockout_until=0.0
                target.current_hp=target.max_hp()
                target.current_mana=target.max_mana()
                await target.send("ADMIN: przywrócono HP i Manę.")
            else:
                audit("wyrzuc",target.character.name)
                await target.send("ADMIN: sesja została rozłączona.")
                target.closed=True
                target.writer.close()
                await self.send("Gracz został rozłączony.")
                return True
            audit(action,target.character.name)
            await self.send(f"ADMIN: {action} zakończone dla {target.character.name}.")
            return True
        # Other-player diagnostics: read-only by default.
        if action in ("profesje","zamowienia","prace","najemnicy","questy","eq","napraw"):
            offset=2 if action=="napraw" else 1
            if action=="napraw" and (len(parts)<2 or parts[1].casefold()!="postac"):
                await self.send("Użycie: admin napraw postac NICK [POTWIERDZAM].")
                return True
            nick=" ".join(parts[offset:-1] if check_confirm() else parts[offset:])
            row=target_row(nick)
            if not row:
                await self.send("Nie znaleziono postaci.")
                return True
            cid=int(row['account_id'])
            if action=="napraw":
                if row['room_id'] in ROOMS:
                    await self.send("Diagnostyka: lokacja prawidłowa. Brak automatycznych zmian. Pozostałe problemy wymagają ręcznej diagnozy.")
                elif not check_confirm():
                    await self.send(f"Nieistniejąca lokacja {row['room_id']}. Aby przenieść postać do świątyni: admin napraw postac {row['name']} POTWIERDZAM.")
                elif session_for(row['name']):
                    await self.send("Postać musi być offline przed naprawą zapisu.")
                else:
                    conn.execute("UPDATE characters SET room_id='temple' WHERE account_id=?",(cid,))
                    conn.commit()
                    audit("napraw_lokacja",row['name'])
                    await self.send("Naprawiono wyłącznie identyfikator lokacji. Inne dane nietknięte.")
                return True
            if action=="profesje":
                prows=conn.execute("SELECT profession,level,xp FROM professions WHERE account_id=? ORDER BY profession",(cid,)).fetchall()
                await self.send(f"PROFESJE {row['name']}: {len(prows)}.")
                for entry in prows[:25]:
                    await self.send(f"{entry['profession']}: poziom {entry['level']}, EXP {entry['xp']}.")
            elif action=="zamowienia":
                order=db.crafting_order_v0600(cid)
                await self.send(f"ZAMÓWIENIA {row['name']}: " +
                                (f"{order['item_name']}, {order['progress']}/{order['needed']}" if order and order['needed'] else "brak aktywnego"))
            elif action=="najemnicy":
                active=db.mercenary_contracts(cid)
                await self.send(f"NAJEMNICY {row['name']}: {len(active)} aktywnych; " + ", ".join(x['role'] for x in active))
            elif action=="prace":
                live=session_for(row['name'])
                if live:
                    states=[name for name,flag in (("ryby",live.auto_fishing),("ruda",live.auto_mining),
                           ("drewno",live.auto_woodcutting),("zioła",live.auto_herbalism)) if flag]
                    await self.send("PRACE: " + (", ".join(states) if states else "brak aktywnych prac automatycznych") + ".")
                else:
                    await self.send("Postać offline; aktywności sesyjne nie działają.")
            elif action=="questy":
                quests=db.quest_rows(cid)
                await self.send(f"QUESTY {row['name']}: {len(quests)} zapisów; pokazuję do 15.")
                for q in quests[:15]:
                    await self.send(str(dict(q))[:180])
            elif action=="eq":
                entries=db.equipment(cid)
                await self.send(f"EQ {row['name']}: {len(entries)} slotów.")
                for entry in list(entries)[:25]:
                    await self.send(str(dict(entry))[:180])
            return True
        return False
