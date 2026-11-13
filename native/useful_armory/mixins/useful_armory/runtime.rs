// Useful Armory, native half: what the content mod's items do beyond data.
//
// - The glow (glowing gear casts real coloured light) is Armory Lib's now: `api/` registers
//   the items with it, and the mod's page in Options > Mods too.
// - Gear that does things (phase 2): full armour sets give bonuses, some tools dig more
//   than one block while sneaking (vein mining, a 3 x 3 wide dig, tree felling), hoes and
//   the reaper scythe harvest and replant an area of grown crops, and weapons have effects
//   (backstabs, splash damage, fire, healing, bonus damage, heads).
//
// This file is the mod's logic with no game in it: which items do what, the geometry, the
// caps, the settings and the little state shared between hooks. It is both the module the
// bundle adds to the game (`game::useful_armory`) and this folder's Cargo library, so
// `cargo test` runs it without the game. `glue.rs` and `gear.rs` read and change the game.

/// The mod's id (Options > Mods; the content mod's id too).
pub const ID: &str = "useful_armory";

/// The content mod's namespace: only its items are looked up.
const NAMESPACE: &str = "useful_armory:";

// ---------------------------------------------------------------------------------------
// Settings: one switch per part, on Options > Mods > Useful Armory.
// ---------------------------------------------------------------------------------------

/// The parts of the mod a player can switch off on its settings page, in the page's order.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Feature {
    SetBonuses,
    VeinMining,
    WideDig,
    TreeFelling,
    HarvestSweep,
    WeaponEffects,
}

impl Feature {
    pub const ALL: [Feature; 6] = [
        Feature::SetBonuses,
        Feature::VeinMining,
        Feature::WideDig,
        Feature::TreeFelling,
        Feature::HarvestSweep,
        Feature::WeaponEffects,
    ];

    /// The setting's file name in the mod's data folder.
    pub fn key(self) -> &'static str {
        match self {
            Feature::SetBonuses => "set_bonuses",
            Feature::VeinMining => "vein_mining",
            Feature::WideDig => "wide_dig",
            Feature::TreeFelling => "tree_felling",
            Feature::HarvestSweep => "harvest_sweep",
            Feature::WeaponEffects => "weapon_effects",
        }
    }

    fn bit(self) -> u32 {
        1 << (self as u32)
    }
}

/// A stored switch: on unless it says `false`.
pub fn read_flag(stored: Option<String>) -> bool {
    stored.is_none_or(|v| v.trim() != "false")
}

/// The switches, one bit per `Feature`, and `LOADED` once read from their files. Shared by
/// every thread: the server thread's hooks read them. The settings page is Armory Lib's, so
/// the files are read again once they are a second old.
static FLAGS: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);
const LOADED: u32 = 1 << 31;
/// When the switches were last read, in milliseconds since the first read.
static READ_AT: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
const FRESH_MS: u64 = 1000;

fn now_ms() -> u64 {
    static START: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
    START.get_or_init(std::time::Instant::now).elapsed().as_millis() as u64
}

/// Whether `feature` is on. Reads every switch through `read` (the setting files) the
/// first time and again once the kept bits are a second old.
pub fn enabled(feature: Feature, read: impl FnMut(&str) -> Option<String>) -> bool {
    enabled_at(feature, now_ms(), read)
}

fn enabled_at(feature: Feature, now: u64, read: impl FnMut(&str) -> Option<String>) -> bool {
    use std::sync::atomic::Ordering;
    let mut read = read;
    let mut flags = FLAGS.load(Ordering::Acquire);
    if flags & LOADED == 0 || now.saturating_sub(READ_AT.load(Ordering::Acquire)) >= FRESH_MS {
        flags = LOADED;
        for f in Feature::ALL {
            if read_flag(read(f.key())) {
                flags |= f.bit();
            }
        }
        FLAGS.store(flags, Ordering::Release);
        READ_AT.store(now, Ordering::Release);
    }
    flags & feature.bit() != 0
}

/// Whether `feature` is on, for the hooks that have no game to read the files with: on until
/// a hook with a game has read them.
pub fn enabled_now(feature: Feature) -> bool {
    let flags = FLAGS.load(std::sync::atomic::Ordering::Acquire);
    flags & LOADED == 0 || flags & feature.bit() != 0
}

/// Whether the mod is on in Options > Mods, as the last server hook with a game saw it, for
/// the hooks with none (damage, knockback).
static MOD_ON: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(true);

pub fn note_mod_on(on: bool) {
    MOD_ON.store(on, std::sync::atomic::Ordering::Release);
}

pub fn mod_on() -> bool {
    MOD_ON.load(std::sync::atomic::Ordering::Acquire)
}

/// The mod's own item id: `useful_armory:souleater` -> `souleater`.
pub fn own(item: &str) -> Option<&str> {
    item.strip_prefix(NAMESPACE)
}

/// A vanilla id without its namespace: `minecraft:zombie` and `zombie` -> `zombie`.
pub fn vanilla(id: &str) -> &str {
    id.strip_prefix("minecraft:").unwrap_or(id)
}

/// Locks shared state, also after a panic elsewhere left the lock poisoned.
fn lock<T>(m: &std::sync::Mutex<T>) -> std::sync::MutexGuard<'_, T> {
    m.lock().unwrap_or_else(std::sync::PoisonError::into_inner)
}

// ---------------------------------------------------------------------------------------
// Armour set bonuses.
// ---------------------------------------------------------------------------------------

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArmorSet {
    Aquite,
    Colosifite,
    Emerald,
    Lapis,
    Obsidian,
    Quartz,
    Redstone,
    Shadow,
    Ultimate,
}

