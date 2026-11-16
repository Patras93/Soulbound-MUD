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
WORKSPACE="${SOULBOUND_WORKSPACE:-$HOME/Soulbound-Linux}"
DB="${SOULBOUND_IMPORT_DB:-$WORKSPACE/current/soulbound.db}"
if [[ ! -f "$DB" ]]; then DB="${SOULBOUND_IMPORT_DB:-./IMPORT_BAZY/soulbound.db}"; fi
if [[ ! -f "$ZIP" || ! -f "$DB" ]]; then echo 'Brak ZIP lub bazy. Przerwano.' >&2; exit 2; fi
printf 'Wydanie v%s, baza %s, instalacja %s. Wpisz WDRAZAM: ' "$V" "$DB" "$WORKSPACE"
read -r consent || exit 2
if [[ "$consent" != 'WDRAZAM' ]]; then echo 'Anulowano. Nic nie zmieniono.'; exit 2; fi
python3 -B -m systems.linux_release deploy --zip "$ZIP" --db "$DB" --workspace "$WORKSPACE"
if [[ ! -f "$HOME/.config/systemd/user/soulbound.service" ]]; then
  echo 'Gra zainstalowana. Aby uruchomic pod systemd, uruchom INSTALUJ_USLUGE_LINUX.sh.'
fi
