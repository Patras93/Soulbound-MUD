# -*- coding: utf-8 -*-
"""Combat victory, loot, quest credit and reward distribution.

v0.47.0: explicit combat architecture. Late-overridden reward helpers are
resolved lazily at use time so historical final behaviour remains unchanged.
"""
import random
import time

from core.bootstrap_economy_professions import SILVER_PER_GOLD, V019_SAFE_INT, currency_reading_text
from core.mines_threat import v0866_is_boss_template
from core.progression_600 import CHARACTER_MAX_LEVEL
from core.progression_resources import v0190_mob_rank, v0190_mob_stage
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from events.contracts import MobDefeatedEvent, PlayerMobKillProgressionEvent, PlayerMobKillQuestEvent
from network.protocol_gameplay_utils import (
    BOSS_CHEST_OPENED_CATEGORY_V11332,
    boss_floor_chest_state_id,
    mob_respawn_seconds,
)
from systems.dungeons_regions import is_astral_boss_floor, is_crypt_boss_floor
from systems.equipment_crafting import (
    GUILD_CLASS_QUESTS, LEGENDARY_CLASS_RELIC_BY_CLASS_TIER,
    LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER,
)
from systems.drop_excitement import authored_drop_chance_v11329
from systems.dungeon_experience_v1285 import dungeon_recipient_xp_v1286
from systems.legendary_reborn import boss_legendary_roll_v1150
from systems.infinite_equipment import infinite_equipment_variant_for_drop
from systems.elemental_combat import mob_element_affinities_v11339
from systems.milestone import dungeon_party_bonus_v0320
from systems.combat_profile_records import record_combat_profile_v11341
from world.dynamic_content import (
    BESTIARY_CATALOG, BOSS_COLLECTION_CATALOG, canonical_bestiary_template_id,
    quest_kill_targets_v0389,
)
from world.economy_quests import legendary_loot_mastery_for_floor, milestone_boss_tier
from world.generation_systems import V020_GAUNTLETS, V020_MYTHIC_WORLD_BOSS_SECONDS
from world.runtime_progression import v0210_endless_gauntlet_identity
from world.uoss_superboss_world import UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331
from world.uoss_superboss_runtime import (
    mark_superboss_clear_v11135,
    superboss_key_from_template_v11135,
    superboss_personal_reward_v11135,
    superboss_shared_drop_v11135,
    advance_superboss_series_v11138,
    superboss_helper_release_v1146,
)


def party_drop_recipients_v0359(item_id, recipients):
    """Return every eligible local party member for a successful mob drop."""
    return list(recipients or [])


def _final_combat_reward(*args, **kwargs):
    # This function is historically overridden through several world layers.
    # Importing it only when combat resolves preserves the final v0.46 behaviour.
    from world.global_difficulty_overdrive import v0190_combat_reward
    return v0190_combat_reward(*args, **kwargs)


def _final_boss_floor_identity(*args, **kwargs):
    # Magitek installs the final implementation after Session is assembled.
    from world.magitek_infinite import boss_floor_identity
    return boss_floor_identity(*args, **kwargs)


def _v11323_mob_trophy_spec(template):
    # Loaded late like the final reward wrapper so the finished difficulty/rank
    # view is used instead of an early compatibility snapshot.
    from world.global_difficulty_overdrive import mob_trophy_spec_v11323
    return mob_trophy_spec_v11323(template)


def _v11325_legacy_identity_drop_spec(template):
    from systems.legacy_value_sweep import legacy_identity_drop_spec_v11325
    return legacy_identity_drop_spec_v11325(template, random.random())



def _v0711_crypt_soul_shard_guaranteed(template_id, template):
    """Return True for Crypt/Mythic Crypt combat templates, including variants."""
    if not isinstance(template, dict):
        return False
    try:
        if int(template.get("crypt_floor", 0) or 0) > 0:
            return True
        if int(template.get("mythic_crypt_floor", 0) or 0) > 0:
            return True
    except (TypeError, ValueError):  # AUDIT_INTENTIONAL_PASS: malformed floor metadata falls back to other Crypt markers
        pass
    if template.get("crypt_boss") or template.get("mythic_crypt_boss"):
        return True
    if str(template_id) in {"skeleton", "crypt_wraith"}:
        return True
    for key in ("elite_base_template", "rare_base_template", "base_template", "template_id"):
        base_id = str(template.get(key) or "")
        if base_id in {"skeleton", "crypt_wraith"}:
            return True
        base = globals().get("MOB_TEMPLATES", {}).get(base_id)
        if isinstance(base, dict):
            try:
                if int(base.get("crypt_floor", 0) or 0) > 0 or int(base.get("mythic_crypt_floor", 0) or 0) > 0:
                    return True
            except (TypeError, ValueError):  # AUDIT_INTENTIONAL_PASS: malformed base-floor metadata is treated as non-Crypt
                pass
    return False

async def _run_with_deferred_kill_commits_v11125(session, callback, *args, **kwargs):
    """Batch commit-heavy kill progression into one SQLite flush."""
    with session.server.db.conn.deferred_commits():
        return await callback(session, *args, **kwargs)


def deferred_kill_commits_v11125(callback):
    async def wrapped(self, mob, *args, **kwargs):
        # v1.40.0: kill events can converge from AoE, realtime attacks and
        # mercenary hits in the same asyncio loop. Claim the MobState BEFORE
        # the first await, otherwise two callbacks may award the same kill.
        # No permanent lock: a failed callback can be retried, and respawning
        # bosses keep their normal reward flow on their next real death.
        if mob is None or not getattr(mob, "alive", False):
            return None
        if getattr(mob, "v1400_kill_in_progress", False):
            return None
        mob.v1400_kill_in_progress = True
        try:
            return await _run_with_deferred_kill_commits_v11125(
                self, callback, mob, *args, **kwargs
            )
        finally:
            mob.v1400_kill_in_progress = False
    wrapped.__name__ = callback.__name__
    wrapped.__doc__ = callback.__doc__
    wrapped.__wrapped__ = callback
    return wrapped

