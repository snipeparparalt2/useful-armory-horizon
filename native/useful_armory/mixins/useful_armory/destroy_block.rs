// Hook helper: native_destroy_block (HEAD). Vein mining, wide dig and tree felling.
fn useful_armory_destroy_block(
    game: &mut crate::game::Game<'_>,
    pos: [i32; 3],
    state: horizon_world::registry::BlockStateId,
    canceled: &mut bool,
) {
    crate::game::useful_armory_gear::on_destroy_block(game, pos, state, canceled);
}
