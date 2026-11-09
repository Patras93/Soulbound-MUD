# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: mercenaries_expeditions."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class MercenariesExpeditionsV109Mixin:
    def mercenary_memory_save_v1260(self, account_id, role, species, values):
        import json
        with self.conn:
            self.conn.execute('INSERT INTO mercenary_memory_v1260('
                'account_id,role,species,attempts_json,success_json) VALUES(?,?,?,?,?) '
                'ON CONFLICT(account_id,role,species) DO UPDATE SET '
                'attempts_json=excluded.attempts_json,success_json=excluded.success_json',
                (int(account_id),str(role),str(species)[:160],
                 json.dumps(values['attempts']),json.dumps(values['success'])))

    def grand_expedition_start_v1260(self, account_id):
        row=self.conn.execute('SELECT cycle,completed FROM grand_expeditions_v1260 WHERE account_id=?',
                              (int(account_id),)).fetchone()
        if row and not row['completed']:
            return False
        cycle = int(row['cycle'])+1 if row else 1
        with self.conn:
            self.conn.execute('INSERT INTO grand_expeditions_v1260(account_id,cycle,stage,completed) '
                'VALUES(?,?,0,0) ON CONFLICT(account_id) DO UPDATE SET '
                'cycle=excluded.cycle,stage=0,completed=0',(int(account_id),cycle))
        return True

    def grand_expedition_state_v1260(self, account_id):
        row=self.conn.execute('SELECT cycle,stage,completed FROM grand_expeditions_v1260 '
                              'WHERE account_id=?',(int(account_id),)).fetchone()
        return dict(row) if row else None

    def grand_expedition_claim_v1260(self, account_id):
        with self.conn:
            row=self.conn.execute('SELECT cycle FROM grand_expeditions_v1260 '
                'WHERE account_id=? AND stage=4 AND completed=0',(int(account_id),)).fetchone()
            if not row:
                return None
            self.conn.execute('UPDATE grand_expeditions_v1260 SET completed=1 '
                              'WHERE account_id=?',(int(account_id),))
        return int(row['cycle'])
