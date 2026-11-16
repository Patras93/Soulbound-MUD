#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
exec python3 -B -m systems.linux_release install-service --workspace "${SOULBOUND_WORKSPACE:-$HOME/Soulbound-Linux}"