/// Each set's pieces: head, chest, legs, feet (the ids are the content mod's legacy names).
const SETS: &[(ArmorSet, [&str; 4])] = &[
    (ArmorSet::Aquite, ["aquitehelmet", "aquitebody", "aquitelegs", "aquiteboots"]),
    (
        ArmorSet::Colosifite,
        ["colosifitearmorhelmet", "colosifitearmorbody", "colosifitearmorlegs", "colosifitearmorboots"],
    ),
    (
        ArmorSet::Emerald,
        ["emeraldarmorhelmet", "emeraldarmorbody", "emeraldarmorlegs", "emeraldarmorboots"],
    ),
    (ArmorSet::Lapis, ["lapisarmorhelmet", "lapisarmorbody", "lapisarmorlegs", "lapisarmorboots"]),
    (
        ArmorSet::Obsidian,
        ["obsidainarmorhelmet", "obsidainarmorbody", "obsidainarmorlegs", "obsidainarmorboots"],
    ),
    (ArmorSet::Quartz, ["quartzamorhelmet", "quartzamorbody", "quartzamorlegs", "quartzamorboots"]),
    (
        ArmorSet::Redstone,
        ["redstonearmorhelmet", "redstonearmorbody", "redstonearmorlegs", "redstonearmorboots"],
    ),
    (ArmorSet::Shadow, ["shadowhelmet", "shadowbody", "shadowlegs", "shadowboots"]),
    (ArmorSet::Ultimate, ["ultimateahelmet", "ultimateabody", "ultimatealegs", "ultimateaboots"]),
];

/// The set whose four pieces are worn (head, chest, legs, feet), if one is whole.
pub fn armor_set(worn: [Option<&str>; 4]) -> Option<ArmorSet> {
    let worn = worn.map(|w| w.and_then(own));
    SETS.iter()
        .find(|(_, pieces)| (0..4).all(|i| worn[i] == Some(pieces[i])))
        .map(|(set, _)| *set)
}

/// A vanilla effect a set keeps on its wearer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct SetEffect {
    pub id: &'static str,
    /// 0 for level I.
    pub amplifier: u8,
    /// Ticks it is given for, each refresh.
    pub duration: i32,
}

/// How often the set's effects are given again, in player ticks.
pub const EFFECT_REFRESH_TICKS: u64 = 20;
/// An effect's length each time: a little over a refresh, so it never runs out while the
/// set is worn and fades soon after it is taken off.
pub const EFFECT_TICKS: i32 = 60;
/// Night vision flickers in its last 10 seconds (200 ticks): keep it above that.
pub const NIGHT_VISION_TICKS: i32 = 260;

const fn fx(id: &'static str, duration: i32) -> SetEffect {
    SetEffect {
        id,
        amplifier: 0,
        duration,
    }
}

const AQUITE_EFFECTS: &[SetEffect] = &[
    fx("minecraft:water_breathing", EFFECT_TICKS),
    fx("minecraft:dolphins_grace", EFFECT_TICKS),
];
const COLOSIFITE_EFFECTS: &[SetEffect] = &[fx("minecraft:fire_resistance", EFFECT_TICKS)];
const EMERALD_EFFECTS: &[SetEffect] = &[fx("minecraft:luck", EFFECT_TICKS)];
const QUARTZ_EFFECTS: &[SetEffect] = &[fx("minecraft:speed", EFFECT_TICKS)];
const REDSTONE_EFFECTS: &[SetEffect] = &[fx("minecraft:haste", EFFECT_TICKS)];
const SHADOW_EFFECTS: &[SetEffect] = &[fx("minecraft:night_vision", NIGHT_VISION_TICKS)];

/// The effects a set gives (the other bonuses are in the damage and experience hooks).
pub fn set_effects(set: ArmorSet) -> &'static [SetEffect] {
    match set {
        ArmorSet::Aquite => AQUITE_EFFECTS,
        ArmorSet::Colosifite => COLOSIFITE_EFFECTS,
        ArmorSet::Emerald => EMERALD_EFFECTS,
        ArmorSet::Quartz => QUARTZ_EFFECTS,
        ArmorSet::Redstone => REDSTONE_EFFECTS,
        ArmorSet::Shadow => SHADOW_EFFECTS,
        ArmorSet::Lapis | ArmorSet::Obsidian | ArmorSet::Ultimate => &[],
    }
}

/// Ultimate: one health point (half a heart) back every 4 seconds.
pub const ULTIMATE_REGEN_TICKS: u64 = 80;
pub const ULTIMATE_REGEN_HEALTH: f32 = 1.0;
/// Obsidian: the share of a knockback that still pushes.
pub const OBSIDIAN_KNOCKBACK_TAKEN: f64 = 0.5;
/// Obsidian: the share of an explosion's damage that still hurts.
pub const OBSIDIAN_EXPLOSION_TAKEN: f32 = 0.5;
/// Lapis: experience picked up is worth this much more.
pub const LAPIS_EXPERIENCE_BONUS: f32 = 0.25;

/// What a set does to damage its wearer is about to take.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum DamageChange {
    Keep,
    Cancel,
    Scale(f32),
}

/// Damage types that count as falling (vanilla's `#minecraft:is_fall`).
const FALL: &[&str] = &["fall", "stalagmite", "ender_pearl"];
/// Damage types that count as explosions (vanilla's `#minecraft:is_explosion`).
const EXPLOSION: &[&str] = &[
    "explosion",
    "player_explosion",
    "bad_respawn_point",
    "fireworks",
    "fireball",
    "wither_skull",
];

pub fn incoming_damage(set: ArmorSet, damage_type: &str) -> DamageChange {
    let kind = vanilla(damage_type);
    match set {
        ArmorSet::Ultimate if FALL.contains(&kind) => DamageChange::Cancel,
        ArmorSet::Obsidian if EXPLOSION.contains(&kind) => {
            DamageChange::Scale(OBSIDIAN_EXPLOSION_TAKEN)
        }
        _ => DamageChange::Keep,
    }
}

