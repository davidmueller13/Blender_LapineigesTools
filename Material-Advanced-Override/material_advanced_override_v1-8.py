######################################################################################################
# A simple add-on that enhance the override material tool (from renderlayer panel)                   #
# Author: Lapineige                                                                                  #
# License: GPL v3                                                                                    #
######################################################################################################


############# Add-on description (used by Blender)

bl_info = {
    "name": "Material Advanced Override",
    "description": 'Material Override Tools - with advanced exclude options',
    "author": "Lapineige",
    "version": (1, 8),
    "blender": (2, 72, 0),
    "location": "Properties > Render Layers",
    "warning": "",
    "wiki_url": "http://le-terrier-de-lapineige.over-blog.com/2015/05/add-on-advanced-material-override-regler-votre-eclairage-plus-facilement.html",
    "tracker_url": "http://blenderlounge.fr/forum/viewtopic.php?f=26&t=810",
    "category": "Render"}

import bpy
import blf
from bpy.app.handlers import persistent

############
# Properties

bpy.types.Scene.OW_only_selected = bpy.props.BoolProperty(name='Affect Only Selected', default=False, description='Override material only for selected objects')
bpy.types.Scene.OW_exclude_type = bpy.props.EnumProperty(items=[('index','Material Index','Exclude by Material Index',0),('group','Group','Exclude by Object Group',1),('layer','Layer','Exclude by Layer',2),('emit','Emit','Exclude materials using emission shader',3)], description='Set exclusion criteria')
bpy.types.Scene.OW_pass_index = bpy.props.IntProperty(name='Pass Index', default=1, description='(Material) pass index exclude')
bpy.types.Scene.OW_material = bpy.props.StringProperty(name='Material', maxlen=63, description='Material to exclude')
bpy.types.Scene.OW_group = bpy.props.StringProperty(name='Group', maxlen=63, description='Group of objects to exclude')
bpy.types.Scene.OW_display_override = bpy.props.BoolProperty(name="Show 'Override ON' Reminder", default=True, description="Show 'Override On' in the 3D view")
bpy.types.Scene.OW_start_on_render = bpy.props.BoolProperty(name="Override Render", default=False, description='Override material during render')
bpy.types.Scene.OW_vis_hide_camera_rays = bpy.props.BoolProperty(name="Camera", default=False, description='Hide excluded objects from Camera rays')
bpy.types.Scene.OW_vis_hide_diffuse_rays = bpy.props.BoolProperty(name="Diffuse", default=False, description='Hide excluded objects from Diffuse rays')
bpy.types.Scene.OW_vis_hide_glossy_rays = bpy.props.BoolProperty(name="Glossy", default=False, description='Hide excluded objects from Glossy rays')
bpy.types.Scene.OW_vis_hide_transmission_rays = bpy.props.BoolProperty(name="Transmission", default=False, description='Hide excluded objects from Transmission rays')
bpy.types.Scene.OW_vis_hide_shadow_rays = bpy.props.BoolProperty(name="Shadow", default=False, description='Hide excluded objects from Shadow rays')
bpy.types.Scene.OW_vis_hide_scatter_rays = bpy.props.BoolProperty(name="Scatter", default=False, description='Hide excluded objects from Volume scatter rays')

############

def draw_callback_px(self, context):
    if context.scene.OW_display_override:
        font_id = 0  # XXX, need to find out how best to get this
        blf.position(font_id, 28, bpy.context.area.height-85, 0)
        blf.draw(font_id, "Override ON")

############
# Layout

