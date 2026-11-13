<p align="center">
  <img src="docs/images/banner.png" alt="Useful Armory" width="100%">
</p>

<p align="center">
  <b>Weapons, armour, trinkets and dungeons for <a href="https://github.com/horizon-rust/horizon">Horizon</a>, the Rust rewrite of Minecraft: Java Edition.</b><br>
  Useful Armory started as a Forge 1.12.2 mod I made as a kid. This is it rebuilt and expanded.
</p>

<p align="center">
  <img alt="Horizon" src="https://img.shields.io/badge/Horizon-fdc87ae%20(2026--11--08)-6b4fd8">
  <img alt="Game data" src="https://img.shields.io/badge/game%20data-26.3-3d8b5a">
  <img alt="Version" src="https://img.shields.io/badge/version-0.1.7%20in%20development-e0a81e">
  <img alt="Licence" src="https://img.shields.io/badge/licence-MPL--2.0-c0392b">
</p>

<p align="center">
  <a href="../../releases">Releases</a> ·
  <a href="docs/items.md">Every item and its stats</a> ·
  <a href="docs/ROADMAP.md">Roadmap</a> ·
  <a href="docs/SCREENSHOTS.md">Screenshots</a> ·
  <a href="../../issues/new/choose">Report a bug</a>
</p>

<p align="center">
  <img src="docs/images/aquite-armor.png" alt="Worn Aquite armour in game" width="49%">
  <img src="docs/images/emissive-armor-night.png" alt="Aquite armour glowing at night" width="49%">
</p>

> **Status:** 0.1.7 is being built on `main` and has not been play-tested yet. The latest published
> release is **0.1.6** (content only). Everything below describes 0.1.7 unless it says otherwise.

## What's inside

<img src="docs/images/sets.png" align="right" width="320" alt="The eight material sets">

**Eight material sets**: Aquite, Colosifite, Emerald, Lapis, Obsidian, Quartz, Redstone and Shadow.
Each has a sword, pickaxe, axe, shovel, hoe and four armour pieces. On top of those comes the
**Ultimate** set, which cycles through seven colours.

**Full-set bonuses.** Wear all four pieces of a set:

| Set | Bonus |
|---|---|
| Aquite | Water breathing and dolphin's grace |
| Colosifite | Fire resistance |
| Emerald | Luck |
| Lapis | +25% experience |
| Obsidian | Half knockback and half explosion damage |
| Quartz | Speed |
| Redstone | Haste |
| Shadow | Night vision |
| Ultimate | Slow regeneration and no fall damage |

**Glowing gear.** Glowing items (Aquite, Shadow and a few special weapons) light up the world
around you in their own colour, whether you hold them, wear them or drop them. Aquite and Shadow
armour and ores also have full-bright accents.

<br clear="right">

### Weapons

<img src="docs/images/weapons.png" align="left" width="320" alt="Daggers, greatswords and halberds">

- **Daggers** deal bonus damage when you strike from behind.
- **Greatswords** splash damage onto nearby enemies.
- **Halberds** reach one block further.
- **Unique weapons**: the **Magma sword** sets targets on fire, the **Soul eater** heals you on a
  kill, the **Pigman sword** hits piglins harder, **The Nether's legacy** is stronger in the Nether,
  and the **Reaper scythe** makes mobs drop their heads.

<br clear="left">

### Tools that do more (hold sneak)

| Ability | Tools |
|---|---|
| Vein mining | Colosifite, Emerald and Shadow pickaxes |
| 3x3 digging | Obsidian pickaxe and shovel |
| Tree felling | Aquite, Emerald and Shadow axes |
| Harvest sweep | Any hoe (3x3), the Reaper scythe (5x5) |

Every ability has its own switch under **Options > Mods > Useful Armory**. Use these switches if
you also run a separate vein-mining or tree-felling mod.

### Places to find

Twelve generated places, with loot in every chest and barrel:

| Place | Where |
|---|---|
| Ruined forge | Forests, plains, meadows |
| Wanderer's camp | Forests, taiga, savanna, plains, desert |
| Aquite shrine | Beaches, rivers, swamps |
| Colosifite watchtower | Hills, savanna, badlands. Guarded by tower sentries |
| Bandit fort | Forests, taiga, savanna, plains, meadows |
| Armory blacksmith | Plains, desert, savanna, snowy and taiga villages |
| Pigman outpost | Nether wastes |
| Shadow vault | A mausoleum on the surface, with a spiral stair down to the vault and its guardians |
| Miner's cache | Underground, Y 0 to 40 |
| Forgotten armory | Underground, Y -30 to 20, rare |
| Infested mine | Underground, Y -20 to 40 |
| Crypt | A mausoleum entrance leading down into a multi-room dungeon with one treasure room |

Find one with `/locate structure useful_armory:<name>`, or drop one in front of you with
`/place structure useful_armory:<name>`. Only newly generated chunks get places. Six **relics**
(cracked soul gem, ancient hilt, forge master's hammer head, shadow shard, tarnished ring, faded map
scrap) turn up in their chests.

### New ores

<img src="docs/images/ores-and-storage.png" align="right" width="360" alt="Ores and storage blocks in game">

Aquite, Colosifite and Shadow ore generate in stone, and in deepslate further down. The ore
textures hold only the mineral and draw the game's own stone underneath, so they match any resource
pack.

