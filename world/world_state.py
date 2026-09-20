
@dataclass
class CorpseState:
    key: str
    room_id: str
    mob_name: str
    mob_template_id: str
    items: list
    created_at: float
    expires_at: float


@dataclass
class MobState:
    key: str
    room_id: str
    template_id: str
    hp: int
    alive: bool = True
    respawn_at: float = 0.0
    engaged_by: Optional[str] = None
    combat_turn: int = 0
    player_hits: int = 0
    phase_stage: int = 0
    engaged_at: float = 0.0
    home_room_id: str = ""
    next_wander_at: float = 0.0


# ============================================================
# v0.29.0 - DYNAMIC WORLD EVENTS + BOSS/NEMESIS GENERATOR
# ============================================================
def v0290_active_world_events(now=None):
    return dynamic_world_v029.active_events(
        ROOMS, MOB_SPAWNS, MOB_TEMPLATES, str(V0250_WORLD_SEED), now=now
    )

def v0290_event_for_room(room_id, now=None):
    room_id = str(room_id or "")
    return tuple(event for event in v0290_active_world_events(now) if event["room_id"] == room_id)

HELP_TOPICS["dynamic_world_v029"] = [
    "dynamiceventy pokazuje pięć godzinnych wydarzeń generowanych z aktualnego świata i etapów Generator Core.",
    "Event może wygenerować Elite, Rare, czempiona albo proceduralnego World Bossa. Wszystkie są pasywne do chwili ataku.",
    "nemesis pokazuje przeciwnika, który ostatnio cię pokonał. Nemesis rośnie po kolejnych zwycięstwach nad tobą i czeka w miejscu ostatniej porażki.",
]
HELP_TOPIC_ALIASES.update({
    "dynamiczne eventy":"dynamic_world_v029", "dynamiceventy":"dynamic_world_v029",
    "nemesis":"dynamic_world_v029", "nemezis":"dynamic_world_v029",
})

