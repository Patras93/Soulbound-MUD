# -*- coding: utf-8 -*-
"""Regression: a downed player can request help on public channels without gameplay bypass."""
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import ast
registry_tree=ast.parse((ROOT/'player/session_mixins/command_registry.py').read_text(encoding='utf-8'))
safe_node=next(node for node in registry_tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DOWNED_SAFE_COMMANDS' for t in node.targets))
DOWNED_SAFE_COMMANDS=ast.literal_eval(safe_node.value)
social_tree=ast.parse((ROOT/'player/session_mixins/social_base.py').read_text(encoding='utf-8'))
original=next(node for node in social_tree.body if isinstance(node,ast.ClassDef) and node.name=='SessionBaseSocialMixin')
methods=[node for node in original.body if isinstance(node,ast.AsyncFunctionDef) and node.name in ('channel_broadcast_v03050','show_channels_v03050')]
ns={}
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='SessionBaseSocialMixin',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[])),str(ROOT/'player/session_mixins/social_base.py'),'exec'),ns)
SessionBaseSocialMixin=ns['SessionBaseSocialMixin']

class Session(SessionBaseSocialMixin):
    def __init__(self, name, server, hp=0):
        self.server=server
        self.character=SimpleNamespace(name=name)
        self.current_hp=hp
        self.closed=False
        self.received=[]
    async def send(self, message, **kwargs):
        self.received.append((str(message),kwargs.get('history_category')))

async def check_chat():
    server=SimpleNamespace(sessions=[])
    dead=Session('Powalony', server, 0)
    live=Session('Ratownik', server, 100)
    server.sessions=[dead,live]
    await dead.channel_broadcast_v03050('gossip','Proszę o wskrzeszenie!')
    expected='[GOSSIP] Powalony: Proszę o wskrzeszenie!'
    assert dead.received[-1]==(expected,'chat')
    assert live.received[-1]==(expected,'chat')
    await dead.channel_broadcast_v03050('newbie','Potrzebna pomoc')
    assert live.received[-1]==('[NEWBIE] Powalony: Potrzebna pomoc','chat')
    await dead.show_channels_v03050()
    assert 'także po śmierci' in dead.received[-1][0]
    before=len(live.received)
    await dead.channel_broadcast_v03050('gossip','  ')
    assert len(live.received)==before and 'Użycie:' in dead.received[-1][0]
    return 6

def main():
    for name in ('gossip','newbie','channels'):
        assert name in DOWNED_SAFE_COMMANDS,name
    for name in ('trade','attack','north','dungeonexit'):
        assert name not in DOWNED_SAFE_COMMANDS,name
    assert asyncio.run(check_chat())==6
    print('DOWNED HELP CHANNELS: 13/13 PASS')
if __name__=='__main__':main()
