# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.ioauthcharacter_part01 as _sb420_src_01
# SessionIOAuthCharacterMixin.set_encoding -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.history_buffer_category -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.normalize_history_category -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.show_history_buffer -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.send -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.set_combat_log -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.combat_hp_warning -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.read_line -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.login_flow -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.recover_password_from_login_v1222 -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.recover_password_by_email_v1223 -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.do_login -> player/session_methods_v4200/ioauthcharacter_part01.py
# SessionIOAuthCharacterMixin.send_character_list -> player/session_methods_v4200/ioauthcharacter_part01.py
import player.session_methods_v4200.ioauthcharacter_part02 as _sb420_src_02
# SessionIOAuthCharacterMixin.choose_existing_character -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.delete_character_flow -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.send_admin_account_list_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.select_admin_master_account_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.disconnect_master_sessions_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.admin_show_account_characters_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.admin_wipe_master_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.admin_delete_character_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.admin_wipe_all_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.admin_character_menu_v0301 -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.character_selection_flow -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.do_new_account -> player/session_methods_v4200/ioauthcharacter_part02.py
# SessionIOAuthCharacterMixin.ask_name_declension -> player/session_methods_v4200/ioauthcharacter_part02.py
import player.session_methods_v4200.ioauthcharacter_part03 as _sb420_src_03
# SessionIOAuthCharacterMixin.character_creator -> player/session_methods_v4200/ioauthcharacter_part03.py
# SessionIOAuthCharacterMixin.start_session_summary -> player/session_methods_v4200/ioauthcharacter_part03.py
# SessionIOAuthCharacterMixin.show_session_summary -> player/session_methods_v4200/ioauthcharacter_part03.py
# SessionIOAuthCharacterMixin.enter_world -> player/session_methods_v4200/ioauthcharacter_part03.py


# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import re
from core.bootstrap_economy_professions import (
    HISTORY_BUFFER_DEFAULT_SHOW,
    HISTORY_BUFFER_LIMIT,
    MAX_CHARACTERS_PER_ACCOUNT,
    VERSION,
    currency_reading_text,
)
from core.classes_skills import (
    CLASSES,
    CLASS_DESCRIPTIONS,
    CLASS_SKILLS,
    RACES,
    ROOMS,
    class_starting_stats_for,
    race_class_recommendation_text,
    starting_hp_mana_for,
)
from network.protocol_gameplay_utils import (
    clean_telnet,
    normalize_lookup_text,
    safe_name,
    telnet_charset_offer_bytes,
    verify_password,
)
from player.character import Character
from core.promotion_patterns_v2003 import is_level_promotion_v2003

import time
import secrets
import hmac
import hashlib
import sqlite3
import smtplib
from network.account_email_v1223 import (
    normalized_email_v1223, smtp_ready_v1223, send_code_v1223,
    allow_verification_send_v1223,
)
# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: io_auth_character."""

# v1.17.8: cache log verbosity on each session to keep rapid combat messages
# from competing for SQLite during multi-player fights. A new account ID,
# explicit setting change or a 30-second expiry refreshes the DB value.
COMBAT_LOG_MODE_CACHE_SECONDS_V1178 = 30.0

