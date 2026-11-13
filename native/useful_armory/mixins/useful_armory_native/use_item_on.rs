// Hook helper: native_use_item_on (HEAD). The hoes' harvest sweep.
fn useful_armory_use_item_on(
    game: &mut crate::game::Game<'_>,
    stack: &horizon_client::items::ItemStack,
    pos: [i32; 3],
    claimed: &mut bool,
) {
    crate::game::useful_armory_gear::on_use_item_on(game, stack, pos, claimed);
}
