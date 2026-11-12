// Hook helper: native_visuals (HEAD). Pushes this frame's coloured lights.
fn useful_armory_visuals(
    game: &crate::game::Game<'_>,
    lights: &mut Vec<horizon_client::mod_api::NativeColoredLight>,
) {
    crate::game::useful_armory_glue::on_visuals(game, lights);
}
