# -*- coding: utf-8 -*-
"""v109: muzeum, osiągnięcia i zlecenia — bounty_board. Historyczne metody bez zmian."""
from .dependencies import *

class MuseumBountyBoardV109Mixin:
    async def show_bounty_board(self):
            state = self.ensure_bounty_board()
            active = state.get("active") or {}
            await self.send(
                f"TABLICA ZLECEŃ. Ukończone kontrakty: {int(state.get('completed_count', 0))}."
            )
            if active:
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                status = "cel wykonany" if progress >= needed else "w toku"
                await self.send(
                    f"Aktywny kontrakt: {active.get('label', 'Kontrakt')}. "
                    f"Postęp {progress} z {needed}, {status}. "
                    f"Nagroda: {int(active.get('reward_soul_xp', 0))} Soul XP i "
                    f"{currency_reading_text(0, int(active.get('reward_gold', 0)), 0)}."
                )
            else:
                await self.send("Aktywny kontrakt: brak.")
            await self.send("DOSTĘPNE KONTRAKTY:")
            for index, offer in enumerate(state.get("offers") or [], 1):
                await self.send(
                    f"{index}. {offer.get('label', 'Kontrakt')}. "
                    f"Start 0 z {int(offer.get('needed', 1))}. "
                    f"Nagroda: {int(offer.get('reward_soul_xp', 0))} Soul XP i "
                    f"{currency_reading_text(0, int(offer.get('reward_gold', 0)), 0)}."
                )
            await self.send(
                "Komendy: bounty accept <1-3>, bounty aktywne, bounty odbierz, bounty porzuć; "
                "bounty odśwież losuje nową tablicę tylko bez aktywnego kontraktu."
            )

    async def share_bounty_with_party_v1119(self, contract):
            """Lider synchronizuje NOWY kontrakt z aktywnymi kontami w drużynie.

            Każdy członek otrzymuje osobny trwały wpis SQLite: własny progres,
            własne nagrody i dotychczasową tablicę ofert. Aktywne kontrakty
            innych graczy są nietykalne; przyjęcie nie wykonuje się ponownie
            podczas logowania ani podczas rezygnacji lidera.
            """
            party_key = self.server.party_key_for_account(self.account_id)
            if party_key is None or int(party_key) != int(self.account_id):
                return
            candidates = list(self.server.party_sessions(self.account_id) or ())
            added = []
            skipped = []
            seen = {self.account_id}
            for member in sorted(candidates, key=lambda session: (
                str(getattr(getattr(session, "character", None), "name", "")).casefold(),
                str(getattr(session, "account_id", "")),
            )):
                account_id = getattr(member, "account_id", None)
                if (account_id is None or account_id in seen
                        or getattr(member, "closed", False)
                        or not getattr(member, "character", None)):
                    continue
                seen.add(account_id)
                # Nie udostępniaj kontraktu sesji, która wyszła z drużyny.
                if self.server.party_key_for_account(account_id) != party_key:
                    continue
                state = self.server.db.bounty_board_state(account_id)
                if state.get("active"):
                    skipped.append(member.character.name)
                    await member.send(
                        f"Lider {self.character.name} przyjął bounty, lecz masz już "
                        "aktywny kontrakt. Twój postęp pozostał bez zmian."
                    )
                    continue
                own_contract = dict(contract)
                own_contract["progress"] = 0
                own_contract["completed"] = False
                self.server.db.save_bounty_board_state(
                    account_id,
                    offers=state.get("offers", []),
                    active=own_contract,
                    completed_count=state.get("completed_count", 0),
                )
                added.append(member.character.name)
                await member.send(
                    f"Lider {self.character.name} przyjął dla drużyny bounty: "
                    f"{own_contract.get('label', 'Kontrakt')}. "
                    f"Postęp 0 z {int(own_contract.get('needed', 1))}. "
                    "Twój postęp i nagrody są niezależne. Sprawdź: bounty aktywne."
                )
            if added:
                await self.send("Bounty otrzymali członkowie drużyny: " + ", ".join(added) + ".")
            if skipped:
                await self.send("Nie nadpisano aktywnych kontraktów: " + ", ".join(skipped) + ".")

    async def handle_bounty(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            # The physical contract board is in Gildia Dusz, not a portable UI.
            # A player's active contract remains readable (and abandonable)
            # everywhere so previously accepted quests never become trapped.
            remote = {"aktywne", "aktywny", "active", "progress", "postep", "porzuc", "abandon", "cancel"}
            if str(self.character.room_id) != 'guild_hall' and norm not in remote:
                await self.send('Tablica Zleceń stoi w Sali Głównej Gildii Dusz. '
                                'Udaj się tam, aby przyjąć, odebrać lub odświeżyć kontrakt. '
                                'Zdalnie: bounty aktywne lub bounty porzuc.')
                return
            if not norm or norm in ("lista", "list", "status", "info"):
                await self.show_bounty_board()
                return
            state = self.ensure_bounty_board()
            active = state.get("active") or {}

            if norm in ("aktywne", "aktywny", "active", "progress", "postep", "postęp"):
                if not active:
                    await self.send("Nie masz aktywnego kontraktu. Wpisz bounty.")
                    return
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                await self.send(
                    f"Kontrakt: {active.get('label', 'Kontrakt')}. Postęp {progress} z {needed}."
                )
                return

            if norm in ("porzuc", "porzuć", "abandon", "cancel"):
                if not active:
                    await self.send("Nie masz aktywnego kontraktu do porzucenia.")
                    return
                label = str(active.get("label", "Kontrakt"))
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                self.server.db.save_bounty_board_state(
                    self.account_id,
                    offers=state.get("offers", []),
                    active={},
                    completed_count=state.get("completed_count", 0),
                )
                await self.send(
                    f"Porzucono kontrakt: {label}. Postęp {progress} z {needed} został anulowany. "
                    "Oferty na Tablicy Zleceń pozostały bez zmian."
                )
                return

            if norm in ("odbierz", "claim"):
                if not active:
                    await self.send("Nie masz aktywnego kontraktu do odebrania.")
                    return
                progress = max(0, int(active.get("progress", 0)))
                needed = max(1, int(active.get("needed", 1)))
                if progress < needed:
                    await self.send(
                        f"Kontrakt nie jest ukończony. Postęp {progress} z {needed}."
                    )
                    return
                soul_xp = max(0, int(active.get("reward_soul_xp", 0)))
                gold = max(0, int(active.get("reward_gold", 0)))
                label = str(active.get("label", "Kontrakt"))
                contract_stage=self.bounty_content_stage_v11342(active)
                if str(active.get("kind")) == "kill":
                    combat_quest = {
                        "kind": "kill",
                        "target": active.get("target"),
                        "needed": needed,
                        "repeatable": True,
                    }
                    contract_stage=max(
                        contract_stage,v0190_quest_stage(combat_quest)
                    )
                    contract_stat_xp = v0914_combat_quest_stat_reward(
                        combat_quest
                    )
                    await self.grant_combat_quest_stat_xp(
                        contract_stat_xp,
                        repeatable=True,
                        source_label="Kontrakt bojowy",
                        content_level=contract_stage,
                        content_scaled=True,
                    )
                if soul_xp:
                    await self.grant_soul_xp(
                        soul_xp,
                        content_level=contract_stage,
                        content_scaled=True,
                    )
                self.character.gold += gold
                self.server.db.save_character(self.character)
                completed = int(state.get("completed_count", 0)) + 1
                self.server.db.add_lifetime_stat(self.account_id, "bounties_completed", 1)
                offers = self.generate_bounty_offers()
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=offers, active={}, completed_count=completed
                )
                await self.set_achievement_progress("bounties_completed", completed)
                await self.send(
                    f"Kontrakt odebrany: {label}. Nagroda: {soul_xp} Soul XP i " + currency_reading_text(0, gold, 0) + ". "
                    f"Ukończone kontrakty: {completed}. Tablica wylosowała nowe oferty."
                )
                return

            if norm in ("odswiez", "odśwież", "refresh", "new", "nowe"):
                if active:
                    await self.send(
                        "Nie można odświeżyć Tablicy Zleceń przy aktywnym kontrakcie."
                    )
                    return
                offers = self.generate_bounty_offers()
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=offers, active={},
                    completed_count=state.get("completed_count", 0),
                )
                await self.send("Tablica Zleceń została ponownie wylosowana.")
                await self.show_bounty_board()
                return

            accept_text = norm
            for prefix in ("accept ", "przyjmij ", "wez ", "weź "):
                if accept_text.startswith(prefix):
                    accept_text = accept_text[len(prefix):].strip()
                    break
            if accept_text.isdigit():
                if active:
                    progress = int(active.get("progress", 0))
                    needed = int(active.get("needed", 1))
                    await self.send(
                        f"Masz już aktywny kontrakt. Postęp {progress} z {needed}."
                    )
                    return
                index = int(accept_text) - 1
                offers = list(state.get("offers") or [])
                if not (0 <= index < len(offers)):
                    await self.send("Nie ma takiego numeru kontraktu. Wpisz bounty.")
                    return
                active = dict(offers[index])
                active["progress"] = 0
                active["completed"] = False
                self.server.db.save_bounty_board_state(
                    self.account_id, offers=offers, active=active,
                    completed_count=state.get("completed_count", 0),
                )
                await self.send(
                    f"Przyjęto kontrakt: {active['label']}. Postęp 0 z {int(active['needed'])}. "
                    f"Nagroda: {int(active['reward_soul_xp'])} Soul XP i " + currency_reading_text(0, int(active['reward_gold']), 0) + "."
                )
                await self.share_bounty_with_party_v1119(active)
                return

            await self.send(
                "Użycie: bounty; bounty accept <1-3>; bounty aktywne; "
                "bounty odbierz; bounty porzuć lub bounty porzuc; bounty odśwież."
            )

    async def advance_bounty(self, kind, target=None, amount=1):
            state = self.server.db.bounty_board_state(self.account_id)
            active = state.get("active") or {}
            if not active:
                return False
            kind = str(kind or "")
            if str(active.get("kind")) != kind:
                return False
            if kind == "kill":
                wanted = canonical_bestiary_template_id(active.get("target"))
                actual = canonical_bestiary_template_id(target)
                if wanted != actual:
                    return False
            old = max(0, int(active.get("progress", 0)))
            needed = max(1, int(active.get("needed", 1)))
            if old >= needed:
                return False
            new = min(needed, old + max(0, int(amount)))
            if new <= old:
                return False
            active["progress"] = new
            active["completed"] = new >= needed
            self.server.db.save_bounty_board_state(
                self.account_id,
                offers=state.get("offers", []),
                active=active,
                completed_count=state.get("completed_count", 0),
            )
            if new >= needed:
                await self.send(
                    f"Kontrakt: {active.get('label', 'Kontrakt')}. Postęp {new} z {needed}. "
                    "Cel wykonany. Użyj bounty odbierz."
                )
            else:
                await self.send(
                    f"Kontrakt: {active.get('label', 'Kontrakt')}. Postęp {new} z {needed}."
                )
            return True
