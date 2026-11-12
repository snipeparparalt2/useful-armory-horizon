# Useful Armory, native half (Horizon native mod)

The behaviour the content mod can't do as data. It has the same id as the content mod,
`useful_armory`, which holds the items. So far it does one thing: the glow.

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

## Install

Needs the Useful Armory content mod (the `useful_armory` `.hmod` in `horizon-mods/`) for the items.

1. Put `useful_armory-<version>.hnmod` in the instance's `horizon-native-mods/` folder.
2. In the Horizon launcher open Mods and press **Build**. Native mods are Rust that is compiled
   into the game, so the launcher downloads its own Rust and rebuilds the game once.
3. In game: Options > Mods > Useful Armory switches it on and off.

From source: `horizon-launcher native-build native/useful_armory/mixins/useful_armory --instance <instance> --trust-native-code`,
or `python3 tools/package.py` for the `.hnmod`.

## Files

| File | What it is |
|---|---|
| `compatibility.json` | The Horizon and horizon-mixins commits it was made and checked on |
| `mixins/useful_armory/horizon-mixin.toml` | The bundle: two modules and two HEAD hooks, pinned to Horizon `fdc87ae` |
| `mixins/useful_armory/runtime.rs` | Which items glow, how bright, which lights a frame keeps. Also this crate's library: `cargo test` |
| `mixins/useful_armory/glue.rs` | Reads the player's hands and armour, the mobs and the dropped items from the game |
| `mixins/useful_armory/visuals.rs`, `list.rs` | One small helper per hook (`native_visuals`, `native_mods`) |

To make another item glow, add its id and colour to `GLOW` in `runtime.rs` (keep the list sorted).

## Checking it against Horizon

It hooks two native hook points but also reads `Game`'s inventory and mob list directly, so it is
pinned to one Horizon commit (`horizon_revision`). After moving to a newer Nightly, check it again
with horizon-mods' tool:

```sh
python3 native/tools/native.py check /path/to/native/useful_armory --horizon latest
```
