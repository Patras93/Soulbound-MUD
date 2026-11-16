#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
V="$(tr -d '\r\n' < VERSION)"
ZIP="${SOULBOUND_ZIP:-}"
if [[ -z "$ZIP" ]]; then
  for candidate in "../Soulbound-MUD-v${V}"*.zip "./Soulbound-MUD-v${V}"*.zip; do
    if [[ -f "$candidate" ]]; then ZIP="$candidate"; break; fi
  done
fi
DB="${SOULBOUND_IMPORT_DB:-${SOULBOUND_WORKSPACE:-$HOME/Soulbound-Linux}/current/soulbound.db}"
if [[ ! -f "$DB" ]]; then DB="${SOULBOUND_IMPORT_DB:-./IMPORT_BAZY/soulbound.db}"; fi
if [[ -z "$ZIP" || ! -f "$ZIP" ]]; then
  echo 'BRAK ZIP: umiesc pelna paczke ZIP obok folderu Soulbound-MUD lub ustaw SOULBOUND_ZIP.' >&2; exit 2
fi
if [[ ! -f "$DB" ]]; then
  echo 'BRAK BAZY: wstaw kopie do IMPORT_BAZY/soulbound.db lub ustaw SOULBOUND_IMPORT_DB.' >&2; exit 2
fi
exec python3 -B -m validation.linux_predeploy_runner --zip "$ZIP" --db "$DB"