class SessionCombatRewardsMixin:
    def class_for_milestone_loot(self):
                active = self.active_class_names()
                if active:
                    return active[0]
                return self.character.class_name

    async def grant_milestone_boss_loot(self, template, floor):
                marker = milestone_boss_tier(floor)
                if not marker:
                    return
                class_name = self.class_for_milestone_loot()
                if class_name not in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER:
                    return
                mastery = legendary_loot_mastery_for_floor(floor)
                set_pool = list(LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER[class_name][mastery])
                discovered_eq = self.server.db.collection_entry_ids(self.account_id, "equipment")
                missing = [item_id for item_id in set_pool if item_id not in discovered_eq]
                set_item = random.choice(missing or set_pool)
                self.server.db.add_item(self.account_id, set_item, 1)
                await self.record_item_collection(
                    set_item, source=template.get("name", "Boss kamienia milowego"), announce=True
                )
                boss_id = str(template.get("template_id") or "")
                if boss_id:
                    self.server.db.add_boss_codex_drop(self.account_id, boss_id, set_item)
                await self.send(
                    f"Loot setowy klasy {class_name}: {ITEMS[set_item]['name']}. "
                    f"Wymaga Biegłości {mastery}."
                )
                if marker == 100:
                    relic_id = LEGENDARY_CLASS_RELIC_BY_CLASS_TIER[class_name][mastery]
                    self.server.db.add_item(self.account_id, relic_id, 1)
                    await self.record_item_collection(
                        relic_id, source=template.get("name", "Boss setnego piętra"), announce=True
                    )
                    if boss_id:
                        self.server.db.add_boss_codex_drop(self.account_id, boss_id, relic_id)
                    await self.send(
                        f"Legendarny loot klasy {class_name}: {ITEMS[relic_id]['name']}. "
                        f"Wymaga Biegłości {mastery}."
                    )

    @deferred_kill_commits_v11125
    async def mob_defeated(self, mob):
                # Zwycięstwo, loot, questy i nagrody są zawsze ważne nawet w trybie
                # combat concise. Nie dziedziczą wyciszenia rutynowej auto kolejki.
                self.auto_queue_casting = False
                template = MOB_TEMPLATES[mob.template_id]
                # v1.28.1: all actual killed encounter helpers reward XP, but
                # never gold, items, boss lockouts or repeatable quest kills.
                _summon_kill_v1281 = bool(
                    getattr(mob, "monster_ai_summoned_v1160", False)
                    or getattr(mob, "uoss_summon_parent_v1144", None)
                    or template.get("uoss_superboss_add")
                )
                if _summon_kill_v1281:
                    if getattr(mob, "summon_xp_awarded_v1281", False) or not mob.alive:
                        return
                    # Mark before awaiting progression or broadcasts: simultaneous
                    # kill callbacks cannot collect this summon twice.
                    mob.summon_xp_awarded_v1281 = True
                    mob.alive = False
                    mob.engaged_by = None
                    if getattr(mob, "v016_ephemeral", False):
                        mob.respawn_at = float("inf")
                        mob.v016_expires_at = time.time() - 1
                    else:
                        mob.respawn_at = time.time() + mob_respawn_seconds(template)
                    for _participant in tuple(self.server.sessions):
                        if _participant.combat_mob_key == mob.key:
                            _participant.combat_mob_key = None
                    recipients = self.server.party_sessions(
                        self.account_id, same_room=self.character.room_id
                    ) or [self]
                    _base_xp_v1281 = min(V019_SAFE_INT, max(
                        1, int(template.get("source_xp", 0) or 0),
                        max(1, int(template.get("level", 1) or 1)) * 400,
                    ))
                    for session in sorted(recipients, key=lambda s: s.character.name.lower()):
                        _xp_v1281 = min(V019_SAFE_INT, max(1, int(_base_xp_v1281)))
                        _xp_v1281 = session.apply_double_xp(_xp_v1281)
                        for _stat in session.character.STAT_PROGRESS_FIELDS:
                            for _msg in session.character.add_stat_progress(
                                _xp_v1281, targets=(_stat,), single_level_cap=False,
                            ):
                                await session.send(_msg)
                        await session.grant_combat_soul_xp_v11350(
                            _xp_v1281, content_level=v0190_mob_stage(template),
                            content_scaled=True,
                        )
                        await session.grant_class_xp(
                            _xp_v1281, single_level_cap=False,
                            content_level=v0190_mob_stage(template), content_scaled=True,
                        )
                        for _msg in session.add_character_xp_with_event(
                            _xp_v1281, single_level_cap=False,
                            content_level=v0190_mob_stage(template), content_scaled=True,
                        ):
                            await session.send(_msg)
                        await session.send(
                            f"Pokonujesz pomocnika: {template['name']}. "
                            f"EXP +{_xp_v1281} (postać, klasa, Soul i rozwój statystyk)."
                        )
                    return
                self.server.world.clear_monster_ai_adds_v1160(mob)
                _nemesis_owner = int(template.get("v029_nemesis_owner_account_id", 0) or 0)
                if _nemesis_owner:
                    _resolved = self.server.db.defeat_nemesis_v029(_nemesis_owner)
                    self.server.db.add_collection_entry(_nemesis_owner, "nemesis_defeated_v029", str(template.get("name", mob.template_id)))
                    for _s in list(self.server.sessions):
                        if _s.account_id == _nemesis_owner:
                            await _s.send(
                                f"NEMESIS POKONANY: {template['name']}. Łącznie pokonane Nemesis: {int(_resolved['defeats'] or 0) if _resolved else 1}."
                            )
                            break
                fight_duration_ms = None
                if mob.engaged_at > 0:
                    fight_duration_ms = max(1, int(round((time.monotonic() - mob.engaged_at) * 1000)))
                # Dismiss UOSS encounter summons when the parent boss falls.
                # This keeps the arena safe after the boss's 24h lockout begins.
                if template.get("uoss_unique_superboss_key"):
                    self.server.world.clear_superboss_companions_v1144(mob)
                mob.alive = False
                respawn_seconds = mob_respawn_seconds(template)
                mob.respawn_at = time.time() + respawn_seconds
                mob.engaged_by = None
                corpse=self.server.world.create_corpse(mob)
                if corpse:
                    if corpse.items:
                        await self.send(f"Pozostaje ciało: {corpse.mob_name}. Ma na sobie {len(corpse.items)} elementów ekwipunku. Wpisz ciało albo przeszukaj ciało.")
                    else:
                        await self.send(f"Pozostaje ciało: {corpse.mob_name}. Nie widać na nim ekwipunku.")

                for session in list(self.server.sessions):
                    if session.combat_mob_key == mob.key:
                        session.combat_mob_key = None

                recipients = self.server.party_sessions(
                    self.account_id, same_room=self.character.room_id
                )
                if not recipients:
                    recipients = [self]
                recipients = sorted(
                    recipients, key=lambda s: s.character.name.lower()
                )
                # v1.70.2: fame is earned once per genuinely defeated, placed boss,
                # for each eligible member present in the same room.
                from systems.fame_v1702 import record_fame_kill
                from systems.fame_v1702 import fame_pay_later
                for _fame_session, _fame_region in record_fame_kill(
                    self.server.db.conn, recipients, mob, template
                ):
                    # SQLite permanently credits Fame right after the kill;
                    # the queued bonus EXP remains delayed and restart-safe.
                    await _fame_session.send(
                        'FAME ZALICZONE — nowy cel w terenie '
                        + str(_fame_region) + '. Premia EXP po chwili. '
                        'Sprawdź fame cele lub fame log.')
                    import asyncio
                    asyncio.create_task(fame_pay_later(_fame_session))
                count = len(recipients)

                _deep_apanda_floor = int(
                    template.get("uoss_deep_dungeon_apanda_floor", 0) or 0
                )
                if _deep_apanda_floor > 0:
                    for session in recipients:
                        if session.server.db.add_collection_entry(
                            session.account_id,
                            UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331,
                            str(_deep_apanda_floor),
                        ):
                            await session.send(
                                f"Deep Dungeon: pokonujesz Apandę progu "
                                f"{_deep_apanda_floor}. Zejście niżej jest "
                                "odblokowane dla tej postaci."
                            )

                # v1.11.35: unique UOSS Super Boss completion/reward runtime.
                # Party recipients are already filtered to the same room by the canonical
                # party system above, so every active local participant receives credit.
                _uoss_key = superboss_key_from_template_v11135(template)
                if _uoss_key:
                    _first_clear_sessions = []
                    for session in recipients:
                        if mark_superboss_clear_v11135(session.server.db, session.account_id, _uoss_key):
                            _first_clear_sessions.append(session)
                            if hasattr(session.server.db, 'add_server_chronicle_event_v03811'):
                                session.server.db.add_server_chronicle_event_v03811(
                                    'pierwszy_superboss',
                                    f'{session.character.name} pokonał {template.get("name", _uoss_key)}!',
                                    account_id=session.account_id,
                                    actor_name=session.character.name,
                                    subject_id=_uoss_key,
                                    subject_name=template.get('name', _uoss_key), importance=4,
                                    event_key=f'superboss:first:{session.account_id}:{_uoss_key}')
                        _personal = superboss_personal_reward_v11135(
                            session.server.db, session.account_id, _uoss_key
                        )
                        if _personal:
                            _iid, _label = _personal
                            await session.send(f"Super Boss: otrzymujesz {_label}. Nagroda jest osobista.")
                    if _first_clear_sessions:
                        _personal_drops = superboss_shared_drop_v11135(
                            self.server.db, _first_clear_sessions, _uoss_key
                        )
                        for _winner, _iid in _personal_drops:
                            await _winner.record_item_collection(
                                _iid, source=template.get("name", "Super Boss"), announce=False
                            )
                            await _winner.send(
                                f"Super Boss: otrzymujesz własny unikalny drop: {ITEMS.get(_iid, {}).get('name', _iid)}."
                            )
                    for session in _first_clear_sessions:
                        _series = advance_superboss_series_v11138(
                            session.server.db, session.account_id, _uoss_key
                        )
                        if _series:
                            _stage, _required, _complete = _series
                            await session.send(
                                f"Seria Super Bossa: {_stage} z {_required}."
                                + (" Seria ukończona." if _complete else "")
                            )
                            if _uoss_key == "elementals" and _complete:
                                await session.send(
                                    "Pokonałeś wszystkie osiem Duchów Many. Odblokowano silniejszego przeciwnika."
                                )
                        await session.send(
                            f"Super Boss pokonany: {template.get('name', _uoss_key)}. Kolejna nagroda będzie dostępna po 24 godzinach."
                        )

                if _uoss_key:
                    # All boss targets have been detached above. Release once
                    # for the entire local party after the completed fight.
                    superboss_helper_release_v1146(self, force=True)

                # v0.42.0: the combat producer announces one real defeat;
                # chronicle/analytics consumers subscribe without being embedded here.
                await self.server.events.publish(MobDefeatedEvent(
                    killer_session=self,
                    mob=mob,
                    recipients=tuple(recipients),
                    template_id=mob.template_id,
                    template=template,
                    fight_duration_ms=fight_duration_ms,
                ))

                # v1.22.5: genuine kills advance the hunter board for each
                # eligible present player independently (including party members).
                for session in recipients:
                    for tier, progress, needed in session.server.db.hunter_kill_v1225(session.account_id, mob.template_id, template):
                        await session.send(f'Łowcy {tier}: {progress} z {needed}.' +
                                           (' Zlecenie gotowe, odbierz nagrodę w Sali Łowców.' if progress >= needed else ''))

                # v1.22.0: every same-room participant advances their own
                # active crisis on genuine regional victories. Never on summons.
                if template.get("v1200_region"):
                    for session in recipients:
                        await session.record_world_crisis_kill_v1220(mob, template)

                if template.get("v020_megadungeon_boss"):
                    _mk=str(template.get("v020_mega_key")); _mi=int(template.get("v020_mega_index",0) or 0)
                    for session in recipients:
                        first=session.server.db.mark_boss_floor_cleared(session.account_id,f"v020_mega_{_mk}",_mi)
                        session.server.db.add_collection_entry(session.account_id,"mega_boss_kills_v020",f"{_mk}:{_mi}")
                        if first:
                            await session.send(f"Megaloch: próg {_mi} zaliczony na stałe. Przejście do następnej sekcji pozostanie otwarte po respawnie bossa.")
                if template.get("v020_gauntlet") and int(template.get("v020_gauntlet_round",0) or 0)==5:
                    _gk=str(template.get("v020_gauntlet"))
                    for session in recipients:
                        first=session.server.db.add_collection_entry(session.account_id,"gauntlet_clears_v020",_gk)
                        session.server.db.add_collection_entry(session.account_id,"gauntlet_final_kills_v020",f"{_gk}:{int(time.time()//3600)}")
                        if first: await session.unlock_title(f"v020:gauntlet:{_gk}",f"Pogromca Próby: {V020_GAUNTLETS[_gk]['name']}")
                if template.get("v020_mythic_world_boss"):
                    _bid=canonical_bestiary_template_id(mob.template_id)
                    for session in recipients:
                        session.server.db.add_collection_entry(session.account_id,"mythic_world_kills_v020",f"{_bid}:{int(time.time()//V020_MYTHIC_WORLD_BOSS_SECONDS)}")
                        await session.add_faction_reputation_v016("frontier_watch",75,reason="mythic_world_boss")
                if template.get("v021_endless_gauntlet"):
                    _round=v0210_endless_gauntlet_identity(mob.room_id) or 0
                    for session in recipients:
                        best=session.server.db.mark_endless_gauntlet_round_v021(session.account_id,_round)
                        session.server.db.add_collection_entry(session.account_id,"endless_gauntlet_v021",str(_round))
                        if _round and _round%25==0:
                            await session.unlock_title(f"v021:endless:{_round}",f"Wieczny Pretendent — runda {_round}")
                        await session.send(f"Endless Gauntlet: ukończona runda {_round}. Najlepsza runda {best}.")

                boss_kind, cleared_floor = _final_boss_floor_identity(template)
                if boss_kind and cleared_floor:
                    for session in recipients:
                        # Każdy nowy prawidłowy kill tworzy świeżą skrzynię
                        # dla nagrodzonej postaci/drużyny. Dzięki temu skrzynia
                        # po otwarciu może trwale zniknąć aż do następnego killa.
                        self.server.db.remove_collection_entry(
                            session.account_id,
                            BOSS_CHEST_OPENED_CATEGORY_V11332,
                            boss_floor_chest_state_id(
                                boss_kind, cleared_floor
                            ),
                        )
                        # NVDA: explicit chest notice even if player has the
                        # boss room's map message scrolled away in combat log.
                        await session.send(
                            f'Skrzynia Bossa, piętro {cleared_floor}: '
                            'jest w komnacie pokonanego bossa. '
                            'Przeszukaj ciało, weź klucz i wpisz odklucz.'
                        )
                        first_clear = self.server.db.mark_boss_floor_cleared(
                            session.account_id, boss_kind, cleared_floor
                        )
                        if first_clear:
                            self.server.db.mark_instance_checkpoint(
                                session.account_id, boss_kind, cleared_floor
                            )
                            await session.send(
                                f"Próg bossa {cleared_floor} został zaliczony na stałe. "
                                "Po respawnie boss pozostaje opcjonalny i nie blokuje już dalszej drogi."
                            )
                        if milestone_boss_tier(cleared_floor):
                            await session.grant_milestone_boss_loot(template, cleared_floor)

                boss_floor = (
                    int(template.get("crypt_floor", 0))
                    if template.get("crypt_boss")
                    else 0
                )
                if is_crypt_boss_floor(boss_floor):
                    for session in recipients:
                        before_checkpoint = (
                            self.server.db.crypt_portal(session.account_id)
                        )
                        after_checkpoint = (
                            self.server.db.unlock_crypt_portal(
                                session.account_id, boss_floor
                            )
                        )
                        if after_checkpoint > before_checkpoint:
                            await session.send(
                                f"Odblokowano Portal Krypty do piętra "
                                f"{boss_floor}."
                            )
                            await session.send(
                                "Portal odblokowany. Ten boss został zaliczony; po respawnie jest opcjonalny "
                                "i nie blokuje już zejścia dla tej postaci."
                            )

                astral_boss_floor = (
                    int(template.get("astral_floor", 0))
                    if template.get("astral_boss")
                    else 0
                )
                if is_astral_boss_floor(astral_boss_floor):
                    for session in recipients:
                        before_checkpoint = (
                            self.server.db.astral_portal(
                                session.account_id
                            )
                        )
                        after_checkpoint = (
                            self.server.db.unlock_astral_portal(
                                session.account_id,
                                astral_boss_floor,
                            )
                        )
                        if after_checkpoint > before_checkpoint:
                            await session.send(
                                f"Odblokowano Astralny Portal do poziomu "
                                f"{astral_boss_floor}."
                            )
                            await session.send(
                                "Checkpoint Wieży zapisany. Ten boss został zaliczony; po respawnie jest opcjonalny "
                                "i nie blokuje już drogi w górę dla tej postaci."
                            )

                # v1.13.41: public profile record — strongest opponent ever killed.
                # Uses the opponent's authored XP value, never temporary Double XP/
                # party multipliers, so profile comparisons stay stable.
                for session in recipients:
                    record_combat_profile_v11341(
                        session.server.db,
                        session.account_id,
                        "best_kill",
                        template,
                    )

                for session in recipients:
                    if count > 1:
                        await session.send(
                            f"Drużyna pokonuje: {template['name']}. "
                            f"Nagrody obejmują {count} obecnych członków."
                        )
                    else:
                        await session.send(f"Pokonujesz: {template['name']}.")

                # v1.12.6: brak kary za grę w drużynie.
                # Każdy obecny członek drużyny otrzymuje pełną pulę monet za moba,
                # tak samo jak każdy otrzymuje własne pełne nagrody EXP/progresji.
                _adaptive_reward_mult_v11330=max(
                    1.0,
                    float(getattr(mob,"adaptive_reward_multiplier_v11330",1.0) or 1.0),
                )
                _elite_reward_mult_v11338=max(
                    1.0,
                    float(template.get("elite_reward_multiplier_v11338",1.0) or 1.0),
                )
                _combat_reward_mult_v11338=(
                    _adaptive_reward_mult_v11330 * _elite_reward_mult_v11338
                )
                generated_coins=min(
                    V019_SAFE_INT,
                    max(
                        0,
                        int(round(
                            _final_combat_reward(template,"coins")
                            * _combat_reward_mult_v11338
                        )),
                    ),
                )
                currency_rewards={currency:{s.account_id:0 for s in recipients} for currency in ("silver","gold","mithril")}
                if generated_coins>0:
                    for session in recipients:
                        currency_rewards["silver"][session.account_id]=generated_coins

                _v0927_guild_progressed = set()
                for session in recipients:
                    silver = min(V019_SAFE_INT, int(round(currency_rewards["silver"][session.account_id] * session.v0210_reward_multiplier())))
                    gold = currency_rewards["gold"][session.account_id]
                    mithril = currency_rewards["mithril"][session.account_id]
                    session.character.silver += silver
                    session.character.gold += gold
                    session.character.mithril += mithril

                    if silver or gold or mithril:
                        await session.send(
                            "Nagroda walutowa: "
                            + currency_reading_text(silver, gold, mithril) + "."
                        )

                    # v1.28.6: dungeon XP is normalized per recipient, AFTER
                    # party/adaptive bonuses. Long-term requirements stay intact.
                    xp_profile=session.dynamic_kill_xp_profile(template,room_id=session.character.room_id)
                    # v0.23.0: NIE podbijamy mnożnika do minimum 1.0. To był błąd,
                    # przez który słabsze moby nigdy nie traciły EXP podczas farmy.
                    xp_mult=(
                        float(xp_profile["multiplier"])
                        * session.v0210_reward_multiplier()
                        * _combat_reward_mult_v11338
                    )
                    # Scanner-authored UOSSMUD XP is an exact reward, not an
                    # input to Soulbound's dynamic mob reward generator.
                    source_xp_exact = bool(template.get("source_xp_exact"))
                    source_xp = max(0,int(template.get("source_xp",0) or 0))
                    uoss_full_progression_source_xp_exact = bool(
                        template.get("uoss_full_progression_source_xp_exact")
                    ) and source_xp_exact and source_xp > 0
                    _party_bonus=dungeon_party_bonus_v0320(session)
                    xp_mult*=float(_party_bonus.get("multiplier",1.0))
                    if int(_party_bonus.get("bonus_pct",0))>0:
                        await session.send_combat(f"Dungeon Party Bonus: +{int(_party_bonus['bonus_pct'])}% EXP; członków obok {_party_bonus['members']}; różne klasy {_party_bonus['diverse']}.",detail="full")
                    raw_stat_reward = min(
                        V019_SAFE_INT,
                        source_xp
                        if uoss_full_progression_source_xp_exact
                        else max(
                            0,
                            int(round(
                                _final_combat_reward(template,"stat") * xp_mult
                            )),
                        ),
                    )
                    raw_stat_reward=session.apply_double_xp(raw_stat_reward)
                    stat_rewards=[]
                    for stat_name in session.character.STAT_PROGRESS_FIELDS:
                        stat_rewards.append(raw_stat_reward)
                        for msg in session.character.add_stat_progress(
                            raw_stat_reward,
                            targets=(stat_name,),
                            single_level_cap=False,
                        ):
                            await session.send(msg)
                    stat_reward_text=str(raw_stat_reward)

                    soul_xp_reward = min(
                        V019_SAFE_INT,
                        source_xp
                        if uoss_full_progression_source_xp_exact
                        else max(
                            0,
                            int(round(
                                _final_combat_reward(template,"soul") * xp_mult
                            )),
                        ),
                    )
                    await session.grant_combat_soul_xp_v11350(
                        soul_xp_reward,
                        content_level=v0190_mob_stage(template),
                        content_scaled=True,
                    )

                    class_xp_reward = min(
                        V019_SAFE_INT,
                        source_xp
                        if uoss_full_progression_source_xp_exact
                        else max(
                            0,
                            int(round(
                                _final_combat_reward(template,"class") * xp_mult
                            )),
                        ),
                    )
                    character_xp_reward=min(
                        V019_SAFE_INT,
                        source_xp
                        if source_xp_exact
                        else max(
                            0,
                            int(round(
                                _final_combat_reward(template,"character")
                                * xp_mult
                            )),
                        ),
                    )
                    # v1.28.6: prevent 10+ levels from a single deep-floor
                    # kill. Use this player's REAL level (and active class
                    # levels), not the killed mob's depth, for each XP axis.
                    # Non-dungeon and exact UOSS source XP are unchanged.
                    _double_factor_v1286 = max(1.0, float(session.apply_double_xp(1000)) / 1000.0)
                    _mentor_factor_v1286 = 1.0 + max(0.0, float(session.mentor_bonus_percent_v03050())) / 100.0
                    _guild_factor_v1286 = 1.0 + max(0.0, float(session.guild_bonus_percent_v0926())) / 100.0
                    _active_classes_v1286 = session.active_class_names()
                    _class_level_v1286 = min(
                        (session.class_mastery_level(_name) for _name in _active_classes_v1286),
                        default=1,
                    )
                    # Class XP splits evenly between active classes, so use
                    # the lowest class requirement to protect multiclass alts.
                    class_xp_reward = dungeon_recipient_xp_v1286(
                        template, "class", class_xp_reward, _class_level_v1286,
                        combat_multiplier=xp_mult,
                        downstream_multiplier=_double_factor_v1286 * _mentor_factor_v1286 * _guild_factor_v1286,
                    )
                    soul_xp_reward = dungeon_recipient_xp_v1286(
                        template, "soul", soul_xp_reward, session.character.soul_level,
                        combat_multiplier=xp_mult,
                        downstream_multiplier=_double_factor_v1286 * _mentor_factor_v1286,
                    )
                    character_xp_reward = dungeon_recipient_xp_v1286(
                        template, "character", character_xp_reward,
                        session.character.character_level,
                        combat_multiplier=xp_mult,
                        downstream_multiplier=_double_factor_v1286,
                    )
                    reward_model_text = (
                        f"UOSS source EXP exact na wszystkie osie: {source_xp}"
                        if uoss_full_progression_source_xp_exact
                        else "Balans EXP po walce + korekta poziomu odbiorcy w lochach"
                    )
                    await session.send_combat(
                        f"{reward_model_text}: etap {v0190_mob_stage(template)}, "
                        f"ranga {v0190_mob_rank(template)}, siła postaci {xp_profile['power']}/{CHARACTER_MAX_LEVEL}, "
                        f"siła moba {xp_profile['target']}/{CHARACTER_MAX_LEVEL}, mnożnik x{xp_profile['multiplier']:.2f}; "
                        f"adaptive reward x{_adaptive_reward_mult_v11330:.2f}; "
                        f"elite reward x{_elite_reward_mult_v11338:.2f}; "
                        f"bazowy EXP każdego statu {stat_reward_text}; Soul XP {soul_xp_reward}; "
                        f"Class XP {class_xp_reward}; EXP postaci {character_xp_reward}; "
                        "EXP postaci, klasy i Duszy w lochach nie przeskakuje wielu poziomów za jedno zabicie.",
                        detail="full",
                    )
                    await session.grant_class_xp(
                        class_xp_reward,
                        single_level_cap=False,
                        content_level=v0190_mob_stage(template),
                        content_scaled=True,
                    )
                    for _msg in session.add_character_xp_with_event(
                        character_xp_reward,
                        single_level_cap=False,
                        content_level=v0190_mob_stage(template),
                        content_scaled=True,
                    ):
                        await session.send(_msg)
                    await self.server.events.publish(
                        PlayerMobKillQuestEvent(session=session, mob=mob)
                    )

                    bestiary_row, bestiary_new, bestiary_record = self.server.db.record_bestiary_kill(
                        session.account_id, mob.template_id, fight_duration_ms
                    )
                    bestiary_id = canonical_bestiary_template_id(mob.template_id)
                    if bestiary_id in BOSS_COLLECTION_CATALOG:
                        self.server.db.record_boss_codex_kill(
                            session.account_id, bestiary_id, grouped=(count > 1)
                        )
                        try:
                            self.server.db.record_activity_v0560(
                                session.account_id, "boss", str(template.get("name") or bestiary_id),
                                f"Czas walki: {max(0, int(fight_duration_ms or 0))} ms. "
                                f"Tryb: {'drużyna' if count > 1 else 'solo'}."
                            )
                        except Exception as exc:
                            print(f"COMBAT_ACTIVITY_LOG_ERROR: {type(exc).__name__}: {exc}", flush=True)
                    # v0.9.27: wspólne kontrakty i osiągnięcia Gildii.
                    _guild=session.guild_row_v0926()
                    if _guild:
                        _gid=int(_guild["clan_id"])
                        if _gid not in _v0927_guild_progressed:
                            _v0927_guild_progressed.add(_gid)
                            _is_boss=v0866_is_boss_template(template)
                            self.server.db.clan_metric_add(_gid,"boss_kills" if _is_boss else "mob_kills",1)
                            _changed=self.server.db.guild_contract_add_v0927(_gid,"bosses" if _is_boss else "kills",1)
                            await session.finish_ready_guild_contracts_v0927(_gid,_changed)
                            if template.get("guild_boss") and int(template.get("guild_id",0))==_gid:
                                _rec=self.server.db.conn.execute("SELECT fastest_kill_ms FROM player_guild_boss_records_v0927 WHERE clan_id=?",(_gid,)).fetchone()
                                _old=int(_rec["fastest_kill_ms"]) if _rec and _rec["fastest_kill_ms"] is not None else None
                                _best=fight_duration_ms if _old is None else min(_old,fight_duration_ms)
                                _name=str(template.get("name","Boss Gildii")); _tid=f"hall_{int(template.get('guild_hall_level',1))}"
                                self.server.db.conn.execute("INSERT INTO player_guild_boss_records_v0927(clan_id,kills,fastest_kill_ms,last_boss_name,last_killed_at) VALUES(?,1,?,?,CURRENT_TIMESTAMP) ON CONFLICT(clan_id) DO UPDATE SET kills=kills+1,fastest_kill_ms=?,last_boss_name=?,last_killed_at=CURRENT_TIMESTAMP",(_gid,_best,_name,_best,_name))
                                self.server.db.conn.execute("INSERT INTO player_guild_trophies_v0927(clan_id,trophy_id,name,count) VALUES(?,?,?,1) ON CONFLICT(clan_id,trophy_id) DO UPDATE SET count=count+1",(_gid,_tid,f"Trofeum: {_name}"))
                                _reward=(2_000+int(template.get('guild_hall_level',1))*1_000)*SILVER_PER_GOLD
                                self.server.db.conn.execute("UPDATE player_clans SET treasury=treasury+? WHERE id=?",(_reward,_gid)); self.server.db.conn.commit(); self.server.db.clan_metric_add(_gid,"guild_boss_kills",1); self.server.db.clan_log(_gid,session.account_id,f"Gildia pokonuje {_name}. Trofeum zapisane; do skarbca trafia {currency_reading_text(_reward,0,0)}.")
                                await session.send(f"Boss Gildii pokonany. Trofeum zapisane, a skarbiec otrzymuje {currency_reading_text(_reward,0,0)}.")
                    await self.server.events.publish(PlayerMobKillProgressionEvent(
                        session=session,
                        mob=mob,
                        template=template,
                        bestiary_id=bestiary_id,
                        fight_duration_ms=fight_duration_ms,
                        party_size=count,
                        is_boss=bool(v0866_is_boss_template(template)),
                        is_world_boss=bool(
                            template.get("world_boss")
                            or template.get("v016_world_boss")
                            or template.get("v020_mythic_world_boss")
                        ),
                        is_legendary_rare=bool(template.get("v016_legendary_rare")),
                        is_v016_world_boss=bool(template.get("v016_world_boss")),
                        is_great_ruin_guardian=bool(template.get("v018_great_ruin_guardian")),
                        is_legendary_event_boss=bool(template.get("v018_legendary_event_boss")),
                        biome=str(template.get("v016_biome", "any")),
                    ))
                    bestiary_ids_now = {
                        str(row["mob_template_id"])
                        for row in self.server.db.bestiary_rows(session.account_id)
                    }
                    await session.set_achievement_progress(
                        "bestiary_unique", len(bestiary_ids_now.intersection(BESTIARY_CATALOG))
                    )
                    bestiary_name = MOB_TEMPLATES.get(bestiary_id, template).get("name", template["name"])
                    if bestiary_new:
                        await session.send(
                            f"Bestiariusz: nowy wpis — {bestiary_name}. "
                            "Wpisz bestiariusz " + bestiary_name + "."
                        )
                    elif bestiary_record and bestiary_row and bestiary_row["fastest_kill_ms"] is not None:
                        await session.send(
                            f"Bestiariusz: nowy rekord {bestiary_name}: "
                            f"{int(bestiary_row['fastest_kill_ms']) / 1000.0:.2f} s."
                        )

                    # v1.11.32: bojowe zadania klasowe zaliczają tylko właściwy rodzaj celu.
                    try:
                        await session.advance_class_guild_quest_v11132("kill", 1)
                        if v0866_is_boss_template(template):
                            await session.advance_class_guild_quest_v11132("boss", 1)
                    except Exception as exc:
                        print(f"CLASS_GUILD_QUEST_PROGRESS_ERROR: {type(exc).__name__}: {exc}", flush=True)
                        print(f"GUILD_CLASS_QUEST_PROGRESS_ERROR: {type(exc).__name__}: {exc}", flush=True)

                    # v0.8.10: bounty zalicza się każdemu uprawnionemu członkowi drużyny.
                    try:
                        bounty_state = session.character.guild_bounty_state()
                        if bounty_state.get("target") == mob.template_id and not bounty_state.get("completed"):
                            bounty_state["completed"] = True
                            session.character.set_guild_bounty_state(bounty_state)
                            await session.send("Cel zlecenia Gildii pokonany. Użyj: guildbounty odbierz.")
                    except Exception as exc:
                        print(f"GUILD_BOUNTY_PROGRESS_ERROR: {type(exc).__name__}: {exc}", flush=True)

                    # v0.8.53: każdy zabijalny mob może być bezpośrednim celem questa
                    # przez własny template_id. Zachowujemy również historyczne aliasy
                    # quest_target/quest_targets, więc stare questy nadal zaliczają całe
                    # rodziny mobów (np. wszystkie odmiany goblinów).
                    quest_targets = quest_kill_targets_v0389(mob.template_id, template)

                    for target in quest_targets:
                        changed = self.server.db.increment_quest(
                            session.account_id, target
                        )
                        for quest_id, _progress in changed:
                            await session.announce_active_quest_progress(
                                quest_id,
                                template.get("name", mob.template_id),
                            )

                    if count >= 2:
                        _party_contract_categories_v11339 = []
                        if template.get("elite_affix") or str(template.get("rank") or "") == "elite":
                            _party_contract_categories_v11339.append("elite")
                        if v0866_is_boss_template(template):
                            _party_contract_categories_v11339.append("boss")
                        if mob_element_affinities_v11339(template):
                            _party_contract_categories_v11339.append("elemental")
                        if template.get("v11339_named_rare"):
                            _party_contract_categories_v11339.append("named_rare")
                        for _contract_category_v11339 in dict.fromkeys(
                            _party_contract_categories_v11339
                        ):
                            _contract_changes_v11339 = (
                                self.server.db.increment_party_contract_v11339(
                                    session.account_id,
                                    _contract_category_v11339,
                                    1,
                                )
                            )
                            for _qid_v11339, _progress_v11339, _needed_v11339 in _contract_changes_v11339:
                                await session.announce_active_quest_progress(
                                    _qid_v11339,
                                    template.get("name", mob.template_id),
                                )

                    await session.grant_hourly_quest_kill_drop_v0929(
                        mob.template_id, template
                    )
                    try:
                        _dur=int(fight_duration_ms or 0)
                        session.server.db.conn.execute("INSERT INTO combat_recaps_v03052(account_id,opponent,duration_ms,damage_dealt,damage_taken,healing,crits,skills_used,result) VALUES(?,?,?,?,?,?,?,?,?)",(session.account_id,str(template.get("name",mob.template_id)),_dur,int(getattr(session,"_recap52_dealt",0)),int(getattr(session,"_recap52_taken",0)),int(getattr(session,"_recap52_heal",0)),int(getattr(session,"_recap52_crits",0)),int(getattr(session,"_recap52_skills",0)),"victory"))
                        session.server.db.set_recap_summary_v0320(session.account_id, self.character.name, f"Pokonano {template.get('name',mob.template_id)}", int(getattr(session,"_recap32_guard_saved",0)), int(getattr(session,"_recap52_heal",0)), "victory")
                        session.server.db.add_combat_event_v0320(session.account_id,f"Finalny cios zadaje {self.character.name}. {template.get('name',mob.template_id)} zostaje pokonany.","final")
                        session._recap52_start=0
                    except Exception as exc:
                        print(f"COMBAT_RECAP_SAVE_ERROR: {type(exc).__name__}: {exc}", flush=True)
                    # v1.11.24: rewardy całego party są jedną transakcją. Poprzednio
                    # każdy recipient robił COMMIT recapu, a save_character zaraz
                    # potem wykonywał drugi COMMIT.
                    self.server.db.save_character(session.character, commit=False)

                # Jeden commit po progresji i zapisach wszystkich odbiorców nagrody.
                # Zachowuje te same dane, ale usuwa serię fsynców przy każdym killu.
                self.server.db.conn.commit()

                # v0.71.1: lazy/infinite Crypt templates can be rebuilt after boot.
                # Guarantee the authored Soul Shard drop at the actual reward boundary
                # so no later numeric rebalance can silently reduce it again.
                if _v0711_crypt_soul_shard_guaranteed(mob.template_id, template):
                    template.setdefault("drops", {})["soul_shard"] = 1.0

                for item_id, chance in template["drops"].items():
                    _effective_drop_chance_v11329 = authored_drop_chance_v11329(
                        template, item_id, chance
                    )
                    _elite_drop_mult_v11338 = max(
                        1.0,
                        float(template.get("elite_drop_multiplier_v11338", 1.0) or 1.0),
                    )
                    _effective_drop_chance_v11329 = min(
                        1.0,
                        float(_effective_drop_chance_v11329) * _elite_drop_mult_v11338,
                    )
                    if random.random() <= _effective_drop_chance_v11329:
                        # v0.35.9: every normal mob drop is shared locally with the
                        # whole eligible party. Roll the configured chance exactly once
                        # per defeated mob; on success each present reward recipient gets
                        # one copy of the same item.
                        drop_recipients = party_drop_recipients_v0359(item_id, recipients)
                        for winner in drop_recipients:
                            if item_id in globals().get("TECH_COMPONENT_IDS", set()) or ITEMS.get(item_id, {}).get("craftbox_category") == "technology":
                                self.server.db.add_storage_item(winner.account_id, "craftbox", item_id, 1)
                            else:
                                self.server.db.add_item(winner.account_id, item_id, 1)
                            await winner.record_item_collection(
                                item_id, source=template["name"], announce=True
                            )

                        boss_id_for_drop = canonical_bestiary_template_id(mob.template_id)
                        if boss_id_for_drop in BOSS_COLLECTION_CATALOG:
                            for party_session in recipients:
                                new_drop = self.server.db.add_boss_codex_drop(
                                    party_session.account_id, boss_id_for_drop, item_id
                                )
                                if new_drop:
                                    await party_session.send(
                                        f"Boss Codex: odkryty drop {ITEMS[item_id]['name']} z "
                                        f"{BOSS_COLLECTION_CATALOG[boss_id_for_drop]}."
                                    )

                        for party_session in drop_recipients:
                            if party_session.loot_message_allowed(item_id):
                                if count > 1:
                                    await party_session.send(
                                        f"Drop drużynowy: każdy obecny członek otrzymuje "
                                        f"{ITEMS[item_id]['name']}."
                                    )
                                else:
                                    await party_session.send(
                                        f"Drop: otrzymujesz {ITEMS[item_id]['name']}."
                                    )

                # v1.15.0: independent and rare boss-relic/catalyst roll.
                # One random result per killed boss, then identical for the local party.
                if v0866_is_boss_template(template) or template.get("uoss_unique_superboss_key"):
                    _legendary_id_v1150 = boss_legendary_roll_v1150(template)
                    if _legendary_id_v1150:
                        _legendary_id_v1150 = infinite_equipment_variant_for_drop(
                            _legendary_id_v1150, template
                        )
                        for _winner in recipients:
                            self.server.db.add_item(_winner.account_id, _legendary_id_v1150, 1)
                            await _winner.record_item_collection(
                                _legendary_id_v1150, source=template.get("name","Boss"), announce=True
                            )
                            await _winner.send(
                                f"LEGENDARNY ŁUP: {ITEMS[_legendary_id_v1150]['name']}. "
                                "Nagroda z bossa, niezależna od normalnego dropu."
                            )

                # v1.13.23: one independent, stage-scaled "o kurde" trophy roll.
                # It never replaces authored drops and follows the same full-party
                # reward rule as normal loot.
                _trophy_spec = _v11323_mob_trophy_spec(template)
                if _trophy_spec:
                    _trophy_item_id, _trophy_chance = _trophy_spec
                    if random.random() <= float(_trophy_chance):
                        _trophy_recipients = party_drop_recipients_v0359(
                            _trophy_item_id, recipients
                        )
                        for _winner in _trophy_recipients:
                            self.server.db.add_item(
                                _winner.account_id, _trophy_item_id, 1
                            )
                            await _winner.record_item_collection(
                                _trophy_item_id,
                                source=template.get("name", "Walka"),
                                announce=True,
                            )
                            await _winner.send(
                                f"Rzadki łup bojowy: otrzymujesz "
                                f"{ITEMS[_trophy_item_id]['name']}. "
                                "To trofeum ma wysoką wartość sprzedaży."
                            )

                # v1.13.25: weak legacy families get a characteristic material,
                # but this is deliberately NOT another global trophy system.
                _legacy_drop_v11325 = _v11325_legacy_identity_drop_spec(template)
                if _legacy_drop_v11325:
                    _legacy_item_id_v11325, _legacy_chance_v11325 = _legacy_drop_v11325
                    _legacy_recipients_v11325 = party_drop_recipients_v0359(
                        _legacy_item_id_v11325, recipients
                    )
                    for _winner in _legacy_recipients_v11325:
                        self.server.db.add_item(
                            _winner.account_id, _legacy_item_id_v11325, 1
                        )
                        await _winner.record_item_collection(
                            _legacy_item_id_v11325,
                            source=template.get("name", "Walka"),
                            announce=True,
                        )
                        await _winner.send(
                            f"Łup charakterystyczny: "
                            f"{ITEMS[_legacy_item_id_v11325]['name']}."
                        )

                await self.server.broadcast_room(
                    self.character.room_id,
                    (
                        f"{self.character.name} i drużyna pokonują "
                        f"{template['name']}."
                        if count > 1
                        else f"{self.character.name} pokonuje {template['name']}."
                    ),
                    exclude=self,
                )

