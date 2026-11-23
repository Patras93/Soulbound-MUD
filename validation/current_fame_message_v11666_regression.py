# -*- coding: utf-8 -*-
"""v116.00.66: Fame deferred payout must send notification without TypeError.

Verify live no-CAP and legacy fixture CAP branches with isolated in-memory DB.
"""
import asyncio
import time
from validation.v2103_fame_exploration_quest_currency import _MockSession
from systems.fame_v1702 import ensure_schema, pay_due_fame
from systems.milestone_cap_rewards_v2103 import fame_cap_awards_v2103


def run():
    checks=0
    for active in (False, True):
        s=_MockSession()
        s.server.db._uncapped_awards_v11664=active
        conn=s.server.db.conn
        ensure_schema(conn)
        conn.execute('''INSERT INTO fame_pending_v1703
            (account_id,region,boss_id,boss_name,reward_xp,due_at)
            VALUES(?,?,?,?,?,?)''',
            (s.account_id,'Test','boss_66','Boss regresyjny',1234,time.time()-1))
        conn.commit()
        award=fame_cap_awards_v2103(s)
        assert asyncio.run(pay_due_fame(s)) == 1
        checks+=1
        message=[m for m in s.messages if 'FAME —' in m][-1]
        assert 'Boss regresyjny, ZALICZONE' in message
        assert f'postać +{award["character"]}' in message
        assert f'Dusza +{award["soul"]}' in message
        checks+=1
        if active:
            assert 'Bez CAP i EXP Banku.' in message and '1 Fame = 10%' not in message
        else:
            assert '1 Fame = 10% bieżącego Multi Cap' in message and 'Bez CAP i EXP Banku.' not in message
        checks+=1
        assert conn.execute('SELECT delivered FROM fame_pending_v1703').fetchone()[0]==1
        assert asyncio.run(pay_due_fame(s))==0
        assert len(s.received)==4 and s.server.db.saved==1
        checks+=1
        conn.close()
    print(f'FAME PAYOUT MESSAGE v116.00.66: {checks}/{checks} PASS')
    return checks

if __name__=='__main__':run()
