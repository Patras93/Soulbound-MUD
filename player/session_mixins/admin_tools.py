# -*- coding: utf-8 -*-
"""Admin commands, wipe and unlock helpers."""

from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES
import os
import time
import sqlite3
from contextlib import closing
from pathlib import Path  # canonical current dependency
from datetime import datetime, timezone
from data.npcs import NPCS  # canonical current dependency
from data.mobs import MOB_TEMPLATES  # canonical current dependency

from data.rooms import ROOMS  # canonical current dependency
from data.items import ITEMS  # canonical current dependency
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


from .admin_tools_parts_v109 import AdminGuardianControlsV109Mixin, AdminSessionSafetyV109Mixin

from .admin_tools_parts_v109 import AdminBossChestsV109Mixin

from .admin_tools_parts_v109 import AdminWipeSafetyV109Mixin
from .admin_tools_parts_v109 import AdminOwnerDashboardV109Mixin

class SessionAdminToolsMixin(AdminGuardianControlsV109Mixin, AdminSessionSafetyV109Mixin, AdminBossChestsV109Mixin, AdminWipeSafetyV109Mixin, AdminOwnerDashboardV109Mixin):

    def is_admin(self):
            from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES  # explicit current dependency
            if self.master_account_id is None:
                return False
            username = self.server.db.account_name(self.master_account_id).casefold()
            return bool(username and username in ADMIN_ACCOUNT_NAMES)

    async def admin_command(self, args=""):
            from data.rooms import ROOMS  # canonical current dependency
            from data.items import ITEMS  # canonical current dependency
            raw = str(args or "").strip()
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
                await self.send("admin blad lista 20; admin blad diagnoza NUMER; admin blad questy NICK; admin blad napraw NUMER NICK QUEST_ID POTWIERDZAM.")
                await self.send("Wyczysc naprawione POTWIERDZAM - usuwa wyłącznie oznaczone jako naprawione błędy SB, nie postacie.")
                await self.send("wipe moje postacie POTWIERDZAM / wipe my characters CONFIRM.")
                await self.send("wipe wszystkie postacie POTWIERDZAM / wipe all characters CONFIRM.")
                await self.send("Wipe usuwa postacie i ich progres, ale NIE usuwa kont/loginów/haseł.")
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





