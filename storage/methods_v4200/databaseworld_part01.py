# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def unlock_crypt_checkpoint(self, account_id, floor):
    floor = int(floor)
    if not _dbw_is_crypt_boss_floor_lazy(floor):
        return self.crypt_checkpoint(account_id)

    current = self.crypt_checkpoint(account_id)
    new_value = max(current, floor)
    if new_value != current:
        self.conn.execute(
            "UPDATE characters SET crypt_checkpoint=? "
            "WHERE account_id=?",
            (new_value, account_id),
        )
        self.conn.commit()
    return new_value


def unlock_astral_checkpoint(self, account_id, floor):
    floor = int(floor)
    if not _dbw_is_astral_boss_floor_lazy(floor):
        return self.astral_checkpoint(account_id)

    current = self.astral_checkpoint(account_id)
    new_value = max(current, floor)
    if new_value != current:
        self.conn.execute(
            """
            INSERT INTO astral_progress(account_id,checkpoint)
            VALUES(?,?)
            ON CONFLICT(account_id)
            DO UPDATE SET checkpoint=excluded.checkpoint
            """,
            (account_id, new_value),
        )
        self.conn.commit()
    return new_value


def boss_floor_cleared(self, account_id, dungeon_kind, floor):
    dungeon_kind = str(dungeon_kind or "").strip().lower()
    floor = max(1, int(floor))
    # Zgodność starych save'ów: checkpoint Krypty/Wieży oznacza, że wszystkie
    # wcześniejsze bossy co 10 zostały już kiedyś pokonane.
    if dungeon_kind == "crypt" and floor <= self.crypt_checkpoint(account_id):
        return True
    if dungeon_kind == "astral" and floor <= self.astral_checkpoint(account_id):
        return True
    row = self.conn.execute(
        "SELECT 1 FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=? AND floor=?",
        (account_id, dungeon_kind, floor),
    ).fetchone()
    return bool(row)


def mine_progress(self, account_id):
    self.ensure_mine_progress(account_id)
    row = self.conn.execute(
        """
        SELECT max_floor_unlocked,wall_hits,wall_required_hits
        FROM mine_progress
        WHERE account_id=?
        """,
        (account_id,),
    ).fetchone()
    highest = max(
        MINE_MIN_FLOOR,
        int(row["max_floor_unlocked"]),
    )
    hits = max(0, int(row["wall_hits"]))
    required_hits = max(0, int(row["wall_required_hits"]))

    # Stare zapisy nie miały losowego progu. Losujemy go raz
    # dla aktualnej ściany i zapisujemy, aby restart niczego nie zmieniał.
    if required_hits <= hits:
        required_hits = roll_mine_wall_hits_required(highest, hits)
        self.conn.execute(
            "UPDATE mine_progress SET wall_required_hits=? WHERE account_id=?",
            (required_hits, account_id),
        )
        self.conn.commit()

    return {
        "max_floor_unlocked": highest,
        "wall_hits": hits,
        "wall_required_hits": required_hits,
    }


def add_mine_wall_hit(self, account_id, floor):
    floor = int(floor)
    progress = self.mine_progress(account_id)
    highest = progress["max_floor_unlocked"]
    hits = progress["wall_hits"]
    required_hits = progress["wall_required_hits"]

    if floor != highest:
        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "wall_required_hits": required_hits,
            "unlocked_floor": None,
        }

    hits += 1
    unlocked_floor = None
    if hits >= required_hits:
        highest = highest + 1
        hits = 0
        unlocked_floor = highest
        required_hits = roll_mine_wall_hits_required(highest, 0)

    self.conn.execute(
        """
        UPDATE mine_progress
        SET max_floor_unlocked=?, wall_hits=?, wall_required_hits=?
        WHERE account_id=?
        """,
        (highest, hits, required_hits, account_id),
    )
    self.conn.commit()
    return {
        "max_floor_unlocked": highest,
        "wall_hits": hits,
        "wall_required_hits": required_hits,
        "unlocked_floor": unlocked_floor,
    }


