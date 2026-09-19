# Soulbound v0.32.0

## Craft Quest + Salvage Progress Fix

- Wszystkie udane receptury wysyłają wspólny event craftu do aktywnych questów.
- Naprawione są m.in. zlecenia Broka na hełmy i pozostałe podobne cele craftingowe.
- Zwykły Salvage, Salvage 3.0 oraz Tech Salvage dają Kowalstwo XP.
- Salvage nie zwiększa sztucznie użyć/XP Młota Rzemieślniczego.

## Forge & Materials 3.0

- Salvage 3.0: EQ + technologiczne przedmioty, Boardy, Upgrade Kity i części bossowe.
- Refining 2.0: Hartowana Stal, Stop Magitek, Astralny Stop, Stop Eternium.
- Forge 3.0: +1..+10; od +4/+7/+10 wymagane są coraz wyższe stopy Refining.
- Tech EQ: 8-częściowe sety Meca, Inżyniera i Cyborga z progami 2/4/6/8.
- Socket Crafting: `socketcraft <EQ>`, maks. +2 trwałe gniazda na przedmiot.
- Rune Crafting: runy zużywają Pył Runiczny + odpowiedni klejnot/materiał technologiczny.
- V-MAX Upgrade Path: `vmaxupgrade duration` (+10 s, maks. 3) i `vmaxupgrade cooling` (-8 s Overheat, maks. 2).
- Material Conversion UI: `konwersje`.
- Hurtowe przetapianie: `przetop max <metal>`, `przetop wszystko`.
- Hurtowy crafting: `craft max <receptura>`.
- Full Crafting Audit 2.0: 0 błędów, 0 martwych materiałów.

## Poprzednie zmiany

## v0.31.13 — Salvage Smelting Auto-Pull
- `przetop <metal>` najpierw używa normalnej rudy z Sakwy Górnika.
- Gdy rudy brakuje, automatycznie pobiera zgodne fragmenty ze Szkatułki -> Salvage.
- Obsługiwane: żelazo, stal, kobalt, runiczne, Smocza Stal, Astral, Pustka i Eternium.
- Salvage ma przelicznik 2 fragmenty -> 1 sztabka; świeża ruda pozostaje 1 -> 1.
- Mithril i Adamantyt pozostają materiałami ulepszania EQ, ponieważ obecna linia Kowalstwa nie ma dla nich osobnych sztabek/receptur przetopu.

Tech Crafting + Machine Salvage 2.0 + Runes & Sockets 2.0.

Najważniejsze:
- Machine komponenty trafiają do Szkatułki -> Technologia.
- `techsalvage` rozkłada zaawansowane części Machine.
- `techcraft` tworzy Boardy, komponent Meca, Upgrade Kit Inżyniera i technologiczne EQ.
- `vmaxstatus` pokazuje dokładny stan V-MAX/Overheat.
- istniejące runy i Gem Cutting zostały zachowane i rozszerzone; `gemsockets` pokazuje gniazda EQ.
- przetop wszystkich rud: 1 ruda -> 1 sztabka.

v0.31.12 — Tech Crafting, Machine Salvage 2.0, Runes & Sockets 2.0
- Machine components now go to Craftbox -> Technology.
- Tech Salvage converts advanced Machine parts into Servo/Circuit/Power Cell/Plating.
- Tech Crafting adds Cyborg Boards, Mec component, Engineer Upgrade Kit and technological EQ.
- Existing runes/gem sockets expanded; high-level armor can receive gem sockets.
- V-MAX status UI added.
- All ore smelting recipes are now 1 ore -> 1 ingot.

# Soulbound v0.31.10

Magitek Dungeon 2.0 + Full Mec Rework + Engineer Upgrade 2.0.

Najważniejsze:
- pełny authored Mec kit z gałęziami Melee/Ranged/Feedback/Magic/Support/Counter/Inherent/Passive;
- V-MAX i interakcje Cosmic Rave / Shoot-All / Starlight Shower;
- Self-Repair, mastery/programs/protocols;
- Engineer Upgrade 2.0 z trwałymi slotami i opisem efektów;
- 16 nowych pomieszczeń Magitek Dungeon 2.0 + 4 bossy.
- brak systemu AP.


## v0.31.10
Stalowe Płyty z Pancerza można przetapiać w Kuźni: 4 płyty = 1 Sztabka Stali. Komendy: `przetop płyty` / `smelt plates`.


## v0.31.12
Odłamki Żelaza z salvage: 2 sztuki można przetopić w Kuźni w 1 Żelazną sztabkę.

## v0.32.0 — Party Progress, Recap & Tech Set Milestone
- Party Quest Progress 2.0: kill questy i boss credit dla członków party stojących w tej samej lokacji; gather/craft pozostają indywidualne.
- Dungeon Party Bonuses: mały bonus EXP tylko w lochach, do +7%, zależny od pełnej drużyny i różnorodności klas.
- Death/Combat Recap 2.0: finalny cios, przyczyna, 10 ostatnich zdarzeń, healing saved i guard saved.
- Tech Set Upgrade: 24 części setów Mec/Inżynier/Cyborg można podnosić do Mk-II/Mk-III.
- Salvage 4.0: zwrot run przy ostatniej kopii EQ oraz odzysk klejnotów zależny od Kowalstwa.


## v0.33.0 — progres umiejętności i EQ
Każda aktywna umiejętność rozwija swoją skuteczność z Skill Level 1-400. Skill Level wpływa globalnie na moc efektu oraz cooldown; pasywy rozwijają się podczas używania aktywnych umiejętności tej samej klasy. EQ ma nieliniową krzywą 1-400, więc kolejne progi sprzętu dają coraz większą, odczuwalną przewagę.