class SessionIOAuthCharacterMixin:
    def combat_log_mode_cached_v1178(self):
            account_id = self.account_id
            if account_id is None:
                return "normal"
            now = time.monotonic()
            cached = getattr(self, "_combat_log_mode_cache_v1178", None)
            if (cached is not None and cached[0] == account_id
                    and now - cached[2] < COMBAT_LOG_MODE_CACHE_SECONDS_V1178):
                return cached[1]
            mode = self.server.db.combat_log_mode(account_id)
            self._combat_log_mode_cache_v1178 = (account_id, mode, now)
            return mode

    def encode_session_text(self, value):
            value = str(value)
            try:
                return value.encode(
                    self.output_encoding,
                    errors="strict",
                )
            except UnicodeEncodeError:
                return value.encode(
                    self.output_encoding,
                    errors="replace",
                )

    async def negotiate_polish_charset(self):
            if self.closed:
                return
            try:
                self.writer.write(
                    telnet_charset_offer_bytes()
                )
                await self.writer.drain()
            except (ConnectionError, BrokenPipeError):
                self.closed = True

    async def show_encoding(self):
            label = (
                "UTF-8"
                if self.output_encoding == "utf-8"
                else "Windows-1250"
            )
            await self.send(
                f"Kodowanie sesji: {label}."
            )
            await self.send(
                "Zmiana: kodowanie utf8 albo kodowanie cp1250."
            )

    async def set_encoding(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_encoding")

    def history_buffer_category(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method history_buffer_category")

    def record_history_buffer(self, text, category=None, combat_detail=None):
            if self.history_replaying:
                return
            raw = str(text or "").strip()
            if not raw:
                return
            category = category or self.history_buffer_category(raw, combat_detail=combat_detail)
            if category not in self.history_buffers:
                return
            self.history_sequence += 1
            stamp = time.strftime("%H:%M:%S")
            self.history_buffers[category].append((self.history_sequence, stamp, raw))

    def normalize_history_category(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method normalize_history_category")

    async def show_history_buffer(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_history_buffer")

    async def send(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method send")

    async def send_combat(self, text, detail="essential"):
            try:
                if self.account_id:
                    self.server.db.add_combat_event_v0320(self.account_id, str(text), "combat")
            except Exception as exc:
                print(f"COMBAT_EVENT_LOG_ERROR: {type(exc).__name__}: {exc}", flush=True)
            await self.send(text, combat_detail=detail)

    async def set_combat_log(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_combat_log")

    async def combat_hp_warning(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method combat_hp_warning")

    async def prompt(self, text):
            if self.closed:
                return
            try:
                self.writer.write(
                    self.encode_session_text(text)
                )
                await self.writer.drain()
            except (ConnectionError, BrokenPipeError):
                self.closed = True

    async def read_line(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method read_line")

    async def ask(self, text):
            await self.prompt(text)
            return await self.read_line()

    async def close_from_main_menu(self):
            """Opcja Wyjdź ma naprawdę zamknąć połączenie klienta."""
            try:
                await self.send("Do zobaczenia.")
            except Exception:  # AUDIT_INTENTIONAL_PASS: connection may already be gone while saying goodbye
                pass
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:  # AUDIT_INTENTIONAL_PASS: peer may already have closed the socket
                pass
            self.closed = True

    async def login_flow(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method login_flow")

    async def recover_password_from_login_v1222(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method recover_password_from_login_v1222")

    async def close_password_reset_sessions_v1223(self, username):
        row = self.server.db.master_account_by_name(username)
        if row is None:
            return
        for active in list(self.server.sessions):
            if active is self or getattr(active, "master_account_id", None) != int(row["id"]):
                continue
            await active.send("Hasło konta zostało zmienione. Połącz się ponownie.")
            await active.close()

    async def recover_password_by_email_v1223(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method recover_password_by_email_v1223")

    async def do_login(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method do_login")

    async def send_character_list(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method send_character_list")

    async def choose_existing_character(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method choose_existing_character")

    async def delete_character_flow(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method delete_character_flow")

    async def send_admin_account_list_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method send_admin_account_list_v0301")

    async def select_admin_master_account_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method select_admin_master_account_v0301")

    async def disconnect_master_sessions_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method disconnect_master_sessions_v0301")

    async def admin_show_account_characters_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method admin_show_account_characters_v0301")

    async def admin_wipe_master_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method admin_wipe_master_v0301")

    async def admin_delete_character_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method admin_delete_character_v0301")

    async def admin_wipe_all_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method admin_wipe_all_v0301")

    async def admin_character_menu_v0301(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method admin_character_menu_v0301")

    async def character_selection_flow(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method character_selection_flow")

    async def do_new_account(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method do_new_account")

    async def choose_number(self, items, prompt_text):
            while True:
                raw = await self.ask(prompt_text)
                if raw is None:
                    return None
                try:
                    n = int(raw)
                    if 1 <= n <= len(items):
                        return items[n - 1]
                except ValueError:  # AUDIT_INTENTIONAL_PASS: invalid menu input is handled by the message below
                    pass
                await self.send("Nieprawidłowy numer.")

    def valid_name_case_form(self, value):
            value = value.strip()
            if not (1 <= len(value) <= 40):
                return False
            return not any(ord(ch) < 32 for ch in value)

    async def ask_name_declension(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method ask_name_declension")

    async def character_creator(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method character_creator")


    def start_session_summary(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method start_session_summary")

    def session_summary_add(self, key, amount, subkey=None):
        state = getattr(self, "_session_summary", None)
        if not state:
            return
        amount = max(0, int(amount or 0))
        if amount <= 0:
            return
        if subkey is None:
            state[key] = int(state.get(key, 0) or 0) + amount
        else:
            bucket = state.setdefault(key, {})
            bucket[str(subkey)] = int(bucket.get(str(subkey), 0) or 0) + amount

    async def show_session_summary(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_session_summary")

    async def enter_world(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method enter_world")

# v4.20.0: exact historical implementations rebound onto original class.
SessionIOAuthCharacterMixin.set_encoding = _sb420_bind(_sb420_src_01.set_encoding, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.history_buffer_category = _sb420_bind(_sb420_src_01.history_buffer_category, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.normalize_history_category = _sb420_bind(_sb420_src_01.normalize_history_category, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.show_history_buffer = _sb420_bind(_sb420_src_01.show_history_buffer, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.send = _sb420_bind(_sb420_src_01.send, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.set_combat_log = _sb420_bind(_sb420_src_01.set_combat_log, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.combat_hp_warning = _sb420_bind(_sb420_src_01.combat_hp_warning, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.read_line = _sb420_bind(_sb420_src_01.read_line, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.login_flow = _sb420_bind(_sb420_src_01.login_flow, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.recover_password_from_login_v1222 = _sb420_bind(_sb420_src_01.recover_password_from_login_v1222, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.recover_password_by_email_v1223 = _sb420_bind(_sb420_src_01.recover_password_by_email_v1223, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.do_login = _sb420_bind(_sb420_src_01.do_login, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.send_character_list = _sb420_bind(_sb420_src_01.send_character_list, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.choose_existing_character = _sb420_bind(_sb420_src_02.choose_existing_character, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.delete_character_flow = _sb420_bind(_sb420_src_02.delete_character_flow, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.send_admin_account_list_v0301 = _sb420_bind(_sb420_src_02.send_admin_account_list_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.select_admin_master_account_v0301 = _sb420_bind(_sb420_src_02.select_admin_master_account_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.disconnect_master_sessions_v0301 = _sb420_bind(_sb420_src_02.disconnect_master_sessions_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.admin_show_account_characters_v0301 = _sb420_bind(_sb420_src_02.admin_show_account_characters_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.admin_wipe_master_v0301 = _sb420_bind(_sb420_src_02.admin_wipe_master_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.admin_delete_character_v0301 = _sb420_bind(_sb420_src_02.admin_delete_character_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.admin_wipe_all_v0301 = _sb420_bind(_sb420_src_02.admin_wipe_all_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.admin_character_menu_v0301 = _sb420_bind(_sb420_src_02.admin_character_menu_v0301, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.character_selection_flow = _sb420_bind(_sb420_src_02.character_selection_flow, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.do_new_account = _sb420_bind(_sb420_src_02.do_new_account, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.ask_name_declension = _sb420_bind(_sb420_src_02.ask_name_declension, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.character_creator = _sb420_bind(_sb420_src_03.character_creator, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.start_session_summary = _sb420_bind(_sb420_src_03.start_session_summary, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.show_session_summary = _sb420_bind(_sb420_src_03.show_session_summary, globals(), "SessionIOAuthCharacterMixin")
SessionIOAuthCharacterMixin.enter_world = _sb420_bind(_sb420_src_03.enter_world, globals(), "SessionIOAuthCharacterMixin")

