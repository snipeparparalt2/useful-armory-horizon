// Hook helper: native_hurt_enemy (HEAD). The magma sword's fire and greatsword splashes.
fn useful_armory_hurt_enemy(
    game: &mut crate::game::Game<'_>,
    stack: &horizon_client::items::ItemStack,
    entity: u32,
) {
    crate::game::useful_armory_gear::on_hurt_enemy(game, stack, entity);
}
