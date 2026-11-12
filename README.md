# Useful Armory for Horizon

A mod made with Claude. I imported the old Minecraft mod I made as a kid (Useful Armory, Forge 1.12.2) and
I'm adding way more, all for [Horizon](https://github.com/horizon-rust/horizon), the Rust rewrite of
Minecraft: Java Edition.

It comes in two parts:

| Part | File | What it does |
|---|---|---|
| **Content mod** | `useful_armory-<version>.hmod` | The items, blocks, recipes, textures and creative tab. Data only, no code. |
| **Native mod** | `useful_armory-<version>.hnmod` | Rust compiled into the game, for behaviour data can't do. So far: glowing gear lights up the world around you in its own colour. |

Both halves share the id `useful_armory`, the usual Horizon pattern for a content mod with a native
companion. The content mod works on its own. The native mod is optional and needs the content mod for the
items. Mobs, custom sounds and special item behaviour will go in the native half later.

## What's in the mod

117 items, 7 blocks and 124 recipes, all under the `useful_armory:` namespace and listed in one creative
tab, "Useful Armory". The full list with every stat is in [docs/items.md](docs/items.md).

### Eight equipment sets

Each material has an ingot and a full set made from it: sword, pickaxe, axe, shovel, hoe, helmet, chestplate,
leggings and boots. Most also have three extra weapon types: a **dagger** (fast, lighter hits), a
**greatsword** (slow, heavy) and a **halberd** (slowest, heaviest), the last two built on a long stick.

| Set | Colour | Notes |
|---|---|---|
| Aquite | aqua | Mid-tier, mined from aquite ore. **Glows.** |
| Colosifite | orange | Mid-tier, mined from colosifite ore. |
| Emerald | green | High armour toughness and very durable tools. |
| Lapis | blue | Cheap early set. |
| Obsidian | dark purple | 6000-durability tools. |
| Quartz | white | Light early set. |
| Redstone | red | Cheap early set, made from redstone ingots. |
| Shadow | black and violet | Top regular tier: 8000-durability tools, the hardest-hitting regular weapons. **Glows.** |

On top of those there is the **Ultimate** armour (the best in the mod, its colours cycle through the
rainbow), made from ultimate ingots, nuggets and blocks.

### Special weapons

| Weapon | Attack damage | Notes |
|---|---|---|
| Soul eater | +12 | The strongest weapon, 100,000 durability. Made with a souled nether star. **Glows pink.** |
| The nether's legacy | +10 | Assembled from three parts: sword handle, sword middle and obsidian blade. **Glows cyan.** |
| Pigman sword | +7.5 | 10,000 durability. |
| Magma sword | +6.5 | 10,000 durability. **Glows orange.** |
| Reaper scythe | +5 | Also mines like a fast axe. |

### Materials and oddities

Long stick and diamond stick (handles), obsidian string, enchanted magma, souled nether star (**glows**),
bloody rotten flesh, glowing rotten flesh (**glows green**, obviously), ultimate nugget and ingot.

### Blocks

Aquite ore, colosifite ore, shadow ore, colosifite block, shadow block, ultimate block and "Bruh moment".

### Ores in the world

The three ores generate in every Overworld biome, in stone and deepslate. Mine them with a stone pickaxe or
better and smelt the ore block into its ingot.

| Ore | Height (Y) | Veins per chunk | Vein size | Notes |
|---|---|---|---|---|
| Colosifite | -32 to 56 | 10 | up to 8 | The common one, about as easy to find as iron. |
| Aquite | -16 to 64 | 8 | up to 7 | A little rarer and higher up. |
| Shadow | -64 to -8 | 3 | up to 5 | Rare and deep, like diamonds. Half the ore that would touch a cave is left out, so it mostly hides inside the rock. |

The numbers live in `content/data/useful_armory/worldgen/` (`feature/` is the vein, `placed_feature/` is
where and how often) and `neoforge/biome_modifier/add_ores.json` adds them to the Overworld. Only newly
generated chunks get ores.

## The glow

Some items used to have a soft halo painted into their icon. That halo is gone from the textures. Instead,
the native mod makes the glow happen in the world: hold a glowing item, or wear a
glowing armour piece, and the blocks and mobs around you are lit in that item's colour.

| Gear | Light colour |
|---|---|
| Aquite tools, weapons and armour | aqua `#8cffe2` |
| Shadow tools, weapons and armour | violet `#9e60ff` |
| Soul eater | pink `#e8aaec` |
| Magma sword | orange `#ff8c1e` |
| The nether's legacy | cyan `#50e6f0` |
| Souled nether star | ice blue `#96f0ff` |
| Glowing rotten flesh | green `#b4ff46` |

