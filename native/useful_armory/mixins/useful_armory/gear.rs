// Gear that does things: what the set bonuses, tool abilities and weapon effects read and
// change in the game. Added to the game as `game::useful_armory_gear`; the decisions are in
// `game::useful_armory` (runtime.rs). Everything here runs on the server (single player's
// server thread, a LAN host, a dedicated server), inside the hooks named in each function.
use crate::game::Game;
use crate::game::native_player_state::NativeEffect;
use crate::game::useful_armory::{self as m, Feature};
use horizon_client::items::ItemStack;
use horizon_client::mod_api::NativeLootDrops;
use horizon_world::player_inventory::EquipmentSlot;
use horizon_world::registry::BlockStateId;

/// Whether `feature` is on: the mod in Options > Mods, and its switch on the mod's page.
fn on(game: &Game<'_>, feature: Feature) -> bool {
    game.native_on(m::ID) && m::enabled(feature, |key| game.native_setting(m::ID, key))
}

// ---- Set bonuses -----------------------------------------------------------------------

/// `native_player_tick`, each server tick of each living player, with that player swapped in:
/// reads their armour, keeps their set's effects on them and heals the ultimate set's wearer.
/// Also deals the splash damage of their greatsword hits since their last tick.
pub(super) fn on_player_tick(game: &mut Game<'_>) {
    let mod_on = game.native_on(m::ID);
    m::note_mod_on(mod_on);
    let Some(me) = game.native_acting_player() else {
        return;
    };
    let set = if mod_on && on(game, Feature::SetBonuses) {
        let worn = [
            EquipmentSlot::Head,
            EquipmentSlot::Chest,
            EquipmentSlot::Legs,
            EquipmentSlot::Feet,
        ]
        .map(|slot| game.native_equipment(slot));
        m::armor_set(worn.each_ref().map(|s| s.as_ref().map(|s| &*s.item)))
    } else {
        None
    };
    let (before, ticks) = m::note_wearer(me.uuid, me.entity_id, set);
    if let Some(old) = before
        && before != set
    {
        take_set_effects(game, me.uuid, old);
    }
    if let Some(set) = set {
        if before != Some(set) || ticks % m::EFFECT_REFRESH_TICKS == 0 {
            for e in m::set_effects(set) {
                game.native_add_effect(me.uuid, &effect(e));
            }
        }
        if set == m::ArmorSet::Ultimate && ticks % m::ULTIMATE_REGEN_TICKS == 0 {
            let max = game
                .native_attribute(me.uuid, "minecraft:max_health")
                .map_or(20.0, |(_, value)| value as f32);
            if me.health > 0.0 && me.health < max {
                let health = (me.health + m::ULTIMATE_REGEN_HEALTH).min(max);
                game.native_set_player_status(me.uuid, Some(health), None, None);
            }
        }
    }
    let splashes = m::take_splashes(me.uuid);
    if mod_on && on(game, Feature::WeaponEffects) {
        for splash in splashes {
            deal_splash(game, &me.dimension, me.entity_id, &splash);
        }
    }
}

fn effect(e: &m::SetEffect) -> NativeEffect {
    NativeEffect {
        id: e.id.to_owned(),
        amplifier: e.amplifier,
        duration: e.duration,
        ambient: true,
        particles: false,
    }
}

/// The set came off: its effects go at once rather than running out. Only what looks like
/// the set's own (the same level, no longer than it gives) is taken; a potion's stays.
fn take_set_effects(game: &mut Game<'_>, uuid: u128, set: m::ArmorSet) {
    let Some(now) = game.native_effects(uuid) else {
        return;
    };
    for e in m::set_effects(set) {
        let ours = now
            .iter()
            .any(|n| n.id == e.id && n.amplifier == e.amplifier && (0..=e.duration).contains(&n.duration));
        if ours {
            game.native_remove_effect(uuid, e.id);
        }
    }
}

/// `native_living_incoming_damage_v3` (no game: the hit is in progress), for a player victim
/// (`victim_uuid`): the ultimate set takes no fall damage, the obsidian set half of an
/// explosion's.
pub(super) fn on_incoming_damage(
    victim_uuid: Option<u128>,
    damage_type: &str,
    amount: &mut f32,
    canceled: &mut bool,
) {
    let Some(uuid) = victim_uuid else {
        return;
    };
    if *canceled || !m::mod_on() || !m::enabled_now(Feature::SetBonuses) {
        return;
    }
    let Some(set) = m::with_wearer(uuid, |w| w.set).flatten() else {
        return;
    };
    match m::incoming_damage(set, damage_type) {
        m::DamageChange::Keep => {}
        m::DamageChange::Cancel => *canceled = true,
        m::DamageChange::Scale(share) => *amount *= share,
    }
}

