from data import catalog_mutations as _catalog_mut
from core.bootstrap_economy_professions import SILVER_PER_GOLD
from core.mines_threat import v0866_room_threat_profile
from systems.items_resources import economy_stage_anchor_v11314
from systems.infinite_equipment import infinite_equipment_variant_for_drop
from systems.elite_legends_v1250 import (
    legendary_roll_v1250, legend_variant_id_v1250, build_legendary_v1250,
)
from systems.elite_variants import (
    build_elite_variant_template_v11338,
    elite_roll_affix_v11338,
    elite_source_template_id_v11338,
    elite_variant_id_v11338,
)
from world.world_secrets_v1190 import (
    create_world_secret_rooms_v1190, secret_room_identity_v1190,
    attach_surface_secret_npc_v1190,
)
from world.uoss_superboss_world import (
    create_infinite_uoss_deep_dungeon_floor_definition_v11331,
    uoss_deep_dungeon_floor_number_v11331,
)

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
    # AoE: mob trafiony obszarówką zachowuje aggro nawet gdy nie jest głównym combat_mob_key.
    aoe_engaged_by: Optional[str] = None
    # v1.13.30: encounter-local adaptive scaling. Template identity stays intact.
    adaptive_max_hp_v11330: int = 0
    adaptive_hp_multiplier_v11330: float = 1.0
    adaptive_reward_multiplier_v11330: float = 1.0
    adaptive_party_size_v11330: int = 1
    adaptive_party_dps_v11330: float = 0.0
    adaptive_rank_v11330: str = ""


# ============================================================
# v0.29.0 - DYNAMIC WORLD EVENTS + BOSS/NEMESIS GENERATOR
# ============================================================
def v0290_active_world_events(now=None):
    events = dynamic_world_v029.active_events(
        ROOMS, MOB_SPAWNS, MOB_TEMPLATES, str(V0250_WORLD_SEED), now=now
    )
    # v1.20.0: use the EXISTING ephemeral event spawner for new regions.
    # The module is imported lazily because this World module precedes its
    # authored catalogs in the legacy bootstrap order.
    from world.great_world import v1200_rotating_events
    return tuple(events) + v1200_rotating_events(now)

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


# Weighted mean payout is ~9.6% of a full same-stage economy activity.
V11314_TREASURE_CHEST_PAYOUT_MULTIPLIERS = {
    "common": 0.045,
    "rare": 0.100,
    "epic": 0.250,
    "legendary": 0.600,
}
V11314_TREASURE_CHEST_LEGACY_COINS = {
    "common": 80,
    "rare": 280,
    "epic": 650,
    "legendary": 1_400,
}


def treasure_chest_economy_stage_v11314(room_id):
    """Etap skrzyni wynika z lokacji i jej realnych spawnów, nie z gracza."""
    room = ROOMS.get(str(room_id or ""), {}) or {}
    candidates = []
    for key in ("generator_level", "recommended_mastery"):
        try:
            value = int(room.get(key, 0) or 0)
        except (TypeError, ValueError, OverflowError):
            value = 0
        if value > 0:
            candidates.append(value)
    fallback = max(candidates) if candidates else 1
    try:
        profile = v0866_room_threat_profile(room_id, fallback=fallback)
        target = int((profile or {}).get("target", fallback) or fallback)
    except Exception as exc:
        print(
            f"TREASURE_CHEST_STAGE_FALLBACK_ERROR: {type(exc).__name__}: {exc}",
            flush=True,
        )
        target = fallback
    return max(1, min(800, max(fallback, target)))


