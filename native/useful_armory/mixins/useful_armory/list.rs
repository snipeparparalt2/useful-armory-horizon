// Hook helper: native_mods (HEAD). The mod's row in Options > Mods.
fn useful_armory_list(mods: &mut Vec<horizon_client::mod_api::NativeMod>) {
    crate::game::useful_armory_glue::on_list(mods);
}
