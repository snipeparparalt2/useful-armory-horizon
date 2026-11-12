Current distribution constraint: one standalone content .hmod; the native lighting companion has been retired. Native-render suggestions below are research notes, not a planned dependency. Unsupported visual features should wait for content-level Horizon support rather than requiring a separate library mod.

# Useful Armory roadmap

This is a proposal for future work, not a list of features already shipped. The published 0.1.2 content stays unchanged while these improvements are designed and tested.

## 1. Ultimate RGB armor — first priority

**Player experience:** Ultimate equipment smoothly cycles red → orange → yellow → green → cyan → blue → purple → red. Every worn piece uses the same phase, so a full set looks intentional rather than like independently blinking parts. Preserve the texture's shading, dark outlines, and material detail while changing the colored metal areas.

Suggested default: a gentle eight-second cycle. Add settings for cycle speed, saturation, brightness, a fixed hue, and animation off. Avoid flashing white transitions. Optional matching glow should be restrained and should use the existing native light budget.

### Implementation plan

1. Make a small prototype using only the Ultimate chestplate. Confirm how the pinned Horizon renderer handles animated equipment textures; do not assume item `.mcmeta` animation automatically works for worn armor.
2. Prefer a content-only animated equipment strip if the renderer supports it. Worn armor frames are rectangular (currently 128×64), so set explicit frame width and height rather than treating the sheet as square item frames.
3. If that route is unsupported, add a narrowly scoped native render hook that chooses a shared hue or animation frame for Useful Armory Ultimate equipment. Keep it separate from the colored-light code: illuminating nearby blocks does not recolor the armor itself.
4. Use one shared world-time phase for the wearer, inventory previews, and remote players. Preserve alpha, shading, damage overlays, and enchantment glint. Avoid per-piece timers that reset when equipment changes.
5. Extend to helmet, chestplate, leggings, boots, item icons, and displayed equipment. Verify player inventory previews, third-person view, armor stands, other players, and mobs wearing the armor.
6. Ship the static current texture as fallback when the native companion is absent. Add synchronization only if a shared world-time phase is insufficient; cosmetic color changes must not affect game stats.

**Acceptance:** a full set cycles smoothly without UV distortion, flicker, color seams, glint loss, or a visible phase reset when swapping pieces. Test mixed sets, rejoining a server, low FPS, and paused single-player. Compare frame time with the feature on and off, including a room full of armor stands. Static-color and animation-off modes must work.

## 2. Give existing materials clear identities

Keep existing item IDs and crafting progression. Review actual stats against vanilla before changing numbers; publish a before/after balance table.

| Family | Proposed identity | First mechanic to prototype |
|---|---|---|
| Aquite | Exploration and underwater utility | Modest underwater mining bonus while wearing a set |
| Colosifite | Heavy impact | Slow charged strike with clear windup and a short cooldown |
| Shadow | Precise late-game offense | Short, limited mobility skill with a visible cooldown |
| Lapis | Enchanting specialist | Better enchanting value rather than raw damage inflation |
| Quartz | Fast, light tools | Faster use with lower durability and readable tradeoffs |
| Redstone | Charged utility | Visible charge meter consumed by a mining burst |
| Emerald | Reliable utility | Efficient repair and a modest durability advantage |
| Obsidian | Defense and endurance | Knockback resistance with a mobility tradeoff |
| Ultimate | Expensive endgame flexibility | RGB identity first; modest configurable set bonus later |

These are candidates, not commitments. Start with two contrasting families and playtest survival progression before expanding. Avoid making one set strictly best at everything.

## 3. Finish signature weapons

- **Daggers:** quick attacks and a carefully bounded positional bonus. Show the condition in the tooltip.
- **Greatswords:** readable windup and a modest sweep; no unavoidable large-area damage.
- **Halberds:** measured reach with slower recovery. Server-side range checks must match the animation.
- **Soul Eater:** earn limited soul charges from eligible kills; spend charges on a small heal or special strike. Cap storage and prevent trivial farming loops.
- **The Nether's Legacy:** a heat mechanic that rewards timing, with clear overheat feedback.
- **Reaper Scythe:** useful crop harvesting and replanting before adding more combat effects; respect protection and tool durability.
- **Tripleslap:** revisit the original three-arrow bow after confirming its content registration, ammunition consumption, durability, cooldowns, enchantments, and server authority. A language entry alone is not an implemented weapon.

For each weapon, implement one complete mechanic with its tooltip, sound, animation, crafting cost, cooldown display, and survival tests before adding a second mechanic.

## 4. Reliable mining and survival progression

The current 0.1.2 source attaches ores only to Overworld biomes. Build a small validation matrix: default terrain, large biomes, amplified/custom terrain if supported, flat with stone layers, void, Nether, and End.

- Verify new-chunk generation, height bands, harvest requirements, drops, smelting, Fortune, and Silk Touch using fixed seeds.
- Add host-appropriate deepslate ore textures and block variants.
- Decide whether Nether/End access means actual dimension-specific deposits or alternative crafting. Do not blindly place stone ore into every dimension.
- Provide a craftable alloy route for worlds without suitable rock. A void or bedrock-only flat world cannot spawn underground ore without additional terrain.
- Add recipe guidance and progression advancements. Document that existing chunks are not automatically changed.

**Acceptance:** every advertised world preset has a tested acquisition path. Save migration retains existing item IDs and does not invalidate placed blocks.

## 5. Presentation and quality of life

- A concise in-game guide for material tiers, repairs, ore heights, and special controls.
- Separate creative tabs only if the single tab becomes difficult to navigate; consistent names and searchable keywords first.
- Subtle material sounds, ability feedback, and restrained particles; settings for particles and dynamic lights.
- Recipes and repair paths for all equipment, plus config options for servers.
- Screenshots and short clips of actual gameplay for the mod page, including a dark scene for glow and a full RGB armor cycle.

## 6. Expand after the existing gear is complete

First expansion candidate: a small ruined forge containing material clues and a useful crafting reward. Follow with a properly implemented Gold Chicken if it fits progression. Larger dungeons, bosses, and dimensions come later because they need substantially more art, AI, world-generation, and compatibility work.

## Suggested release order

1. **Publication and installation:** complete source, trustworthy downloads, clear instructions, and the native-folder error fixed.
2. **RGB visual update:** one polished full-set color cycle, settings, multiplayer checks, and verified native compatibility if required.
3. **Combat and progression update:** two material identities, weapon distinctions, repairs, and acquisition tests.
4. **World expansion:** host-specific ores, forge structure, then new mobs.

Treat each release as complete only when its advertised features have been seen working in-game. Track unfinished ideas separately from released functionality.