def mine_tunnel_hit_v1251(self, account_id, floor, x, y, direction):
    """One real mining action advances one persistent wall; never deletes old tunnels."""
    from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS, mine_tunnel_room_id
    account_id, floor, x, y = map(int, (account_id, floor, x, y))
    if direction not in HORIZONTAL_MINE_DIRECTIONS:
        raise ValueError('invalid horizontal mine direction')
    if floor < MINE_MIN_FLOOR or not self.mine_tunnel_exists_v1251(account_id, floor, x, y):
        raise ValueError('mine tunnel origin not available')
    dx, dy = HORIZONTAL_MINE_DIRECTIONS[direction]
    nx, ny = x + dx, y + dy
    target = mine_tunnel_room_id(floor, account_id, nx, ny)
    if self.mine_tunnel_exists_v1251(account_id, floor, nx, ny):
        return {'hits': 0, 'required_hits': 0, 'opened': True, 'new': False, 'target': target}
    row = self.conn.execute(
        "SELECT hits,required_hits FROM mine_tunnel_walls_v1251 "
        "WHERE account_id=? AND floor=? AND x=? AND y=? AND direction=?",
        (account_id, floor, x, y, direction),
    ).fetchone()
    hits = int(row['hits']) if row else 0
    required = int(row['required_hits']) if row else roll_mine_wall_hits_required(floor)
    hits += 1
    if hits >= required:
        self.conn.execute(
            "INSERT OR IGNORE INTO mine_tunnel_cells_v1251(account_id,floor,x,y) VALUES(?,?,?,?)",
            (account_id, floor, nx, ny),
        )
        self.conn.execute(
            "DELETE FROM mine_tunnel_walls_v1251 WHERE account_id=? AND floor=? AND x=? AND y=? AND direction=?",
            (account_id, floor, x, y, direction),
        )
        self.conn.commit()
        return {'hits': hits, 'required_hits': required, 'opened': True, 'new': True, 'target': target}
    self.conn.execute(
        "INSERT INTO mine_tunnel_walls_v1251 "
        "(account_id,floor,x,y,direction,hits,required_hits) VALUES(?,?,?,?,?,?,?) "
        "ON CONFLICT(account_id,floor,x,y,direction) DO UPDATE SET hits=excluded.hits, required_hits=excluded.required_hits",
        (account_id, floor, x, y, direction, hits, required),
    )
    self.conn.commit()
    return {'hits': hits, 'required_hits': required, 'opened': False, 'new': False, 'target': target}


def mine_discover_v1260(self, account_id, floor, x, y, name):
    """Exactly-once local + global discoveries, in one SQLite transaction."""
    account_id, floor, x, y = map(int, (account_id,floor,x,y))
    with self.conn:
        local = self.conn.execute(
            'INSERT OR IGNORE INTO mine_discoveries_v1260(account_id,floor,x,y) '
            'VALUES(?,?,?,?)', (account_id,floor,x,y)).rowcount > 0
        global_first = False
        if local:
            global_first = self.conn.execute(
                'INSERT OR IGNORE INTO mine_first_discoveries_v1260('
                'floor,x,y,account_id,actor_name) VALUES(?,?,?,?,?)',
                (floor,x,y,account_id,str(name or 'Górnik')[:120])).rowcount > 0
    return {'new':local,'global_first':global_first}


def mercenary_memory_read_v1260(self, account_id, role, species):
    import json
    row = self.conn.execute(
        'SELECT attempts_json,success_json FROM mercenary_memory_v1260 '
        'WHERE account_id=? AND role=? AND species=?',
        (int(account_id),str(role),str(species)[:160])).fetchone()
    if not row:
        return None
    try:
        attempts = json.loads(row['attempts_json']); success = json.loads(row['success_json'])
        if len(attempts)==len(success)==3 and all(int(i)>=0 for i in attempts):
            return {'attempts':[int(i) for i in attempts],
                    'success':[float(i) for i in success]}
    except (ValueError,TypeError,IndexError):
        return None
    return None