class AdvancedMaterialOverride(bpy.types.Panel):
    """  """
    bl_label = "Advanced Material Override"
    bl_idname = "advanced_material_override"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render_layer"

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        if bpy.types.RENDER_OT_override_setup.l_mat:
            row.operator('render.override_restore')
            row.prop(context.scene, 'OW_start_on_render', toggle=True, icon='RENDER_STILL')
            layout.prop(context.scene, 'OW_display_override')
        else:
            row.operator('render.override_setup')
            row.prop(context.scene, 'OW_start_on_render', toggle=True, icon='RENDER_STILL')#.enabled = False

        layout.prop_search(context.scene, "OW_material", bpy.data, "materials", icon='MATERIAL_DATA')
        row = layout.row()
        row.prop(context.scene, 'OW_only_selected', toggle=True, icon='BORDER_RECT')

        box = layout.box()
        if bpy.types.RENDER_OT_override_setup.l_mat:
            box.enabled = False
            row.enabled = False
        #else:
            #box.enabled = True
            #row.enabled = True

        box.label('Objects not affected:')
        row = box.row()
        row.prop(context.scene, 'OW_exclude_type', expand=True)
        if context.scene.OW_exclude_type == 'index':
            box.prop(context.scene, 'OW_pass_index')
        elif context.scene.OW_exclude_type == 'group':
            box.prop_search(context.scene, "OW_group", bpy.data, "groups", icon='GROUP')
        elif context.scene.OW_exclude_type == 'layer':
            box.prop(context.scene, 'override_layer', text='')
        box.label('Ray visibility - Hide:')
        row = box.row(align=True)
        col = row.column(align=True)
        col.prop(context.scene, 'OW_vis_hide_camera_rays', toggle=True, icon='RESTRICT_VIEW_ON')
        col.prop(context.scene, 'OW_vis_hide_diffuse_rays', toggle=True, icon='RESTRICT_VIEW_ON')
        col.prop(context.scene, 'OW_vis_hide_glossy_rays', toggle=True, icon='RESTRICT_VIEW_ON')
        col = row.column(align=True)
        col.prop(context.scene, 'OW_vis_hide_transmission_rays', toggle=True, icon='RESTRICT_VIEW_ON')
        col.prop(context.scene, 'OW_vis_hide_shadow_rays', toggle=True, icon='RESTRICT_VIEW_ON')
        col.prop(context.scene, 'OW_vis_hide_scatter_rays', toggle=True, icon='RESTRICT_VIEW_ON')

############
# Viewport

class OverrideDraw(bpy.types.Operator):
    """  """
    bl_idname = "view3d.display_override"
    bl_label = "Display Override"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        #context.area.tag_redraw()
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        return {'FINISHED'}

############
# Operators