/// The extra experience points for `points` picked up with the lapis set, carrying the
/// fractions in `carry` so the bonus is exactly a quarter over time.
pub fn lapis_bonus(points: i32, carry: &mut f32) -> i32 {
    if points <= 0 {
        return 0;
    }
    let total = points as f32 * LAPIS_EXPERIENCE_BONUS + *carry;
    let whole = total.floor();
    *carry = total - whole;
    whole as i32
}

/// A player as the server's player tick last saw them: what the hooks without a game (damage,
/// knockback) and the experience hook need to know about the wearer.
#[derive(Clone, Debug)]
pub struct Wearer {
    pub uuid: u128,
    pub entity: i32,
    pub set: Option<ArmorSet>,
    /// Their player ticks counted since they were first seen.
    pub ticks: u64,
    pub xp_carry: f32,
    seen: std::time::Instant,
}

/// A wearer not seen for this long (left, died) is no longer trusted.
const WEARER_STALE: std::time::Duration = std::time::Duration::from_secs(2);
const MAX_WEARERS: usize = 256;

static WEARERS: std::sync::Mutex<Vec<Wearer>> = std::sync::Mutex::new(Vec::new());

/// The player tick of `uuid`: keeps their entity id and set, and counts their ticks.
/// Returns the set they had at their last tick and this tick's count.
pub fn note_wearer(uuid: u128, entity: i32, set: Option<ArmorSet>) -> (Option<ArmorSet>, u64) {
    let now = std::time::Instant::now();
    let mut all = lock(&WEARERS);
    all.retain(|w| w.uuid == uuid || now.duration_since(w.seen) < WEARER_STALE * 30);
    if let Some(w) = all.iter_mut().find(|w| w.uuid == uuid) {
        let before = if now.duration_since(w.seen) < WEARER_STALE {
            w.set
        } else {
            None
        };
        w.entity = entity;
        w.set = set;
        w.ticks += 1;
        w.seen = now;
        return (before, w.ticks);
    }
    if all.len() >= MAX_WEARERS {
        all.remove(0);
    }
    all.push(Wearer {
        uuid,
        entity,
        set,
        ticks: 1,
        xp_carry: 0.0,
        seen: now,
    });
    (None, 1)
}

/// The set the player with entity id `entity` wears.
pub fn set_of_entity(entity: i32) -> Option<ArmorSet> {
    if entity <= 0 {
        return None;
    }
    let now = std::time::Instant::now();
    lock(&WEARERS)
        .iter()
        .find(|w| w.entity == entity && now.duration_since(w.seen) < WEARER_STALE)
        .and_then(|w| w.set)
}

/// Runs `f` on the player `uuid`'s record, if they were seen lately.
pub fn with_wearer<T>(uuid: u128, f: impl FnOnce(&mut Wearer) -> T) -> Option<T> {
    let now = std::time::Instant::now();
    lock(&WEARERS)
        .iter_mut()
        .find(|w| w.uuid == uuid && now.duration_since(w.seen) < WEARER_STALE)
        .map(f)
}

// ---------------------------------------------------------------------------------------
// Tool abilities.
// ---------------------------------------------------------------------------------------

/// What a tool does to the blocks around the one broken, while its holder sneaks.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ability {
    /// Breaks the ore blocks of the same kind connected to a broken ore.
    VeinMine,
    /// Breaks the 3 x 3 square around the broken block, facing the player.
    WideDig,
    /// Breaks the logs connected to and above a broken log.
    FellTree,
}

impl Ability {
    pub fn feature(self) -> Feature {
        match self {
            Ability::VeinMine => Feature::VeinMining,
            Ability::WideDig => Feature::WideDig,
            Ability::FellTree => Feature::TreeFelling,
        }
    }
}

pub fn tool_ability(item: &str) -> Option<Ability> {
    match own(item)? {
        "colosifitepickaxe" | "emeraldpickaxe" | "shadowpickaxe" => Some(Ability::VeinMine),
        "obsidianpickaxe" | "obsidianshovel" => Some(Ability::WideDig),
        "aquiteaxe" | "emeraldaxe" | "shadowaxe" => Some(Ability::FellTree),
        _ => None,
    }
}

/// Most extra blocks one break takes with each ability.
pub const VEIN_MAX: usize = 32;
pub const TREE_MAX: usize = 64;

/// The block tags that make a block an ore.
pub const ORE_TAGS: &[&str] = &[
    "c:ores",
    "minecraft:coal_ores",
    "minecraft:copper_ores",
    "minecraft:iron_ores",
    "minecraft:gold_ores",
    "minecraft:redstone_ores",
    "minecraft:lapis_ores",
    "minecraft:diamond_ores",
    "minecraft:emerald_ores",
];

/// The content mod's ores, which no ore tag lists.
const MOD_ORES: &[&str] = &[
    "aquiteore",
    "colosifiteore",
    "shadowore",
    "deepslate_aquite_ore",
    "deepslate_colosifite_ore",
    "deepslate_shadow_ore",
];

pub fn is_mod_ore(block: &str) -> bool {
    own(block).is_some_and(|b| MOD_ORES.contains(&b))
}

/// An ore by its name, for when the tags can't be read.
pub fn looks_like_ore(block: &str) -> bool {
    is_mod_ore(block) || block.ends_with("_ore")
}

/// A log by its name, for when the tags can't be read.
pub fn looks_like_log(block: &str) -> bool {
    ["_log", "_stem", "_wood", "_hyphae"]
        .iter()
        .any(|end| block.ends_with(end))
        && !block.contains("stripped_")
}

