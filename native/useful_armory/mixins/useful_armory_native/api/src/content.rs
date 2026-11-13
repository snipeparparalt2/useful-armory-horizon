//! What Useful Armory registers with Armory Lib, as plain tables with nothing from the game
//! in them. `cargo test` in `native/useful_armory` runs this file's tests.

/// The native half's id: its row in Options > Mods and its settings folder.
pub const ID: &str = "useful_armory_native";
/// The content mod's namespace: items, entity types and textures.
pub const NAMESPACE: &str = "useful_armory";
pub const TITLE: &str = "Useful Armory 0.1.7";
pub const DESCRIPTION: &str = "Glowing gear lights up the world; full armour sets give bonuses; sneak to vein mine, dig 3 x 3 or fell trees; hoes harvest an area; weapons have effects. Each part can be switched off here.";

/// The settings page's switches: key and label. Every key but `glow` is one of
/// `runtime.rs`'s `Feature` keys, which the mixin code reads.
pub const SWITCHES: &[(&str, &str)] = &[
    ("glow", "Glow"),
    ("set_bonuses", "Set bonuses"),
    ("vein_mining", "Vein mining"),
    ("wide_dig", "Wide dig"),
    ("tree_felling", "Tree felling"),
    ("harvest_sweep", "Harvest sweep"),
    ("weapon_effects", "Weapon effects"),
];

/// Item id (without the namespace) -> glow colour, 0xRRGGBB. These are the sprites
/// gen_textures.py marks as glowing (its GLOW table).
pub const GLOW: &[(&str, u32)] = &[
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

/// The mod's creatures, all copies of `minecraft:zombie`: id, whether the texture has a
/// glowing `_e` layer, whether fire harms it, and the effect its hit leaves (id, amplifier,
/// ticks).
pub const MOBS: &[(&str, bool, bool, Option<(&str, u8, i32)>)] = &[
    ("ember_brute", true, false, None),
    ("lost_pigman", false, false, None),
    ("shade", true, true, None),
    ("tide_lurker", true, true, Some(("minecraft:slowness", 1, 100))),
    ("tower_sentry", true, true, None),
    ("vault_guardian", true, true, None),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tables_are_sorted_and_unique() {
        assert!(GLOW.windows(2).all(|w| w[0].0 < w[1].0));
        assert!(GLOW.iter().all(|(_, rgb)| *rgb <= 0xff_ffff));
        assert!(MOBS.windows(2).all(|w| w[0].0 < w[1].0));
        let keys: std::collections::HashSet<_> = SWITCHES.iter().map(|(k, _)| k).collect();
        assert_eq!(keys.len(), SWITCHES.len());
    }

    #[test]
    fn known_gear_glows() {
        let of = |id: &str| GLOW.iter().find(|(i, _)| *i == id).map(|(_, rgb)| *rgb);
        assert_eq!(of("shadowsword"), Some(0x9e60ff));
        assert_eq!(of("aquitehelmet"), Some(0x8cffe2));
        assert_eq!(of("lavasword"), Some(0xff8c1e));
        assert_eq!(of("emeraldsword"), None);
    }
}
