// Reads the game for Useful Armory's glow (who holds or wears glowing gear this frame, and the
// coloured lights that makes) and keeps the mod's row and settings page in Options > Mods.
// Added to the game as `game::useful_armory_glue`.
use crate::game::useful_armory as m;
use crate::game::{Game, shield};
use horizon_client::mod_api::{NativeColoredLight, NativeMod};

/// `native_visuals`: once a world frame. Lights are frame-local, so taking the gear off,
/// turning the mod off in Options > Mods or leaving the world puts them out at once.
pub(super) fn on_visuals(game: &Game<'_>, lights: &mut Vec<NativeColoredLight>) {
    if !game.native_on(m::ID) || !m::enabled(m::Feature::Glow, |k| game.native_setting(m::ID, k)) {
        return;
    }
    let Some(p) = game.player.as_ref() else {
        return;
    };
    // Where the frame draws the player, as Horizon's own dynamic lights place a held torch.
    let feet = game
        .previous_position
        .lerp(p.position, game.clock.camera_fraction());
    let mut found: Vec<([f64; 3], m::Glow)> = Vec::new();

    // The player: both hands and the four armour slots (head, chest, legs, feet).
    if !p.spectator {
        let held = [
            game.stack_in(game.selected).map(|s| &*s.item),
            game.stack_in(shield::OFFHAND_SLOT).map(|s| &*s.item),
        ];
        let worn = [
            game.armor[0].as_ref().map(|s| &*s.item),
            game.armor[1].as_ref().map(|s| &*s.item),
            game.armor[2].as_ref().map(|s| &*s.item),
            game.armor[3].as_ref().map(|s| &*s.item),
        ];
        if let Some(glow) = m::glow(held, worn) {
            found.push(([feet.x, feet.y + 1.2, feet.z], glow));
        }
    }

    // Mobs and the other players, by what the server says they hold and wear.
    for mob in game.mobs.iter().filter(|mob| !mob.removed && !mob.invisible) {
        let e = &mob.extra;
        let held = [e.main_hand.as_deref(), e.off_hand.as_deref()];
        let worn = [
            e.head.as_deref(),
            e.chest.as_deref(),
            e.legs.as_deref(),
            e.feet.as_deref(),
        ];
        if let Some(glow) = m::glow(held, worn) {
            let at = mob.position;
            found.push(([at.x, at.y + f64::from(mob.height()) * 0.6, at.z], glow));
        }
    }

    // Glowing items on the ground.
    for item in game.dropped.iter() {
        if let Some(glow) = m::dropped(&item.stack.item) {
            let at = item.position;
            found.push(([at.x, at.y + 0.25, at.z], glow));
        }
    }

    m::nearest([feet.x, feet.y, feet.z], &mut found, m::MAX_LIGHTS);
    lights.extend(found.into_iter().map(|(at, glow)| NativeColoredLight {
        at,
        rgb: glow.rgb,
        radius: glow.radius,
        intensity: glow.intensity,
    }));
}

/// `native_mods`: the mod's row in Options > Mods, where it is switched on and off.
pub(super) fn on_list(mods: &mut Vec<NativeMod>) {
    mods.push(NativeMod {
        id: m::ID.into(),
        title: format!("{} {}", m::NAME, m::VERSION),
        description: m::DESCRIPTION.into(),
        keys: Vec::new(),
    });
}

/// `native_settings`: the mod's page, one switch per part.
pub(super) fn on_settings(game: &Game<'_>, mod_id: &str, buttons: &mut Vec<String>) {
    if mod_id != m::ID {
        return;
    }
    for f in m::Feature::ALL {
        let on = m::enabled(f, |k| game.native_setting(m::ID, k));
        buttons.push(m::setting_label(f, on));
    }
}

/// `native_settings_click`: button `button` of the mod's page flips its part, and keeps it.
pub(super) fn on_settings_click(game: &Game<'_>, mod_id: &str, button: usize) {
    if mod_id != m::ID {
        return;
    }
    let Some(&f) = m::Feature::ALL.get(button) else {
        return;
    };
    let on = !m::enabled(f, |k| game.native_setting(m::ID, k));
    m::set_enabled(f, on, |k| game.native_setting(m::ID, k));
    game.native_set_setting(m::ID, f.key(), if on { "true" } else { "false" });
}
