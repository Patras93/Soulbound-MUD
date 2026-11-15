#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
WORKSPACE="${SOULBOUND_WORKSPACE:-$HOME/Soulbound-Linux}"
if [[ -f "$HOME/.config/systemd/user/soulbound.service" ]]; then
  exec python3 -B -m systems.linux_release status-service --workspace "$WORKSPACE"
fi
echo 'Brak uslugi systemd. Dzialanie serwera sprawdz przez klienta TCP na porcie 4000.'
