# Useful Armory

A revival of my old Minecraft 1.12.2 mod for Horizon, the Rust rewrite of Minecraft. Craft equipment from Aquite, Colosifite, Shadow, and familiar materials, with armor, tools, daggers, greatswords, halberds, and special weapons.

- 117 standalone item definitions, 7 blocks, and 124 recipes.
- Eight regular equipment families plus Ultimate armor.
- Three custom ores configured for newly generated Overworld terrain.
- Animated Ultimate inventory icons; static multicolor worn armor in this release.
- Optional native companion for colored visual light from selected gear. Standalone logic tests pass; in-game integration is still being verified.

**Target:** Horizon nightly `fdc87ae`, Minecraft data 26.3.

Install the content `.hmod` in `horizon-mods/`, enable Useful Armory, and restart. The optional glow `.hnmod` belongs in `horizon-native-mods/` and requires a native game build. Putting the `.hmod` in the native folder produces a missing-manifest error.

[Downloads, source, and instructions](https://github.com/snipeparparalt2/useful-armory-horizon)

[Known issues and validation](https://github.com/snipeparparalt2/useful-armory-horizon/blob/main/docs/VALIDATION.md)

[Upcoming ideas](https://github.com/snipeparparalt2/useful-armory-horizon/blob/main/docs/ROADMAP.md): synchronized RGB worn armor, stronger material identities, finished weapon abilities, and broader survival acquisition paths. These are planned, not shipped.