/// What makes two ores one vein: the same ore, deepslate or not (`minecraft:deepslate_iron_ore`
/// and `minecraft:iron_ore`; the mod's `aquiteore` and `deepslate_aquite_ore`).
pub fn vein_kind(block: &str) -> String {
    let (ns, path) = block.split_once(':').unwrap_or(("minecraft", block));
    let path = path.strip_prefix("deepslate_").unwrap_or(path);
    format!("{ns}:{}", path.replace('_', ""))
}

/// The 26 blocks around a block (faces, edges and corners).
pub fn around() -> impl Iterator<Item = [i32; 3]> {
    (-1..=1)
        .flat_map(|x| (-1..=1).flat_map(move |y| (-1..=1).map(move |z| [x, y, z])))
        .filter(|d| *d != [0, 0, 0])
}

/// The blocks connected to `origin` through its 26 neighbours that `accept` takes, nearest
/// first, at most `max`, without `origin` itself.
pub fn flood(
    origin: [i32; 3],
    max: usize,
    mut accept: impl FnMut([i32; 3]) -> bool,
) -> Vec<[i32; 3]> {
    let mut seen = std::collections::HashSet::from([origin]);
    let mut queue = std::collections::VecDeque::from([origin]);
    let mut found = Vec::new();
    while let Some(at) = queue.pop_front() {
        for d in around() {
            let p = [at[0] + d[0], at[1] + d[1], at[2] + d[2]];
            if !seen.insert(p) || !accept(p) {
                continue;
            }
            found.push(p);
            if found.len() >= max {
                return found;
            }
            queue.push_back(p);
        }
    }
    found
}

/// An axis of the world: the one a wide dig's square faces along.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Axis {
    X,
    Y,
    Z,
}

/// The face of `block` that `point` (where the player's view meets it) lies on, as its axis.
pub fn hit_axis(block: [i32; 3], point: [f64; 3]) -> Option<Axis> {
    let mut best: Option<(f64, Axis)> = None;
    for (i, axis) in [Axis::X, Axis::Y, Axis::Z].into_iter().enumerate() {
        let f = point[i] - f64::from(block[i]);
        if !(-0.01..=1.01).contains(&f) {
            return None;
        }
        let off = f.abs().min((1.0 - f).abs());
        if best.is_none_or(|(b, _)| off < b) {
            best = Some((off, axis));
        }
    }
    best.filter(|(off, _)| *off < 0.01).map(|(_, axis)| axis)
}

/// The axis a player looks along (yaw 0 faces south, +Z; 90 west, -X): up or down past 45
/// degrees, else the nearer horizontal one.
pub fn look_axis(yaw: f32, pitch: f32) -> Axis {
    if pitch.abs() > 45.0 {
        return Axis::Y;
    }
    let r = yaw.to_radians();
    if r.sin().abs() > r.cos().abs() {
        Axis::X
    } else {
        Axis::Z
    }
}

/// The eight blocks of the 3 x 3 square around `origin`, across `axis`.
pub fn square(origin: [i32; 3], axis: Axis) -> Vec<[i32; 3]> {
    let mut out = Vec::with_capacity(8);
    for a in -1..=1 {
        for b in -1..=1 {
            if a == 0 && b == 0 {
                continue;
            }
            let [x, y, z] = origin;
            out.push(match axis {
                Axis::X => [x, y + a, z + b],
                Axis::Y => [x + a, y, z + b],
                Axis::Z => [x + a, y + b, z],
            });
        }
    }
    out
}

/// Whether a tool with `max` durability (0: it never wears), `damage` taken, can spend more
/// and still keep more than `keep` points.
pub fn spare_durability(max: u32, damage: u32, keep: u32) -> bool {
    max == 0 || max.saturating_sub(damage) > keep
}

/// While extra blocks are broken: their breaks call the break hook again, which must leave
/// them alone.
static BREAKING: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

/// Marks extra blocks being broken until it is dropped; None when that is already so.
pub struct Breaking(());

impl Breaking {
    pub fn start() -> Option<Breaking> {
        (!BREAKING.swap(true, std::sync::atomic::Ordering::AcqRel)).then_some(Breaking(()))
    }
}

impl Drop for Breaking {
    fn drop(&mut self) {
        BREAKING.store(false, std::sync::atomic::Ordering::Release);
    }
}

/// Whether extra blocks are being broken now.
pub fn breaking() -> bool {
    BREAKING.load(std::sync::atomic::Ordering::Acquire)
}

// ---------------------------------------------------------------------------------------
// Harvest sweep.
// ---------------------------------------------------------------------------------------

/// How far from the clicked crop a hoe harvests: 1 for the 3 x 3 square, 2 for 5 x 5.
pub fn harvest_radius(item: &str) -> Option<i32> {
    match own(item)? {
        "aquitehoe" | "colosifitehoe" | "emeraldhoe" | "lapishoe" | "obsidianhoe"
        | "quartzhoe" | "redstonehoe" | "shadowhoe" => Some(1),
        "reaperscyth" => Some(2),
        _ => None,
    }
}

/// A crop a hoe harvests: its block, its grown `age` and what is planted again.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Crop {
    pub block: &'static str,
    pub grown: u8,
    pub seed: &'static str,
}

const CROPS: &[Crop] = &[
    Crop {
        block: "minecraft:wheat",
        grown: 7,
        seed: "minecraft:wheat_seeds",
    },
    Crop {
        block: "minecraft:carrots",
        grown: 7,
        seed: "minecraft:carrot",
    },
    Crop {
        block: "minecraft:potatoes",
        grown: 7,
        seed: "minecraft:potato",
    },
    Crop {
        block: "minecraft:beetroots",
        grown: 3,
        seed: "minecraft:beetroot_seeds",
    },
    Crop {
        block: "minecraft:nether_wart",
        grown: 3,
        seed: "minecraft:nether_wart",
    },
];

pub fn crop(block: &str) -> Option<&'static Crop> {
    CROPS.iter().find(|c| c.block == block)
}

