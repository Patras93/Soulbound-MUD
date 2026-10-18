# -*- coding: utf-8 -*-
"""Global no-version commands and help-is-help semantics, v11.00.7."""
from __future__ import annotations
import asyncio
import server
from core.bootstrap_economy_professions import VERSION
from core.command_catalog import COMMAND_CATALOG
from player.session_mixins.command_registry import (COMMAND_REGISTRY,
    VERSIONLESS_COMMAND_ALIASES_V1107, resolve_session_command)
from player.session_mixins.help_system import SessionHelpSystemMixin
from systems.content_registry import HELP_TOPICS

class _Help(SessionHelpSystemMixin):
    def __init__(self):
        self.sent = []
        self.skill_queries = []
    def is_admin(self):
        return False
    async def send(self, message, *args, **kwargs):
        self.sent.append(str(message))
    async def show_skill_help(self, query):
        self.skill_queries.append(query)
        return True

async def _run_help(text):
    s = _Help()
    await s.show_help(text)
    return s

def run_regression():
    checks = 0
    def ck(ok, why):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError('GLOBALNE KOMENDY / HELP v11.00.7: ' + why)
    ck(VERSION == server.VERSION and VERSION in ('11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17',), 'consistent version')
    ck(not COMMAND_CATALOG.conflicts(), 'no catalog alias conflicts')
    for canonical, names in VERSIONLESS_COMMAND_ALIASES_V1107:
        ck(canonical in COMMAND_REGISTRY, 'existing handler ' + canonical)
        for alias in names:
            ck(resolve_session_command(alias) == canonical, 'alias ' + alias)
            result = asyncio.run(_run_help(alias))
            ck(bool(result.sent) and result.sent[0].startswith('POMOC:'),
               'command alias opens help ' + alias)
            ck(not result.skill_queries, 'alias never invokes skill help '+alias)
            # Preserve handler identity; no new expense, XP, or combat logic.
            ck(COMMAND_CATALOG.definition(alias).handler == COMMAND_REGISTRY[canonical][0],
               'same implementation ' + alias)
    for old in ('profesje6','ocean5','ocean4','handel4','lochy7','lochy50','era60','imperium7'):
        ck(resolve_session_command(old) == old, 'old command intact '+old)
    ck(resolve_session_command('targ') == 'trade', 'no stealing trade')
    ck(resolve_session_command('profesje') == 'professions', 'no stealing profession overview')
    ck(resolve_session_command('praca') == 'tasks', 'no stealing work tasks')
    for topic in ('','kupiectwo','proste komendy','globalne komendy','morza','flota',
                  'sekretylochu','era','zapomnianelochy','zawody','zadaniaklasowe',
                  'nawigacja','kariera','klasy','fame','tematy','niewymyslonatemat888'):
        result = asyncio.run(_run_help(topic))
        ck(bool(result.sent), 'help response '+topic)
        ck(not result.skill_queries, 'general help never requests a skill: '+topic)
        ck('Użycie: help skill' not in '\n'.join(result.sent), 'no skill use message '+topic)
    for token in ('unknownalias7889','niewymyslonatemat888'):
        result = asyncio.run(_run_help(token))
        ck('Nie ma tematu' in '\n'.join(result.sent), 'unknown is a help-not-found message')
    for token in ('sekretylochu','morza','flota','gildiaklasowa','kodekskolekcji',
                  'lowcy','egzaminklasowy','mistrzowiepracy'):
        s = asyncio.run(_run_help(token))
        ck(s.sent[0].startswith('POMOC:'), 'help page '+token)
    s = asyncio.run(_run_help('skill'))
    ck(s.sent[0] == 'POMOC: UMIEJĘTNOŚCI', 'skill overview not a command prompt')
    ck(not s.skill_queries, 'missing skill name does not dispatch')
    s = asyncio.run(_run_help('skill ognista kula'))
    ck(s.skill_queries == ['skill ognista kula'], 'explicit skill help only')
    for cmd in ('mistrzowieprofesji','sekretylochu','zadaniaklasowe','gildiaklasowa'):
        s = asyncio.run(_run_help(cmd))
        ck(len(s.sent) < 25, 'bounded NVDA output '+cmd)
    print(f'GLOBALNE KOMENDY / HELP v11.00.7: {checks} checks PASS')
    return checks

if __name__ == '__main__':
    run_regression()
