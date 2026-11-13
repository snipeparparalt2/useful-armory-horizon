# Places: design brief for the 0.1.7 structures

This is the building design for phase 1 of Useful Armory 0.1.7. The buildings are generated
by Python (`tools/gen_phase1.py` and the modules it imports) into structure `.nbt` files.
Nothing here is built by hand in game.

The bar: these should look like buildings a careful builder made, not boxes. Bigger than the
first pass, layered materials, depth in the walls, real roofs, furnished interiors, signs of
age, light sources, and a reason to walk through every room.

## Ground rules

- Target is Horizon `fdc87ae`, Minecraft data 26.3. Only use block ids and state properties
  that exist there. `tools/structkit.py` validates every block against a schema file when one
  is given (`--schema path/to/block_schema.json`); a build that fails validation is a bug.
- Give every block its full set of state properties (stairs: `facing`, `half`, `shape`,
  `waterlogged`; doors: all five; and so on). The toolkit helpers do this.
- Fences, walls, glass panes and iron bars must have their connection properties set. The
  toolkit computes them in `finalize()`.
- Our own blocks may be used: `useful_armory:aquiteore`, `colosifiteore`, `shadowore`,
  `deepslate_aquite_ore`, `deepslate_colosifite_ore`, `deepslate_shadow_ore`,
  `colosfiteblock`, `shadowblock`, `ultimateblock` (sparingly). The aquite and shadow ores
  glow, so they work as accent lighting.
- No vanilla structures are copied. No command blocks, no structure blocks, no entities in
  the files (armour stands and item frames are entities: leave them out).
- Fire safety: no lava or fire next to wood or wool. Campfires are fine.
- Cells that are never set keep whatever the world has. Surface buildings set air inside and
  just around themselves so terrain and trees do not poke through; underground buildings
  are fully enclosed shells that carve their own air.
- Randomness is seeded per piece (`Piece.rnd`), so the output is byte-identical each run.
- Every chest or barrel with loot uses `Piece.chest(...)` with a loot table name from the
  list below. Every spawner uses `Piece.spawner(...)`.
- Keep each single piece within 48 x 48 blocks horizontally.

## Detailing checklist (apply to every building)

1. **Mixed palettes.** Never one block for a whole wall. Blend 3 to 4 related blocks
   (bricks, cracked, mossy, plain stone, cobble) with weights, heavier wear near the ground
   and near openings.
2. **Wall depth.** Corner pillars or buttresses one block proud of the wall, a plinth course
   at the base, a trim course under the roof, window sills and lintels from stairs and slabs.
3. **Real roofs.** Gabled or hipped from stairs with slab ridges and overhanging eaves, or
   crenellated parapets with walkways. No flat plank lids.
4. **Openings.** Doors (or door frames with one door missing), shuttered windows
   (trapdoors), panes or iron bars, arrow slits on defensive buildings.
5. **Floors.** Patterned: borders, a centre motif, carpets or rugs, a change of material
   between rooms.
6. **Furniture with a purpose.** Each room reads as something: beds for a bunk room, tables
   (fence post plus pressure plate or a slab on a fence), benches (stairs), shelves
   (bookshelves, barrels on their side, `chiseled_bookshelf`), workstations, storage stacks.
7. **Light.** Lanterns hanging from chains or beams, candles, wall torches, soul lanterns
   underground, sea lanterns for water themes. Every room has at least one light unless it
   is meant to be dark.
8. **Age.** Cracks, moss, vines or glow lichen, cobwebs in corners and ceilings, missing
   blocks, rubble piles, a collapsed section where it fits the story.
9. **Surroundings** (surface only). A path to the door, a fence or low wall, a well, woodpile,
   cart, crates, crops or flowers, so the building sits in a place.
10. **A find.** Something off the main path: a chest behind a bookshelf, under a floor
    trapdoor, at the top of a ladder, behind rubble.

## Loot tables (all exist already)

`chests/ruined_forge`, `chests/wanderers_camp`, `chests/aquite_shrine`,
`chests/colosifite_watchtower`, `chests/pigman_outpost`, `chests/shadow_vault`,
`chests/miners_cache`, `chests/forgotten_armory`, `chests/village_blacksmith`.
New ones to add with the new places: `chests/bandit_fort`, `chests/infested_mine`,
`chests/crypt`, `chests/crypt_treasure`.

## Mobs available for spawners