/// Whether a crop with the `age` property `age` is fully grown.
pub fn grown(crop: &Crop, age: Option<&str>) -> bool {
    age.and_then(|a| a.trim().parse::<u8>().ok())
        .is_some_and(|a| a >= crop.grown)
}

/// The blocks of the square of `radius` around `center` on its level, `center` first.
pub fn field(center: [i32; 3], radius: i32) -> Vec<[i32; 3]> {
    let mut out = vec![center];
    for dx in -radius..=radius {
        for dz in -radius..=radius {
            if dx != 0 || dz != 0 {
                out.push([center[0] + dx, center[1], center[2] + dz]);
            }
        }
    }
    out
}

/// Takes one `seed` out of a harvest's drops (item, count), for replanting: whether there was
/// one.
pub fn take_one<'a>(drops: impl IntoIterator<Item = (&'a str, &'a mut u32)>, seed: &str) -> bool {
    for (item, count) in drops {
        if item == seed && *count > 0 {
            *count -= 1;
            return true;
        }
    }
    false
}

// ---------------------------------------------------------------------------------------
// Weapon effects.
// ---------------------------------------------------------------------------------------

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Weapon {
    Dagger,
    Greatsword,
    MagmaSword,
    SoulEater,
    PigmanSword,
    NetherLegacy,
    ReaperScythe,
}

pub fn weapon(item: &str) -> Option<Weapon> {
    let id = own(item)?;
    Some(match id {
        "lavasword" => Weapon::MagmaSword,
        "souleater" => Weapon::SoulEater,
        "pigmansword" => Weapon::PigmanSword,
        "thenetherlegacy" => Weapon::NetherLegacy,
        "reaperscyth" => Weapon::ReaperScythe,
        _ if id.ends_with("dagger") => Weapon::Dagger,
        _ if id.ends_with("greatsword") => Weapon::Greatsword,
        _ => return None,
    })
}

/// A dagger's hit from behind does this much.
pub const BACKSTAB_MULTIPLIER: f32 = 2.0;
/// Behind means within this many degrees of straight behind the target's facing.
pub const BACKSTAB_DEGREES: f64 = 60.0;
/// A greatsword's hit also hurts the other mobs this close to its target (blocks)...
pub const SPLASH_RADIUS: f64 = 1.5;
/// ... for this share of the hit.
pub const SPLASH_SHARE: f32 = 0.5;
/// The magma sword sets its target burning for this long (4 seconds).
pub const MAGMA_FIRE_TICKS: i32 = 80;
/// The soul eater gives its wielder this much health per kill (one heart).
pub const SOUL_EATER_HEAL: f32 = 2.0;
/// The pigman sword against the piglin family, and the nether's legacy in the Nether.
pub const PIGMAN_MULTIPLIER: f32 = 1.5;
pub const NETHER_LEGACY_MULTIPLIER: f32 = 1.5;

const PIGLIN_FAMILY: &[&str] = &["piglin", "piglin_brute", "hoglin", "zoglin", "zombified_piglin"];

/// Whether the attacker at `attacker` stands behind a target at `target` that faces `view`:
/// within `BACKSTAB_DEGREES` of straight behind it, on the ground plane.
pub fn behind(target: [f64; 3], view: [f64; 3], attacker: [f64; 3]) -> bool {
    let (fx, fz) = (view[0], view[2]);
    let (ax, az) = (attacker[0] - target[0], attacker[2] - target[2]);
    let (lf, la) = ((fx * fx + fz * fz).sqrt(), (ax * ax + az * az).sqrt());
    if lf < 1e-6 || la < 1e-6 {
        return false;
    }
    // The angle between "behind the target" (-facing) and the way to the attacker.
    let cos = -(fx * ax + fz * az) / (lf * la);
    cos >= BACKSTAB_DEGREES.to_radians().cos() - 1e-9
}

/// What a hit by `weapon` on a mob of type `kind` is multiplied by.
pub fn hit_multiplier(weapon: Weapon, kind: &str, in_nether: bool, from_behind: bool) -> f32 {
    match weapon {
        Weapon::Dagger if from_behind => BACKSTAB_MULTIPLIER,
        Weapon::PigmanSword if PIGLIN_FAMILY.contains(&vanilla(kind)) => PIGMAN_MULTIPLIER,
        Weapon::NetherLegacy if in_nether => NETHER_LEGACY_MULTIPLIER,
        _ => 1.0,
    }
}

/// The head a reaper scythe's kill may drop, and the chance.
pub fn reaper_head(kind: &str) -> Option<(&'static str, f32)> {
    match vanilla(kind) {
        "zombie" => Some(("minecraft:zombie_head", 0.10)),
        "skeleton" => Some(("minecraft:skeleton_skull", 0.10)),
        "creeper" => Some(("minecraft:creeper_head", 0.10)),
        "wither_skeleton" => Some(("minecraft:wither_skeleton_skull", 0.05)),
        _ => None,
    }
}

/// A greatsword's hit that landed: its splash is dealt in the attacker's next player tick,
/// once the hit is over.
#[derive(Clone, Debug, PartialEq)]
pub struct Splash {
    pub attacker: u128,
    pub victim: u32,
    pub at: [f64; 3],
    pub amount: f32,
}

/// A few of each are ever waiting; more means something never picked them up.
const MAX_WAITING: usize = 64;

