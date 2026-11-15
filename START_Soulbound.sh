#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
WORKSPACE="${SOULBOUND_WORKSPACE:-$HOME/Soulbound-Linux}"
if [[ ! -f "$WORKSPACE/current/server.py" ]]; then echo 'Najpierw zainstaluj wydanie Linux.' >&2; exit 2; fi
if [[ -f "$HOME/.config/systemd/user/soulbound.service" ]]; then
  exec python3 -B -m systems.linux_release start-service --workspace "$WORKSPACE"
fi
cd -- "$WORKSPACE/current"
export PYTHONUTF8=1 PYTHONUNBUFFERED=1 SOULBOUND_HOST=0.0.0.0 SOULBOUND_PORT=4000 SOULBOUND_MAX_CLIENTS=6
export SOULBOUND_DB="$WORKSPACE/current/soulbound.db"
exec python3 -B -u server.py
