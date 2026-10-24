# -*- coding: utf-8 -*-
"""Release sync and split Telnet-banner regressions, no real game process."""
from pathlib import Path
import socket
import threading
import re
from validation.v8700_native_fresh_tcp import receive_login_banner


def run():
    root=Path(__file__).resolve().parents[1]
    from core.bootstrap_economy_professions import VERSION
    count=0
    def ck(flag, what):
        nonlocal count
        assert flag, what
        count+=1
    ck(VERSION == root.joinpath('VERSION').read_text(encoding='utf-8').strip(), 'VERSION / runtime')
    change=root.joinpath('CHANGELOG_PL.txt').read_text(encoding='utf-8')
    ck(change.startswith('Aktualna paczka: v'+VERSION+'\n'), 'CHANGELOG release identity')
    registry=root.joinpath('systems/content_registry.py').read_text(encoding='utf-8')
    titles=re.findall(r'^LATEST_CHANGES_TITLE\s*=\s*"Soulbound v([^\s]+)',registry,re.M)
    ck(bool(titles) and titles[-1] == VERSION, 'canonical content registry release identity')
    from validation.release_contracts import release_valid
    ck(release_valid(VERSION, '96.00.4'), 'minimum v96.00.4 release')
    banner=('SOULBOUND ONLINE v'+VERSION).encode('ascii')
    def frames_result(frames):
        rx,tx=socket.socketpair()
        def writer():
            try:
                for payload in frames:
                    tx.sendall(payload)
            finally:
                tx.close()
        t=threading.Thread(target=writer,daemon=True)
        t.start()
        try:
            return receive_login_banner(rx,banner,budget=1.5)
        finally:
            rx.close()
            t.join(timeout=1)
    correct=frames_result([b'\xff\xfa*\x01\xff\xf0',b'SOULBOUND ON',b'LINE v',VERSION.encode('ascii')])
    ck(banner in correct, 'accept exact banner assembled from split packets')
    ck(correct.startswith(b'\xff'), 'retain telnet preamble')
    wrong=frames_result([b'\xff\xfd*',b'SOULBOUND ONLINE v96.00.3'])
    ck(banner not in wrong, 'reject wrong-version banner')
    incomplete=frames_result([b'\xff\xfb*',b'SOULBOUND ON'])
    ck(banner not in incomplete, 'reject partial banner')
    return count

if __name__=='__main__':
    print(f'V96.00.4 RELEASE TCP: {run()} checks PASS',flush=True)