/// A greatsword hit being dealt: its target, its damage and where the target stands.
static HITS: std::sync::Mutex<Vec<(u32, f32, [f64; 3])>> = std::sync::Mutex::new(Vec::new());
static SPLASHES: std::sync::Mutex<Vec<Splash>> = std::sync::Mutex::new(Vec::new());
/// Mobs a reaper scythe killed whose head drops with their loot.
static HEADS: std::sync::Mutex<Vec<(u32, &'static str)>> = std::sync::Mutex::new(Vec::new());

fn push_capped<T>(list: &mut Vec<T>, item: T) {
    if list.len() >= MAX_WAITING {
        list.remove(0);
    }
    list.push(item);
}

/// The damage hook: a greatsword is about to hit `victim` at `at` for `amount`.
pub fn note_hit(victim: u32, amount: f32, at: [f64; 3]) {
    let mut hits = lock(&HITS);
    hits.retain(|(v, _, _)| *v != victim);
    push_capped(&mut hits, (victim, amount, at));
}

/// The hit on `victim` landed (the weapon's hurt-enemy hook): its damage and where.
pub fn take_hit(victim: u32) -> Option<(f32, [f64; 3])> {
    let mut hits = lock(&HITS);
    let i = hits.iter().position(|(v, _, _)| *v == victim)?;
    let (_, amount, at) = hits.remove(i);
    Some((amount, at))
}

pub fn queue_splash(splash: Splash) {
    push_capped(&mut lock(&SPLASHES), splash);
}

/// The splashes waiting for `attacker`'s player tick.
pub fn take_splashes(attacker: u128) -> Vec<Splash> {
    let mut all = lock(&SPLASHES);
    let (mine, rest) = std::mem::take(&mut *all)
        .into_iter()
        .partition(|s| s.attacker == attacker);
    *all = rest;
    mine
}

/// Whether a mob standing at `at` is caught by a splash around `center`.
pub fn in_splash(center: [f64; 3], at: [f64; 3]) -> bool {
    let d2: f64 = (0..3).map(|i| (at[i] - center[i]).powi(2)).sum();
    d2 <= SPLASH_RADIUS * SPLASH_RADIUS
}

/// A reaper scythe killed mob `entity`: `head` drops with its loot.
pub fn note_head(entity: u32, head: &'static str) {
    push_capped(&mut lock(&HEADS), (entity, head));
}

/// The head mob `entity`'s loot gets, once.
pub fn take_head(entity: u32) -> Option<&'static str> {
    let mut heads = lock(&HEADS);
    let i = heads.iter().position(|(e, _)| *e == entity)?;
    Some(heads.remove(i).1)
}

#[cfg(test)]
mod tests {
    use super::*;

    // ---- Phase 2 ----

    fn ua(id: &str) -> String {
        format!("useful_armory:{id}")
    }

    #[test]
    fn settings_read_on_unless_false_and_label() {
        assert!(read_flag(None));
        assert!(read_flag(Some("true".into())));
        assert!(!read_flag(Some(" false\n".into())));
        let keys: std::collections::HashSet<_> = Feature::ALL.iter().map(|f| f.key()).collect();
        assert_eq!(keys.len(), Feature::ALL.len());
    }

    #[test]
    fn settings_load_and_refresh() {
        // Only this test touches the switches.
        let mut asked = 0;
        assert!(!enabled_at(Feature::WideDig, 5_000, |k| {
            asked += 1;
            (k == "wide_dig").then(|| "false".to_owned())
        }));
        assert_eq!(asked, Feature::ALL.len());
        assert!(enabled_at(Feature::VeinMining, 5_500, |_| panic!("read again too soon")));
        assert!(!enabled_now(Feature::WideDig));
        // A second on, the page's change is picked up.
        assert!(enabled_at(Feature::WideDig, 6_000, |_| None));
        assert!(enabled_now(Feature::WideDig));
    }

    #[test]
    fn whole_sets_only() {
        let set = |ids: [&str; 4]| {
            let ids = ids.map(ua);
            armor_set([Some(&ids[0]), Some(&ids[1]), Some(&ids[2]), Some(&ids[3])])
        };
        assert_eq!(set(["aquitehelmet", "aquitebody", "aquitelegs", "aquiteboots"]), Some(ArmorSet::Aquite));
        assert_eq!(
            set(["obsidainarmorhelmet", "obsidainarmorbody", "obsidainarmorlegs", "obsidainarmorboots"]),
            Some(ArmorSet::Obsidian)
        );
        assert_eq!(
            set(["quartzamorhelmet", "quartzamorbody", "quartzamorlegs", "quartzamorboots"]),
            Some(ArmorSet::Quartz)
        );
        assert_eq!(
            set(["ultimateahelmet", "ultimateabody", "ultimatealegs", "ultimateaboots"]),
            Some(ArmorSet::Ultimate)
        );
        // Mixed, out of place, incomplete or vanilla.
        assert_eq!(set(["aquitehelmet", "shadowbody", "aquitelegs", "aquiteboots"]), None);
        assert_eq!(set(["aquitebody", "aquitehelmet", "aquitelegs", "aquiteboots"]), None);
        let h = ua("shadowhelmet");
        assert_eq!(armor_set([Some(&h), None, None, None]), None);
        assert_eq!(
            armor_set([Some("shadowhelmet"), Some("shadowbody"), Some("shadowlegs"), Some("shadowboots")]),
            None
        );
        // Every set's pieces are distinct items.
        let all: std::collections::HashSet<_> = SETS.iter().flat_map(|(_, p)| p.iter()).collect();
        assert_eq!(all.len(), SETS.len() * 4);
    }

    #[test]
    fn set_effects_and_damage() {
        assert!(set_effects(ArmorSet::Shadow)[0].duration > 200);
        assert!(set_effects(ArmorSet::Aquite).iter().any(|e| e.id == "minecraft:water_breathing"));
        for (set, _) in SETS {
            for e in set_effects(*set) {
                assert!(e.id.starts_with("minecraft:"));
                assert!(e.duration as u64 > EFFECT_REFRESH_TICKS);
            }
        }
        assert_eq!(incoming_damage(ArmorSet::Ultimate, "minecraft:fall"), DamageChange::Cancel);
        assert_eq!(incoming_damage(ArmorSet::Ultimate, "minecraft:explosion"), DamageChange::Keep);
        assert_eq!(
            incoming_damage(ArmorSet::Obsidian, "minecraft:player_explosion"),
            DamageChange::Scale(OBSIDIAN_EXPLOSION_TAKEN)
        );
        assert_eq!(incoming_damage(ArmorSet::Obsidian, "minecraft:fall"), DamageChange::Keep);
        assert_eq!(incoming_damage(ArmorSet::Quartz, "minecraft:fall"), DamageChange::Keep);
    }

