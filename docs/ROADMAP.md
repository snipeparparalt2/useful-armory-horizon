# Useful Armory roadmap

**0.1.7 is the current work** and its scope is fixed: see [HANDOFF.md](HANDOFF.md). Everything
after it on this page is a **proposal**. The owner picks what goes in and in which order, and
nothing below gets started before 0.1.7 is released.

Tags: **[data]** content mod only (JSON, structures, loot); **[native]** needs the Rust half;
**[art]** needs new textures or models. Size: S (a day), M (a few days), L (a week or more).

## 0.1.7: gear that does things, places, creatures, trinkets, souls (in progress)

Places and loot, set bonuses, tool abilities, weapon effects and coloured gear light are done but
untested in game. Creatures are partly done: the four new mobs exist as data, and their looks
and behaviours still need native work. Still to come: trinkets, backpacks and waystones; souls,
the soul forge and bosses; the shadow citadel; custom enchantments and armour trims. Details and
status are in [HANDOFF.md](HANDOFF.md).

---

## Proposed 0.1.8 "The Armory": show off, maintain and carry your gear

The mod is called Useful Armory, but there is nowhere to put the armory. This update is about
displaying, maintaining and carrying gear.

| Feature | What it is | Tags | Size |
|---|---|---|---|
| Weapon rack | Wall block that holds three weapons, drawn on the wall; take and put back with a click | data, native, art | M |
| Armour mannequin | Block that wears a full set and swaps it with yours in one click | data, native, art | M |
| Display case | Glass-topped block for a relic or trinket, with a soft light inside | data, native, art | S |
| Material shields | One per set with a small perk: Obsidian ignores some knockback, Aquite works under water, Shadow hides you for a moment after a block | data, native, art | M |
| Material arrows and a quiver | Aquite (slows), Colosifite (sets alight), Shadow (pierces) arrows; a quiver trinket that holds them | data, native, art | M |
| Whetstone and repair kits | A whetstone gives a weapon a short sharpness boost; repair kits mend one set's gear anywhere | data, native, art | S |
| Armorer's Codex | In-game guide book (Horizon's mod screen hook): every set, bonus, ability, ore height and place | native, art | M |
| Ultimate colour cycle | All worn Ultimate pieces cycle colour in step, with a speed setting; the worn armour is static today | native, art | M |

## Proposed 0.1.9 "Bounties and Trades": reasons to visit villages

| Feature | What it is | Tags | Size |
|---|---|---|---|
| Bounty board | Village block with three daily contracts (slay 8 shades, bring 16 colosifite ore, clear a bandit fort) that pay emeralds, relics and trims | data, native, art | L |
| Travelling smith | A rare wandering trader (the wandering-trader template) who sells relics, trim templates, whetstones and rare weapon parts | data, native, art | M |
| Armorsmith trades | The village armory blacksmith's smith trades in mod ingots and buys back worn gear | data, native | S |
| Mini-bosses | Bandit captain (bandit fort), watch captain (colosifite watchtower), drowned admiral (aquite shrine at sea): tougher, named, with a sure relic drop | data, native, art | M |
| Advancements | A Useful Armory advancement tab: first ore of each kind, each full set, each place found, each boss | data | S, if Horizon reads mod advancements (check first) |

## Proposed 0.2.0 "Deep and Far": a place for every material, and the End

| Feature | What it is | Tags | Size |
|---|---|---|---|
| Aquite reef | Warm-ocean ruin overgrown with aquite crystal; the tide lurkers' home | data, art | M |
| Colosifite fissure | A badlands crack with lava falls and rich colosifite seams; ember brutes guard it | data, art | M |
| Shadow rift | Deep dark ruin round a torn rift; shades pour out at night | data, native, art | M |
| A ninth material, from the End | An End-only ore and full set (working name **Astralite**), with a slow-falling set bonus and a void-resistant tool line | data, native, art | L |
| Star forge | End-island structure where Astralite is worked; a hard fight at the top | data, native, art | L |
| Ultimate rework | Ultimate crafted from one ingot of every material, so it becomes the real endgame | data | S |
| Materials in any world | Ore routes for flat and void worlds (a sieve, or trading with the travelling smith), so every world preset has a way to get them | data, native | M |

## Ideas parking lot (not scheduled)

- **Weapon forging**: blades, guards and hilts as separate parts (The Nether's Legacy already works this way) that combine into custom weapons with mixed stats. [data, native, art] L
- **Horse armour per material**: the eight materials as horse armour, with the set colours. [data, art] S
- **Hound armour**: armour for the tamed shadow hound and for wolves. [data, art] S
- **Two-piece bonuses**: a smaller bonus at two pieces, the full one at four; mixed-set combos. [native] M
- **Material identities**: the 0.1.2 roadmap's idea of a play style per set (Quartz fast but fragile, Redstone charge meter, Colosifite charged strike). Fold this into a balance pass once 0.1.7's bonuses are tested. [native] M
- **Sounds**: material hit and break sounds, mob voices, ability sounds. [data, art] M

## How to pick

Each update should be finished and seen working in game before the next one starts, and each
feature should ship with its tooltip, recipe, sound, Codex page and a test checklist. A good
first choice after 0.1.7 is **0.1.8**: it is mostly about the gear players already have.