Ours: `useful_armory:vault_guardian`, `useful_armory:tower_sentry` (both zombie-based).
Vanilla, by theme: `minecraft:pillager`, `minecraft:vindicator` (bandits);
`minecraft:spider`, `minecraft:cave_spider`, `minecraft:silverfish` (mine);
`minecraft:skeleton`, `minecraft:zombie`, `minecraft:husk` (crypt);
`minecraft:zombified_piglin`, `minecraft:piglin_brute`, `minecraft:magma_cube` (Nether).
Spawners sit where the player will fight: open floors, not behind walls. Guardian types
burn in daylight, so their spawners are indoors.

## The twelve places

Sizes are targets (width x height x depth); go bigger if the design needs it.

### 1. Ruined forge (surface; forests, plains, meadows) about 19 x 12 x 17
A stone smithy hall that burned out long ago. Two bays: the forge hall and a lean-to store.
Half the gabled roof (dark oak or deepslate tile stairs over spruce beams) has fallen in,
leaving rafters. A square chimney stack rises above the ridge with a blast furnace and
campfire at its base. Inside: anvils, a quench trough (`water_cauldron`), tool wall,
smithing table, bellows suggestion (trapdoors and barrels), coal pile, ingot stacks
(our ore blocks half buried in rubble). Outside: collapsed wall section spilling rubble, an
overgrown cart, woodpile, a path. Loot: one chest in the store, one under rubble in the hall
(`chests/ruined_forge`).

### 2. Wanderer's camp (surface; forests, taiga, savanna, plains, desert) about 21 x 8 x 21
A travellers' camp around a stone fire ring with log and stair seating. Three or four tents
of different wool colours with carpet floors and beds, one larger supply tent with barrels
and crates. A covered wagon (slabs, fences, trapdoor sides, wool cover), a hitching rail,
drying rack, cooking spot with cauldron and smoker, lantern posts, a lookout platform on
log stilts with a ladder, a partial log palisade on one side. Loot: barrel in the supply
tent, chest on the wagon (`chests/wanderers_camp`).

### 3. Aquite shrine (surface; beaches, rivers, swamps) about 21 x 14 x 21
A water shrine on a stepped round platform (three tiers of prismarine with stair edges).
A ring of eight columns, some broken, joined by arches of stairs; a central canopy over an
altar. Water channels cut into the platform run from a central basin to the edge. Aquite ore
inlays glow in the floor and columns; sea lanterns under water in the basin; dark prismarine
trim; a sunken stair leads under the altar to a small flooded reliquary. Loot: altar chest
and reliquary chest (`chests/aquite_shrine`).

### 4. Colosifite watchtower (surface; hills, savanna, badlands) about 17 x 30 x 17
A round-cornered stone tower, 9 to 11 wide, four floors, with a wider overhanging top
(upside-down stairs as machicolations), crenellated walkway and a conical stair roof with a
colosifite block finial and signal fire (campfire) under it. A ruined curtain wall and
gatehouse stub around the base, a stable lean-to, a well. Inside: store room, bunk room,
armoury, lookout; a continuous ladder or wrapped stair; arrow slits with iron bars. Tower
sentry spawner on the bunk and lookout floors. Loot: three chests across floors, best one
at the top (`chests/colosifite_watchtower`).

### 5. Pigman outpost (Nether wastes; placed by height, enclosed) about 23 x 14 x 23
A small nether brick keep: square curtain with four corner turrets, a gate with nether
brick fence portcullis, an inner yard and a two-floor hall. Gold and gilded blackstone
trim, polished blackstone floors, crimson timber details, shroomlights and soul campfires
for light, a lava channel behind nether brick fences, a gold-block throne dais, a treasury
behind iron bars. Because it is placed by height it must look right buried or free: full
outer shell and floor. Spawners: zombified piglin in the yard, piglin brute in the hall.
Loot: hall chest and treasury chest (`chests/pigman_outpost`).

### 6. Shadow vault (underground, Y -52 to -12) about 21 x 11 x 21
A sealed vault: the player digs in. An outer ring corridor (deepslate bricks, tiles,
cracked variants, sculk patches, cobwebs) around an inner sanctum reached through an
iron-bar gate. Sanctum: shadow block pillars, a raised dais with the main chest under a
ceiling of glowing deepslate shadow ore, soul lanterns, candles, crying obsidian accents,
tinted glass. Side alcoves with smaller caches. Two vault guardian spawners: one in the
corridor, one in the sanctum. Loot: `chests/shadow_vault` (main plus two alcoves).