- One held item lights about 6 blocks around you.
- Every extra glowing piece (the other hand, each armour slot) makes the light reach further and shine
  brighter. A full set with its weapon reaches about 9 blocks.
- Mixed sets blend their colours.
- Mobs and other players holding or wearing the gear glow too, and glowing items lying on the ground give a
  small light.
- Switch it on and off in game under Options > Mods > Useful Armory.

It is a visual light (Horizon's coloured lights for native mods, `native_visuals`). It doesn't change the
light level the game uses for mob spawning or crops, and it doesn't need a shader pack.

How it works, in short: once a frame the mod reads what the player holds and wears (and what nearby mobs and
dropped items are), looks each item up in a colour table, and hands Horizon up to six coloured lights, the
nearest first. See [native/useful_armory](native/useful_armory/README.md).

## Install

Both parts target Horizon commit `fdc87ae` (Minecraft 26.3).

1. Build the two files (see below) or take them from a release.
2. Put `useful_armory-<version>.hmod` in the instance's `horizon-mods/` folder. That's all the content mod
   needs.
3. For the glow, put `useful_armory-<version>.hnmod` in `horizon-native-mods/`, then open Mods in the
   Horizon launcher and press **Build**. Native mods are Rust source that is compiled into the game, so the
   launcher downloads its own Rust toolchain and rebuilds the game once. This takes a while the first time.

## Repository layout

```
content/                      the content mod, exactly as it is zipped into the .hmod
  horizon-mod.toml              manifest (id, version, Horizon API)
  assets/useful_armory/         textures, item and block models, armour layers, language file
  data/useful_armory/horizon/   item, block and creative-tab definitions (Horizon's content format)
  data/useful_armory/recipe/    crafting and smelting recipes
  data/useful_armory/worldgen/  ore veins and where they generate
  data/useful_armory/neoforge/biome_modifier/  adds the ores to the Overworld biomes
  data/useful_armory/loot_table/  block drops
native/useful_armory/         the native mod (Rust)
  mixins/useful_armory/         the bundle Horizon compiles: horizon-mixin.toml, runtime.rs, glue.rs, helpers
  Cargo.toml                    lets `cargo test` run the mod's logic without the game
tools/
  gen_textures.py               draws every texture from shape templates and colour palettes
  package.py                    zips content/ and the native bundle into dist/
  item_list.py                  writes docs/items.md from content/
docs/items.md                 every item and block with its stats
```

## Building

Needs Python 3.11 or newer. The texture generator also needs Pillow (`pip install pillow`).

```sh
python3 tools/package.py        # dist/useful_armory-<version>.hmod and dist/useful_armory-<version>.hnmod
python3 tools/item_list.py      # refresh docs/items.md after changing items
(cd native/useful_armory && cargo test)   # the native mod's logic
```

### Textures

Every texture is generated, not hand-drawn: `tools/gen_textures.py` draws each sprite from a shape template
and shades it with a per-material colour ramp, so changing one palette restyles a whole set.

```sh
python3 tools/gen_textures.py content/assets/useful_armory/textures
```

- `--std-armor` writes worn armour at the vanilla 64x32 size instead of 128x64.
- `--halo` paints the old halo back into the glowing sprites (off by default, since the glow is in-game light
  now).

The `GLOW` table in the generator and the `GLOW` table in
`native/useful_armory/mixins/useful_armory/runtime.rs` hold the same colours. To make another item
glow, add its id and colour to the Rust table (keep it sorted by id).

## Status

- The content mod is a port of the 1.12.2 mod's equipment and crafting, plus ore generation. Both files pass
  `cargo horizon-mod check`. The ore files follow the format of Horizon's own ore test, but ore generation
  has not been seen in a running game yet.
- There are no deepslate versions of the ores yet: below Y 0 they keep their stone look.
- The two halves are two files for now. Horizon's file format allows one `.hmod` holding both, but the
  launcher at `fdc87ae` only builds native code from `.hnmod` files in `horizon-native-mods/`.
- The native mod has been applied with horizon-mixins and type-checked against Horizon `fdc87ae` with
  warnings denied, and its logic is unit tested. It has not been played in a running game yet.
- The native mod is pinned to `fdc87ae`: Horizon has no stable helper yet for reading the armour the local
  player wears, so it reads the inventory straight from the game and has to be re-checked on newer Nightlies.
- Planned: dungeons, mobs, custom sounds, more items, new mechanics and dimensions.
