# Soulbound v0.71.7 — Runtime Performance II

v0.71.7 extends the v0.71.5–v0.71.6 performance line without changing gameplay data or balance.

## Runtime hot-path improvements

- Inventory/equipment commands now operate on the player's owned inventory rows instead of scanning the 66k+ global ITEMS catalog and querying SQLite once per catalog entry. This covers Auto EQ, equip resolution, EQ comparison, player transfers, bank deposits, Salvage planning and upgrade lists.
- Auto EQ loads equipped slots once and batches slot writes into one final commit. Ordinary manual equip keeps immediate persistence.
- World refresh now builds a live-mob-per-room index during its existing pass. Room targeting and dungeon boss gates read the current room index instead of rescanning the full world.
- Dynamic mob spawn/removal invalidates the room index; wander updates it; room reads still filter current alive/room state for coalescing-window safety.
- Mining caches the base raw-gem catalog instead of scanning ITEMS on each gem-drop attempt.
- Item-source lookup, quest-map cleanup, crafting-quality equivalents, Codex relic IDs and legendary leaderboard IDs use catalog caches/indexes with size-based invalidation.
- Bulk Salvage plans from owned inventory plus one equipment snapshot rather than catalog-wide item quantity probes.

## Memory and save compatibility

Memory Efficiency II v0.61.6 remains enabled. No wipe and no SQLite migration are required.

## Gameplay identity check

Final v0.71.6 and v0.71.7 runtime catalogs produced identical SHA-256 signatures for:

- ITEMS: 66,246 entries
- MOB_TEMPLATES: 14,559
- QUESTS: 844
- ROOMS: 1,573
- MOB_SPAWNS: 1,776

The release changes access patterns and caching, not content or balance.

## Verification

- FAST PREDEPLOY: PASS.
- Runtime manifest: 181 modules; 0 missing; 0 syntax errors.
- Railway critical import: PASS.
- SQLite smoke: 102 tables / 105 objects.
- Commands: 877 aliases / 239 handlers.
- Normal assembled runtime load in the test environment: approximately 22–23 seconds.
- Per-room mob index smoke test matched the canonical full-world scan.
- Full historical audit was started but did not complete within the available execution window; it produced no error before termination and is not marked PASS.