class World:
    def __init__(self):
        self.mobs = {}
        self.corpses = {}
        self.corpse_counter = 0
        self.treasure_chest_opened_at = {}
        counts = {}
        # v0.36.2: initial open-world spawns use the CURRENT room stage, not only
        # the shared base template's earliest spawn. This keeps terrain 100+
        # and endgame regions from inheriting low-level combat numbers.
        for room_id, template_id in list(MOB_SPAWNS):
            template_id = resolve_world_spawn_template(template_id)
            template_id = self._terrain_scaled_template_v0362(room_id, template_id)
            counts[(room_id, template_id)] = counts.get((room_id, template_id), 0) + 1
            n = counts[(room_id, template_id)]
            key = f"{room_id}:{template_id}:{n}"
            v0190_apply_combat_template(MOB_TEMPLATES[template_id])
            self.mobs[key] = MobState(
                key=key, room_id=room_id, template_id=template_id,
                hp=MOB_TEMPLATES[template_id]["max_hp"],
                home_room_id=room_id,
                next_wander_at=time.time() + random.uniform(
                    MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS
                ),
            )

    def _terrain_scaled_template_v0362(self, room_id, template_id):
        """Return a room-stage clone for ordinary open-world terrain mobs.

        Dungeons/gauntlets keep their dedicated floor logic. Open-world normal,
        elite and rare mobs are additionally tougher from stage 50 upward.
        """
        room_id = str(room_id or "")
        template_id = str(template_id or "")
        room = ROOMS.get(room_id, {})
        template = MOB_TEMPLATES.get(template_id)
        if not isinstance(room, dict) or not isinstance(template, dict):
            return template_id

        # Known instanced/floor systems keep their authored difficulty rules.
        dungeon_flags = (
            "crypt_floor", "astral_floor", "mythic_crypt_floor", "mythic_astral_floor",
            "giant_fortress_floor", "profession_dungeon_floor", "v020_gauntlet",
            "v020_mega_gate", "v0140_mini_dungeon", "v0180_great_ruin",
        )
        if any(room.get(flag) is not None for flag in dungeon_flags):
            return template_id

        try:
            room_stage = int(room.get("generator_level", room.get("recommended_mastery", 1)) or 1)
        except Exception:
            room_stage = 1
        try:
            recommended = int(room.get("recommended_mastery", 0) or 0)
        except Exception:
            recommended = 0
        stage = max(1, min(CHARACTER_MAX_LEVEL, room_stage, ))
        if recommended > stage:
            stage = max(1, min(CHARACTER_MAX_LEVEL, recommended))

        try:
            base_stage = int(template.get("generator_level", 1) or 1)
        except Exception:
            base_stage = 1
        rank = generator_core_v027.mob_rank(template)
        is_terrain_rank = rank in ("normal", "elite", "rare")
        needs_room_clone = stage > base_stage
        needs_terrain_boost = is_terrain_rank and stage >= 50
        if not needs_room_clone and not needs_terrain_boost:
            return template_id

        runtime_stage = max(base_stage, stage)
        runtime_id = f"{template_id}__terrain_v0362_{runtime_stage:03d}"
        if runtime_id not in MOB_TEMPLATES:
            import copy as _copy
            clone = _copy.deepcopy(template)
            clone["base_template"] = str(template.get("base_template") or template_id)
            clone["terrain_runtime_clone_v0362"] = True
            clone["terrain_room_stage_v0362"] = runtime_stage
            generator_core_v027.runtime_mob_balance(runtime_id, clone, runtime_stage, rank=rank)
            if is_terrain_rank and runtime_stage >= 50:
                # Level 50 ~= 1.5x HP, 100 = 2x, 200 = 3x, 300+ = 4x.
                # Damage rises more gently: +5% at 50, +10% at 100,
                # +20% at 200 and up to +50% in the highest regions.
                hp_mult = min(4.0, 1.0 + runtime_stage / 100.0)
                dmg_mult = 1.0 + min(0.50, runtime_stage / 1000.0)
                clone["terrain_hp_multiplier_v0362"] = round(hp_mult, 3)
                clone["terrain_damage_multiplier_v0362"] = round(dmg_mult, 3)
                clone["max_hp"] = max(1, int(round(int(clone.get("max_hp", 1)) * hp_mult)))
                clone["base_max_hp"] = clone["max_hp"]
                clone["damage"] = max(1, int(round(int(clone.get("damage", 1)) * dmg_mult)))
            MOB_TEMPLATES[runtime_id] = clone
        return runtime_id

    def _register_runtime_spawn(self, room_id, template_id):
        room_meta = ROOMS.get(str(room_id or ""), {})
        template_id = self._terrain_scaled_template_v0362(room_id, template_id)
        template_meta = MOB_TEMPLATES.get(template_id)
        if isinstance(template_meta, dict):
            template_meta["auto_aggro"] = False
        if not any(r == room_id and t == template_id for r, t in MOB_SPAWNS):
            MOB_SPAWNS.append((room_id, template_id))
        existing = [m for m in self.mobs.values() if m.room_id == room_id and m.template_id == template_id]
        if existing:
            return existing[0]
        n = 1 + sum(1 for m in self.mobs.values() if m.room_id == room_id and m.template_id == template_id)
        key = f"{room_id}:{template_id}:{n}"
        v0190_apply_combat_template(MOB_TEMPLATES[template_id])
        mob = MobState(
            key=key, room_id=room_id, template_id=template_id,
            hp=MOB_TEMPLATES[template_id]["max_hp"],
            home_room_id=room_id,
            next_wander_at=time.time() + random.uniform(
                MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS
            ),
        )
        self.mobs[key] = mob
        return mob

    def _ensure_v0290_event_spawns(self, room_id, now=None):
        created = []
        for event in v0290_event_for_room(room_id, now=now):
            for index in range(int(event.get("count", 1) or 1)):
                event_key = f"v029:{event['token']}:{index}"
                existing = next((m for m in self.mobs.values() if getattr(m, "v029_event_key", "") == event_key), None)
                if existing:
                    created.append(existing)
                    continue
                template_id, _ = dynamic_world_v029.build_event_template(
                    event, index, MOB_TEMPLATES, generator_core_v027, str(V0250_WORLD_SEED)
                )
                if not template_id:
                    continue
                mob = MobState(
                    key=f"{event_key}:{template_id}", room_id=str(room_id), template_id=template_id,
                    hp=MOB_TEMPLATES[template_id]["max_hp"], home_room_id=str(room_id),
                    next_wander_at=time.time()+random.uniform(MOB_WANDER_MIN_SECONDS,MOB_WANDER_MAX_SECONDS),
                )
                mob.v029_event_key = event_key
                mob.v029_expires_at = float(event["expires_at"])
                mob.v016_ephemeral = True
                self.mobs[mob.key] = mob
                created.append(mob)
        return created

    def remove_v029_nemesis(self, account_id):
        account_id = int(account_id)
        for key, mob in list(self.mobs.items()):
            tmpl = MOB_TEMPLATES.get(mob.template_id, {})
            if int(tmpl.get("v029_nemesis_owner_account_id", 0) or 0) == account_id:
                self.mobs.pop(key, None)

    def ensure_v029_nemesis(self, record):
        if not record or not int(record["active"] or 0):
            return None
        account_id = int(record["account_id"])
        room_id = str(record["room_id"])
        if room_id not in ROOMS and not self.ensure_runtime_room(room_id):
            return None
        existing = next((m for m in self.mobs.values() if int(MOB_TEMPLATES.get(m.template_id, {}).get("v029_nemesis_owner_account_id", 0) or 0) == account_id and m.alive), None)
        if existing:
            return existing
        template_id, _ = dynamic_world_v029.build_nemesis_template(record, MOB_TEMPLATES, generator_core_v027)
        if not template_id:
            return None
        mob = MobState(
            key=f"v029nemesis:{account_id}:{int(record['rank'])}:{template_id}",
            room_id=room_id, template_id=template_id, hp=MOB_TEMPLATES[template_id]["max_hp"],
            home_room_id=room_id, next_wander_at=time.time()+365*24*3600,
        )
        mob.v016_ephemeral = True
        self.mobs[mob.key] = mob
        return mob

    def _ensure_v0160_encounters(self, room_id, now=None):
        created = []
        for encounter in v0160_encounters_for_room(room_id, now):
            event_key = "v016:" + encounter["token"]
            existing = next((m for m in self.mobs.values() if getattr(m, "v016_event_key", "") == event_key), None)
            if existing:
                created.append(existing)
                continue
            template_id = encounter.get("template_id")
            if not template_id or template_id not in MOB_TEMPLATES:
                continue
            key = f"{event_key}:{template_id}"
            v0190_apply_combat_template(MOB_TEMPLATES[template_id])
            mob = MobState(
                key=key, room_id=room_id, template_id=template_id,
                hp=MOB_TEMPLATES[template_id]["max_hp"], home_room_id=room_id,
                next_wander_at=time.time()+random.uniform(MOB_WANDER_MIN_SECONDS,MOB_WANDER_MAX_SECONDS),
            )
            mob.v016_event_key = event_key
            mob.v016_expires_at = float(encounter["expires_at"])
            mob.v016_ephemeral = True
            mob.v016_encounter_type = encounter["type"]
            self.mobs[key] = mob
            created.append(mob)
        return created

    def _ensure_v0200_mythic_encounters(self, room_id, now=None):
        created=[]
        for encounter in v0200_mythic_encounters_for_room(room_id,now):
            event_key="v020mythic:"+encounter["token"]
            existing=next((m for m in self.mobs.values() if getattr(m,"v020_event_key","")==event_key),None)
            if existing:
                created.append(existing); continue
            tid=encounter["template_id"]
            mob=MobState(key=f"{event_key}:{tid}",room_id=room_id,template_id=tid,hp=MOB_TEMPLATES[tid]["max_hp"],home_room_id=room_id,
                next_wander_at=time.time()+random.uniform(MOB_WANDER_MIN_SECONDS,MOB_WANDER_MAX_SECONDS))
            mob.v020_event_key=event_key; mob.v016_expires_at=float(encounter["expires_at"]); mob.v016_ephemeral=True
            self.mobs[mob.key]=mob; created.append(mob)
        return created

    def _ensure_v0140_event_spawn(self, room_id, now=None):
        event = v0140_event_for_room(room_id, "rare_hunt", now=now)
        if not event:
            return None
        event_key = "v0140event:" + event["token"]
        for mob in self.mobs.values():
            if getattr(mob, "v0140_event_key", "") == event_key:
                return mob
        template_id = v0140_rare_template_for_kind(event["kind"], salt=event["token"])
        if not template_id:
            return None
        key = f"{event_key}:{template_id}"
        mob = MobState(
            key=key, room_id=room_id, template_id=template_id,
            hp=MOB_TEMPLATES[template_id]["max_hp"], home_room_id=room_id,
            next_wander_at=time.time() + random.uniform(MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS),
        )
        mob.v0140_event_key = event_key
        mob.v0140_event_expires_at = float(event["expires_at"])
        self.mobs[key] = mob
        return mob

    def _ensure_v0180_legendary_event_spawn(self, room_id, now=None):
        event = v0180_legendary_event_for_room(room_id, now=now)
        if not event or event.get("type") != "titan_awakening":
            return None
        event_key = "v018legend:" + event["token"]
        existing = next((m for m in self.mobs.values() if getattr(m, "v018_event_key", "") == event_key), None)
        if existing:
            return existing
        tid = V018_TITAN_TEMPLATES.get(event["kind"])
        if not tid:
            return None
        mob = MobState(
            key=f"{event_key}:{tid}", room_id=room_id, template_id=tid,
            hp=MOB_TEMPLATES[tid]["max_hp"], home_room_id=room_id,
            next_wander_at=time.time()+random.uniform(MOB_WANDER_MIN_SECONDS,MOB_WANDER_MAX_SECONDS),
        )
        mob.v018_event_key=event_key
        # Reuse mature ephemeral cleanup semantics from v0.16.
        mob.v016_expires_at=float(event["expires_at"]); mob.v016_ephemeral=True
        self.mobs[mob.key]=mob
        return mob

    def ensure_v0180_special_room(self, room_id):
        created_room, spawns = v0180_create_archipelago_room_definition(room_id)
        if not created_room:
            created_room, spawns = v0180_create_ruin_room_definition(room_id)
        if not created_room:
            created_room, spawns = v0180_create_endless_room_definition(room_id)
        if not created_room:
            return False
        for spawn_room, template_id in spawns:
            self._generatorize_runtime_room(spawn_room)
            self._register_runtime_spawn(spawn_room, template_id)
        _ROOM_THREAT_CACHE.pop(created_room, None)
        _ZONE_THREAT_CACHE.clear()
        return True

    def ensure_v0140_special_room(self, room_id):
        created_room, spawns = v0140_create_mini_room_definition(room_id)
        if not created_room:
            created_room, spawns = v0140_create_secret_room_definition(room_id)
        if not created_room:
            return False
        for spawn_room, template_id in spawns:
            self._register_runtime_spawn(spawn_room, template_id)
        _ROOM_THREAT_CACHE.pop(created_room, None)
        _ZONE_THREAT_CACHE.clear()
        return True

    def _generatorize_runtime_room(self, room_id):
        room=ROOMS.get(str(room_id or ""))
        if isinstance(room,dict):
            generator_core_v027.runtime_room_level(str(room_id),room,ROOMS)
            return True
        return False

    def ensure_hybrid_surface_room(self, room_id):
        room_id = str(room_id or "")
        if not room_id:
            return False
        if room_id in ROOMS:
            self._generatorize_runtime_room(room_id)
            self._ensure_v0290_event_spawns(room_id)
            self._ensure_v0140_event_spawn(room_id)
            self._ensure_v0160_encounters(room_id)
            self._ensure_v0180_legendary_event_spawn(room_id)
            self._ensure_v0200_mythic_encounters(room_id)
            return True
        created_room, spawns = v0130_create_frontier_room_definition(room_id)
        if not created_room:
            return False
        self._generatorize_runtime_room(created_room)
        for spawn_room, template_id in spawns:
            self._generatorize_runtime_room(spawn_room)
            self._register_runtime_spawn(spawn_room, template_id)
        self._ensure_v0290_event_spawns(room_id)
        self._ensure_v0140_event_spawn(room_id)
        self._ensure_v0160_encounters(room_id)
        self._ensure_v0180_legendary_event_spawn(room_id)
        self._ensure_v0200_mythic_encounters(room_id)
        _ROOM_THREAT_CACHE.pop(created_room, None)
        _ZONE_THREAT_CACHE.clear()
        return True

    def ensure_runtime_room(self, room_id):
        room_id = str(room_id or "")
        if room_id in ROOMS:
            self._generatorize_runtime_room(room_id)
            self._ensure_v0290_event_spawns(room_id)
            self._ensure_v0140_event_spawn(room_id)
            self._ensure_v0160_encounters(room_id)
            self._ensure_v0180_legendary_event_spawn(room_id)
            self._ensure_v0200_mythic_encounters(room_id)
            return True
        created_room, spawns = v0210_create_endless_gauntlet_room_definition(room_id)
        if created_room:
            self._generatorize_runtime_room(created_room)
            for spawn_room, template_id in spawns:
                self._generatorize_runtime_room(spawn_room)
                self._register_runtime_spawn(spawn_room, template_id)
            _ROOM_THREAT_CACHE.pop(created_room, None); _ZONE_THREAT_CACHE.clear()
            return True
        created_room, spawns = v0200_create_mega_room_definition(room_id)
        if created_room:
            self._generatorize_runtime_room(created_room)
            for spawn_room, template_id in spawns:
                self._generatorize_runtime_room(spawn_room)
                self._register_runtime_spawn(spawn_room, template_id)
            _ROOM_THREAT_CACHE.pop(created_room, None); _ZONE_THREAT_CACHE.clear()
            return True
        if self.ensure_hybrid_surface_room(room_id):
            self._generatorize_runtime_room(room_id); return True
        if self.ensure_v0180_special_room(room_id):
            self._generatorize_runtime_room(room_id); return True
        if self.ensure_v0140_special_room(room_id):
            self._generatorize_runtime_room(room_id); return True
        ok=self.ensure_infinite_dungeon_floor(room_id)
        if ok: self._generatorize_runtime_room(room_id)
        return ok

    def ensure_infinite_dungeon_floor(self, room_id):
        room_id = str(room_id or "")
        if not room_id:
            return False
        if room_id in ROOMS:
            self._generatorize_runtime_room(room_id)
            return True

        created_room = None
        spawns = []

        floor = crypt_floor_number(room_id)
        if floor is not None:
            created_room, spawns = create_infinite_crypt_floor_definition(
                floor, mythic=False
            )
        else:
            floor = mythic_crypt_floor_number(room_id)
            if floor is not None:
                created_room, spawns = create_infinite_crypt_floor_definition(
                    floor, mythic=True
                )
            else:
                floor = astral_floor_number(room_id)
                if floor is not None:
                    created_room, spawns = create_infinite_astral_floor_definition(
                        floor, mythic=False
                    )
                else:
                    floor = mythic_astral_floor_number(room_id)
                    if floor is not None:
                        created_room, spawns = create_infinite_astral_floor_definition(
                            floor, mythic=True
                        )
                    else:
                        floor = giant_fortress_floor_number(room_id)
                        if floor is not None:
                            created_room, spawns = create_infinite_giant_fortress_floor_definition(
                                floor
                            )
                        else:
                            floor = mine_floor_number(room_id)
                            if floor is not None:
                                created_room, spawns = create_infinite_mine_floor_definition(
                                    floor
                                )
                            else:
                                dungeon, floor = profession_dungeon_floor(room_id)
                                if dungeon is not None:
                                    created_room, spawns = (
                                        create_infinite_profession_dungeon_floor_definition(
                                            dungeon, floor
                                        )
                                    )

        if not created_room:
            return False
        ROOMS[created_room]["procedural_dynamic"] = True
        ROOMS[created_room]["generated_on_demand"] = True
        self._generatorize_runtime_room(created_room)
        # v0.10.0: każde dynamicznie tworzone piętro dostaje ten sam duży,
        # wielopokojowy układ co ręcznie przygotowana część instancji.
        spawns = v0100_expand_instance_floor(
            created_room, spawns, runtime=True
        )
        for spawn_room, template_id in spawns:
            self._register_runtime_spawn(spawn_room, template_id)
        _ROOM_THREAT_CACHE.pop(created_room, None)
        _ZONE_THREAT_CACHE.clear()
        return True

    def ensure_infinite_crypt_floor(self, room_id):
        # Zachowany alias dla starszego kodu/testów.
        return self.ensure_infinite_dungeon_floor(room_id)

    def refresh(self):
        now = time.time()
        # v0.16.0: tymczasowe world bossy i legendary rare znikają po rotacji,
        # ale nigdy w trakcie walki. Po pokonaniu nie respawnują w tym samym oknie.
        for mob_key, mob in list(self.mobs.items()):
            expires = float(getattr(mob, "v016_expires_at", 0.0) or 0.0)
            if expires and expires <= now and not mob.engaged_by:
                self.mobs.pop(mob_key, None)

        # v0.29.0: proceduralne eventy znikają po swojej godzinnej rotacji.
        for mob_key, mob in list(self.mobs.items()):
            expires = float(getattr(mob, "v029_expires_at", 0.0) or 0.0)
            if expires and expires <= now and not mob.engaged_by:
                self.mobs.pop(mob_key, None)

        # v0.14.0: eventowy rare znika po zakończeniu okna eventu, ale nigdy
        # w połowie aktywnej walki. Nie pozostawia trwałego spawnu.
        for mob_key, mob in list(self.mobs.items()):
            expires = float(getattr(mob, "v0140_event_expires_at", 0.0) or 0.0)
            if expires and expires <= now and not mob.engaged_by:
                self.mobs.pop(mob_key, None)
        for corpse_key, corpse in list(self.corpses.items()):
            if corpse.expires_at <= now:
                self.corpses.pop(corpse_key, None)
        for mob in self.mobs.values():
            if getattr(mob, "v016_ephemeral", False) and not mob.alive:
                continue
            if not mob.alive and mob.respawn_at <= now:
                mob.alive = True
                mob.hp = MOB_TEMPLATES[mob.template_id]["max_hp"]
                mob.engaged_by = None
                mob.combat_turn = 0
                mob.player_hits = 0
                mob.phase_stage = 0
                mob.engaged_at = 0.0
                if mob.home_room_id:
                    mob.room_id = mob.home_room_id
                mob.next_wander_at = now + random.uniform(
                    MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS
                )

    def wander_step(self, now=None):
        """Wykonuje pojedynczy bezpieczny tick ruchu zwykłych mobów."""
        self.refresh()
        now = time.time() if now is None else float(now)
        moves = []
        live_counts = {}
        for other in self.mobs.values():
            if other.alive:
                live_counts[other.room_id] = live_counts.get(other.room_id, 0) + 1

        for mob in self.mobs.values():
            if not mob.alive or mob.engaged_by:
                continue
            if now < float(mob.next_wander_at or 0.0):
                continue
            mob.next_wander_at = now + random.uniform(
                MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS
            )
            template = MOB_TEMPLATES.get(mob.template_id, {})
            if not mob_template_can_wander(template):
                continue
            candidates = [
                target for target in mob_wander_candidates(mob.room_id)
                if live_counts.get(target, 0) < MOB_WANDER_ROOM_CAP
            ]
            if not candidates:
                continue
            old_room = mob.room_id
            target = random.choice(candidates)
            mob.room_id = target
            live_counts[old_room] = max(0, live_counts.get(old_room, 1) - 1)
            live_counts[target] = live_counts.get(target, 0) + 1
            moves.append((mob, old_room, target))
        return moves

    def live_crypt_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if mob.alive and mob.room_id == room_id and MOB_TEMPLATES[mob.template_id].get("crypt_boss"):
                return mob
        return None

    def crypt_descent_blocked(self, room_id, direction="down"):
        # v0.10.1: boss blokuje tylko rzeczywiste zejście na dalsze piętro.
        # Wszystkie przejścia wewnątrz bieżącego piętra pozostają dostępne.
        if direction != "down":
            return False
        floor = crypt_floor_number(room_id)
        if floor is None or not is_crypt_boss_floor(floor):
            return False
        target = ROOMS.get(room_id, {}).get("exits", {}).get(direction)
        target_floor = crypt_floor_number(target)
        if target_floor is None or target_floor <= floor:
            return False
        return self.live_crypt_boss(room_id) is not None

    def live_astral_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[mob.template_id].get("astral_boss")
            ):
                return mob
        return None

    def astral_ascent_blocked(self, room_id, direction="up"):
        if direction != "up":
            return False
        floor = astral_floor_number(room_id)
        if floor is None or not is_astral_boss_floor(floor):
            return False
        target = ROOMS.get(room_id, {}).get("exits", {}).get(direction)
        target_floor = astral_floor_number(target)
        if target_floor is None or target_floor <= floor:
            return False
        return self.live_astral_boss(room_id) is not None

    def live_mythic_crypt_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[mob.template_id].get(
                    "mythic_crypt_boss"
                )
            ):
                return mob
        return None

    def mythic_crypt_descent_blocked(
        self, room_id, direction="down"
    ):
        if direction != "down":
            return False
        floor = mythic_crypt_floor_number(room_id)
        if floor is None or not is_mythic_crypt_boss_floor(floor):
            return False
        target = ROOMS.get(room_id, {}).get("exits", {}).get(direction)
        target_floor = mythic_crypt_floor_number(target)
        if target_floor is None or target_floor <= floor:
            return False
        return self.live_mythic_crypt_boss(room_id) is not None

    def live_mythic_astral_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[mob.template_id].get(
                    "mythic_astral_boss"
                )
            ):
                return mob
        return None

    def mythic_astral_ascent_blocked(
        self, room_id, direction="up"
    ):
        if direction != "up":
            return False
        floor = mythic_astral_floor_number(room_id)
        if floor is None or not is_mythic_astral_boss_floor(floor):
            return False
        target = ROOMS.get(room_id, {}).get("exits", {}).get(direction)
        target_floor = mythic_astral_floor_number(target)
        if target_floor is None or target_floor <= floor:
            return False
        return self.live_mythic_astral_boss(room_id) is not None

    def live_giant_fortress_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[
                    mob.template_id
                ].get("giant_fortress_boss")
            ):
                return mob
        return None

    def giant_fortress_ascent_blocked(
        self, room_id, direction="up"
    ):
        if direction != "up":
            return False
        floor = giant_fortress_floor_number(room_id)
        if floor is None or not is_giant_fortress_boss_floor(floor):
            return False
        target = ROOMS.get(room_id, {}).get("exits", {}).get(direction)
        target_floor = giant_fortress_floor_number(target)
        if target_floor is None or target_floor <= floor:
            return False
        return self.live_giant_fortress_boss(room_id) is not None

    def create_corpse(self, mob):
        template=MOB_TEMPLATES[mob.template_id]
        if template.get("leave_corpse", True) is False: return None
        pool=list(template.get("corpse_equipment_pool",()))
        guaranteed=min(len(pool),max(0,int(template.get("corpse_equipment_guaranteed",0))))
        items=random.sample(pool,guaranteed) if guaranteed else []
        if items:
            is_crypt_boss = bool(
                template.get("crypt_boss")
                or template.get("mythic_crypt_boss")
            )
            items = [
                roll_crypt_loot_item(
                    item_id, is_boss=is_crypt_boss
                )
                for item_id in items
            ]

        # v0.8.72: boss piętra co 10 zawsze zostawia właściwy klucz na ciele.
        boss_key = boss_key_for_template(template)
        if boss_key and boss_key not in ITEMS:
            if template.get("crypt_boss"):
                _ensure_dynamic_boss_key("crypt", int(template.get("crypt_floor", 0) or 0))
            elif template.get("mythic_crypt_boss"):
                _ensure_dynamic_boss_key("mythic_crypt", int(template.get("mythic_crypt_floor", 0) or 0))
        if boss_key and boss_key not in items:
            items.append(boss_key)

        material_pool = list(template.get("corpse_material_pool", ()))
        material_count = min(
            len(material_pool),
            max(0, int(template.get("corpse_material_guaranteed", 0))),
        )
        if material_count:
            material_items = random.sample(material_pool, material_count)
            # Nie dodawaj tego samego ID dwa razy, jeśli jakaś przyszła
            # ręczna pula moba zacznie zawierać część materiałową.
            for item_id in material_items:
                if item_id not in items:
                    items.append(item_id)

        # v0.30.34: materiały o losowej szansie mogą naprawdę leżeć na ciele.
        # Jest to osobne od globalnego `drops`, który przyznaje przedmiot od razu.
        # Dzięki temu questy typu odzysk z pancerza wymagają przeszukania ciała.
        for item_id, chance in (template.get("corpse_material_chances") or {}).items():
            if item_id in ITEMS and random.random() <= max(0.0, min(1.0, float(chance))):
                if item_id not in items:
                    items.append(item_id)
        # v0.9.11: losowy drop klasowego EQ z mobów. Poziom przedmiotu
        # wynika z siły moba/material tieru, a klasa/linia/slot są losowe.
        # Zwykły mob nie gwarantuje klasowego przedmiotu, więc nie zalewamy ekonomii.
        class_pool = class_equipment_drop_pool(template)
        if class_pool and random.random() < class_equipment_drop_chance(template):
            class_item = random.choice(class_pool)
            if class_item not in items:
                items.append(class_item)
        self.corpse_counter += 1; now=time.time()
        corpse=CorpseState(
            key=f"corpse:{self.corpse_counter}", room_id=mob.room_id,
            mob_name=template["name"], mob_template_id=mob.template_id,
            items=items, created_at=now,
            expires_at=now+CORPSE_LIFETIME_SECONDS,
        )
        self.corpses[corpse.key]=corpse
        return corpse

    def treasure_chest_status(self, room_id, opened_at=0):
        cfg=TREASURE_CHESTS.get(room_id)
        if not cfg:
            return None, 0
        opened=float(opened_at or 0.0)
        remaining=max(0,int(round(opened + int(cfg["respawn"]) - time.time())))
        return cfg, remaining

    def open_treasure_chest(self, room_id):
        cfg=TREASURE_CHESTS.get(room_id)
        if not cfg:
            return None
        keys=list(TREASURE_CHEST_RARITIES)
        weights=[TREASURE_CHEST_RARITIES[k][1] for k in keys]
        rarity=random.choices(keys,weights=weights,k=1)[0]
        base=list(cfg.get("base_pool",()))
        set_pool=list(cfg.get("set_pool",()))
        pool=list(base)
        if rarity in ("rare","epic","legendary"):
            pool += set_pool
        item_count={"common":1,"rare":1,"epic":2,"legendary":3}[rarity]
        items=[]
        if pool:
            for _ in range(item_count):
                items.append(random.choice(pool))
        silver={"common":80,"rare":180,"epic":350,"legendary":700}[rarity]
        gold={"common":0,"rare":1,"epic":3,"legendary":7}[rarity]
        return {"rarity":rarity,"items":items,"silver":silver,"gold":gold,"name":cfg["name"]}

    def room_corpses(self, room_id):
        self.refresh()
        return [c for c in self.corpses.values() if c.room_id==room_id]

    def find_corpse(self, room_id, query=""):
        """Znajdź ciało po nazwie albo stabilnym indeksie z listy w pokoju.

        Obsługa v0.9.10: 2.cialo, 2. ciało, 2.corpse, corpse 2 oraz
        2.goblin (drugie pasujące ciało goblina). Numeracja jest wspólna dla
        look/l, przeszukaj/loot oraz wez/get.
        """
        corpses = self.room_corpses(room_id)
        raw = str(query or "").strip()
        q = normalize_lookup_text(raw)
        if not q:
            return corpses[0] if len(corpses) == 1 else None

        corpse_words = ("cialo", "zwloki", "body", "corpse")

        # 2.cialo / 2. cialo / 2.corpse -> drugi wpis z listy wszystkich ciał.
        m = re.match(r"^(\d+)\s*\.?\s*(cialo|zwloki|body|corpse)$", q)
        if m:
            index = int(m.group(1))
            return corpses[index - 1] if 1 <= index <= len(corpses) else None

        # cialo 2 / corpse 2
        m = re.match(r"^(cialo|zwloki|body|corpse)\s+(\d+)$", q)
        if m:
            index = int(m.group(2))
            return corpses[index - 1] if 1 <= index <= len(corpses) else None

        # 2.goblin -> drugie ciało pasujące do nazwy goblina.
        m = re.match(r"^(\d+)\s*\.?\s+(.+)$", q)
        if not m:
            m = re.match(r"^(\d+)\.(.+)$", raw.lower().replace("ł", "l"))
        if m:
            index = int(m.group(1))
            name_query = normalize_lookup_text(m.group(2))
            if name_query in corpse_words:
                return corpses[index - 1] if 1 <= index <= len(corpses) else None
            matches = [
                c for c in corpses
                if name_query in normalize_lookup_text(c.mob_name)
            ]
            return matches[index - 1] if 1 <= index <= len(matches) else None

        # cialo goblin / corpse goblin
        for prefix in corpse_words:
            if q == prefix:
                return corpses[0] if len(corpses) == 1 else None
            if q.startswith(prefix + " "):
                q = q[len(prefix):].strip()
                break

        exact = [c for c in corpses if q == normalize_lookup_text(c.mob_name)]
        if exact:
            return exact[0]
        partial = [c for c in corpses if q in normalize_lookup_text(c.mob_name)]
        return partial[0] if partial else None

    def room_mobs(self, room_id):
        self.refresh()
        return [m for m in self.mobs.values() if m.room_id == room_id and m.alive]

    def find_mob(self, room_id, query):
        """Znajdź dowolnego żywego moba możliwego do walki w pokoju.

        v0.8.35: resolver jest celowo bardziej tolerancyjny dla komendy
        ``k <mob>`` / ``atakuj <mob>``. Obsługuje polskie znaki i ich brak,
        pełną nazwę, id szablonu, początek/fragment nazwy oraz numer wystąpienia
        (np. ``k 2 goblin``). Jeżeli kilka żywych mobów pasuje do zwykłego
        zapytania, wybierane jest najlepsze dostępne dopasowanie zamiast
        odrzucania celu jako niejednoznacznego.
        """
        mobs = self.room_mobs(room_id)
        raw = str(query or "").strip()
        if not raw:
            return mobs[0] if len(mobs) == 1 else None

        requested_index = 1
        index_match = re.match(r"^(\d+)\s+(.+)$", raw)
        if index_match:
            requested_index = max(1, int(index_match.group(1)))
            raw = index_match.group(2).strip()

        q = normalize_lookup_text(raw)
        if not q:
            return None

        ranked = []
        for order, mob in enumerate(mobs):
            template = MOB_TEMPLATES.get(mob.template_id, {})
            # World.room_mobs zwraca tylko żywe moby. max_hp > 0 jest
            # dodatkowym zabezpieczeniem, że cel rzeczywiście należy do walki.
            if int(template.get("max_hp", 0) or 0) <= 0:
                continue

            name = normalize_lookup_text(template.get("name", ""))
            template_id = normalize_lookup_text(mob.template_id)
            aliases = [
                normalize_lookup_text(alias)
                for alias in template.get("mob_aliases", ())
                if str(alias).strip()
            ]
            texts = [name, template_id] + aliases

            score = None
            if any(q == text for text in texts if text):
                score = 0
            elif any(text.startswith(q) for text in texts if text):
                score = 1
            elif any(q in text.split() for text in texts if text):
                score = 2
            elif any(q in text for text in texts if text):
                score = 3

            if score is not None:
                ranked.append((score, order, mob))

        if not ranked:
            return None

        ranked.sort(key=lambda item: (item[0], item[1]))
        best_score = ranked[0][0]
        best = [item[2] for item in ranked if item[0] == best_score]
        if requested_index <= len(best):
            return best[requested_index - 1]
        return None