def grand_expedition_visit_v1260(self, account_id, category):
    """Stages: city -> ocean -> dungeon -> mine; grant at most once per step."""
    kinds=('city','ocean','dungeon','mine')
    with self.conn:
        row=self.conn.execute('SELECT stage,completed FROM grand_expeditions_v1260 '
                              'WHERE account_id=?',(int(account_id),)).fetchone()
        if not row or row['completed'] or row['stage']>=len(kinds):
            return None
        stage=int(row['stage'])
        if str(category)!=kinds[stage]:
            return None
        self.conn.execute('UPDATE grand_expeditions_v1260 SET stage=? WHERE account_id=?',
                          (stage+1,int(account_id)))
    return stage+1


def mine_startup_status(self):
    """v1.25.0: informational startup snapshot; NEVER reset mining progress.

    The mine is persistent per character/account: unlocked depth, partial
    wall progress, and current room survive routine process restarts and
    Railway deployments as long as the configured SQLite DB is on a
    persistent volume.  Do not modify either table during bootstrap.
    """
    progress = self.conn.execute(
        """SELECT COUNT(*) AS accounts, COALESCE(MAX(max_floor_unlocked), 1) AS max_depth
           FROM mine_progress"""
    ).fetchone()
    characters = self.conn.execute(
        "SELECT COUNT(*) AS miners FROM characters WHERE room_id LIKE 'mine_floor_%'"
    ).fetchone()
    return {
        "accounts_with_mine_progress": int(progress["accounts"] or 0),
        "max_floor_unlocked": max(MINE_MIN_FLOOR, int(progress["max_depth"] or 1)),
        "characters_inside_mine": int(characters["miners"] or 0),
        "persistent": True,
    }


def mark_room_discovered_with_points_v2322(self, account_id, room_id, ep_points):
    """Atomically save a new room, its EP award, and lifetime totals.

    Previously discovered rooms are intentionally unchanged (no duplicate
    EP or re-award on login). Existing SQLite saves need no reset.
    """
    points = max(1, min(30, int(ep_points)))
    with self.conn:
        cursor = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rooms(account_id,room_id) VALUES(?,?)",
            (account_id, str(room_id)),
        )
        if cursor.rowcount <= 0:
            return False
        self.conn.execute(
            "INSERT INTO exploration_room_points_v2322(account_id,room_id,ep_points) "
            "VALUES(?,?,?)", (account_id, str(room_id), points),
        )
        for metric, value in (("rooms_discovered", 1), ("explorer_points", points)):
            self.conn.execute(
                "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
                "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
                "value=lifetime_statistics.value+excluded.value,updated_at=CURRENT_TIMESTAMP",
                (account_id, metric, value),
            )
    return True


def record_bestiary_kill(self, account_id, mob_template_id, kill_ms=None):
    mob_template_id = _dbw_canonical_bestiary_template_id_lazy(mob_template_id)
    previous = self.conn.execute(
        "SELECT kills,fastest_kill_ms FROM bestiary_stats "
        "WHERE account_id=? AND mob_template_id=?",
        (account_id, mob_template_id),
    ).fetchone()
    is_new = previous is None
    old_fastest = int(previous["fastest_kill_ms"]) if previous and previous["fastest_kill_ms"] is not None else None
    clean_ms = None
    if kill_ms is not None:
        try:
            clean_ms = max(1, int(kill_ms))
        except (TypeError, ValueError):
            clean_ms = None
    self.conn.execute(
        """
        INSERT INTO bestiary_stats(
            account_id,mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at
        ) VALUES(?,?,1,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
        ON CONFLICT(account_id,mob_template_id) DO UPDATE SET
            kills=bestiary_stats.kills+1,
            fastest_kill_ms=CASE
                WHEN excluded.fastest_kill_ms IS NULL THEN bestiary_stats.fastest_kill_ms
                WHEN bestiary_stats.fastest_kill_ms IS NULL THEN excluded.fastest_kill_ms
                WHEN excluded.fastest_kill_ms < bestiary_stats.fastest_kill_ms THEN excluded.fastest_kill_ms
                ELSE bestiary_stats.fastest_kill_ms
            END,
            last_killed_at=CURRENT_TIMESTAMP
        """,
        (account_id, mob_template_id, clean_ms),
    )
    self.conn.commit()
    row = self.bestiary_entry(account_id, mob_template_id)
    new_fastest = row["fastest_kill_ms"] if row else None
    is_record = (
        clean_ms is not None
        and new_fastest == clean_ms
        and (old_fastest is None or clean_ms < old_fastest)
    )
    return row, is_new, is_record


