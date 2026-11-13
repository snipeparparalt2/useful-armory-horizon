// Hook helper: native_living_knockback (HEAD). The obsidian set's knockback resistance.
fn useful_armory_knockback(entity: i32, kind: &str, strength: &mut f64) {
    crate::game::useful_armory_gear::on_knockback(entity, kind, strength);
}