# v0.24.4: jasne wyświetlanie wspólnego zapasu dla równoległych questów.
HELP_TOPICS.setdefault("questy", []).append(
    "v0.30.7: Questy na ryby, zioła, drewno, rudy i inne zużywane zasoby pamiętają wewnętrznie zdarzenia zdobycia od 0/x, ale widoczny Postęp pokazuje tylko zaliczone sztuki nadal dostępne do oddania. Po zużyciu części zapasu licznik spada odpowiednio; stary zapas sprzed przyjęcia nadal nie daje darmowego postępu."
)

# v0.24.4: finalny HELP umiejętności po zbudowaniu całej siatki 1-600.
_FINAL_SKILL_HELP_ENTRIES = tuple(
    (class_name, skill)
    for class_name, skills in CLASS_SKILLS.items()
    for skill in skills
)
_FINAL_SKILL_HELP_COUNT = len(_FINAL_SKILL_HELP_ENTRIES)
# Indeks dokładnych nazw/ID/aliasów: `help <pełna nazwa>` nie skanuje już
# całej tabeli 1476 wpisów. Fragmenty nadal używają kontrolowanego skanu.
_FINAL_SKILL_HELP_EXACT_INDEX = {}
_FINAL_SKILL_HELP_SEARCH_ROWS = []
for _help_class_name, _help_skill in _FINAL_SKILL_HELP_ENTRIES:
    _help_values = [_help_skill.get("name", ""), _help_skill.get("id", "")]
    _help_values.extend(_help_skill.get("aliases", []))
    _help_norms = tuple(sorted({
        normalize_lookup_text(_value)
        for _value in _help_values
        if normalize_lookup_text(_value)
    }))
    _FINAL_SKILL_HELP_SEARCH_ROWS.append((_help_class_name, _help_skill, _help_norms))
    for _help_key in _help_norms:
        _FINAL_SKILL_HELP_EXACT_INDEX.setdefault(_help_key, []).append(
            (_help_class_name, _help_skill)
        )