/// `native_living_knockback` (no game): the obsidian set is pushed half as far.
pub(super) fn on_knockback(entity: i32, kind: &str, strength: &mut f64) {
    if m::vanilla(kind) != "player" || !m::mod_on() || !m::enabled_now(Feature::SetBonuses) {
        return;
    }
    if m::set_of_entity(entity) == Some(m::ArmorSet::Obsidian) {
        *strength *= m::OBSIDIAN_KNOCKBACK_TAKEN;
    }
}

/// `native_player_exp_change`: an experience orb the player picks up (kills, ores, and also
/// smelting, breeding and fishing, which drop orbs too) is worth a quarter more with the
/// lapis set.
pub(super) fn on_experience(game: &Game<'_>, player: u128, amount: &mut i32) {
    if *amount <= 0 || !on(game, Feature::SetBonuses) {
        return;
    }
    let bonus = m::with_wearer(player, |w| {
        if w.set == Some(m::ArmorSet::Lapis) {
            m::lapis_bonus(*amount, &mut w.xp_carry)
        } else {
            0
        }
    });
    *amount = amount.saturating_add(bonus.unwrap_or(0));
}

// ---- Tool abilities --------------------------------------------------------------------

/// `native_destroy_block`: a player is about to break the block `state` at `pos`, with their
/// state swapped in. Sneaking with a vein-mining, wide-dig or tree-felling tool breaks more
/// blocks first, each as that player's own break (drops for the tool, wear, statistics,
/// experience, protection), which calls this hook again: `m::Breaking` keeps those alone.
pub(super) fn on_destroy_block(
    game: &mut Game<'_>,
    pos: [i32; 3],
    state: BlockStateId,
    canceled: &mut bool,
) {
    if *canceled || m::breaking() || !game.native_authoritative() || !game.native_sneaking() {
        return;
    }
    let Some(tool) = game.native_equipment(EquipmentSlot::MainHand) else {
        return;
    };
    let Some(ability) = m::tool_ability(&tool.item) else {
        return;
    };
    if !on(game, ability.feature()) {
        return;
    }
    let Some(name) = game.native_state_block(state).map(str::to_owned) else {
        return;
    };
    let targets = match ability {
        m::Ability::VeinMine => vein(game, pos, &name, &tool),
        m::Ability::WideDig => wide(game, pos, state, &tool),
        m::Ability::FellTree => tree(game, pos, &name),
    };
    if targets.is_empty() {
        return;
    }
    let Some(_guard) = m::Breaking::start() else {
        return;
    };
    // The original break's position marks which destroy event the breaker's own client
    // predicted; the extra blocks' events must reach them.
    let own_break = game.lan_break_pos.take();
    for (at, block) in targets {
        if !tool_left(game, &tool) {
            break;
        }
        if game.native_block(at) != block {
            continue;
        }
        let _ = game.with_player_actor(|g| g.break_block_as_player(at));
    }
    game.lan_break_pos = own_break;
}

/// Whether the player still holds the tool (it may have broken) with wear to spare: enough
/// for this extra block and the original one, which comes after.
fn tool_left(game: &Game<'_>, tool: &ItemStack) -> bool {
    let Some(now) = game.native_equipment(EquipmentSlot::MainHand) else {
        return false;
    };
    if now.item != tool.item {
        return false;
    }
    let (max, per_block) = game
        .items()
        .get(&now.item)
        .map_or((0, 1), |i| (i.max_damage, i.tool_damage_per_block.unwrap_or(1)));
    m::spare_durability(max, now.damage, 2 * per_block)
}

/// Whether a block counts as an ore: an ore tag, the mod's own ores, or (with no tags to read)
/// a name ending in `_ore`.
fn is_ore(game: &Game<'_>, block: &str) -> bool {
    if m::is_mod_ore(block) {
        return true;
    }
    let mut tags = m::ORE_TAGS
        .iter()
        .map(|tag| game.native_block_name_in_tag(block, tag));
    match tags.next() {
        Some(Err(_)) | None => m::looks_like_ore(block),
        Some(Ok(first)) => first || tags.any(|t| t == Ok(true)),
    }
}

fn is_log(game: &Game<'_>, block: &str) -> bool {
    match game.native_block_name_in_tag(block, "minecraft:logs") {
        Ok(tagged) => tagged,
        Err(_) => m::looks_like_log(block),
    }
}

/// Whether the tool gets the block's drops (`Player.hasCorrectToolForDrops`).
fn harvests(game: &Game<'_>, tool: &ItemStack, state: BlockStateId) -> bool {
    let facts = game.res.facts().get(state);
    !facts.requires_tool || game.items().correct_for_drops(Some(tool), &facts.name)
}