class OverrideSetup(bpy.types.Operator):
    """ Override the materials and store the data needed to revert it """
    bl_idname = "render.override_setup"
    bl_label = "Override Setup"

    l_mat = list()
    l_mesh = list()
    l_hidden = list()

    bpy.types.Scene.override_layer = bpy.props.BoolVectorProperty(subtype='LAYER', size=20, default=[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

    @classmethod
    def poll(cls, context):
        if not bpy.context.scene.render.engine == 'CYCLES':
            return False
        if context.scene.OW_exclude_type == 'group' and not context.scene.OW_group:
            return False
        if context.scene.OW_exclude_type == 'layer' and not True in [i for i in context.scene.override_layer]:
            return False
        return context.scene.OW_material

    def execute(self, context):

        for obj in bpy.data.objects:
            for rd_layer in context.scene.render.layers: # INFO: the render layers also have a layers property #TODO check for renderlayer before parsing list of object ? (might be an issue if rdlayer feature is not used)
                if (obj.select == True)*context.scene.OW_only_selected or not context.scene.OW_only_selected:
                    if not hasattr(obj.data,'name'): # for empty, camera, lamp
                        continue
                    if False: #renderlayer: TODO
                         if not True in [l == list(obj.layers) for l in list(rd_layer.layers)]: # to be sure object is on this renderlayer
                            continue

                    if not obj.data.name in self.l_mesh: # test mesh instead of object -> in case of instancing, avoid duplicate and save some performance
                        self.l_mesh.append(obj.data.name)
                    else:
                        continue

                    if not len(obj.material_slots) and hasattr(obj.data,'materials'):
                        new_mat = bpy.data.materials.new('Default')
                        obj.data.materials.append(new_mat)
                    elif len(obj.material_slots):
                        if context.scene.OW_exclude_type == 'index':
                            if not obj.material_slots[0].material.pass_index == context.scene.OW_pass_index:
                                if context.scene.OW_material:
                                    self._save_mat(obj)
                                    self._change_mat(context,obj)
                                    obj.material_slots[0].material = bpy.data.materials[context.scene.OW_material]
                            else:
                                if context.scene.OW_vis_hide_camera_rays: #TODO this should be optimised to use only 1 tuple for 1 object, and not a list of tuples (duplicating obj data)
                                    self.l_hidden.append( (obj,obj.cycles_visibility.camera,'camera') )
                                    obj.cycles_visibility.camera = False
                                if context.scene.OW_vis_hide_diffuse_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.diffuse,'diffuse') )
                                    obj.cycles_visibility.diffuse = False
                                if context.scene.OW_vis_hide_glossy_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.glossy,'glossy') )
                                    obj.cycles_visibility.glossy = False
                                if context.scene.OW_vis_hide_transmission_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.transmission,'transmission') )
                                    obj.cycles_visibility.transmission = False
                                if context.scene.OW_vis_hide_shadow_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.shadow,'shadow') )
                                    obj.cycles_visibility.shadow = False
                                if context.scene.OW_vis_hide_scatter_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.scatter,'scatter') )
                                    obj.cycles_visibility.scatter = False

                        elif context.scene.OW_exclude_type == 'group' and context.scene.OW_group:
                            if obj.name in [g_obj.name for g_obj in bpy.data.groups[context.scene.OW_group].objects]:
                                if context.scene.OW_material:
                                    self._save_mat(obj)
                                    self._change_mat(context, obj)
                                    obj.material_slots[0].material = bpy.data.materials[context.scene.OW_material]
                            else:
                                if context.scene.OW_vis_hide_camera_rays: #TODO this should be optimised to use only 1 tuple for 1 object, and not a list of tuples (duplicating obj data)
                                    self.l_hidden.append( (obj,obj.cycles_visibility.camera,'camera') )
                                    obj.cycles_visibility.camera = False
                                if context.scene.OW_vis_hide_diffuse_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.diffuse,'diffuse') )
                                    obj.cycles_visibility.diffuse = False
                                if context.scene.OW_vis_hide_glossy_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.glossy,'glossy') )
                                    obj.cycles_visibility.glossy = False
                                if context.scene.OW_vis_hide_transmission_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.transmission,'transmission') )
                                    obj.cycles_visibility.transmission = False
                                if context.scene.OW_vis_hide_shadow_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.shadow,'shadow') )
                                    obj.cycles_visibility.shadow = False
                                if context.scene.OW_vis_hide_scatter_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.scatter,'scatter') )
                                    obj.cycles_visibility.scatter = False

                        elif context.scene.OW_exclude_type == 'layer':
                            if not (True in [(context.scene.override_layer[index])*(context.scene.override_layer[index]==obj.layers[index]) for index in range(len(obj.layers))]):
                                if context.scene.OW_material:
                                    self._save_mat(obj)
                                    self._change_mat(context, obj)
                                    obj.material_slots[0].material = bpy.data.materials[context.scene.OW_material]
                            else:
                                if context.scene.OW_vis_hide_camera_rays: #TODO this should be optimised to use only 1 tuple for 1 object, and not a list of tuples (duplicating obj data)
                                    self.l_hidden.append( (obj,obj.cycles_visibility.camera,'camera') )
                                    obj.cycles_visibility.camera = False
                                if context.scene.OW_vis_hide_diffuse_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.diffuse,'diffuse') )
                                    obj.cycles_visibility.diffuse = False
                                if context.scene.OW_vis_hide_glossy_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.glossy,'glossy') )
                                    obj.cycles_visibility.glossy = False
                                if context.scene.OW_vis_hide_transmission_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.transmission,'transmission') )
                                    obj.cycles_visibility.transmission = False
                                if context.scene.OW_vis_hide_shadow_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.shadow,'shadow') )
                                    obj.cycles_visibility.shadow = False
                                if context.scene.OW_vis_hide_scatter_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.scatter,'scatter') )
                                    obj.cycles_visibility.scatter = False

                        elif context.scene.OW_exclude_type == 'emit':
                            if not self._check_if_emit(context, obj):
                                if context.scene.OW_material:
                                    self._save_mat(obj)
                                    self._change_mat(context, obj)
                                    obj.material_slots[0].material = bpy.data.materials[context.scene.OW_material]
                            else:
                                if context.scene.OW_vis_hide_camera_rays: #TODO this should be optimised to use only 1 tuple for 1 object, and not a list of tuples (duplicating obj data)
                                    self.l_hidden.append( (obj,obj.cycles_visibility.camera,'camera') )
                                    obj.cycles_visibility.camera = False
                                if context.scene.OW_vis_hide_diffuse_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.diffuse,'diffuse') )
                                    obj.cycles_visibility.diffuse = False
                                if context.scene.OW_vis_hide_glossy_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.glossy,'glossy') )
                                    obj.cycles_visibility.glossy = False
                                if context.scene.OW_vis_hide_transmission_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.transmission,'transmission') )
                                    obj.cycles_visibility.transmission = False
                                if context.scene.OW_vis_hide_shadow_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.shadow,'shadow') )
                                    obj.cycles_visibility.shadow = False
                                if context.scene.OW_vis_hide_scatter_rays:
                                    self.l_hidden.append( (obj,obj.cycles_visibility.scatter,'scatter') )
                                    obj.cycles_visibility.scatter = False
        return {'FINISHED'}

    def _save_mat(self, obj):
        self.l_mat.append( (obj,[]) ) #### TODO
        for slot in obj.material_slots:
            self.l_mat[-1][1].append( (slot,slot.material) )

    def _change_mat(self, context, obj):
        for slot in obj.material_slots:
            slot.material = bpy.data.materials[context.scene.OW_material]

    def _check_if_emit(self, context, obj):
        for slot in obj.material_slots:
            if not hasattr(slot.material,'node_tree.nodes'): # need node_tree.nodes to be sure it is not a group (in this case the empty has no node-tree)
                continue
            for node in slot.material.node_tree.nodes:
                if node.type == 'EMISSION':
                    return True
        return False

