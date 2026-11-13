// Hook helper: native_mob_killed (HEAD). The soul eater's heal and the reaper scythe's heads.
fn useful_armory_mob_killed(game: &mut crate::game::Game<'_>, player: u128, entity: u32, kind: &str) {
    crate::game::useful_armory_gear::on_mob_killed(game, player, entity, kind);
}