def record_boss_codex_kill(self, account_id, boss_id, grouped=False):
    boss_id = _dbw_canonical_bestiary_template_id_lazy(boss_id)
    if boss_id not in _dbw_boss_collection_catalog_lazy():
        return None
    solo_inc = 0 if grouped else 1
    group_inc = 1 if grouped else 0
    self.conn.execute(
        "INSERT INTO boss_codex_stats(account_id,boss_id,solo_kills,group_kills) VALUES(?,?,?,?) "
        "ON CONFLICT(account_id,boss_id) DO UPDATE SET "
        "solo_kills=boss_codex_stats.solo_kills+excluded.solo_kills, "
        "group_kills=boss_codex_stats.group_kills+excluded.group_kills",
        (account_id, boss_id, solo_inc, group_inc),
    )
    self.conn.commit()
    return self.boss_codex_stats(account_id, boss_id)


def promote_nemesis_v029(self, account_id, base_template_id, base_name, player_name, level, room_id):
    account_id = int(account_id)
    previous = self.nemesis_row_v029(account_id)
    same = bool(previous and int(previous["active"] or 0) and str(previous["base_template_id"]) == str(base_template_id))
    rank = min(10, (int(previous["rank"] or 1) + 1) if same else 1)
    kills = (int(previous["kills_player"] or 0) + 1) if same else 1
    defeats = int(previous["defeats"] or 0) if previous else 0
    stage = max(1, min(400, int(level or 1) + (rank - 1) * 8))
    name = dynamic_world_v029.nemesis_name(str(base_name), account_id, str(player_name), rank)
    self.conn.execute(
        "INSERT INTO nemesis_v029(account_id,base_template_id,nemesis_name,rank,level,room_id,kills_player,defeats,active,updated_at) "
        "VALUES(?,?,?,?,?,?,?,?,1,CURRENT_TIMESTAMP) "
        "ON CONFLICT(account_id) DO UPDATE SET base_template_id=excluded.base_template_id,nemesis_name=excluded.nemesis_name,"
        "rank=excluded.rank,level=excluded.level,room_id=excluded.room_id,kills_player=excluded.kills_player,defeats=excluded.defeats,"
        "active=1,updated_at=CURRENT_TIMESTAMP",
        (account_id, str(base_template_id), name, rank, stage, str(room_id), kills, defeats),
    )
    self.conn.commit()
    return self.nemesis_row_v029(account_id)


def add_ascension_xp_v021(self, account_id, track, amount):
    from world.runtime_progression import V021_ASCENSION_MAX_RANK, v0210_ascension_xp_to_next
    row=self.ascension_row_v021(account_id,track)
    rank=max(0,int(row["rank"] or 0)); xp=max(0,int(row["xp"] or 0)); gain=max(0,int(amount or 0))
    xp=min(V019_SAFE_INT,xp+gain); ups=0
    while rank < V021_ASCENSION_MAX_RANK:
        needed=v0210_ascension_xp_to_next(rank)
        if needed<=0 or xp<needed: break
        xp-=needed; rank+=1; ups+=1
    if rank>=V021_ASCENSION_MAX_RANK:
        rank=V021_ASCENSION_MAX_RANK; xp=0
    self.conn.execute(
        "UPDATE ascension_progress_v021 SET rank=?,xp=? WHERE account_id=? AND track=?",
        (rank,xp,account_id,str(track)),
    ); self.conn.commit()
    return {"track":str(track),"rank":rank,"xp":xp,"rank_ups":ups,"gain":gain,"next_xp":v0210_ascension_xp_to_next(rank)}


