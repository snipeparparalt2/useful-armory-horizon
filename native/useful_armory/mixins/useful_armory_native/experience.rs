// Hook helper: native_player_exp_change (HEAD). The lapis set's experience bonus.
fn useful_armory_experience(game: &crate::game::Game<'_>, player: u128, amount: &mut i32) {
    crate::game::useful_armory_gear::on_experience(game, player, amount);
}