/// The ore blocks of the broken one's kind connected to it, with their names.
fn vein(game: &Game<'_>, pos: [i32; 3], block: &str, tool: &ItemStack) -> Vec<([i32; 3], String)> {
    if !is_ore(game, block) {
        return Vec::new();
    }
    let kind = m::vein_kind(block);
    m::flood(pos, m::VEIN_MAX, |at| {
        let state = game.world.block(at[0], at[1], at[2]);
        let name = &game.res.facts().get(state).name;
        m::vein_kind(name) == kind && harvests(game, tool, state)
    })
    .into_iter()
    .map(|at| (at, block_name(game, at)))
    .collect()
}

/// The logs of the broken one's kind connected to it, at its height and above.
fn tree(game: &Game<'_>, pos: [i32; 3], block: &str) -> Vec<([i32; 3], String)> {
    if !is_log(game, block) {
        return Vec::new();
    }
    m::flood(pos, m::TREE_MAX, |at| at[1] >= pos[1] && block_name(game, at) == block)
        .into_iter()
        .map(|at| (at, block.to_owned()))
        .collect()
}

/// The 3 x 3 square around the broken block, across the face the player looks at: the blocks
/// the tool is made for, no harder than the one broken.
fn wide(
    game: &Game<'_>,
    pos: [i32; 3],
    state: BlockStateId,
    tool: &ItemStack,
) -> Vec<([i32; 3], String)> {
    let hardness = game.res.facts().get(state).hardness;
    let axis = game
        .native_raycast(8.0)
        .filter(|hit| [hit.block_x, hit.block_y, hit.block_z] == pos)
        .and_then(|hit| m::hit_axis(pos, [hit.x, hit.y, hit.z]))
        .or_else(|| {
            game.native_acting_player()
                .map(|p| m::look_axis(p.yaw, p.pitch))
        })
        .unwrap_or(m::Axis::Y);
    m::square(pos, axis)
        .into_iter()
        .filter_map(|at| {
            let state = game.world.block(at[0], at[1], at[2]);
            let facts = game.res.facts().get(state);
            let fits = !game.res.behaviours().is_air(state)
                && (0.0..=hardness).contains(&facts.hardness)
                && game.items().correct_for_drops(Some(tool), &facts.name);
            fits.then(|| (at, facts.name.to_string()))
        })
        .collect()
}

fn block_name(game: &Game<'_>, at: [i32; 3]) -> String {
    game.native_block(at)
}

// ---- Harvest sweep ---------------------------------------------------------------------

/// `native_use_item_on`: a right click with `stack` on the block at `pos`. A mod hoe on a
/// grown crop harvests and replants the grown crops around it (the reaper scythe a wider
/// square), one durability each, as long as the hoe has more than one point left.
pub(super) fn on_use_item_on(
    game: &mut Game<'_>,
    stack: &ItemStack,
    pos: [i32; 3],
    claimed: &mut bool,
) {
    if *claimed || !game.native_authoritative() {
        return;
    }
    let Some(radius) = m::harvest_radius(&stack.item) else {
        return;
    };
    if !on(game, Feature::HarvestSweep) || grown_crop(game, pos).is_none() {
        return;
    }
    *claimed = true;
    let dimension = game.dim.id().to_owned();
    for at in m::field(pos, radius) {
        let Some(crop) = grown_crop(game, at) else {
            continue;
        };
        let Some(hoe) = game.held().cloned() else {
            break;
        };
        let max = game.items().get(&hoe.item).map_or(0, |i| i.max_damage);
        if hoe.item != stack.item || !m::spare_durability(max, hoe.damage, 1) {
            break;
        }
        let Some(mut drops) = game.native_machine_destroy_block(at, Some(&hoe), true) else {
            continue;
        };
        let replant = m::take_one(
            drops.iter_mut().map(|d| (&*d.item, &mut d.count)),
            crop.seed,
        );
        for stack in drops.into_iter().filter(|d| d.count > 0) {
            game.pop_resource(at, stack);
        }
        if replant && let Some(seedling) = game.native_default_state(crop.block) {
            game.native_set_block(&dimension, at, seedling, horizon_world::level::flags::UPDATE_ALL);
        }
        game.damage_held(1);
    }
}

