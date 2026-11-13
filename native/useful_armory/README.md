# Useful Armory, native half (Horizon native mod)

The behaviour the content mod can't do as data. It has the same id as the content mod,
`useful_armory`, which holds the items. It needs [Armory Lib](https://github.com/snipeparparalt2/armory_lib) (`armory_lib`), the
library mod that draws the glow and the mod's creatures and keeps the settings page. It does
five things, each with its own switch:

- **Glow**: glowing gear casts coloured light.
- **Set bonuses**: a full armour set gives a bonus.
- **Vein mining**, **wide dig**, **tree felling**: some tools break more than one block while
  you sneak.
- **Harvest sweep**: the mod's hoes and the reaper scythe harvest and replant an area of crops.
- **Weapon effects**: daggers, greatswords and the special weapons do something extra.

Everything but the glow runs on the server (single player's server thread, a LAN host or a
dedicated server). The item tooltips saying what each item does are lore lines in the content
mod, written by `tools/gen_phase2.py`.

## The glow

Glowing Useful Armory gear casts real coloured light. Hold a glowing item or wear a glowing
armour piece and the blocks and mobs around you light up in that item's colour. Mobs and other
players carrying the gear glow too, and so do the items lying on the ground.

It replaces the soft halo that used to be painted into the item textures: the textures are
clean now and the glow happens in the world.

| Gear | Colour |
|---|---|
| Aquite tools, weapons and armour | aqua `#8cffe2` |
| Shadow tools, weapons and armour | violet `#9e60ff` |
| Soul eater | pink `#e8aaec` |
| Magma sword | orange `#ff8c1e` |
| The nether's legacy | cyan `#50e6f0` |
| Souled nether star | ice blue `#96f0ff` |
| Glowing rotten flesh | green `#b4ff46` |

One held item lights about 6 blocks. Each extra glowing piece (other hand, each armour slot)
makes the light reach further and shine brighter; a full set with its weapon reaches about
9 blocks. Mixed sets blend their colours. It is a visual light (Horizon's `native_visuals`
coloured lights): it does not stop mobs spawning or change the light level blocks see.
Armory Lib draws it; this mod registers the items and colours (`api/src/content.rs`).

## Creatures

The shade, tide lurker, ember brute, lost pigman, vault guardian and tower sentry are copies
of the zombie in the content mod. Registered with Armory Lib, each is drawn with its own
texture and glowing layer on the zombie's body, doesn't turn into a drowned, and takes no
damage from burning (so daylight can't kill it; the flames still show). A tide lurker's hit
slows the player for 5 seconds.

## Set bonuses

Active while all four pieces of one set are worn. The effects are vanilla's, given again every
second for 3 seconds (night vision for 13, so it never flickers), without particles; they are
taken off at once when the set comes off.

| Set | Bonus |
|---|---|
| Aquite | Water breathing and dolphin's grace (faster swimming) |
| Colosifite | Fire resistance |
| Emerald | Luck |
| Lapis | Experience orbs picked up are worth 25% more |
| Obsidian | Knockback halved; explosions do half damage |
| Quartz | Speed |
| Redstone | Haste |
| Shadow | Night vision |
| Ultimate | One health point back every 4 seconds; no fall damage |

The lapis bonus is on every orb picked up: the game's experience hook can't tell an orb from a
kill or an ore from one a furnace, breeding or fishing dropped. The shadow set does not change
how far hostile mobs notice a sneaking wearer: Horizon has no hook for a mob's detection range
at this commit (`native_living_change_target` names the mob and the player, not where either
stands or how far the mob can see).

## Tool abilities

All only while sneaking, on the server. The extra blocks are broken as the player's own breaks,
one by one: drops for the tool (Fortune, Silk Touch, the right tool for the drop), wear on the
tool, statistics, experience from ores and spawn protection are all as if mined by hand. They
stop when the tool has only enough durability left for the block actually clicked, so the
abilities never break a tool. Creative mode digs the same blocks and drops nothing.

| Tool | Ability |
|---|---|
| Colosifite, emerald and shadow pickaxes | **Vein mining**: breaking an ore also breaks the ore blocks of the same kind connected to it (through faces, edges and corners), up to 32. Deepslate and plain ore count as one kind. An ore is a block in `c:ores` or the vanilla `minecraft:*_ores` tags, or one of the mod's own ores |
| Obsidian pickaxe and shovel | **Wide dig**: also breaks the 3 x 3 square around the block, across the face you hit (from where you look when that can't be told), only blocks the tool is made for and no harder than the block you broke |
| Aquite, emerald and shadow axes | **Tree felling**: breaking a log also breaks the logs of the same kind connected to it at its height and above, up to 64 |

**Harvest sweep** (no sneaking): right-click a fully grown crop with any of the mod's hoes to
harvest the grown crops in the 3 x 3 square around it (the reaper scythe: 5 x 5) and plant each
again with one of its own seeds. One durability per crop; it stops before the hoe would break.
Wheat, carrots, potatoes, beetroots and nether wart.

The emerald axe's item data mines like a pickaxe (its tool rules are the pickaxe's); tree felling
still works with it, as logs drop for any tool.

## Weapon effects

| Weapon | Effect |
|---|---|
| Daggers | Double damage when you are within 60 degrees of straight behind the target |
| Greatswords | The other mobs within 1.5 blocks of the target take half the hit's damage too |
| Halberds | One more block of reach: data, an `entity_interaction_range` modifier on the item |
| Magma sword | Sets the target on fire for 4 seconds |
| Soul eater | Heals you a heart on each kill |
| Pigman sword | 50% more damage to piglins, piglin brutes, hoglins, zoglins and zombified piglins |
| The nether's legacy | 50% more damage in the Nether |
| Reaper scythe | Zombies, skeletons and creepers it kills drop their head 10% of the time, wither skeletons 5% |

The numbers are named constants at the top of each part of `runtime.rs`.

## Settings

Options > Mods > Useful Armory switches the whole mod on and off. Its page has one switch per
part: Glow, Set bonuses, Vein mining, Wide dig, Tree felling, Harvest sweep, Weapon effects (all
on at first). Armory Lib draws the page; a change takes effect within a second. They are kept as files in `horizon-mods/.horizon-mod-data/useful_armory/`. If you
also run the Veinminer or TreeFall native mods, switch off the matching part here (or there):
both would act on the same break. The server's own switches count, so on a LAN world the host's.

## Install

Needs the Useful Armory content mod (the `useful_armory` `.hmod` in `horizon-mods/`) for the items,
and [Armory Lib](https://github.com/snipeparparalt2/armory_lib).

1. Put `useful_armory-<version>.hnmod` and `armory_lib-<version>.hnmod` in the instance's
   `horizon-native-mods/` folder. Without the library the launcher's build stops and says so.
2. In the Horizon launcher open Mods and press **Build**. Native mods are Rust that is compiled
   into the game, so the launcher downloads its own Rust and rebuilds the game once.
3. In game: Options > Mods > Useful Armory switches it on and off.

From source: `horizon-launcher native-build native/useful_armory/mixins/useful_armory --instance <instance> --trust-native-code`,
or `python3 tools/package.py` (or `node tools/package.cjs`) for the `.hnmod`.

## Files

| File | What it is |
|---|---|
| `compatibility.json` | The Horizon and horizon-mixins commits it was made and checked on |
| `mixins/useful_armory/horizon-mixin.toml` | The bundle: two modules and the HEAD hooks below, the `[api]` package and the dependency on `armory_lib`, pinned to Horizon `fdc87ae` |
| `mixins/useful_armory/runtime.rs` | The decisions, with no game in them: which items do what, set detection, the flood fill, the 3 x 3 geometry, the backstab angle, the caps, the switches. Also this crate's library: `cargo test` |
| `mixins/useful_armory/api/` | The package the launcher links beside the game. `src/content.rs` lists the glowing items, the creatures and the settings switches; `src/lib.rs` registers them with Armory Lib |
| `mixins/useful_armory/gear.rs` | Set bonuses, tool abilities, harvest sweep and weapon effects: what they read and change in the game |
| the other `.rs` files | One small helper per hook, calling into `gear.rs` |

## Hooks used

| Hook point | For |
|---|---|
| `native_player_tick` | Reads each player's armour (`native_equipment`), gives the set effects (`native_add_effect`, `native_remove_effect`), heals the ultimate set (`native_set_player_status`), deals greatsword splashes (`native_mobs`, `native_hurt_entity`) |
| `native_living_incoming_damage_v3` | No fall damage (ultimate), half explosion damage (obsidian), for the player victim by UUID |
| `native_living_knockback` | The obsidian set's knockback, for the player victim by entity id |
| `native_player_exp_change` | The lapis set's experience |
| `native_destroy_block` | Vein mining, wide dig, tree felling (`native_sneaking`, `native_block_name_in_tag`, `native_raycast`, then the game's own player break for each extra block) |
| `native_use_item_on` | Harvest sweep (`native_machine_destroy_block` with the hoe as the tool, `native_set_block` to replant) |
| `native_living_incoming_damage_v2` | Dagger, pigman sword and nether's legacy damage; greatsword hits remembered |
| `native_hurt_enemy` | Magma sword fire; greatsword splash queued for the player tick |
| `native_mob_killed` | Soul eater heal; reaper scythe head roll (`native_level_random`) |
| `native_loot_drops` | The reaper scythe's head joins the mob's loot |

Breaking an extra block runs the break hook again: a guard in `runtime.rs` (`Breaking`) keeps
those breaks from starting more.

## Checking it against Horizon

Besides the hook points and their helpers it reads `Game` directly (the inventory and mob list,
block facts, item info) and calls the game's own player break (`break_block_as_player`) and
`pop_resource`, so it is pinned to one Horizon commit (`horizon_revision`). After moving to a
newer Nightly, check it again with horizon-mods' tool:

```sh
python3 native/tools/native.py check /path/to/native/useful_armory --horizon latest
```

The logic alone: `cargo test --offline` in this folder.
