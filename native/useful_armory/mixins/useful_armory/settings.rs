// Hook helper: native_settings (HEAD). The mod's settings page: one switch per part.
fn useful_armory_settings(game: &crate::game::Game<'_>, mod_id: &str, buttons: &mut Vec<String>) {
    crate::game::useful_armory_glue::on_settings(game, mod_id, buttons);
}