HELP_TOPICS.setdefault("umiejetnosci", []).extend([
    f"Aktualna baza zawiera {_FINAL_SKILL_HELP_COUNT} skilli/spelli. Każdy ma własny HELP generowany z aktywnej definicji umiejętności.",
    "Użyj help <pełna nazwa>, help skill <pełna nazwa> albo skill info <pełna nazwa>. Wszystkie aktualne nazwy skilli/spelli są globalnie unikalne.",
])
HELP_TOPICS.setdefault("nazwy_skilli", []).append(
    f"Audyt v0.25.0: {_FINAL_SKILL_HELP_COUNT}/{_FINAL_SKILL_HELP_COUNT} aktualnych skilli/spelli ma dostępny HELP po pełnej, globalnie unikalnej nazwie oraz po identyfikatorze."
)

# v0.30.32: pełne pomoce klas + katalogi skills all / spells all.
_CLASS_TYPE_LABEL_V03032 = {"physical": "fizyczna", "magic": "magiczna"}
for _class_name, _class_type, _soul_weapon, _base_power in CLASSES:
    _topic_key = "klasa_" + normalize_lookup_text(_class_name).replace(" ", "_")
    _teacher = next(
        (npc for npc in NPCS.values() if npc.get("teacher_class") == _class_name),
        None,
    )
    _teacher_name = _teacher.get("name", "brak") if _teacher else "brak"
    _teacher_room = (
        ROOMS.get(_teacher.get("room"), {}).get("name", "nieznana lokacja")
        if _teacher else "nieznana lokacja"
    )
    _skill_count = len(CLASS_SKILLS.get(_class_name, []))
    _scale_text = (
        "Siła dla ofensywy fizycznej; Zręczność wspiera krytyk, unik i szybkość."
        if _class_type == "physical"
        else "Inteligencja dla ofensywy magicznej; Siła Woli wspiera Manę i obronę magiczną."
    )
    HELP_TOPICS[_topic_key] = [
        f"{_class_name}. Typ: {_CLASS_TYPE_LABEL_V03032.get(_class_type, _class_type)}. Broń Duszy: {_soul_weapon}.",
        CLASS_DESCRIPTIONS.get(_class_name, ""),
        _scale_text,
        f"Biegłość klasy: 1-600. Umiejętności/spelle w aktualnej puli: {_skill_count}.",
        f"Nauczyciel: {_teacher_name}. Lokacja: {_teacher_room}.",
        f"Komendy: skills {_class_name}; kodeksklasowy {_class_name}; help skill <nazwa>; multiclass.",
    ]
    for _alias in {_class_name.lower(), normalize_lookup_text(_class_name)}:
        HELP_TOPIC_ALIASES[_alias] = _topic_key