    #[test]
    fn lapis_gives_a_quarter_more_over_time() {
        let mut carry = 0.0;
        let total: i32 = (0..100).map(|_| lapis_bonus(1, &mut carry)).sum();
        assert_eq!(total, 25);
        assert_eq!(lapis_bonus(8, &mut 0.0), 2);
        assert_eq!(lapis_bonus(0, &mut carry), 0);
        assert_eq!(lapis_bonus(-5, &mut carry), 0);
    }

    #[test]
    fn wearers_are_found_by_entity_and_uuid() {
        let uuid = 0xfeed_u128;
        assert_eq!(note_wearer(uuid, 9001, Some(ArmorSet::Lapis)), (None, 1));
        assert_eq!(set_of_entity(9001), Some(ArmorSet::Lapis));
        assert_eq!(note_wearer(uuid, 9001, None), (Some(ArmorSet::Lapis), 2));
        assert_eq!(set_of_entity(9001), None);
        assert_eq!(with_wearer(uuid, |w| w.ticks), Some(2));
        assert_eq!(with_wearer(0xbeef, |w| w.ticks), None);
    }

    #[test]
    fn tools_and_their_abilities() {
        assert_eq!(tool_ability(&ua("shadowpickaxe")), Some(Ability::VeinMine));
        assert_eq!(tool_ability(&ua("obsidianshovel")), Some(Ability::WideDig));
        assert_eq!(tool_ability(&ua("emeraldaxe")), Some(Ability::FellTree));
        assert_eq!(tool_ability(&ua("aquitepickaxe")), None);
        assert_eq!(tool_ability("minecraft:diamond_pickaxe"), None);
        assert_eq!(Ability::WideDig.feature(), Feature::WideDig);
    }

    #[test]
    fn ores_logs_and_veins() {
        assert!(is_mod_ore("useful_armory:deepslate_shadow_ore"));
        assert!(!is_mod_ore("useful_armory:shadowblock"));
        assert!(looks_like_ore("minecraft:iron_ore") && looks_like_ore("useful_armory:aquiteore"));
        assert!(!looks_like_ore("minecraft:stone"));
        assert!(looks_like_log("minecraft:oak_log") && looks_like_log("minecraft:crimson_stem"));
        assert!(!looks_like_log("minecraft:stripped_oak_log") && !looks_like_log("minecraft:oak_planks"));
        assert_eq!(vein_kind("minecraft:deepslate_iron_ore"), vein_kind("minecraft:iron_ore"));
        assert_eq!(vein_kind("useful_armory:deepslate_aquite_ore"), vein_kind("useful_armory:aquiteore"));
        assert_ne!(vein_kind("minecraft:gold_ore"), vein_kind("minecraft:nether_gold_ore"));
        assert_ne!(vein_kind("minecraft:iron_ore"), vein_kind("minecraft:copper_ore"));
    }

    #[test]
    fn flood_follows_26_neighbours_and_stops_at_the_cap() {
        assert_eq!(around().count(), 26);
        // A diagonal line is connected through corners.
        let line: Vec<[i32; 3]> = (1..=5).map(|i| [i, i, i]).collect();
        let found = flood([0, 0, 0], 32, |p| line.contains(&p));
        assert_eq!(found, line);
        // A solid 5x5x5 cube is cut at the cap, nearest first.
        let cube = |p: [i32; 3]| p.iter().all(|c| (-2..=2).contains(c));
        let found = flood([0, 0, 0], 32, cube);
        assert_eq!(found.len(), 32);
        assert!(found[..26].iter().all(|p| p.iter().all(|c| c.abs() <= 1)));
        assert!(!found.contains(&[0, 0, 0]));
        let mut unique = found.clone();
        unique.sort();
        unique.dedup();
        assert_eq!(unique.len(), found.len());
        // Logs above only.
        let origin = [0, 64, 0];
        let trunk = |p: [i32; 3]| p[0] == 0 && p[2] == 0 && (60..70).contains(&p[1]) && p[1] >= origin[1];
        assert_eq!(flood(origin, TREE_MAX, trunk).len(), 5);
        assert!(flood(origin, 32, |_| false).is_empty());
    }

    #[test]
    fn wide_dig_square_faces_the_player() {
        assert_eq!(hit_axis([3, 64, 5], [3.5, 65.0, 5.2]), Some(Axis::Y));
        assert_eq!(hit_axis([3, 64, 5], [4.0, 64.5, 5.5]), Some(Axis::X));
        assert_eq!(hit_axis([-3, 64, -5], [-2.3, 64.5, -5.0]), Some(Axis::Z));
        assert_eq!(hit_axis([3, 64, 5], [3.5, 64.5, 5.5]), None);
        assert_eq!(hit_axis([3, 64, 5], [9.0, 64.0, 5.5]), None);
        assert_eq!(look_axis(0.0, 10.0), Axis::Z);
        assert_eq!(look_axis(90.0, -20.0), Axis::X);
        assert_eq!(look_axis(-135.0, 0.0), Axis::Z);
        assert_eq!(look_axis(30.0, 80.0), Axis::Y);
        for axis in [Axis::X, Axis::Y, Axis::Z] {
            let sq = square([0, 64, 0], axis);
            assert_eq!(sq.len(), 8);
            assert!(!sq.contains(&[0, 64, 0]));
            let fixed = match axis {
                Axis::X => 0,
                Axis::Y => 1,
                Axis::Z => 2,
            };
            assert!(sq.iter().all(|p| p[fixed] == [0, 64, 0][fixed]));
        }
    }

