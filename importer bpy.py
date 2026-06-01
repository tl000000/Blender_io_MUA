import bpy
import os
import math
import struct
from mathutils import Matrix, Vector, Quaternion,Euler
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

bl_info = {
    "name": "Mua Importer",
    "author": "tianling",
    "description": "",
    "blender": (4, 2, 19),
    "version": (0, 0, 1),
    "location": "",
    "warning": "Unfinshed",
    "category": "Import-Export",
}

class MuaImport(bpy.types.Operator, ImportHelper):
    bl_idname = "import_mua.mua"
    bl_label = "Import MUA File(.MUA)"
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
                if version == 1006:
                    data_types_order = [
                        'skeleton', 'bone', 'mesh', 'vertex_group', 
                        'material', 'texture', 'texture_name_index',
                        'uv_animation', 'bone_animation_list', 
                        'bone_animation_values', 'color_mixer_animation',
                        'evb_filename_index', 'polygon_and_vertex_group_index',
                        'vertex_info', 'triangle_strip_list', 
                        'name_info_index', 'name'
                    ]
                elif version == 1007:
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
                    0x2,#triangle_strip_list
                    0x10,#name_info_index
                    0x1,#name
                    0x4#evb_file_info
                ]

                # 地址表解析
                address_table_start = 0x20
                parsed_data = {}
                
                for i in range(0,data_type_count):
                    # 每个地址表项占8字节，前4字节为起始地址，后4字节为数量
                    f.seek(address_table_start + i * 8)
                    data_block_address, data_block_count = struct.unpack('II', f.read(8))
                    
                    # 获取数据类型名称
                    data_type_name = data_types_order[i]
                    
                    # 调用对应的处理函数
                    handler = data_type_handlers.get(data_type_name, None)

                    if handler:
                        f.seek(data_block_address)
                        if data_block_count:
                            block_data = f.read(data_block_count * single_data_size[i])
                            parsed_data[data_type_name] = handler(block_data, data_block_count)
                        else:
                            continue
                    else:
                        self.report({'WARNING'}, "Unhandled data type: {}".format(data_type_name))
                
                #empty scence
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.object.delete()

                # 创建blender对象
                self.create_blender_objects(parsed_data)

                return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

    def handle_skeleton(self, data, count):
        # 解析skeleton数据块的前8字节：前4字节为偏移数，后4字节为骨骼数量
        skeleton = []
        index = 0
        for _ in range(count):
            bone_offset = struct.unpack_from('I', data, offset=index)
            index += 4
            bone_count = struct.unpack_from('I', data, offset=index)
            index += 4
            unknow = struct.unpack_from('fff', data, offset=index)
            index += 12

            index += 12
            
            skeleton.append({
                'bone_offset':bone_offset,
                'bone_count':bone_count,
                'unknow':(unknow)
            })
        return skeleton
        
    def handle_bone(self, data, count):
        index = 0
        bone = []
        for _ in range(count):
            bone_name_index = struct.unpack_from('I', data, offset=index)
            index += 4
            bone_type = struct.unpack_from('I', data, offset=index)
            index += 4
            position = struct.unpack_from('fff', data, offset=index)
            index += 12
            rotation= struct.unpack_from('fff', data, offset=index)#radian
            index += 12
            scale = struct.unpack_from('fff', data, offset=index)
            index += 12
            unknow = struct.unpack_from('fff', data, offset=index)
            index += 12
            bone_index = struct.unpack_from('I', data, offset=index)
            index += 4
            parent_bone_index = struct.unpack_from('I', data, offset=index)
            index += 4
            child_bone_index = struct.unpack_from('I', data, offset=index)
            index += 4
            sibling_bone_index = struct.unpack_from('I', data, offset=index)
            index += 4
            matrices = []
            for _ in range(3):
                matrix = struct.unpack_from('16f', data, offset=index)
                matrices.append(matrix)
                index += 64
            keyframe_count = struct.unpack_from('I', data, offset=index)[0]
            index += 4
            keyframe_indices = struct.unpack_from('4I', data, offset=index)
            index += 16
            
            index += 20 #no data
            
            bone.append({
                'name_index': bone_name_index,
                'bone_type': bone_type,
                'position': position, 
                'rotation': rotation,
                'scale': scale,
                'unknow': unknow, 
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
            bind_skeleton_index = struct.unpack_from('f', data, offset=index)
            index += 8
            vertex_group_count = struct.unpack_from('I', data, offset=index)
            index += 4
            vertex_group_offset = struct.unpack_from('I', data, offset=index)
            index += 4
            vertex_count = struct.unpack_from('I', data, offset=index)
            index += 4
            vertex_offset = struct.unpack_from('I', data, offset=index)
            index += 4
            unknow = struct.unpack_from('38f', data, offset=index)#LOD or something
            index += 156
            name_index = struct.unpack_from('I', data, offset=index)
            index += 4
            skeletion_index = struct.unpack_from('I', data, offset=index)
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
            matirial_index = struct.unpack_from('I', data, offset=index)
            index += 4
            trianglestrp_count = struct.unpack_from('I', data, offset=index)
            index += 4
            trianglestrp_offset = struct.unpack_from('I', data, offset=index)
            index += 4
            evb_value_offset = struct.unpack_from('I', data, offset=index)
            index += 4
            evb_value_count = struct.unpack_from('I', data, offset=index)
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
            texture_count = struct.unpack_from('I', data, offset=index)
            index += 4
            texture_offset = struct.unpack_from('I', data, offset=index)
            index += 8
            mat_value = struct.unpack_from('12f', data, offset=index)
            index += 48
            color_blend = struct.unpack_from('I', data, offset=index)
            index += 4
            color_blend_frame = struct.unpack_from('I', data, offset=index)
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
            self_index = struct.unpack_from('I', data, offset=index)
            index += 4
            self_offset = struct.unpack_from('I', data, offset=index)
            index += 4
            uv_anim_count = struct.unpack_from('I', data, offset=index)
            index += 4
            uv_anim_offset = struct.unpack_from('I', data, offset=index)
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
            tex_name_index = struct.unpack_from('I', data, offset=index)
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
            move_x = struct.unpack_from('I', data, offset=index)
            index += 4
            move_y = struct.unpack_from('I', data, offset=index)
            index += 4
            scale_x = struct.unpack_from('I', data, offset=index)
            index += 4
            scale_y = struct.unpack_from('I', data, offset=index)
            index += 4
            keyframe = struct.unpack_from('I', data, offset=index)
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
        anim_data_count = int(count/4)
        for _ in range(anim_data_count):
            transition = struct.unpack_from('I', data, offset=index)
            index += 16
            rotation = struct.unpack_from('I', data, offset=index)
            index += 16
            Shearing = struct.unpack_from('I', data, offset=index)
            index += 16
            scale = struct.unpack_from('I', data, offset=index)
            index += 16

            anim_list.append({
                'index':(transition,rotation,Shearing,scale)
            })
        
        return anim_list

    def handle_bone_animation_values(self, data, count):
        index = 0
        anim = []
        for _ in range(count):
            value = struct.unpack_from('4f', data, offset=index)
            index += 16
            frame = struct.unpack_from('I', data, offset=index)
            index += 4

            index += 12#no data

            anim.append({
                'data':value,
                'frame':frame
            })
        
        return anim
            
    def handle_color_mixer_animation(self, data, count):
        index = 0
        blend = []
        for _ in range(count):
            color = struct.unpack_from('4f', data, offset=index)
            index += 16
            
            index += 16
            
            blend.append({
                'color':color
            })
        return blend

    def handle_evb_filename_index(self, data, count):
        index = 0
        evb_name = []
        for _ in range(count):
            evb_name_index = struct.unpack_from('I', data, offset=index)
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
            M_index = struct.unpack_from('I', data, offset=index)
            index += 4
            G_index = struct.unpack_from('I', data, offset=index)
            index += 4
            
            index += 24#no data

            M_G.append({
                'M_index':M_index,
                'G_index':G_index
            })
        
        return M_G

    def handle_vertex_info(self, data, count):
        vert = []
        for _ in range(count):
            position_z, position_x, position_y = struct.unpack_from('<fff', data, offset=0)
            normal_z, normal_x, normal_y = struct.unpack_from('<fff', data, offset=12)
            tanget_z, tanget_x, tanget_y = struct.unpack_from('<fff', data, offset=24)
            uv_x, uv_y = struct.unpack_from('<ff', data, offset=36)
            b, g, r, a = struct.unpack_from('<4B', data, offset=48)
            bone1, bone2, bone3 = struct.unpack_from('<fff', data, offset=52)
            weight1, weight2, weight3 = struct.unpack_from('<fff', data, offset=64)

            vert.append({
                'position': (position_x, position_y, position_z),
                'normal': (normal_x, normal_y, normal_z),
                'tanget': (tanget_x, tanget_y, tanget_z),
                'uv': (uv_x, uv_y),
                'vert_color': (r/255, g/255, b/255, a/255),
                'weight_bone': (bone1, bone2, bone3),
                'weight_value': (weight1, weight2, weight3)
            })
        
        return vert

    def handle_triangle_strip_list(self, data, count):
        index = 0
        strip = []
        for _ in range(count):
            vert_index = struct.unpack_from('B', data, offset=index)
            index += 1

            strip.append(vert_index)

        return strip

    def handle_name_info_index(self, data, count):
        index = 0
        names_list = []
        for _ in range(count):
            name_offset = struct.unpack_from('I', data, offset=index)
            index += 4
            name_lengh = struct.unpack_from('I', data, offset=index)
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
            ndata = struct.unpack_from('B', data, offset=index)[0]
            index += 1

            name_data.append(ndata)

        return name_data

    def handle_evb_file_info(self, data, count):
        index = 0
        evb = []
        for _ in range(count):
            evb_value = struct.unpack_from('I', data, offset=index)
            index += 4

            evb.append({
                'value': evb_value
            })

        return evb
    
    def create_blender_objects(self, parsed_data):
        names = self.getname(parsed_data)
        armture = self.create_armature(parsed_data,names)

    def getname(self,parsed_data):
        names = []
        name_count = len(parsed_data['name_info_index'])
        for i in range (name_count):
            data_offset = parsed_data['name_info_index'][i]['offset'][0]
            data_end =  data_offset + parsed_data['name_info_index'][i]['lengh'][0]

            namedata = bytes(parsed_data['name'][data_offset:data_end])
            
            try:
                name = namedata.decode('shift_jis', errors='replace')
                names.append(name)
            except UnicodeDecodeError:
            # 如果解码失败，使用占位符
                names.append('?')
        return names

    def create_armature(self,parsed_data,names):
        
        for i in range (len(parsed_data['skeleton'])):
            armature_name = f"Armature_{i}"
            if armature_name in bpy.data.armatures:
                bpy.data.armatures.remove(bpy.data.armatures[armature_name])
            armature_data =bpy.data.armatures.new(f"Armature_{i}")
            
            armature = bpy.data.objects.new(f"skel_{i}", armature_data)
            bpy.context.collection.objects.link(armature)
            
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='EDIT')
            
            bones = {}
            for bone in parsed_data['bone']:
                bone_name = names[bone['name_index'][0]]
                edit_bone = armature_data.edit_bones.new(bone_name)

                pos = list(bone['position'])
                #reset xyz order
                pos[0],pos[1],pos[2] = pos[1],pos[2],pos[0]
                rot = list(bone['rotation'])
                scl = list(bone['scale'])
                add = (math.cos(rot[0])*scl[0],math.cos(rot[1])*scl[1],math.cos(rot[1])*scl[1])
                
                edit_bone.head = Vector(pos)
                edit_bone.tail = Vector(pos) + Vector(add)

                if bone['parent_index'][0] != 0xFFFFFFFF:  
                    parent_name = names[bone['parent_index'][0]]
                    if parent_name in armature_data.edit_bones:
                        edit_bone.parent = armature_data.edit_bones[parent_name]
                
                bones[bone['bone_index'][0]] = edit_bone

            bpy.ops.object.mode_set(mode='OBJECT')

        return armature

    def decode_triangle_strip(indices):
        faces = []
        count = len(indices)
        if count < 3:
            pass

        for i in range(count - 2):
            a = indices[i]
            b = indices[i + 1]
            c = indices[i + 2]

            if a == b or b == c or a == c:
                continue

            if a == b or b == c or a == c:
                continue
        
            # 根据三角形位置决定顶点顺序（保持逆时针）
            if i % 2 == 0:
                face = (a, b, c)

            else:
            # 奇数三角形需要交换两个顶点以保持方向
                face = (b, a, c)  # 或者 (a, c, b)，需测试
            faces.append(face)
        return faces

    def create_meshes(self,parsed_data,names,armature):
        for mesh_data in parsed_data['mesh']:
            mesh_name = names[mesh_data['name_index'][0]]
            mesh_data_blender = bpy.data.meshes.new(mesh_name)
            mesh_obj = bpy.data.objects.new(mesh_name, mesh_data_blender)
            bpy.context.collection.objects.link(mesh_obj)
        
        vertices = []
        edges = []
        faces = []
        vertex_groups = {}

        if parsed_data['vertex_info']:
            for vert in parsed_data['vertex_info']:
                vertices.append(vert['position'])

        if parsed_data['triangle_strip_list']:
            # 这里需要根据三角形带数据生成面
            # 这是一个简化的示例，实际需要更复杂的处理
            strip_data = parsed_data['triangle_strip_list']
            # 假设每3个顶点组成一个三角形面
            for i in range(0, len(strip_data), 3):
                if i+2 < len(strip_data):
                    faces.append((
                        strip_data[i]['vert'],
                        strip_data[i+1]['vert'],
                        strip_data[i+2]['vert']
                    ))

        mesh_data_blender.from_pydata(vertices, edges, faces)
        mesh_data_blender.update()

        if parsed_data['vertex_info'] and mesh_data_blender.uv_layers:
            uv_layer = mesh_data_blender.uv_layers.active.data
            for poly in mesh_data_blender.polygons:
                for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    vert_idx = mesh_data_blender.loops[loop_idx].vertex_index
                    uv_coords = parsed_data['vertex_info'][vert_idx]['uv']
                    uv_layer[loop_idx].uv = (uv_coords[0], uv_coords[1])

        if armature and parsed_data['vertex_info']:
                for bone in armature.data.bones:
                    vertex_group = mesh_obj.vertex_groups.new(name=bone.name)
                    vertex_groups[bone.name] = vertex_group
                
                for i, vert in enumerate(parsed_data['vertex_info']):
                    weights = vert['weight_value']
                    bones = vert['weight_bone']
                    
                    # 分配权重到顶点组
                    for j in range(3):
                        if weights[j] > 0:
                            bone_name = f"Bone_{int(bones[j])}"
                            if bone_name in vertex_groups:
                                vertex_groups[bone_name].add([i], weights[j], 'REPLACE')

    def create_materials(self,parsed_data,names,texture_path, frame):
        obj = bpy.data.objects[obj_name]
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        if material_name in bpy.data.materials:
            mat = bpy.data.materials[material_name]
        else:
            mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        mapping = nodes.new(type='ShaderNodeMapping')
        tex_image = nodes.new(type='ShaderNodeTexImage')
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        output = nodes.new(type='ShaderNodeOutputMaterial')
        attr_color = nodes.new(type='ShaderNodeAttribute')
        mixer = nodes.new(type='ShaderNodeMix')

        tex_coord.location = (-800, 0)
        mapping.location = (-600, 0)
        tex_image.location = (-400, 0)
        bsdf.location = (-100, 0)
        output.location = (200, 0)
        attr_color.location = (-300, 300)
        mixer.location = (-100,300)

        attr_color.attribute_name = 'vert color'
        mapping.vector_type = 'TEXTURE'
        mixer.data_type = 'RGBA'
        mixer.blend_type = 'MULTIPLY'

        if os.path.exists(texture_path):
            tex_image.image = bpy.data.images.load(texture_path)

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], tex_image.inputs['Vector'])
        links.new(tex_image.outputs['Color'], mixer.inputs['A'])
        links.new(attr_color.outputs['Color'], mixer.inputs['B'])
        links.new(mixer.outputs['Result'], bsdf.inputs['Base Color'])
        links.new(tex_image.outputs['Alpha'], bsdf.inputs['Alpha'])
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # 为映射节点添加动画
        # X轴偏移动画
        mapping.inputs['Location'].keyframe_insert(data_path='default_value', 
                                               index=0, frame=start_frame)
        mapping.inputs['Location'].default_value[0] = 0.5  # X轴偏移值
        mapping.inputs['Location'].keyframe_insert(data_path='default_value', 
                                               index=0, frame=end_frame)
    
        # Y轴偏移动画
        mapping.inputs['Location'].keyframe_insert(data_path='default_value', 
                                               index=1, frame=start_frame)
        mapping.inputs['Location'].default_value[1] = 0.5  # Y轴偏移值
        mapping.inputs['Location'].keyframe_insert(data_path='default_value', 
                                               index=1, frame=end_frame)
    
        # X轴缩放动画
        mapping.inputs['Scale'].keyframe_insert(data_path='default_value', 
                                            index=0, frame=start_frame)
        mapping.inputs['Scale'].default_value[0] = 2.0  # X轴缩放值
        mapping.inputs['Scale'].keyframe_insert(data_path='default_value', 
                                            index=0, frame=end_frame)
    
        # Y轴缩放动画
        mapping.inputs['Scale'].keyframe_insert(data_path='default_value', 
                                            index=1, frame=start_frame)
        mapping.inputs['Scale'].default_value[1] = 2.0  # Y轴缩放值
        mapping.inputs['Scale'].keyframe_insert(data_path='default_value', 
                                            index=1, frame=end_frame)
    
        # 添加材质到对象
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    
        # 如果指定了顶点组，将材质分配到顶点组
        if vertex_group_name:
            assign_material_to_vertex_group(obj, mat, vertex_group_name)
    
        return mat

def menu_import(self, context):
    self.layout.operator(MuaImport.bl_idname, text="Import MUA File(.MUA)")

# 注册插件
def register():
    bpy.utils.register_class(MuaImport)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)

# 注销插件
def unregister():
    bpy.utils.unregister_class(MuaImport)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)

if __name__ == "__main__":
    register()
