// Useful Armory, native half. So far it is the glow: the glowing Useful Armory items cast
// real coloured light.
//
// The item icons used to carry a soft halo painted into the texture. The halo is gone from
// the textures; this mod puts the glow in the world instead: hold a glowing item, or wear a
// glowing armour piece, and the blocks and mobs around you are lit in that item's colour.
// Mobs and other players carrying them glow too, and so do the items lying on the ground.
//
// This file is the mod's logic (which items glow, how bright, which lights a frame keeps).
// It is both the module the bundle adds to the game (`game::useful_armory`) and this
// folder's Cargo library, so `cargo test` runs it without the game.

/// The mod's id (Options > Mods; the content mod's id too), name and version.
pub const ID: &str = "useful_armory";
pub const NAME: &str = "Useful Armory";
pub const VERSION: &str = "0.1.1";
pub const DESCRIPTION: &str = "Glowing Useful Armory gear lights up the world around you in its own colour while you hold or wear it.";

/// The content mod's namespace: only its items are looked up.
const NAMESPACE: &str = "useful_armory:";

/// Item id (without the namespace) -> glow colour, 0xRRGGBB. Sorted by id: `glow_of` does a
/// binary search. These are the sprites gen_textures.py marks as glowing (its GLOW table).
const GLOW: &[(&str, u32)] = &[
    ("aquiteaxe", 0x8cffe2),
    ("aquitebody", 0x8cffe2),
    ("aquiteboots", 0x8cffe2),
    ("aquitedagger", 0x8cffe2),
    ("aquitegreatsword", 0x8cffe2),
    ("aquitehalbert", 0x8cffe2),
    ("aquitehelmet", 0x8cffe2),
    ("aquitehoe", 0x8cffe2),
    ("aquitelegs", 0x8cffe2),
    ("aquitepickaxe", 0x8cffe2),
    ("aquiteshovel", 0x8cffe2),
    ("aquitesword", 0x8cffe2),
    ("erottenflesh", 0xb4ff46),
    ("lavasword", 0xff8c1e),
    ("shadowaxe", 0x9e60ff),
    ("shadowbody", 0x9e60ff),
    ("shadowboots", 0x9e60ff),
    ("shadowdagger", 0x9e60ff),
    ("shadowgreatsword", 0x9e60ff),
    ("shadowhelmet", 0x9e60ff),
    ("shadowhoe", 0x9e60ff),
    ("shadowlegs", 0x9e60ff),
    ("shadowotehrweapon", 0x9e60ff),
    ("shadowpickaxe", 0x9e60ff),
    ("shadowshovel", 0x9e60ff),
    ("shadowsword", 0x9e60ff),
    ("souleater", 0xe8aaec),
    ("soulednetherstar", 0x96f0ff),
    ("thenetherlegacy", 0x50e6f0),
];

/// Horizon draws at most 8 coloured lights per mod (16 in all); the nearest ones are kept.
pub const MAX_LIGHTS: usize = 6;
/// Horizon refuses lights more than 32 blocks from the player; stay well inside.
pub const REACH: f64 = 24.0;

/// A held item counts fully, a worn armour piece half.
const HELD: f32 = 1.0;
const WORN: f32 = 0.5;

/// One coloured light: what Horizon's `NativeColoredLight` takes besides the position.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Glow {
    pub rgb: u32,
    /// Blocks, 0.25 to 16.
    pub radius: f32,
    /// 0 to 1.
    pub intensity: f32,
}

/// The colour an item glows in, if it does.
pub fn glow_of(item: &str) -> Option<u32> {
    let name = item.strip_prefix(NAMESPACE)?;
    GLOW.binary_search_by(|(id, _)| (*id).cmp(name))
        .ok()
        .map(|i| GLOW[i].1)
}