    #[test]
    fn durability_is_kept() {
        assert!(spare_durability(0, 0, 2));
        assert!(spare_durability(100, 97, 2));
        assert!(!spare_durability(100, 98, 2));
        assert!(!spare_durability(100, 120, 1));
    }

    #[test]
    fn breaking_guard_is_not_reentrant() {
        let first = Breaking::start();
        assert!(first.is_some() && breaking());
        assert!(Breaking::start().is_none());
        drop(first);
        assert!(!breaking());
        assert!(Breaking::start().is_some());
    }

    #[test]
    fn hoes_harvest_grown_crops() {
        assert_eq!(harvest_radius(&ua("obsidianhoe")), Some(1));
        assert_eq!(harvest_radius(&ua("reaperscyth")), Some(2));
        assert_eq!(harvest_radius("minecraft:iron_hoe"), None);
        let wheat = crop("minecraft:wheat").unwrap();
        assert!(grown(wheat, Some("7")) && !grown(wheat, Some("6")) && !grown(wheat, None));
        assert!(grown(crop("minecraft:beetroots").unwrap(), Some("3")));
        assert!(crop("minecraft:pumpkin_stem").is_none());
        assert_eq!(field([0, 64, 0], 1).len(), 9);
        assert_eq!(field([0, 64, 0], 2).len(), 25);
        assert_eq!(field([4, 64, 4], 2)[0], [4, 64, 4]);
        let mut drops = vec![("minecraft:wheat".to_owned(), 1u32), ("minecraft:wheat_seeds".to_owned(), 2)];
        assert!(take_one(drops.iter_mut().map(|(i, c)| (i.as_str(), c)), "minecraft:wheat_seeds"));
        assert_eq!(drops[1].1, 1);
        assert!(!take_one(drops.iter_mut().map(|(i, c)| (i.as_str(), c)), "minecraft:carrot"));
    }

    #[test]
    fn weapons_and_their_effects() {
        assert_eq!(weapon(&ua("shadowdagger")), Some(Weapon::Dagger));
        assert_eq!(weapon(&ua("colosifitegreatsword")), Some(Weapon::Greatsword));
        assert_eq!(weapon(&ua("lavasword")), Some(Weapon::MagmaSword));
        assert_eq!(weapon(&ua("reaperscyth")), Some(Weapon::ReaperScythe));
        assert_eq!(weapon(&ua("shadowsword")), None);
        assert_eq!(weapon("minecraft:iron_sword"), None);
        assert_eq!(hit_multiplier(Weapon::Dagger, "minecraft:zombie", false, true), 2.0);
        assert_eq!(hit_multiplier(Weapon::Dagger, "minecraft:zombie", false, false), 1.0);
        assert_eq!(hit_multiplier(Weapon::PigmanSword, "zombified_piglin", false, false), 1.5);
        assert_eq!(hit_multiplier(Weapon::PigmanSword, "minecraft:zombie", true, false), 1.0);
        assert_eq!(hit_multiplier(Weapon::NetherLegacy, "minecraft:zombie", true, false), 1.5);
        assert_eq!(hit_multiplier(Weapon::NetherLegacy, "minecraft:zombie", false, true), 1.0);
        assert_eq!(reaper_head("minecraft:wither_skeleton"), Some(("minecraft:wither_skeleton_skull", 0.05)));
        assert_eq!(reaper_head("minecraft:spider"), None);
    }

    #[test]
    fn backstab_is_within_60_degrees_of_behind() {
        // The target at the origin faces south (+Z): behind it is north (-Z).
        let (t, view) = ([0.0, 64.0, 0.0], [0.0, -0.3, 1.0]);
        assert!(behind(t, view, [0.0, 64.0, -2.0]));
        let at = |deg: f64| {
            let r = deg.to_radians();
            [2.0 * r.sin(), 64.0, -2.0 * r.cos()]
        };
        assert!(behind(t, view, at(59.0)) && behind(t, view, at(-59.0)));
        assert!(!behind(t, view, at(61.0)) && !behind(t, view, at(-61.0)));
        assert!(!behind(t, view, [0.0, 64.0, 2.0]));
        assert!(!behind(t, view, [2.0, 64.0, 0.0]));
        assert!(!behind(t, [0.0, 1.0, 0.0], [0.0, 64.0, -2.0]));
        assert!(!behind(t, view, t));
    }

    #[test]
    fn splashes_and_heads_wait_for_their_turn() {
        note_hit(71, 8.0, [1.0, 64.0, 1.0]);
        note_hit(71, 9.0, [1.0, 64.0, 1.0]);
        assert_eq!(take_hit(71), Some((9.0, [1.0, 64.0, 1.0])));
        assert_eq!(take_hit(71), None);
        let s = |attacker| Splash {
            attacker,
            victim: 72,
            at: [0.0; 3],
            amount: 4.0,
        };
        queue_splash(s(1));
        queue_splash(s(2));
        queue_splash(s(1));
        assert_eq!(take_splashes(1).len(), 2);
        assert_eq!(take_splashes(1).len(), 0);
        assert_eq!(take_splashes(2), vec![s(2)]);
        assert!(in_splash([0.0, 64.0, 0.0], [1.0, 64.0, 1.0]));
        assert!(!in_splash([0.0, 64.0, 0.0], [1.5, 64.0, 1.0]));
        note_head(73, "minecraft:zombie_head");
        assert_eq!(take_head(73), Some("minecraft:zombie_head"));
        assert_eq!(take_head(73), None);
        for i in 0..200 {
            note_head(1000 + i, "minecraft:creeper_head");
        }
        assert!(lock(&HEADS).len() <= MAX_WAITING);
    }
}
