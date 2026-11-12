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
