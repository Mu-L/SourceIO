import math
from functools import partial
import bpy

from SourceIO.blender_bindings.models import import_model
from SourceIO.blender_bindings.models.common import put_into_collections
from SourceIO.blender_bindings.operators.import_settings_base import ModelOptions
from SourceIO.blender_bindings.utils.bpy_utils import get_new_unique_collection, get_or_create_collection
from SourceIO.library.shared.content_manager import ContentManager
from SourceIO.library.utils.math_utilities import parse_hammer_vector
from SourceIO.library.utils.tiny_path import TinyPath


def handle_generic_model_prop(content_manager: ContentManager, entity_data, scale, parent_collection, fix_rotation=True,
                              single_collection=False):
    model_name = TinyPath(entity_data['model'])
    return handle_model_prop(content_manager, model_name, entity_data, scale, parent_collection,
                             single_collection=single_collection,
                             fix_rotation=fix_rotation)


def handle_model_prop_with_collection(model_name, group_collection_name, content_manager: ContentManager, entity_data,
                                      scale, parent_collection,
                                      fix_rotation=True, single_collection=False):
    if not single_collection:
        group_collection = get_or_create_collection(group_collection_name, parent_collection)
        parent_collection = get_or_create_collection(entity_data["classname"], group_collection)

    return handle_model_prop(content_manager, model_name, entity_data, scale, parent_collection, fix_rotation,
                             single_collection)


def handle_model_prop(content_manager: ContentManager, model_name, entity_data, scale, parent_collection,
                      fix_rotation=True, single_collection=False):
    origin = parse_hammer_vector(entity_data.get('origin', '0 0 0')) * scale
    angles = [math.radians(a) for a in parse_hammer_vector(entity_data.get('angles', '0 0 0'))]

    if fix_rotation:
        x, y, z = angles
        y += math.pi / 2
        angles = [x, z, y]
    if not angles:
        angles = 0.0, math.radians(entity_data.get('angle', '0')), 0.0
    target_name = entity_data.get('targetname', entity_data['classname'])
    mdl_buffer = content_manager.find_file(TinyPath(model_name))
    if mdl_buffer:
        if single_collection:
            master_collection = parent_collection
        else:
            master_collection = get_new_unique_collection(target_name, parent_collection)
        opts = ModelOptions()
        opts.scale = scale
        opts.bodygroup_grouping = True
        opts.create_flex_drivers = False
        opts.import_physics = True
        opts.import_textures = True
        opts.use_bvlg = False
        model_container = import_model(model_name, mdl_buffer, content_manager, opts, None)
        put_into_collections(model_container, target_name, master_collection, opts.bodygroup_grouping)
        # master_collection, disable_collection_sort=True, re_use_meshes=True)
        if model_container.armature:
            model_container.armature.location = origin
            model_container.armature.rotation_euler = angles
        else:
            for o in model_container.objects:
                o.location = origin
                o.rotation_euler = angles
        entity_data_holder = bpy.data.objects.new(target_name, None)
        entity_data_holder.location = origin
        entity_data_holder.rotation_euler = angles
        entity_data_holder.scale *= scale
        entity_data_holder['entity_data'] = {'entity': entity_data}
        master_collection.objects.link(entity_data_holder)
    pass


