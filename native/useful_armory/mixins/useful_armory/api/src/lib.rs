//! Useful Armory's trait-mod package. The gear abilities are mixin code (`../runtime.rs`,
//! `../gear.rs`); this package only tells Armory Lib what the mod has: its settings page,
//! its glowing items, and its creatures' looks and rules. The library does the rest.
#![forbid(unsafe_code)]

mod content;

use armory_lib::{GearLight, MobLook, MobRules, Page, Rig, Switch};
use horizon_client::mod_api::Hooks;

pub fn hooks() -> Box<dyn Hooks> {
    register();
    Box::new(Mod)
}

/// Nothing to hear: the mod's own hooks are mixin injections.
struct Mod;
impl Hooks for Mod {}

fn register() {
    let id = content::ID;
    armory_lib::register_page(Page {
        mod_id: id.into(),
        title: content::TITLE.into(),
        description: content::DESCRIPTION.into(),
        switches: content::SWITCHES
            .iter()
            .map(|(key, label)| Switch::new(key, label))
            .collect(),
    });
    for (item, rgb) in content::GLOW {
        armory_lib::register_gear_light(
            GearLight::new(id, &format!("{id}:{item}"), *rgb).setting("glow"),
        );
    }
    for (mob, glows, hit) in content::MOBS {
        let kind = format!("{id}:{mob}");
        let texture = format!("{id}:entity/{mob}/{mob}");
        let mut look = MobLook::new(id, &kind, Rig::zombie(), &texture);
        if *glows {
            look = look.emissive(&format!("{texture}_e"));
        }
        armory_lib::register_mob_look(look);
        // Copies of a zombie: they must not die in daylight or turn into drowned.
        let mut rules = MobRules::new(id, &kind).no_conversion().fire_proof();
        if let Some((effect, amplifier, ticks)) = hit {
            rules = rules.on_hit(effect, *amplifier, *ticks);
        }
        armory_lib::register_mob_rules(rules);
    }
}
