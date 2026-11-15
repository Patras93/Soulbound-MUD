#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
WORKSPACE="${SOULBOUND_WORKSPACE:-$HOME/Soulbound-Linux}"
if [[ -f "$HOME/.config/systemd/user/soulbound.service" ]]; then
  exec python3 -B -m systems.linux_release stop-service --workspace "$WORKSPACE"
fi
echo 'Nie ma uslugi systemd. Serwer uruchomiony w terminalu zatrzymaj Ctrl+C; nie zabijam obcego procesu.'
