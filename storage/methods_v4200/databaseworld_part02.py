# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
def record_fishing_global_v022(self, fish_id, item_id, holder_name, length_mm, weight_g, account_id=None):
    from world.runtime_progression import v022_fish_rarity_score, v022_fish_rarity_text
    fish_id=base_fish_species_id(fish_id); item_id=str(item_id or fish_id); holder_name=str(holder_name or "Nieznany")
    length_mm=max(0,int(length_mm or 0)); weight_g=max(0,int(weight_g or 0))
    row=self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(fish_id,)).fetchone()
    old_l=int(row["best_length_mm"] or 0) if row else 0; old_w=int(row["best_weight_g"] or 0) if row else 0
    new_l=length_mm>old_l; new_w=weight_g>old_w
    best_l=max(old_l,length_mm); best_w=max(old_w,weight_g)
    lholder=holder_name if new_l else (str(row["length_holder"] or "") if row else "")
    wholder=holder_name if new_w else (str(row["weight_holder"] or "") if row else "")
    self.conn.execute("""INSERT INTO fish_global_records_v022(fish_id,best_length_mm,length_holder,best_weight_g,weight_holder,updated_at) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(fish_id) DO UPDATE SET best_length_mm=excluded.best_length_mm,length_holder=excluded.length_holder,best_weight_g=excluded.best_weight_g,weight_holder=excluded.weight_holder,updated_at=CURRENT_TIMESTAMP""",
        (fish_id,best_l,lholder,best_w,wholder))
    score=v022_fish_rarity_score(item_id); rare=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()
    old_score=int(rare["rarity_score"] or 0) if rare else 0; old_rare_weight=int(rare["weight_g"] or 0) if rare else 0
    new_rare=score>old_score or (score==old_score and weight_g>old_rare_weight)
    if new_rare:
        self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES('global',?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
            (score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
    new_personal_rare=False
    if account_id is not None:
        pkey=f"account:{int(account_id)}"; personal=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(pkey,)).fetchone()
        pscore=int(personal["rarity_score"] or 0) if personal else 0; pweight=int(personal["weight_g"] or 0) if personal else 0
        new_personal_rare=score>pscore or (score==pscore and weight_g>pweight)
        if new_personal_rare:
            self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
                (pkey,score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
    self.conn.commit(); return {"new_global_length":new_l,"new_global_weight":new_w,"new_global_rarest":new_rare,"new_personal_rarest":new_personal_rare}


def add_world_project_contribution_v022(self, project_id, account_id, category, amount, points):
    from world.runtime_progression import V022_WORLD_PROJECTS
    spec=V022_WORLD_PROJECTS[project_id]; state=self.world_project_state_v022(project_id); progress=dict(state["progress"]); category=str(category); amount=max(0,int(amount)); points=max(0,int(points))
    need=int(spec["requirements"].get(category,0)); old=int(progress.get(category,0) or 0); accepted=min(amount,max(0,need-old))
    if accepted<=0: return {"accepted":0,"completed":state["completed"],"newly_completed":False,"progress":progress}
    progress[category]=old+accepted
    completed=all(int(progress.get(k,0) or 0)>=int(v) for k,v in spec["requirements"].items())
    newly=completed and not state["completed"]
    self.conn.execute("UPDATE world_projects_v022 SET progress_json=?,completed=?,completed_at=CASE WHEN ?=1 AND completed=0 THEN CURRENT_TIMESTAMP ELSE completed_at END WHERE project_id=?",(json.dumps(progress,ensure_ascii=False,separators=(",",":")),1 if completed else 0,1 if completed else 0,project_id))
    cur=self.world_project_contribution_v022(project_id,account_id); resources=dict(cur["resources"]); coins=int(cur["coins"]);
    if category=="coins": coins+=accepted
    else: resources[category]=int(resources.get(category,0) or 0)+accepted
    self.conn.execute("""INSERT INTO world_project_contributions_v022(project_id,account_id,points,resources_json,coins,reward_claimed,updated_at) VALUES(?,?,?,?,?,0,CURRENT_TIMESTAMP)
        ON CONFLICT(project_id,account_id) DO UPDATE SET points=world_project_contributions_v022.points+excluded.points,resources_json=excluded.resources_json,coins=excluded.coins,updated_at=CURRENT_TIMESTAMP""",
        (project_id,account_id,points,json.dumps(resources,ensure_ascii=False,separators=(",",":")),coins))
    self.conn.commit(); return {"accepted":accepted,"completed":completed,"newly_completed":newly,"progress":progress}


def postal_delivery_state_v0522(self, account_id):
    row = self.conn.execute(
        "SELECT active_json,completed_count,abandoned_count FROM postal_delivery_state_v0522 WHERE account_id=?",
        (int(account_id),),
    ).fetchone()
    if not row:
        return {"active": {}, "completed_count": 0, "abandoned_count": 0}
    try:
        active = json.loads(row["active_json"] or "{}")
    except Exception:
        active = {}
    return {
        "active": active if isinstance(active, dict) else {},
        "completed_count": max(0, int(row["completed_count"] or 0)),
        "abandoned_count": max(0, int(row["abandoned_count"] or 0)),
    }


def save_postal_delivery_state_v0522(
    self, account_id, *, active=None, completed_count=None, abandoned_count=None
):
    current = self.postal_delivery_state_v0522(account_id)
    active = current["active"] if active is None else dict(active or {})
    completed_count = current["completed_count"] if completed_count is None else max(0, int(completed_count))
    abandoned_count = current["abandoned_count"] if abandoned_count is None else max(0, int(abandoned_count))
    self.conn.execute(
        """
        INSERT INTO postal_delivery_state_v0522(account_id,active_json,completed_count,abandoned_count,updated_at)
        VALUES(?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(account_id) DO UPDATE SET
            active_json=excluded.active_json,
            completed_count=excluded.completed_count,
            abandoned_count=excluded.abandoned_count,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            int(account_id),
            json.dumps(active, ensure_ascii=False, separators=(",", ":")),
            completed_count,
            abandoned_count,
        ),
    )
    self.conn.commit()
    return {
        "active": active,
        "completed_count": completed_count,
        "abandoned_count": abandoned_count,
    }


def courier_guild_state_v0530(self, account_id):
    row = self.conn.execute(
        "SELECT reputation,total_earnings,longest_route,visited_cities_json "
        "FROM courier_guild_state_v0530 WHERE account_id=?",
        (int(account_id),),
    ).fetchone()
    if not row:
        return {
            "reputation": 1,
            "total_earnings": 0,
            "longest_route": 0,
            "visited_cities": [],
        }
    try:
        visited = json.loads(row["visited_cities_json"] or "[]")
    except Exception:
        visited = []
    if not isinstance(visited, list):
        visited = []
    return {
        "reputation": max(1, min(400, int(row["reputation"] or 1))),
        "total_earnings": max(0, int(row["total_earnings"] or 0)),
        "longest_route": max(0, int(row["longest_route"] or 0)),
        "visited_cities": sorted({str(x) for x in visited if str(x).strip()}),
    }


def save_courier_guild_state_v0530(
    self, account_id, *, reputation=None, total_earnings=None,
    longest_route=None, visited_cities=None
):
    current = self.courier_guild_state_v0530(account_id)
    reputation = current["reputation"] if reputation is None else max(1, min(400, int(reputation)))
    total_earnings = current["total_earnings"] if total_earnings is None else max(0, int(total_earnings))
    longest_route = current["longest_route"] if longest_route is None else max(0, int(longest_route))
    visited_cities = current["visited_cities"] if visited_cities is None else sorted({str(x) for x in visited_cities if str(x).strip()})
    self.conn.execute(
        """
        INSERT INTO courier_guild_state_v0530(
            account_id,reputation,total_earnings,longest_route,visited_cities_json,updated_at
        ) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(account_id) DO UPDATE SET
            reputation=excluded.reputation,
            total_earnings=excluded.total_earnings,
            longest_route=excluded.longest_route,
            visited_cities_json=excluded.visited_cities_json,
            updated_at=CURRENT_TIMESTAMP
        """,
        (
            int(account_id), reputation, total_earnings, longest_route,
            json.dumps(visited_cities, ensure_ascii=False, separators=(",", ":")),
        ),
    )
    self.conn.commit()
    return {
        "reputation": reputation,
        "total_earnings": total_earnings,
        "longest_route": longest_route,
        "visited_cities": visited_cities,
    }


def add_city_reputation_v0710(self, account_id, city_name, amount=1):
    city_name = str(city_name or "").strip()
    amount = int(amount or 0)
    if not city_name or amount == 0:
        return self.city_reputation_v0710(account_id, city_name) if city_name else 1
    old = self.city_reputation_v0710(account_id, city_name)
    new = max(1, min(400, old + amount))
    self.conn.execute(
        """
        INSERT INTO city_reputation_v0710(account_id,city_name,reputation,updated_at)
        VALUES(?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(account_id,city_name) DO UPDATE SET
            reputation=excluded.reputation,updated_at=CURRENT_TIMESTAMP
        """,
        (int(account_id), city_name, new),
    )
    self.conn.commit()
    return new