HELP_TOPICS["klasy"] = [
    "Soulbound ma 14 klas: " + ", ".join(row[0] for row in CLASSES) + ".",
    "Każda klasa ma Biegłość 1-600, własną Broń Duszy, pasywy i pulę skilli/spelli.",
    "help <klasa> otwiera osobną pomoc klasy, np. help wojownik, help kapłan, help mag.",
    "skills pokazuje szczegóły umiejętności aktywnych klas; skills all pokazuje nazwy wszystkich umiejętności wszystkich 14 klas.",
    "spells / spels / czary pokazuje czary aktywnych klas magicznych; spells all / spels all pokazuje czary wszystkich klas magicznych.",
    "kodeksklasowy <klasa> czyta pełną progresję, wymagania Biegłości, nauczyciela, koszt i status nauki.",
]
HELP_TOPICS.setdefault("umiejetnosci", []).extend([
    "skills all pokazuje wszystkie skille i spelle pogrupowane klasami, po 20 nazw na linię dla wygodnego czytania NVDA.",
    "spells all / spels all / czary all pokazuje pełną pulę klas magicznych: Mag, Nekromanta, Kapłan, Czarownik, Druid i Psionik.",
    "skills <klasa> oraz spells <klasa magiczna> ograniczają katalog do jednej klasy.",
])
HELP_TOPIC_ALIASES.update({
    "spells": "umiejetnosci", "spels": "umiejetnosci", "czary": "umiejetnosci",
    "skills all": "umiejetnosci", "spells all": "umiejetnosci", "spels all": "umiejetnosci",
})