class OverrideRestore(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "render.override_restore"
    bl_label = "Override Restore"

    def execute(self, context):
        context.scene.OW_display_override = False

        for data in bpy.types.RENDER_OT_override_setup.l_mat:
            print('DATA: ', data)
            obj, mat_data = data
            if bpy.data.objects.find(obj.name) != -1: # to be sure obj exist => avoid crash
                for slot, material in mat_data:
                    slot.material = material
            else:
                self.report({'WARNING'}, 'Failed to restore material for object: ' + obj.name)

        for data in bpy.types.RENDER_OT_override_setup.l_hidden:
            obj,visibility,type = data

            if type == 'camera':
                obj.cycles_visibility.camera = visibility
            elif type == 'diffuse':
                obj.cycles_visibility.diffuse = visibility
            elif type == 'glossy':
                obj.cycles_visibility.glossy = visibility
            elif  type == 'transmission':
                obj.cycles_visibility.transmission = visibility
            elif type == 'shadow':
                obj.cycles_visibility.shadow = visibility
            elif type == 'scatter':
                obj.cycles_visibility.scatter = visibility

        bpy.types.RENDER_OT_override_setup.l_mat = list()
        bpy.types.RENDER_OT_override_setup.l_mesh = list()
        bpy.types.RENDER_OT_override_setup.l_hidden = list()
        return {'FINISHED'}

############
# Handlers

@persistent
def stop_on_save(dummy):
    if bpy.types.RENDER_OT_override_setup.l_mat:
        bpy.ops.render.override_restore()

@persistent
def mat_override_pre_render(dummy):
    if not bpy.types.RENDER_OT_override_setup.l_mat:
        if bpy.context.scene.OW_start_on_render and bpy.ops.render.override_setup.poll():
            bpy.ops.render.override_setup()
@persistent
def mat_override_post_render(dummy):
    if bpy.context.scene.OW_start_on_render:
        bpy.ops.render.override_restore()

@persistent
def mat_override_stop_on_load(dummy):
    if hasattr(bpy.types, 'RENDER_OT_override_setup'): # as it is persistent, need to be sure the add-on is active
        if bpy.types.RENDER_OT_override_setup.l_mesh:
            bpy.ops.render.override_restore()

##############

def register():
    bpy.utils.register_class(OverrideSetup)
    bpy.utils.register_class(OverrideRestore)
    bpy.utils.register_class(AdvancedMaterialOverride)
    bpy.utils.register_class(OverrideDraw)
    #bpy.ops.view3d.display_override()

    bpy.app.handlers.save_pre.append(stop_on_save)
    bpy.app.handlers.render_init.append(mat_override_pre_render)
    bpy.app.handlers.render_post.append(mat_override_post_render)
    bpy.app.handlers.load_pre.append(mat_override_stop_on_load)

def unregister():
    if bpy.types.RENDER_OT_override_setup.l_mat:
            bpy.ops.render.override_restore() # To make sure materials will be restored
    bpy.utils.unregister_class(OverrideSetup)
    bpy.utils.unregister_class(OverrideRestore)
    bpy.utils.unregister_class(AdvancedMaterialOverride)
    bpy.utils.unregister_class(OverrideDraw)
    bpy.app.handlers.save_pre.remove(stop_on_save)
    bpy.app.handlers.render_init.remove(mat_override_pre_render)
    bpy.app.handlers.render_post.remove(mat_override_post_render)
    bpy.app.handlers.load_pre.remove(mat_override_stop_on_load)


if __name__ == "__main__":
    register()
