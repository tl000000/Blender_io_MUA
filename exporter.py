import bpy
import bmesh
import math
import mathutils
import struct

from math import sin, cos, pi

def write_some_data(context, filepath):
    print("running write_some_data...")
    f = open(filepath, 'wb')
    f.write(header)
    f.close()

    return {'FINISHED'}

def get_mesh_data():
    bpy.ops.object.select_by_type(extend=False,type='MESH')
    mesh_object = bpy.context.active_object
    
def get_bone_data():
    bpy.ops.object.select_by_type(extend=False,type='Armature')
    Armature_object = bpy.context.active_object


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper,orientation_helper
from bpy.types import Operator
from bpy.props import StringProperty

header = b'\x4D\x55\x41\x00\xEE\x03\x00\x00\x11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

class ExportMUA(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_scene.mua"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export MUA"

    # ExportHelper mixin class uses this
    filename_ext = ".MUA"

    filter_glob: StringProperty(
        default="*.MUA",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return write_some_data(context, self.filepath)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportMUA.bl_idname, text="Arcsys MUA Export(.MUA)")


# Register and add to the "file selector" menu (required to use F3 search "Text Export Operator" for quick access).
def register_exporter():
    bpy.utils.register_class(ExportMUA)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister_exporter():
    bpy.utils.unregister_class(ExportMUA)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_scene.MUA('INVOKE_DEFAULT')
