# -*- coding: utf-8 -*-
"""Guild and clan persistence."""

import time

from network.protocol_gameplay_utils import (
    V0926_GUILD_DEFAULT_ROLES, V0927_GUILD_CONTRACTS, normalize_lookup_text,
    v0926_guild_bonus_percent,
)

class DatabaseGuildMixin:
    def clan_membership(self, account_id):
        # Wewnętrzna nazwa pozostaje dla zgodności z v0.9.25; UI mówi Gildia.
        return self.conn.execute(
            "SELECT c.id clan_id,c.name,c.level,c.treasury,m.rank,c.owner_account_id "
            "FROM player_clan_members m JOIN player_clans c ON c.id=m.clan_id WHERE m.account_id=?",
            (account_id,),
        ).fetchone()

    def guild_memberships_for_master_v0345(self, master_account_id):
        """Zwróć Gildie wszystkich postaci należących do jednego konta głównego.

        v0.34.5: profile postaci używają osobnych technicznych account_id, dlatego
        Gildia musi być rozpoznawana przez account_characters, a nie tylko bieżący
        profil postaci.
        """
        return self.conn.execute(
            """
            SELECT ac.slot, ac.character_account_id, ch.name AS character_name,
                   m.clan_id, m.rank, c.name AS clan_name
            FROM account_characters ac
            JOIN characters ch ON ch.account_id=ac.character_account_id
            JOIN player_clan_members m ON m.account_id=ac.character_account_id
            JOIN player_clans c ON c.id=m.clan_id
            WHERE ac.master_account_id=?
            ORDER BY ac.slot, ac.character_account_id
            """,
            (int(master_account_id),),
        ).fetchall()

    def ensure_character_guild_from_master_v0345(self, master_account_id, character_account_id):
        """Dopisz postać do Gildii konta jako zwykłego członka.

        Zasady bezpieczeństwa:
        - brak Gildii na koncie -> nic nie rób;
        - dokładnie jedna Gildia na pozostałych postaciach -> dopisz `member`;
        - różne Gildie na jednym starym koncie -> nie wybieraj losowo i nic nie zmieniaj.
        Ranga lidera/oficera nie jest kopiowana, żeby nie tworzyć kilku technicznych
        liderów tej samej Gildii.
        """
        master_account_id=int(master_account_id)
        character_account_id=int(character_account_id)
        current=self.clan_membership(character_account_id)
        memberships=[r for r in self.guild_memberships_for_master_v0345(master_account_id)
                     if int(r["character_account_id"]) != character_account_id]
        clan_ids=sorted({int(r["clan_id"]) for r in memberships})
        all_clan_ids=sorted(set(clan_ids + ([int(current["clan_id"])] if current else [])))
        if len(all_clan_ids) > 1:
            return {"status":"conflict","clan_ids":all_clan_ids}
        if current:
            return {"status":"already","clan_id":int(current["clan_id"]),"name":str(current["name"])}
        if not clan_ids:
            return {"status":"none"}
        if len(clan_ids) != 1:
            return {"status":"conflict","clan_ids":clan_ids}
        clan_id=clan_ids[0]
        clan=self.conn.execute("SELECT name FROM player_clans WHERE id=?",(clan_id,)).fetchone()
        if not clan:
            return {"status":"missing_clan","clan_id":clan_id}
        self.conn.execute(
            "INSERT OR IGNORE INTO player_clan_members(clan_id,account_id,rank) VALUES(?,?,'member')",
            (clan_id,character_account_id),
        )
        ch=self.character_for_account(character_account_id)
        ch_name=str(ch["name"]) if ch else f"account {character_account_id}"
        self.conn.execute(
            "INSERT INTO player_clan_log(clan_id,actor_account_id,message) VALUES(?,?,?)",
            (clan_id,character_account_id,f"{ch_name} automatycznie dołącza do Gildii jako postać tego samego konta."),
        )
        self.conn.commit()
        return {"status":"joined","clan_id":clan_id,"name":str(clan["name"]),"rank":"member"}

    def guild_bonus_percent_v0926(self, account_id):
        row=self.clan_membership(account_id)
        return v0926_guild_bonus_percent(int(row["level"])) if row else 0

    def ensure_guild_default_roles_v0926(self, clan_id):
        clan_id=int(clan_id)
        for key,data in V0926_GUILD_DEFAULT_ROLES.items():
            self.conn.execute(
                "INSERT OR IGNORE INTO player_clan_roles(clan_id,role_key,name,priority,withdraw_money,withdraw_items,invite,kick) VALUES(?,?,?,?,?,?,?,?)",
                (clan_id,key,data["name"],data["priority"],data["withdraw_money"],data["withdraw_items"],data["invite"],data["kick"]),
            )
        self.conn.commit()

    def guild_role_v0926(self, clan_id, role_key):
        if str(role_key)=="leader":
            return {"role_key":"leader","name":"Lider","priority":1000,"withdraw_money":1,"withdraw_items":1,"invite":1,"kick":1}
        self.ensure_guild_default_roles_v0926(clan_id)
        return self.conn.execute(
            "SELECT role_key,name,priority,withdraw_money,withdraw_items,invite,kick FROM player_clan_roles WHERE clan_id=? AND role_key=?",
            (int(clan_id),str(role_key)),
        ).fetchone()

    def guild_role_by_name_v0926(self, clan_id, query):
        self.ensure_guild_default_roles_v0926(clan_id)
        norm=normalize_lookup_text(query)
        rows=self.conn.execute(
            "SELECT role_key,name,priority,withdraw_money,withdraw_items,invite,kick FROM player_clan_roles WHERE clan_id=?",
            (int(clan_id),),
        ).fetchall()
        exact=[r for r in rows if normalize_lookup_text(r["name"])==norm or normalize_lookup_text(r["role_key"])==norm]
        if exact: return exact[0]
        partial=[r for r in rows if norm and (norm in normalize_lookup_text(r["name"]) or norm in normalize_lookup_text(r["role_key"]))]
        return partial[0] if len(partial)==1 else None

    def clan_log(self, clan_id, actor_account_id, message):
        self.conn.execute("INSERT INTO player_clan_log(clan_id,actor_account_id,message) VALUES(?,?,?)", (clan_id,actor_account_id,str(message)))
        self.conn.commit()

    def clan_metric_add(self, clan_id, metric, amount=1):
        self.conn.execute(
            "INSERT INTO player_clan_metrics(clan_id,metric,value) VALUES(?,?,?) ON CONFLICT(clan_id,metric) DO UPDATE SET value=value+excluded.value",
            (clan_id,metric,int(amount)),
        )
        self.conn.commit()

    def guild_hall_v0927(self, clan_id):
        clan_id=int(clan_id)
        self.conn.execute("INSERT OR IGNORE INTO player_guild_halls_v0927(clan_id) VALUES(?)",(clan_id,))
        self.conn.commit()
        return self.conn.execute("SELECT * FROM player_guild_halls_v0927 WHERE clan_id=?",(clan_id,)).fetchone()

    def guild_contract_row_v0927(self, clan_id, contract_id):
        self.conn.execute("INSERT OR IGNORE INTO player_guild_contracts_v0927(clan_id,contract_id) VALUES(?,?)",(int(clan_id),str(contract_id)))
        self.conn.commit()
        return self.conn.execute("SELECT * FROM player_guild_contracts_v0927 WHERE clan_id=? AND contract_id=?",(int(clan_id),str(contract_id))).fetchone()

    def guild_contract_add_v0927(self, clan_id, kind, amount=1):
        clan_id=int(clan_id); now=int(time.time()); changed=[]
        for contract_id,definition in V0927_GUILD_CONTRACTS.items():
            if definition["kind"]!=kind: continue
            row=self.guild_contract_row_v0927(clan_id,contract_id)
            if int(row["ready_at"] or 0)>now: continue
            need=int(definition["need"]); new=min(need,int(row["progress"] or 0)+int(amount))
            self.conn.execute("UPDATE player_guild_contracts_v0927 SET progress=? WHERE clan_id=? AND contract_id=?",(new,clan_id,contract_id))
            changed.append((contract_id,new,need))
        self.conn.commit(); return changed

    def guild_contract_complete_v0927(self, clan_id, contract_id):
        clan_id=int(clan_id); definition=V0927_GUILD_CONTRACTS[str(contract_id)]
        row=self.guild_contract_row_v0927(clan_id,contract_id)
        if int(row["progress"] or 0)<int(definition["need"]): return False
        ready=int(time.time())+int(definition["cooldown"]); reward=int(definition["reward"])
        self.conn.execute("UPDATE player_guild_contracts_v0927 SET progress=0,completed_count=completed_count+1,ready_at=? WHERE clan_id=? AND contract_id=?",(ready,clan_id,contract_id))
        self.conn.execute("UPDATE player_clans SET treasury=treasury+? WHERE id=?",(reward,clan_id))
        self.conn.commit(); return True
