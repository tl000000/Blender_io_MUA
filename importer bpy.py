import bpy
import struct
from bpy.props import StringProperty, FilePath
from bpy_extras.io_utils import ImportHelper

class MuaImport(bpy.types.Operator, ImportHelper):
    bl_idname = "import_mua.mua"
    bl_label = "Import MUA File"
    filename_ext = ".mua"

    def execute(self, context):
        filepath = self.filepath
        try:
            with open(filepath, 'rb') as f:
                # 读取文件头信息
                file_header = f.read(0x20)
                
                # 解析前4字节为文件名标识
                file_id = struct.unpack('I', file_header[0:4])[0]
                
                # 版本号
                version = struct.unpack('I', file_header[4:8])[0]
                
                # 数据类型数
                data_type_count = struct.unpack('I', file_header[8:12])[0]

                # 定义地址表数据类型的顺序和处理函数
                if version == 1007:
                    data_types_order = [
                        'skeleton', 'bone', 'mesh', 'vertex_group', 
                        'material', 'texture', 'texture_name_index',
                        'uv_animation', 'bone_animation_list', 
                        'bone_animation_values', 'color_mixer_animation',
                        'evb_filename_index', 'polygon_and_vertex_group_index',
                        'vertex_info', 'triangle_strip_list', 
                        'name_info_index', 'name'
                    ]
                elif version == 1008:
                    data_types_order = [
                        'skeleton', 'bone', 'mesh', 'vertex_group', 
                        'material', 'texture', 'texture_name_index',
                        'uv_animation', 'bone_animation_list', 
                        'bone_animation_values', 'color_mixer_animation',
                        'evb_filename_index', 'polygon_and_vertex_group_index',
                        'vertex_info', 'triangle_strip_list', 
                        'name_info_index', 'name', 'evb_file_info'
                    ]
                else:
                    self.report({'ERROR'}, "Unsupported MUA version: {}".format(version))
                    return {'CANCELLED'}

                # 创建数据类型到处理函数的映射
                data_type_handlers = {
                    'skeleton': self.handle_skeleton,
                    'bone': self.handle_bone,
                    'mesh': self.handle_mesh,
                    'vertex_group': self.handle_vertex_group,
                    'material': self.handle_material,
                    'texture': self.handle_texture,
                    'texture_name_index': self.handle_texture_name_index,
                    'uv_animation': self.handle_uv_animation,
                    'bone_animation_list': self.handle_bone_animation_list,
                    'bone_animation_values': self.handle_bone_animation_values,
                    'color_mixer_animation': self.handle_color_mixer_animation,
                    'evb_filename_index': self.handle_evb_filename_index,
                    'polygon_and_vertex_group_index': self.handle_polygon_and_vertex_group_index,
                    'vertex_info': self.handle_vertex_info,
                    'triangle_strip_list': self.handle_triangle_strip_list,
                    'name_info_index': self.handle_name_info_index,
                    'name': self.handle_name,
                    'evb_file_info': self.handle_evb_file_info
                }


                single_data_size = [
                    0x20,#skeleton
                    0x130,#bone
                    0xc0,#mesh
                    0x20,#vertex_group
                    0x50,#material
                    0x20,#texture
                    0x10,#texture_name_index
                    0x1c,#uv_animation
                    0x10,#bone_animation_list
                    0x20,#bone_animation_values
                    0x20,#color_mixer_animation
                    0x10,#evb_filename_index
                    0x20,#polygon_and_vertex_group_index
                    0x50,#vertex_info
                    0x1,#triangle_strip_list
                    0x10,#name_info_index
                    0x1,#name
                    0x4#evb_file_info
                ]

                # 地址表解析
                address_table_start = 0x20
                
                for i in range(data_type_count):
                    # 每个地址表项占8字节，前4字节为起始地址，后4字节为数量
                    f.seek(address_table_start + (i-1) * 8)
                    data_block_address, data_block_count = struct.unpack('II', f.read(8))
                    
                    # 获取数据类型名称
                    data_type_name = data_types_order[i]
                    
                    # 调用对应的处理函数
                    handler = data_type_handlers.get(data_type_name, None)

                    parsed_data =[]
                    if handler:
                        f.seek(data_block_address)
                        if data_block_count:
                            block_data = f.read(data_block_count * single_data_size[i])
                            parsed_data[data_type_name] = handler(block_data, data_block_count)
                        else:
                            continue
                    else:
                        self.report({'WARNING'}, "Unhandled data type: {}".format(data_type_name))

                # 创建blender对象
                self.create_blender_objects(parsed_data)

                return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

    # 数据块处理函数示例（需要根据具体格式实现）
    def handle_skeleton(self, data, count):
        # 解析skeleton数据块的前8字节：前4字节为偏移数，后4字节为骨骼数量
        index = 0
        skeleton = []
        for _ in range(count):

            bone_offset = struct.unpack('I', data, offset=index)
            index += 4
            bone_count = struct.unpack('I', data, offset=index)
            index += 4
            wunknow1,wunknow2,wunknow3 = struct.unpack('Iff', data, offset=index)
            index += 0x18

            skeleton.append({
                'bone_offset':bone_offset,
                'bone_count':bone_count,
                'unknow':(wunknow1,wunknow2,wunknow3)
            })
        return skeleton
        
    def handle_bone(self, data, count):
        index = 0
        bone = []
        for _ in range(count):
            bone_name_index = struct.unpack('I', data, offset=index)
            index += 4
            bone_type = struct.unpack('I', data, offset=index)
            index += 4
            position_z, position_x, position_y = struct.unpack('fff', data, offset=index)
            index += 12
            rotation_z,rotation_x, rotation_y= struct.unpack('fff', data, offset=index)#radian
            index += 12
            scale_z,scale_x,scale_y = struct.unpack_from('fff', data, offset=index)
            index += 12
            unknow_z,unknow_x,unknow_y = struct.unpack('fff', data, offset=index)
            index += 12
            bone_index = struct.unpack('I', data, offset=index)
            index += 4
            parent_bone_index = struct.unpack('I', data, offset=index)
            index += 4
            child_bone_index = struct.unpack('I', data, offset=index)
            index += 4
            sibling_bone_index = struct.unpack('I', data, offset=index)
            index += 4
            matrices = []
            for _ in range(3):
                matrix = struct.unpack_from('<16f', data, offset=index)
                matrices.append(matrix)
                index += 64
            keyframe_count = struct.unpack_from('<I', data, offset=index)[0]
            index += 4
            keyframe_indices = struct.unpack_from('<4I', data, offset=index)
            index += 16
            
            index += 0x20 #no data

            bone.append({
                'name_index': bone_name_index,
                'bone_type': bone_type,
                'position': (position_x, position_y, position_z),  # 调整为 X、Y、Z 顺序
                'rotation': (rotation_z,rotation_x, rotation_y),
                'scale': (scale_z,scale_x,scale_y) ,
                'unknow': (unknow_z,unknow_x,unknow_y),  # 调整为 X、Y、Z 顺序
                'bone_index': bone_index,
                'parent_index': parent_bone_index,
                'child_index': child_bone_index,
                'sibling_index': sibling_bone_index,
                'matrices': matrices,#three axis Transform matrix 
                'keyframe_count': keyframe_count,
                'keyframe_indices': keyframe_indices
            })

        return bone

    def handle_mesh(self, data, count):
        index = 0
        mesh = []
        for _ in range(count):
            bind_skeleton_index = struct.unpack('f', data, offset=index)
            index += 8
            vertex_group_count = struct.unpack('I', data, offset=index)
            index += 4
            vertex_group_offset = struct.unpack('I', data, offset=index)
            index += 4
            vertex_count = struct.unpack('I', data, offset=index)
            index += 4
            vertex_offset = struct.unpack('I', data, offset=index)
            index += 4
            unknow = struct.unpack('38f', data, offset=index)#LOD or something
            index += 156
            name_index = struct.unpack('I', data, offset=index)
            index += 4
            skeletion_index = struct.unpack('I', data, offset=index)
            index += 4
            
            index += 4#no data

            mesh.append({
                'skeleton': bind_skeleton_index,
                'group_count': vertex_group_count,
                'group_offset': vertex_group_offset,
                'vertex_count': vertex_count,
                'vertex_offset': vertex_offset,
                'unknow': unknow,
                'name_index': name_index,
                'root': skeletion_index
            })
        return mesh

    def handle_vertex_group(self, data, count):
        index = 0
        group = []
        for _ in range(count):
            matirial_index = struct.unpack('I', data, offset=index)
            index += 4
            trianglestrp_count = struct.unpack('I', data, offset=index)
            index += 4
            trianglestrp_offset = struct.unpack('I', data, offset=index)
            index += 4
            evb_value_offset = struct.unpack('I', data, offset=index)
            index += 4
            evb_value_count = struct.unpack('I', data, offset=index)
            index += 4

            index += 12#no data

            group.append({
                'mat_index': matirial_index,
                'strip_count': trianglestrp_count,
                'strip_offset': trianglestrp_offset,
                'evb_offset': evb_value_offset,
                'evb_count': evb_value_count,
            })
        return group

    def handle_material(self, data, count):
        index = 0
        matirial = []
        for _ in range(count):
            texture_count = struct.unpack('I', data, offset=index)
            index += 4
            texture_offset = struct.unpack('I', data, offset=index)
            index += 8
            mat_value = struct.unpack('12f', data, offset=index)
            index += 48
            color_blend = struct.unpack('I', data, offset=index)
            index += 4
            color_blend_frame = struct.unpack('I', data, offset=index)
            index += 4

            index +=12#no data

            matirial.append({
                'tex_count': texture_count,
                'tex_offset': texture_offset,
                'mat': mat_value,
                'color_blend': color_blend,
                'color_blend_frame': color_blend_frame,
            })
        return matirial

    def handle_texture(self, data, count):
        index = 0
        texture = []
        for _ in range(count):
            self_index = struct.unpack('I', data, offset=index)
            index += 4
            self_offset = struct.unpack('I', data, offset=index)
            index += 4
            uv_anim_count = struct.unpack('I', data, offset=index)
            index += 4
            uv_anim_offset = struct.unpack('I', data, offset=index)
            index += 4

            index += 16#no data
            
            texture.append({
                'self_index':self_index,
                'self_offset': self_offset,
                'uv_anime_frame': uv_anim_count,
                'uv_anime_offset': uv_anim_offset,

            })
        return texture

    def handle_texture_name_index(self, data, count):
        index = 0
        tex_name = []
        for _ in range(count):
            tex_name_index = struct.unpack('I', data, offset=index)
            index += 4
            
            index += 12#no data

            tex_name.append({
                'index':tex_name_index
            })
        
        return tex_name

    def handle_uv_animation(self, data, count):
        index = 0
        uv_anim = []
        for _ in range(count):
            move_x = struct.unpack('I', data, offset=index)
            index += 4
            move_y = struct.unpack('I', data, offset=index)
            index += 4
            scale_x = struct.unpack('I', data, offset=index)
            index += 4
            scale_y = struct.unpack('I', data, offset=index)
            index += 4
            keyframe = struct.unpack('I', data, offset=index)
            index += 4

            index +=8

            uv_anim.append({
                'move_x':move_x,
                'move_y':move_y,
                'scale_x':scale_x,
                'scale_y':scale_y,
                'keyframe':keyframe
            })

    def handle_bone_animation_list(self, data, count):
        index = 0
        anim_list = []
        for _ in range(count):
            transition = struct.unpack('I', data, offset=index)
            index += 16
            rotation = struct.unpack('I', data, offset=index)
            index += 16
            Shearing = struct.unpack('I', data, offset=index)
            index += 16
            scale = struct.unpack('I', data, offset=index)
            index += 16

            anim_list.append({
                'index':(transition,rotation,Shearing,scale)
            })

    def handle_bone_animation_values(self, data, count):
        index = 0
        anim = []
        for _ in range(count):
            value1,value2,value3,value4 = struct.unpack('4f', data, offset=index)
            index += 16
            frame = struct.unpack('I', data, offset=index)
            index += 4

            index += 12#no data

            anim.append({
                'data':(value1,value2,value3,value4),
                'frame':frame
            })
            

    def handle_color_mixer_animation(self, data, count):
        index = 0
        blend = []
        for _ in range(count):
            alphy,blue,green,red = struct.unpack('4f', data, offset=index)
            index += 16
            
            index += 16
            
            blend.append({
                'color':(alphy,blue,green,red)
            })


    def handle_evb_filename_index(self, data, count):
        index = 0
        evb_name = []
        for _ in range(count):
            evb_name_index = struct.unpack('I', data, offset=index)
            index += 4
            
            index += 12#no data

            evb_name.append({
                'index':evb_name_index
            })
        
        return evb_name

    def handle_polygon_and_vertex_group_index(self, data, count):
        index = 0
        M_G = []
        for _ in range(count):
            M_index = struct.unpack('I', data, offset=index)
            index += 4
            G_index = struct.unpack('I', data, offset=index)
            index += 4
            
            index += 24#no data

            M_G.append({
                'M_index':M_index,
                'G_index':G_index
            })
        
        return M_G

    def handle_vertex_info(self, data, count):
        index = 0
        vert = []
        for _ in range(count):
            position_z, position_x, position_y = struct.unpack('fff', data, offset=index)
            index += 12
            normal_z, normal_x, normal_y = struct.unpack('fff', data, offset=index)
            index += 12
            tanget_z, tanget_x, tanget_y = struct.unpack('fff', data, offset=index)
            index += 12
            uv_x, uv_y = struct.unpack('ff', data, offset=index)
            index += 12
            index += 4
            b, g, r, a = struct.unpack('4B', data, offset=index)
            index += 4
            bone1, bone2, bone3 = struct.unpack('fff', data, offset=index)
            index += 12
            weight1, weight2, weight3 = struct.unpack('fff', data, offset=index)
            index += 12

            vert.append({
                'position': (position_x, position_y, position_z),
                'normal': (normal_z, normal_x, normal_y),
                'tanget': (tanget_z, tanget_x, tanget_y),
                'uv': (uv_x, uv_y),
                'vert_color': (r, g, b, a),
                'weight_bone': (bone1, bone2, bone3),
                'weight_value': (weight1, weight2, weight3)
            })
        
        return vert

    def handle_triangle_strip_list(self, data, count):
        index = 0
        strip = []
        for _ in range(count):
            vert_index = struct.unpack('b', data, offset=index)
            index += 1

            strip.append({
                'vert': vert_index
            })

        return strip

    def handle_name_info_index(self, data, count):
        index = 0
        names_list = []
        for _ in range(count):
            name_offset = struct.unpack('I', data, offset=index)
            index += 4
            name_lengh = struct.unpack('I', data, offset=index)
            index += 4

            index += 8#no data

            names_list.append({
                'offset':name_offset,
                'lengh':name_lengh
            })

        return names_list

    def handle_name(self, data, count):
        index = 0
        name_data = []
        for _ in range(count):
            data = struct.unpack('B', data, offset=index)
            index += 1

            name_data.append({
                'data': name_data
            })
    
        return name_data

    def handle_evb_file_info(self, data, count):
        index = 0
        evb = []
        for _ in range(count):
            evb_value = struct.unpack('I', data, offset=index)
            index += 4

            evb.append({
                'value': evb_value
            })

        return evb
    
    def create_blender_objects(self, parsed_data):
        self.create_armature(parsed_data)
        self.create_meshes(parsed_data)
        self.create_materials(parsed_data)

    def create_armature(parsed_data):
        for i in range (parsed_data['skeleton']):
            bpy.data.armatures.new(f"Armature_{i}")

    def create_meshes(parsed_data):
        for mesh_data in parsed_data['mesh']:
            mesh_name = f"Mesh_{mesh_data['name_index']}"
            mesh_data_blender = bpy.data.meshes.new(mesh_name)
            mesh_obj = bpy.data.objects.new(mesh_name, mesh_data_blender)

    def create_materials():
        pass

def menu_import(self, context):
    self.layout.operator(MuaImport.bl_idname, text="Import MUA File")

# 注册插件
bpy.utils.register_class(MuaImport)
bpy.types.TOPBAR_MT_file_import.append(menu_import)

# 注销插件
def unregister():
    bpy.utils.unregister_class(MuaImport)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)