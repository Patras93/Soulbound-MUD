# -*- coding: utf-8 -*-
"""Ochrona historycznych ścieżek World Threat poza staging v106."""
from __future__ import annotations
from unittest.mock import patch
import os
import socket

def run():
    assert os.environ.get('SOULBOUND_V106_STAGING') != '1'
    # Direct invocation must also be safe while production listens on 4000.
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as test_sock:
        test_sock.bind(('127.0.0.1',0))
        selected=test_sock.getsockname()[1]
    os.environ['SOULBOUND_HOST']='127.0.0.1'
    os.environ['SOULBOUND_PORT']=str(selected)
    os.environ.pop('SOULBOUND_DB',None)
    import server
    from world.dynamic_content import MOB_TEMPLATES
    w=server.World()
    checks=0
    with patch.dict(os.environ, {'SOULBOUND_V106_STAGING':'0'}):
        # An old v105 region must still use its historical world threat path.
        older=[m for m in w.mobs.values() if str(m.template_id).startswith('v10500_')]
        assert older, 'brak prawdziwych potworów v105'
        for mob in older[:15]:
            tid=str(mob.template_id)
            assert mob.hp==MOB_TEMPLATES[tid]['max_hp'],tid
            checks+=1
    print(f'V106 NONSTAGING v105 WORLD: {checks} PASS',flush=True)
    return checks
if __name__=='__main__':run()