# v0.25.0: publiczny status Global Generator 2.0.
COMMAND_ALIASES.update({
    "generator": "globalgenerator", "generatory": "globalgenerator",
    "worldgen": "globalgenerator", "generatorświata": "globalgenerator",
    "generatorswiata": "globalgenerator", "losowyswiat": "globalgenerator",
})
HELP_TOPICS["global_generator"] = [
    "Global Generator 2.0 używa jednego trwałego seedu serwera. Seed zapisuje się obok bazy i nie zmienia świata po restarcie.",
    "Generator obejmuje profile wszystkich lokacji, Kopalnię Głębinową, proceduralne piętra lochów, hotspoty profesji, pogodę/sezony, wydarzenia, sekrety, mapy skarbów, dynamiczne questy i tablice kontraktów.",
    "Miasta, ważni NPC, quest huby i fabularni bossowie pozostają stałe, aby losowość nie łamała fabuły ani zapisów.",
    "Godzinne hotspoty profesji dają +5 procent XP profesji/narzędzia w wybranej strefie, ale nie zwiększają liczby surowców, więc nie pompują ekonomii.",
    "Wpisz generator, aby przeczytać profil aktualnej lokacji i aktywne lokalne bonusy.",
]
HELP_TOPIC_ALIASES.update({
    "generator":"global_generator", "generatory":"global_generator",
    "worldgen":"global_generator", "generator swiata":"global_generator",
    "generator świata":"global_generator", "losowy swiat":"global_generator",
    "losowy świat":"global_generator",
})

