# -*- coding: utf-8 -*-
"""Courier delivery, Courier Guild and postal achievements session services."""

import hashlib
import random
import time

from config.postal import (
    COURIER_ALL_CITIES_ACHIEVEMENT_V0540,
    COURIER_ALL_PACKAGE_TYPES_ACHIEVEMENT_V0540,
    COURIER_CITY_ROOM_TO_NAME_V0530,
    COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550,
    COURIER_DELIVERY_ACHIEVEMENTS_V0540,
    COURIER_PACKAGE_CLASSES_V0530,
    COURIER_PACKAGE_TYPE_ACHIEVEMENTS_V0550,
    COURIER_RANKS_V0530,
    COURIER_REPUTATION_MAX_V0530,
    CITY_REPUTATION_MAX_V0710,
    CITY_REPUTATION_RANKS_V0710,
    POSTAL_CITY_HUBS_V0522,
    POSTAL_OFFERS_PER_CITY_V0522,
    POSTAL_REFRESH_SECONDS_V0522,
    courier_next_rank_v0530,
    courier_rank_for_reputation_v0530,
    courier_unlocked_package_keys_v0530,
    city_rank_for_reputation_v0710,
)
from player.session_mixins.inventory_equipment import CURRENCY_SQLITE_SAFE_TOTAL
from player.session_mixins.shops_teachers import currency_reading_text
from player.session_mixins.skill_learning import normalize_lookup_text


