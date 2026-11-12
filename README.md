# Useful Armory for Horizon

**An old Minecraft mod, brought back for Minecraft Rust.** Useful Armory started as a Forge 1.12.2 mod I made as a kid. This project ports its equipment and crafting to [Horizon](https://github.com/horizon-rust/horizon), with AI-assisted development and more planned.

[Download content mod](dist/useful_armory-0.1.2.hmod?raw=true) · [Download optional glow mod](dist/useful_armory-0.1.1.hnmod?raw=true) · [Every item and its stats](docs/items.md) · [Roadmap](docs/ROADMAP.md) · [Report a bug](https://github.com/snipeparparalt2/useful-armory-horizon/issues)

## Choose your download

| Package | Version | What it adds | Install folder |
|---|---|---|---|
| **Content — required** | 0.1.2 | Equipment, textures, recipes, blocks, and ore generation definitions | `horizon-mods/` |
| **Glow — optional native companion** | 0.1.1 | Colored visual lights from selected held, worn, and dropped gear | `horizon-native-mods/` |

Both target **Horizon nightly `fdc87ae` / Minecraft data 26.3**. Compatibility with newer Nightlies is not established. The two package version numbers are intentionally different: these are the versions in the supplied source. The downloaded filename `useful_armory-0.1.2_1.hmod` contains version **0.1.2**; `_1` is not a new mod version.

## Install

1. Open the game folder for your Horizon instance. On the default Windows setup it is `%APPDATA%\horizon`.
2. Put **one** Useful Armory `.hmod` in `horizon-mods/`. Replace older copies of the same mod; do not keep several versions enabled.
3. Enable **Useful Armory** in the Mods screen and restart the game. The stored enable key is `mod.useful_armory:true`.
4. Optional: place the **`.hnmod`** glow companion in `horizon-native-mods/`, then use the launcher's native **Build** action. This compiles Rust into the game and can take a while the first time.

**Getting `missing horizon-native.json`?** A content `.hmod` has probably been put in `horizon-native-mods/`. Move it to `horizon-mods/`. Use the separate `.hnmod` for native builds. Renaming the extension or adding a dummy manifest does not turn a content pack into a native mod.

The content pack does not need a native build. Keep a backup of important worlds when changing mods or Horizon versions.

## What you can make

**117 standalone items, 7 blocks, and 124 recipes**, collected in the **Useful Armory** creative tab. These counts come from the published content files; block inventory forms are additional to the 117 item definitions.

| Equipment family | Theme |
|---|---|
| Aquite | Aqua equipment and its own ore |
| Colosifite | Orange equipment and its own ore |
| Lapis | Blue equipment made from familiar resources |
| Quartz | Pale equipment |
| Redstone | Red equipment and redstone ingots |
| Emerald | Green equipment |
| Obsidian | Dark, durable equipment |
| Shadow | Violet and black equipment and deep ore |
| Ultimate | Endgame armor, ingots, nuggets, and a storage block |

The regular families include tools, swords, and armor. Several also have **daggers, greatswords, and halberds**. Special weapons include **Soul Eater**, **The Nether's Legacy**, **Magma Sword**, **Pigman Sword**, and **Reaper Scythe**. See the [item reference](docs/items.md) for the actual item stats.

The current content preserves the supplied build's artwork and balance. Publishing it does not silently replace its textures or rebalance its equipment.

**Known recipe issue:** Shadow leggings currently craft a chestplate. This supplied-build defect is recorded for the next patch in [validation notes](docs/VALIDATION.md).

### Mining the new ores

The current configuration adds the three ores to **Overworld biomes**, replacing stone and deepslate in newly generated chunks.

| Ore | Y range | Placement attempts per chunk | Maximum vein size |
|---|---:|---:|---:|
| Colosifite | -32 to 56 | 10 | 8 |
| Aquite | -16 to 64 | 8 | 7 |
| Shadow | -64 to -8 | 3 | 5 |

Placement attempts are not guaranteed veins: terrain and replacement rules affect the result. Shadow also discards half of candidate ore exposed to air. Existing chunks are not repopulated. This version does **not** promise ores in the Nether, End, void worlds, or every flat preset. Broader world support is on the [roadmap](docs/ROADMAP.md).

### Optional colored glow

The native companion provides visual lights for Aquite and Shadow gear, Soul Eater, Magma Sword, The Nether's Legacy, the Souled Nether Star, and glowing rotten flesh. Its source includes handling for the local player, nearby entities, and dropped items. Multiple glowing pieces increase the light radius, and mixed equipment blends colors.

These are **visual lights**: they do not prevent mob spawning or change crop growth. The five standalone native logic tests pass. Rendering behavior in a game built with this exact companion still needs verification; compilation and logic tests are not the same as a gameplay test. Details are in the [native companion documentation](native/useful_armory/README.md).

### Rainbow armor: what works today

Ultimate inventory icons have seven color-animation frames. **Worn Ultimate armor is currently a static multicolor texture**, not a smoothly cycling RGB surface. Synchronized color cycling for the full worn set is the first proposed feature in the roadmap. It is not included in this release.

## Build from source

The repository includes the complete supplied content, texture generator, native Rust source, packaging tools, and item reference. The content files were compared byte-for-byte with the attached `0.1.2` package before publication.

With Python 3.11 or newer:

```sh
python tools/package.py
python tools/item_list.py
```

Alternatively, Node.js 18 or newer can package the existing assets without Python:

```sh
node tools/package.cjs
```

Both packaging paths write the content `.hmod` and the optional native `.hnmod` into `dist/`. Texture regeneration is a separate, optional operation requiring Pillow; it is not needed to package the existing artwork.

```sh
python -m pip install pillow
python tools/gen_textures.py content/assets/useful_armory/textures
cargo test --manifest-path native/useful_armory/Cargo.toml
```

Regeneration overwrites texture assets. Review the changes before committing. Native game integration is pinned in `native/useful_armory/compatibility.json`; the launcher performs the actual game build.

## Repository map

- `content/` — everything loaded from the content mod, including textures and recipes.
- `native/useful_armory/` — optional colored-light runtime, hooks, compatibility pins, and tests.
- `tools/` — texture generation, packaging, and item documentation.
- `docs/items.md` — item and block reference.
- `docs/ROADMAP.md` — proposed visual, gameplay, and world-generation improvements.
- `docs/VALIDATION.md` — what was checked and what still needs in-game verification.
- `dist/` — downloadable packages and checksums.

## Help improve it

When reporting a bug, include the Horizon revision, content/native mod versions, world preset, whether the chunk is new, and steps to reproduce it. A screenshot or short clip helps for rendering problems.

Ideas are welcome, especially improvements that give the existing gear a purpose before adding more sets. See the [roadmap](docs/ROADMAP.md) for priorities and acceptance checks.

