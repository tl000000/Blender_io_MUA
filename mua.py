import bpy
import os
import struct
from mathutils import Matrix, Vector

# Maya 到 Blender 的单位转换比例
MAYA_TO_BLENDER_SCALE = 0.01  # 1 cm (Maya) = 0.01 m (Blender)

# 读取地址表
def read_address_table(file):
    file.seek(0x20)  # 跳转到地址表起始位置
    address_table = []
    
    # 每个条目8字节：起始地址（4字节）、数据块数（4字节）
    while file.tell() < 0xA8:  # 读取到地址表结束位置
        entry = file.read(8)  # 每个条目8字节
        if not entry:
            break
        
        # 解析起始地址和数据块数
        start_address, block_count = struct.unpack('<II', entry)
        address_table.append({
            'start': start_address,
            'block_count': block_count
        })
    
    return address_table

# 读取数据块
def read_data_block(file, start_address, block_size, block_count):
    file.seek(start_address)
    blocks = []
    for _ in range(block_count):
        block_data = file.read(block_size)
        blocks.append(block_data)
    return blocks

# 解析名称数据
def parse_names(file, name_address_index, name_data_index):
    names = []
    
    # 读取名称地址索引块（第十六个条目）
    name_address_blocks = read_data_block(file, name_address_index['start'], 0x10, name_address_index['block_count'])
    
    # 读取名称数据块（第十七个条目）
    name_data_blocks = read_data_block(file, name_data_index['start'], 0x10, name_data_index['block_count'])
    
    for block in name_address_blocks:
        # 解析名称地址偏移和名称长度
        name_offset, name_length = struct.unpack_from('<II', block, offset=0)
        
        # 跳转到名称数据的地址
        file.seek(name_data_index['start'] + name_offset)
        
        # 读取名称数据
        name_data = file.read(name_length)
        
        # 解析名称数据（假设为 Shift_JIS 编码）
        try:
            name = name_data.decode('shift_jis', errors='replace')
            names.append(name)
        except UnicodeDecodeError:
            # 如果解码失败，使用占位符
            names.append('?')
    
    return names

# 解析骨架数据
def parse_skeleton(data):
    skeletons = []
    index = 0
    buffer_length = len(data)
    
    # 每个骨架数据长度为 0x20 字节
    while index + 0x20 <= buffer_length:
        # 读取骨骼偏移量（4字节）
        bone_offset = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取骨骼数量（4字节）
        bone_count = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 忽略剩余数据（0x18 字节）
        index += 0x18
        
        skeletons.append({
            'bone_offset': bone_offset,
            'bone_count': bone_count
        })
    
    return skeletons

# 解析骨骼数据
def parse_bones(data, bone_offset, bone_count):
    bones = []
    index = bone_offset * 0x130  # 每个骨骼数据长度为 0x130 字节
    buffer_length = len(data)
    
    for _ in range(bone_count):
        if index + 0x130 > buffer_length:
            break  # 超出数据范围，退出循环
        
        # 读取名称索引（4字节）
        name_index = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取骨骼类型（4字节）
        bone_type = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取骨骼位置（12字节，3个浮点数，顺序为 Z、Y、X）
        position_z, position_y, position_x = struct.unpack_from('<3f', data, offset=index)
        index += 12
        
        # 读取骨骼旋转角度（12字节，3个浮点数）
        rotation = struct.unpack_from('<3f', data, offset=index)
        index += 12
        
        # 读取骨骼缩放（12字节，3个浮点数）
        scale = struct.unpack_from('<3f', data, offset=index)
        index += 12
        
        # 读取骨骼末端（12字节，3个浮点数，顺序为 Z、Y、X）
        end_z, end_y, end_x = struct.unpack_from('<3f', data, offset=index)
        index += 12
        
        # 读取骨骼索引号（4字节）
        bone_index = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取父骨骼索引（4字节）
        parent_index = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取子骨骼索引（4字节）
        child_index = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取下一个同级骨骼索引（4字节）
        sibling_index = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取三个轴向的旋转矩阵（3个64字节，每个矩阵16个浮点数）
        matrices = []
        for _ in range(3):
            matrix = struct.unpack_from('<16f', data, offset=index)
            matrices.append(matrix)
            index += 64
        
        # 读取动画关键帧数（4字节）
        keyframe_count = struct.unpack_from('<I', data, offset=index)[0]
        index += 4
        
        # 读取动画关键帧值索引（4个4字节）
        keyframe_indices = struct.unpack_from('<4I', data, offset=index)
        index += 16
        
        # 忽略剩余数据（0x130 - 已读取的字节数）
        index += 0x130 - (4 * 15 + 12 * 4 + 64 * 3 + 4 + 16)
        
        bones.append({
            'name_index': name_index,
            'bone_type': bone_type,
            'position': (position_x, position_y, position_z),  # 调整为 X、Y、Z 顺序
            'rotation': rotation,
            'scale': scale,
            'end': (end_x, end_y, end_z),  # 调整为 X、Y、Z 顺序
            'bone_index': bone_index,
            'parent_index': parent_index,
            'child_index': child_index,
            'sibling_index': sibling_index,
            'matrices': matrices,
            'keyframe_count': keyframe_count,
            'keyframe_indices': keyframe_indices
        })
    
    return bones