# ============================================================
# v0.25.0 - UNIQUE NPC NAMES
# Ważni NPC są stałymi postaciami fabularnymi, więc nie losujemy ich przy
# każdym restarcie. Usuwamy natomiast kolizje samych imion, aby komendy,
# questy, HELP i reakcje profesyjne nie myliły dwóch różnych osób.
# ============================================================
V0250_NPC_RENAMES = {
    "mountain_ore_storekeeper_borin": "Magazynier Davor",
    "mountain_scout_harek": "Zwiadowca Kalen",
    "guild_quartermaster_shadow": "Kwatermistrzyni Vessa",
    "cartographer_lysa": "Kartografka Selia",
    "swamp_herbalist_nela": "Bagienna Zielarka Maera",
    "pharmacist_neris": "Aptekarka Elira",
}


def v0250_apply_unique_npc_names():
    replacements = {}
    for npc_id, new_name in V0250_NPC_RENAMES.items():
        npc = NPCS.get(npc_id)
        if not npc:
            continue
        old_name = str(npc.get("name", ""))
        if old_name and old_name != new_name:
            replacements[old_name] = new_name
            npc["name"] = new_name

    if not replacements:
        return

    # Quest giver jest tekstem wyświetlanym graczowi; targety używają ID NPC.
    for quest in QUESTS.values():
        giver = str(quest.get("giver", ""))
        if giver in replacements:
            quest["giver"] = replacements[giver]
        description = str(quest.get("description", ""))
        for old_name, new_name in replacements.items():
            description = description.replace(old_name, new_name)
        if description:
            quest["description"] = description

    # Aktualizuj tekstowe HELP-y, aby nie zostały stare imiona po migracji.
    for topic, lines in list(HELP_TOPICS.items()):
        if not isinstance(lines, list):
            continue
        fixed = []
        for line in lines:
            text = str(line)
            for old_name, new_name in replacements.items():
                text = text.replace(old_name, new_name)
            fixed.append(text)
        HELP_TOPICS[topic] = fixed

    # Odmiany i skrócone odwołania, których nie da się poprawić samą
    # zamianą pełnej nazwy NPC. Dotyczy wyłącznie przemianowanych postaci.
    text_replacements = {
        "Magazyniera Borina": "Magazyniera Davora",
        "Magazynier Borin": "Magazynier Davor",
        "wróć do Harka": "wróć do Kalena",
        "Aptekarce Neris": "Aptekarce Elirze",
        "Aptekarka Neris": "Aptekarka Elira",
        "quest list Neris": "quest list Elira",
        "Neris ma powtarzalny co 60 minut quest na 8 świeżo zebranych ziół":
            "Elira ma powtarzalny co 60 minut quest na 8 świeżo zebranych ziół",
    }
    for quest in QUESTS.values():
        for field in ("giver", "description"):
            text = str(quest.get(field, ""))
            for old_text, new_text in text_replacements.items():
                text = text.replace(old_text, new_text)
            if text:
                quest[field] = text
    for npc in NPCS.values():
        text = str(npc.get("dialogue", ""))
        for old_text, new_text in text_replacements.items():
            text = text.replace(old_text, new_text)
        if text:
            npc["dialogue"] = text
    for topic, lines in list(HELP_TOPICS.items()):
        if not isinstance(lines, list):
            continue
        fixed = []
        for line in lines:
            text = str(line)
            for old_text, new_text in text_replacements.items():
                text = text.replace(old_text, new_text)
            fixed.append(text)
        HELP_TOPICS[topic] = fixed


v0250_apply_unique_npc_names()


def v0250_duplicate_npc_given_names():
    seen = {}
    duplicates = {}
    for npc_id, npc in NPCS.items():
        name = str(npc.get("name", "")).strip()
        if not name:
            continue
        given = name.split()[-1].casefold()
        if given in seen:
            duplicates.setdefault(given, [seen[given]]).append((npc_id, name))
        else:
            seen[given] = (npc_id, name)
    return duplicates


# ============================================================
# v0.26.0 - MUZEUM 2.0 + TYTUŁY I PRESTIŻ
# Jedna, osiągalna kolekcja końcowa bez dublowania wpisów starego Codexu.
# ============================================================
V0260_WOOD_CATALOG = {
    item_id: ITEMS[item_id]["name"]
    for item_id in sorted(WOOD_RESOURCE_IDS)
    if item_id in ITEMS
}

V0260_LEGENDARY_ITEM_CATALOG = {
    item_id: data["name"]
    for item_id, data in ITEMS.items()
    if (
        str(data.get("rarity", "")).lower() in ("legendary", "mythic", "eternal")
        or data.get("legendary_set_loot")
        or data.get("legendary_class_relic")
    )
    and not str(item_id).startswith("corpse_")
}


def _v0260_set_piece_key(item_id, item):
    if item.get("class_set_name"):
        return str(item.get("class_set_piece") or item.get("slot") or item_id)
    if item.get("crypt_set_tier"):
        return str(item.get("crypt_base_item") or item_id)
    return str(item_id)


def _v0260_build_set_piece_groups():
    groups = {}
    for item_id, set_id in SET_ENTRY_BY_ITEM.items():
        item = ITEMS.get(item_id, {})
        piece_key = _v0260_set_piece_key(item_id, item)
        groups.setdefault(set_id, {}).setdefault(piece_key, set()).add(item_id)
    return {
        set_id: {piece: frozenset(ids) for piece, ids in pieces.items()}
        for set_id, pieces in groups.items()
    }


V0260_SET_PIECE_GROUPS = _v0260_build_set_piece_groups()
V0260_SET_CATALOG = {
    set_id: row["name"] for set_id, row in SET_COLLECTION_CATALOG.items()
}

V0260_SURFACE_SECRET_CATALOG = {}
for _rid in v0140_surface_secret_room_ids():
    _info = v0140_surface_secret_info(_rid)
    if _info:
        V0260_SURFACE_SECRET_CATALOG[_rid] = _info["name"]

V0260_INSTANCE_SECRET_CATALOG = {}
for _kind, _info in INSTANCE_MAP_DEFS.items():
    for _idx, _title in enumerate(INSTANCE_SECRET_TITLES):
        _key = f"instance:{_kind}:{_idx}"
        V0260_INSTANCE_SECRET_CATALOG[_key] = f"{_title} — {_info['label']}"

