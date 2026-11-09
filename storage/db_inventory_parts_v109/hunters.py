# -*- coding: utf-8 -*-
"""v109 wydzielone metody SQLite: hunters; AST bez zmian."""
from .dependencies import *

class HuntersV109Mixin:
    def hunter_state_v1225(self, account_id, tier):
        return self.conn.execute('SELECT * FROM hunter_contracts_v1225 WHERE account_id=? AND tier=?',(int(account_id),tier)).fetchone()

    def hunter_accept_v1225(self, account_id, tier, target_id, needed, reward_silver, now):
        account_id=int(account_id)
        self.conn.execute('SAVEPOINT hunter_accept_v1225')
        try:
            old=self.hunter_state_v1225(account_id,tier)
            if old and old['state'] in ('active','ready'):
                result='active'
            elif old and int(old['ready_after'])>int(now):
                result='cooldown'
            else:
                self.conn.execute("INSERT INTO hunter_contracts_v1225(account_id,tier,target_id,needed,progress,reward_silver,state,ready_after) VALUES(?,?,?,?,0,?,'active',0) ON CONFLICT(account_id,tier) DO UPDATE SET target_id=excluded.target_id, needed=excluded.needed,progress=0,reward_silver=excluded.reward_silver,state='active',ready_after=0",(account_id,tier,str(target_id),int(needed),int(reward_silver)))
                result='ok'
            self.conn.execute('RELEASE SAVEPOINT hunter_accept_v1225')
            self.conn.commit()
            return result
        except Exception:
            self.conn.execute('ROLLBACK TO SAVEPOINT hunter_accept_v1225')
            self.conn.execute('RELEASE SAVEPOINT hunter_accept_v1225')
            raise

    def hunter_kill_v1225(self, account_id, mob_template_id, template=None):
        """Credit genuine kills by category, including valid world variants."""
        from data.mobs import MOB_TEMPLATES
        template = template if template is not None else MOB_TEMPLATES.get(str(mob_template_id), {})
        template = template or {}
        key = str(mob_template_id)
        rank = str(template.get('rank', '')).casefold()
        is_boss = bool(rank in ('boss', 'world_boss', 'superboss') or any(template.get(flag) for flag in (
            'world_boss', 'mini_boss', 'crypt_boss', 'mythic_crypt_boss',
            'astral_boss', 'mythic_astral_boss', 'giant_fortress_boss',
            'uoss_unique_superboss_key', 'boss_mechanic', 'v020_mythic_world_boss', 'boss')))
        is_elite = bool(template.get('elite') or rank == 'elite' or key.endswith('_elite'))
        matched = {
            'zwykle': not is_boss and not is_elite and (key.startswith('goblin_') or key == 'goblin' or template.get('quest_target') == 'goblin'),
            'elitarne': is_elite,
            'boss': is_boss,
        }
        changed=[]
        for row in self.conn.execute("SELECT tier,progress,needed FROM hunter_contracts_v1225 WHERE account_id=? AND state='active'",(int(account_id),)).fetchall():
            if not matched.get(row['tier'], False):
                continue
            count=min(int(row['needed']),int(row['progress'])+1)
            self.conn.execute("UPDATE hunter_contracts_v1225 SET progress=?,state=? WHERE account_id=? AND tier=? AND state='active'",(count,'ready' if count >= int(row['needed']) else 'active',int(account_id),row['tier']))
            changed.append((row['tier'],count,int(row['needed'])))
        if changed:self.conn.commit()
        return changed

    def hunter_claim_v1225(self, account_id, tier, now, cooldown):
        """Mark bounty complete and deposit reward in same SQLite transaction."""
        master=int(self.master_account_for_character(account_id))
        self.conn.execute('SAVEPOINT hunter_claim_v1225')
        try:
            row=self.hunter_state_v1225(account_id,tier)
            if not row or row['state']!='ready':
                result=0
            else:
                reward=int(row['reward_silver'])
                self.conn.execute('INSERT OR IGNORE INTO bank_balances(account_id,silver,gold,mithril) VALUES(?,0,0,0)',(master,))
                balance=self.conn.execute('SELECT silver,gold,mithril FROM bank_balances WHERE account_id=?',(master,)).fetchone()
                from core.bootstrap_economy_professions import legacy_currency_to_coins,CURRENCY_SQLITE_SAFE_TOTAL
                total=legacy_currency_to_coins(*balance)
                if reward<=0 or total+reward>CURRENCY_SQLITE_SAFE_TOTAL:
                    result=-1
                else:
                    self.conn.execute('UPDATE bank_balances SET silver=?,gold=0,mithril=0 WHERE account_id=?',(total+reward,master))
                    self.conn.execute("UPDATE hunter_contracts_v1225 SET state='cooldown',ready_after=? WHERE account_id=? AND tier=? AND state='ready'",(int(now)+int(cooldown),int(account_id),tier))
                    result=reward
            if result>0:
                self.conn.execute('RELEASE SAVEPOINT hunter_claim_v1225')
                self.conn.commit()
            else:
                self.conn.execute('ROLLBACK TO SAVEPOINT hunter_claim_v1225')
                self.conn.execute('RELEASE SAVEPOINT hunter_claim_v1225')
            return result
        except Exception:
            self.conn.execute('ROLLBACK TO SAVEPOINT hunter_claim_v1225')
            self.conn.execute('RELEASE SAVEPOINT hunter_claim_v1225')
            raise
