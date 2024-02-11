
import bpy
import bmesh
import math
import mathutils
import struct

def stripify(Tristriplist,bm):
    Ind = Tristriplist
    IndsCount = len(Tristriplist)
    for i in range(IndsCount - 2):
        Facelist.append((bm.verts[Ind[i]], bm.verts[Ind[i + 1]],bm.verts[Ind[i + 2]]))
    return Facelist
    
    
def read_Address(f):
    #get address and count for data block
    addr = []
    count = []
    for i in range(0,17):
        f.seek(0x20+i*0x8)
        addr.append(int.from_bytes(f.read(4),byteorder='little'))
        i += 1
        
    for i in range(0,17):
        f.seek(0x24+i*0x8)
        count.append(int.from_bytes(f.read(4),byteorder='little'))
        i += 1
        
    return addr,count
    
def read_stringname(f,addr,count):
    Name = []
    stringlength = []
    stringoffset = []
    for i in range(0, count[15]):
        f.seek(addr[15] + i * 0x10)
        stringoffset.append(int.from_bytes(f.read(4),byteorder='little'))
        stringlength.append(int.from_bytes(f.read(4),byteorder='little'))
        f.seek(addr[16] + stringoffset[i])
        Name.append(f.read(stringlength[i]).decode("shift-jis"))
    return Name
    
matrixX = []
matrixY = []
matrixZ = []
def read_Skeleton(f,addr,count,Name,CurCollection):
    for i in range(0,count[0]):
        f.seek(addr[0]+ i * 0x20)
        SkeletonIndex = int.from_bytes(f.read(4),byteorder='little')
        SkeletonBoneCount = int.from_bytes(f.read(4),byteorder='little')
        armature_data = bpy.data.armatures.new("Armature %u" %(i))
        armature_obj = bpy.data.objects.new("Armature %u" %(i), armature_data)
        CurCollection.objects.link(armature_obj)
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        for j in range(0,SkeletonBoneCount):
            f.seek(addr[1]+ j * 0x130)
            boneNameIndex = int.from_bytes(f.read(4),byteorder='little')
            boneType = int.from_bytes(f.read(4),byteorder='little',signed = True)
            trans = struct.unpack('<fff', f.read(4*3))
            Rot = struct.unpack('<fff', f.read(4*3))
            Scal = struct.unpack('<fff', f.read(4*3))
            bonetail = struct.unpack('<fff', f.read(4*3))
            boneIndex = int.from_bytes(f.read(4),byteorder='little')
            bonePIndex = int.from_bytes(f.read(4),byteorder='little',signed = True)
            boneCIndex = int.from_bytes(f.read(4),byteorder='little',signed = True)
            boneSIndex = int.from_bytes(f.read(4),byteorder='little',signed = True)
            matrixX.append(struct.unpack('<ffff', f.read(4*4)))
            matrixX.append(struct.unpack('<ffff', f.read(4*4)))
            matrixX.append(struct.unpack('<ffff', f.read(4*4)))
            matrixX.append(struct.unpack('<ffff', f.read(4*4)))
            matrixY.append(struct.unpack('<ffff', f.read(4*4)))
            matrixY.append(struct.unpack('<ffff', f.read(4*4)))
            matrixY.append(struct.unpack('<ffff', f.read(4*4)))
            matrixY.append(struct.unpack('<ffff', f.read(4*4)))
            matrixZ.append(struct.unpack('<ffff', f.read(4*4)))
            matrixZ.append(struct.unpack('<ffff', f.read(4*4)))
            matrixZ.append(struct.unpack('<ffff', f.read(4*4)))
            matrixZ.append(struct.unpack('<ffff', f.read(4*4)))
            framecount = int.from_bytes(f.read(4),byteorder='little')
            
            eul = mathutils.Euler(Rot, 'XYZ')
            
            edit_bone = armature_obj.data.edit_bones.new(Name[boneNameIndex])
            edit_bone.use_connect = False
            edit_bone.use_local_location = True
            edit_bone.head = (0,0,0)
            edit_bone.tail = bonetail
            edit_bone.matrix = matrixX
            matrixX.clear()
            matrixY.clear()
            matrixZ.clear()
            
            if bonePIndex != -1:
               edit_bone.parent = armature_obj.data.edit_bones[bonePIndex]
               
    bpy.ops.object.mode_set(mode='OBJECT')

Tristriplist = []
Facelist = []
def read_mesh(f,addr,count,Name,CurCollection):
    for m in range(0,count[2]):
        f.seek(addr[2]+ m * 0xC0)
        SkeletonIndex = struct.unpack('<f', f.read(4))
        _,VertextGroupCount = f.read(4),int.from_bytes(f.read(4),byteorder='little')
        VertextGroupOffset = int.from_bytes(f.read(4),byteorder='little')
        VertextCount = int.from_bytes(f.read(4),byteorder='little')
        VertexOffset = int.from_bytes(f.read(4),byteorder='little')
        _,MNIndex = f.read(156),int.from_bytes(f.read(4),byteorder='little')
        MSRIndex = int.from_bytes(f.read(4),byteorder='little')
        
        mesh = bpy.data.meshes.new("Mesh")
        obj = bpy.data.objects.new("MyObject", mesh)
        CurCollection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        
        mesh = bpy.context.object.data
        bm = bmesh.new()
        
        for v in range(0,VertextCount):
            f.seek(addr[13]+ v * 0x50)
            vec = mathutils.Vector(struct.unpack('<fff', f.read(4*3)))
            nrm = mathutils.Vector(struct.unpack('<fff', f.read(4*3)))
            tan = mathutils.Vector(struct.unpack('<fff', f.read(4*3)))
            UV = mathutils.Vector(struct.unpack('<ff', f.read(4*2)))
            vert = bm.verts.new(vec)
            vert.normal = nrm
        
        for g in range(0,VertextGroupCount):
            f.seek(addr[3]+ g * 0x20)
            MatIndex  = int.from_bytes(f.read(4),byteorder='little')
            FIcount = int.from_bytes(f.read(4),byteorder='little')
            FIoffset = int.from_bytes(f.read(4),byteorder='little')
            f.seek(addr[14]+ FIoffset * 0x2)
            for i in range(0,FIcount):
                Tristriplist.append(int.from_bytes(f.read(2),byteorder='little'))
            Facelist = stripify(Tristriplist,bm)
            for f in Facelist:
                face = bm.faces.new()
                face.verts = 
            
            
        bm.to_mesh(mesh)
        bm.free()
        
        

def read_some_data(context, filepath):
    f = open(filepath, 'rb')
    
    CurCollection = bpy.data.collections.new("Mesh Collection")
    bpy.context.scene.collection.children.link(CurCollection)
    
    addr,count = read_Address(f)
    Name = read_stringname(f,addr,count)
    #read_Skeleton(f,addr,count,Name,CurCollection)
    read_mesh(f,addr,count,Name,CurCollection)
    
    f.close()

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator


class ImportMUA(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_scene.mua"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import MUA"

    # ImportHelper mixin class uses this
    filename_ext = ".MUA"

    filter_glob: StringProperty(
        default="*.MUA",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return read_some_data(context, self.filepath)


# Only needed if you want to add into a dynamic menu.
def menu_func_import(self, context):
    self.layout.operator(ImportMUA.bl_idname, text="Arcsys MUA Import(.MUA)")


# Register and add to the "file selector" menu (required to use F3 search "MUA Import Operator" for quick access).
def register_importer():
    bpy.utils.register_class(ImportMUA)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister_importer():
    bpy.utils.unregister_class(ImportMUA)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_scene.MUA('INVOKE_DEFAULT')
