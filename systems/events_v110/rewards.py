# -*- coding: utf-8 -*-
"""Jedna nagroda na konto i rotację, transakcyjna i bez dostępu do EQ."""

def reward_id(slug):return 'v11000_event_'+slug+'_seal'

def plan_rewards(slot,slug,participant_ids):
    # Deterministic bounded plan; excludes malformed/duplicate accounts.
    ids=sorted({int(x) for x in participant_ids if type(x) is int and 0<x<2**63})
    return [(slot,aid,reward_id(slug)) for aid in ids]