| Ore | Y range | Attempts per chunk | Max vein |
|---|---:|---:|---:|
| Colosifite | -32 to 56 | 10 | 8 |
| Aquite | -16 to 64 | 8 | 7 |
| Shadow | -64 to -8 | 3 | 5 |

<br clear="right">

<p align="center">
  <img src="docs/images/armor.png" alt="Worn armour for every set" width="100%">
</p>

## Still being built for 0.1.7

0.1.7 ships as one update. These parts are in progress, and the textures for most are already drawn:

- [ ] New mobs: shade, tide lurker, ember brute and lost pigman, plus their own looks for the vault guardian and tower sentry
- [ ] Gold chicken, a tameable shadow hound and the armory golem
- [ ] Trinkets (rings, charms, amulets), backpacks, waystones and the recall charm
- [ ] Soul jar, soul forge upgrades, and charged greatsword and halberd attacks
- [ ] Bosses (forge warden, pigman king, reaper) and the shadow citadel
- [ ] Custom enchantments and armour trims

<p align="center">
  <img src="docs/images/new-gear.png" alt="Trinkets, backpacks and soul gear" width="49%">
  <img src="docs/images/mobs.png" alt="New mobs" width="49%">
</p>

## Install

You need **Horizon nightly `fdc87ae`** (2026-11-08), which runs game data 26.3.

From 0.1.7 on, Useful Armory comes as **two files** with the same id, attached to each
[release](../../releases), and needs the library mod [Armory Lib](https://github.com/snipeparparalt2/armory_lib):

| File | Put it in | What it is |
|---|---|---|
| `useful_armory-<version>.hmod` | `horizon-mods/` | Items, blocks, recipes, loot, places and world generation |
| `useful_armory-<version>.hnmod` | `horizon-native-mods/` | The Rust code for glowing gear, set bonuses, tool abilities and weapon effects. The launcher compiles it into the game. |
| `armory_lib-<version>.hnmod` ([Armory Lib releases](https://github.com/snipeparparalt2/armory_lib/releases)) | `horizon-native-mods/` | The library the native half is built on: it draws the glow and the new mobs and keeps the settings page. |

1. Open your Horizon game folder. On a default Windows install it is `%APPDATA%\horizon`.
2. Put each file in its folder, and remove older copies of Useful Armory.
3. Build in the Horizon launcher, enable **Useful Armory** in the Mods screen, and restart.

**Getting `missing horizon-native.json`?** The `.hmod` is in `horizon-native-mods/`. Move it to
`horizon-mods/`.

Native mods are compiled into the game and are not sandboxed, so only install them from sources you
trust. The full source is in [`native/useful_armory/`](native/useful_armory). Back up important
worlds before changing mods or Horizon versions.

### Check a download

Release files are signed with [minisign](https://jedisct1.github.io/minisign/). Each file has a
`.minisig` beside it, which you can check against the key in `minisign.pub`:

```sh
minisign -Vm useful_armory-<version>.hmod -p minisign.pub
```

## Gallery

<p align="center">
  <img src="docs/images/emissive-ores-night.png" alt="Ore accents at night" width="80%"><br>
  <img src="docs/images/animations.gif" alt="Animated textures" width="80%"><br>
  <img src="docs/images/uniques.png" alt="Unique weapons and the Ultimate set" width="49%">
  <img src="docs/images/blocks.png" alt="Blocks" width="49%">
</p>

The four in-game captures were taken on 0.1.5 with the optional Wisdom Horizon shaders, before the
ores moved from cobblestone to stone. The other images are texture renders. New in-game screenshots
will follow the 0.1.7 play-test. See [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md) for captions.

## Build from source

```sh
python3 tools/gen_phase1.py --schema <block_schema.json>   # places, loot, relics, ores, mobs
python3 tools/gen_phase2.py                                # ability tooltips on items
python3 tools/package.py                                   # dist/useful_armory-<version>.hmod and .hnmod
(cd native/useful_armory && cargo test)                    # native logic tests
cargo horizon-mod check dist/useful_armory-<version>.hmod  # Horizon's own package check
```

Textures are drawn by script with Pillow: `tools/gen_textures.py` (equipment, blocks, worn armour)
and `tools/gen_new_art.py` (trinkets, backpacks, soul gear, waystone, soul forge, mobs). Both
overwrite their files, so review the changes before committing. Releases are signed as described in
[docs/SIGNING.md](docs/SIGNING.md).

## Repository map

- `content/`: everything the content mod loads (textures, models, recipes, loot, places)
- `native/useful_armory/`: the native half (Rust). It depends on [Armory Lib](https://github.com/snipeparparalt2/armory_lib), which has its own repository
- `tools/`: generators, packaging and the item list
- `docs/`: [items](docs/items.md), [roadmap](docs/ROADMAP.md), [validation](docs/VALIDATION.md), [screenshots](docs/SCREENSHOTS.md), [signing](docs/SIGNING.md)
- `dist/`: the latest built packages and their checksums

## Reporting a bug

[Open an issue](../../issues/new/choose) and fill in the template. Include the Horizon revision,
both Useful Armory versions, and `logs/latest.log`. Screenshots help with rendering problems.

## Licence

Everything in this repository, code and art alike, is licensed under the
[Mozilla Public License 2.0](LICENSE). You may play it, share it and reuse its files in your own
projects. If you change any of this mod's files and share the result, those files must stay under
MPL-2.0 with their source available. Minecraft, Horizon and shader content shown in screenshots
belongs to its owners.
