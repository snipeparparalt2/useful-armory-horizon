// Hook helper: native_loot_drops (HEAD). A head the reaper scythe took joins the loot.
fn useful_armory_loot_drops(
    game: &crate::game::Game<'_>,
    context: &horizon_client::mod_api::NativeLootDrops<'_>,
    drops: &mut Vec<horizon_client::items::ItemStack>,
) {
    crate::game::useful_armory_gear::on_loot_drops(game, context, drops);
}