/// The light of what someone holds (main hand, off hand) and wears (head, chest, legs, feet).
/// More glowing gear reaches further and shines brighter; mixed sets blend their colours.
pub fn glow(held: [Option<&str>; 2], worn: [Option<&str>; 4]) -> Option<Glow> {
    let mut sum = [0.0f32; 3];
    let mut weight = 0.0f32;
    let pieces = held
        .into_iter()
        .map(|i| (i, HELD))
        .chain(worn.into_iter().map(|i| (i, WORN)));
    for (item, w) in pieces {
        let Some(rgb) = item.and_then(glow_of) else {
            continue;
        };
        let [_, r, g, b] = rgb.to_be_bytes();
        sum[0] += f32::from(r) * w;
        sum[1] += f32::from(g) * w;
        sum[2] += f32::from(b) * w;
        weight += w;
    }
    if weight <= 0.0 {
        return None;
    }
    let channel = |v: f32| (v / weight).round().clamp(0.0, 255.0) as u32;
    Some(Glow {
        rgb: channel(sum[0]) << 16 | channel(sum[1]) << 8 | channel(sum[2]),
        // One held item: 6.5 blocks at 0.45. A full set and a weapon: 9.5 blocks at 0.75.
        radius: (5.0 + 1.5 * weight).min(11.0),
        intensity: (0.30 + 0.15 * weight).min(0.9),
    })
}

/// The fainter light of a glowing item lying on the ground.
pub fn dropped(item: &str) -> Option<Glow> {
    glow_of(item).map(|rgb| Glow {
        rgb,
        radius: 3.5,
        intensity: 0.3,
    })
}

/// Keeps the `max` lights nearest `player` within `REACH`, nearest first.
pub fn nearest(player: [f64; 3], lights: &mut Vec<([f64; 3], Glow)>, max: usize) {
    let far = |at: &[f64; 3]| {
        (at[0] - player[0]).powi(2) + (at[1] - player[1]).powi(2) + (at[2] - player[2]).powi(2)
    };
    lights.retain(|(at, _)| at.iter().all(|v| v.is_finite()) && far(at) <= REACH * REACH);
    lights.sort_by(|a, b| far(&a.0).total_cmp(&far(&b.0)));
    lights.truncate(max);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_table_is_sorted_for_the_binary_search() {
        assert!(GLOW.windows(2).all(|w| w[0].0 < w[1].0));
        assert!(GLOW.iter().all(|(_, rgb)| *rgb <= 0xff_ffff));
    }

    #[test]
    fn only_glowing_useful_armory_items_glow() {
        assert_eq!(glow_of("useful_armory:shadowsword"), Some(0x9e60ff));
        assert_eq!(glow_of("useful_armory:aquitehelmet"), Some(0x8cffe2));
        assert_eq!(glow_of("useful_armory:lavasword"), Some(0xff8c1e));
        assert_eq!(glow_of("useful_armory:emeraldsword"), None);
        assert_eq!(glow_of("minecraft:torch"), None);
        assert_eq!(glow_of("shadowsword"), None);
    }

    #[test]
    fn more_gear_shines_further_and_stays_in_horizons_bounds() {
        let sword = glow([Some("useful_armory:shadowsword"), None], [None; 4]).unwrap();
        assert_eq!(sword.rgb, 0x9e60ff);
        let set = glow(
            [Some("useful_armory:shadowsword"), None],
            [
                Some("useful_armory:shadowhelmet"),
                Some("useful_armory:shadowbody"),
                Some("useful_armory:shadowlegs"),
                Some("useful_armory:shadowboots"),
            ],
        )
        .unwrap();
        assert_eq!(set.rgb, 0x9e60ff);
        assert!(set.radius > sword.radius && set.intensity > sword.intensity);
        for g in [sword, set] {
            assert!((0.25..=16.0).contains(&g.radius) && (0.0..=1.0).contains(&g.intensity));
        }
        assert_eq!(glow([Some("minecraft:torch"), None], [None; 4]), None);
        assert_eq!(glow([None; 2], [None; 4]), None);
    }

    #[test]
    fn mixed_sets_blend() {
        let g = glow(
            [Some("useful_armory:shadowsword"), Some("useful_armory:aquitesword")],
            [None; 4],
        )
        .unwrap();
        assert_eq!(g.rgb, 0x95b0f1);
    }

    #[test]
    fn the_nearest_lights_within_reach_are_kept() {
        let g = dropped("useful_armory:soulednetherstar").unwrap();
        let mut lights: Vec<_> = (0..10).map(|i| ([f64::from(i) * 4.0, 64.0, 0.0], g)).collect();
        lights.push(([f64::NAN, 64.0, 0.0], g));
        lights.reverse();
        nearest([0.0, 64.0, 0.0], &mut lights, MAX_LIGHTS);
        assert_eq!(lights.len(), MAX_LIGHTS);
        assert_eq!(lights[0].0[0], 0.0);
        assert!(lights.iter().all(|(at, _)| at[0] <= REACH));
    }
}