class World:
    def __init__(self):
        self.mobs = {}
        self.corpses = {}
        self.corpse_counter = 0
        self.treasure_chest_opened_at = {}
        # Boss chest visibility can recover after an actual boss respawn or restart.
        self.boss_chest_world_started_v1288 = time.time()
        # v0.71.5: repeated combat/command paths used to rescan the entire
        # world several times per command.  Keep a tiny freshness window; the
        # dedicated wander loop still forces a refresh every five seconds.
        self._last_refresh_at = 0.0
        self._refresh_min_interval = 0.25
        self._last_live_counts = {}
        self._last_live_by_room = {}
        counts = {}
        # v0.36.2: initial open-world spawns use the CURRENT room stage, not only
        # the shared base template's earliest spawn. This keeps terrain 100+
        # and endgame regions from inheriting low-level combat numbers.
        for room_id, template_id in list(MOB_SPAWNS):
            template_id = resolve_world_spawn_template(template_id)
            spawn_template_id = self._terrain_scaled_template_v0362(room_id, template_id)
            counts[(room_id, spawn_template_id)] = counts.get((room_id, spawn_template_id), 0) + 1
            n = counts[(room_id, spawn_template_id)]
            key = f"{room_id}:{spawn_template_id}:{n}"
            template_id = self._elite_spawn_template_v11338(spawn_template_id)
            v0190_apply_combat_template(MOB_TEMPLATES[template_id])
            self.mobs[key] = MobState(
                key=key, room_id=room_id, template_id=template_id,
                hp=MOB_TEMPLATES[template_id]["max_hp"],
                home_room_id=room_id,
                next_wander_at=time.time() + random.uniform(
                    MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS
                ),
            )
            self._last_refresh_at = 0.0

    def _elite_spawn_template_v11338(self, template_id):
        """Roll one ordinary spawn into a reviewed elite affix, if eligible."""
        template_id = str(template_id or "")
        current = MOB_TEMPLATES.get(template_id)
        if not isinstance(current, dict):
            return template_id
        source_id = elite_source_template_id_v11338(template_id, current)
        source = MOB_TEMPLATES.get(source_id, current)
        # v1.25 rarer tiers roll before ordinary elite affixes; one variant per spawn.
        legend_rank = legendary_roll_v1250(source)
        if legend_rank:
            legend_id = legend_variant_id_v1250(source_id, legend_rank)
            if legend_id not in MOB_TEMPLATES:
                clone = build_legendary_v1250(source_id, source, legend_rank)
                _catalog_mut.catalog_assign(clone, "MOB_TEMPLATES", MOB_TEMPLATES, (legend_id,))
                v0190_apply_combat_template(MOB_TEMPLATES[legend_id])
            return legend_id
        affix = elite_roll_affix_v11338(source)
        if not affix:
            return source_id
        variant_id = elite_variant_id_v11338(source_id, affix)
        if variant_id not in MOB_TEMPLATES:
            clone = build_elite_variant_template_v11338(source_id, source, affix)
            _catalog_mut.catalog_assign(
                clone, "MOB_TEMPLATES", MOB_TEMPLATES, (variant_id,)
            )
            v0190_apply_combat_template(MOB_TEMPLATES[variant_id])
        return variant_id

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
        rank = balance_math.mob_rank(template)
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
            balance_math.runtime_mob_balance(runtime_id, clone, runtime_stage, rank=rank)
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
            _catalog_mut.catalog_assign(clone, 'MOB_TEMPLATES', MOB_TEMPLATES, (runtime_id,))
        return runtime_id

    def _register_runtime_spawn(self, room_id, template_id):
        room_meta = ROOMS.get(str(room_id or ""), {})
        spawn_template_id = self._terrain_scaled_template_v0362(room_id, template_id)
        template_meta = MOB_TEMPLATES.get(spawn_template_id)
        if isinstance(template_meta, dict):
            template_meta["auto_aggro"] = False
        if not any(r == room_id and t == spawn_template_id for r, t in MOB_SPAWNS):
            MOB_SPAWNS.append((room_id, spawn_template_id))
        existing = [
            m for m in self.mobs.values()
            if m.room_id == room_id
            and elite_source_template_id_v11338(
                m.template_id, MOB_TEMPLATES.get(m.template_id, {})
            ) == spawn_template_id
        ]
        if existing:
            return existing[0]
        n = 1 + sum(
            1 for m in self.mobs.values()
            if m.room_id == room_id
            and elite_source_template_id_v11338(
                m.template_id, MOB_TEMPLATES.get(m.template_id, {})
            ) == spawn_template_id
        )
        key = f"{room_id}:{spawn_template_id}:{n}"
        template_id = self._elite_spawn_template_v11338(spawn_template_id)
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
        self._last_refresh_at = 0.0
        return mob

    def spawn_superboss_summon_v1144(self, boss_mob, template_id):
        """Spawn an encounter-only add; never register it in persistent MOB_SPAWNS.

        Distinct summons (notably Odin's three Gungnirs) must have distinct
        MobState keys. A summoned add shares the owner's engagement and cannot
        respawn as a permanent world mob after the fight.
        """
        template=MOB_TEMPLATES.get(str(template_id))
        if not boss_mob or not boss_mob.alive or not template:
            return None
        owner=str(getattr(boss_mob,"engaged_by","") or "")
        if not owner:
            return None
        number=int(getattr(boss_mob,"uoss_add_sequence_v1144",0) or 0)+1
        boss_mob.uoss_add_sequence_v1144=number
        key=f"{boss_mob.key}:uoss_add:{number}"
        add=MobState(
            key=key, room_id=boss_mob.room_id, template_id=str(template_id),
            hp=int(template.get("max_hp",1)), engaged_by=owner,
            engaged_at=time.monotonic(), home_room_id=boss_mob.room_id,
        )
        add.v016_ephemeral=True
        add.v016_expires_at=time.time()+1800
        add.uoss_summon_parent_v1144=boss_mob.key
        self.mobs[key]=add
        self._last_refresh_at=0.0
        return add

    def spawn_boss_companion_v1281(self, boss_mob):
        """Spawn a temporary guardian tied to a real boss, with XP on defeat."""
        from systems.boss_companions_v1281 import boss_guardian_role_v12811
        if not boss_mob or not boss_mob.alive or not boss_mob.engaged_by:
            return None
        parent_template = MOB_TEMPLATES.get(boss_mob.template_id, {})
        if not parent_template or parent_template.get("uoss_unique_superboss_key"):
            return None
        # v1.28.9: summons have NO simultaneous-live count limit. Each
        # scheduled boss action creates another distinct guardian, even if all
        # earlier guardians are still alive; parent-death cleanup is unchanged.
        seq = int(getattr(boss_mob, "boss_add_seq_v1281", 0) or 0) + 1
        boss_mob.boss_add_seq_v1281 = seq
        role, title, damage_type, hp_mult, damage_mult = boss_guardian_role_v12811(
            parent_template, boss_mob, seq)
        tid = f"{boss_mob.template_id}__guardian_{role}_v12811"
        if tid not in MOB_TEMPLATES:
            parent_level = max(1, int(parent_template.get("level", 1) or 1))
            authored_hp = max(1, int(parent_template.get("max_hp", 1) or 1))
            reward = max(500, parent_level * 400,
                         int(parent_template.get("source_xp", 0) or 0) // 8)
            parent_stage = max(1, min(800, int(parent_template.get("v019_stage") or
                                           parent_template.get("generator_level") or
                                           parent_level)))
            guardian_hp = max(100, int(authored_hp * hp_mult) // 5)
            guardian = {
                "name": f"{title} {parent_template.get('name', 'Bossa')}",
                "level": parent_level, "max_hp": guardian_hp,
                "base_max_hp": guardian_hp, "max_mp": 0,
                "v019_stage": parent_stage, "generator_level": parent_stage,
                "damage": max(1, int((parent_template.get("damage", 10) or 10) * damage_mult) // 3),
                "damage_type": damage_type, "silver": 0, "gold": 0, "mithril": 0,
                "source_xp": reward, "source_xp_exact": True,
                "character_xp_reward": 0, "class_xp_reward": 0,
                "soul_reward": 0, "stat_reward": 0, "drops": {},
                "quest_target": None, "stationary_mob": True, "auto_aggro": False,
                "boss_companion_v1281": True, "boss_guardian_role_v12811": role,
            }
            _catalog_mut.catalog_assign(guardian, "MOB_TEMPLATES", MOB_TEMPLATES, (tid,))
        boss_max_hp = max(1, int(getattr(boss_mob, "adaptive_max_hp_v11330", 0) or
                                 parent_template.get("max_hp", 100) or 100))
        cap = max(100, int(boss_max_hp * hp_mult) // 5)
        if role == "uzdrowiciel":
            # The healer has an actual support effect, not just a healer name.
            boss_mob.hp = min(boss_max_hp, max(0, int(boss_mob.hp)) + max(1, boss_max_hp // 40))
        add = MobState(
            key=f"{boss_mob.key}:boss_guard:{seq}", room_id=boss_mob.room_id,
            template_id=tid, hp=cap, engaged_by=boss_mob.engaged_by,
            engaged_at=time.monotonic(), home_room_id=boss_mob.room_id,
        )
        add.monster_ai_parent_v1160 = boss_mob.key
        add.monster_ai_summoned_v1160 = True
        add.v016_ephemeral = True
        add.v016_expires_at = time.time() + 1800
        self.mobs[add.key] = add
        self._last_refresh_at = 0.0
        return add

    def mob_templates_for_ai_v1160(self, mob):
        return MOB_TEMPLATES.get(str(getattr(mob, "template_id", "")), {})

    def spawn_monster_ai_add_v1160(self, parent, template_id, now=None):
        """One unbankable, short-lived summon per encounter, using existing templates."""
        import time as _time
        now = _time.monotonic() if now is None else float(now)
        if not parent or not parent.alive or not parent.engaged_by:
            return None
        current = [add for add in self.mobs.values()
                   if getattr(add, "monster_ai_parent_v1160", None) == parent.key and add.alive]
        if current:
            return None
        template = MOB_TEMPLATES.get(str(template_id), {})
        if not template or any(template.get(f) for f in ("uoss_superboss", "boss", "world_boss", "training_dummy")):
            return None
        # Register a distinguishable, ephemeral display species. Attacking by name
        # must not confuse the summoned shade with the original creature in NVDA.
        summon_template_id = f"{template_id}__monster_ai_shade_v1160"
        if summon_template_id not in MOB_TEMPLATES:
            shade_template = dict(template)
            shade_template["name"] = "Widmo " + " ".join(str(template.get("name", "Potwór")).split()[-2:])
            shade_template["quest_target"] = ""
            shade_template["elite_affix"] = ""
            shade_template["boss_mechanic"] = ""
            shade_template["ai_ephemeral_summon_v1160"] = True
            _catalog_mut.catalog_assign(shade_template, "MOB_TEMPLATES", MOB_TEMPLATES, (summon_template_id,))
        seq = int(getattr(parent, "monster_ai_add_sequence_v1160", 0) or 0) + 1
        parent.monster_ai_add_sequence_v1160 = seq
        add = MobState(
            key=f"{parent.key}:ai_add:{seq}", room_id=parent.room_id,
            template_id=summon_template_id, hp=max(1, int(template.get("max_hp", 1) * .4)),
            engaged_by=parent.engaged_by, engaged_at=now,
            home_room_id=parent.room_id,
        )
        add.monster_ai_parent_v1160 = parent.key
        add.monster_ai_summoned_v1160 = True
        add.v016_ephemeral = True
        add.v016_expires_at = _time.time() + 120.0
        self.mobs[add.key] = add
        self._last_refresh_at = 0.0
        return add

    def clear_monster_ai_adds_v1160(self, parent):
        removed = 0
        for add in self.mobs.values():
            if getattr(add, "monster_ai_parent_v1160", None) == parent.key and add.alive:
                add.alive = False
                add.engaged_by = None
                add.respawn_at = float("inf")
                add.v016_expires_at = __import__("time").time() - 1
                removed += 1
        if removed:
            self._last_refresh_at = 0.0
        return removed

    def engage_superboss_companions_v1144(self, boss_mob):
        """Culex crystals and Ruby tentacles already spawn in their arena.

        Join them to the existing battle exactly once, without cloning adds.
        """
        if not boss_mob or not boss_mob.alive or not boss_mob.engaged_by:
            return ()
        boss_template=MOB_TEMPLATES.get(boss_mob.template_id,{})
        boss_key=str(boss_template.get("uoss_unique_superboss_key") or "")
        if boss_key not in ("culex","ruby_weapon"):
            return ()
        newly=[]
        for add in self.mobs.values():
            if add.room_id != boss_mob.room_id or not add.alive or add.key==boss_mob.key:
                continue
            add_template=MOB_TEMPLATES.get(add.template_id,{})
            if not add_template.get("uoss_superboss_add") or add_template.get("parent") != boss_key:
                continue
            if add.engaged_by:
                continue
            add.engaged_by=boss_mob.engaged_by
            add.engaged_at=time.monotonic()
            newly.append(add)
        return tuple(newly)

    def clear_superboss_companions_v1144(self, boss_mob):
        """A defeated boss cannot leave active minions attacking its party."""
        if not boss_mob:
            return 0
        owner=str(getattr(boss_mob,"engaged_by","") or "")
        boss_key=str(MOB_TEMPLATES.get(boss_mob.template_id,{}).get("uoss_unique_superboss_key") or "")
        cleared=0
        for add in self.mobs.values():
            if add.room_id!=boss_mob.room_id or add.key==boss_mob.key:
                continue
            child=str(getattr(add,"uoss_summon_parent_v1144","") or "")
            static=bool(boss_key and MOB_TEMPLATES.get(add.template_id,{}).get("parent")==boss_key
                        and MOB_TEMPLATES.get(add.template_id,{}).get("uoss_superboss_add"))
            if child==boss_mob.key:
                add.alive=False
                add.engaged_by=None
                add.respawn_at=float("inf")
                add.v016_expires_at=time.time()-1
                cleared+=1
            elif static and (not owner or add.engaged_by==owner):
                add.engaged_by=None
                cleared+=1
        self._last_refresh_at=0.0
        return cleared

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
                    event, index, MOB_TEMPLATES, balance_math, str(V0250_WORLD_SEED)
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
                self._last_refresh_at = 0.0
                created.append(mob)
        return created

    def remove_v029_nemesis(self, account_id):
        account_id = int(account_id)
        for key, mob in list(self.mobs.items()):
            tmpl = MOB_TEMPLATES.get(mob.template_id, {})
            if int(tmpl.get("v029_nemesis_owner_account_id", 0) or 0) == account_id:
                self.mobs.pop(key, None)
                self._last_refresh_at = 0.0

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
        template_id, _ = dynamic_world_v029.build_nemesis_template(record, MOB_TEMPLATES, balance_math)
        if not template_id:
            return None
        mob = MobState(
            key=f"v029nemesis:{account_id}:{int(record['rank'])}:{template_id}",
            room_id=room_id, template_id=template_id, hp=MOB_TEMPLATES[template_id]["max_hp"],
            home_room_id=room_id, next_wander_at=time.time()+365*24*3600,
        )
        mob.v016_ephemeral = True
        self.mobs[mob.key] = mob
        self._last_refresh_at = 0.0
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
            self._last_refresh_at = 0.0
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
            self.mobs[mob.key]=mob; self._last_refresh_at = 0.0; created.append(mob)
        return created

    def _ensure_v0140_event_spawn(self, room_id, now=None):
        created = []
        events = (
            v11339_combat_events_for_room(room_id, now=now)
            if "v11339_combat_events_for_room" in globals()
            else tuple(
                event for event in (
                    v0140_event_for_room(room_id, "rare_hunt", now=now),
                )
                if event
            )
        )
        for event in events:
            event_key = "v0140event:" + event["token"]
            existing = next(
                (
                    mob for mob in self.mobs.values()
                    if getattr(mob, "v0140_event_key", "") == event_key
                ),
                None,
            )
            if existing:
                created.append(existing)
                continue
            if "v11339_named_rare_template_for_kind" in globals():
                template_id = v11339_named_rare_template_for_kind(
                    event["kind"], event.get("type", "rare_hunt")
                )
            else:
                template_id = v0140_rare_template_for_kind(
                    event["kind"], salt=event["token"]
                )
            if not template_id:
                continue
            key = f"{event_key}:{template_id}"
            mob = MobState(
                key=key, room_id=room_id, template_id=template_id,
                hp=MOB_TEMPLATES[template_id]["max_hp"], home_room_id=room_id,
                next_wander_at=time.time() + random.uniform(
                    MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS
                ),
            )
            mob.v0140_event_key = event_key
            mob.v0140_event_expires_at = float(event["expires_at"])
            self.mobs[key] = mob
            self._last_refresh_at = 0.0
            created.append(mob)
        return created[0] if created else None

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
        self._last_refresh_at = 0.0
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
        attach_surface_secret_npc_v1190(created_room, ROOMS, NPCS)
        for spawn_room, template_id in spawns:
            self._register_runtime_spawn(spawn_room, template_id)
        _ROOM_THREAT_CACHE.pop(created_room, None)
        _ZONE_THREAT_CACHE.clear()
        return True

    def _generatorize_runtime_room(self, room_id):
        room=ROOMS.get(str(room_id or ""))
        if isinstance(room,dict):
            balance_math.runtime_room_level(str(room_id),room,ROOMS)
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

    def _ensure_city_world_event_v12812(self, room_id):
        from systems.world_events_v12812 import active_city_event_v12812
        event = active_city_event_v12812()
        if event['room_id'] != str(room_id):
            return False
        key=f"v12812:event:{event['slot']}:{event['slug']}"
        if key in self.mobs: return True
        template_id=event['template_id']
        if template_id not in MOB_TEMPLATES: return False
        v0190_apply_combat_template(MOB_TEMPLATES[template_id])
        mob=MobState(
            key=key, room_id=str(room_id), template_id=template_id,
            hp=int(MOB_TEMPLATES[template_id]['max_hp']),
            home_room_id=str(room_id), next_wander_at=event['expires_at'])
        mob.v016_ephemeral=True
        mob.v029_expires_at=float(event['expires_at'])
        self.mobs[key]=mob
        self._last_refresh_at=0.0
        return True

    def ensure_runtime_room(self, room_id):
        room_id = str(room_id or "")
        # Private, mined-out chambers are recreated deterministically after deploy.
        from core.mine_tunnels import mine_tunnel_identity
        tunnel = mine_tunnel_identity(room_id)
        if tunnel is not None and room_id not in ROOMS:
            floor, account_id, x, y = tunnel
            base_id = mine_floor_id(floor)
            if not self.ensure_runtime_room(base_id):
                return False
            base = ROOMS[base_id]
            from core.mine_world_v1260 import geology_v1260
            geo = geology_v1260(floor, x, y)
            gather = dict(base.get('infinite_gather_feature', {}) or {})
            if geo['bonus_quantity']:
                gather['quantity_bonus'] = int(gather.get('quantity_bonus',0) or 0) + geo['bonus_quantity']
                gather['xp_mult'] = max(1.,float(gather.get('xp_mult',1.) or 1.)) * (1 + min(2.,geo['richness']/5.))
                gather['label'] = geo['name']
            _catalog_mut.catalog_assign({
                'zone': 'Kopalnia Głębinowa',
                'name': f'Kopalnia - poziom {floor}, chodnik ({x}, {y})',
                'desc': f"{geo['description']} Wykopana przez górnika odnoga na poziomie {floor}. Kierunki: kopalnia mapa, kopalnia droga.",
                'exits': {
                    'up': 'crystal_chamber' if floor == 1 else mine_floor_id(floor - 1),
                    'down': mine_floor_id(floor + 1),
                },
                'procedural_infinite': True,
                'generated_on_demand': True,
                'mine_tunnel_owner_v1251': account_id,
                'infinite_gather_feature': gather,
                'mine_geology_v1260':geo['kind'],
            }, 'ROOMS', ROOMS, (room_id,))
            if geo['has_guardian']:
                # A real killable boss guarding a one-time treasure; combat and
                # loot still use the native Soulbound systems.
                guard_id = f'mine_guard_v1260_{floor}_{geo["distance"]}'
                if guard_id not in MOB_TEMPLATES:
                    import copy
                    guard = copy.deepcopy(MOB_TEMPLATES['goblin_warchief'])
                    guard.update({
                        'name':f'Strażnik Skarbca Głębin, poziom {floor}',
                        'boss': True, 'world_boss': False,
                        'max_hp':max(300,int((floor+geo['distance'])*120)),
                        'damage':max(8,int(floor*2.5)),
                        'gold':max(10,int(floor * geo['richness'] * 10)),
                        'soul_reward':max(1000, int(floor * geo['richness']*120)),
                        'stat_reward':max(200,int(floor*geo['richness']*50)),
                        'quest_target':None,
                        'mine_guard_v1260':True,
                    })
                    _catalog_mut.catalog_assign(guard, 'MOB_TEMPLATES', MOB_TEMPLATES, (guard_id,))
                self._register_runtime_spawn(room_id,guard_id)
            return True
        if room_id in ROOMS:
            self._ensure_city_world_event_v12812(room_id)
            self._generatorize_runtime_room(room_id)
            # v1.19.3: generated secret chamber/archive have their own
            # curated guardian and rare encounters. Generic world-event
            # spawners are not valid here: repeated entrance previously
            # produced extra enemies and could block guarded treasure.
            # Rehydration at server start is handled by MOB_SPAWNS.
            if ROOMS[room_id].get("v1190_secret_role") in ("chamber", "archive", "vault"):
                return True
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
        # v1.19.0: rehydrate player position inside a secret chamber after restart.
        secret = secret_room_identity_v1190(room_id)
        if secret:
            role, kind, floor = secret
            if kind not in INSTANCE_MAP_DEFS or not instance_secret_name(kind, floor):
                return False
            parent = {
                "crypt": crypt_floor_id, "mythic_crypt": mythic_crypt_floor_id,
                "astral": astral_floor_id, "mythic_astral": mythic_astral_floor_id,
                "giant": giant_fortress_floor_id, "mine": mine_floor_id,
                "magitek": magitek_floor_id,
            }.get(kind)
            if parent is None and kind not in PROF_DUNGEON_PREFIXES:
                return False
            parent_id = (parent(floor) if parent else
                         profession_dungeon_room_id(kind, floor))
            if not self.ensure_runtime_room(parent_id):
                return False
            created, spawns = create_world_secret_rooms_v1190(
                kind, floor, parent_id, ROOMS, TREASURE_CHESTS,
                CHEST_COLLECTION_CATALOG, NPCS, MOB_SPAWNS, MOB_TEMPLATES)
            if not created:
                return False
            for spawn_room, template_id in spawns:
                self._register_runtime_spawn(spawn_room, template_id)
            _ROOM_THREAT_CACHE.pop(created, None)
            return room_id in ROOMS
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

        floor = uoss_deep_dungeon_floor_number_v11331(room_id)
        if floor is not None:
            created_room, spawns = (
                create_infinite_uoss_deep_dungeon_floor_definition_v11331(
                    floor
                )
            )
        else:
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
        _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (created_room, "procedural_dynamic"))
        _catalog_mut.catalog_assign(True, 'ROOMS', ROOMS, (created_room, "generated_on_demand"))
        from systems.underground_cities_v12812 import attach_city_v12812
        attach_city_v12812(created_room, ROOMS)
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

    def refresh(self, force=False):
        """Refresh expirations/respawns with one mob pass.

        v0.71.5: historically this method made four independent full scans of
        ``self.mobs`` and was called from several hot combat paths.  The result
        is now coalesced for 250 ms and expiration + respawn + live room counts
        are handled in one pass.  Callers that need the scheduled world tick
        immediately (wander_step) use ``force=True``.
        """
        now = time.time()
        if not force and (now - self._last_refresh_at) < self._refresh_min_interval:
            return self._last_live_counts

        expired_keys = []
        live_counts = {}
        live_by_room = {}
        for mob_key, mob in self.mobs.items():
            # Summons never outlive their summoner or leave a stale fight running.
            parent_key = getattr(mob, "monster_ai_parent_v1160", None)
            if parent_key:
                parent = self.mobs.get(parent_key)
                expired_add = now >= float(getattr(mob, "v016_expires_at", 0.0) or 0.0) > 0.0
                if expired_add or not parent or not parent.alive or not parent.engaged_by:
                    mob.alive = False
                    mob.engaged_by = None
                    mob.respawn_at = float("inf")
                    mob.v016_expires_at = now - 1
            expires = max(
                float(getattr(mob, "v016_expires_at", 0.0) or 0.0),
                float(getattr(mob, "v029_expires_at", 0.0) or 0.0),
                float(getattr(mob, "v0140_event_expires_at", 0.0) or 0.0),
            )
            if expires and expires <= now and not mob.engaged_by:
                expired_keys.append(mob_key)
                continue

            if not (getattr(mob, "v016_ephemeral", False) and not mob.alive):
                if not mob.alive and mob.respawn_at <= now:
                    current_template = MOB_TEMPLATES.get(mob.template_id, {})
                    source_template_id = elite_source_template_id_v11338(
                        mob.template_id, current_template
                    )
                    mob.template_id = self._elite_spawn_template_v11338(
                        source_template_id
                    )
                    v0190_apply_combat_template(MOB_TEMPLATES[mob.template_id])
                    mob.alive = True
                    mob.hp = MOB_TEMPLATES[mob.template_id]["max_hp"]
                    mob.engaged_by = None
                    mob.aoe_engaged_by = None
                    mob.combat_turn = 0
                    for field in (
                        "monster_ai_next_action_v1160", "monster_ai_empowered_until_v1160",
                        "monster_ai_guard_until_v1160", "monster_ai_summon_used_v1160",
                        "monster_ai_resurrect_used_v1160", "monster_ai_add_sequence_v1160",
                        "monster_ai_raised_once_v1160", "monster_ai_lifesteal_turn_v1160",
                    ):
                        if hasattr(mob, field):
                            delattr(mob, field)
                    mob.player_hits = 0
                    mob.phase_stage = 0
                    mob.engaged_at = 0.0
                    mob.adaptive_max_hp_v11330 = 0
                    mob.adaptive_hp_multiplier_v11330 = 1.0
                    mob.adaptive_reward_multiplier_v11330 = 1.0
                    mob.adaptive_party_size_v11330 = 1
                    mob.adaptive_party_dps_v11330 = 0.0
                    mob.adaptive_rank_v11330 = ""
                    # Respawn begins a fresh UOSS fight, not the prior summon phase.
                    mob.uoss_start_effects_done_v11176 = False
                    mob.uoss_last_summon_turn_v1144 = -1
                    mob.uoss_add_sequence_v1144 = 0
                    mob.uoss_summon_used_v1144 = False
                    mob.uoss_ability_announced_turn_v1145 = -1
                    mob.uoss_shin_zantetsuken_started_v11160 = 0
                    if mob.home_room_id:
                        mob.room_id = mob.home_room_id
                    mob.next_wander_at = now + random.uniform(
                        MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS
                    )

            if mob.alive:
                live_counts[mob.room_id] = live_counts.get(mob.room_id, 0) + 1
                live_by_room.setdefault(mob.room_id, []).append(mob)

        for mob_key in expired_keys:
            self.mobs.pop(mob_key, None)

        for corpse_key, corpse in tuple(self.corpses.items()):
            if corpse.expires_at <= now:
                self.corpses.pop(corpse_key, None)

        self._last_refresh_at = now
        self._last_live_counts = live_counts
        self._last_live_by_room = {room_id: tuple(rows) for room_id, rows in live_by_room.items()}
        return live_counts

    def wander_step(self, now=None):
        """Wykonuje pojedynczy bezpieczny tick ruchu zwykłych mobów."""
        now = time.time() if now is None else float(now)
        # v0.71.5: refresh already calculates per-room live counts, so wander no
        # longer performs a second full counting pass before its movement pass.
        # v1.11.22: zwykłe odświeżenie ma już cache i jest wywoływane
        # przez aktywność graczy. Wander nie wymusza pełnego skanu świata co
        # 5 sekund; pełny refresh wykona się tylko gdy cache jest nieaktualny.
        live_counts = dict(self.refresh())
        moves = []

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
        self._last_live_counts = live_counts
        if moves:
            by_room = {room_id: list(rows) for room_id, rows in self._last_live_by_room.items()}
            for mob, old_room, target in moves:
                old_rows = by_room.get(old_room, [])
                if mob in old_rows:
                    old_rows.remove(mob)
                if old_rows:
                    by_room[old_room] = old_rows
                else:
                    by_room.pop(old_room, None)
                by_room.setdefault(target, []).append(mob)
            self._last_live_by_room = {room_id: tuple(rows) for room_id, rows in by_room.items()}
        return moves

    def live_crypt_boss(self, room_id):
        for mob in self.room_mobs(room_id):
            if MOB_TEMPLATES[mob.template_id].get("crypt_boss"):
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
        for mob in self.room_mobs(room_id):
            if MOB_TEMPLATES[mob.template_id].get("astral_boss"):
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
        for mob in self.room_mobs(room_id):
            if MOB_TEMPLATES[mob.template_id].get("mythic_crypt_boss"):
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
        for mob in self.room_mobs(room_id):
            if MOB_TEMPLATES[mob.template_id].get("mythic_astral_boss"):
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
        for mob in self.room_mobs(room_id):
            if MOB_TEMPLATES[mob.template_id].get("giant_fortress_boss"):
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
                infinite_equipment_variant_for_drop(
                    roll_crypt_loot_item(
                        item_id, is_boss=is_crypt_boss
                    ),
                    template,
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
            class_item = infinite_equipment_variant_for_drop(
                random.choice(class_pool), template
            )
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

        stage = treasure_chest_economy_stage_v11314(room_id)
        payout_coins = max(
            int(V11314_TREASURE_CHEST_LEGACY_COINS[rarity]),
            int(round(
                economy_stage_anchor_v11314(stage)
                * V11314_TREASURE_CHEST_PAYOUT_MULTIPLIERS[rarity]
            )),
        )
        gold, silver = divmod(payout_coins, SILVER_PER_GOLD)
        return {
            "rarity":rarity,
            "items":items,
            "silver":silver,
            "gold":gold,
            "name":cfg["name"],
            "economy_stage":stage,
            "payout_coins":payout_coins,
        }

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
        # v0.71.7: refresh already builds a live-room index. Combat, look,
        # targeting and boss gates now read only the current room instead of
        # rescanning every mob in the world.
        self.refresh()
        return [
            mob for mob in self._last_live_by_room.get(room_id, ())
            if mob.alive and mob.room_id == room_id
        ]

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
# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.
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


# v0.49.0: aliasy komend są centralnie zdefiniowane w config/command_aliases.py.
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