def mark_instance_floor_visited(self, account_id, instance_kind, floor):
    instance_kind = str(instance_kind or "")
    floor = max(1, int(floor))
    previous = self.conn.execute(
        "SELECT 1 FROM instance_map_progress WHERE account_id=? AND instance_kind=? AND floor=?",
        (account_id, instance_kind, floor),
    ).fetchone()
    self.conn.execute(
        "INSERT INTO instance_map_progress(account_id,instance_kind,floor) VALUES(?,?,?) "
        "ON CONFLICT(account_id,instance_kind,floor) DO UPDATE SET last_visited_at=CURRENT_TIMESTAMP",
        (account_id, instance_kind, floor),
    )
    self.conn.commit()
    return previous is None


def instance_checkpoint_floors(self, account_id, instance_kind):
    kind = str(instance_kind or "")
    result = {
        int(row["floor"])
        for row in self.conn.execute(
            "SELECT floor FROM instance_map_checkpoints WHERE account_id=? AND instance_kind=?",
            (account_id, kind),
        ).fetchall()
    }
    # Jednorazowo zaliczone bramki bossów są również checkpointami mapy.
    result.update(
        int(row["floor"])
        for row in self.conn.execute(
            "SELECT floor FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=?",
            (account_id, kind),
        ).fetchall()
    )
    # Zgodność starych save'ów, które miały tylko najwyższy portal.
    if kind == "crypt":
        highest = self.crypt_checkpoint(account_id)
        result.update(range(10, highest + 1, 10))
    elif kind == "astral":
        highest = self.astral_checkpoint(account_id)
        start = _dbw_astral_min_floor_lazy()
        if highest >= start:
            result.update(range(start, highest + 1, 10))
    return result


def record_activity_v0560(self, account_id, category, title, detail="", created_at=None):
    category = str(category or "system").strip().casefold()[:32] or "system"
    title = " ".join(str(title or "").split())[:240]
    detail = " ".join(str(detail or "").split())[:500]
    if not title:
        return False
    stamp = int(time.time() if created_at is None else created_at)
    self.conn.execute(
        "INSERT INTO activity_journal_v0560(account_id,category,title,detail,created_at) VALUES(?,?,?,?,?)",
        (int(account_id), category, title, detail, stamp),
    )
    # The journal is intentionally bounded; enough for recent history without
    # allowing an endlessly growing save.
    self.conn.execute(
        "DELETE FROM activity_journal_v0560 WHERE account_id=? AND id NOT IN ("
        "SELECT id FROM activity_journal_v0560 WHERE account_id=? ORDER BY created_at DESC,id DESC LIMIT 300)",
        (int(account_id), int(account_id)),
    )
    self.conn.commit()
    return True


def bounty_board_state(self, account_id):
    row = self.conn.execute(
        "SELECT offers_json,active_json,completed_count FROM bounty_boards WHERE account_id=?",
        (account_id,),
    ).fetchone()
    if not row:
        return {"offers": [], "active": {}, "completed_count": 0}
    try:
        offers = json.loads(row["offers_json"] or "[]")
    except Exception:
        offers = []
    try:
        active = json.loads(row["active_json"] or "{}")
    except Exception:
        active = {}
    if not isinstance(offers, list):
        offers = []
    if not isinstance(active, dict):
        active = {}
    return {
        "offers": offers,
        "active": active,
        "completed_count": max(0, int(row["completed_count"] or 0)),
    }


