# -*- coding: utf-8 -*-
"""Oryginalne metody wydzielone w v109 bez zmiany algorytmow."""
from __future__ import annotations
from datetime import datetime,timezone
from data.mobs import MOB_TEMPLATES
from core.mines_threat import ITEMS
from network.protocol_gameplay_utils import (BOSS_CHEST_OPENED_CATEGORY_V11332,_boss_floor_chest_spec,boss_chest_reward_roll,boss_floor_chest_name,boss_floor_chest_state_id,boss_floor_key_id)
from ..admin_tools import boss_chest_should_restore_v1288

class AdminBossChestsV109Mixin:
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