# 在Blender中创建骨架和骨骼
def create_skeleton(skeletons, bones_data, names):
    for skeleton in skeletons:
        # 创建一个新的骨架对象
        armature = bpy.data.armatures.new(name=f"Skeleton_{skeleton['bone_offset']}")
        armature_obj = bpy.data.objects.new(name=f"Skeleton_{skeleton['bone_offset']}", object_data=armature)
        bpy.context.collection.objects.link(armature_obj)
        
        # 设置骨架对象为活动对象
        bpy.context.view_layer.objects.active = armature_obj
        armature_obj.select_set(True)
        
        # 进入编辑模式以添加骨骼
        bpy.ops.object.mode_set(mode='EDIT')
        
        # 创建骨骼
        bones = {}
        for bone_data in bones_data[skeleton['bone_offset']:skeleton['bone_offset'] + skeleton['bone_count']]:
            # 根据名称索引获取骨骼名称
            if bone_data['name_index'] < len(names):
                bone_name = names[bone_data['name_index']]
            else:
                bone_name = f"Bone_{bone_data['bone_index']}"
            
            # 创建骨骼
            bone = armature.edit_bones.new(bone_name)
            bones[bone_data['bone_index']] = bone
            
            # 设置骨骼位置和末端（应用单位缩放和顺序调整）
            bone.head = Vector(bone_data['position']) * MAYA_TO_BLENDER_SCALE
            bone.tail = Vector(bone_data['end']) * MAYA_TO_BLENDER_SCALE
            
            # 设置父骨骼
            if bone_data['parent_index'] != 0xFFFFFFFF:  # 假设0xFFFFFFFF表示无父骨骼
                parent_bone = bones.get(bone_data['parent_index'])
                if parent_bone:
                    bone.parent = parent_bone
            
            # 应用旋转矩阵
            if bone_data['matrices']:
                # 使用第一个旋转矩阵（假设为主要旋转矩阵）
                matrix_data = bone_data['matrices'][0]
                matrix = Matrix([
                    [matrix_data[0], matrix_data[1], matrix_data[2], matrix_data[3]],
                    [matrix_data[4], matrix_data[5], matrix_data[6], matrix_data[7]],
                    [matrix_data[8], matrix_data[9], matrix_data[10], matrix_data[11]],
                    [matrix_data[12], matrix_data[13], matrix_data[14], matrix_data[15]]
                ])
                bone.matrix = matrix
            
            # 打印骨骼信息
            print(f"骨骼名称: {bone_name}")
            print(f"骨骼位置: {bone.head}")
            print(f"骨骼末端: {bone.tail}")
            print(f"父骨骼索引: {bone_data['parent_index']}")
            print(f"旋转矩阵: {bone.matrix}")
            print("------")
        
        # 退出编辑模式
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 打印调试信息
        print(f"骨架 {skeleton['bone_offset']} 已创建并链接到场景。")
        print(f"骨骼数量: {skeleton['bone_count']}")

# 导入模型
def import_metadata_model(filepath):
    with open(filepath, 'rb') as file:
        # 读取地址表
        address_table = read_address_table(file)
        
        # 解析名称数据（第十六个和第十七个条目）
        name_address_index = address_table[15]  # 第十六个条目
        name_data_index = address_table[16]  # 第十七个条目
        names = parse_names(file, name_address_index, name_data_index)
        
        # 解析骨架数据块（假设骨架数据块是第一个块）
        skeleton_data = read_data_block(file, address_table[0]['start'], 0x20, address_table[0]['block_count'])
        skeletons = parse_skeleton(skeleton_data[0])  # 假设骨架数据块只有一个块
        
        # 解析骨骼数据块（假设骨骼数据块是第二个块）
        bones_data = read_data_block(file, address_table[1]['start'], 0x130, address_table[1]['block_count'])
        bones = []
        for skeleton in skeletons:
            # 解析每个骨架对应的骨骼数据
            bones.extend(parse_bones(b''.join(bones_data), skeleton['bone_offset'], skeleton['bone_count']))
        
        # 在Blender中创建骨架和骨骼
        if skeletons and bones:
            create_skeleton(skeletons, bones, names)
        
        print("解析的名称数据:", names)
        print("解析的骨架数据:", skeletons)
        print("解析的骨骼数据:", bones)

# 定义导入操作类
class ImportMetadataModel(bpy.types.Operator):
    """导入元数据格式模型"""
    bl_idname = "import_scene.metadata_model"
    bl_label = "导入元数据模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 文件路径属性
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    # 执行导入操作
    def execute(self, context):
        # 验证文件后缀名
        if not self.filepath.lower().endswith('.mua'):
            self.report({'ERROR'}, "文件后缀名必须是 .mua")
            return {'CANCELLED'}
        
        try:
            import_metadata_model(self.filepath)
            self.report({'INFO'}, "模型导入成功")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"导入失败: {str(e)}")
            return {'CANCELLED'}
    
    # 打开文件选择器
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# 定义菜单项
def menu_func_import(self, context):
    self.layout.operator(ImportMetadataModel.bl_idname, text="元数据模型 (.mua)")

# 注册插件
def register():
    bpy.utils.register_class(ImportMetadataModel)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

# 注销插件
def unregister():
    bpy.utils.unregister_class(ImportMetadataModel)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()