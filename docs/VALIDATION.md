# Validation and provenance

## Original 0.1.2 publication

- Content version: **0.1.2**, taken from the supplied `useful_armory-0.1.2_1.hmod`.
- Source: the matching `useful-armory-horizon-source.zip` supplied in Downloads.
- Compared all **778 content files** byte-for-byte between the archive and source: **no differences**.
- Counts: **117 standalone item definitions, 7 block definitions, 124 recipe files**.
- Native companion version: **0.1.1**, as declared by its supplied Cargo manifest, mixin manifest, and runtime.
- Target: Horizon `fdc87aecdbd116bf1e08adcd062fcbaea8c2e2ca`, game data 26.3.
- Native mixins pin: `e8cd0aa38cffef49cb2e088ef716baa107148c02` from the supplied compatibility file.
- Ran the standalone native tests with the locally installed Rust toolchain: **5 passed, 0 failed**. They cover item lookup, color blending, radius bounds, and nearest-light selection.
- Rebuilt both packages twice with the Node packager: identical hashes across runs. Compared every rebuilt content archive entry to the supplied package: identical payloads. The ZIP container itself may differ because the packager normalizes timestamps.

## Installation issue

The screenshot's `missing horizon-native.json` came from a content `.hmod` placed in `horizon-native-mods/`. The attached file has a root `horizon-mod.toml` and no native manifest, as expected for a content-only package. The misplaced duplicate was archived, the matching current content package remained in `horizon-mods/`, and the enable setting was normalized to the manifest ID.

A launcher refresh/restart is still needed to observe the updated folder state in its UI. The native companion is a separate `.hnmod`; its packager writes a real root `horizon-native.json` plus the Rust mixin files.

The genuine supplied-source native companion was packaged and installed in the native folder. Its game build has not been run as part of this publication task.

## Recipe fix in 0.1.3

`content/data/useful_armory/recipe/shadowleggins.json` now outputs one `useful_armory:shadowlegs` instead of `useful_armory:shadowbody`. Its seven-ingot pattern and ingredients are unchanged. The only content changes from 0.1.2 are this result and the manifest version. The rebuilt archive was checked for the corrected result and an unchanged chestplate recipe. No native rebuild is needed for this data-only fix.

## Bounds of verification

The original 0.1.2 content was preserved unchanged; 0.1.3 contains the narrow recipe fix described above. Earlier development builds and their tests are not evidence that every behavior in this supplied build works. The native runtime's full game integration and visual lighting still require an in-game build and playtest on the pinned revision. Standalone unit tests do not establish renderer compatibility.

Ore configuration attaches features to Overworld biomes only. The current generator emits animated Ultimate inventory sprites but static 128×64 worn armor textures. The roadmap describes proposed RGB armor work; it is not claimed as shipped.

Build artifacts include no user accounts, local control tokens, game executables, world saves, or private logs.


## Texture-loading fix in 0.1.4

Reproduced invisible inventory icons using the untouched supplied 0.1.2 content on the installed fdc87ae executable. Explicit model parent namespaces alone did not resolve the issue. Relocating `textures/items/` to `textures/item/` and `textures/blocks/` to `textures/block/`, and updating the model references, restored the tested items and blocks in-game.

All supplied PNG files and animation metadata are preserved byte-for-byte, including worn armor textures. No artwork was generated or recolored. The texture generator now writes to the modern paths so future regeneration cannot undo this fix. Representative swords, tools, armor icons, worn armor, ore, and storage-block icons were visually checked in the diagnostic world. The Shadow leggings recipe correction remains included.

## Cleanup and licensing in 0.1.5

Removed the Test Tool (`useful_armory:wow`) and Bruh moment (`useful_armory:bruhmoment`) registrations, model definitions, creative entries, block tags, loot definition, language labels, and their unused test images. Neither had a crafting recipe. Existing saves referencing these removed IDs no longer have corresponding mod definitions.

Current counts: **116 standalone item definitions, 6 block definitions, 124 recipes**. Everything, code and art, is licensed under MPL-2.0 (changed 2026-11-12); the content package carries the licence text as `LICENSE`. Native gameplay code remains unchanged at 0.1.1.

### Standalone emissive update

Version 0.1.5 removes the native companion and ships one content file. Its six emissive overlays target worn Aquite/Shadow armor and placed Aquite/Shadow ores, using Horizon's built-in `_e.png` convention. Held/inventory items remain unchanged. The base worn-armor artwork is unchanged.