V0260_SECRET_CATALOG = dict(V0260_SURFACE_SECRET_CATALOG)
V0260_SECRET_CATALOG.update(V0260_INSTANCE_SECRET_CATALOG)

V0260_MUSEUM_CATALOGS = {
    "fish": FISH_COLLECTION_CATALOG,
    "minerals": MINERAL_COLLECTION_CATALOG,
    "herbs": HERB_COLLECTION_CATALOG,
    "wood": V0260_WOOD_CATALOG,
    "bosses": BOSS_COLLECTION_CATALOG,
    "sets": V0260_SET_CATALOG,
    "legendary": V0260_LEGENDARY_ITEM_CATALOG,
    "secrets": V0260_SECRET_CATALOG,
}
V0260_MUSEUM_LABELS = {
    "fish": "Ryby",
    "minerals": "Rudy i minerały",
    "herbs": "Zioła",
    "wood": "Drewno",
    "bosses": "Bossowie",
    "sets": "Kompletne sety",
    "legendary": "Legendarne przedmioty",
    "secrets": "Sekrety",
}
V0260_MUSEUM_ALIASES = {
    "ryby": "fish", "ryba": "fish", "fish": "fish",
    "rudy": "minerals", "mineral": "minerals", "mineraly": "minerals", "minerały": "minerals", "minerals": "minerals",
    "ziola": "herbs", "zioła": "herbs", "herbs": "herbs",
    "drewno": "wood", "wood": "wood",
    "boss": "bosses", "bossowie": "bosses", "bosses": "bosses",
    "set": "sets", "sety": "sets", "sets": "sets",
    "legendy": "legendary", "legendarne": "legendary", "legendarny": "legendary", "legendary": "legendary",
    "sekrety": "secrets", "sekret": "secrets", "secrets": "secrets",
}

V0260_MUSEUM_CATEGORY_TITLES = {
    "fish": "Mistrz Wielkich Wód",
    "minerals": "Mistrz Głębin",
    "herbs": "Arcyzielarz Dziedzictwa",
    "wood": "Strażnik Starych Borów",
    "bosses": "Pogromca Wszystkich Bossów",
    "sets": "Kustosz Zbrojowni",
    "legendary": "Strażnik Legend",
    "secrets": "Kartograf Końca Świata",
}
V0260_GLOBAL_MUSEUM_TITLES = (
    (10, "Kolekcjoner Dusz"),
    (25, "Badacz Dziedzictwa"),
    (50, "Kustosz Soulbound"),
    (75, "Mistrz Muzeum"),
    (90, "Strażnik Dziedzictwa"),
    (100, "Legenda Kompletnej Kolekcji"),
)
V0260_TITLE_BONUSES = {
    "Mistrz Wielkich Wód": {"tool": "fishing", "percent": 2, "text": "+2% XP Wędkarstwa i Wędki"},
    "Mistrz Głębin": {"tool": "mining", "percent": 2, "text": "+2% XP Górnictwa i Kilofa"},
    "Arcyzielarz Dziedzictwa": {"tool": "herbalism", "percent": 2, "text": "+2% XP Zielarstwa i Sierpa"},
    "Strażnik Starych Borów": {"tool": "woodcutting", "percent": 2, "text": "+2% XP Drwalstwa i Piły"},
    "Legenda Kompletnej Kolekcji": {"tool": "all", "percent": 1, "text": "+1% XP wszystkich profesji i narzędzi"},
}


def v0260_museum_rank(percent):
    percent = max(0, min(100, int(percent)))
    if percent >= 100:
        return "Legenda Muzeum"
    if percent >= 90:
        return "Strażnik Dziedzictwa"
    if percent >= 75:
        return "Mistrz Muzeum"
    if percent >= 50:
        return "Kustosz"
    if percent >= 25:
        return "Badacz Dziedzictwa"
    if percent >= 10:
        return "Kolekcjoner"
    return "Nowicjusz"


COMMAND_ALIASES.update({
    "muzeum": "museum", "museum": "museum", "kolekcje": "museum",
    "prestiz": "prestige", "prestiż": "prestige", "prestige": "prestige",
})
HELP_TOPIC_ALIASES.update({
    "muzeum": "museum_v026", "museum": "museum_v026", "kolekcje": "museum_v026",
    "prestiz": "prestige_v026", "prestiż": "prestige_v026", "prestige": "prestige_v026",
})
HELP_TOPICS["museum_v026"] = [
    "Muzeum 2.0 śledzi osiem skończonych kolekcji: ryby, rudy/minerały, zioła, drewno, bossów, kompletne sety, legendarne przedmioty i sekrety.",
    "muzeum / museum - podsumowanie wszystkich działów i globalny procent ukończenia kolekcji gry. Każdy z 8 działów waży równo po 12,5% wyniku.",
    "muzeum ryby|rudy|ziola|drewno|bossowie|sety|legendarne|sekrety [strona] - szczegóły działu. Nieodkryte wpisy nie zdradzają nazw.",
    "Set zalicza się dopiero po odkryciu wszystkich jego logicznych części. Sekrety nieskończonych instancji liczą skończone archetypy sekretów dla każdego typu instancji.",
    "100% działu odblokowuje tytuł. Tytuły czterech profesji dają mały bonus +2% XP właściwej profesji i narzędzia tylko wtedy, gdy są aktywne.",
]
HELP_TOPICS["prestige_v026"] = [
    "prestiz / prestiż / prestige - pokaż Prestiż Muzealny 0-1000, rangę, globalne ukończenie i aktywny bonus tytułu.",
    "Prestiż Muzealny wynika wyłącznie z procentu ukończenia Muzeum: 100% = 1000 punktów. Nie resetuje postaci i nie zużywa kolekcji.",
    "Większość tytułów jest prestiżowa. Mistrz Wielkich Wód, Mistrz Głębin, Arcyzielarz Dziedzictwa i Strażnik Starych Borów dają po +2% XP swojej profesji/narzędzia; Legenda Kompletnej Kolekcji daje +1% wszystkim profesjom i narzędziom.",
]
# Nadpisz dawną informację, że absolutnie wszystkie tytuły są kosmetyczne.
HELP_TOPICS["tytuly"] = [
    "tytuly / titles - lista odblokowanych tytułów wraz z informacją o ewentualnym bonusie.",
    "tytul <numer lub nazwa> / title <number or name> - ustaw aktywny tytuł; tytul off wyłącza tytuł.",
    "Większość tytułów jest czysto prestiżowa. Wybrane tytuły Muzeum mają mały bonus do XP profesji/narzędzia; tytuły nie zwiększają obrażeń ani obrony.",
]

# Łowca 1000 Bossów jest długoterminowym, prestiżowym progiem bez bonusu bojowego.
_boss_tiers = list(ACHIEVEMENT_TRACKS["boss_kills"]["tiers"])
if not any(int(req) == 1000 for req, _tier in _boss_tiers):
    _boss_tiers.append((1000, "Mythic"))
ACHIEVEMENT_TRACKS["boss_kills"]["tiers"] = tuple(_boss_tiers)
ACHIEVEMENT_TITLE_REWARDS[("boss_kills", "Mythic")] = "Łowca 1000 Bossów"
