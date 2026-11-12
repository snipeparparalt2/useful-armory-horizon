# Useful Armory for Horizon

**An old Minecraft mod, brought back for Minecraft Rust.** Useful Armory started as a Forge 1.12.2 mod I made as a kid. This project ports its equipment and crafting to [Horizon](https://github.com/horizon-rust/horizon), with AI-assisted development and more planned.

[Download content mod](dist/useful_armory-0.1.6.hmod?raw=true) · [Every item and its stats](docs/items.md) · [Roadmap](docs/ROADMAP.md) · [Report a bug](https://github.com/snipeparparalt2/useful-armory-horizon/issues)

## Download

| Package | Version | What it adds | Install folder |
|---|---|---|---|
| **Content — required** | 0.1.6 | Equipment, textures, recipes, blocks, and ore generation definitions | `horizon-mods/` |

**Targets Horizon nightly `fdc87ae` / Minecraft data 26.3.** Version 0.1.6 is one standalone content mod. No native companion, library mod, or native game build is needed.

## Install

1. Open the game folder for your Horizon instance. On the default Windows setup it is `%APPDATA%\horizon`.
2. Put **one** Useful Armory `.hmod` in `horizon-mods/`. Replace older copies of the same mod; do not keep several versions enabled.
3. Enable **Useful Armory** in the Mods screen and restart the game. The stored enable key is `mod.useful_armory:true`.

**Getting `missing horizon-native.json`?** A content `.hmod` has probably been put in `horizon-native-mods/`. Move it to `horizon-mods/`. Renaming the extension or adding a dummy manifest does not turn a content pack into a native mod.

The content pack does not need a native build. Keep a backup of important worlds when changing mods or Horizon versions.

## What you can make

Version 0.1.5 removed the old Test Tool and Bruh moment block. Version 0.1.6 puts the ores back in stone and removes unused leftover textures from the original mod, including the big crafting table.

**116 standalone items, 6 blocks, and 124 recipes**, collected in the **Useful Armory** creative tab. These counts come from the published content files; block inventory forms are additional to the 116 item definitions.

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

**Fixed in 0.1.4:** existing texture files now use the modern atlas paths, fixing invisible item icons and block textures without redrawing any artwork. The 0.1.3 recipe fix is included: the seven-ingot Shadow leggings recipe now produces Shadow leggings instead of a chestplate. 

### Mining the new ores

The current configuration adds the three ores to **Overworld biomes**, replacing stone and deepslate in newly generated chunks.

| Ore | Y range | Placement attempts per chunk | Maximum vein size |
|---|---:|---:|---:|
| Colosifite | -32 to 56 | 10 | 8 |
| Aquite | -16 to 64 | 8 | 7 |
| Shadow | -64 to -8 | 3 | 5 |

Placement attempts are not guaranteed veins: terrain and replacement rules affect the result. Shadow also discards half of candidate ore exposed to air. Existing chunks are not repopulated. This version does **not** promise ores in the Nether, End, void worlds, or every flat preset. Broader world support is on the [roadmap](docs/ROADMAP.md).

### Emissive armor and ore accents

Aquite and Shadow worn armor and placed ore blocks have selected full-bright texture accents, included in the normal `.hmod`. Their base artwork is preserved. Shaders can add bloom around those accents; the gallery uses Wisdom Horizon 1.3.7. The shader is optional and is not bundled.

These textures do not cast colored light onto nearby blocks or affect mob spawning. Held items and inventory icons do not gain emissive overlays on the targeted Horizon build. The former separate native lighting companion has been removed.

**Ores sit in stone (0.1.6).** The ore textures hold only the mineral. Each ore block draws the game's own stone texture underneath, so the rock always matches the stone around it, including under a resource pack, and the mod ships no vanilla pixels.

### Rainbow armor: what works today

Ultimate inventory icons have seven color-animation frames. **Worn Ultimate armor is currently a static multicolor texture**, not a smoothly cycling RGB surface. Synchronized color cycling for the full worn set is the first proposed feature in the roadmap. It is not included in this release.

## Build from source

The repository includes the complete supplied content, texture generator, packaging tools, and item reference. The content files were compared byte-for-byte with the attached `0.1.2` package before publication.

With Python 3.11 or newer:

```sh
python tools/package.py
python tools/item_list.py
```

Alternatively, Node.js 18 or newer can package the existing assets without Python:

```sh
node tools/package.cjs
```

Both packaging paths write a single content `.hmod` into `dist/`. Texture regeneration is a separate, optional operation requiring Pillow; it is not needed to package the existing artwork.

```sh
python -m pip install pillow
python tools/gen_textures.py content/assets/useful_armory/textures
```

Regeneration overwrites texture assets. Review the changes before committing.

## Repository map

- `content/` — everything loaded from the content mod, including textures and recipes.
- `tools/` — texture generation, packaging, and item documentation.
- `docs/items.md` — item and block reference.
- `docs/ROADMAP.md` — proposed visual, gameplay, and world-generation improvements.
- `docs/VALIDATION.md` — what was checked and what still needs in-game verification.
- `dist/` — downloadable packages and checksums.

## Help improve it

When reporting a bug, include the Horizon revision, content/native mod versions, world preset, whether the chunk is new, and steps to reproduce it. A screenshot or short clip helps for rendering problems.

Ideas are welcome, especially improvements that give the existing gear a purpose before adding more sets. See the [roadmap](docs/ROADMAP.md) for priorities and acceptance checks.




## License

Code, structured gameplay data, and textual documentation are licensed under the [MIT License](LICENSE). The standard license text is from the [Open Source Initiative](https://opensource.org/license/mit).

**Artwork is not MIT-licensed.** Textures, logos, and project-owned visual assets are reserved under the [Artwork License](ARTWORK_LICENSE.md). You may use them while playing the official mod; separate reuse requires permission. Third-party game content in screenshots retains its own rights.

## Screenshots

In-game captures from content version 0.1.5, taken before the ores moved from a cobblestone to a stone background in 0.1.6. See the [screenshot gallery](docs/SCREENSHOTS.md) for captions and full-size files.

![Useful Armory ores and storage blocks](docs/images/ores-and-storage.png)