Aquite, Colosifite, and Shadow ore backgrounds use vanilla cobblestone. Respectively 187, 172, and 181 background pixels per 16×16 face were copied exactly; the remaining mineral pixels were preserved from the supplied artwork. The third-party cobblestone pixels retain their original rights. Source tools accept a locally supplied vanilla cobblestone texture rather than including a separate copy of it.

The former native tests above describe historical versions, not a requirement for the standalone release. The old native source and packages remain in Git history only.

### Final visual checks

Verified Aquite worn armor emissive accents in a nighttime third-person screenshot, with the held sword remaining non-emissive. Verified the current ore textures on placed blocks. Gallery images were captured using Wisdom Horizon 1.3.7 shaders with the native companion absent. Screenshots are original game captures, not generated promotional renders.

Placed ore glow uses a separate transparent mineral overlay with `light_emission: 15` in the block model, because the initial automatic `_e` pairing did not produce visible ore emission in the tested binary. Final nighttime screenshots verify the explicit content-model overlay. The worn armor uses the built-in `_e` equipment texture path. Neither changes world light levels or requires native code.

## Stone ores and package clean-up in 0.1.6

- **Ores in stone.** `block/aquite_ore.png`, `colosifite_ore.png` and `shadow_ore.png` are now mineral-only overlays on a transparent background, with a one-pixel pocket shadow under and to the right of each mineral patch. Every mineral pixel is identical to 0.1.5 (checked pixel by pixel against the 0.1.5 files). The three ore block models draw `minecraft:block/stone` first, the overlay second and, for Aquite and Shadow, the unchanged emissive layer third.
- **No vanilla pixels shipped.** 0.1.5 copied the vanilla cobblestone texture into the ore backgrounds. 0.1.6 references the player's own stone texture at run time instead. `tools/ore_backgrounds.ps1` is removed and `tools/gen_textures.py` no longer takes `--cobblestone`.
- **Leftovers removed.** 25 texture files that no model or equipment file referenced, and their 7 animation files, were taken out of the package: the big crafting table's block and screen textures, the old chicken textures, singularity and mask sprites, a duplicate set of bow frames and misplaced armour layers. `mod_logo.png` moved to `docs/images/original-mod-logo.png`. No model points at a missing texture afterwards (checked by script).
- `cargo horizon-mod check`, built from Horizon `fdc87ae`, accepts the 0.1.6 package.

**Not yet seen in game:** the three-layer ore models. The two-layer emissive models they extend are known to work in 0.1.5, but 0.1.6 itself needs a look in a world: placed ore, ore in the inventory, and breaking particles.

## Places to loot, 0.2.0

Everything new in 0.2.0 is written by `tools/gen_phase1.py`; running it twice gives byte-identical files.

What was checked without the game:

- Structure, template pool, structure set and biome tag files use the same keys and shapes as Horizon's own test of a mod-defined jigsaw structure (`content_root_carries_a_structure_mod`, Horizon `fdc87ae`); the village addition uses `horizon:add_to` as that test does.
- The nine `.nbt` building files were read back with an independent reader: sizes, block counts, `DataVersion` 5023, and every chest, barrel, spawner and jigsaw block entity are as intended. Previews of each building were rendered from the files and looked over.
- Every loot table entry in the mod's namespace names an item or block the mod defines (the generator refuses to run otherwise).
- All JSON parses, and `cargo horizon-mod check` built from Horizon `fdc87ae` accepts the package.

**Not yet seen in game, and the things to try first:**

1. The mod still loads (a malformed worldgen file can make Horizon start without content mods; `logs/latest.log` says so).
2. `/place structure useful_armory:ruined_forge` and the other seven: the building appears and its chest has loot.
3. `/locate structure useful_armory:wanderers_camp` in a new world.
4. The spawners: whether a spawner accepts the mod's own `tower_sentry` and `vault_guardian` types.
5. The village blacksmith: whether it joins village streets. Its street connector is hand-written.
6. Deepslate ores below Y 0 in new chunks, and their inventory icons.

Known rough edges: surface buildings sit flat on the highest ground under them, so on slopes one side can be buried or raised. The Pigman outpost is placed by height only, so it can end up inside netherrack or sticking out over a lava lake.
