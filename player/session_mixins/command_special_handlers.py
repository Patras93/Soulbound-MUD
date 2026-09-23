# -*- coding: utf-8 -*-
"""Focused handlers for formerly inline command-loop branches (v0.49.0)."""
from __future__ import annotations

from core.command_catalog import COMMAND_LOOP_BREAK
from network.protocol_gameplay_utils import normalize_lookup_text


class SessionCommandSpecialHandlersMixin:
    async def command_lifetime_v0490(self, args):
        history_prefix = str(args or "").strip().split(maxsplit=1)[0] if str(args or "").strip() else ""
        if self.normalize_history_category(history_prefix) or self.normalize_description_query(history_prefix) in (
            "clear", "wyczysc", "wyczyść", "reset",
        ):
            await self.show_history_buffer(args)
        else:
            await self.show_lifetime_statistics()

    async def command_leaderboards_v0490(self, args):
        if normalize_lookup_text(args or "") in (
            "profesje", "profession", "professions", "bossowie", "bosses",
            "kolekcje", "collection", "rekordy", "records", "gildie", "guilds",
            "mentor", "mentorzy",
        ):
            await self.leaderboards_v03052(args)
        else:
            await self.show_leaderboards(args)

    async def command_codex_v0490(self, args):
        codex_args = (args or "").strip()
        codex_norm = self.normalize_description_query(codex_args)
        if codex_norm in ("klasy", "klasa", "class", "classes"):
            await self.show_class_codex("info")
        elif codex_norm.startswith("klasy ") or codex_norm.startswith("klasa "):
            await self.show_class_codex(codex_args.split(maxsplit=1)[1])
        elif codex_norm.startswith("class ") or codex_norm.startswith("classes "):
            await self.show_class_codex(codex_args.split(maxsplit=1)[1])
        else:
            await self.show_world_codex(args)

    async def command_channels_v0490(self, args):
        parts = str(args or "").strip().split(maxsplit=1)
        if parts and normalize_lookup_text(parts[0]) in ("history", "historia"):
            await self.show_channel_history_v03051(parts[1] if len(parts) > 1 else "gossip")
        else:
            await self.show_channels_v03050()

    async def command_mentor_v0490(self, args):
        normalized = normalize_lookup_text(str(args or "").strip())
        if normalized in ("zadania", "tasks"):
            await self.mentor_tasks_v03051(False)
        elif normalized in ("odbierz", "claim"):
            await self.mentor_tasks_v03051(True)
        else:
            await self.mentor_v03052(args)

    async def command_skill_v0490(self, args):
        skill_args = str(args or "").strip()
        skill_args_norm = normalize_lookup_text(skill_args)
        if skill_args_norm in ("info", "help", "opis"):
            await self.show_skill_help("")
            return
        if any(skill_args_norm.startswith(prefix) for prefix in ("info ", "help ", "opis ")):
            query = skill_args.split(maxsplit=1)[1] if " " in skill_args else ""
            if not await self.show_skill_help(query):
                await self.send("Nie znam takiej umiejętności ani spella. Wpisz skillnames.")
            return
        await self.use_class_skill(args)

    async def command_fish_v0490(self, args):
        mode = str(args or "").strip().lower()
        if mode in ("on", "start", "1"):
            await self.set_auto_fishing(True)
        elif mode in ("off", "stop", "0"):
            await self.set_auto_fishing(False)
        elif mode:
            await self.send("Użycie: fish, fish on, fish off, low on albo low off.")
        else:
            await self.fish()

    async def command_mine_v0490(self, args):
        mode = str(args or "").strip().lower()
        if mode in ("on", "start", "1"):
            await self.set_auto_mining(True)
        elif mode in ("off", "stop", "0"):
            await self.set_auto_mining(False)
        elif mode:
            await self.send("Użycie: mine, mine on, mine off, kop on albo kop off.")
        else:
            await self.mine()

    async def command_woodcut_v0490(self, args):
        mode = str(args or "").strip().lower()
        if mode in ("on", "start", "1"):
            await self.set_auto_woodcutting(True)
        elif mode in ("off", "stop", "0"):
            await self.set_auto_woodcutting(False)
        elif mode:
            await self.send("Użycie: tnij, tnij on, tnij off, woodcut on albo woodcut off.")
        else:
            await self.woodcut()

    async def command_herb_v0490(self, args):
        mode = str(args or "").strip().lower()
        if mode in ("on", "start", "1"):
            await self.set_auto_herbalism(True)
        elif mode in ("off", "stop", "0"):
            await self.set_auto_herbalism(False)
        elif mode:
            await self.send("Użycie: zbieraj, zbieraj on albo zbieraj off.")
        else:
            await self.gather_herb()

    async def command_craft_v0490(self, args):
        if not str(args or "").strip():
            await self.send("Użycie: craft <receptura>. Wpisz receptury.")
        else:
            await self.craft_item_v03114(args)

    async def command_jewelcraft_v0490(self, args):
        if not str(args or "").strip():
            await self.send("Użycie: jub <receptura>. Wpisz receptury jubilerstwo.")
        else:
            await self.jewelcraft_item(args)

    async def command_cook_v0490(self, args):
        cook_mode = str(args or "").strip().lower()
        if cook_mode in ("lista", "list", "receptury", "przepisy"):
            await self.show_recipes("cook")
        elif not cook_mode:
            await self.send("Użycie: gotuj <potrawa>. Wpisz gotuj lista albo receptury cook.")
        else:
            await self.cook_item(args)

    async def command_alchemy_v0490(self, args):
        if not str(args or "").strip():
            await self.send("Użycie: alchemia <mikstura>. Wpisz receptury alchemia.")
        else:
            await self.alchemy_item(args)

    async def command_equip_v0490(self, args):
        equip_target = self.normalize_description_query(str(args or "").strip())
        if equip_target in ("druzyna", "druzyne", "party"):
            await self.create_party()
        else:
            await self.equip_item(args)

    async def command_save_v0490(self):
        self.server.db.save_character(self.character)
        await self.send("Postać zapisana.")

    async def command_quit_v0490(self):
        await self.send("Zapisuję postać i wracam do wyboru postaci.")
        await self.leave_current_character_for_selection()

        selected = await self.character_selection_flow()
        if selected is True:
            await self.enter_world()
            return None

        # Opcja 4 w MENU POSTACI wylogowuje konto. Zachowujemy wtedy
        # normalny ekran logowania bez rozłączania klienta.
        if not self.closed and self.master_account_id is None:
            if await self.login_flow():
                await self.enter_world()
                return None

        self.closed = True
        return COMMAND_LOOP_BREAK
