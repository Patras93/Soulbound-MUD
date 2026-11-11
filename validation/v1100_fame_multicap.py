# -*- coding: utf-8 -*-
"""Direct Fame Multi Cap assertions, including independence from level thresholds."""
from systems.milestone_cap_rewards_v2103 import fame_cap_awards_v2103

class DatabaseFake:
    def __init__(self, value): self.value=value
    def multi_cap_v23215(self, account):
        assert account==123
        return self.value
class ServerFake:
    def __init__(self, value): self.db=DatabaseFake(value)
class SessionFake:
    account_id=123
    def __init__(self, value): self.server=ServerFake(value)

def run_regression():
    checks=0
    for amount in (1, 40000, 80000, 248500, 1000000000):
        result=fame_cap_awards_v2103(SessionFake(amount))
        assert result=={key:amount for key in ('character','soul','stat','class_total')}
        checks+=4
    return checks

if __name__=='__main__':
    print('FAME 100% MULTI CAP:',run_regression(),'PASS')
