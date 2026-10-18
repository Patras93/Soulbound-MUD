# -*- coding: utf-8 -*-
"""Pure boss-phase companion coordination for v11.

Only benefits players facing authored v11 bosses. Never weakens existing
mercenary owner-equipment power, spell scaling or permanent save state.
"""


def companion_coordination_v1100(template, *, hired_count=0, is_summon=False):
    template = template or {}
    active = template.get('v1100_eternal_glory_boss') or template.get('v1100_vault_boss')
    if not active:
        return 1.0
    if is_summon:
        return 1.08
    if int(hired_count) > 1:
        return 1.12
    return 1.06


def run_regression():
    checks=0
    for template in ({}, {'boss':True}, {'v1100_eternal_glory_boss':True}, {'v1100_vault_boss':True}):
        for n in (0,1,2,3,14):
            for summoned in (False,True):
                value=companion_coordination_v1100(template,hired_count=n,is_summon=summoned)
                assert value>=1, 'never reduce 100% equipment-scaled mercenary damage'
                assert (value==1.0)==(not template.get('v1100_eternal_glory_boss') and not template.get('v1100_vault_boss'))
                checks+=2
    return checks

if __name__=='__main__':
    print('V11 COMPANION TACTICS',run_regression(),'PASS')