class SessionCourierDeliveryMixin:
    def postal_city_for_room_v0522(self, room_id=None):
        room_id = str(room_id or self.character.room_id)
        for city_name, hub_room in POSTAL_CITY_HUBS_V0522.items():
            if hub_room == room_id:
                return city_name
        return None

    def courier_city_for_room_v0530(self, room_id=None):
        return COURIER_CITY_ROOM_TO_NAME_V0530.get(str(room_id or self.character.room_id))

    def courier_record_current_city_v0530(self):
        city = self.courier_city_for_room_v0530()
        if city:
            return self.server.db.record_courier_city_visit_v0530(self.account_id, city)
        return self.server.db.courier_guild_state_v0530(self.account_id)

    async def add_city_reputation_v0710(self, city_name, amount=1, reason="", announce=True):
        city_name = str(city_name or "").strip()
        if city_name not in POSTAL_CITY_HUBS_V0522:
            return 1
        old = self.server.db.city_reputation_v0710(self.account_id, city_name)
        new = self.server.db.add_city_reputation_v0710(self.account_id, city_name, amount)
        if announce and new != old:
            old_rank = city_rank_for_reputation_v0710(old)
            new_rank = city_rank_for_reputation_v0710(new)
            msg = f"Reputacja miasta {city_name}: +{max(0, new-old)}, teraz {new}/{CITY_REPUTATION_MAX_V0710}."
            if new_rank["name"] != old_rank["name"]:
                msg += f" Nowa ranga: {new_rank['name']}."
            await self.send(msg)
        return new

    async def show_city_reputation_v0710(self, args=""):
        query = normalize_lookup_text(args)
        reps = self.server.db.city_reputations_v0710(self.account_id)
        if query:
            matches = []
            for city in POSTAL_CITY_HUBS_V0522:
                if query in normalize_lookup_text(city):
                    matches.append(city)
            if not matches:
                await self.send("Nie znam takiego miasta. Wpisz reputacjamiast bez nazwy, aby zobaczyć wszystkie.")
                return
            city = matches[0]
            rep = int(reps.get(city, 1) or 1)
            rank = city_rank_for_reputation_v0710(rep)
            await self.send(
                f"REPUTACJA MIASTA: {city}. {rep}/{CITY_REPUTATION_MAX_V0710}. "
                f"Ranga: {rank['name']}. Bonus do wypłat kurierskich kierowanych do tego miasta: +{int(round(rank['courier_bonus']*100))}%."
            )
            return
        await self.send(f"REPUTACJE MIAST: {len(POSTAL_CITY_HUBS_V0522)} miast i osad.")
        for city in POSTAL_CITY_HUBS_V0522:
            rep = int(reps.get(city, 1) or 1)
            rank = city_rank_for_reputation_v0710(rep)
            await self.send(f"{city}: {rep}/{CITY_REPUTATION_MAX_V0710}, {rank['name']}.")
        await self.send("Szczegóły: reputacjamiast <miasto>. Reputację zdobywasz lokalnymi questami i dostawami paczek.")

    def postal_refresh_slot_v0522(self, now=None):
        now = int(time.time() if now is None else now)
        return now // POSTAL_REFRESH_SECONDS_V0522

    def postal_seconds_to_refresh_v0522(self, now=None):
        now = int(time.time() if now is None else now)
        elapsed = now % POSTAL_REFRESH_SECONDS_V0522
        return POSTAL_REFRESH_SECONDS_V0522 - elapsed if elapsed else POSTAL_REFRESH_SECONDS_V0522

    def courier_rep_gain_v0530(self, offer):
        distance = max(0, int((offer or {}).get('distance', 0) or 0))
        package_key = str((offer or {}).get('package_key') or 'zwykla')
        spec = COURIER_PACKAGE_CLASSES_V0530.get(package_key, COURIER_PACKAGE_CLASSES_V0530['zwykla'])
        return max(1, min(12, 1 + distance // 25 + int(spec.get('rep_bonus', 0) or 0)))

    async def courier_unlock_titles_v0530(self, reputation):
        reputation = max(1, min(COURIER_REPUTATION_MAX_V0530, int(reputation or 1)))
        for threshold, title_name, _payout_bonus in COURIER_RANKS_V0530:
            if reputation >= threshold:
                await self.unlock_title(
                    f"courier_guild_v0530:{threshold}", title_name, announce=True
                )

    async def courier_sync_achievements_v0540(self, announce=True):
        delivery = self.server.db.postal_delivery_state_v0522(self.account_id)
        guild = self.server.db.courier_guild_state_v0530(self.account_id)
        completed = max(0, int(delivery.get('completed_count', 0) or 0))
        visited = set(guild.get('visited_cities') or [])
        unlocked_now = []

        for threshold, achievement_id, name, tier in COURIER_DELIVERY_ACHIEVEMENTS_V0540:
            if completed >= int(threshold):
                if self.server.db.unlock_achievement(self.account_id, achievement_id, name, tier):
                    unlocked_now.append(name)

        achievement_id, name, tier = COURIER_ALL_CITIES_ACHIEVEMENT_V0540
        if set(POSTAL_CITY_HUBS_V0522).issubset(visited):
            if self.server.db.unlock_achievement(self.account_id, achievement_id, name, tier):
                unlocked_now.append(name)

        completed_types = {
            key for key in COURIER_PACKAGE_CLASSES_V0530
            if (
                self.server.db.achievement_metric(self.account_id, f"courier_package_type:{key}") >= 1
                or self.server.db.achievement_metric(self.account_id, f"courier_package_type_count:{key}") >= 1
            )
        }
        achievement_id, name, tier = COURIER_ALL_PACKAGE_TYPES_ACHIEVEMENT_V0540
        if set(COURIER_PACKAGE_CLASSES_V0530).issubset(completed_types):
            if self.server.db.unlock_achievement(self.account_id, achievement_id, name, tier):
                unlocked_now.append(name)

        city_counts = {}
        for city_name, achievement in COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550.items():
            count = self.server.db.achievement_metric(
                self.account_id, f"courier_destination_count:{city_name}"
            )
            city_counts[city_name] = count
            if count >= 100:
                achievement_id, name, tier = achievement
                if self.server.db.unlock_achievement(self.account_id, achievement_id, name, tier):
                    unlocked_now.append(name)

        package_type_counts = {}
        for key, achievement in COURIER_PACKAGE_TYPE_ACHIEVEMENTS_V0550.items():
            count = self.server.db.achievement_metric(
                self.account_id, f"courier_package_type_count:{key}"
            )
            package_type_counts[key] = count
            if count >= 100:
                achievement_id, name, tier = achievement
                if self.server.db.unlock_achievement(self.account_id, achievement_id, name, tier):
                    unlocked_now.append(name)

        if announce:
            for name in unlocked_now:
                await self.send(f"Osiągnięcie kurierskie: {name}.")
        return {
            'completed': completed,
            'visited': visited,
            'completed_types': completed_types,
            'city_counts': city_counts,
            'package_type_counts': package_type_counts,
            'unlocked_now': unlocked_now,
        }

    async def postal_show_achievements_v0540(self):
        self.courier_record_current_city_v0530()
        state = await self.courier_sync_achievements_v0540(announce=True)
        completed = int(state['completed'])
        visited = set(state['visited'])
        completed_types = set(state['completed_types'])
        await self.send("OSIĄGNIĘCIA KURIERSKIE:")
        for threshold, _achievement_id, name, _tier in COURIER_DELIVERY_ACHIEVEMENTS_V0540:
            status = "UKOŃCZONE" if completed >= threshold else f"{completed}/{threshold}"
            await self.send(f"{name}: {status}.")
        city_total = len(POSTAL_CITY_HUBS_V0522)
        city_status = "UKOŃCZONE" if len(visited) >= city_total else f"{len(visited)}/{city_total}"
        await self.send(f"Kurier: Wszystkie miasta: {city_status}.")
        type_total = len(COURIER_PACKAGE_CLASSES_V0530)
        type_status = "UKOŃCZONE" if len(completed_types) >= type_total else f"{len(completed_types)}/{type_total}"
        await self.send(f"Kurier: Wszystkie typy paczek: {type_status}.")
        if completed_types:
            names = [COURIER_PACKAGE_CLASSES_V0530[key]['name'] for key in COURIER_PACKAGE_CLASSES_V0530 if key in completed_types]
            await self.send("Ukończone typy: " + ", ".join(names) + ".")
        await self.send("OSIĄGNIĘCIA ZA MIASTA — po 100 dostaw:")
        for city_name in POSTAL_CITY_HUBS_V0522:
            count = int(state.get('city_counts', {}).get(city_name, 0) or 0)
            await self.send(
                f"{city_name}: {'UKOŃCZONE' if count >= 100 else f'{count}/100'}."
            )
        await self.send("OSIĄGNIĘCIA ZA TYPY PACZEK — po 100 dostaw:")
        for key, spec in COURIER_PACKAGE_CLASSES_V0530.items():
            count = int(state.get('package_type_counts', {}).get(key, 0) or 0)
            await self.send(
                f"{spec['name']}: {'UKOŃCZONE' if count >= 100 else f'{count}/100'}."
            )

    def postal_offers_v0522(self, origin_city, now=None):
        origin_city = str(origin_city or '')
        origin_room = POSTAL_CITY_HUBS_V0522.get(origin_city)
        if not origin_room:
            return []
        guild_state = self.server.db.courier_guild_state_v0530(self.account_id)
        reputation = int(guild_state.get('reputation', 1) or 1)
        rank = courier_rank_for_reputation_v0530(reputation)
        eligible_keys = list(courier_unlocked_package_keys_v0530(reputation)) or ['zwykla']
        # v0.55.0: once prestige deliveries unlock, keep one visible in every
        # refreshed offer list instead of making the endgame class depend on luck.
        prestige_unlocked = 'prestizowa' in eligible_keys
        slot = self.postal_refresh_slot_v0522(now)
        seed_text = f"soulbound-v0530-postal:{slot}:{origin_room}:{reputation}"
        seed = int.from_bytes(hashlib.sha256(seed_text.encode('utf-8')).digest()[:8], 'big')
        rng = random.Random(seed)
        destinations = [name for name in POSTAL_CITY_HUBS_V0522 if name != origin_city]
        rng.shuffle(destinations)
        destinations = destinations[:min(POSTAL_OFFERS_PER_CITY_V0522, len(destinations))]
        rng.shuffle(eligible_keys)
        if prestige_unlocked:
            eligible_keys = ['prestizowa'] + [key for key in eligible_keys if key != 'prestizowa']
        offers = []
        for index, destination_city in enumerate(destinations, 1):
            destination_room = POSTAL_CITY_HUBS_V0522[destination_city]
            route = self.shortest_path(origin_room, destination_room)
            distance = len(route) if route is not None else 0
            package_key = eligible_keys[(index - 1) % len(eligible_keys)]
            spec = COURIER_PACKAGE_CLASSES_V0530[package_key]
            base = max(300, 180 + distance * 95)
            city_rep = self.server.db.city_reputation_v0710(self.account_id, destination_city)
            city_rank = city_rank_for_reputation_v0710(city_rep)
            payout_mult = (
                float(spec['reward_mult'])
                * (1.0 + float(rank['payout_bonus']))
                * (1.0 + float(city_rank['courier_bonus']))
            )
            reward = min(CURRENCY_SQLITE_SAFE_TOTAL, max(1, int(round(base * payout_mult))))
            offers.append({
                'number': index,
                'offer_slot': slot,
                'origin_city': origin_city,
                'origin_room': origin_room,
                'destination_city': destination_city,
                'destination_room': destination_room,
                'package_key': package_key,
                'package_name': spec['name'],
                'package_description': spec['description'],
                'distance': distance,
                'reward_coins': reward,
                'courier_reputation_at_offer': reputation,
                'courier_rank_at_offer': rank['name'],
                'destination_city_reputation_at_offer': city_rep,
                'destination_city_rank_at_offer': city_rank['name'],
            })
        return offers

    def postal_guide_query_v0522(self, active):
        if str((active or {}).get('destination_room') or '') == 'courier_office':
            return 'poczta'
        return str((active or {}).get('destination_city') or 'miasto')

    async def postal_show_guild_v0530(self):
        state = self.courier_record_current_city_v0530()
        await self.courier_sync_achievements_v0540(announce=True)
        reputation = int(state.get('reputation', 1) or 1)
        rank = courier_rank_for_reputation_v0530(reputation)
        next_rank = courier_next_rank_v0530(reputation)
        await self.courier_unlock_titles_v0530(reputation)
        unlocked = [COURIER_PACKAGE_CLASSES_V0530[key]['name'] for key in courier_unlocked_package_keys_v0530(reputation)]
        await self.send(
            f"GILDIA KURIERÓW. Reputacja: {reputation}/{COURIER_REPUTATION_MAX_V0530}. "
            f"Ranga: {rank['name']}. Bonus wypłaty: +{int(round(rank['payout_bonus']*100))}%. "
            "Wszystkie zlecenia kurierskie są bez ryzyka losowej utraty lub obniżenia nagrody."
        )
        if next_rank:
            await self.send(
                f"Następna ranga: {next_rank['name']} przy reputacji {next_rank['threshold']}. "
                f"Brakuje {max(0, int(next_rank['threshold']) - reputation)}."
            )
        else:
            await self.send("Osiągnięto maksymalną rangę: Mistrz Szlaków.")
        await self.send("Odblokowane przesyłki: " + ", ".join(unlocked) + ".")

    async def postal_show_statistics_v0530(self):
        self.courier_record_current_city_v0530()
        await self.courier_sync_achievements_v0540(announce=True)
        guild = self.server.db.courier_guild_state_v0530(self.account_id)
        delivery = self.server.db.postal_delivery_state_v0522(self.account_id)
        visited = list(guild.get('visited_cities') or [])
        await self.send(
            "STATYSTYKI KURIERA: "
            f"dostarczone paczki {int(delivery.get('completed_count',0) or 0)}; "
            f"łączny zarobek {currency_reading_text(int(guild.get('total_earnings',0) or 0),0,0)}; "
            f"najdłuższa trasa {int(guild.get('longest_route',0) or 0)} przejść; "
            f"odwiedzone miasta {len(visited)}/{len(POSTAL_CITY_HUBS_V0522)}."
        )
        await self.send("Odwiedzone: " + (", ".join(visited) if visited else "brak") + ".")

    async def postal_show_status_v0522(self):
        self.courier_record_current_city_v0530()
        state = self.server.db.postal_delivery_state_v0522(self.account_id)
        active = state.get('active') or {}
        if not active:
            await self.send(
                f"Nie niesiesz teraz paczki. Dostarczone paczki: {state.get('completed_count', 0)}. "
                "Idź do punktu pocztowego i wpisz poczta lista."
            )
            return
        await self.send(
            f"AKTYWNA PACZKA: {active.get('package_name','Paczka')}. "
            f"Z: {active.get('origin_city','?')}. Do: {active.get('destination_city','?')}. "
            f"Nagroda: {currency_reading_text(int(active.get('reward_coins',0) or 0),0,0)}. "
            f"Cel podróży: prowadz {self.postal_guide_query_v0522(active)}."
        )

    async def postal_show_offers_v0522(self, now=None):
        self.courier_record_current_city_v0530()
        await self.courier_sync_achievements_v0540(announce=True)
        city = self.postal_city_for_room_v0522()
        if not city:
            await self.send(
                "Listę paczek można sprawdzić w punkcie pocztowym miasta. "
                "Wpisz walk miasta, aby zobaczyć wszystkie miasta i osady."
            )
            return
        guild = self.server.db.courier_guild_state_v0530(self.account_id)
        rank = courier_rank_for_reputation_v0530(guild.get('reputation', 1))
        offers = self.postal_offers_v0522(city, now=now)
        await self.send(
            f"POCZTA — {city}. PACZKI DO DOSTARCZENIA. "
            f"Gildia Kurierów: {rank['name']}, reputacja {guild.get('reputation',1)}/400."
        )
        for offer in offers:
            await self.send(
                f"{offer['number']}. {offer['package_name']} do: {offer['destination_city']}. "
                f"Trasa: około {offer['distance']} przejść. "
                f"Nagroda: {currency_reading_text(offer['reward_coins'],0,0)}. "
                f"{offer.get('package_description','')}"
            )
        left = self.postal_seconds_to_refresh_v0522(now=now)
        minutes, seconds = divmod(left, 60)
        await self.send(
            f"Lista odświeża się co 15 minut. Następne odświeżenie za {minutes} min {seconds} s. "
            "Weź paczkę: paczka <numer> albo poczta wez <numer>. "
            "Profil: poczta gildia. Statystyki: poczta statystyki."
        )

    async def postal_accept_v0522(self, raw_number):
        state = self.server.db.postal_delivery_state_v0522(self.account_id)
        if state.get('active'):
            await self.send("Masz już aktywną paczkę. Wpisz poczta status albo poczta porzuc.")
            return
        city = self.postal_city_for_room_v0522()
        if not city:
            await self.send("Paczkę można odebrać tylko w punkcie pocztowym miasta. Wpisz walk miasta.")
            return
        self.server.db.record_courier_city_visit_v0530(self.account_id, city)
        value = str(raw_number or '').strip()
        if not value.isdigit():
            await self.send("Podaj numer z aktualnej listy, np. paczka 2.")
            return
        offers = self.postal_offers_v0522(city)
        number = int(value)
        if number < 1 or number > len(offers):
            await self.send("Nie ma takiej paczki na aktualnej liście. Wpisz poczta lista.")
            return
        offer = dict(offers[number - 1])
        offer['accepted_at'] = int(time.time())
        # v0.54.0: erase legacy risk/deadline state even if an old client or
        # saved offer carried these fields. Courier deliveries are deterministic.
        for legacy_key in ('risk_probability', 'risk_percent', 'incident_penalty', 'incident', 'time_limit_seconds', 'deadline_at'):
            offer.pop(legacy_key, None)
        self.server.db.save_postal_delivery_state_v0522(self.account_id, active=offer)
        await self.courier_sync_achievements_v0540(announce=True)
        await self.send(
            f"Odbierasz: {offer['package_name']}. Cel: {offer['destination_city']}. "
            f"Nagroda: {currency_reading_text(offer['reward_coins'],0,0)}. "
            f"Możesz wpisać prowadz {self.postal_guide_query_v0522(offer)}."
        )

    async def postal_deliver_v0522(self):
        state = self.server.db.postal_delivery_state_v0522(self.account_id)
        active = state.get('active') or {}
        if not active:
            await self.send("Nie masz aktywnej paczki do dostarczenia.")
            return
        if self.character.room_id != active.get('destination_room'):
            await self.send(
                f"Ta paczka jest dla: {active.get('destination_city','?')}. "
                f"Wpisz prowadz {self.postal_guide_query_v0522(active)}."
            )
            return
        destination_city = str(active.get('destination_city') or '')
        if destination_city:
            self.server.db.record_courier_city_visit_v0530(self.account_id, destination_city)
        # v0.54.0: deliveries are risk-free. Legacy incident/deadline fields
        # from v0.53.0 are deliberately ignored and never reduce the reward.
        reward = max(0, int(active.get('reward_coins', 0) or 0))
        wallet = self.character_wallet_silver_value()
        self.character.silver = min(CURRENCY_SQLITE_SAFE_TOTAL, wallet + reward)
        self.character.gold = 0
        self.character.mithril = 0
        self.server.db.save_character(self.character)
        completed = int(state.get('completed_count', 0) or 0) + 1
        self.server.db.save_postal_delivery_state_v0522(
            self.account_id, active={}, completed_count=completed
        )
        guild = self.server.db.courier_guild_state_v0530(self.account_id)
        rep_gain = self.courier_rep_gain_v0530(active)
        new_rep = min(COURIER_REPUTATION_MAX_V0530, int(guild.get('reputation',1) or 1) + rep_gain)
        total_earnings = min(
            CURRENCY_SQLITE_SAFE_TOTAL,
            int(guild.get('total_earnings',0) or 0) + reward,
        )
        longest_route = max(
            int(guild.get('longest_route',0) or 0),
            max(0, int(active.get('distance',0) or 0)),
        )
        guild = self.server.db.save_courier_guild_state_v0530(
            self.account_id,
            reputation=new_rep,
            total_earnings=total_earnings,
            longest_route=longest_route,
        )
        city_rep_gain = 0
        new_city_rep = 1
        if destination_city:
            city_rep_gain = max(1, min(6, 1 + max(0, int(active.get('distance',0) or 0)) // 30))
            new_city_rep = await self.add_city_reputation_v0710(
                destination_city, city_rep_gain, reason="courier_delivery", announce=False
            )
        try:
            self.server.db.add_lifetime_stat(self.account_id, 'packages_delivered', 1)
            self.server.db.add_lifetime_stat(self.account_id, 'courier_earnings', reward)
            self.server.db.set_lifetime_stat_max(self.account_id, 'courier_longest_route', longest_route)
        except Exception:
            pass
        package_key = str(active.get('package_key') or 'zwykla')
        self.server.db.set_achievement_metric_max(
            self.account_id, f"courier_package_type:{package_key}", 1
        )
        self.server.db.add_achievement_metric(
            self.account_id, f"courier_package_type_count:{package_key}", 1
        )
        if destination_city:
            self.server.db.add_achievement_metric(
                self.account_id, f"courier_destination_count:{destination_city}", 1
            )
        await self.courier_unlock_titles_v0530(new_rep)
        await self.courier_sync_achievements_v0540(announce=True)
        rank = courier_rank_for_reputation_v0530(new_rep)
        try:
            package_name = str((COURIER_PACKAGE_CLASSES_V0530.get(package_key) or {}).get('name') or package_key)
            self.server.db.record_activity_v0560(
                self.account_id, "dostawa", f"Paczka do {destination_city or '?'}",
                f"Typ: {package_name}. Nagroda: {currency_reading_text(reward,0,0)}."
            )
        except Exception:
            pass
        await self.send(
            f"Paczka dostarczona do: {destination_city or '?'}. "
            f"Nagroda: {currency_reading_text(reward,0,0)}. "
            f"Reputacja Gildii Kurierów: +{rep_gain}, teraz {new_rep}/400 ({rank['name']}). "
            + (f"Reputacja miasta {destination_city}: +{city_rep_gain}, teraz {new_city_rep}/400. " if destination_city else "")
            + f"Łącznie dostarczonych paczek: {completed}."
        )
        await self.send("Możesz od razu sprawdzić nowe zlecenia: poczta lista.")

    async def handle_postal_v0522(self, args=''):
        raw = str(args or '').strip()
        norm = normalize_lookup_text(raw)
        if not raw or norm in ('lista','list','paczki','oferty','offers'):
            await self.postal_show_offers_v0522()
            return
        if norm in ('status','stan','info'):
            await self.postal_show_status_v0522()
            return
        if norm in ('gildia','guild','reputacja','rep','ranga','rank'):
            await self.postal_show_guild_v0530()
            return
        if norm in ('statystyki','staty','stats','statistics'):
            await self.postal_show_statistics_v0530()
            return
        if norm in ('osiagniecia','osiągnięcia','achievements','achievement'):
            await self.postal_show_achievements_v0540()
            return
        if norm in ('dostarcz','deliver','oddaj'):
            await self.postal_deliver_v0522()
            return
        if norm in ('porzuc','porzuć','abandon','cancel'):
            state = self.server.db.postal_delivery_state_v0522(self.account_id)
            if not state.get('active'):
                await self.send("Nie masz aktywnej paczki.")
                return
            abandoned = int(state.get('abandoned_count', 0) or 0) + 1
            self.server.db.save_postal_delivery_state_v0522(
                self.account_id, active={}, abandoned_count=abandoned
            )
            await self.send("Porzucasz aktywną dostawę. Możesz wziąć nową paczkę z aktualnej listy.")
            return
        parts = raw.split(maxsplit=1)
        first = normalize_lookup_text(parts[0]) if parts else ''
        if first in ('wez','weź','take','odbierz','accept'):
            await self.postal_accept_v0522(parts[1] if len(parts) > 1 else '')
            return
        if raw.isdigit():
            await self.postal_accept_v0522(raw)
            return
        await self.send(
            "Poczta: poczta lista, paczka <numer>, poczta wez <numer>, "
            "poczta status, poczta dostarcz, poczta porzuc, poczta gildia, "
            "poczta statystyki, poczta osiągnięcia."
        )