fn grown_crop(game: &Game<'_>, at: [i32; 3]) -> Option<&'static m::Crop> {
    let crop = m::crop(&game.native_block(at))?;
    m::grown(crop, game.native_block_property(at, "age").as_deref()).then_some(crop)
}

// ---- Weapon effects --------------------------------------------------------------------

/// `native_living_incoming_damage_v2`: a player's weapon is about to hit the mob `entity`
/// (melee, sweep or spear), with that player swapped in. Daggers from behind, the pigman
/// sword on the piglin family and the nether's legacy in the Nether hit harder; a greatsword's
/// hit is kept for its splash.
#[allow(clippy::too_many_arguments)]
pub(super) fn on_weapon_hit(
    game: &mut Game<'_>,
    entity: i32,
    kind: &str,
    source_position: Option<[f64; 3]>,
    victim_position: [f64; 3],
    victim_view: [f64; 3],
    weapon: Option<&ItemStack>,
    amount: &mut f32,
    canceled: &mut bool,
) {
    if *canceled {
        return;
    }
    let Some(w) = weapon.and_then(|s| m::weapon(&s.item)) else {
        return;
    };
    if !on(game, Feature::WeaponEffects) {
        return;
    }
    let attacker = source_position.or_else(|| game.native_acting_player().map(|p| p.position));
    let from_behind = attacker.is_some_and(|a| m::behind(victim_position, victim_view, a));
    let in_nether = game.dim.id() == "minecraft:the_nether";
    *amount *= m::hit_multiplier(w, kind, in_nether, from_behind);
    if w == m::Weapon::Greatsword
        && let Ok(victim) = u32::try_from(entity)
    {
        m::note_hit(victim, *amount, victim_position);
    }
}

/// `native_hurt_enemy`: the player's hit with `stack` landed on the mob `entity`. The magma
/// sword sets it burning; a greatsword's splash is queued for the player's tick.
pub(super) fn on_hurt_enemy(game: &mut Game<'_>, stack: &ItemStack, entity: u32) {
    let Some(w) = m::weapon(&stack.item) else {
        return;
    };
    let hit = (w == m::Weapon::Greatsword).then(|| m::take_hit(entity)).flatten();
    if !on(game, Feature::WeaponEffects) {
        return;
    }
    match w {
        m::Weapon::MagmaSword => {
            if let Some(mob) = game.mobs.iter_mut().find(|mob| mob.id == entity) {
                mob.fire_ticks = mob.fire_ticks.max(m::MAGMA_FIRE_TICKS);
            }
        }
        m::Weapon::Greatsword => {
            if let (Some((amount, at)), Some(me)) = (hit, game.native_acting_player()) {
                m::queue_splash(m::Splash {
                    attacker: me.uuid,
                    victim: entity,
                    at,
                    amount: amount * m::SPLASH_SHARE,
                });
            }
        }
        _ => {}
    }
}

/// The splash of a greatsword hit: the other mobs around its target take their share, from
/// the attacking player.
fn deal_splash(game: &mut Game<'_>, dimension: &str, attacker: i32, splash: &m::Splash) {
    let caught: Vec<u32> = game
        .native_mobs(dimension)
        .into_iter()
        .filter(|mob| mob.id != splash.victim && m::in_splash(splash.at, mob.pos))
        .map(|mob| mob.id)
        .collect();
    let by = u32::try_from(attacker).ok();
    for id in caught {
        game.native_hurt_entity(dimension, id, splash.amount, "minecraft:player_attack", by);
    }
}

/// `native_mob_killed`: the player's blow killed the mob `entity` of type `kind`, with the
/// player swapped in. The soul eater heals its wielder; the reaper scythe may take a head.
pub(super) fn on_mob_killed(game: &mut Game<'_>, player: u128, entity: u32, kind: &str) {
    let Some(w) = game
        .native_equipment(EquipmentSlot::MainHand)
        .and_then(|s| m::weapon(&s.item))
    else {
        return;
    };
    if !on(game, Feature::WeaponEffects) {
        return;
    }
    match w {
        m::Weapon::SoulEater => {
            if let Some(me) = game.native_acting_player()
                && me.uuid == player
                && me.health > 0.0
            {
                let health = me.health + m::SOUL_EATER_HEAL;
                game.native_set_player_status(player, Some(health), None, None);
            }
        }
        m::Weapon::ReaperScythe => {
            let Some((head, chance)) = m::reaper_head(kind) else {
                return;
            };
            let dimension = game.dim.id().to_owned();
            let roll = game.native_level_random(&dimension).map(|r| {
                use horizon_core::random::RandomSource;
                r.next_float()
            });
            if roll.is_some_and(|r| r < chance) {
                m::note_head(entity, head);
            }
        }
        _ => {}
    }
}

/// `native_loot_drops`: a mob the reaper scythe killed for its head drops it with its loot
/// (once, and not a second one where its own loot rolled it).
pub(super) fn on_loot_drops(
    game: &Game<'_>,
    context: &NativeLootDrops<'_>,
    drops: &mut Vec<ItemStack>,
) {
    let Some((entity, _)) = context.entity else {
        return;
    };
    let Some(head) = m::take_head(entity) else {
        return;
    };
    if game.native_on(m::ID) && !drops.iter().any(|d| &*d.item == head) {
        drops.push(ItemStack::new(head, 1));
    }
}
