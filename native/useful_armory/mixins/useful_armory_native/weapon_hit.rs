// Hook helper: native_living_incoming_damage_v2 (HEAD). Weapon damage bonuses.
fn useful_armory_weapon_hit(
    game: &mut crate::game::Game<'_>,
    entity: i32,
    kind: &str,
    source_position: Option<[f64; 3]>,
    victim_position: [f64; 3],
    victim_view: [f64; 3],
    weapon: Option<&horizon_client::items::ItemStack>,
    amount: &mut f32,
    canceled: &mut bool,
) {
    crate::game::useful_armory_gear::on_weapon_hit(
        game,
        entity,
        kind,
        source_position,
        victim_position,
        victim_view,
        weapon,
        amount,
        canceled,
    );
}
