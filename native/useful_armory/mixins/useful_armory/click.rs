// Hook helper: native_settings_click (HEAD). A switch on the mod's page was clicked.
fn useful_armory_click(game: &crate::game::Game<'_>, mod_id: &str, button: usize) {
    crate::game::useful_armory_glue::on_settings_click(game, mod_id, button);
}