entity_handlers = {
    'monster_scientist': partial(handle_model_prop_with_collection, TinyPath('models/scientist.mdl'), "monster"),
    'monster_sitting_scientist': partial(handle_model_prop_with_collection, TinyPath('models/scientist.mdl'),
                                         "monster"),
    'monster_barney': partial(handle_model_prop_with_collection, TinyPath('models/barney.mdl'), "monster"),
    'monster_cine_barney': partial(handle_model_prop_with_collection, TinyPath('models/cine-barney.mdl'), "monster"),
    'monster_cine_panther': partial(handle_model_prop_with_collection, TinyPath('models/cine-panther.mdl'), "monster"),
    'monster_cine_scientist': partial(handle_model_prop_with_collection, TinyPath('models/cine-scientist.mdl'),
                                      "monster"),
    'monster_gman': partial(handle_model_prop_with_collection, TinyPath('models/gman.mdl'), "monster"),
    'monster_faceless': partial(handle_model_prop_with_collection, TinyPath('models/Faceless.mdl'), "monster"),
    'monster_polyrobo': partial(handle_model_prop_with_collection, TinyPath('models/polyrobo.mdl'), "monster"),
    'monster_boid': partial(handle_model_prop_with_collection, TinyPath('models/boid.mdl'), "monster"),
    'monster_boid_flock': partial(handle_model_prop_with_collection, TinyPath('models/boid.mdl'), "monster"),
    'item_battery': partial(handle_model_prop_with_collection, TinyPath('models/w_battery.mdl'), "item"),
    'item_healthkit': partial(handle_model_prop_with_collection, TinyPath('models/w_medkit.mdl'), "item"),
    'weapon_crossbow': partial(handle_model_prop_with_collection, TinyPath('models/w_crossbow.mdl'), "weapon"),
    'ammo_crossbow': partial(handle_model_prop_with_collection, TinyPath('models/w_crossbow_clip.mdl'), "ammo"),
    'ammo_buckshot': partial(handle_model_prop_with_collection, TinyPath('models/w_shotbox.mdl'), "ammo"),
    'ammo_gaussclip': partial(handle_model_prop_with_collection, TinyPath('models/w_gaussammo.mdl'), "ammo"),
    'ammo_rpgclip': partial(handle_model_prop_with_collection, TinyPath('models/w_rpgammo.mdl'), "ammo"),
    'weapon_rpg': partial(handle_model_prop_with_collection, TinyPath('models/w_rpg.mdl'), "weapon"),
    'weapon_9mmAR': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmAR.mdl'), "weapon"),
    'weapon_snark': partial(handle_model_prop_with_collection, TinyPath('models/w_sqknest.mdl'), "weapon"),
    'weapon_gauss': partial(handle_model_prop_with_collection, TinyPath('models/w_gauss.mdl'), "weapon"),
    'ammo_9mmAR': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmARclip.mdl'), "ammo"),
    'item_longjump': partial(handle_model_prop_with_collection, TinyPath('models/w_longjump.mdl'), "item"),
    'weapon_handgrenade': partial(handle_model_prop_with_collection, TinyPath('models/w_grenade.mdl'), "weapon"),
    'ammo_ARgrenades': partial(handle_model_prop_with_collection, TinyPath('models/w_ARgrenade.mdl'), "ammo"),
    'weapon_egon': partial(handle_model_prop_with_collection, TinyPath('models/w_egon.mdl'), "weapon"),
    'weapon_hornetgun': partial(handle_model_prop_with_collection, TinyPath('models/w_hgun.mdl'), "weapon"),
    'weapon_357': partial(handle_model_prop_with_collection, TinyPath('models/w_357.mdl'), "weapon"),
    'ammo_357': partial(handle_model_prop_with_collection, TinyPath('models/w_357ammobox.mdl'), "ammo"),
    'weapon_satchel': partial(handle_model_prop_with_collection, TinyPath('models/w_satchel.mdl'), "weapon"),
    'weapon_shotgun': partial(handle_model_prop_with_collection, TinyPath('models/w_shotgun.mdl'), "weapon"),

    'ammo_9mmbox': partial(handle_model_prop_with_collection, TinyPath('models/w_chainammo.mdl'), "ammo"),
    'ammo_9mmclip': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmclip.mdl'), "ammo"),
    'ammo_egonclip': partial(handle_model_prop_with_collection, TinyPath('models/w_chainammo.mdl'), "ammo"),
    'ammo_glockclip': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmclip.mdl'), "ammo"),
    'ammo_mp5clip': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmARclip.mdl'), "ammo"),
    'ammo_mp5grenades': partial(handle_model_prop_with_collection, TinyPath('models/w_ARgrenade.mdl'), "ammo"),
    'crossbow_bolt': partial(handle_model_prop_with_collection, TinyPath('models/crossbow_bolt.mdl'), "ammo"),
    'cycler_prdroid': partial(handle_model_prop_with_collection, TinyPath('models/prdroid.mdl'), "monster"),
    'grenade': partial(handle_model_prop_with_collection, TinyPath('models/grenade.mdl'), "ammo"),
    'hornet': partial(handle_model_prop_with_collection, TinyPath('models/hornet.mdl'), "weapon"),
    'hvr_rocket': partial(handle_model_prop_with_collection, TinyPath('models/HVR.mdl'), "ammo"),
    'item_airtank': partial(handle_model_prop_with_collection, TinyPath('models/w_oxygen.mdl'), "item"),
    'item_antidote': partial(handle_model_prop_with_collection, TinyPath('models/w_antidote.mdl'), "item"),
    'item_security': partial(handle_model_prop_with_collection, TinyPath('models/w_security.mdl'), "item"),
    'item_sodacan': partial(handle_model_prop_with_collection, TinyPath('models/can.mdl'), "item"),
    'item_suit': partial(handle_model_prop_with_collection, TinyPath('models/w_suit.mdl'), "item"),
    'monster_alien_grunt': partial(handle_model_prop_with_collection, TinyPath('models/agrunt.mdl'), "monster"),
    'monster_alien_slave': partial(handle_model_prop_with_collection, TinyPath('models/islave.mdl'), "monster"),
    'monster_apache': partial(handle_model_prop_with_collection, TinyPath('models/apache.mdl'), "monster"),
    'monster_babycrab': partial(handle_model_prop_with_collection, TinyPath('models/baby_headcrab.mdl'), "monster"),
    'monster_barnacle': partial(handle_model_prop_with_collection, TinyPath('models/barnacle.mdl'), "monster"),
    'monster_barney_dead': partial(handle_model_prop_with_collection, TinyPath('models/barney.mdl'), "monster"),
    'monster_bigmomma': partial(handle_model_prop_with_collection, TinyPath('models/big_mom.mdl'), "monster"),
    'monster_bloater': partial(handle_model_prop_with_collection, TinyPath('models/floater.mdl'), "monster"),
    'monster_bullchicken': partial(handle_model_prop_with_collection, TinyPath('models/bullsquid.mdl'), "monster"),
    'monster_cine2_hvyweapons': partial(handle_model_prop_with_collection, TinyPath('models/cine2_hvyweapons.mdl'),
                                        "monster"),
    'monster_cine2_scientist': partial(handle_model_prop_with_collection,
                                       TinyPath('models/cine2-scientist.md,"monster')),
    'monster_cine2_slave': partial(handle_model_prop_with_collection, TinyPath('models/cine2_slave.mdl'), "monster"),
    'monster_cine3_barney': partial(handle_model_prop_with_collection, TinyPath('models/cine3-barney.md,"monster')),
    'monster_cine3_scientist': partial(handle_model_prop_with_collection,
                                       TinyPath('models/cine3-scientist.md,"monster')),
    'monster_cockroach': partial(handle_model_prop_with_collection, TinyPath('models/roach.mdl'), "monster"),
    'monster_flyer': partial(handle_model_prop_with_collection, TinyPath('models/boid.mdl'), "monster"),
    'monster_gargantua': partial(handle_model_prop_with_collection, TinyPath('models/garg.mdl'), "monster"),
    'monster_headcrab': partial(handle_model_prop_with_collection, TinyPath('models/headcrab.mdl'), "monster"),
    'monster_hevsuit_dead': partial(handle_model_prop_with_collection, TinyPath('models/player.mdl'), "monster"),
    'monster_hgrunt_dead': partial(handle_model_prop_with_collection, TinyPath('models/hgrunt.mdl'), "monster"),
    'monster_houndeye': partial(handle_model_prop_with_collection, TinyPath('models/houndeye.mdl'), "monster"),
    'monster_human_assassin': partial(handle_model_prop_with_collection, TinyPath('models/hassassin.mdl'), "monster"),
    'monster_human_grunt': partial(handle_model_prop_with_collection, TinyPath('models/hgrunt.mdl'), "monster"),
    'monster_ichthyosaur': partial(handle_model_prop_with_collection, TinyPath('models/icky.mdl'), "monster"),
    'monster_leech': partial(handle_model_prop_with_collection, TinyPath('models/leech.mdl'), "monster"),
    'monster_miniturret': partial(handle_model_prop_with_collection, TinyPath('models/miniturret.mdl'), "monster"),
    'monster_nihilanth': partial(handle_model_prop_with_collection, TinyPath('models/nihilanth.mdl'), "monster"),
    'monster_osprey': partial(handle_model_prop_with_collection, TinyPath('models/osprey.mdl'), "monster"),
    'monster_rat': partial(handle_model_prop_with_collection, TinyPath('models/bigrat.mdl'), "monster"),
    'monster_satchel': partial(handle_model_prop_with_collection, TinyPath('models/w_satchel.mdl'), "monster"),
    'monster_scientist_dead': partial(handle_model_prop_with_collection, TinyPath('models/scientist.mdl'), "monster"),
    'monster_sentry': partial(handle_model_prop_with_collection, TinyPath('models/sentry.mdl'), "monster"),
    'monster_snark': partial(handle_model_prop_with_collection, TinyPath('models/w_squeak.mdl'), "monster"),
    'monster_tentacle': partial(handle_model_prop_with_collection, TinyPath('models/tentacle2.mdl'), "monster"),
    'monster_tentaclemaw': partial(handle_model_prop_with_collection, TinyPath('models/maw.mdl'), "monster"),
    'monster_tripmine': partial(handle_model_prop_with_collection, TinyPath('models/w_tripmine.mdl'), "monster"),
    'monster_vortigaunt': partial(handle_model_prop_with_collection, TinyPath('models/islave.mdl'), "monster"),
    'monster_zombie': partial(handle_model_prop_with_collection, TinyPath('models/zombie.mdl'), "monster"),
    'player': partial(handle_model_prop_with_collection, TinyPath('models/player.mdl'), "monster"),
    'rpg_rocket': partial(handle_model_prop_with_collection, TinyPath('models/rpgrocket.mdl'), "ammo"),
    'spark_shower': partial(handle_model_prop_with_collection, TinyPath('models/grenade.mdl'), "ammo"),
    'weapon_9mmhandgun': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmhandgun.mdl'), "weapon"),
    'weapon_crowbar': partial(handle_model_prop_with_collection, TinyPath('models/w_crowbar.mdl'), "weapon"),
    'weapon_glock': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmhandgun.mdl'), "weapon"),
    'weapon_mp5': partial(handle_model_prop_with_collection, TinyPath('models/w_9mmAR.mdl'), "weapon"),
    'weapon_python': partial(handle_model_prop_with_collection, TinyPath('models/w_357.mdl'), "weapon"),
    'weapon_tripmine': partial(handle_model_prop_with_collection, TinyPath('models/v_tripmine.mdl'), "weapon"),
    'weaponbox': partial(handle_model_prop_with_collection, TinyPath('models/w_weaponbox.mdl'), "ammo"),
    'xen_hair': partial(handle_model_prop_with_collection, TinyPath('models/hair.mdl'), "monster"),
    'xen_plantlight': partial(handle_model_prop_with_collection, TinyPath('models/light.mdl'), "monster"),
    'xen_tree': partial(handle_model_prop_with_collection, TinyPath('models/tree.mdl'), "monster"),

    'monster_generic': handle_generic_model_prop,
    'cycler': handle_generic_model_prop,
    'cycler_sprite': handle_generic_model_prop,
    'env_model': handle_generic_model_prop,
}
