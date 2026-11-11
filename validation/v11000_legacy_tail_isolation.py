# -*- coding: utf-8 -*-
"""Compatibility entrypoint for the archived v110 test suite.

The five real checks now belong to v111; neither current FAST nor FULL
imports this shim. It may be retired once v110 historical gates are migrated.
"""
from validation.v11100_current_tail_isolation import AUDITS, verify_result, _unused_loopback_port, run, regression
if __name__ == '__main__':
    print(f'V110 LEGACY V103 ISOLATION CONTRACT: {regression()} checks PASS',flush=True)