def save_bounty_board_state(self, account_id, offers=None, active=None, completed_count=None):
    current = self.bounty_board_state(account_id)
    if offers is None:
        offers = current["offers"]
    if active is None:
        active = current["active"]
    if completed_count is None:
        completed_count = current["completed_count"]
    self.conn.execute(
        """
        INSERT INTO bounty_boards(account_id,offers_json,active_json,completed_count,updated_at)
        VALUES(?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(account_id) DO UPDATE SET
            offers_json=excluded.offers_json,
            active_json=excluded.active_json,
            completed_count=excluded.completed_count,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            account_id,
            json.dumps(list(offers or []), ensure_ascii=False, separators=(",", ":")),
            json.dumps(dict(active or {}), ensure_ascii=False, separators=(",", ":")),
            max(0, int(completed_count or 0)),
        ),
    )
    self.conn.commit()


def save_dynamic_world_quest_v015(self, account_id, quest):
    quest = dict(quest or {})
    self.conn.execute(
        """
        INSERT INTO dynamic_world_quests_v015(
            account_id,quest_key,quest_type,target,label,needed,progress,
            reward_soul_xp,reward_gold,accepted_slot,completed,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(account_id) DO UPDATE SET
            quest_key=excluded.quest_key, quest_type=excluded.quest_type,
            target=excluded.target, label=excluded.label, needed=excluded.needed,
            progress=excluded.progress, reward_soul_xp=excluded.reward_soul_xp,
            reward_gold=excluded.reward_gold, accepted_slot=excluded.accepted_slot,
            completed=excluded.completed, updated_at=CURRENT_TIMESTAMP
        """,
        (account_id, str(quest.get("quest_key", "")), str(quest.get("quest_type", "")),
         str(quest.get("target", "any")), str(quest.get("label", "")),
         max(0,int(quest.get("needed",0))), max(0,int(quest.get("progress",0))),
         max(0,int(quest.get("reward_soul_xp",0))), max(0,int(quest.get("reward_gold",0))),
         int(quest.get("accepted_slot",0)), 1 if quest.get("completed") else 0)
    )
    self.conn.commit()


def record_fish_catch(self, account_id, fish_id, quantity, length_mm, weight_g, room_id):
    fish_id = base_fish_species_id(fish_id)
    quantity = max(1, int(quantity or 1))
    length_mm = max(0, int(length_mm or 0))
    weight_g = max(0, int(weight_g or 0))
    room_id = str(room_id or "")
    old = self.fish_journal_entry(account_id, fish_id)
    old_length = int(old["best_length_mm"] or 0) if old else 0
    old_weight = int(old["best_weight_g"] or 0) if old else 0
    result = {
        "new_species": old is None,
        "new_length_record": length_mm > old_length,
        "new_weight_record": weight_g > old_weight,
    }
    self.conn.execute(
        """
        INSERT INTO fish_journal(
            account_id,fish_id,caught_count,best_length_mm,best_weight_g,
            first_room_id,last_room_id,first_caught_at,last_caught_at
        ) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
        ON CONFLICT(account_id,fish_id) DO UPDATE SET
            caught_count=fish_journal.caught_count+excluded.caught_count,
            best_length_mm=MAX(fish_journal.best_length_mm,excluded.best_length_mm),
            best_weight_g=MAX(fish_journal.best_weight_g,excluded.best_weight_g),
            last_room_id=excluded.last_room_id,
            last_caught_at=CURRENT_TIMESTAMP
        """,
        (account_id, fish_id, quantity, length_mm, weight_g, room_id, room_id),
    )
    self.conn.commit()
    row = self.fish_journal_entry(account_id, fish_id)
    result.update({
        "caught_count": int(row["caught_count"] or 0),
        "best_length_mm": int(row["best_length_mm"] or 0),
        "best_weight_g": int(row["best_weight_g"] or 0),
    })
    return result

