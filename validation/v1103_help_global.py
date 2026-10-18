# -*- coding: utf-8 -*-
"""Global HELP / NPC-independent documentation regression, v11.00.3."""
from __future__ import annotations
import asyncio
import server  # bootstrap authored world before importing session mixins
from core.bootstrap_economy_professions import VERSION
from core.command_catalog import COMMAND_CATALOG
from player.session_mixins.help_system import SessionHelpSystemMixin
from player.session_mixins.command_registry import resolve_session_command
from systems.new_professions import PROFESSIONS, BASE_ACTIONS
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES


class _HelpSession(SessionHelpSystemMixin):
    def __init__(self):
        self.messages=[]
    def is_admin(self):
        return False
    async def send(self,text,*a,**kw):
        self.messages.append(str(text))
    async def show_skill_help(self, topic):
        return False


async def _help(topic):
    s=_HelpSession()
    await s.show_help(topic)
    return s.messages


def run_regression():
    checks=0
    def ck(condition, message):
        nonlocal checks
        checks+=1
        if not condition:
            raise AssertionError(f'HELP v11.00.3: {message}')
    ck(VERSION in ('11.00.3','11.00.4','11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12') and server.VERSION == VERSION, 'current version')
    for cmd in ('help', 'pomoc'):
        ck(resolve_session_command(cmd, 'kupiectwo') == 'help', f'{cmd} dispatch')
    ck(COMMAND_CATALOG.definition('help').handler=='show_help', 'registered command')
    for prof, (_,_,tool_name) in PROFESSIONS.items():
        topic=prof.lower()
        rows=asyncio.run(_help(topic))
        ck(rows[0].startswith('POMOC:'), f'{prof} header')
        ck(tool_name in '\n'.join(rows), f'{prof} tool')
        for act in BASE_ACTIONS:
            if act.prof==prof:
                ck(f'profesje6 praca {prof} {act.code}' in '\n'.join(rows), f'{prof}: {act.code}')
    rows=asyncio.run(_help('klasy'))
    ck('22 grywalne' in '\n'.join(rows), 'help klasy uses canonical topic, not multiclass')
    ck(rows[0] == 'POMOC: KLASY', 'help klasy canonical title')
    for text in ('KUPIECTWO','kupiectwo','kupiec','handel','kupi-ectwo'):
        rows=asyncio.run(_help(text))
        ck('Waga Kupiecka' in '\n'.join(rows), f'alias {text}')
    for q in ('hodowla zwierząt','hodowla zwierzat','hodowla_zwierzat','hodowla','żeglarstwo','zeglarstwo','karawany','karawana'):
        rows=asyncio.run(_help(q))
        ck(rows and rows[0].startswith('POMOC:'), f'alias {q}')
    rows=asyncio.run(_help(''))
    ck(any('POMOC — KATEGORIE' in x for x in rows), 'help index')
    rows=asyncio.run(_help('tematy'))
    ck(any('strona 1/' in x for x in rows), 'paginated topic list')
    ck(len(rows)<35, 'NVDA bounded index')
    rows=asyncio.run(_help('tematy 2'))
    ck(any('strona 2/' in x for x in rows), 'page two')
    rows=asyncio.run(_help('tematy wszystkie'))
    ck(len(rows)>100,'opt-in full index')
    rows=asyncio.run(_help('szukaj kupiectwo'))
    ck('kupiectwo' in '\n'.join(rows), 'search matches profession')
    rows=asyncio.run(_help('nieistniejace123'))
    ck('Nie ma tematu' in '\n'.join(rows), 'real unknown')
    rows=asyncio.run(_help('kupiectw'))
    ck('help kupiectwo' in '\n'.join(rows), 'typo suggests existing help')
    rows=asyncio.run(_help('admin_owner'))
    ck('Nieznany temat' in '\n'.join(rows), 'admin help private')
    rows=asyncio.run(_help('fame'))
    ck(rows[0].startswith('POMOC:'), 'old help retained')
    print(f'GLOBAL HELP v11.00.3: {checks} checks PASS')
    return checks

if __name__=='__main__':run_regression()
