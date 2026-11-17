# -*- coding: utf-8 -*-
"""Linux PREDEPLOY entrypoint. Never installed into the live runtime."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from systems import linux_release
from validation.linux_legacy_windows_fixtures import install_test_fixtures, remove_test_fixtures


def main(argv=None):
    parser=argparse.ArgumentParser(description='PREDEPLOY pelnej paczki Linux')
    parser.add_argument('--zip',required=True)
    parser.add_argument('--db',required=True)
    parser.add_argument('--approval',default=str(linux_release.ROOT.parent/'Soulbound_PREDEPLOY_LINUX'/'last_result.json'))
    args=parser.parse_args(argv)
    try:
        linux_release.predeploy(args.zip,args.db,args.approval,
            stage_hooks=(install_test_fixtures,remove_test_fixtures))
        return 0
    except (Exception,KeyboardInterrupt) as error:
        print('PREDEPLOY LINUX FAIL: '+type(error).__name__+': '+str(error),file=sys.stderr,flush=True)
        return 2

if __name__=='__main__':raise SystemExit(main())
