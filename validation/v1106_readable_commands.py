# -*- coding: utf-8 -*-
"""Readable player-facing commands must use old, tested transaction paths."""
import asyncio
from types import SimpleNamespace
import server  # installs base NPC and quest registries needed by the empire mixin
from player.session_mixins.command_registry import (
    SessionCommandRegistryMixin, resolve_session_command, COMMAND_REGISTRY,
)
from player.session_mixins.profesje6 import SessionProfesje6Mixin
from player.session_mixins.living_empire_v7000 import SessionLivingEmpireV7000Mixin
from systems.new_professions import PROFESSIONS, BASE_ACTIONS


class _S(SessionCommandRegistryMixin, SessionLivingEmpireV7000Mixin, SessionProfesje6Mixin):
    def __init__(self):
        self.calls=[]
        self.server=SimpleNamespace(report_runtime_error=lambda *a, **k: None)
    async def profesje6_command(self, args):
        self.calls.append(('profesje6',args))
    async def imperium7_command(self, args):
        self.calls.append(('imperium7',args))


def run_regression():
    checks=0
    def ck(value, msg):
        nonlocal checks
        checks+=1
        if not value:raise AssertionError('READABLE COMMANDS v11.00.6: '+str(msg))

    # Legacy commands retain their original handlers. `praca` and bare
    # `profesje` MUST NOT be stolen from existing players.
    for token, args, expected in (
        ('profesje','', 'professions'), ('praca','', 'tasks'),
        ('imperium','status', 'imperium'),
        ('profesje6','kup Kupiectwo','profesje6'),
        ('imperium7','karawana lista','imperium7'),
        ('profesje','kup Kupiectwo','profesje6'),
        ('profesje','praca Kupiectwo pakuj','profesje6'),
        ('profesje','czynności Żeglarstwo','profesje6'),
        ('profesje','status Hodowla zwierząt','profesje6'),
        ('profesja','praca Kupiectwo pakuj','profesja'),
        ('pracuj','Kupiectwo pakuj','pracuj'),
        ('karawana','lista','karawana'),
        ('karawany','start rynek','karawana'),
        ('lowy','lista','lowy'), ('łowy','start','lowy'),
        ('wyprawa','start rafa','wyprawa'),
        ('rozbudowa','status','rozbudowa'),
        ('żeglarstwo','status','zeglarstwo'),
        ('łowiectwo','praca trop','lowiectwo'),
        ('inżynieria','montuj','inzynieria'),
        ('okrętownictwo','buduj','okretnictwo'),
        ('profesje','', 'professions'),
    ):
        ck(resolve_session_command(token,args)==expected, token+' '+args)

    async def routed(token,args, expected):
        s=_S()
        result=await s.dispatch_registered_command(resolve_session_command(token,args),args)
        ck(result is True, 'dispatch '+token)
        ck(s.calls == [expected], 'actual command '+token+' '+args+' '+repr(s.calls))

    async def run():
        for verb in ('lista','kup Kupiectwo','praca Kupiectwo pakuj','czynnosci Kupiectwo',
                     'zamowienie Kupiectwo', 'oddaj Kupiectwo','status Kupiectwo'):
            await routed('profesja',verb,('profesje6',verb))
            await routed('profesje',verb,('profesje6',verb))
        for verb in ('lista','start rynek','odbierz'):
            await routed('karawana',verb,('imperium7','karawana '+verb))
            await routed('lowy',verb,('imperium7','lowy '+verb))
            await routed('wyprawa',verb,('imperium7','wyprawa '+verb))
        await routed('rozbudowa','status',('imperium7','status'))
        await routed('pracuj','Kupiectwo pakuj 25',('profesje6','praca Kupiectwo pakuj 25'))
        for command, profession in (
            ('lowiectwo','Łowiectwo'),('rolnictwo','Rolnictwo'),
            ('hodowla','Hodowla zwierząt'),('okretnictwo','Okrętownictwo'),
            ('murarstwo','Murarstwo'),('inzynieria','Inżynieria'),
            ('kupiectwo','Kupiectwo'),('zeglarstwo','Żeglarstwo'),
        ):
            ck(profession in PROFESSIONS, 'missing profession '+profession)
            await routed(command,'',('profesje6','status '+profession))
            await routed(command,'kup',('profesje6','kup '+profession))
            await routed(command,'czynnosci',('profesje6','czynnosci '+profession))
            await routed(command,'zamowienie',('profesje6','zamowienie '+profession))
            await routed(command,'oddaj',('profesje6','oddaj '+profession))
            act=next(a.code for a in BASE_ACTIONS if a.prof==profession)
            await routed(command,act,('profesje6','praca '+profession+' '+act))
            await routed(command,'praca '+act+' 25',('profesje6','praca '+profession+' '+act+' 25'))
    asyncio.run(run())
    print(f'PROSTE KOMENDY v11.00.6: {checks} checks PASS')
    return checks

if __name__=='__main__':run_regression()
