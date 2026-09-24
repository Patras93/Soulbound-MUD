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
from network.protocol_gameplay_utils import mob_respawn_seconds
from systems.dungeons_regions import is_astral_boss_floor, is_crypt_boss_floor
from systems.equipment_crafting import (
    GUILD_CLASS_QUESTS, LEGENDARY_CLASS_RELIC_BY_CLASS_TIER,
    LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER,
)
from systems.milestone import dungeon_party_bonus_v0320
from world.dynamic_content import (
    BESTIARY_CATALOG, BOSS_COLLECTION_CATALOG, canonical_bestiary_template_id,
    quest_kill_targets_v0389,
)
from world.economy_quests import legendary_loot_mastery_for_floor, milestone_boss_tier
from world.generation_systems import V020_GAUNTLETS, V020_MYTHIC_WORLD_BOSS_SECONDS
from world.runtime_progression import v0210_endless_gauntlet_identity


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


def _v0711_crypt_soul_shard_guaranteed(template_id, template):
    """Return True for Crypt/Mythic Crypt combat templates, including variants."""
    if not isinstance(template, dict):
        return False
    try:
        if int(template.get("crypt_floor", 0) or 0) > 0:
            return True
        if int(template.get("mythic_crypt_floor", 0) or 0) > 0:
            return True
    except Exception:
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
            except Exception:
                pass
    return False

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

    async def mob_defeated(self, mob):
                # Zwycięstwo, loot, questy i nagrody są zawsze ważne nawet w trybie
                # combat concise. Nie dziedziczą wyciszenia rutynowej auto kolejki.
                self.auto_queue_casting = False
                template = MOB_TEMPLATES[mob.template_id]
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
                count = len(recipients)

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

                for session in recipients:
                    if count > 1:
                        await session.send(
                            f"Drużyna pokonuje: {template['name']}. "
                            f"Nagrody obejmują {count} obecnych członków."
                        )
                    else:
                        await session.send(f"Pokonujesz: {template['name']}.")

                # v0.19: jedna wspólna pula monet z generatora całej gry.
                generated_coins=_final_combat_reward(template,"coins")
                currency_rewards={currency:{s.account_id:0 for s in recipients} for currency in ("silver","gold","mithril")}
                if generated_coins>0:
                    base_share,remainder=divmod(generated_coins,count)
                    for session in recipients:
                        currency_rewards["silver"][session.account_id]=base_share
                    currency_rewards["silver"][self.account_id]+=remainder

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
                            "Twój udział waluty: "
                            + currency_reading_text(silver, gold, mithril) + "."
                        )

                    # v0.19: Global Progression & Reward Generator.
                    # Duże nagrody nie są przycinane procentowym capem. Długość gry
                    # kontrolują rosnące wymagania EXP oraz kosztów.
                    xp_profile=session.dynamic_kill_xp_profile(template,room_id=session.character.room_id)
                    # v0.23.0: NIE podbijamy mnożnika do minimum 1.0. To był błąd,
                    # przez który słabsze moby nigdy nie traciły EXP podczas farmy.
                    xp_mult=float(xp_profile["multiplier"]) * session.v0210_reward_multiplier()
                    _party_bonus=dungeon_party_bonus_v0320(session)
                    xp_mult*=float(_party_bonus.get("multiplier",1.0))
                    if int(_party_bonus.get("bonus_pct",0))>0:
                        await session.send_combat(f"Dungeon Party Bonus: +{int(_party_bonus['bonus_pct'])}% EXP; członków obok {_party_bonus['members']}; różne klasy {_party_bonus['diverse']}.",detail="full")
                    raw_stat_reward=min(V019_SAFE_INT,max(0,int(round(_final_combat_reward(template,"stat")*xp_mult))))
                    raw_stat_reward=session.apply_double_xp(raw_stat_reward)
                    stat_rewards=[]
                    for stat_name in session.character.STAT_PROGRESS_FIELDS:
                        stat_rewards.append(raw_stat_reward)
                        for msg in session.character.add_stat_progress(raw_stat_reward,targets=(stat_name,)):
                            await session.send(msg)
                    stat_reward_text=str(raw_stat_reward)

                    soul_xp_reward=min(V019_SAFE_INT,max(0,int(round(_final_combat_reward(template,"soul")*xp_mult))))
                    await session.grant_soul_xp(soul_xp_reward)

                    class_xp_reward=min(V019_SAFE_INT,max(0,int(round(_final_combat_reward(template,"class")*xp_mult))))
                    await session.send_combat(
                        f"Generator v0.19 + dynamiczny EXP v0.23: etap {v0190_mob_stage(template)}, "
                        f"ranga {v0190_mob_rank(template)}, siła postaci {xp_profile['power']}/{CHARACTER_MAX_LEVEL}, "
                        f"siła moba {xp_profile['target']}/{CHARACTER_MAX_LEVEL}, mnożnik x{xp_profile['multiplier']:.2f}; "
                        f"bazowy EXP statów {stat_reward_text}; Soul XP {soul_xp_reward}; Class XP {class_xp_reward}; "
                        f"EXP postaci {character_xp_reward if 'character_xp_reward' in locals() else _final_combat_reward(template,'character')}.",
                        detail="full",
                    )
                    await session.grant_class_xp(class_xp_reward)
                    character_xp_reward=min(V019_SAFE_INT,max(0,int(round(_final_combat_reward(template,"character")*xp_mult))))
                    for _msg in session.add_character_xp_with_event(character_xp_reward):
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
                        except Exception:
                            pass
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

                    # v0.8.10: postęp zadania klasowego Gildii.
                    try:
                        active_classes = session.active_class_names()
                        guild_class = active_classes[0] if active_classes else session.character.class_name
                        quest_data = GUILD_CLASS_QUESTS.get(guild_class)
                        states = session.character._guild_json("guild_class_quests_json")
                        state = states.get(guild_class, {})
                        if quest_data and isinstance(state, dict) and state.get("accepted") and not state.get("completed"):
                            needed = int(quest_data[4])
                            old_progress = int(state.get("progress", 0))
                            new_progress = min(needed, old_progress + 1)
                            state["progress"] = new_progress
                            states[guild_class] = state
                            session.character._set_guild_json("guild_class_quests_json", states)
                            if new_progress >= needed:
                                await session.send(
                                    f"Zadanie Gildii {quest_data[0]}: {new_progress} z {needed}. "
                                    "Cel wykonany. Użyj zadanieklasowe, aby odebrać nagrodę."
                                )
                            else:
                                await session.send(f"Zadanie Gildii {quest_data[0]}: {new_progress} z {needed}.")
                    except Exception:
                        pass

                    # v0.8.10: bounty zalicza się każdemu uprawnionemu członkowi drużyny.
                    try:
                        bounty_state = session.character.guild_bounty_state()
                        if bounty_state.get("target") == mob.template_id and not bounty_state.get("completed"):
                            bounty_state["completed"] = True
                            session.character.set_guild_bounty_state(bounty_state)
                            await session.send("Cel zlecenia Gildii pokonany. Użyj: guildbounty odbierz.")
                    except Exception:
                        pass

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

                    await session.grant_hourly_quest_kill_drop_v0929(
                        mob.template_id, template
                    )
                    try:
                        _dur=int(fight_duration_ms or 0)
                        session.server.db.conn.execute("INSERT INTO combat_recaps_v03052(account_id,opponent,duration_ms,damage_dealt,damage_taken,healing,crits,skills_used,result) VALUES(?,?,?,?,?,?,?,?,?)",(session.account_id,str(template.get("name",mob.template_id)),_dur,int(getattr(session,"_recap52_dealt",0)),int(getattr(session,"_recap52_taken",0)),int(getattr(session,"_recap52_heal",0)),int(getattr(session,"_recap52_crits",0)),int(getattr(session,"_recap52_skills",0)),"victory"))
                        session.server.db.set_recap_summary_v0320(session.account_id, self.character.name, f"Pokonano {template.get('name',mob.template_id)}", int(getattr(session,"_recap32_guard_saved",0)), int(getattr(session,"_recap52_heal",0)), "victory")
                        session.server.db.add_combat_event_v0320(session.account_id,f"Finalny cios zadaje {self.character.name}. {template.get('name',mob.template_id)} zostaje pokonany.","final")
                        session.server.db.conn.commit(); session._recap52_start=0
                    except Exception:
                        pass
                    self.server.db.save_character(session.character)

                # v0.71.1: lazy/infinite Crypt templates can be rebuilt after boot.
                # Guarantee the authored Soul Shard drop at the actual reward boundary
                # so no later numeric rebalance can silently reduce it again.
                if _v0711_crypt_soul_shard_guaranteed(mob.template_id, template):
                    template.setdefault("drops", {})["soul_shard"] = 1.0

                for item_id, chance in template["drops"].items():
                    if random.random() <= chance:
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

