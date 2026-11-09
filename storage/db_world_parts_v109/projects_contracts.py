# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: projects_contracts."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class ProjectsContractsV109Mixin:
    def world_project_state_v022(self, project_id):
        project_id=str(project_id); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        if not row:
            self.conn.execute("INSERT INTO world_projects_v022(project_id,progress_json,completed) VALUES(?,'{}',0)",(project_id,)); self.conn.commit(); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        try: progress=json.loads(row["progress_json"] or "{}")
        except Exception: progress={}
        return {"project_id":project_id,"progress":progress if isinstance(progress,dict) else {},"completed":bool(row["completed"]),"completed_at":row["completed_at"]}

    def world_project_contribution_v022(self, project_id, account_id):
        row=self.conn.execute("SELECT * FROM world_project_contributions_v022 WHERE project_id=? AND account_id=?",(project_id,account_id)).fetchone()
        if not row: return {"points":0,"coins":0,"resources":{},"reward_claimed":False}
        try: resources=json.loads(row["resources_json"] or "{}")
        except Exception: resources={}
        return {"points":int(row["points"] or 0),"coins":int(row["coins"] or 0),"resources":resources if isinstance(resources,dict) else {},"reward_claimed":bool(row["reward_claimed"])}

    def mark_world_project_reward_claimed_v022(self, project_id, account_id):
        cur=self.conn.execute("UPDATE world_project_contributions_v022 SET reward_claimed=1,updated_at=CURRENT_TIMESTAMP WHERE project_id=? AND account_id=? AND reward_claimed=0",(project_id,account_id)); self.conn.commit(); return cur.rowcount>0

    def legendary_contract_state_v022(self, account_id):
        row=self.conn.execute("SELECT * FROM legendary_contracts_v022 WHERE account_id=?",(account_id,)).fetchone()
        if not row: return {"offers":[],"active":{},"completed_count":0}
        try: offers=json.loads(row["offers_json"] or "[]")
        except Exception: offers=[]
        try: active=json.loads(row["active_json"] or "{}")
        except Exception: active={}
        return {"offers":offers if isinstance(offers,list) else [],"active":active if isinstance(active,dict) else {},"completed_count":int(row["completed_count"] or 0)}

    def save_legendary_contract_state_v022(self, account_id, offers=None, active=None, completed_count=None):
        cur=self.legendary_contract_state_v022(account_id); offers=cur["offers"] if offers is None else offers; active=cur["active"] if active is None else active; completed_count=cur["completed_count"] if completed_count is None else completed_count
        self.conn.execute("""INSERT INTO legendary_contracts_v022(account_id,offers_json,active_json,completed_count,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET offers_json=excluded.offers_json,active_json=excluded.active_json,completed_count=excluded.completed_count,updated_at=CURRENT_TIMESTAMP""",
            (account_id,json.dumps(list(offers or []),ensure_ascii=False,separators=(",",":")),json.dumps(dict(active or {}),ensure_ascii=False,separators=(",",":")),max(0,int(completed_count or 0))))
        self.conn.commit()