### 7. Miner's cache (underground, Y 0 to 40) about 25 x 9 x 25
A worked-out mine junction: four tunnels meeting at a timbered hub with a hoist frame and a
ladder shaft stub going up. Timber sets (log posts, plank or log caps, fence struts) every
few blocks, rails with gaps, ore showing in the walls (ours plus coal and iron), a tool
room with barrels, crafting table and furnace, a sleeping nook, one tunnel collapsed into
rubble with a cache behind it, puddles, hanging lanterns. Loot: barrels in the tool room and
the cache behind the collapse (`chests/miners_cache`). No spawner: a quiet find.

### 8. Forgotten armory (underground, Y -30 to 20, rare) about 33 x 12 x 25
A buried arsenal. A pillared central hall with a vaulted ceiling (stairs), banners of
coloured wool on the walls, weapon racks suggested with fences, trapdoors and anvils. Four
side rooms: library (bookshelves, lectern), forge (blast furnaces, anvils, cauldrons),
barracks (rows of beds, chests at the feet), treasury behind iron bars with colosifite and
shadow blocks stacked as bullion. A hidden room behind a bookshelf. Vault guardian spawners
in the hall and barracks. Loot: `chests/forgotten_armory` in library, forge, treasury and
the hidden room.

### 9. Armory blacksmith (villages) about 15 x 11 x 13
A proper village smithy that fits beside vanilla houses: stone lower walls, timber-framed
upper walls, gabled spruce roof with eaves, stone chimney with campfire smoke, open-sided
forge porch on fence posts with furnace, blast furnace, anvil, grindstone and water trough.
Shop room with counter, barrels, display shelves, a bed loft up a ladder. Glass pane
windows with shutters, a door, flower pots, a lantern over the door, a path stub to the
street connector. Keep the jigsaw connector exactly as in the current generator
(`minecraft:building_entrance`, at ground level on the front edge, facing out). Loot:
`chests/village_blacksmith`.

### 10. Bandit fort (surface; plains, forests, taiga, savanna; common) about 37 x 16 x 37
A log palisade fort: a stockade of pointed logs (logs topped with fences or walls) with a
gate and two flanking towers, a walkway behind the wall. Inside: a central fire, a
longhouse (bunks, tables, kitchen), a leader's tent on a platform, a cage of iron bars, a
stolen-goods pile (barrels, chests, hay, wool), target dummies (hay plus fences), a lookout
tower. Pillager spawners at the gate and yard, a vindicator spawner in the longhouse; four
spawners in all. Loot: `chests/bandit_fort` in longhouse, leader's tent, goods pile.

### 11. Infested mine (underground, Y -20 to 40; common) about 45 x 14 x 45
A larger abandoned mine overrun by spiders: a main gallery with side drifts on two levels
joined by ladders and a stair ramp, timbering in poor repair, heavy cobwebs, egg-sac
clusters (white wool or bone blocks wrapped in web), ore pockets, broken rails and a
minecart-loading bay, an underground pool. It ends in a wide webbed cavern (the nest) with
the best chest. Spawners: cave spider in the drifts (three), spider in the nest (two),
silverfish in one infested stone-brick section. Loot: `chests/infested_mine` (four).

### 12. Crypt dungeon (underground, Y -10 to 30; common) jigsaw, different every time
Built from pieces joined by jigsaw connectors so each crypt differs.
- **Entrance** (start piece): a descending stair from a small roofed stone entry, ending in
  a vestibule with connectors.
- **Corridors**: straight, corner, T-junction and crossing; 5 wide outside, 3 wide inside,
  arched ceilings, wall niches with skulls (`skeleton_skull`) and candles.
- **Rooms** (each about 11 x 7 x 11 to 15 x 8 x 15): tomb hall with stone coffins, ossuary
  with bone-block walls, chapel with pews and altar, flooded chamber, collapsed chamber,
  guard room with spawner.
- **Treasure room**: exactly one per crypt (`lithostitched:guaranteed`), `chests/crypt_treasure`.
- **Dead ends**: capped corridor ends so nothing opens into rock.
Mobs: skeleton, zombie and vault guardian spawners in rooms. Loot: `chests/crypt` in rooms.
Depth 5. All pieces are fully enclosed shells.
