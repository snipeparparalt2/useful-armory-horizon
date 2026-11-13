// Hook helper: native_player_tick (HEAD). Set bonuses and greatsword splashes, per player.
fn useful_armory_player_tick(game: &mut crate::game::Game<'_>) {
    crate::game::useful_armory_gear::on_player_tick(game);
}
