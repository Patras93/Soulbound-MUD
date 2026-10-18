# -*- coding: utf-8 -*-
"""v11.00.11: help NAME must show skill documentation, never cast a skill."""
from __future__ import annotations
import asyncio
from types import SimpleNamespace
import server  # Install complete HELP and 22-class skill indexes.
from core.classes_skills import CLASS_SKILLS
from core.bootstrap_economy_professions import VERSION
from player.session_mixins.help_system import SessionHelpSystemMixin
from world.world_state import _FINAL_SKILL_HELP_EXACT_INDEX, _FINAL_SKILL_HELP_SEARCH_ROWS
from storage.db_shared import normalize_lookup_text

class _Probe(SessionHelpSystemMixin):
    def __init__(self):
        self.sent=[]
        self.lookups=[]
    def is_admin(self): return False
    async def send(self, value, *args, **kwargs): self.sent.append(str(value))
    async def show_skill_help(self, query):
        self.lookups.append(str(query))
        await self.send('HELP SKILL: ' + str(query))
        return True

class _DB:
    def knows_skill(self, account_id, skill_id): return False

class _Actual(SessionHelpSystemMixin):
    def __init__(self, klass):
        self.sent=[]
        self.klass=klass
        self.server=SimpleNamespace(db=_DB())
        self.account_id=1
    def is_admin(self): return False
    async def send(self, value, *args, **kwargs): self.sent.append(str(value))
    def skill_queue_type(self, skill): return 'normal'
    def skill_queue_type_label(self, kind): return 'ręczna'
    def skill_required_mastery(self, skill): return int(skill.get('unlock') or 1)
    def class_mastery_level(self, klass): return 1
    def active_class_names(self): return (self.klass,)
    def class_teacher(self, klass): return (None,None)

async def _help(text, session):
    await session.show_help(text)
    return session

def run_regression():
    checks=0
    def ck(condition, why):
        nonlocal checks
        checks+=1
        if not condition: raise AssertionError('HELP SKILLI v11.00.11: '+why)
    ck(VERSION in ('11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17',) and server.VERSION==VERSION, 'release version')
    ck(len(CLASS_SKILLS)==22, '22 class catalogues')
    ck(len(_FINAL_SKILL_HELP_SEARCH_ROWS)==5461, 'global matching index complete')
    ck(sum(len(v) for v in CLASS_SKILLS.values())==5461, 'all skills retained')
    for klass, skills in CLASS_SKILLS.items():
        ck(bool(skills), 'class skills '+klass)
        # Real dispatch without the extra "skill" keyword, plus accented
        # and accent-free variants; no action/cast can be invoked.
        for skill in (skills[0], skills[len(skills)//2], skills[-1]):
            name=skill['name']
            sid=skill['id']
            ck(bool(_FINAL_SKILL_HELP_EXACT_INDEX.get(normalize_lookup_text(name))), 'index name '+sid)
            for query in (name, normalize_lookup_text(name), sid, 'skill '+name):
                sess=asyncio.run(_help(query, _Probe()))
                ck(len(sess.lookups)==1 and normalize_lookup_text(sess.lookups[0])==normalize_lookup_text(query), 'help dispatch '+query+' / '+str(sess.sent[:3])+' / '+str(sess.lookups))
                ck(sess.sent[0].startswith('HELP SKILL:'), 'help result '+query)
        # Check one real, complete help page, including unlearned skills.
        sk=skills[0]
        sess=asyncio.run(_help(sk['name'], _Actual(klass)))
        ck(sess.sent and sess.sent[0]=='HELP SKILL: '+sk['name']+'.', 'real help name '+klass)
        ck(any('Klasa: '+klass in t for t in sess.sent), 'real help class '+klass)
        ck(any(t.startswith('Status:') for t in sess.sent), 'real help status '+klass)
    # Historical command aliases for renamed skills must continue to open help.
    sample_aliases=0
    for klass, skills in CLASS_SKILLS.items():
        sample=next((sk for sk in skills if sk.get('pre_v1110_skill_name')),None)
        if sample:
            old=sample['pre_v1110_skill_name']
            sess=asyncio.run(_help(old,_Probe()))
            ck(len(sess.lookups)==1 and normalize_lookup_text(sess.lookups[0])==normalize_lookup_text(old), 'old skill alias '+klass)
            sample_aliases+=1
    ck(sample_aliases==22,'legacy alias samples for all classes')
    # Existing docs, commands, unknown names remain help-only.
    for topic in ('', 'kupiectwo','klasy','komendy','najemnicy','skill','tematy',
                  'proste komendy','niewymyslonytemat987654321'):
        sess=asyncio.run(_help(topic, _Probe()))
        ck(bool(sess.sent), 'nonempty help '+topic)
        ck(not sess.lookups, 'non-skill topic not redirected '+topic)
    for prefix in ('help ', 'pomoc '):
        skill=CLASS_SKILLS['Paladyn'][0]
        sess=asyncio.run(_help(prefix+skill['name'],_Probe()))
        ck(len(sess.lookups)==1 and normalize_lookup_text(sess.lookups[0])==normalize_lookup_text(prefix+skill['name']), 'prefixed spell '+prefix)
    print(f'HELP SKILLI v11.00.11: {checks} checks PASS; 22 klasy; nowe nazwy, stare aliasy i ID; prawdziwy opis skilla')
    return checks

if __name__=='__main__': run_regression()
