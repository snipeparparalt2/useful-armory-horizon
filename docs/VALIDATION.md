# Validation and provenance

## Current publication

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

## Known content defect retained from the supplied release

`content/data/useful_armory/recipe/shadowleggins.json` outputs `useful_armory:shadowbody`, a chestplate. The expected leggings result is `useful_armory:shadowlegs`. This is documented for the next patch; the published 0.1.2 payload intentionally matches the supplied finished build.

## Bounds of verification

The latest content is preserved unchanged. Earlier development builds and their tests are not evidence that every behavior in this supplied build works. The native runtime's full game integration and visual lighting still require an in-game build and playtest on the pinned revision. Standalone unit tests do not establish renderer compatibility.

Ore configuration attaches features to Overworld biomes only. The current generator emits animated Ultimate inventory sprites but static 128×64 worn armor textures. The roadmap describes proposed RGB armor work; it is not claimed as shipped.

Build artifacts include no user accounts, local control tokens, game executables, world saves, or private logs.
